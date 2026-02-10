from bbcoach.data.storage import load_schedule
import pandas as pd

try:
    df = load_schedule()
    if df.empty:
        print("Schedule is empty.")
    else:
        print("Unique dates found:")
        print(df["date"].unique())
        print("\nFirst 5 rows:")
        print(df[["date"]].head())

        # Test parsing
        print("\nTesting pd.to_datetime:")
        try:
            pd.to_datetime(df["date"])
            print(
                "Default pd.to_datetime works (but prompts warning if format varying)."
            )
        except Exception as e:
            print(f"Error: {e}")

except Exception as e:
    print(f"Error loading schedule: {e}")
