import pandas as pd
import sys
import os

sys.path.append(os.path.abspath("src"))
from bbcoach.data.storage import load_players, load_teams

players = load_players()
teams = load_teams()

print("Players Columns:", players.columns)
print("Teams Columns:", teams.columns)

if not players.empty and not teams.empty:
    print(
        "\nSample Player Team ID:",
        players["team_id"].iloc[0],
        type(players["team_id"].iloc[0]),
    )
    print("Sample Team ID:", teams["id"].iloc[0], type(teams["id"].iloc[0]))

    # Check for mismatch in latest season
    latest_season = players["season"].max()
    print(f"\nLatest Season: {latest_season}")

    # Pick a team
    team_id = teams["id"].iloc[0]
    team_name = teams["name"].iloc[0]
    print(f"Checking Team: {team_name} (ID: {team_id})")

    team_players = players[
        (players["team_id"] == team_id) & (players["season"] == latest_season)
    ]
    print(f"Players found for {team_name} in {latest_season}: {len(team_players)}")

    # Check for "Total" or similar in names
    totals = players[players["name"].str.contains("Total", case=False, na=False)]
    if not totals.empty:
        print("\nFound 'Total' rows:")
        print(totals[["name", "season", "raw_stats"]].head())
    else:
        print("\nNo 'Total' rows found in players names.")

    # Check mapping
    distinct_team_ids = players["team_id"].unique()
    print(f"\nDistinct Team IDs in players: {len(distinct_team_ids)}")
    print(f"Distinct IDs in teams: {len(teams)}")
