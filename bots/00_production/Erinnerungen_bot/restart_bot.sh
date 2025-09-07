#!/bin/bash

echo "🔄 Restarting Erinnerungen Bot..."
docker compose down
sleep 2
docker compose up -d

if [ $? -eq 0 ]; then
    echo "✅ Erinnerungen Bot restarted successfully!"
    echo "📋 Use 'docker compose logs -f erinnerungen-bot' to view logs"
else
    echo "❌ Failed to restart Erinnerungen Bot"
    exit 1
fi
