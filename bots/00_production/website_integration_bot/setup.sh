#!/bin/bash

# Website Integration Bot Setup Script

echo "🤖 Website Integration Bot Setup"
echo "================================"

# Check if virtual environment exists
if [ ! -d "website_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv website_env
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source website_env/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To start the bot:"
echo "1. source website_env/bin/activate"
echo "2. python website_bot.py"
echo ""
echo "Make sure DISCORD_TOKEN is set in the main .env file!"
