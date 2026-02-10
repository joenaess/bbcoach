import unittest
from unittest.mock import patch
import os
import sys
import pandas as pd
from pathlib import Path
import shutil

sys.path.append(os.path.abspath("src"))
from bbcoach.data.genius_scraper import GeniusScraper
import bbcoach.data.storage as storage


class TestLeagueSeparation(unittest.TestCase):
    def setUp(self):
        self.scraper = GeniusScraper()
        # Use a temp directory for storage tests
        self.test_dir = Path("tests/temp_data")
        if not self.test_dir.exists():
            self.test_dir.mkdir()

        # Monkey patch DATA_DIR in storage module
        self.original_data_dir = storage.DATA_DIR
        storage.DATA_DIR = self.test_dir

    def tearDown(self):
        # Restore DATA_DIR
        storage.DATA_DIR = self.original_data_dir
        # cleanup
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch("bbcoach.data.genius_scraper.GeniusScraper.fetch_page")
    def test_scraper_injects_league(self, mock_fetch):
        # Mock HTML responses
        stats_html = """
        <html><body><table>
            <thead><tr><th>Player</th><th>PPG</th></tr></thead>
            <tbody><tr><td><a href="/person/1">P1</a></td><td>20.0</td></tr></tbody>
        </table></body></html>
        """
        teams_html = """<html><body><a href="/competition/100/team/10">Team A</a></body></html>"""
        roster_html = """<html><body><div id="BLOCK_TEAM_HOME_PLAYERS"><a href="/person/1">P1</a></div></body></html>"""

        mock_fetch.side_effect = [stats_html, teams_html, roster_html]

        # Run scrape for "Men"
        players, teams = self.scraper.scrape_competition(100, 2025, league="Men")

        self.assertEqual(len(players), 1)
        self.assertIn("league", players[0])
        self.assertEqual(players[0]["league"], "Men")

        # Verify keys exist (PPG, etc) even if not in original table (defaults)
        self.assertIn("RPG", players[0])
        self.assertEqual(players[0]["RPG"], 0.0)

    def test_storage_handles_leagues(self):
        # Create dummy data
        men_players = [
            {
                "id": "1",
                "name": "P1",
                "team_id": "T1",
                "season": 2025,
                "league": "Men",
                "PPG": 10.0,
            }
        ]
        women_players = [
            {
                "id": "2",
                "name": "P2",
                "team_id": "T2",
                "season": 2025,
                "league": "Women",
                "PPG": 12.0,
            }
        ]

        # Save Men
        storage.save_players(men_players)

        # Save Women
        storage.save_players(women_players)

        # Load
        df = storage.load_players()

        self.assertEqual(len(df), 2)
        self.assertIn("league", df.columns)

        men_df = df[df["league"] == "Men"]
        women_df = df[df["league"] == "Women"]

        self.assertEqual(len(men_df), 1)
        self.assertEqual(men_df.iloc[0]["name"], "P1")

        self.assertEqual(len(women_df), 1)
        self.assertEqual(women_df.iloc[0]["name"], "P2")

    def test_load_players_legacy_compatibility(self):
        # Test loading data WITHOUT league column (should default to Men)
        # And WITH raw_stats (should calculate)

        # Create a dataframe manually and save it
        legacy_data = pd.DataFrame(
            [
                {
                    "id": "3",
                    "name": "Legacy Player",
                    "team_id": "T3",
                    "season": 2024,
                    "raw_stats": [
                        "Player",
                        "-",
                        "-",
                        "42",
                        "10",
                        "3.0",
                        "2",
                        "-",
                        "30.0",
                        "50%",
                        "40%",
                        "80%",
                    ],
                    # Indices: 3=PTS, 4=RPG, 5=APG, 6=GP, 8=MIN, 9=FG%, 10=3P%
                }
            ]
        )

        path = self.test_dir / "players.parquet"
        legacy_data.to_parquet(path)

        # Load using storage.load_players
        df = storage.load_players()

        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["league"], "Men")  # Default check
        self.assertEqual(df.iloc[0]["PPG"], 21.0)  # 42 points / 2 games = 21.0
        self.assertEqual(df.iloc[0]["RPG"], 5.0)

    def test_mixed_data_handling(self):
        # One row with raw_stats (Old), one without (New)
        mixed_data = [
            {
                "id": "Old",
                "name": "Old P",
                "team_id": "T1",
                "season": 2024,
                "league": "Men",
                "raw_stats": [
                    "P",
                    "-",
                    "-",
                    "30",
                    "5",
                    "5",
                    "3",
                    "-",
                    "30",
                    "-",
                    "-",
                    "-",
                ],
                "PPG": 0.0,  # Will be overwritten
            },
            {
                "id": "New",
                "name": "New P",
                "team_id": "T2",
                "season": 2025,
                "league": "Women",
                "PPG": 15.5,
                "RPG": 8.0,
                # No raw_stats
            },
        ]

        # Create DF and save
        storage.save_players(mixed_data)

        df = storage.load_players()

        self.assertEqual(len(df), 2)

        # Check Old (Should be parsed: 30 pts / 3 games = 10.0)
        old_p = df[df["id"] == "Old"].iloc[0]
        self.assertEqual(old_p["PPG"], 10.0)

        # Check New (Should preserve 15.5)
        new_p = df[df["id"] == "New"].iloc[0]
        self.assertEqual(new_p["PPG"], 15.5)


if __name__ == "__main__":
    unittest.main()
