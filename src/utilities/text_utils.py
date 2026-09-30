"""Small, dependency-light helpers used everywhere."""
from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from typing import Any, List, Optional

_URL_RE = re.compile(r"https?://[^\s<>\"'\)\]]+", re.IGNORECASE)
_EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"   # pictographs, emoticons, transport, symbols
    "\U00002600-\U000027BF"   # misc symbols, dingbats
    "\U0000FE00-\U0000FE0F"   # variation selectors
    "\U0001F1E6-\U0001F1FF"   # flags
    "\u200d"
    "]+",
    flags=re.UNICODE,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data or b"").hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes((text or "").encode("utf-8"))


def extract_urls(text: str, limit: int = 12) -> List[str]:
    seen: List[str] = []
    for m in _URL_RE.findall(text or ""):
        url = m.rstrip(".,;:!?")
        if url not in seen:
            seen.append(url)
        if len(seen) >= limit:
            break
    return seen


def strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text or "")


def truncate(text: str, n: int, suffix: str = "…") -> str:
    text = text or ""
    return text if len(text) <= n else text[: max(0, n - len(suffix))] + suffix


def esc(text: Any) -> str:
    """HTML-escape untrusted text for use inside unsafe_allow_html blocks."""
    return html.escape(str(text if text is not None else ""), quote=True)


def extract_json(text: str) -> Optional[Any]:
    """Recover a JSON object/array from an LLM reply (handles ```json fences and chatter)."""
    if not text:
        return None
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
    if fence:
        cleaned = fence.group(1).strip()
    for candidate in (cleaned,):
        try:
            return json.loads(candidate)
        except Exception:
            pass
    # first balanced {...} or [...]
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start: end + 1])
            except Exception:
                continue
    return None


_md = None


def md_to_html(text: str) -> str:
    """
    Markdown -> HTML with raw HTML DISABLED (so model output or user text can never inject markup).
    Falls back to escaped text with <br> if markdown-it-py is missing.
    """
    global _md
    text = text or ""
    if _md is None:
        try:
            from markdown_it import MarkdownIt

            _md = MarkdownIt("commonmark", {"html": False, "linkify": False, "breaks": True}).enable("table").enable("strikethrough")
        except Exception:
            _md = False
    if _md is False:
        return html.escape(text).replace("\n", "<br>")
    rendered = _md.render(text)
    # open links safely
    rendered = re.sub(r"<a href=", '<a target="_blank" rel="noopener noreferrer" href=', rendered)
    return rendered


def clean_for_speech(text: str, max_chars: int = 1800) -> str:
    """Strip markdown / urls / emoji so text-to-speech sounds natural."""
    t = re.sub(r"\[EFFIONG_[A-Z_]+(?:::[^\]]*)?\]", " ", text or "")
    t = re.sub(r"```[\s\S]*?```", " ", t)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = _URL_RE.sub(" ", t)
    t = re.sub(r"[#*_`>|~]+", " ", t)
    t = strip_emoji(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:max_chars]


def split_sentences(text: str, max_len: int = 220) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text or "")
    out: List[str] = []
    for p in parts:
        p = p.strip()
        while len(p) > max_len:
            cut = p.rfind(" ", 0, max_len)
            cut = cut if cut > 40 else max_len
            out.append(p[:cut].strip())
            p = p[cut:].strip()
        if p:
            out.append(p)
    return out
