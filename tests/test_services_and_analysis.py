import os
import sys
from unittest.mock import MagicMock

import pandas as pd
import pytest

sys.path.append(os.path.abspath("src"))

from bbcoach.analysis import (  # noqa: E402
    get_multi_season_aggregates,
    get_team_aggregates,
    predict_matchup,
    predict_matchup_multi_season,
)
from bbcoach.core import AnalyticsService, CoachService, DataService  # noqa: E402
from bbcoach.data.storage import save_players, save_schedule, save_teams  # noqa: E402


@pytest.fixture
def sample_players_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": "p1",
                "name": "Alpha Guard",
                "team_id": "t1",
                "season": 2024,
                "league": "Men",
                "PPG": 20.0,
                "RPG": 4.0,
                "APG": 7.0,
                "GP": 12,
                "MIN": 34.0,
                "FG%": 47.0,
                "3P%": 39.0,
                "TO": 2.5,
                "EFF": 21.0,
            },
            {
                "id": "p2",
                "name": "Alpha Center",
                "team_id": "t1",
                "season": 2024,
                "league": "Men",
                "PPG": 14.0,
                "RPG": 10.5,
                "APG": 1.5,
                "GP": 12,
                "MIN": 30.0,
                "FG%": 58.0,
                "3P%": 20.0,
                "TO": 1.8,
                "EFF": 19.5,
            },
            {
                "id": "p3",
                "name": "Beta Wing",
                "team_id": "t2",
                "season": 2024,
                "league": "Men",
                "PPG": 22.0,
                "RPG": 6.0,
                "APG": 4.0,
                "GP": 12,
                "MIN": 35.0,
                "FG%": 45.0,
                "3P%": 37.0,
                "TO": 3.0,
                "EFF": 20.0,
            },
        ]
    )


def test_get_team_aggregates(sample_players_df):
    stats = get_team_aggregates(sample_players_df, "t1", 2024)
    assert stats is not None
    assert stats["total_ppg"] == 34.0
    assert stats["total_rpg"] == 14.5
    assert stats["top_scorer"] == "Alpha Guard"
    assert stats["top_rebounder"] == "Alpha Center"
    assert stats["top_playmaker"] == "Alpha Guard"
    assert stats["rotation"][0]["PPG"] == 20.0
    assert stats["rotation"][0]["ppg"] == 20.0


def test_predict_matchup_and_multi_season(sample_players_df):
    single = predict_matchup(sample_players_df, "t1", "t2", 2024)
    assert "DEEP MATCHUP ANALYSIS" in single
    assert "Alpha Guard" in single
    assert "Beta Wing" in single

    multi_agg = get_multi_season_aggregates(sample_players_df, "t1")
    assert multi_agg is not None
    assert multi_agg["total_ppg"] == 34.0

    multi = predict_matchup_multi_season(sample_players_df, "t1", "t2")
    assert "MULTI-SEASON TREND ANALYSIS" in multi


def test_data_service_with_custom_dir(tmp_path, sample_players_df):
    save_players(sample_players_df.to_dict(orient="records"), data_dir=tmp_path)
    save_teams(
        [{"id": "t1", "name": "Alpha", "season": 2024, "league": "Men"}],
        data_dir=tmp_path,
    )
    save_schedule(
        [
            {
                "date": "2024-10-15",
                "team_id": "t1",
                "team_name": "Alpha",
                "opponent": "Beta",
                "opponent_id": "t2",
                "result": "90-85",
                "home_away": "Home",
                "season": 2024,
            }
        ],
        data_dir=tmp_path,
    )

    ds = DataService(data_dir=str(tmp_path))
    ds.update_metadata()

    status = ds.get_data_status()
    assert status["players_count"] == 3
    assert status["teams_count"] == 1
    assert status["schedule_count"] == 1
    assert status["last_fetched"] is not None
    assert status["seasons_in_data"] == [2024]

    analytics = AnalyticsService(ds)
    assert analytics.get_available_seasons("Men") == [2024]
    assert len(analytics.get_available_teams(2024, "Men")) == 1
    assert len(analytics.get_team_schedule("t1", 2024)) == 1


def test_coach_service_lazy_model_info():
    cs = CoachService(provider="gemini", model_name="gemini-2.0-flash")
    # Should not initialize _coach just to get model info
    info = cs.get_model_info()
    assert cs._coach is None
    assert "Gemini (gemini-2.0-flash)" in info

    mock_coach = MagicMock()
    mock_coach.ask.return_value = "Play fast in transition."
    cs._coach = mock_coach

    answer = cs.ask("What pace should we use?", "Fast guards")
    assert answer == "Play fast in transition."
    mock_coach.ask.assert_called_once()


def test_timestral_predictor_with_mock_forecaster():
    import numpy as np
    import torch

    from bbcoach.ai.timestral_predictor import (
        TimestralPredictor,
        _win_prob_from_quantiles,
        canonical_team_name,
    )

    assert canonical_team_name("Högsbo Basket") == "Högsbo Lions"
    assert canonical_team_name("Norrköping Dolphins") == "Norrköping Dolphins"

    q_levels = tuple(
        [0.02, 0.05]
        + [round(x / 100.0, 2) for x in range(10, 95, 5)]
        + [0.95, 0.98]
    )
    # Positive quantiles -> >50% win probability
    pos_q = np.linspace(-5.0, 20.0, 21)
    wp = _win_prob_from_quantiles(pos_q, q_levels)
    assert 0.5 < wp < 1.0

    # Build a synthetic schedule DataFrame with completed and upcoming 2026-2027 games
    rows = []
    for i in range(65):
        rows.append(
            {
                "date": f"Oct {(i % 28) + 1}, 2025, 7:00 PM",
                "team_id": "t1",
                "team_name": "Norrköping Dolphins",
                "opponent": "BC Luleå",
                "opponent_id": "t2",
                "result": "90-80 (W)",
                "team_score": 90.0,
                "opponent_score": 80.0,
                "point_diff": 10.0,
                "home_away": "Home" if i % 2 == 0 else "Away",
                "season": 2025,
                "league": "Men",
            }
        )
        rows.append(
            {
                "date": f"Oct {(i % 28) + 1}, 2025, 7:00 PM",
                "team_id": "t2",
                "team_name": "BC Luleå",
                "opponent": "Norrköping Dolphins",
                "opponent_id": "t1",
                "result": "80-90 (L)",
                "team_score": 80.0,
                "opponent_score": 90.0,
                "point_diff": -10.0,
                "home_away": "Away" if i % 2 == 0 else "Home",
                "season": 2025,
                "league": "Men",
            }
        )
    # Upcoming 2026-2027 game
    rows.append(
        {
            "date": "Nov 10, 2026, 7:04 PM",
            "team_id": "t1_2026",
            "team_name": "Norrköping Dolphins",
            "opponent": "BC Luleå",
            "opponent_id": "t2_2026",
            "result": "Upcoming",
            "team_score": None,
            "opponent_score": None,
            "point_diff": None,
            "home_away": "Home",
            "season": 2026,
            "league": "Men",
        }
    )
    sched_df = pd.DataFrame(rows)

    def fake_forecast(context, prediction_length, **kwargs):
        ctx_arr = np.asarray(context)
        b, v, _ = ctx_arr.shape
        # Return deterministic increasing quantiles around 85 (or +8 for diff)
        base = 85.0 if v == 2 else 8.0
        q_grid = np.linspace(base - 10.0, base + 10.0, 21, dtype=np.float32)
        tensor = torch.tensor(np.broadcast_to(q_grid, (b, v, prediction_length, 21)).copy())
        res = MagicMock()
        res.quantiles = tensor
        res.quantile_levels = q_levels
        return res

    mock_fc = MagicMock()
    mock_fc.forecast.side_effect = fake_forecast

    predictor = TimestralPredictor()
    predictor._forecaster = mock_fc

    traj = predictor.forecast_team_trajectory(
        sched_df, "Norrköping Dolphins", league="Men", horizon=2
    )
    assert traj is not None
    assert traj["team_name"] == "Norrköping Dolphins"
    assert len(traj["forecast"]) >= 1
    assert traj["forecast"][0]["win_probability"] > 50.0
    assert "coaching_tag" in traj["forecast"][0]
    assert "target_score_to_win" in traj["forecast"][0]
    assert len(traj["schedule_coaching_insights"]) == 3

    h2h = predictor.predict_head_to_head(
        sched_df, "Norrköping Dolphins", "BC Luleå", league="Men", team_a_home=True
    )
    assert h2h is not None
    assert h2h["team_a"] == "Norrköping Dolphins"
    assert h2h["team_b"] == "BC Luleå"
    assert "win_prob_a" in h2h
    assert "coach_brief" in h2h
    assert h2h["coach_brief"]["target_score_to_win_75"] > h2h["coach_brief"]["target_score_to_win_50"]
    assert len(h2h["coach_brief"]["suggested_coach_prompts"]) == 3

    # Verify What-If defensive clamp + offensive boost increases Team A's projected spread & win prob
    h2h_boosted = predictor.predict_head_to_head(
        sched_df,
        "Norrköping Dolphins",
        "BC Luleå",
        league="Men",
        team_a_home=True,
        team_a_off_boost=5.0,
        team_a_def_boost=5.0,
    )
    assert h2h_boosted["spread"]["median"] > h2h["spread"]["median"]
    assert h2h_boosted["win_prob_a"] >= h2h["win_prob_a"]

    backtest = predictor.evaluate_historical_backtest(
        sched_df, league="Men", eval_games_per_team=4
    )
    assert "metrics" in backtest
    assert "timestral_209m" in backtest["metrics"]


