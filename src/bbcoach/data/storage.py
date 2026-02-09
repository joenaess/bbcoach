import pandas as pd
from pathlib import Path

DATA_DIR = Path("data_storage")


def ensure_data_dir():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)


def save_teams(teams_data: list[dict], filename="teams.parquet"):
    ensure_data_dir()
    df = pd.DataFrame(teams_data)
    # Append if exists, or overwrite? For now overwrite to keep it simple or we can use partition by season
    # Let's just save one big file for now
    path = DATA_DIR / filename
    if path.exists():
        existing_df = pd.read_parquet(path)
        # simplistic merge: concat and drop duplicates
        df = pd.concat([existing_df, df]).drop_duplicates(
            subset=["id", "season"], keep="last"
        )

    df.to_parquet(path)
    print(f"Saved {len(df)} teams to {path}")


def save_players(players_data: list[dict], filename="players.parquet"):
    ensure_data_dir()
    df = pd.DataFrame(players_data)
    path = DATA_DIR / filename
    if path.exists():
        existing_df = pd.read_parquet(path)
        df = pd.concat([existing_df, df]).drop_duplicates(
            subset=["id", "season", "team_id"], keep="last"
        )

    df.to_parquet(path)
    print(f"Saved {len(df)} players to {path}")


def load_teams() -> pd.DataFrame:
    path = DATA_DIR / "teams.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()


def load_players() -> pd.DataFrame:
    path = DATA_DIR / "players.parquet"
    if path.exists():
        df = pd.read_parquet(path)

        # Pre-process raw stats into columns if they exist
        if "raw_stats" in df.columns:
            # We need to extract stats. The logic is similar to app.py
            # Expected raw indices: 3:PPG, 4:RPG, 5:APG, 10:3P%

            def extract_stat(row, idx):
                try:
                    val = row[idx]
                    return float(val) if val != "-" else 0.0
                except Exception:
                    return 0.0

            # Vectorized approach or apply? Apply is safer for arrays
            # Let's use a simpler apply for now
            df["PPG"] = df["raw_stats"].apply(lambda x: extract_stat(x, 3))
            df["RPG"] = df["raw_stats"].apply(lambda x: extract_stat(x, 4))
            df["APG"] = df["raw_stats"].apply(lambda x: extract_stat(x, 5))
            df["SPG"] = (
                df["raw_stats"].apply(lambda x: extract_stat(x, 12))
                if len(df) > 0 and len(df.iloc[0]["raw_stats"]) > 12
                else 0.0
            )  # Index 12 is usually SPG? Need to verify mapping
            # Let's stick to known indices from app.py: 3,4,5.
            # 3P% is string with % often, or float? In scraper it seemed to be strings.
            # In app.py usage: raw[10] is 3P%.

            def extract_pct(row, idx):
                try:
                    val = str(row[idx]).replace("%", "")
                    return float(val) if val != "-" else 0.0
                except Exception:
                    return 0.0

            df["3P%"] = df["raw_stats"].apply(lambda x: extract_pct(x, 10))

            # Additional safer defaults
            if "SPG" not in df.columns:
                df["SPG"] = 0.0
            if "BPG" not in df.columns:
                df["BPG"] = 0.0

        return df


def save_schedule(schedule_data: list[dict], filename="schedule.parquet"):
    ensure_data_dir()
    if not schedule_data:
        return

    df = pd.DataFrame(schedule_data)
    path = DATA_DIR / filename

    if path.exists():
        existing_df = pd.read_parquet(path)
        # simplistic merge: concat and drop duplicates
        df = pd.concat([existing_df, df]).drop_duplicates(
            subset=["team_id", "date", "opponent"],
            keep="last",  # Drop exact duplicates but keep new
        )

    df.to_parquet(path)
    print(f"Saved {len(df)} schedule items to {path}")


def load_schedule() -> pd.DataFrame:
    path = DATA_DIR / "schedule.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()
