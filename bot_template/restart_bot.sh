#!/bin/bash

# Quick restart script for {BOT_NAME} Bot
BOT_NAME="{BOT_NAME}"

echo "🔄 Restarting ${BOT_NAME} Bot..."

# Stop the current container
docker compose down

# Wait a moment
sleep 2

# Start it again
docker compose up -d

if [ $? -eq 0 ]; then
    echo "✅ ${BOT_NAME} Bot restarted successfully!"
    echo "📋 Use 'docker compose logs -f ${BOT_NAME}-bot' to view logs"
else
    echo "❌ Failed to restart ${BOT_NAME} Bot"
    exit 1
fi
