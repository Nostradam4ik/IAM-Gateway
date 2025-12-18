"""
Stockage pour les operations et reconciliations.
Utilise PostgreSQL pour persister les donnees entre redemarrages.
Les donnees de demo ne sont plus generees - seules les vraies operations sont enregistrees.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import structlog
import uuid
import json

from app.core.config import settings

logger = structlog.get_logger()


class MemoryStore:
    """Stockage persistant dans PostgreSQL."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        # Cache local pour acces rapide (synchronise avec DB)
        self.operations: Dict[str, Any] = {}
        self.reconciliation_jobs: Dict[str, Any] = {}
        self.audit_logs: List[Dict[str, Any]] = []
        self.discrepancies: Dict[str, List[Any]] = {}
        self.workflows: Dict[str, Any] = {}
        self._cache_loaded = False
        # NE PAS charger de donnees de demo - on charge depuis la DB

    async def ensure_cache_loaded(self):
        """Charge le cache depuis la base de donnees."""
        if self._cache_loaded:
            return
        await self._load_from_database()
        self._cache_loaded = True

    async def _load_from_database(self):
        """Charge les donnees existantes depuis PostgreSQL."""
        try:
            async with self.async_session() as session:
                # Charger les operations
                result = await session.execute(text("""
                    SELECT id, request_id, operation_type, status, target_system,
                           identity_id, attributes, calculated_attributes,
                           error_message, created_at, updated_at
                    FROM provisioning_operations
                    ORDER BY created_at DESC
                    LIMIT 500
                """))
                rows = result.fetchall()

                self.operations = {}
                for row in rows:
                    op_id = str(row[0])
                    # Parse target_systems from comma-separated string
                    target_system_str = row[4] or ""
                    target_systems = target_system_str.split(",") if target_system_str else []

                    # Build calculated_attributes structure
                    calc_attrs = row[7] or {}
                    if target_systems and not calc_attrs:
                        # Create structure for display
                        calc_attrs = {ts: {} for ts in target_systems}

                    self.operations[op_id] = {
                        "operation_id": op_id,
                        "request_id": row[1],
                        "operation_type": row[2],
                        "status": row[3],
                        "target_systems": target_systems,
                        "account_id": row[5],
                        "user_data": row[6] or {},
                        "calculated_attributes": calc_attrs,
                        "message": row[8] or "",
                        "timestamp": row[9].isoformat() if row[9] else datetime.utcnow().isoformat(),
                        "updated_at": row[10].isoformat() if row[10] else None
                    }

                # Charger les logs d'audit
                result = await session.execute(text("""
                    SELECT id, timestamp, event_type, target_system, identity_id,
                           action, status, actor, details
                    FROM audit_logs
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """))
                rows = result.fetchall()

                self.audit_logs = []
                for i, row in enumerate(rows):
                    self.audit_logs.append({
                        "id": i + 1,
                        "db_id": str(row[0]),
                        "created_at": row[1].isoformat() if row[1] else datetime.utcnow().isoformat(),
                        "event_type": row[2] or "unknown",
                        "target_system": row[3] or "",
                        "account_id": row[4] or "",
                        "action": row[5] or "-",
                        "severity": row[6] or "info",
                        "actor": row[7] or "system",
                        "details": row[8] or {}
                    })

                # Charger les jobs de reconciliation
                result = await session.execute(text("""
                    SELECT id, target_system, status, started_at, completed_at,
                           total_accounts, matched_accounts, discrepancies, triggered_by
                    FROM reconciliation_jobs
                    ORDER BY started_at DESC
                    LIMIT 100
                """))
                rows = result.fetchall()

                self.reconciliation_jobs = {}
                for row in rows:
                    job_id = str(row[0])
                    self.reconciliation_jobs[job_id] = {
                        "id": job_id,
                        "target_systems": [row[1]] if row[1] else [],
                        "status": row[2] or "pending",
                        "started_at": row[3].isoformat() if row[3] else None,
                        "completed_at": row[4].isoformat() if row[4] else None,
                        "total_accounts": row[5] or 0,
                        "processed_accounts": row[6] or 0,
                        "discrepancies_found": row[7] or 0,
                        "started_by": row[8] or "system"
                    }

                # Charger les workflows
                result = await session.execute(text("""
                    SELECT id, workflow_id, operation_id, status, current_level, total_levels,
                           user_name, operation_name, pending_approvers, context,
                           approve_token, reject_token, email_sent, decided_at, decided_by,
                           created_at, expires_at
                    FROM workflows
                    ORDER BY created_at DESC
                    LIMIT 200
                """))
                rows = result.fetchall()

                self.workflows = {}
                for row in rows:
                    wf_id = str(row[0])
                    pending_approvers_str = row[8] or ""
                    pending_approvers = pending_approvers_str.split(",") if pending_approvers_str else []

                    self.workflows[wf_id] = {
                        "id": wf_id,
                        "workflow_id": row[1],
                        "operation_id": row[2],
                        "status": row[3] or "pending",
                        "current_level": row[4] or 1,
                        "total_levels": row[5] or 1,
                        "user_name": row[6] or "",
                        "operation_name": row[7] or "",
                        "pending_approvers": pending_approvers,
                        "context": row[9] or {},
                        "approve_token": row[10],
                        "reject_token": row[11],
                        "email_sent": row[12] or False,
                        "decided_at": row[13].isoformat() if row[13] else None,
                        "decided_by": row[14],
                        "created_at": row[15].isoformat() if row[15] else datetime.utcnow().isoformat(),
                        "expires_at": row[16].isoformat() if row[16] else None
                    }

                logger.info(
                    "Database cache loaded",
                    operations=len(self.operations),
                    audit_logs=len(self.audit_logs),
                    recon_jobs=len(self.reconciliation_jobs),
                    workflows=len(self.workflows)
                )

        except Exception as e:
            logger.error("Failed to load from database", error=str(e))
            # En cas d'erreur, on garde des dictionnaires vides

    def _run_async(self, coro):
        """Execute une coroutine de maniere synchrone."""
        try:
            loop = asyncio.get_running_loop()
            # Si on est dans une loop, creer une task
            future = asyncio.ensure_future(coro)
            return None  # On ne peut pas attendre
        except RuntimeError:
            # Pas de loop en cours, en creer une nouvelle
            return asyncio.run(coro)

    # Operations
    def save_operation(self, operation_id: str, operation_data: Dict[str, Any]) -> None:
        """Sauvegarde une operation dans PostgreSQL et le cache."""
        # Mettre a jour le cache immediatement
        self.operations[operation_id] = {
            **operation_data,
            "operation_id": operation_id,
            "saved_at": datetime.utcnow().isoformat()
        }

        # Sauvegarder en DB de maniere asynchrone
        async def _save():
            try:
                async with self.async_session() as session:
                    account_id = operation_data.get("account_id", "")
                    status = operation_data.get("status", "pending")
                    target_systems = operation_data.get("target_systems", [])
                    target_system = ",".join(target_systems) if isinstance(target_systems, list) else str(target_systems)
                    attributes = operation_data.get("user_data", operation_data.get("attributes", {}))
                    calculated = operation_data.get("calculated_attributes", {})
                    message = operation_data.get("message", "")

                    await session.execute(text("""
                        INSERT INTO provisioning_operations
                        (id, request_id, operation_type, status, target_system, identity_id, identity_type,
                         attributes, calculated_attributes, error_message, created_at)
                        VALUES (:id, :request_id, :op_type, :status, :target, :identity, :identity_type,
                                CAST(:attrs AS jsonb), CAST(:calc AS jsonb), :msg, :created)
                        ON CONFLICT (id) DO UPDATE SET
                            status = EXCLUDED.status,
                            calculated_attributes = EXCLUDED.calculated_attributes,
                            error_message = EXCLUDED.error_message,
                            updated_at = CURRENT_TIMESTAMP
                    """), {
                        "id": operation_id,
                        "request_id": operation_id[:8],
                        "op_type": operation_data.get("operation", "create"),
                        "status": status,
                        "target": target_system,
                        "identity": account_id,
                        "identity_type": "employee",
                        "attrs": json.dumps(attributes) if attributes else "{}",
                        "calc": json.dumps(calculated) if calculated else "{}",
                        "msg": message,
                        "created": datetime.utcnow()
                    })
                    await session.commit()
                    logger.info("Operation saved to database", operation_id=operation_id)
            except Exception as e:
                logger.error("Failed to save operation to DB", error=str(e))

        self._run_async(_save())

    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Recupere une operation par ID."""
        return self.operations.get(operation_id)

    def list_operations(
        self,
        account_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Liste les operations avec filtres."""
        ops = list(self.operations.values())

        if account_id:
            ops = [o for o in ops if o.get("account_id") == account_id]

        if status:
            ops = [o for o in ops if o.get("status") == status]

        ops.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return ops[offset:offset + limit]

    def update_operation(self, operation_id: str, updates: Dict[str, Any]) -> None:
        """Met a jour une operation."""
        if operation_id in self.operations:
            self.operations[operation_id].update(updates)
            self.operations[operation_id]["updated_at"] = datetime.utcnow().isoformat()
            # Re-sauvegarder en DB
            self.save_operation(operation_id, self.operations[operation_id])

    # Reconciliation Jobs
    def save_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Sauvegarde un job de reconciliation."""
        self.reconciliation_jobs[job_id] = {
            **job_data,
            "saved_at": datetime.utcnow().isoformat()
        }

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Recupere un job par ID."""
        return self.reconciliation_jobs.get(job_id)

    def list_jobs(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Liste les jobs de reconciliation."""
        jobs = list(self.reconciliation_jobs.values())
        jobs.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return jobs[offset:offset + limit]

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        """Met a jour un job."""
        if job_id in self.reconciliation_jobs:
            self.reconciliation_jobs[job_id].update(updates)

    # Discrepancies
    def save_discrepancies(self, job_id: str, discrepancies: List[Any]) -> None:
        """Sauvegarde les divergences d'un job."""
        self.discrepancies[job_id] = discrepancies

    def get_discrepancies(self, job_id: str) -> List[Any]:
        """Recupere les divergences d'un job."""
        return self.discrepancies.get(job_id, [])

    # Audit Logs
    def add_audit_log(self, log_entry: Dict[str, Any]) -> None:
        """Ajoute une entree d'audit dans PostgreSQL et le cache."""
        target_systems = log_entry.get("target_systems", [])
        target_system = target_systems[0] if target_systems else log_entry.get("target_system", "")

        log_type = log_entry.get("type", "info")
        action = log_entry.get("action", "")
        event_type = f"{log_type}_{action}" if action else log_type

        status = log_entry.get("status", "")
        if status == "error" or status == "failed":
            severity = "error"
        elif status == "warning":
            severity = "warning"
        else:
            severity = "info"

        log_id = str(uuid.uuid4())
        normalized_entry = {
            "id": len(self.audit_logs) + 1,
            "db_id": log_id,
            "created_at": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "action": action or log_entry.get("action", "-"),
            "account_id": log_entry.get("account_id", log_entry.get("job_id", "")),
            "actor": log_entry.get("actor", "system"),
            "target_system": target_system,
            "severity": severity,
            "details": log_entry
        }

        self.audit_logs.insert(0, normalized_entry)
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[:1000]

        # Sauvegarder en DB
        async def _save():
            try:
                async with self.async_session() as session:
                    await session.execute(text("""
                        INSERT INTO audit_logs
                        (id, timestamp, event_type, target_system, identity_id, action, status, actor, details)
                        VALUES (:id, :ts, :event_type, :target, :identity, :action, :status, :actor, CAST(:details AS jsonb))
                    """), {
                        "id": log_id,
                        "ts": datetime.utcnow(),
                        "event_type": event_type,
                        "target": target_system,
                        "identity": log_entry.get("account_id", log_entry.get("job_id", "")),
                        "action": action or log_entry.get("action", "-"),
                        "status": severity,
                        "actor": log_entry.get("actor", "system"),
                        "details": json.dumps(log_entry)
                    })
                    await session.commit()
                    logger.info("Audit log saved to database", event_type=event_type)
            except Exception as e:
                logger.error("Failed to save audit log to DB", error=str(e))

        self._run_async(_save())

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Recupere les logs recents."""
        return self.audit_logs[:limit]

    def search_logs(self, query: str, log_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Recherche dans les logs."""
        results = self.audit_logs

        if log_type:
            results = [l for l in results if l.get("event_type") == log_type]

        if query:
            query_lower = query.lower()
            results = [
                l for l in results
                if query_lower in str(l).lower()
            ]

        return results[:limit]

    # Workflows
    def _parse_datetime(self, value) -> Optional[datetime]:
        """Convertit une valeur en datetime."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return None
        return None

    def save_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> None:
        """Sauvegarde un workflow dans PostgreSQL et le cache."""
        self.workflows[workflow_id] = {
            **workflow_data,
            "saved_at": datetime.utcnow().isoformat()
        }

        # Sauvegarder en DB de maniere asynchrone
        async def _save():
            try:
                async with self.async_session() as session:
                    pending_approvers = workflow_data.get("pending_approvers", [])
                    pending_approvers_str = ",".join(pending_approvers) if isinstance(pending_approvers, list) else str(pending_approvers)
                    context = workflow_data.get("context", {})

                    # Convertir les dates
                    decided_at = self._parse_datetime(workflow_data.get("decided_at"))
                    created_at = self._parse_datetime(workflow_data.get("created_at")) or datetime.utcnow()
                    expires_at = self._parse_datetime(workflow_data.get("expires_at"))

                    await session.execute(text("""
                        INSERT INTO workflows
                        (id, workflow_id, operation_id, status, current_level, total_levels,
                         user_name, operation_name, pending_approvers, context,
                         approve_token, reject_token, email_sent, decided_at, decided_by,
                         created_at, expires_at)
                        VALUES (:id, :workflow_id, :operation_id, :status, :current_level, :total_levels,
                                :user_name, :operation_name, :pending_approvers, CAST(:context AS jsonb),
                                :approve_token, :reject_token, :email_sent, :decided_at, :decided_by,
                                :created_at, :expires_at)
                        ON CONFLICT (id) DO UPDATE SET
                            status = EXCLUDED.status,
                            decided_at = EXCLUDED.decided_at,
                            decided_by = EXCLUDED.decided_by,
                            context = EXCLUDED.context
                    """), {
                        "id": workflow_id,
                        "workflow_id": workflow_data.get("workflow_id", ""),
                        "operation_id": workflow_data.get("operation_id", ""),
                        "status": workflow_data.get("status", "pending"),
                        "current_level": workflow_data.get("current_level", 1),
                        "total_levels": workflow_data.get("total_levels", 1),
                        "user_name": workflow_data.get("user_name", ""),
                        "operation_name": workflow_data.get("operation_name", ""),
                        "pending_approvers": pending_approvers_str,
                        "context": json.dumps(context) if context else "{}",
                        "approve_token": workflow_data.get("approve_token"),
                        "reject_token": workflow_data.get("reject_token"),
                        "email_sent": workflow_data.get("email_sent", False),
                        "decided_at": decided_at,
                        "decided_by": workflow_data.get("decided_by"),
                        "created_at": created_at,
                        "expires_at": expires_at
                    })
                    await session.commit()
                    logger.info("Workflow saved to database", workflow_id=workflow_id)
            except Exception as e:
                logger.error("Failed to save workflow to DB", error=str(e))

        self._run_async(_save())

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Recupere un workflow par ID."""
        return self.workflows.get(workflow_id)

    def list_workflows(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Liste les workflows avec filtres."""
        wfs = list(self.workflows.values())
        if status:
            wfs = [w for w in wfs if w.get("status") == status]
        wfs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return wfs[offset:offset + limit]


# Instance globale
memory_store = MemoryStore()
