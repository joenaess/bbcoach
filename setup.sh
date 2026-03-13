#!/bin/bash
# Complete setup script for BBCoach

echo "🏀 BBCoach Complete Setup"
echo ""

# Check if Python is available
if ! command -v uv &> /dev/null; then
    echo "❌ 'uv' is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ 'node' is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Backend setup
echo "📦 Setting up backend..."
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    uv sync
else
    echo "Backend dependencies already installed"
fi

echo ""

# Frontend setup
echo "📦 Setting up frontend..."
cd web

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
else
    echo "Frontend dependencies already installed"
fi

cd ..

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           ✅ BBCoach setup complete!                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🎉 Ready to run!"
echo ""
echo "Start the services in separate terminals:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd $(pwd)"
echo "  ./start-api.sh"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd $(pwd)/web"
echo "  ./start.sh"
echo ""
echo "Then visit:"
echo "  • Frontend: http://localhost:3000"
echo "  • API Docs: http://localhost:8000/docs"
echo ""
