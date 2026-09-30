"""
EFFIONG AI - Agent scheduler (continuous self-learning)
=======================================================
Runs agents on a timer inside the server process.  Off by default; enable with  ENABLE_BACKGROUND_LEARNING=true.
Only one scheduler ever runs per process, and every job is time-boxed so it cannot starve the portal.
"""
from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from src import config
from src.core.health import HEALTH, write_operator_log
from src.services.agent_service import agent_service

DEFAULT_TOPICS = [
    "African history archaeology discoveries", "oral tradition preservation Africa", "African kingdoms and empires history",
    "African languages preservation", "Africa heritage restitution artefacts", "African Union news", "AfCFTA trade news",
]


class AgentScheduler:
    def __init__(self) -> None:
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def create_job(self, name: str, agent_type: str, objective: str, interval_minutes: int) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self.jobs[job_id] = {"job_id": job_id, "name": name, "agent_type": agent_type, "objective": objective,
                                 "interval_minutes": interval_minutes, "status": "active", "last_run": None,
                                 "next_run": datetime.now(timezone.utc), "execution_count": 0, "last_result": None}
        return job_id

    def pause_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = "paused"
                return True
        return False

    def resume_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = "active"
                return True
        return False

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            return self.jobs.pop(job_id, None) is not None

    def execute_job(self, job_id: str) -> None:
        job = self.jobs.get(job_id)
        if not job:
            return
        try:
            job["last_result"] = agent_service.execute_agent(job["agent_type"], job["objective"])
        except Exception as exc:
            job["last_result"] = {"status": "FAILED", "error": str(exc)}
            HEALTH.flag("scheduler", f"{job['name']}: {exc}")
        job["last_run"] = datetime.now(timezone.utc)
        job["execution_count"] += 1
        job["next_run"] = job["last_run"] + timedelta(minutes=job["interval_minutes"])
        write_operator_log("agent_job", {"job": job["name"], "result": job["last_result"]})

    def _loop(self) -> None:
        while self.running:
            now = datetime.now(timezone.utc)
            for job_id, job in list(self.jobs.items()):
                if job["status"] == "active" and job["next_run"] <= now:
                    self.execute_job(job_id)
            time.sleep(30)

    def start(self) -> None:
        with self._lock:
            if self.running:
                return
            self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="effiong-scheduler")
        self._thread.start()

    def stop(self) -> None:
        self.running = False


scheduler = AgentScheduler()
_started = False


def start_background_learning() -> bool:
    """Idempotent: call from app start-up. Returns True if learning is (now) active."""
    global _started
    if not config.get_bool("ENABLE_BACKGROUND_LEARNING", False):
        return False
    if _started:
        return True
    _started = True
    minutes = config.get_int("LEARNING_INTERVAL_MINUTES", 360)
    for i, topic in enumerate(DEFAULT_TOPICS):
        job_id = scheduler.create_job(f"scan: {topic}", "heritage_scan", topic, minutes * max(1, len(DEFAULT_TOPICS)) // 1)
        scheduler.jobs[job_id]["next_run"] = datetime.now(timezone.utc) + timedelta(minutes=minutes * i // max(1, len(DEFAULT_TOPICS)) + 1)
    scheduler.start()
    return True
