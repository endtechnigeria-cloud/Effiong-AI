"""
EFFIONG AI - Media orchestration layer (asset storage + result types)
=====================================================================
Generated images / videos / documents are written to ./generated_assets (auto-cleaned) and referenced from chat
history by path or URL.  Small images are also embedded (compressed) in chat history so they survive restarts.
"""
from __future__ import annotations

import base64
import io
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.core.health import HEALTH, safe_import

ASSET_DIR = os.environ.get("EFFIONG_ASSET_DIR", "generated_assets")
_MAX_ASSET_BYTES = 600 * 1024 * 1024
_MAX_AGE_SECONDS = 24 * 3600
_lock = threading.Lock()


@dataclass
class MediaResult:
    kind: str                      # image | video | svg | chart
    provider: str
    prompt: str
    url: Optional[str] = None      # public URL (stable, survives restarts)
    path: Optional[str] = None     # server file path (ephemeral on free hosts)
    data: Optional[bytes] = None   # raw bytes when available
    mime: str = ""
    notes: List[str] = field(default_factory=list)
    is_placeholder: bool = False

    def to_attachment(self, embed_max_bytes: int = 160_000) -> Dict[str, Any]:
        """JSON-safe dict stored in chat history and rendered by the chat UI."""
        att: Dict[str, Any] = {"kind": self.kind, "provider": self.provider, "prompt": self.prompt,
                               "mime": self.mime, "placeholder": self.is_placeholder}
        if self.url:
            att["src"] = self.url
        if self.path:
            att["path"] = self.path
        if self.kind in ("image", "chart") and self.data:
            thumb = compress_for_history(self.data, embed_max_bytes)
            if thumb:
                att["b64"] = base64.b64encode(thumb).decode("ascii")
                att["b64_mime"] = "image/jpeg"
        if self.kind == "svg" and self.data:
            att["svg"] = self.data.decode("utf-8", errors="replace")
        return att


def compress_for_history(data: bytes, max_bytes: int) -> Optional[bytes]:
    Image = safe_import("PIL.Image", "vision")
    if Image is None:
        return data if len(data) <= max_bytes else None
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        side = 1024
        for quality in (80, 68, 55, 42):
            work = img.copy()
            work.thumbnail((side, side))
            buf = io.BytesIO()
            work.save(buf, "JPEG", quality=quality, optimize=True)
            if buf.tell() <= max_bytes:
                return buf.getvalue()
            side = int(side * 0.8)
    except Exception as exc:
        HEALTH.flag("media", f"compress failed: {exc}")
    return None


def save_asset(data: bytes, ext: str) -> str:
    os.makedirs(ASSET_DIR, exist_ok=True)
    path = os.path.join(ASSET_DIR, f"EFFIONG_{uuid.uuid4().hex[:10]}{ext}")
    with open(path, "wb") as fh:
        fh.write(data)
    cleanup_assets()
    return path


def cleanup_assets() -> None:
    """Delete old files and keep the folder under the size cap (protects free-host disk)."""
    with _lock:
        try:
            files = []
            now = time.time()
            for name in os.listdir(ASSET_DIR):
                p = os.path.join(ASSET_DIR, name)
                if os.path.isfile(p):
                    st = os.stat(p)
                    if now - st.st_mtime > _MAX_AGE_SECONDS:
                        os.unlink(p)
                    else:
                        files.append((st.st_mtime, st.st_size, p))
            total = sum(f[1] for f in files)
            for _, size, p in sorted(files):
                if total <= _MAX_ASSET_BYTES:
                    break
                os.unlink(p)
                total -= size
        except FileNotFoundError:
            pass
        except Exception as exc:
            HEALTH.flag("media", f"cleanup failed: {exc}")


class MediaService:
    """Small facade so other modules can ask 'what can the media pipeline do right now?'"""

    def health_check(self) -> Dict[str, Any]:
        return {"service": "media_service", "asset_dir": ASSET_DIR,
                "capabilities": ["images", "videos", "documents", "charts", "svg-graphics"]}


media_service = MediaService()
