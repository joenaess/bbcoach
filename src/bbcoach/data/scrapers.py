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

    # SBL Herr 2024-2025 (Genius ID: 41539)
    # SBL Dam (Genius ID: 42013)

    competitions = [
        {"id": 41539, "name": "SBL Herr", "year": 2025},
        {"id": 42013, "name": "SBL Dam", "year": 2025},
    ]

    all_players = []
    all_teams = []

    total_comps = len(competitions)

    for i, comp in enumerate(competitions, 1):
        logger.info(f"Scraping Competition {i}/{total_comps}: {comp['name']}")
        players, teams = scraper.scrape_competition(comp["id"], comp["year"])
        if players:
            all_players.extend(players)
        if teams:
            for t in teams:
                t["season"] = comp["year"]
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
