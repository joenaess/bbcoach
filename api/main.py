"""
FastAPI Backend for BBCoach

RESTful API providing endpoints for the basketball coaching application.
"""
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

import logging
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bbcoach.config import settings
from bbcoach.core import CoachService, AnalyticsService, DataService

logger = logging.getLogger(__name__)


# Pydantic models for request/response
class CoachRequest(BaseModel):
    question: str
    context: str = ""
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None


class ScoutRequest(BaseModel):
    opponent_name: str
    stats_summary: str


class MatchupRequest(BaseModel):
    team_a_id: str
    team_b_id: str
    season: int


class PlayerRequest(BaseModel):
    player_names: list[str]
    season: int
    league: str = "Men"


# Global service instances
data_service: DataService
analytics_service: AnalyticsService
coach_service: CoachService


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
    description="AI-powered basketball coaching analytics平台",
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
    season: int = Query(..., description="Season year"),
    league: str = Query("Men", description="League filter"),
    metric: str = Query("PPG", description="Statistic to sort by"),
    limit: int = Query(10, description="Number of results"),
):
    """Get top players by metric."""
    players = analytics_service.get_top_players(season, league, metric, limit)
    return {"season": season, "league": league, "metric": metric, "players": players}


@app.get("/api/stats/team/{team_id}")
async def get_team_stats(team_id: str, season: int = Query(...)):
    """Get team statistics."""
    stats = analytics_service.get_team_stats(team_id, season)
    if stats is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"team_id": team_id, "season": season, "stats": stats}


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
async def predict_multi_season_matchup(team_a_id: str, team_b_id: str):
    """Predict matchup using multi-season data."""
    analysis = analytics_service.predict_matchup_multi_season(team_a_id, team_b_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Multi-season prediction failed")
    return {
        "team_a_id": team_a_id,
        "team_b_id": team_b_id,
        "analysis": analysis,
    }


# Coach/AI endpoints
@app.post("/api/coach/ask")
async def ask_coach(request: CoachRequest):
    """Ask the AI coach a question."""
    try:
        # Reload coach if provider specified
        if request.provider:
            coach_service.reload_provider(request.provider, request.api_key, request.model_name)

        response = coach_service.ask(request.question, request.context)
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
