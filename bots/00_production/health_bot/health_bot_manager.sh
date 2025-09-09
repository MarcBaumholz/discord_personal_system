#!/bin/bash

# Health Bot Docker Management Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[HEALTH BOT]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to build the Docker image
build_image() {
    print_status "Building Health Bot Docker image..."
    docker build -t health-bot .
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully!"
    else
        print_error "Failed to build Docker image!"
        exit 1
    fi
}

# Function to start the container
start_container() {
    print_status "Starting Health Bot container..."
    
    # Check if container already exists
    if docker ps -a --format "table {{.Names}}" | grep -q "health-bot"; then
        print_warning "Container already exists. Stopping and removing..."
        docker stop health-bot > /dev/null 2>&1
        docker rm health-bot > /dev/null 2>&1
    fi
    
    # Start the container
    docker-compose up -d
    if [ $? -eq 0 ]; then
        print_success "Health Bot container started successfully!"
        print_status "Container will run daily health reports at 09:00 AM"
        print_status "Check logs with: ./health_bot_manager.sh logs"
    else
        print_error "Failed to start container!"
        exit 1
    fi
}

# Function to stop the container
stop_container() {
    print_status "Stopping Health Bot container..."
    docker-compose down
    if [ $? -eq 0 ]; then
        print_success "Health Bot container stopped!"
    else
        print_error "Failed to stop container!"
        exit 1
    fi
}

# Function to show container status
show_status() {
    print_status "Health Bot Container Status:"
    echo ""
    docker ps -a --filter "name=health-bot" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    # Show health status
    if docker ps --format "{{.Names}}" | grep -q "health-bot"; then
        HEALTH_STATUS=$(docker inspect health-bot --format='{{.State.Health.Status}}' 2>/dev/null)
        if [ "$HEALTH_STATUS" = "healthy" ]; then
            print_success "Container is healthy and running!"
        elif [ "$HEALTH_STATUS" = "unhealthy" ]; then
            print_error "Container is unhealthy!"
        else
            print_warning "Container health status: $HEALTH_STATUS"
        fi
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing Health Bot logs (Press Ctrl+C to exit):"
    echo ""
    docker-compose logs -f health-bot
}

# Function to restart the container
restart_container() {
    print_status "Restarting Health Bot container..."
    stop_container
    sleep 2
    start_container
}

# Function to update the container
update_container() {
    print_status "Updating Health Bot container..."
    stop_container
    build_image
    start_container
}

# Function to show help
show_help() {
    echo "Health Bot Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build     Build the Docker image"
    echo "  start     Start the Health Bot container"
    echo "  stop      Stop the Health Bot container"
    echo "  restart   Restart the Health Bot container"
    echo "  status    Show container status"
    echo "  logs      Show container logs"
    echo "  update    Update and restart the container"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start the health bot"
    echo "  $0 logs      # View logs"
    echo "  $0 status    # Check status"
}

# Main script logic
case "$1" in
    build)
        check_docker
        build_image
        ;;
    start)
        check_docker
        start_container
        ;;
    stop)
        check_docker
        stop_container
        ;;
    restart)
        check_docker
        restart_container
        ;;
    status)
        check_docker
        show_status
        ;;
    logs)
        check_docker
        show_logs
        ;;
    update)
        check_docker
        update_container
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
