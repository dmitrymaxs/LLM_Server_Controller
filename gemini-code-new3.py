import sys
import os
import json
import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog

CONFIG_FILE = "llama_config.json"

class LlamaServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Llama Server Controller")
        self.root.geometry("920x760")

        self.process = None
        self.is_running = False
        self.log_lines = []

        self.default_params = {
            "--ctx-size": "16384",
            "--n-gpu-layers": "99",
            "--no-mmap": True,
            "-fa": "on",
            "--cache-type-k": "q8_0",
            "--cache-type-v": "q8_0",
            "--temp": "1.0",
            "--top-p": "0.95",
            "--top-k": "64",
            "--spec-type": "draft-mtp",
            "--spec-draft-n-max": "6",
            "--host": "0.0.0.0",
            "--port": "18080"
        }

        self.default_config = self.get_default_config()

        self.config = self.load_config()
        self.param_entries = {}

        self.apply_window_geometry()
        self.create_widgets()
        self.apply_config_to_form()

    def get_default_config(self):
        return {
            "exe_path": "",
            "model_path": "",
            "window": {
                "width": "920",
                "height": "760"
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

        loaded_params = loaded_config.get("params", {})
        if isinstance(loaded_params, dict):
            for param, default_value in self.default_params.items():
                if param in loaded_params:
                    value = loaded_params[param]
                    if isinstance(default_value, bool):
                        config["params"][param] = bool(value)
                    else:
                        config["params"][param] = str(value)

        return config

    def load_config(self, file_path=CONFIG_FILE):
        """Загружает конфигурацию приложения из файла"""
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
            "params": params
        }

    def save_config(self, file_path=CONFIG_FILE):
        """Сохраняет конфигурацию приложения в файл"""
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
        # --- 1. Панель выбора путей ---
        path_frame = tk.LabelFrame(self.root, text=" Настройки путей ", padx=10, pady=5)
        path_frame.pack(fill=tk.X, padx=10, pady=5)

        # Выбор llama-server.exe
        tk.Label(path_frame, text="Сервер:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.exe_entry = tk.Entry(path_frame, width=70)
        self.exe_entry.grid(row=0, column=1, padx=5, pady=2)
        tk.Button(path_frame, text="Обзор...", command=self.browse_exe).grid(row=0, column=2, padx=2, pady=2)

        # Выбор модели .gguf
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

        # --- 2. Панель настройки переменных (Аргументов) ---
        param_frame = tk.LabelFrame(self.root, text=" Параметры запуска (можно менять) ", padx=10, pady=5)
        param_frame.pack(fill=tk.X, padx=10, pady=5)

        # Сетка параметров (вывод в 4 колонки)
        row, col = 0, 0
        for param, value in self.default_params.items():
            if isinstance(value, bool):
                # Если параметр — флаг (выключатель)
                var = tk.BooleanVar(value=value)
                chk = tk.Checkbutton(param_frame, text=param, variable=var, font=("Arial", 9))
                chk.grid(row=row, column=col*2, columnspan=2, sticky=tk.W, padx=5, pady=2)
                self.param_entries[param] = var
            else:
                # Обычный параметр со значением
                lbl = tk.Label(param_frame, text=f"{param}:", font=("Arial", 9))
                lbl.grid(row=row, column=col*2, sticky=tk.W, padx=(5, 2))
                
                # Делаем поле ввода чуть шире для длинных названий параметров (например, draft-mtp)
                width_size = 12 if len(str(value)) > 5 else 10
                ent = tk.Entry(param_frame, width=width_size)
                ent.insert(0, str(value))
                ent.grid(row=row, column=col*2 + 1, sticky=tk.W, padx=(0, 10), pady=2)
                self.param_entries[param] = ent

            col += 1
            if col > 3:  # Перенос на новую строку после 4-х колонок
                col = 0
                row += 1

        settings_frame = tk.Frame(self.root)
        settings_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        tk.Button(settings_frame, text="Сохранить настройки", command=self.save_current_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(settings_frame, text="Импорт настроек", command=self.import_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(settings_frame, text="Экспорт настроек", command=self.export_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(settings_frame, text="Сбросить параметры", command=self.reset_settings).pack(side=tk.LEFT, padx=5)

        # --- 3. Панель управления (Кнопки) ---
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

        # --- 4. Логи ---
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

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def browse_exe(self):
        """Проводник для выбора файла сервера"""
        file_path = filedialog.askopenfilename(
            title="Выберите llama-server.exe",
            filetypes=[("Исполняемые файлы", "*.exe"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.exe_entry.delete(0, tk.END)
            self.exe_entry.insert(0, os.path.normpath(file_path))

    def browse_model(self):
        """Проводник для выбора файла модели"""
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

    def generate_args(self):
        """Динамически собирает аргументы командной строки на основе данных из GUI"""
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
        """Потокобезопасная запись в лог-интерфейс"""
        self.root.after(0, lambda: self.append_log(text))

    def clear_logs(self):
        self.log_lines.clear()
        self.log_area.delete("1.0", tk.END)

    def copy_logs_to_clipboard(self):
        """Копирует выделенный текст или весь лог в буфер обмена"""
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
        """Потоковое чтение вывода фонового процесса"""
        for line in iter(self.process.stdout.readline, ''):
            if not self.is_running:
                break
            self.log(line)
        self.process.wait()
        self.root.after(0, self.set_stopped_state)

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
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.restart_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Статус: Работает", fg="green")
            self.log(f"--- Запуск сервера ---\nКоманда: {' '.join(full_cmd)}\n\n")
            threading.Thread(target=self.read_output, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Ошибка запуска", str(e))

    def stop_server(self, log_message=True):
        if self.process and self.is_running:
            self.is_running = False
            self.process.terminate()
            self.set_stopped_state()
            if log_message:
                self.log("\n--- Сервер принудительно остановлен ---\n")

    def restart_server(self):
        if not self.is_running:
            self.start_server()
            return

        self.log("\n--- Перезапуск сервера ---\n")
        self.stop_server(log_message=False)
        self.root.after(500, self.start_server)

    def set_stopped_state(self):
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Статус: Остановлен", fg="red")

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