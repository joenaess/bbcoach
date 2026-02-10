import pandas as pd
import os
import sys

# Ensure src is in path
sys.path.append(os.path.abspath("src"))


def verify_data():
    if not os.path.exists("data_storage/players.parquet"):
        print("Error: data_storage/players.parquet not found.")
        return

    df = pd.read_parquet("data_storage/players.parquet")
    print(f"Loaded players.parquet: {len(df)} rows.")

    # Filter for Ali Sow
    ali_sow = df[df["name"].str.contains("Ali Sow", case=False, na=False)]
    if not ali_sow.empty:
        print("\nFound Ali Sow:")
        print(ali_sow[["name", "team_name", "PPG", "GP", "season"]].to_string())

        # Check if PPG > 15 (Expected ~20.4)
        ppg = ali_sow.iloc[0]["PPG"]
        if ppg > 15:
            print(f"\nSUCCESS: Ali Sow PPG ({ppg}) looks correct for a top scorer.")
        else:
            print(f"\nFAILURE: Ali Sow PPG ({ppg}) is too low.")
    else:
        print("\nWARNING: Ali Sow not found.")

    # Filter for Lamonte Turner
    lamonte = df[df["name"].str.contains("Lamonte Turner", case=False, na=False)]
    if not lamonte.empty:
        print("\nFound Lamonte Turner:")
        print(lamonte[["name", "team_name", "PPG", "GP", "season"]].to_string())
    else:
        print("\nWARNING: Lamonte Turner not found.")

    # Top 5 Scorers
    print("\nTop 5 Scorers (SBL Herr 2025):")
    # Assuming season 2025 for now
    season_df = df[df["season"] == 2025]
    if not season_df.empty:
        top5 = season_df.sort_values(by="PPG", ascending=False).head(5)
        print(top5[["name", "team_name", "PPG", "GP"]].to_string())
    else:
        print("No players for season 2025 found.")


if __name__ == "__main__":
    verify_data()
