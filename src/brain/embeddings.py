"""
EFFIONG AI - Embedding layer
============================
Two interchangeable embedders that both output 768 numbers:

* local-hash-768 : signed feature hashing of words + word pairs (no network, no quota, deterministic,
                   works offline - always available).
* gemini-768     : Gemini embeddings (semantic).  Enabled with  EMBEDDING_PROVIDER = "gemini".

Every vector is tagged with the embedder that produced it; vectors are only ever compared with vectors
that carry the same tag, so switching provider later can never silently corrupt search results.
"""
from __future__ import annotations

import math
import re
import zlib
from collections import Counter
from typing import List, Tuple

import requests

from src import config
from src.core.health import HEALTH

DIM = 768
LOCAL_TAG = "local-hash-768"
GEMINI_TAG = "gemini-768"

_STOP = set(
    "a an the and or but if of to in on at by for with from as is are was were be been being it its this that these those "
    "i you he she we they them his her our your their my me not no do does did have has had will would can could should "
    "what which who whom when where why how than then so such into about over under also just".split()
)
_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


class EmbeddingEngine:
    def __init__(self) -> None:
        self.dim = DIM

    # -- public ----------------------------------------------------------------------
    @property
    def tag(self) -> str:
        return GEMINI_TAG if self._wants_gemini() else LOCAL_TAG

    def embed(self, text: str) -> Tuple[List[float], str]:
        """Return (vector, tag). Falls back to the local embedder if Gemini is unavailable."""
        if self._wants_gemini():
            vec = self._gemini(text)
            if vec:
                return vec, GEMINI_TAG
            HEALTH.flag("embeddings", "Gemini embeddings unavailable - using local hashing embeddings")
        return self._local(text), LOCAL_TAG

    def get_embedding(self, text: str) -> List[float]:
        """Backwards-compatible helper (older modules call this)."""
        return self.embed(text)[0]

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0
        n = min(len(a), len(b))
        dot = sum(x * y for x, y in zip(a[:n], b[:n]))
        na = math.sqrt(sum(x * x for x in a[:n]))
        nb = math.sqrt(sum(y * y for y in b[:n]))
        return dot / (na * nb) if na and nb else 0.0

    # -- local -----------------------------------------------------------------------
    def _local(self, text: str) -> List[float]:
        tokens = [t for t in _TOKEN.findall((text or "").lower()) if t not in _STOP and len(t) > 1]
        feats = list(tokens) + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
        counts = Counter(feats)
        vec = [0.0] * DIM
        for feat, c in counts.items():
            h = zlib.crc32(feat.encode("utf-8"))
            idx = h % DIM
            sign = 1.0 if (h >> 16) & 1 else -1.0
            weight = 1.0 + math.log(c)
            if "_" in feat:
                weight *= 0.7  # word pairs help ordering but should not dominate
            vec[idx] += sign * weight
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm else vec

    # -- gemini ----------------------------------------------------------------------
    @staticmethod
    def _wants_gemini() -> bool:
        return config.get("EMBEDDING_PROVIDER", "local").lower() == "gemini" and bool(config.get_keys("GEMINI_API_KEY"))

    def _gemini(self, text: str) -> List[float]:
        model = config.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")
        for key in config.get_keys("GEMINI_API_KEY"):
            try:
                r = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent",
                    headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                    json={"content": {"parts": [{"text": (text or "")[:6000]}]}, "outputDimensionality": DIM},
                    timeout=15,
                )
                if r.status_code == 200:
                    values = (r.json().get("embedding") or {}).get("values") or []
                    if len(values) == DIM:
                        norm = math.sqrt(sum(v * v for v in values)) or 1.0
                        return [v / norm for v in values]
            except requests.RequestException:
                continue
        return []
