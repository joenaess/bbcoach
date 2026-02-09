import streamlit as st


def render_player_card(player_data, rank=None):
    """
    Renders a stylized player card using HTML/CSS.
    """
    name = player_data["name"]
    team = player_data.get("team", "Unknown")
    ppg = player_data["PPG"]
    rpg = player_data["RPG"]
    apg = player_data["APG"]

    rank_html = (
        f'<div style="font-size: 1.5rem; font-weight: bold; color: #555; margin-right: 15px;">#{rank}</div>'
        if rank
        else ""
    )

    html = f"""
    <div class="player-card">
        {rank_html}
        <div style="flex-grow: 1;">
            <div class="player-name">{name}</div>
            <div class="player-team">{team}</div>
        </div>
        <div style="display: flex; gap: 10px;">
            <div class="stat-badge">{ppg} PPG</div>
            <div class="stat-badge" style="background: #262730; color: #BDC1C6;">{rpg} RPG</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_stat_metric(label, value, delta=None, color=None):
    """
    Wrapper for st.metric with custom styling hooks if needed.
    """
    st.metric(label=label, value=value, delta=delta)
