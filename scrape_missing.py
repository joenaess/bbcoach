import asyncio
from playwright.async_api import async_playwright
import sys
import os

sys.path.append(os.path.abspath("src"))
from bbcoach.data.storage import save_players


async def scrape_missing_teams():
    missing_teams = [
        {
            "id": "2059",
            "name": "Boras Basket",
            "url": "https://www.proballers.com/basketball/team/2059/boras-basket",
        },
        {
            "id": "15363",
            "name": "Högsbo Basket",
            "url": "https://www.proballers.com/basketball/team/15363/hogsbo-basket",
        },
    ]

    seasons = [2025, 2024, 2023, 2022, 2021]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for team in missing_teams:
            print(f"Scraping {team['name']} ({team['id']})")

            for season in seasons:
                url = f"{team['url']}/{season}"
                print(f"  Visiting {url}")
                try:
                    await page.goto(url, timeout=60000)
                    await page.wait_for_timeout(3000)  # Wait for load

                    # Check if 404 or empty
                    content = await page.content()
                    if "404 Not Found" in content:
                        print(f"    {season}: 404 Not Found")
                        continue

                    # Parse players
                    players_data = await page.eval_on_selector_all(
                        "tbody tr",
                        """rows => rows.map(row => {
                            const cells = Array.from(row.querySelectorAll('td'));
                            const link = row.querySelector('td a');
                            return {
                                raw_stats: cells.map(c => c.innerText.trim()),
                                link: link ? link.href : null,
                                name: link ? link.innerText.trim() : null
                            }
                        })""",
                    )

                    parsed_players = []
                    for p_data in players_data:
                        if p_data["link"] and p_data["name"]:
                            parsed_players.append(
                                {
                                    "id": p_data["link"].split("/")[-2],
                                    "name": p_data["name"],
                                    "link": p_data["link"],
                                    "team_url": team["url"],
                                    "season": season,
                                    "raw_stats": p_data["raw_stats"],
                                    "team_id": team["id"],
                                }
                            )

                    if parsed_players:
                        save_players(parsed_players)
                        print(f"    Saved {len(parsed_players)} players for {season}")
                    else:
                        print(f"    No players found for {season}")

                except Exception as e:
                    print(f"    Error scraping {season}: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_missing_teams())
