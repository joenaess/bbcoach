import pandas as pd
import sys
import os

sys.path.append(os.path.abspath("src"))
from bbcoach.data.storage import load_players, load_teams
from bbcoach.analysis import get_team_aggregates, predict_matchup

players = load_players()
teams = load_teams()

print(f"Total Players: {len(players)}")
print(f"Total Teams: {len(teams)}")

if not teams.empty:
    # Try to reproduce the error with the user's likely selection
    # Assuming they might be selecting 'Unknown' or a team with ID mismatch

    latest_season = players["season"].max()
    print(f"Latest Season: {latest_season}")

    for _, team in teams.iterrows():
        print(f"\nChecking Team: {team['name']} (ID: {team['id']})")
        stats = get_team_aggregates(players, team["id"], latest_season)
        if stats:
            print(
                f"  Success: {stats['roster_size']} players, {stats['total_ppg']:.1f} PPG"
            )
        else:
            print(f"  FAILED: No data returned from get_team_aggregates")
            # Dig deeper
            team_players = players[
                (players["team_id"] == team["id"])
                & (players["season"] == latest_season)
            ]
            print(
                f"  Actual rows in DF for season {latest_season}: {len(team_players)}"
            )
            if not team_players.empty:
                print("  Why did it fail? Printing sample raw_stats:")
                print(team_players.iloc[0]["raw_stats"])

    # Test comparison
    if len(teams) >= 2:
        t1 = teams.iloc[0]
        t2 = teams.iloc[1]
        print(f"\nTesting Matchup: {t1['name']} vs {t2['name']}")
        analysis = predict_matchup(players, t1["id"], t2["id"], latest_season)
        print(f"Analysis Result:\n{analysis}")
