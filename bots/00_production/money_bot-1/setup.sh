#!/bin/bash

# Money Bot Docker Setup Script

echo "🤖 Money Bot Docker Setup"
echo "=========================="

# Check if .env file exists in parent discord directory
ENV_FILE="../../../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found at $ENV_FILE"
    echo "Please create the .env file with the following variables:"
    echo "DISCORD_TOKEN=your_discord_token"
    echo "NOTION_TOKEN=your_notion_token"
    echo "OPENROUTER_API_KEY=your_openrouter_api_key"
    exit 1
fi

echo "✅ .env file found"

# Function to build the Docker image
build_bot() {
    echo "🔨 Building Money Bot Docker image..."
    docker build -t money-bot:latest .
    if [ $? -eq 0 ]; then
        echo "✅ Docker image built successfully!"
    else
        echo "❌ Failed to build Docker image"
        exit 1
    fi
}

# Function to run the bot
run_bot() {
    echo "🚀 Starting Money Bot..."
    docker compose up -d
    if [ $? -eq 0 ]; then
        echo "✅ Money Bot started successfully!"
        echo "📋 Use 'docker compose logs -f money-bot' to view logs"
        echo "🛑 Use 'docker compose down' to stop the bot"
    else
        echo "❌ Failed to start Money Bot"
        exit 1
    fi
}

# Function to stop the bot
stop_bot() {
    echo "🛑 Stopping Money Bot..."
    docker compose down
    echo "✅ Money Bot stopped"
}

# Function to view logs
logs_bot() {
    echo "📋 Viewing Money Bot logs..."
    docker compose logs -f money-bot
}

# Main menu
case "$1" in
    "build")
        build_bot
        ;;
    "run")
        run_bot
        ;;
    "start")
        build_bot
        run_bot
        ;;
    "stop")
        stop_bot
        ;;
    "logs")
        logs_bot
        ;;
    "restart")
        stop_bot
        build_bot
        run_bot
        ;;
    *)
        echo "Usage: $0 {build|run|start|stop|logs|restart}"
        echo ""
        echo "Commands:"
        echo "  build    - Build the Docker image"
        echo "  run      - Run the bot (image must be built first)"
        echo "  start    - Build and run the bot"
        echo "  stop     - Stop the bot"
        echo "  logs     - View bot logs"
        echo "  restart  - Stop, rebuild, and start the bot"
        exit 1
        ;;
esac
