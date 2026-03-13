import sys
import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Add src and project root to path
sys.path.append(os.path.abspath("src"))
sys.path.append(os.path.abspath("."))

from fastapi.testclient import TestClient

# Mock data to prevent "NoneType has no attribute empty" errors for API tests 
# since tests shouldn't rely on existing parquet files
mock_players_df = pd.DataFrame({"name": ["Test"], "PPG": [10.0], "season": [2024], "league": ["Men"]})
mock_teams_df = pd.DataFrame({"id": ["t1"], "name": ["Test Team"], "season": [2024], "league": ["Men"]})
mock_schedule_df = pd.DataFrame([{"game": 1}])

import api.main

api.main.data_service.load_players = MagicMock(return_value=mock_players_df)
api.main.data_service.load_teams = MagicMock(return_value=mock_teams_df)
api.main.data_service.load_schedule = MagicMock(return_value=mock_schedule_df)

client = TestClient(api.main.app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_get_data_status():
    """Test getting data status"""
    response = client.get("/api/data/status")
    assert response.status_code == 200

def test_get_seasons():
    """Test getting available seasons"""
    response = client.get("/api/stats/seasons")
    assert response.status_code == 200

def test_get_teams():
    """Test getting teams for a season"""
    seasons_response = client.get("/api/stats/seasons")
    seasons = seasons_response.json().get("seasons", [])
    if seasons:
        response = client.get(f"/api/stats/teams?season={seasons[0]}")
        assert response.status_code == 200

def test_get_top_players():
    """Test getting top players"""
    seasons_response = client.get("/api/stats/seasons")
    seasons = seasons_response.json().get("seasons", [])
    if seasons:
        response = client.get(f"/api/stats/top-players?season={seasons[0]}&limit=5")
        assert response.status_code == 200

def test_get_model_info():
    """Test getting coach model information"""
    response = client.get("/api/coach/model-info")
    assert response.status_code == 200
