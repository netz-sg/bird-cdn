#!/bin/bash
# Backend Startup Script
# 1. Setup cron for log aggregation
# 2. Start FastAPI application

set -e

echo "🚀 Starting Bird-CDN Backend..."

# Setup log aggregation cron job
if [ -f "/app/setup_tracking_cron.sh" ]; then
    echo "📊 Setting up tracking cron job..."
    bash /app/setup_tracking_cron.sh
else
    echo "⚠️  Cron setup script not found, skipping..."
fi

# Start FastAPI application
echo "🌐 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
