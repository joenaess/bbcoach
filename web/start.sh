#!/bin/bash
# Start BBCoach Frontend (Next.js)

echo "🚀 Starting BBCoach Frontend..."

cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the Next.js dev server
echo "🔥 Starting development server on http://localhost:3000"
npm run dev
