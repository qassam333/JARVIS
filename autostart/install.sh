#!/bin/bash
# JARVIS Auto-start Script
# Run this to enable/disable JARVIS startup

JARVIS_DIR="/home/deep/BACKUP/GG POJECT/GGjarvis/JARVIS"
SERVICE_FILE="$JARVIS_DIR/autostart/jarvis.service"
DESKTOP_FILE="$JARVIS_DIR/autostart/jarvis.desktop"

install_systemd() {
    echo "Installing systemd service..."
    mkdir -p ~/.config/systemd/user
    sed -e "s|%USER%|$USER|g" -e "s|%DIR%|$JARVIS_DIR|g" "$SERVICE_FILE" > ~/.config/systemd/user/jarvis.service
    systemctl --user daemon-reload
    systemctl --user enable jarvis.service
    echo "JARVIS will start on next login."
}

install_desktop() {
    echo "Installing desktop entry..."
    mkdir -p ~/.config/autostart
    sed -e "s|%USER%|$USER|g" -e "s|%DIR%|$JARVIS_DIR|g" "$SERVICE_FILE" | sed "s|ExecStart=.*|ExecStart=/bin/bash -c 'cd \\\"$JARVIS_DIR\\\" \\&\\& source .venv/bin/activate \\&\\& jarvis voice'|" > ~/.config/autostart/jarvis.desktop
    chmod +x ~/.config/autostart/jarvis.desktop
    echo "JARVIS will start on login."
}

uninstall() {
    echo "Removing autostart..."
    rm -f ~/.config/systemd/user/jarvis.service
    rm -f ~/.config/autostart/jarvis.desktop
    systemctl --user daemon-reload 2>/dev/null
    echo "Autostart removed."
}

case "${1:-install}" in
    install)
        if command -v systemctl &> /dev/null; then
            install_systemd
        else
            install_desktop
        fi
        ;;
    systemd)
        install_systemd
        ;;
    desktop)
        install_desktop
        ;;
    uninstall)
        uninstall
        ;;
    *)
        echo "Usage: $0 [install|systemd|desktop|uninstall]"
        ;;
esac
