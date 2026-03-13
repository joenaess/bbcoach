"""
Data Service

Abstraction layer over data storage operations.
"""
import logging
import json
from datetime import datetime
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
        self._players_cache: pd.DataFrame = pd.DataFrame()
        self._teams_cache: pd.DataFrame = pd.DataFrame()
        self._schedule_cache: pd.DataFrame = pd.DataFrame()

    def clear_cache(self):
        """Clear the data cache."""
        self._players_cache = pd.DataFrame()
        self._teams_cache = pd.DataFrame()
        self._schedule_cache = pd.DataFrame()
        logger.info("Data cache cleared")

    def get_metadata(self) -> dict:
        """Get the data storage metadata."""
        meta_path = self.data_dir / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading metadata: {e}")
        return {"last_fetched": None}

    def update_metadata(self):
        """Update the last_fetched timestamp in metadata."""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)
            
        meta_path = self.data_dir / "metadata.json"
        metadata = self.get_metadata()
        metadata["last_fetched"] = datetime.now().isoformat()
        
        try:
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing metadata: {e}")

    def load_players(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Load players data.

        Args:
            use_cache: Whether to use cached data

        Returns:
            DataFrame with player data
        """
        if use_cache and not self._players_cache.empty:
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
        if use_cache and not self._teams_cache.empty:
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
        if use_cache and not self._schedule_cache.empty:
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

        metadata = self.get_metadata()

        return {
            "players_count": len(players_df),
            "teams_count": len(teams_df),
            "schedule_count": len(schedule_df),
            "has_players": not players_df.empty,
            "has_teams": not teams_df.empty,
            "has_schedule": not schedule_df.empty,
            "last_fetched": metadata.get("last_fetched"),
            "seasons_in_data": (
                sorted(players_df["season"].unique().tolist())
                if not players_df.empty
                else []
            ),
        }
