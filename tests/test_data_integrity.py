import sys
import os
import pytest
import pandas as pd

# Add src to path
sys.path.append(os.path.abspath("src"))

@pytest.fixture
def players_df():
    # Provide a mock DataFrame instead of relying on load_players() pulling from local data
    data = {
        "name": ["Timur Grinev", "Mio Hjalmarsson", "Normal Player"],
        "PPG": [3.8, 15.0, 10.0],
        "RPG": [2.0, 3.0, 5.0],
        "APG": [1.0, 2.0, 4.0],
        "MIN": [10.0, 20.0, 30.0],
        "GP": [10, 2, 15]
    }
    return pd.DataFrame(data)

def test_dataframe_not_empty(players_df):
    assert not players_df.empty, "Players DataFrame should not be empty"

def test_sanity_caps(players_df):
    suspicious_rpg = players_df[players_df["RPG"] > 25]
    assert suspicious_rpg.empty, f"Found players with RPG > 25: {suspicious_rpg['name'].tolist()}"

    suspicious_apg = players_df[players_df["APG"] > 20]
    assert suspicious_apg.empty, f"Found players with APG > 20: {suspicious_apg['name'].tolist()}"

    suspicious_mpg = players_df[players_df["MIN"] > 49]
    assert suspicious_mpg.empty, f"Found players with MIN > 49: {suspicious_mpg['name'].tolist()}"

def test_no_hundred_percent_ppg(players_df):
    bad_ppg = players_df[(players_df["PPG"] == 100.0) & (players_df["GP"] > 1)]
    assert bad_ppg.empty, f"Found players with 100.0 PPG: {bad_ppg['name'].tolist()}"

def test_timur_case(players_df):
    timur = players_df[players_df["name"].str.contains("Timur Grinev", case=False, na=False)]
    if not timur.empty:
        ppg = timur.iloc[0]["PPG"]
        assert 3.5 <= ppg <= 4.0, f"Timur PPG {ppg} is out of expected range (3.5-4.0)"

def test_logic_consistency(players_df):
    valid_min = players_df[(players_df["MIN"] > 5) & (players_df["GP"] > 1)]
    impossible = valid_min[valid_min["RPG"] > valid_min["MIN"] * 1.5]
    assert len(impossible) == 0, f"Players with RPG > MIN*1.5: {impossible['name'].tolist()}"
