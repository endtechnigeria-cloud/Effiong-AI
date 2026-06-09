# src/services/agent_scheduler.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import threading
import time

from src.services.agent_service import agent_service
from src.services.operator_service import operator_service


class AgentScheduler:
    """
    ============================================================
    EFFIONG AI AGENT SCHEDULER ENGINE
    ============================================================

    Problem #11

    PURPOSE
    -------
    Runs autonomous agents on schedules.

    Supports:

    - Scheduled research
    - Scheduled predictions
    - Heritage monitoring
    - Repository monitoring
    - Future event tracking
    - Verification queue processing
    - Knowledge graph maintenance

    FUTURE CAPABILITIES
    -------------------
    - Daily African Heritage Scan
    - Weekly Historical Report
    - Geopolitical Monitoring
    - Repository Synchronization
    - Prediction Recalculation
    - Automated Fact Verification
    """

    def __init__(self):

        self.jobs = {}

        self.running = False

        self.scheduler_thread = None

    # =========================================================
    # CREATE JOB
    # =========================================================

    def create_job(
        self,
        name: str,
        agent_type: str,
        objective: str,
        interval_minutes: int
    ) -> str:

        job_id = str(uuid.uuid4())

        self.jobs[job_id] = {

            "job_id":
                job_id,

            "name":
                name,

            "agent_type":
                agent_type,

            "objective":
                objective,

            "interval_minutes":
                interval_minutes,

            "status":
                "active",

            "last_run":
                None,

            "next_run":
                datetime.utcnow(),

            "execution_count":
                0,

            "created_at":
                datetime.utcnow().isoformat()
        }

        return job_id

    # =========================================================
    # DELETE JOB
    # =========================================================

    def delete_job(
        self,
        job_id: str
    ) -> bool:

        if job_id in self.jobs:

            del self.jobs[job_id]

            return True

        return False

    # =========================================================
    # PAUSE JOB
    # =========================================================

    def pause_job(
        self,
        job_id: str
    ) -> bool:

        if job_id in self.jobs:

            self.jobs[job_id]["status"] = "paused"

            return True

        return False

    # =========================================================
    # RESUME JOB
    # =========================================================

    def resume_job(
        self,
        job_id: str
    ) -> bool:

        if job_id in self.jobs:

            self.jobs[job_id]["status"] = "active"

            return True

        return False

    # =========================================================
    # EXECUTE JOB
    # =========================================================

    def execute_job(
        self,
        job_id: str
    ):

        if job_id not in self.jobs:
            return

        job = self.jobs[job_id]

        try:

            result = agent_service.execute_agent(

                agent_type=job["agent_type"],

                objective=job["objective"]
            )

            job["last_run"] = (
                datetime.utcnow()
            )

            job["next_run"] = (
                datetime.utcnow()
                +
                timedelta(
                    minutes=job["interval_minutes"]
                )
            )

            job["execution_count"] += 1

            operator_service.log_user_event(

                "scheduled_agent_execution",

                {
                    "job_id":
                        job_id,

                    "agent_type":
                        job["agent_type"],

                    "status":
                        result["status"]
                }
            )

        except Exception as e:

            operator_service.raise_alert(

                "warning",

                f"Scheduler job failed: {str(e)}"
            )

    # =========================================================
    # CHECK DUE JOBS
    # =========================================================

    def check_due_jobs(self):

        now = datetime.utcnow()

        for job_id, job in self.jobs.items():

            if job["status"] != "active":
                continue

            if job["next_run"] <= now:

                self.execute_job(job_id)

    # =========================================================
    # MAIN LOOP
    # =========================================================

    def scheduler_loop(self):

        while self.running:

            try:

                self.check_due_jobs()

            except Exception as e:

                operator_service.raise_alert(

                    "critical",

                    f"Scheduler Loop Error: {str(e)}"
                )

            time.sleep(30)

    # =========================================================
    # START
    # =========================================================

    def start(self):

        if self.running:
            return

        self.running = True

        self.scheduler_thread = threading.Thread(

            target=self.scheduler_loop,

            daemon=True
        )

        self.scheduler_thread.start()

    # =========================================================
    # STOP
    # =========================================================

    def stop(self):

        self.running = False

    # =========================================================
    # DEFAULT AGENTS
    # =========================================================

    def install_default_jobs(self):

        self.create_job(

            name="Daily Heritage Scan",

            agent_type="heritage_agent",

            objective="Monitor African historical developments",

            interval_minutes=1440
        )

        self.create_job(

            name="Repository Synchronization",

            agent_type="research_agent",

            objective="Scan repositories for new knowledge",

            interval_minutes=360
        )

        self.create_job(

            name="Prediction Refresh",

            agent_type="prediction_agent",

            objective="Update prediction models",

            interval_minutes=720
        )

    # =========================================================
    # JOB LIST
    # =========================================================

    def get_jobs(self) -> List[Dict]:

        return list(self.jobs.values())

    # =========================================================
    # DASHBOARD VIEW
    # =========================================================

    def scheduler_dashboard(self) -> Dict:

        active_jobs = sum(

            1

            for job in self.jobs.values()

            if job["status"] == "active"
        )

        paused_jobs = sum(

            1

            for job in self.jobs.values()

            if job["status"] == "paused"
        )

        return {

            "scheduler_running":
                self.running,

            "total_jobs":
                len(self.jobs),

            "active_jobs":
                active_jobs,

            "paused_jobs":
                paused_jobs,

            "jobs":
                self.get_jobs()
        }

    # =========================================================
    # HEALTH CHECK
    # =========================================================

    def health_check(self):

        return {

            "service":
                "agent_scheduler",

            "status":
                "online",

            "running":
                self.running,

            "registered_jobs":
                len(self.jobs)
        }


# ============================================================
# GLOBAL INSTANCE
# ============================================================

agent_scheduler = AgentScheduler()