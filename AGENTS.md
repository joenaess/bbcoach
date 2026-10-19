# AGENTS.md - Development Guidelines for BBCoach

## Architecture

Full-stack application: **Next.js 14.1 frontend** + **FastAPI backend** + **Python 3.13 services**

- Frontend: `web/` (Next.js, TypeScript, Tailwind, SWR, Zustand)
- Backend API: `api/main.py` (FastAPI with 19 REST endpoints)
- Core Services: `src/bbcoach/core/` (CoachService, AnalyticsService, DataService)
- Data/AI: `src/bbcoach/data/`, `src/bbcoach/ai/` (`coach.py`, `timestral_predictor.py`), `src/bbcoach/rag/`
- Focus Club Architecture: Anchored on **Högsbo** (`focusClub: "Högsbo"` via `resolveFocusTeam` in `web/hooks/use-app-store.ts` and canonical club matching in `src/bbcoach/analysis.py` and `src/bbcoach/ai/timestral_predictor.py`)

## Development Commands

### Initial Setup
```bash
./setup.sh                    # One-time setup (both backend + frontend)
```

### Backend (FastAPI)
```bash
./start-api.sh                # Start development server (auto-reload)
# or manually:
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Next.js)
```bash
cd web && npm run dev         # Start dev server on localhost:3000
cd web && npm run build       # Production build
cd web && npm run lint        # Frontend linting
```

### Testing
```bash
uv run pytest                 # Run all unit & API tests (35 tests)
uv run pytest -v              # Verbose output
uv run pytest -m integration  # Run live external network integration tests
uv run pytest tests/test_storage.py::test_save_and_load_teams  # Single test
uv run pytest tests/ -k "save"  # Tests matching pattern
```

### Linting
```bash
uv run ruff check             # Check Python code
uv run ruff check --fix       # Auto-fix issues
```

## Code Style Guidelines

### Python Version and Tooling
- Python 3.13 required (specified in .python-version)
- Uses `uv` for package management (not pip)
- Ruff for linting, Pytest for testing

### Imports
- Standard library imports first, then third-party, then local (`from bbcoach.*`)
- Use `# noqa: E402` for imports after code/statements
- Add `sys.path.append(os.path.abspath("src"))` before local imports in test files and scripts
- Lazy load heavy modules (AI models) when possible to avoid long startup times

### Type Hints
- Use modern type hints: `list[dict]`, `dict[str, str]`, not `List[Dict]`
- Always annotate function parameters and return types
- Examples: `def save_teams(teams_data: list[dict]) -> None`, `def load_players() -> pd.DataFrame`

### Naming Conventions
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE` (e.g., `LOCAL_MODEL_NAME`, `DATA_DIR`)
- Be descriptive: `get_team_aggregates`, `predict_matchup_multi_season`

### Formatting
- 4-space indentation
- Double quotes for strings
- One blank line between functions (two recommended for function groups)
- Max line length ~100-120 characters (be reasonable)

### Error Handling
- Use `try-except` blocks for operations that may fail (file I/O, parsing, network)
- Catch `Exception` broadly when appropriate, add context to error messages
- Return empty DataFrames (`pd.DataFrame()`) or `None` on errors in core functions
- Use `continue` in loops to skip bad data rather than crash

### Data Handling (Pandas)
- Always check `if not df.empty:` before DataFrame operations
- Check column existence: `if "column_name" not in df.columns:`
- Use `.loc[]` or `.iloc[]` for DataFrame indexing
- Chain method calls for readability: `players_df[players_df["season"] == season].sort_values("PPG", ascending=False)`
- Store data in Parquet format in `data_storage/` directory

### Testing
- Use pytest fixtures for setup/teardown: `@pytest.fixture`
- Fixtures commonly yield resources and handle cleanup
- Add test files to `tests/` directory, named `test_*.py`
- Import test modules without `bbcoach.` prefix when path is added
- Test function names: `test_` prefix describing what is tested
- API tests: Add both `sys.path.append(os.path.abspath("src"))` and `sys.path.append(os.path.abspath("."))` to import FastAPI app
- API tests mock DataService methods to avoid requiring existing Parquet files

### File Organization
- `src/bbcoach/` - Main source code
- `src/bbcoach/data/` - Data scrapers, storage, analytics
- `src/bbcoach/ai/` - AI/coach implementation & `Timestral-209M` probabilistic forecaster
- `src/bbcoach/rag/` - RAG pipeline, vector store
- `tests/` - All test files
- `data_storage/` - Parquet data files (automated)

### Logging and Print Statements
- Use `logging` for backend modules (setup with `logger = logging.getLogger(__name__)`)
- Print progress for long-running operations (e.g., scrapers: "Processing Team X/Y")

### Environment Configuration
- Load environment variables with `load_dotenv()` from `python-dotenv`
- File `.env` for local secrets (API keys)
- Required keys: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (optional for local model)

### Key Dependencies
- Playwright for web scraping
- PyArrow/Parquet for data storage
- ChromaDB for vector storage
- Transformers/PyTorch & `timestral` (`mistralai/Timestral-209M`) for local AI & time-series forecasting
- Multiple AI providers: Google Gemini, OpenAI, Anthropic, local Qwen

### Important Notes
- Local AI model (Qwen 2.5-1.5B) used as fallback when no API key provided
- `Timestral-209M` (`src/bbcoach/ai/timestral_predictor.py`) provides 21-quantile score forecasts, win probabilities, and What-If tactical simulations with automatic CUDA-to-CPU fallback
- Scrapers fetch basketball stats and schedules from Genius Sports across `2024–2026` (`SBL Herr` and `SBL Dam`)
- RAG system scrapes BreakthroughBasketball.com for drills
- Support both Men's and Women's leagues with canonical cross-season club resolution (e.g., `Högsbo Basket` $\leftrightarrow$ `Högsbo Lions`)
