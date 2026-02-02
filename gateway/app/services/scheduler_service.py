"""
Service de planification des taches automatiques.
Gere les synchronisations programmees Odoo -> MidPoint.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
import structlog
import asyncio
import threading

logger = structlog.get_logger()

# Simple in-memory storage for scheduler data (thread-safe)
class SchedulerStore:
    """Thread-safe storage for scheduler data."""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value


scheduler_store = SchedulerStore()

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


class ScheduledSyncService:
    """Service pour gerer les synchronisations planifiees."""

    def __init__(self):
        self.scheduler = self._get_scheduler()

    def _get_scheduler(self) -> AsyncIOScheduler:
        """Get or create the global scheduler."""
        global scheduler
        if scheduler is None:
            scheduler = AsyncIOScheduler(
                jobstores={'default': MemoryJobStore()},
                job_defaults={
                    'coalesce': True,  # Combine missed executions
                    'max_instances': 1,  # Only one instance at a time
                    'misfire_grace_time': 60 * 5  # 5 minutes grace
                }
            )
        return scheduler

    def start(self):
        """Start the scheduler if not running."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    async def _execute_odoo_midpoint_sync(self, job_id: str):
        """Execute Odoo to MidPoint synchronization."""
        from app.connectors.odoo_connector import OdooConnector
        from app.services.midpoint_client import MidPointClient

        logger.info("Starting scheduled Odoo->MidPoint sync", job_id=job_id)

        # Update job status
        job_status = scheduler_store.get("scheduled_jobs", {})
        if job_id in job_status:
            job_status[job_id]["last_run"] = datetime.utcnow().isoformat()
            job_status[job_id]["status"] = "running"
            scheduler_store.set("scheduled_jobs", job_status)

        results = {
            "job_id": job_id,
            "started_at": datetime.utcnow().isoformat(),
            "synced": 0,
            "skipped": 0,
            "errors": 0,
            "details": []
        }

        try:
            odoo = OdooConnector()
            client = MidPointClient()

            # Get all Odoo employees
            employees = await odoo.list_employees()

            # Get existing MidPoint users
            midpoint_users = await client.get_all_accounts()
            existing_emails = {u.get("email", "").lower() for u in midpoint_users if u.get("email")}
            existing_usernames = {u.get("name", "").lower() for u in midpoint_users if u.get("name")}

            for emp in employees:
                emp_name = emp.get("name", "")
                emp_email = emp.get("email", "")

                # Generate username
                name_parts = emp_name.split()
                if len(name_parts) >= 2:
                    firstname = name_parts[0]
                    lastname = " ".join(name_parts[1:])
                    username = f"{firstname.lower()}{lastname.lower().replace(' ', '')}"
                else:
                    firstname = emp_name
                    lastname = ""
                    username = emp_name.lower().replace(" ", "")

                # Check if exists
                if emp_email and emp_email.lower() in existing_emails:
                    results["skipped"] += 1
                    continue
                if username.lower() in existing_usernames:
                    results["skipped"] += 1
                    continue

                # Create in MidPoint
                try:
                    user_data = {
                        "username": username,
                        "firstname": firstname,
                        "lastname": lastname,
                        "email": emp_email or f"{username}@example.com",
                        "department": emp.get("department"),
                        "title": emp.get("job_title"),
                    }

                    midpoint_result = await client.create_account(user_data)

                    if midpoint_result and midpoint_result.get("status") == "already_exists":
                        results["skipped"] += 1
                    else:
                        results["synced"] += 1
                        results["details"].append({
                            "name": emp_name,
                            "username": username,
                            "status": "created"
                        })

                    # Update tracking sets
                    if emp_email:
                        existing_emails.add(emp_email.lower())
                    existing_usernames.add(username.lower())

                except Exception as e:
                    results["errors"] += 1
                    results["details"].append({
                        "name": emp_name,
                        "status": "error",
                        "error": str(e)[:100]
                    })

            results["completed_at"] = datetime.utcnow().isoformat()
            results["status"] = "completed"

            # Update job status
            if job_id in job_status:
                job_status[job_id]["status"] = "idle"
                job_status[job_id]["last_result"] = results
                scheduler_store.set("scheduled_jobs", job_status)

            # Store execution history
            history = scheduler_store.get("sync_history", [])
            history.insert(0, results)
            # Keep last 50 executions
            scheduler_store.set("sync_history", history[:50])

            logger.info(
                "Scheduled sync completed",
                job_id=job_id,
                synced=results["synced"],
                skipped=results["skipped"],
                errors=results["errors"]
            )

        except Exception as e:
            logger.error("Scheduled sync failed", job_id=job_id, error=str(e))
            results["status"] = "failed"
            results["error"] = str(e)
            results["completed_at"] = datetime.utcnow().isoformat()

            if job_id in job_status:
                job_status[job_id]["status"] = "error"
                job_status[job_id]["last_error"] = str(e)
                scheduler_store.set("scheduled_jobs", job_status)

        return results

    def add_daily_sync(
        self,
        job_id: str,
        hour: int,
        minute: int = 0,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Add a daily sync job at a specific time.

        Args:
            job_id: Unique identifier for the job
            hour: Hour of day (0-23)
            minute: Minute (0-59)
            enabled: Whether the job is enabled
        """
        # Remove existing job if exists
        self.remove_job(job_id)

        if enabled:
            trigger = CronTrigger(hour=hour, minute=minute)

            self.scheduler.add_job(
                self._execute_odoo_midpoint_sync,
                trigger=trigger,
                id=job_id,
                args=[job_id],
                name=f"Daily Odoo->MidPoint sync at {hour:02d}:{minute:02d}"
            )

        # Store job config
        job_status = scheduler_store.get("scheduled_jobs", {})
        job_status[job_id] = {
            "type": "daily",
            "hour": hour,
            "minute": minute,
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat(),
            "status": "idle" if enabled else "disabled",
            "next_run": self._get_next_run(job_id)
        }
        scheduler_store.set("scheduled_jobs", job_status)

        logger.info(
            "Daily sync job configured",
            job_id=job_id,
            hour=hour,
            minute=minute,
            enabled=enabled
        )

        return job_status[job_id]

    def add_interval_sync(
        self,
        job_id: str,
        hours: int = 0,
        minutes: int = 30,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Add an interval-based sync job.

        Args:
            job_id: Unique identifier for the job
            hours: Interval hours
            minutes: Interval minutes
            enabled: Whether the job is enabled
        """
        # Remove existing job if exists
        self.remove_job(job_id)

        if enabled:
            trigger = IntervalTrigger(hours=hours, minutes=minutes)

            self.scheduler.add_job(
                self._execute_odoo_midpoint_sync,
                trigger=trigger,
                id=job_id,
                args=[job_id],
                name=f"Interval Odoo->MidPoint sync every {hours}h {minutes}m"
            )

        # Store job config
        job_status = scheduler_store.get("scheduled_jobs", {})
        job_status[job_id] = {
            "type": "interval",
            "hours": hours,
            "minutes": minutes,
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat(),
            "status": "idle" if enabled else "disabled",
            "next_run": self._get_next_run(job_id)
        }
        scheduler_store.set("scheduled_jobs", job_status)

        logger.info(
            "Interval sync job configured",
            job_id=job_id,
            hours=hours,
            minutes=minutes,
            enabled=enabled
        )

        return job_status[job_id]

    def add_cron_sync(
        self,
        job_id: str,
        cron_expression: str,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Add a cron-based sync job for advanced scheduling.

        Args:
            job_id: Unique identifier for the job
            cron_expression: Cron expression (minute hour day month day_of_week)
            enabled: Whether the job is enabled
        """
        # Remove existing job if exists
        self.remove_job(job_id)

        if enabled:
            # Parse cron expression
            parts = cron_expression.split()
            if len(parts) >= 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )

                self.scheduler.add_job(
                    self._execute_odoo_midpoint_sync,
                    trigger=trigger,
                    id=job_id,
                    args=[job_id],
                    name=f"Cron Odoo->MidPoint sync: {cron_expression}"
                )

        # Store job config
        job_status = scheduler_store.get("scheduled_jobs", {})
        job_status[job_id] = {
            "type": "cron",
            "cron": cron_expression,
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat(),
            "status": "idle" if enabled else "disabled",
            "next_run": self._get_next_run(job_id)
        }
        scheduler_store.set("scheduled_jobs", job_status)

        logger.info(
            "Cron sync job configured",
            job_id=job_id,
            cron=cron_expression,
            enabled=enabled
        )

        return job_status[job_id]

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.remove_job(job_id)

            # Remove from storage
            job_status = scheduler_store.get("scheduled_jobs", {})
            if job_id in job_status:
                del job_status[job_id]
                scheduler_store.set("scheduled_jobs", job_status)

            logger.info("Job removed", job_id=job_id)
            return True
        except Exception as e:
            logger.error("Failed to remove job", job_id=job_id, error=str(e))
            return False

    def toggle_job(self, job_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        """Enable or disable a job."""
        job_status = scheduler_store.get("scheduled_jobs", {})

        if job_id not in job_status:
            return None

        job_config = job_status[job_id]

        if enabled:
            # Re-add the job based on its type
            if job_config["type"] == "daily":
                return self.add_daily_sync(
                    job_id,
                    job_config["hour"],
                    job_config["minute"],
                    enabled=True
                )
            elif job_config["type"] == "interval":
                return self.add_interval_sync(
                    job_id,
                    job_config.get("hours", 0),
                    job_config.get("minutes", 30),
                    enabled=True
                )
            elif job_config["type"] == "cron":
                return self.add_cron_sync(
                    job_id,
                    job_config["cron"],
                    enabled=True
                )
        else:
            # Remove from scheduler but keep config
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass

            job_config["enabled"] = False
            job_config["status"] = "disabled"
            job_config["next_run"] = None
            scheduler_store.set("scheduled_jobs", job_status)

        return job_config

    def run_job_now(self, job_id: str) -> bool:
        """Manually trigger a job to run immediately."""
        job_status = scheduler_store.get("scheduled_jobs", {})

        if job_id not in job_status:
            return False

        # Run the sync in background
        asyncio.create_task(self._execute_odoo_midpoint_sync(job_id))
        return True

    def _get_next_run(self, job_id: str) -> Optional[str]:
        """Get the next scheduled run time for a job."""
        try:
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                return job.next_run_time.isoformat()
        except Exception:
            pass
        return None

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all scheduled jobs with their status."""
        job_status = scheduler_store.get("scheduled_jobs", {})

        jobs = []
        for job_id, config in job_status.items():
            # Update next_run from scheduler
            config["next_run"] = self._get_next_run(job_id)
            config["job_id"] = job_id
            jobs.append(config)

        return jobs

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job's configuration and status."""
        job_status = scheduler_store.get("scheduled_jobs", {})
        if job_id in job_status:
            config = job_status[job_id].copy()
            config["next_run"] = self._get_next_run(job_id)
            config["job_id"] = job_id
            return config
        return None

    def get_sync_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the history of sync executions."""
        history = scheduler_store.get("sync_history", [])
        return history[:limit]


# Global service instance
sync_scheduler = ScheduledSyncService()


def init_scheduler():
    """Initialize and start the scheduler."""
    sync_scheduler.start()
    logger.info("Sync scheduler initialized")


def shutdown_scheduler():
    """Shutdown the scheduler."""
    sync_scheduler.stop()
    logger.info("Sync scheduler shutdown")
