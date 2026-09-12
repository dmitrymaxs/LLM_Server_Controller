# LLM Server Controller v0.1.6

GUI-приложение для запуска и управления локальным LLM (Large Language Model) сервером на базе llama.cpp.

## Возможности

- **Запуск / остановка / перезапуск** llama-server с графическим интерфейсом
- **Встроенная установка** llama.cpp — скачивание бинарников с GitHub Releases автоматически
- **Настройка параметров** llama-server через 12 категорий групп (контекст, GPU, память, CPU, генерация и т.д.)
- **Интерфейс на русском / английском**
- **Логи в реальном времени** — просмотр, копирование, сохранение, очистка
- **Экспорт/импорт настроек** в JSON-файл
- **Список устройств GPU** через команду `--list-devices`
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
| **Сервер** | Путь к `llama-server.exe` (Windows) / `llama-server` (Linux). Кнопка "Обзор" открывает диалог выбора файла. Кнопка "Скачать llama.cpp" — встроенная установка. Кнопка "Устройства" показывает список GPU через `--list-devices`. |
| **Модель** | Путь к файлу модели формата `.gguf`. Кнопка "Обзор" открывает диалог выбора файла. |
| **Размер окна** | Ширина и высота окна приложения в пикселях (например, 1200×800). |
| **Команды** | Дополнительные аргументы для llama-server (например: `--temp 0.7 --top-k 40`). Поддерживаются кавычки для групповых аргументов. |

### Управление параметрами

Параметры llama-server разделены на категории, которые можно переключать в боковой панели:

| Группа | Параметры |
|-------|-----------|
| **Основные** | `--ctx-size` (размер контекста), `--n-gpu-layers`, `--flash-attn`, `--threads`, `--cache-type-k/v`, `--load-mode` (auto, none, mmap, mlock, mmap+mlock, dio), `--agent`, `--host`, `--port` |
| **Контекст** | `--keep`, `--parallel`, `--slots` |
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
| **Диагностика** | `--verbose`, `--log-file`, `--metrics` |
| **Backend: CUDA/Vulkan/HIP/Metal/SYCL** | Выбор GPU-бэкенда через параметр `--device` |

### Управление сервером

- **Старт** — запускает llama-server. Статус меняется на оранжевый (загрузка) → зелёный (готов).
- **Стоп** — останавливает сервер принудительно.
- **Перезапуск** — сначала останавливает, затем запускает заново.
- При успешной загрузке модели статус становится **зелёным**, и при включённом选项中 автоматически открывается браузер с URL сервера (`http://localhost:18080/`).

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
| **Параметры** | Переключение между группами параметров |
| **Звуки** | Вкл/выкл звуковые сигналы при загрузке / остановке сервера |

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
- Язык интерфейса
- Путь к каталогам установки llama.cpp
- Размер окна приложения
- Настройки звуков
- Дополнительные аргументы
- Все параметры llama-server

## Конфликт путей

При запуске приложения приложение автоматически проверяет пути: если путь к серверу или модели не существует — показывает ошибку. Если в директории установки есть другой файл с тем же именем, предлагает выбрать другую директорию.

## Обновления и поддержка

- **Сайт проекта**: https://llm-server.github.io/
- **GitHub Releases**: https://github.com/dmitrymaxs/LLM_Server_Controller/releases
- **Источники библиотек**: llama.cpp (ggml-org), PyInstaller, pywebview

---

# LLM Server Controller v0.1.6

GUI application for launching and managing a local LLM (Large Language Model) server based on llama.cpp.

## Features

- **Start / Stop / Restart** llama-server with a graphical interface
- **Built-in installation** of llama.cpp — automatically downloads binaries from GitHub Releases
- **Parameter configuration** for llama-server across 12 parameter groups (context, GPU, memory, CPU, generation, etc.)
- **Russian / English interface**
- **Real-time logs** — view, copy, save, and clear
- **Export/Import settings** to/from a JSON file
- **GPU device list** via the `--list-devices` command
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
| **Server** | Path to `llama-server.exe` (Windows) / `llama-server` (Linux). The "Browse" button opens a file selection dialog. The "Download llama.cpp" button triggers built-in installation. The "Devices" button lists GPUs via `--list-devices`. |
| **Model** | Path to the `.gguf` model file. The "Browse" button opens a file selection dialog. |
| **Window Size** | Width and height of the application window in pixels (e.g., 1200×800). |
| **Commands** | Additional arguments for llama-server (e.g.: `--temp 0.7 --top-k 40`). Quotes support grouped arguments. |

### Parameter Configuration

llama-server parameters are organized into categories, switchable in the side panel:

| Group | Parameters |
|-------|-------------|
| **Main** | `--ctx-size` (context size), `--n-gpu-layers`, `--flash-attn`, `--threads`, `--cache-type-k/v`, `--host`, `--port` |
| **Context** | `--keep`, `--parallel`, `--slots` |
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
| **Diagnostics** | `--verbose`, `--log-file`, `--metrics` |
| **Backend: CUDA/Vulkan/HIP/Metal/SYCL** | GPU backend selection via `--device` parameter |

### Server Control

- **Start** — launches llama-server. Status changes to orange (loading) → green (ready).
- **Stop** — forcefully stops the server.
- **Restart** — first stops, then starts again.
- When the model loads successfully, status becomes **green**, and if enabled, the browser automatically opens with the server URL (`http://localhost:18080/`).

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
| **Parameters** | Switch between parameter groups |
| **Sounds** | Enable/disable sound beeps on server load / stop |

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
- Interface language
- llama.cpp installation directories
- Application window size
- Sound settings
- Custom arguments
- All llama-server parameters

## Path Conflict Handling

On launch, the app automatically validates paths: if the server or model path does not exist — it shows an error. If a different file with the same name exists in the install directory — it prompts to choose another directory.

## Updates & Support

- **Project website**: https://llm-server.github.io/
- **GitHub Releases**: https://github.com/dmitrymaxs/LLM_Server_Controller/releases
- **Library sources**: llama.cpp (ggml-org), PyInstaller, pywebview
