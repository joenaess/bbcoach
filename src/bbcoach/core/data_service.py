"""
Data Service

Abstraction layer over data storage operations.
"""
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from bbcoach.config import settings
from bbcoach.data.storage import (
    load_players as storage_load_players,
    load_teams as storage_load_teams,
    load_schedule as storage_load_schedule,
)

logger = logging.getLogger(__name__)


class DataService:
    """Service for data operations."""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the data service.

        Args:
            data_dir: Path to data directory (defaults to settings)
        """
        self.data_dir = Path(data_dir or settings.data_dir)

        # Data cache to avoid repeated loading
        self._players_cache: Optional[pd.DataFrame] = None
        self._teams_cache: Optional[pd.DataFrame] = None
        self._schedule_cache: Optional[pd.DataFrame] = None

    def clear_cache(self):
        """Clear the data cache."""
        self._players_cache = None
        self._teams_cache = None
        self._schedule_cache = None
        logger.info("Data cache cleared")

    def load_players(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Load players data.

        Args:
            use_cache: Whether to use cached data

        Returns:
            DataFrame with player data
        """
        if use_cache and self._players_cache is not None:
            return self._players_cache

        df = storage_load_players()
        self._players_cache = df
        return df

    def load_teams(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Load teams data.

        Args:
            use_cache: Whether to use cached data

        Returns:
            DataFrame with team data
        """
        if use_cache and self._teams_cache is not None:
            return self._teams_cache

        df = storage_load_teams()
        self._teams_cache = df
        return df

    def load_schedule(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Load schedule data.

        Args:
            use_cache: Whether to use cached data

        Returns:
            DataFrame with schedule data
        """
        if use_cache and self._schedule_cache is not None:
            return self._schedule_cache

        df = storage_load_schedule()
        self._schedule_cache = df
        return df

    def get_data_status(self) -> dict:
        """
        Get status of data files.

        Returns:
            Dictionary with data file information
        """
        players_df = self.load_players()
        teams_df = self.load_teams()
        schedule_df = self.load_schedule()

        return {
            "players_count": len(players_df),
            "teams_count": len(teams_df),
            "schedule_count": len(schedule_df),
            "has_players": not players_df.empty,
            "has_teams": not teams_df.empty,
            "has_schedule": not schedule_df.empty,
            "seasons_in_data": (
                sorted(players_df["season"].unique().tolist())
                if not players_df.empty
                else []
            ),
        }
