#!/bin/bash

# Quick restart script for Allgemeine Wohl Bot

echo "🔄 Restarting Allgemeine Wohl Bot..."

# Stop the current container
docker compose down

# Wait a moment
sleep 2

# Start it again
docker compose up -d

if [ $? -eq 0 ]; then
    echo "✅ Allgemeine Wohl Bot restarted successfully!"
    echo "📋 Use 'docker compose logs -f allgemeine-wohl-bot' to view logs"
else
    echo "❌ Failed to restart Allgemeine Wohl Bot"
    exit 1
fi
