"""
EFFIONG AI - Archive (persistence layer)
=========================================
Saves/loads chat threads and the heritage ledger so a Streamlit rerun (or a redeploy, on hosts with a persistent
disk) doesn't lose them.  Local JSON files are the tier-1 store (always on); when SUPABASE_URL + SUPABASE_KEY are
configured, records are also synced there so multiple app instances / a future mobile app can share state.

Chat history: each thread's own message list, images/media kept as compact JSON attachments (see MediaResult /
FileService.Attachment.meta) - never raw un-bounded bytes, so files stay small.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src import config
from src.core.health import HEALTH

DATA_DIR = os.environ.get("EFFIONG_DATA_DIR", "app_data")
CHATS_FILE = os.path.join(DATA_DIR, "chat_threads.json")
HERITAGE_FILE = os.path.join(DATA_DIR, "heritage_ledger.json")
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return default
    except Exception as exc:
        HEALTH.flag("archive:local", f"read {path}: {exc}")
        return default


def _write_json_atomic(path: str, data: Any) -> bool:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = f"{path}.tmp.{uuid.uuid4().hex[:6]}"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, default=str)
        os.replace(tmp, path)
        return True
    except Exception as exc:
        HEALTH.flag("archive:local", f"write {path}: {exc}")
        return False


class ChatArchive:
    """threads = {thread_id: {"title","created_at","updated_at","messages":[...]}}"""

    def __init__(self, path: str = CHATS_FILE) -> None:
        self.path = path

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        with _lock:
            return _read_json(self.path, {})

    def load_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        return self.load_all().get(thread_id)

    def save_thread(self, thread_id: str, title: str, messages: List[Dict[str, Any]]) -> bool:
        with _lock:
            threads = _read_json(self.path, {})
            existing = threads.get(thread_id, {})
            threads[thread_id] = {"title": title or existing.get("title") or "New chat",
                                  "created_at": existing.get("created_at") or _now(), "updated_at": _now(),
                                  "messages": messages}
            ok = _write_json_atomic(self.path, threads)
        if ok and config.get("SUPABASE_URL") and config.get("SUPABASE_KEY"):
            self._sync_remote(thread_id, threads[thread_id])
        return ok

    def delete_thread(self, thread_id: str) -> bool:
        with _lock:
            threads = _read_json(self.path, {})
            if thread_id in threads:
                del threads[thread_id]
                return _write_json_atomic(self.path, threads)
        return False

    def list_threads(self) -> List[Dict[str, Any]]:
        threads = self.load_all()
        rows = [{"id": tid, "title": t.get("title", "Untitled"), "updated_at": t.get("updated_at", "")} for tid, t in threads.items()]
        return sorted(rows, key=lambda r: r["updated_at"], reverse=True)

    def new_thread_id(self) -> str:
        return f"thread_{uuid.uuid4().hex[:12]}"

    def _sync_remote(self, thread_id: str, thread: Dict[str, Any]) -> None:
        try:
            from supabase import create_client

            client = create_client(config.get("SUPABASE_URL"), config.get("SUPABASE_KEY"))
            client.table("chat_threads").upsert({"id": thread_id, "title": thread["title"], "updated_at": thread["updated_at"],
                                                 "messages": thread["messages"]}).execute()
            HEALTH.ok("archive:supabase", "chat synced")
        except Exception as exc:
            HEALTH.flag("archive:supabase", f"{exc.__class__.__name__}: {exc}")


class HeritageArchive:
    """Flat JSON list of heritage records, mirroring HeritageStore.records."""

    def __init__(self, path: str = HERITAGE_FILE) -> None:
        self.path = path

    def load(self) -> List[Dict[str, Any]]:
        with _lock:
            return _read_json(self.path, [])

    def save(self, records: List[Dict[str, Any]]) -> bool:
        with _lock:
            ok = _write_json_atomic(self.path, records)
        if ok and config.get("SUPABASE_URL") and config.get("SUPABASE_KEY"):
            self._sync_remote(records)
        return ok

    def _sync_remote(self, records: List[Dict[str, Any]]) -> None:
        try:
            from supabase import create_client

            client = create_client(config.get("SUPABASE_URL"), config.get("SUPABASE_KEY"))
            if records:
                client.table("heritage_records").upsert(records).execute()
            HEALTH.ok("archive:supabase", f"{len(records)} heritage record(s) synced")
        except Exception as exc:
            HEALTH.flag("archive:supabase", f"{exc.__class__.__name__}: {exc}")

    def load_from_remote_if_empty(self) -> List[Dict[str, Any]]:
        local = self.load()
        if local or not (config.get("SUPABASE_URL") and config.get("SUPABASE_KEY")):
            return local
        try:
            from supabase import create_client

            client = create_client(config.get("SUPABASE_URL"), config.get("SUPABASE_KEY"))
            rows = client.table("heritage_records").select("*").execute().data or []
            if rows:
                self.save(rows)
            return rows
        except Exception as exc:
            HEALTH.flag("archive:supabase", f"{exc.__class__.__name__}: {exc}")
            return local


chat_archive = ChatArchive()
heritage_archive = HeritageArchive()
