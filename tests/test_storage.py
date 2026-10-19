import pytest

import bbcoach.data.storage as storage
from bbcoach.data.storage import (
    load_players,
    load_schedule,
    load_teams,
    save_players,
    save_schedule,
    save_teams,
)


@pytest.fixture(autouse=True)
def clean_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data_storage")
    yield


def test_save_and_load_teams():
    teams = [
        {"id": "1", "name": "Team A", "season": 2023, "url": "http://a"},
        {"id": "2", "name": "Team B", "season": 2023, "url": "http://b"},
    ]
    save_teams(teams)

    df = load_teams()
    assert len(df) == 2
    assert "Team A" in df["name"].values
    assert (df["league"] == "Men").all()


def test_save_and_load_players():
    players = [
        {"id": "p1", "name": "Player 1", "team_id": "1", "season": 2023},
        {"id": "p2", "name": "Player 2", "team_id": "1", "season": 2023},
    ]
    save_players(players)

    df = load_players()
    assert len(df) == 2
    assert "Player 1" in df["name"].values


def test_incremental_save():
    # Batch 1
    save_players([{"id": "p1", "name": "Player 1", "team_id": "1", "season": 2023}])
    # Batch 2
    save_players([{"id": "p2", "name": "Player 2", "team_id": "1", "season": 2023}])

    df = load_players()
    assert len(df) == 2


def test_save_and_load_schedule():
    games = [
        {
            "date": "2025-01-10",
            "team_id": "1",
            "team_name": "Team A",
            "opponent": "Team B",
            "opponent_id": "2",
            "result": "85-78",
            "home_away": "Home",
            "season": 2025,
        }
    ]
    save_schedule(games)

    df = load_schedule()
    assert len(df) == 1
    assert df.iloc[0]["opponent"] == "Team B"

