"""
EFFIONG AI - Security & Resource Shielding Matrix
=================================================
Protects the free-tier tokens and the host from runaway scripts, loops and abuse.

* RateGuard      - per-user throttling, per-minute burst cap, per-user daily limits, global daily cap
* ExecutionBudget- hard deadline + maximum number of provider calls for ONE request (stops loops)
* safe_get       - HTTP fetch that refuses private / local addresses (SSRF protection) and caps size
* sanitize_text  - strips control characters and caps length before anything reaches a model
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import threading
import time
from collections import defaultdict, deque
from datetime import date
from typing import Deque, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests

from src import config
from src.core.health import HEALTH, OPERATOR_LOG_DIR, write_operator_log

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text(text: str, max_chars: Optional[int] = None) -> str:
    text = _CONTROL_CHARS.sub("", text or "")
    limit = max_chars or int(config.limits()["max_input_chars"])
    return text[:limit].strip()


# --------------------------------------------------------------------------------------
# Rate / quota guard
# --------------------------------------------------------------------------------------
class RateGuard:
    """
    kinds:  chat | media | upload_mb   (media = image/video/document generation)
    Usage counters persist in operator_logs/usage.json so a restart does not reset the day's totals.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self._lock = threading.Lock()
        self._recent: Dict[str, Deque[float]] = defaultdict(deque)
        self._last_request: Dict[str, float] = {}
        self._path = path or os.path.join(OPERATOR_LOG_DIR, "usage.json")
        self._day = date.today().isoformat()
        self._usage: Dict[str, Dict[str, float]] = {}
        self._global = 0
        self._dirty = 0
        self._load()

    # -- persistence -------------------------------------------------------------
    def _load(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if data.get("day") == self._day:
                self._usage = data.get("users", {})
                self._global = int(data.get("global", 0))
        except Exception:
            pass

    def _flush(self, force: bool = False) -> None:
        self._dirty += 1
        if not force and self._dirty < 5:
            return
        self._dirty = 0
        try:
            os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
            tmp = self._path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump({"day": self._day, "users": self._usage, "global": self._global}, fh)
            os.replace(tmp, self._path)
        except Exception:
            pass

    def _roll_day(self) -> None:
        today = date.today().isoformat()
        if today != self._day:
            self._day = today
            self._usage = {}
            self._global = 0

    # -- public API --------------------------------------------------------------
    def check(self, user_id: str, kind: str = "chat", amount: float = 1) -> Tuple[bool, str]:
        """Return (allowed, friendly_message). Records usage when allowed."""
        lim = config.limits()
        now = time.time()
        user_id = user_id or "anonymous"
        with self._lock:
            self._roll_day()

            if self._global >= lim["global_daily_limit"]:
                return False, ("🛡️ Effiong AI has reached today's platform-wide free-tier limit. "
                               "This protects the shared free tokens - please try again tomorrow.")

            if kind in ("chat", "media"):
                # spacing between requests
                last = self._last_request.get(user_id, 0.0)
                if now - last < lim["min_seconds_between_requests"]:
                    return False, "⏱️ Please wait a moment before sending the next request."
                # burst window
                window = self._recent[user_id]
                while window and now - window[0] > 60:
                    window.popleft()
                if len(window) >= lim["max_requests_per_minute"]:
                    return False, "⏱️ Too many requests in one minute. Please slow down for a few seconds."

            counters = self._usage.setdefault(user_id, {"chat": 0, "media": 0, "upload_mb": 0})
            caps = {
                "chat": lim["daily_chat_limit_per_user"],
                "media": lim["daily_media_limit_per_user"],
                "upload_mb": lim["daily_upload_mb_per_user"],
            }
            cap = caps.get(kind, lim["daily_chat_limit_per_user"])
            if counters.get(kind, 0) + amount > cap:
                label = {"chat": "messages", "media": "image/video/document generations", "upload_mb": "MB of uploads"}.get(kind, kind)
                return False, f"🛡️ Daily limit reached ({int(cap)} {label}). It resets tomorrow - this keeps the free tokens available for everyone."

            counters[kind] = counters.get(kind, 0) + amount
            if kind in ("chat", "media"):
                self._last_request[user_id] = now
                self._recent[user_id].append(now)
                self._global += 1
            self._flush()
            return True, ""

    def usage_for(self, user_id: str) -> Dict[str, float]:
        with self._lock:
            self._roll_day()
            return dict(self._usage.get(user_id or "anonymous", {}))

    def reset(self) -> None:
        with self._lock:
            self._usage.clear()
            self._recent.clear()
            self._last_request.clear()
            self._global = 0
            self._flush(force=True)


GUARD = RateGuard()


# --------------------------------------------------------------------------------------
# Per-request execution budget (loop / runaway protection)
# --------------------------------------------------------------------------------------
class BudgetExceeded(RuntimeError):
    pass


class ExecutionBudget:
    """Passed down through one user request. Every provider call must call .spend()."""

    def __init__(self, deadline_seconds: Optional[float] = None, max_calls: Optional[int] = None) -> None:
        lim = config.limits()
        self.deadline = time.time() + float(deadline_seconds or lim["request_deadline_seconds"])
        self.max_calls = int(max_calls or lim["max_provider_calls_per_request"])
        self.calls = 0

    def remaining(self) -> float:
        return max(0.0, self.deadline - time.time())

    def spend(self) -> None:
        self.calls += 1
        if self.calls > self.max_calls:
            raise BudgetExceeded("provider call budget for this request exhausted")
        if self.remaining() <= 0:
            raise BudgetExceeded("time budget for this request exhausted")

    def timeout_for(self, wanted: float) -> float:
        return max(3.0, min(float(wanted), self.remaining()))


# --------------------------------------------------------------------------------------
# SSRF-safe HTTP
# --------------------------------------------------------------------------------------
class UnsafeURL(ValueError):
    pass


def _ip_is_public(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast
                or addr.is_reserved or addr.is_unspecified)


def assert_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURL("only http/https links are allowed")
    host = parsed.hostname
    if not host:
        raise UnsafeURL("link has no host")
    if host.lower() in {"localhost", "metadata.google.internal"} or host.endswith((".local", ".internal")):
        raise UnsafeURL("local addresses are blocked")
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise UnsafeURL(f"cannot resolve host: {exc}") from exc
    for info in infos:
        if not _ip_is_public(info[4][0]):
            raise UnsafeURL("private / internal network addresses are blocked")
    return url


def safe_get(url: str, timeout: float = 15, max_bytes: int = 4_000_000, headers: Optional[dict] = None,
             max_redirects: int = 4) -> requests.Response:
    """GET with SSRF checks on every hop and a hard cap on downloaded bytes."""
    hdrs = {"User-Agent": "EffiongAI/3.0 (+truth-seeking research bot)", "Accept": "*/*"}
    hdrs.update(headers or {})
    current = url
    for _ in range(max_redirects + 1):
        assert_public_url(current)
        resp = requests.get(current, headers=hdrs, timeout=timeout, stream=True, allow_redirects=False)
        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            loc = resp.headers.get("Location")
            resp.close()
            if not loc:
                raise UnsafeURL("redirect without location")
            current = urljoin(current, loc)
            continue
        chunks, size = [], 0
        for chunk in resp.iter_content(chunk_size=65536):
            size += len(chunk)
            chunks.append(chunk)
            if size >= max_bytes:
                break
        resp.close()
        resp._content = b"".join(chunks)  # type: ignore[attr-defined]
        resp._content_consumed = True  # type: ignore[attr-defined]
        return resp
    raise UnsafeURL("too many redirects")


def report_abuse(user_id: str, reason: str) -> None:
    HEALTH.flag("shield", f"{user_id}: {reason}", status="ok")
    write_operator_log("shield_block", {"user": user_id, "reason": reason})
