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


def create_trend_line(team_name: str, games_df: pd.DataFrame):
    """
    Placeholder for trend line. Requires game log data which we might not have fully parsed yet.
    """
    pass
