#!/bin/bash

# Discord Bot Docker Setup Script Template
# Replace {BOT_NAME} with your actual bot name

BOT_NAME="{BOT_NAME}"
echo "🤖 ${BOT_NAME} Bot Docker Setup"
echo "================================"

# Check if .env file exists in parent discord directory
ENV_FILE="../../../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found at $ENV_FILE"
    echo "Please create the .env file with the following variables:"
    echo "DISCORD_TOKEN=your_discord_token"
    echo "# Add other environment variables your bot needs:"
    echo "# API_KEY=your_api_key"
    echo "# DATABASE_URL=your_database_url"
    exit 1
fi

echo "✅ .env file found"

# Create necessary directories
mkdir -p logs data

# Function to build the Docker image
build_bot() {
    echo "🔨 Building ${BOT_NAME} Bot Docker image..."
    docker build -t ${BOT_NAME}-bot:latest .
    if [ $? -eq 0 ]; then
        echo "✅ Docker image built successfully!"
    else
        echo "❌ Failed to build Docker image"
        exit 1
    fi
}

# Function to run the bot
run_bot() {
    echo "🚀 Starting ${BOT_NAME} Bot..."
    docker compose up -d
    if [ $? -eq 0 ]; then
        echo "✅ ${BOT_NAME} Bot started successfully!"
        echo "📋 Use 'docker compose logs -f ${BOT_NAME}-bot' to view logs"
        echo "🛑 Use 'docker compose down' to stop the bot"
        echo "🔄 Use './restart_bot.sh' to restart the bot"
    else
        echo "❌ Failed to start ${BOT_NAME} Bot"
        exit 1
    fi
}

# Function to stop the bot
stop_bot() {
    echo "🛑 Stopping ${BOT_NAME} Bot..."
    docker compose down
    if [ $? -eq 0 ]; then
        echo "✅ ${BOT_NAME} Bot stopped successfully!"
    else
        echo "❌ Failed to stop ${BOT_NAME} Bot"
    fi
}

# Function to restart the bot
restart_bot() {
    echo "🔄 Restarting ${BOT_NAME} Bot..."
    stop_bot
    sleep 2
    run_bot
}

# Function to view logs
view_logs() {
    echo "📋 Viewing ${BOT_NAME} Bot logs (Ctrl+C to exit)..."
    docker compose logs -f ${BOT_NAME}-bot
}

# Function to show status
show_status() {
    echo "📊 ${BOT_NAME} Bot Status:"
    echo "========================"
    docker compose ps
    echo ""
    echo "Container logs (last 10 lines):"
    docker compose logs --tail=10 ${BOT_NAME}-bot
}

# Function to clean up
cleanup() {
    echo "🧹 Cleaning up ${BOT_NAME} Bot..."
    docker compose down --rmi local --volumes
    echo "✅ Cleanup completed!"
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
    *)
        echo "Usage: $0 {build|start|stop|restart|logs|status|cleanup}"
        echo ""
        echo "Commands:"
        echo "  build    - Build the Docker image"
        echo "  start    - Start the bot (run)"
        echo "  stop     - Stop the bot"
        echo "  restart  - Restart the bot"
        echo "  logs     - View bot logs in real-time"
        echo "  status   - Show current status"
        echo "  cleanup  - Stop and remove everything"
        echo ""
        echo "Example: $0 build && $0 start"
        exit 1
        ;;
esac
