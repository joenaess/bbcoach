import pandas as pd
import os

pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)

if os.path.exists("data_storage/players.parquet"):
    df = pd.read_parquet("data_storage/players.parquet")

    target_name = "Timur"
    target = df[df["name"].str.contains(target_name, case=False, na=False)]

    if not target.empty:
        print(f"Found {len(target)} players matching '{target_name}'")
        for i, row in target.iterrows():
            print(f"\n--- {row['name']} ---")
            print(f"Team ID: {row['team_id']}")
            print(f"Season: {row['season']}")
            print(f"Parsed PPG: {row.get('PPG', 'N/A')}")
            print("Raw Stats:")
            print(row["raw_stats"])

            # Check index 3 specifically
            if len(row["raw_stats"]) > 3:
                print(f"Index 3 (PPG Source): {repr(row['raw_stats'][3])}")
    else:
        print(f"No player found matching '{target_name}'")
else:
    print("players.parquet not found.")
