# FastAPI Backend for BBCoach

This directory contains the FastAPI backend that provides a RESTful API for the BBCoach basketball analytics platform.

## Overview

The API is built with:
- **FastAPI 0.135** - Modern, fast Python web framework
- **Pydantic** - Data validation using Python type annotations
- **Uvicorn** - ASGI server for production deployment
- **15 RESTful endpoints** - Complete API coverage

## Quick Start

### Installation

```bash
# From project root
uv sync
```

### Running the Server

```bash
# Using the provided script (recommended)
./start-api.sh

# Or run directly with Python
uv run python -m api.main

# Or use uvicorn directly
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Interactive Documentation

Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### Health & Status

**GET** `/health`
- Returns: `{"status": "healthy", "service": "bbcoach-api"}`
- Purpose: Health check for load balancers and monitoring

**GET** `/api/data/status`
- Returns: Data status with player/team/schedule counts
- Purpose: Check data availability and freshness

**GET** `/api/data/refresh`
- Returns: Clear cache and reload all data
- Purpose: Manual data refresh trigger

### Statistics

**GET** `/api/stats/seasons`
- Query params: `league` (Men/Women)
- Returns: Available seasons for a league
- Purpose: Get list of seasons with data

**GET** `/api/stats/teams`
- Query params: `season`, `league`
- Returns: List of teams for given season and league
- Purpose: Get team roster for season

**GET** `/api/stats/top-players`
- Query params: `season`, `league`, `metric`, `limit`
- Returns: Top N players by metric
- Purpose: Leaderboards (PPG, RPG, APG, etc.)

**GET** `/api/stats/team/{team_id}`
- Query params: `season`
- Returns: Team statistics and roster
- Purpose: Detailed team analysis

**POST** `/api/stats/compare-players`
- Body: `{ "player_names": [...], "season": 2025, "league": "Men" }`
- Returns: Comparison data for selected players
- Purpose: Player comparison tool

### Analytics

**POST** `/api/analytics/predict-matchup`
- Body: `{ "team_a_id": "...", "team_b_id": "...", "season": 2025 }`
- Returns: AI-powered matchup analysis
- Purpose: Game prediction with lineups and stats

**POST** `/api/analytics/predict-matchup-multi-season`
- Body: `{ "team_a_id": "...", "team_b_id": "..." }`
- Returns: Multi-season historical trend analysis
- Purpose: Long-term team comparison

### Coach (AI)

**POST** `/api/coach/ask`
- Body: `{ "question": "...", "context": "...", "provider": "optional" }`
- Returns: AI coach response with model info
- Purpose: Interactive coaching chat

**POST** `/api/coach/scouting-report`
- Body: `{ "opponent_name": "...", "stats_summary": "..." }`
- Returns: Generated scouting report
- Purpose: Create pre-game scouting reports

**GET** `/api/coach/model-info`
- Returns: Current AI model information
- Purpose: Check which AI provider is active

## Request/Response Models

### CoachRequest
```typescript
{
  question: string;
  context?: string;
  provider?: "gemini" | "openai" | "anthropic" | "local";
  api_key?: string;
  model_name?: string;
}
```

### MatchupRequest
```typescript
{
  team_a_id: string;
  team_b_id: string;
  season: number;
}
```

### PlayerRequest
```typescript
{
  player_names: string[];
  season: number;
  league: "Men" | "Women";
}
```

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# AI Provider API Keys
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS (Frontend domains)
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# Scraper Configuration
SCRAPER_TIMEOUT=60
SCRAPER_DELAY=1.0
MAX_CONCURRENT_REQUESTS=3

# Data Paths
DATA_DIR=data_storage
VECTOR_DB_DIR=.vectordb

# Logging
LOG_LEVEL=INFO
```

### AI Provider Priority

1. Gemini (if `GEMINI_API_KEY` set)
2. OpenAI (if `OPENAI_API_KEY` set)
3. Anthropic (if `ANTHROPIC_API_KEY` set)
4. Local Qwen 2.5-1.5B (automatic fallback if no API keys)

## Data Storage

The API uses Apache Parquet format for efficient data storage:

- **Players**: `data_storage/players.parquet`
- **Teams**: `data_storage/teams.parquet`
- **Schedule**: `data_storage/schedule.parquet`
- **Vector DB**: `.vectordb/` (ChromaDB)

Data is cached in memory via the DataService layer for performance.

## Integration

### Frontend Integration

The Next.js frontend integrates via the API client at `/lib/api-client.ts`:

```typescript
import api from '@/lib/api-client';

// Examples
const status = await api.dataStatus();
const players = await api.getTopPlayers(2025, "Men", "PPG", 10);
const analysis = await api.predictMatchup({ team_a_id, team_b_id, season: 2025 });
const response = await api.askCoach({ question, context });
```

### API Rewrites

Next.js is configured to proxy API requests:

```javascript
// next.config.js
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/api/:path*',
    },
  ];
}
```

This allows the frontend to call `/api/*` and have it proxied to the backend.

## Testing

### Manual Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# Data status
curl http://localhost:8000/api/data/status

# Get seasons
curl "http://localhost:8000/api/stats/seasons?league=Men"

# Get teams
curl "http://localhost:8000/api/stats/teams?season=2025&league=Men"

# Get top players
curl "http://localhost:8000/api/stats/top-players?season=2025&league=Men&metric=PPG&limit=10"

# Ask AI coach
curl -X POST http://localhost:8000/api/coach/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What defense should we run?","context":""}'
```

### Using the Test Script

```bash
python test_api.py
```

## Performance

- **Data Caching**: DataLoader caches Parquet data in memory
- **Lazy Loading**: AI models loaded on first use
- **Async Operations**: FastAPI handles concurrent requests efficiently
- **Optimized Parquet**: Columnar storage for fast analytics

## Error Handling

The API uses proper HTTP status codes:
- `200 OK` - Successful request
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

All endpoints return JSON responses with error messages.

## Deployment

### Production Server

```bash
# Start production server (no reload)
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .
RUN pip install uv && uv sync

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Recommended Platforms
- Railway (easy Python deployment)
- Render
- Heroku
- AWS EC2 + nginx

## Architecture

```
┌─────────────────────────────────────┐
│         FastAPI Application            │
│  ┌────────────────────────────────┐  │
│  │    Pydantic Models            │  │
│  │    (Request/Response)          │  │
│  └────────────────────────────────┘  │
│            ↓                          │
│  ┌────────────────────────────────┐  │
│  │    Service Layer               │  │
│  │  (Coach, Analytics, Data)      │  │
│  └────────────────────────────────┘  │
│            ↓                          │
│  ┌────────────────────────────────┐  │
│  │    AI Coach (Multi-provider)   │  │
│  │  - Gemini                      │  │
│  │  - OpenAI                      │  │
│  │  - Anthropic                   │  │
│  │  - Local Qwen                  │  │
│  └────────────────────────────────┘  │
│            ↓                          │
│  ┌────────────────────────────────┐  │
│  │    Data Storage                │  │
│  │    - Parquet files              │  │
│  │    - ChromaDB (RAG)            │  │
│  └────────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Dependencies

See `../pyproject.toml` for the complete list of Python dependencies.

Key dependencies:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `requests` - HTTP client (for scrapers)
- `beautifulsoup4` - HTML parsing
- `pandas` - Data manipulation
- `pyarrow` - Parquet I/O
- `transformers` - AI models
- `google-genai` - Gemini SDK
- `openai` - OpenAI SDK
- `anthropic` - Anthropic SDK
- `chromadb` - Vector database

## Development

### Running with Auto-Reload

```bash
uv run uvicorn api.main:app --reload
```

Changes to Python files will automatically trigger a server restart.

### CORS Configuration

For development, CORS allows requests from `http://localhost:3000`. In production, update `CORS_ORIGINS` to include your production frontend domain.

### Logging

Standard Python logging is configured with the level set by `LOG_LEVEL`. Logs are output to stdout for container/PM2 capture.

## License

MIT License - see ../LICENSE file for details
