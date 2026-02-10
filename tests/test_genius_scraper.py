import unittest
from unittest.mock import patch
import os
import sys

sys.path.append(os.path.abspath("src"))
from bbcoach.data.genius_scraper import GeniusScraper


class TestGeniusScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = GeniusScraper()

    def test_parse_player_stats(self):
        # Mock HTML with multiple tables
        html = """
        <html>
        <body>
            <table>
                <thead>
                    <tr><th>Player</th><th>PPG</th><th>RPG</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td><a href="/person/123?">John Doe</a></td>
                        <td>10.5</td><td>5.0</td>
                    </tr>
                </tbody>
            </table>
            <table>
                <thead>
                    <tr><th>Player</th><th>MPG</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td><a href="/person/123?">John Doe</a></td>
                        <td>30.0</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """

        data = self.scraper.parse_player_stats(html)

        self.assertIn("123", data)
        player = data["123"]
        self.assertEqual(player["name"], "John Doe")
        self.assertEqual(player["genius_id"], "123")
        self.assertEqual(player["PPG"], 10.5)
        self.assertEqual(player["RPG"], 5.0)
        self.assertEqual(player["MIN"], 30.0)  # Normalized from MPG

    @patch("bbcoach.data.genius_scraper.GeniusScraper.fetch_page")
    def test_scrape_competition(self, mock_fetch):
        # Mock responses
        # 1. Global Stats
        mock_fetch.side_effect = [
            # Stats Page
            """
            <html><body><table>
                <thead><tr><th>Player</th><th>PPG</th></tr></thead>
                <tbody><tr><td><a href="/person/1">P1</a></td><td>20.0</td></tr></tbody>
            </table></body></html>
            """,
            # Teams Page
            """
            <html><body>
                <a href="/competition/1/team/10">Team A</a>
            </body></html>
            """,
            # Team Page (Roster)
            """
            <html><body>
                <div id="BLOCK_TEAM_HOME_PLAYERS">
                    <a href="/person/1">P1</a>
                </div>
            </body></html>
            """,
        ]

        players, teams = self.scraper.scrape_competition(1, 2025)

        self.assertEqual(len(teams), 1)
        self.assertEqual(teams[0]["id"], "10")

        self.assertEqual(len(players), 1)
        p1 = players[0]
        self.assertEqual(p1["id"], "1")
        self.assertEqual(p1["team_id"], "10")
        self.assertEqual(p1["PPG"], 20.0)


if __name__ == "__main__":
    unittest.main()
