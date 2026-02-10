import requests
from bs4 import BeautifulSoup
import logging
import re
import time

logger = logging.getLogger(__name__)


class GeniusScraper:
    BASE_URL = "https://hosted.dcd.shared.geniussports.com/SBF/en/competition"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def fetch_page(self, url):
        try:
            # Increased timeout to 60s as server seems slow (curl took ~20s)
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def get_comp_url(self, comp_id, endpoint):
        return f"{self.BASE_URL}/{comp_id}/{endpoint}?"

    def parse_player_stats(self, html):
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            logger.warning("No tables found in player stats page")
            return {}

        players_data = {}

        for table_idx, table in enumerate(tables):
            headers = []
            thead = table.find("thead")
            if thead:
                headers = [th.get_text(strip=True) for th in thead.find_all("th")]

            tbody = table.find("tbody")
            if not tbody:
                continue

            for tr in tbody.find_all("tr"):
                cells = tr.find_all("td")
                if not cells:
                    continue

                # Extract Player info from first cell
                player_cell = cells[0]
                link_tag = player_cell.find("a")
                if not link_tag:
                    continue

                player_name = link_tag.get_text(strip=True)
                href = link_tag.get("href", "")

                # Extract ID from href: .../person/2504042?
                match = re.search(r"/person/(\d+)", href)
                player_id = match.group(1) if match else None

                if not player_id:
                    continue

                if player_id not in players_data:
                    players_data[player_id] = {
                        "name": player_name,
                        "link": href,
                        "genius_id": player_id,
                    }

                # Extract Stats
                # Skip first cell (Player Name)
                for i, cell in enumerate(cells[1:], start=1):
                    if i < len(headers):
                        header = headers[i]
                        val_str = cell.get_text(strip=True)
                        # Convert to float if possible
                        try:
                            val = float(val_str)
                        except ValueError:
                            # Handle percentage strings "64.7%"
                            if "%" in val_str:
                                try:
                                    val = float(val_str.replace("%", ""))
                                except ValueError:
                                    val = val_str
                            else:
                                val = val_str

                        players_data[player_id][header] = val

            # Normalize keys for app compatibility
            if player_id in players_data:
                p = players_data[player_id]
                if "G" in p and "GP" not in p:
                    p["GP"] = p["G"]
                if "MPG" in p and "MIN" not in p:
                    p["MIN"] = p["MPG"]
                if "STPG" in p and "SPG" not in p:
                    p["SPG"] = p["STPG"]
                if "BLKPG" in p and "BPG" not in p:
                    p["BPG"] = p["BLKPG"]
                if "TOPG" in p and "TO" not in p:
                    p["TO"] = p["TOPG"]

        return players_data

    def get_teams(self, comp_id):
        # The team list is often on the standings or teams page.
        # Or even the stats page has links to teams in the summary.
        # Let's use the 'teams' endpoint if it exists, or 'statistics/team'.
        # Based on dump, 'statistics/team' has links.
        url = self.get_comp_url(comp_id, "statistics/team")
        html = self.fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")

        teams = []
        # Look for links containing /team/
        # Filter to ensure they are team links for this competition
        seen_ids = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if f"/competition/{comp_id}/team/" in href:
                match = re.search(r"/team/(\d+)", href)
                if match:
                    team_id = match.group(1)
                    if team_id not in seen_ids:
                        seen_ids.add(team_id)
                        teams.append(
                            {"id": team_id, "name": a.get_text(strip=True), "url": href}
                        )
        return teams

    def get_team_roster(self, team_url):
        # Fetch team page
        # Note: team_url might be relative or absolute.
        if not team_url.startswith("http"):
            # Handle relative if needed, but our scrape produces absolute from href usually?
            # Wait, request headers usually return absolute?
            # Let's ensure it works.
            pass

        html = self.fetch_page(team_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Look for the Roster table
        # Div ID: BLOCK_TEAM_HOME_PLAYERS
        roster_div = soup.find("div", id="BLOCK_TEAM_HOME_PLAYERS")
        player_ids = []

        if roster_div:
            for a in roster_div.find_all("a", href=True):
                href = a["href"]
                if "/person/" in href:
                    match = re.search(r"/person/(\d+)", href)
                    if match:
                        player_ids.append(match.group(1))

        return list(set(player_ids))  # Unique IDs

    def scrape_competition(self, comp_id, season_year, league=None):
        logger.info(
            f"Scraping competition {comp_id} for season {season_year} ({league})"
        )

        # 1. Get Global Stats
        stats_url = self.get_comp_url(comp_id, "statistics/player")
        logger.info(f"Fetching Global Stats from {stats_url}")
        stats_html = self.fetch_page(stats_url)
        if not stats_html:
            logger.error(f"Failed to fetch global stats for competition {comp_id}")
            return [], []

        global_stats = self.parse_player_stats(stats_html)
        logger.info(f"Found {len(global_stats)} players with stats.")

        if not global_stats:
            return [], []

        # 2. Get Teams
        teams = self.get_teams(comp_id)
        logger.info(f"Found {len(teams)} teams.")

        final_players = []

        for team in teams:
            logger.info(f"Processing Team: {team['name']} ({team['id']})")
            roster_ids = self.get_team_roster(team["url"])
            logger.info(f"  Found {len(roster_ids)} players in roster.")

            for pid in roster_ids:
                if pid in global_stats:
                    p_data = global_stats[pid].copy()
                    p_data["team_id"] = team["id"]
                    p_data["team_name"] = team["name"]
                    p_data["season"] = season_year
                    p_data["id"] = pid  # Use Genius ID as main ID
                    if league:
                        p_data["league"] = league

                    # Normalize KEYS to match what app expects
                    # The app expects: PPG, APG, RPG, GP, MIN, 'raw_stats' (legacy)
                    # We should populate 'raw_stats' with dummy data to prevent crashes in storage.py
                    # if it still relies on it, or better, update storage.py to handle direct columns.
                    # Per plan, we will update storage.py.

                    # Ensure essential numeric fields exist
                    for key in [
                        "PPG",
                        "RPG",
                        "APG",
                        "GP",
                        "MIN",
                        "3P%",
                        "FG%",
                        "FT%",
                        "EFF",
                    ]:
                        if key not in p_data:
                            p_data[key] = 0.0

                    final_players.append(p_data)
                else:
                    # Player in roster but no stats? (Maybe 0 games?)
                    pass

            time.sleep(1)  # Politeness

        return final_players, teams

    def get_schedule(self, comp_id):
        url = self.get_comp_url(comp_id, "schedule")
        html = self.fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        schedule_data = []

        # Look for match wrappers
        matches = soup.find_all("div", class_="match-wrap")

        for match in matches:
            # 1. Date
            date_text = "Unknown"
            date_div = match.find("div", class_="match-time")
            if date_div:
                span = date_div.find("span")
                if span:
                    date_text = span.get_text(strip=True)

            # 2. Teams
            sched_teams = match.find("div", class_="sched-teams")
            if not sched_teams:
                continue

            home_div = sched_teams.find("div", class_="home-team")
            away_div = sched_teams.find(
                "div", class_="visiting-team"
            )  # "visiting-team" or "away-team"? usually "visiting-team" in genius

            if not away_div:
                away_div = sched_teams.find("div", class_="away-team")  # fallback

            if not home_div or not away_div:
                continue

            # Helper to get team info
            def get_team_info(div):
                name_div = div.find("div", class_="team-name")
                if not name_div:
                    return None, None
                a_tag = name_div.find("a")
                if not a_tag:
                    return None, None

                name = a_tag.get_text(strip=True)
                href = a_tag["href"]
                # Extract ID
                tid = None
                match_id = re.search(r"/team/(\d+)", href)
                if match_id:
                    tid = match_id.group(1)
                return name, tid

            home_name, home_id = get_team_info(home_div)
            away_name, away_id = get_team_info(away_div)

            if not home_id or not away_id:
                continue

            # 3. Score
            # Usually in div.team-score
            def get_score(div):
                score_div = div.find("div", class_="team-score")
                if score_div:
                    return score_div.get_text(strip=True)
                return "0"

            home_score = get_score(home_div)
            away_score = get_score(away_div)

            result_str = "Scheduled"
            # If scores are numeric, create result string
            if home_score.isdigit() and away_score.isdigit():
                # Logic: if date is in past (heuristic) or status is complete?
                # The match div has class STATUS_COMPLETE
                if "STATUS_COMPLETE" in match.get("class", []):
                    result_str = f"{home_score}-{away_score}"

            # Add records
            schedule_data.append(
                {
                    "date": date_text,
                    "team_id": home_id,
                    "team_name": home_name,
                    "opponent": away_name,
                    "opponent_id": away_id,
                    "result": result_str,
                    "home_away": "Home",
                }
            )

            schedule_data.append(
                {
                    "date": date_text,
                    "team_id": away_id,
                    "team_name": away_name,
                    "opponent": home_name,
                    "opponent_id": home_id,
                    "result": result_str,
                    "home_away": "Away",
                }
            )

        return schedule_data
