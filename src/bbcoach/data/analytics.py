import pandas as pd
import plotly.graph_objects as go
from typing import List


def create_radar_chart(player_stats: pd.DataFrame, metrics: List[str] = None):
    """
    Creates a radar chart comparing players based on provided stats.

    Args:
        player_stats (pd.DataFrame): DataFrame containing player stats.
                                     Must have 'name' column and numeric columns for metrics.
        metrics (List[str]): List of column names to potentiall visualize.
                             Defaults to ['PPG', 'RPG', 'APG', 'SPG', '3P%'].
    """
    if metrics is None:
        metrics = ["PPG", "RPG", "APG", "SPG", "3P%"]

    # Filter for average stats columns effectively
    # Ensure columns exist
    available_metrics = [m for m in metrics if m in player_stats.columns]

    if not available_metrics or player_stats.empty:
        return None

    fig = go.Figure()

    for i, row in player_stats.iterrows():
        # Normalize or use raw? For now, raw values, but radar charts often need normalization
        # to be fair (e.g. 30 PPG vs 2 SPG).
        # Let's simple plot raw for now, knowing the scale difference might be an issue.
        # Ideally we'd use percentiles, but we don't have league-wide context easily here.

        values = [row[m] for m in available_metrics]
        # Close the polygon
        values.append(values[0])
        plot_metrics = available_metrics + [available_metrics[0]]

        fig.add_trace(
            go.Scatterpolar(
                r=values, theta=plot_metrics, fill="toself", name=row["name"]
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, player_stats[available_metrics].max().max() * 1.1],
            )
        ),
        showlegend=True,
        title="Player Comparison",
    )
    return fig


def create_win_loss_trend(team_name: str):
    """
    Creates a trend line of cumulative wins/losses over a simulated season.
    Mocks data for now as we don't have game logs.
    """
    import numpy as np

    # Simulate 30 games
    games = 30

    # deterministic seed based on team name length for consistency
    np.random.seed(len(team_name))

    # Base win probability (0.3 to 0.7)
    win_prob = 0.3 + (len(team_name) % 5) * 0.1

    results = np.random.choice([1, 0], size=games, p=[win_prob, 1 - win_prob])
    cumulative_wins = np.cumsum(results)
    cumulative_losses = np.cumsum(1 - results)

    # Net Score (Win - Loss)
    net_score = cumulative_wins - cumulative_losses

    df = pd.DataFrame(
        {
            "Game": range(1, games + 1),
            "Net Score": net_score,
            "Result": ["Win" if r == 1 else "Loss" for r in results],
        }
    )

    fig = go.Figure()

    # Color based on value (Green for positive, Red for negative)
    fig.add_trace(
        go.Scatter(
            x=df["Game"],
            y=df["Net Score"],
            mode="lines+markers",
            name="Net Performance",
            line=dict(color="#FF5722", width=3),
            marker=dict(
                size=8, color=["green" if r == "Win" else "red" for r in df["Result"]]
            ),
        )
    )

    fig.update_layout(
        title=f"Season Momentum: {team_name} (Simulated)",
        xaxis_title="Game Number",
        yaxis_title="Net Wins (Wins - Losses)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    return fig
