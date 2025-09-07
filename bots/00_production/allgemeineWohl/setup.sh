#!/bin/bash

# Allgemeine Wohl Bot Docker Setup Script

echo "🤖 Allgemeine Wohl Bot Docker Setup"
echo "==================================="

# Check if .env file exists in parent discord directory
ENV_FILE="../../../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found at $ENV_FILE"
    echo "Please create the .env file with the following variables:"
    echo "DISCORD_TOKEN=your_discord_token"
    echo "NOTION_TOKEN=your_notion_token"
    echo "OPENROUTER_API_KEY=your_openrouter_api_key"
    echo "ALLGEMEINE_WOHL_CHANNEL_ID=your_channel_id"
    echo "ALLGEMEINE_WOHL_DATABASE_ID=your_database_id"
    echo "GROUND_TRUTH_DATABASE_ID=your_ground_truth_database_id"
    exit 1
fi

echo "✅ .env file found"

# Create necessary directories
mkdir -p logs

# Function to build the Docker image
build_bot() {
    echo "🔨 Building Allgemeine Wohl Bot Docker image..."
    docker build -t allgemeine-wohl-bot:latest .
    if [ $? -eq 0 ]; then
        echo "✅ Docker image built successfully!"
    else
        echo "❌ Failed to build Docker image"
        exit 1
    fi
}

# Function to run the bot
run_bot() {
    echo "🚀 Starting Allgemeine Wohl Bot..."
    docker compose up -d
    if [ $? -eq 0 ]; then
        echo "✅ Allgemeine Wohl Bot started successfully!"
        echo "📋 Use 'docker compose logs -f allgemeine-wohl-bot' to view logs"
        echo "🛑 Use 'docker compose down' to stop the bot"
        echo "🔄 Use './restart_bot.sh' to restart the bot"
    else
        echo "❌ Failed to start Allgemeine Wohl Bot"
        exit 1
    fi
}

# Function to stop the bot
stop_bot() {
    echo "🛑 Stopping Allgemeine Wohl Bot..."
    docker compose down
    if [ $? -eq 0 ]; then
        echo "✅ Allgemeine Wohl Bot stopped successfully!"
    else
        echo "❌ Failed to stop Allgemeine Wohl Bot"
    fi
}

# Function to restart the bot
restart_bot() {
    echo "🔄 Restarting Allgemeine Wohl Bot..."
    stop_bot
    sleep 2
    run_bot
}

# Function to view logs
view_logs() {
    echo "📋 Viewing Allgemeine Wohl Bot logs (Ctrl+C to exit)..."
    docker compose logs -f allgemeine-wohl-bot
}

# Function to show status
show_status() {
    echo "📊 Allgemeine Wohl Bot Status:"
    echo "============================="
    docker compose ps
    echo ""
    echo "Container logs (last 10 lines):"
    docker compose logs --tail=10 allgemeine-wohl-bot
}

# Function to clean up
cleanup() {
    echo "🧹 Cleaning up Allgemeine Wohl Bot..."
    docker compose down --rmi local --volumes
    echo "✅ Cleanup completed!"
}

# Function to backup state
backup_state() {
    echo "💾 Backing up bot state..."
    cp bot_state.json "bot_state_backup_$(date +%Y%m%d_%H%M%S).json"
    echo "✅ State backed up!"
}

# Main menu
case "$1" in
    "build")
        build_bot
        ;;
    "start"|"run")
        run_bot
        ;;
    "stop")
        stop_bot
        ;;
    "restart")
        restart_bot
        ;;
    "logs")
        view_logs
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "backup")
        backup_state
        ;;
    *)
        echo "Usage: $0 {build|start|stop|restart|logs|status|cleanup|backup}"
        echo ""
        echo "Commands:"
        echo "  build    - Build the Docker image"
        echo "  start    - Start the bot (run)"
        echo "  stop     - Stop the bot"
        echo "  restart  - Restart the bot"
        echo "  logs     - View bot logs in real-time"
        echo "  status   - Show current status"
        echo "  cleanup  - Stop and remove everything"
        echo "  backup   - Backup bot state file"
        echo ""
        echo "Example: $0 build && $0 start"
        exit 1
        ;;
esac
