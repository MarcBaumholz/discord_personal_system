#!/bin/bash

echo "🔄 Restarting Calories Bot..."
docker compose down
sleep 2
docker compose up -d

if [ $? -eq 0 ]; then
    echo "✅ Calories Bot restarted successfully!"
    echo "📋 Use 'docker compose logs -f calories-bot' to view logs"
else
    echo "❌ Failed to restart Calories Bot"
    exit 1
fi
