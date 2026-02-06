"""
Service de planification des taches automatiques.
Gere les synchronisations programmees Odoo -> MidPoint.
Inclut: attribution auto roles/groupes, gestion contrats expires.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, time, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
import structlog
import asyncio
import threading

logger = structlog.get_logger()

# ==================== ROLE & GROUP MAPPINGS ====================

# Department to MidPoint Role mapping (role de base par departement)
DEPARTMENT_ROLE_MAPPING = {
    # IT / Informatique
    "it": "role-department-it",
    "informatique": "role-department-it",
    "dsi": "role-department-it",
    "si": "role-department-it",
    # RH / HR
    "hr": "role-department-hr",
    "rh": "role-department-hr",
    "ressources-humaines": "role-department-hr",
    # Finance / Comptabilite
    "finance": "role-department-finance",
    "comptabilite": "role-department-finance",
    "accounting": "role-department-finance",
    # Ventes / Commercial
    "sales": "role-department-sales",
    "ventes": "role-department-sales",
    "commercial": "role-department-sales",
    # Marketing / Communication
    "marketing": "role-department-marketing",
    "communication": "role-department-marketing",
    # Direction / Management
    "management": "role-department-management",
    "direction": "role-department-management",
    "executive": "role-department-management",
    # R&D / Recherche
    "rd": "role-department-rd",
    "r&d": "role-department-rd",
    "recherche": "role-department-rd",
    "research": "role-department-rd",
    # Support / Helpdesk
    "support": "role-department-support",
    "helpdesk": "role-department-support",
    "assistance": "role-department-support",
    # Juridique / Legal
    "juridique": "role-department-legal",
    "legal": "role-department-legal",
    # Production / Operations
    "production": "role-department-production",
    "operations": "role-department-production",
    # Qualite
    "qualite": "role-department-quality",
    "quality": "role-department-quality",
    # Logistique
    "logistique": "role-department-logistics",
    "logistics": "role-department-logistics",
    # Default
    "default": "role-employee-full"
}

# Job Title to Additional Roles mapping (roles supplementaires par poste)
JOB_TITLE_ROLE_MAPPING = {
    # Developpeurs
    "developpeur": ["role-developer", "role-git-access"],
    "developer": ["role-developer", "role-git-access"],
    "dev": ["role-developer", "role-git-access"],
    "programmeur": ["role-developer", "role-git-access"],
    "ingenieur logiciel": ["role-developer", "role-git-access", "role-senior"],
    "software engineer": ["role-developer", "role-git-access", "role-senior"],
    # DevOps / SysAdmin
    "devops": ["role-devops", "role-server-access", "role-git-access"],
    "sysadmin": ["role-sysadmin", "role-server-access"],
    "administrateur systeme": ["role-sysadmin", "role-server-access"],
    "admin systeme": ["role-sysadmin", "role-server-access"],
    # Managers / Responsables
    "manager": ["role-manager", "role-reports-access"],
    "responsable": ["role-manager", "role-reports-access"],
    "chef de projet": ["role-project-manager", "role-manager"],
    "project manager": ["role-project-manager", "role-manager"],
    "chef d'equipe": ["role-team-lead", "role-manager"],
    "team lead": ["role-team-lead", "role-manager"],
    # Directeurs
    "directeur": ["role-director", "role-manager", "role-reports-access", "role-budget-access"],
    "director": ["role-director", "role-manager", "role-reports-access", "role-budget-access"],
    "dsi": ["role-cio", "role-director", "role-admin-it"],
    "cio": ["role-cio", "role-director", "role-admin-it"],
    "cto": ["role-cto", "role-director", "role-admin-it"],
    "ceo": ["role-ceo", "role-director", "role-admin-full"],
    "pdg": ["role-ceo", "role-director", "role-admin-full"],
    # Analystes
    "analyste": ["role-analyst", "role-reports-access"],
    "analyst": ["role-analyst", "role-reports-access"],
    "data analyst": ["role-data-analyst", "role-database-read"],
    "business analyst": ["role-business-analyst", "role-reports-access"],
    # Support
    "technicien": ["role-technician", "role-helpdesk"],
    "technician": ["role-technician", "role-helpdesk"],
    "support": ["role-support", "role-helpdesk"],
    "helpdesk": ["role-support", "role-helpdesk"],
    # Consultants
    "consultant": ["role-consultant", "role-external"],
    "prestataire": ["role-contractor", "role-external"],
    "contractor": ["role-contractor", "role-external"],
    "stagiaire": ["role-intern", "role-limited"],
    "intern": ["role-intern", "role-limited"],
    # Admin
    "administrateur": ["role-admin"],
    "admin": ["role-admin"],
}

# Department to LDAP Group mapping (groupe principal)
DEPARTMENT_GROUP_MAPPING = {
    "it": "IT",
    "informatique": "IT",
    "dsi": "IT",
    "hr": "RH",
    "rh": "RH",
    "ressources-humaines": "RH",
    "finance": "Finance",
    "comptabilite": "Finance",
    "sales": "Sales",
    "ventes": "Sales",
    "commercial": "Sales",
    "marketing": "Marketing",
    "communication": "Marketing",
    "management": "Management",
    "direction": "Management",
    "rd": "R&D",
    "r&d": "R&D",
    "recherche": "R&D",
    "support": "Support",
    "helpdesk": "Support",
    "juridique": "Legal",
    "legal": "Legal",
    "production": "Production",
    "operations": "Production",
    "qualite": "Quality",
    "logistique": "Logistics",
    "default": "Employees"
}

# Job Title to Additional LDAP Groups mapping
JOB_TITLE_GROUP_MAPPING = {
    # Developpeurs
    "developpeur": ["Developers", "Git-Users"],
    "developer": ["Developers", "Git-Users"],
    "dev": ["Developers", "Git-Users"],
    # DevOps
    "devops": ["DevOps", "Developers", "Server-Admins"],
    "sysadmin": ["SysAdmins", "Server-Admins"],
    "administrateur systeme": ["SysAdmins", "Server-Admins"],
    # Managers
    "manager": ["Managers"],
    "responsable": ["Managers"],
    "chef de projet": ["Project-Managers", "Managers"],
    "project manager": ["Project-Managers", "Managers"],
    "chef d'equipe": ["Team-Leads", "Managers"],
    # Directeurs
    "directeur": ["Directors", "Managers", "VIP"],
    "director": ["Directors", "Managers", "VIP"],
    "dsi": ["Directors", "IT-Admins", "VIP"],
    "cto": ["Directors", "IT-Admins", "VIP"],
    "ceo": ["Directors", "Executive", "VIP"],
    # Support
    "technicien": ["Technicians", "Helpdesk"],
    "support": ["Helpdesk"],
    # Externes
    "consultant": ["External", "Consultants"],
    "prestataire": ["External", "Contractors"],
    "stagiaire": ["Interns", "Limited-Access"],
}

# Acces speciaux par departement (groupes supplementaires automatiques)
DEPARTMENT_EXTRA_GROUPS = {
    "it": ["VPN-Users", "Server-Access"],
    "rd": ["VPN-Users", "Lab-Access"],
    "management": ["VPN-Users", "Reports-Access"],
    "finance": ["Accounting-System"],
}

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
        """Execute Odoo to MidPoint synchronization with auto role/group assignment."""
        from app.connectors.odoo_connector import OdooConnector
        from app.connectors.ldap_connector import LDAPConnector
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
            "roles_assigned": 0,
            "groups_assigned": 0,
            "details": []
        }

        try:
            odoo = OdooConnector()
            client = MidPointClient()
            ldap = LDAPConnector()

            # Get all Odoo employees
            employees = await odoo.list_employees()

            # Get existing MidPoint users
            midpoint_users = await client.get_all_accounts()
            existing_emails = {u.get("email", "").lower() for u in midpoint_users if u.get("email")}
            existing_usernames = {u.get("name", "").lower() for u in midpoint_users if u.get("name")}

            for emp in employees:
                emp_name = emp.get("name", "")
                emp_email = emp.get("email", "")
                dept_normalized = emp.get("department_normalized", "default")

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
                user_exists = False
                if emp_email and emp_email.lower() in existing_emails:
                    user_exists = True
                if username.lower() in existing_usernames:
                    user_exists = True

                if user_exists:
                    results["skipped"] += 1
                    # Still try to assign role/group if user exists
                    await self._assign_role_and_group(
                        client, ldap, username, dept_normalized, results,
                        job_title=emp.get("job_title")
                    )
                    continue

                # Create in MidPoint
                try:
                    # Get role based on department
                    role_name = DEPARTMENT_ROLE_MAPPING.get(dept_normalized, DEPARTMENT_ROLE_MAPPING["default"])

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

                        # Auto-assign roles and groups based on department and job title
                        role_group_result = await self._assign_role_and_group(
                            client, ldap, username, dept_normalized, results,
                            job_title=emp.get("job_title")
                        )

                        results["details"].append({
                            "name": emp_name,
                            "username": username,
                            "department": emp.get("department"),
                            "job_title": emp.get("job_title"),
                            "status": "created",
                            "roles_assigned": role_group_result.get("roles", []),
                            "groups_assigned": role_group_result.get("groups", [])
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
                errors=results["errors"],
                roles_assigned=results["roles_assigned"],
                groups_assigned=results["groups_assigned"]
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

    async def _assign_role_and_group(
        self,
        midpoint_client,
        ldap_connector,
        username: str,
        department: str,
        results: Dict[str, Any],
        job_title: str = None
    ) -> Dict[str, Any]:
        """Assign MidPoint roles and LDAP groups based on department and job title."""
        assignment_result = {"roles": [], "groups": []}

        # Normalize job title for lookup
        job_title_lower = job_title.lower().strip() if job_title else ""

        # ==================== MIDPOINT ROLES ====================

        roles_to_assign = []

        # 1. Role de base par departement
        dept_role = DEPARTMENT_ROLE_MAPPING.get(department, DEPARTMENT_ROLE_MAPPING["default"])
        roles_to_assign.append(dept_role)

        # 2. Roles additionnels par poste/fonction
        for title_key, title_roles in JOB_TITLE_ROLE_MAPPING.items():
            if title_key in job_title_lower:
                roles_to_assign.extend(title_roles)
                break

        # 3. Role employe de base pour tout le monde
        if "role-employee-full" not in roles_to_assign:
            roles_to_assign.append("role-employee-full")

        # Deduplicate roles
        roles_to_assign = list(set(roles_to_assign))

        # Assign all roles
        for role_name in roles_to_assign:
            try:
                role_result = await midpoint_client.assign_role_by_name(username, role_name)
                if role_result:
                    results["roles_assigned"] += 1
                    assignment_result["roles"].append(role_name)
                    logger.info("Role assigned", username=username, role=role_name)
            except Exception as e:
                logger.warning("Failed to assign role", username=username, role=role_name, error=str(e))

        # ==================== LDAP GROUPS ====================

        groups_to_assign = []

        # 1. Groupe principal par departement
        dept_group = DEPARTMENT_GROUP_MAPPING.get(department, DEPARTMENT_GROUP_MAPPING["default"])
        groups_to_assign.append(dept_group)

        # 2. Groupes additionnels par poste/fonction
        for title_key, title_groups in JOB_TITLE_GROUP_MAPPING.items():
            if title_key in job_title_lower:
                groups_to_assign.extend(title_groups)
                break

        # 3. Groupes supplementaires par departement (ex: VPN pour IT)
        if department in DEPARTMENT_EXTRA_GROUPS:
            groups_to_assign.extend(DEPARTMENT_EXTRA_GROUPS[department])

        # 4. Groupe Employees pour tout le monde
        if "Employees" not in groups_to_assign:
            groups_to_assign.append("Employees")

        # Deduplicate groups
        groups_to_assign = list(set(groups_to_assign))

        # Assign all groups
        for group_cn in groups_to_assign:
            try:
                group_result = await ldap_connector.add_to_group(username, group_cn)
                if group_result:
                    results["groups_assigned"] += 1
                    assignment_result["groups"].append(group_cn)
                    logger.info("Group assigned", username=username, group=group_cn)
            except Exception as e:
                logger.warning("Failed to assign group", username=username, group=group_cn, error=str(e))

        return assignment_result

    async def _execute_contract_expiration_check(self, job_id: str):
        """Check for expired contracts and deactivate accounts."""
        from app.connectors.odoo_connector import OdooConnector
        from app.connectors.ldap_connector import LDAPConnector
        from app.services.midpoint_client import MidPointClient

        logger.info("Starting contract expiration check", job_id=job_id)

        results = {
            "job_id": job_id,
            "started_at": datetime.utcnow().isoformat(),
            "expired_found": 0,
            "deactivated": 0,
            "errors": 0,
            "details": []
        }

        try:
            odoo = OdooConnector()
            client = MidPointClient()
            ldap = LDAPConnector()

            # Get expired contracts
            expired = await odoo.get_expired_contracts()
            results["expired_found"] = len(expired)

            for item in expired:
                emp = item["employee"]
                contract = item["contract"]
                emp_name = emp.get("name", "")
                emp_email = emp.get("email", "")

                # Generate username
                name_parts = emp_name.split()
                if len(name_parts) >= 2:
                    username = f"{name_parts[0].lower()}{name_parts[1].lower()}"
                else:
                    username = emp_name.lower().replace(" ", "")

                try:
                    # Deactivate in MidPoint
                    await client.disable_account(username)

                    # Deactivate in LDAP
                    await ldap.disable_account(username)

                    # Deactivate in Odoo
                    if emp.get("user_id"):
                        await odoo.disable_account(str(emp["user_id"]))

                    results["deactivated"] += 1
                    results["details"].append({
                        "name": emp_name,
                        "username": username,
                        "contract_end": contract.get("date_end"),
                        "status": "deactivated"
                    })

                    logger.info(
                        "Account deactivated due to contract expiration",
                        username=username,
                        contract_end=contract.get("date_end")
                    )

                except Exception as e:
                    results["errors"] += 1
                    results["details"].append({
                        "name": emp_name,
                        "status": "error",
                        "error": str(e)[:100]
                    })

            results["completed_at"] = datetime.utcnow().isoformat()
            results["status"] = "completed"

            # Store in history
            history = scheduler_store.get("contract_check_history", [])
            history.insert(0, results)
            scheduler_store.set("contract_check_history", history[:50])

            logger.info(
                "Contract expiration check completed",
                job_id=job_id,
                expired_found=results["expired_found"],
                deactivated=results["deactivated"]
            )

        except Exception as e:
            logger.error("Contract expiration check failed", job_id=job_id, error=str(e))
            results["status"] = "failed"
            results["error"] = str(e)

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

    def add_contract_check(
        self,
        job_id: str,
        hour: int = 6,
        minute: int = 0,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Add a daily job to check for expired contracts.

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
                self._execute_contract_expiration_check,
                trigger=trigger,
                id=job_id,
                args=[job_id],
                name=f"Daily contract expiration check at {hour:02d}:{minute:02d}"
            )

        # Store job config
        job_status = scheduler_store.get("scheduled_jobs", {})
        job_status[job_id] = {
            "type": "contract_check",
            "hour": hour,
            "minute": minute,
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat(),
            "status": "idle" if enabled else "disabled",
            "next_run": self._get_next_run(job_id)
        }
        scheduler_store.set("scheduled_jobs", job_status)

        logger.info(
            "Contract check job configured",
            job_id=job_id,
            hour=hour,
            minute=minute,
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
            elif job_config["type"] == "contract_check":
                return self.add_contract_check(
                    job_id,
                    job_config.get("hour", 6),
                    job_config.get("minute", 0),
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
