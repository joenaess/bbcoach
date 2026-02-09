import streamlit as st
import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from bbcoach.data.storage import load_players, load_teams

# Lazy load AI model to avoid long startup time if not needed immediately
# from bbcoach.ai.coach import BasketballCoach
from bbcoach.analysis import predict_matchup

st.set_page_config(
    page_title="Swedish Basketball League Coach", layout="wide", page_icon="🏀"
)

# --- THEME CSS ---
st.markdown(
    """
    <style>
    /* Basketball Theme Colors */
    :root {
        --primary-color: #FF5722; /* Basketball Orange */
        --background-color: #FAFAFA;
        --secondary-background-color: #F0F2F6;
        --text-color: #333333;
        --font: "sans-serif";
    }
    
    .stAppHeader {
        background-color: #1E1E1E !important;
        color: white !important;
    }
    
    /* Custom Title */
    h1 {
        color: #E65100;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
    }
    
    h2, h3 {
        color: #BF360C;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #263238;
        color: white;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #E65100;
        color: white;
        border-radius: 20px;
        font-weight: bold;
        border: none;
    }
    .stButton > button:hover {
        background-color: #FF6D00;
        color: white;
    }
    
    /* Dataframes */
    [data-testid="stDataFrame"] {
        border: 2px solid #FFCC80;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
        import json
        from datetime import datetime, timedelta

        try:
            with open("data_storage/metadata.json", "r") as f:
                meta = json.load(f)
                last_update = meta.get("last_updated", "Unknown")

                # Check freshness (e.g., < 24 hours)
                try:
                    last_dt = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")
                    if datetime.now() - last_dt < timedelta(hours=24):
                        is_fresh = True
                except:
                    pass
        except:
            pass

    if is_fresh:
        st.success(f"✅ Stats Up-to-Date\n({last_update})")
    else:
        st.warning(f"⚠️ Stats Outdated\n({last_update})")

    if st.button("Fetch New Stats"):
        import subprocess
        import re

        progress_bar = st.progress(0, text="Starting Scraper...")
        status_text = st.empty()

        try:
            # Run the scraper as a subprocess and read stdout
            process = subprocess.Popen(
                ["uv", "run", "python", "src/bbcoach/data/scrapers.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
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
                st.error(f"Error fetching stats. Check logs.")

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
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["League Stats", "Game Predictor", "Coach's Corner"])

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

if page == "League Stats":
    st.header("League Statistics")

    if players_df.empty:
        st.warning("No data found. Please run the scraper first.")
    else:
        st.subheader("Player Stats")
        season = st.selectbox("Select Season", players_df["season"].unique())

        filtered_players = players_df[players_df["season"] == season]

        # Create a mapping for Team ID to Name
        team_id_map = dict(zip(teams_df["id"], teams_df["name"]))

        # Parse stats for display
        display_data = []
        for _, row in filtered_players.iterrows():
            try:
                raw = row["raw_stats"]
                # Indices based on analysis.py logic
                display_data.append(
                    {
                        "Name": row["name"],
                        "Team": team_id_map.get(
                            str(row["team_id"]), row["team_id"]
                        ),  # Map ID to Name
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
            except:
                continue

        if display_data:
            st.dataframe(pd.DataFrame(display_data))
        else:
            st.dataframe(filtered_players)  # Fallback

        st.subheader("Team Roster")

        # Default to Coach Team if available
        default_team_index = 0
        unique_team_ids = filtered_players["team_id"].unique()

        # Try to find the ID of the selected coach team
        if st.session_state.get("coach_team"):
            # This is a bit tricky since we only have ID in players_df and Name in teams_df relationship
            # Let's find the ID for the selected team name
            team_record = teams_df[teams_df["name"] == st.session_state["coach_team"]]
            if not team_record.empty:
                coach_team_id = team_record.iloc[0]["id"]
                # Check if this ID is in the current filtered players (season might differ)
                if coach_team_id in unique_team_ids:
                    default_team_index = list(unique_team_ids).index(coach_team_id)

        selected_team_id = st.selectbox(
            "Select Team ID", unique_team_ids, index=default_team_index
        )
        team_roster = filtered_players[filtered_players["team_id"] == selected_team_id]
        st.dataframe(team_roster)

elif page == "Game Predictor":
    st.header("Matchup Predictor")

    # Team Selection for Opponent
    opponent_name = st.selectbox("Select Opponent", teams_df["name"].unique())
    opponent_record = teams_df[teams_df["name"] == opponent_name]

    season = st.selectbox("Season", sorted(players_df["season"].unique(), reverse=True))
    use_multi_season = st.checkbox("Include Multi-Season Trend Analysis?", value=False)

    if st.button("Analyze Matchup"):
        if not opponent_record.empty and st.session_state.get("coach_team"):
            opp_id = opponent_record.iloc[0]["id"]

            # Get Coach Team ID
            coach_record = teams_df[teams_df["name"] == st.session_state["coach_team"]]
            if not coach_record.empty:
                coach_id = coach_record.iloc[0]["id"]

                # 1. Single Season Analysis
                analysis = predict_matchup(players_df, coach_id, opp_id, season)
                st.text(analysis)

                # 2. Multi-Season Analysis (Optional)
                if use_multi_season:
                    from bbcoach.analysis import predict_matchup_multi_season

                    trend_analysis = predict_matchup_multi_season(
                        players_df, coach_id, opp_id
                    )
                    st.text(trend_analysis)
                    analysis += "\n" + trend_analysis

                # Button to save
                if st.button("Save to Context"):
                    st.session_state["prediction_context"] = analysis
                    save_context(analysis)
                    st.success("Analysis saved to AI Context!")
            else:
                st.error("Please select your Coach Team in the sidebar first.")


elif page == "Coach's Corner":
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
                            except:
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
                    except:
                        pass

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
            st.success(f"Analysis saved to tmp_prompt.txt!")
            st.markdown(f"**Preview:**\\n{analysis}")
    else:
        st.info("Select a Coach Team first.")
