#!/bin/bash

# JARVIS Dashboard Startup Script
# Usage: ./start.sh [--browser] [--help]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/../.venv"

# Check for --browser flag
OPEN_BROWSER=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --browser|-b)
            OPEN_BROWSER=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./start.sh [--browser]"
            echo "  --browser, -b  Open dashboard in browser"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    fi
}

echo "========================================"
echo "  JARVIS Dashboard"
echo "  O4 Studio Life Management"
echo "========================================"
echo ""

# Check if backend is already running
if curl -s http://localhost:8080/api/profile > /dev/null 2>&1; then
    echo "Backend already running on http://localhost:8080"
else
    echo "Starting backend server..."
    activate_venv
    uvicorn jarvis.dashboard.backend.main:app --host 0.0.0.0 --port 8080 &
    BACKEND_PID=$!
    
    sleep 2
    
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "Error: Backend failed to start"
        exit 1
    fi
    echo "Backend started successfully"
fi

echo ""
echo "========================================"
echo "  Dashboard running!"
echo "  URL: http://localhost:8080"
echo "========================================"
echo ""

if [ "$OPEN_BROWSER" = true ]; then
    echo "Opening in browser..."
    xdg-open http://localhost:8080 2>/dev/null || echo "Open manually: http://localhost:8080"
fi

echo "Press Ctrl+C to stop"
echo ""

# Handle shutdown
cleanup() {
    echo ""
    echo "Stopping dashboard..."
    deactivate 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait forever (or until Ctrl+C)
while true; do
    sleep 1
done
