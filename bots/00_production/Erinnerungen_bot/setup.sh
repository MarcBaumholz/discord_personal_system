#!/bin/bash

# Erinnerungen Bot Docker Setup Script

echo "📅 Erinnerungen Bot Docker Setup"
echo "==============================="

ENV_FILE="../../../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found at $ENV_FILE"
    exit 1
fi

echo "✅ .env file found"
mkdir -p logs

build_bot() {
    echo "🔨 Building Erinnerungen Bot Docker image..."
    docker build -t erinnerungen-bot:latest .
    if [ $? -eq 0 ]; then
        echo "✅ Docker image built successfully!"
    else
        echo "❌ Failed to build Docker image"
        exit 1
    fi
}

run_bot() {
    echo "🚀 Starting Erinnerungen Bot..."
    docker compose up -d
    if [ $? -eq 0 ]; then
        echo "✅ Erinnerungen Bot started successfully!"
        echo "📋 Use 'docker compose logs -f erinnerungen-bot' to view logs"
        echo "🛑 Use 'docker compose down' to stop the bot"
        echo "🔄 Use './restart_bot.sh' to restart the bot"
    else
        echo "❌ Failed to start Erinnerungen Bot"
        exit 1
    fi
}

stop_bot() {
    echo "🛑 Stopping Erinnerungen Bot..."
    docker compose down
}

restart_bot() {
    echo "🔄 Restarting Erinnerungen Bot..."
    stop_bot
    sleep 2
    run_bot
}

view_logs() {
    echo "📋 Viewing Erinnerungen Bot logs..."
    docker compose logs -f erinnerungen-bot
}

show_status() {
    echo "📊 Erinnerungen Bot Status:"
    docker compose ps
    echo ""
    echo "Container logs (last 10 lines):"
    docker compose logs --tail=10 erinnerungen-bot
}

cleanup() {
    echo "🧹 Cleaning up Erinnerungen Bot..."
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
        exit 1
        ;;
esac
