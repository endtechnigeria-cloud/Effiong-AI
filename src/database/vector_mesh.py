"""
EFFIONG AI - Vector Mesh (self-learning knowledge memory)
=========================================================
Where Effiong AI keeps what it has learned from the web and from the knowledge repositories so it can
recall it later without asking again.

Tier 1  local SQLite file  (always on, free, survives restarts on your own disk)
Tier 2  Pinecone           (used when PINECONE_API_KEY is set; index dimension must be 768)
Tier 3  Supabase pgvector  (used when SUPABASE_URL + SUPABASE_KEY are set and supabase_schema.sql was run)

Privacy rule: only PUBLIC knowledge (web snippets, repository records, verified heritage records) is stored
here.  Private user chats are never written to this shared memory.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import numpy as np

from src import config
from src.brain.embeddings import DIM, EmbeddingEngine
from src.core.health import HEALTH
from src.utilities.text_utils import sha256_text, truncate

MAX_ROWS = 20000


class VectorMesh:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.embedding_engine = EmbeddingEngine()
        self.db_path = db_path or config.get("KNOWLEDGE_DB_PATH", "vector_memory/knowledge.db")
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS memories (id TEXT PRIMARY KEY, text TEXT, meta TEXT, vec BLOB, tag TEXT, created REAL)"
        )
        self._conn.commit()
        self._cache: Dict[str, Any] = {"tag": None, "ids": [], "mat": None, "rows": 0}
        self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="effiong-learn")
        self._remote_off_until = 0.0
        self._pinecone_index = None

    # ------------------------------------------------------------------ write
    def upsert_vector(self, node_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        text = (text or "").strip()
        if not text:
            return False
        metadata = metadata or {}
        vec, tag = self.embedding_engine.embed(text)
        try:
            blob = np.asarray(vec, dtype=np.float32).tobytes()
            with self._lock:
                self._conn.execute(
                    "INSERT OR REPLACE INTO memories (id, text, meta, vec, tag, created) VALUES (?,?,?,?,?,?)",
                    (node_id, text, json.dumps(metadata, ensure_ascii=False, default=str), blob, tag, time.time()),
                )
                self._conn.commit()
                self._cache["tag"] = None  # invalidate
                self._prune()
        except Exception as exc:
            HEALTH.flag("memory:sqlite", f"{exc.__class__.__name__}: {exc}")
            return False
        self._pool.submit(self._remote_upsert, node_id, text, metadata, vec, tag)
        return True

    def learn(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store a piece of public knowledge under a content-derived id (dedupes automatically)."""
        return self.upsert_vector("k_" + sha256_text(text)[:20], text, metadata)

    def _prune(self) -> None:
        n = self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        if n > MAX_ROWS:
            self._conn.execute(
                "DELETE FROM memories WHERE id IN (SELECT id FROM memories ORDER BY created ASC LIMIT ?)", (n - MAX_ROWS,)
            )
            self._conn.commit()

    # ------------------------------------------------------------------ read
    def query_similarity(self, query_text: str, limit: int = 3, min_score: float = 0.12) -> List[Dict[str, Any]]:
        qvec, tag = self.embedding_engine.embed(query_text)
        results = self._local_search(qvec, tag, limit)
        remote = self._remote_query(qvec, tag, limit)
        seen = {r["id"] for r in results}
        results.extend(r for r in remote if r["id"] not in seen)
        results = [r for r in results if r["score"] >= min_score]
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    def _local_search(self, qvec: List[float], tag: str, limit: int) -> List[Dict[str, Any]]:
        try:
            with self._lock:
                if self._cache["tag"] != tag:
                    rows = self._conn.execute("SELECT id, vec FROM memories WHERE tag=?", (tag,)).fetchall()
                    ids = [r[0] for r in rows]
                    mat = np.vstack([np.frombuffer(r[1], dtype=np.float32) for r in rows]) if rows else np.zeros((0, DIM), np.float32)
                    self._cache.update(tag=tag, ids=ids, mat=mat)
                ids, mat = self._cache["ids"], self._cache["mat"]
                if not ids:
                    return []
                scores = mat @ np.asarray(qvec, dtype=np.float32)
                top = np.argsort(-scores)[:limit]
                out = []
                for i in top:
                    row = self._conn.execute("SELECT text, meta FROM memories WHERE id=?", (ids[i],)).fetchone()
                    if row:
                        out.append({"id": ids[i], "text": row[0], "metadata": json.loads(row[1] or "{}"), "score": float(scores[i])})
                return out
        except Exception as exc:
            HEALTH.flag("memory:sqlite", f"{exc.__class__.__name__}: {exc}")
            return []

    def count(self) -> int:
        try:
            with self._lock:
                return int(self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0])
        except Exception:
            return 0

    # ------------------------------------------------------------------ remote tiers
    def _remote_enabled(self) -> bool:
        return time.time() >= self._remote_off_until

    def _remote_fail(self, component: str, exc: Exception) -> None:
        self._remote_off_until = time.time() + 300
        HEALTH.flag(component, f"{exc.__class__.__name__}: {exc} (retry in 5 min)")

    def _pinecone(self):
        if self._pinecone_index is not None:
            return self._pinecone_index
        key = config.get("PINECONE_API_KEY")
        if not key:
            return None
        from pinecone import Pinecone, ServerlessSpec  # optional dependency

        pc = Pinecone(api_key=key)
        name = config.get("PINECONE_INDEX", "effiong-ai")
        try:
            names = pc.list_indexes().names()
        except Exception:
            names = [i["name"] for i in pc.list_indexes()]
        if name not in names:
            pc.create_index(name=name, dimension=DIM, metric="cosine",
                            spec=ServerlessSpec(cloud=config.get("PINECONE_CLOUD", "aws"), region=config.get("PINECONE_ENV", "us-east-1")))
        self._pinecone_index = pc.Index(name)
        return self._pinecone_index

    def _supabase(self):
        url, key = config.get("SUPABASE_URL"), config.get("SUPABASE_KEY")
        if not (url and key):
            return None
        from supabase import create_client  # optional dependency

        return create_client(url, key)

    def _remote_upsert(self, node_id: str, text: str, metadata: Dict[str, Any], vec: List[float], tag: str) -> None:
        if not self._remote_enabled():
            return
        if config.get("PINECONE_API_KEY"):
            try:
                idx = self._pinecone()
                meta = {"text": truncate(text, 1500), "emb": tag}
                meta.update({k: (v if isinstance(v, (str, int, float, bool)) else json.dumps(v, default=str)[:300])
                             for k, v in metadata.items() if v is not None})
                idx.upsert(vectors=[{"id": node_id, "values": list(map(float, vec)), "metadata": meta}], namespace="effiong")
                HEALTH.ok("memory:pinecone", "upserted")
            except Exception as exc:
                self._remote_fail("memory:pinecone", exc)
        if config.get("SUPABASE_URL") and config.get("SUPABASE_KEY"):
            try:
                client = self._supabase()
                client.table("knowledge").upsert({
                    "id": node_id, "content": text, "metadata": metadata, "embedding": list(map(float, vec)), "emb_tag": tag,
                }).execute()
                HEALTH.ok("memory:supabase", "upserted")
            except Exception as exc:
                self._remote_fail("memory:supabase", exc)

    def _remote_query(self, qvec: List[float], tag: str, limit: int) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        if not self._remote_enabled():
            return out
        if config.get("PINECONE_API_KEY"):
            try:
                res = self._pinecone().query(vector=list(map(float, qvec)), top_k=limit, include_metadata=True, namespace="effiong")
                for m in getattr(res, "matches", []) or []:
                    md = dict(m.metadata or {})
                    if md.get("emb", tag) != tag:
                        continue
                    out.append({"id": m.id, "text": md.pop("text", ""), "metadata": md, "score": float(m.score)})
            except Exception as exc:
                self._remote_fail("memory:pinecone", exc)
        if config.get("SUPABASE_URL") and config.get("SUPABASE_KEY"):
            try:
                rows = self._supabase().rpc("match_knowledge", {"query_embedding": list(map(float, qvec)), "match_count": limit, "tag": tag}).execute().data or []
                for r in rows:
                    out.append({"id": r["id"], "text": r.get("content", ""), "metadata": r.get("metadata") or {}, "score": float(r.get("similarity", 0))})
            except Exception as exc:
                self._remote_fail("memory:supabase", exc)
        return out


_MESH: Optional[VectorMesh] = None
_MESH_LOCK = threading.Lock()


def get_mesh() -> VectorMesh:
    """Process-wide singleton (SQLite connection is shared across Streamlit sessions)."""
    global _MESH
    with _MESH_LOCK:
        if _MESH is None:
            _MESH = VectorMesh()
        return _MESH
