#!/bin/bash
# PopWallpaper launcher - uses mpvpaper for video, linux-wallpaperengine for scene/web
# Usage: lanzador.sh <type> <path> [monitor]
#   type = video | scene | web
#   path = folder_path for scene/web, or video file for video
#   monitor = X11 output name (optional, defaults to *)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TYPE="$1"
PATH_ARG="$2"
MONITOR="$3"

if [ -z "$TYPE" ] || [ -z "$PATH_ARG" ]; then
    echo "Usage: lanzador.sh <video|scene|web> <path> [monitor]"
    exit 1
fi

# Kill existing wallpaper processes
pkill -f "mpvpaper" 2>/dev/null
pkill -f "linux-wallpaperengine" 2>/dev/null
sleep 0.3

# Clean up old IPC socket
rm -f /tmp/mpvpaper-ipc 2>/dev/null

if [ "$TYPE" = "video" ]; then
    # Use mpvpaper for video wallpapers
    MPVPAPER=""
    for candidate in \
        "$(command -v mpvpaper 2>/dev/null)" \
        /usr/local/bin/mpvpaper; do
        if [ -n "$candidate" ] && [ -x "$candidate" ]; then
            MPVPAPER="$candidate"
            break
        fi
    done

    if [ -z "$MPVPAPER" ]; then
        echo "ERROR: mpvpaper not found!"
        exit 1
    fi

    MONITOR_VAL="${MONITOR:-*}"

    MPV_ARGS=("-o" "loop" "--input-ipc-server=/tmp/mpvpaper-ipc")

    if [ "$MONITOR_VAL" = "*" ]; then
        MPV_ARGS+=("--no-audio" "$MONITOR_VAL" "$PATH_ARG")
    else
        MPV_ARGS+=("--no-audio" "$MONITOR_VAL" "$PATH_ARG")
    fi

    nohup "$MPVPAPER" "${MPV_ARGS[@]}" >/dev/null 2>&1 &

else
    # Use linux-wallpaperengine for scene/web wallpapers
    WPE=""
    for candidate in \
        /opt/linux-wallpaperengine/linux-wallpaperengine \
        "$(command -v linux-wallpaperengine 2>/dev/null)"; do
        if [ -n "$candidate" ] && [ -x "$candidate" ]; then
            WPE="$candidate"
            break
        fi
    done

    if [ -z "$WPE" ]; then
        echo "ERROR: linux-wallpaperengine not found!"
        echo "Scene and Web wallpapers require linux-wallpaperengine."
        exit 1
    fi

    launch_wpe() {
        local monitor="$1"
        local args=("--silent")
        if [ -n "$monitor" ] && [ "$monitor" != "*" ]; then
            args+=("--screen-root" "$monitor")
        fi
        args+=("$PATH_ARG")
        nohup "$WPE" "${args[@]}" >/dev/null 2>&1 &
    }

    if [ -z "$MONITOR" ] || [ "$MONITOR" = "*" ]; then
        while IFS= read -r name; do
            launch_wpe "$name"
        done < <(xrandr --listmonitors 2>/dev/null | awk 'NR>1{gsub(/\+/,"",$2); print $2}')
    else
        launch_wpe "$MONITOR"
    fi
fi
