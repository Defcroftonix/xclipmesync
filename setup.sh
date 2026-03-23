#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/clipboard_sync.py"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/clipboard-sync.service"
PYTHON=$(which python3)

# Check dependencies
if ! command -v xclip &>/dev/null; then
    echo "Error: xclip is not installed. Install it with:"
    echo "  sudo apt install xclip   # Debian/Ubuntu"
    echo "  sudo pacman -S xclip     # Arch"
    echo "  sudo dnf install xclip   # Fedora"
    exit 1
fi

PYTHON=$(which python3 2>/dev/null)
if [ -z "$PYTHON" ]; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Need at least 2 displays
if [ "$#" -lt 2 ]; then
    DISPLAYS=":0 :1"
    echo "No displays specified, defaulting to :0 and :1"
else
    DISPLAYS="$@"
fi

# Write service file
mkdir -p "$SERVICE_DIR"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=X11 clipboard sync

[Service]
ExecStart=$PYTHON $SCRIPT_PATH $DISPLAYS
Restart=on-failure

[Install]
WantedBy=default.target
EOF

# Enable linger so service survives without active session
loginctl enable-linger "$USER"

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now clipboard-sync

echo "Done! Clipboard sync running across: $DISPLAYS"
echo "Check status with: systemctl --user status clipboard-sync"
