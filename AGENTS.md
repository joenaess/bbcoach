# AGENTS.md - Development Guidelines for BBCoach

This file provides essential information for agentic coding assistants working in this repository.

## Build, Lint, and Test Commands

### Dependencies
```bash
uv sync                    # Install project dependencies
```

### Linting
```bash
uv run ruff check          # Run linter
uv run ruff check --fix    # Auto-fix linting issues
```

### Testing
```bash
uv run pytest                      # Run all tests
uv run pytest -v                   # Run tests with verbose output
uv run pytest tests/test_storage.py::test_save_and_load_teams    # Run single test
uv run pytest tests/ -k "save"     # Run tests matching pattern
```

### Running the Application
```bash
uv run streamlit run app.py                    # Launch Streamlit app
uv run python src/bbcoach/data/scrapers.py    # Run scraper manually
```

## Code Style Guidelines

### Python Version and Tooling
- Python 3.13+ required
- Uses `uv` for package management (not pip)
- Ruff for linting (configured in pyproject.toml dev dependencies)
- Pytest for testing

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

### File Organization
- `src/bbcoach/` - Main source code
- `src/bbcoach/data/` - Data scrapers, storage, analytics
- `src/bbcoach/ai/` - AI/coach implementation
- `src/bbcoach/rag/` - RAG pipeline, vector store
- `src/bbcoach/ui/` - Streamlit UI components
- `tests/` - All test files
- `data_storage/` - Parquet data files (automated)

### Logging and Print Statements
- Use `print()` for user-facing output in the Streamlit app
- Use `logging` for backend modules (setup with `logger = logging.getLogger(__name__)`)
- Print progress for long-running operations (e.g., scrapers: "Processing Team X/Y")

### Environment Configuration
- Load environment variables with `load_dotenv()` from `python-dotenv`
- File `.env` for local secrets (API keys)
- Required keys: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (optional for local model)

### Key Dependencies
- Streamlit for UI
- Pandas for data manipulation
- PyArrow/Parquet for data storage
- Playwright for web scraping
- ChromaDB for vector storage
- Transformers/PyTorch for local AI models
- Multiple AI providers: Google Gemini, OpenAI, Anthropic, local Qwen

### Important Notes
- Local AI model (Qwen 2.5-1.5B) used as fallback when no API key provided
- Scrapers fetch basketball stats from Proballers.com
- RAG system scrapes BreakthroughBasketball.com for drills
- Support both Men's and Women's leagues
- Data includes players, teams, schedules across multiple seasons (2021-2025)
