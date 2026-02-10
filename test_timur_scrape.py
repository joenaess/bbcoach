import asyncio
import os
import sys

sys.path.append(os.path.abspath("src"))
from bbcoach.data.scrapers import BasketballScraper


async def test_scrape():
    print("Testing Scraper for Timur Grinev...")
    url = "https://www.proballers.com/basketball/team/15363/boras-basket"
    season = 2024

    scraper = BasketballScraper(headless=True)
    await scraper.start()

    try:
        result = await scraper.scrape_team_season(url, season)

        if result and "players" in result:
            print(f"Scraped {len(result['players'])} player rows.")

            # Find ALL rows for Timur
            timur_rows = [p for p in result["players"] if "Timur" in p["name"]]

            if timur_rows:
                print(f"\nFound {len(timur_rows)} rows for Timur:")
                for i, row in enumerate(timur_rows):
                    print(f"\nRow {i}:")
                    print(f"Name: {repr(row['name'])}")
                    print(f"Raw Stats: {row['raw_stats']}")
                    if len(row["raw_stats"]) > 3:
                        print(f"PPG (Idx 3): {row['raw_stats'][3]}")
            else:
                print("❌ Timur Grinev not found.")

                # Print all names to check
                print(
                    "Names found:", [p["name"].strip() for p in result["players"][:10]]
                )

        else:
            print("❌ No data returned.")
    finally:
        await scraper.stop()


if __name__ == "__main__":
    asyncio.run(test_scrape())
