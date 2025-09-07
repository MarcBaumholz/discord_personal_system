#!/bin/bash
# Setup script for Todo Bot

echo "🤖 Setting up Todo Bot..."

# Check if we're in the right directory
if [[ ! -f "todo_agent.py" ]]; then
    echo "❌ Error: Please run this script from the todo_bot directory"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "/home/pi/Documents/calories_env" ]]; then
    echo "⚠️ Virtual environment not found at /home/pi/Documents/calories_env"
    echo "Creating new virtual environment..."
    python3 -m venv /home/pi/Documents/todo_env
    ENV_PATH="/home/pi/Documents/todo_env"
else
    echo "✅ Using existing virtual environment"
    ENV_PATH="/home/pi/Documents/calories_env"
fi

# Activate virtual environment and install requirements
echo "📦 Installing requirements..."
source "$ENV_PATH/bin/activate"
pip install -r requirements.txt

# Check if .env file exists
if [[ ! -f "../.env" ]]; then
    echo "❌ Error: .env file not found at ../env"
    echo "Please make sure the .env file exists with DISCORD_TOKEN and TODOIST_API_KEY"
    exit 1
fi

# Check required environment variables
source "../.env"
if [[ -z "$DISCORD_TOKEN" ]]; then
    echo "❌ Error: DISCORD_TOKEN not set in .env file"
    exit 1
fi

if [[ -z "$TODOIST_API_KEY" ]]; then
    echo "❌ Error: TODOIST_API_KEY not set in .env file"
    exit 1
fi

# Test the bot
echo "🧪 Testing bot..."
python test_todo_bot.py

if [[ $? -eq 0 ]]; then
    echo "✅ Todo Bot setup completed successfully!"
    echo ""
    echo "To start the bot:"
    echo "  source $ENV_PATH/bin/activate"
    echo "  python todo_agent.py"
    echo ""
    echo "Or start as part of multibot system:"
    echo "  python ../start_multibot.py"
else
    echo "❌ Tests failed. Please check the configuration."
    exit 1
fi
