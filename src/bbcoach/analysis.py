def get_team_aggregates(players_df, team_id, season):
    """
    Aggregates player stats to estimate team strength for a given season.
    """
    team_players = players_df[
        (players_df["team_id"] == team_id) & (players_df["season"] == season)
    ]

    if team_players.empty:
        return None

    stats = {
        "total_ppg": 0.0,
        "total_rpg": 0.0,
        "total_apg": 0.0,
        "roster_size": len(team_players),
    }

    # Simple summation of averages (rough estimate of team potential)
    # Ideally we'd valid minutes or use team-level stats, but we only have player avgs.
    # We will sum the top 8 rotation players to avoid roster bloat skewing.

    # Safe parsing helper
    def parse_stat(val):
        try:
            return float(val)
        except Exception:
            return 0.0

    # Extract numeric stats from raw_stats array
    # Indices based on inspection:
    # 0: #, 1: Name, 2: Height, 3: Age, 4: GP, 5: MIN, 6: PTS
    # 14: REB, 15: AST, 16: STL, 17: BLK, 18: TO, 20: EFF
    parsed_players = []

    for _, row in team_players.iterrows():
        try:
            # Use direct columns if available (Genius Scraper)
            if "PPG" in row:
                p_stats = {
                    "name": row.get("name", "").strip(),
                    "ppg": float(row.get("PPG", 0.0)),
                    "rpg": float(row.get("RPG", 0.0)),
                    "apg": float(row.get("APG", 0.0)),
                    "gp": float(row.get("GP", 0.0)),
                    "min": float(row.get("MIN", 0.0)),
                    "fg_pct": float(row.get("FG%", 0.0)),
                    "3p_pct": float(row.get("3P%", 0.0)),
                    "to": float(row.get("TO", 0.0)),
                    "eff": float(row.get("EFF", 0.0)),
                }
                parsed_players.append(p_stats)
            else:
                # Legacy fallback via raw_stats
                # (Keep existing logic if needed or just simplify since we are moving to Genius)
                # But for safety, let's keep the fallback if raw_stats exists
                if "raw_stats" in row:
                    # ... (The old logic was quite fragile and commented out mostly)
                    # For now, let's assume if PPG is missing, we skip or use default 0
                    pass
        except Exception:
            continue

    # Sort by PPG to get rotation
    # FILTER: Exclude players with fewer than 5 games played to avoid 1-game wonders skewing analysis
    # Exception: If the season is very early (e.g. team played < 8 games total), we might need to lower this.
    # But for now, hard filter GP >= 5 is safer.

    # Check max GP in the roster to gauge season progress
    max_gp = max((p["gp"] for p in parsed_players), default=0)
    gp_threshold = 5 if max_gp >= 8 else 1  # Adaptive threshold

    rotation_candidates = [p for p in parsed_players if p["gp"] >= gp_threshold]

    # Fallback: if we filtered everyone out (unlikely), use everyone
    if not rotation_candidates:
        rotation_candidates = parsed_players

    rotation_candidates.sort(key=lambda x: x["ppg"], reverse=True)
    rotation = rotation_candidates[:8]  # Top 8 rotation from eligible players

    stats["total_ppg"] = sum(p["ppg"] for p in rotation)
    stats["total_rpg"] = sum(p["rpg"] for p in rotation)
    stats["total_apg"] = sum(p["apg"] for p in rotation)

    # Advanced Stats
    stats["total_3p_made"] = sum(p.get("3p_made", 0) for p in rotation)
    stats["avg_fg_pct"] = (
        sum(p.get("fg_pct", 0) for p in rotation) / len(rotation) if rotation else 0
    )
    stats["avg_3p_pct"] = (
        sum(p.get("3p_pct", 0) for p in rotation) / len(rotation) if rotation else 0
    )
    stats["total_to"] = sum(p.get("to", 0) for p in rotation)
    stats["total_min"] = sum(p.get("min", 0) for p in rotation)

    stats["top_scorer"] = rotation[0]["name"] if rotation else "N/A"
    # Find top playmaker
    sorted_apg = sorted(rotation, key=lambda x: x["apg"], reverse=True)
    stats["top_playmaker"] = sorted_apg[0]["name"] if sorted_apg else "N/A"
    # Find top rebounder
    sorted_rpg = sorted(rotation, key=lambda x: x["rpg"], reverse=True)
    stats["top_rebounder"] = sorted_rpg[0]["name"] if sorted_rpg else "N/A"

    # Store full rotation for matchup
    stats["rotation"] = parsed_players  # Return ALL parsed players, not just top 8
    stats["top_8"] = rotation

    return stats


def predict_matchup(players_df, team_a_id, team_b_id, season):
    """
    Compares two teams and returns a context string.
    """
    stats_a = get_team_aggregates(players_df, team_a_id, season)
    stats_b = get_team_aggregates(players_df, team_b_id, season)

    if not stats_a or not stats_b:
        return f"Insufficient data for matchup prediction in season {season}."

    diff_ppg = stats_a["total_ppg"] - stats_b["total_ppg"]

    # Matchup Logic
    def get_matchup(role, stat_key, label):
        # Safety check for empty rotation
        if not stats_a["rotation"] or not stats_b["rotation"]:
            return f"{label}: Insufficient player data."

        p_a = sorted(
            stats_a["rotation"], key=lambda x: x.get(stat_key, 0), reverse=True
        )[0]
        p_b = sorted(
            stats_b["rotation"], key=lambda x: x.get(stat_key, 0), reverse=True
        )[0]
        ex_a = p_a.get(stat_key, 0)
        ex_b = p_b.get(stat_key, 0)
        diff = ex_a - ex_b
        edge = "You" if diff > 0 else "Opponent"
        return (
            f"{label}: {p_a['name']} ({ex_a}) vs {p_b['name']} ({ex_b}) -> Edge: {edge}"
        )

    analysis = f"""
    DEEP MATCHUP ANALYSIS (Season {season})
    ======================================
    Team Comparison (Rotation of Top 8):
    Your Team: {stats_a["total_ppg"]:.1f} PPG | {stats_a["total_rpg"]:.1f} RPG | {stats_a["total_apg"]:.1f} APG | {stats_a["avg_3p_pct"]:.1f}% 3P
    Opponent : {stats_b["total_ppg"]:.1f} PPG | {stats_b["total_rpg"]:.1f} RPG | {stats_b["total_apg"]:.1f} APG | {stats_b["avg_3p_pct"]:.1f}% 3P

    Projected Outcome:
    Scoring Differential: {diff_ppg:+.1f} points ({"Advantage You" if diff_ppg > 0 else "Advantage Opponent"})

    Key Individual Matchups:
    1. {get_matchup("Scorer", "ppg", "Top Scorer")}
    2. {get_matchup("Playmaker", "apg", "Playmaker")}
    3. {get_matchup("Rebounder", "rpg", "Paint/Reb")}

    Tactical Notes:
    - 3-Point Threat: {"You shoot better from deep." if stats_a["avg_3p_pct"] > stats_b["avg_3p_pct"] else "Opponent has better shooters."}
    - Ball Security: {"Your team protects the ball better." if stats_a["total_to"] < stats_b["total_to"] else "Opponent calculates fewer turnovers."}
    """

    # 2. Projected Lineups (Top 5 by Minutes)
    # Sort full roster by minutes for starters
    full_a = sorted(stats_a["rotation"], key=lambda x: x.get("min", 0), reverse=True)
    full_b = sorted(stats_b["rotation"], key=lambda x: x.get("min", 0), reverse=True)

    starters_a = full_a[:5]
    bench_a = full_a[5:7]  # Next 2

    starters_b = full_b[:5]
    bench_b = full_b[5:7]

    def format_lineup(players):
        return ", ".join(
            [f"{p['name']} ({p['ppg']}p/{p['rpg']}r/{p['apg']}a)" for p in players]
        )

    analysis += f"""
    PROJECTED LINEUPS & ROTATION
    ============================
    Your Starters: {format_lineup(starters_a)}
    Your Key Bench: {format_lineup(bench_a)}
    
    Opponent Starters: {format_lineup(starters_b)}
    Opponent Key Bench: {format_lineup(bench_b)}
    """

    # 3. Full Troop Stats (Context Injection)
    def format_full_roster(team_rotation, label):
        roster_str = f"\nFULL {label} ROSTER STATS (Season {season}):\n"
        roster_str += "Name | PPG | RPG | APG | FG% | 3P% | TO\n"
        roster_str += "--- | --- | --- | --- | --- | --- | ---\n"
        for p in team_rotation:
            roster_str += f"{p['name']} | {p['ppg']} | {p['rpg']} | {p['apg']} | {p['fg_pct']}% | {p['3p_pct']}% | {p['to']}\n"
        return roster_str

    analysis += format_full_roster(stats_a["rotation"], "YOUR TEAM")
    analysis += format_full_roster(stats_b["rotation"], "OPPONENT")

    return analysis


def get_multi_season_aggregates(players_df, team_id, seasons=None):
    """
    Aggregates stats for a team across specified seasons.
    """
    if seasons is None:
        seasons = sorted(players_df["season"].unique().tolist(), reverse=True)

    aggregated_stats = {
        "total_ppg": 0,
        "total_rpg": 0,
        "total_apg": 0,
        "avg_3p_pct": 0,
        "total_to": 0,
        "count": 0,
    }

    valid_seasons = 0
    for season in seasons:
        stats = get_team_aggregates(players_df, team_id, season)
        if stats:
            aggregated_stats["total_ppg"] += stats["total_ppg"]
            aggregated_stats["total_rpg"] += stats["total_rpg"]
            aggregated_stats["total_apg"] += stats["total_apg"]
            aggregated_stats["avg_3p_pct"] += stats["avg_3p_pct"]
            aggregated_stats["total_to"] += stats["total_to"]
            valid_seasons += 1

    if valid_seasons > 0:
        return {
            k: v / valid_seasons for k, v in aggregated_stats.items() if k != "count"
        }
    return None


def predict_matchup_multi_season(players_df, team_a_id, team_b_id):
    """
    Compares two teams based on multi-season performance.
    """
    stats_a = get_multi_season_aggregates(players_df, team_a_id)
    stats_b = get_multi_season_aggregates(players_df, team_b_id)

    if not stats_a or not stats_b:
        return "Insufficient historical data for multi-season prediction."

    diff_ppg = stats_a["total_ppg"] - stats_b["total_ppg"]

    analysis = (
        f"MULTI-SEASON TREND ANALYSIS (2021-2025)\n"
        f"=======================================\n"
        f"Historical Team Potentials (Avg per Season):\n"
        f"Your Team: {stats_a['total_ppg']:.1f} PPG | {stats_a['total_rpg']:.1f} RPG | {stats_a['total_apg']:.1f} APG | {stats_a['avg_3p_pct']:.1f}% 3P\n"
        f"Opponent : {stats_b['total_ppg']:.1f} PPG | {stats_b['total_rpg']:.1f} RPG | {stats_b['total_apg']:.1f} APG | {stats_b['avg_3p_pct']:.1f}% 3P\n"
        f"\n"
        f"Historical Edge:\n"
        f"Scoring: {'You' if diff_ppg > 0 else 'Opponent'} ({abs(diff_ppg):.1f} PPG)\n"
        f"Modeling suggests consistent performance trends favor {'Your Team' if diff_ppg > 0 else 'Opponent'}.\n"
    )
    return analysis
