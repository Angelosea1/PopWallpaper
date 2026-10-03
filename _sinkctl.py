#!/usr/bin/env python3
"""Sink input controller for PopWallpaper. Finds wallpaper-related sink inputs and mutes/unmutes them."""

import subprocess
import sys
import os

WALLPAPER_APPS = ['mpv', 'mpvpaper', 'linux-wallpaperengine']

def run_pactl(*args):
    env = os.environ.copy()
    env['LANG'] = 'C'
    return subprocess.run(['pactl'] + list(args), capture_output=True, text=True, env=env)

def get_wallpaper_sink_inputs():
    """Find sink input indices for wallpaper-related apps."""
    result = run_pactl('list', 'sink-inputs')
    lines = result.stdout.split('\n')

    current_index = None
    current_is_wallpaper = False
    found_indices = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('Sink Input #'):
            if current_index is not None and current_is_wallpaper:
                found_indices.append(current_index)
            try:
                current_index = stripped.split('#')[1].strip()
            except (IndexError, ValueError):
                current_index = None
            current_is_wallpaper = False

        elif current_index is not None:
            lower = stripped.lower()
            if 'node.name' in lower or 'application.name' in lower or 'media.name' in lower:
                for app in WALLPAPER_APPS:
                    if app in lower:
                        current_is_wallpaper = True
                        break

            if 'mute: yes' in lower or 'mute: sim' in lower:
                pass  # Will be checked in is-muted action

    if current_index is not None and current_is_wallpaper:
        found_indices.append(current_index)

    return found_indices

def is_any_muted(indices):
    """Check if any of the given sink inputs are muted."""
    result = run_pactl('list', 'sink-inputs')
    lines = result.stdout.split('\n')

    current_index = None
    current_mute_status = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('Sink Input #'):
            if current_index in indices and current_mute_status:
                return True
            try:
                current_index = stripped.split('#')[1].strip()
            except (IndexError, ValueError):
                current_index = None
            current_mute_status = False

        elif current_index in indices:
            lower = stripped.lower()
            if 'mute: yes' in lower or 'mute: sim' in lower:
                current_mute_status = True

    if current_index in indices and current_mute_status:
        return True

    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: _sinkctl.py <mute|unmute|toggle-mute|is-muted>", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    indices = get_wallpaper_sink_inputs()

    if action == 'is-muted':
        print('yes' if is_any_muted(indices) else 'no')

    elif action == 'mute':
        for idx in indices:
            run_pactl('set-sink-input-mute', idx, '1')

    elif action == 'unmute':
        for idx in indices:
            run_pactl('set-sink-input-mute', idx, '0')

    elif action == 'toggle-mute':
        for idx in indices:
            run_pactl('set-sink-input-mute', idx, 'toggle')

if __name__ == '__main__':
    main()
