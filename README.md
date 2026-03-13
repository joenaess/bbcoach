# BBCoach 🏀

**AI-powered analytics and tactical assistant for the Swedish Basketball League (SBL).**

[![Next.js](https://img.shields.io/badge/Next.js-14.1-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)](https://www.typescriptlang.org/)

## 🌟 Features

### 🧠 AI Coach
- **Multiple AI Providers**: Gemini 2.0 Flash, OpenAI GPT-4o, Anthropic Claude, or local Qwen 2.5-1.5B
- **Interactive Chat**: Ask tactical questions, get play suggestions, scouting reports
- **Knowledge Base**: Integration with basketball drills and plays library
- **Export Conversations**: Save coaching sessions to Markdown

### 📊 Advanced Analytics
- **Game Predictor**: AI-powered matchup analysis with projected lineups
- **Multi-Season Trends**: Analyze historical data from 2021-2025
- **Player Comparison**: Side-by-side statistical comparison with visual charts
- **League Statistics**: Top players by any metric (PPG, RPG, APG, 3P%, etc.)
- **Team Statistics**: Aggregated team stats and roster analysis

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
│  │             │  │  Chat        │  │             │              │
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
│  │  (15 REST)  │  │   (Business) │  │  (Parquet)  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Config    │  │  AI Coach   │  │  Scrapers   │              │
│  │   Layer     │  │  (Multiple) │  │  (Genius)   │              │
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
- Select any two teams
- Single season matchup analysis
- Multi-season historical trends
- Tabbed interface
- Formatted AI analysis display

### 5. AI Coach (`/coach`)
- Interactive chat interface
- Ask tactical questions
- Get play suggestions
- Generate scouting reports
- Context sidebar with team info
- Export conversation to Markdown
- Message history

### 6. Player Comparison (`/comparison`)
- Select 2 players from roster
- Side-by-side metric comparison
- Visual comparison bars
- Additional stats summary

### 7. Schedule (`/schedule`)
- Team selector
- View team roster
- Player statistics display
- Key player identification

---

## 📡 API Documentation

### Available Endpoints

**Health & Data:**
- `GET /health` - Health check
- `GET /api/data/status` - Data file status
- `GET /api/data/refresh` - Clear and reload data cache

**Statistics:**
- `GET /api/stats/seasons` - Get available seasons
- `GET /api/stats/teams` - Get teams for season
- `GET /api/stats/top-players` - Get top players by metric
- `GET /api/stats/team/{team_id}` - Get team statistics
- `POST /api/stats/compare-players` - Compare multiple players

**Analytics:**
- `POST /api/analytics/predict-matchup` - Predict matchup (single season)
- `POST /api/analytics/predict-matchup-multi-season` - Predict matchup (multi-season)

**Coach (AI):**
- `POST /api/coach/ask` - Ask the AI coach a question
- `POST /api/coach/scouting-report` - Generate scouting report
- `GET /api/coach/model-info` - Get current model information

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

The app will use the first available API key in this order:
1. Gemini (if `GEMINI_API_KEY` is set)
2. OpenAI (if `OPENAI_API_KEY` is set)
3. Anthropic (if `ANTHROPIC_API_KEY` is set)
4. Local Qwen model (automatic fallback)

### Data Configuration

- **Data Directory**: `data_storage/` (Parquet files)
- **Vector DB**: `.vectordb/` (ChromaDB)
- **Competitions**: Configured in `src/bbcoach/config/settings.py`

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/test_storage.py::test_save_and_load_teams

# Run tests matching pattern
uv run pytest tests/ -k "save"
```

### Linting

```bash
# Check code
uv run ruff check

# Auto-fix issues
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
│   ├── main.py                # API application with 15 endpoints
│   └── README.md              # API documentation
│
├── src/bbcoach/               # Python modules
│   ├── config/                # Configuration management
│   │   └── settings.py        # Pydantic settings
│   ├── core/                  # Business logic layer
│   │   ├── coach_service.py   # AI coach operations
│   │   ├── analytics_service.py # Statistics & predictions
│   │   └── data_service.py    # Data management
│   ├── ai/                    # AI coach implementation
│   │   └── coach.py          # Multi-provider AI coach
│   ├── data/                  # Data operations
│   │   ├── storage.py         # Parquet data storage
│   │   ├── scrapers.py        # Main scraper orchestrator
│   │   ├── genius_scraper.py  # Genius Sports scraper
│   │   └── analytics.py      # Statistical analysis
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
│   │   ├── predictor/         # Game predictor
│   │   ├── coach/             # AI coach chat
│   │   ├── comparison/        # Player comparison
│   │   ├── schedule/          # Schedule page
│   │   ├── not-found.tsx      # 404 page
│   │   └── ...
│   ├── components/ui/         # UI components
│   ├── hooks/                # React hooks
│   │   ├── use-api.ts         # SWR data hooks
│   │   └── use-app-store.ts   # Zustand global state
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
├── data_storage/              # Parquet data files
├── .vectordb/                 # ChromaDB vector store
├── tests/                     # Test files test_*.py
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

- **Players**: 342+ (Men's and Women's leagues)
- **Teams**: 24+ across multiple seasons
- **Games**: 642+ in schedule
- **Seasons**: 2021-2025

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

### v2.0.0 (Current) - Architecture Migration
- ✅ Migrated from Streamlit monolith to Next.js + FastAPI
- ✅ Added RESTful API with 15 endpoints
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
