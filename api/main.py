"""
FastAPI Backend for BBCoach

RESTful API providing endpoints for the basketball coaching application.
"""
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src to path
sys.path.append(os.path.abspath("src"))

from bbcoach.config import settings  # noqa: E402
from bbcoach.core import AnalyticsService, CoachService, DataService  # noqa: E402
from bbcoach.data.scrapers import main as scrape_all  # noqa: E402

logger = logging.getLogger(__name__)


# Pydantic models for request/response
class CoachRequest(BaseModel):
    question: str
    context: str = ""
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    team_id: Optional[str] = None
    season: Optional[int] = None


class MultiMatchupRequest(BaseModel):
    team_a_id: str
    team_b_id: str


class ScoutRequest(BaseModel):
    opponent_name: str
    stats_summary: str


class MatchupRequest(BaseModel):
    team_a_id: str
    team_b_id: str
    season: int


class TimestralMatchupRequest(BaseModel):
    team_a_id: str
    team_b_id: str
    league: str = "Men"
    team_a_home: bool = True
    pace_adjustment: float = 0.0
    team_a_off_boost: float = 0.0
    team_a_def_boost: float = 0.0


class PlayerRequest(BaseModel):
    player_names: list[str]
    season: int
    league: str = "Men"


# Global service instances
data_service = DataService()
analytics_service = AnalyticsService(data_service)
coach_service = CoachService()

# Global scraper progress state
scraping_progress = {
    "status": "idle",
    "current": 0,
    "total": 0,
    "team": "",
    "league": "",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    logger.info("Starting BBCoach API...")

    # Initialize services
    global data_service, analytics_service, coach_service

    data_service = DataService()
    analytics_service = AnalyticsService(data_service)
    coach_service = CoachService()

    # Check data status
    data_status = data_service.get_data_status()
    logger.info(f"Data status: {data_status}")

    yield

    logger.info("Shutting down BBCoach API...")


# Create FastAPI app
app = FastAPI(
    title="BBCoach API",
    description="AI-powered basketball coaching analytics platform",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "bbcoach-api"}


# Data endpoints
@app.get("/api/data/status")
async def get_data_status():
    """Get data file status."""
    return data_service.get_data_status()


@app.get("/api/data/refresh")
async def refresh_data_cache():
    """Clear and reload data cache."""
    data_service.clear_cache()
    status = data_service.get_data_status()
    return {"message": "Cache refreshed", "status": status}


@app.post("/api/data/fetch")
async def fetch_latest_data(background_tasks: BackgroundTasks):
    """Run the scraper in the background and return immediately."""
    global scraping_progress

    if scraping_progress["status"] == "fetching":
        return {
            "message": "Scraping is already in progress.",
            "status": data_service.get_data_status(),
        }

    scraping_progress = {
        "status": "fetching",
        "current": 0,
        "total": 0,
        "team": "Initializing...",
        "league": "Starting",
    }

    def update_progress(team_name, current_idx, total_count, league_name):
        scraping_progress["current"] = current_idx
        scraping_progress["total"] = total_count
        scraping_progress["team"] = team_name
        scraping_progress["league"] = league_name

    def run_scraper_task():
        try:
            scrape_all(progress_callback=update_progress)
            data_service.update_metadata()
            data_service.clear_cache()  # Force reload from disk
            scraping_progress["status"] = "idle"
        except Exception as e:
            scraping_progress["status"] = "error"
            logger.error(f"Error fetching data: {e}", exc_info=True)

    background_tasks.add_task(run_scraper_task)

    return {
        "message": "Scraping started in background.",
        "status": data_service.get_data_status(),
    }


@app.get("/api/data/fetch-progress")
async def get_fetch_progress():
    """Return the current data scraping execution progress."""
    return scraping_progress


# Stats endpoints
@app.get("/api/stats/seasons")
async def get_seasons(league: str = Query("Men", description="League filter")):
    """Get available seasons."""
    seasons = analytics_service.get_available_seasons(league)
    return {"league": league, "seasons": seasons}


@app.get("/api/stats/teams")
async def get_teams(
    season: int = Query(..., description="Season year"),
    league: str = Query("Men", description="League filter"),
):
    """Get teams for a given season and league."""
    teams = analytics_service.get_available_teams(season, league)
    return {"season": season, "league": league, "teams": teams}


@app.get("/api/stats/top-players")
async def get_top_players(
    season: int, league: str = "Men", metric: str = "PPG", limit: int = 10
):
    """Get top players for a specific metric."""
    players = analytics_service.get_top_players(season, league, metric, limit)
    return {"season": season, "league": league, "metric": metric, "players": players}


@app.get("/api/stats/team/{team_id}")
async def get_team_stats(team_id: str, season: int = Query(...)):
    """Get team statistics."""
    stats = analytics_service.get_team_stats(team_id, season)
    if stats is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"team_id": team_id, "season": season, "stats": stats}


@app.get("/api/stats/schedule/{team_id}")
async def get_team_schedule(
    team_id: str, season: Optional[int] = Query(None, description="Optional season filter")
):
    """Get schedule for a specific team."""
    schedule = analytics_service.get_team_schedule(team_id, season)
    return {"team_id": team_id, "season": season, "schedule": schedule}


@app.post("/api/stats/compare-players")
async def compare_players(request: PlayerRequest):
    """Compare multiple players."""
    comparison = analytics_service.compare_players(
        request.player_names, request.season, request.league
    )
    if comparison is None:
        raise HTTPException(status_code=404, detail="Players not found")
    return comparison.to_dict(orient="records")


# Analytics endpoints
@app.post("/api/analytics/predict-matchup")
async def predict_matchup(request: MatchupRequest):
    """Predict matchup between two teams."""
    analysis = analytics_service.predict_matchup(
        request.team_a_id, request.team_b_id, request.season
    )
    if analysis is None:
        raise HTTPException(
            status_code=404, detail="Matchup prediction failed - check team IDs and season"
        )
    return {
        "team_a_id": request.team_a_id,
        "team_b_id": request.team_b_id,
        "season": request.season,
        "analysis": analysis,
    }


@app.post("/api/analytics/predict-matchup-multi-season")
async def predict_multi_season_matchup(request: MultiMatchupRequest):
    """Predict matchup using multi-season data."""
    analysis = analytics_service.predict_matchup_multi_season(request.team_a_id, request.team_b_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Multi-season prediction failed")
    return {
        "team_a_id": request.team_a_id,
        "team_b_id": request.team_b_id,
        "analysis": analysis,
    }


@app.get("/api/analytics/timestral/forecast/{team_id}")
async def timestral_team_forecast(
    team_id: str,
    league: str = Query("Men", description="League filter (Men or Women)"),
    horizon: int = Query(6, ge=1, le=15, description="Forecast horizon in games"),
):
    """Forecast upcoming team games with 21-quantile distributions via Timestral-209M."""
    forecast = analytics_service.forecast_team_trajectory(
        team_id=team_id, league=league, horizon=horizon
    )
    if forecast is None:
        raise HTTPException(
            status_code=404,
            detail="Insufficient historical schedule data for Timestral forecast",
        )
    return forecast


@app.post("/api/analytics/timestral/matchup")
async def timestral_matchup_prediction(request: TimestralMatchupRequest):
    """Predict head-to-head matchup probabilities and score quantiles via Timestral-209M."""
    prediction = analytics_service.predict_timestral_matchup(
        team_a_id=request.team_a_id,
        team_b_id=request.team_b_id,
        league=request.league,
        team_a_home=request.team_a_home,
        pace_adjustment=request.pace_adjustment,
        team_a_off_boost=request.team_a_off_boost,
        team_a_def_boost=request.team_a_def_boost,
    )
    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail="Insufficient historical schedule data for Timestral matchup prediction",
        )
    return prediction


@app.get("/api/analytics/timestral/evaluate")
async def timestral_evaluate_backtest(
    league: str = Query("Men", description="League filter (Men or Women)"),
    eval_games_per_team: int = Query(6, ge=1, le=15, description="Held-out games per team"),
):
    """Evaluate Timestral-209M on held-out historical SBL games vs baselines."""
    evaluation = analytics_service.evaluate_timestral_backtest(
        league=league, eval_games_per_team=eval_games_per_team
    )
    if evaluation is None or "error" in evaluation:
        raise HTTPException(
            status_code=404,
            detail=(evaluation or {}).get("error", "Timestral evaluation failed"),
        )
    return evaluation



# Coach/AI endpoints
@app.post("/api/coach/ask")
async def ask_coach(request: CoachRequest):
    """Ask the AI coach a question."""
    try:
        # Reload coach if provider specified
        if request.provider:
            coach_service.reload_provider(request.provider, request.api_key, request.model_name)

        # If the frontend pushed myTeamId, get their real data for the AI logic context
        resolved_context = request.context
        if request.team_id and request.season:
            stats = analytics_service.get_team_stats(request.team_id, request.season)
            if stats:
                resolved_context = f"Team Statistics ({request.season}):\n{stats}\n\n" + resolved_context

        response = coach_service.ask(request.question, resolved_context)
        model_info = coach_service.get_model_info()

        return {
            "question": request.question,
            "response": response,
            "model": model_info,
        }
    except Exception as e:
        logger.error(f"Error in ask_coach: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/coach/scouting-report")
async def generate_scouting_report(request: ScoutRequest):
    """Generate a scouting report for an opponent."""
    try:
        report = coach_service.generate_scouting_report(
            request.opponent_name, request.stats_summary
        )
        model_info = coach_service.get_model_info()

        return {
            "opponent": request.opponent_name,
            "report": report,
            "model": model_info,
        }
    except Exception as e:
        logger.error(f"Error generating scouting report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/coach/model-info")
async def get_model_info():
    """Get information about the current AI model."""
    try:
        model_info = coach_service.get_model_info()
        return {"model": model_info}
    except Exception as e:
        logger.error(f"Error getting model info: {e}", exc_info=True)
        return {"model": "Error loading model", "error": str(e)}


# Run server
if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level)

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
