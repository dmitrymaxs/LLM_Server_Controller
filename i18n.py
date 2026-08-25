"""Интернационализация (RU/EN) для LLM Server Controller.

Поддерживается два языка: "ru" и "en". Выбор текущего языка хранится в
объекте :class:`I18n`. Все строки интерфейса и сообщений берутся из словаря
``TRANSLATIONS``. PARAM_GROUPS (названия категорий и подсказки параметров)
локализуются отдельно через словари ``GROUP_TITLES`` и ``PARAM_HINTS``.
"""

from __future__ import annotations

DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = ("ru", "en")


def _map(key: str, ru: str, en: str) -> dict:
    return {"ru": ru, "en": en}


TRANSLATIONS = {
    # --- Заголовок окна ---
    "app_title": _map("app_title", "LLM Server Controller v.0.1.6", "LLM Server Controller v.0.1.6"),

    # --- Меню ---
    "menu_file": _map("menu_file", "Файл", "File"),
    "menu_params": _map("menu_params", "Параметры", "Parameters"),
    "menu_sounds": _map("menu_sounds", "Звуки", "Sounds"),
    "menu_help": _map("menu_help", "Справка", "Help"),

    "menu_import": _map("menu_import", "Импорт", "Import"),
    "menu_export": _map("menu_export", "Экспорт", "Export"),
    "menu_install_llama": _map("menu_install_llama", "Установить llama.cpp", "Install llama.cpp"),
    "menu_exit": _map("menu_exit", "Выход", "Exit"),
    "menu_help_help": _map("menu_help_help", "Справка", "Help"),
    "menu_about": _map("menu_about", "О программе", "About"),
    "menu_sound_loaded": _map("menu_sound_loaded", "Звук загрузки", "Loaded sound"),
    "menu_sound_stopped": _map("menu_sound_stopped", "Звук отключения", "Stopped sound"),

    # --- Настройки путей ---
    "frame_paths": _map("frame_paths", " Настройки путей ", " Path settings "),
    "label_server": _map("label_server", "Сервер:", "Server:"),
    "label_model": _map("label_model", "Модель:", "Model:"),
    "btn_browse": _map("btn_browse", "Обзор...", "Browse..."),
    "btn_download_llama": _map("btn_download_llama", "Скачать llama.cpp", "Download llama.cpp"),
    "btn_download_llama_progress": _map("btn_download_llama_progress", "Список...", "Listing..."),
    "btn_download_llama_installing": _map("btn_download_llama_installing", "Установка...", "Installing..."),
    "btn_devices": _map("btn_devices", "Устройства", "Devices"),
    "btn_devices_loading": _map("btn_devices_loading", "Загрузка...", "Loading..."),
    "label_window_size": _map("label_window_size", "Окно (Ш×В):", "Window (W×H):"),
    "label_commands": _map("label_commands", "Команды:", "Commands:"),

    # --- Тулбар ---
    "btn_save": _map("btn_save", "Сохранить", "Save"),
    "btn_import": _map("btn_import", "Импорт", "Import"),
    "btn_export": _map("btn_export", "Экспорт", "Export"),
    "btn_reset": _map("btn_reset", "Сброс", "Reset"),
    "btn_start": _map("btn_start", "Запустить", "Start"),
    "btn_stop": _map("btn_stop", "Остановить", "Stop"),
    "btn_restart": _map("btn_restart", "Перезапустить", "Restart"),
    "chk_open_browser": _map("chk_open_browser", "Открыть браузер при загрузке", "Open browser on load"),
    "btn_lang_ru": _map("btn_lang_ru", "RU", "RU"),
    "btn_lang_en": _map("btn_lang_en", "EN", "EN"),

    # --- Статусы ---
    "status_stopped": _map("status_stopped", "Статус: Остановлен", "Status: Stopped"),
    "status_loading": _map("status_loading", "Статус: Загружается", "Status: Loading"),
    "status_running": _map("status_running", "Статус: Работает", "Status: Running"),
    "status_load_error": _map("status_load_error", "Статус: Ошибка загрузки", "Status: Load error"),
    "label_status_prefix": _map("label_status_prefix", "Статус:", "Status:"),

    # --- Параметры запуска ---
    "frame_params": _map("frame_params", " Параметры запуска ", " Launch parameters "),
    "label_categories": _map("label_categories", "Категории", "Categories"),
    "chk_enable": _map("chk_enable", "Включить", "Enable"),

    # --- Логи ---
    "label_server_logs": _map("label_server_logs", "Логи сервера", "Server logs"),
    "btn_copy": _map("btn_copy", "Копировать", "Copy"),
    "btn_clear": _map("btn_clear", "Очистить", "Clear"),
    "btn_save_log": _map("btn_save_log", "Сохранить", "Save"),

    # --- Диалоги: общие ---
    "msg_success": _map("msg_success", "Успех", "Success"),
    "msg_attention": _map("msg_attention", "Внимание", "Attention"),
    "msg_error": _map("msg_error", "Ошибка", "Error"),
    "msg_confirm": _map("msg_confirm", "Подтверждение", "Confirmation"),
    "msg_choice_required": _map("msg_choice_required", "Выбор обязателен", "Selection required"),
    "msg_recommended_suffix": _map("msg_recommended_suffix", " — Рекомендуется", " — Recommended"),
    "msg_exit": _map("msg_exit", "Выход", "Exit"),
    "btn_ok": _map("btn_ok", "OK", "OK"),
    "btn_close": _map("btn_close", "Закрыть", "Close"),
    "btn_cancel": _map("btn_cancel", "Отмена", "Cancel"),
    "btn_install_confirm": _map("btn_install_confirm", "Установить", "Install"),

    # --- Установка llama.cpp ---
    "msg_install_already_running": _map(
        "msg_install_already_running",
        "Установка llama.cpp уже выполняется.",
        "llama.cpp installation is already running.",
    ),
    "msg_install_while_running": _map(
        "msg_install_while_running",
        "Нельзя устанавливать llama.cpp во время работы сервера.",
        "Cannot install llama.cpp while the server is running.",
    ),
    "log_fetch_assets": _map(
        "log_fetch_assets",
        "--- Загрузка списка сборок llama.cpp с GitHub ---\n",
        "--- Fetching llama.cpp build list from GitHub ---\n",
    ),
    "msg_release_info": _map("msg_release_info", "Релиз", "Release"),
    "msg_builds_count": _map("msg_builds_count", "сборок", "builds"),
    "title_select_build": _map("title_select_build", "Выбор сборки llama.cpp", "Select llama.cpp build"),
    "msg_select_build": _map(
        "msg_select_build",
        "Выберите {platform}-сборку llama.cpp — релиз {tag}",
        "Select {platform} llama.cpp build — release {tag}",
    ),
    "msg_select_build_hint": _map(
        "msg_select_build_hint",
        "Список загружен с GitHub Releases. Vulkan x64 отмечен как рекомендуемый, если доступен.",
        "List loaded from GitHub Releases. Vulkan x64 is marked as recommended when available.",
    ),
    "msg_select_one_build": _map(
        "msg_select_one_build",
        "Выберите один вариант сборки.",
        "Select one build variant.",
    ),
    "title_select_install_dir": _map(
        "title_select_install_dir",
        "Выберите папку для установки llama.cpp",
        "Select folder for llama.cpp installation",
    ),
    "msg_install_path_is_file": _map(
        "msg_install_path_is_file",
        "Указан путь к файлу. Выберите папку для установки.",
        "A file path was specified. Select a folder for installation.",
    ),
    "msg_install_dir_not_empty": _map(
        "msg_install_dir_not_empty",
        "Папка установки не пуста. Существующие файлы могут быть перезаписаны. Продолжить?",
        "The installation folder is not empty. Existing files may be overwritten. Continue?",
    ),
    "log_install_header": _map("log_install_header", "--- Установка llama.cpp ---", "--- Installing llama.cpp ---"),
    "log_source": _map("log_source", "Источник:", "Source:"),
    "log_release": _map("log_release", "Релиз:", "Release:"),
    "log_variant": _map("log_variant", "Вариант:", "Variant:"),
    "log_folder": _map("log_folder", "Папка:", "Folder:"),
    "msg_install_complete": _map("msg_install_complete", "Установка завершена", "Installation complete"),
    "msg_install_complete_body": _map(
        "msg_install_complete_body",
        "llama.cpp установлен в:\n{dir}\n\nСборка: {label}\n{exe_name}:\n{exe_path}",
        "llama.cpp installed to:\n{dir}\n\nBuild: {label}\n{exe_name}:\n{exe_path}",
    ),
    "msg_install_error": _map("msg_install_error", "Ошибка установки llama.cpp", "llama.cpp installation error"),
    "msg_install_error_log": _map(
        "msg_install_error_log",
        "Ошибка установки llama.cpp: {error}\n\n",
        "llama.cpp installation error: {error}\n\n",
    ),
    "err_server_not_found": _map(
        "err_server_not_found",
        "Не найден {exe} после распаковки архива.",
        "{exe} not found after extracting the archive.",
    ),

    # --- Скачивание/распаковка ---
    "log_downloading": _map("log_downloading", "Скачивание:", "Downloading:"),
    "log_download_complete": _map("log_download_complete", "Скачивание завершено:", "Download complete:"),
    "log_extracting": _map("log_extracting", "Распаковка:", "Extracting:"),
    "err_unsafe_archive_path": _map(
        "err_unsafe_archive_path",
        "Небезопасный путь в архиве: {name}",
        "Unsafe path in archive: {name}",
    ),
    "log_dll_copied": _map(
        "log_dll_copied",
        "DLL-файлы скопированы рядом с llama-server.exe: {count}\n",
        "DLL files copied next to llama-server.exe: {count}\n",
    ),
    "log_exe_found": _map(
        "log_exe_found",
        "Установка завершена. Найден исполняемый файл: {path}\n\n",
        "Installation complete. Executable found: {path}\n\n",
    ),

    # --- Устройства ---
    "err_invalid_exe": _map(
        "err_invalid_exe",
        "Укажите корректный путь к {exe}",
        "Specify a valid path to {exe}",
    ),
    "title_devices_ok": _map("title_devices_ok", "Устройства системы (--list-devices)", "System devices (--list-devices)"),
    "title_devices_error": _map(
        "title_devices_error",
        "Устройства (--list-devices, код {code})",
        "Devices (--list-devices, code {code})",
    ),
    "msg_empty_output": _map(
        "msg_empty_output",
        "Команда завершилась с кодом {code}.\nВывод пуст.",
        "Command finished with code {code}.\nOutput is empty.",
    ),
    "err_list_devices_timeout": _map(
        "err_list_devices_timeout",
        "Превышено время ожидания команды --list-devices",
        "Timed out waiting for --list-devices",
    ),

    # --- Модель/пути ---
    "title_select_exe_win": _map("title_select_exe_win", "Выберите llama-server.exe", "Select llama-server.exe"),
    "title_select_exe_unix": _map("title_select_exe_unix", "Выберите llama-server", "Select llama-server"),
    "ft_executables_win": _map("ft_executables_win", "Исполняемые файлы", "Executable files"),
    "ft_executables_unix": _map("ft_executables_unix", "Исполняемые файлы", "Executable files"),
    "ft_all_files": _map("ft_all_files", "Все файлы", "All files"),
    "title_select_model": _map("title_select_model", "Выберите файл модели GGUF", "Select GGUF model file"),
    "ft_gguf": _map("ft_gguf", "Модели GGUF", "GGUF models"),

    # --- Сохранение/импорт/экспорт/сброс ---
    "msg_settings_saved": _map(
        "msg_settings_saved",
        "Настройки сохранены в {file}",
        "Settings saved to {file}",
    ),
    "msg_save_error": _map("msg_save_error", "Ошибка сохранения", "Save error"),
    "title_import": _map("title_import", "Импорт настроек", "Import settings"),
    "ft_json": _map("ft_json", "JSON файлы", "JSON files"),
    "msg_import_done": _map(
        "msg_import_done",
        "Настройки импортированы и сохранены в локальный конфиг.",
        "Settings imported and saved to local config.",
    ),
    "title_export": _map("title_export", "Экспорт настроек", "Export settings"),
    "msg_export_done": _map(
        "msg_export_done",
        "Настройки экспортированы в:\n{path}",
        "Settings exported to:\n{path}",
    ),
    "msg_export_error": _map("msg_export_error", "Ошибка экспорта", "Export error"),
    "msg_reset_while_running": _map(
        "msg_reset_while_running",
        "Нельзя сбрасывать настройки во время работы сервера.",
        "Cannot reset settings while the server is running.",
    ),
    "msg_reset_done": _map(
        "msg_reset_done",
        "Настройки возвращены к значениям по умолчанию.",
        "Settings restored to default values.",
    ),

    # --- Логи: операции ---
    "msg_logs_copied": _map(
        "msg_logs_copied",
        "Данные из логов скопированы в буфер обмена.",
        "Log data copied to clipboard.",
    ),
    "msg_nothing_to_copy": _map("msg_nothing_to_copy", "Нет данных для копирования.", "Nothing to copy."),
    "msg_no_logs_to_save": _map("msg_no_logs_to_save", "Нет логов для сохранения.", "No logs to save."),
    "title_save_logs": _map("title_save_logs", "Сохранить логи", "Save logs"),
    "ft_log": _map("ft_log", "Log файлы", "Log files"),
    "ft_text": _map("ft_text", "Текстовые файлы", "Text files"),
    "msg_logs_saved": _map("msg_logs_saved", "Логи сохранены в:\n{path}", "Logs saved to:\n{path}"),

    # --- Запуск/остановка ---
    "log_start_server": _map("log_start_server", "--- Запуск сервера ---", "--- Starting server ---"),
    "log_command": _map("log_command", "Команда:", "Command:"),
    "err_invalid_model": _map(
        "err_invalid_model",
        "Укажите корректный путь к файлу модели (.gguf)",
        "Specify a valid path to the model file (.gguf)",
    ),
    "err_invalid_window_size": _map(
        "err_invalid_window_size",
        "Ширина и высота окна должны быть целыми числами.",
        "Window width and height must be integers.",
    ),
    "err_start": _map("err_start", "Ошибка запуска", "Start error"),
    "log_force_stopped": _map("log_force_stopped", "--- Сервер принудительно остановлен ---", "--- Server forcefully stopped ---"),
    "log_restarting": _map("log_restarting", "--- Перезапуск сервера ---", "--- Restarting server ---"),
    "log_opening_browser": _map("log_opening_browser", "Открытие браузера:", "Opening browser:"),
    "log_browser_open_failed": _map(
        "log_browser_open_failed",
        "Не удалось открыть браузер автоматически: {error}\n",
        "Failed to open browser automatically: {error}\n",
    ),

    # --- Выход ---
    "msg_exit_confirm": _map(
        "msg_exit_confirm",
        "Сервер еще работает. Завершить процесс и выйти?",
        "The server is still running. Terminate the process and exit?",
    ),

    # --- Справка / О программе ---
    "title_help": _map("title_help", "Справка", "Help"),
    "title_about": _map("title_about", "О программе", "About"),

    # --- releases.py сообщения ---
    "err_latest_no_tag": _map(
        "err_latest_no_tag",
        "GitHub API не вернул tag_name для latest release",
        "GitHub API did not return tag_name for latest release",
    ),
    "err_empty_tag": _map("err_empty_tag", "Пустой release tag", "Empty release tag"),
    "rels_no_win_builds": _map(
        "rels_no_win_builds",
        "В релизе {tag} не найдены Windows-сборки; показан запасной список.",
        "No Windows builds found in release {tag}; a fallback list is shown.",
    ),
    "rels_no_linux_builds": _map(
        "rels_no_linux_builds",
        "В релизе {tag} не найдены Linux-сборки; показан запасной список.",
        "No Linux builds found in release {tag}; a fallback list is shown.",
    ),
    "rels_fetch_win_failed": _map(
        "rels_fetch_win_failed",
        "Не удалось загрузить список с GitHub ({error}). Используется запасной список.",
        "Failed to load the list from GitHub ({error}). A fallback list is used.",
    ),
    "rels_fetch_linux_failed": _map(
        "rels_fetch_linux_failed",
        "Не удалось загрузить список Linux-сборок с GitHub ({error}). Используется запасной список.",
        "Failed to load the Linux build list from GitHub ({error}). A fallback list is used.",
    ),
}


# Названия категорий параметров (id группы -> {lang: title})
GROUP_TITLES = {
    "main":            {"ru": "Основные",                       "en": "Main"},
    "context":         {"ru": "Контекст",                       "en": "Context"},
    "gpu":             {"ru": "GPU и вычисления",                 "en": "GPU & compute"},
    "memory":          {"ru": "Память",                          "en": "Memory"},
    "cpu":             {"ru": "Производительность CPU",          "en": "CPU performance"},
    "batch":           {"ru": "Batch",                           "en": "Batch"},
    "generation":      {"ru": "Генерация текста",                 "en": "Text generation"},
    "draft":           {"ru": "Draft Model (Speculative Decoding)", "en": "Draft Model (Speculative Decoding)"},
    "moe":             {"ru": "MoE (Mixture of Experts)",         "en": "MoE (Mixture of Experts)"},
    "embeddings":      {"ru": "Embeddings и Reranking",           "en": "Embeddings & Reranking"},
    "server":          {"ru": "Сервер",                          "en": "Server"},
    "security":        {"ru": "Безопасность",                     "en": "Security"},
    "diagnostics":     {"ru": "Логирование и диагностика",        "en": "Logging & diagnostics"},
    "backend_cuda":    {"ru": "Backend: CUDA (NVIDIA)",           "en": "Backend: CUDA (NVIDIA)"},
    "backend_vulkan":  {"ru": "Backend: Vulkan (NVIDIA/AMD/Intel)", "en": "Backend: Vulkan (NVIDIA/AMD/Intel)"},
    "backend_hip":     {"ru": "Backend: HIP (AMD ROCm)",         "en": "Backend: HIP (AMD ROCm)"},
    "backend_metal":   {"ru": "Backend: Metal (Apple)",           "en": "Backend: Metal (Apple)"},
    "backend_sycl":    {"ru": "Backend: SYCL (Intel GPU)",        "en": "Backend: SYCL (Intel GPU)"},
}


# Подсказки параметров: ключ параметра -> {lang: hint}
PARAM_HINTS = {
    "--ctx-size":        {"ru": "Размер контекста",                "en": "Context size"},
    "--alias":           {"ru": "Алиас модели (для идентификации в API)", "en": "Model alias (for API identification)"},
    "--n-gpu-layers":    {"ru": "Слои на GPU (-ngl)",              "en": "GPU layers (-ngl)"},
    "-fa":               {"ru": "Flash Attention (--flash-attn)",  "en": "Flash Attention (--flash-attn)"},
    "--threads":         {"ru": "Потоки CPU (-t)",                 "en": "CPU threads (-t)"},
    "--cache-type-k":    {"ru": "Формат Key Cache",                "en": "Key Cache format"},
    "--cache-type-v":    {"ru": "Формат Value Cache",              "en": "Value Cache format"},
    "--no-mmap":         {"ru": "Отключить memory mapping",        "en": "Disable memory mapping"},
    "--mlock":           {"ru": "Блокировка модели в RAM",         "en": "Lock model in RAM"},
    "--host":            {"ru": "IP-адрес сервера",                "en": "Server IP address"},
    "--port":            {"ru": "TCP-порт",                        "en": "TCP port"},
    "--keep":            {"ru": "Сохраняемые токены при переполнении", "en": "Tokens kept on overflow"},
    "--parallel":        {"ru": "Одновременные контексты",         "en": "Concurrent contexts"},
    "--slots":           {"ru": "Режим слотов",                    "en": "Slot mode"},
    "--slot-save-path":  {"ru": "Каталог сохранения слотов",        "en": "Slot save directory"},
    "--split-mode":      {"ru": "Распределение между GPU (-sm)",   "en": "Distribution between GPUs (-sm)"},
    "--main-gpu":        {"ru": "Главная видеокарта",              "en": "Main GPU"},
    "--tensor-split":    {"ru": "Доля тензоров на каждый GPU",      "en": "Tensor share per GPU"},
    "--device":          {"ru": "Устройство (CUDA0, Vulkan0…)",     "en": "Device (CUDA0, Vulkan0...)"},
    "--defrag-thold":    {"ru": "Порог дефрагментации KV Cache",   "en": "KV Cache defrag threshold"},
    "--no-kv-offload":   {"ru": "Не переносить KV Cache на GPU",   "en": "Do not offload KV Cache to GPU"},
    "--threads-batch":   {"ru": "Потоки обработки prompt (-tb)",  "en": "Prompt processing threads (-tb)"},
    "--cpu-mask":        {"ru": "Маска процессорных ядер",         "en": "CPU core mask"},
    "--cpu-range":       {"ru": "Диапазон ядер CPU",              "en": "CPU core range"},
    "--poll":            {"ru": "Активное ожидание CPU",          "en": "CPU busy polling"},
    "--prio":            {"ru": "Приоритет процесса",              "en": "Process priority"},
    "--batch-size":      {"ru": "Размер batch (-b)",               "en": "Batch size (-b)"},
    "--ubatch-size":     {"ru": "Размер micro batch (-ub)",        "en": "Micro batch size (-ub)"},
    "--temp":            {"ru": "Температура",                     "en": "Temperature"},
    "--top-k":           {"ru": "Top-K sampling",                 "en": "Top-K sampling"},
    "--top-p":           {"ru": "Top-P sampling",                 "en": "Top-P sampling"},
    "--min-p":           {"ru": "Min-P sampling",                 "en": "Min-P sampling"},
    "--typical-p":       {"ru": "Typical sampling",               "en": "Typical sampling"},
    "--repeat-last-n":   {"ru": "Окно повторов",                   "en": "Repeat window"},
    "--repeat-penalty":  {"ru": "Штраф за повторение",            "en": "Repetition penalty"},
    "--presence-penalty": {"ru": "Штраф за присутствие",          "en": "Presence penalty"},
    "--frequency-penalty": {"ru": "Штраф за частоту",             "en": "Frequency penalty"},
    "--mirostat":        {"ru": "Алгоритм Mirostat",               "en": "Mirostat algorithm"},
    "--mirostat-lr":     {"ru": "Скорость обучения Mirostat",     "en": "Mirostat learning rate"},
    "--mirostat-ent":    {"ru": "Целевая энтропия Mirostat",       "en": "Mirostat target entropy"},
    "--seed":            {"ru": "Seed генератора",                 "en": "Generator seed"},
    "--draft-model":     {"ru": "Путь к draft-модели",             "en": "Path to draft model"},
    "--draft-max":       {"ru": "Макс. draft-токенов",            "en": "Max draft tokens"},
    "--draft-min":       {"ru": "Мин. draft-токенов",             "en": "Min draft tokens"},
    "--gpu-layers-draft": {"ru": "GPU-слои для draft-модели",      "en": "GPU layers for draft model"},
    "--n-cpu-moe":       {"ru": "Эксперты на CPU",                "en": "Experts on CPU"},
    "--cpu-moe":         {"ru": "Включить CPU-эксперты",          "en": "Enable CPU experts"},
    "--embedding":       {"ru": "Режим эмбеддингов",               "en": "Embeddings mode"},
    "--reranking":       {"ru": "Режим reranker",                 "en": "Reranker mode"},
    "--timeout":         {"ru": "Тайм-аут соединения",            "en": "Connection timeout"},
    "--path":            {"ru": "Базовый URL-путь",                 "en": "Base URL path"},
    "--no-webui":        {"ru": "Отключить встроенный WebUI",      "en": "Disable built-in WebUI"},
    "--ssl-cert-file":   {"ru": "Файл SSL-сертификата",           "en": "SSL certificate file"},
    "--ssl-key-file":    {"ru": "Файл SSL-ключа",                 "en": "SSL key file"},
    "--api-key":         {"ru": "API-ключ авторизации",            "en": "Authorization API key"},
    "--verbose":         {"ru": "Подробные логи (-v)",             "en": "Verbose logs (-v)"},
    "--log-file":        {"ru": "Запись журнала в файл",           "en": "Write log to file"},
    "--log-format":      {"ru": "Формат журналов (text, json…)",  "en": "Log format (text, json...)"},
    "--metrics":         {"ru": "Публикация метрик",               "en": "Publish metrics"},
    "--no-perf":         {"ru": "Отключить статистику производительности", "en": "Disable performance stats"},
    "--device-cuda":     {"ru": "Устройство CUDA (напр. CUDA0)",   "en": "CUDA device (e.g. CUDA0)"},
    "--device-vulkan":   {"ru": "Устройство Vulkan (напр. Vulkan0)", "en": "Vulkan device (e.g. Vulkan0)"},
    "--device-hip":      {"ru": "Устройство HIP (напр. HIP0)",     "en": "HIP device (e.g. HIP0)"},
    "--device-metal":   {"ru": "Устройство Metal",                 "en": "Metal device"},
    "--device-sycl":     {"ru": "Устройство SYCL",                 "en": "SYCL device"},
}


# Подсказки для групп (id группы -> {lang: hint}). Рекомендуемые backend-описания.
GROUP_HINTS = {
    "main":           {"ru": "Наиболее часто используемые параметры",      "en": "Most commonly used parameters"},
    "backend_cuda":   {"ru": "Максимальная поддержка GPU. --device CUDA0, CUDA1…", "en": "Maximum GPU support. --device CUDA0, CUDA1..."},
    "backend_vulkan": {"ru": "Универсальный backend. --device Vulkan0…",   "en": "Universal backend. --device Vulkan0..."},
    "backend_hip":    {"ru": "AMD ROCm. --device HIP0…",                   "en": "AMD ROCm. --device HIP0..."},
    "backend_metal":  {"ru": "Только Apple Silicon",                      "en": "Apple Silicon only"},
    "backend_sycl":   {"ru": "Преимущественно Intel GPU",                 "en": "Primarily Intel GPU"},
}


# --- Тексты справки, отдельные большие блоки ---------------------------------

HELP_TEXT_RU = """LLM Server Controller — справка

Назначение программы:
Приложение позволяет выбрать llama-server, указать GGUF-модель, настроить параметры запуска,
запустить сервер, остановить его, перезапустить и просматривать логи.

Описание полей:
Сервер — путь к файлу llama-server.
Устройства — запускает llama-server --list-devices и показывает доступные GPU/CPU
устройства перед настройкой --device.
Модель — путь к файлу модели в формате .gguf.
Ширина окна — ширина окна приложения в пикселях.
Высота окна — высота окна приложения в пикселях.
Команды — дополнительные аргументы llama-server, которых нет в категориях.
Вписываются через пробел, как в командной строке. Аргументы со
пробелами берутся в двойные кавычки. Пример:
--jinja --special-flag "D:\\Path With Spaces\\file.txt"
Эти аргументы добавляются в конец команды запуска сервера.

Описание параметров запуска:
Слева — список категорий, справа — поля выбранной группы (4 колонки).
Переключение: клик в списке или меню «Параметры». Разделитель между параметрами
и логами можно перетаскивать для изменения высоты панелей.

Основные:
--ctx-size — размер контекста; --n-gpu-layers — слои на GPU; -fa — Flash Attention;
--threads — потоки CPU; --cache-type-k/v — формат KV Cache; --no-mmap, --mlock — память;
--host, --port — сетевые настройки сервера.

Другие группы: Контекст, GPU, Память, CPU, Batch, Генерация, Draft Model, MoE,
Embeddings, Сервер, Безопасность, Диагностика, а также Backend (CUDA, Vulkan, HIP, Metal, SYCL).
Поля backend-устройств (--device-cuda и т.д.) передаются как --device при запуске.

Кнопки и функции:
Сохранить настройки — сохраняет текущие пути, размеры окна и параметры в llama_config.json.
Импорт настроек — загружает настройки из внешнего JSON-файла.
Экспорт настроек — сохраняет текущие настройки в выбранный JSON-файл.
Сбросить параметры — возвращает параметры и размеры окна к значениям по умолчанию.
Запустить сервер — запускает llama-server с текущими параметрами.
Остановить — завершает работающий сервер.
Перезапустить — останавливает и снова запускает сервер с текущими настройками.
Сохранить лог — сохраняет видимые логи в файл .log или .txt.
Очистить лог — очищает окно логов.
Копировать лог — копирует выделенный фрагмент лога или весь лог, если выделения нет.

Меню Файл:
Импорт — загрузка настроек из JSON-файла.
Экспорт — сохранение текущих настроек в JSON-файл.
Выход — закрытие приложения с сохранением текущих настроек.

Замечания:
Некоторые параметры зависят от версии llama-server и вашей сборки.
Если сервер не запускается, проверьте путь к серверу, путь к модели и совместимость параметров."""

HELP_TEXT_EN = """LLM Server Controller — Help

Purpose:
The application lets you pick llama-server, specify a GGUF model, configure launch parameters,
start the server, stop it, restart it, and view logs.

Field descriptions:
Server — path to the llama-server file.
Devices — runs llama-server --list-devices and shows available GPU/CPU
devices before configuring --device.
Model — path to the model file in .gguf format.
Window width — application window width in pixels.
Window height — application window height in pixels.
Commands — extra llama-server arguments not covered by the categories.
They are entered separated by spaces, like in a command line. Arguments
with spaces are wrapped in double quotes. Example:
--jinja --special-flag "D:\\Path With Spaces\\file.txt"
These arguments are appended to the end of the server launch command.

Launch parameters:
On the left — list of categories, on the right — fields of the selected group (4 columns).
Switching: click in the list or via the "Parameters" menu. The divider between parameters
and logs can be dragged to change the panel heights.

Main:
--ctx-size — context size; --n-gpu-layers — GPU layers; -fa — Flash Attention;
--threads — CPU threads; --cache-type-k/v — KV Cache format; --no-mmap, --mlock — memory;
--host, --port — server network settings.

Other groups: Context, GPU, Memory, CPU, Batch, Generation, Draft Model, MoE,
Embeddings, Server, Security, Diagnostics, as well as Backend (CUDA, Vulkan, HIP, Metal, SYCL).
Backend-device fields (--device-cuda, etc.) are passed as --device on launch.

Buttons and functions:
Save settings — saves current paths, window size and parameters to llama_config.json.
Import settings — loads settings from an external JSON file.
Export settings — saves current settings to a chosen JSON file.
Reset parameters — restores parameters and window size to default values.
Start server — launches llama-server with current parameters.
Stop — terminates the running server.
Restart — stops and starts the server again with current settings.
Save log — saves visible logs to a .log or .txt file.
Clear log — clears the log window.
Copy log — copies the selected log fragment or the whole log if nothing is selected.

File menu:
Import — load settings from a JSON file.
Export — save current settings to a JSON file.
Exit — close the application, saving current settings.

Notes:
Some parameters depend on the llama-server version and your build.
If the server does not start, check the server path, model path, and parameter compatibility."""

HELP_TEXT = {"ru": HELP_TEXT_RU, "en": HELP_TEXT_EN}


class I18n:
    """Хранит текущий язык и возвращает переведённые строки."""

    def __init__(self, language: str = DEFAULT_LANGUAGE):
        self.language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    def set_language(self, language: str) -> None:
        if language in SUPPORTED_LANGUAGES:
            self.language = language

    def toggle(self) -> str:
        self.language = "en" if self.language == "ru" else "ru"
        return self.language

    def tr(self, key: str, **kwargs) -> str:
        entry = TRANSLATIONS.get(key)
        if entry is None:
            return key
        text = entry.get(self.language, entry.get(DEFAULT_LANGUAGE, key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                pass
        return text

    def group_title(self, group_id: str) -> str:
        entry = GROUP_TITLES.get(group_id)
        if not entry:
            return group_id
        return entry.get(self.language, entry.get(DEFAULT_LANGUAGE, group_id))

    def group_hint(self, group_id: str) -> str:
        entry = GROUP_HINTS.get(group_id)
        if not entry:
            return ""
        return entry.get(self.language, entry.get(DEFAULT_LANGUAGE, ""))

    def param_hint(self, param_key: str, fallback: str = "") -> str:
        entry = PARAM_HINTS.get(param_key)
        if not entry:
            return fallback
        return entry.get(self.language, entry.get(DEFAULT_LANGUAGE, fallback))

    def help_text(self) -> str:
        return HELP_TEXT.get(self.language, HELP_TEXT[DEFAULT_LANGUAGE])
