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

            # Pre-calculate GP to identify Totals
            df["GP"] = df["raw_stats"].apply(lambda x: extract_stat(x, 6))

            def smart_parse_ppg(row):
                """
                Detects if a row is 'Totals' (integers) or 'Averages' (floats).
                If Total and GP > 1, returns Total / GP.
                """
                try:
                    raw_pts = str(row[3])
                    if "%" in raw_pts:
                        return 0.0  # Bad row (Shooting stats)

                    pts = float(raw_pts) if raw_pts != "-" else 0.0

                    # Heuristic for Total:
                    # 1. GP > 1
                    # 2. Points are high (e.g. > 40) OR No decimal point in source string (integers)
                    # Checking for decimal point is tricky with floats, so rely on magnitude + integer-like string

                    is_integer_string = "." not in raw_pts and raw_pts != "-"
                    gp = float(row[6]) if row[6] != "-" else 0.0

                    if gp > 1 and (pts > 40 or (is_integer_string and pts > 20)):
                        # Likely a total
                        return round(pts / gp, 1)

                    # Fallback Sanity Check for 100.0 PPG (Mio Hjalmarsson case if unhandled)
                    if pts >= 99.0 and gp > 5:
                        # Unlikely to average 100 PPG?
                        # Could be a percentage slipped in?
                        # If raw string literally was "100", treat as Total -> 100/GP
                        return round(pts / gp, 1)

                    return pts
                except Exception:
                    return 0.0

            # General function for other stats (RPG, APG) following same logic if needed
            # For now, let's just fix PPG specifically or apply generic total-fix

            def smart_parse(row, idx):
                try:
                    raw_val = str(row[idx])
                    if "%" in raw_val:
                        return 0.0

                    val = float(raw_val) if raw_val != "-" else 0.0

                    # If we determined the row is a "Total Row" via PPG check, we should divide this too.
                    # But doing it row-by-row is expensive.
                    # Let's simple check: if value is integer-string and > 20 and GP > 1, divide?
                    # Except REB/AST are lower.

                    # Better approach: Check if PPG logic decided it was a total.
                    # Let's re-use the "is_total" concept.
                    # raw[3] is PTS.
                    raw_pts = str(row[3])
                    is_total_row = False
                    gp = float(row[6]) if row[6] != "-" else 0.0

                    if (
                        gp > 1
                        and "." not in raw_pts
                        and raw_pts != "-"
                        and float(raw_pts) > 0
                    ):
                        # Strong indicator of total row if PTS is integer
                        is_total_row = True

                    if is_total_row:
                        return round(val / gp, 1)

                    return val
                except Exception:
                    return 0.0

            # Apply Smart Parse
            # Note: We pass the whole 'raw_stats' list to apply, so x is the list.
            # But we also need GP.
            # It's cleaner to use apply on the DataFrame row, but 'raw_stats' is a column of lists.

            # Let's map it using the list directly
            df["PPG"] = df["raw_stats"].apply(
                lambda x: smart_parse_ppg(x) if len(x) > 6 else 0.0
            )

            # For others, we need a slightly localized smart_parse that knows about the list
            # We can just define a helper that takes the list
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

            df["RPG"] = df["raw_stats"].apply(lambda x: get_stat_smart(x, 4))
            # Sanity Cap for RPG: > 20 is likely error (League leader usually ~12)
            df["RPG"] = df.apply(
                lambda row: 0.0 if row["RPG"] > 20 else row["RPG"], axis=1
            )

            df["APG"] = df["raw_stats"].apply(lambda x: get_stat_smart(x, 5))
            # Sanity Cap for APG: > 15 is likely error
            df["APG"] = df.apply(
                lambda row: 0.0 if row["APG"] > 15 else row["APG"], axis=1
            )

            df["MIN"] = df["raw_stats"].apply(lambda x: get_stat_smart(x, 8))
            # Sanity Cap for MIN: > 48 (NBA max)
            df["MIN"] = df.apply(
                lambda row: 0.0 if row["MIN"] > 48 else row["MIN"], axis=1
            )

            # Consistency Check: PPG vs MIN
            # It's impossible to score 20 PPG in 2 MPG. (10 pts per minute is unheard of).
            # Threshold: If PPG > MIN * 1.5 AND MIN > 1 (to avoid div/0 or 1-min wonders), flag as suspicious.
            # Realistically, high scoring is ~0.5-0.8 pts/min. > 1.5 is very likely data error (e.g. Total Pts in Avg Min?).
            def check_ppg_min(row):
                ppg = row["PPG"]
                min_played = row["MIN"]
                if min_played > 1 and ppg > (
                    min_played * 2.5
                ):  # Very generous buffer (2.5 pts/min)
                    # Likely error. Set PPG to 0 or cap it?
                    # Let's cap it to MIN * 2 (still insane but better than 100)
                    return round(min_played * 2, 1)
                return ppg

            df["PPG"] = df.apply(check_ppg_min, axis=1)

            df["TO"] = df["raw_stats"].apply(lambda x: get_stat_smart(x, 18))

            # Percentages
            df["3P%"] = df["raw_stats"].apply(
                lambda x: extract_stat(x, 10, is_percent=True)
            )
            df["FG%"] = df["raw_stats"].apply(
                lambda x: extract_stat(x, 9, is_percent=True)
            )
            df["EFF"] = df["raw_stats"].apply(
                lambda x: extract_stat(x, -4)
            )  # Index -4 for EFF usually safe?

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
