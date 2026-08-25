import sys
import os
import json
import re
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
import urllib.request
import webbrowser
import zipfile
import tarfile

if sys.platform == "win32":
    import winsound
else:
    winsound = None

from tkinter import scrolledtext, messagebox, filedialog

from params_config import (
    PARAM_GROUPS,
    BACKEND_DEVICE_KEYS,
    build_default_params,
    normalize_loaded_params,
)
from releases import fetch_windows_assets, fetch_linux_assets, build_download_url
from i18n import I18n, DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

CONFIG_FILE = "llama_config.json"
APP_ICON_ICO_CANDIDATES = [
    "256х256.ico",
    "64х64.ico",
    "48х48.ico",
    "32х32.ico",
    "24х24.ico",
    "16х16.ico",
]
APP_ICON_PNG_CANDIDATES = [
    "256х256.png",
    "64х64.png",
    "32х32.png",
    "24х24.png",
    "16х16.png",
    "icon48х48.png",
]
APP_VERSION = "0.1.6"
APP_AUTHOR = "Dmitry Maksimov"
APP_LICENSE = "MIT"
PARAM_GRID_COLUMNS = 4
LLAMA_CPP_RELEASES_URL = "https://github.com/ggml-org/llama.cpp/releases"
LLAMA_CPP_INSTALL_DIRNAME = "llama.cpp"
LLAMA_SERVER_FILENAME = "llama-server.exe" if sys.platform == "win32" else "llama-server"
LLAMA_CPP_RECOMMENDED_LABEL = "Windows x64 (Vulkan)" if sys.platform == "win32" else "Linux x64 (Vulkan)"


def get_app_base_dir():
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and os.path.isdir(meipass):
            return meipass
        exe_dir = os.path.dirname(sys.executable)
        internal_dir = os.path.join(exe_dir, "_internal")
        if os.path.isdir(internal_dir):
            return internal_dir
        return exe_dir
    return os.path.dirname(os.path.abspath(__file__))


def get_app_path(*parts):
    base = get_app_base_dir()
    return os.path.join(base, *parts)


def get_user_config_dir():
    """Каталог, в который у пользователя гарантированно есть право на запись,
    независимо от того, на какой диск/в какую папку установлено приложение
    (в отличие от папки рядом с exe, которая может быть защищена, например
    C:\\Program Files)."""
    appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    config_dir = os.path.join(appdata, "LLM_Server_Controller")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_user_config_path():
    return os.path.join(get_user_config_dir(), CONFIG_FILE)


class LlamaServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM Server Controller v.0.1.6")
        self.root.geometry("1000x900")
        self.apply_app_icon()

        self.process = None
        self.is_running = False
        self.server_ready = False
        self.loading_blink_job = None
        self.loading_blink_visible = True
        self.manual_stop_requested = False
        self.log_lines = []
        self.current_release_tag = None

        self.default_params = build_default_params()
        self.default_config = self.get_default_config()

        self.config = self.load_config()
        self.i18n = I18n(self.config.get("language", DEFAULT_LANGUAGE))
        self.param_entries = {}
        self.param_group_frames = {}
        self.param_group_meta = {}
        self.params_listbox = None
        self.params_content_canvas = None
        self.params_content_host = None
        self.active_param_group_id = "main"
        self.main_paned = None
        self.enable_loaded_sound_var = tk.BooleanVar(value=self.config.get("sounds", {}).get("loaded", True))
        self.enable_stopped_sound_var = tk.BooleanVar(value=self.config.get("sounds", {}).get("stopped", True))
        self.open_browser_on_load_var = tk.BooleanVar(value=self.config.get("open_browser_on_load", True))
        self.install_in_progress = False

        self.apply_window_geometry()
        self.create_menu()
        self.create_widgets()
        self.apply_config_to_form()
        self.root.after(150, self._init_paned_sash)

    def _init_paned_sash(self):
        if self.main_paned is None:
            return
        try:
            height = self.main_paned.winfo_height()
            if height > 240:
                self.main_paned.sash_place(0, 0, 0, int(height * 0.58))
        except tk.TclError:
            pass

    def apply_app_icon(self):
        ico_paths = []
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                ico_paths.extend(
                    os.path.join(meipass, "icons", name)
                    for name in APP_ICON_ICO_CANDIDATES
                )
                ico_paths.extend(
                    os.path.join(meipass, name)
                    for name in APP_ICON_ICO_CANDIDATES
                )

                icons_dir = os.path.join(meipass, "icons")
                if os.path.isdir(icons_dir):
                    ico_paths.extend(
                        os.path.join(icons_dir, name)
                        for name in sorted(os.listdir(icons_dir))
                        if name.lower().endswith(".ico") and name not in APP_ICON_ICO_CANDIDATES
                    )
                ico_paths.extend(
                    os.path.join(meipass, name)
                    for name in sorted(os.listdir(meipass))
                    if name.lower().endswith(".ico") and name not in APP_ICON_ICO_CANDIDATES
                )

        icons_dir = get_app_path("icons")
        ico_paths.extend(get_app_path("icons", name) for name in APP_ICON_ICO_CANDIDATES)
        if os.path.isdir(icons_dir):
            ico_paths.extend(
                os.path.join(icons_dir, name)
                for name in sorted(os.listdir(icons_dir))
                if name.lower().endswith(".ico") and name not in APP_ICON_ICO_CANDIDATES
            )

        base_dir = get_app_base_dir()
        ico_paths.extend(get_app_path(name) for name in APP_ICON_ICO_CANDIDATES)
        if os.path.isdir(base_dir):
            ico_paths.extend(
                os.path.join(base_dir, name)
                for name in sorted(os.listdir(base_dir))
                if name.lower().endswith(".ico") and name not in APP_ICON_ICO_CANDIDATES
            )

        for icon_path in ico_paths:
            if icon_path and os.path.exists(icon_path):
                try:
                    self.root.iconbitmap(icon_path)
                    return
                except tk.TclError:
                    pass

        png_paths = []
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                png_paths.extend(
                    os.path.join(meipass, "icons", name)
                    for name in APP_ICON_PNG_CANDIDATES
                )
                png_paths.extend(
                    os.path.join(meipass, name)
                    for name in APP_ICON_PNG_CANDIDATES
                )
        png_paths.extend(get_app_path("icons", name) for name in APP_ICON_PNG_CANDIDATES)
        png_paths.extend(get_app_path(name) for name in APP_ICON_PNG_CANDIDATES)

        for icon_path in png_paths:
            if icon_path and os.path.exists(icon_path):
                try:
                    self.window_icon = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, self.window_icon)
                    return
                except tk.TclError:
                    pass

    def create_menu(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label=self.tr("menu_import"), command=self.import_settings)
        file_menu.add_command(label=self.tr("menu_export"), command=self.export_settings)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("menu_install_llama"), command=self.install_llama_cpp)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("menu_exit"), command=self.on_close)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label=self.tr("menu_help_help"), command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label=self.tr("menu_about"), command=self.show_about)

        sound_menu = tk.Menu(menu_bar, tearoff=0)
        sound_menu.add_checkbutton(label=self.tr("menu_sound_loaded"), variable=self.enable_loaded_sound_var, command=self.on_sound_settings_changed)
        sound_menu.add_checkbutton(label=self.tr("menu_sound_stopped"), variable=self.enable_stopped_sound_var, command=self.on_sound_settings_changed)

        params_menu = tk.Menu(menu_bar, tearoff=0)
        for group in PARAM_GROUPS:
            params_menu.add_command(
                label=self.i18n.group_title(group["id"]),
                command=lambda gid=group["id"]: self.show_param_section(gid),
            )

        menu_bar.add_cascade(label=self.tr("menu_file"), menu=file_menu)
        menu_bar.add_cascade(label=self.tr("menu_params"), menu=params_menu)
        menu_bar.add_cascade(label=self.tr("menu_sounds"), menu=sound_menu)
        menu_bar.add_cascade(label=self.tr("menu_help"), menu=help_menu)
        self.root.config(menu=menu_bar)
        self.menu_bar = menu_bar

    def get_default_config(self):
        return {
            "exe_path": "",
            "model_path": "",
            "language": DEFAULT_LANGUAGE,
            "install": {
                "directory": "",
                "asset_label": LLAMA_CPP_RECOMMENDED_LABEL,
                "release_tag": ""
            },
            "window": {
                "width": "1000",
                "height": "900"
            },
            "sounds": {
                "loaded": True,
                "stopped": True
            },
            "open_browser_on_load": True,
            "custom_args": "",
            "params": self.default_params.copy()
        }

    def merge_config(self, loaded_config):
        config = self.get_default_config()
        if not isinstance(loaded_config, dict):
            return config

        config["exe_path"] = loaded_config.get("exe_path", "")
        config["model_path"] = loaded_config.get("model_path", "")

        loaded_language = loaded_config.get("language", "")
        if loaded_language in SUPPORTED_LANGUAGES:
            config["language"] = loaded_language

        loaded_install = loaded_config.get("install", {})
        if isinstance(loaded_install, dict):
            config["install"].update({
                "directory": str(loaded_install.get("directory", config["install"]["directory"])),
                "asset_label": str(loaded_install.get("asset_label", config["install"]["asset_label"])),
                "release_tag": str(loaded_install.get("release_tag", config["install"]["release_tag"])),
            })

        loaded_window = loaded_config.get("window", {})
        if isinstance(loaded_window, dict):
            config["window"].update({
                "width": str(loaded_window.get("width", config["window"]["width"])),
                "height": str(loaded_window.get("height", config["window"]["height"]))
            })

        loaded_sounds = loaded_config.get("sounds", {})
        if isinstance(loaded_sounds, dict):
            config["sounds"].update({
                "loaded": bool(loaded_sounds.get("loaded", config["sounds"]["loaded"])),
                "stopped": bool(loaded_sounds.get("stopped", config["sounds"]["stopped"]))
            })

        config["open_browser_on_load"] = bool(loaded_config.get("open_browser_on_load", config["open_browser_on_load"]))
        loaded_custom_args = loaded_config.get("custom_args", "")
        config["custom_args"] = loaded_custom_args if isinstance(loaded_custom_args, str) else str(loaded_custom_args or "")

        loaded_params = normalize_loaded_params(loaded_config.get("params", {}))
        for param, default_value in self.default_params.items():
            if param in loaded_params:
                value = loaded_params[param]
                if isinstance(default_value, bool):
                    config["params"][param] = bool(value)
                else:
                    config["params"][param] = str(value)

        return config

    def load_config(self, file_path=None):
        if file_path is None:
            file_path = get_user_config_path()

            # Миграция: если пользователь раньше сохранял конфиг рядом с exe
            # (например, на диске, где запись разрешена), а в новом
            # пользовательском каталоге конфига ещё нет — переносим его.
            if not os.path.exists(file_path):
                legacy_path = get_app_path(CONFIG_FILE)
                if os.path.exists(legacy_path):
                    try:
                        shutil.copy2(legacy_path, file_path)
                    except OSError:
                        pass

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return self.merge_config(json.load(f))
            except (OSError, json.JSONDecodeError):
                pass
        return self.get_default_config()

    def collect_form_state(self):
        params = {}
        for param, widget in self.param_entries.items():
            if isinstance(widget, tk.BooleanVar):
                params[param] = widget.get()
            else:
                params[param] = widget.get().strip()

        width = self.window_width_entry.get().strip() if hasattr(self, "window_width_entry") else self.config["window"]["width"]
        height = self.window_height_entry.get().strip() if hasattr(self, "window_height_entry") else self.config["window"]["height"]

        return {
            "exe_path": os.path.normpath(self.exe_entry.get().strip()) if hasattr(self, "exe_entry") else self.config.get("exe_path", ""),
            "model_path": os.path.normpath(self.model_entry.get().strip()) if hasattr(self, "model_entry") else self.config.get("model_path", ""),
            "language": self.i18n.language,
            "install": {
                "directory": self.config.get("install", {}).get("directory", ""),
                "asset_label": self.config.get("install", {}).get("asset_label", LLAMA_CPP_RECOMMENDED_LABEL),
                "release_tag": self.config.get("install", {}).get("release_tag", ""),
            },
            "window": {
                "width": width or self.default_config["window"]["width"],
                "height": height or self.default_config["window"]["height"]
            },
            "sounds": {
                "loaded": self.enable_loaded_sound_var.get(),
                "stopped": self.enable_stopped_sound_var.get()
            },
            "open_browser_on_load": self.open_browser_on_load_var.get(),
            "custom_args": self.custom_args_entry.get().strip() if hasattr(self, "custom_args_entry") else self.config.get("custom_args", ""),
            "params": params
        }

    def save_config(self, file_path=None):
        if file_path is None:
            file_path = get_user_config_path()

        self.config = self.merge_config(self.collect_form_state())
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def tr(self, key, **kwargs):
        return self.i18n.tr(key, **kwargs)

    def _apply_run_state_to_controls(self):
        """Приводит состояние кнопок/статуса в соответствие с is_running/server_ready
        (используется после перестроения интерфейса)."""
        if self.is_running:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.restart_btn.config(state=tk.NORMAL)
            if self.server_ready:
                self.status_label.config(text=self.tr("status_running"), fg="green")
            else:
                self.status_label.config(text=self.tr("status_loading"), fg="#ff9800")
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.restart_btn.config(state=tk.DISABLED)
            self.status_label.config(text=self.tr("status_stopped"), fg="red")
        if self.install_in_progress:
            self.install_llama_btn.config(state=tk.DISABLED, text=self.tr("btn_download_llama_installing"))
        else:
            self.install_llama_btn.config(state=tk.NORMAL, text=self.tr("btn_download_llama"))

    def toggle_language(self):
        """Переключает язык интерфейса RU <-> EN с перестроением окна."""
        if self.is_running:
            messagebox.showwarning(self.tr("msg_attention"), self.tr("msg_reset_while_running"))
            return
        self.i18n.toggle()
        self.config["language"] = self.i18n.language
        self.rebuild_ui()
        self.save_config()

    def _capture_form_state(self):
        """Снимок значений формы (пути, размеры, параметры) для восстановления
        после перестроения интерфейса."""
        snapshot = {}
        if hasattr(self, "exe_entry"):
            snapshot["exe_path"] = self.exe_entry.get()
        if hasattr(self, "model_entry"):
            snapshot["model_path"] = self.model_entry.get()
        if hasattr(self, "window_width_entry"):
            snapshot["width"] = self.window_width_entry.get()
        if hasattr(self, "window_height_entry"):
            snapshot["height"] = self.window_height_entry.get()
        if hasattr(self, "custom_args_entry"):
            snapshot["custom_args"] = self.custom_args_entry.get()
        for param, widget in self.param_entries.items():
            if isinstance(widget, tk.BooleanVar):
                snapshot[param] = widget.get()
            else:
                snapshot[param] = widget.get()
        return snapshot

    def _restore_form_snapshot(self, snapshot):
        if not snapshot:
            return
        if "exe_path" in snapshot and hasattr(self, "exe_entry"):
            self.exe_entry.delete(0, tk.END)
            self.exe_entry.insert(0, snapshot["exe_path"])
        if "model_path" in snapshot and hasattr(self, "model_entry"):
            self.model_entry.delete(0, tk.END)
            self.model_entry.insert(0, snapshot["model_path"])
        if "width" in snapshot and hasattr(self, "window_width_entry"):
            self.window_width_entry.delete(0, tk.END)
            self.window_width_entry.insert(0, snapshot["width"])
        if "height" in snapshot and hasattr(self, "window_height_entry"):
            self.window_height_entry.delete(0, tk.END)
            self.window_height_entry.insert(0, snapshot["height"])
        if "custom_args" in snapshot and hasattr(self, "custom_args_entry"):
            self.custom_args_entry.delete(0, tk.END)
            self.custom_args_entry.insert(0, snapshot["custom_args"])
        for param, widget in self.param_entries.items():
            if param not in snapshot:
                continue
            value = snapshot[param]
            if isinstance(widget, tk.BooleanVar):
                widget.set(bool(value))
            else:
                widget.delete(0, tk.END)
                widget.insert(0, str(value))

    def rebuild_ui(self):
        """Уничтожает и заново создаёт меню и виджеты на текущем языке,
        сохраняя значения полей и состояние выполнения."""
        snapshot = self._capture_form_state()
        try:
            self.root.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
        self.param_entries = {}
        self.param_group_frames = {}
        self.param_group_meta = {}

        for child in self.root.winfo_children():
            child.destroy()

        # контекстное меню лога создается внутри create_widgets
        self.create_menu()
        self.create_widgets()
        self._restore_form_snapshot(snapshot)
        self.root.after(150, self._init_paned_sash)

    def apply_window_geometry(self):
        window_cfg = self.config.get("window", {})
        width = window_cfg.get("width", "1000")
        height = window_cfg.get("height", "900")
        if width.isdigit() and height.isdigit():
            self.root.geometry(f"{width}x{height}")

    def apply_config_to_form(self):
        self.exe_entry.delete(0, tk.END)
        self.exe_entry.insert(0, self.config.get("exe_path", ""))

        self.model_entry.delete(0, tk.END)
        self.model_entry.insert(0, self.config.get("model_path", ""))

        window_cfg = self.config.get("window", {})
        self.window_width_entry.delete(0, tk.END)
        self.window_width_entry.insert(0, window_cfg.get("width", "1000"))
        self.window_height_entry.delete(0, tk.END)
        self.window_height_entry.insert(0, window_cfg.get("height", "900"))

        if hasattr(self, "custom_args_entry"):
            self.custom_args_entry.delete(0, tk.END)
            self.custom_args_entry.insert(0, self.config.get("custom_args", ""))

        params = self.config.get("params", {})
        for param, widget in self.param_entries.items():
            value = params.get(param, self.default_params[param])
            if isinstance(widget, tk.BooleanVar):
                widget.set(bool(value))
            else:
                widget.delete(0, tk.END)
                widget.insert(0, str(value))

    def create_widgets(self):
        path_frame = tk.LabelFrame(self.root, text=" " + self.tr("frame_paths") + " ", padx=8, pady=4)
        path_frame.pack(fill=tk.X, padx=10, pady=(8, 4))
        self.path_frame = path_frame

        tk.Label(path_frame, text=self.tr("label_server")).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.exe_entry = tk.Entry(path_frame)
        self.exe_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        tk.Button(path_frame, text=self.tr("btn_browse"), command=self.browse_exe).grid(row=0, column=2, padx=2, pady=2)
        self.install_llama_btn = tk.Button(path_frame, text=self.tr("btn_download_llama"), command=self.install_llama_cpp)
        self.install_llama_btn.grid(row=0, column=3, padx=2, pady=2)
        self.list_devices_btn = tk.Button(
            path_frame, text=self.tr("btn_devices"), command=self.list_devices,
        )
        self.list_devices_btn.grid(row=0, column=4, padx=2, pady=2)

        tk.Label(path_frame, text=self.tr("label_model")).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.model_entry = tk.Entry(path_frame)
        self.model_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        tk.Button(path_frame, text=self.tr("btn_browse"), command=self.browse_model).grid(row=1, column=2, padx=2, pady=2)

        size_frame = tk.Frame(path_frame)
        size_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(2, 0))
        tk.Label(size_frame, text=self.tr("label_window_size")).pack(side=tk.LEFT)
        self.window_width_entry = tk.Entry(size_frame, width=6)
        self.window_width_entry.pack(side=tk.LEFT, padx=(6, 2))
        tk.Label(size_frame, text="×").pack(side=tk.LEFT)
        self.window_height_entry = tk.Entry(size_frame, width=6)
        self.window_height_entry.pack(side=tk.LEFT, padx=(2, 0))

        tk.Label(path_frame, text=self.tr("label_commands")).grid(row=3, column=0, sticky=tk.W, pady=2)
        self.custom_args_entry = tk.Entry(path_frame, font=("Consolas", 9))
        self.custom_args_entry.grid(row=3, column=1, columnspan=4, sticky=tk.EW, padx=5, pady=2)
        path_frame.columnconfigure(1, weight=1)

        toolbar = tk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=4)
        self.toolbar = toolbar

        tk.Button(toolbar, text=self.tr("btn_save"), command=self.save_current_settings).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(toolbar, text=self.tr("btn_import"), command=self.import_settings).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text=self.tr("btn_export"), command=self.export_settings).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text=self.tr("btn_reset"), command=self.reset_settings).pack(side=tk.LEFT, padx=4)

        tk.Frame(toolbar, width=24).pack(side=tk.LEFT)

        self.start_btn = tk.Button(
            toolbar, text=self.tr("btn_start"), bg="#4CAF50", fg="white",
            font=("Arial", 10, "bold"), command=self.start_server,
        )
        self.start_btn.pack(side=tk.LEFT, padx=4)

        self.stop_btn = tk.Button(
            toolbar, text=self.tr("btn_stop"), bg="#f44336", fg="white",
            font=("Arial", 10, "bold"), command=self.stop_server, state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        self.restart_btn = tk.Button(
            toolbar, text=self.tr("btn_restart"), bg="#ff9800", fg="white",
            font=("Arial", 10, "bold"), command=self.restart_server, state=tk.DISABLED,
        )
        self.restart_btn.pack(side=tk.LEFT, padx=4)

        tk.Frame(toolbar, width=12).pack(side=tk.LEFT)

        self.open_browser_on_load_chk = tk.Checkbutton(
            toolbar, text=self.tr("chk_open_browser"), variable=self.open_browser_on_load_var,
            font=("Arial", 9), command=self.on_browser_checkbox_changed,
        )
        self.open_browser_on_load_chk.pack(side=tk.LEFT, padx=4)

        self.lang_btn = tk.Button(
            toolbar, text=self.tr("btn_lang_" + self.i18n.language),
            font=("Arial", 9, "bold"), width=4, command=self.toggle_language,
        )
        self.lang_btn.pack(side=tk.LEFT, padx=4)

        self.status_label = tk.Label(toolbar, text=self.tr("status_stopped"), fg="red", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT, padx=4)

        self.main_paned = tk.PanedWindow(
            self.root, orient=tk.VERTICAL, sashwidth=7, sashrelief=tk.RAISED, showhandle=True,
        )
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        params_outer = tk.LabelFrame(self.main_paned, text=" " + self.tr("frame_params") + " ", padx=6, pady=4)
        self.main_paned.add(params_outer, minsize=320, stretch="always")

        params_body = tk.Frame(params_outer)
        params_body.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(params_body, width=210)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text=self.tr("label_categories"), font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 4))

        list_frame = tk.Frame(sidebar)
        list_frame.pack(fill=tk.BOTH, expand=True)

        list_scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.params_listbox = tk.Listbox(
            list_frame,
            activestyle=tk.NONE,
            exportselection=False,
            font=("Segoe UI", 9),
            highlightthickness=1,
            yscrollcommand=list_scroll.set,
        )
        list_scroll.config(command=self.params_listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.params_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for index, group in enumerate(PARAM_GROUPS):
            prefix = "   " if group.get("backend") else ""
            self.params_listbox.insert(tk.END, f"{prefix}{self.i18n.group_title(group['id'])}")
            self.param_group_meta[index] = group["id"]

        self.params_listbox.bind("<<ListboxSelect>>", self._on_param_group_selected)

        content_panel = tk.Frame(params_body)
        content_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.group_title_label = tk.Label(content_panel, text="", font=("Arial", 10, "bold"), anchor=tk.W)
        self.group_title_label.pack(fill=tk.X, pady=(0, 2))

        self.group_hint_label = tk.Label(
            content_panel, text="", font=("Arial", 8), fg="#555555",
            anchor=tk.W, justify=tk.LEFT, wraplength=720,
        )
        self.group_hint_label.pack(fill=tk.X, pady=(0, 6))

        content_scrollbar = tk.Scrollbar(content_panel, orient=tk.VERTICAL)
        self.params_content_canvas = tk.Canvas(
            content_panel,
            highlightthickness=0,
            yscrollcommand=content_scrollbar.set,
        )
        content_scrollbar.config(command=self.params_content_canvas.yview)
        content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.params_content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.params_content_host = tk.Frame(self.params_content_canvas)
        self.params_content_window = self.params_content_canvas.create_window(
            (0, 0), window=self.params_content_host, anchor=tk.NW,
        )

        self.params_content_host.bind(
            "<Configure>",
            lambda _event: self.params_content_canvas.configure(
                scrollregion=self.params_content_canvas.bbox("all"),
            ),
        )
        self.params_content_canvas.bind(
            "<Configure>",
            lambda event: self.params_content_canvas.itemconfig(
                self.params_content_window, width=event.width,
            ),
        )
        self.params_content_canvas.bind_all("<MouseWheel>", self._on_params_mousewheel, add="+")

        for group in PARAM_GROUPS:
            group_frame = tk.Frame(self.params_content_host, padx=4, pady=2)
            self.param_group_frames[group["id"]] = group_frame
            self._build_param_group_grid(group_frame, group)

        log_container = tk.Frame(self.main_paned)
        self.main_paned.add(log_container, minsize=140, stretch="always")

        log_header_frame = tk.Frame(log_container)
        log_header_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 4))

        tk.Label(log_header_frame, text=self.tr("label_server_logs"), font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        copy_btn = tk.Button(log_header_frame, text=self.tr("btn_copy"), font=("Arial", 8), command=self.copy_logs_to_clipboard)
        copy_btn.pack(side=tk.RIGHT, padx=4)

        clear_btn = tk.Button(log_header_frame, text=self.tr("btn_clear"), font=("Arial", 8), command=self.clear_logs)
        clear_btn.pack(side=tk.RIGHT, padx=4)

        save_log_btn = tk.Button(log_header_frame, text=self.tr("btn_save_log"), font=("Arial", 8), command=self.save_logs)
        save_log_btn.pack(side=tk.RIGHT, padx=4)

        self.log_area = scrolledtext.ScrolledText(
            log_container,
            wrap=tk.WORD,
            bg="#1e1e1e",
            fg="#d4d4d4",
            font=("Consolas", 9),
        )
        self.log_area.pack(expand=True, fill=tk.BOTH)

        self.log_area.insert("1.0", "".join(self.log_lines))
        self.log_area.see(tk.END)

        self.log_context_menu = tk.Menu(self.root, tearoff=0)
        self.log_context_menu.add_command(label=self.tr("btn_copy"), command=self.copy_logs_to_clipboard)
        self.log_area.bind("<Button-3>", self.show_log_context_menu)
        self.log_area.bind("<Double-Button-1>", self.show_log_context_menu)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._apply_run_state_to_controls()

        self.show_param_group(self.active_param_group_id)

    def _build_param_group_grid(self, parent, group):
        row, col = 0, 0
        for spec in group["params"]:
            param = spec["key"]
            value = self.default_params[param]
            hint = self.i18n.param_hint(param, spec.get("hint", ""))

            cell = tk.Frame(parent, padx=6, pady=4)
            cell.grid(row=row, column=col, sticky=tk.NW)

            tk.Label(cell, text=param, font=("Consolas", 9, "bold"), anchor=tk.W).pack(fill=tk.X)

            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                chk = tk.Checkbutton(cell, text=self.tr("chk_enable"), variable=var, font=("Arial", 9))
                chk.pack(anchor=tk.W, pady=(2, 0))
                self.param_entries[param] = var
            else:
                ent = tk.Entry(cell, width=16, font=("Consolas", 9))
                ent.insert(0, str(value))
                ent.pack(anchor=tk.W, pady=(2, 0))
                self.param_entries[param] = ent

            if hint:
                tk.Label(cell, text=hint, font=("Arial", 8), fg="#777777", wraplength=180, justify=tk.LEFT).pack(
                    anchor=tk.W, pady=(2, 0),
                )

            col += 1
            if col >= PARAM_GRID_COLUMNS:
                col = 0
                row += 1

        for column in range(PARAM_GRID_COLUMNS):
            parent.columnconfigure(column, weight=1, uniform="param_cols")

    def _on_param_group_selected(self, _event=None):
        selection = self.params_listbox.curselection()
        if not selection:
            return
        group_id = self.param_group_meta.get(selection[0])
        if group_id:
            self.show_param_group(group_id, from_listbox=True)

    def show_param_group(self, group_id, from_listbox=False):
        if group_id not in self.param_group_frames:
            return

        self.active_param_group_id = group_id
        for frame in self.param_group_frames.values():
            frame.pack_forget()

        active_frame = self.param_group_frames[group_id]
        active_frame.pack(fill=tk.BOTH, expand=True)
        self.params_content_canvas.yview_moveto(0)

        group = next((item for item in PARAM_GROUPS if item["id"] == group_id), None)
        if group:
            self.group_title_label.config(text=self.i18n.group_title(group["id"]))
            self.group_hint_label.config(text=self.i18n.group_hint(group["id"]) or group.get("hint", ""))

        if not from_listbox:
            for index, gid in self.param_group_meta.items():
                if gid == group_id:
                    self.params_listbox.selection_clear(0, tk.END)
                    self.params_listbox.selection_set(index)
                    self.params_listbox.see(index)
                    break

    def browse_exe(self):
        if sys.platform == "win32":
            title = self.tr("title_select_exe_win")
            filetypes = [(self.tr("ft_executables_win"), "*.exe"), (self.tr("ft_all_files"), "*.*")]
        else:
            title = self.tr("title_select_exe_unix")
            filetypes = [(self.tr("ft_executables_unix"), "*"), (self.tr("ft_all_files"), "*.*")]
        file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if file_path:
            self.exe_entry.delete(0, tk.END)
            self.exe_entry.insert(0, os.path.normpath(file_path))

    def install_llama_cpp(self):
        if self.install_in_progress:
            messagebox.showinfo(self.tr("menu_install_llama"), self.tr("msg_install_already_running"))
            return
        if self.is_running:
            messagebox.showwarning(self.tr("msg_attention"), self.tr("msg_install_while_running"))
            return

        self.install_in_progress = True
        self.install_llama_btn.config(state=tk.DISABLED, text=self.tr("btn_download_llama_progress"))
        self.log(self.tr("log_fetch_assets"))
        threading.Thread(
            target=self._fetch_assets_and_prompt,
            daemon=True,
        ).start()

    def _fetch_assets_and_prompt(self):
        try:
            if sys.platform == "win32":
                tag, assets, warning = fetch_windows_assets(timeout=45, language=self.i18n.language)
            else:
                tag, assets, warning = fetch_linux_assets(timeout=45, language=self.i18n.language)
            self.root.after(0, lambda: self._on_assets_loaded(tag, assets, warning))
        except Exception as exc:
            error_message = str(exc) or exc.__class__.__name__
            self.root.after(0, lambda message=error_message: self._handle_llama_install_error(message))
            self.root.after(0, self._reset_install_controls)

    def _on_assets_loaded(self, tag, assets, warning):
        self.install_in_progress = False
        self.install_llama_btn.config(state=tk.NORMAL, text=self.tr("btn_download_llama"))
        self.current_release_tag = tag
        if warning:
            self.log(f"{warning}\n")
        self.log(f"{self.tr('msg_release_info')}: {tag}, {self.tr('msg_builds_count')}: {len(assets)}\n")

        selected_asset = self._prompt_llama_asset(assets, tag)
        if not selected_asset:
            return

        default_dir = self.config.get("install", {}).get("directory") or os.path.join(os.getcwd(), "llama.cpp")
        install_dir = filedialog.askdirectory(
            title=self.tr("title_select_install_dir"),
            initialdir=default_dir if os.path.isdir(default_dir) else os.getcwd(),
            mustexist=False,
        )
        if not install_dir:
            return

        install_dir = os.path.normpath(install_dir)
        if os.path.isfile(install_dir):
            messagebox.showerror(self.tr("msg_error"), self.tr("msg_install_path_is_file"))
            return

        if os.path.isdir(install_dir) and os.listdir(install_dir):
            overwrite = messagebox.askyesno(
                self.tr("msg_confirm"),
                self.tr("msg_install_dir_not_empty"),
            )
            if not overwrite:
                return

        self.install_in_progress = True
        self.install_llama_btn.config(state=tk.DISABLED, text=self.tr("btn_download_llama_installing"))
        self.log(
            f"--- {self.tr('log_install_header')} ---\n{self.tr('log_source')} {LLAMA_CPP_RELEASES_URL}\n"
            f"{self.tr('log_release')} {tag}\n{self.tr('log_variant')} {selected_asset['label']}\n{self.tr('log_folder')} {install_dir}\n\n"
        )
        threading.Thread(
            target=self._install_llama_cpp_worker,
            args=(selected_asset, install_dir, tag),
            daemon=True,
        ).start()

    def _prompt_llama_asset(self, assets, release_tag):
        selected_value = {"asset": None}
        platform_label = "Windows" if sys.platform == "win32" else "Linux"
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{self.tr('title_select_build')} ({release_tag})")
        dialog.geometry("560x460")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(
            dialog,
            text=self.tr("msg_select_build", platform=platform_label, tag=release_tag),
            font=("Arial", 10, "bold"),
            anchor=tk.W,
            justify=tk.LEFT,
        ).pack(fill=tk.X, padx=12, pady=(12, 6))

        tk.Label(
            dialog,
            text=self.tr("msg_select_build_hint"),
            fg="#555555",
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=520,
        ).pack(fill=tk.X, padx=12, pady=(0, 8))

        list_frame = tk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        listbox = tk.Listbox(list_frame, exportselection=False, yscrollcommand=scrollbar.set, height=14)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        remembered_label = self.config.get("install", {}).get("asset_label", "")
        default_index = next(
            (index for index, asset in enumerate(assets) if asset.get("recommended")),
            0,
        )
        recommended_suffix_default = self.tr("msg_recommended_suffix")
        for index, asset in enumerate(assets):
            if not asset.get("label"):
                continue
            suffix = " + CUDA DLLs" if asset.get("dll_asset") else ""
            recommended_suffix = recommended_suffix_default if asset.get("recommended") else ""
            size = asset.get("size") or 0
            size_suffix = f" ({size / (1024 ** 2):.0f} MB)" if size else ""
            listbox.insert(tk.END, f"{asset['label']}{suffix}{recommended_suffix}{size_suffix}")
            if asset["label"] == remembered_label:
                default_index = index
        if assets:
            listbox.selection_set(default_index)
            listbox.see(default_index)

        buttons = tk.Frame(dialog)
        buttons.pack(fill=tk.X, padx=12, pady=(8, 12))

        def confirm_selection(_event=None):
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning(self.tr("msg_choice_required"), self.tr("msg_select_one_build"), parent=dialog)
                return
            selected_value["asset"] = assets[selection[0]]
            dialog.destroy()

        def cancel_selection():
            dialog.destroy()

        listbox.bind("<Double-Button-1>", confirm_selection)
        tk.Button(buttons, text=self.tr("btn_install_confirm"), command=confirm_selection).pack(side=tk.RIGHT, padx=(4, 0))
        tk.Button(buttons, text=self.tr("btn_cancel"), command=cancel_selection).pack(side=tk.RIGHT)

        self.root.wait_window(dialog)
        return selected_value["asset"]

    def _install_llama_cpp_worker(self, selected_asset, install_dir, release_tag):
        archive_url = build_download_url(release_tag, selected_asset["asset"], selected_asset)
        dll_asset = selected_asset.get("dll_asset")
        dll_url = build_download_url(release_tag, dll_asset, None) if dll_asset else None
        temp_dir = tempfile.mkdtemp(prefix="llama_cpp_install_")

        try:
            os.makedirs(install_dir, exist_ok=True)
            main_archive_path = os.path.join(temp_dir, selected_asset["asset"])
            self._download_file(archive_url, main_archive_path, selected_asset["asset"], release_tag)
            if sys.platform == "win32":
                self._extract_zip(main_archive_path, install_dir)
            else:
                self._extract_tar_gz(main_archive_path, install_dir)

            if dll_url and dll_asset:
                dll_archive_path = os.path.join(temp_dir, dll_asset)
                self._download_file(dll_url, dll_archive_path, dll_asset, release_tag)
                self._extract_zip(dll_archive_path, install_dir)

            exe_path = self._find_llama_server(install_dir)
            if not exe_path:
                raise FileNotFoundError(self.tr("err_server_not_found", exe=LLAMA_SERVER_FILENAME))
            if sys.platform != "win32":
                os.chmod(exe_path, os.stat(exe_path).st_mode | 0o111)
            if dll_asset:
                self._copy_dlls_to_exe_dir(install_dir, os.path.dirname(exe_path))

            self.root.after(
                0,
                lambda: self._finish_llama_install(selected_asset, install_dir, exe_path, release_tag),
            )
        except Exception as exc:
            error_message = str(exc) or exc.__class__.__name__
            self.root.after(0, lambda message=error_message: self._handle_llama_install_error(message))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            self.root.after(0, self._reset_install_controls)

    def _download_file(self, url, destination_path, display_name, release_tag=None):
        tag = release_tag or self.current_release_tag or "b9870"
        self.root.after(
            0,
            lambda: self.log(
                f"{self.tr('log_downloading')} {display_name}\n{self.tr('log_source')} {LLAMA_CPP_RELEASES_URL}\n{self.tr('log_release')} {tag}\nURL: {url}\n"
            ),
        )
        request = urllib.request.Request(url, headers={"User-Agent": "LLM-Server-Controller/0.1"})
        with urllib.request.urlopen(request) as response, open(destination_path, "wb") as target:
            total = response.headers.get("Content-Length")
            total_size = int(total) if total and total.isdigit() else 0
            downloaded = 0

            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                target.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = int(downloaded * 100 / total_size)
                    self.root.after(0, lambda p=percent, name=display_name: self.install_llama_btn.config(text=f"{p}% {name[:18]}"))

        self.root.after(0, lambda: self.log(f"{self.tr('log_download_complete')} {display_name}\n"))

    def _extract_zip(self, archive_path, install_dir):
        self.root.after(0, lambda: self.log(f"{self.tr('log_extracting')} {os.path.basename(archive_path)} -> {install_dir}\n"))
        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(install_dir)

    def _extract_tar_gz(self, archive_path, install_dir):
        self.root.after(0, lambda: self.log(f"{self.tr('log_extracting')} {os.path.basename(archive_path)} -> {install_dir}\n"))
        install_dir = os.path.abspath(install_dir)
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive.getmembers():
                member_path = os.path.abspath(os.path.join(install_dir, member.name))
                if not (member_path == install_dir or member_path.startswith(install_dir + os.sep)):
                    raise RuntimeError(self.tr("err_unsafe_archive_path", name=member.name))
            archive.extractall(install_dir)

    def _find_llama_server(self, install_dir):
        for root_dir, _dirs, files in os.walk(install_dir):
            if LLAMA_SERVER_FILENAME in files:
                return os.path.normpath(os.path.join(root_dir, LLAMA_SERVER_FILENAME))
        return ""

    def _copy_dlls_to_exe_dir(self, install_dir, exe_dir):
        copied = 0
        for root_dir, _dirs, files in os.walk(install_dir):
            if os.path.normcase(os.path.normpath(root_dir)) == os.path.normcase(os.path.normpath(exe_dir)):
                continue
            for file_name in files:
                if file_name.lower().endswith(".dll"):
                    source_path = os.path.join(root_dir, file_name)
                    destination_path = os.path.join(exe_dir, file_name)
                    if os.path.normcase(source_path) != os.path.normcase(destination_path):
                        shutil.copy2(source_path, destination_path)
                        copied += 1
        if copied:
            self.root.after(0, lambda: self.log(self.tr("log_dll_copied", count=copied)))

    def _finish_llama_install(self, selected_asset, install_dir, exe_path, release_tag):
        self.exe_entry.delete(0, tk.END)
        self.exe_entry.insert(0, exe_path)
        self.config["install"] = {
            "directory": install_dir,
            "asset_label": selected_asset["label"],
            "release_tag": release_tag,
        }
        self.save_config()
        self.log(self.tr("log_exe_found", path=exe_path))
        messagebox.showinfo(
            self.tr("msg_install_complete"),
            self.tr("msg_install_complete_body", dir=install_dir, label=selected_asset['label'], exe_name=LLAMA_SERVER_FILENAME, exe_path=exe_path),
        )

    def _handle_llama_install_error(self, error_message):
        self.log(self.tr("msg_install_error_log", error=error_message))
        messagebox.showerror(self.tr("msg_install_error"), error_message)

    def _reset_install_controls(self):
        self.install_in_progress = False
        self.install_llama_btn.config(state=tk.NORMAL, text=self.tr("btn_download_llama"))

    def _get_hidden_startupinfo(self):
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            return startupinfo
        return None

    def list_devices(self):
        exe_path = os.path.normpath(self.exe_entry.get().strip())
        if not exe_path or not os.path.exists(exe_path):
            messagebox.showerror(self.tr("msg_error"), self.tr("err_invalid_exe", exe=LLAMA_SERVER_FILENAME))
            return

        self.list_devices_btn.config(state=tk.DISABLED, text=self.tr("btn_devices_loading"))
        threading.Thread(target=self._run_list_devices, args=(exe_path,), daemon=True).start()

    def _run_list_devices(self, exe_path):
        cmd = [exe_path, "--list-devices"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=self._get_hidden_startupinfo(),
                timeout=30,
            )
            output = result.stdout or ""
            if result.stderr:
                if output:
                    output += "\n"
                output += result.stderr
            if not output.strip():
                output = self.tr("msg_empty_output", code=result.returncode)

            title = self.tr("title_devices_ok")
            if result.returncode != 0:
                title = self.tr("title_devices_error", code=result.returncode)

            self.root.after(0, lambda: self._show_devices_result(title, output, cmd))
        except subprocess.TimeoutExpired:
            self.root.after(
                0,
                lambda: messagebox.showerror(self.tr("msg_error"), self.tr("err_list_devices_timeout")),
            )
        except OSError as exc:
            self.root.after(0, lambda: messagebox.showerror(self.tr("msg_error"), str(exc)))
        finally:
            self.root.after(0, self._list_devices_finished)

    def _list_devices_finished(self):
        self.list_devices_btn.config(state=tk.NORMAL, text=self.tr("btn_devices"))

    def _show_devices_result(self, title, output, cmd):
        self.log(f"--- {title} ---\n{self.tr('log_command')} {' '.join(cmd)}\n\n{output}\n")

        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("760x440")
        window.transient(self.root)

        tk.Label(
            window,
            text=" ".join(cmd),
            font=("Consolas", 9),
            fg="#555555",
            anchor=tk.W,
        ).pack(fill=tk.X, padx=10, pady=(10, 4))

        text_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, font=("Consolas", 10))
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=4)
        text_area.insert("1.0", output)
        text_area.config(state=tk.DISABLED)

        btn_frame = tk.Frame(window)
        btn_frame.pack(pady=(0, 10))

        def copy_output():
            self.root.clipboard_clear()
            self.root.clipboard_append(output)
            self.root.update()

        tk.Button(btn_frame, text=self.tr("btn_copy"), command=copy_output).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text=self.tr("btn_close"), command=window.destroy).pack(side=tk.LEFT, padx=4)

    def browse_model(self):
        file_path = filedialog.askopenfilename(
            title=self.tr("title_select_model"),
            filetypes=[(self.tr("ft_gguf"), "*.gguf"), (self.tr("ft_all_files"), "*.*")]
        )
        if file_path:
            self.model_entry.delete(0, tk.END)
            self.model_entry.insert(0, os.path.normpath(file_path))

    def save_current_settings(self):
        try:
            self.save_config()
            self.apply_window_size_from_fields()
            messagebox.showinfo(self.tr("msg_success"), self.tr("msg_settings_saved", file=CONFIG_FILE))
        except OSError as exc:
            messagebox.showerror(self.tr("msg_save_error"), str(exc))

    def on_sound_settings_changed(self):
        self.save_config()

    def on_browser_checkbox_changed(self):
        self.save_config()

    def play_loaded_sound(self):
        if sys.platform == "win32" and self.enable_loaded_sound_var.get():
            winsound.MessageBeep(winsound.MB_ICONASTERISK)

    def play_stopped_sound(self):
        if sys.platform == "win32" and self.enable_stopped_sound_var.get():
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

    def start_loading_blink(self):
        self.stop_loading_blink()
        self.loading_blink_visible = True
        self.animate_loading_status()

    def stop_loading_blink(self):
        if self.loading_blink_job is not None:
            self.root.after_cancel(self.loading_blink_job)
            self.loading_blink_job = None
        self.loading_blink_visible = True

    def animate_loading_status(self):
        if not self.is_running or self.server_ready:
            self.loading_blink_job = None
            return

        self.loading_blink_visible = not self.loading_blink_visible
        color = "#ff9800" if self.loading_blink_visible else "#ffd180"
        self.status_label.config(text=self.tr("status_loading"), fg=color)
        self.loading_blink_job = self.root.after(500, self.animate_loading_status)

    def set_loading_error_state(self):
        self.stop_loading_blink()
        self.status_label.config(text=self.tr("status_load_error"), fg="#b00020")

    def import_settings(self):
        file_path = filedialog.askopenfilename(
            title=self.tr("title_import"),
            filetypes=[(self.tr("ft_json"), "*.json"), (self.tr("ft_all_files"), "*.*")]
        )
        if not file_path:
            return

        imported_config = self.load_config(file_path)
        self.config = imported_config
        self.i18n.set_language(self.config.get("language", self.i18n.language))
        self.apply_window_geometry()
        self.apply_config_to_form()
        self.save_config()
        messagebox.showinfo(self.tr("title_import"), self.tr("msg_import_done"))

    def export_settings(self):
        file_path = filedialog.asksaveasfilename(
            title=self.tr("title_export"),
            defaultextension=".json",
            filetypes=[(self.tr("ft_json"), "*.json"), (self.tr("ft_all_files"), "*.*")]
        )
        if not file_path:
            return

        try:
            export_config = self.merge_config(self.collect_form_state())
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_config, f, ensure_ascii=False, indent=4)
            messagebox.showinfo(self.tr("title_export"), self.tr("msg_export_done", path=file_path))
        except OSError as exc:
            messagebox.showerror(self.tr("msg_export_error"), str(exc))

    def reset_settings(self):
        if self.is_running:
            messagebox.showwarning(self.tr("msg_attention"), self.tr("msg_reset_while_running"))
            return

        self.config = self.get_default_config()
        self.i18n.set_language(self.config.get("language", self.i18n.language))
        self.apply_window_geometry()
        self.apply_config_to_form()
        self.save_config()
        messagebox.showinfo(self.tr("msg_success"), self.tr("msg_reset_done"))

    def apply_window_size_from_fields(self):
        width = self.window_width_entry.get().strip()
        height = self.window_height_entry.get().strip()
        if width.isdigit() and height.isdigit():
            self.root.geometry(f"{width}x{height}")

    def show_help(self):
        help_text = self.i18n.help_text()

        help_window = tk.Toplevel(self.root)
        help_window.title(self.tr("title_help"))
        help_window.geometry("760x620")
        help_window.transient(self.root)

        text_area = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=("Segoe UI", 10))
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        text_area.insert("1.0", help_text)
        text_area.config(state=tk.DISABLED)

        close_btn = tk.Button(help_window, text=self.tr("btn_close"), command=help_window.destroy)
        close_btn.pack(pady=(0, 10))

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title(self.tr("title_about"))
        about_window.transient(self.root)
        about_window.grab_set()

        info_lines = [
            ("LLM Server Controller", None),
            (f"Version: {APP_VERSION}", None),
            (f"Author: {APP_AUTHOR}", None),
            (f"License: {APP_LICENSE}", None),
        ]

        for text, url in info_lines:
            lbl = tk.Label(about_window, text=text, justify=tk.LEFT, padx=20, pady=2)
            lbl.pack(anchor="w")

        website_link = tk.Label(about_window, text="Website: https://llm-server.github.io/", justify=tk.LEFT, padx=20, pady=2, fg="blue", cursor="hand2")
        website_link.pack(anchor="w")
        website_link.bind("<Button-1>", lambda e: webbrowser.open("https://llm-server.github.io/"))

        donate_btn = tk.Button(about_window, text="Donate", command=lambda: webbrowser.open("pay.heleket.com/wallet/61486d55-7249-4cab-8596-fbd38b3e9047"))
        donate_btn.pack(pady=(10, 10))

        close_btn = tk.Button(about_window, text="OK", command=about_window.destroy)
        close_btn.pack(pady=(0, 10))

    def _on_params_mousewheel(self, event):
        if self.params_content_canvas is None:
            return
        widget = event.widget
        while widget is not None:
            if widget in (self.params_content_canvas, self.params_content_host):
                self.params_content_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return
            widget = getattr(widget, "master", None)

    def show_param_section(self, section_id):
        self.show_param_group(section_id)

    def get_param_value(self, param):
        widget = self.param_entries.get(param)
        if widget is None:
            return None
        if isinstance(widget, tk.BooleanVar):
            return widget.get()
        return widget.get().strip()

    def generate_args(self):
        model_path = os.path.normpath(self.model_entry.get().strip()) if hasattr(self, "model_entry") else ""
        model_name = os.path.splitext(os.path.basename(model_path))[0] if model_path else ""

        dynamic_args = []
        for param, widget in self.param_entries.items():
            if param in BACKEND_DEVICE_KEYS:
                continue
            if isinstance(widget, tk.BooleanVar):
                if widget.get():
                    dynamic_args.append(param)
            else:
                val = widget.get().strip()
                if val:
                    val = val.replace("{model_name}", model_name).replace("{alias}", model_name)
                    dynamic_args.extend([param, val])

        device_value = self.get_param_value("--device") or ""
        if not device_value:
            for key in BACKEND_DEVICE_KEYS:
                val = self.get_param_value(key) or ""
                if val:
                    device_value = val
                    break

        if device_value:
            dynamic_args.extend(["--device", device_value])

        return dynamic_args

    def parse_custom_args(self, raw_args):
        """Разбирает строку дополнительных аргументов в список токенов,
        сохраняя аргументы со пробелами, взятые в двойные кавычки."""
        if not raw_args:
            return []

        tokens = []
        regex = re.compile(r'"((?:[^"\\]|\\.)*)"|(\S+)')
        for match in regex.finditer(raw_args):
            if match.group(1) is not None:
                tokens.append(match.group(1))
            else:
                tokens.append(match.group(2))

        return tokens

    def get_custom_args(self):
        if not hasattr(self, "custom_args_entry"):
            return []
        raw = self.custom_args_entry.get().strip()
        return self.parse_custom_args(raw)

    def append_log(self, text):
        self.log_lines.append(text)
        self.log_area.insert(tk.END, text)
        self.log_area.see(tk.END)

    def log(self, text):
        self.root.after(0, lambda: self.append_log(text))

    def clear_logs(self):
        self.log_lines.clear()
        self.log_area.delete("1.0", tk.END)

    def show_log_context_menu(self, event):
        try:
            self.log_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.log_context_menu.grab_release()

    def copy_logs_to_clipboard(self):
        try:
            logs = self.log_area.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        except tk.TclError:
            logs = self.log_area.get("1.0", tk.END).strip()

        if logs:
            self.root.clipboard_clear()
            self.root.clipboard_append(logs)
            self.root.update()
            messagebox.showinfo(self.tr("msg_success"), self.tr("msg_logs_copied"))
        else:
            messagebox.showwarning(self.tr("msg_attention"), self.tr("msg_nothing_to_copy"))

    def save_logs(self):
        logs = self.log_area.get("1.0", tk.END).strip()
        if not logs:
            messagebox.showwarning(self.tr("msg_attention"), self.tr("msg_no_logs_to_save"))
            return

        file_path = filedialog.asksaveasfilename(
            title=self.tr("title_save_logs"),
            defaultextension=".log",
            filetypes=[(self.tr("ft_log"), "*.log"), (self.tr("ft_text"), "*.txt"), (self.tr("ft_all_files"), "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(logs + "\n")
            messagebox.showinfo(self.tr("msg_success"), self.tr("msg_logs_saved", path=file_path))
        except OSError as exc:
            messagebox.showerror(self.tr("msg_save_error"), str(exc))

    def read_output(self):
        for line in iter(self.process.stdout.readline, ''):
            if not self.is_running:
                break
            self.log(line)
            if not self.server_ready and "llama_server: model loaded" in line:
                self.server_ready = True
                self.root.after(0, self.set_ready_state)

        self.process.wait()
        exit_code = self.process.returncode

        if self.manual_stop_requested:
            self.root.after(0, lambda: self.set_stopped_state(play_sound=True))
        elif not self.server_ready and exit_code is not None:
            self.root.after(0, self.set_loading_error_state)
        else:
            self.root.after(0, lambda: self.set_stopped_state(play_sound=True))

    def start_server(self):
        if self.is_running:
            return

        exe_path = os.path.normpath(self.exe_entry.get().strip())
        model_path = os.path.normpath(self.model_entry.get().strip())

        if not exe_path or not os.path.exists(exe_path):
            messagebox.showerror(self.tr("msg_error"), self.tr("err_invalid_exe", exe=LLAMA_SERVER_FILENAME))
            return
        if not model_path or not os.path.exists(model_path):
            messagebox.showerror(self.tr("msg_error"), self.tr("err_invalid_model"))
            return

        width = self.window_width_entry.get().strip()
        height = self.window_height_entry.get().strip()
        if (width and not width.isdigit()) or (height and not height.isdigit()):
            messagebox.showerror(self.tr("msg_error"), self.tr("err_invalid_window_size"))
            return

        self.save_config()
        self.apply_window_size_from_fields()

        custom_args = self.generate_args()
        extra_args = self.get_custom_args()
        full_cmd = [exe_path, "-m", model_path] + custom_args + extra_args

        try:
            startupinfo = self._get_hidden_startupinfo()

            self.process = subprocess.Popen(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
                bufsize=1
            )

            self.is_running = True
            self.server_ready = False
            self.manual_stop_requested = False
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.restart_btn.config(state=tk.NORMAL)
            self.status_label.config(text=self.tr("status_loading"), fg="#ff9800")
            self.start_loading_blink()
            self.log(f"--- {self.tr('log_start_server')} ---\n{self.tr('log_command')} {' '.join(full_cmd)}\n\n")
            threading.Thread(target=self.read_output, daemon=True).start()

        except Exception as e:
            messagebox.showerror(self.tr("err_start"), str(e))

    def stop_server(self, log_message=True):
        if self.process and self.is_running:
            self.manual_stop_requested = True
            self.is_running = False
            self.process.terminate()
            self.set_stopped_state(play_sound=False)
            if log_message:
                self.log(f"\n--- {self.tr('log_force_stopped')} ---\n")

    def restart_server(self):
        if not self.is_running:
            self.start_server()
            return

        self.log(f"\n--- {self.tr('log_restarting')} ---\n")
        self.stop_server(log_message=False)
        self.root.after(500, self.start_server)

    def get_server_url(self):
        host = self.get_param_value("host") or "localhost"
        port = self.get_param_value("port") or "18080"

        if host in {"0.0.0.0", "::", "*", ""}:
            host = "localhost"

        return f"http://{host}:{port}/"

    def open_server_in_browser(self):
        url = self.get_server_url()
        self.log(f"{self.tr('log_opening_browser')} {url}\n")
        try:
            webbrowser.open(url)
        except Exception as exc:
            self.log(self.tr("log_browser_open_failed", error=exc))

    def set_ready_state(self):
        if self.is_running:
            self.stop_loading_blink()
            self.status_label.config(text=self.tr("status_running"), fg="green")
            self.play_loaded_sound()
            if self.open_browser_on_load_var.get():
                self.open_server_in_browser()

    def set_stopped_state(self, play_sound=False):
        self.stop_loading_blink()
        self.is_running = False
        self.server_ready = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.DISABLED)
        self.status_label.config(text=self.tr("status_stopped"), fg="red")
        if play_sound:
            self.play_stopped_sound()

    def _save_config_safely(self):
        try:
            self.save_config()
        except OSError as exc:
            messagebox.showerror(self.tr("msg_save_error"), str(exc))

    def on_close(self):
        if self.is_running:
            if messagebox.askokcancel(self.tr("msg_exit"), self.tr("msg_exit_confirm")):
                self.stop_server()
                self._save_config_safely()
                self.root.destroy()
        else:
            self._save_config_safely()
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = LlamaServerGUI(root)
    root.mainloop()
