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

# --- MODEL INFO & SIDEBAR ---
# We need to initialize the coach early or check env to know the model for display
# But loading the model is heavy, so let's check the env variable directly for the UI label
import os
from dotenv import load_dotenv

load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
active_model_label = (
    "Google Gemini 2.0 Flash ⚡" if gemini_key else "Local Model (Qwen 1.5B) 💻"
)

with st.sidebar:
    st.markdown("### 🤖 Active AI Model")
    st.info(f"**{active_model_label}**")
    st.markdown("---")

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
    selected_team_name = st.sidebar.selectbox("Select Your Team", team_names, index=0)
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
                with st.spinner("Loading AI Coach (this may take a moment)..."):
                    from bbcoach.ai.coach import BasketballCoach

                    # Initialize with GPU if available
                    st.session_state.coach = BasketballCoach()

            # Prepare context
            coach_team = st.session_state.get("coach_team", "Unknown Team")

            # --- SYSTEM PROMPT ---
            system_prompt = f"""
            You are the deeply analytical **Assistant Coach** of {coach_team} in the Swedish Basketball League.
            Your job is to support the Head Coach with data-driven tactical advice, practice recommendations, and playbook adjustments.

            **YOUR CAPABILITIES:**
            1. **Game Tactics**: Suggest offensive/defensive schemes based on matchups (e.g., "Switch all screens," "Zone defense against their poor shooters").
            2. **Practice Focus**: Recommend specific drills based on recent performance or upcoming opponent weaknesses (e.g., "Close-out drills" if opponent shoots 3s well).
            3. **Playbook Setups**: Propose specific plays (ATO, P&R coverage) to exploit gaps in the opponent's defense.
            
            **GUIDELINES:**
            - Use the **FULL ROSTER STATS** provided to find hidden gems or specific mismatches (not just starters).
            - Be specific. Don't say "play better defense," say "We need to ICE the pick-and-roll against {opponent_name if "opponent_name" in locals() else "them"} because their guards are poor shooters."
            - Refer to "Our Starters" and "Their Starters" explicitly when analyzing rotations.
            """

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
            message_placeholder.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

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
            st.markdown(f"**Preview:**\n{analysis}")
    else:
        st.info("Select a Coach Team first.")
