#!/bin/bash
# Bot restart script with improved error handling

echo "🔄 Restarting Money Bot..."

# Kill any existing bot processes
pkill -f "python.*bot.py" 2>/dev/null || true
sleep 2

# Activate virtual environment and start bot
cd /home/pi/Documents/discord/bots/00_production/money_bot-1
source ../../../venv/bin/activate

echo "🚀 Starting Money Bot with improvements..."
echo "📊 Features:"
echo "  • Async API calls to prevent heartbeat blocking"
echo "  • Fast image processing with manual entry guidance"
echo "  • 10-15 second timeouts to keep Discord connection stable"
echo "  • DeepSeek free model for text analysis"
echo ""

python bot.py
