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
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel

from bbcoach.config import settings
from bbcoach.core import CoachService, AnalyticsService, DataService
from bbcoach.data.scrapers import main as scrape_all

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
    "league": ""
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


@app.post("/api/data/fetch")
async def fetch_latest_data(background_tasks: BackgroundTasks):
    """Run the scraper in the background and return immediately."""
    global scraping_progress
    
    if scraping_progress["status"] == "fetching":
        return {"message": "Scraping is already in progress.", "status": data_service.get_data_status()}

    scraping_progress = {
        "status": "fetching",
        "current": 0,
        "total": 0,
        "team": "Initializing...",
        "league": "Starting"
    }
    
    def update_progress(team_name, current_idx, total_count, league_name):
        scraping_progress["current"] = current_idx
        scraping_progress["total"] = total_count
        scraping_progress["team"] = team_name
        scraping_progress["league"] = league_name

    def run_scraper_task():
        try:
            players_count, teams_count = scrape_all(progress_callback=update_progress)
            data_service.update_metadata()
            data_service.clear_cache()  # Force reload from disk
            scraping_progress["status"] = "idle"
        except Exception as e:
            scraping_progress["status"] = "error"
            logger.error(f"Error fetching data: {e}", exc_info=True)

    background_tasks.add_task(run_scraper_task)
    
    return {
        "message": "Scraping started in background.",
        "status": data_service.get_data_status()
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


@app.get("/api/stats/top-players", response_class=ORJSONResponse)
async def get_top_players(
    season: int, league: str = "Men", metric: str = "PPG", limit: int = 10
):
    """Get top players for a specific metric."""
    players = analytics_service.get_top_players(season, league, metric, limit)
    return {"season": season, "league": league, "metric": metric, "players": players}


@app.get("/api/stats/team/{team_id}", response_class=ORJSONResponse)
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
