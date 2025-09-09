#!/bin/bash

# Health Bot Startup Script
echo "🏥 Starting Health Bot with Docker..."

# Set timezone
export TZ=Europe/Berlin

# Create logs directory if it doesn't exist
mkdir -p logs

# Set Python path
export PYTHONPATH=/app

# Start the health bot
echo "🚀 Launching Health Bot..."
echo "⏰ Scheduled for daily reports at 09:00 AM (Europe/Berlin timezone)"
echo "📊 Monitoring health data from Oura Ring"
echo "🍽️ Tracking calories from Notion database"
echo "💬 Sending reports to Discord channel"

# Run the health bot
python health_bot.py
