import pandas as pd
import sys
from pathlib import Path

# Add src to path just in case, though we just need pandas here mostly
sys.path.append("src")
from bbcoach.data.storage import load_players


def inspect_problematic_players():
    print("Loading players...")
    try:
        # load_players is in src/bbcoach/data/storage.py
        # It relies on data_storage existing relative to where it runs or absolute path.
        # Ensure imports work
        sys.path.append("/home/jonas/Projects/bbcoach/src")
        from bbcoach.data.storage import load_players

        df = load_players()
    except Exception as e:
        print(f"Error loading players: {e}")
        return

    if df.empty:
        print("No players found in storage.")
        return

    # Filter for Ali Sow and Lamonte Turner (handling potential spelling variations)
    target_names = ["Ali Sow", "Lamonte Turner", "Lamonte Tunrer"]

    print(f"Searching for: {target_names}")

    # Check if name column exists
    if "name" not in df.columns:
        print("Name column missing.")
        return

    mask = df["name"].isin(target_names)
    # Also check case-insensitive match
    mask_ci = df["name"].str.lower().isin([n.lower() for n in target_names])

    found = df[mask_ci]

    # Print columns
    cols = ["name", "team_id", "season", "PPG", "GP", "MIN", "raw_stats"]
    cols = [c for c in cols if c in df.columns]

    if found.empty:
        print("Players not found.")
        # Print top 5 scorers to see if they appear there under different names/stats
        if "PPG" in df.columns:
            print("\nTop 5 Scorer candidates (PPG > 20):")
            print(df[df["PPG"] > 20][cols].head(10).to_string())
        else:
            print("PPG column missing.")
    else:
        print(f"\nFound {len(found)} records:")
        print(found[cols].to_string())


if __name__ == "__main__":
    inspect_problematic_players()
