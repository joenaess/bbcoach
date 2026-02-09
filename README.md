# Swedish Basketball League AI Coach 🏀

**AI-powered analytics and tactical assistant for the Swedish Basketball League (SBL).**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

## 🌟 Features

### 🧠 Dual-Engine AI Coach

- **Cloud Power**: Integration with **Google Gemini 2.0 Flash** for high-speed, deep-reasoning tactical advice.
- **Local Privacy**: Fallback to **Qwen 2.5-1.5B (Local)** for offline-capable, private analysis.
- **Persona**: "Deeply Analytical Assistant Coach" that suggests specific defensive schemes (e.g., "ICE the P&R") and practice drills.

### 📊 Advanced Analytics

- **Game Predictor**:
  - **Projected Lineups**: Infers Starting 5 and Key Bench players based on minutes distributions.
  - **Multi-Season Trends**: Aggregates data from 2021-2025 to determine true program strength.
  - **Deep Stats**: Calculates **eFG%**, **Turnover Ratio**, and **3P% Efficiency**.
- **League Stats**: Historical data browser for Teams and Players.

### 🎨 Pro Interface

- **Basketball Theme**: Custom UI with SBL-inspired colors and professional layout.
- **Active Model Indicator**: Real-time display of the currently active AI model.

---

## 🚀 Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/joenaess/bbcoach.git
cd bbcoach
```

### 2. Install Dependencies

This project uses `uv` for fast package management.

```bash
uv sync
# OR standard pip
pip install -r requirements.txt
```

### 3. Configure AI (Optional)

To use the **Gemini 2.0 Flash** model, you need a Google API Key.

1. Copy the example env file:

    ```bash
    cp .env.example .env
    ```

2. Add your key to `.env`:

    ```
    GEMINI_API_KEY=your_api_key_here
    ```

*If no key is provided, the app defaults to the Local Qwen model automatically.*

### 4. Fetch Data

The scraper runs in the background to fetch stats from Proballers. To run it manually:

```bash
uv run python src/bbcoach/data/scrapers.py
```

### 5. Run the App

```bash
uv run streamlit run app.py
```

---

## 📂 Project Structure

- `src/bbcoach/data`: Scrapers and Parquet storage logic.
- `src/bbcoach/ai`: AI implementation (`coach.py`) handling Gemini/Local switching.
- `src/bbcoach/analysis.py`: Statistical engines for matchups and lineups.
- `app.py`: Main Streamlit application.

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a PR.

## 📄 License

MIT License.
