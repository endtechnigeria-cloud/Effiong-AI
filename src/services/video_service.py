"""
EFFIONG AI - Video generation (multi-tier, background-safe)
===========================================================
Tier order (each is bounded in time; the first to deliver wins):

  1. Google Veo (the engine behind Google Flow) - only if ENABLE_VEO=true and a Gemini key on a billed project exists
  2. Pollinations video (free)
  3. PixVerse   (if PIXVERSE_API_KEY)
  4. Kling AI   (if KLING_API_KEY)
  5. Local Motion Render - ALWAYS available and free: image keyframes -> cinematic pan/zoom + cross-fades -> MP4

Google Flow itself has no public API, Runway / Pika / Hailuo / Capcut / Canva have no free API tier, so they are
not wired in.  To add one, write a `_tier_xxx` method and append it to TIERS.
"""
from __future__ import annotations

import io
import os
import time
import urllib.parse
import uuid
from typing import Callable, List, Optional, Tuple

import requests

from src import config
from src.core.guard import BudgetExceeded, ExecutionBudget
from src.core.health import HEALTH, safe_import
from src.services.image_service import ImageService, render_poster
from src.services.media_service import ASSET_DIR, MediaResult, save_asset


def enrich_video_prompt(user_text: str) -> str:
    import re

    subject = re.sub(r"(?i)\b(please|can you|generate|create|make|animate|render|produce|an?|the|video|animation|clip|"
                     r"footage|motion|of|for me)\b", " ", user_text or "")
    subject = re.sub(r"\s+", " ", subject).strip(" .,:;-") or (user_text or "a scene").strip()
    if len(subject.split()) <= 6:
        return (f"Cinematic continuous motion shot of {subject}, fluid movement, photorealistic rendering, "
                "dramatic lighting, professional cinematography")
    return subject


class VideoService:
    def __init__(self) -> None:
        self.images = ImageService()

    # ------------------------------------------------------------------ remote tiers
    def _reachable_video(self, url: str, timeout: float) -> bool:
        try:
            r = requests.get(url, stream=True, timeout=(10, timeout), headers={"Range": "bytes=0-65535"})
            ok = r.status_code in (200, 206) and ("video" in (r.headers.get("Content-Type") or "") or url.endswith(".mp4"))
            r.close()
            return ok
        except requests.RequestException:
            return False

    def _tier_veo(self, prompt: str, timeout: float, on_status) -> Optional[str]:
        if not config.get_bool("ENABLE_VEO", False):
            return None
        model = config.get("VEO_MODEL", "veo-3.0-fast-generate-001")
        for key in config.get_keys("GEMINI_API_KEY"):
            hdr = {"x-goog-api-key": key, "Content-Type": "application/json"}
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predictLongRunning",
                              headers=hdr, json={"instances": [{"prompt": prompt}]}, timeout=30)
            if r.status_code != 200:
                HEALTH.flag("video:veo", f"HTTP {r.status_code}")
                continue
            op = r.json().get("name")
            deadline = time.time() + timeout
            while op and time.time() < deadline:
                time.sleep(8)
                s = requests.get(f"https://generativelanguage.googleapis.com/v1beta/{op}", headers=hdr, timeout=30)
                if s.status_code == 200 and s.json().get("done"):
                    samples = (((s.json().get("response") or {}).get("generateVideoResponse") or {}).get("generatedSamples")) or []
                    if samples:
                        uri = samples[0]["video"]["uri"]
                        vid = requests.get(uri, headers={"x-goog-api-key": key}, timeout=120)
                        if vid.status_code == 200:
                            return save_asset(vid.content, ".mp4")
                    break
        return None

    def _tier_pollinations(self, prompt: str, timeout: float, on_status) -> Optional[str]:
        enc = urllib.parse.quote(prompt[:500])
        url = f"https://gen.pollinations.ai/video/{enc}?model=veo&seed={int(time.time())}&aspectRatio=16:9"
        headers = {}
        if config.get("POLLINATIONS_API_KEY"):
            headers["Authorization"] = f"Bearer {config.get('POLLINATIONS_API_KEY')}"
        r = requests.get(url, headers=headers, stream=True, timeout=(10, timeout))
        if r.status_code == 200 and "video" in (r.headers.get("Content-Type") or ""):
            data = b"".join(r.iter_content(65536))
            if len(data) > 20_000:
                return save_asset(data, ".mp4")
        HEALTH.flag("video:pollinations", f"HTTP {r.status_code}")
        return None

    def _tier_pixverse(self, prompt: str, timeout: float, on_status) -> Optional[str]:
        key = config.get("PIXVERSE_API_KEY")
        if not key:
            return None
        hdr = {"API-KEY": key, "Ai-Trace-Id": str(uuid.uuid4()), "Content-Type": "application/json"}
        r = requests.post("https://app-api.pixverse.ai/openapi/v2/video/text/generate", headers=hdr, timeout=20,
                          json={"prompt": prompt, "duration": 5, "quality": "540p", "aspect_ratio": "16:9", "model": "v4.5"})
        if r.status_code != 200:
            HEALTH.flag("video:pixverse", f"HTTP {r.status_code}")
            return None
        vid = ((r.json().get("Resp") or {}).get("video_id")) or r.json().get("video_id")
        deadline = time.time() + timeout
        while vid and time.time() < deadline:
            time.sleep(5)
            s = requests.get(f"https://app-api.pixverse.ai/openapi/v2/video/result/{vid}", headers=hdr, timeout=20)
            body = (s.json().get("Resp") or {}) if s.status_code == 200 else {}
            if body.get("status") == 1 and body.get("url"):
                return body["url"]
        return None

    def _tier_kling(self, prompt: str, timeout: float, on_status) -> Optional[str]:
        key = config.get("KLING_API_KEY")
        if not key:
            return None
        hdr = {"Authorization": f"Bearer {key}", "X-API-Key": key, "Content-Type": "application/json"}
        r = requests.post("https://api.klingai.com/v1/videos/text2video", headers=hdr, timeout=20,
                          json={"prompt": prompt, "model_name": "kling-v1", "duration": "5", "mode": "std"})
        if r.status_code not in (200, 201, 202):
            HEALTH.flag("video:kling", f"HTTP {r.status_code}")
            return None
        task = (r.json().get("data") or {}).get("task_id")
        deadline = time.time() + timeout
        while task and time.time() < deadline:
            time.sleep(6)
            s = requests.get(f"https://api.klingai.com/v1/videos/text2video/{task}", headers=hdr, timeout=20)
            body = (s.json().get("data") or {}) if s.status_code == 200 else {}
            if body.get("task_status") == "succeed":
                vids = (body.get("task_result") or {}).get("videos") or []
                if vids:
                    return vids[0].get("url")
        return None

    TIERS: List[Tuple[str, str, float]] = [
        ("Google Veo", "_tier_veo", 150), ("Pollinations Video", "_tier_pollinations", 100),
        ("PixVerse", "_tier_pixverse", 60), ("Kling AI", "_tier_kling", 60),
    ]

    # ------------------------------------------------------------------ public
    def generate(self, user_prompt: str, budget: Optional[ExecutionBudget] = None,
                 on_status: Optional[Callable[[str], None]] = None, remote_tiers: bool = True) -> MediaResult:
        prompt = enrich_video_prompt(user_prompt)
        if remote_tiers:
            for label, fn_name, wanted in self.TIERS:
                try:
                    if budget:
                        budget.spend()
                    if on_status:
                        on_status(f"🎬 Rendering with {label}...")
                    out = getattr(self, fn_name)(prompt, budget.timeout_for(wanted) if budget else wanted, on_status)
                except BudgetExceeded:
                    break
                except Exception as exc:
                    HEALTH.flag(f"video:{label.lower().split()[0]}", f"{exc.__class__.__name__}: {exc}")
                    continue
                if out:
                    is_url = out.startswith("http")
                    if is_url and not self._reachable_video(out, 30):
                        continue
                    HEALTH.ok(f"video:{label.lower().split()[0]}", "generated")
                    return MediaResult(kind="video", provider=label, prompt=prompt, url=out if is_url else None,
                                       path=None if is_url else out, mime="video/mp4")
        if on_status:
            on_status("🎞️ Building a motion render locally (free, always available)...")
        return self.local_motion_render(user_prompt, budget)

    # ------------------------------------------------------------------ local pipeline
    def local_motion_render(self, user_prompt: str, budget: Optional[ExecutionBudget] = None,
                            keyframes: int = 4, seconds_each: float = 3.0, fps: int = 20) -> MediaResult:
        """Cinematic slideshow: Ken-Burns pan/zoom on AI keyframes with cross-fades, encoded to H.264 MP4."""
        angles = ["wide establishing shot", "dramatic close-up detail", "moody atmospheric mid shot", "sweeping panoramic view"]
        frames_src: List[bytes] = []
        provider_notes: List[str] = []
        for i in range(keyframes):
            try:
                if budget and budget.remaining() < 25:
                    break
                res = self.images.generate(f"{user_prompt}, {angles[i % len(angles)]}", budget=budget, size=(1280, 720), enrich=(i == 0))
                if res.data and not res.is_placeholder:
                    frames_src.append(res.data)
                    provider_notes.append(res.provider)
            except Exception as exc:
                HEALTH.flag("video:local", f"keyframe failed: {exc.__class__.__name__}")
        placeholder = False
        if not frames_src:
            placeholder = True
            frames_src = [render_poster(user_prompt)]
        mp4 = _render_ken_burns(frames_src, seconds_each, fps)
        path = save_asset(mp4, ".mp4")
        res = MediaResult(kind="video", provider="Local Motion Render" + (f" (keyframes: {provider_notes[0]})" if provider_notes else ""),
                          prompt=user_prompt, path=path, data=None, mime="video/mp4", is_placeholder=placeholder)
        if placeholder:
            res.notes.append("Image engines were busy, so the motion render animates a text poster.")
        return res


def _render_ken_burns(images: List[bytes], seconds_each: float, fps: int, size: Tuple[int, int] = (960, 544)) -> bytes:
    """Encode an MP4 from still images with slow zoom/pan and cross-fade transitions."""
    import numpy as np

    imageio = safe_import("imageio.v2", "video-render")
    Image = safe_import("PIL.Image", "vision")
    if imageio is None or Image is None:
        raise RuntimeError("imageio/Pillow unavailable for local video rendering")
    W, H = size
    fade = int(fps * 0.6)
    n = int(seconds_each * fps)

    prepared = []
    for raw in images:
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        scale = 1.25
        im = im.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
        prepared.append(im)

    def shot(im, idx: int, t: float) -> "np.ndarray":
        big_w, big_h = im.size
        zoom = 1.0 + 0.18 * t if idx % 2 == 0 else 1.18 - 0.18 * t
        cw, ch = max(W // 2, min(big_w, int(big_w / zoom))), max(H // 2, min(big_h, int(big_h / zoom)))
        pan_x = (big_w - cw) * (t if idx % 3 != 1 else 1 - t)
        pan_y = (big_h - ch) * 0.5
        crop = im.crop((int(pan_x), int(pan_y), int(pan_x) + cw, int(pan_y) + ch)).resize((W, H), Image.BILINEAR)
        return np.asarray(crop)

    buf_path = os.path.join(ASSET_DIR, f"_tmp_{uuid.uuid4().hex[:8]}.mp4")
    os.makedirs(ASSET_DIR, exist_ok=True)
    writer = imageio.get_writer(buf_path, fps=fps, codec="libx264", quality=7, macro_block_size=16)
    try:
        for idx, im in enumerate(prepared):
            nxt = prepared[(idx + 1) % len(prepared)] if len(prepared) > 1 else None
            for f in range(n):
                t = f / max(1, n - 1)
                frame = shot(im, idx, t)
                if nxt is not None and idx < len(prepared) - 1 and f >= n - fade:
                    a = (f - (n - fade)) / fade
                    frame = (frame * (1 - a) + shot(nxt, idx + 1, 0.0) * a).astype("uint8")
                writer.append_data(frame)
    finally:
        writer.close()
    try:
        with open(buf_path, "rb") as fh:
            return fh.read()
    finally:
        try:
            os.unlink(buf_path)
        except OSError:
            pass
