"""
Analytics Service

Business logic for statistical analysis and predictions.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

from bbcoach.analysis import (
    get_team_aggregates,
    predict_matchup,
    predict_matchup_multi_season,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics operations."""

    def __init__(self, data_service, timestral_predictor=None):
        """
        Initialize the analytics service.

        Args:
            data_service: DataService instance for loading data
            timestral_predictor: Optional TimestralPredictor instance (lazy-loaded by default)
        """
        self.data_service = data_service
        self._timestral_predictor = timestral_predictor

    @property
    def timestral_predictor(self):
        """Lazy-load TimestralPredictor on first request."""
        if self._timestral_predictor is None:
            from bbcoach.ai.timestral_predictor import TimestralPredictor

            self._timestral_predictor = TimestralPredictor()
        return self._timestral_predictor

    def get_top_players(
        self, season: int, league: str = "Men", metric: str = "PPG", limit: int = 10
    ) -> list[dict]:
        """
        Get top players by a specific metric.

        Args:
            season: Season year
            league: League (Men/Women)
            metric: Statistic to sort by (PPG, RPG, APG, etc.)
            limit: Number of players to return

        Returns:
            List of player dictionaries
        """
        players_df = self.data_service.load_players()
        if players_df.empty:
            return []

        filtered = players_df[
            (players_df["season"] == season) & (players_df["league"] == league)
        ]

        if metric not in filtered.columns:
            logger.warning(f"Metric {metric} not found in data")
            return []

        top_players = filtered.sort_values(metric, ascending=False).head(limit)

        # Convert NaN values to None directly so JSON encoders handle them gracefully
        top_players = top_players.replace({np.nan: None})

        return top_players.to_dict(orient="records")

    def get_team_stats(self, team_id: str, season: int) -> Optional[dict]:
        """
        Get aggregated statistics for a team.

        Args:
            team_id: Team identifier
            season: Season year

        Returns:
            Dictionary with team statistics or None if not found
        """
        players_df = self.data_service.load_players()

        if players_df.empty:
            return None

        try:
            stats = get_team_aggregates(players_df, team_id, season)
            return stats
        except Exception as e:
            logger.error(f"Error getting team stats for {team_id}: {e}")
            return None

    def get_team_schedule(
        self, team_id: str, season: Optional[int] = None
    ) -> list[dict]:
        """
        Get schedule games for a specific team.

        Args:
            team_id: Team identifier
            season: Optional season filter

        Returns:
            List of schedule game dictionaries
        """
        schedule_df = self.data_service.load_schedule()
        if schedule_df.empty or "team_id" not in schedule_df.columns:
            return []

        filtered = schedule_df[schedule_df["team_id"].astype(str) == str(team_id)]
        if season is not None and "season" in filtered.columns:
            filtered = filtered[filtered["season"] == season]

        filtered = filtered.replace({np.nan: None})
        return filtered.to_dict(orient="records")

    def predict_matchup(
        self, team_a_id: str, team_b_id: str, season: int
    ) -> Optional[str]:
        """
        Predict the outcome of a matchup between two teams.

        Args:
            team_a_id: First team ID
            team_b_id: Second team ID
            season: Season year

        Returns:
            Matchup analysis text or None
        """
        players_df = self.data_service.load_players()

        if players_df.empty:
            return None

        try:
            analysis = predict_matchup(players_df, team_a_id, team_b_id, season)
            return analysis
        except Exception as e:
            logger.error(f"Error predicting matchup: {e}")
            return None

    def predict_matchup_multi_season(
        self, team_a_id: str, team_b_id: str
    ) -> Optional[str]:
        """
        Predict matchup based on multi-season data.

        Args:
            team_a_id: First team ID
            team_b_id: Second team ID

        Returns:
            Multi-season analysis or None
        """
        players_df = self.data_service.load_players()
        teams_df = self.data_service.load_teams()

        if players_df.empty:
            return None

        try:
            analysis = predict_matchup_multi_season(
                players_df, team_a_id, team_b_id, teams_df=teams_df
            )
            return analysis
        except Exception as e:
            logger.error(f"Error in multi-season prediction: {e}")
            return None

    def compare_players(
        self, player_names: list[str], season: int, league: str = "Men"
    ) -> Optional[pd.DataFrame]:
        """
        Compare multiple players.

        Args:
            player_names: List of player names
            season: Season year
            league: League (Men/Women)

        Returns:
            DataFrame with player comparison or None
        """
        players_df = self.data_service.load_players()

        if players_df.empty:
            return None

        filtered = players_df[
            (players_df["season"] == season)
            & (players_df["league"] == league)
            & (players_df["name"].isin(player_names))
        ]

        if filtered.empty:
            return None

        return filtered

    def get_available_seasons(self, league: str = "Men") -> list[int]:
        """Get list of available seasons for a league."""
        players_df = self.data_service.load_players()

        if players_df.empty:
            return []

        filtered = players_df[players_df["league"] == league]
        return sorted(filtered["season"].dropna().unique().astype(int).tolist(), reverse=True)

    def get_available_teams(self, season: int, league: str = "Men") -> list[dict]:
        """Get list of teams for a given season and league."""
        teams_df = self.data_service.load_teams()

        if teams_df.empty:
            return []

        filtered = teams_df[
            (teams_df["season"] == season) & (teams_df["league"] == league)
        ]

        return filtered.to_dict(orient="records")

    def forecast_team_trajectory(
        self, team_id: str, league: str = "Men", horizon: int = 6
    ) -> Optional[dict]:
        """
        Forecast upcoming team game trajectory using mistralai/Timestral-209M.
        """
        schedule_df = self.data_service.load_schedule()
        if schedule_df.empty:
            return None

        try:
            return self.timestral_predictor.forecast_team_trajectory(
                schedule_df, team_identifier=team_id, league=league, horizon=horizon
            )
        except Exception as e:
            logger.error(f"Error in Timestral trajectory forecast for {team_id}: {e}", exc_info=True)
            return None

    def predict_timestral_matchup(
        self,
        team_a_id: str,
        team_b_id: str,
        league: str = "Men",
        team_a_home: bool = True,
        pace_adjustment: float = 0.0,
        team_a_off_boost: float = 0.0,
        team_a_def_boost: float = 0.0,
    ) -> Optional[dict]:
        """
        Predict head-to-head matchup probabilities and score quantiles using Timestral-209M.
        """
        schedule_df = self.data_service.load_schedule()
        if schedule_df.empty:
            return None

        try:
            return self.timestral_predictor.predict_head_to_head(
                schedule_df,
                team_a_identifier=team_a_id,
                team_b_identifier=team_b_id,
                league=league,
                team_a_home=team_a_home,
                pace_adjustment=pace_adjustment,
                team_a_off_boost=team_a_off_boost,
                team_a_def_boost=team_a_def_boost,
            )
        except Exception as e:
            logger.error(
                f"Error in Timestral head-to-head prediction ({team_a_id} vs {team_b_id}): {e}",
                exc_info=True,
            )
            return None

    def evaluate_timestral_backtest(
        self, league: str = "Men", eval_games_per_team: int = 6
    ) -> Optional[dict]:
        """
        Evaluate Timestral-209M on historical SBL games vs Rolling-5 and Season Average baselines.
        """
        schedule_df = self.data_service.load_schedule()
        if schedule_df.empty:
            return None

        try:
            return self.timestral_predictor.evaluate_historical_backtest(
                schedule_df, league=league, eval_games_per_team=eval_games_per_team
            )
        except Exception as e:
            logger.error(f"Error in Timestral backtest evaluation: {e}", exc_info=True)
            return None


