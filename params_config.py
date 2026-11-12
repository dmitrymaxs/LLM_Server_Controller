"""Группы параметров llama-server по справочнику (Глава 45)."""

LEGACY_PARAM_ALIASES = {
    "-ncmoe": "--n-cpu-moe",
    "--spec-draft-n-max": "--draft-max",
    "-mlock": "--mlock",
}

CACHE_TYPE_CHOICES = [
    "f32",
    "f16",
    "bf16",
    "q4_0",
    "q4_1",
    "q5_0",
    "q5_1",
    "q8_0",
    "q8_1",
    "iq4_nl",
]

LOAD_MODE_CHOICES = [
    "auto",
    "none",
    "mmap",
    "mlock",
    "mmap+mlock",
    "dio",
]

PARAM_GROUPS = [
    {
        "id": "main",
        "title": "Основные",
        "expanded": True,
        "hint": "Наиболее часто используемые параметры",
        "params": [
            {"key": "--ctx-size", "default": "16384", "hint": "Размер контекста"},
            {"key": "--alias", "default": "", "hint": "Алиас модели (для идентификации в API)"},
            {"key": "--n-gpu-layers", "default": "99", "hint": "Слои на GPU (-ngl)"},
            {"key": "-fa", "default": "on", "hint": "Flash Attention (--flash-attn)"},
            {"key": "--threads", "default": "", "hint": "Потоки CPU (-t)"},
            {"key": "--load-mode", "default": "mlock", "choices": LOAD_MODE_CHOICES, "hint": "Режим загрузки модели в память"},
            {"key": "--cache-type-k", "default": "q8_0", "choices": CACHE_TYPE_CHOICES, "hint": "Формат Key Cache"},
            {"key": "--cache-type-v", "default": "q8_0", "choices": CACHE_TYPE_CHOICES, "hint": "Формат Value Cache", "row_break_after": True},
            {"key": "--host", "default": "0.0.0.0", "hint": "IP-адрес сервера"},
            {"key": "--port", "default": "18080", "hint": "TCP-порт"},
            {"key": "--agent", "default": False, "hint": "Режим агента WebUI (встроенные инструменты, CORS-прокси)"},
            {"key": "-lv", "default": False, "flag_value": "4", "hint": "Детализация логов (-lv 4)"},
            {"key": "--reasoning", "default": "auto", "choices": ["auto", "on", "off"], "hint": "Reasoning/thinking в чате (on/off/auto)"},
        ],
    },
    {
        "id": "context",
        "title": "Контекст",
        "expanded": False,
        "params": [
            {"key": "--keep", "default": "", "hint": "Сохраняемые токены при переполнении"},
            {"key": "--parallel", "default": "", "hint": "Одновременные контексты"},
            {"key": "--slots", "default": "", "hint": "Режим слотов"},
            {"key": "--slot-save-path", "default": "", "hint": "Каталог сохранения слотов"},
        ],
    },
    {
        "id": "gpu",
        "title": "GPU и вычисления",
        "expanded": False,
        "params": [
            {"key": "--split-mode", "default": "", "hint": "Распределение между GPU (-sm)"},
            {"key": "--main-gpu", "default": "", "hint": "Главная видеокарта"},
            {"key": "--tensor-split", "default": "", "hint": "Доля тензоров на каждый GPU"},
            {"key": "--device", "default": "", "hint": "Устройство (CUDA0, Vulkan0…)"},
        ],
    },
    {
        "id": "memory",
        "title": "Память",
        "expanded": False,
        "params": [
            {"key": "--defrag-thold", "default": "", "hint": "Порог дефрагментации KV Cache"},
            {"key": "--no-kv-offload", "default": False, "hint": "Не переносить KV Cache на GPU"},
        ],
    },
    {
        "id": "cpu",
        "title": "Производительность CPU",
        "expanded": False,
        "params": [
            {"key": "--threads-batch", "default": "", "hint": "Потоки обработки prompt (-tb)"},
            {"key": "--cpu-mask", "default": "", "hint": "Маска процессорных ядер"},
            {"key": "--cpu-range", "default": "", "hint": "Диапазон ядер CPU"},
            {"key": "--poll", "default": "", "hint": "Активное ожидание CPU"},
            {"key": "--prio", "default": "", "hint": "Приоритет процесса"},
        ],
    },
    {
        "id": "batch",
        "title": "Batch",
        "expanded": False,
        "params": [
            {"key": "--batch-size", "default": "", "hint": "Размер batch (-b)"},
            {"key": "--ubatch-size", "default": "", "hint": "Размер micro batch (-ub)"},
        ],
    },
    {
        "id": "generation",
        "title": "Генерация текста",
        "expanded": False,
        "params": [
            {"key": "--temp", "default": "1.0", "hint": "Температура"},
            {"key": "--top-k", "default": "64", "hint": "Top-K sampling"},
            {"key": "--top-p", "default": "0.95", "hint": "Top-P sampling"},
            {"key": "--min-p", "default": "", "hint": "Min-P sampling"},
            {"key": "--typical-p", "default": "", "hint": "Typical sampling"},
            {"key": "--repeat-last-n", "default": "", "hint": "Окно повторов"},
            {"key": "--repeat-penalty", "default": "", "hint": "Штраф за повторение"},
            {"key": "--presence-penalty", "default": "", "hint": "Штраф за присутствие"},
            {"key": "--frequency-penalty", "default": "", "hint": "Штраф за частоту"},
            {"key": "--mirostat", "default": "", "hint": "Алгоритм Mirostat"},
            {"key": "--mirostat-lr", "default": "", "hint": "Скорость обучения Mirostat"},
            {"key": "--mirostat-ent", "default": "", "hint": "Целевая энтропия Mirostat"},
            {"key": "--seed", "default": "", "hint": "Seed генератора"},
        ],
    },
    {
        "id": "draft",
        "title": "Draft Model (Speculative Decoding)",
        "expanded": False,
        "params": [
            {"key": "--draft-model", "default": "", "hint": "Путь к draft-модели"},
            {"key": "--draft-max", "default": "", "hint": "Макс. draft-токенов"},
            {"key": "--draft-min", "default": "", "hint": "Мин. draft-токенов"},
            {"key": "--gpu-layers-draft", "default": "", "hint": "GPU-слои для draft-модели"},
        ],
    },
    {
        "id": "moe",
        "title": "MoE (Mixture of Experts)",
        "expanded": False,
        "params": [
            {"key": "--n-cpu-moe", "default": "", "hint": "Эксперты на CPU"},
            {"key": "--cpu-moe", "default": False, "hint": "Включить CPU-эксперты"},
        ],
    },
    {
        "id": "embeddings",
        "title": "Embeddings и Reranking",
        "expanded": False,
        "params": [
            {"key": "--embedding", "default": False, "hint": "Режим эмбеддингов"},
            {"key": "--reranking", "default": False, "hint": "Режим reranker"},
        ],
    },
    {
        "id": "server",
        "title": "Сервер",
        "expanded": False,
        "params": [
            {"key": "--timeout", "default": "", "hint": "Тайм-аут соединения"},
            {"key": "--path", "default": "", "hint": "Базовый URL-путь"},
            {"key": "--no-webui", "default": False, "hint": "Отключить встроенный WebUI"},
        ],
    },
    {
        "id": "security",
        "title": "Безопасность",
        "expanded": False,
        "params": [
            {"key": "--ssl-cert-file", "default": "", "hint": "Файл SSL-сертификата"},
            {"key": "--ssl-key-file", "default": "", "hint": "Файл SSL-ключа"},
            {"key": "--api-key", "default": "", "hint": "API-ключ авторизации"},
        ],
    },
    {
        "id": "diagnostics",
        "title": "Логирование и диагностика",
        "expanded": False,
        "params": [
            {"key": "--verbose", "default": False, "hint": "Подробные логи (-v)"},
            {"key": "--log-file", "default": "", "hint": "Запись журнала в файл"},
            {"key": "--log-format", "default": "", "hint": "Формат журналов (text, json…)"},
            {"key": "--metrics", "default": False, "hint": "Публикация метрик"},
            {"key": "--no-perf", "default": False, "hint": "Отключить статистику производительности"},
        ],
    },
    {
        "id": "backend_cuda",
        "title": "Backend: CUDA (NVIDIA)",
        "expanded": False,
        "backend": "CUDA",
        "hint": "Максимальная поддержка GPU. --device CUDA0, CUDA1…",
        "params": [
            {"key": "--device-cuda", "default": "", "hint": "Устройство CUDA (напр. CUDA0)", "maps_to": "--device"},
        ],
    },
    {
        "id": "backend_vulkan",
        "title": "Backend: Vulkan (NVIDIA/AMD/Intel)",
        "expanded": False,
        "backend": "Vulkan",
        "hint": "Универсальный backend. --device Vulkan0…",
        "params": [
            {"key": "--device-vulkan", "default": "", "hint": "Устройство Vulkan (напр. Vulkan0)", "maps_to": "--device"},
        ],
    },
    {
        "id": "backend_hip",
        "title": "Backend: HIP (AMD ROCm)",
        "expanded": False,
        "backend": "HIP",
        "hint": "AMD ROCm. --device HIP0…",
        "params": [
            {"key": "--device-hip", "default": "", "hint": "Устройство HIP (напр. HIP0)", "maps_to": "--device"},
        ],
    },
    {
        "id": "backend_metal",
        "title": "Backend: Metal (Apple)",
        "expanded": False,
        "backend": "Metal",
        "hint": "Только Apple Silicon",
        "params": [
            {"key": "--device-metal", "default": "", "hint": "Устройство Metal", "maps_to": "--device"},
        ],
    },
    {
        "id": "backend_sycl",
        "title": "Backend: SYCL (Intel GPU)",
        "expanded": False,
        "backend": "SYCL",
        "hint": "Преимущественно Intel GPU",
        "params": [
            {"key": "--device-sycl", "default": "", "hint": "Устройство SYCL", "maps_to": "--device"},
        ],
    },
]

BACKEND_DEVICE_KEYS = (
    "--device-cuda",
    "--device-vulkan",
    "--device-hip",
    "--device-metal",
    "--device-sycl",
)

# ================= llama-cli (интерактивный чат в терминале) =================
# Отдельный набор параметров: ключи могут совпадать с серверными
# (--ctx-size, --threads ...), но виджеты диалога CLI хранятся отдельно
# (self.cli_param_widgets) и сохраняются в config["cli_params"].

CLI_PARAM_GROUPS = [
    {
        "id": "cli_main",
        "title": "CLI: Основные",
        "expanded": True,
        "hint": "Модель берётся из поля диалога, остальное — флаги llama-cli",
        "params": [
            {"key": "--prompt", "default": "", "hint": "Стартовый промпт (-p)"},
            {"key": "--system-prompt", "default": "", "hint": "Системный промпт (-sys)"},
            {"key": "--file", "default": "", "hint": "Файл с промптом (-f)"},
            {"key": "--ctx-size", "default": "4096", "hint": "Размер контекста (-c)"},
            {"key": "--predict", "default": "", "hint": "Макс. новых токенов (-n)"},
            {"key": "--threads", "default": "", "hint": "Потоки CPU (-t)"},
            {"key": "--n-gpu-layers", "default": "", "hint": "Слои на GPU (-ngl)"},
            {"key": "--device", "default": "", "hint": "Устройство (CUDA0, Vulkan0…)"},
            {"key": "--interactive", "default": False, "hint": "Интерактивный режим (-i)"},
            {"key": "--conversation", "default": False, "hint": "Режим диалога (-cnv)"},
            {"key": "--reverse-prompt", "default": "", "hint": "Строка возврата управления (-r)"},
            {"key": "--color", "default": "auto", "choices": ["auto", "on", "off"], "hint": "Цветной вывод (-co)"},
            {"key": "-lv", "default": False, "flag_value": "4", "hint": "Детализация логов (-lv 4)"},
            {"key": "--reasoning", "default": "auto", "choices": ["auto", "on", "off"], "hint": "Reasoning/thinking в чате (on/off/auto)"},
        ],
    },
    {
        "id": "cli_gen",
        "title": "CLI: Генерация",
        "expanded": False,
        "params": [
            {"key": "--temp", "default": "", "hint": "Температура"},
            {"key": "--top-k", "default": "", "hint": "Top-K sampling"},
            {"key": "--top-p", "default": "", "hint": "Top-P sampling"},
            {"key": "--min-p", "default": "", "hint": "Min-P sampling"},
            {"key": "--repeat-penalty", "default": "", "hint": "Штраф за повторение"},
            {"key": "--repeat-last-n", "default": "", "hint": "Окно повторов"},
            {"key": "--seed", "default": "", "hint": "Seed генератора"},
            {"key": "--flash-attn", "default": "auto", "choices": ["auto", "on", "off"], "hint": "Flash Attention (-fa)"},
        ],
    },
]


def build_default_cli_params():
    params = {}
    for group in CLI_PARAM_GROUPS:
        for spec in group["params"]:
            params[spec["key"]] = spec["default"]
    return params


CLI_LEGACY_ALIASES = {
    "--prompt-file": "--file",
}

# Старые булевы значения tri-state параметров (--color/--flash-attn/
# --reasoning раньше были чекбоксами) маппятся в on/off/auto: True —
# явное "on", False — дефолтное поведение "auto" (флаг раньше просто
# не передавался).
CLI_BOOL_TRISTATE_KEYS = ("--color", "--flash-attn", "--reasoning")


def normalize_loaded_cli_params(loaded_params):
    if not isinstance(loaded_params, dict):
        return {}
    incoming = dict(loaded_params)
    for old_key, new_key in CLI_LEGACY_ALIASES.items():
        if old_key in incoming:
            if new_key not in incoming:
                incoming[new_key] = incoming.pop(old_key)
            else:
                incoming.pop(old_key, None)
    for key in CLI_BOOL_TRISTATE_KEYS:
        if isinstance(incoming.get(key), bool):
            incoming[key] = "on" if incoming[key] else "auto"
    normalized = {}
    for group in CLI_PARAM_GROUPS:
        for spec in group["params"]:
            key = spec["key"]
            default = spec["default"]
            if key in incoming:
                value = incoming[key]
                if isinstance(default, bool):
                    normalized[key] = bool(value)
                else:
                    normalized[key] = str(value)
            else:
                normalized[key] = default
    return normalized


# ================= llama-bench (замер производительности) =================
# Отдельное окно по типу CLI: путь к бинарнику + модель берутся из полей
# диалога, остальное — флаги llama-bench. Ключи используются длинные
# (--n-prompt вместо -p и т.д.), bench принимает обе формы.
# Значения могут быть списками через запятую (напр. "128,256") — bench
# сам прогоняет все комбинации.

BENCH_OUTPUT_CHOICES = ["md", "csv", "json", "jsonl", "sql"]

BENCH_PARAM_GROUPS = [
    {
        "id": "bench_main",
        "title": "Bench: Тест",
        "expanded": True,
        "hint": "Что замеряем: pp — обработка промпта, tg — генерация",
        "params": [
            {"key": "--n-prompt", "default": "512", "hint": "Промпт-токены pp (-p)"},
            {"key": "--n-gen", "default": "128", "hint": "Генерация токенов tg (-n)"},
            {"key": "-pg", "default": "", "hint": "Комбо-тест pp,tg (напр. 512,128)"},
            {"key": "--n-depth", "default": "0", "hint": "Глубина контекста KV (-d)"},
            {"key": "--repetitions", "default": "5", "hint": "Повторы каждого теста (-r)"},
            {"key": "--output", "default": "md", "choices": BENCH_OUTPUT_CHOICES, "hint": "Формат вывода (-o)"},
            {"key": "--progress", "default": False, "hint": "Индикатор прогресса"},
            {"key": "--no-warmup", "default": False, "hint": "Пропустить warmup-прогоны"},
            {"key": "--verbose", "default": False, "hint": "Подробный вывод (-v)"},
        ],
    },
    {
        "id": "bench_compute",
        "title": "Bench: Вычисления",
        "expanded": False,
        "hint": "Потоки, GPU-слои, батчи — как у сервера",
        "params": [
            {"key": "--threads", "default": "", "hint": "Потоки CPU (-t)"},
            {"key": "--n-gpu-layers", "default": "", "hint": "Слои на GPU (-ngl)"},
            {"key": "--flash-attn", "default": "auto", "choices": ["auto", "on", "off"], "hint": "Flash Attention (-fa)"},
            {"key": "--cache-type-k", "default": "", "choices": ["", "f32", "f16", "bf16", "q8_0", "q4_0", "q4_1", "q8_1", "iq4_nl"], "hint": "Формат Key Cache (-ctk)"},
            {"key": "--cache-type-v", "default": "", "choices": ["", "f32", "f16", "bf16", "q8_0", "q4_0", "q4_1", "q8_1", "iq4_nl"], "hint": "Формат Value Cache (-ctv)"},
            {"key": "--batch-size", "default": "", "hint": "Размер batch (-b)"},
            {"key": "--ubatch-size", "default": "", "hint": "Размер micro batch (-ub)"},
            {"key": "--device", "default": "", "hint": "Устройство (CUDA0, Vulkan0…)"},
            {"key": "--split-mode", "default": "", "hint": "Распределение между GPU (-sm)"},
            {"key": "--no-kv-offload", "default": False, "hint": "Не переносить KV Cache на GPU"},
        ],
    },
]


def build_default_bench_params():
    params = {}
    for group in BENCH_PARAM_GROUPS:
        for spec in group["params"]:
            params[spec["key"]] = spec["default"]
    return params


BENCH_BOOL_TRISTATE_KEYS = ("--flash-attn",)


def normalize_loaded_bench_params(loaded_params):
    if not isinstance(loaded_params, dict):
        return {}
    incoming = dict(loaded_params)
    for key in BENCH_BOOL_TRISTATE_KEYS:
        if isinstance(incoming.get(key), bool):
            incoming[key] = "on" if incoming[key] else "auto"
    normalized = {}
    for group in BENCH_PARAM_GROUPS:
        for spec in group["params"]:
            key = spec["key"]
            default = spec["default"]
            if key in incoming:
                value = incoming[key]
                if isinstance(default, bool):
                    normalized[key] = bool(value)
                else:
                    normalized[key] = str(value)
            else:
                normalized[key] = default
    return normalized


def build_default_params():
    params = {}
    for group in PARAM_GROUPS:
        for spec in group["params"]:
            params[spec["key"]] = spec["default"]
    return params


def normalize_loaded_params(loaded_params):
    if not isinstance(loaded_params, dict):
        return {}

    normalized = dict(loaded_params)
    for old_key, new_key in LEGACY_PARAM_ALIASES.items():
        if old_key in normalized and new_key not in normalized:
            normalized[new_key] = normalized.pop(old_key)

    # Миграция: --no-mmap и --mlock заменены в llama-server на --load-mode
    if "--load-mode" not in normalized:
        no_mmap = bool(normalized.get("--no-mmap", False))
        mlock = bool(normalized.get("--mlock", False))
        if mlock:
            normalized["--load-mode"] = "mlock" if no_mmap else "mmap+mlock"
        else:
            normalized["--load-mode"] = "none" if no_mmap else "auto"
    normalized.pop("--no-mmap", None)
    normalized.pop("--mlock", None)

    # Миграция: --reasoning раньше был чекбоксом (bool) — маппим
    # в tri-state on/off/auto: True — явное "on", False — "auto".
    if isinstance(normalized.get("--reasoning"), bool):
        normalized["--reasoning"] = "on" if normalized["--reasoning"] else "auto"

    device_value = normalized.get("--device", "")
    if device_value:
        lower = device_value.lower()
        if lower.startswith("cuda"):
            normalized["--device-cuda"] = device_value
        elif lower.startswith("vulkan"):
            normalized["--device-vulkan"] = device_value
        elif lower.startswith("hip"):
            normalized["--device-hip"] = device_value
        elif lower.startswith("metal"):
            normalized["--device-metal"] = device_value
        elif lower.startswith("sycl"):
            normalized["--device-sycl"] = device_value

    return normalized
