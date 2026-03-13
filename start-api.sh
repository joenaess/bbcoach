#!/bin/bash
# Start BBCoach API Server

echo "Starting BBCoach API Server..."

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running 'uv sync'..."
    uv sync
fi

# Start the API server
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
