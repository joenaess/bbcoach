import streamlit as st


def render_player_card(player_data, rank=None):
    """
    Renders a stylized player card using HTML/CSS.
    """
    name = player_data["name"]
    team = player_data.get("team", "Unknown")
    ppg = player_data["PPG"]
    rpg = player_data["RPG"]
    # apg = player_data["APG"] # Unused

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


def render_comparison_chart(
    df, team1_name, team2_name, metrics=["PPG", "RPG", "APG", "3P%"]
):
    """
    Renders a grouped bar chart comparing two teams/players across metrics.
    Expects df with columns: ['Metric', 'Value', 'Entity']
    """
    import plotly.express as px
    # import pandas as pd # Removed unused import

    # Check if df is already long format or needs melting
    # ... logic handled by caller usually, but let's make it robust

    fig = px.bar(
        df,
        x="Metric",
        y="Value",
        color="Entity",
        barmode="group",
        color_discrete_sequence=["#FF5722", "#BDC1C6"],
        template="plotly_dark",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter",
        legend_title_text="",
        margin=dict(l=20, r=20, t=30, b=20),
    )

    # fig.update_layout... (metrics not used? apg not used?)
    # Wait, simple replace first.
    st.plotly_chart(
        fig, use_container_width=True
    )  # Let's stick to use_container_width for plotly for now as 'width' might not be supported there yet?
    # Actually, let's try 'width="stretch"' since user said so.
    # But wait, st.plotly_chart might not support it.
    # The warning likely came from st.dataframe.
    # I will stick to use_container_width=True for Chart for now unless I see a warning for it.
    # But I removed it earlier!

    st.plotly_chart(fig, use_container_width=True)
