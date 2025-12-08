"""
Stockage en memoire pour les operations et reconciliations.
Permet de persister les donnees pendant l'execution du serveur.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading


class MemoryStore:
    """Singleton pour stocker les donnees en memoire."""

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
        self.operations: Dict[str, Any] = {}
        self.reconciliation_jobs: Dict[str, Any] = {}
        self.audit_logs: List[Dict[str, Any]] = []
        self.discrepancies: Dict[str, List[Any]] = {}
        self.workflows: Dict[str, Any] = {}
        self._init_demo_data()

    # Operations
    def save_operation(self, operation_id: str, operation_data: Dict[str, Any]) -> None:
        """Sauvegarde une operation."""
        self.operations[operation_id] = {
            **operation_data,
            "saved_at": datetime.utcnow().isoformat()
        }

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

        # Filtrer par account_id
        if account_id:
            ops = [o for o in ops if o.get("account_id") == account_id]

        # Filtrer par status
        if status:
            ops = [o for o in ops if o.get("status") == status]

        # Trier par date (plus recent en premier)
        ops.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Pagination
        return ops[offset:offset + limit]

    def update_operation(self, operation_id: str, updates: Dict[str, Any]) -> None:
        """Met a jour une operation."""
        if operation_id in self.operations:
            self.operations[operation_id].update(updates)
            self.operations[operation_id]["updated_at"] = datetime.utcnow().isoformat()

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
        """Ajoute une entree d'audit."""
        # Transform field names to match frontend expectations
        target_systems = log_entry.get("target_systems", [])
        target_system = target_systems[0] if target_systems else log_entry.get("target_system", "")

        # Map type to event_type format expected by frontend
        log_type = log_entry.get("type", "info")
        action = log_entry.get("action", "")
        event_type = f"{log_type}_{action}" if action else log_type

        # Determine severity based on status
        status = log_entry.get("status", "")
        if status == "error" or status == "failed":
            severity = "error"
        elif status == "warning":
            severity = "warning"
        else:
            severity = "info"

        normalized_entry = {
            "id": len(self.audit_logs) + 1,
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
        # Garder seulement les 1000 derniers logs
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[:1000]

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Recupere les logs recents."""
        return self.audit_logs[:limit]

    def search_logs(self, query: str, log_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Recherche dans les logs."""
        results = self.audit_logs

        if log_type:
            results = [l for l in results if l.get("type") == log_type]

        if query:
            query_lower = query.lower()
            results = [
                l for l in results
                if query_lower in str(l).lower()
            ]

        return results[:limit]


    # Workflows
    def save_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> None:
        """Sauvegarde un workflow."""
        self.workflows[workflow_id] = {
            **workflow_data,
            "saved_at": datetime.utcnow().isoformat()
        }

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

    def _init_demo_data(self):
        """Initialise les donnees de demo au demarrage."""
        import uuid
        from datetime import timedelta

        # Demo operations
        demo_operations = [
            {"firstname": "Jean", "lastname": "Dupont", "department": "IT", "status": "success", "targets": ["LDAP", "SQL"]},
            {"firstname": "Marie", "lastname": "Martin", "department": "HR", "status": "success", "targets": ["LDAP", "SQL", "Odoo"]},
            {"firstname": "Pierre", "lastname": "Bernard", "department": "Finance", "status": "success", "targets": ["LDAP"]},
            {"firstname": "Sophie", "lastname": "Petit", "department": "IT", "status": "pending", "targets": ["LDAP", "SQL"]},
            {"firstname": "Lucas", "lastname": "Robert", "department": "Sales", "status": "failed", "targets": ["Odoo"]},
            {"firstname": "Emma", "lastname": "Richard", "department": "Marketing", "status": "success", "targets": ["LDAP", "SQL"]},
            {"firstname": "Hugo", "lastname": "Durand", "department": "IT", "status": "success", "targets": ["LDAP"]},
            {"firstname": "Lea", "lastname": "Leroy", "department": "HR", "status": "pending_approval", "targets": ["LDAP", "SQL", "Odoo"]},
            {"firstname": "Thomas", "lastname": "Moreau", "department": "Finance", "status": "success", "targets": ["SQL"]},
            {"firstname": "Camille", "lastname": "Simon", "department": "R&D", "status": "success", "targets": ["LDAP", "SQL"]},
        ]

        for i, op in enumerate(demo_operations):
            op_id = str(uuid.uuid4())
            account_id = f"{op['firstname'].lower()}.{op['lastname'].lower()}"
            timestamp = (datetime.utcnow() - timedelta(hours=i*2)).isoformat()

            self.operations[op_id] = {
                "operation_id": op_id,
                "account_id": account_id,
                "status": op["status"],
                "target_systems": op["targets"],
                "calculated_attributes": {
                    "LDAP": {"uid": account_id, "cn": f"{op['firstname']} {op['lastname']}", "mail": f"{account_id}@example.com"},
                    "SQL": {"username": account_id, "email": f"{account_id}@example.com", "department": op["department"]}
                },
                "user_data": {
                    "firstname": op["firstname"],
                    "lastname": op["lastname"],
                    "email": f"{account_id}@example.com",
                    "department": op["department"]
                },
                "message": "" if op["status"] == "success" else "En attente" if "pending" in op["status"] else "Erreur de connexion",
                "timestamp": timestamp
            }

        # Demo workflows (approbations en attente)
        demo_workflows = [
            {"user": "Sophie Petit", "operation": "Création compte IT", "level": 1, "status": "pending"},
            {"user": "Lea Leroy", "operation": "Création compte HR", "level": 2, "status": "pending"},
            {"user": "Marc Dubois", "operation": "Modification droits", "level": 1, "status": "pending"},
            {"user": "Anne Lefebvre", "operation": "Création compte Finance", "level": 3, "status": "pending"},
        ]

        for i, wf in enumerate(demo_workflows):
            wf_id = str(uuid.uuid4())
            op_id = str(uuid.uuid4())
            timestamp = (datetime.utcnow() - timedelta(hours=i*3)).isoformat()

            self.workflows[wf_id] = {
                "id": wf_id,
                "workflow_id": "wf-default-pre",
                "operation_id": op_id,
                "operation_name": wf["operation"],
                "user_name": wf["user"],
                "status": wf["status"],
                "current_level": wf["level"],
                "total_levels": 3,
                "pending_approvers": ["manager@example.com", "admin"],
                "created_at": timestamp,
                "expires_at": (datetime.utcnow() + timedelta(hours=72)).isoformat()
            }

        # Demo reconciliation jobs
        demo_recon_jobs = [
            {"targets": ["LDAP"], "status": "completed", "total": 118, "processed": 118, "discrepancies": 3},
            {"targets": ["SQL"], "status": "completed", "total": 143, "processed": 143, "discrepancies": 5},
            {"targets": ["LDAP", "SQL"], "status": "completed", "total": 261, "processed": 261, "discrepancies": 8},
            {"targets": ["Odoo"], "status": "in_progress", "total": 20, "processed": 12, "discrepancies": 1},
        ]

        for i, job in enumerate(demo_recon_jobs):
            job_id = str(uuid.uuid4())
            started_at = (datetime.utcnow() - timedelta(hours=i*6)).isoformat()
            completed_at = (datetime.utcnow() - timedelta(hours=i*6-1)).isoformat() if job["status"] == "completed" else None

            self.reconciliation_jobs[job_id] = {
                "id": job_id,
                "status": job["status"],
                "target_systems": job["targets"],
                "total_accounts": job["total"],
                "processed_accounts": job["processed"],
                "discrepancies_found": job["discrepancies"],
                "started_at": started_at,
                "completed_at": completed_at,
                "started_by": "admin",
                "errors": []
            }

            # Add some discrepancies for completed jobs
            if job["status"] == "completed" and job["discrepancies"] > 0:
                discrepancies = []
                for d in range(min(job["discrepancies"], 3)):
                    discrepancies.append({
                        "account_id": f"user{d+1}.test",
                        "target_system": job["targets"][0],
                        "discrepancy_type": ["missing_in_target", "attribute_mismatch", "extra_in_target"][d % 3],
                        "midpoint_value": {"email": f"user{d+1}@midpoint.com"},
                        "target_value": {"email": f"user{d+1}@target.com"} if d % 3 == 1 else None,
                        "recommendation": "Synchroniser depuis MidPoint"
                    })
                self.discrepancies[job_id] = discrepancies

        # Demo audit logs
        demo_logs = [
            {"action": "provision_create", "account_id": "jean.dupont", "target": "LDAP", "status": "success"},
            {"action": "provision_create", "account_id": "jean.dupont", "target": "SQL", "status": "success"},
            {"action": "workflow_started", "account_id": "sophie.petit", "target": "LDAP", "status": "info"},
            {"action": "provision_create", "account_id": "marie.martin", "target": "LDAP", "status": "success"},
            {"action": "reconciliation_start", "account_id": "job-001", "target": "LDAP", "status": "info"},
            {"action": "provision_failed", "account_id": "lucas.robert", "target": "Odoo", "status": "error"},
            {"action": "workflow_approved", "account_id": "emma.richard", "target": "LDAP", "status": "success"},
            {"action": "login", "account_id": "admin", "target": "Gateway", "status": "success"},
        ]

        for i, log in enumerate(demo_logs):
            timestamp = (datetime.utcnow() - timedelta(minutes=i*15)).isoformat()
            self.audit_logs.append({
                "id": i + 1,
                "created_at": timestamp,
                "event_type": log["action"],
                "action": log["action"].replace("_", " ").title(),
                "account_id": log["account_id"],
                "actor": "admin",
                "target_system": log["target"],
                "severity": "error" if log["status"] == "error" else "info",
                "details": log
            })


# Instance globale
memory_store = MemoryStore()
