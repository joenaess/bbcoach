import os
import sys
from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Add src and project root to path
sys.path.append(os.path.abspath("src"))
sys.path.append(os.path.abspath("."))

import api.main  # noqa: E402


@pytest.fixture(autouse=True)
def mock_services(monkeypatch):
    mock_players_df = pd.DataFrame(
        {
            "id": ["p1", "p2", "p3"],
            "name": ["Player One", "Player Two", "Player Three"],
            "team_id": ["t1", "t1", "t2"],
            "PPG": [18.5, 12.0, 21.0],
            "RPG": [6.5, 8.0, 5.0],
            "APG": [4.2, 2.1, 6.0],
            "GP": [15, 15, 15],
            "MIN": [32.0, 28.0, 34.0],
            "FG%": [48.5, 52.0, 45.0],
            "3P%": [38.0, 33.3, 40.0],
            "TO": [2.0, 1.5, 2.5],
            "EFF": [20.0, 16.0, 22.0],
            "season": [2024, 2024, 2024],
            "league": ["Men", "Men", "Men"],
        }
    )
    mock_teams_df = pd.DataFrame(
        {
            "id": ["t1", "t2"],
            "name": ["Team Alpha", "Team Beta"],
            "season": [2024, 2024],
            "league": ["Men", "Men"],
        }
    )
    mock_schedule_df = pd.DataFrame(
        [
            {
                "date": "2024-11-01",
                "team_id": "t1",
                "team_name": "Team Alpha",
                "opponent": "Team Beta",
                "opponent_id": "t2",
                "result": "88-82",
                "home_away": "Home",
                "season": 2024,
            }
        ]
    )

    monkeypatch.setattr(
        api.main.data_service, "load_players", MagicMock(return_value=mock_players_df)
    )
    monkeypatch.setattr(
        api.main.data_service, "load_teams", MagicMock(return_value=mock_teams_df)
    )
    monkeypatch.setattr(
        api.main.data_service, "load_schedule", MagicMock(return_value=mock_schedule_df)
    )
    monkeypatch.setattr(
        api.main.data_service,
        "get_metadata",
        MagicMock(return_value={"last_fetched": "2026-01-01T00:00:00"}),
    )
    monkeypatch.setattr(
        api.main.coach_service,
        "ask",
        MagicMock(return_value="Run a 2-3 zone defense and focus on box-outs."),
    )
    monkeypatch.setattr(
        api.main.coach_service,
        "generate_scouting_report",
        MagicMock(return_value="Scouting Report: Key threat is Player Three."),
    )
    monkeypatch.setattr(
        api.main.coach_service,
        "get_model_info",
        MagicMock(return_value="Local Model (Qwen/Qwen2.5-1.5B-Instruct) 💻"),
    )
    monkeypatch.setattr(api.main.coach_service, "reload_provider", MagicMock())


client = TestClient(api.main.app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "bbcoach-api"


def test_get_data_status():
    """Test getting data status."""
    response = client.get("/api/data/status")
    assert response.status_code == 200
    data = response.json()
    assert data["players_count"] == 3
    assert data["teams_count"] == 2
    assert data["schedule_count"] == 1
    assert data["has_players"] is True
    assert 2024 in data["seasons_in_data"]


def test_refresh_data_cache():
    """Test clearing and refreshing data cache."""
    response = client.get("/api/data/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Cache refreshed"
    assert "status" in data


def test_fetch_progress():
    """Test scraping progress endpoint."""
    response = client.get("/api/data/fetch-progress")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_get_seasons():
    """Test getting available seasons."""
    response = client.get("/api/stats/seasons?league=Men")
    assert response.status_code == 200
    data = response.json()
    assert data["league"] == "Men"
    assert data["seasons"] == [2024]


def test_get_teams():
    """Test getting teams for a season."""
    response = client.get("/api/stats/teams?season=2024&league=Men")
    assert response.status_code == 200
    data = response.json()
    assert len(data["teams"]) == 2
    assert data["teams"][0]["name"] == "Team Alpha"


def test_get_top_players():
    """Test getting top players."""
    response = client.get("/api/stats/top-players?season=2024&league=Men&metric=PPG&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["players"]) == 2
    assert data["players"][0]["name"] == "Player Three"
    assert data["players"][0]["PPG"] == 21.0


def test_get_team_stats_found_and_not_found():
    """Test getting team statistics for valid and invalid teams."""
    response = client.get("/api/stats/team/t1?season=2024")
    assert response.status_code == 200
    data = response.json()
    assert data["team_id"] == "t1"
    assert data["stats"]["top_scorer"] == "Player One"
    assert len(data["stats"]["rotation"]) == 2

    not_found = client.get("/api/stats/team/unknown_team?season=2024")
    assert not_found.status_code == 404


def test_get_team_schedule():
    """Test getting schedule for a team."""
    response = client.get("/api/stats/schedule/t1?season=2024")
    assert response.status_code == 200
    data = response.json()
    assert data["team_id"] == "t1"
    assert len(data["schedule"]) == 1
    assert data["schedule"][0]["opponent"] == "Team Beta"


def test_compare_players():
    """Test comparing multiple players."""
    response = client.post(
        "/api/stats/compare-players",
        json={"player_names": ["Player One", "Player Three"], "season": 2024, "league": "Men"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    not_found = client.post(
        "/api/stats/compare-players",
        json={"player_names": ["Nonexistent"], "season": 2024, "league": "Men"},
    )
    assert not_found.status_code == 404


def test_predict_matchup():
    """Test single-season and multi-season matchup prediction endpoints."""
    response = client.post(
        "/api/analytics/predict-matchup",
        json={"team_a_id": "t1", "team_b_id": "t2", "season": 2024},
    )
    assert response.status_code == 200
    data = response.json()
    assert "DEEP MATCHUP ANALYSIS" in data["analysis"]

    multi_response = client.post(
        "/api/analytics/predict-matchup-multi-season",
        json={"team_a_id": "t1", "team_b_id": "t2"},
    )
    assert multi_response.status_code == 200
    assert "MULTI-SEASON TREND ANALYSIS" in multi_response.json()["analysis"]


def test_ask_coach_and_scouting_report():
    """Test AI coach ask and scouting report endpoints."""
    ask_resp = client.post(
        "/api/coach/ask",
        json={
            "question": "How do we defend their pick and roll?",
            "context": "Opponent has a strong guard",
            "team_id": "t1",
            "season": 2024,
        },
    )
    assert ask_resp.status_code == 200
    assert "zone defense" in ask_resp.json()["response"]

    scout_resp = client.post(
        "/api/coach/scouting-report",
        json={"opponent_name": "Team Beta", "stats_summary": "85 PPG, 40% 3P"},
    )
    assert scout_resp.status_code == 200
    assert scout_resp.json()["opponent"] == "Team Beta"
    assert "Player Three" in scout_resp.json()["report"]


def test_get_model_info():
    """Test getting coach model information."""
    response = client.get("/api/coach/model-info")
    assert response.status_code == 200
    assert "Qwen" in response.json()["model"]


def test_timestral_endpoints(monkeypatch):
    """Test Timestral trajectory forecast, head-to-head matchup, and evaluation endpoints."""
    mock_forecast = {
        "model": "mistralai/Timestral-209M",
        "team_name": "Team Alpha",
        "league": "Men",
        "historical_games_used": 90,
        "seasons_covered": [2024, 2025, 2026],
        "recent_avg_ppg": 88.5,
        "recent_avg_opp_ppg": 81.2,
        "expected_wins_next_n": 4.2,
        "horizon": 6,
        "history": [],
        "forecast": [
            {
                "step": 1,
                "date": "Oct 23, 2026, 7:04 PM",
                "season": 2026,
                "opponent": "Team Beta",
                "home_away": "Home",
                "team_score": {"median": 89.0, "q10": 77.0, "q25": 83.0, "q75": 95.0, "q90": 101.0},
                "opponent_score": {"median": 81.0, "q10": 70.0, "q25": 75.0, "q75": 87.0, "q90": 93.0},
                "point_diff": {"median": 8.0, "q10": -6.0, "q25": 1.0, "q75": 15.0, "q90": 22.0},
                "win_probability": 72.5,
            }
        ],
    }
    mock_matchup = {
        "model": "mistralai/Timestral-209M",
        "league": "Men",
        "team_a": "Team Alpha",
        "team_b": "Team Beta",
        "venue": "Team Alpha Home",
        "win_prob_a": 71.2,
        "win_prob_b": 28.8,
        "team_a_score": {"median": 89.5, "q10": 76.0, "q25": 82.5, "q75": 96.0, "q90": 103.0},
        "team_b_score": {"median": 81.5, "q10": 70.0, "q25": 76.0, "q75": 87.0, "q90": 94.0},
        "spread": {"median": 8.0, "q10": -7.5, "q25": 0.5, "q75": 15.5, "q90": 23.0},
        "total_points": {"median": 171.0, "q10": 146.0, "q90": 197.0},
        "head_to_head_history": [],
    }
    mock_eval = {
        "model": "mistralai/Timestral-209M",
        "league": "Men",
        "teams_evaluated": 10,
        "games_evaluated": 60,
        "metrics": {
            "timestral_209m": {
                "win_accuracy_pct": 70.0,
                "spread_mae": 11.01,
                "score_mae": 8.06,
                "brier_score": 0.1989,
                "interval_80_coverage_pct": 91.7,
            },
            "rolling_5_baseline": {
                "win_accuracy_pct": 65.0,
                "spread_mae": 12.35,
                "score_mae": 8.86,
            },
            "season_avg_baseline": {
                "win_accuracy_pct": 61.7,
                "spread_mae": 10.77,
                "score_mae": 8.25,
            },
        },
        "sample_predictions": [],
    }

    monkeypatch.setattr(
        api.main.analytics_service,
        "forecast_team_trajectory",
        MagicMock(return_value=mock_forecast),
    )
    monkeypatch.setattr(
        api.main.analytics_service,
        "predict_timestral_matchup",
        MagicMock(return_value=mock_matchup),
    )
    monkeypatch.setattr(
        api.main.analytics_service,
        "evaluate_timestral_backtest",
        MagicMock(return_value=mock_eval),
    )

    fc_resp = client.get("/api/analytics/timestral/forecast/t1?league=Men&horizon=6")
    assert fc_resp.status_code == 200
    assert fc_resp.json()["team_name"] == "Team Alpha"
    assert fc_resp.json()["expected_wins_next_n"] == 4.2

    m_resp = client.post(
        "/api/analytics/timestral/matchup",
        json={"team_a_id": "t1", "team_b_id": "t2", "league": "Men", "team_a_home": True},
    )
    assert m_resp.status_code == 200
    assert m_resp.json()["win_prob_a"] == 71.2

    ev_resp = client.get("/api/analytics/timestral/evaluate?league=Men&eval_games_per_team=6")
    assert ev_resp.status_code == 200
    assert ev_resp.json()["metrics"]["timestral_209m"]["win_accuracy_pct"] == 70.0


