"""
EFFIONG AI - Image generation (multi-tier)
==========================================
Default : Pollinations (free, no key)
Tiers   : Hugging Face FLUX -> Cloudflare Workers AI FLUX -> Together FLUX (free) -> Leonardo AI ->
          Gemini image model -> local poster canvas (never blank, always clearly labelled)

Adobe Firefly, Ideogram and Canva AI have no free public API, so they are not wired in; add them later
by writing one small `_tier_xxx` function below and appending it to TIERS.
"""
from __future__ import annotations

import base64
import io
import random
import re
import textwrap
import time
import urllib.parse
from typing import Callable, List, Optional, Tuple

import requests

from src import config
from src.core.guard import BudgetExceeded, ExecutionBudget
from src.core.health import HEALTH, safe_import
from src.services.media_service import MediaResult, save_asset

_IMG_MIME = ("image/png", "image/jpeg", "image/webp")


def _looks_like_image(data: bytes) -> bool:
    return len(data) > 2000 and (data[:8].startswith(b"\x89PNG") or data[:3] == b"\xff\xd8\xff" or data[:4] == b"RIFF")


def enrich_prompt(user_text: str) -> str:
    """Turn vague requests into a strong art prompt (only when the request is short)."""
    subject = re.sub(
        r"(?i)\b(please|can you|could you|generate|create|make|draw|paint|render|design|show me|give me|produce|"
        r"an?|the|image|picture|photo|photograph|illustration|artwork|of|for me)\b", " ", user_text or "")
    subject = re.sub(r"\s+", " ", subject).strip(" .,:;-") or (user_text or "a scene").strip()
    if len(subject.split()) <= 6:
        return (f"A highly detailed, professional, cinematic image of {subject}, 8k resolution, masterpiece quality, "
                "dynamic natural lighting, rich textures, sharp focus, photorealistic")
    return subject


class ImageService:
    def __init__(self) -> None:
        self.width, self.height = 1280, 720

    # ------------------------------------------------------------------ tiers
    def _tier_pollinations(self, prompt: str, w: int, h: int, seed: int, timeout: float) -> Optional[Tuple[bytes, str]]:
        enc = urllib.parse.quote(prompt[:900])
        url = f"https://image.pollinations.ai/prompt/{enc}?width={w}&height={h}&model=flux&nologo=true&enhance=true&seed={seed}"
        headers = {}
        key = config.get("POLLINATIONS_API_KEY")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200 and _looks_like_image(r.content):
            return r.content, url
        HEALTH.flag("image:pollinations", f"HTTP {r.status_code}")
        return None

    def _tier_huggingface(self, prompt: str, w: int, h: int, seed: int, timeout: float) -> Optional[Tuple[bytes, str]]:
        for key in config.get_keys("HF_TOKEN"):
            r = requests.post(
                "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
                headers={"Authorization": f"Bearer {key}"}, json={"inputs": prompt}, timeout=timeout)
            if r.status_code == 200 and _looks_like_image(r.content):
                return r.content, ""
            HEALTH.flag("image:huggingface", f"HTTP {r.status_code}")
        return None

    def _tier_cloudflare(self, prompt: str, w: int, h: int, seed: int, timeout: float) -> Optional[Tuple[bytes, str]]:
        acct, tok = config.get("CLOUDFLARE_ACCOUNT_ID"), config.get("CLOUDFLARE_API_TOKEN")
        if not (acct and tok):
            return None
        r = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/@cf/black-forest-labs/flux-1-schnell",
                          headers={"Authorization": f"Bearer {tok}"}, json={"prompt": prompt[:2000], "steps": 4}, timeout=timeout)
        if r.status_code == 200:
            b64 = (r.json().get("result") or {}).get("image")
            if b64:
                return base64.b64decode(b64), ""
        HEALTH.flag("image:cloudflare", f"HTTP {r.status_code}")
        return None

    def _tier_together(self, prompt: str, w: int, h: int, seed: int, timeout: float) -> Optional[Tuple[bytes, str]]:
        for key in config.get_keys("TOGETHER_API_KEY"):
            r = requests.post("https://api.together.xyz/v1/images/generations",
                              headers={"Authorization": f"Bearer {key}"},
                              json={"model": config.get("TOGETHER_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell-Free"),
                                    "prompt": prompt[:1500], "width": 1024, "height": 768, "steps": 4, "n": 1,
                                    "response_format": "b64_json"}, timeout=timeout)
            if r.status_code == 200:
                items = r.json().get("data") or []
                if items and items[0].get("b64_json"):
                    return base64.b64decode(items[0]["b64_json"]), ""
            HEALTH.flag("image:together", f"HTTP {r.status_code}")
        return None

    def _tier_leonardo(self, prompt: str, w: int, h: int, seed: int, timeout: float) -> Optional[Tuple[bytes, str]]:
        for key in config.get_keys("LEONARDO_API_KEY"):
            hdr = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "accept": "application/json"}
            r = requests.post("https://cloud.leonardo.ai/api/rest/v1/generations", headers=hdr,
                              json={"prompt": prompt[:1000], "width": 1024, "height": 768, "num_images": 1}, timeout=25)
            if r.status_code != 200:
                HEALTH.flag("image:leonardo", f"HTTP {r.status_code}")
                continue
            gid = (r.json().get("sdGenerationJob") or {}).get("generationId")
            deadline = time.time() + min(timeout, 60)
            while gid and time.time() < deadline:
                time.sleep(4)
                g = requests.get(f"https://cloud.leonardo.ai/api/rest/v1/generations/{gid}", headers=hdr, timeout=20)
                imgs = ((g.json().get("generations_by_pk") or {}).get("generated_images") or []) if g.status_code == 200 else []
                if imgs:
                    img = requests.get(imgs[0]["url"], timeout=30)
                    if img.status_code == 200:
                        return img.content, imgs[0]["url"]
        return None

    def _tier_gemini(self, prompt: str, w: int, h: int, seed: int, timeout: float) -> Optional[Tuple[bytes, str]]:
        model = config.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
        for key in config.get_keys("GEMINI_API_KEY"):
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                              headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                              json={"contents": [{"parts": [{"text": prompt}]}],
                                    "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}}, timeout=timeout)
            if r.status_code == 200:
                for cand in r.json().get("candidates", []):
                    for part in (cand.get("content") or {}).get("parts", []):
                        inline = part.get("inlineData") or part.get("inline_data")
                        if inline and inline.get("data"):
                            return base64.b64decode(inline["data"]), ""
            HEALTH.flag("image:gemini", f"HTTP {r.status_code}")
        return None

    TIERS: List[Tuple[str, str]] = [
        ("Pollinations", "_tier_pollinations"), ("Hugging Face FLUX", "_tier_huggingface"),
        ("Cloudflare FLUX", "_tier_cloudflare"), ("Together FLUX", "_tier_together"),
        ("Leonardo AI", "_tier_leonardo"), ("Gemini Image", "_tier_gemini"),
    ]

    # ------------------------------------------------------------------ public
    def generate(self, user_prompt: str, budget: Optional[ExecutionBudget] = None, size: Tuple[int, int] = (1280, 720),
                 enrich: bool = True, on_status: Optional[Callable[[str], None]] = None) -> MediaResult:
        prompt = enrich_prompt(user_prompt) if enrich else user_prompt
        w, h = size
        seed = random.randint(1000, 999999)
        for label, fn_name in self.TIERS:
            try:
                if budget:
                    budget.spend()
                if on_status:
                    on_status(f"🎨 Rendering with {label}...")
                out = getattr(self, fn_name)(prompt, w, h, seed, budget.timeout_for(70) if budget else 70)
            except BudgetExceeded:
                break
            except Exception as exc:
                HEALTH.flag(f"image:{label.lower().split()[0]}", f"{exc.__class__.__name__}: {exc}")
                continue
            if out:
                data, url = out
                HEALTH.ok(f"image:{label.lower().split()[0]}", "generated")
                res = MediaResult(kind="image", provider=label, prompt=prompt, url=url or None, data=data, mime="image/png")
                if not url:
                    res.path = save_asset(data, ".png")
                return res
        return self._poster_fallback(user_prompt, prompt)

    # guaranteed last tier ---------------------------------------------------------------
    def _poster_fallback(self, user_prompt: str, prompt: str) -> MediaResult:
        data = render_poster(user_prompt)
        res = MediaResult(kind="image", provider="Local poster canvas", prompt=prompt, data=data, mime="image/png",
                          is_placeholder=True)
        res.path = save_asset(data, ".png")
        res.notes.append("All free image engines were busy, so a text poster was drawn locally. Try again in a minute.")
        return res


def render_poster(text: str, size: Tuple[int, int] = (1280, 720)) -> bytes:
    """Brand-coloured poster with the request text (used when every image engine is unavailable)."""
    Image = safe_import("PIL.Image", "vision")
    ImageDraw = safe_import("PIL.ImageDraw", "vision")
    ImageFont = safe_import("PIL.ImageFont", "vision")
    if not (Image and ImageDraw and ImageFont):
        raise RuntimeError("Pillow is not available")
    w, h = size
    import numpy as np

    t = np.linspace(0, 1, h).reshape(h, 1)
    col = np.stack([11 + 60 * t, 15 + 34 * t, 23 + 8 * t], axis=-1)          # h x 1 x 3
    arr = np.broadcast_to(col, (h, w, 3)).astype("uint8")
    img = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(img)
    d.rectangle([24, 24, w - 24, h - 24], outline="#D27D2D", width=4)
    try:
        import matplotlib

        font_path = matplotlib.get_data_path() + "/fonts/ttf/DejaVuSans.ttf"
        big, small = ImageFont.truetype(font_path, 44), ImageFont.truetype(font_path, 24)
    except Exception:
        big = small = ImageFont.load_default()
    d.text((70, 60), "EFFIONG AI", fill="#D27D2D", font=big)
    lines = textwrap.wrap((text or "").strip(), 46)[:7]
    y = 170
    for line in lines:
        d.text((70, y), line, fill="#F0F6FC", font=big)
        y += 62
    d.text((70, h - 90), "Visual engines are busy - text poster placeholder", fill="#8B949E", font=small)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()
