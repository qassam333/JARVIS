#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "       JARVIS Docker Management Script        "
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

show_help() {
    cat << EOF
Usage: ./run.sh [COMMAND]

Commands:
    build       Build Docker image
    start       Start JARVIS container
    stop        Stop JARVIS container
    restart     Restart JARVIS container
    logs        Show container logs
    shell       Open shell in running container
    status      Show container status
    clean       Remove containers and images
    api         Start with API enabled
    voice       Start with voice support

Examples:
    ./run.sh build
    ./run.sh start
    ./run.sh logs -f
EOF
}

# Create directories if they don't exist
mkdir -p data voices whisper.cpp/models

# Build Docker image
build() {
    echo -e "${GREEN}Building JARVIS Docker image...${NC}"
    docker build -t jarvis:latest .
    echo -e "${GREEN}Build complete!${NC}"
}

# Start container
start() {
    echo -e "${GREEN}Starting JARVIS...${NC}"
    docker compose up -d jarvis
    echo -e "${GREEN}JARVIS started!${NC}"
    echo "Run './run.sh logs -f' to see output"
}

# Stop container
stop() {
    echo -e "${YELLOW}Stopping JARVIS...${NC}"
    docker compose stop jarvis
    echo -e "${YELLOW}JARVIS stopped${NC}"
}

# Restart container
restart() {
    echo -e "${YELLOW}Restarting JARVIS...${NC}"
    docker compose restart jarvis
    echo -e "${GREEN}JARVIS restarted${NC}"
}

# Show logs
show_logs() {
    docker compose logs -f jarvis "${@}"
}

# Open shell
shell_exec() {
    docker compose exec jarvis "${@}"
}

# Show status
status() {
    docker compose ps
}

# Clean up
clean() {
    echo -e "${RED}WARNING: This will remove all JARVIS containers and images${NC}"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Cleaning up...${NC}"
        docker compose down --rmi local -v
        echo -e "${RED}Cleanup complete${NC}"
    else
        echo "Cancelled"
    fi
}

# Start with API
start_api() {
    echo -e "${GREEN}Starting JARVIS with API...${NC}"
    docker compose --profile api up -d jarvis-api
    echo -e "${GREEN}API started at http://localhost:8000${NC}"
}

# Start with voice (needs audio device)
start_voice() {
    echo -e "${YELLOW}Starting JARVIS with voice support...${NC}"
    docker compose run --rm --device /dev/snd:/dev/snd -it jarvis voice --ptt
}

# Main
case "${1:-}" in
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        show_logs "${@:2}"
        ;;
    shell)
        shell_exec "${@:2}"
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    api)
        start_api
        ;;
    voice)
        start_voice
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
