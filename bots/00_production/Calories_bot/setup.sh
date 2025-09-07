#!/bin/bash

# Calories Bot Docker Setup Script

echo "🍎 Calories Bot Docker Setup"
echo "============================"

ENV_FILE="../../../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found at $ENV_FILE"
    echo "Please create the .env file with required variables"
    exit 1
fi

echo "✅ .env file found"
mkdir -p logs/errors logs/food_analysis logs/monthly_reports logs/system logs/user_activity reports

build_bot() {
    echo "🔨 Building Calories Bot Docker image..."
    docker build -t calories-bot:latest .
    if [ $? -eq 0 ]; then
        echo "✅ Docker image built successfully!"
    else
        echo "❌ Failed to build Docker image"
        exit 1
    fi
}

run_bot() {
    echo "🚀 Starting Calories Bot..."
    docker compose up -d
    if [ $? -eq 0 ]; then
        echo "✅ Calories Bot started successfully!"
        echo "📋 Use 'docker compose logs -f calories-bot' to view logs"
        echo "🛑 Use 'docker compose down' to stop the bot"
        echo "🔄 Use './restart_bot.sh' to restart the bot"
    else
        echo "❌ Failed to start Calories Bot"
        exit 1
    fi
}

stop_bot() {
    echo "🛑 Stopping Calories Bot..."
    docker compose down
}

restart_bot() {
    echo "🔄 Restarting Calories Bot..."
    stop_bot
    sleep 2
    run_bot
}

view_logs() {
    echo "📋 Viewing Calories Bot logs..."
    docker compose logs -f calories-bot
}

show_status() {
    echo "📊 Calories Bot Status:"
    docker compose ps
    echo ""
    echo "Container logs (last 10 lines):"
    docker compose logs --tail=10 calories-bot
}

cleanup() {
    echo "🧹 Cleaning up Calories Bot..."
    docker compose down --rmi local --volumes
    echo "✅ Cleanup completed!"
}

case "$1" in
    "build") build_bot ;;
    "start"|"run") run_bot ;;
    "stop") stop_bot ;;
    "restart") restart_bot ;;
    "logs") view_logs ;;
    "status") show_status ;;
    "cleanup") cleanup ;;
    *)
        echo "Usage: $0 {build|start|stop|restart|logs|status|cleanup}"
        echo ""
        echo "Commands:"
        echo "  build    - Build the Docker image"
        echo "  start    - Start the bot"
        echo "  stop     - Stop the bot"
        echo "  restart  - Restart the bot"
        echo "  logs     - View bot logs in real-time"
        echo "  status   - Show current status"
        echo "  cleanup  - Stop and remove everything"
        exit 1
        ;;
esac
