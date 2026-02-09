import asyncio
from playwright.async_api import async_playwright


async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        # 1. Visit specific season team page to check links
        season_team_url = "https://www.proballers.com/basketball/team/3014/umea/2023"
        print(f"Navigating to {season_team_url}")
        await page.goto(season_team_url)
        print("Waiting for 10 seconds...")
        await page.wait_for_timeout(10000)

        # Get table headers
        headers = await page.eval_on_selector_all(
            "table thead th", "elements => elements.map(e => e.innerText)"
        )
        print(f"Headers: {headers}")
        # Check breadcrumbs or league links
        links = await page.eval_on_selector_all(
            "a", "elements => elements.map(e => ({href: e.href, text: e.innerText}))"
        )
        league_links = [
            link_item
            for link_item in links
            if "sweden-basketligan" in link_item["href"]
        ]

        import json

        with open("past_season_links.json", "w") as f:
            json.dump(league_links, f, indent=2)

        # 2. Get list of all teams
        teams_url = (
            "https://www.proballers.com/basketball/league/190/sweden-basketligan/teams"
        )
        print(f"Navigating to {teams_url}")
        await page.goto(teams_url)
        print("Waiting for 10 seconds...")
        await page.wait_for_timeout(10000)

        team_links = await page.eval_on_selector_all(
            "a", "elements => elements.map(e => ({href: e.href, text: e.innerText}))"
        )

        # Filter for team links (usually /basketball/team/...)
        all_teams = [
            link_item
            for link_item in team_links
            if "/basketball/team/" in link_item["href"]
        ]

        with open("all_teams.json", "w") as f:
            json.dump(all_teams, f, indent=2)
        print(f"Dumped {len(all_teams)} teams to all_teams.json")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect())
