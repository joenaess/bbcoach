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
        df = pd.concat([existing_df, df]).drop_duplicates(subset=["id", "season"])

    df.to_parquet(path)
    print(f"Saved {len(df)} teams to {path}")


def save_players(players_data: list[dict], filename="players.parquet"):
    ensure_data_dir()
    df = pd.DataFrame(players_data)
    path = DATA_DIR / filename
    if path.exists():
        existing_df = pd.read_parquet(path)
        df = pd.concat([existing_df, df]).drop_duplicates(
            subset=["id", "season", "team_id"]
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
        return pd.read_parquet(path)
    return pd.DataFrame()
