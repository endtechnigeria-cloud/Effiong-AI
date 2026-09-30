"""
EFFIONG AI - central configuration
==================================
One place that knows how to read settings and API keys.

Lookup order for every name:
    1. real environment variable   (Hugging Face Spaces, Docker, Render, local shell)
    2. Streamlit secrets           (Streamlit Community Cloud "Secrets" box / .streamlit/secrets.toml)

Nothing in here imports Streamlit at module import time, so the same engine can be
used by the FastAPI backend (main.py) without Streamlit installed.

Multiple keys per provider are supported for automatic "next free token" rotation:
    GEMINI_API_KEY   = "key-one"
    GEMINI_API_KEY_2 = "key-two"
    GEMINI_API_KEY_3 = "key-three"
    GEMINI_API_KEYS  = "key-four,key-five"        (comma separated list also works)
"""
from __future__ import annotations

import os
import threading
from typing import Dict, List

APP_NAME = "Effiong AI"
APP_TAGLINE = "Sovereign Wisdom Engine"
APP_VERSION = "3.0.0"

# Names that different people / older files used for the same secret.
ALIASES: Dict[str, List[str]] = {
    "OPENROUTER_API_KEY": ["OPENROUTER_KEY"],
    "OPENROUTER_KEY": ["OPENROUTER_API_KEY"],
    "XAI_API_KEY": ["GROK_API_KEY"],
    "GROK_API_KEY": ["XAI_API_KEY"],
    "HF_TOKEN": ["HUGGINGFACE_API_KEY", "HF_API_KEY", "HUGGINGFACE_TOKEN"],
    "GEMINI_API_KEY": ["GOOGLE_API_KEY"],
    "SUPABASE_KEY": ["SUPABASE_ANON_KEY", "SUPABASE_PUBLISHABLE_KEY"],
    "GITHUB_TOKEN": ["GH_TOKEN"],
    "ZENODO_TOKEN": ["ZENODO_ACCESS_TOKEN"],
}

_lock = threading.Lock()
_flat_cache: Dict[str, str] | None = None


def _flatten(data, out: Dict[str, str], prefix: str = "") -> None:
    for k, v in (data or {}).items():
        name = str(k).upper()
        if isinstance(v, dict):
            _flatten(v, out, f"{prefix}{name}_")
            # also expose un-prefixed names for nested tables ([gemini] key = "...")
            for sk, sv in v.items():
                if isinstance(sv, (str, int, float, bool)):
                    out.setdefault(str(sk).upper(), str(sv))
        elif isinstance(v, (str, int, float, bool)):
            out[f"{prefix}{name}"] = str(v)


def _streamlit_secrets() -> Dict[str, str]:
    """Read st.secrets defensively (it raises when no secrets file exists)."""
    global _flat_cache
    with _lock:
        if _flat_cache is not None:
            return _flat_cache
        flat: Dict[str, str] = {}
        try:
            import streamlit as st  # noqa: WPS433 (optional dependency)

            try:
                raw = dict(st.secrets)
            except Exception:
                raw = {}
            _flatten(raw, flat)
        except Exception:
            flat = {}
        _flat_cache = flat
        return flat


def refresh() -> None:
    """Forget cached secrets (used by tests and after secrets change)."""
    global _flat_cache
    with _lock:
        _flat_cache = None


def get(name: str, default: str = "") -> str:
    """Return a setting as a stripped string ('' / default when not set)."""
    candidates = [name] + ALIASES.get(name, [])
    for cand in candidates:
        val = os.environ.get(cand)
        if val is not None and str(val).strip():
            return str(val).strip()
    secrets = _streamlit_secrets()
    for cand in candidates:
        val = secrets.get(cand.upper())
        if val is not None and str(val).strip():
            return str(val).strip()
    return default


def get_bool(name: str, default: bool = False) -> bool:
    raw = get(name, "")
    if raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "y"}


def get_int(name: str, default: int) -> int:
    try:
        return int(float(get(name, str(default))))
    except (TypeError, ValueError):
        return default


def get_float(name: str, default: float) -> float:
    try:
        return float(get(name, str(default)))
    except (TypeError, ValueError):
        return default


def get_keys(base: str) -> List[str]:
    """
    All configured keys for a provider, in order, de-duplicated.
    base='GEMINI_API_KEY' -> GEMINI_API_KEY, GEMINI_API_KEY_2.._9, GEMINI_API_KEYS(csv)
    """
    keys: List[str] = []

    def add(value: str) -> None:
        value = (value or "").strip().strip('"').strip("'")
        if value and value not in keys and not value.lower().startswith(("your_", "paste_", "xxx", "changeme")):
            keys.append(value)

    add(get(base))
    for i in range(2, 10):
        add(get(f"{base}_{i}"))
    for item in get(f"{base}S").split(","):
        add(item)
    # aliases (single key only, to avoid double counting the same secret)
    for alt in ALIASES.get(base, []):
        add(get(alt))
    return keys


def load_secrets_into_env() -> int:
    """
    Copy Streamlit secrets into os.environ (without overwriting real env vars) so that
    libraries which only look at the environment (supabase, pinecone, ...) work too.
    Returns how many variables were added.
    """
    added = 0
    for k, v in _streamlit_secrets().items():
        if k not in os.environ and v:
            os.environ[k] = v
            added += 1
    return added


# ----------------------------------------------------------------------------------
# Runtime limits (Security & Resource Shielding Matrix) - all overridable via secrets
# ----------------------------------------------------------------------------------
def limits() -> Dict[str, float]:
    return {
        "min_seconds_between_requests": get_float("MIN_SECONDS_BETWEEN_REQUESTS", 1.2),
        "max_requests_per_minute": get_int("MAX_REQUESTS_PER_MINUTE", 12),
        "daily_chat_limit_per_user": get_int("DAILY_CHAT_LIMIT_PER_USER", 150),
        "daily_media_limit_per_user": get_int("DAILY_MEDIA_LIMIT_PER_USER", 25),
        "daily_upload_mb_per_user": get_int("DAILY_UPLOAD_MB_PER_USER", 200),
        "global_daily_limit": get_int("GLOBAL_DAILY_LIMIT", 5000),
        "max_input_chars": get_int("MAX_INPUT_CHARS", 12000),
        "max_files_per_message": get_int("MAX_FILES_PER_MESSAGE", 10),
        "max_file_mb": get_int("MAX_FILE_MB", 100),
        "request_deadline_seconds": get_int("REQUEST_DEADLINE_SECONDS", 110),
        "max_provider_calls_per_request": get_int("MAX_PROVIDER_CALLS_PER_REQUEST", 14),
    }
