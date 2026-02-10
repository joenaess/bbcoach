import pandas as pd
from pathlib import Path

DATA_DIR = Path("data_storage")


def ensure_data_dir():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)


def save_teams(teams_data: list[dict], filename="teams.parquet"):
    ensure_data_dir()
    df = pd.DataFrame(teams_data)
    path = DATA_DIR / filename
    if path.exists():
        existing_df = pd.read_parquet(path)
        # simplistic merge: concat and drop duplicates
        # Include league in subset if available
        subset = ["id", "season"]
        if "league" in df.columns:
            subset.append("league")

        df = pd.concat([existing_df, df]).drop_duplicates(subset=subset, keep="last")

    df.to_parquet(path)
    print(f"Saved {len(df)} teams to {path}")


def save_players(players_data: list[dict], filename="players.parquet"):
    ensure_data_dir()
    df = pd.DataFrame(players_data)
    path = DATA_DIR / filename
    if path.exists():
        existing_df = pd.read_parquet(path)
        # Include league in subset if available
        subset = ["id", "season", "team_id"]
        if "league" in df.columns or "league" in existing_df.columns:
            subset.append("league")

        df = pd.concat([existing_df, df]).drop_duplicates(subset=subset, keep="last")

    df.to_parquet(path)
    print(f"Saved {len(df)} players to {path}")


def load_teams() -> pd.DataFrame:
    path = DATA_DIR / "teams.parquet"
    if path.exists():
        df = pd.read_parquet(path)
        if "league" not in df.columns:
            df["league"] = "Men"  # Default to Men for legacy data
        return df
    return pd.DataFrame()


def load_players() -> pd.DataFrame:
    path = DATA_DIR / "players.parquet"
    if path.exists():
        df = pd.read_parquet(path)

        # Default league if missing
        if "league" not in df.columns:
            df["league"] = "Men"

        # Pre-process raw stats into columns if they exist
        if "raw_stats" in df.columns:
            # We need to extract stats. The logic is similar to app.py
            # Expected raw indices: 3:PPG, 4:RPG, 5:APG, 10:3P%

            # Clean names first
            if "name" in df.columns:
                df["name"] = df["name"].astype(str).str.strip()

            def extract_stat(row, idx, is_percent=False):
                try:
                    val = str(row[idx])
                    if "%" in val:
                        if is_percent:
                            return float(val.replace("%", ""))
                        return 0.0  # Percent where number expected

                    if val == "-":
                        return 0.0

                    return float(val)
                except Exception:
                    return 0.0

            # Helper to safely get raw stats list
            def get_raw(x):
                # Handle lists and numpy arrays (from parquet)
                if x is not None and hasattr(x, "__len__") and not isinstance(x, str):
                    if len(x) > 0:
                        return x
                return None

            # Only apply logic where raw_stats is valid
            # If raw_stats is missing (new data), we trust the existing columns (PPG, etc.)

            # Helper wrapper to apply only if raw stats exist
            def smart_apply(row, func, col_name):
                raw = get_raw(row.get("raw_stats"))
                if raw is not None and len(raw) > 0:
                    return func(raw)
                # Return existing value if available, else 0.0
                return row.get(col_name, 0.0)

            # Pre-calculate GP to identify Totals
            # df["GP"] = df["raw_stats"].apply(lambda x: extract_stat(x, 6)) # OLD
            df["GP"] = df.apply(
                lambda r: smart_apply(r, lambda x: extract_stat(x, 6), "GP"), axis=1
            )

            def smart_parse_ppg(raw_list):
                """
                Detects if a row is 'Totals' (integers) or 'Averages' (floats).
                If Total and GP > 1, returns Total / GP.
                """
                try:
                    if len(raw_list) <= 6:
                        return 0.0

                    row = raw_list  # Alias for clarity in logic copy-paste

                    raw_pts = str(row[3])
                    if "%" in raw_pts:
                        return 0.0  # Bad row (Shooting stats)

                    pts = float(raw_pts) if raw_pts != "-" else 0.0

                    # Heuristic for Total:
                    is_integer_string = "." not in raw_pts and raw_pts != "-"
                    gp = float(row[6]) if row[6] != "-" else 0.0

                    if gp > 1 and (pts > 40 or (is_integer_string and pts > 20)):
                        # Likely a total
                        return round(pts / gp, 1)

                    # Fallback Sanity Check for 100.0 PPG
                    if pts >= 99.0 and gp > 5:
                        return round(pts / gp, 1)

                    return pts
                except Exception:
                    return 0.0

            # General function for other stats (RPG, APG)
            def get_stat_smart(raw_list, idx):
                if len(raw_list) <= idx:
                    return 0.0
                try:
                    raw_val = str(raw_list[idx])
                    if "%" in raw_val:
                        return 0.0
                    val = float(raw_val) if raw_val != "-" else 0.0

                    # Check if total row based on PTS (idx 3)
                    raw_pts = str(raw_list[3])
                    gp = float(raw_list[6]) if raw_list[6] != "-" else 0.0

                    if (
                        gp > 1
                        and "." not in raw_pts
                        and raw_pts != "-"
                        and float(raw_pts) > 20
                    ):
                        return round(val / gp, 1)

                    return val
                except Exception:
                    return 0.0

            # Apply Smart Parse
            df["PPG"] = df.apply(
                lambda r: smart_apply(r, lambda x: smart_parse_ppg(x), "PPG"), axis=1
            )

            # RPG
            df["RPG"] = df.apply(
                lambda r: smart_apply(r, lambda x: get_stat_smart(x, 4), "RPG"), axis=1
            )
            # Sanity Cap for RPG
            df["RPG"] = df.apply(
                lambda row: 0.0 if row["RPG"] > 20 else row["RPG"], axis=1
            )

            # APG
            df["APG"] = df.apply(
                lambda r: smart_apply(r, lambda x: get_stat_smart(x, 5), "APG"), axis=1
            )
            # Sanity Cap for APG
            df["APG"] = df.apply(
                lambda row: 0.0 if row["APG"] > 15 else row["APG"], axis=1
            )

            # MIN
            df["MIN"] = df.apply(
                lambda r: smart_apply(r, lambda x: get_stat_smart(x, 8), "MIN"), axis=1
            )
            # Sanity Cap for MIN
            df["MIN"] = df.apply(
                lambda row: 0.0 if row["MIN"] > 48 else row["MIN"], axis=1
            )

            # Consistency Check: PPG vs MIN
            def check_ppg_min(row):
                ppg = row.get("PPG", 0.0)
                min_played = row.get("MIN", 0.0)
                if min_played > 1 and ppg > (min_played * 2.5):
                    return round(min_played * 2, 1)
                return ppg

            df["PPG"] = df.apply(check_ppg_min, axis=1)

            df["TO"] = df.apply(
                lambda r: smart_apply(r, lambda x: get_stat_smart(x, 18), "TO"), axis=1
            )

            # Percentages
            df["3P%"] = df.apply(
                lambda r: smart_apply(r, lambda x: extract_stat(x, 10, True), "3P%"),
                axis=1,
            )
            df["FG%"] = df.apply(
                lambda r: smart_apply(r, lambda x: extract_stat(x, 9, True), "FG%"),
                axis=1,
            )
            df["EFF"] = df.apply(
                lambda r: smart_apply(r, lambda x: extract_stat(x, -4), "EFF"), axis=1
            )

            # Additional simple column checks
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
