import logging
import sys
import os

# Ensure we can import from bbcoach
sys.path.append(os.path.abspath("src"))

from bbcoach.data.genius_scraper import GeniusScraper
from bbcoach.data.storage import save_players, save_teams

# Configure logging to show up in stdout for the UI
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Genius Sports Scraper...")
    scraper = GeniusScraper()

    # Configuration for Competitions
    competitions = [
        # --- MEN (SBL Herr) ---
        {"id": 41539, "name": "SBL Herr", "year": 2025, "league": "Men"},
        {"id": None, "name": "SBL Herr", "year": 2024, "league": "Men"},
        {"id": None, "name": "SBL Herr", "year": 2023, "league": "Men"},
        {"id": None, "name": "SBL Herr", "year": 2022, "league": "Men"},
        {"id": None, "name": "SBL Herr", "year": 2021, "league": "Men"},
        # --- WOMEN (SBL Dam) ---
        {"id": 42013, "name": "SBL Dam", "year": 2025, "league": "Women"},
        {"id": None, "name": "SBL Dam", "year": 2024, "league": "Women"},
        {"id": None, "name": "SBL Dam", "year": 2023, "league": "Women"},
        {"id": None, "name": "SBL Dam", "year": 2022, "league": "Women"},
        {"id": None, "name": "SBL Dam", "year": 2021, "league": "Women"},
    ]

    all_players = []
    all_teams = []

    total_comps = len(competitions)

    for i, comp in enumerate(competitions, 1):
        if comp["id"] is None:
            logger.info(f"Skipping {comp['name']} {comp['year']} - No ID")
            continue

        logger.info(
            f"Scraping Competition {i}/{total_comps}: {comp['name']} ({comp['league']})"
        )
        players, teams = scraper.scrape_competition(
            comp["id"], comp["year"], league=comp["league"]
        )

        if players:
            all_players.extend(players)
        if teams:
            for t in teams:
                t["season"] = comp["year"]
                t["league"] = comp["league"]
            all_teams.extend(teams)

    logger.info(f"Total Players Scraped: {len(all_players)}")
    logger.info(f"Total Teams Scraped: {len(all_teams)}")

    if all_players:
        logger.info("Saving players...")
        save_players(all_players, filename="players.parquet")

    if all_teams:
        logger.info("Saving teams...")
        save_teams(all_teams, filename="teams.parquet")

    logger.info("Scraping Complete!")


if __name__ == "__main__":
    main()
