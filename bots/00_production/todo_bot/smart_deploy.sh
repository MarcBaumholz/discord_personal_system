#!/bin/bash
# Smart Docker Deployment for Todo Bot
# Überprüft laufende Container und startet/aktualisiert sie mit der neuesten Version

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISCORD_DIR="/home/pi/Documents/discord"
TODO_BOT_DIR="$SCRIPT_DIR"

echo "🐳 Smart Docker Deployment für Discord Todo Bot"
echo "==============================================="

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Prüfe ob Docker installiert ist
if ! command -v docker &> /dev/null; then
    log_error "Docker ist nicht installiert!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose ist nicht installiert!"
    exit 1
fi

log_success "Docker und Docker Compose verfügbar"

# Prüfe .env Datei
ENV_FILE="$DISCORD_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    log_error ".env Datei nicht gefunden: $ENV_FILE"
    exit 1
fi

# Lade Environment Variablen
set -a  # automatically export all variables
source "$ENV_FILE"
set +a

# Prüfe wichtige Environment Variablen
if [[ -z "$DISCORD_TOKEN" ]]; then
    log_error "DISCORD_TOKEN nicht in .env gesetzt"
    exit 1
fi

if [[ -z "$TODOIST_API_KEY" ]]; then
    log_error "TODOIST_API_KEY nicht in .env gesetzt"
    exit 1
fi

log_success "Environment Variablen geladen"

# Funktion: Prüfe laufende Container
check_running_containers() {
    log_info "Prüfe laufende Discord Bot Container..."
    
    # Alle laufenden Container mit "discord" oder "bot" im Namen
    RUNNING_CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -i -E "(discord|bot)" | tail -n +2 || true)
    
    if [[ -z "$RUNNING_CONTAINERS" ]]; then
        log_info "Keine Discord Bot Container laufen aktuell"
        return 0
    fi
    
    echo "Laufende Bot Container:"
    echo "$RUNNING_CONTAINERS"
    echo
    
    return 1  # Container found
}

# Funktion: Stoppe Container
stop_containers() {
    local pattern="$1"
    log_info "Stoppe Container mit Pattern: $pattern"
    
    CONTAINERS_TO_STOP=$(docker ps --format "{{.Names}}" | grep -i "$pattern" || true)
    
    if [[ -n "$CONTAINERS_TO_STOP" ]]; then
        echo "$CONTAINERS_TO_STOP" | xargs -r docker stop
        echo "$CONTAINERS_TO_STOP" | xargs -r docker rm
        log_success "Container gestoppt: $CONTAINERS_TO_STOP"
    else
        log_info "Keine Container zu stoppen gefunden"
    fi
}

# Funktion: Build Image
build_image() {
    local context_dir="$1"
    local image_name="$2"
    
    log_info "Baue Image: $image_name in $context_dir"
    
    cd "$context_dir"
    
    # Build with cache busting for latest changes
    docker build --no-cache -t "$image_name" .
    
    if [[ $? -eq 0 ]]; then
        log_success "Image $image_name erfolgreich gebaut"
        return 0
    else
        log_error "Fehler beim Bauen von $image_name"
        return 1
    fi
}

# Funktion: Start Container mit Docker Compose
start_service() {
    local compose_file="$1"
    local service_name="$2"
    
    log_info "Starte Service: $service_name mit $compose_file"
    
    if [[ ! -f "$compose_file" ]]; then
        log_error "Docker Compose Datei nicht gefunden: $compose_file"
        return 1
    fi
    
    cd "$(dirname "$compose_file")"
    docker-compose -f "$(basename "$compose_file")" up -d
    
    if [[ $? -eq 0 ]]; then
        log_success "Service $service_name gestartet"
        return 0
    else
        log_error "Fehler beim Starten von $service_name"
        return 1
    fi
}

# Funktion: Health Check
wait_for_health() {
    local container_name="$1"
    local max_wait=120  # 2 minutes
    local wait_time=0
    
    log_info "Warte auf Health Check für $container_name..."
    
    while [[ $wait_time -lt $max_wait ]]; do
        HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-health")
        
        if [[ "$HEALTH_STATUS" == "healthy" ]]; then
            log_success "$container_name ist gesund"
            return 0
        elif [[ "$HEALTH_STATUS" == "unhealthy" ]]; then
            log_warning "$container_name ist ungesund"
            # Zeige Logs
            log_info "Letzte Logs von $container_name:"
            docker logs --tail 20 "$container_name"
            return 1
        fi
        
        sleep 5
        wait_time=$((wait_time + 5))
        echo -n "."
    done
    
    echo
    log_warning "Health Check Timeout für $container_name"
    return 1
}

# Funktion: Cleanup alte Images
cleanup_images() {
    log_info "Bereinige alte Docker Images..."
    
    docker image prune -f
    
    # Entferne dangling images
    DANGLING=$(docker images -f "dangling=true" -q)
    if [[ -n "$DANGLING" ]]; then
        echo "$DANGLING" | xargs docker rmi
        log_success "Dangling Images entfernt"
    fi
}

# Hauptlogik
main() {
    log_info "Starte Smart Deployment..."
    
    # 1. Prüfe laufende Container
    check_running_containers
    HAS_RUNNING=$?
    
    # 2. Stoppe Todo Bot Container falls läuft
    stop_containers "todo"
    
    # 3. Baue neues Todo Bot Image
    if ! build_image "$TODO_BOT_DIR" "discord-todo-bot"; then
        log_error "Build fehlgeschlagen"
        exit 1
    fi
    
    # 4. Starte Todo Bot
    if ! start_service "$TODO_BOT_DIR/docker-compose.todo.yml" "todo-bot"; then
        log_error "Start fehlgeschlagen"
        exit 1
    fi
    
    # 5. Warte auf Health Check
    sleep 10  # Kurz warten bis Container startet
    wait_for_health "discord-todo-bot"
    
    # 6. Prüfe ob Hauptbots laufen sollen
    if [[ $HAS_RUNNING -eq 1 ]]; then
        log_info "Hauptbots waren vorher aktiv, aktualisiere sie auch..."
        
        # Stoppe Hauptbots
        stop_containers "discord-bots"
        
        # Baue Hauptbot Image
        if build_image "$DISCORD_DIR" "discord-bots"; then
            # Starte Hauptbots
            start_service "$DISCORD_DIR/docker-compose.yml" "discord-bots"
            sleep 10
            wait_for_health "discord-bots"
        fi
    fi
    
    # 7. Cleanup
    cleanup_images
    
    # 8. Status Report
    echo
    log_info "=== DEPLOYMENT STATUS ==="
    
    echo "Laufende Container:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -i -E "(discord|bot)" || echo "Keine Bot Container gefunden"
    
    echo
    echo "Images:"
    docker images | grep -E "(discord|bot)" || echo "Keine Bot Images gefunden"
    
    echo
    log_success "Smart Deployment abgeschlossen!"
    
    echo
    echo "📋 Nächste Schritte:"
    echo "   • Teste im Discord Channel: $WEEKLY_PLANNING_CHANNEL_ID"
    echo "   • Schreibe eine Nachricht → wird automatisch zu Todo"
    echo "   • Verwende !todo um alle Todos zu sehen"
    echo "   • Logs: docker logs discord-todo-bot"
    echo "   • Health: docker inspect discord-todo-bot"
}

# Parameter handling
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        log_info "Container Status:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -i -E "(discord|bot)" || echo "Keine Bot Container gefunden"
        echo
        log_info "Image Status:"
        docker images | grep -E "(discord|bot)" || echo "Keine Bot Images gefunden"
        ;;
    "logs")
        CONTAINER_NAME="${2:-discord-todo-bot}"
        log_info "Zeige Logs für $CONTAINER_NAME:"
        docker logs -f "$CONTAINER_NAME"
        ;;
    "stop")
        stop_containers "discord"
        stop_containers "bot"
        ;;
    "clean")
        stop_containers "discord"
        stop_containers "bot"
        cleanup_images
        ;;
    *)
        echo "Usage: $0 [deploy|status|logs|stop|clean]"
        echo "  deploy  - Full deployment (default)"
        echo "  status  - Show container status"
        echo "  logs    - Show container logs"
        echo "  stop    - Stop all bot containers"
        echo "  clean   - Stop containers and cleanup images"
        exit 1
        ;;
esac
