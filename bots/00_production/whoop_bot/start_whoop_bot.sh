#!/bin/bash
# WHOOP Discord Bot Startup Script

echo "🏃‍♂️ Starting WHOOP Discord Bot..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with your Discord token and WHOOP credentials"
    exit 1
fi

# Check if whoop_tokens.json exists
if [ ! -f "whoop_tokens.json" ]; then
    echo "⚠️  whoop_tokens.json not found!"
    echo "The bot will need to authenticate with WHOOP first"
fi

# Create logs directory
mkdir -p logs

# Build and start the container
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting WHOOP Discord Bot container..."
docker-compose up -d

echo "✅ WHOOP Discord Bot started!"
echo ""
echo "📊 Management Commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop bot:      docker-compose down"
echo "  Restart bot:   docker-compose restart"
echo "  Update bot:    docker-compose down && docker-compose build && docker-compose up -d"
echo ""
echo "⏰ Schedule:"
echo "  Daily WHOOP data will be sent at 12:00 AM (midnight)"
echo "  Manual commands: !whoop, !whoop_now, !whoop_schedule"
echo ""
echo "🔧 Bot Status:"
docker-compose ps
