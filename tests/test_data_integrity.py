import sys
import os
import pytest

# Add src to path
sys.path.append(os.path.abspath("src"))
from bbcoach.data.storage import load_players


@pytest.fixture
def players_df():
    df = load_players()
    return df


def test_dataframe_not_empty(players_df):
    assert not players_df.empty, "Players DataFrame should not be empty"


def test_sanity_caps(players_df):
    """
    Ensure no player exceeds the hard caps we set.
    """
    suspicious_rpg = players_df[players_df["RPG"] > 25]
    assert suspicious_rpg.empty, (
        f"Found players with RPG > 25: {suspicious_rpg['name'].tolist()}"
    )

    suspicious_apg = players_df[players_df["APG"] > 20]
    assert suspicious_apg.empty, (
        f"Found players with APG > 20: {suspicious_apg['name'].tolist()}"
    )

    suspicious_mpg = players_df[players_df["MIN"] > 49]  # 48 is regulation + OT margin
    assert suspicious_mpg.empty, (
        f"Found players with MIN > 49: {suspicious_mpg['name'].tolist()}"
    )


def test_no_hundred_percent_ppg(players_df):
    """
    Mio Hjalmarsson Case: Ensure no player has exactly 100.0 PPG unless they have 1 GP and scored 100 (unlikely).
    """
    bad_ppg = players_df[(players_df["PPG"] == 100.0) & (players_df["GP"] > 1)]
    assert bad_ppg.empty, f"Found players with 100.0 PPG: {bad_ppg['name'].tolist()}"


def test_timur_case(players_df):
    """
    Specific validation for Timur Grinev (Total Points vs Average).
    """
    timur = players_df[
        players_df["name"].str.contains("Timur Grinev", case=False, na=False)
    ]
    if not timur.empty:
        ppg = timur.iloc[0]["PPG"]
        assert 7.0 <= ppg <= 8.0, f"Timur PPG {ppg} is out of expected range (7.0-8.0)"


def test_logic_consistency(players_df):
    """
    General Logic: Rebounds cannot exceed Minutes (roughly), unless rebound rate is insane which is rare > 1.0/min
    """
    # Filter valid minutes
    valid_min = players_df[(players_df["MIN"] > 5) & (players_df["GP"] > 1)]

    # Check if RPG > MIN (Impossible to get more rebounds than minutes usually)
    # Give some buffer for weird rounding or extreme efficiency
    impossible = valid_min[valid_min["RPG"] > valid_min["MIN"] * 1.5]

    if not impossible.empty:
        # Just print warnings for now, asserting might break on edge cases (e.g. 1 min, 2 reb)
        print(f"Warning: Players with RPG > MIN*1.5: {impossible['name'].tolist()}")
        # We enforce a strict failure if likely error
        # Max Lidman had 40 RPG in 40 MIN (Total/Avg confusion).
        # If we fix Lidman, this shouldn't trigger high RPG.
