import logging
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath("src"))

from bbcoach.data.genius_scraper import GeniusScraper
from bbcoach.data.storage import save_players, save_teams, save_schedule

logging.basicConfig(level=logging.INFO)


def run_scraper():
    scraper = GeniusScraper()

    # Configuration for Competitions
    # We only have confirmed IDs for 2025.
    # Placeholders for past seasons added as comments or dummy entries if we want to test logic without data.
    # Logic: If ID is None, skip.

    competitions = [
        # --- MEN (SBL Herr) ---
        {"id": 41539, "name": "SBL Herr", "year": 2025, "league": "Men"},
        {"id": None, "name": "SBL Herr", "year": 2024, "league": "Men"},  # Missing ID
        {"id": None, "name": "SBL Herr", "year": 2023, "league": "Men"},  # Missing ID
        {"id": None, "name": "SBL Herr", "year": 2022, "league": "Men"},  # Missing ID
        {"id": None, "name": "SBL Herr", "year": 2021, "league": "Men"},  # Missing ID
        # --- WOMEN (SBL Dam) ---
        {"id": 42013, "name": "SBL Dam", "year": 2025, "league": "Women"},
        {"id": None, "name": "SBL Dam", "year": 2024, "league": "Women"},  # Missing ID
        {"id": None, "name": "SBL Dam", "year": 2023, "league": "Women"},  # Missing ID
        {"id": None, "name": "SBL Dam", "year": 2022, "league": "Women"},  # Missing ID
        {"id": None, "name": "SBL Dam", "year": 2021, "league": "Women"},  # Missing ID
    ]

    all_players = []
    all_teams = []
    all_schedule = []

    for comp in competitions:
        if comp["id"] is None:
            logging.warning(
                f"Skipping {comp['name']} {comp['year']} ({comp['league']}) - No Competition ID"
            )
            continue

        logging.info(
            f"Starting Scrape: {comp['name']} {comp['year']} ({comp['league']})"
        )
        players, teams = scraper.scrape_competition(
            comp["id"], comp["year"], league=comp["league"]
        )

        if players:
            all_players.extend(players)
        if teams:
            # Enrich teams with metadata
            for t in teams:
                t["season"] = comp["year"]
                t["league"] = comp["league"]
            all_teams.extend(teams)

        # 3. Get Schedule
        logging.info(f"Fetching Schedule for {comp['name']}...")
        schedule = scraper.get_schedule(comp["id"])
        if schedule:
            # Enrich schedule with league/season
            for s in schedule:
                s["league"] = comp["league"]
                s["season"] = comp["year"]
            all_schedule.extend(schedule)
            logging.info(f"  Found {len(schedule)} games.")

    print(f"Total Players Scraped: {len(all_players)}")
    print(f"Total Teams Scraped: {len(all_teams)}")
    print(f"Total Games Scraped: {len(all_schedule)}")

    if all_players:
        save_players(all_players, filename="players.parquet")

    if all_teams:
        save_teams(all_teams, filename="teams.parquet")

    if all_schedule:
        save_schedule(all_schedule, filename="schedule.parquet")


if __name__ == "__main__":
    run_scraper()
