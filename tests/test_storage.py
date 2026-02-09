import pytest
import pandas as pd
from bbcoach.data.storage import (
    save_players,
    load_players,
    save_teams,
    load_teams,
    DATA_DIR,
)
import shutil


@pytest.fixture(scope="function")
def clean_data_dir():
    # Setup
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    yield
    # Teardown
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)


def test_save_and_load_teams(clean_data_dir):
    teams = [
        {"id": "1", "name": "Team A", "season": 2023, "url": "http://a"},
        {"id": "2", "name": "Team B", "season": 2023, "url": "http://b"},
    ]
    save_teams(teams)

    df = load_teams()
    assert len(df) == 2
    assert "Team A" in df["name"].values


def test_save_and_load_players(clean_data_dir):
    players = [
        {"id": "p1", "name": "Player 1", "team_id": "1", "season": 2023},
        {"id": "p2", "name": "Player 2", "team_id": "1", "season": 2023},
    ]
    save_players(players)

    df = load_players()
    assert len(df) == 2
    assert "Player 1" in df["name"].values


def test_incremental_save(clean_data_dir):
    # Batch 1
    save_players([{"id": "p1", "name": "Player 1", "team_id": "1", "season": 2023}])
    # Batch 2
    save_players([{"id": "p2", "name": "Player 2", "team_id": "1", "season": 2023}])

    df = load_players()
    assert len(df) == 2
