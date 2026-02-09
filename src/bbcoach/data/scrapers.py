import asyncio
import json
import random
from typing import List, Dict
from playwright.async_api import async_playwright, Page
import sys
import os

sys.path.append(os.path.abspath("src"))
from bbcoach.data.storage import save_teams, save_players, save_schedule
import re

# Base URL
BASE_URL = "https://www.proballers.com"


class BasketballScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.playwright = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    async def stop(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _get_page(self) -> Page:
        page = await self.context.new_page()
        return page

    async def bypass_cloudflare(self, page: Page):
        # Allow time for Cloudflare challenge to pass
        # Random sleep to be safe
        await asyncio.sleep(8 + random.random() * 4)

    async def scrape_team_season(self, team_url: str, year: int) -> Dict:
        """
        Scrapes a team's page for a specific season.
        url format: .../team/ID/SLUG/YEAR
        """
        target_url = f"{team_url}/{year}"
        page = await self._get_page()

        try:
            print(f"Scraping {target_url}")
            await page.goto(target_url)
            await self.bypass_cloudflare(page)

            title = await page.title()
            if "404" in title or "Not Found" in title:
                print(f"404 for {target_url}")
                return None

            # Extract Roster
            # Simple extraction of all links in tables to find players
            # We assume a roster table exists.

            players = await page.eval_on_selector_all(
                "table tbody tr",
                """rows => rows.map(row => {
                const cells = Array.from(row.querySelectorAll('td'));
                if (cells.length < 2) return null;
                const link = cells[0].querySelector('a');
                return {
                    name: link ? link.innerText : cells[0].innerText,
                    link: link ? link.href : null,
                    stats: cells.map(c => c.innerText)
                };
            })""",
            )

            parsed_players = []
            for p in players:
                if p is None or not p["link"] or "/player/" not in p["link"]:
                    continue

                # Parse Stats if possible
                # stats[0] is Name/Pos/Height etc mixed usually or just Name
                # Usually standard roster on proballers:
                # #, Name, Pos, Height, Age, GP, MIN, PTS, REB, AST, ...

                try:
                    # Extract player ID
                    # link: .../basketball/player/ID/slug
                    pid = p["link"].split("/player/")[1].split("/")[0]

                    parsed_players.append(
                        {
                            "id": pid,
                            "name": p["name"],
                            "link": p["link"],
                            "team_url": team_url,
                            "season": year,
                            "raw_stats": p["stats"],
                        }
                    )
                except Exception:
                    pass

            return {
                "team_url": team_url,
                "year": year,
                "players": parsed_players,
            }

        except Exception as e:
            print(f"Error scraping {target_url}: {e}")
            return None
        finally:
            await page.close()

    async def scrape_team_schedule(self, team_url: str, year: int) -> List[Dict]:
        """
        Scrapes a team's schedule for a specific season.
        url format: .../team/ID/SLUG/schedule/YEAR
        """
        target_url = f"{team_url}/schedule/{year}"
        page = await self._get_page()

        try:
            print(f"Scraping Schedule {target_url}")
            await page.goto(target_url)
            await self.bypass_cloudflare(page)

            # Extract Schedule Table
            # Look for table with Date, Opponent, Score
            games = await page.eval_on_selector_all(
                "table tbody tr",
                """rows => rows.map(row => {
                const cells = Array.from(row.querySelectorAll('td'));
                if (cells.length < 4) return null;
                
                // Try to identify columns loosely
                // Date is usually first
                // Opponent has a link usually
                // Score is usually centered
                
                const date = cells[0].innerText.trim();
                const opponentLink = row.querySelector('a[href*="/team/"]');
                const opponent = opponentLink ? opponentLink.innerText.trim() : cells[2].innerText.trim();
                const result = cells[3] ? cells[3].innerText.trim() : "";
                
                return {
                    date: date,
                    opponent: opponent,
                    result: result
                };
            })""",
            )

            clean_games = []
            team_id = team_url.split("/team/")[1].split("/")[0]

            for g in games:
                if g and g["date"] and g["opponent"]:
                    g["team_id"] = team_id
                    g["season"] = year
                    clean_games.append(g)

            return clean_games

        except Exception as e:
            print(f"Error scraping schedule {target_url}: {e}")
            return []
        finally:
            await page.close()

    async def scrape_all_teams(self, teams: List[Dict], years: List[int]):
        all_players = []
        all_teams_data = []

        for i, team in enumerate(teams):
            team_href = team.get("href")
            if not team_href:
                continue

            # Normalize URL (remove trailing year)
            base_team_url = re.sub(r"/\d{4}$", "", team_href)
            team_id = base_team_url.split("/team/")[1].split("/")[0]

            team_record = {
                "id": team_id,
                "name": team.get("text"),
                "url": base_team_url,
                "seasons": years,
            }
            all_teams_data.append(team_record)

            print(f"Processing Team {i + 1}/{len(teams)}: {team.get('text')}")

            for year in years:
                data = await self.scrape_team_season(base_team_url, year)
                if data:
                    # Add team_id to players
                    for p in data["players"]:
                        p["team_id"] = team_id

                    all_players.extend(data["players"])

                    # Save incrementally
                    # Just passing the new batch
                    save_players(data["players"], filename="players.parquet")

                # Scrape Schedule (Only need to do this once per season really, but doing it here is fine)
                # We should probably only do it for the LATEST season to save time?
                # or if year == max(years)?
                # Let's do it for all requested years to be safe.
                schedule_data = await self.scrape_team_schedule(base_team_url, year)
                if schedule_data:
                    save_schedule(schedule_data, filename="schedule.parquet")

                # Politeness sleep
                await asyncio.sleep(2)

        # Save Teams
        # We need to flatten team season data? Or just save team info
        # Let's verify what save_teams expects. It expects list[dict].
        # We will iterate and create a row for each season or just team info?
        # So we just save team info for now.
        save_teams(all_teams_data, filename="teams.parquet")


async def run_scraper():
    print("Starting Scraper...")
    scraper = BasketballScraper()
    await scraper.start()

    # Load teams from json
    if not os.path.exists("all_teams.json"):
        print(
            "all_teams.json not found. Creating dummy list or running inspector first?"
        )
        # This assumes all_teams.json exists from previous steps.
        # If not, we might need to run inspect_page first.
        # For now, let's assume it exists.
        return

    with open("all_teams.json", "r") as f:
        all_teams = json.load(f)

    test_teams = []
    seen_urls = set()
    for t in all_teams:
        href = t.get("href")
        if (
            not href
            or "/schedule" in href
            or "/all-time-roster" in href
            or "/team-records" in href
        ):
            continue

        base_url = re.sub(r"/\d{4}$", "", href)

        if base_url not in seen_urls:
            seen_urls.add(base_url)
            test_teams.append(t)

    print(f"Found {len(test_teams)} unique teams.")

    # PROD RUN: last 5 seasons
    years = [2025, 2024, 2023, 2022, 2021]

    await scraper.scrape_all_teams(test_teams, years)
    await scraper.stop()

    # Save Metadata with Timestamp
    from datetime import datetime

    metadata = {"last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    os.makedirs("data_storage", exist_ok=True)
    with open("data_storage/metadata.json", "w") as f:
        json.dump(metadata, f)
    print("Scraping Complete. Metadata Saved.")


if __name__ == "__main__":
    asyncio.run(run_scraper())
