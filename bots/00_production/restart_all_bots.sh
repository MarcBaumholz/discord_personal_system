#!/bin/bash
# Complete Bot Restart & Update Script
# Startet alle Discord Bots neu mit neuester Version und Startnachrichten

set -e

echo "🤖 Discord Bots Complete Restart & Update"
echo "======================================="

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_header() { echo -e "${PURPLE}🚀 $1${NC}"; }

# Bot Verzeichnisse definieren
declare -A BOT_CONFIGS
BOT_CONFIGS=(
    ["todo-bot"]="/home/pi/Documents/discord/bots/00_production/todo_bot"
    ["calories-bot"]="/home/pi/Documents/discord/bots/00_production/Calories_bot"
    ["money-bot"]="/home/pi/Documents/discord/bots/00_production/money_bot-1"
    ["erinnerungen-bot"]="/home/pi/Documents/discord/bots/00_production/Erinnerungen_bot"
    ["tagebuch-bot"]="/home/pi/Documents/discord/bots/00_production/Tagebuch_bot"
    ["preisvergleich-bot"]="/home/pi/Documents/discord/bots/00_production/preisvergleich_bot"
    ["allgemeine-wohl-bot"]="/home/pi/Documents/discord/bots/00_production/allgemeineWohl"
)

# Funktion: Container stoppen
stop_all_bots() {
    log_header "Stoppe alle Bot Container..."
    
    RUNNING_BOTS=$(docker ps --format "{{.Names}}" | grep -E "(discord|bot)" || true)
    
    if [[ -n "$RUNNING_BOTS" ]]; then
        echo "$RUNNING_BOTS" | while read bot; do
            log_info "Stoppe $bot..."
            docker stop "$bot" || true
            docker rm "$bot" || true
        done
        log_success "Alle Bots gestoppt"
    else
        log_info "Keine Bots zu stoppen"
    fi
}

# Funktion: Images bauen
build_bot_images() {
    log_header "Baue neue Bot Images..."
    
    for bot_name in "${!BOT_CONFIGS[@]}"; do
        bot_dir="${BOT_CONFIGS[$bot_name]}"
        
        if [[ -d "$bot_dir" ]] && [[ -f "$bot_dir/Dockerfile" ]]; then
            log_info "Baue Image für $bot_name..."
            
            cd "$bot_dir"
            
            # Bestimme Image Namen
            if [[ "$bot_name" == "todo-bot" ]]; then
                image_name="discord-todo-bot"
            else
                image_name="${bot_name//-/_}_${bot_name}"
            fi
            
            # Build mit no-cache für frische Version
            docker build --no-cache -t "$image_name" . > /dev/null 2>&1
            
            if [[ $? -eq 0 ]]; then
                log_success "Image $image_name gebaut"
            else
                log_error "Fehler beim Bauen von $image_name"
            fi
        else
            log_warning "Kein Dockerfile für $bot_name in $bot_dir"
        fi
    done
}

# Funktion: Bot starten
start_bot() {
    local bot_name="$1"
    local bot_dir="$2"
    
    log_info "Starte $bot_name..."
    
    if [[ ! -d "$bot_dir" ]]; then
        log_error "Bot Verzeichnis nicht gefunden: $bot_dir"
        return 1
    fi
    
    cd "$bot_dir"
    
    # Suche nach docker-compose Datei
    COMPOSE_FILE=""
    if [[ -f "docker-compose.yml" ]]; then
        COMPOSE_FILE="docker-compose.yml"
    elif [[ -f "docker-compose.todo.yml" ]]; then
        COMPOSE_FILE="docker-compose.todo.yml"
    elif [[ -f "docker-compose.${bot_name}.yml" ]]; then
        COMPOSE_FILE="docker-compose.${bot_name}.yml"
    fi
    
    if [[ -n "$COMPOSE_FILE" ]]; then
        # Mit Docker Compose starten
        docker-compose -f "$COMPOSE_FILE" up -d --build > /dev/null 2>&1
        
        if [[ $? -eq 0 ]]; then
            log_success "$bot_name mit Docker Compose gestartet"
        else
            log_error "Fehler beim Starten von $bot_name mit Docker Compose"
            return 1
        fi
    else
        # Fallback: Direkt mit Docker starten
        log_warning "Kein docker-compose.yml für $bot_name, verwende direkten Docker start"
        
        # Bestimme Container Namen und Image
        container_name="discord-$bot_name"
        image_name="${bot_name//-/_}_${bot_name}"
        
        docker run -d \
            --name "$container_name" \
            --env-file "/home/pi/Documents/discord/bots/00_production/.env" \
            --restart unless-stopped \
            "$image_name" > /dev/null 2>&1
        
        if [[ $? -eq 0 ]]; then
            log_success "$bot_name direkt mit Docker gestartet"
        else
            log_error "Fehler beim direkten Docker Start von $bot_name"
            return 1
        fi
    fi
    
    return 0
}

# Funktion: Warten auf Bot Health
wait_for_bot_health() {
    local bot_name="$1"
    local container_name="discord-$bot_name"
    local max_wait=60
    local wait_time=0
    
    log_info "Warte auf Gesundheitsstatus für $bot_name..."
    
    while [[ $wait_time -lt $max_wait ]]; do
        # Prüfe ob Container läuft
        if docker ps --format "{{.Names}}" | grep -q "$container_name\|$bot_name"; then
            # Prüfe Health Status (falls verfügbar)
            HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-health")
            
            if [[ "$HEALTH_STATUS" == "healthy" ]] || [[ "$HEALTH_STATUS" == "no-health" ]]; then
                log_success "$bot_name ist bereit"
                return 0
            fi
        fi
        
        sleep 2
        wait_time=$((wait_time + 2))
        echo -n "."
    done
    
    echo
    log_warning "$bot_name Health Check Timeout"
    return 1
}

# Funktion: Status anzeigen
show_final_status() {
    log_header "Final Status Report"
    
    echo "Laufende Bot Container:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -E "(discord|bot)" || echo "Keine Bot Container gefunden"
    
    echo
    echo "Bot Images:"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | grep -E "(discord|bot)" | head -10
    
    echo
    log_info "Prüfe Container Logs für Startnachrichten..."
    
    # Zeige letzte Logs von jedem Bot
    RUNNING_CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E "(discord|bot)" || true)
    
    if [[ -n "$RUNNING_CONTAINERS" ]]; then
        echo "$RUNNING_CONTAINERS" | while read container; do
            echo "--- Logs von $container ---"
            docker logs --tail 5 "$container" 2>/dev/null | head -3 || echo "Keine Logs verfügbar"
            echo
        done
    fi
}

# Funktion: Cleanup alte Images
cleanup_old_images() {
    log_info "Bereinige alte Images..."
    
    # Entferne dangling images
    docker image prune -f > /dev/null 2>&1
    
    # Entferne unbenutzte Images (älter als 24h)
    docker image prune -a -f --filter "until=24h" > /dev/null 2>&1
    
    log_success "Image Cleanup abgeschlossen"
}

# Main Execution
main() {
    log_header "Starte Complete Bot Restart & Update Prozess..."
    
    # 1. Stoppe alle Bots
    stop_all_bots
    
    # 2. Kurz warten
    sleep 5
    
    # 3. Baue neue Images
    build_bot_images
    
    # 4. Starte alle Bots einzeln
    log_header "Starte alle Bots..."
    
    for bot_name in "${!BOT_CONFIGS[@]}"; do
        bot_dir="${BOT_CONFIGS[$bot_name]}"
        
        if start_bot "$bot_name" "$bot_dir"; then
            # Kurz warten zwischen Bot starts
            sleep 3
            
            # Warte auf Gesundheitsstatus
            wait_for_bot_health "$bot_name"
        fi
    done
    
    # 5. Cleanup
    cleanup_old_images
    
    # 6. Final Status
    echo
    show_final_status
    
    log_header "🎉 Bot Restart Complete!"
    
    echo
    echo "📋 Nächste Schritte:"
    echo "   • Prüfe Discord Channels auf Startnachrichten"
    echo "   • Teste Bot Funktionalität in entsprechenden Channels"
    echo "   • Überwache Logs: docker logs <container-name>"
    echo "   • Status prüfen: docker ps | grep bot"
}

# Unterstützung für verschiedene Modi
case "${1:-full}" in
    "full")
        main
        ;;
    "status")
        show_final_status
        ;;
    "stop")
        stop_all_bots
        ;;
    "cleanup")
        cleanup_old_images
        ;;
    *)
        echo "Usage: $0 [full|status|stop|cleanup]"
        echo "  full    - Complete restart (default)"
        echo "  status  - Show current status"
        echo "  stop    - Stop all bots"
        echo "  cleanup - Cleanup old images"
        exit 1
        ;;
esac
