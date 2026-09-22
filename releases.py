"""Загрузка списка сборок llama.cpp с GitHub Releases API."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


def _tr(language: str, key: str, **kwargs) -> str:
    from i18n import TRANSLATIONS
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    lang = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    text = entry.get(lang, entry.get(DEFAULT_LANGUAGE, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass
    return text

GITHUB_API_RELEASES = "https://api.github.com/repos/ggml-org/llama.cpp/releases"
GITHUB_DOWNLOAD_BASE = "https://github.com/ggml-org/llama.cpp/releases/download"
USER_AGENT = "LLM-Server-Controller/0.1 (+https://github.com/ggml-org/llama.cpp)"

FALLBACK_TAG = "b9870"
FALLBACK_ASSETS: List[Dict[str, Any]] = [
    {
        "label": "Windows x64 (Vulkan)",
        "asset": f"llama-{FALLBACK_TAG}-bin-win-vulkan-x64.zip",
        "dll_asset": None,
        "arch": "x64",
        "backend": "Vulkan",
        "recommended": True,
        "browser_download_url": f"{GITHUB_DOWNLOAD_BASE}/{FALLBACK_TAG}/llama-{FALLBACK_TAG}-bin-win-vulkan-x64.zip",
    },
    {
        "label": "Windows x64 (CPU)",
        "asset": f"llama-{FALLBACK_TAG}-bin-win-cpu-x64.zip",
        "dll_asset": None,
        "arch": "x64",
        "backend": "CPU",
        "recommended": False,
        "browser_download_url": f"{GITHUB_DOWNLOAD_BASE}/{FALLBACK_TAG}/llama-{FALLBACK_TAG}-bin-win-cpu-x64.zip",
    },
    {
        "label": "Windows x64 (CUDA 12)",
        "asset": f"llama-{FALLBACK_TAG}-bin-win-cuda-12.4-x64.zip",
        "dll_asset": f"cudart-llama-bin-win-cuda-12.4-x64.zip",
        "arch": "x64",
        "backend": "CUDA 12",
        "recommended": False,
        "browser_download_url": f"{GITHUB_DOWNLOAD_BASE}/{FALLBACK_TAG}/llama-{FALLBACK_TAG}-bin-win-cuda-12.4-x64.zip",
    },
    {
        "label": "Windows x64 (CUDA 13)",
        "asset": f"llama-{FALLBACK_TAG}-bin-win-cuda-13.3-x64.zip",
        "dll_asset": f"cudart-llama-bin-win-cuda-13.3-x64.zip",
        "arch": "x64",
        "backend": "CUDA 13",
        "recommended": False,
        "browser_download_url": f"{GITHUB_DOWNLOAD_BASE}/{FALLBACK_TAG}/llama-{FALLBACK_TAG}-bin-win-cuda-13.3-x64.zip",
    },
    {
        "label": "Windows x64 (HIP)",
        "asset": f"llama-{FALLBACK_TAG}-bin-win-hip-radeon-x64.zip",
        "dll_asset": None,
        "arch": "x64",
        "backend": "HIP",
        "recommended": False,
        "browser_download_url": f"{GITHUB_DOWNLOAD_BASE}/{FALLBACK_TAG}/llama-{FALLBACK_TAG}-bin-win-hip-radeon-x64.zip",
    },
]

FALLBACK_LINUX_ASSETS: List[Dict[str, Any]] = [
    {"label": "Linux x64 (Vulkan)", "asset": f"llama-{FALLBACK_TAG}-bin-ubuntu-vulkan-x64.tar.gz", "dll_asset": None, "arch": "x64", "backend": "Vulkan", "recommended": True, "browser_download_url": f"{GITHUB_DOWNLOAD_BASE}/{FALLBACK_TAG}/llama-{FALLBACK_TAG}-bin-ubuntu-vulkan-x64.tar.gz"},
    {"label": "Linux x64 (CPU)", "asset": f"llama-{FALLBACK_TAG}-bin-ubuntu-x64.tar.gz", "dll_asset": None, "arch": "x64", "backend": "CPU", "recommended": False, "browser_download_url": f"{GITHUB_DOWNLOAD_BASE}/{FALLBACK_TAG}/llama-{FALLBACK_TAG}-bin-ubuntu-x64.tar.gz"},
]



def _http_get_json(url: str, timeout: int = 30) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8"))


def fetch_latest_release_tag(timeout: int = 30) -> str:
    data = _http_get_json(f"{GITHUB_API_RELEASES}/latest", timeout=timeout)
    tag = data.get("tag_name") or data.get("name") or ""
    if not tag:
        raise RuntimeError("GitHub API did not return tag_name for latest release")
    return str(tag)


APP_GITHUB_REPO = "dmitrymaxs/LLM_Server_Controller"


def fetch_github_latest_release(repo: str, timeout: int = 20) -> Dict[str, str]:
    """Возвращает latest release произвольного GitHub-репо: tag, url, name."""
    data = _http_get_json(f"https://api.github.com/repos/{repo}/releases/latest", timeout=timeout)
    tag = str(data.get("tag_name") or data.get("name") or "").strip()
    if not tag:
        raise RuntimeError("GitHub API did not return tag_name for latest release")
    return {
        "tag": tag,
        "url": str(data.get("html_url") or f"https://github.com/{repo}/releases"),
        "name": str(data.get("name") or tag),
    }


def parse_version_tuple(text: str) -> Tuple[int, ...]:
    """Извлекает числовой кортеж из тега: v0.1.8 -> (0, 1, 8), b9870 -> (9870,)."""
    return tuple(int(part) for part in re.findall(r"\d+", text or ""))


def parse_llama_version_output(output: str) -> str:
    """Вытаскивает тег сборки (bNNNN) из вывода `llama-server --version`.

    Примеры входов: "version: 9870 (abc123...)", "llama.cpp b9870", "build 9870".
    Возвращает "b9870" или "" если распознать не удалось.
    """
    text = output or ""
    match = re.search(r"\bb\s*(\d{3,})\b", text, re.IGNORECASE)
    if match:
        return f"b{match.group(1)}"
    for pattern in (r"version\s*[:\-]?\s*(\d{3,})", r"build\s+(\d{3,})"):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"b{match.group(1)}"
    return ""


def get_llama_server_version(exe_path: str, timeout: int = 15) -> str:
    """Запускает `llama-server --version` и возвращает тег сборки (bNNNN).

    Путь берётся из конфигурации, поэтому работает и для сервера,
    установленного вручную в нестандартную папку. При любой ошибке — "".
    """
    import os
    import subprocess
    import sys

    if not exe_path or not os.path.exists(exe_path):
        return ""
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    try:
        result = subprocess.run(
            [exe_path, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo,
            timeout=timeout,
        )
        output = (result.stdout or "") + "\n" + (result.stderr or "")
        return parse_llama_version_output(output)
    except (OSError, subprocess.SubprocessError, ValueError):
        return ""


def is_newer_tag(latest_tag: str, current_tag: str) -> bool:
    """True, если latest_tag новее current_tag. Несравнимые, но разные теги — тоже True."""
    if not latest_tag or latest_tag == current_tag:
        return False
    latest_ver = parse_version_tuple(latest_tag)
    current_ver = parse_version_tuple(current_tag)
    if latest_ver and current_ver:
        return latest_ver > current_ver
    return True


def fetch_recent_releases(timeout: int = 30, per_page: int = 40) -> List[Dict[str, Any]]:
    return _http_get_json(f"{GITHUB_API_RELEASES}?per_page={per_page}", timeout=timeout)


def _pick_release_with_assets(
    releases: List[Dict[str, Any]],
    parser,
) -> Optional[Dict[str, Any]]:
    """Возвращает самый новый релиз, у которого есть подходящие сборки.

    /releases/latest у llama.cpp указывает на старый стабильный тег (v0.x),
    к которому бинарные архивы не прикладываются; актуальные сборки живут
    в свежих пре-релизах (bNNNNN), поэтому ищем по списку от нового к старому.
    """
    for release in releases:
        if release.get("draft"):
            continue
        if parser(release):
            return release
    return None


def fetch_release(tag: str, timeout: int = 30) -> Dict[str, Any]:
    tag = tag.strip()
    if not tag:
        raise ValueError("Empty release tag")
    return _http_get_json(f"{GITHUB_API_RELEASES}/tags/{tag}", timeout=timeout)


def _classify_windows_asset(name: str) -> Optional[Dict[str, Any]]:
    lower = name.lower()
    if not lower.endswith(".zip"):
        return None
    if lower.startswith("cudart-"):
        return None
    if "win" not in lower:
        return None
    if not (lower.startswith("llama-") and "-bin-win-" in lower):
        if "bin-win-" not in lower:
            return None

    arch = "arm64" if "arm64" in lower else "x64"
    recommended = False
    backend = "Unknown"
    label = name

    if "vulkan" in lower:
        backend = "Vulkan"
        label = f"Windows {arch} (Vulkan)"
        recommended = arch == "x64"
    elif "cuda-13" in lower or "cuda_13" in lower:
        backend = "CUDA 13"
        m = re.search(r"cuda[_-]?(\d+(?:\.\d+)*)", lower)
        ver = m.group(1) if m else "13"
        label = f"Windows {arch} (CUDA {ver})"
    elif "cuda-12" in lower or "cuda_12" in lower or "cuda" in lower:
        backend = "CUDA 12"
        m = re.search(r"cuda[_-]?(\d+(?:\.\d+)*)", lower)
        ver = m.group(1) if m else "12"
        label = f"Windows {arch} (CUDA {ver})"
    elif "hip" in lower or "rocm" in lower or "radeon" in lower:
        backend = "HIP"
        label = f"Windows {arch} (HIP)"
    elif "sycl" in lower:
        backend = "SYCL"
        label = f"Windows {arch} (SYCL)"
    elif "openvino" in lower:
        backend = "OpenVINO"
        label = f"Windows {arch} (OpenVINO)"
    elif "opencl" in lower:
        backend = "OpenCL"
        label = f"Windows {arch} (OpenCL)"
    elif "cpu" in lower:
        backend = "CPU"
        label = f"Windows {arch} (CPU)"
    else:
        backend = "Other"
        label = f"Windows {arch} ({name})"

    return {
        "label": label,
        "asset": name,
        "dll_asset": None,
        "arch": arch,
        "backend": backend,
        "recommended": recommended,
    }


def _match_cudart(assets_by_name: Dict[str, Dict[str, Any]], main_asset: str) -> Optional[str]:
    lower = main_asset.lower()
    m = re.search(r"cuda[_-](\d+(?:\.\d+)*)", lower)
    if not m:
        return None
    version = m.group(1)
    candidates = []
    for name in assets_by_name:
        n = name.lower()
        if not n.startswith("cudart-"):
            continue
        if "win" not in n:
            continue
        if version in n:
            candidates.append(name)
    if candidates:
        for name in candidates:
            if "x64" in name.lower():
                return name
        return candidates[0]
    for name in assets_by_name:
        n = name.lower()
        if n.startswith("cudart-") and "win" in n:
            return name
    return None


def parse_windows_assets_from_release(release: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_assets = release.get("assets") or []
    by_name: Dict[str, Dict[str, Any]] = {}
    for item in raw_assets:
        name = item.get("name") or ""
        if not name:
            continue
        by_name[name] = item

    result: List[Dict[str, Any]] = []
    seen_labels: set = set()

    for name, item in sorted(by_name.items(), key=lambda x: x[0].lower()):
        classified = _classify_windows_asset(name)
        if not classified:
            continue
        dll = _match_cudart(by_name, name) if "cuda" in classified["backend"].lower() else None
        classified["dll_asset"] = dll
        classified["browser_download_url"] = item.get("browser_download_url") or (
            f"{GITHUB_DOWNLOAD_BASE}/{release.get('tag_name', '')}/{name}"
        )
        classified["size"] = item.get("size") or 0
        label = classified["label"]
        if label in seen_labels:
            classified["label"] = f"{label} [{name}]"
        seen_labels.add(classified["label"])
        result.append(classified)

    for asset in result:
        if asset.get("backend") == "Vulkan" and asset.get("arch") == "x64":
            asset["recommended"] = True
            break

    def sort_key(a: Dict[str, Any]):
        order = {
            "Vulkan": 0,
            "CUDA 13": 1,
            "CUDA 12": 2,
            "HIP": 3,
            "SYCL": 4,
            "OpenVINO": 5,
            "OpenCL": 6,
            "CPU": 7,
        }
        backend = a.get("backend", "Other")
        base = 0 if a.get("recommended") else 10
        return (base, order.get(backend, 50), a.get("label", ""))

    result.sort(key=sort_key)
    return result

def _classify_linux_asset(name: str) -> Optional[Dict[str, Any]]:
    lower = name.lower()
    if not lower.endswith(".tar.gz") or "ubuntu" not in lower or "x64" not in lower:
        return None
    if "vulkan" in lower:
        return {"label": "Linux x64 (Vulkan)", "asset": name, "dll_asset": None, "arch": "x64", "backend": "Vulkan", "recommended": True}
    if re.search(r"-bin-ubuntu-x64\.tar\.gz$", lower):
        return {"label": "Linux x64 (CPU)", "asset": name, "dll_asset": None, "arch": "x64", "backend": "CPU", "recommended": False}
    return None

def parse_linux_assets_from_release(release: Dict[str, Any]) -> List[Dict[str, Any]]:
    result = []
    for item in release.get("assets") or []:
        name = item.get("name") or ""
        classified = _classify_linux_asset(name)
        if not classified:
            continue
        classified["browser_download_url"] = item.get("browser_download_url") or f"{GITHUB_DOWNLOAD_BASE}/{release.get('tag_name', '')}/{name}"
        classified["size"] = item.get("size") or 0
        result.append(classified)
    result.sort(key=lambda a: (0 if a.get("recommended") else 10, a.get("label", "")))
    return result

def fetch_linux_assets(tag: Optional[str] = None, timeout: int = 30, language: str = DEFAULT_LANGUAGE) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
    try:
        if not tag:
            releases = fetch_recent_releases(timeout=timeout)
            release = _pick_release_with_assets(releases, parse_linux_assets_from_release)
            if release is None:
                release = _http_get_json(f"{GITHUB_API_RELEASES}/latest", timeout=timeout)
        else:
            release = fetch_release(tag, timeout=timeout)
        actual_tag = str(release.get("tag_name") or tag)
        assets = parse_linux_assets_from_release(release)
        if not assets:
            return actual_tag, [dict(a) for a in FALLBACK_LINUX_ASSETS], _tr(language, "rels_no_linux_builds", tag=actual_tag)
        return actual_tag, assets, None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError, RuntimeError) as exc:
        assets = []
        for item in FALLBACK_LINUX_ASSETS:
            copy = dict(item)
            if tag and tag != FALLBACK_TAG:
                copy["asset"] = copy["asset"].replace(FALLBACK_TAG, tag)
                copy["browser_download_url"] = f"{GITHUB_DOWNLOAD_BASE}/{tag}/{copy['asset']}"
            assets.append(copy)
        return tag or FALLBACK_TAG, assets, _tr(language, "rels_fetch_linux_failed", error=exc)



def fetch_windows_assets(
    tag: Optional[str] = None,
    timeout: int = 30,
    language: str = DEFAULT_LANGUAGE,
) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
    try:
        if not tag:
            releases = fetch_recent_releases(timeout=timeout)
            release = _pick_release_with_assets(releases, parse_windows_assets_from_release)
            if release is None:
                release = _http_get_json(f"{GITHUB_API_RELEASES}/latest", timeout=timeout)
        else:
            release = fetch_release(tag, timeout=timeout)
        actual_tag = str(release.get("tag_name") or tag)
        assets = parse_windows_assets_from_release(release)
        if not assets:
            return actual_tag, [dict(a) for a in FALLBACK_ASSETS], (
                _tr(language, "rels_no_win_builds", tag=actual_tag)
            )
        return actual_tag, assets, None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError, RuntimeError) as exc:
        assets = []
        for item in FALLBACK_ASSETS:
            copy = dict(item)
            if tag and tag != FALLBACK_TAG:
                copy["asset"] = copy["asset"].replace(FALLBACK_TAG, tag)
                if copy.get("dll_asset"):
                    copy["dll_asset"] = copy["dll_asset"]
                copy["browser_download_url"] = (
                    f"{GITHUB_DOWNLOAD_BASE}/{tag}/{copy['asset']}"
                )
            assets.append(copy)
        used_tag = tag or FALLBACK_TAG
        return used_tag, assets, _tr(language, "rels_fetch_win_failed", error=exc)


def build_download_url(tag: str, asset_name: str, asset_entry: Optional[Dict[str, Any]] = None) -> str:
    if asset_entry and asset_entry.get("browser_download_url"):
        return asset_entry["browser_download_url"]
    return f"{GITHUB_DOWNLOAD_BASE}/{tag}/{asset_name}"