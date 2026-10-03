#!/bin/bash
# PopWallpaper - Setup Script
# Installs linux-wallpaperengine for full Wallpaper Engine support

set -e

echo "============================================================"
echo "PopWallpaper - Setup"
echo "============================================================"

# Check if already installed
if command -v linux-wallpaperengine &>/dev/null || [ -x /usr/local/bin/wpe/linux-wallpaperengine ]; then
    echo "✅ linux-wallpaperengine is already installed!"
    linux-wallpaperengine --help 2>/dev/null | head -1 || true
    exit 0
fi

echo ""
echo "linux-wallpaperengine is required for Scene and Web wallpapers."
echo ""
echo "Install options:"
echo "  1) Download precompiled .deb (requires sudo)"
echo "  2) Build from source (requires build tools + sudo)"
echo "  3) Skip (video wallpapers only with mpvpaper)"
echo ""
read -p "Choose [1/2/3]: " CHOICE

case "$CHOICE" in
    1)
        echo ""
        echo "Downloading precompiled .deb..."
        TMP_DIR=$(mktemp -d)
        wget -q --show-progress -O "$TMP_DIR/int_linux_wallpaper_engine_amd64.deb" \
            "https://github.com/slynobody/linux_wallpaper_engine__precompiled/releases/download/0.8/int_linux_wallpaper_engine_amd64.deb"

        echo "Installing runtime dependencies..."
        sudo apt install -y libkissfft-float131 2>/dev/null || sudo apt install -y libkissfft-float 2>/dev/null || true
        echo "Installing (requires sudo)..."
        sudo apt install -y "$TMP_DIR/int_linux_wallpaper_engine_amd64.deb"
        rm -rf "$TMP_DIR"
        echo ""
        echo "✅ linux-wallpaperengine installed!"
        echo "   Binary location: /usr/local/bin/wpe/linux-wallpaperengine"
        ;;
    2)
        echo ""
        echo "Installing build dependencies..."
        sudo apt update
        sudo apt install -y build-essential cmake git \
            libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev \
            libgl-dev libglew-dev freeglut3-dev libglfw3-dev \
            libsdl2-dev liblz4-dev libglm-dev \
            libavcodec-dev libavformat-dev libavutil-dev libswscale-dev \
            libxxf86vm-dev libmpv-dev mpv libmpv2 \
            libpulse-dev libpulse0 libfftw3-dev libfreetype-dev \
            libkissfft-dev 2>/dev/null || true

        echo "Cloning linux-wallpaperengine..."
        TMP_DIR=$(mktemp -d)
        git clone --recurse-submodules https://github.com/Almamu/linux-wallpaperengine.git "$TMP_DIR/linux-wallpaperengine"

        echo "Building..."
        cd "$TMP_DIR/linux-wallpaperengine"
        mkdir build && cd build
        cmake -DCMAKE_BUILD_TYPE='Release' ..
        make -j$(nproc)

        echo "Installing..."
        sudo mkdir -p /opt/linux-wallpaperengine
        sudo cp -r output/* /opt/linux-wallpaperengine/
        sudo chmod +x /opt/linux-wallpaperengine/linux-wallpaperengine

        # Create symlink
        sudo ln -sf /opt/linux-wallpaperengine/linux-wallpaperengine /usr/local/bin/linux-wallpaperengine

        cd /
        rm -rf "$TMP_DIR"
        echo ""
        echo "✅ linux-wallpaperengine built and installed!"
        ;;
    3)
        echo ""
        echo "Skipping. Video wallpapers will use mpvpaper."
        echo "Scene and Web wallpapers will not be available."
        exit 0
        ;;
    *)
        echo "Invalid choice."
        exit 1
        ;;
esac

echo ""
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Run ./run.sh to start PopWallpaper."
