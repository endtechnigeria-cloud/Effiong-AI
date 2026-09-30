"""
EFFIONG AI - Failover Orchestration & High Availability
=======================================================
Rules this module enforces for the whole system:

* An optional library or provider that fails must NEVER take the portal down.
* Every failure is isolated, recorded (with a reason) and flagged for the operator.
* The main portal keeps answering using whatever is still alive.

Usage
-----
    from src.core.health import safe_import, guarded, HEALTH

    docx = safe_import("docx", component="word-export")     # None if the library is broken/missing

    @guarded("search", default="")
    def risky(): ...
"""
from __future__ import annotations

import functools
import importlib
import json
import os
import threading
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

OPERATOR_LOG_DIR = os.environ.get("EFFIONG_LOG_DIR", "operator_logs")
_MAX_LOG_BYTES = 1_000_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class HealthRegistry:
    """Thread-safe registry of component states: ok | degraded | down."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._components: Dict[str, Dict[str, Any]] = {}

    # -- state changes ----------------------------------------------------------
    def ok(self, component: str, detail: str = "") -> None:
        with self._lock:
            entry = self._components.setdefault(component, {"failures": 0})
            entry.update(status="ok", detail=detail, updated=_now())

    def flag(self, component: str, reason: str, status: str = "degraded") -> None:
        """Mark a component as broken and tell the operator (log file + registry)."""
        with self._lock:
            entry = self._components.setdefault(component, {"failures": 0})
            entry["failures"] = entry.get("failures", 0) + 1
            entry.update(status=status, detail=str(reason)[:400], updated=_now())
        write_operator_log("component_flagged", {"component": component, "status": status, "reason": str(reason)[:400]})

    # -- read -------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {k: dict(v) for k, v in sorted(self._components.items())}

    def degraded(self) -> Dict[str, Dict[str, Any]]:
        return {k: v for k, v in self.snapshot().items() if v.get("status") != "ok"}


HEALTH = HealthRegistry()

_log_lock = threading.Lock()


def write_operator_log(event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    """Append one JSON line to operator_logs/events.jsonl (never raises)."""
    try:
        os.makedirs(OPERATOR_LOG_DIR, exist_ok=True)
        path = os.path.join(OPERATOR_LOG_DIR, "events.jsonl")
        line = json.dumps({"ts": _now(), "event": event, **(payload or {})}, ensure_ascii=False)
        with _log_lock:
            if os.path.exists(path) and os.path.getsize(path) > _MAX_LOG_BYTES:
                os.replace(path, path + ".1")
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    except Exception:
        pass  # logging must never be the thing that breaks the app


def read_operator_log(limit: int = 100) -> list:
    path = os.path.join(OPERATOR_LOG_DIR, "events.jsonl")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()[-limit:]
        return [json.loads(x) for x in lines if x.strip()]
    except Exception:
        return []


def safe_import(module_name: str, component: Optional[str] = None, attr: Optional[str] = None) -> Any:
    """
    Import a module (or one attribute of it). Returns None instead of raising and flags the
    component as degraded, so the caller can fall back to another tier.
    """
    component = component or module_name
    try:
        module = importlib.import_module(module_name)
        HEALTH.ok(component, f"{module_name} loaded")
        return getattr(module, attr) if attr else module
    except Exception as exc:  # ImportError, OSError from native libs, version clashes ...
        HEALTH.flag(component, f"import failed: {module_name}: {exc.__class__.__name__}: {exc}")
        return None


def guarded(component: str, default: Any = None, log_traceback: bool = False) -> Callable:
    """Decorator: run the function, swallow + record any exception, return `default`."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                detail = f"{fn.__name__}: {exc.__class__.__name__}: {exc}"
                if log_traceback:
                    detail += "\n" + traceback.format_exc(limit=4)
                HEALTH.flag(component, detail)
                return default(*args, **kwargs) if callable(default) else default

        return wrapper

    return decorator


class Timer:
    """Tiny helper: with Timer() as t: ...; t.seconds"""

    def __enter__(self) -> "Timer":
        self.start = time.time()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.seconds = time.time() - self.start
