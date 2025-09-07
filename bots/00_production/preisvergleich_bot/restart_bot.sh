#!/bin/bash

echo "🔄 Restarting Preisvergleich Bot..."
docker compose down
sleep 2
docker compose up -d

if [ $? -eq 0 ]; then
    echo "✅ Preisvergleich Bot restarted successfully!"
    echo "📋 Use 'docker compose logs -f preisvergleich-bot' to view logs"
else
    echo "❌ Failed to restart Preisvergleich Bot"
    exit 1
fi
