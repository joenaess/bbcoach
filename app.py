import streamlit as st
import pandas as pd
import sys
import os
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.append(os.path.abspath("src"))

from bbcoach.data.storage import load_players, load_teams, load_schedule  # noqa: E402
from bbcoach.ui.components import (  # noqa: E402
    render_player_card,
    render_comparison_chart,
)

# Lazy load AI model to avoid long startup time if not needed immediately
# from bbcoach.ai.coach import BasketballCoach
from bbcoach.analysis import predict_matchup  # noqa: E402
from bbcoach.rag.pipeline import RAGPipeline  # noqa: E402

st.set_page_config(
    page_title="Swedish Basketball League Coach", layout="wide", page_icon="🏀"
)


# --- THEME CSS ---
# --- THEME CSS ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


css_path = os.path.join(os.path.dirname(__file__), "assets/style.css")
if os.path.exists(css_path):
    load_css(css_path)
else:
    st.warning("CSS file not found. Using default styles.")


st.title("🏀 Swedish Basketball League AI Coach")

# --- SIDEBAR & SETTINGS ---
with st.sidebar:
    st.markdown("### ⚙️ AI Settings")

    # 1. API Keys & Provider
    with st.expander("Configure AI Models", expanded=False):
        # Check available keys
        has_gemini = bool(os.getenv("GEMINI_API_KEY"))
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

        provider_options = ["Local (Qwen 2.5)"]
        provider_options.append(f"Google Gemini {'✅' if has_gemini else '❌'}")
        provider_options.append(f"OpenAI (GPT-4o) {'✅' if has_openai else '❌'}")
        provider_options.append(
            f"Anthropic (Claude 3.5) {'✅' if has_anthropic else '❌'}"
        )

        # Determine default index based on what's available
        default_idx = 0
        if has_gemini:
            default_idx = 1
        elif has_openai:
            default_idx = 2
        elif has_anthropic:
            default_idx = 3

        selected_provider_label = st.selectbox(
            "Select AI Provider", provider_options, index=default_idx
        )

        # Map label back to internal code
        provider = "local"
        if "Gemini" in selected_provider_label:
            provider = "gemini"
        elif "OpenAI" in selected_provider_label:
            provider = "openai"
        elif "Anthropic" in selected_provider_label:
            provider = "anthropic"

        api_key_input = ""
        st.session_state["ai_provider"] = provider  # Default

        if provider == "gemini":
            api_key_input = st.text_input(
                "Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password"
            )
            st.session_state["ai_key"] = api_key_input
        elif provider == "openai":
            api_key_input = st.text_input(
                "OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password"
            )
            st.session_state["ai_key"] = api_key_input
        elif provider == "anthropic":
            api_key_input = st.text_input(
                "Anthropic API Key",
                value=os.getenv("ANTHROPIC_API_KEY", ""),
                type="password",
            )
            st.session_state["ai_key"] = api_key_input
        else:
            st.session_state["ai_key"] = None

        # Model Selection Logic
        model_options = []
        default_idx = 0

        if provider == "gemini":
            model_options = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
        elif provider == "openai":
            model_options = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        elif provider == "anthropic":
            model_options = [
                "claude-3-5-sonnet-latest",
                "claude-3-opus-latest",
                "claude-3-haiku-20240307",
            ]

        selected_model = None
        if model_options:
            selected_model = st.selectbox(
                "Select Model", model_options, index=default_idx
            )
            st.session_state["ai_model"] = selected_model
        else:
            st.session_state["ai_model"] = None

        if st.button("Apply AI Settings"):
            # Save to .env
            from dotenv import set_key, find_dotenv

            env_file = find_dotenv()
            if not env_file:
                env_file = ".env"  # Create if missing
                with open(env_file, "w") as f:
                    pass

            if "Gemini" in provider and api_key_input:
                set_key(env_file, "GEMINI_API_KEY", api_key_input)
                os.environ["GEMINI_API_KEY"] = api_key_input
            elif "OpenAI" in provider and api_key_input:
                set_key(env_file, "OPENAI_API_KEY", api_key_input)
                os.environ["OPENAI_API_KEY"] = api_key_input
            elif "Anthropic" in provider and api_key_input:
                set_key(env_file, "ANTHROPIC_API_KEY", api_key_input)
                os.environ["ANTHROPIC_API_KEY"] = api_key_input

            # Force reload of coach
            if "coach" in st.session_state:
                del st.session_state["coach"]
            st.success(f"Settings Applied & Saved to {env_file}!")

    st.markdown("---")

    # 2. Data Refresh with Progress
    st.markdown("### 🔄 Data Sync")

    # Check Last Update
    last_update = "Never"
    is_fresh = False

    if os.path.exists("data_storage/metadata.json"):
        try:
            with open("data_storage/metadata.json", "r") as f:
                meta = json.load(f)
                last_update = meta.get("last_updated", "Unknown")

                # Check freshness (e.g., < 24 hours)
                try:
                    last_dt = datetime.datetime.strptime(
                        last_update, "%Y-%m-%d %H:%M:%S"
                    )
                    if datetime.datetime.now() - last_dt < datetime.timedelta(weeks=2):
                        is_fresh = True
                except Exception:
                    pass
        except Exception:
            pass

    # 3. Robust Data Check
    data_exists = os.path.exists("data_storage/players.parquet")

    if data_exists and last_update == "Never":
        try:
            # Metadata missing, but data exists.
            # Try to get file timestamp, otherwise default to NOW to fix user issue.
            if os.path.exists("data_storage/players.parquet"):
                ts = os.path.getmtime("data_storage/players.parquet")
                last_dt = datetime.datetime.fromtimestamp(ts)
            else:
                last_dt = datetime.datetime.now()

            last_update = last_dt.strftime("%Y-%m-%d %H:%M:%S")

            # Check if fresh (2 weeks)
            if datetime.datetime.now() - last_dt < datetime.timedelta(weeks=2):
                is_fresh = True

            # Create the missing metadata file
            with open("data_storage/metadata.json", "w") as f:
                json.dump({"last_updated": last_update}, f)
        except Exception:
            # If all else fails but data exists, just say it's updated now
            last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            is_fresh = True

    if is_fresh:
        st.success(f"✅ Stats Up-to-Date\n({last_update})")
    elif data_exists:
        st.warning(f"⚠️ Stats Outdated\nLast check: {last_update}")
    else:
        st.warning("⚠️ No Data Found\nPlease fetch stats to begin.")

    if st.button("Fetch New Stats"):
        import subprocess
        import re

        progress_bar = st.progress(0, text="Starting Scraper...")
        status_text = st.empty()

        try:
            # Run the scraper as a subprocess and read stdout
            # Run the scraper with unbuffered output to ensure progress updates
            # Also set PYTHONPATH to include src
            import os

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"

            process = subprocess.Popen(
                ["uv", "run", "python", "-u", "src/bbcoach/data/scrapers.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env,
            )

            # Read stdout line by line
            total_teams = 15  # Estimate or Parse
            current_team_idx = 0

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                if line:
                    line = line.strip()
                    # Look for "Processing Team X/Y"
                    # Pattern example: "Processing Team 1/14: Boras Basket"
                    match = re.search(r"Processing Team (\d+)/(\d+): (.+)", line)
                    if match:
                        current = int(match.group(1))
                        total = int(match.group(2))
                        team_name = match.group(3)

                        progress = min(current / total, 1.0)
                        progress_bar.progress(
                            progress, text=f"Scraping: {team_name} ({current}/{total})"
                        )
                    else:
                        # Other logs
                        status_text.caption(f"Log: {line}")

            if process.returncode == 0:
                progress_bar.progress(1.0, text="Complete!")
                st.success("Stats successfully updated!")
                st.rerun()
            else:
                st.error("Error fetching stats. Check logs.")

        except Exception as e:
            st.error(f"Execution Error: {e}")

# Context Helpers
CONTEXT_FILE = "tmp_prompt.txt"


def save_context(text):
    with open(CONTEXT_FILE, "a") as f:
        f.write(text + "\n")


def load_context():
    if os.path.exists(CONTEXT_FILE):
        with open(CONTEXT_FILE, "r") as f:
            return f.read()
    return ""


def clear_context():
    if os.path.exists(CONTEXT_FILE):
        os.remove(CONTEXT_FILE)


# Sidebar
st.sidebar.title("Settings")

# --- CONTEXT RESET ---
with st.sidebar:
    st.markdown("---")
    if st.button("Reset Context"):
        st.session_state["prediction_context"] = ""
        save_context("")  # Clear file
        if "messages" in st.session_state:
            st.session_state["messages"] = []
        st.success("Context Cleared! (Coach persona remains)")


@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_data():
    players = load_players()
    teams = load_teams()
    return players, teams


if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

players_df, teams_df = get_data()

# --- LEAGUE FILTER ---
# Ensure "league" column exists (backwards compatibility handled in storage.py but good to be safe)
if "league" not in players_df.columns and not players_df.empty:
    players_df["league"] = "Men"
if "league" not in teams_df.columns and not teams_df.empty:
    teams_df["league"] = "Men"

# Sidebar Selection
st.sidebar.markdown("### 🏆 League")
available_leagues = ["Men", "Women"]
# Ideally, we could check what's in the data, but we want to support both.
selected_league = st.sidebar.radio(
    "Select League", available_leagues, index=0, horizontal=True
)

# Filter Dataframes
if not players_df.empty:
    players_df = players_df[players_df["league"] == selected_league]

if not teams_df.empty:
    teams_df = teams_df[teams_df["league"] == selected_league]

st.sidebar.markdown(f"**Total Players:** {len(players_df)}")
st.sidebar.markdown(f"**Total Teams:** {len(teams_df)}")

# Coach Team Selection
if not teams_df.empty:
    team_names = teams_df["name"].unique()

    # Default to Högsbo
    default_index = 0
    hogsbo_matches = [i for i, name in enumerate(team_names) if "Högsbo" in name]
    if hogsbo_matches:
        default_index = hogsbo_matches[0]

    selected_team_name = st.sidebar.selectbox(
        "Select Your Team", team_names, index=default_index
    )
    st.session_state["coach_team"] = selected_team_name
else:
    st.session_state["coach_team"] = None

# --- TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "League Stats",
        "Player Comparison",
        "Game Predictor",
        "Coach's Corner",
        "Schedule",
        "Knowledge Base",
    ]
)

# --- TAB 5: Schedule ---
with tab5:
    st.title("📅 Game Schedule")

    schedule_df = load_schedule()

    if schedule_df.empty:
        st.info("No schedule data found. Please fetch stats to load the schedule.")
    else:
        # Filter by Team
        teams_list = sorted(schedule_df["team_id"].unique())

        # Try to default to coach's team if set
        default_team_index = 0
        if "coach" in st.session_state and st.session_state["coach"].team_name:
            # This might be tricky as team_name is name not ID, but let's try to match or just default to 0
            pass

        selected_team_id = st.selectbox(
            "Select Team", teams_list, format_func=lambda x: f"Team {x}"
        )
        # Ideally we want team names here. We can merge with teams_df if available.

        # IMPROVEMENT: Load teams to get names
        teams_df = load_teams()
        if not teams_df.empty:
            # Create a mapping
            id_to_name = dict(zip(teams_df["id"], teams_df["name"]))
            team_name = id_to_name.get(selected_team_id, selected_team_id)
            st.subheader(f"Schedule for {team_name}")
        else:
            st.subheader(f"Schedule for Team {selected_team_id}")

        team_schedule = schedule_df[schedule_df["team_id"] == selected_team_id].copy()

        # Sort by date
        # Date format might be string, let's try to convert for sorting
        try:
            team_schedule["date_dt"] = pd.to_datetime(
                team_schedule["date"], errors="coerce", format="mixed"
            )
            team_schedule = team_schedule.sort_values("date_dt")
        except Exception:
            pass

        # Display
        st.dataframe(
            team_schedule[["date", "opponent", "result"]],
            hide_index=True,
            width="stretch",
            column_config={
                "date": "Date",
                "opponent": "Opponent",
                "result": "Result/Time",
            },
        )

# ------------------------------------------------------------------
# TAB 1: League Stats
# ------------------------------------------------------------------
with tab1:
    if not players_df.empty:
        # Move season selection UP so selected_season is available
        selected_season = st.selectbox(
            "Select Season", sorted(players_df["season"].unique(), reverse=True)
        )

        st.header(f"League Stats ({selected_season})")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Top Scorers")
            # Filter by season
            season_players = players_df[players_df["season"] == selected_season]
            if not season_players.empty:
                top_scorers = season_players.sort_values(
                    by="PPG", ascending=False
                ).head(5)
                # Create mapping for display
                team_id_map = dict(zip(teams_df["id"], teams_df["name"]))

                for rank, (_, row) in enumerate(top_scorers.iterrows(), 1):
                    player_data = row.to_dict()
                    player_data["team"] = team_id_map.get(
                        str(row["team_id"]), str(row["team_id"])
                    )
                    render_player_card(player_data, rank=rank)

        with c2:
            st.subheader("Top Rebounders")
            if not season_players.empty:
                top_reb = season_players.sort_values(by="RPG", ascending=False).head(5)

                team_id_map = dict(zip(teams_df["id"], teams_df["name"]))

                for rank, (_, row) in enumerate(top_reb.iterrows(), 1):
                    player_data = row.to_dict()
                    player_data["team"] = team_id_map.get(
                        str(row["team_id"]), str(row["team_id"])
                    )
                    render_player_card(player_data, rank=rank)

        # --- FULL STATS TABLE ---
        st.subheader("Advanced League Data")

        # Create a mapping for Team ID to Name
        team_id_map = dict(zip(teams_df["id"], teams_df["name"]))

        # Parse stats for display
        display_data = []
        for _, row in season_players.iterrows():
            try:
                # Use direct columns if available (new scraper), else fallback to raw_stats (legacy)
                if "PPG" in row:
                    display_data.append(
                        {
                            "Name": row["name"],
                            "Team": team_id_map.get(
                                str(row["team_id"]), row["team_id"]
                            ),
                            "PPG": row.get("PPG", 0),
                            "RPG": row.get("RPG", 0),
                            "APG": row.get("APG", 0),
                            "GP": row.get("GP", 0),
                            "MIN": row.get("MIN", 0),
                            "FG%": row.get("FG%", 0),
                            "3P%": row.get("3P%", 0),
                            "FT%": row.get("FT%", 0),
                            "EFF": row.get("EFF", 0),
                        }
                    )
                else:
                    # Legacy fallback
                    raw = row["raw_stats"]
                    display_data.append(
                        {
                            "Name": row["name"],
                            "Team": team_id_map.get(
                                str(row["team_id"]), row["team_id"]
                            ),
                            "PPG": raw[3],
                            "RPG": raw[4],
                            "APG": raw[5],
                            "GP": raw[6],
                            "MIN": raw[8],
                            "FG%": raw[9],
                            "3P%": raw[10],
                            "FT%": raw[11],
                            "EFF": raw[-4] if len(raw) > 20 else "N/A",
                        }
                    )
            except Exception:
                continue

        if display_data:
            st.dataframe(pd.DataFrame(display_data))

        st.divider()

        # Team Roster Lookup
        st.subheader("Team Roster Lookup")
        unique_team_ids = season_players["team_id"].unique()

        # Default to Coach Team if available
        default_team_index = 0
        if st.session_state.get("coach_team"):
            team_record = teams_df[teams_df["name"] == st.session_state["coach_team"]]
            if not team_record.empty:
                coach_team_id = team_record.iloc[0]["id"]
                if coach_team_id in unique_team_ids:
                    default_team_index = list(unique_team_ids).index(coach_team_id)

        selected_team_id = st.selectbox(
            "Select Team ID", unique_team_ids, index=default_team_index
        )
        team_roster = season_players[season_players["team_id"] == selected_team_id]
        st.dataframe(team_roster)

    else:
        st.warning("No data found. Please run the scraper first.")

    # ------------------------------------------------------------------
    # TAB 2: Player Comparison (Analytics)
    # ------------------------------------------------------------------
with tab2:
    st.header("🔬 Player Comparison")

    if not players_df.empty:
        from bbcoach.data.analytics import create_radar_chart

        # Select Players
        all_player_names = players_df["name"].sort_values().unique().tolist()

        col1, col2 = st.columns(2)
        with col1:
            p1_name = st.selectbox("Select Player 1", all_player_names, index=0)
        with col2:
            # Try to pick a different default
            default_idx_2 = 1 if len(all_player_names) > 1 else 0
            p2_name = st.selectbox(
                "Select Player 2", all_player_names, index=default_idx_2
            )

        if p1_name and p2_name:
            # Get stats
            p1_stats = players_df[players_df["name"] == p1_name].iloc[0]
            p2_stats = players_df[players_df["name"] == p2_name].iloc[0]

            # Prepare data for chart
            comparison_df = players_df[
                players_df["name"].isin([p1_name, p2_name])
            ].copy()

            # Render Chart
            fig = create_radar_chart(comparison_df)
            if fig:
                # use_container_width=True is deprecated
                st.plotly_chart(fig)
            else:
                st.warning("Not enough data to generate chart.")

            # Data Table
            st.subheader("Head-to-Head Stats")

            # Map team name for display
            team_id_map = dict(zip(teams_df["id"], teams_df["name"]))
            comparison_df["team"] = (
                comparison_df["team_id"]
                .astype(str)
                .map(team_id_map)
                .fillna(comparison_df["team_id"])
            )

            st.dataframe(
                comparison_df[["name", "team", "PPG", "RPG", "APG", "3P%"]],
                hide_index=True,
            )

# ------------------------------------------------------------------
# TAB 3: Game Predictor
# ------------------------------------------------------------------
with tab3:
    st.header("Matchup & Scouting")

    # Sub-tabs for Predictor vs Scouting Report
    subtab_pred, subtab_scout = st.tabs(["🔮 Game Predictor", "📋 Scouting Report"])

    with subtab_pred:
        # Team Selection for Opponent
        opponent_name = st.selectbox(
            "Select Opponent", teams_df["name"].unique(), key="pred_opp"
        )
        opponent_record = teams_df[teams_df["name"] == opponent_name]

        season = st.selectbox(
            "Season",
            sorted(players_df["season"].unique(), reverse=True),
            key="pred_season",
        )

        with st.expander("⚙️ Advanced Settings"):
            use_multi_season = st.checkbox(
                "Include Multi-Season Trend Analysis?", value=False
            )

        if st.button("Analyze Matchup", type="primary"):
            if not opponent_record.empty and st.session_state.get("coach_team"):
                opp_id = opponent_record.iloc[0]["id"]
                st.divider()

                # Get Coach Team ID
                coach_record = teams_df[
                    teams_df["name"] == st.session_state["coach_team"]
                ]
                if not coach_record.empty:
                    coach_id = coach_record.iloc[0]["id"]

                    # --- VISUALIZATION ---
                    # Calculate aggregate stats for chart
                    my_team_stats = players_df[
                        (players_df["team_id"] == coach_id)
                        & (players_df["season"] == season)
                    ]
                    opp_team_stats = players_df[
                        (players_df["team_id"] == opp_id)
                        & (players_df["season"] == season)
                    ]

                    if not my_team_stats.empty and not opp_team_stats.empty:
                        # Helper to get team avg
                        def get_avg(df, col):
                            return round(df[col].mean(), 1)

                        chart_data = [
                            {
                                "Metric": "PPG",
                                "Value": get_avg(my_team_stats, "PPG"),
                                "Entity": st.session_state["coach_team"],
                            },
                            {
                                "Metric": "PPG",
                                "Value": get_avg(opp_team_stats, "PPG"),
                                "Entity": opponent_name,
                            },
                            {
                                "Metric": "RPG",
                                "Value": get_avg(my_team_stats, "RPG"),
                                "Entity": st.session_state["coach_team"],
                            },
                            {
                                "Metric": "RPG",
                                "Value": get_avg(opp_team_stats, "RPG"),
                                "Entity": opponent_name,
                            },
                            {
                                "Metric": "APG",
                                "Value": get_avg(my_team_stats, "APG"),
                                "Entity": st.session_state["coach_team"],
                            },
                            {
                                "Metric": "APG",
                                "Value": get_avg(opp_team_stats, "APG"),
                                "Entity": opponent_name,
                            },
                        ]
                        render_comparison_chart(
                            pd.DataFrame(chart_data),
                            st.session_state["coach_team"],
                            opponent_name,
                            key="matchup_chart",
                        )

                    # --- AI ANALYSIS ---
                    with st.spinner("Asking Assistant Coach..."):
                        # 1. Single Season Analysis
                        analysis = predict_matchup(players_df, coach_id, opp_id, season)
                        st.markdown("### 🧠 Coach's Analysis")
                        st.markdown(analysis)

                        # 2. Multi-Season Analysis (Optional)
                        if use_multi_season:
                            from bbcoach.analysis import predict_matchup_multi_season

                            trend_analysis = predict_matchup_multi_season(
                                players_df, coach_id, opp_id
                            )
                            st.divider()
                            st.markdown("### 📈 Historical Trends")
                            st.markdown(trend_analysis)
                            analysis += "\n\n" + trend_analysis

                        # Button to save
                        col_save, col_dl = st.columns(2)
                        with col_save:
                            if st.button("Save to Context"):
                                st.session_state["prediction_context"] = analysis
                                save_context(analysis)
                                st.success("Analysis saved to AI Context!")

                        with col_dl:
                            game_plan_text = f"# 🏀 Game Plan: {st.session_state['coach_team']} vs {opponent_name}\n\n"
                            game_plan_text += f"**Season:** {season}\n"
                            game_plan_text += f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n"
                            game_plan_text += "---\n\n"
                            game_plan_text += analysis

                            st.download_button(
                                label="Download Game Plan 📥",
                                data=game_plan_text,
                                file_name=f"game_plan_{opponent_name}_{pd.Timestamp.now().strftime('%Y%m%d')}.md",
                                mime="text/markdown",
                            )
                else:
                    st.error("Please select your Coach Team in the sidebar first.")

    with subtab_scout:
        st.markdown("### 📝 AI Scouting Report Generator")
        scout_opp_name = st.selectbox(
            "Target Opponent", teams_df["name"].unique(), key="scout_opp"
        )
        scout_season = st.selectbox(
            "Season Data",
            sorted(players_df["season"].unique(), reverse=True),
            key="scout_season",
        )

        if st.button("Generate Scouting Report", type="primary"):
            # Check if coach is loaded
            if "coach" not in st.session_state:
                # Logic to load coach if missing (duplicated from Chat, could be refactored)
                st.warning(
                    "Please initialize AI settings in the sidebar first (or just ask a question in Coach's Corner to wake him up)."
                )
            else:
                with st.spinner(f"Scouting {scout_opp_name} ({scout_season})..."):
                    # Gather Stats
                    opp_record = teams_df[teams_df["name"] == scout_opp_name]
                    if not opp_record.empty:
                        opp_id = opp_record.iloc[0]["id"]
                        opp_players = players_df[
                            (players_df["team_id"] == opp_id)
                            & (players_df["season"] == scout_season)
                        ]

                        if not opp_players.empty:
                            try:
                                # Prepare stats summary string
                                stats_str = ""
                                # Sort by PPG to get key players
                                top_players = opp_players.sort_values(
                                    by="PPG", ascending=False
                                ).head(8)

                                for _, p in top_players.iterrows():
                                    stats_str += f"- {p['name']}: {p['PPG']} PPG, {p['RPG']} RPG, {p['APG']} APG, {p['3P%']}% 3P\n"

                                report = (
                                    st.session_state.coach.generate_scouting_report(
                                        scout_opp_name, stats_str
                                    )
                                )
                                st.markdown(report)

                                # Save option
                                st.download_button(
                                    label="Download Report",
                                    data=report,
                                    file_name=f"scouting_report_{scout_opp_name}.md",
                                    mime="text/markdown",
                                )
                            except Exception as e:
                                st.error(f"Error generating report: {e}")
                        else:
                            st.warning("No player data found for this team/season.")

# ------------------------------------------------------------------
# TAB 4: Coach's Corner
# ------------------------------------------------------------------
with tab4:
    st.header("Coach's Corner 🧠")
    coach_team = st.session_state.get("coach_team", "a team")
    st.write(f"As the coach of **{coach_team}**, ask about your players or opponents.")

    # Show current context
    current_context = load_context()
    with st.expander("Current Context (tmp_prompt.txt)"):
        st.code(current_context)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask Coach..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")

            # Load coach only when needed
            if "coach" not in st.session_state:
                with st.spinner("Loading AI Coach..."):
                    import importlib
                    import bbcoach.ai.coach

                    importlib.reload(bbcoach.ai.coach)
                    from bbcoach.ai.coach import BasketballCoach

                    # Get config from session
                    p_type = st.session_state.get("ai_provider", "local")
                    p_key = st.session_state.get("ai_key", None)
                    p_model = st.session_state.get("ai_model", None)

                    st.session_state.coach = BasketballCoach(
                        provider=p_type, api_key=p_key, model_name=p_model
                    )

            # Prepare context
            coach_team = st.session_state.get("coach_team", "Unknown Team")

            # --- SYSTEM PROMPT ---
            system_prompt = (
                f"You are the deeply analytical **Assistant Coach** of {coach_team} in the Swedish Basketball League.\\n"
                f"Your job is to support the Head Coach with data-driven tactical advice, practice recommendations, and playbook adjustments.\\n\\n"
                f"**YOUR CAPABILITIES:**\\n"
                f"1. **Game Tactics**: Suggest offensive/defensive schemes based on matchups (e.g., 'Switch all screens,' 'Zone defense against their poor shooters').\\n"
                f"2. **Practice Focus**: Recommend specific drills based on recent performance or upcoming opponent weaknesses (e.g., 'Close-out drills' if opponent shoots 3s well).\\n"
                f"3. **Playbook Setups**: Propose specific plays (ATO, P&R coverage) to exploit gaps in the opponent's defense.\\n\\n"
                f"**GUIDELINES:**\\n"
                f"- Use the **FULL ROSTER STATS** provided to find hidden gems or specific mismatches (not just starters).\\n"
                f"- Be specific. Don't say 'play better defense,' say 'We need to ICE the pick-and-roll against {opponent_name if 'opponent_name' in locals() else 'them'} because their guards are poor shooters.'\\n"
                f"- Refer to 'Our Starters' and 'Their Starters' explicitly when analyzing rotations."
            )

            context = f"{system_prompt}\n\n=== CONTEXT DATA ===\n"

            # 1. Automatic Team & Opponent Context (if analysis exists or manually selected)
            # If the user has run an analysis, it's in the file context.
            # But let's also inject the roster summary of the CURRENT coach team automatically.

            if not players_df.empty and st.session_state.get("coach_team"):
                team_record = teams_df[
                    teams_df["name"] == st.session_state["coach_team"]
                ]
                if not team_record.empty:
                    tid = team_record.iloc[0]["id"]
                    latest_season = players_df["season"].max()
                    # Get top 8 rotation for context to save tokens
                    team_players = players_df[
                        (players_df["team_id"] == tid)
                        & (players_df["season"] == latest_season)
                    ]

                    if not team_players.empty:
                        # Parse stats for cleaner context
                        roster_summary = []
                        for _, p in team_players.iterrows():
                            try:
                                raw = p["raw_stats"]
                                roster_summary.append(
                                    f"{p['name']}: {raw[3]} PPG, {raw[4]} RPG, {raw[5]} APG, {raw[10]} 3P%"
                                )
                            except Exception:
                                continue

                        # Top 10 by PPG (approx)
                        context += (
                            f"\nYOUR ROSTER ({latest_season}):\n"
                            + "\n".join(roster_summary[:10])
                            + "\n"
                        )

            # 2. Load file context (Matchup Analysis)
            file_context = load_context()
            if file_context:
                context += f"\n=== MATCHUP ANALYSIS ===\n{file_context}\n"

            # 3. Mentioned Players (Specific Queries)
            found_mentions = []
            if not players_df.empty:
                prompt_lower = prompt.lower()
                unique_players = players_df[
                    players_df["season"] == players_df["season"].max()
                ]

                for idx, row in unique_players.iterrows():
                    name = str(row["name"])
                    if name.lower() in prompt_lower:
                        found_mentions.append(row)

            if found_mentions:
                context += "\n=== SPECIFIC PLAYERS ===\n"
                for p in found_mentions:
                    try:
                        raw = p["raw_stats"]
                        # Detailed stats for mentioned players
                        context += f"- {p['name']} ({p['season']}): {raw[3]} PPG, {raw[4]} RPG, {raw[5]} APG, {raw[9]} FG%, {raw[10]} 3P%, {raw[18]} TO\n"
                    except Exception:
                        pass

            # 4. RAG / Knowledge Base Integration
            # Query the vector store for relevant drills/plays
            try:
                pipeline = RAGPipeline()
                # Get top 3 results
                results = pipeline.query(prompt, n=3)

                if results and results["documents"] and results["documents"][0]:
                    rag_context = (
                        "\n=== KNOWLEDGE BASE RESOURCES (Breakthrough Basketball) ===\n"
                    )
                    rag_context += "Use the following drills or plays to answer the user's question if relevant:\n\n"

                    # Store metadata to show to user
                    used_resources = []

                    for i, doc in enumerate(results["documents"][0]):
                        meta = results["metadatas"][0][i]
                        title = meta.get("title", "Untitled")
                        url = meta.get("url", "#")
                        rag_context += f"Resource {i + 1}: {title}\nContent: {doc}\n\n"
                        used_resources.append({"title": title, "url": url})

                    context += rag_context

                    # Show the user what we found
                    with message_placeholder.container():
                        with st.expander("📚 Consulted Knowledge Base", expanded=False):
                            for res in used_resources:
                                st.markdown(f"- [{res['title']}]({res['url']})")
            except Exception as e:
                # Don't crash chat if RAG fails
                print(f"RAG Error: {e}")

            response = st.session_state.coach.ask(context, prompt)

            # Show which model was used
            used_model = st.session_state.coach.get_model_info()
            final_response = f"**{used_model}**\n\n{response}"

            message_placeholder.markdown(final_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": final_response}
        )


# Sidebar Analysis Tools (Updated to write to file)
with st.sidebar.expander("Analysis Tools"):
    st.write("Generate insights to add to context.")
    if st.session_state.get("coach_team"):
        opponent_name = st.selectbox(
            "Select Opponent",
            [t for t in team_names if t != st.session_state["coach_team"]],
            key="sidebar_opponent",
        )
        if st.button("Analyze Matchup & Save"):
            # Get IDs
            my_team_id = teams_df[
                teams_df["name"] == st.session_state["coach_team"]
            ].iloc[0]["id"]
            opp_team_id = teams_df[teams_df["name"] == opponent_name].iloc[0]["id"]
            latest_season = players_df["season"].max()

            analysis = predict_matchup(
                players_df, my_team_id, opp_team_id, latest_season
            )
            save_context(analysis)
            st.session_state["prediction_context"] = (
                analysis  # Keep session state for immediate feedback
            )
            st.success("Analysis saved to tmp_prompt.txt!")
            st.markdown(f"**Preview:**\\n{analysis}")
    else:
        st.info("Select a Coach Team first.")
# ------------------------------------------------------------------
# TAB 6: Knowledge Base
# ------------------------------------------------------------------
with tab6:
    st.header("📚 Coach's Knowledge Base")
    st.markdown(
        "Access thousands of basketball drills and plays from _Breakthrough Basketball_."
    )

    # Status/Ingestion
    with st.expander("Manage Knowledge Base", expanded=False):
        st.info(
            "The Knowledge Base is processed locally. Updating it may take a few minutes."
        )

        col_kp1, col_kp2 = st.columns([1, 1])
        with col_kp1:
            if st.button("Update Knowledge Base (Scrape & Index)"):
                with st.spinner(
                    "Scraping Breakthrough Basketball and indexing content..."
                ):
                    try:
                        # Use a persistent pipeline instance or create new
                        pipeline = RAGPipeline()
                        # Start from main drills page and crawl a bit
                        count = pipeline.run_ingestion(
                            [
                                "https://www.breakthroughbasketball.com/drills/basketballdrills.html"
                            ],
                            max_depth=1,
                            max_pages=30,
                        )
                        st.success(f"Successfully indexed {count} new documents!")
                    except Exception as e:
                        st.error(f"Error updating knowledge base: {e}")

        with col_kp2:
            if st.button("Reset Knowledge Base"):
                try:
                    pipeline = RAGPipeline()
                    pipeline.reset_db()
                    st.success("Knowledge Base reset.")
                except Exception as e:
                    st.error(f"Error resetting: {e}")

    # Search Interface
    st.subheader("Search Drills & Plays")

    # Initialize session state for search
    if "kb_search_query" not in st.session_state:
        st.session_state["kb_search_query"] = ""

    search_query = st.text_input(
        "What are you looking for?",
        placeholder="e.g., 'shooting drills for youth', 'zone defense plays'",
        key="kb_search_input",
    )

    if search_query:
        pipeline = RAGPipeline()
        results = pipeline.query(search_query, n=5)

        if results and results["documents"] and results["documents"][0]:
            st.markdown(f"**Found {len(results['documents'][0])} results:**")

            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                title = meta.get("title", "Untitled Resource")
                url = meta.get("url", "#")

                with st.container():
                    st.markdown(f"### [{title}]({url})")
                    st.caption(f"Source: {url}")
                    # Show preview of markdown content
                    # Truncate content for preview if too long, or use an expander
                    with st.expander("View Content", expanded=(i == 0)):
                        st.markdown(doc)
                    st.divider()
        else:
            st.info(
                "No matching drills found. Try a different search term or update the Knowledge Base."
            )
