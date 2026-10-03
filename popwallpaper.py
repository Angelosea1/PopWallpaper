#!/usr/bin/env python3
"""
PopWallpaper - Wallpaper Engine Manager for Pop!_OS
Supports video, scene, and web wallpapers via linux-wallpaperengine
"""

import os
import sys
import json
import time
import signal
import shutil
import subprocess
import shlex
import logging

CONFIG_DIR = os.path.expanduser("~/.config/popwallpaper")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, "popwallpaper.desktop")

os.makedirs(CONFIG_DIR, exist_ok=True)
LOG_FILE = os.path.join(CONFIG_DIR, "boot.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("popwallpaper")


def truncate_text(text, max_length=40):
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


class Wallpaper:
    def __init__(self, title, wallpaper_type, folder_path, preview_path=None, media_path=None, workshop_id=None):
        self.title = title
        self.wallpaper_type = wallpaper_type
        self.folder_path = folder_path
        self.preview_path = preview_path
        self.media_path = media_path
        self.workshop_id = workshop_id

    @property
    def type_badge(self):
        return {'video': '🎬 Video', 'scene': '🎨 Scene', 'web': '🌐 Web'}.get(self.wallpaper_type, self.wallpaper_type)


class WallpaperScanner:
    WORKSHOP_PATHS = [
        os.path.expanduser("~/.steam/debian-installation/steamapps/workshop/content/431960"),
        os.path.expanduser("~/.local/share/Steam/steamapps/workshop/content/431960"),
        os.path.expanduser("~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/workshop/content/431960"),
    ]

    @classmethod
    def get_workshop_path(cls):
        for path in cls.WORKSHOP_PATHS:
            if os.path.exists(path):
                return path
        return cls.WORKSHOP_PATHS[0]

    @classmethod
    def _find_preview(cls, folder_path):
        for ext in ['preview.jpg', 'preview.png', 'preview.gif', 'preview.jpeg']:
            p = os.path.join(folder_path, ext)
            if os.path.exists(p):
                return p
        return None

    @classmethod
    def scan_wallpapers(cls):
        wallpapers = []
        workshop_path = cls.get_workshop_path()
        if not os.path.exists(workshop_path):
            return wallpapers

        for folder_name in os.listdir(workshop_path):
            folder_path = os.path.join(workshop_path, folder_name)
            if not os.path.isdir(folder_path):
                continue
            project_json = os.path.join(folder_path, "project.json")
            if not os.path.exists(project_json):
                continue
            try:
                with open(project_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                wp_type = data.get('type', '').lower()
                title = data.get('title', f'Untitled ({folder_name})')
                preview_path = cls._find_preview(folder_path)
                media_path = None
                if wp_type == 'video':
                    video_file = data.get('file', '')
                    if video_file:
                        candidate = os.path.join(folder_path, video_file)
                        if os.path.exists(candidate):
                            media_path = candidate
                    if not media_path:
                        for ext in ['.mp4', '.webm', '.avi', '.mkv']:
                            for f in os.listdir(folder_path):
                                if f.lower().endswith(ext):
                                    media_path = os.path.join(folder_path, f)
                                    break
                            if media_path:
                                break
                wallpapers.append(Wallpaper(title, wp_type, folder_path, preview_path, media_path, workshop_id=folder_name))
            except (json.JSONDecodeError, IOError):
                continue
        wallpapers.sort(key=lambda w: w.title.lower())
        return wallpapers


class WallpaperManager:
    _WPE_BIN = None
    _MPVPAPER_BIN = None
    _processes = {}

    _WPE_ENV = None  # cached env with LD_LIBRARY_PATH for WPE

    @classmethod
    def _get_wpe_env(cls):
        """Return an env dict with LD_LIBRARY_PATH set for WPE."""
        if cls._WPE_ENV is not None:
            return cls._WPE_ENV
        env = os.environ.copy()
        wpe_lib = "/opt/linux-wallpaperengine"
        extra = [wpe_lib]
        for d in ["/usr/local/lib", "/usr/lib"]:
            if os.path.isdir(d):
                extra.append(d)
        existing = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = ":".join(extra) + (":" + existing if existing else "")
        cls._WPE_ENV = env
        return env

    @classmethod
    def _find_wpe(cls):
        if cls._WPE_BIN:
            return cls._WPE_BIN
        candidates = [shutil.which("linux-wallpaperengine"),
                      "/usr/local/bin/linux-wallpaperengine",
                      "/opt/linux-wallpaperengine/linux-wallpaperengine",
                      "/usr/local/bin/wpe/linux-wallpaperengine"]
        for p in candidates:
            if p and os.path.isfile(p) and os.access(p, os.X_OK):
                cls._WPE_BIN = p
                return p
        return None

    @classmethod
    def _find_mpvpaper(cls):
        if cls._MPVPAPER_BIN:
            return cls._MPVPAPER_BIN
        for p in [shutil.which("mpvpaper"), "/usr/local/bin/mpvpaper"]:
            if p and os.path.isfile(p) and os.access(p, os.X_OK):
                cls._MPVPAPER_BIN = p
                return p
        return None

    @classmethod
    def _get_monitors(cls):
        try:
            result = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True)
            monitors = []
            for line in result.stdout.strip().split('\n')[1:]:
                parts = line.strip().split()
                if len(parts) >= 2:
                    monitors.append(parts[1].lstrip('+'))
            return monitors
        except Exception:
            return []

    @classmethod
    def _stop_monitor(cls, monitor):
        procs = cls._processes.pop(monitor, [])
        for p in procs:
            try:
                p.kill()
            except Exception:
                pass

    @staticmethod
    def apply_wallpaper(wallpaper, monitor="*", audio_monitor=None):
        targets = []
        if monitor and monitor != "*":
            targets = [monitor]
        else:
            targets = WallpaperManager._get_monitors()

        for t in targets:
            WallpaperManager._stop_monitor(t)

        if wallpaper.wallpaper_type == "video":
            mpv = WallpaperManager._find_mpvpaper()
            if not mpv:
                return False
            path = wallpaper.media_path or wallpaper.folder_path
            display = monitor if (monitor and monitor != "*") else "*"
            cmd = [mpv, "-o", "loop", "--input-ipc-server=/tmp/mpvpaper-ipc", display, path]
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            WallpaperManager._processes.setdefault(display, []).append(p)
        else:
            wpe = WallpaperManager._find_wpe()
            if not wpe:
                return False
            targets_wpe = targets if targets else WallpaperManager._get_monitors()
            wpe_env = WallpaperManager._get_wpe_env()
            for m in targets_wpe:
                args = ["--screen-root", m]
                if audio_monitor and m != audio_monitor:
                    args.append("--silent")
                args.append("--fullscreen-pause-only-active")
                args.append(wallpaper.folder_path)
                p = subprocess.Popen(
                    [wpe] + args,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                    start_new_session=True,
                    env=wpe_env
                )
                WallpaperManager._processes.setdefault(m, []).append(p)
                time.sleep(1)
                if p.poll() is not None and p.returncode != 0:
                    err = p.stderr.read().decode(errors='replace')[:200] if p.stderr else ""
                    log.error(f"WPE failed on {m}: {err}")
        return True

    @staticmethod
    def apply_from_config(config):
        WallpaperManager.stop()
        monitors = WallpaperManager._get_monitors()
        wallpapers = WallpaperScanner.scan_wallpapers()
        wallpaper_by_id = {w.workshop_id: w for w in wallpapers}
        audio_monitor = config.get("audio_monitor")

        for entry in config.get("wallpapers", []):
            wp = wallpaper_by_id.get(entry.get("workshop_id"))
            if not wp:
                continue
            monitor = entry.get("monitor", "*")
            if monitor != "*" and monitor not in monitors:
                continue
            WallpaperManager.apply_wallpaper(wp, monitor, audio_monitor=audio_monitor)

    @staticmethod
    def _get_wallpaper_sink_inputs():
        env = os.environ.copy()
        env['LANG'] = 'C'
        result = subprocess.run(['pactl', 'list', 'sink-inputs'], capture_output=True, text=True, env=env)
        lines = result.stdout.split('\n')
        current_index = None
        current_is_wallpaper = False
        found = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('Sink Input #'):
                if current_index is not None and current_is_wallpaper:
                    found.append(current_index)
                try:
                    current_index = stripped.split('#')[1].strip()
                except (IndexError, ValueError):
                    current_index = None
                current_is_wallpaper = False
            elif current_index is not None:
                lower = stripped.lower()
                if any(k in lower for k in ['node.name', 'application.name', 'media.name']):
                    if any(app in lower for app in ['mpv', 'mpvpaper', 'linux-wallpaperengine']):
                        current_is_wallpaper = True
        if current_index is not None and current_is_wallpaper:
            found.append(current_index)
        return found

    @staticmethod
    def toggle_mute():
        for idx in WallpaperManager._get_wallpaper_sink_inputs():
            subprocess.run(['pactl', 'set-sink-input-mute', idx, 'toggle'], capture_output=True)

    @staticmethod
    def set_mute(muted):
        val = '1' if muted else '0'
        for idx in WallpaperManager._get_wallpaper_sink_inputs():
            subprocess.run(['pactl', 'set-sink-input-mute', idx, val], capture_output=True)

    @staticmethod
    def is_muted():
        env = os.environ.copy()
        env['LANG'] = 'C'
        for idx in WallpaperManager._get_wallpaper_sink_inputs():
            result = subprocess.run(['pactl', 'list', 'sink-inputs'], capture_output=True, text=True, env=env)
            current = None
            for line in result.stdout.split('\n'):
                s = line.strip()
                if s.startswith('Sink Input #'):
                    try:
                        current = s.split('#')[1].strip()
                    except (IndexError, ValueError):
                        current = None
                elif current == idx and ('mute: yes' in s.lower() or 'mute: sim' in s.lower()):
                    return True
        return False

    @staticmethod
    def stop():
        for monitor, procs in list(WallpaperManager._processes.items()):
            for p in procs:
                try:
                    p.kill()
                except Exception:
                    pass
        WallpaperManager._processes.clear()
        subprocess.run(['pkill', '-x', 'mpv'], capture_output=True)
        subprocess.run(['pkill', '-x', 'mpvpaper'], capture_output=True)
        result = subprocess.run(['pgrep', '-f', 'linux-wallpaperengine'], capture_output=True, text=True)
        for pid in result.stdout.strip().split():
            if pid.isdigit():
                subprocess.run(['kill', '-9', pid], capture_output=True)
        try:
            os.remove('/tmp/mpvpaper-ipc')
        except OSError:
            pass


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"wallpapers": [], "apply_on_boot": False}


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def set_autostart(enabled):
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    if enabled:
        script_path = os.path.abspath(__file__)
        run_sh = os.path.join(os.path.dirname(script_path), "run.sh")
        exec_line = f'bash -c "sleep 8 && {shlex.quote(run_sh)} --apply-only"'
        content = f"""[Desktop Entry]
Type=Application
Name=PopWallpaper
Exec={exec_line}
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
X-COSMIC-Autostart-enabled=true
"""
        with open(AUTOSTART_FILE, 'w') as f:
            f.write(content)
    else:
        if os.path.exists(AUTOSTART_FILE):
            os.remove(AUTOSTART_FILE)


def wait_for_display(timeout=60, interval=3):
    """Wait until xrandr returns at least one monitor."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        monitors = WallpaperManager._get_monitors()
        if monitors:
            log.info(f"Display ready, monitors: {monitors}")
            return monitors
        log.info("Waiting for display...")
        time.sleep(interval)
    log.warning("Timeout waiting for display, proceeding anyway")
    return WallpaperManager._get_monitors()


def apply_only_mode():
    log.info("=== apply_only_mode starting ===")
    config = load_config()
    if not config.get("apply_on_boot"):
        log.info("apply_on_boot is disabled, exiting")
        return
    if not config.get("wallpapers"):
        log.info("No wallpapers configured, exiting")
        return

    log.info(f"Config: {config}")
    wait_for_display(timeout=90, interval=3)
    WallpaperManager.apply_from_config(config)
    log.info("Wallpapers applied, entering monitoring loop")

    try:
        signal.pause()
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutting down")
    WallpaperManager.stop()


if __name__ == "__main__":
    if "--apply-only" in sys.argv:
        apply_only_mode()
    else:
        import customtkinter as ctk
        from tkinter import messagebox
        from PIL import Image

        class PopWallpaperApp(ctk.CTk):
            def __init__(self):
                super().__init__()
                self.title("PopWallpaper Manager")
                self.geometry("1000x600")
                ctk.set_appearance_mode("dark")
                ctk.set_default_color_theme("blue")

                self.config = load_config()
                self.wallpapers = []
                self.current_wallpaper = None
                self._ready = False
                self.monitors = WallpaperManager._get_monitors()
                self.create_ui()

                self.protocol("WM_DELETE_WINDOW", self.on_closing)

                self.check_wpe_installed()
                self.load_wallpapers()
                self._ready = True

            def check_wpe_installed(self):
                if WallpaperManager._find_wpe():
                    return
                self.after(500, lambda: messagebox.showwarning(
                    "linux-wallpaperengine not found",
                    "linux-wallpaperengine is not installed.\n\n"
                    "Scene and Web wallpapers require it.\n"
                    "Run setup.sh or install manually."
                ))

            def create_ui(self):
                self.grid_columnconfigure(1, weight=1)
                self.grid_rowconfigure(0, weight=1)

                self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
                self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
                self.sidebar.grid_rowconfigure(1, weight=1)

                ctk.CTkLabel(self.sidebar, text="Wallpapers", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
                self.wallpaper_list = ctk.CTkScrollableFrame(self.sidebar, width=260)
                self.wallpaper_list.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
                ctk.CTkButton(self.sidebar, text="🔄 Refresh List", command=self.load_wallpapers).grid(row=2, column=0, padx=20, pady=(10, 5))

                controls_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
                controls_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
                controls_frame.grid_columnconfigure(0, weight=1)
                controls_frame.grid_columnconfigure(1, weight=1)

                self.stop_btn = ctk.CTkButton(
                    controls_frame, text="⏹ Stop",
                    fg_color="#a11d1d", hover_color="#7a1616",
                    command=self.stop_wallpaper
                )
                self.stop_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

                muted = WallpaperManager.is_muted()
                self.mute_btn = ctk.CTkButton(
                    controls_frame,
                    text="🔊 Unmute" if muted else "🔇 Mute",
                    fg_color="#4a4a4a", hover_color="#333333",
                    command=self.toggle_mute
                )
                self.mute_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

                monitor_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
                monitor_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

                ctk.CTkLabel(monitor_frame, text="Monitor:", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=5)
                monitor_names = ["All"] + self.monitors
                self.monitor_var = ctk.StringVar(value=monitor_names[0])
                self.monitor_menu = ctk.CTkOptionMenu(
                    monitor_frame, variable=self.monitor_var,
                    values=monitor_names, width=260
                )
                self.monitor_menu.pack(fill="x", padx=5)

                audio_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
                audio_frame.grid(row=5, column=0, padx=10, pady=(0, 5), sticky="ew")

                ctk.CTkLabel(audio_frame, text="Audio Monitor:", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=5)
                audio_names = ["None"] + self.monitors
                saved_audio = self.config.get("audio_monitor", self.monitors[0] if self.monitors else "None")
                self.audio_var = ctk.StringVar(value=saved_audio if saved_audio in audio_names else "None")
                self.audio_menu = ctk.CTkOptionMenu(
                    audio_frame, variable=self.audio_var,
                    values=audio_names, width=260,
                    command=self._on_audio_monitor_change
                )
                self.audio_menu.pack(fill="x", padx=5)

                filter_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
                filter_frame.grid(row=6, column=0, padx=10, pady=(0, 5), sticky="ew")

                ctk.CTkLabel(filter_frame, text="Filter:", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=5)
                self.filter_var = ctk.StringVar(value="All Types")
                self.filter_menu = ctk.CTkOptionMenu(
                    filter_frame, variable=self.filter_var,
                    values=["All Types", "🎬 Video", "🎨 Scene", "🌐 Web"],
                    command=lambda _: self.reload_list(),
                    width=260
                )
                self.filter_menu.pack(fill="x", padx=5)

                self.boot_var = ctk.BooleanVar(value=self.config.get("apply_on_boot", False))
                self.boot_check = ctk.CTkCheckBox(
                    self.sidebar, text="Apply on boot",
                    variable=self.boot_var, command=self._toggle_boot
                )
                self.boot_check.grid(row=7, column=0, padx=20, pady=(5, 10), sticky="w")

                self.main_panel = ctk.CTkFrame(self, corner_radius=0)
                self.main_panel.grid(row=0, column=1, sticky="nsew")
                self.main_panel.grid_rowconfigure(1, weight=1)
                self.main_panel.grid_columnconfigure(0, weight=1)

                self.title_label = ctk.CTkLabel(
                    self.main_panel, text="Select a wallpaper",
                    font=ctk.CTkFont(size=24, weight="bold"),
                    wraplength=680, justify="center"
                )
                self.title_label.grid(row=0, column=0, padx=40, pady=(40, 20), sticky="ew")

                self.preview_frame = ctk.CTkFrame(self.main_panel)
                self.preview_frame.grid(row=1, column=0, padx=40, pady=20, sticky="nsew")
                self.preview_frame.grid_rowconfigure(0, weight=1)
                self.preview_frame.grid_columnconfigure(0, weight=1)

                self.preview_label = ctk.CTkLabel(self.preview_frame, text="No preview available")
                self.preview_label.grid(row=0, column=0, sticky="nsew")

                self.apply_btn = ctk.CTkButton(
                    self.main_panel, text="Apply Wallpaper",
                    font=ctk.CTkFont(size=18, weight="bold"), height=50,
                    command=self.apply_current_wallpaper, state="disabled"
                )
                self.apply_btn.grid(row=2, column=0, padx=40, pady=40)

                self.status_bar = ctk.CTkLabel(self, text="Ready", anchor="w")
                self.status_bar.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

            def _on_audio_monitor_change(self, value):
                self.config["audio_monitor"] = value
                save_config(self.config)

            def _toggle_boot(self):
                enabled = self.boot_var.get()
                self.config["apply_on_boot"] = enabled
                save_config(self.config)
                set_autostart(enabled)

            def load_wallpapers(self):
                self.status_bar.configure(text="Scanning...")
                self.update()
                self.wallpapers = WallpaperScanner.scan_wallpapers()
                self.reload_list()

            def reload_list(self):
                for w in self.wallpaper_list.winfo_children():
                    w.destroy()

                filter_text = self.filter_var.get()
                filtered = self.wallpapers
                if filter_text == "🎬 Video":
                    filtered = [w for w in self.wallpapers if w.wallpaper_type == 'video']
                elif filter_text == "🎨 Scene":
                    filtered = [w for w in self.wallpapers if w.wallpaper_type == 'scene']
                elif filter_text == "🌐 Web":
                    filtered = [w for w in self.wallpapers if w.wallpaper_type == 'web']

                if not filtered:
                    self.status_bar.configure(text="No wallpapers found" + (f" ({filter_text})" if filter_text != "All Types" else ""))
                    return

                for wp in filtered:
                    frame = ctk.CTkFrame(self.wallpaper_list, fg_color="transparent")
                    frame.pack(fill="x", padx=5, pady=2)

                    thumb = None
                    if wp.preview_path and os.path.exists(wp.preview_path):
                        try:
                            img = Image.open(wp.preview_path)
                            if img.format == 'GIF':
                                img.seek(0)
                                img = img.convert('RGB')
                            img.thumbnail((50, 50), Image.Resampling.LANCZOS)
                            thumb = ctk.CTkImage(light_image=img, dark_image=img, size=(50, 50))
                        except:
                            pass

                    display_name = f"{wp.type_badge}  {truncate_text(wp.title, max_length=30)}"
                    btn = ctk.CTkButton(
                        frame, text=display_name, image=thumb, compound="left",
                        anchor="w", height=60 if thumb else 35,
                        command=lambda w=wp: self.select_wallpaper(w)
                    )
                    btn.pack(fill="x")

                self.status_bar.configure(text=f"Found {len(filtered)} wallpapers" + (f" ({filter_text})" if filter_text != "All Types" else ""))

            def select_wallpaper(self, wp):
                self.current_wallpaper = wp
                self.title_label.configure(text=f"{wp.type_badge}  {wp.title}")
                self.apply_btn.configure(state="normal")

                if wp.preview_path and os.path.exists(wp.preview_path):
                    try:
                        img = Image.open(wp.preview_path)
                        if img.format == 'GIF':
                            img.seek(0)
                            img = img.convert('RGB')
                        orig_w, orig_h = img.size
                        scale = min(700 / orig_w, 350 / orig_h)
                        new_size = (int(orig_w * scale), int(orig_h * scale))
                        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                        self.preview_image = ctk.CTkImage(
                            light_image=img_resized, dark_image=img_resized, size=new_size
                        )
                        self.preview_label.configure(image=self.preview_image, text="")
                        self.preview_label.update_idletasks()
                        self.preview_label.update()
                    except Exception:
                        self.preview_label.configure(image=None, text="Preview error")
                        self.preview_label.update()
                else:
                    self.preview_image = None
                    self.preview_label.configure(image=None, text="No preview")
                    self.preview_label.update()

                self.status_bar.configure(text=f"Selected: {wp.title} ({wp.type_badge})")

            def apply_current_wallpaper(self):
                if self.current_wallpaper:
                    monitor_val = self.monitor_var.get()
                    monitor = None if monitor_val == "All" else monitor_val
                    audio_monitor = self.audio_var.get()
                    ok = WallpaperManager.apply_wallpaper(self.current_wallpaper, monitor, audio_monitor=audio_monitor)
                    if ok:
                        self.status_bar.configure(text=f"Applied: {self.current_wallpaper.title} on {monitor_val}")
                        self._save_to_config(self.current_wallpaper, monitor_val)
                    else:
                        hint = ""
                        if self.current_wallpaper.wallpaper_type != "video" and not WallpaperManager._find_wpe():
                            hint = " (linux-wallpaperengine not found — run setup.sh)"
                        self.status_bar.configure(text=f"FAILED: {self.current_wallpaper.title}{hint}")

            def _save_to_config(self, wp, monitor_val):
                wallpapers = self.config.get("wallpapers", [])
                if monitor_val == "All":
                    self.config["wallpapers"] = [{"workshop_id": wp.workshop_id, "monitor": m} for m in self.monitors]
                else:
                    wallpapers = [w for w in wallpapers if w.get("monitor") != monitor_val]
                    wallpapers.append({"workshop_id": wp.workshop_id, "monitor": monitor_val})
                    self.config["wallpapers"] = wallpapers
                save_config(self.config)

            def stop_wallpaper(self):
                WallpaperManager.stop()
                self.status_bar.configure(text="Wallpaper stopped")

            def toggle_mute(self):
                WallpaperManager.toggle_mute()
                muted = WallpaperManager.is_muted()
                self.mute_btn.configure(text="🔊 Unmute" if muted else "🔇 Mute")
                self.status_bar.configure(text="Muted" if muted else "Unmuted")

            def on_closing(self):
                self.destroy()

        app = PopWallpaperApp()
        app.mainloop()
