import sys
import os
import json
import re
import shutil
import subprocess
import tempfile
import threading
import time
import ctypes
import tkinter as tk
import urllib.parse
import urllib.request
import webbrowser
import zipfile
import tarfile

if sys.platform == "win32":
    from ctypes import wintypes

if sys.platform == "win32":
    import winsound
else:
    winsound = None

from tkinter import font as tkfont
from tkinter import messagebox, filedialog, ttk

from params_config import (
    PARAM_GROUPS,
    BACKEND_DEVICE_KEYS,
    build_default_params,
    normalize_loaded_params,
)
from releases import (
    fetch_windows_assets,
    fetch_linux_assets,
    build_download_url,
    fetch_github_latest_release,
    get_llama_server_version,
    is_newer_tag,
    APP_GITHUB_REPO,
)
from i18n import I18n, DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

CONFIG_FILE = "llama_config.json"
APP_ICON_ICO_CANDIDATES = [
    "256x256.ico",
    "64x64.ico",
    "48x48.ico",
    "32x32.ico",
    "24x24.ico",
    "16x16.ico",
]
APP_ICON_PNG_CANDIDATES = [
    "256x256.png",
    "64x64.png",
    "32x32.png",
    "24x24.png",
    "16x16.png",
    "icon48x48.png",
]
APP_VERSION = "0.2.0"
APP_AUTHOR = "Dmitry Maksimov"
APP_LICENSE = "MIT"
PARAM_GRID_COLUMNS = 3
MAX_LOG_LINES = 5000
LOG_TRIM_LINES = 1000
STOP_GRACE_TIMEOUT = 5.0
STOP_KILL_TIMEOUT = 5.0
LLAMA_CPP_RELEASES_URL = "https://github.com/ggml-org/llama.cpp/releases"
PI_AGENT_INSTALL_URL = "https://pi.dev/install.ps1"
PI_AGENT_INSTALL_COMMAND = 'powershell -c "irm https://pi.dev/install.ps1 | iex"'
APP_RELEASES_URL = f"https://github.com/{APP_GITHUB_REPO}/releases"
LLAMA_CPP_INSTALL_DIRNAME = "llama.cpp"
LLAMA_SERVER_FILENAME = "llama-server.exe" if sys.platform == "win32" else "llama-server"
LLAMA_CPP_RECOMMENDED_LABEL = "Windows x64 (Vulkan)" if sys.platform == "win32" else "Linux x64 (Vulkan)"
THEME_LIGHT = "light"
THEME_DARK = "dark"
THEME_NAMES = (THEME_LIGHT, THEME_DARK)
THEMES = {
    THEME_LIGHT: {
        "bg": "#f3f2f1",
        "card_bg": "#ffffff",
        "border": "#e1dfdd",
        "fg": "#201f1e",
        "secondary_fg": "#484644",
        "muted_fg": "#797775",
        "entry_bg": "#ffffff",
        "entry_fg": "#201f1e",
        "entry_border": "#c8c6c4",
        "button_bg": "#f5f5f5",
        "button_fg": "#201f1e",
        "button_border": "#e1dfdd",
        "button_hover": "#ececea",
        "button_press": "#dbd9d7",
        "accent": "#0f6cbd",
        "accent_hover": "#115ea3",
        "accent_press": "#0c5a9e",
        "accent_fg": "#ffffff",
        "success": "#107c10",
        "success_hover": "#0c6510",
        "success_press": "#054b16",
        "danger": "#c42b1c",
        "danger_hover": "#a4261c",
        "danger_press": "#7a1f16",
        "warning": "#ca5010",
        "warning_hover": "#ab440b",
        "warning_press": "#8a3709",
        "check_select": "#ffffff",
        "select_bg": "#0f6cbd",
        "select_fg": "#ffffff",
        "menu_bg": "#ffffff",
        "menu_fg": "#201f1e",
        "link_fg": "#0f6cbd",
        "log_bg": "#1e1e1e",
        "log_fg": "#d4d4d4",
    },
    THEME_DARK: {
        "bg": "#1e1e1e",
        "card_bg": "#252526",
        "border": "#3e3e42",
        "fg": "#f3f3f3",
        "secondary_fg": "#cccccc",
        "muted_fg": "#9d9d9d",
        "entry_bg": "#3c3c3c",
        "entry_fg": "#f3f3f3",
        "entry_border": "#545454",
        "button_bg": "#333333",
        "button_fg": "#f3f3f3",
        "button_border": "#454545",
        "button_hover": "#3d3d3d",
        "button_press": "#2b2b2b",
        "accent": "#0f6cbd",
        "accent_hover": "#115ea3",
        "accent_press": "#0c5a9e",
        "accent_fg": "#ffffff",
        "success": "#107c10",
        "success_hover": "#0c6510",
        "success_press": "#054b16",
        "danger": "#c42b1c",
        "danger_hover": "#a4261c",
        "danger_press": "#7a1f16",
        "warning": "#ca5010",
        "warning_hover": "#ab440b",
        "warning_press": "#8a3709",
        "check_select": "#3c3c3c",
        "select_bg": "#094771",
        "select_fg": "#ffffff",
        "menu_bg": "#252526",
        "menu_fg": "#f3f3f3",
        "link_fg": "#4cc2ff",
        "log_bg": "#1e1e1e",
        "log_fg": "#d4d4d4",
    },
}


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


class StatusBadge(tk.Canvas):
    """Circular status badge widget for server status.

    Colors:
        - working: green  (server running and ready)
        - not_working: blue (server stopped)
        - starting: yellow (server starting/loading)
    """

    STATUS_COLORS = {
        "working": "#4CAF50",
        "not_working": "#2196F3",
        "starting": "#FF9800",
    }

    def __init__(self, parent, width=24, height=24, status="starting", **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        self.width = width
        self.height = height
        self._status = status
        self._draw_badge()

    def set_status(self, status):
        """Update badge status and color."""
        if status not in self.STATUS_COLORS:
            status = "starting"
        self._status = status
        self._draw_badge()

    def _draw_badge(self):
        color = self.STATUS_COLORS.get(self._status, "#999999")
        outer_radius = max(3, min(self.width, self.height) // 4)
        self.create_oval(
            (self.width - 1) / 2 - outer_radius,
            (self.height - 1) / 2 - outer_radius,
            (self.width - 1) / 2 + outer_radius,
            (self.height - 1) / 2 + outer_radius,
            fill=color,
            outline="white",
            width=1,
        )
        inner_radius = max(2, min(self.width, self.height) // 6)
        self.create_oval(
            (self.width - 1) / 2 - inner_radius,
            (self.height - 1) / 2 - inner_radius,
            (self.width - 1) / 2 + inner_radius,
            (self.height - 1) / 2 + inner_radius,
            fill=color,
            outline="white",
            width=1,
        )


# ================= Встраиваемая консоль (Windows) =================
# Настоящее окно консоли (conhost/cmd.exe) встраивается в панель через
# SetParent — поэтому интерактивные TUI-программы (например pi) работают
# прямо в правой панели. Linux: xterm -into.

_WIN32_CONSOLE_CLASS = "ConsoleWindowClass"
_WIN32_GWL_STYLE = -16
_WIN32_WS_CAPTION = 0x00C00000
_WIN32_WS_THICKFRAME = 0x00040000
_WIN32_WS_MINIMIZEBOX = 0x00020000
_WIN32_WS_MAXIMIZEBOX = 0x00010000
_WIN32_WS_SYSMENU = 0x00080000
_WIN32_WS_DLGFRAME = 0x00400000
_WIN32_WS_BORDER = 0x00800000
_WIN32_WS_CHILD = 0x40000000
_WIN32_WS_POPUP = 0x80000000
_WIN32_GA_PARENT = 1
_WIN32_GWL_EXSTYLE = -20
_WIN32_GWLP_WNDPROC = -4
_WIN32_WS_EX_NOPARENTNOTIFY = 0x00000004
_WIN32_WM_SETFOCUS = 0x0007
_WIN32_WM_PARENTNOTIFY = 0x0210
_WIN32_WM_LBUTTONDOWN = 0x0201
_WIN32_WM_RBUTTONDOWN = 0x0204
_WIN32_WM_MBUTTONDOWN = 0x0207
_WIN32_SWP_NOSIZE = 0x0001
_WIN32_SWP_NOMOVE = 0x0002
_WIN32_SWP_NOZORDER = 0x0004
_WIN32_SWP_FRAMECHANGED = 0x0020
_WIN32_SW_HIDE = 0
_WIN32_SW_SHOW = 5

_win32_api_cache = None


class _WinRect(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def _win32_api():
    """Настраивает argtypes/restype для используемых функций WinAPI.

    Без этого ctypes возвращает обрезанные до 32 бит HANDLE/HWND/LONG_PTR
    на 64-битном Python.
    """
    global _win32_api_cache
    if _win32_api_cache is not None:
        return _win32_api_cache
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        _long_ptr = ctypes.c_int64
    else:
        _long_ptr = ctypes.c_long
    try:
        get_style = user32.GetWindowLongPtrW
        set_style = user32.SetWindowLongPtrW
    except AttributeError:  # 32-битный Python
        get_style = user32.GetWindowLongW
        set_style = user32.SetWindowLongW
    get_style.argtypes = [wintypes.HWND, ctypes.c_int]
    get_style.restype = _long_ptr
    set_style.argtypes = [wintypes.HWND, ctypes.c_int, _long_ptr]
    set_style.restype = _long_ptr
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
    user32.SetParent.restype = wintypes.HWND
    user32.MoveWindow.argtypes = [
        wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.BOOL,
    ]
    user32.MoveWindow.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetFocus.argtypes = [wintypes.HWND]
    user32.SetFocus.restype = wintypes.HWND
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, ctypes.c_uint]
    user32.GetAncestor.restype = wintypes.HWND
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(_WinRect)]
    user32.GetClientRect.restype = wintypes.BOOL
    user32.CallWindowProcW.argtypes = [
        ctypes.c_void_p, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM,
    ]
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        user32.CallWindowProcW.restype = ctypes.c_int64
    else:
        user32.CallWindowProcW.restype = ctypes.c_long
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetFocus.argtypes = []
    user32.GetFocus.restype = wintypes.HWND
    user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    user32.AttachThreadInput.restype = wintypes.BOOL
    kernel32.GetCurrentThreadId.argtypes = []
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    _win32_api_cache = {
        "user32": user32,
        "kernel32": kernel32,
        "get_style": get_style,
        "set_style": set_style,
    }
    return _win32_api_cache


def _hwnd_to_int(hwnd):
    """Нормализует HWND (int/HWND/None) к int (0 — нет окна)."""
    try:
        value = getattr(hwnd, "value", hwnd)
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _win32_wndproc_type():
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        result = ctypes.c_int64
    else:
        result = ctypes.c_long
    return ctypes.WINFUNCTYPE(
        result, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM,
    )


def _win32_process_children(root_pid, _depth=0):
    """Возвращает множество PID: сам процесс и все его потомки.

    Нужно, потому что окно консоли принадлежит conhost.exe или его
    дочернему cmd.exe, а не напрямую запущенному нами процессу.
    """
    try:
        kernel32 = ctypes.windll.kernel32
        TH32CS_SNAPPROCESS = 0x00000002

        class _ProcessEntry(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.CHAR * 260),
            ]

        kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        kernel32.Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry)]
        kernel32.Process32First.restype = wintypes.BOOL
        kernel32.Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry)]
        kernel32.Process32Next.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if int(snap) == -1:
            return {int(root_pid)}
        try:
            children = {}
            entry = _ProcessEntry()
            entry.dwSize = ctypes.sizeof(_ProcessEntry)
            ok = kernel32.Process32First(snap, ctypes.byref(entry))
            while ok:
                children.setdefault(int(entry.th32ParentProcessID), []).append(
                    int(entry.th32ProcessID)
                )
                ok = kernel32.Process32Next(snap, ctypes.byref(entry))
        finally:
            kernel32.CloseHandle(snap)
        result = {int(root_pid)}
        frontier = [int(root_pid)]
        while frontier:
            current = frontier.pop()
            for child in children.get(current, []):
                if child not in result:
                    result.add(child)
                    frontier.append(child)
        return result
    except Exception:
        return {int(root_pid)}


def _win32_find_console_window(pid, proc=None, timeout=8.0):
    """Ищет видимое HWND окна консоли (ConsoleWindowClass).

    Окно принадлежит conhost.exe или его дочернему процессу, поэтому
    ищем среди самого процесса и всех его потомков.
    Возвращает HWND или None (окно не появилось / процесс уже завершился).
    """
    api = _win32_api()
    user32 = api["user32"]
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum_cb(hwnd, _lparam):
        try:
            owner = wintypes.DWORD(0)
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if int(owner.value) not in _enum_cb.allowed:
                return True
            buf = ctypes.create_unicode_buffer(256)
            if user32.GetClassNameW(hwnd, buf, 256) <= 0:
                return True
            if buf.value == _WIN32_CONSOLE_CLASS and user32.IsWindowVisible(hwnd):
                found.append(hwnd)
                return False
        except Exception:
            pass
        return True

    _enum_cb.allowed = {int(pid)}
    deadline = time.time() + timeout
    while time.time() < deadline:
        del found[:]
        try:
            _enum_cb.allowed = _win32_process_children(pid)
            user32.EnumWindows(_enum_cb, 0)
        except Exception:
            pass
        if found:
            return found[0]
        if proc is not None:
            try:
                if proc.poll() is not None:
                    return None
            except Exception:
                pass
        time.sleep(0.15)
    return None


def _win32_kill_tree(pid):
    """Завершает процесс и всё его дерево (консоль + запущенные в ней программы)."""
    try:
        subprocess.run(
            ["taskkill", "/PID", str(int(pid)), "/T", "/F"],
            capture_output=True,
            startupinfo=_hidden_startupinfo_for_kill(),
            timeout=15,
        )
    except Exception:
        pass


def _hidden_startupinfo_for_kill():
    try:
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = subprocess.SW_HIDE
        return info
    except Exception:
        return None


def _win32_embed_console_window(host_hwnd, console_hwnd):
    """Убирает рамку консоли, встраивает её в host и растягивает на всю область."""
    api = _win32_api()
    user32 = api["user32"]
    user32.ShowWindow(console_hwnd, _WIN32_SW_HIDE)
    try:
        style = int(api["get_style"](console_hwnd, _WIN32_GWL_STYLE))
    except Exception:
        style = 0
    if style:
        # Окно консоли — WS_POPUP: у таких окон GetParent возвращает
        # владельца, а не родителя. Переводим в WS_CHILD, чтобы оно стало
        # полноценным дочерним окном панели (фокус, z-order, GetParent).
        style &= ~(
            _WIN32_WS_CAPTION
            | _WIN32_WS_THICKFRAME
            | _WIN32_WS_MINIMIZEBOX
            | _WIN32_WS_MAXIMIZEBOX
            | _WIN32_WS_SYSMENU
            | _WIN32_WS_DLGFRAME
            | _WIN32_WS_BORDER
            | _WIN32_WS_POPUP
        )
        style |= _WIN32_WS_CHILD
        try:
            api["set_style"](console_hwnd, _WIN32_GWL_STYLE, style)
        except Exception:
            pass
    try:
        # Гарантируем WM_PARENTNOTIFY при кликах по консоли, чтобы хост
        # мог возвращать ей клавиатурный фокус (см. _terminal_host_wndproc).
        exstyle = int(api["get_style"](console_hwnd, _WIN32_GWL_EXSTYLE))
        if exstyle & _WIN32_WS_EX_NOPARENTNOTIFY:
            api["set_style"](
                console_hwnd, _WIN32_GWL_EXSTYLE,
                exstyle & ~_WIN32_WS_EX_NOPARENTNOTIFY,
            )
    except Exception:
        pass
    user32.SetWindowPos(
        console_hwnd, None, 0, 0, 0, 0,
        _WIN32_SWP_NOZORDER | _WIN32_SWP_NOMOVE | _WIN32_SWP_NOSIZE | _WIN32_SWP_FRAMECHANGED,
    )
    prev_parent = user32.SetParent(console_hwnd, host_hwnd)
    if not prev_parent:
        raise OSError("SetParent failed")
    _win32_fit_console_to_host(host_hwnd, console_hwnd)
    user32.ShowWindow(console_hwnd, _WIN32_SW_SHOW)
    return True


def _win32_fit_console_to_host(host_hwnd, console_hwnd):
    """Растягивает встроенную консоль на клиентскую область хоста."""
    api = _win32_api()
    user32 = api["user32"]
    rect = _WinRect()
    try:
        if not user32.GetClientRect(host_hwnd, ctypes.byref(rect)):
            return False
    except Exception:
        return False
    width = int(rect.right - rect.left)
    height = int(rect.bottom - rect.top)
    if width <= 0 or height <= 0:
        return False
    try:
        return bool(user32.MoveWindow(console_hwnd, 0, 0, width, height, True))
    except Exception:
        return False


class _HfDownloadCancelled(Exception):
    """Служебное исключение: пользователь отменил скачивание файла."""


class LlamaServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM Server Controller v.0.2.0")
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
        initial_theme = self.config.get("theme", THEME_LIGHT)
        if initial_theme not in THEME_NAMES:
            initial_theme = THEME_LIGHT
        self.theme_var = tk.StringVar(value=initial_theme)
        self._theme_menus = []
        self.param_entries = {}
        self.param_group_frames = {}
        self.param_group_meta = {}
        self.params_listbox = None
        self.params_content_canvas = None
        self.params_content_host = None
        self.active_param_group_id = "main"
        self.main_paned = None
        self.center_paned = None
        # Правая панель: встроенная настоящая консоль ОС (Windows: cmd.exe
        # через SetParent; Linux: xterm -into), а не эмуляция через pipe.
        self.terminal_frame = None
        self.terminal_host = None
        self.terminal_status_label = None
        self.terminal_cwd = os.getcwd()
        self.terminal_proc = None
        self.terminal_hwnd = None
        self.terminal_gen = 0
        self._terminal_host_old_wndproc = None
        self._terminal_host_wndproc_cb = None
        try:
            self._terminal_root_hwnd = int(root.winfo_id())
        except (tk.TclError, TypeError, ValueError):
            self._terminal_root_hwnd = None
        self.terminal_visible_var = tk.BooleanVar(value=bool(self.config.get("terminal_visible", False)))
        self._terminal_watchdog_job = None
        self._terminal_resize_job = None
        self._terminal_spawn_failures = 0
        self.models_dir = str(self.config.get("models_dir", "") or "")
        self.models_window = None
        self.models_local_files = []
        self.hf_models = []
        self.hf_files = []
        self.hf_current_model = ""
        self.hf_download_flag = None
        self.enable_loaded_sound_var = tk.BooleanVar(value=self.config.get("sounds", {}).get("loaded", True))
        self.enable_stopped_sound_var = tk.BooleanVar(value=self.config.get("sounds", {}).get("stopped", True))
        self.open_browser_on_load_var = tk.BooleanVar(value=self.config.get("open_browser_on_load", True))
        self.install_in_progress = False
        self._restart_pending = False
        self.update_info = {
            "app_tag": None,
            "app_url": None,
            "app_error": None,
            "llama_tag": None,
            "llama_error": None,
            "llama_current": "",
        }
        self.update_badge = None
        self.badge = None
        self._exe_edit_job = None

        self.apply_window_geometry()
        self._setup_default_fonts()
        self.create_menu()
        self.create_widgets()
        self.apply_config_to_form()
        self.root.after(150, self._init_paned_sash)
        self.root.after(2500, lambda: self.check_updates(auto=True))

    def _init_paned_sash(self):
        if self.main_paned is not None:
            try:
                height = self.main_paned.winfo_height()
                if height > 240:
                    self.main_paned.sash_place(0, 0, int(height * 0.45))
            except tk.TclError:
                pass
        if self.center_paned is not None and self.terminal_frame is not None:
            try:
                if self.terminal_visible_var.get():
                    width = self.center_paned.winfo_width()
                    if width > 400:
                        self.center_paned.sash_place(0, int(width * 0.68), 0)
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
        # Кастомная полоска меню: на Windows нативный tk.Menu-менюбар рисуется
        # ОС и не красится через bg/fg, а Menubutton-выпадашки в этом
        # приложении не открываются. Поэтому заголовки — обычные кнопки,
        # а выпадающие панели — собственные Toplevel-окна без grab:
        # позиционируются под заголовком и полностью темятся.
        # Сами tk.Menu остаются хранилищем пунктов: команды/состояния
        # читаются из них и выполняются через menu.invoke(i).
        try:
            self.root.config(menu="")
        except tk.TclError:
            pass
        self._close_menu_popup()

        menu_bar_frame = tk.Frame(self.root)
        menu_bar_frame.pack(side=tk.TOP, fill=tk.X)

        file_menu = tk.Menu(menu_bar_frame, tearoff=0)
        file_menu.add_command(label=self.tr("menu_import"), command=self.import_settings)
        file_menu.add_command(label=self.tr("menu_export"), command=self.export_settings)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("menu_install_llama"), command=self.install_llama_cpp)
        file_menu.add_command(label=self.tr("menu_install_pi"), command=self.install_pi_agent)
        file_menu.add_command(label=self.tr("btn_devices"), command=self.list_devices)
        file_menu.add_command(label=self.tr("menu_models"), command=self.open_models_browser)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("menu_exit"), command=self.on_close)

        help_menu = tk.Menu(menu_bar_frame, tearoff=0)
        help_menu.add_command(label=self.tr("menu_help_help"), command=self.show_help)
        help_menu.add_command(label=self.tr("menu_check_updates"), command=lambda: self.check_updates(auto=False))
        help_menu.add_separator()
        help_menu.add_command(label=self.tr("menu_about"), command=self.show_about)

        sound_menu = tk.Menu(menu_bar_frame, tearoff=0)
        sound_menu.add_checkbutton(label=self.tr("menu_sound_loaded"), variable=self.enable_loaded_sound_var, command=self.on_sound_settings_changed)
        sound_menu.add_checkbutton(label=self.tr("menu_sound_stopped"), variable=self.enable_stopped_sound_var, command=self.on_sound_settings_changed)

        params_menu = tk.Menu(menu_bar_frame, tearoff=0)
        for group in PARAM_GROUPS:
            params_menu.add_command(
                label=self.i18n.group_title(group["id"]),
                command=lambda gid=group["id"]: self.show_param_section(gid),
            )

        view_menu = tk.Menu(menu_bar_frame, tearoff=0)
        view_menu.add_radiobutton(
            label=self.tr("theme_light"), variable=self.theme_var,
            value=THEME_LIGHT, command=lambda: self.set_theme(THEME_LIGHT),
        )
        view_menu.add_radiobutton(
            label=self.tr("theme_dark"), variable=self.theme_var,
            value=THEME_DARK, command=lambda: self.set_theme(THEME_DARK),
        )
        view_menu.add_separator()
        view_menu.add_checkbutton(
            label=self.tr("menu_terminal"), variable=self.terminal_visible_var,
            command=self.toggle_terminal,
        )

        self.file_menu = file_menu
        self._dropdown_menus = {
            "menu_file": file_menu,
            "menu_params": params_menu,
            "menu_sounds": sound_menu,
            "menu_view": view_menu,
            "menu_help": help_menu,
        }
        self._menu_buttons = []
        for label_key, dropdown in (
            ("menu_file", file_menu),
            ("menu_params", params_menu),
            ("menu_sounds", sound_menu),
            ("menu_view", view_menu),
            ("menu_help", help_menu),
        ):
            btn = tk.Button(
                menu_bar_frame, text=self.tr(label_key),
                relief=tk.FLAT, padx=10, pady=4,
            )
            btn._is_menu_header = True
            btn.configure(command=lambda m=dropdown, b=btn: self._toggle_menu_popup(b, m))
            btn.pack(side=tk.LEFT)
            self._menu_buttons.append(btn)
        self.menu_bar_frame = menu_bar_frame
        self.menu_bar = menu_bar_frame
        self._theme_menus = [file_menu, help_menu, sound_menu, params_menu, view_menu]
        self._menu_popup = None
        self._menu_popup_menu = None
        self._menu_popup_header = None
        if not getattr(self, "_menu_popup_away_bound", False):
            self.root.bind_all("<Button-1>", self._menu_popup_away, add="+")
            self.root.bind_all("<Escape>", self._menu_popup_esc, add="+")
            self._menu_popup_away_bound = True

    def _toggle_menu_popup(self, header_btn, menu):
        try:
            popup = getattr(self, "_menu_popup", None)
            alive = popup is not None and popup.winfo_exists()
        except tk.TclError:
            alive = False
        if alive and getattr(self, "_menu_popup_menu", None) is menu:
            self._close_menu_popup()
            return
        self._close_menu_popup()
        pal = self._current_palette()
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.configure(bg=pal["menu_bg"], bd=1, relief="solid")
        try:
            popup.attributes("-topmost", True)
        except tk.TclError:
            pass
        body = tk.Frame(popup, bg=pal["menu_bg"])
        body.pack(fill=tk.BOTH, expand=True)
        self._menu_popup = popup
        self._menu_popup_menu = menu
        self._menu_popup_header = header_btn
        self._menu_popup_body = body
        popup.bind("<Escape>", lambda _e: self._close_menu_popup())
        self._render_menu_popup_rows()
        try:
            popup.update_idletasks()
            req_w = popup.winfo_reqwidth()
            req_h = popup.winfo_reqheight()
            try:
                hdr_w = int(header_btn.winfo_width())
            except tk.TclError:
                hdr_w = 0
            w = max(req_w, hdr_w)
            x = int(header_btn.winfo_rootx())
            y = int(header_btn.winfo_rooty() + header_btn.winfo_height())
            try:
                sw = int(popup.winfo_screenwidth())
                sh = int(popup.winfo_screenheight())
            except tk.TclError:
                sw, sh = x + w + 1, y + req_h + 1
            if x + w > sw:
                x = max(0, sw - w)
            if y + req_h > sh:
                y = max(0, int(header_btn.winfo_rooty()) - req_h)
            popup.geometry(f"{w}x{req_h}+{x}+{y}")
        except tk.TclError:
            pass

    def _render_menu_popup_rows(self):
        popup = getattr(self, "_menu_popup", None)
        menu = getattr(self, "_menu_popup_menu", None)
        body = getattr(self, "_menu_popup_body", None)
        if popup is None or menu is None or body is None:
            return
        try:
            if not popup.winfo_exists():
                return
        except tk.TclError:
            return
        for child in body.winfo_children():
            try:
                child.destroy()
            except tk.TclError:
                pass
        pal = self._current_palette()
        try:
            body.configure(bg=pal["menu_bg"])
        except tk.TclError:
            return
        try:
            last = menu.index("end")
        except tk.TclError:
            return
        if last is None:
            return
        for i in range(last + 1):
            try:
                kind = menu.type(i)
            except tk.TclError:
                continue
            if kind == "separator":
                sep = tk.Frame(body, height=1, bg=pal["entry_border"])
                sep.pack(fill=tk.X, padx=8, pady=4)
                continue
            if kind == "tearoff":
                continue
            try:
                label = str(menu.entrycget(i, "label"))
                state = str(menu.entrycget(i, "state"))
            except tk.TclError:
                continue
            prefix = ""
            if kind == "checkbutton":
                try:
                    var_name = str(menu.entrycget(i, "variable"))
                    on = bool(int(self.root.getvar(var_name)))
                except (tk.TclError, ValueError):
                    on = False
                prefix = "✓ " if on else "    "
            elif kind == "radiobutton":
                try:
                    var_name = str(menu.entrycget(i, "variable"))
                    value = str(menu.entrycget(i, "value"))
                    on = str(self.root.getvar(var_name)) == value
                except tk.TclError:
                    on = False
                prefix = "● " if on else "○ "
            row = tk.Button(
                body, text=prefix + label, anchor=tk.W, relief=tk.FLAT,
                bg=pal["menu_bg"], fg=pal["menu_fg"],
                activebackground=pal["select_bg"],
                activeforeground=pal["select_fg"],
                disabledforeground=pal["muted_fg"],
                padx=12, pady=4,
                command=lambda idx=i: self._menu_popup_activate(idx),
            )
            if state != "normal":
                try:
                    row.configure(state=tk.DISABLED)
                except tk.TclError:
                    pass
            row.pack(fill=tk.X)
            row.bind(
                "<Enter>",
                lambda _e, w=row: w.configure(bg=pal["select_bg"], fg=pal["select_fg"])
                if w.cget("state") == tk.NORMAL else None,
            )
            row.bind(
                "<Leave>",
                lambda _e, w=row: w.configure(bg=pal["menu_bg"], fg=pal["menu_fg"])
                if w.cget("state") == tk.NORMAL else None,
            )

    def _menu_popup_activate(self, idx):
        menu = getattr(self, "_menu_popup_menu", None)
        if menu is None:
            return
        try:
            kind = menu.type(idx)
        except tk.TclError:
            self._close_menu_popup()
            return
        try:
            menu.invoke(idx)
        except tk.TclError:
            pass
        if kind == "command":
            self._close_menu_popup()
        else:
            try:
                popup = getattr(self, "_menu_popup", None)
                if popup is not None and popup.winfo_exists():
                    self._render_menu_popup_rows()
                else:
                    self._close_menu_popup()
            except tk.TclError:
                self._close_menu_popup()

    def _menu_popup_away(self, event):
        popup = getattr(self, "_menu_popup", None)
        if popup is None:
            return
        try:
            if not popup.winfo_exists():
                self._close_menu_popup()
                return
        except tk.TclError:
            self._close_menu_popup()
            return
        w = getattr(event, "widget", None)
        if w in getattr(self, "_menu_buttons", []):
            return
        try:
            path = str(w)
            if path == str(popup) or path.startswith(str(popup) + "."):
                return
        except tk.TclError:
            pass
        self._close_menu_popup()

    def _menu_popup_esc(self, _event=None):
        if getattr(self, "_menu_popup", None) is not None:
            self._close_menu_popup()

    def _close_menu_popup(self):
        popup = getattr(self, "_menu_popup", None)
        self._menu_popup = None
        self._menu_popup_menu = None
        self._menu_popup_header = None
        if popup is None:
            return
        try:
            popup.destroy()
        except tk.TclError:
            pass

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
                "width": "1200",
                "height": "900"
            },
            "sounds": {
                "loaded": True,
                "stopped": True
            },
            "open_browser_on_load": True,
            "custom_args": "",
            "theme": THEME_LIGHT,
            "terminal_visible": False,
            "models_dir": "",
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
        config["terminal_visible"] = bool(loaded_config.get("terminal_visible", config.get("terminal_visible", False)))
        config["models_dir"] = str(loaded_config.get("models_dir", config.get("models_dir", "")) or "")
        loaded_theme = loaded_config.get("theme", "")
        if loaded_theme in THEME_NAMES:
            config["theme"] = loaded_theme
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
            "theme": self.theme_var.get() if hasattr(self, "theme_var") else self.config.get("theme", THEME_LIGHT),
            "terminal_visible": self.terminal_visible_var.get() if hasattr(self, "terminal_visible_var") else self.config.get("terminal_visible", False),
            "models_dir": getattr(self, "models_dir", "") or "",
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

    def _status_fg(self, name):
        """Цвет статуса из текущей палитры: ok/warn/err."""
        pal = self._current_palette()
        return {
            "ok": pal["success"],
            "warn": pal["warning"],
            "err": pal["danger"],
        }.get(name, pal["fg"])

    def _apply_run_state_to_controls(self):
        """Приводит состояние кнопок/статуса в соответствие с is_running/server_ready
        (используется после перестроения интерфейса)."""
        if self.is_running:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.restart_btn.config(state=tk.NORMAL)
            if self.server_ready:
                self.status_label.config(text=self.tr("status_running"), fg=self._status_fg("ok"))
            else:
                self.status_label.config(text=self.tr("status_loading"), fg=self._status_fg("warn"))
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.restart_btn.config(state=tk.DISABLED)
            self.status_label.config(text=self.tr("status_stopped"), fg=self._status_fg("err"))
        if self.install_in_progress:
            self.install_llama_btn.config(state=tk.DISABLED, text=self.tr("btn_download_llama_installing"))
        else:
            self.install_llama_btn.config(state=tk.NORMAL, text=self.tr("btn_download_llama"))
        self._update_badge_status()

    def _update_badge_status(self):
        """Updates the circular badge color based on server state.

        - working (green): is_running and server_ready
        - starting (yellow): is_running and not server_ready
        - not_working (blue): not is_running
        """
        if self.is_running and self.server_ready:
            status = "working"
        elif self.is_running and not self.server_ready:
            status = "starting"
        else:
            status = "not_working"
        if getattr(self, "badge", None) is not None:
            self.badge.set_status(status)

    # --- Проверка обновлений (приложение + сборки llama.cpp) ---
    def check_updates(self, auto=False):
        """Запускает фоновую проверку обновлений. auto=True — тихо (бейдж)."""
        if getattr(self, "_update_check_running", False):
            if not auto:
                self.show_updates_dialog()
            return
        self._update_check_running = True
        self._refresh_update_badge()
        threading.Thread(target=self._check_updates_worker, args=(auto,), daemon=True).start()

    def _check_updates_worker(self, auto):
        exe_snapshot = (self.config.get("exe_path") or "").strip()
        app_tag = app_url = app_error = None
        try:
            release = fetch_github_latest_release(APP_GITHUB_REPO, timeout=20)
            app_tag = release["tag"]
            app_url = release["url"]
        except Exception as exc:
            app_error = str(exc) or exc.__class__.__name__
        llama_tag = llama_error = None
        try:
            if sys.platform == "win32":
                tag, _assets, _warning = fetch_windows_assets(timeout=30, language=self.i18n.language)
            else:
                tag, _assets, _warning = fetch_linux_assets(timeout=30, language=self.i18n.language)
            llama_tag = tag
        except Exception as exc:
            llama_error = str(exc) or exc.__class__.__name__
        # Версия установленного сервера: сначала спрашиваем сам бинарник
        # по пути из конфигурации (работает и для нестандартной папки),
        # запасной вариант — тег папки установки, если exe лежит в ней.
        # Если путь сменили, пока воркер работал, — чужой результат отбрасываем.
        exe_path = (self.config.get("exe_path") or "").strip()
        llama_current = get_llama_server_version(exe_path, timeout=15)
        if not llama_current:
            llama_current = self._install_tag_for_exe(exe_path)
        if (self.config.get("exe_path") or "").strip() != exe_snapshot:
            llama_current = ""
        self.root.after(
            0,
            lambda: self._on_updates_checked(
                auto, app_tag, app_url, app_error, llama_tag, llama_error,
                llama_current, exe_snapshot,
            ),
        )

    def _on_updates_checked(self, auto, app_tag, app_url, app_error, llama_tag, llama_error,
                            llama_current="", exe_snapshot=None):
        self._update_check_running = False
        if exe_snapshot is not None and self._current_exe_path() != exe_snapshot:
            llama_current = ""
        self.update_info.update({
            "app_tag": app_tag,
            "app_url": app_url or APP_RELEASES_URL,
            "app_error": app_error,
            "llama_tag": llama_tag,
            "llama_error": llama_error,
            "llama_current": llama_current,
        })
        self._refresh_update_badge()
        self._refresh_server_version_label(detect=False)
        if not auto:
            self.show_updates_dialog()

    def _install_tag_for_exe(self, exe):
        """Тег из install.release_tag, но только если exe лежит в папке установки.

        Иначе (сервер выбран вручную из другой папки) тег к этому файлу
        отношения не имеет — возвращаем "", чтобы не показывать чужую версию.
        """
        install = self.config.get("install", {})
        tag = (install.get("release_tag") or "").strip()
        directory = (install.get("directory") or "").strip()
        if not tag:
            return ""
        if not exe or not directory:
            return tag
        try:
            exe_abs = os.path.normcase(os.path.abspath(os.path.normpath(exe)))
            dir_abs = os.path.normcase(os.path.abspath(os.path.normpath(directory)))
            if os.path.commonpath([exe_abs, dir_abs]) == dir_abs:
                return tag
        except ValueError:
            return ""
        except OSError:
            return tag
        return ""

    def _llama_current(self):
        """Установленная сборка: живой опрос, иначе тег папки установки."""
        current = (self.update_info.get("llama_current") or "").strip()
        if not current:
            current = self._install_tag_for_exe(self._current_exe_path())
        return current

    def _current_exe_path(self):
        """Путь к серверу: из поля формы, иначе из конфига."""
        if hasattr(self, "exe_entry"):
            return self.exe_entry.get().strip()
        return (self.config.get("exe_path") or "").strip()

    def _refresh_server_version_label(self, detect=True):
        """Показывает актуальную версию llama-server рядом с полем «Сервер»."""
        label = getattr(self, "server_version_label", None)
        if label is None:
            return
        exe = self._current_exe_path()
        try:
            if not exe:
                label.config(text="")
                return
            if not os.path.exists(exe):
                label.config(text=self.tr("server_version_not_found"))
                return
            current = self._llama_current()
            if current:
                label.config(text=self.tr("label_server_version", version=current))
                return
            label.config(text=self.tr("server_version_checking"))
            if detect:
                self._detect_server_version_async()
        except tk.TclError:
            pass

    def _detect_server_version_async(self):
        if getattr(self, "_server_version_detecting", False):
            return
        exe = self._current_exe_path()
        if not exe or not os.path.exists(exe):
            return
        self._server_version_detecting = True
        threading.Thread(target=self._server_version_worker, args=(exe,), daemon=True).start()

    def _server_version_worker(self, exe):
        version = get_llama_server_version(exe, timeout=15)
        self.root.after(0, lambda: self._on_server_version_detected(exe, version))

    def _on_server_version_detected(self, exe, version):
        self._server_version_detecting = False
        label = getattr(self, "server_version_label", None)
        if label is None:
            return
        if self._current_exe_path() != exe:
            return
        try:
            if version:
                self.update_info["llama_current"] = version
                label.config(text=self.tr("label_server_version", version=version))
                self._refresh_update_badge()
            else:
                label.config(text=self.tr("server_version_unknown"))
        except tk.TclError:
            pass

    def _on_exe_path_changed(self, detect=True):
        """Путь к серверу сменился: сбрасываем кэшированную версию,
        обновляем надпись «Установленная версия» и бейдж обновлений."""
        self.update_info["llama_current"] = ""
        self._refresh_server_version_label(detect=detect)
        self._refresh_update_badge()

    def _on_exe_entry_edited(self, _event=None):
        """Ручной ввод пути: обновляем версию с задержкой, чтобы не
        запускать опрос на каждое нажатие клавиши."""
        old_job = getattr(self, "_exe_edit_job", None)
        if old_job is not None:
            try:
                self.root.after_cancel(old_job)
            except tk.TclError:
                pass
        self._exe_edit_job = self.root.after(700, self._on_exe_entry_changed_debounced)

    def _on_exe_entry_changed_debounced(self):
        self._exe_edit_job = None
        self._on_exe_path_changed()

    def _updates_available(self):
        """Возвращает (app_newer, llama_newer)."""
        info = self.update_info
        app_newer = bool(info.get("app_tag")) and is_newer_tag(info["app_tag"], APP_VERSION)
        llama_current = self._llama_current()
        if info.get("llama_tag"):
            llama_newer = (not llama_current) or is_newer_tag(info["llama_tag"], llama_current)
        else:
            llama_newer = False
        return app_newer, llama_newer

    def _refresh_update_badge(self):
        badge = getattr(self, "update_badge", None)
        if badge is None:
            return
        pal = self._current_palette()
        try:
            if getattr(self, "_update_check_running", False):
                badge.config(text=self.tr("update_checking"), fg=pal["link_fg"])
                return
            app_newer, llama_newer = self._updates_available()
            parts = []
            if app_newer:
                parts.append(self.tr("badge_app", tag=self.update_info["app_tag"]))
            if llama_newer:
                parts.append(self.tr("badge_llama", tag=self.update_info["llama_tag"]))
            text = self.tr("badge_prefix") + " • ".join(parts) if parts else ""
            badge.config(text=text, fg=pal["link_fg"])
        except tk.TclError:
            pass

    def show_updates_dialog(self):
        info = self.update_info
        app_newer, llama_newer = self._updates_available()
        window = tk.Toplevel(self.root)
        window.title(self.tr("title_updates"))
        window.geometry("520x300")
        window.transient(self.root)

        if not info.get("app_tag") and not info.get("llama_tag"):
            error = info.get("app_error") or info.get("llama_error") or ""
            if getattr(self, "_update_check_running", False):
                summary = self.tr("update_checking")
            elif error:
                summary = self.tr("update_check_failed", error=error)
            else:
                summary = self.tr("update_checking")
            app_row = summary
            llama_row = ""
        else:
            if app_newer:
                app_row = self.tr("update_app_available", latest=info["app_tag"], current=APP_VERSION)
            else:
                app_row = self.tr("update_app_uptodate", current=APP_VERSION)
            llama_current = self._llama_current()
            if info.get("llama_tag"):
                if llama_newer and llama_current:
                    llama_row = self.tr(
                        "update_llama_available",
                        latest=info["llama_tag"], current=llama_current,
                    )
                elif llama_newer:
                    exe_name = os.path.basename((self.config.get("exe_path") or "").strip())
                    if exe_name:
                        llama_row = self.tr(
                            "update_llama_unknown",
                            exe=exe_name, latest=info["llama_tag"],
                        )
                    else:
                        llama_row = self.tr("update_llama_not_installed", latest=info["llama_tag"])
                else:
                    llama_row = self.tr("update_llama_uptodate", current=llama_current or info["llama_tag"])
            else:
                llama_row = self.tr("update_check_failed", error=info.get("llama_error") or "")

        def open_releases():
            webbrowser.open(info.get("app_url") or APP_RELEASES_URL)

        def install_llama():
            window.destroy()
            self.install_llama_cpp()

        app_frame = tk.Frame(window)
        app_frame.pack(fill=tk.X, padx=12, pady=(12, 4))
        tk.Label(
            app_frame, text=app_row, anchor=tk.W, justify=tk.LEFT, wraplength=340,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(app_frame, text=self.tr("btn_open_releases"), command=open_releases).pack(side=tk.RIGHT, padx=(8, 0))

        if llama_row:
            llama_frame = tk.Frame(window)
            llama_frame.pack(fill=tk.X, padx=12, pady=4)
            tk.Label(
                llama_frame, text=llama_row, anchor=tk.W, justify=tk.LEFT, wraplength=340,
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Button(llama_frame, text=self.tr("menu_install_llama"), command=install_llama).pack(side=tk.RIGHT, padx=(8, 0))

        buttons = tk.Frame(window)
        buttons.pack(fill=tk.X, padx=12, pady=(12, 12))
        tk.Button(buttons, text=self.tr("btn_close"), command=window.destroy).pack(side=tk.RIGHT)
        self.apply_theme()

    def toggle_language(self):
        """Переключает язык интерфейса RU <-> EN с перестроением окна."""
        if self.is_running:
            messagebox.showwarning(self.tr("msg_attention"), self.tr("msg_reset_while_running"))
            return
        self.i18n.toggle()
        self.config["language"] = self.i18n.language
        self.rebuild_ui()
        self.save_config()

    def set_theme(self, theme):
        """Переключает светлую/тёмную тему и сохраняет выбор в конфиг."""
        if theme not in THEME_NAMES:
            return
        self.theme_var.set(theme)
        self.config["theme"] = theme
        self.apply_theme()
        self.save_config()

    def _current_palette(self):
        theme = self.theme_var.get() if hasattr(self, "theme_var") else THEME_LIGHT
        if theme not in THEMES:
            theme = THEME_LIGHT
        return THEMES[theme]

    _BUTTON_KINDS = ("default", "primary", "success", "danger", "warning")

    @staticmethod
    def _setup_default_fonts():
        """Современный базовый шрифт интерфейса (идемпотентно)."""
        for name, family, size in (
            ("TkDefaultFont", "Segoe UI", 9),
            ("TkTextFont", "Consolas", 9),
            ("TkHeadingFont", "Segoe UI", 9),
            ("TkCaptionFont", "Segoe UI", 8),
            ("TkSmallCaptionFont", "Segoe UI", 8),
            ("TkTooltipFont", "Segoe UI", 8),
            ("TkMenuFont", "Segoe UI", 9),
            ("TkIconFont", "Segoe UI", 9),
        ):
            try:
                tkfont.nametofont(name).configure(family=family, size=size)
            except tk.TclError:
                pass

    def _swap_legacy_fonts(self, node=None):
        """Заменяет Arial на Segoe UI у всех созданных виджетов.

        Новые объекты шрифтов кэшируются, поэтому проход дешёвый
        и безопасно вызывается при каждом применении темы.
        """
        if node is None:
            node = self.root
            if not hasattr(self, "_font_cache"):
                self._font_cache = {}
        try:
            children = node.winfo_children()
        except tk.TclError:
            return
        for child in children:
            try:
                spec = child.cget("font")
            except tk.TclError:
                spec = None
            if spec:
                try:
                    key = str(spec)
                except tk.TclError:
                    continue
                if key not in self._font_cache:
                    try:
                        probe = tkfont.Font(font=key)
                        if str(probe.cget("family")).lower() == "arial":
                            probe.configure(family="Segoe UI")
                            self._font_cache[key] = probe
                        else:
                            self._font_cache[key] = False
                    except tk.TclError:
                        self._font_cache[key] = False
                modern = self._font_cache[key]
                if modern:
                    try:
                        child.configure(font=modern)
                    except tk.TclError:
                        pass
            self._swap_legacy_fonts(child)

    def _modern_button(self, parent, text, command=None, kind="default", font=None, **kwargs):
        """Создаёт плоскую кнопку в стиле темы (см. _style_button)."""
        btn = tk.Button(parent, text=text, command=command, **kwargs)
        if font is not None:
            try:
                btn.configure(font=font)
            except tk.TclError:
                pass
        btn._btn_kind = kind if kind in self._BUTTON_KINDS else "default"
        self._style_button(btn, self._current_palette())
        return btn

    def _style_button(self, widget, pal):
        """Плоский стиль кнопки с hover/press. Вызывается из теме́ра."""
        kind = getattr(widget, "_btn_kind", "default")
        if kind not in self._BUTTON_KINDS:
            kind = "default"
        if kind == "default":
            bg, fg = pal["button_bg"], pal["button_fg"]
            hov, press = pal["button_hover"], pal["button_press"]
            edge = pal["button_border"]
        elif kind == "primary":
            bg, fg = pal["accent"], pal["accent_fg"]
            hov, press, edge = pal["accent_hover"], pal["accent_press"], pal["accent"]
        elif kind == "success":
            bg, fg = pal["success"], "#ffffff"
            hov, press, edge = pal["success_hover"], pal["success_press"], pal["success"]
        elif kind == "danger":
            bg, fg = pal["danger"], "#ffffff"
            hov, press, edge = pal["danger_hover"], pal["danger_press"], pal["danger"]
        else:
            bg, fg = pal["warning"], "#ffffff"
            hov, press, edge = pal["warning_hover"], pal["warning_press"], pal["warning"]
        widget._btn_colors = (bg, hov, press)
        # Отключённая акцентная кнопка: светлый текст читается на цветном фоне.
        dis_fg = pal["muted_fg"] if kind == "default" else "#e6e6e6"
        try:
            widget.configure(
                relief=tk.FLAT, bd=0, highlightthickness=1,
                highlightbackground=edge, highlightcolor=pal["accent"],
                bg=bg, fg=fg,
                activebackground=hov, activeforeground=fg,
                disabledforeground=dis_fg,
                padx=10, pady=3,
            )
        except tk.TclError:
            return
        if getattr(widget, "_modern_hover_bound", False):
            return
        widget._modern_hover_bound = True
        widget.bind(
            "<Enter>",
            lambda _e, w=widget: w.configure(bg=w._btn_colors[1])
            if w.cget("state") == tk.NORMAL else None,
        )
        widget.bind(
            "<Leave>",
            lambda _e, w=widget: w.configure(bg=w._btn_colors[0]),
        )
        widget.bind(
            "<ButtonPress-1>",
            lambda _e, w=widget: w.configure(bg=w._btn_colors[2])
            if w.cget("state") == tk.NORMAL else None,
        )
        widget.bind(
            "<ButtonRelease-1>",
            lambda _e, w=widget: w.configure(bg=w._btn_colors[1])
            if w.cget("state") == tk.NORMAL else None,
        )

    def _make_scrolled_text(self, parent, scrollbar_style=None, pack_padx=0, pack_pady=0, **text_kwargs):
        """Text + ttk.Scrollbar (в отличие от ScrolledText красится в тёмной теме).

        Возвращает виджет Text с тем же API (insert/get/delete/see/bind).
        """
        container = tk.Frame(parent)
        container.pack(expand=True, fill=tk.BOTH, padx=pack_padx, pady=pack_pady)
        text = tk.Text(container, **text_kwargs)
        if scrollbar_style:
            scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL,
                                      command=text.yview, style=scrollbar_style)
        else:
            scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return text

    def _inherited_bg(self, widget, pal):
        """Фон родителя: контейнеры сливаются с поверхностью (карточки)."""
        try:
            master = widget.master
            if master is not None:
                return master.cget("bg")
        except (tk.TclError, AttributeError):
            pass
        return pal["bg"]

    def apply_theme(self):
        """Применяет текущую тему ко всем виджетам окна (включая диалоги)."""
        pal = self._current_palette()
        try:
            self.root.configure(bg=pal["bg"])
        except tk.TclError:
            pass
        try:
            style = ttk.Style(self.root)
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass
            style.configure(
                "TCombobox",
                fieldbackground=pal["entry_bg"],
                background=pal["button_bg"],
                foreground=pal["entry_fg"],
                arrowcolor=pal["fg"],
            )
            style.map(
                "TCombobox",
                fieldbackground=[("readonly", pal["entry_bg"])],
                foreground=[("readonly", pal["entry_fg"])],
                background=[("readonly", pal["button_bg"])],
                arrowcolor=[("readonly", pal["fg"])],
            )
            style.configure(
                "Treeview",
                background=pal["entry_bg"],
                foreground=pal["entry_fg"],
                fieldbackground=pal["entry_bg"],
                rowheight=22,
            )
            style.map(
                "Treeview",
                background=[("selected", pal["select_bg"])],
                foreground=[("selected", pal["select_fg"])],
            )
            style.configure(
                "Treeview.Heading",
                background=pal["button_hover"],
                foreground=pal["button_fg"],
            )
            style.configure("TSeparator", background=pal["border"])
            style.map(
                "Treeview.Heading",
                background=[("active", pal["select_bg"])],
                foreground=[("active", pal["select_fg"])],
            )
            style.configure("TNotebook", background=pal["bg"])
            style.configure(
                "TNotebook.Tab",
                background=pal["button_bg"],
                foreground=pal["button_fg"],
                padding=6,
            )
            style.map(
                "TNotebook.Tab",
                background=[("selected", pal["select_bg"])],
                foreground=[("selected", pal["select_fg"])],
            )
            style.configure(
                "TProgressbar",
                background=pal["select_bg"],
                troughcolor=pal["entry_bg"],
            )
        except tk.TclError:
            pass
        try:
            # Скроллбары: классический tk.Scrollbar игнорирует цвета в Win11,
            # поэтому везде используется ttk.Scrollbar (clam красит полностью).
            # Стрелки красятся в цвет ползунка (arrowcolor) — так задумано.
            for _sb_style in ("TScrollbar", "Vertical.TScrollbar", "Horizontal.TScrollbar"):
                style.configure(
                    _sb_style,
                    background=pal["entry_border"],
                    troughcolor=pal["bg"],
                    bordercolor=pal["bg"],
                    arrowcolor=pal["entry_border"],
                    relief="flat",
                )
                style.map(
                    _sb_style,
                    background=[("active", pal["select_bg"])],
                    arrowcolor=[("active", pal["select_bg"])],
                )
            # Тёмный вариант для лога (сам лог тёмный в обеих темах).
            for _sb_style in ("Darkbar.Vertical.TScrollbar", "Darkbar.Horizontal.TScrollbar"):
                style.configure(
                    _sb_style,
                    background="#5a5a5a",
                    troughcolor="#1e1e1e",
                    bordercolor="#1e1e1e",
                    arrowcolor="#5a5a5a",
                    relief="flat",
                )
                style.map(
                    _sb_style,
                    background=[("active", "#0f6cbd")],
                    arrowcolor=[("active", "#0f6cbd")],
                )
        except tk.TclError:
            pass
        for menu in getattr(self, "_theme_menus", []):
            try:
                menu.configure(
                    bg=pal["menu_bg"],
                    fg=pal["menu_fg"],
                    activebackground=pal["select_bg"],
                    activeforeground=pal["select_fg"],
                    selectcolor=pal["fg"],
                )
            except tk.TclError:
                pass
        try:
            getattr(self, "menu_bar_frame", None).configure(bg=pal["menu_bg"])
        except (tk.TclError, AttributeError):
            pass
        for btn in getattr(self, "_menu_buttons", []):
            self._style_menu_header(btn, pal)
        self._theme_widget_tree(self.root, pal)
        self._swap_legacy_fonts()
        self._apply_run_state_to_controls()
        self._refresh_update_badge()

    def _style_menu_header(self, widget, pal):
        """Стиль кнопки-заголовка полоски меню (цвета темы)."""
        try:
            widget.configure(
                bg=pal["menu_bg"], fg=pal["menu_fg"],
                activebackground=pal["select_bg"],
                activeforeground=pal["select_fg"],
                relief=tk.FLAT, bd=0, highlightthickness=0,
                padx=10, pady=4,
            )
        except tk.TclError:
            pass

    def _theme_widget_tree(self, node, pal):
        for child in node.winfo_children():
            self._theme_widget(child, pal)
            self._theme_widget_tree(child, pal)

    def _theme_widget(self, widget, pal):
        try:
            widget_class = widget.winfo_class()
        except tk.TclError:
            return
        try:
            if widget_class == "Labelframe":
                widget.configure(
                    bg=pal["card_bg"], fg=pal["fg"],
                    relief=tk.SOLID, borderwidth=1,
                    font=("Segoe UI", 9, "bold"),
                )
            elif widget_class == "Frame":
                widget.configure(bg=self._inherited_bg(widget, pal))
            elif widget_class in ("PanedWindow", "Panedwindow", "Toplevel", "Tk"):
                widget.configure(bg=pal["bg"])
                if widget_class.lower() == "panedwindow":
                    try:
                        widget.configure(sashrelief=tk.FLAT)
                    except tk.TclError:
                        pass
            elif widget_class == "Canvas":
                bg = self._inherited_bg(widget, pal)
                widget.configure(bg=bg, highlightbackground=bg)
            elif widget_class == "Label":
                if widget == getattr(self, "update_badge", None):
                    widget.configure(bg=self._inherited_bg(widget, pal))
                    return
                bg = self._inherited_bg(widget, pal)
                try:
                    current_fg = widget.cget("fg")
                except tk.TclError:
                    current_fg = ""
                if current_fg in ("#555555",):
                    widget.configure(bg=bg, fg=pal["secondary_fg"])
                elif current_fg in ("#777777",):
                    widget.configure(bg=bg, fg=pal["muted_fg"])
                else:
                    widget.configure(bg=bg, fg=pal["fg"])
            elif widget_class == "Button":
                if getattr(widget, "_is_menu_header", False):
                    self._style_menu_header(widget, pal)
                else:
                    self._style_button(widget, pal)
            elif widget_class == "Checkbutton":
                bg = self._inherited_bg(widget, pal)
                widget.configure(
                    bg=bg, fg=pal["fg"],
                    activebackground=bg,
                    activeforeground=pal["fg"],
                    selectcolor=pal["check_select"],
                    relief=tk.FLAT,
                )
            elif widget_class == "Entry":
                widget.configure(
                    relief=tk.FLAT, bd=0, highlightthickness=1,
                    highlightbackground=pal["entry_border"],
                    highlightcolor=pal["accent"],
                    bg=pal["entry_bg"], fg=pal["entry_fg"],
                    insertbackground=pal["entry_fg"],
                    selectbackground=pal["select_bg"],
                    selectforeground=pal["select_fg"],
                )
            elif widget_class == "Listbox":
                widget.configure(
                    relief=tk.FLAT, bd=0, highlightthickness=1,
                    highlightbackground=pal["border"],
                    highlightcolor=pal["accent"],
                    bg=pal["entry_bg"], fg=pal["entry_fg"],
                    selectbackground=pal["select_bg"],
                    selectforeground=pal["select_fg"],
                )
            elif widget_class == "Text":
                if widget == getattr(self, "log_area", None):
                    widget.configure(
                        relief=tk.FLAT, bd=0, highlightthickness=1,
                        highlightbackground=pal["border"],
                        highlightcolor=pal["border"],
                        bg=pal["log_bg"], fg=pal["log_fg"],
                        insertbackground=pal["log_fg"],
                        selectbackground=pal["select_bg"],
                        selectforeground=pal["select_fg"],
                    )
                else:
                    widget.configure(
                        relief=tk.FLAT, bd=0, highlightthickness=1,
                        highlightbackground=pal["entry_border"],
                        highlightcolor=pal["accent"],
                        bg=pal["entry_bg"], fg=pal["entry_fg"],
                        insertbackground=pal["entry_fg"],
                        selectbackground=pal["select_bg"],
                        selectforeground=pal["select_fg"],
                    )
            elif widget_class == "Scrollbar":
                widget.configure(
                    relief=tk.FLAT, borderwidth=0, width=13,
                    bg=pal["button_bg"], troughcolor=pal["bg"],
                    activebackground=pal["select_bg"],
                )
        except tk.TclError:
            pass

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
        # Сохраняем видимость консоли (сам процесс консоли переживает
        # rebuild отдельно: см. rebuild_ui/_terminal_shutdown).
        try:
            snapshot["terminal_visible"] = bool(self.terminal_visible_var.get())
        except (tk.TclError, AttributeError):
            snapshot["terminal_visible"] = False
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
            elif isinstance(widget, tk.StringVar):
                widget.set(str(value))
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
        # Сохраняем флаг видимости терминала до пересоздания BooleanVar в меню.
        terminal_visible = snapshot.get("terminal_visible", False)
        try:
            self.terminal_visible_var.set(bool(terminal_visible))
        except (tk.TclError, AttributeError):
            pass
        self.param_entries = {}
        self.param_group_frames = {}
        self.param_group_meta = {}

        # Встроенная консоль привязана к HWND хоста: при уничтожении виджетов
        # её окно умрёт вместе с родителем, поэтому процесс гасим заранее,
        # а после перестроения панель сама запустит новую консоль.
        self._terminal_shutdown()

        for child in self.root.winfo_children():
            child.destroy()

        # контекстное меню лога создается внутри create_widgets
        self.create_menu()
        try:
            self.terminal_visible_var.set(bool(terminal_visible))
        except (tk.TclError, AttributeError):
            pass
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
            elif isinstance(widget, tk.StringVar):
                widget.set(str(value))
            else:
                widget.delete(0, tk.END)
                widget.insert(0, str(value))

        try:
            visible = bool(self.config.get("terminal_visible", False))
            self.terminal_visible_var.set(visible)
            if visible:
                self.show_terminal(save=False)
            else:
                self.hide_terminal(save=False)
        except (tk.TclError, AttributeError):
            pass

        self.models_dir = str(self.config.get("models_dir", "") or "")

    def create_widgets(self):
        # Горизонтальный сплит: слева основной интерфейс, справа терминал.
        self.center_paned = tk.PanedWindow(
            self.root, orient=tk.HORIZONTAL, sashwidth=7, sashrelief=tk.RAISED, showhandle=True,
        )
        self.center_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(8, 8))

        left_container = tk.Frame(self.center_paned)
        self.center_paned.add(left_container, minsize=560, stretch="always")
        self.left_container = left_container

        path_frame = tk.LabelFrame(left_container, text=" " + self.tr("frame_paths") + " ", padx=8, pady=4)
        path_frame.pack(fill=tk.X, pady=(0, 4))
        self.path_frame = path_frame

        server_label_badge_frame = tk.Frame(path_frame, padx=2, pady=2)
        server_label_badge_frame.grid(row=0, column=0, sticky=tk.W, pady=2)

        label_server = tk.Label(server_label_badge_frame, text=self.tr("label_server"), font=("Arial", 10, "bold"))
        self.badge = StatusBadge(server_label_badge_frame, width=24, height=24, status="starting")
        label_server.pack(side=tk.LEFT, padx=2)
        self.badge.pack(side=tk.LEFT, padx=2)

        self.exe_entry = tk.Entry(path_frame)
        self.exe_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        self.exe_entry.bind("<KeyRelease>", self._on_exe_entry_edited)
        self.exe_entry.bind("<FocusOut>", lambda _event: self._on_exe_path_changed())
        tk.Button(path_frame, text=self.tr("btn_browse"), command=self.browse_exe).grid(row=0, column=2, padx=2, pady=2)
        self.install_llama_btn = tk.Button(path_frame, text=self.tr("btn_download_llama"), command=self.install_llama_cpp)
        self.install_llama_btn._btn_kind = "primary"
        self.install_llama_btn.grid(row=0, column=3, padx=2, pady=2)
        self.server_version_label = tk.Label(path_frame, text="", font=("Arial", 9, "italic"))
        self.server_version_label.grid(row=0, column=5, padx=6, pady=2, sticky=tk.W)
        self.update_badge = tk.Label(path_frame, text="", fg="#1565c0", cursor="hand2", font=("Arial", 9, "bold"))
        self.update_badge.grid(row=1, column=5, padx=6, pady=2, sticky=tk.W)
        self.update_badge.bind("<Button-1>", lambda _event: self.show_updates_dialog())

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
        self.open_browser_on_load_chk = tk.Checkbutton(
            path_frame, text=self.tr("chk_open_browser"), variable=self.open_browser_on_load_var,
            font=("Arial", 9), command=self.on_browser_checkbox_changed,
        )
        self.open_browser_on_load_chk.grid(row=2, column=5, sticky=tk.W, padx=6, pady=(2, 0))

        tk.Label(path_frame, text=self.tr("label_commands")).grid(row=3, column=0, sticky=tk.W, pady=2)
        self.custom_args_entry = tk.Entry(path_frame, font=("Consolas", 9))
        self.custom_args_entry.grid(row=3, column=1, columnspan=4, sticky=tk.EW, padx=5, pady=2)
        path_frame.columnconfigure(1, weight=1)

        toolbar = tk.Frame(left_container)
        toolbar.pack(fill=tk.X, pady=4)
        self.toolbar = toolbar

        tk.Button(toolbar, text=self.tr("btn_save"), command=self.save_current_settings).pack(side=tk.LEFT, padx=(0, 2))
        tk.Button(toolbar, text=self.tr("btn_import"), command=self.import_settings).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text=self.tr("btn_export"), command=self.export_settings).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text=self.tr("btn_reset"), command=self.reset_settings).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text=self.tr("btn_models"), command=self.open_models_browser).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        self.start_btn = self._modern_button(
            toolbar, text=self.tr("btn_start"), kind="success",
            font=("Arial", 10, "bold"), command=self.start_server,
        )
        self.start_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = self._modern_button(
            toolbar, text=self.tr("btn_stop"), kind="danger",
            font=("Arial", 10, "bold"), command=self.stop_server, state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        self.restart_btn = self._modern_button(
            toolbar, text=self.tr("btn_restart"), kind="warning",
            font=("Arial", 10, "bold"), command=self.restart_server, state=tk.DISABLED,
        )
        self.restart_btn.pack(side=tk.LEFT, padx=2)
        self._semantic_buttons = ()

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        self.lang_btn = tk.Button(
            toolbar, text=self.tr("btn_lang_" + self.i18n.language),
            font=("Arial", 9, "bold"), width=4, command=self.toggle_language,
        )
        self.lang_btn.pack(side=tk.LEFT, padx=2)

        self.main_paned = tk.PanedWindow(
            left_container, orient=tk.VERTICAL, sashwidth=5, sashrelief=tk.FLAT, showhandle=True,
        )
        self.main_paned.pack(fill=tk.BOTH, expand=True, pady=(0, 0))

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

        list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
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

        self.group_title_label = tk.Label(content_panel, text="", font=("Segoe UI", 11, "bold"), anchor=tk.W)
        self.group_title_label.pack(fill=tk.X, pady=(0, 2))

        self.group_hint_label = tk.Label(
            content_panel, text="", font=("Arial", 8), fg="#555555",
            anchor=tk.W, justify=tk.LEFT, wraplength=720,
        )
        self.group_hint_label.pack(fill=tk.X, pady=(0, 6))

        content_scrollbar = ttk.Scrollbar(content_panel, orient=tk.VERTICAL)
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

        self.status_label = tk.Label(log_header_frame, text=self.tr("status_stopped"), fg="red", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT, padx=(8, 0))

        copy_btn = tk.Button(log_header_frame, text=self.tr("btn_copy"), font=("Arial", 8), command=self.copy_logs_to_clipboard)
        copy_btn.pack(side=tk.RIGHT, padx=4)

        clear_btn = tk.Button(log_header_frame, text=self.tr("btn_clear"), font=("Arial", 8), command=self.clear_logs)
        clear_btn.pack(side=tk.RIGHT, padx=4)

        save_log_btn = tk.Button(log_header_frame, text=self.tr("btn_save_log"), font=("Arial", 8), command=self.save_logs)
        save_log_btn.pack(side=tk.RIGHT, padx=4)

        self.log_area = self._make_scrolled_text(
            log_container,
            scrollbar_style="Darkbar.Vertical.TScrollbar",
            wrap=tk.WORD,
            bg="#1e1e1e",
            fg="#d4d4d4",
            font=("Consolas", 9),
        )

        self.log_area.insert("1.0", "".join(self.log_lines))
        self.log_area.see(tk.END)

        self.log_context_menu = tk.Menu(self.root, tearoff=0)
        self.log_context_menu.add_command(label=self.tr("btn_copy"), command=self.copy_logs_to_clipboard)
        self.log_area.bind("<Button-3>", self.show_log_context_menu)
        self.log_area.bind("<Double-Button-1>", self.show_log_context_menu)

        self._build_terminal_panel()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._apply_run_state_to_controls()

        self.show_param_group(self.active_param_group_id)

        if not hasattr(self, "_semantic_buttons"):
            self._semantic_buttons = ()
        self._theme_menus.append(self.log_context_menu)
        self.apply_theme()
        self._refresh_server_version_label(detect=False)

    # ================= КОНСОЛЬ (правая панель) =================
    def _build_terminal_panel(self):
        """Создаёт правую панель с настоящей консолью ОС.

        Windows: окно cmd.exe встраивается в панель через SetParent,
        поэтому работают интерактивные программы (например pi).
        Linux: встраивается xterm через ключ -into.
        """
        cwd = getattr(self, "terminal_cwd", "") or ""
        if not isinstance(cwd, str) or not os.path.isdir(cwd):
            try:
                cwd = os.getcwd()
            except OSError:
                cwd = os.path.expanduser("~")
        self.terminal_cwd = cwd

        self.terminal_frame = tk.LabelFrame(
            self.center_paned, text=" " + self.tr("terminal_title") + " ", padx=6, pady=4,
        )

        header = tk.Frame(self.terminal_frame)
        header.pack(fill=tk.X, pady=(0, 4))
        self.terminal_status_label = tk.Label(header, text="", font=("Arial", 8), anchor=tk.W)
        self.terminal_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(header, text=self.tr("terminal_focus"), font=("Arial", 8),
                  command=self._terminal_focus_embedded).pack(side=tk.RIGHT, padx=2)
        tk.Button(header, text=self.tr("terminal_new"), font=("Arial", 8),
                  command=self._terminal_respawn).pack(side=tk.RIGHT, padx=2)
        tk.Button(header, text=self.tr("terminal_close"), font=("Arial", 8),
                  command=self.hide_terminal).pack(side=tk.RIGHT, padx=2)

        self.terminal_host = tk.Frame(self.terminal_frame, bg="black")
        self.terminal_host.pack(fill=tk.BOTH, expand=True)
        self.terminal_host.bind("<Configure>", self._terminal_on_host_configure)
        self.terminal_host.bind("<Button-1>", self._terminal_focus_embedded)
        try:
            self._terminal_root_hwnd = int(self.root.winfo_id())
        except (tk.TclError, TypeError, ValueError):
            pass
        self._terminal_subclass_host()

        if bool(self.terminal_visible_var.get()):
            try:
                self.center_paned.add(self.terminal_frame, minsize=300, stretch="always")
            except tk.TclError:
                pass
            self.root.after(150, self._init_paned_sash)
            self.root.after(250, self._terminal_ensure)

    def toggle_terminal(self):
        """Показывает/скрывает терминал из меню Вид -> Терминал."""
        try:
            visible = bool(self.terminal_visible_var.get())
        except (tk.TclError, AttributeError):
            visible = False
        if visible:
            self.show_terminal(save=True)
        else:
            self.hide_terminal(save=True)

    def show_terminal(self, save=False):
        try:
            self.terminal_visible_var.set(True)
        except (tk.TclError, AttributeError):
            pass
        if self.terminal_frame is not None and self.center_paned is not None:
            try:
                panes = list(self.center_paned.panes())
                if str(self.terminal_frame) not in panes:
                    self.center_paned.add(self.terminal_frame, minsize=300, stretch="always")
            except tk.TclError:
                pass
            self.root.after(150, self._init_paned_sash)
            self.root.after(150, self._terminal_ensure)
        if save:
            try:
                self.save_config()
            except OSError:
                pass

    def hide_terminal(self, save=False):
        try:
            self.terminal_visible_var.set(False)
        except (tk.TclError, AttributeError):
            pass
        # Процесс консоли переживает скрытие: при повторном показе
        # встроенное окно используется повторно, сессия не теряется.
        self._terminal_cancel_watchdog()
        self._terminal_cancel_resize()
        if self.terminal_frame is not None and self.center_paned is not None:
            try:
                self.center_paned.forget(self.terminal_frame)
            except tk.TclError:
                pass
        if save:
            try:
                self.save_config()
            except OSError:
                pass

    def _terminal_set_status(self, text):
        try:
            label = getattr(self, "terminal_status_label", None)
            if label is not None and label.winfo_exists():
                label.config(text=text)
        except tk.TclError:
            pass

    def _terminal_is_alive(self):
        """Проверяет, что процесс консоли жив и окно встроено."""
        proc = getattr(self, "terminal_proc", None)
        if proc is None:
            return False
        try:
            if proc.poll() is not None:
                return False
        except Exception:
            return False
        if sys.platform == "win32":
            hwnd = getattr(self, "terminal_hwnd", None)
            if not hwnd:
                return False
            try:
                return bool(_win32_api()["user32"].IsWindow(hwnd))
            except Exception:
                return False
        return True

    def _terminal_ensure(self):
        """Гарантирует запущенную встроенную консоль (запускает при нужды)."""
        if self._terminal_is_alive():
            self._terminal_resize_embedded()
            self._terminal_focus_embedded()
            self._terminal_start_watchdog()
            return
        if getattr(self, "_terminal_spawn_failures", 0) >= 3:
            return
        self._terminal_set_status(self.tr("terminal_starting"))
        try:
            host_hwnd = int(self.terminal_host.winfo_id())
        except (tk.TclError, TypeError, ValueError, AttributeError):
            return
        gen = getattr(self, "terminal_gen", 0)
        cwd = getattr(self, "terminal_cwd", "") or ""
        if not isinstance(cwd, str) or not os.path.isdir(cwd):
            cwd = os.path.expanduser("~")
        threading.Thread(
            target=self._terminal_spawn_thread,
            args=(gen, host_hwnd, cwd),
            daemon=True,
        ).start()

    def _terminal_spawn_thread(self, gen, host_hwnd, cwd):
        """Запускает консоль и ищет её окно (фон, без обращений к Tk)."""
        try:
            if sys.platform == "win32":
                # Явно запускаем через conhost.exe: тогда окно — классическая
                # ConsoleWindowClass, а не вкладка Windows Terminal (поведение
                # WT зависит от настроек системы и вкладку встроить нельзя).
                system_root = os.environ.get("SystemRoot", r"C:\Windows")
                conhost = os.path.join(system_root, "System32", "conhost.exe")
                if not os.path.exists(conhost):
                    conhost = "conhost.exe"
                proc = subprocess.Popen(
                    [conhost, "cmd.exe"],
                    cwd=cwd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                if shutil.which("xterm") is None:
                    raise FileNotFoundError("xterm")
                proc = subprocess.Popen(
                    ["xterm", "-into", str(host_hwnd)],
                    cwd=cwd,
                )
        except Exception as exc:
            self.root.after(0, self._terminal_spawn_failed, gen, str(exc))
            return
        hwnd = None
        if sys.platform == "win32":
            hwnd = _win32_find_console_window(proc.pid, proc=proc, timeout=6.0)
        self.root.after(0, lambda: self._terminal_finish_embed(gen, proc, hwnd))

    def _terminal_spawn_failed(self, gen, error):
        if gen != getattr(self, "terminal_gen", 0):
            return
        self._terminal_spawn_failures = getattr(self, "_terminal_spawn_failures", 0) + 1
        self._terminal_set_status(self.tr("terminal_embed_error", error=error))

    def _terminal_finish_embed(self, gen, proc, hwnd):
        """Встраивает найденное окно консоли в панель (поток UI)."""
        if gen != getattr(self, "terminal_gen", 0):
            self._terminal_kill_proc(proc)
            return
        try:
            dead = proc.poll() is not None
        except Exception:
            dead = True
        if dead:
            self._terminal_spawn_failed(gen, proc.args if hasattr(proc, "args") else "")
            return
        if sys.platform == "win32":
            if not hwnd:
                self._terminal_spawn_failed(gen, "console window")
                self._terminal_kill_proc(proc)
                return
            try:
                host_hwnd = int(self.terminal_host.winfo_id())
            except (tk.TclError, TypeError, ValueError, AttributeError):
                self._terminal_spawn_failed(gen, "host window")
                self._terminal_kill_proc(proc)
                return
            try:
                _win32_embed_console_window(host_hwnd, hwnd)
            except Exception as exc:
                self._terminal_spawn_failed(gen, str(exc))
                self._terminal_kill_proc(proc)
                return
            self.terminal_hwnd = hwnd
            self._terminal_set_status("cmd.exe")
        else:
            self.terminal_hwnd = None
            self._terminal_set_status("shell")
        self.terminal_proc = proc
        self._terminal_spawn_failures = 0
        self._terminal_focus_embedded()
        self._terminal_start_watchdog()

    def _terminal_on_host_configure(self, _event=None):
        job = getattr(self, "_terminal_resize_job", None)
        if job is not None:
            try:
                self.root.after_cancel(job)
            except (tk.TclError, ValueError):
                pass
        try:
            self._terminal_resize_job = self.root.after(150, self._terminal_resize_embedded)
        except tk.TclError:
            pass

    def _terminal_cancel_resize(self):
        job = getattr(self, "_terminal_resize_job", None)
        if job is not None:
            try:
                self.root.after_cancel(job)
            except (tk.TclError, ValueError):
                pass
            self._terminal_resize_job = None

    def _terminal_resize_embedded(self):
        self._terminal_resize_job = None
        if sys.platform != "win32":
            return
        hwnd = getattr(self, "terminal_hwnd", None)
        host = getattr(self, "terminal_host", None)
        if not hwnd or host is None:
            return
        try:
            if not host.winfo_exists():
                return
            host_hwnd = int(host.winfo_id())
        except (tk.TclError, TypeError, ValueError, AttributeError):
            return
        try:
            _win32_fit_console_to_host(host_hwnd, hwnd)
        except Exception:
            pass

    def _terminal_focus_embedded(self, _event=None):
        """Возвращает клавиатурный фокус во встроенную консоль.

        SetFocus в окно чужого процесса срабатывает только если наше
        приложение в foreground, иначе временно объединяем очереди ввода
        (AttachThreadInput). Без Tk-вызовов — безопасно из WndProc.
        """
        if sys.platform != "win32":
            return None
        hwnd = getattr(self, "terminal_hwnd", None)
        if not hwnd:
            return None
        try:
            api = _win32_api()
            user32 = api["user32"]
            try:
                if not user32.IsWindow(hwnd):
                    return None
            except Exception:
                pass
            target = _hwnd_to_int(hwnd)
            if not target:
                return None
            root_hwnd = getattr(self, "_terminal_root_hwnd", None)
            try:
                if root_hwnd and _hwnd_to_int(user32.GetForegroundWindow()) != int(root_hwnd):
                    user32.SetForegroundWindow(root_hwnd)
            except Exception:
                pass
            try:
                user32.SetFocus(hwnd)
            except Exception:
                pass
            try:
                focused = _hwnd_to_int(user32.GetFocus())
            except Exception:
                focused = 0
            if focused != target:
                try:
                    our_tid = int(api["kernel32"].GetCurrentThreadId())
                    con_tid = int(user32.GetWindowThreadProcessId(hwnd, None))
                except Exception:
                    con_tid = 0
                if con_tid and con_tid != our_tid:
                    try:
                        if user32.AttachThreadInput(our_tid, con_tid, True):
                            try:
                                if root_hwnd:
                                    user32.SetForegroundWindow(root_hwnd)
                                user32.SetFocus(hwnd)
                            finally:
                                user32.AttachThreadInput(our_tid, con_tid, False)
                    except Exception:
                        pass
        except Exception:
            pass
        return None

    def _terminal_subclass_host(self):
        """Перехватывает сообщения хоста, чтобы клики по встроенной консоли
        (они не доходят до Tk-биндингов) возвращали ей фокус."""
        if sys.platform != "win32":
            return
        if getattr(self, "_terminal_host_old_wndproc", None) is not None:
            return
        host = getattr(self, "terminal_host", None)
        if host is None:
            return
        try:
            if not host.winfo_exists():
                return
            host_hwnd = int(host.winfo_id())
        except (tk.TclError, TypeError, ValueError, AttributeError):
            return
        try:
            api = _win32_api()
            cb = _win32_wndproc_type()(self._terminal_host_wndproc)
            old = api["set_style"](host_hwnd, _WIN32_GWLP_WNDPROC, ctypes.cast(cb, ctypes.c_void_p).value)
            if not old:
                return
            self._terminal_host_wndproc_cb = cb  # держим ссылку, иначе упадём
            self._terminal_host_old_wndproc = _hwnd_to_int(old)
        except Exception:
            self._terminal_host_wndproc_cb = None
            self._terminal_host_old_wndproc = None

    def _terminal_unsubclass_host(self):
        if sys.platform != "win32":
            return
        old = getattr(self, "_terminal_host_old_wndproc", None)
        host = getattr(self, "terminal_host", None)
        self._terminal_host_old_wndproc = None
        self._terminal_host_wndproc_cb = None
        if not old or host is None:
            return
        try:
            if not host.winfo_exists():
                return
            host_hwnd = int(host.winfo_id())
        except (tk.TclError, TypeError, ValueError, AttributeError):
            return
        try:
            _win32_api()["set_style"](host_hwnd, _WIN32_GWLP_WNDPROC, old)
        except Exception:
            pass

    def _terminal_host_wndproc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == _WIN32_WM_PARENTNOTIFY:
                if int(wparam) & 0xFFFF in (
                    _WIN32_WM_LBUTTONDOWN,
                    _WIN32_WM_RBUTTONDOWN,
                    _WIN32_WM_MBUTTONDOWN,
                ):
                    self._terminal_focus_embedded()
            elif msg == _WIN32_WM_SETFOCUS:
                self._terminal_focus_embedded()
        except Exception:
            pass
        try:
            old = getattr(self, "_terminal_host_old_wndproc", None)
            if old:
                return _win32_api()["user32"].CallWindowProcW(
                    ctypes.c_void_p(old), hwnd, msg, wparam, lparam,
                )
        except Exception:
            pass
        return 0

    def _terminal_kill_proc(self, proc):
        """Завершает процесс консоли вместе с программами, запущенными в ней."""
        if proc is None:
            return
        if sys.platform == "win32":
            try:
                _win32_kill_tree(proc.pid)
            except Exception:
                pass
        try:
            proc.terminate()
        except OSError:
            pass

    def _terminal_respawn(self):
        """Кнопка «Новая»: убивает текущую консоль и запускает свежую."""
        self.terminal_gen = getattr(self, "terminal_gen", 0) + 1
        self._terminal_spawn_failures = 0
        proc = getattr(self, "terminal_proc", None)
        self.terminal_proc = None
        self.terminal_hwnd = None
        self._terminal_kill_proc(proc)
        self._terminal_ensure()

    def _terminal_shutdown(self):
        """Гасит консоль перед уничтожением виджетов (rebuild/выход).

        Окно консоли — дочернее для HWND хоста, поэтому умрёт вместе с ним;
        процесс завершаем явно, чтобы не оставлять сироту.
        """
        self.terminal_gen = getattr(self, "terminal_gen", 0) + 1
        self._terminal_cancel_watchdog()
        self._terminal_cancel_resize()
        self._terminal_unsubclass_host()
        proc = getattr(self, "terminal_proc", None)
        self.terminal_proc = None
        self.terminal_hwnd = None
        self._terminal_kill_proc(proc)

    def _terminal_start_watchdog(self):
        self._terminal_cancel_watchdog()
        try:
            self._terminal_watchdog_job = self.root.after(2500, self._terminal_watchdog_tick)
        except tk.TclError:
            self._terminal_watchdog_job = None

    def _terminal_cancel_watchdog(self):
        job = getattr(self, "_terminal_watchdog_job", None)
        if job is not None:
            try:
                self.root.after_cancel(job)
            except (tk.TclError, ValueError):
                pass
            self._terminal_watchdog_job = None

    def _terminal_watchdog_tick(self):
        """Следит за консолью: если процесс умер (например, набрали exit),
        запускает свежую консоль."""
        self._terminal_watchdog_job = None
        try:
            visible = bool(self.terminal_visible_var.get())
        except (tk.TclError, AttributeError):
            visible = False
        if not visible:
            return
        if self._terminal_is_alive():
            self._terminal_start_watchdog()
            return
        if getattr(self, "_terminal_spawn_failures", 0) >= 3:
            self._terminal_set_status(self.tr("terminal_embed_error", error=""))
            return
        self._terminal_set_status(self.tr("terminal_not_running"))
        self._terminal_ensure()

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
            elif spec.get("choices"):
                choices = list(spec["choices"])
                if value not in choices:
                    choices.insert(0, str(value))
                var = tk.StringVar(value=str(value))
                combo = ttk.Combobox(
                    cell,
                    textvariable=var,
                    values=choices,
                    state="readonly",
                    width=16,
                    font=("Consolas", 9),
                )
                combo.pack(anchor=tk.W, pady=(2, 0))
                self.param_entries[param] = var
            else:
                ent = tk.Entry(cell, width=18, font=("Consolas", 9))
                ent.insert(0, str(value))
                ent.pack(anchor=tk.W, pady=(2, 0))
                self.param_entries[param] = ent

            if hint:
                tk.Label(cell, text=hint, font=("Arial", 8), fg="#777777", wraplength=210, justify=tk.LEFT).pack(
                    anchor=tk.W, pady=(2, 0),
                )

            col += 1
            if spec.get("row_break_after"):
                col = 0
                row += 1
            elif col >= PARAM_GRID_COLUMNS:
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
            self._on_exe_path_changed()

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

    def install_pi_agent(self):
        """Загрузка и установка pi-агента через официальный install.ps1.

        Установщик интерактивный, поэтому запускается в отдельном видимом
        окне PowerShell, а не в скрытом процессе.
        """
        if sys.platform != "win32":
            messagebox.showinfo(
                self.tr("menu_install_pi"),
                self.tr("msg_pi_unsupported", command=PI_AGENT_INSTALL_COMMAND),
            )
            return
        proc = getattr(self, "_pi_install_proc", None)
        try:
            already_running = proc is not None and proc.poll() is None
        except Exception:
            already_running = False
        if already_running:
            messagebox.showinfo(self.tr("menu_install_pi"), self.tr("msg_pi_install_already_running"))
            return
        if not messagebox.askyesno(
            self.tr("menu_install_pi"),
            self.tr("msg_pi_install_confirm", command=PI_AGENT_INSTALL_COMMAND),
        ):
            return
        try:
            self._pi_install_proc = subprocess.Popen(
                [
                    "powershell", "-NoExit", "-ExecutionPolicy", "Bypass",
                    "-Command", f"irm {PI_AGENT_INSTALL_URL} | iex",
                ],
                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
            )
        except Exception as exc:
            messagebox.showerror(self.tr("msg_error"), str(exc) or exc.__class__.__name__)
            return
        self.log(f"{self.tr('log_pi_install', command=PI_AGENT_INSTALL_COMMAND)}\n")

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

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
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

        self.apply_theme()
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
        self._on_exe_path_changed()
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

        self._set_devices_menu_state(tk.DISABLED)
        threading.Thread(target=self._run_list_devices, args=(exe_path,), daemon=True).start()

    def _set_devices_menu_state(self, state):
        menu = getattr(self, "file_menu", None)
        if menu is None:
            return
        try:
            menu.entryconfig(self.tr("btn_devices"), state=state)
        except tk.TclError:
            pass

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
        self._set_devices_menu_state(tk.NORMAL)

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

        text_area = self._make_scrolled_text(window, wrap=tk.WORD, font=("Consolas", 10),
                                               pack_padx=10, pack_pady=4)
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
        self.apply_theme()

    # ================= МОДЕЛИ (локальные + HuggingFace) =================
    HF_API_BASE = "https://huggingface.co"
    HF_USER_AGENT = "LLM-Server-Controller/0.1"
    MODELS_SCAN_LIMIT = 5000

    @staticmethod
    def _format_size(num_bytes):
        try:
            size = float(num_bytes)
        except (TypeError, ValueError):
            return "?"
        if size < 0:
            return "?"
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024.0 or unit == "TB":
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _models_alive(self):
        window = getattr(self, "models_window", None)
        try:
            return window is not None and window.winfo_exists()
        except tk.TclError:
            return False

    def open_models_browser(self):
        """Отдельное окно: локальные .gguf модели + поиск и скачивание
        с HuggingFace. Открывается из меню Файл и кнопкой тулбара."""
        try:
            if self._models_alive():
                self.models_window.lift()
                try:
                    self.models_window.focus_set()
                except tk.TclError:
                    pass
                return
        except tk.TclError:
            pass

        window = tk.Toplevel(self.root)
        window.title(self.tr("title_models"))
        window.geometry("980x700")
        window.transient(self.root)
        self.models_window = window
        self.models_local_files = []
        self.hf_models = []
        self.hf_files = []
        self.hf_current_model = ""
        self.hf_download_flag = None

        top = tk.Frame(window)
        top.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(top, text=self.tr("models_dir_label"), font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        self.models_dir_entry = tk.Entry(top, font=("Consolas", 9))
        self.models_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 4))
        self.models_dir_entry.insert(0, getattr(self, "models_dir", "") or "")
        tk.Button(top, text=self.tr("btn_browse"), font=("Arial", 8),
                  command=self._models_browse_dir).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text=self.tr("btn_refresh"), font=("Arial", 8),
                  command=self._refresh_local_models).pack(side=tk.LEFT, padx=2)

        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        self.models_notebook = notebook

        local_tab = tk.Frame(notebook)
        notebook.add(local_tab, text=self.tr("tab_local"))
        self._build_models_local_tab(local_tab)

        hf_tab = tk.Frame(notebook)
        notebook.add(hf_tab, text=self.tr("tab_hf"))
        self._build_models_hf_tab(hf_tab)

        bottom = tk.Frame(window)
        bottom.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Button(bottom, text=self.tr("btn_close"), command=self._close_models_browser).pack(side=tk.RIGHT)

        window.protocol("WM_DELETE_WINDOW", self._close_models_browser)
        self._refresh_local_models()
        self.apply_theme()

    def _close_models_browser(self):
        flag = getattr(self, "hf_download_flag", None)
        if isinstance(flag, dict):
            flag["cancel"] = True
        window = getattr(self, "models_window", None)
        self.models_window = None
        self.hf_download_flag = None
        try:
            if window is not None and window.winfo_exists():
                window.destroy()
        except tk.TclError:
            pass

    # ---------- Вкладка «Локальные» ----------
    def _build_models_local_tab(self, parent):
        cols = ("name", "size")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=18)
        tree.heading("name", text=self.tr("col_name"))
        tree.heading("size", text=self.tr("col_size"))
        tree.column("name", width=520, stretch=True)
        tree.column("size", width=120, stretch=False, anchor=tk.E)
        scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree.bind("<Double-Button-1>", lambda _e: self._models_use_selected())
        self.local_tree = tree

        btnrow = tk.Frame(parent)
        btnrow.pack(fill=tk.X, pady=(6, 2))
        tk.Button(btnrow, text=self.tr("btn_use_model"), font=("Arial", 9, "bold"),
                  command=self._models_use_selected).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(btnrow, text=self.tr("btn_reveal"), font=("Arial", 8),
                  command=self._models_reveal).pack(side=tk.LEFT, padx=4)
        tk.Button(btnrow, text=self.tr("btn_refresh"), font=("Arial", 8),
                  command=self._refresh_local_models).pack(side=tk.LEFT, padx=4)
        self.local_status = tk.Label(btnrow, text="", font=("Arial", 8), anchor=tk.W)
        self.local_status.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)

    def _models_browse_dir(self):
        if not self._models_alive():
            return
        initial = self.models_dir_entry.get().strip() or os.getcwd()
        directory = filedialog.askdirectory(
            title=self.tr("models_dir_label"),
            initialdir=initial if os.path.isdir(initial) else os.getcwd(),
            mustexist=False,
        )
        if not directory:
            return
        directory = os.path.normpath(directory)
        self.models_dir_entry.delete(0, tk.END)
        self.models_dir_entry.insert(0, directory)
        self.models_dir = directory
        self.save_config()
        self._refresh_local_models()

    def _refresh_local_models(self):
        if not self._models_alive():
            return
        directory = self.models_dir_entry.get().strip()
        tree = getattr(self, "local_tree", None)
        try:
            for item in tree.get_children():
                tree.delete(item)
        except (tk.TclError, AttributeError):
            return
        self.models_local_files = []
        if not directory or not os.path.isdir(directory):
            self.local_status.config(text=self.tr("models_no_dir"))
            return
        found = []
        count = 0
        try:
            for root_dir, _dirs, files in os.walk(directory):
                for name in files:
                    if not name.lower().endswith(".gguf"):
                        continue
                    path = os.path.join(root_dir, name)
                    try:
                        size = os.path.getsize(path)
                    except OSError:
                        continue
                    found.append((path, size))
                    count += 1
                    if count >= self.MODELS_SCAN_LIMIT:
                        break
                if count >= self.MODELS_SCAN_LIMIT:
                    break
        except OSError:
            pass
        # Текущая модель — всегда первой, даже если вне папки.
        current = ""
        try:
            current = os.path.normpath(self.model_entry.get().strip())
        except (tk.TclError, AttributeError):
            current = ""
        if current and current.lower().endswith(".gguf") and os.path.isfile(current):
            if all(os.path.normcase(p) != os.path.normcase(current) for p, _s in found):
                try:
                    found.insert(0, (current, os.path.getsize(current)))
                except OSError:
                    pass
        found.sort(key=lambda item: os.path.basename(item[0]).lower())
        self.models_local_files = found
        for path, size in found:
            try:
                tree.insert("", tk.END, values=(os.path.basename(path), self._format_size(size)), tags=(path,))
            except tk.TclError:
                break
        if found:
            self.local_status.config(text=self.tr("models_found", n=len(found)))
        else:
            self.local_status.config(text=self.tr("models_empty"))

    def _models_selected_path(self):
        tree = getattr(self, "local_tree", None)
        try:
            selection = tree.selection()
        except (tk.TclError, AttributeError):
            return ""
        if not selection:
            return ""
        try:
            tags = tree.item(selection[0], "tags")
        except tk.TclError:
            return ""
        return str(tags[0]) if tags else ""

    def _models_use_selected(self):
        path = self._models_selected_path()
        if not path:
            messagebox.showwarning(self.tr("msg_attention"), self.tr("msg_no_file_selected"))
            return
        self._use_model_path(path)

    def _use_model_path(self, path):
        path = os.path.normpath(path)
        try:
            self.model_entry.delete(0, tk.END)
            self.model_entry.insert(0, path)
        except (tk.TclError, AttributeError):
            return
        try:
            self.save_config()
        except OSError as exc:
            messagebox.showerror(self.tr("msg_save_error"), str(exc))
            return
        messagebox.showinfo(self.tr("msg_success"), self.tr("msg_model_set", path=path))

    def _models_reveal(self):
        path = self._models_selected_path()
        directory = os.path.dirname(path) if path else self.models_dir_entry.get().strip()
        if not directory or not os.path.isdir(directory):
            messagebox.showwarning(self.tr("msg_attention"), self.tr("models_no_dir"))
            return
        try:
            if sys.platform == "win32":
                os.startfile(directory)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", directory])
            else:
                subprocess.Popen(["xdg-open", directory])
        except OSError as exc:
            messagebox.showerror(self.tr("msg_error"), str(exc))

    # ---------- Вкладка «HuggingFace» ----------
    def _build_models_hf_tab(self, parent):
        search_row = tk.Frame(parent)
        search_row.pack(fill=tk.X, pady=(2, 4))
        tk.Label(search_row, text=self.tr("hf_search_label"), font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        self.hf_search_entry = tk.Entry(search_row, font=("Consolas", 10))
        self.hf_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 4))
        self.hf_search_entry.bind("<Return>", lambda _e: self._hf_do_search())
        self.hf_search_btn = tk.Button(search_row, text=self.tr("btn_search"),
                                       font=("Arial", 9, "bold"), command=self._hf_do_search)
        self.hf_search_btn.pack(side=tk.LEFT)

        filter_row = tk.Frame(parent)
        filter_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(filter_row, text=self.tr("hf_sort_label"), font=("Arial", 8)).pack(side=tk.LEFT)
        self._hf_sort_map = {
            self.tr("hf_sort_likes"): "likes",
            self.tr("hf_sort_downloads"): "downloads",
            self.tr("hf_sort_updated"): "lastModified",
        }
        self.hf_sort_combo = ttk.Combobox(
            filter_row, values=list(self._hf_sort_map.keys()),
            state="readonly", width=18, font=("Arial", 9),
        )
        self.hf_sort_combo.pack(side=tk.LEFT, padx=(4, 12))
        self.hf_sort_combo.set(self.tr("hf_sort_likes"))
        tk.Label(filter_row, text=self.tr("hf_limit_label"), font=("Arial", 8)).pack(side=tk.LEFT)
        self.hf_limit_combo = ttk.Combobox(
            filter_row, values=["10", "25", "50", "100"],
            state="readonly", width=6, font=("Arial", 9),
        )
        self.hf_limit_combo.pack(side=tk.LEFT, padx=(4, 0))
        self.hf_limit_combo.set("25")

        tk.Label(parent, text=self.tr("hf_models_label"), font=("Arial", 9, "bold"), anchor=tk.W).pack(fill=tk.X)
        models_frame = tk.Frame(parent)
        models_frame.pack(fill=tk.BOTH, expand=True)
        cols = ("model", "likes", "downloads", "updated")
        self.hf_models_tree = ttk.Treeview(models_frame, columns=cols, show="headings", height=8)
        self.hf_models_tree.heading("model", text=self.tr("col_model"))
        self.hf_models_tree.heading("likes", text=self.tr("col_likes"))
        self.hf_models_tree.heading("downloads", text=self.tr("col_downloads"))
        self.hf_models_tree.heading("updated", text=self.tr("col_updated"))
        self.hf_models_tree.column("model", width=420, stretch=True)
        self.hf_models_tree.column("likes", width=90, stretch=False, anchor=tk.E)
        self.hf_models_tree.column("downloads", width=110, stretch=False, anchor=tk.E)
        self.hf_models_tree.column("updated", width=120, stretch=False)
        mscroll = ttk.Scrollbar(models_frame, orient=tk.VERTICAL, command=self.hf_models_tree.yview)
        self.hf_models_tree.configure(yscrollcommand=mscroll.set)
        mscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.hf_models_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.hf_models_tree.bind("<<TreeviewSelect>>", self._hf_on_model_selected)

        tk.Label(parent, text=self.tr("hf_files_label"), font=("Arial", 9, "bold"), anchor=tk.W).pack(fill=tk.X, pady=(4, 0))
        files_frame = tk.Frame(parent)
        files_frame.pack(fill=tk.BOTH, expand=True)
        fcols = ("file", "size")
        self.hf_files_tree = ttk.Treeview(files_frame, columns=fcols, show="headings", height=7)
        self.hf_files_tree.heading("file", text=self.tr("col_file"))
        self.hf_files_tree.heading("size", text=self.tr("col_size"))
        self.hf_files_tree.column("file", width=560, stretch=True)
        self.hf_files_tree.column("size", width=120, stretch=False, anchor=tk.E)
        fscroll = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.hf_files_tree.yview)
        self.hf_files_tree.configure(yscrollcommand=fscroll.set)
        fscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.hf_files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.hf_files_tree.bind("<Double-Button-1>", lambda _e: self._hf_download_selected())

        dl_row = tk.Frame(parent)
        dl_row.pack(fill=tk.X, pady=(6, 2))
        self.hf_download_btn = tk.Button(dl_row, text=self.tr("btn_download"),
                                         font=("Arial", 9, "bold"), command=self._hf_download_selected)
        self.hf_download_btn._btn_kind = "primary"
        self.hf_download_btn.pack(side=tk.LEFT, padx=(0, 4))
        self.hf_cancel_btn = tk.Button(dl_row, text=self.tr("btn_cancel"),
                                       font=("Arial", 8), command=self._hf_cancel_download,
                                       state=tk.DISABLED)
        self.hf_cancel_btn.pack(side=tk.LEFT, padx=4)
        self.hf_progress = ttk.Progressbar(dl_row, mode="determinate", maximum=100, value=0)
        self.hf_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4))
        self.hf_progress_label = tk.Label(dl_row, text="", font=("Consolas", 8), width=26, anchor=tk.E)
        self.hf_progress_label.pack(side=tk.LEFT)
        self.hf_status = tk.Label(parent, text="", font=("Arial", 8), anchor=tk.W)
        self.hf_status.pack(fill=tk.X, pady=(2, 0))

    def _hf_api_json(self, path, timeout=30):
        request = urllib.request.Request(
            self.HF_API_BASE + path,
            headers={"User-Agent": self.HF_USER_AGENT},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)

    def _hf_head_size(self, url, timeout=15):
        try:
            request = urllib.request.Request(
                url, method="HEAD",
                headers={"User-Agent": self.HF_USER_AGENT},
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                length = response.headers.get("Content-Length")
                if length and length.isdigit():
                    return int(length)
        except Exception:
            pass
        return None

    def _hf_status(self, text):
        if not self._models_alive():
            return
        try:
            self.hf_status.config(text=text)
        except (tk.TclError, AttributeError):
            pass

    def _hf_do_search(self):
        if not self._models_alive():
            return
        query = self.hf_search_entry.get().strip()
        if not query:
            self._hf_status(self.tr("hf_enter_query"))
            return
        try:
            limit = int(self.hf_limit_combo.get())
        except (tk.TclError, ValueError, AttributeError):
            limit = 25
        sort_key = self._hf_sort_map.get(self.hf_sort_combo.get(), "likes")
        self.hf_search_btn.config(state=tk.DISABLED)
        self._hf_status(self.tr("hf_searching"))
        threading.Thread(
            target=self._hf_search_worker,
            args=(query, sort_key, limit),
            daemon=True,
        ).start()

    def _hf_search_worker(self, query, sort_key, limit):
        try:
            params = urllib.parse.urlencode({
                "search": query,
                "filter": "gguf",
                "sort": sort_key,
                "direction": "-1",
                "limit": max(1, min(int(limit), 100)),
            })
            data = self._hf_api_json("/api/models?" + params, timeout=30)
            if not isinstance(data, list):
                data = []
            self.root.after(0, lambda: self._hf_show_models(data))
        except Exception as exc:
            message = str(exc) or exc.__class__.__name__
            self.root.after(0, lambda: self._hf_search_failed(message))

    def _hf_search_failed(self, message):
        if not self._models_alive():
            return
        try:
            self.hf_search_btn.config(state=tk.NORMAL)
        except (tk.TclError, AttributeError):
            pass
        self._hf_status(self.tr("hf_error", error=message))

    def _hf_show_models(self, data):
        if not self._models_alive():
            return
        try:
            self.hf_search_btn.config(state=tk.NORMAL)
            for item in self.hf_models_tree.get_children():
                self.hf_models_tree.delete(item)
            for item in self.hf_files_tree.get_children():
                self.hf_files_tree.delete(item)
        except (tk.TclError, AttributeError):
            return
        self.hf_models = data if isinstance(data, list) else []
        self.hf_files = []
        self.hf_current_model = ""
        if not self.hf_models:
            self._hf_status(self.tr("hf_no_results"))
            return
        for index, model in enumerate(self.hf_models):
            model_id = str(model.get("id", ""))
            likes = model.get("likes", 0) or 0
            downloads = model.get("downloads", 0) or 0
            updated = str(model.get("lastModified") or "")[:10]
            try:
                self.hf_models_tree.insert(
                    "", tk.END, iid=str(index),
                    values=(model_id, f"{likes:,}".replace(",", " "), f"{downloads:,}".replace(",", " "), updated),
                )
            except tk.TclError:
                break
        self._hf_status(self.tr("hf_found", n=len(self.hf_models)))

    def _hf_on_model_selected(self, _event=None):
        if not self._models_alive():
            return
        try:
            selection = self.hf_models_tree.selection()
        except (tk.TclError, AttributeError):
            return
        if not selection:
            return
        try:
            index = int(selection[0])
            model = self.hf_models[index]
        except (ValueError, IndexError, TypeError):
            return
        model_id = str(model.get("id", ""))
        if not model_id:
            return
        self.hf_current_model = model_id
        try:
            for item in self.hf_files_tree.get_children():
                self.hf_files_tree.delete(item)
        except (tk.TclError, AttributeError):
            return
        self.hf_files = []
        self._hf_status(self.tr("hf_loading_files"))
        threading.Thread(target=self._hf_files_worker, args=(model_id,), daemon=True).start()

    def _hf_files_worker(self, model_id):
        try:
            data = self._hf_api_json("/api/models/" + model_id, timeout=30)
            siblings = data.get("siblings", []) if isinstance(data, dict) else []
            gguf_files = [
                str(item.get("rfilename", ""))
                for item in siblings
                if isinstance(item, dict) and str(item.get("rfilename", "")).lower().endswith(".gguf")
            ]
            self.root.after(0, lambda: self._hf_show_files(model_id, gguf_files))
        except Exception as exc:
            message = str(exc) or exc.__class__.__name__
            self.root.after(0, lambda mid=model_id, msg=message: self._hf_files_failed(mid, msg))

    def _hf_files_failed(self, model_id, message):
        if not self._models_alive() or self.hf_current_model != model_id:
            return
        self._hf_status(self.tr("hf_error", error=message))

    def _hf_show_files(self, model_id, gguf_files):
        if not self._models_alive() or self.hf_current_model != model_id:
            return
        try:
            for item in self.hf_files_tree.get_children():
                self.hf_files_tree.delete(item)
        except (tk.TclError, AttributeError):
            return
        if not gguf_files:
            self._hf_status(self.tr("hf_no_gguf"))
            return
        self.hf_files = [(name, None) for name in gguf_files]
        for index, name in enumerate(gguf_files):
            try:
                self.hf_files_tree.insert("", tk.END, iid=str(index), values=(name, "..."))
            except tk.TclError:
                break
        self._hf_status(self.tr("hf_files_ready", n=len(gguf_files)))
        threading.Thread(target=self._hf_sizes_worker, args=(model_id, list(gguf_files)), daemon=True).start()

    def _hf_sizes_worker(self, model_id, gguf_files):
        for index, name in enumerate(gguf_files):
            if not self._models_alive() or self.hf_current_model != model_id:
                return
            url = self._hf_file_url(model_id, name)
            size = self._hf_head_size(url)
            self.root.after(0, lambda i=index, s=size, mid=model_id: self._hf_update_file_size(i, s, mid))

    def _hf_update_file_size(self, index, size, model_id):
        if not self._models_alive() or self.hf_current_model != model_id:
            return
        try:
            name = self.hf_files[index][0]
        except (IndexError, TypeError, AttributeError):
            return
        self.hf_files[index] = (name, size)
        try:
            if self.hf_files_tree.exists(str(index)):
                self.hf_files_tree.item(str(index), values=(name, self._format_size(size)))
        except tk.TclError:
            pass

    def _hf_file_url(self, model_id, rfilename):
        return f"{self.HF_API_BASE}/{model_id}/resolve/main/{urllib.parse.quote(rfilename)}"

    def _hf_selected_file(self):
        try:
            selection = self.hf_files_tree.selection()
        except (tk.TclError, AttributeError):
            return None
        if not selection:
            return None
        try:
            return self.hf_files[int(selection[0])]
        except (ValueError, IndexError, TypeError):
            return None

    def _hf_download_selected(self):
        if not self._models_alive():
            return
        if getattr(self, "hf_download_flag", None) is not None:
            return
        if not self.hf_current_model:
            self._hf_status(self.tr("hf_no_results"))
            return
        picked = self._hf_selected_file()
        if not picked:
            messagebox.showwarning(self.tr("msg_attention"), self.tr("msg_no_file_selected"), parent=self.models_window)
            return
        rfilename = picked[0]
        directory = (getattr(self, "models_dir", "") or "").strip()
        if not directory or not os.path.isdir(directory):
            directory = filedialog.askdirectory(
                title=self.tr("dl_choose_dir"),
                initialdir=os.getcwd(),
                mustexist=False,
                parent=self.models_window,
            )
            if not directory:
                return
            directory = os.path.normpath(directory)
            self.models_dir = directory
            try:
                self.models_dir_entry.delete(0, tk.END)
                self.models_dir_entry.insert(0, directory)
            except (tk.TclError, AttributeError):
                pass
            self.save_config()
        dest = os.path.join(directory, os.path.basename(rfilename))
        if os.path.exists(dest):
            if not messagebox.askyesno(self.tr("msg_confirm"), self.tr("dl_exists", path=dest), parent=self.models_window):
                return
        url = self._hf_file_url(self.hf_current_model, rfilename)
        try:
            self.hf_download_btn.config(state=tk.DISABLED)
            self.hf_cancel_btn.config(state=tk.NORMAL)
            self.hf_progress.stop()
            self.hf_progress.config(mode="determinate", value=0)
            self.hf_progress_label.config(text="")
        except (tk.TclError, AttributeError):
            return
        flag = {"cancel": False}
        self.hf_download_flag = flag
        threading.Thread(
            target=self._hf_download_worker,
            args=(url, dest, picked[1], flag),
            daemon=True,
        ).start()

    def _hf_cancel_download(self):
        flag = getattr(self, "hf_download_flag", None)
        if isinstance(flag, dict):
            flag["cancel"] = True

    def _hf_progress(self, done, total):
        if not self._models_alive():
            return
        try:
            if total and total > 0:
                self.hf_progress.config(mode="determinate", maximum=100)
                self.hf_progress["value"] = min(100.0, done * 100.0 / total)
                self.hf_progress_label.config(
                    text=f"{self._format_size(done)} / {self._format_size(total)}")
            else:
                self.hf_progress.config(mode="indeterminate")
                self.hf_progress.start(20)
                self.hf_progress_label.config(text=self._format_size(done))
        except (tk.TclError, AttributeError):
            pass

    def _hf_download_worker(self, url, dest, total, flag):
        part = dest + ".part"
        try:
            request = urllib.request.Request(url, headers={"User-Agent": self.HF_USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response, open(part, "wb") as target:
                header_total = response.headers.get("Content-Length")
                if header_total and header_total.isdigit():
                    total = int(header_total)
                done = 0
                while True:
                    if flag.get("cancel"):
                        raise _HfDownloadCancelled()
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    target.write(chunk)
                    done += len(chunk)
                    self.root.after(0, lambda d=done, t=total: self._hf_progress(d, t))
            if flag.get("cancel"):
                raise _HfDownloadCancelled()
            os.replace(part, dest)
            self.root.after(0, lambda: self._hf_download_finished(dest, None))
        except _HfDownloadCancelled:
            try:
                if os.path.exists(part):
                    os.remove(part)
            except OSError:
                pass
            self.root.after(0, lambda: self._hf_download_finished(dest, "cancelled"))
        except Exception as exc:
            try:
                if os.path.exists(part):
                    os.remove(part)
            except OSError:
                pass
            message = str(exc) or exc.__class__.__name__
            self.root.after(0, lambda: self._hf_download_finished(dest, message))

    def _hf_download_finished(self, dest, error):
        self.hf_download_flag = None
        if not self._models_alive():
            return
        try:
            self.hf_download_btn.config(state=tk.NORMAL)
            self.hf_cancel_btn.config(state=tk.DISABLED)
            self.hf_progress.stop()
        except (tk.TclError, AttributeError):
            return
        if error is None:
            try:
                self.hf_progress["value"] = 100
                self.hf_progress_label.config(text=self.tr("dl_done", path=""))
            except (tk.TclError, AttributeError):
                pass
            self._refresh_local_models()
            messagebox.showinfo(self.tr("msg_success"), self.tr("dl_done", path=dest), parent=self.models_window)
            if messagebox.askyesno(self.tr("msg_confirm"), self.tr("dl_use_after"), parent=self.models_window):
                self._use_model_path(dest)
        elif error == "cancelled":
            try:
                self.hf_progress_label.config(text="")
            except (tk.TclError, AttributeError):
                pass
            self._hf_status(self.tr("dl_cancelled"))
        else:
            self._hf_status(self.tr("dl_error", error=error))

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
        pal = self._current_palette()
        color = pal["warning"] if self.loading_blink_visible else pal["muted_fg"]
        self.status_label.config(text=self.tr("status_loading"), fg=color)
        self.loading_blink_job = self.root.after(500, self.animate_loading_status)

    def set_loading_error_state(self):
        self.stop_loading_blink()
        self.status_label.config(text=self.tr("status_load_error"), fg=self._status_fg("err"))
        self._update_badge_status()

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
        self._on_exe_path_changed()
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
        self._on_exe_path_changed(detect=False)
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

        text_area = self._make_scrolled_text(help_window, wrap=tk.WORD, font=("Segoe UI", 10),
                                               pack_padx=10, pack_pady=10)
        text_area.insert("1.0", help_text)
        text_area.config(state=tk.DISABLED)

        close_btn = tk.Button(help_window, text=self.tr("btn_close"), command=help_window.destroy)
        close_btn.pack(pady=(0, 10))
        self.apply_theme()

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

        donate_btn = tk.Button(
            about_window,
            text="Donate",
            command=lambda: webbrowser.open("https://pay.heleket.com/wallet/61486d55-7249-4cab-8596-fbd38b3e9047"),
        )
        donate_btn.pack(pady=(10, 10))

        default_fg = donate_btn.cget("fg") or "black"
        blink_visible = True
        blink_job = {"id": None}

        def _on_about_close():
            if blink_job["id"] is not None:
                try:
                    about_window.after_cancel(blink_job["id"])
                except tk.TclError:
                    pass
                blink_job["id"] = None
            about_window.destroy()

        def _toggle_donate_blink():
            nonlocal blink_visible
            blink_visible = not blink_visible
            if donate_btn.winfo_exists():
                donate_btn.config(fg="#ff0000" if blink_visible else default_fg)
            blink_job["id"] = about_window.after(700, _toggle_donate_blink)

        close_btn = tk.Button(about_window, text="OK", command=_on_about_close)
        close_btn.pack(pady=(0, 10))
        self.apply_theme()

        about_window.protocol("WM_DELETE_WINDOW", _on_about_close)
        blink_job["id"] = about_window.after(700, _toggle_donate_blink)

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
        # Храним лог построчно с жёстким лимитом, иначе за долгую работу
        # log_lines и виджет съедят всю память. Чистим пакетно: старые строки
        # удаляются и из списка, и из виджета, счёт 1:1 (splitlines keepends).
        if not text:
            return
        self.log_lines.extend(text.splitlines(keepends=True))
        self.log_area.insert(tk.END, text)
        self.log_area.see(tk.END)
        overflow = len(self.log_lines) - MAX_LOG_LINES
        if overflow >= LOG_TRIM_LINES:
            del self.log_lines[:overflow]
            try:
                self.log_area.delete("1.0", f"{overflow + 1}.0")
            except tk.TclError:
                pass

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

    def read_output(self, proc=None):
        # Привязываемся к своему процессу локально: после рестарта
        # self.process уже указывает на новый сервер, а этот поток
        # дочитывает вывод старого и не должен трогать UI нового.
        proc = proc if proc is not None else self.process
        if proc is None or proc.stdout is None:
            return
        for line in iter(proc.stdout.readline, ''):
            if not self.is_running or self.process is not proc:
                break
            self.log(line)
            if not self.server_ready and "llama_server: model loaded" in line:
                self.server_ready = True
                self._update_badge_status()
                self.root.after(0, self.set_ready_state)

        try:
            proc.wait()
        except (OSError, ValueError):
            pass
        if self.process is not proc:
            return
        exit_code = proc.returncode

        if self.manual_stop_requested:
            self.root.after(0, lambda: self.set_stopped_state(play_sound=True))
        elif not self.server_ready and exit_code is not None:
            self.root.after(0, self.set_loading_error_state)
        else:
            self.root.after(0, lambda: self.set_stopped_state(play_sound=True))

    def start_server(self):
        if self.is_running:
            return
        if self._restart_pending:
            self.log(f"--- {self.tr('log_restarting')} ---\n")
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
            self.status_label.config(text=self.tr("status_loading"), fg=self._status_fg("warn"))
            self.start_loading_blink()
            self._update_badge_status()
            self.log(f"--- {self.tr('log_start_server')} ---\n{self.tr('log_command')} {' '.join(full_cmd)}\n\n")
            threading.Thread(target=self.read_output, args=(self.process,), daemon=True).start()

        except Exception as e:
            messagebox.showerror(self.tr("err_start"), str(e))

    def _terminate_process(self, proc):
        """Мягкая остановка; возвращает False если процесс уже мёртв."""
        if proc is None:
            return False
        try:
            proc.terminate()
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False

    def _reap_process(self, proc, after=None):
        """Ждём завершения (terminate -> wait -> kill -> wait), зомби не оставляем.

        Работает в фоновом потоке, UI не блокирует. Колбэк after вызывается
        в потоке UI уже после гарантированного освобождения порта.
        """
        if proc is None:
            if after is not None:
                self._run_on_ui_thread(after)
            return
        try:
            proc.wait(timeout=STOP_GRACE_TIMEOUT)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except (ProcessLookupError, PermissionError, OSError):
                pass
            try:
                proc.wait(timeout=STOP_KILL_TIMEOUT)
            except (subprocess.TimeoutExpired, OSError, ValueError):
                pass
        except (OSError, ValueError):
            pass
        for stream in (getattr(proc, "stdout", None), getattr(proc, "stderr", None)):
            try:
                if stream is not None:
                    stream.close()
            except (OSError, ValueError):
                pass
        if after is not None:
            self._run_on_ui_thread(after)

    def _run_on_ui_thread(self, callback):
        try:
            if self.root.winfo_exists():
                self.root.after(0, callback)
        except tk.TclError:
            pass

    def stop_server(self, log_message=True):
        proc = self.process
        if proc is None or not self.is_running:
            return
        self.manual_stop_requested = True
        self.is_running = False
        self._update_badge_status()
        self._terminate_process(proc)
        self.set_stopped_state(play_sound=False)
        if log_message:
            self.log(f"\n--- {self.tr('log_force_stopped')} ---\n")
        threading.Thread(target=self._reap_process, args=(proc,), daemon=True).start()

    def restart_server(self):
        if not self.is_running:
            self.start_server()
            return
        if self._restart_pending:
            return

        proc = self.process
        self.log(f"\n--- {self.tr('log_restarting')} ---\n")
        self.manual_stop_requested = True
        self.is_running = False
        self._update_badge_status()
        self._restart_pending = True
        self._terminate_process(proc)
        self.set_stopped_state(play_sound=False)
        threading.Thread(target=self._reap_process, args=(proc, self._start_after_reap), daemon=True).start()

    def _start_after_reap(self):
        """Запуск нового сервера строго после смерти старого (порт свободен)."""
        self._restart_pending = False
        self.start_server()

    def get_server_url(self):
        host = self.get_param_value("--host") or "localhost"
        port = self.get_param_value("--port") or "18080"

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
            self.status_label.config(text=self.tr("status_running"), fg=self._status_fg("ok"))
            self._update_badge_status()
            self.play_loaded_sound()
            if self.open_browser_on_load_var.get():
                self.open_server_in_browser()

    def set_stopped_state(self, play_sound=False):
        self.stop_loading_blink()
        self.is_running = False
        self.server_ready = False
        self._update_badge_status()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.DISABLED)
        self.status_label.config(text=self.tr("status_stopped"), fg=self._status_fg("err"))
        if play_sound:
            self.play_stopped_sound()

    def _save_config_safely(self):
        try:
            self.save_config()
        except OSError as exc:
            messagebox.showerror(self.tr("msg_save_error"), str(exc))

    def on_close(self):
        # Гасим встроенную консоль, чтобы не оставлять сироту.
        self._terminal_cancel_watchdog()
        self._terminal_cancel_resize()
        self._terminal_unsubclass_host()
        self._terminal_kill_proc(getattr(self, "terminal_proc", None))
        if self.is_running:
            if messagebox.askokcancel(self.tr("msg_exit"), self.tr("msg_exit_confirm")):
                proc = self.process
                self.stop_server()
                self._save_config_safely()
                self.root.destroy()
                # Окно уже закрыто — можно блокирующе дождаться процесса,
                # чтобы не оставить сироту, держащую порт.
                self._reap_process(proc)
        else:
            self._save_config_safely()
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = LlamaServerGUI(root)
    root.mainloop()
