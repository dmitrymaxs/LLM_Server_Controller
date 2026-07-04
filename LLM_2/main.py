import sys
import os
import json
import subprocess
import threading
import tkinter as tk
import winsound
from tkinter import scrolledtext, messagebox, filedialog

CONFIG_FILE = "llama_config.json"
APP_VERSION = "0.1.0"
APP_AUTHOR = "Dmitry Maksimov"
APP_LICENSE = "MIT"

class CollapsibleFrame:
    """Виджет сворачиваемой рамки с заголовком."""

    def __init__(self, parent, title):
        self.is_open = False
        self.header = tk.Frame(parent, cursor="hand2", bg="#e8e8e8")
        self.header.pack(fill=tk.X, padx=2, pady=(4, 0))

        self.indicator = tk.Label(self.header, text="\u25B6", width=2, bg="#e8e8e8",
                                  font=("Arial", 9), fg="#555555")
        self.indicator.pack(side=tk.LEFT, padx=(4, 0))

        self.title_label = tk.Label(self.header, text=title, font=("Arial", 9, "bold"),
                                    bg="#e8e8e8", fg="#333333")
        self.title_label.pack(side=tk.LEFT, padx=4, pady=3)

        self.content = tk.Frame(parent)

        self.header.bind("<Button-1>", self.toggle)
        self.title_label.bind("<Button-1>", self.toggle)
        self.indicator.bind("<Button-1>", self.toggle)

    def toggle(self, event=None):
        if self.is_open:
            self.content.pack_forget()
            self.indicator.config(text="\u25B6")
            self.is_open = False
        else:
            self.content.pack(fill=tk.X, padx=8, pady=(2, 4))
            self.indicator.config(text="\u25BC")
            self.is_open = True


PARAM_GROUPS = [
    ("\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043f\u0430\u043c\u044f\u0442\u044c\u044e", [
        ("--no-mmap", "\u041e\u0442\u043a\u043b\u044e\u0447\u0438\u0442\u044c mmap"),
        ("--mlock", "\u0417\u0430\u043a\u0440\u0435\u043f\u0438\u0442\u044c \u0432 RAM"),
        ("--direct-io", "Direct I/O"),
        ("--no-host", "\u041e\u0442\u043a\u043b\u044e\u0447\u0438\u0442\u044c Host Buffer"),
        ("--repack", "\u0420\u0435\u043f\u0430\u043a\u043e\u0432\u043a\u0430 \u0442\u0435\u043d\u0437\u043e\u0440\u043e\u0432"),
        ("--kv-offload", "KV Cache \u043d\u0430 GPU"),
        ("--cache-type-k", "\u0422\u0438\u043f K Cache"),
        ("--cache-type-v", "\u0422\u0438\u043f V Cache"),
        ("--cache-ram", "Cache RAM"),
    ]),
    ("\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430 CPU", [
        ("--threads", "\u041f\u043e\u0442\u043e\u043a\u0438"),
        ("--threads-batch", "\u041f\u043e\u0442\u043e\u043a\u0438 \u0431\u0430\u0442\u0447"),
        ("--cpu-range", "\u0414\u0438\u0430\u043f\u0430\u0437\u043e\u043d \u044f\u0434\u0435\u0440"),
        ("--numa", "NUMA"),
    ]),
    ("\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430 GPU", [
        ("--split-mode", "Split Mode"),
        ("--tensor-split", "Tensor Split"),
        ("--main-gpu", "Main GPU"),
        ("--device", "\u0423\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u043e"),
    ]),
    ("\u041a\u043e\u043d\u0442\u0435\u043a\u0441\u0442 \u0438 RoPE", [
        ("--rope-scaling", "RoPE Scaling"),
        ("--rope-scale", "RoPE Scale"),
        ("--rope-freq-base", "Freq Base"),
        ("--rope-freq-scale", "Freq Scale"),
        ("--no-context-shift", "\u041e\u0442\u043a\u043b\u044e\u0447\u0438\u0442\u044c Context Shift"),
    ]),
    ("YaRN (\u0440\u0430\u0441\u0448\u0438\u0440\u0435\u043d\u0438\u0435 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442\u0430)", [
        ("--yarn-orig-ctx", "Orig Ctx"),
        ("--yarn-scale", "Scale"),
        ("--yarn-ext-factor", "Ext Factor"),
        ("--yarn-attn-factor", "Attn Factor"),
        ("--yarn-beta-fast", "Beta Fast"),
        ("--yarn-beta-slow", "Beta Slow"),
    ]),
    ("Sampling \u0438 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044f", [
        ("--temp", "\u0422\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u0430"),
        ("--top-p", "Top P"),
        ("--top-k", "Top K"),
        ("--min-p", "Min P"),
        ("--repeat-penalty", "Repeat Penalty"),
        ("--repeat-last-n", "Repeat Last N"),
        ("--presence-penalty", "Presence Penalty"),
        ("--frequency-penalty", "Frequency Penalty"),
        ("--seed", "Seed"),
        ("--spec-type", "Spec Decode Type"),
        ("--spec-draft-n-max", "Spec Draft N Max"),
        ("-ncmoe", "MoE \u044d\u043a\u0441\u043f\u0435\u0440\u0442\u044b"),
    ]),
    ("\u0421\u0435\u0440\u0432\u0435\u0440", [
        ("--host", "Host"),
        ("--port", "Port"),
    ]),
]


class LlamaServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM Server Controller")
        self.root.geometry("920x900")

        self.process = None
        self.is_running = False
        self.server_ready = False
        self.loading_blink_job = None
        self.loading_blink_visible = True
        self.manual_stop_requested = False
        self.log_lines = []

        self.default_params = {
            "--ctx-size": "16384",
            "--n-gpu-layers": "99",
            "--no-mmap": True,
            "--mlock": False,
            "-fa": "on",
            "-ncmoe": "",
            "--cache-type-k": "q8_0",
            "--cache-type-v": "q8_0",
            "--temp": "1.0",
            "--top-p": "0.95",
            "--top-k": "64",
            "--spec-type": "",
            "--spec-draft-n-max": "6",
            "--host": "0.0.0.0",
            "--port": "18080",
            # Управление памятью
            "--direct-io": False,
            "--no-host": False,
            "--repack": True,
            "--kv-offload": True,
            "--cache-ram": "",
            # Настройка CPU
            "--threads": "",
            "--threads-batch": "",
            "--cpu-range": "",
            "--numa": "",
            # Настройка GPU
            "--split-mode": "",
            "--tensor-split": "",
            "--main-gpu": "",
            "--device": "",
            # Контекст и RoPE
            "--rope-scaling": "",
            "--rope-scale": "",
            "--rope-freq-base": "",
            "--rope-freq-scale": "",
            "--no-context-shift": False,
            # YaRN
            "--yarn-orig-ctx": "",
            "--yarn-scale": "",
            "--yarn-ext-factor": "",
            "--yarn-attn-factor": "",
            "--yarn-beta-fast": "",
            "--yarn-beta-slow": "",
            # Sampling и генерация
            "--min-p": "",
            "--repeat-penalty": "",
            "--repeat-last-n": "",
            "--presence-penalty": "",
            "--frequency-penalty": "",
            "--seed": "",
        }

        self.default_config = self.get_default_config()

        self.config = self.load_config()
        self.param_entries = {}
        self.enable_loaded_sound_var = tk.BooleanVar(value=self.config.get("sounds", {}).get("loaded", True))
        self.enable_stopped_sound_var = tk.BooleanVar(value=self.config.get("sounds", {}).get("stopped", True))

        self.apply_window_geometry()
        self.create_menu()
        self.create_widgets()
        self.apply_config_to_form()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Импорт", command=self.import_settings)
        file_menu.add_command(label="Экспорт", command=self.export_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_close)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Справка", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="О программе", command=self.show_about)

        sound_menu = tk.Menu(menu_bar, tearoff=0)
        sound_menu.add_checkbutton(label="Звук загрузки", variable=self.enable_loaded_sound_var, command=self.on_sound_settings_changed)
        sound_menu.add_checkbutton(label="Звук отключения", variable=self.enable_stopped_sound_var, command=self.on_sound_settings_changed)

        menu_bar.add_cascade(label="Файл", menu=file_menu)
        menu_bar.add_cascade(label="Звуки", menu=sound_menu)
        menu_bar.add_cascade(label="Справка", menu=help_menu)
        self.root.config(menu=menu_bar)

    def get_default_config(self):
        return {
            "exe_path": "",
            "model_path": "",
            "window": {
                "width": "920",
                "height": "900"
            },
            "sounds": {
                "loaded": True,
                "stopped": True
            },
            "params": self.default_params.copy()
        }

    def merge_config(self, loaded_config):
        config = self.get_default_config()
        if not isinstance(loaded_config, dict):
            return config

        config["exe_path"] = loaded_config.get("exe_path", "")
        config["model_path"] = loaded_config.get("model_path", "")

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

        loaded_params = loaded_config.get("params", {})
        if isinstance(loaded_params, dict):
            if "-mlock" in loaded_params and "--mlock" not in loaded_params:
                loaded_params["--mlock"] = loaded_params["-mlock"]
            for param, default_value in self.default_params.items():
                if param in loaded_params:
                    value = loaded_params[param]
                    if isinstance(default_value, bool):
                        config["params"][param] = bool(value)
                    else:
                        config["params"][param] = str(value)

        return config

    def load_config(self, file_path=CONFIG_FILE):
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
            "window": {
                "width": width or self.default_config["window"]["width"],
                "height": height or self.default_config["window"]["height"]
            },
            "sounds": {
                "loaded": self.enable_loaded_sound_var.get(),
                "stopped": self.enable_stopped_sound_var.get()
            },
            "params": params
        }

    def save_config(self, file_path=CONFIG_FILE):
        self.config = self.merge_config(self.collect_form_state())
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def apply_window_geometry(self):
        window_cfg = self.config.get("window", {})
        width = window_cfg.get("width", "920")
        height = window_cfg.get("height", "760")
        if width.isdigit() and height.isdigit():
            self.root.geometry(f"{width}x{height}")

    def apply_config_to_form(self):
        self.exe_entry.delete(0, tk.END)
        self.exe_entry.insert(0, self.config.get("exe_path", ""))

        self.model_entry.delete(0, tk.END)
        self.model_entry.insert(0, self.config.get("model_path", ""))

        window_cfg = self.config.get("window", {})
        self.window_width_entry.delete(0, tk.END)
        self.window_width_entry.insert(0, window_cfg.get("width", "920"))
        self.window_height_entry.delete(0, tk.END)
        self.window_height_entry.insert(0, window_cfg.get("height", "760"))

        params = self.config.get("params", {})
        for param, widget in self.param_entries.items():
            value = params.get(param, self.default_params[param])
            if isinstance(widget, tk.BooleanVar):
                widget.set(bool(value))
            else:
                widget.delete(0, tk.END)
                widget.insert(0, str(value))

    def create_widgets(self):
        path_frame = tk.LabelFrame(self.root, text=" Настройки путей ", padx=10, pady=5)
        path_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(path_frame, text="Сервер:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.exe_entry = tk.Entry(path_frame, width=70)
        self.exe_entry.grid(row=0, column=1, padx=5, pady=2)
        tk.Button(path_frame, text="Обзор...", command=self.browse_exe).grid(row=0, column=2, padx=2, pady=2)

        tk.Label(path_frame, text="Модель:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.model_entry = tk.Entry(path_frame, width=70)
        self.model_entry.grid(row=1, column=1, padx=5, pady=2)
        tk.Button(path_frame, text="Обзор...", command=self.browse_model).grid(row=1, column=2, padx=2, pady=2)

        tk.Label(path_frame, text="Ширина окна:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.window_width_entry = tk.Entry(path_frame, width=12)
        self.window_width_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        tk.Label(path_frame, text="Высота окна:").grid(row=2, column=1, sticky=tk.E, pady=2)
        self.window_height_entry = tk.Entry(path_frame, width=12)
        self.window_height_entry.grid(row=2, column=2, sticky=tk.W, padx=5, pady=2)

        # === Параметры запуска (группированные секции) ===
        param_frame = tk.LabelFrame(self.root, text=" Параметры запуска (можно менять) ", padx=10, pady=5)
        param_frame.pack(fill=tk.X, padx=10, pady=5)

        # --- Основные параметры (всегда видны) ---
        main_label = tk.Label(param_frame, text="\u25BC Основные параметры:", font=("Arial", 9, "bold"), fg="#333333")
        main_label.pack(anchor=tk.W, padx=2, pady=(0, 2))

        main_frame = tk.Frame(param_frame)
        main_frame.pack(fill=tk.X, padx=4)

        main_params = [
            ("--ctx-size", "Контекст"),
            ("--n-gpu-layers", "GPU слои"),
            ("-fa", "Flash Attn"),
            ("--host", "Host"),
            ("--port", "Port"),
        ]
        row, col = 0, 0
        for param_key, display_name in main_params:
            value = self.default_params[param_key]
            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                chk = tk.Checkbutton(main_frame, text=display_name, variable=var, font=("Arial", 9))
                chk.grid(row=row, column=col * 2, columnspan=2, sticky=tk.W, padx=5, pady=2)
                self.param_entries[param_key] = var
            else:
                lbl = tk.Label(main_frame, text=f"{display_name}:", font=("Arial", 9))
                lbl.grid(row=row, column=col * 2, sticky=tk.W, padx=(5, 2), pady=2)
                width_size = 12 if len(str(value)) > 5 else 10
                ent = tk.Entry(main_frame, width=width_size)
                ent.insert(0, str(value))
                ent.grid(row=row, column=col * 2 + 1, sticky=tk.W, padx=(0, 10), pady=2)
                self.param_entries[param_key] = ent
            col += 1
            if col > 2:
                col = 0
                row += 1

        # --- Сворачиваемые группы параметров ---
        for group_title, group_params in PARAM_GROUPS:
            cf = CollapsibleFrame(param_frame, group_title)
            row, col = 0, 0
            for param_key, display_name in group_params:
                value = self.default_params[param_key]
                if isinstance(value, bool):
                    var = tk.BooleanVar(value=value)
                    chk = tk.Checkbutton(cf.content, text=display_name, variable=var, font=("Arial", 9))
                    chk.grid(row=row, column=col * 2, columnspan=2, sticky=tk.W, padx=5, pady=2)
                    self.param_entries[param_key] = var
                else:
                    lbl = tk.Label(cf.content, text=f"{display_name}:", font=("Arial", 9))
                    lbl.grid(row=row, column=col * 2, sticky=tk.W, padx=(5, 2), pady=2)
                    width_size = 12 if len(str(value)) > 5 else 10
                    ent = tk.Entry(cf.content, width=width_size)
                    ent.insert(0, str(value))
                    ent.grid(row=row, column=col * 2 + 1, sticky=tk.W, padx=(0, 10), pady=2)
                    self.param_entries[param_key] = ent
                col += 1
                if col > 2:
                    col = 0
                    row += 1

        settings_frame = tk.Frame(self.root)
        settings_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        tk.Button(settings_frame, text="Сохранить настройки", command=self.save_current_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(settings_frame, text="Импорт настроек", command=self.import_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(settings_frame, text="Экспорт настроек", command=self.export_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(settings_frame, text="Сбросить параметры", command=self.reset_settings).pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5, fill=tk.X, padx=10)

        self.start_btn = tk.Button(btn_frame, text="Запустить сервер", bg="#4CAF50", fg="white",
                                   font=("Arial", 10, "bold"), command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(btn_frame, text="Остановить", bg="#f44336", fg="white",
                                  font=("Arial", 10, "bold"), command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.restart_btn = tk.Button(btn_frame, text="Перезапустить", bg="#ff9800", fg="white",
                                     font=("Arial", 10, "bold"), command=self.restart_server, state=tk.DISABLED)
        self.restart_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(btn_frame, text="Статус: Остановлен", fg="red", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT, padx=10)

        log_header_frame = tk.Frame(self.root)
        log_header_frame.pack(anchor=tk.W, fill=tk.X, padx=10, pady=(5, 0))

        log_label = tk.Label(log_header_frame, text="Логи сервера:", font=("Arial", 10, "italic"))
        log_label.pack(side=tk.LEFT)

        copy_btn = tk.Button(log_header_frame, text="Копировать лог", font=("Arial", 8),
                             command=self.copy_logs_to_clipboard)
        copy_btn.pack(side=tk.RIGHT, padx=5)

        clear_btn = tk.Button(log_header_frame, text="Очистить лог", font=("Arial", 8),
                              command=self.clear_logs)
        clear_btn.pack(side=tk.RIGHT, padx=5)

        save_log_btn = tk.Button(log_header_frame, text="Сохранить лог", font=("Arial", 8),
                                 command=self.save_logs)
        save_log_btn.pack(side=tk.RIGHT, padx=5)

        self.log_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            bg="#1e1e1e",
            fg="#d4d4d4",
            font=("Consolas", 9)
        )
        self.log_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        self.log_context_menu = tk.Menu(self.root, tearoff=0)
        self.log_context_menu.add_command(label="Копировать", command=self.copy_logs_to_clipboard)
        self.log_area.bind("<Button-3>", self.show_log_context_menu)
        self.log_area.bind("<Double-Button-1>", self.show_log_context_menu)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def browse_exe(self):
        file_path = filedialog.askopenfilename(
            title="Выберите llama-server.exe",
            filetypes=[("Исполняемые файлы", "*.exe"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.exe_entry.delete(0, tk.END)
            self.exe_entry.insert(0, os.path.normpath(file_path))

    def browse_model(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл модели GGUF",
            filetypes=[("Модели GGUF", "*.gguf"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.model_entry.delete(0, tk.END)
            self.model_entry.insert(0, os.path.normpath(file_path))

    def save_current_settings(self):
        try:
            self.save_config()
            self.apply_window_size_from_fields()
            messagebox.showinfo("Успех", f"Настройки сохранены в {CONFIG_FILE}")
        except OSError as exc:
            messagebox.showerror("Ошибка сохранения", str(exc))

    def on_sound_settings_changed(self):
        self.save_config()

    def play_loaded_sound(self):
        if self.enable_loaded_sound_var.get():
            winsound.MessageBeep(winsound.MB_ICONASTERISK)

    def play_stopped_sound(self):
        if self.enable_stopped_sound_var.get():
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
        self.status_label.config(text="Статус: Загружается", fg=color)
        self.loading_blink_job = self.root.after(500, self.animate_loading_status)

    def set_loading_error_state(self):
        self.stop_loading_blink()
        self.status_label.config(text="Статус: Ошибка загрузки", fg="#b00020")

    def import_settings(self):
        file_path = filedialog.askopenfilename(
            title="Импорт настроек",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if not file_path:
            return

        imported_config = self.load_config(file_path)
        self.config = imported_config
        self.apply_window_geometry()
        self.apply_config_to_form()
        self.save_config()
        messagebox.showinfo("Импорт завершен", "Настройки импортированы и сохранены в локальный конфиг.")

    def export_settings(self):
        file_path = filedialog.asksaveasfilename(
            title="Экспорт настроек",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if not file_path:
            return

        try:
            export_config = self.merge_config(self.collect_form_state())
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_config, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Экспорт завершен", f"Настройки экспортированы в:\n{file_path}")
        except OSError as exc:
            messagebox.showerror("Ошибка экспорта", str(exc))

    def reset_settings(self):
        if self.is_running:
            messagebox.showwarning("Внимание", "Нельзя сбрасывать настройки во время работы сервера.")
            return

        self.config = self.get_default_config()
        self.apply_window_geometry()
        self.apply_config_to_form()
        self.save_config()
        messagebox.showinfo("Сброс выполнен", "Настройки возвращены к значениям по умолчанию.")

    def apply_window_size_from_fields(self):
        width = self.window_width_entry.get().strip()
        height = self.window_height_entry.get().strip()
        if width.isdigit() and height.isdigit():
            self.root.geometry(f"{width}x{height}")

    def show_help(self):
        help_text = (
            "Llama Server Controller — справка\n\n"
            "Назначение программы:\n"
            "Приложение позволяет выбрать llama-server.exe, указать GGUF-модель, настроить параметры запуска,\n"
            "запустить сервер, остановить его, перезапустить и просматривать логи.\n\n"
            "Описание полей:\n"
            "Сервер — путь к файлу llama-server.exe.\n"
            "Модель — путь к файлу модели в формате .gguf.\n"
            "Ширина окна — ширина окна приложения в пикселях.\n"
            "Высота окна — высота окна приложения в пикселях.\n\n"
            "Параметры запуска сгруппированы по категориям:\n"
            "Основные параметры — всегда видны: контекст, GPU слои, Flash Attention, хост и порт.\n"
            "Остальные группы можно раскрыть нажатием на заголовок:\n\n"
            "Управление памятью:\n"
            "--no-mmap — отключает memory mapping при чтении модели.\n"
            "--mlock — блокирует модель в RAM, запрещает выгрузку в swap.\n"
            "--direct-io — использует DirectIO при чтении модели.\n"
            "--no-host — отключает Host Buffer (промежуточная память CPU-GPU).\n"
            "--repack — включает репаковку весов модели (по умолчанию вкл).\n"
            "--kv-offload — перенос KV Cache на GPU (по умолчанию вкл).\n"
            "--cache-type-k — тип кэша для K-тензоров (f32/f16/q8_0/q5_1/q4_0/iq4_nl).\n"
            "--cache-type-v — тип кэша для V-тензоров.\n"
            "--cache-ram — управление кэшем в RAM.\n\n"
            "Настройка CPU:\n"
            "--threads — количество потоков CPU для генерации.\n"
            "--threads-batch — количество потоков для обработки Prefill.\n"
            "--cpu-range — диапазон ядер CPU (например 0-15).\n"
            "--numa — управление NUMA (disabled/distribute/isolate/mirror/numactl).\n\n"
            "Настройка GPU:\n"
            "--split-mode — распределение модели между несколькими GPU (none/layer/row).\n"
            "--tensor-split — доля модели на каждую видеокарту (например 4,8).\n"
            "--main-gpu — номер основной видеокарты.\n"
            "--device — имя устройства (CUDA0/Vulkan0/HIP0 и т.д.).\n\n"
            "Контекст и RoPE:\n"
            "--rope-scaling — алгоритм масштабирования RoPE (none/linear/yarn).\n"
            "--rope-scale — коэффициент масштабирования.\n"
            "--rope-freq-base — базовая частота вращения RoPE.\n"
            "--rope-freq-scale — дополнительный коэффициент масштабирования частоты.\n"
            "--no-context-shift — отключает автоматический сдвиг контекста.\n\n"
            "YaRN (расширение контекста):\n"
            "--yarn-orig-ctx — исходный размер контекста модели.\n"
            "--yarn-scale — коэффициент масштабирования YaRN.\n"
            "--yarn-ext-factor, --yarn-attn-factor, --yarn-beta-fast, --yarn-beta-slow —\n"
            "параметры тонкой настройки алгоритма YaRN.\n\n"
            "Sampling и генерация:\n"
            "--temp — температура генерации (0 = детерминированный режим).\n"
            "--top-p — nucleus sampling (ограничение по накопленной вероятности).\n"
            "--top-k — ограничение выбора K наиболее вероятными токенами.\n"
            "--min-p — минимальная вероятность токена.\n"
            "--repeat-penalty — штраф за повторение токенов.\n"
            "--repeat-last-n — окно последних токенов для штрафа за повторение.\n"
            "--presence-penalty — штраф за частое появление токенов.\n"
            "--frequency-penalty — штраф пропорциональный частоте токена.\n"
            "--seed — зерно случайности для воспроизводимости.\n"
            "--spec-type — тип speculative decoding.\n"
            "--spec-draft-n-max — макс. число черновых токенов в speculative decoding.\n"
            "-ncmoe — кол-во активных экспертов для MoE-моделей.\n\n"
            "Сервер:\n"
            "--host — адрес прослушивания (0.0.0.0 — все интерфейсы).\n"
            "--port — TCP-порт сервера.\n\n"
            "Кнопки и функции:\n"
            "Сохранить настройки — сохраняет текущие пути, размеры окна и параметры в llama_config.json.\n"
            "Импорт настроек — загружает настройки из внешнего JSON-файла.\n"
            "Экспорт настроек — сохраняет текущие настройки в выбранный JSON-файл.\n"
            "Сбросить параметры — возвращает параметры и размеры окна к значениям по умолчанию.\n"
            "Запустить сервер — запускает llama-server.exe с текущими параметрами.\n"
            "Остановить — завершает работающий сервер.\n"
            "Перезапустить — останавливает и снова запускает сервер с текущими настройками.\n"
            "Сохранить лог — сохраняет видимые логи в файл .log или .txt.\n"
            "Очистить лог — очищает окно логов.\n"
            "Копировать лог — копирует выделенный фрагмент лога или весь лог, если выделения нет.\n\n"
            "Меню Файл:\n"
            "Импорт — загрузка настроек из JSON-файла.\n"
            "Экспорт — сохранение текущих настроек в JSON-файл.\n"
            "Выход — закрытие приложения с сохранением текущих настроек.\n\n"
            "Замечания:\n"
            "Некоторые параметры зависят от версии llama-server и вашей сборки.\n"
            "Если сервер не запускается, проверьте путь к exe, путь к модели и совместимость параметров."
        )

        help_window = tk.Toplevel(self.root)
        help_window.title("Справка")
        help_window.geometry("760x750")
        help_window.transient(self.root)

        text_area = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=("Segoe UI", 10))
        text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        text_area.insert("1.0", help_text)
        text_area.config(state=tk.DISABLED)

        close_btn = tk.Button(help_window, text="Закрыть", command=help_window.destroy)
        close_btn.pack(pady=(0, 10))

    def show_about(self):
        about_text = (
            "Llama Server Controller\n"
            f"Version: {APP_VERSION}\n"
            f"Author: {APP_AUTHOR}\n"
            f"License: {APP_LICENSE}"
        )
        messagebox.showinfo("О программе", about_text)

    def generate_args(self):
        dynamic_args = []
        for param, widget in self.param_entries.items():
            if isinstance(widget, tk.BooleanVar):
                if widget.get():
                    dynamic_args.append(param)
            else:
                val = widget.get().strip()
                if val:
                    dynamic_args.extend([param, val])
        return dynamic_args

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
            messagebox.showinfo("Успех", "Данные из логов скопированы в буфер обмена.")
        else:
            messagebox.showwarning("Внимание", "Нет данных для копирования.")

    def save_logs(self):
        logs = self.log_area.get("1.0", tk.END).strip()
        if not logs:
            messagebox.showwarning("Внимание", "Нет логов для сохранения.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Сохранить логи",
            defaultextension=".log",
            filetypes=[("Log файлы", "*.log"), ("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(logs + "\n")
            messagebox.showinfo("Успех", f"Логи сохранены в:\n{file_path}")
        except OSError as exc:
            messagebox.showerror("Ошибка сохранения", str(exc))

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
            messagebox.showerror("Ошибка", "Укажите корректный путь к llama-server.exe")
            return
        if not model_path or not os.path.exists(model_path):
            messagebox.showerror("Ошибка", "Укажите корректный путь к файлу модели (.gguf)")
            return

        width = self.window_width_entry.get().strip()
        height = self.window_height_entry.get().strip()
        if (width and not width.isdigit()) or (height and not height.isdigit()):
            messagebox.showerror("Ошибка", "Ширина и высота окна должны быть целыми числами.")
            return

        self.save_config()
        self.apply_window_size_from_fields()

        custom_args = self.generate_args()
        full_cmd = [exe_path, "-m", model_path] + custom_args

        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

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
            self.status_label.config(text="Статус: Загружается", fg="#ff9800")
            self.start_loading_blink()
            self.log(f"--- Запуск сервера ---\nКоманда: {' '.join(full_cmd)}\n\n")
            threading.Thread(target=self.read_output, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Ошибка запуска", str(e))

    def stop_server(self, log_message=True):
        if self.process and self.is_running:
            self.manual_stop_requested = True
            self.is_running = False
            self.process.terminate()
            self.set_stopped_state(play_sound=False)
            if log_message:
                self.log("\n--- Сервер принудительно остановлен ---\n")

    def restart_server(self):
        if not self.is_running:
            self.start_server()
            return

        self.log("\n--- Перезапуск сервера ---\n")
        self.stop_server(log_message=False)
        self.root.after(500, self.start_server)

    def set_ready_state(self):
        if self.is_running:
            self.stop_loading_blink()
            self.status_label.config(text="Статус: Работает", fg="green")
            self.play_loaded_sound()

    def set_stopped_state(self, play_sound=False):
        self.stop_loading_blink()
        self.is_running = False
        self.server_ready = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Статус: Остановлен", fg="red")
        if play_sound:
            self.play_stopped_sound()

    def on_close(self):
        if self.is_running:
            if messagebox.askokcancel("Выход", "Сервер еще работает. Завершить процесс и выйти?"):
                self.stop_server()
                self.save_config()
                self.root.destroy()
        else:
            self.save_config()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LlamaServerGUI(root)
    root.mainloop()
