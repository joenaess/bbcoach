import pandas as pd
import sys
import os

sys.path.append(os.path.abspath("src"))
from bbcoach.data.storage import load_players, load_teams

players = load_players()
if not players.empty:
    print("Columns:", players.columns)
    print("First row raw_stats:", players.iloc[0]["raw_stats"])
    print("Sample:\n", players.head(1).to_string())
else:
    print("No players found.")

teams = load_teams()
if not teams.empty:
    print("Teams Columns:", teams.columns)
    print("Teams Sample:\n", teams.head(1).to_string())
