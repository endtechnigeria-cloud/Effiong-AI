"""Vision helpers: prepare images for the multimodal brain tiers."""
from __future__ import annotations

import io
from typing import Optional, Tuple

from src.core.health import safe_import


def normalize_image(data: bytes, mime: str = "image/png", max_side: int = 1800) -> Tuple[str, bytes]:
    """Downscale big photos and convert exotic formats to JPEG/PNG so every provider accepts them."""
    Image = safe_import("PIL.Image", "vision", None)
    if Image is None:
        return mime, data
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        if max(img.size) > max_side:
            img.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        if img.mode in ("RGBA", "LA", "P") and mime == "image/png":
            img.save(buf, format="PNG")
            return "image/png", buf.getvalue()
        img.convert("RGB").save(buf, format="JPEG", quality=88)
        return "image/jpeg", buf.getvalue()
    except Exception:
        return mime, data
