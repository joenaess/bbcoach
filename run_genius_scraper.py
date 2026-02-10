import logging
import sys
import os


# Ensure src is in path
sys.path.append(os.path.abspath("src"))

from bbcoach.data.genius_scraper import GeniusScraper
from bbcoach.data.storage import save_players, save_teams

logging.basicConfig(level=logging.INFO)


def run_scraper():
    scraper = GeniusScraper()

    # SBL Herr 2024-2025 (Genius ID: 41539)
    # SBL Dam (Genius ID: 42013)

    competitions = [
        {"id": 41539, "name": "SBL Herr", "year": 2025},
        {"id": 42013, "name": "SBL Dam", "year": 2025},
    ]

    all_players = []
    all_teams = []

    for comp in competitions:
        players, teams = scraper.scrape_competition(comp["id"], comp["year"])
        if players:
            all_players.extend(players)
        if teams:
            for t in teams:
                t["season"] = comp["year"]
                # Add competition name context if needed, but 'teams.parquet' usually just has basic info
            all_teams.extend(teams)

    print(f"Total Players Scraped: {len(all_players)}")
    print(f"Total Teams Scraped: {len(all_teams)}")

    # Save to storage
    # Note: verify that save_players handles the keys correctly or if we need to map them.
    # The keys in `all_players` are 'PPG', 'APG', 'name', 'team_id', etc.
    # We should ensure `storage.py` is ready for this.

    if all_players:
        save_players(all_players, filename="players_genius.parquet")
        # Also overwrite the main players.parquet if desired,
        # but let's separate for safety first or just overwrite per plan.
        # Plan said: "Update save_players ... handle new structure".
        # We will save to players.parquet directly as the user wants to switch.
        save_players(all_players, filename="players.parquet")

    if all_teams:
        save_teams(all_teams, filename="teams.parquet")


if __name__ == "__main__":
    run_scraper()
