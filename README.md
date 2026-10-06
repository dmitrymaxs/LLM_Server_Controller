# LLM Server Controller v0.2.0

GUI-приложение для запуска и управления локальным LLM (Large Language Model) сервером на базе llama.cpp.

## Возможности

- **Запуск / остановка / перезапуск** llama-server с графическим интерфейсом
- **Встроенная установка** llama.cpp — скачивание бинарников с GitHub Releases автоматически
- **Менеджер моделей** — вкладки «Локальные» / «HuggingFace»: просмотр `.gguf` в папке моделей, поиск по HuggingFace Hub (сортировка по лайкам / скачиваниям / обновлению), просмотр GGUF-файлов, скачивание с прогрессом и отменой, кнопка «Использовать» подставляет путь в поле «Модель» (меню **Файл → Модели…**)
- **Встроенный терминал** — настоящая системная консоль в правой панели (Windows: cmd.exe встраивается через SetParent, Linux: `xterm -into`): работают интерактивные TUI-программы, кнопки «Новая консоль» / «Фокус» / «Закрыть», видимость — меню **Вид → Терминал**, выбор сохраняется
- **Установка pi-агента** — меню **Файл → Установить pi-агента** (Windows: открывает отдельное окно PowerShell с командой `irm https://pi.dev/install.ps1 | iex`)
- **Круговой индикатор статуса** — рядом со статусом: зелёный — работает, оранжевый — загружается, синий — остановлен
- **Настройка параметров** llama-server через 18 категорий групп (контекст, GPU, память, CPU, генерация и т.д.)
- **Интерфейс на русском / английском**
- **Логи в реальном времени** — просмотр, копирование, сохранение, очистка
- **Экспорт/импорт настроек** в JSON-файл
- **Список устройств GPU** через команду `--list-devices`
- **Тёмная и светлая темы** — переключение в меню **Вид**, выбор сохраняется
- **Проверка обновлений** — новых версий приложения и сборок llama.cpp (бейдж «Актуальная версия» и меню **Справка → Проверить обновления**)
- **Индикатор версии сервера** — рядом с полем «Сервер» всегда видна установленная сборка (определяется живым опросом `llama-server --version`, работает и для нестандартных папок)
- **Открытие сервера в браузере** после загрузки модели

## Системные требования

- **Windows 10/11 x64** или **Linux (Ubuntu 20.04+)**
- Python 3.8–3.12
- Модель в формате `.gguf`
- GPU (опционально) — NVIDIA CUDA, AMD ROCm/HIP, Intel Vulkan/SYCL

## Установка

### Вариант 1: Скачать готовое приложение

Скачайте последний релиз с [GitHub Releases](https://github.com/dmitrymaxs/LLM_Server_Controller/releases):
- Запустите `LLM Server Controller.exe` (Windows) или `LLM Server Controller` (Linux)

### Вариант 2: Сборка из исходных файлов

1. Установите зависимости:
   ```bash
   pip install pyinstaller>=6.0 pywebview>=6.2.1
   ```
2. Соберите исполняемый файл:
   ```bash
   python -m PyInstaller main.py --onefile --name "LLM Server Controller"
   ```

### Для продолжения работы

Запустите приложение и в меню **Файл → Установить llama.cpp** выберите нужную сборку (Vulkan / CUDA / CPU) для вашей платформы. Приложение скачает и установит бинарники автоматически.

## Быстрый запуск

1. Запустите `LLM Server Controller.exe`
2. Нажмите **Установить llama.cpp**, если сервер ещё не установлен
3. Выберите путь к модели (`.gguf`) через кнопку **Обзор** в поле "Модель"
4. Укажите путь к исполняемому файлу сервера `llama-server.exe` (или `llama-server` на Linux) в поле "Сервер"
5. (Опционально) Настройте параметры: размер контекста, GPU-слои, температуру генерации и т.д.
6. Нажмите **Старт** — сервер запустится, статус сменится на зелёный

## Использование приложения

### Панель управления путями

| Поле | Описание |
|------|----------|
| **Сервер** | Путь к `llama-server.exe` (Windows) / `llama-server` (Linux). Кнопка "Обзор" открывает диалог выбора файла. Кнопка "Скачать llama.cpp" — встроенная установка. Справа показана **установленная версия** (обновляется при смене файла, в т.ч. ручным вводом пути). Ниже — бейдж **«Актуальная версия»**, если вышли обновления. Список GPU — в меню **Файл → Устройства** (`--list-devices`). |
| **Модель** | Путь к файлу модели формата `.gguf`. Кнопка "Обзор" открывает диалог выбора файла. Удобный выбор и скачивание — через менеджер **Файл → Модели…** (кнопка «Использовать» подставляет путь сюда). |
| **Размер окна** | Ширина и высота окна приложения в пикселях (например, 1200×800). |
| **Команды** | Дополнительные аргументы для llama-server (например: `--temp 0.7 --top-k 40`). Поддерживаются кавычки для групповых аргументов. |

### Менеджер моделей (Файл → Модели…)

- **Папка моделей** — поле вверху окна, кнопки «Обзор» и «Обновить»; выбор сохраняется в конфиге (`models_dir`).
- Вкладка **«Локальные»** — список `.gguf`-файлов папки (имя + размер), двойной клик или кнопка **«Использовать»** подставляет путь в поле «Модель», кнопка **«Открыть папку»** показывает файл в проводнике.
- Вкладка **«HuggingFace»** — поиск моделей по HuggingFace Hub (запрос, сортировка по лайкам / скачиваниям / обновлению, лимит), список GGUF-файлов выбранной модели с размерами, кнопка **«Скачать»** с прогрессом и отменой (при существующем файле — запрос на перезапись, после скачивания — предложение использовать модель как текущую).

### Управление параметрами

Параметры llama-server разделены на категории, которые можно переключать в боковой панели:

| Группа | Параметры |
|-------|-----------|
| **Основные** | `--ctx-size` (размер контекста), `--alias` (алиас модели для API), `--n-gpu-layers`, `--flash-attn`, `--threads`, `--cache-type-k/v`, `--load-mode` (auto, none, mmap, mlock, mmap+mlock, dio), `--agent`, `--host`, `--port` |
| **Контекст** | `--keep`, `--parallel`, `--slots`, `--slot-save-path` |
| **GPU и вычисления** | `--split-mode`, `--main-gpu`, `--tensor-split`, `--device` (CUDA0, Vulkan0…) |
| **Память** | `--defrag-thold`, `--no-kv-offload` |
| **CPU** | `--threads-batch`, `--cpu-mask`, `--cpu-range`, `--poll`, `--prio` |
| **Batch** | `--batch-size`, `--ubatch-size` |
| **Генерация текста** | `--temp`, `--top-k`, `--top-p`, `--min-p`, `--typical-p`, `--repeat-last-n`, `--seed` и др. |
| **Draft Model** | Параметры спекулятивного декодирования (`--draft-model`, `--draft-max`) |
| **MoE** | Параметры для моделей Mixture of Experts |
| **Embeddings / Reranking** | Включение режимов эмбеддингов и reranker |
| **Сервер** | `--timeout`, `--path`, `--no-webui` |
| **Безопасность** | SSL-сертификаты, API-ключ авторизации |
| **Диагностика** | `--verbose`, `--log-file`, `--log-format`, `--metrics`, `--no-perf` |
| **Backend: CUDA/Vulkan/HIP/Metal/SYCL** | Выбор GPU-бэкенда через параметр `--device` |

### Управление сервером

- **Старт** — запускает llama-server. Статус меняется на оранжевый (загрузка) → зелёный (готов).
- **Стоп** — останавливает сервер принудительно.
- **Перезапуск** — сначала останавливает, затем запускает заново.
- **Индикатор-бейдж** — кружок рядом со статусом дублирует состояние цветом: зелёный — работает, оранжевый — загружается, синий — остановлен.
- При успешной загрузке модели статус становится **зелёным**, и при включённом чекбоксе автоматически открывается браузер с URL сервера (`http://localhost:18080/`).

### Терминал (Вид → Терминал)

- Правая панель «Терминал» — встроенная настоящая консоль ОС, а не эмуляция через pipe: на Windows окно `cmd.exe` встраивается в панель (интерактивные TUI-программы, например `pi`, работают прямо в панели), на Linux используется `xterm -into`.
- Кнопки заголовка: **«Новая консоль»** (перезапуск), **«Фокус»** (вернуть клавиатурный фокус), **«Закрыть»** (скрыть панель).
- Консоль автоматически перезапускается при закрытии, растягивается при изменении размера панели; видимость панели сохраняется в конфиге (`terminal_visible`).

### Логи

- Правая часть окна отображает логи llama-server в реальном времени (фон — тёмный, шрифт — Consolas).
- **Копировать** — копирует все логи в буфер обмена.
- **Очистить** — удаляет все записанные логи.
- **Сохранить лог** — сохраняет логи в файл `.log` или `.txt`.

### Меню

| Раздел | Действие |
|--------|----------|
| **Файл → Импорт** | Загружает настройки из внешнего JSON-файла |
| **Файл → Экспорт** | Сохраняет текущие настройки в выбранный JSON-файл |
| **Файл → Установить llama.cpp** | Запускает встроенную установку |
| **Файл → Установить pi-агента** | Запускает установщик pi-агента в отдельном окне PowerShell (только Windows) |
| **Файл → Устройства** | Показывает список GPU/CPU через `--list-devices` |
| **Файл → Модели…** | Менеджер моделей: локальные `.gguf` + поиск и скачивание с HuggingFace |
| **Параметры** | Переключение между группами параметров |
| **Звуки** | Вкл/выкл звуковые сигналы при загрузке / остановке сервера |
| **Вид** | Переключение светлой / тёмной темы; показать / скрыть встроенный терминал |
| **Справка → Проверить обновления** | Проверяет новые версии приложения и сборок llama.cpp |

### Обновления

- При старте приложение тихо проверяет новые версии: свою (GitHub Releases) и свежие сборки llama.cpp.
- Если есть новое — в панели путей под версией сервера появляется бейдж **«Актуальная версия: …»** (клик открывает подробности).
- Диалог проверки показывает текущие и доступные версии; кнопки **«Открыть релизы»** (у строки приложения) и **«Установить llama.cpp»** (у строки сборки) ведут к обновлению.
- Версия установленного сервера определяется опросом `llama-server --version` по пути из настроек, поэтому корректна и для серверов в нестандартных папках; сохранённый при установке тег используется только если exe лежит в папке установки.

### Язык интерфейса

Кнопка переключения языка (RU ↔ EN) находится в нижней части панели инструментов. При активном сервере переключение отменено — нужно сначала остановить сервер.

## API сервера llama.cpp

После успешной загрузки модели llama-server доступен по адресу:

```
http://localhost:18080/
```

### Основные эндпоинты

| URL | Описание |
|-----|----------|
| `/v1/models` | Список моделей (REST API) |
| `/v1/completions` | Генерация текста |
| `/v1/chat/completions` | Chat-комpletions |
| `/v1/embeddings` | Эмбеддинги |
| `/v1/rerank` | Reranking (если включён) |

### Пример запроса на генерацию:

```bash
curl http://localhost:18080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "{имя_модели}",
    "messages": [{"role": "user", "content": "Привет!"}],
    "temperature": 0.7,
    "max_tokens": 256
  }'
```

## Структура конфигурации

Настройки сохраняются в JSON-файл `llama_config.json` в каталоге `%APPDATA%\LLM_Server_Controller\` (Windows) или `~/.LLM_Server_Controller/` (Linux). Файл содержит:

- Путь к серверу и модели
- Папка моделей (`models_dir`)
- Язык интерфейса
- Путь к каталогам установки llama.cpp
- Размер окна приложения
- Настройки звуков
- Выбранная тема оформления (светлая/тёмная)
- Видимость встроенного терминала
- Дополнительные аргументы
- Все параметры llama-server

## Конфликт путей

При запуске приложения приложение автоматически проверяет пути: если путь к серверу или модели не существует — показывает ошибку. Если в директории установки есть другой файл с тем же именем, предлагает выбрать другую директорию.

## Обновления и поддержка

- **Сайт проекта**: https://llm-server.github.io/
- **GitHub Releases**: https://github.com/dmitrymaxs/LLM_Server_Controller/releases
- **Источники библиотек**: llama.cpp (ggml-org), PyInstaller, pywebview

---

# LLM Server Controller v0.2.0

GUI application for launching and managing a local LLM (Large Language Model) server based on llama.cpp.

## Features

- **Start / Stop / Restart** llama-server with a graphical interface
- **Built-in installation** of llama.cpp — automatically downloads binaries from GitHub Releases
- **Model manager** — «Local» / «HuggingFace» tabs: browse `.gguf` files in the models folder, search HuggingFace Hub (sort by likes / downloads / updated), preview GGUF files, download with progress and cancel, «Use» button puts the path into the «Model» field (**File → Models…**)
- **Built-in terminal** — a real OS console in the right panel (Windows: cmd.exe embedded via SetParent, Linux: `xterm -into`): interactive TUI programs work inside the panel, «New console» / «Focus» / «Close» buttons, visibility via **View → Terminal**, choice is saved
- **Pi agent installation** — **File → Install pi agent** menu (Windows: opens a separate PowerShell window with `irm https://pi.dev/install.ps1 | iex`)
- **Circular status badge** — next to the status: green — working, orange — loading, blue — stopped
- **Parameter configuration** for llama-server across 18 parameter groups (context, GPU, memory, CPU, generation, etc.)
- **Russian / English interface**
- **Real-time logs** — view, copy, save, and clear
- **Export/Import settings** to/from a JSON file
- **GPU device list** via the `--list-devices` command
- **Dark and light themes** — switch via the **View** menu, choice is saved
- **Update checking** — for new app versions and llama.cpp builds («Latest version» badge and **Help → Check for updates**)
- **Server version indicator** — the installed build is always shown next to the «Server» field (detected live via `llama-server --version`, works for custom folders too)
- **Auto-open server in browser** after model loads

## System Requirements

- **Windows 10/11 x64** or **Linux (Ubuntu 20.04+)**
- Python 3.8–3.12
- Model in `.gguf` format
- GPU (optional) — NVIDIA CUDA, AMD ROCm/HIP, Intel Vulkan/SYCL

## Installation

### Option 1: Download the ready-made application

Download the latest release from [GitHub Releases](https://github.com/dmitrymaxs/LLM_Server_Controller/releases):
- Run `LLM Server Controller.exe` (Windows) or `LLM Server Controller` (Linux)

### Option 2: Build from source files

1. Install dependencies:
   ```bash
   pip install pyinstaller>=6.0 pywebview>=6.2.1
   ```
2. Build the executable:
   ```bash
   python -m PyInstaller main.py --onefile --name "LLM Server Controller"
   ```

### For Continued Use

Launch the application and in the menu **File → Install llama.cpp**, select the appropriate build (Vulkan / CUDA / CPU) for your platform. The app will download and install binaries automatically.

## Quick Start

1. Run `LLM Server Controller.exe`
2. Click **Install llama.cpp** if the server is not yet installed
3. Select the model path (`.gguf`) using the **Browse** button in the "Model" field
4. Specify the path to the server executable `llama-server.exe` (or `llama-server` on Linux) in the "Server" field
5. (Optional) Configure parameters: context size, GPU layers, generation temperature, etc.
6. Click **Start** — the server starts; status changes to green

## Application Usage

### Path Control Panel

| Field | Description |
|-------|-------------|
| **Server** | Path to `llama-server.exe` (Windows) / `llama-server` (Linux). The "Browse" button opens a file selection dialog. The "Download llama.cpp" button triggers built-in installation. The **installed version** is shown on the right (refreshes when the file changes, including manual path edits). Below it — a **«Latest version»** badge when updates are available. The GPU list moved to **File → Devices** (`--list-devices`). |
| **Model** | Path to the `.gguf` model file. The "Browse" button opens a file selection dialog. Convenient pick/download — via the **File → Models…** manager (the «Use» button puts the path here). |
| **Window Size** | Width and height of the application window in pixels (e.g., 1200×800). |
| **Commands** | Additional arguments for llama-server (e.g.: `--temp 0.7 --top-k 40`). Quotes support grouped arguments. |

### Model manager (File → Models…)

- **Models folder** — field at the top of the window, «Browse» and «Refresh» buttons; the choice is saved to the config (`models_dir`).
- **«Local»** tab — list of `.gguf` files in the folder (name + size), double-click or the **«Use»** button puts the path into the «Model» field, **«Open folder»** reveals the file in the file manager.
- **«HuggingFace»** tab — search models on the HuggingFace Hub (query, sort by likes / downloads / updated, limit), list GGUF files of the selected model with sizes, **«Download»** button with progress and cancel (overwrite prompt for existing files, offer to use the downloaded model as current after download).

### Parameter Configuration

llama-server parameters are organized into categories, switchable in the side panel:

| Group | Parameters |
|-------|-------------|
| **Main** | `--ctx-size` (context size), `--alias` (model alias for the API), `--n-gpu-layers`, `--flash-attn`, `--threads`, `--cache-type-k/v`, `--load-mode` (auto, none, mmap, mlock, mmap+mlock, dio), `--agent`, `--host`, `--port` |
| **Context** | `--keep`, `--parallel`, `--slots`, `--slot-save-path` |
| **GPU & Computation** | `--split-mode`, `--main-gpu`, `--tensor-split`, `--device` (CUDA0, Vulkan0…) |
| **Memory** | `--defrag-thold`, `--no-kv-offload` |
| **CPU** | `--threads-batch`, `--cpu-mask`, `--cpu-range`, `--poll`, `--prio` |
| **Batch** | `--batch-size`, `--ubatch-size` |
| **Text Generation** | `--temp`, `--top-k`, `--top-p`, `--min-p`, `--typical-p`, `--repeat-last-n`, `--seed`, etc. |
| **Draft Model** | Speculative decoding parameters (`--draft-model`, `--draft-max`) |
| **MoE** | Parameters for Mixture of Experts models |
| **Embeddings / Reranking** | Enable embedding and reranker modes |
| **Server** | `--timeout`, `--path`, `--no-webui` |
| **Security** | SSL certificates, API key authentication |
| **Diagnostics** | `--verbose`, `--log-file`, `--log-format`, `--metrics`, `--no-perf` |
| **Backend: CUDA/Vulkan/HIP/Metal/SYCL** | GPU backend selection via `--device` parameter |

### Server Control

- **Start** — launches llama-server. Status changes to orange (loading) → green (ready).
- **Stop** — forcefully stops the server.
- **Restart** — first stops, then starts again.
- **Status badge** — a circle next to the status mirrors the state by color: green — working, orange — loading, blue — stopped.
- When the model loads successfully, status becomes **green**, and if enabled, the browser automatically opens with the server URL (`http://localhost:18080/`).

### Terminal (View → Terminal)

- The «Terminal» panel on the right is a built-in real OS console, not a pipe emulation: on Windows the `cmd.exe` window is embedded into the panel (interactive TUI programs such as `pi` work right inside the panel), on Linux `xterm -into` is used.
- Header buttons: **«New console»** (respawn), **«Focus»** (return keyboard focus), **«Close»** (hide the panel).
- The console auto-respawns when closed and stretches on panel resize; panel visibility is saved to the config (`terminal_visible`).

### Logs

- The right side of the window displays llama-server logs in real time (dark background, Consolas font).
- **Copy** — copies all logs to clipboard.
- **Clear** — removes all logged entries.
- **Save Log** — saves logs to a `.log` or `.txt` file.

### Menu

| Section | Action |
|---------|--------|
| **File → Import** | Loads settings from an external JSON file |
| **File → Export** | Saves current settings to a selected JSON file |
| **File → Install llama.cpp** | Triggers built-in installation |
| **File → Install pi agent** | Starts the pi agent installer in a separate PowerShell window (Windows only) |
| **File → Devices** | Lists GPUs/CPUs via `--list-devices` |
| **File → Models…** | Model manager: local `.gguf` files + search and download from HuggingFace |
| **Parameters** | Switch between parameter groups |
| **Sounds** | Enable/disable sound beeps on server load / stop |
| **View** | Switches the light / dark theme; show / hide the built-in terminal |
| **Help → Check for updates** | Checks for new app versions and llama.cpp builds |

### Updates

- On startup the app quietly checks for new versions: its own (GitHub Releases) and fresh llama.cpp builds.
- When something is new, a **«Latest version: …»** badge appears in the path panel under the server version (click opens details).
- The check dialog shows current and available versions; the **«Open releases»** button (next to the app row) and **«Install llama.cpp»** (next to the build row) lead to the update.
- The installed server version is detected by running `llama-server --version` at the configured path, so it is correct for servers in custom folders too; the tag saved at install time is used only if the exe lives in the install folder.

### Interface Language

The language toggle button (RU ↔ EN) is located in the lower part of the toolbar. Language switching is disabled while the server is active — you must stop the server first.

## llama.cpp Server API

After successful model loading, llama-server is accessible at:

```
http://localhost:18080/
```

### Main Endpoints

| URL | Description |
|-----|-------------|
| `/v1/models` | List models (REST API) |
| `/v1/completions` | Text generation |
| `/v1/chat/completions` | Chat completions |
| `/v1/embeddings` | Embeddings |
| `/v1/rerank` | Reranking (if enabled) |

### Example Generation Request:

```bash
curl http://localhost:18080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "{model_name}",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 256
  }'
```

## Configuration Structure

Settings are saved to a JSON file `llama_config.json` in `%APPDATA%\LLM_Server_Controller\` (Windows) or `~/.LLM_Server_Controller/` (Linux). The file contains:

- Server and model paths
- Models folder (`models_dir`)
- Interface language
- llama.cpp installation directories
- Application window size
- Sound settings
- Selected UI theme (light/dark)
- Built-in terminal visibility
- Custom arguments
- All llama-server parameters

## Path Conflict Handling

On launch, the app automatically validates paths: if the server or model path does not exist — it shows an error. If a different file with the same name exists in the install directory — it prompts to choose another directory.

## Updates & Support

- **Project website**: https://llm-server.github.io/
- **GitHub Releases**: https://github.com/dmitrymaxs/LLM_Server_Controller/releases
- **Library sources**: llama.cpp (ggml-org), PyInstaller, pywebview
