import os
import sys
from unittest.mock import MagicMock

import pandas as pd
import pytest

sys.path.append(os.path.abspath("src"))

from bbcoach.analysis import (  # noqa: E402
    get_multi_season_aggregates,
    get_team_aggregates,
    predict_matchup,
    predict_matchup_multi_season,
)
from bbcoach.core import AnalyticsService, CoachService, DataService  # noqa: E402
from bbcoach.data.storage import save_players, save_schedule, save_teams  # noqa: E402


@pytest.fixture
def sample_players_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": "p1",
                "name": "Alpha Guard",
                "team_id": "t1",
                "season": 2024,
                "league": "Men",
                "PPG": 20.0,
                "RPG": 4.0,
                "APG": 7.0,
                "GP": 12,
                "MIN": 34.0,
                "FG%": 47.0,
                "3P%": 39.0,
                "TO": 2.5,
                "EFF": 21.0,
            },
            {
                "id": "p2",
                "name": "Alpha Center",
                "team_id": "t1",
                "season": 2024,
                "league": "Men",
                "PPG": 14.0,
                "RPG": 10.5,
                "APG": 1.5,
                "GP": 12,
                "MIN": 30.0,
                "FG%": 58.0,
                "3P%": 20.0,
                "TO": 1.8,
                "EFF": 19.5,
            },
            {
                "id": "p3",
                "name": "Beta Wing",
                "team_id": "t2",
                "season": 2024,
                "league": "Men",
                "PPG": 22.0,
                "RPG": 6.0,
                "APG": 4.0,
                "GP": 12,
                "MIN": 35.0,
                "FG%": 45.0,
                "3P%": 37.0,
                "TO": 3.0,
                "EFF": 20.0,
            },
        ]
    )


def test_get_team_aggregates(sample_players_df):
    stats = get_team_aggregates(sample_players_df, "t1", 2024)
    assert stats is not None
    assert stats["total_ppg"] == 34.0
    assert stats["total_rpg"] == 14.5
    assert stats["top_scorer"] == "Alpha Guard"
    assert stats["top_rebounder"] == "Alpha Center"
    assert stats["top_playmaker"] == "Alpha Guard"
    assert stats["rotation"][0]["PPG"] == 20.0
    assert stats["rotation"][0]["ppg"] == 20.0


def test_predict_matchup_and_multi_season(sample_players_df):
    single = predict_matchup(sample_players_df, "t1", "t2", 2024)
    assert "DEEP MATCHUP ANALYSIS" in single
    assert "Alpha Guard" in single
    assert "Beta Wing" in single

    multi_agg = get_multi_season_aggregates(sample_players_df, "t1")
    assert multi_agg is not None
    assert multi_agg["total_ppg"] == 34.0

    multi = predict_matchup_multi_season(sample_players_df, "t1", "t2")
    assert "MULTI-SEASON TREND ANALYSIS" in multi


def test_data_service_with_custom_dir(tmp_path, sample_players_df):
    save_players(sample_players_df.to_dict(orient="records"), data_dir=tmp_path)
    save_teams(
        [{"id": "t1", "name": "Alpha", "season": 2024, "league": "Men"}],
        data_dir=tmp_path,
    )
    save_schedule(
        [
            {
                "date": "2024-10-15",
                "team_id": "t1",
                "team_name": "Alpha",
                "opponent": "Beta",
                "opponent_id": "t2",
                "result": "90-85",
                "home_away": "Home",
                "season": 2024,
            }
        ],
        data_dir=tmp_path,
    )

    ds = DataService(data_dir=str(tmp_path))
    ds.update_metadata()

    status = ds.get_data_status()
    assert status["players_count"] == 3
    assert status["teams_count"] == 1
    assert status["schedule_count"] == 1
    assert status["last_fetched"] is not None
    assert status["seasons_in_data"] == [2024]

    analytics = AnalyticsService(ds)
    assert analytics.get_available_seasons("Men") == [2024]
    assert len(analytics.get_available_teams(2024, "Men")) == 1
    assert len(analytics.get_team_schedule("t1", 2024)) == 1


def test_coach_service_lazy_model_info():
    cs = CoachService(provider="gemini", model_name="gemini-2.0-flash")
    # Should not initialize _coach just to get model info
    info = cs.get_model_info()
    assert cs._coach is None
    assert "Gemini (gemini-2.0-flash)" in info

    mock_coach = MagicMock()
    mock_coach.ask.return_value = "Play fast in transition."
    cs._coach = mock_coach

    answer = cs.ask("What pace should we use?", "Fast guards")
    assert answer == "Play fast in transition."
    mock_coach.ask.assert_called_once()
