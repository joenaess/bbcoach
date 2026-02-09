
# Swedish Basketball League AI Coach 🏀

An AI-powered application to analyze Swedish Basketball League stats and provide coaching insights.

## Features

- **League Stats**: View historical player and team statistics.
- **Game Predictor**: Deep matchup analysis with multi-season trends and projected lineups.
- **Coach's Corner**: Chat with an AI Coach (Local Qwen2.5 or Google Gemini Flash) for tactical advice and drills.

## Setup

1. **Install dependencies**:

   ```bash
   uv sync
   ```

   (Or `uv install` depending on uv version, or just ensure `pyproject.toml` dependencies are installed).

2. **Fetch Data**:
   The scraper runs in the background to fetch data from Proballers. To run it manually:

   ```bash
   uv run python src/bbcoach/data/scrapers.py
   ```

   This will populate `data_storage/` with Parquet files.

3. **Run the App**:

   ```bash
   uv run streamlit run app.py
   ```

## Project Structure

- `src/bbcoach/data`: Scrapers and storage logic.
- `src/bbcoach/ai`: AI model wrapper.
- `app.py`: Streamlit frontend.
- `tests/`: Unit tests.
