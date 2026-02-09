import pandas as pd
import sys
import os

sys.path.append(os.path.abspath("src"))
from bbcoach.data.storage import load_players, load_teams

players = load_players()
teams = load_teams()

if not teams.empty:
    team_ids = set(teams["id"])
    player_team_ids = set(players["team_id"])

    missing = team_ids - player_team_ids
    print(f"Missing Team IDs: {missing}")

    missing_names = teams[teams["id"].isin(missing)]["name"].tolist()
    print(f"Missing Team Names: {missing_names}")

    # Check counts for present teams
    print("\nPlayer counts per team:")
    print(players["team_id"].value_counts())
