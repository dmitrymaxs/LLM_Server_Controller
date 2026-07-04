import sys
import os
import json
import subprocess
import threading
import tkinter as tk
import winsound
from tkinter import scrolledtext, messagebox, filedialog

from params_config import (
    PARAM_GROUPS,
    BACKEND_DEVICE_KEYS,
    build_default_params,
    normalize_loaded_params,
)

CONFIG_FILE = "llama_config.json"
APP_VERSION = "0.1.0"
APP_AUTHOR = "Dmitry Maksimov"
APP_LICENSE = "MIT"
PARAM_GRID_COLUMNS = 4


class LlamaServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM Server Controller")
        self.root.geometry("1000x900")

        self.process = None
        self.is_running = False
        self.server_ready = False
        self.loading_blink_job = None
        self.loading_blink_visible = True
        self.manual_stop_requested = False
        self.log_lines = []

        self.default_params = build_default_params()
        self.default_config = self.get_default_config()

        self.config = self.load_config()
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

        params_menu = tk.Menu(menu_bar, tearoff=0)
        for group in PARAM_GROUPS:
            params_menu.add_command(
                label=group["title"],
                command=lambda gid=group["id"]: self.show_param_section(gid),
            )

        menu_bar.add_cascade(label="Файл", menu=file_menu)
        menu_bar.add_cascade(label="Параметры", menu=params_menu)
        menu_bar.add_cascade(label="Звуки", menu=sound_menu)
        menu_bar.add_cascade(label="Справка", menu=help_menu)
        self.root.config(menu=menu_bar)

    def get_default_config(self):
        return {
            "exe_path": "",
            "model_path": "",
            "window": {
                "width": "1000",
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

        loaded_params = normalize_loaded_params(loaded_config.get("params", {}))
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

        params = self.config.get("params", {})
        for param, widget in self.param_entries.items():
            value = params.get(param, self.default_params[param])
            if isinstance(widget, tk.BooleanVar):
                widget.set(bool(value))
            else:
                widget.delete(0, tk.END)
                widget.insert(0, str(value))

    def create_widgets(self):
        path_frame = tk.LabelFrame(self.root, text=" Настройки путей ", padx=8, pady=4)
        path_frame.pack(fill=tk.X, padx=10, pady=(8, 4))

        tk.Label(path_frame, text="Сервер:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.exe_entry = tk.Entry(path_frame)
        self.exe_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        tk.Button(path_frame, text="Обзор...", command=self.browse_exe).grid(row=0, column=2, padx=2, pady=2)
        self.list_devices_btn = tk.Button(
            path_frame, text="Устройства", command=self.list_devices,
        )
        self.list_devices_btn.grid(row=0, column=3, padx=2, pady=2)

        tk.Label(path_frame, text="Модель:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.model_entry = tk.Entry(path_frame)
        self.model_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        tk.Button(path_frame, text="Обзор...", command=self.browse_model).grid(row=1, column=2, padx=2, pady=2)

        size_frame = tk.Frame(path_frame)
        size_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(2, 0))
        tk.Label(size_frame, text="Окно (Ш×В):").pack(side=tk.LEFT)
        self.window_width_entry = tk.Entry(size_frame, width=6)
        self.window_width_entry.pack(side=tk.LEFT, padx=(6, 2))
        tk.Label(size_frame, text="×").pack(side=tk.LEFT)
        self.window_height_entry = tk.Entry(size_frame, width=6)
        self.window_height_entry.pack(side=tk.LEFT, padx=(2, 0))
        path_frame.columnconfigure(1, weight=1)

        toolbar = tk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=4)

        tk.Button(toolbar, text="Сохранить", command=self.save_current_settings).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(toolbar, text="Импорт", command=self.import_settings).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Экспорт", command=self.export_settings).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Сброс", command=self.reset_settings).pack(side=tk.LEFT, padx=4)

        tk.Frame(toolbar, width=24).pack(side=tk.LEFT)

        self.start_btn = tk.Button(
            toolbar, text="Запустить", bg="#4CAF50", fg="white",
            font=("Arial", 10, "bold"), command=self.start_server,
        )
        self.start_btn.pack(side=tk.LEFT, padx=4)

        self.stop_btn = tk.Button(
            toolbar, text="Остановить", bg="#f44336", fg="white",
            font=("Arial", 10, "bold"), command=self.stop_server, state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        self.restart_btn = tk.Button(
            toolbar, text="Перезапустить", bg="#ff9800", fg="white",
            font=("Arial", 10, "bold"), command=self.restart_server, state=tk.DISABLED,
        )
        self.restart_btn.pack(side=tk.LEFT, padx=4)

        self.status_label = tk.Label(toolbar, text="Статус: Остановлен", fg="red", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT, padx=4)

        self.main_paned = tk.PanedWindow(
            self.root, orient=tk.VERTICAL, sashwidth=7, sashrelief=tk.RAISED, showhandle=True,
        )
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        params_outer = tk.LabelFrame(self.main_paned, text=" Параметры запуска ", padx=6, pady=4)
        self.main_paned.add(params_outer, minsize=320, stretch="always")

        params_body = tk.Frame(params_outer)
        params_body.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(params_body, width=210)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Категории", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 4))

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
            self.params_listbox.insert(tk.END, f"{prefix}{group['title']}")
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

        tk.Label(log_header_frame, text="Логи сервера", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        copy_btn = tk.Button(log_header_frame, text="Копировать", font=("Arial", 8), command=self.copy_logs_to_clipboard)
        copy_btn.pack(side=tk.RIGHT, padx=4)

        clear_btn = tk.Button(log_header_frame, text="Очистить", font=("Arial", 8), command=self.clear_logs)
        clear_btn.pack(side=tk.RIGHT, padx=4)

        save_log_btn = tk.Button(log_header_frame, text="Сохранить", font=("Arial", 8), command=self.save_logs)
        save_log_btn.pack(side=tk.RIGHT, padx=4)

        self.log_area = scrolledtext.ScrolledText(
            log_container,
            wrap=tk.WORD,
            bg="#1e1e1e",
            fg="#d4d4d4",
            font=("Consolas", 9),
        )
        self.log_area.pack(expand=True, fill=tk.BOTH)

        self.log_context_menu = tk.Menu(self.root, tearoff=0)
        self.log_context_menu.add_command(label="Копировать", command=self.copy_logs_to_clipboard)
        self.log_area.bind("<Button-3>", self.show_log_context_menu)
        self.log_area.bind("<Double-Button-1>", self.show_log_context_menu)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_param_group("main")

    def _build_param_group_grid(self, parent, group):
        row, col = 0, 0
        for spec in group["params"]:
            param = spec["key"]
            value = self.default_params[param]
            hint = spec.get("hint", "")

            cell = tk.Frame(parent, padx=6, pady=4)
            cell.grid(row=row, column=col, sticky=tk.NW)

            tk.Label(cell, text=param, font=("Consolas", 9, "bold"), anchor=tk.W).pack(fill=tk.X)

            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                chk = tk.Checkbutton(cell, text="Включить", variable=var, font=("Arial", 9))
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
            self.group_title_label.config(text=group["title"])
            self.group_hint_label.config(text=group.get("hint", ""))

        if not from_listbox:
            for index, gid in self.param_group_meta.items():
                if gid == group_id:
                    self.params_listbox.selection_clear(0, tk.END)
                    self.params_listbox.selection_set(index)
                    self.params_listbox.see(index)
                    break

    def browse_exe(self):
        file_path = filedialog.askopenfilename(
            title="Выберите llama-server.exe",
            filetypes=[("Исполняемые файлы", "*.exe"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.exe_entry.delete(0, tk.END)
            self.exe_entry.insert(0, os.path.normpath(file_path))

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
            messagebox.showerror("Ошибка", "Укажите корректный путь к llama-server.exe")
            return

        self.list_devices_btn.config(state=tk.DISABLED, text="Загрузка...")
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
                output = f"Команда завершилась с кодом {result.returncode}.\nВывод пуст."

            title = "Устройства системы (--list-devices)"
            if result.returncode != 0:
                title = f"Устройства (--list-devices, код {result.returncode})"

            self.root.after(0, lambda: self._show_devices_result(title, output, cmd))
        except subprocess.TimeoutExpired:
            self.root.after(
                0,
                lambda: messagebox.showerror("Ошибка", "Превышено время ожидания команды --list-devices"),
            )
        except OSError as exc:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(exc)))
        finally:
            self.root.after(0, self._list_devices_finished)

    def _list_devices_finished(self):
        self.list_devices_btn.config(state=tk.NORMAL, text="Устройства")

    def _show_devices_result(self, title, output, cmd):
        self.log(f"--- {title} ---\nКоманда: {' '.join(cmd)}\n\n{output}\n")

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

        tk.Button(btn_frame, text="Копировать", command=copy_output).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Закрыть", command=window.destroy).pack(side=tk.LEFT, padx=4)

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
            "Устройства — запускает llama-server --list-devices и показывает доступные GPU/CPU\n"
            "устройства перед настройкой --device.\n"
            "Модель — путь к файлу модели в формате .gguf.\n"
            "Ширина окна — ширина окна приложения в пикселях.\n"
            "Высота окна — высота окна приложения в пикселях.\n\n"
            "Описание параметров запуска:\n"
            "Слева — список категорий, справа — поля выбранной группы (4 колонки).\n"
            "Переключение: клик в списке или меню «Параметры». Разделитель между параметрами\n"
            "и логами можно перетаскивать для изменения высоты панелей.\n\n"
            "Основные:\n"
            "--ctx-size — размер контекста; --n-gpu-layers — слои на GPU; -fa — Flash Attention;\n"
            "--threads — потоки CPU; --cache-type-k/v — формат KV Cache; --no-mmap, --mlock — память;\n"
            "--host, --port — сетевые настройки сервера.\n\n"
            "Другие группы: Контекст, GPU, Память, CPU, Batch, Генерация, Draft Model, MoE,\n"
            "Embeddings, Сервер, Безопасность, Диагностика, а также Backend (CUDA, Vulkan, HIP, Metal, SYCL).\n"
            "Поля backend-устройств (--device-cuda и т.д.) передаются как --device при запуске.\n\n"
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
        help_window.geometry("760x620")
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