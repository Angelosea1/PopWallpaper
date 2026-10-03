#!/bin/bash
# Control helper for PopWallpaper - handles both mpvpaper and linux-wallpaperengine
# Usage: wpe_control.sh <command> [args...]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    mute)
        python3 "$SCRIPT_DIR/_sinkctl.py" mute
        ;;
    unmute)
        python3 "$SCRIPT_DIR/_sinkctl.py" unmute
        ;;
    toggle-mute)
        python3 "$SCRIPT_DIR/_sinkctl.py" toggle-mute
        ;;
    is-muted)
        python3 "$SCRIPT_DIR/_sinkctl.py" is-muted
        ;;
    stop)
        kill -9 $(pgrep -x mpv) 2>/dev/null
        killall mpvpaper 2>/dev/null
        pkill -f "linux-wallpaperengine" 2>/dev/null
        rm -f /tmp/mpvpaper-ipc 2>/dev/null
        ;;
    set-wallpaper)
        TYPE="$2"
        WALLPAPER_PATH="$3"
        MONITOR="${4:-}"
        if [ -z "$TYPE" ] || [ -z "$WALLPAPER_PATH" ]; then
            echo "Usage: wpe_control.sh set-wallpaper <type> <path> [monitor]"
            echo "Types: video, scene, web"
            exit 1
        fi
        "$SCRIPT_DIR/lanzador.sh" "$TYPE" "$WALLPAPER_PATH" "$MONITOR"
        ;;
    *)
        echo "Usage: wpe_control.sh <command> [args...]"
        echo "Commands:"
        echo "  mute              - Mute all wallpaper audio"
        echo "  unmute            - Unmute all wallpaper audio"
        echo "  toggle-mute       - Toggle mute"
        echo "  is-muted          - Check if muted"
        echo "  stop              - Stop all wallpaper engines"
        echo "  set-wallpaper <type> <path> [monitor]"
        echo "                    - Set wallpaper (type: video|scene|web)"
        exit 1
        ;;
esac
