# PopWallpaper

> Modern GUI application for managing and applying animated wallpapers from Steam Workshop on Pop!_OS

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Pop!_OS%2024.04-orange.svg)

---

## Features

- Modern dark UI with customtkinter
- Automatic scanning of Steam Workshop wallpapers
- **Full Wallpaper Engine support**: video, scene, and web wallpapers
- Thumbnail previews with GIF/JPG/PNG support
- Per-monitor wallpaper control (apply different wallpapers to each monitor)
- **Audio support**: wallpapers play their audio by default
- **Auto-mute on focus**: mutes wallpaper audio when you switch to another window
- **Apply on boot**: optionally auto-apply wallpapers when you log in
- Monitor selector (All / HDMI-A-1 / DP-1 / etc.)
- Type filter (Video / Scene / Web)
- Persistent background processes (survives app closure)

---

## Requirements

- Python 3.10+
- Pop!_OS 24.04 (Ubuntu-based, X11)
- Steam with Wallpaper Engine workshop content
- mpvpaper (for video wallpapers)
- linux-wallpaperengine (for scene/web wallpapers, built from source)

---

## Installation

### 1. Install system dependencies

```bash
# mpvpaper for video wallpapers
sudo apt install mpvpaper

# linux-wallpaperengine build dependencies (for scene/web wallpapers)
sudo apt install -y build-essential cmake git \
  libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev \
  libgl-dev libglew-dev freeglut3-dev libglfw3-dev \
  libsdl2-dev liblz4-dev libglm-dev \
  libavcodec-dev libavformat-dev libavutil-dev libswscale-dev \
  libxxf86vm-dev libmpv-dev libpulse-dev libpulse0 libfftw3-dev libfreetype-dev
```

### 2. Build linux-wallpaperengine from source

```bash
cd /tmp
git clone --recurse-submodules https://github.com/Almamu/linux-wallpaperengine.git
cd linux-wallpaperengine
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE='Release' ..
make -j$(nproc)

sudo mkdir -p /opt/linux-wallpaperengine
sudo cp -r output/* /opt/linux-wallpaperengine/
sudo chmod +x /opt/linux-wallpaperengine/linux-wallpaperengine
```

### 3. Clone and run

```bash
git clone https://github.com/Angelosea1/PopWallpaper.git
cd PopWallpaper
./run.sh
```

`run.sh` automatically creates a virtual environment and installs Python dependencies on first run.

---

## Supported Wallpaper Types

| Type | Engine | Description |
|------|--------|-------------|
| Video (mp4, webm, avi, mkv) | mpvpaper | Animated video wallpapers with audio |
| Scene | linux-wallpaperengine | Animated scene wallpapers with particles, shaders, and effects |
| Web | linux-wallpaperengine | HTML/JS/CSS wallpapers rendered via CEF |

---

## How It Works

1. Scans Steam Workshop directory for Wallpaper Engine content (`project.json`)
2. Detects wallpaper type (video/scene/web) and extracts metadata
3. For **video**: launches `mpvpaper` with loop and IPC socket for mute control
4. For **scene/web**: launches `linux-wallpaperengine` per-monitor
5. Audio is managed via PulseAudio/PipeWire sink-input control
6. Each monitor runs its own independent wallpaper process
7. Config is saved to `~/.config/popwallpaper/config.json`

---

## Project Structure

```
PopWallpaper/
├── popwallpaper.py        # Main application (GUI + WallpaperManager)
├── run.sh                 # Launcher (creates venv, installs deps, runs app)
├── setup.sh               # Installs linux-wallpaperengine from source
├── lanzador.sh            # Legacy launcher (unused in current architecture)
├── _sinkctl.py            # PulseAudio/PipeWire sink-input controller
├── wpe_control.sh         # Legacy control script (unused in current architecture)
├── requirements.txt       # Python dependencies
├── LICENSE                # MIT License
└── README.md              # This file
```

---

## Configuration

Wallpaper config is saved at `~/.config/popwallpaper/config.json`:

```json
{
  "wallpapers": [
    {"title": "One Piece Legendary", "folder_path": "/path/to/wallpaper", "monitor": "HDMI-A-1"},
    {"title": "Bleach", "folder_path": "/path/to/wallpaper", "monitor": "DP-1"}
  ],
  "apply_on_boot": true
}
```

---

## Troubleshooting

**No wallpapers found:**
- Ensure Steam is installed and Wallpaper Engine is in your library
- Subscribe to wallpapers in the Steam Workshop
- Check the workshop path exists: `~/.local/share/Steam/steamapps/workshop/content/431960`

**Scene/Web wallpapers don't work:**
- Ensure `linux-wallpaperengine` is built and installed at `/opt/linux-wallpaperengine/`
- Verify: `/opt/linux-wallpaperengine/linux-wallpaperengine --help`

**Audio not playing:**
- Ensure PulseAudio or PipeWire is running
- Check with `pactl list sink-inputs` for mpv/wallpaperengine entries

---

## Contributing

Contributions are welcome! Please open an issue or submit a Pull Request.

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Acknowledgments

- [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine) by Almamu for scene/web rendering
- [mpvpaper](https://github.com/GhostNaN/mpvpaper) for video wallpaper rendering
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI
- Steam Workshop community for amazing wallpapers
