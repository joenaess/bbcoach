# BBCoach 🏀

**AI-powered analytics and tactical assistant for the Swedish Basketball League (SBL).**

[![Next.js](https://img.shields.io/badge/Next.js-14.1-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)](https://www.typescriptlang.org/)

## 🌟 Features

### 🧠 AI Coach & Högsbo Focus Club Architecture
- **Högsbo Primary Focus Club**: Anchored by default on **Högsbo** (`Högsbo Lions` / `Högsbo Basket`), automatically resolving Genius Sports' competition-specific team IDs across seasons (`2024–2026`) and leagues (`SBL Herr` Men & `SBL Dam` Women)
- **Schedule-Grounded AI Coach**: Automatically injects Högsbo's upcoming 4-game `Timestral-209M` schedule forecast (`win_probability`, `expected_score`, `coaching_note`) into AI coaching queries and practice planning
- **Multiple AI Providers**: Gemini 2.0 Flash, OpenAI GPT-4o, Anthropic Claude, or local Qwen 2.5-1.5B fallback
- **Knowledge Base**: RAG integration with basketball drills and plays library
- **Export Conversations**: Save coaching sessions and tactical game plans to Markdown

### 📊 Advanced Analytics & `Timestral-209M` Time-Series Forecasting
- **Timestral-209M Probabilistic Forecaster**: Zero-shot 21-quantile score, spread, win probability, and trajectory fan-chart forecasting powered by [`mistralai/Timestral-209M`](https://huggingface.co/mistralai/Timestral-209M) conditioned on known future covariates (home/away, opponent offensive/defensive ratings, and categorical opponent target-encoding) with automatic CUDA-to-CPU fallback
- **Coach's Tactical Brief & "What-If" Simulator**: Translates 21-quantile score distributions into game dynamics (`Shootout Alert`, `Grind-It-Out`, `High Variance`), blow-out/clutch probabilities, and interactive tactical sliders (Pace Control, Offensive Execution `+3% 3P%`, Defensive Scheme `-2 TOV`)
- **2026–2027 SBL Season Support**: Full rosters, team statistics, and 2026–2027 schedules for both `SBL Herr` (Men, ID `48974`) and `SBL Dam` (Women, ID `49288`), alongside historical 2024–2025 data
- **Historical Backtest Evaluation**: Built-in evaluation comparing `Timestral-209M` against Rolling-5 and Season Average baselines (**70.0% win accuracy** on SBL Herr and **70.4% win accuracy** on SBL Dam)
- **Player Comparison & League Statistics**: Side-by-side statistical comparison, top players by metric, and team roster rotation analytics

### 🎨 Modern Interface
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark Theme**: Professional basketball-themed dark mode
- **Real-time Data**: Live data fetching with SWR caching
- **Type-Safe**: Full TypeScript type safety throughout

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Landing    │  │  Dashboard  │  │  Stats      │              │
│  │  Page       │  │             │  │             │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Predictor  │  │  AI Coach    │  │  Comparison │              │
│  │ (Timestral) │  │  (Högsbo)   │  │             │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ API (REST + SWR)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + Python)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  API Layer  │  │   Services  │  │    Data     │              │
│  │  (19 REST)  │  │   (Business) │  │  (Parquet)  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Config    │  │  AI / TS    │  │  Scrapers   │              │
│  │   Layer     │  │ (Timestral) │  │  (Genius)   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │             Vector Database (ChromaDB)                       │   │
│  │              (Drills & Plays Knowledge)                     │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 14.1 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS + Custom dark theme
- **Components**: Radix UI primitives (shadcn/ui style)
- **State Management**: Zustand
- **Data Fetching**: SWR
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Charts**: Recharts, Plotly.js

### Backend
- **Framework**: FastAPI 0.135
- **Language**: Python 3.13+
- **Package Manager**: uv
- **Data Format**: Parquet (PyArrow)
- **Vector DB**: ChromaDB
- **AI Models**: 
  - Google Gemini (cloud)
  - OpenAI (cloud)
  - Anthropic Claude (cloud)
  - Qwen 2.5-1.5B (local)

---

## 📦 Installation

### Prerequisites

- **Node.js** 18+ and npm/yarn/pnpm
- **Python** 3.13+
- **uv** package manager (recommended)

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/joenaess/bbcoach.git
   cd bbcoach
   ```

2. **One-command setup** (recommended)
   ```bash
   ./setup.sh
   ```
   This will:
   - Install Python dependencies
   - Install Node.js dependencies
   - Set up the environment

### Manual Setup

**Backend Setup:**
   ```bash
   # Install Python dependencies
   uv sync
   ```

**Frontend Setup:**
   ```bash
   cd web
   npm install
   cd ..
   ```

---

## 🚀 Running the Application

### Start Both Services

You need two terminal windows:

**Terminal 1 - Backend:**
   ```bash
   ./start-api.sh
   ```

**Terminal 2 - Frontend:**
   ```bash
   cd web && ./start.sh
   # OR
   cd web && npm run dev
   ```

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 🎯 Features & Pages

### 1. Landing Page (`/`)
- Feature overview with 6 cards
- Professional hero section
- Quick links to all pages

### 2. Dashboard (`/dashboard`)
- Real-time data status
- Stat cards (Players, Teams, Games, Seasons)
- Quick action buttons
- Data refresh capability

### 3. League Statistics (`/stats`)
- Top players by any metric
- League toggle (Men/Women)
- Season selector
- Metric selector (PPG, RPG, APG, 3P%, FG%, EFF, etc.)
- Player leaderboards with GP and MIN

### 4. Game Predictor (`/predictor`)
- **Högsbo-Anchored Workflow**: Defaults to **Högsbo** (`Högsbo Lions` / `Högsbo Basket`) as the Primary Focus Team and auto-selects Högsbo's next scheduled 2026–2027 opponent on load
- **Next 2026–2027 Game Spotlight & Opponent Quick-Select**: 1-click chips for upcoming scheduled opponents with live `Timestral-209M` win probabilities
- **Timestral-209M Probabilistic Forecast**: 21-quantile score distributions (`P10`–`P90`), win probability gauge, and trajectory fan charts (`Recharts`)
- **Coach's Tactical Brief & "What-If" Simulator**: Interactive sliders for Pace, Offensive Boost (`+3% 3P%`), and Defensive Scheme (`-2 TOV`), plus 1-click AI Coach Game Plan generation
- **Multi-Season & Historical Backtest Tabs**: Cross-season trend comparison (`2024–2026`) and live `Timestral-209M` historical evaluation vs baselines

### 5. AI Coach (`/coach`)
- **Högsbo Primary Focus Team**: Automatically resolves Högsbo across `SBL Herr` and `SBL Dam` and injects the upcoming 4-game `Timestral-209M` schedule forecast into every coaching query
- **Interactive Chat & Quick Actions**: Generate opponent scouting reports, offensive/defensive strategies, and practice plans grounded in real stats
- **Export Conversation**: Save sessions to Markdown

### 6. Player Comparison (`/comparison`)
- Select 2 players from roster
- Side-by-side metric comparison
- Visual comparison bars
- Additional stats summary

### 7. Schedule (`/schedule`)
- Auto-selects **Högsbo** on load across leagues and seasons
- View team game schedule (opponent, home/away, date, result)
- Fallback to team rotation & key player statistics when schedule data is pending

---

## 📡 API Documentation

### Available Endpoints (19 REST Routes)

**Health & Data:**
- `GET /health` - Health check
- `GET /api/data/status` - Data file status and last-fetched timestamp
- `GET /api/data/refresh` - Clear and reload data cache
- `POST /api/data/fetch` - Trigger background Genius Sports data & schedule scraping
- `GET /api/data/fetch-progress` - Poll live background scraping progress

**Statistics:**
- `GET /api/stats/seasons` - Get available seasons for a league
- `GET /api/stats/teams` - Get teams for a season and league
- `GET /api/stats/top-players` - Get top players by metric
- `GET /api/stats/team/{team_id}` - Get aggregated team statistics and rotation
- `GET /api/stats/schedule/{team_id}` - Get team game schedule
- `POST /api/stats/compare-players` - Compare multiple players side-by-side

**Analytics & Timestral-209M Forecasting:**
- `POST /api/analytics/predict-matchup` - Predict matchup (single season)
- `POST /api/analytics/predict-matchup-multi-season` - Predict matchup (multi-season across canonical club IDs)
- `GET /api/analytics/timestral/forecast/{team_id}` - Forecast upcoming 2026–2027 games with 21-quantile intervals via `Timestral-209M`
- `POST /api/analytics/timestral/matchup` - Probabilistic head-to-head matchup forecast & Coach's Tactical Brief via `Timestral-209M` (supports What-If adjustments)
- `GET /api/analytics/timestral/evaluate` - Evaluate `Timestral-209M` on held-out historical SBL games vs baselines

**Coach (AI):**
- `POST /api/coach/ask` - Ask the AI coach a question (with optional team/season context)
- `POST /api/coach/scouting-report` - Generate an opponent scouting report
- `GET /api/coach/model-info` - Get current AI model information

Interactive API documentation is available at http://localhost:8000/docs

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# AI Provider API Keys (Optional - falls back to local model)
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS (for frontend)
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# Scraper
SCRAPER_TIMEOUT=60
SCRAPER_DELAY=1.0
```

### AI Provider Priority

The app will use the configured provider in `Settings` (or per-request override):
1. Gemini (if `GEMINI_API_KEY` is set)
2. OpenAI (if `OPENAI_API_KEY` is set)
3. Anthropic (if `ANTHROPIC_API_KEY` is set)
4. Local Qwen 2.5-1.5B model (automatic fallback, lazy-loaded on first inference)

### Data Configuration

- **Data Directory**: `data_storage/` (Parquet files: `players.parquet`, `teams.parquet`, `schedule.parquet`, `metadata.json`)
- **Vector DB**: `.vectordb/` (ChromaDB)
- **Competitions**: Configured in `src/bbcoach/config/settings.py` and `src/bbcoach/data/scrapers.py` (includes 2024–2025, 2025–2026, and 2026–2027 `SBL Herr` and `SBL Dam`)

---

## 🧪 Development

### Running Tests

Tests are configured in `pyproject.toml` and isolated from `data_storage/` using temporary directories and mocks.

```bash
# Run all unit and API tests (35 tests; excludes live external network tests by default)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run live network integration tests explicitly
uv run pytest -m integration

# Run specific test file or test case
uv run pytest tests/test_api.py
uv run pytest tests/test_services_and_analysis.py
uv run pytest tests/test_storage.py::test_save_and_load_teams

# Run tests matching pattern
uv run pytest tests/ -k "timestral"
```

### Linting

Ruff is configured in `pyproject.toml` (`target-version = "py313"`, `line-length = 120`, rules `E`, `F`, `W`, `I`):

```bash
# Check Python code
uv run ruff check

# Auto-fix linting and import sorting issues
uv run ruff check --fix
```

### Backend Development

```bash
# Start with auto-reload
./start-api.sh

# Or manually
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd web

# Start dev server
npm run dev

# Type check
npx tsc --noEmit

# Build production
npm run build

# Start production
npm start

# Lint
npm run lint
```

### Project Structure

```
bbcoach/
├── api/                        # FastAPI backend
│   ├── main.py                # API application with 19 endpoints
│   └── README.md              # API documentation
│
├── src/bbcoach/               # Python modules
│   ├── config/                # Configuration management
│   │   └── settings.py        # Pydantic settings
│   ├── core/                  # Business logic layer
│   │   ├── coach_service.py   # AI coach operations
│   │   ├── analytics_service.py # Statistics, predictions & Timestral integration
│   │   └── data_service.py    # Data management
│   ├── ai/                    # AI & Time-Series models
│   │   ├── coach.py           # Multi-provider AI coach
│   │   └── timestral_predictor.py # Timestral-209M probabilistic forecaster
│   ├── data/                  # Data operations
│   │   ├── storage.py         # Parquet data storage
│   │   ├── scrapers.py        # Main scraper orchestrator
│   │   ├── genius_scraper.py  # Genius Sports scraper (stats + schedules)
│   │   └── analytics.py       # Statistical analysis
│   └── rag/                   # RAG pipeline
│       ├── pipeline.py        # RAG orchestration
│       └── vector_store.py    # ChromaDB integration
│
├── web/                        # Next.js frontend
│   ├── app/                   # Next.js App Router
│   │   ├── page.tsx           # Landing page
│   │   ├── layout.tsx         # Root layout
│   │   ├── globals.css        # Global styles
│   │   ├── dashboard/         # Dashboard page
│   │   ├── stats/             # Stats page
│   │   ├── predictor/         # Game predictor & Timestral-209M Coach Simulator
│   │   ├── coach/             # AI coach chat (Högsbo focus)
│   │   ├── comparison/        # Player comparison
│   │   ├── schedule/          # Schedule page
│   │   ├── not-found.tsx      # 404 page
│   │   └── ...
│   ├── components/ui/         # UI components
│   ├── hooks/                # React hooks
│   │   ├── use-api.ts         # SWR data hooks
│   │   └── use-app-store.ts   # Zustand global state & Högsbo focus resolver
│   ├── lib/                  # Utilities
│   │   ├── api-client.ts      # Axios API client
│   │   └── utils.ts           # Helper functions
│   ├── types/                # TypeScript types
│   │   └── api.ts             # API type definitions
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── README.md
│
├── data_storage/              # Parquet data files (players, teams, schedule)
├── .vectordb/                 # ChromaDB vector store
├── tests/                     # Test files test_*.py (35 unit/API + 1 integration)
├── app.py                     # Legacy Streamlit (deprecated)
├── start-api.sh              # Start backend script
├── setup.sh                  # Complete setup script
├── MIGRATION.md              # Migration documentation
├── AGENTS.md                 # Development guides
└── README.md                 # This file
```

---

## 🚢 Deployment

### Deployment Options

**Frontend:**
- Vercel (recommended for Next.js)
- Netlify
- Railway
- AWS Amplify

**Backend:**
- Railway (recommended)
- Render
- AWS (EC2 + nginx)
- Google Cloud Run

### Environment Setup for Production

1. **Backend:**
   - Set environment variables
   - Build with: `uv run uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - Ensure `CORS_ORIGINS` includes your frontend domain

2. **Frontend:**
   - Update `next.config.js` to point to production API
   - Set `NEXT_PUBLIC_API_URL` if needed
   - Build: `npm run build`
   - Start: `npm start`

### Docker Deployment (Optional)

**Backend Dockerfile:**
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .
RUN pip install uv && uv sync

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY web/package*.json ./
RUN npm install

COPY web .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

---

## 📊 Current Data Status

- **Players**: 904 player-season records (`SBL Herr` Men's and `SBL Dam` Women's leagues)
- **Teams**: 68 team entries across seasons (with canonical cross-season club resolution)
- **Games**: 2,760 scheduled and completed games (including 638 fixtures for `2026–2027`)
- **Seasons**: `2024–2025`, `2025–2026`, and `2026–2027`

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Follow the code style guidelines in `AGENTS.md`
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

### Code Style

- **Python**: Use `uv run ruff check` and `uv run ruff check --fix`
- **TypeScript**: Use `npm run lint`
- See `AGENTS.md` for detailed guidelines

---

## 📜 Changelog

### v2.1.0 (Current) - Timestral-209M Forecasting, 2026–2027 Season & Högsbo Focus
- ✅ Integrated [`mistralai/Timestral-209M`](https://huggingface.co/mistralai/Timestral-209M) zero-shot probabilistic time-series forecasting (`70.0%` SBL Herr & `70.4%` SBL Dam backtest win accuracy)
- ✅ Scraped full `2026–2027` SBL Herr (`48974`) and SBL Dam (`49288`) rosters, team stats, and schedules (`2,760` total games)
- ✅ Added Coach's Tactical Brief, Interactive "What-If" Coaching Simulator, and 1-click AI Coach Game Plan generator in `/predictor`
- ✅ Anchored UX and cross-season analytics around **Högsbo** (`Högsbo Lions` / `Högsbo Basket`) across Men's and Women's leagues

### v2.0.0 - Architecture Migration
- ✅ Migrated from Streamlit monolith to Next.js + FastAPI
- ✅ Added RESTful API with 16 endpoints
- ✅ Implemented modern frontend with 6 functional pages
- ✅ Added TypeScript for type safety
- ✅ Integrated SWR for data caching
- ✅ Added Zustand for state management
- ✅ Implemented AI coach with multiple providers
- ✅ Added game predictor with multi-season analysis
- ✅ Created player comparison tool
- ✅ Added export functionality

### v1.0.0 - Original Streamlit Version
- Basic statistics
- Game predictions
- AI coaching chat
- RAG integration

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **Data**: Statistics scraped from Genius Sports
- **AI Models**: Google Gemini, OpenAI, Anthropic, Qwen (local)
- **Knowledge Base**: Basketball drills from Breakthrough Basketball
- **UI Components**: shadcn/ui, Radix UI, Lucide icons

---

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check the API documentation at `/docs` when the backend is running
- Review `AGENTS.md` for development guidelines

---

## 🌟 Star History

If you find this project helpful, please consider giving it a star! ⭐

---

**Built with ❤️ for Swedish basketball coaches and analysts**
