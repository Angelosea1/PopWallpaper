# PopWallpaper

> 🎨 A modern GUI application for managing and applying animated wallpapers from Wallpaper Engine on Pop!_OS 24.04 (COSMIC/Wayland)

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Pop!_OS%2024.04-orange.svg)

**🤖 Developed with AI:** This project was created with assistance from [Google Gemini](https://gemini.google.com/) AI.

---

## ✨ Features

- 🎨 Modern dark UI using customtkinter
- 📁 Automatic scanning of Steam Workshop wallpapers
- 🎬 Support for video wallpapers (.mp4, .webm)
- 🖼️ Preview images (JPG, PNG, GIF) with automatic format detection
- 🔄 Easy wallpaper switching with thumbnail previews
- ⚡ Persistent wallpapers via mpvpaper integration
- 🚀 Independent background process (survives app closure)
- 📝 Smart text handling for long wallpaper names

---

## 📋 Requirements

- Python 3.8+
- mpvpaper (for applying wallpapers)
- Steam with Wallpaper Engine workshop content
- Pop!_OS 24.04 with Wayland/COSMIC

---

## 🚀 Installation

### 1. Install mpvpaper
```bash
sudo apt install mpvpaper
```

### 2. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/PopWallpaper.git
cd PopWallpaper
```

### 3. Install Desktop Shortcut (Recommended)
```bash
python3 install_shortcut.py
```

This will:
- Create a `.desktop` file in your applications menu
- Download an icon for the app
- Configure proper launch paths
- Make PopWallpaper accessible from your app launcher

### 4. Quick Run (Without Installation)
```bash
./run.sh
```

---

## 📖 How It Works

1. Scans your Steam Workshop directory for Wallpaper Engine content
2. Parses `project.json` files to find video wallpapers
3. Filters out non-video types (scenes, web)
4. Displays wallpapers with preview images (supports JPG, PNG, GIF)
5. Applies animated backgrounds using `mpvpaper`
6. Manages processes independently for persistence

### Directory Structure
```
~/.local/share/Steam/steamapps/workshop/content/431960/
├── [workshop_id_1]/
│   ├── project.json
│   ├── preview.jpg (or .png, .gif)
│   └── scene.mp4
└── [workshop_id_2]/
    ├── project.json
    ├── preview.png
    └── video.webm
```

---

## 🛠️ Troubleshooting

**No wallpapers found:**
- Ensure Steam is installed
- Subscribe to Wallpaper Engine wallpapers in Workshop
- Check workshop path: `~/.local/share/Steam/steamapps/workshop/content/431960`

**mpvpaper not found:**
```bash
sudo apt install mpvpaper
```

**If this doesn't work:** Visit the [mpvpaper GitHub repository](https://github.com/GhostNaN/mpvpaper) and follow their installation guide.

**If dependencies are missing:** Try:
```bash
sudo apt install meson ninja-build wayland-protocols libwayland-dev libegl-dev libmpv-dev
```

**Wallpaper not applying:**
- Ensure you're running Wayland (required for mpvpaper)
- Check mpvpaper is working: `mpvpaper --help`

**`ModuleNotFoundError: No module named 'tkinter'`**

Install the tkinter module:
```bash
sudo apt install python3-tk
```

---

## 📁 Project Structure

```
PopWallpaper/
├── popwallpaper.py        # Main application
├── install_shortcut.py    # Desktop shortcut installer
├── lanzador.sh           # Background launcher script
├── run.sh                # Main launcher
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── LICENSE              # MIT License
└── docs/                # Documentation
    ├── CAMBIOS.md       # Spanish changelog
    ├── CORRECCIONES.md  # Bug fixes documentation
    ├── FIX_PREVIEW.md   # Preview image fixes
    └── FIX_LAYOUT.md    # Layout fixes
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**AI Development:** This project was developed with assistance from Google Gemini AI.

---

## 🙏 Acknowledgments

- Developed with [Google Gemini](https://gemini.google.com/) AI assistance
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI
- [mpvpaper](https://github.com/GhostNaN/mpvpaper) for wallpaper rendering
- Wallpaper Engine community for amazing content

---

## 📸 Screenshots

> Add your screenshots here!

---

**Made with ❤️ and 🤖 AI**
