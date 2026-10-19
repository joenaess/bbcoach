"""
Timestral Time-Series Forecasting Service for BBCoach.

Uses `mistralai/Timestral-209M` for zero-shot probabilistic basketball game
and trajectory forecasting with known future covariates (home/away, opponent
offensive/defensive ratings, and categorical opponent encoding).
"""
import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TIMESTRAL_MODEL_ID = "mistralai/Timestral-209M"

# Canonical team name mapping across SBL seasons (2021-2027)
TEAM_NAME_ALIASES: dict[str, str] = {
    "Högsbo Basket": "Högsbo Lions",
    "Umeå BSKT": "Umeå Basket",
    "Sloga": "Sloga Uppsala",
    "IK Eos": "IK Eos Lund",
    "Östersunds Basket": "Östersund Basket",
    "Mark Basket": "Mark Borås",
}


def canonical_team_name(name: str) -> str:
    """Normalize historical club names to their canonical 2026-2027 name."""
    cleaned = str(name or "").strip()
    return TEAM_NAME_ALIASES.get(cleaned, cleaned)


def parse_genius_date(date_str: str, fallback_season: int = 2025) -> datetime:
    """Parse Genius Sports date strings like 'Sep 25, 2026, 6:00 PM'."""
    if not date_str or date_str == "Unknown":
        return datetime(fallback_season, 10, 1)
    cleaned = str(date_str).replace("Date / Time:", "").strip()
    for fmt in ("%b %d, %Y, %I:%M %p", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return datetime(fallback_season, 10, 1)


def _win_prob_from_quantiles(
    quantile_values: np.ndarray, quantile_levels: tuple[float, ...]
) -> float:
    """
    Estimate P(diff > 0) from the 21 quantile predictions of point differential.
    """
    q_vals = np.asarray(quantile_values, dtype=np.float64)
    q_lvls = np.asarray(quantile_levels, dtype=np.float64)

    if np.all(q_vals > 0):
        return 0.99
    if np.all(q_vals <= 0):
        return 0.01

    # Interpolate the quantile level where diff == 0: P(diff <= 0) = F(0)
    cdf_zero = float(np.interp(0.0, q_vals, q_lvls))
    win_prob = 1.0 - cdf_zero
    return float(np.clip(win_prob, 0.01, 0.99))


class TimestralPredictor:
    """Probabilistic basketball forecaster powered by mistralai/Timestral-209M."""

    def __init__(self, model_id: str = TIMESTRAL_MODEL_ID, device: Optional[str] = None):
        self.model_id = model_id
        self.device = device
        self._forecaster = None

    def _get_forecaster(self):
        """Lazy-load TimestralForecaster on first prediction request with automatic CPU fallback."""
        if self._forecaster is None:
            import torch
            from timestral import TimestralForecaster

            resolved_device = self.device
            if resolved_device is None:
                if torch.cuda.is_available():
                    try:
                        free_mem, _ = torch.cuda.mem_get_info()
                        resolved_device = "cuda" if free_mem > 1_200_000_000 else "cpu"
                    except Exception:
                        resolved_device = "cuda"
                else:
                    resolved_device = "cpu"

            logger.info(
                f"Loading Timestral model '{self.model_id}' on {resolved_device}..."
            )
            try:
                self._forecaster = TimestralForecaster.from_pretrained(
                    self.model_id, device=resolved_device
                )
            except Exception as e:
                if resolved_device != "cpu":
                    logger.warning(
                        f"CUDA load failed ({e}); falling back to CPU for '{self.model_id}'."
                    )
                    self._forecaster = TimestralForecaster.from_pretrained(
                        self.model_id, device="cpu"
                    )
                else:
                    raise
        return self._forecaster

    def prepare_schedule_df(self, schedule_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize team names, parse dates, and compute rolling team ratings."""
        if schedule_df.empty:
            return pd.DataFrame()

        df = schedule_df.copy()
        if "league" not in df.columns:
            df["league"] = "Men"
        if "season" not in df.columns:
            df["season"] = 2026

        df["canonical_team"] = df["team_name"].apply(canonical_team_name)
        df["canonical_opponent"] = df["opponent"].apply(canonical_team_name)
        df["parsed_date"] = [
            parse_genius_date(str(d), int(s))
            for d, s in zip(df["date"], df["season"])
        ]

        # Extract numeric scores from result if team_score not populated
        if "team_score" not in df.columns:
            df["team_score"] = None
            df["opponent_score"] = None
            df["point_diff"] = None

        df["team_score"] = pd.to_numeric(df["team_score"], errors="coerce")
        df["opponent_score"] = pd.to_numeric(df["opponent_score"], errors="coerce")
        df["point_diff"] = df["team_score"] - df["opponent_score"]

        df = df.sort_values(["parsed_date", "team_id"]).reset_index(drop=True)
        return df

    def _compute_team_strength_lookup(
        self, df: pd.DataFrame, league: str
    ) -> dict[str, tuple[float, float]]:
        """
        Compute historical offensive (PPG) and defensive (Opp PPG) averages per team.
        """
        completed = df[
            (df["league"] == league) & (df["team_score"].notna())
        ]
        if completed.empty:
            return {}

        league_avg = float(completed["team_score"].mean())
        lookup: dict[str, tuple[float, float]] = {}
        for team_name, grp in completed.groupby("canonical_team"):
            recent = grp.tail(25)
            off = float(recent["team_score"].mean()) if not recent.empty else league_avg
            dfn = (
                float(recent["opponent_score"].mean())
                if not recent.empty
                else league_avg
            )
            lookup[str(team_name)] = (off, dfn)
        return lookup

    def forecast_team_trajectory(
        self,
        schedule_df: pd.DataFrame,
        team_identifier: str,
        league: str = "Men",
        horizon: int = 6,
    ) -> Optional[dict]:
        """
        Forecast the next `horizon` games for a team using Timestral-209M.

        Args:
            schedule_df: Full schedule DataFrame across seasons
            team_identifier: Team ID or team name
            league: 'Men' or 'Women'
            horizon: Number of future games to forecast

        Returns:
            Dictionary with historical games, upcoming forecasts with 21-quantile
            intervals, win probabilities, and summary metrics.
        """
        df = self.prepare_schedule_df(schedule_df)
        if df.empty:
            return None

        league_df = df[df["league"] == league]
        if league_df.empty:
            return None

        # Match by team_id first to find canonical_team, or directly by name
        id_matches = league_df[league_df["team_id"].astype(str) == str(team_identifier)]
        if not id_matches.empty:
            target_team = str(id_matches.iloc[-1]["canonical_team"])
        else:
            target_team = canonical_team_name(team_identifier)

        team_games = league_df[league_df["canonical_team"] == target_team].copy()
        if team_games.empty:
            return None

        completed = team_games[team_games["team_score"].notna()].copy()
        if len(completed) < 4:
            return None

        last_completed_date = completed["parsed_date"].max()
        upcoming = team_games[
            (team_games["team_score"].isna())
            & (team_games["parsed_date"] > last_completed_date)
        ].copy()
        if upcoming.empty:
            upcoming = team_games[
                (team_games["team_score"].isna())
                & (team_games["season"] == team_games["season"].max())
            ].copy()

        pred_len = min(max(1, horizon), max(1, len(upcoming))) if not upcoming.empty else horizon
        upcoming_slice = upcoming.head(pred_len)

        strength_lookup = self._compute_team_strength_lookup(df, league)
        league_avg_pts = float(
            league_df[league_df["team_score"].notna()]["team_score"].mean()
        )

        # Build historical arrays
        hist_team_pts = completed["team_score"].to_numpy(dtype=np.float32)
        hist_opp_pts = completed["opponent_score"].to_numpy(dtype=np.float32)
        hist_diff = completed["point_diff"].to_numpy(dtype=np.float32)

        # Build known covariates over T + pred_len:
        # 1) is_home (+1 / -1)
        # 2) opponent offensive rating
        # 3) opponent defensive rating
        all_rows = (
            pd.concat([completed, upcoming_slice], ignore_index=True)
            if not upcoming_slice.empty
            else completed
        )

        is_home_cov = np.where(all_rows["home_away"] == "Home", 1.0, -1.0).astype(
            np.float32
        )
        opp_off_cov = np.array(
            [
                strength_lookup.get(str(opp), (league_avg_pts, league_avg_pts))[0]
                for opp in all_rows["canonical_opponent"]
            ],
            dtype=np.float32,
        )
        opp_def_cov = np.array(
            [
                strength_lookup.get(str(opp), (league_avg_pts, league_avg_pts))[1]
                for opp in all_rows["canonical_opponent"]
            ],
            dtype=np.float32,
        )

        # Pad covariates if upcoming_slice had fewer rows than pred_len
        if len(all_rows) < len(completed) + pred_len:
            pad_n = (len(completed) + pred_len) - len(all_rows)
            is_home_cov = np.concatenate([is_home_cov, np.zeros(pad_n, dtype=np.float32)])
            opp_off_cov = np.concatenate(
                [opp_off_cov, np.full(pad_n, league_avg_pts, dtype=np.float32)]
            )
            opp_def_cov = np.concatenate(
                [opp_def_cov, np.full(pad_n, league_avg_pts, dtype=np.float32)]
            )

        known_cov = np.stack([is_home_cov, opp_off_cov, opp_def_cov], axis=0)[
            None, ...
        ]  # (1, 3, T + pred_len)

        # Categorical opponent code for univariate point-diff forecast
        unique_opps = {name: float(i + 1) for i, name in enumerate(league_df["canonical_team"].unique())}
        cat_opp = np.array(
            [unique_opps.get(str(opp), 0.0) for opp in all_rows["canonical_opponent"]],
            dtype=np.float32,
        )
        if len(cat_opp) < len(completed) + pred_len:
            cat_opp = np.concatenate(
                [cat_opp, np.zeros((len(completed) + pred_len) - len(cat_opp), dtype=np.float32)]
            )
        cat_known_cov = cat_opp[None, None, :]  # (1, 1, T + pred_len)

        forecaster = self._get_forecaster()

        # 1. Multivariate score forecast (team_score, opponent_score)
        mv_context = np.stack([hist_team_pts, hist_opp_pts], axis=0)[None, ...]  # (1, 2, T)
        mv_forecast = forecaster.forecast(
            context=mv_context,
            prediction_length=pred_len,
            known_covariates=known_cov,
            clip_nonnegative=True,
        )

        # 2. Covariate-conditioned Point Differential forecast with opponent target-encoding
        diff_forecast = forecaster.forecast(
            context=hist_diff[None, None, :],
            prediction_length=pred_len,
            known_covariates=known_cov,
            categorical_known_covariates=cat_known_cov,
            clip_nonnegative=False,
        )

        q_levels = tuple(float(q) for q in diff_forecast.quantile_levels)
        mv_q = mv_forecast.quantiles.detach().cpu().numpy()[0]  # (2, pred_len, 21)
        diff_q = diff_forecast.quantiles.detach().cpu().numpy()[0, 0]  # (pred_len, 21)

        idx_10 = q_levels.index(0.1)
        idx_25 = q_levels.index(0.25)
        idx_50 = q_levels.index(0.5)
        idx_75 = q_levels.index(0.75)
        idx_90 = q_levels.index(0.9)

        # Recent history (last 12 completed games) for fan chart
        recent_completed = completed.tail(12)
        history_items = []
        for _, row in recent_completed.iterrows():
            history_items.append(
                {
                    "date": str(row["date"]),
                    "season": int(row["season"]),
                    "opponent": str(row["canonical_opponent"]),
                    "home_away": str(row["home_away"]),
                    "team_score": float(row["team_score"]),
                    "opponent_score": float(row["opponent_score"]),
                    "point_diff": float(row["point_diff"]),
                    "won": bool(row["point_diff"] > 0),
                }
            )

        forecast_items = []
        for step in range(pred_len):
            if step < len(upcoming_slice):
                u_row = upcoming_slice.iloc[step]
                g_date = str(u_row["date"])
                g_season = int(u_row["season"])
                g_opp = str(u_row["canonical_opponent"])
                g_ha = str(u_row["home_away"])
            else:
                g_date = f"Future Game +{step + 1}"
                g_season = 2026
                g_opp = "League Average Opponent"
                g_ha = "Home"

            t_q = mv_q[0, step]
            o_q = mv_q[1, step]
            d_q = diff_q[step]

            # Blend multivariate implied diff and direct target-encoded diff
            blended_diff_q = 0.5 * (t_q - np.flip(o_q)) + 0.5 * d_q
            win_prob = _win_prob_from_quantiles(blended_diff_q, q_levels)

            # Reconcile median team & opponent scores with blended spread
            total_median = float(t_q[idx_50] + o_q[idx_50])
            spread_median = float(blended_diff_q[idx_50])
            reconciled_t50 = round(0.5 * (total_median + spread_median), 1)
            reconciled_o50 = round(0.5 * (total_median - spread_median), 1)

            win_prob_pct = round(win_prob * 100.0, 1)
            q10_diff = round(float(blended_diff_q[idx_10]), 1)
            q90_diff = round(float(blended_diff_q[idx_90]), 1)

            if win_prob_pct < 42.0:
                coaching_tag = "Must-Prep / Underdog Test"
            elif win_prob_pct <= 60.0:
                coaching_tag = "Swing / Toss-Up Game"
            elif q10_diff < -6.0 and win_prob_pct < 75.0:
                coaching_tag = "Trap Alert / High Volatility"
            else:
                coaching_tag = "Rotation / Edge Opportunity"

            forecast_items.append(
                {
                    "step": step + 1,
                    "date": g_date,
                    "season": g_season,
                    "opponent": g_opp,
                    "home_away": g_ha,
                    "team_score": {
                        "median": reconciled_t50,
                        "q10": round(float(t_q[idx_10]), 1),
                        "q25": round(float(t_q[idx_25]), 1),
                        "q75": round(float(t_q[idx_75]), 1),
                        "q90": round(float(t_q[idx_90]), 1),
                    },
                    "opponent_score": {
                        "median": reconciled_o50,
                        "q10": round(float(o_q[idx_10]), 1),
                        "q25": round(float(o_q[idx_25]), 1),
                        "q75": round(float(o_q[idx_75]), 1),
                        "q90": round(float(o_q[idx_90]), 1),
                    },
                    "point_diff": {
                        "median": round(spread_median, 1),
                        "q10": q10_diff,
                        "q25": round(float(blended_diff_q[idx_25]), 1),
                        "q75": round(float(blended_diff_q[idx_75]), 1),
                        "q90": q90_diff,
                    },
                    "win_probability": win_prob_pct,
                    "coaching_tag": coaching_tag,
                    "target_score_to_win": round(float(o_q[idx_75]) + 1.0, 0),
                }
            )

        expected_wins = sum(item["win_probability"] / 100.0 for item in forecast_items)

        # Build stretch-level coaching insights
        hardest_game = min(forecast_items, key=lambda x: x["win_probability"])
        best_opportunity = max(forecast_items, key=lambda x: x["win_probability"])
        away_count = sum(1 for x in forecast_items if x["home_away"] == "Away")
        swing_games = [
            x for x in forecast_items if 40.0 <= x["win_probability"] <= 62.0
        ]

        swing_note = (
            "Focus late-game ATO & half-court execution on "
            + ", ".join(g["opponent"] for g in swing_games[:3])
            if swing_games
            else "Clear tier separation across this schedule window."
        )
        schedule_coaching_insights = [
            (
                f"Key Prep Target: vs {hardest_game['opponent']} ({hardest_game['date']}, "
                f"{hardest_game['home_away']}) has the lowest projected win probability "
                f"({hardest_game['win_probability']}%)."
            ),
            f"Swing Games ({len(swing_games)} of {pred_len}): {swing_note}",
            (
                f"Load & Rotation Management: {away_count}/{pred_len} upcoming games are on the road; "
                f"highest rotation development margin is vs {best_opportunity['opponent']} "
                f"({best_opportunity['win_probability']}% win prob)."
            ),
        ]

        return {
            "model": self.model_id,
            "team_name": target_team,
            "league": league,
            "historical_games_used": len(completed),
            "seasons_covered": sorted(completed["season"].unique().astype(int).tolist()),
            "recent_avg_ppg": round(float(completed.tail(10)["team_score"].mean()), 1),
            "recent_avg_opp_ppg": round(
                float(completed.tail(10)["opponent_score"].mean()), 1
            ),
            "expected_wins_next_n": round(expected_wins, 2),
            "horizon": pred_len,
            "schedule_coaching_insights": schedule_coaching_insights,
            "history": history_items,
            "forecast": forecast_items,
        }

    def predict_head_to_head(
        self,
        schedule_df: pd.DataFrame,
        team_a_identifier: str,
        team_b_identifier: str,
        league: str = "Men",
        team_a_home: bool = True,
        pace_adjustment: float = 0.0,
        team_a_off_boost: float = 0.0,
        team_a_def_boost: float = 0.0,
    ) -> Optional[dict]:
        """
        Predict a head-to-head matchup between Team A and Team B using Timestral-209M
        by forecasting from both teams' historical trajectories conditioned on the matchup
        and optional coach What-If tactical adjustments.
        """
        df = self.prepare_schedule_df(schedule_df)
        if df.empty:
            return None

        league_df = df[df["league"] == league]
        if league_df.empty:
            return None

        def resolve_name(ident: str) -> str:
            m = league_df[league_df["team_id"].astype(str) == str(ident)]
            if not m.empty:
                return str(m.iloc[-1]["canonical_team"])
            return canonical_team_name(ident)

        team_a = resolve_name(team_a_identifier)
        team_b = resolve_name(team_b_identifier)

        games_a = league_df[
            (league_df["canonical_team"] == team_a) & (league_df["team_score"].notna())
        ].copy()
        games_b = league_df[
            (league_df["canonical_team"] == team_b) & (league_df["team_score"].notna())
        ].copy()

        if len(games_a) < 4 or len(games_b) < 4:
            return None

        strength_lookup = self._compute_team_strength_lookup(df, league)
        league_avg_pts = float(
            league_df[league_df["team_score"].notna()]["team_score"].mean()
        )
        unique_opps = {
            name: float(i + 1) for i, name in enumerate(league_df["canonical_team"].unique())
        }
        forecaster = self._get_forecaster()

        def run_single_side(
            team_games: pd.DataFrame, opp_name: str, is_home_next: bool
        ) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[float, ...]]:
            t_pts = team_games["team_score"].to_numpy(dtype=np.float32)
            o_pts = team_games["opponent_score"].to_numpy(dtype=np.float32)
            diff = team_games["point_diff"].to_numpy(dtype=np.float32)

            hist_home = np.where(team_games["home_away"] == "Home", 1.0, -1.0).astype(
                np.float32
            )
            is_home_cov = np.append(
                hist_home, np.float32(1.0 if is_home_next else -1.0)
            )

            opp_off = [
                strength_lookup.get(str(o), (league_avg_pts, league_avg_pts))[0]
                for o in team_games["canonical_opponent"]
            ] + [strength_lookup.get(opp_name, (league_avg_pts, league_avg_pts))[0]]
            opp_def = [
                strength_lookup.get(str(o), (league_avg_pts, league_avg_pts))[1]
                for o in team_games["canonical_opponent"]
            ] + [strength_lookup.get(opp_name, (league_avg_pts, league_avg_pts))[1]]

            known_cov = np.stack(
                [
                    is_home_cov,
                    np.asarray(opp_off, dtype=np.float32),
                    np.asarray(opp_def, dtype=np.float32),
                ],
                axis=0,
            )[None, ...]

            cat_opp = np.asarray(
                [unique_opps.get(str(o), 0.0) for o in team_games["canonical_opponent"]]
                + [unique_opps.get(opp_name, 0.0)],
                dtype=np.float32,
            )[None, None, :]

            mv_fc = forecaster.forecast(
                context=np.stack([t_pts, o_pts], axis=0)[None, ...],
                prediction_length=1,
                known_covariates=known_cov,
                clip_nonnegative=True,
            )
            diff_fc = forecaster.forecast(
                context=diff[None, None, :],
                prediction_length=1,
                known_covariates=known_cov,
                categorical_known_covariates=cat_opp,
                clip_nonnegative=False,
            )

            mv_q = mv_fc.quantiles.detach().cpu().numpy()[0, :, 0, :]  # (2, 21)
            d_q = diff_fc.quantiles.detach().cpu().numpy()[0, 0, 0, :]  # (21,)
            return mv_q[0], mv_q[1], d_q, tuple(float(q) for q in diff_fc.quantile_levels)

        a_pts_q, a_opp_q, a_diff_q, q_levels = run_single_side(
            games_a, team_b, team_a_home
        )
        b_pts_q, b_opp_q, b_diff_q, _ = run_single_side(
            games_b, team_a, not team_a_home
        )

        # Combine Team A's offensive forecast & Team B's defensive forecast (and vice versa)
        # Apply optional What-If coaching adjustments:
        # - team_a_off_boost shifts Team A's scoring distribution
        # - team_a_def_boost reduces Team B's scoring distribution (positive = stronger defense)
        # - pace_adjustment shifts both teams' scoring distributions
        combined_a_q = (
            0.5 * (a_pts_q + b_opp_q)
            + float(team_a_off_boost)
            + 0.5 * float(pace_adjustment)
        )
        combined_b_q = (
            0.5 * (b_pts_q + a_opp_q)
            - float(team_a_def_boost)
            + 0.5 * float(pace_adjustment)
        )
        combined_diff_q = (
            0.5 * (a_diff_q - np.flip(b_diff_q))
            + float(team_a_off_boost)
            + float(team_a_def_boost)
        )

        win_prob_a = _win_prob_from_quantiles(combined_diff_q, q_levels)
        win_prob_b = 1.0 - win_prob_a

        idx_10 = q_levels.index(0.1)
        idx_25 = q_levels.index(0.25)
        idx_50 = q_levels.index(0.5)
        idx_75 = q_levels.index(0.75)
        idx_90 = q_levels.index(0.9)

        total_median = float(combined_a_q[idx_50] + combined_b_q[idx_50])
        spread_median = float(combined_diff_q[idx_50])
        score_a_med = round(0.5 * (total_median + spread_median), 1)
        score_b_med = round(0.5 * (total_median - spread_median), 1)

        # Head-to-head history
        h2h_games = games_a[games_a["canonical_opponent"] == team_b].tail(6)
        h2h_list = [
            {
                "date": str(r["date"]),
                "season": int(r["season"]),
                "home_away": str(r["home_away"]),
                "team_a_score": int(r["team_score"]),
                "team_b_score": int(r["opponent_score"]),
            }
            for _, r in h2h_games.iterrows()
        ]

        # Build actionable Coach Brief from the quantile forecast
        spread_width_80 = round(
            float(combined_diff_q[idx_90] - combined_diff_q[idx_10]), 1
        )
        if spread_width_80 >= 34.0:
            volatility_rating = "High Volatility"
        elif spread_width_80 >= 25.0:
            volatility_rating = "Moderate Volatility"
        else:
            volatility_rating = "Controlled / Low Volatility"

        win_prob_a_pct = round(win_prob_a * 100.0, 1)
        target_win_50 = round(score_b_med + 1.0, 0)
        target_win_75 = round(float(combined_b_q[idx_75]) + 1.0, 0)
        defensive_hold_target = round(float(combined_a_q[idx_25]) - 1.0, 0)

        if win_prob_a_pct >= 58.0:
            pace_advice = (
                f"Control Pace & Reduce Variance: {team_a} holds a +{round(spread_median, 1)} pt median edge "
                f"({win_prob_a_pct}% win prob). Limit live-ball turnovers, prevent transition 3s, and force {team_b} "
                f"to score against a set half-court defense."
            )
        elif win_prob_a_pct <= 42.0:
            pace_advice = (
                f"Increase Variance & Push Tempo: {team_a} trails by {abs(round(spread_median, 1))} pts at the median, "
                f"but the 75th–90th percentile ceiling reaches +{round(float(combined_diff_q[idx_90]), 1)} pts. "
                f"Push early offense, increase 3PT volume, and use ball-screen pressure to disrupt {team_b}."
            )
        else:
            pace_advice = (
                f"High-Leverage Execution Game: Projected as a 1–2 possession matchup "
                f"(median spread {round(spread_median, 1)} pts). "
                f"Prioritize ATO efficiency, defensive rebounding, and free-throw rate in crunch time."
            )

        a_home_games = games_a[games_a["home_away"] == "Home"].tail(10)
        a_away_games = games_a[games_a["home_away"] == "Away"].tail(10)
        venue_split_note = (
            f"{team_a} averages {round(float(a_home_games['team_score'].mean()), 1)} PPG at home vs "
            f"{round(float(a_away_games['team_score'].mean()), 1)} PPG on the road over their last 10."
            if not a_home_games.empty and not a_away_games.empty
            else f"Venue set to {'Home' if team_a_home else 'Away'} for {team_a}."
        )

        b_q75 = round(float(combined_b_q[idx_75]), 1)
        coach_brief = {
            "target_score_to_win_50": target_win_50,
            "target_score_to_win_75": target_win_75,
            "defensive_hold_target": defensive_hold_target,
            "volatility_rating": volatility_rating,
            "spread_interval_width_80": spread_width_80,
            "pace_and_variance_advice": pace_advice,
            "key_tactical_priorities": [
                (
                    f"Offensive Target ('Magic Number'): Reaching {int(target_win_75)}+ points pushes "
                    f"{team_a}'s win probability above 75% (50% threshold is {int(target_win_50)} pts)."
                ),
                (
                    f"Defensive Clamp Goal: Holding {team_b} at or below {int(defensive_hold_target)} points "
                    f"neutralizes their 75th-percentile scoring run ({b_q75} pts)."
                ),
                venue_split_note,
            ],
            "suggested_coach_prompts": [
                (
                    f"What defensive coverages should {team_a} run to hold "
                    f"{team_b} under {int(defensive_hold_target)} points?"
                ),
                (
                    f"Design a pace and rotation game plan for {team_a} vs {team_b} given a "
                    f"{win_prob_a_pct}% win probability and {volatility_rating.lower()}."
                ),
                (
                    f"What offensive sets and matchup hunts help {team_a} reach the "
                    f"{int(target_win_75)}-point target against {team_b}?"
                ),
            ],
        }

        return {
            "model": self.model_id,
            "league": league,
            "team_a": team_a,
            "team_b": team_b,
            "venue": f"{team_a} Home" if team_a_home else f"{team_b} Home",
            "win_prob_a": win_prob_a_pct,
            "win_prob_b": round(win_prob_b * 100.0, 1),
            "team_a_score": {
                "median": score_a_med,
                "q10": round(float(combined_a_q[idx_10]), 1),
                "q25": round(float(combined_a_q[idx_25]), 1),
                "q75": round(float(combined_a_q[idx_75]), 1),
                "q90": round(float(combined_a_q[idx_90]), 1),
            },
            "team_b_score": {
                "median": score_b_med,
                "q10": round(float(combined_b_q[idx_10]), 1),
                "q25": round(float(combined_b_q[idx_25]), 1),
                "q75": round(float(combined_b_q[idx_75]), 1),
                "q90": round(float(combined_b_q[idx_90]), 1),
            },
            "spread": {
                "median": round(spread_median, 1),
                "q10": round(float(combined_diff_q[idx_10]), 1),
                "q25": round(float(combined_diff_q[idx_25]), 1),
                "q75": round(float(combined_diff_q[idx_75]), 1),
                "q90": round(float(combined_diff_q[idx_90]), 1),
            },
            "total_points": {
                "median": round(total_median, 1),
                "q10": round(float(combined_a_q[idx_10] + combined_b_q[idx_10]), 1),
                "q90": round(float(combined_a_q[idx_90] + combined_b_q[idx_90]), 1),
            },
            "coach_brief": coach_brief,
            "head_to_head_history": h2h_list,
        }

    def evaluate_historical_backtest(
        self,
        schedule_df: pd.DataFrame,
        league: str = "Men",
        eval_games_per_team: int = 8,
    ) -> dict:
        """
        Evaluate Timestral-209M on held-out historical SBL games and compare against
        Season Average and Rolling-5 Average baselines.
        """
        df = self.prepare_schedule_df(schedule_df)
        completed = df[(df["league"] == league) & (df["team_score"].notna())].copy()
        if completed.empty:
            return {"error": "No completed games available for evaluation"}

        forecaster = self._get_forecaster()
        strength_lookup = self._compute_team_strength_lookup(df, league)
        league_avg_pts = float(completed["team_score"].mean())
        unique_opps = {
            name: float(i + 1) for i, name in enumerate(completed["canonical_team"].unique())
        }

        # Collect batched contexts across all teams with >= 60 completed games
        batch_mv_ctx = []
        batch_diff_ctx = []
        batch_known_cov = []
        batch_cat_cov = []
        team_eval_meta = []

        min_ctx_len = 56
        for team_name, grp in completed.groupby("canonical_team"):
            if len(grp) < min_ctx_len + eval_games_per_team:
                continue
            recent_grp = grp.tail(min_ctx_len + eval_games_per_team)
            train_part = recent_grp.iloc[:-eval_games_per_team]
            test_part = recent_grp.iloc[-eval_games_per_team:]

            t_pts = train_part["team_score"].to_numpy(dtype=np.float32)
            o_pts = train_part["opponent_score"].to_numpy(dtype=np.float32)
            diff = train_part["point_diff"].to_numpy(dtype=np.float32)

            is_home = np.where(recent_grp["home_away"] == "Home", 1.0, -1.0).astype(
                np.float32
            )
            opp_off = np.array(
                [
                    strength_lookup.get(str(o), (league_avg_pts, league_avg_pts))[0]
                    for o in recent_grp["canonical_opponent"]
                ],
                dtype=np.float32,
            )
            opp_def = np.array(
                [
                    strength_lookup.get(str(o), (league_avg_pts, league_avg_pts))[1]
                    for o in recent_grp["canonical_opponent"]
                ],
                dtype=np.float32,
            )
            cat_opp = np.array(
                [unique_opps.get(str(o), 0.0) for o in recent_grp["canonical_opponent"]],
                dtype=np.float32,
            )

            batch_mv_ctx.append(np.stack([t_pts, o_pts], axis=0))
            batch_diff_ctx.append(diff[None, :])
            batch_known_cov.append(np.stack([is_home, opp_off, opp_def], axis=0))
            batch_cat_cov.append(cat_opp[None, :])
            team_eval_meta.append((str(team_name), train_part, test_part))

        if not batch_mv_ctx:
            return {"error": "Insufficient historical games per team for backtesting"}

        mv_fc = forecaster.forecast(
            context=np.stack(batch_mv_ctx, axis=0),
            prediction_length=eval_games_per_team,
            known_covariates=np.stack(batch_known_cov, axis=0),
            clip_nonnegative=True,
        )
        diff_fc = forecaster.forecast(
            context=np.stack(batch_diff_ctx, axis=0),
            prediction_length=eval_games_per_team,
            known_covariates=np.stack(batch_known_cov, axis=0),
            categorical_known_covariates=np.stack(batch_cat_cov, axis=0),
            clip_nonnegative=False,
        )

        q_levels = tuple(float(q) for q in diff_fc.quantile_levels)
        mv_q_all = mv_fc.quantiles.detach().cpu().numpy()  # (B, 2, H, 21)
        diff_q_all = diff_fc.quantiles.detach().cpu().numpy()[:, 0, :, :]  # (B, H, 21)

        idx_10 = q_levels.index(0.1)
        idx_50 = q_levels.index(0.5)
        idx_90 = q_levels.index(0.9)

        timestral_spread_err = []
        timestral_score_err = []
        timestral_correct_win = []
        timestral_brier = []
        timestral_in_80 = []

        rolling_spread_err = []
        rolling_score_err = []
        rolling_correct_win = []

        season_spread_err = []
        season_score_err = []
        season_correct_win = []

        sample_predictions = []

        for b_idx, (team_name, train_df, test_df) in enumerate(team_eval_meta):
            season_mean_pts = float(train_df["team_score"].mean())
            season_mean_diff = float(train_df["point_diff"].mean())
            roll5_pts = float(train_df.tail(5)["team_score"].mean())
            roll5_diff = float(train_df.tail(5)["point_diff"].mean())

            for h_idx in range(eval_games_per_team):
                actual_row = test_df.iloc[h_idx]
                actual_pts = float(actual_row["team_score"])
                actual_opp_pts = float(actual_row["opponent_score"])
                actual_diff = float(actual_row["point_diff"])
                actual_win = 1.0 if actual_diff > 0 else 0.0

                t_q = mv_q_all[b_idx, 0, h_idx]
                o_q = mv_q_all[b_idx, 1, h_idx]
                d_q = diff_q_all[b_idx, h_idx]

                blended_diff_q = 0.5 * (t_q - np.flip(o_q)) + 0.5 * d_q
                pred_diff = float(blended_diff_q[idx_50])
                pred_total = float(t_q[idx_50] + o_q[idx_50])
                pred_pts = 0.5 * (pred_total + pred_diff)
                win_prob = _win_prob_from_quantiles(blended_diff_q, q_levels)

                timestral_spread_err.append(abs(pred_diff - actual_diff))
                timestral_score_err.append(abs(pred_pts - actual_pts))
                timestral_correct_win.append(
                    1.0 if (pred_diff > 0) == (actual_diff > 0) else 0.0
                )
                timestral_brier.append((win_prob - actual_win) ** 2)
                timestral_in_80.append(
                    1.0
                    if float(blended_diff_q[idx_10])
                    <= actual_diff
                    <= float(blended_diff_q[idx_90])
                    else 0.0
                )

                # Rolling-5 baseline
                rolling_spread_err.append(abs(roll5_diff - actual_diff))
                rolling_score_err.append(abs(roll5_pts - actual_pts))
                rolling_correct_win.append(
                    1.0 if (roll5_diff > 0) == (actual_diff > 0) else 0.0
                )

                # Season average baseline
                season_spread_err.append(abs(season_mean_diff - actual_diff))
                season_score_err.append(abs(season_mean_pts - actual_pts))
                season_correct_win.append(
                    1.0 if (season_mean_diff > 0) == (actual_diff > 0) else 0.0
                )

                if len(sample_predictions) < 12:
                    sample_predictions.append(
                        {
                            "team": team_name,
                            "opponent": str(actual_row["canonical_opponent"]),
                            "date": str(actual_row["date"]),
                            "season": int(actual_row["season"]),
                            "actual_score": f"{int(actual_pts)}-{int(actual_opp_pts)}",
                            "actual_diff": round(actual_diff, 1),
                            "predicted_diff": round(pred_diff, 1),
                            "predicted_q10": round(float(blended_diff_q[idx_10]), 1),
                            "predicted_q90": round(float(blended_diff_q[idx_90]), 1),
                            "win_prob": round(win_prob * 100.0, 1),
                            "correct": bool((pred_diff > 0) == (actual_diff > 0)),
                        }
                    )

        total_evaluated = len(timestral_spread_err)
        return {
            "model": self.model_id,
            "league": league,
            "teams_evaluated": len(team_eval_meta),
            "games_evaluated": total_evaluated,
            "metrics": {
                "timestral_209m": {
                    "win_accuracy_pct": round(
                        float(np.mean(timestral_correct_win)) * 100.0, 1
                    ),
                    "spread_mae": round(float(np.mean(timestral_spread_err)), 2),
                    "score_mae": round(float(np.mean(timestral_score_err)), 2),
                    "brier_score": round(float(np.mean(timestral_brier)), 4),
                    "interval_80_coverage_pct": round(
                        float(np.mean(timestral_in_80)) * 100.0, 1
                    ),
                },
                "rolling_5_baseline": {
                    "win_accuracy_pct": round(
                        float(np.mean(rolling_correct_win)) * 100.0, 1
                    ),
                    "spread_mae": round(float(np.mean(rolling_spread_err)), 2),
                    "score_mae": round(float(np.mean(rolling_score_err)), 2),
                },
                "season_avg_baseline": {
                    "win_accuracy_pct": round(
                        float(np.mean(season_correct_win)) * 100.0, 1
                    ),
                    "spread_mae": round(float(np.mean(season_spread_err)), 2),
                    "score_mae": round(float(np.mean(season_score_err)), 2),
                },
            },
            "sample_predictions": sample_predictions,
        }
