"""Группы параметров llama-server по справочнику (Глава 45)."""

LEGACY_PARAM_ALIASES = {
    "-ncmoe": "--n-cpu-moe",
    "--spec-draft-n-max": "--draft-max",
    "-mlock": "--mlock",
}

PARAM_GROUPS = [
    {
        "id": "main",
        "title": "Основные",
        "expanded": True,
        "hint": "Наиболее часто используемые параметры",
        "params": [
            {"key": "--ctx-size", "default": "16384", "hint": "Размер контекста"},
            {"key": "--n-gpu-layers", "default": "99", "hint": "Слои на GPU (-ngl)"},
            {"key": "-fa", "default": "on", "hint": "Flash Attention (--flash-attn)"},
            {"key": "--threads", "default": "", "hint": "Потоки CPU (-t)"},
            {"key": "--cache-type-k", "default": "q8_0", "hint": "Формат Key Cache"},
            {"key": "--cache-type-v", "default": "q8_0", "hint": "Формат Value Cache"},
            {"key": "--no-mmap", "default": True, "hint": "Отключить memory mapping"},
            {"key": "--mlock", "default": False, "hint": "Блокировка модели в RAM"},
            {"key": "--host", "default": "0.0.0.0", "hint": "IP-адрес сервера"},
            {"key": "--port", "default": "18080", "hint": "TCP-порт"},
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
