"""
Stockage persistant PostgreSQL pour les operations et audit.
Remplace le stockage en memoire pour persister les donnees entre redemarrages.
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

from app.core.config import settings

logger = structlog.get_logger()


class DatabaseStore:
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
        self._operations_cache: Dict[str, Any] = {}
        self._audit_cache: List[Dict[str, Any]] = []
        self._cache_loaded = False

    async def _ensure_cache_loaded(self):
        """Charge le cache depuis la base de donnees si necessaire."""
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

                for row in rows:
                    op_id = str(row[0])
                    self._operations_cache[op_id] = {
                        "operation_id": op_id,
                        "request_id": row[1],
                        "operation_type": row[2],
                        "status": row[3],
                        "target_system": row[4],
                        "account_id": row[5],
                        "attributes": row[6] or {},
                        "calculated_attributes": row[7] or {},
                        "message": row[8] or "",
                        "timestamp": row[9].isoformat() if row[9] else None,
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

                self._audit_cache = []
                for i, row in enumerate(rows):
                    self._audit_cache.append({
                        "id": i + 1,
                        "db_id": str(row[0]),
                        "created_at": row[1].isoformat() if row[1] else None,
                        "event_type": row[2],
                        "target_system": row[3] or "",
                        "account_id": row[4] or "",
                        "action": row[5] or "",
                        "severity": "error" if row[6] == "error" else "info",
                        "actor": row[7] or "system",
                        "details": row[8] or {}
                    })

                logger.info(
                    "Database cache loaded",
                    operations=len(self._operations_cache),
                    audit_logs=len(self._audit_cache)
                )

        except Exception as e:
            logger.error("Failed to load from database", error=str(e))

    # Operations
    async def save_operation(self, operation_id: str, operation_data: Dict[str, Any]) -> None:
        """Sauvegarde une operation dans PostgreSQL."""
        await self._ensure_cache_loaded()

        try:
            async with self.async_session() as session:
                # Extraire les donnees
                account_id = operation_data.get("account_id", "")
                status = operation_data.get("status", "pending")
                target_systems = operation_data.get("target_systems", [])
                target_system = ",".join(target_systems) if isinstance(target_systems, list) else str(target_systems)
                attributes = operation_data.get("user_data", operation_data.get("attributes", {}))
                calculated = operation_data.get("calculated_attributes", {})
                message = operation_data.get("message", "")

                await session.execute(text("""
                    INSERT INTO provisioning_operations
                    (id, request_id, operation_type, status, target_system, identity_id,
                     attributes, calculated_attributes, error_message, created_at)
                    VALUES (:id, :request_id, :op_type, :status, :target, :identity,
                            :attrs::jsonb, :calc::jsonb, :msg, :created)
                    ON CONFLICT (id) DO UPDATE SET
                        status = :status,
                        calculated_attributes = :calc::jsonb,
                        error_message = :msg,
                        updated_at = CURRENT_TIMESTAMP
                """), {
                    "id": operation_id,
                    "request_id": operation_id[:8],
                    "op_type": operation_data.get("operation", "create"),
                    "status": status,
                    "target": target_system,
                    "identity": account_id,
                    "attrs": str(attributes).replace("'", '"') if attributes else "{}",
                    "calc": str(calculated).replace("'", '"') if calculated else "{}",
                    "msg": message,
                    "created": datetime.utcnow()
                })
                await session.commit()

                # Mettre a jour le cache
                self._operations_cache[operation_id] = {
                    **operation_data,
                    "operation_id": operation_id,
                    "saved_at": datetime.utcnow().isoformat()
                }

                logger.info("Operation saved to database", operation_id=operation_id)

        except Exception as e:
            logger.error("Failed to save operation", error=str(e), operation_id=operation_id)

    def save_operation_sync(self, operation_id: str, operation_data: Dict[str, Any]) -> None:
        """Version synchrone de save_operation."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.save_operation(operation_id, operation_data))
            else:
                loop.run_until_complete(self.save_operation(operation_id, operation_data))
        except RuntimeError:
            # Pas de loop, creer une nouvelle
            asyncio.run(self.save_operation(operation_id, operation_data))

        # Toujours mettre a jour le cache local immediatement
        self._operations_cache[operation_id] = {
            **operation_data,
            "operation_id": operation_id,
            "saved_at": datetime.utcnow().isoformat()
        }

    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Recupere une operation par ID."""
        return self._operations_cache.get(operation_id)

    def list_operations(
        self,
        account_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Liste les operations avec filtres."""
        ops = list(self._operations_cache.values())

        if account_id:
            ops = [o for o in ops if o.get("account_id") == account_id]

        if status:
            ops = [o for o in ops if o.get("status") == status]

        ops.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return ops[offset:offset + limit]

    def update_operation(self, operation_id: str, updates: Dict[str, Any]) -> None:
        """Met a jour une operation."""
        if operation_id in self._operations_cache:
            self._operations_cache[operation_id].update(updates)
            self._operations_cache[operation_id]["updated_at"] = datetime.utcnow().isoformat()
            # Sauvegarder en DB
            self.save_operation_sync(operation_id, self._operations_cache[operation_id])

    # Audit Logs
    async def add_audit_log_async(self, log_entry: Dict[str, Any]) -> None:
        """Ajoute une entree d'audit dans PostgreSQL."""
        await self._ensure_cache_loaded()

        try:
            async with self.async_session() as session:
                log_id = str(uuid.uuid4())
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

                await session.execute(text("""
                    INSERT INTO audit_logs
                    (id, timestamp, event_type, target_system, identity_id, action, status, actor, details)
                    VALUES (:id, :ts, :event_type, :target, :identity, :action, :status, :actor, :details::jsonb)
                """), {
                    "id": log_id,
                    "ts": datetime.utcnow(),
                    "event_type": event_type,
                    "target": target_system,
                    "identity": log_entry.get("account_id", log_entry.get("job_id", "")),
                    "action": action or log_entry.get("action", "-"),
                    "status": severity,
                    "actor": log_entry.get("actor", "system"),
                    "details": str(log_entry).replace("'", '"')
                })
                await session.commit()

                # Mettre a jour le cache
                normalized_entry = {
                    "id": len(self._audit_cache) + 1,
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
                self._audit_cache.insert(0, normalized_entry)

                if len(self._audit_cache) > 1000:
                    self._audit_cache = self._audit_cache[:1000]

                logger.info("Audit log saved to database", event_type=event_type)

        except Exception as e:
            logger.error("Failed to save audit log", error=str(e))

    def add_audit_log(self, log_entry: Dict[str, Any]) -> None:
        """Version synchrone de add_audit_log_async."""
        # Ajouter au cache immediatement
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

        normalized_entry = {
            "id": len(self._audit_cache) + 1,
            "created_at": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "action": action or log_entry.get("action", "-"),
            "account_id": log_entry.get("account_id", log_entry.get("job_id", "")),
            "actor": log_entry.get("actor", "system"),
            "target_system": target_system,
            "severity": severity,
            "details": log_entry
        }
        self._audit_cache.insert(0, normalized_entry)

        if len(self._audit_cache) > 1000:
            self._audit_cache = self._audit_cache[:1000]

        # Sauvegarder en DB de maniere asynchrone
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.add_audit_log_async(log_entry))
            else:
                loop.run_until_complete(self.add_audit_log_async(log_entry))
        except RuntimeError:
            asyncio.run(self.add_audit_log_async(log_entry))

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Recupere les logs recents."""
        return self._audit_cache[:limit]

    def search_logs(self, query: str, log_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Recherche dans les logs."""
        results = self._audit_cache

        if log_type:
            results = [l for l in results if l.get("event_type") == log_type]

        if query:
            query_lower = query.lower()
            results = [
                l for l in results
                if query_lower in str(l).lower()
            ]

        return results[:limit]

    # Reconciliation Jobs (garde la meme interface)
    def save_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Sauvegarde un job de reconciliation."""
        pass  # A implementer si necessaire

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Recupere un job par ID."""
        return None

    def list_jobs(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Liste les jobs de reconciliation."""
        return []

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        """Met a jour un job."""
        pass

    def save_discrepancies(self, job_id: str, discrepancies: List[Any]) -> None:
        """Sauvegarde les divergences d'un job."""
        pass

    def get_discrepancies(self, job_id: str) -> List[Any]:
        """Recupere les divergences d'un job."""
        return []

    # Workflows (garde la meme interface)
    def save_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> None:
        """Sauvegarde un workflow."""
        pass

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Recupere un workflow par ID."""
        return None

    def list_workflows(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Liste les workflows avec filtres."""
        return []


# Instance globale
database_store = DatabaseStore()
