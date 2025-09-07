#!/bin/bash

echo "🔄 Restarting Decision Bot..."
docker compose down
sleep 2
docker compose up -d

if [ $? -eq 0 ]; then
    echo "✅ Decision Bot restarted successfully!"
    echo "📋 Use 'docker compose logs -f decision-bot' to view logs"
else
    echo "❌ Failed to restart Decision Bot"
    exit 1
fi
