"""
Service de reconciliation entre MidPoint et les systemes cibles.

Compare l'etat des comptes dans MidPoint (source de verite) avec
les systemes connectes (LDAP, SQL, Odoo) pour detecter les divergences.

Types de divergences :
  - missing_in_target : compte MidPoint absent du systeme cible
  - missing_in_midpoint : compte orphelin dans le systeme cible
  - attribute_mismatch : attributs differents entre source et cible

Resolution : appliquer la valeur MidPoint, garder la valeur cible,
supprimer l'orphelin, ou ignorer.

ROLE_OIDS : mapping des roles MidPoint pour le provisionnement automatique
vers LDAP (ldap-user) et Odoo (odoo-user).
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import structlog
from pydantic import BaseModel

from app.models.provision import TargetSystem, TargetAccountState
from app.connectors.connector_factory import ConnectorFactory
from app.connectors.midpoint_connector import MidPointConnector
from app.services.midpoint_client import MidPointClient
from app.core.memory_store import memory_store

logger = structlog.get_logger()

# Role OIDs for provisioning to target systems via MidPoint
ROLE_OIDS = {
    "LDAP": "10000000-0000-0000-0000-000000000101",      # ldap-user role
    "ODOO": "10000000-0000-0000-0000-000000000102",      # odoo-user role
    "LDAP_FULL": "10000000-0000-0000-0000-000000000210"  # Employee-Full-Access role
}


class ReconciliationJob(BaseModel):
    """Job de reconciliation."""
    id: str
    status: str
    target_systems: List[str]
    total_accounts: int
    processed_accounts: int
    discrepancies_found: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    started_by: str
    errors: List[Dict[str, Any]] = []


class Discrepancy(BaseModel):
    """Divergence detectee."""
    id: str
    job_id: str
    account_id: str
    target_system: str
    discrepancy_type: str  # "missing_in_target", "missing_in_midpoint", "attribute_mismatch"
    midpoint_value: Optional[Dict[str, Any]]
    target_value: Optional[Dict[str, Any]]
    recommendation: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class ReconciliationService:
    """
    Service de reconciliation entre MidPoint et les systemes cibles.

    Fonctionnalites:
    - Comparaison des etats
    - Detection des divergences
    - Resolution automatique ou manuelle
    - Synchronisation du cache
    """

    # Store jobs in memory (class variable)
    _jobs: Dict[str, "ReconciliationJob"] = {}
    _discrepancies: Dict[str, List["Discrepancy"]] = {}

    def __init__(self, session):
        self.session = session
        self.connector_factory = ConnectorFactory()
        self.midpoint_client = MidPointClient()
        self.midpoint_connector = MidPointConnector()

    async def create_job(
        self,
        target_systems: Optional[List[TargetSystem]],
        account_ids: Optional[List[str]],
        full_sync: bool,
        started_by: str
    ) -> ReconciliationJob:
        """Cree un nouveau job de reconciliation."""
        import uuid

        targets = target_systems or [TargetSystem.LDAP, TargetSystem.SQL, TargetSystem.ODOO]

        job = ReconciliationJob(
            id=str(uuid.uuid4()),
            status="pending",
            target_systems=[t.value for t in targets],
            total_accounts=0,
            processed_accounts=0,
            discrepancies_found=0,
            started_at=datetime.utcnow(),
            started_by=started_by
        )

        # Store job in memory
        ReconciliationService._jobs[job.id] = job

        logger.info(
            "Reconciliation job created",
            job_id=job.id,
            targets=job.target_systems,
            full_sync=full_sync
        )

        return job

    async def run_reconciliation(self, job_id: str) -> None:
        """Execute la reconciliation en arriere-plan."""
        logger.info("Starting reconciliation run", job_id=job_id)

        try:
            # Get job
            job = await self.get_job(job_id)
            job.status = "in_progress"

            # Get accounts from MidPoint
            midpoint_accounts = await self.midpoint_client.get_all_accounts()
            job.total_accounts = len(midpoint_accounts)

            discrepancies = []

            for target_system in job.target_systems:
                connector = self.connector_factory.get_connector(target_system)

                for account in midpoint_accounts:
                    job.processed_accounts += 1
                    account_id = str(account.get("id", "unknown"))

                    try:
                        # Get account from target
                        target_account = await connector.get_account(account_id)

                        if target_account is None:
                            # Missing in target
                            discrepancies.append(Discrepancy(
                                id=f"disc-{len(discrepancies)}",
                                job_id=job_id,
                                account_id=account_id,
                                target_system=target_system,
                                discrepancy_type="missing_in_target",
                                midpoint_value=account,
                                target_value=None,
                                recommendation="Creer le compte dans le systeme cible"
                            ))
                        else:
                            # Compare attributes
                            mismatches = self._compare_attributes(
                                account, target_account, target_system
                            )
                            if mismatches:
                                discrepancies.append(Discrepancy(
                                    id=f"disc-{len(discrepancies)}",
                                    job_id=job_id,
                                    account_id=account_id,
                                    target_system=target_system,
                                    discrepancy_type="attribute_mismatch",
                                    midpoint_value={"mismatches": mismatches, "account": account},
                                    target_value=target_account,
                                    recommendation="Synchroniser les attributs depuis MidPoint"
                                ))

                    except Exception as e:
                        job.errors.append({
                            "account_id": account_id,
                            "target": target_system,
                            "error": str(e)
                        })

                # Check for orphan accounts in target
                target_accounts = await connector.list_accounts()
                midpoint_ids = {str(a.get("id", "")) for a in midpoint_accounts}

                for target_acc in target_accounts:
                    target_id = str(target_acc.get("id", "unknown"))
                    if target_id not in midpoint_ids:
                        discrepancies.append(Discrepancy(
                            id=f"disc-{len(discrepancies)}",
                            job_id=job_id,
                            account_id=target_id,
                            target_system=target_system,
                            discrepancy_type="missing_in_midpoint",
                            midpoint_value=None,
                            target_value=target_acc,
                            recommendation="Supprimer le compte orphelin ou l'importer dans MidPoint"
                        ))

            job.discrepancies_found = len(discrepancies)
            job.status = "completed"
            job.completed_at = datetime.utcnow()

            # Save discrepancies
            ReconciliationService._discrepancies[job_id] = discrepancies

            # Update memory_store with final job status
            memory_store.update_job(job_id, {
                "status": "completed",
                "total_accounts": job.total_accounts,
                "processed_accounts": job.processed_accounts,
                "discrepancies_found": job.discrepancies_found,
                "completed_at": job.completed_at.isoformat(),
                "errors": job.errors
            })

            logger.info(
                "Reconciliation completed",
                job_id=job_id,
                total=job.total_accounts,
                discrepancies=job.discrepancies_found
            )

        except Exception as e:
            logger.error("Reconciliation failed", job_id=job_id, error=str(e))
            # Update job status
            job = await self.get_job(job_id)
            if job:
                job.status = "failed"
                job.errors.append({"error": str(e)})
                # Update memory_store
                memory_store.update_job(job_id, {
                    "status": "failed",
                    "errors": job.errors
                })

    def _compare_attributes(
        self,
        midpoint_account: Dict[str, Any],
        target_account: Dict[str, Any],
        target_system: str
    ) -> List[Dict[str, Any]]:
        """Compare les attributs entre MidPoint et la cible."""
        mismatches = []

        # Define attribute mappings per target
        mappings = {
            "LDAP": {
                "firstname": "givenName",
                "lastname": "sn",
                "email": "mail"
            },
            "SQL": {
                "firstname": "first_name",
                "lastname": "last_name",
                "email": "email"
            },
            "ODOO": {
                "name": "name",
                "email": "login"
            }
        }

        attr_map = mappings.get(target_system, {})

        for mp_attr, target_attr in attr_map.items():
            mp_value = midpoint_account.get(mp_attr)
            target_value = target_account.get(target_attr)

            if mp_value != target_value:
                mismatches.append({
                    "attribute": mp_attr,
                    "midpoint_value": mp_value,
                    "target_value": target_value
                })

        return mismatches

    async def get_job(self, job_id: str) -> Optional[ReconciliationJob]:
        """Recupere un job de reconciliation."""
        return ReconciliationService._jobs.get(job_id)

    async def list_jobs(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List[ReconciliationJob]:
        """Liste les jobs de reconciliation."""
        jobs = list(ReconciliationService._jobs.values())
        jobs.sort(key=lambda j: j.started_at, reverse=True)
        return jobs[offset:offset + limit]

    async def get_discrepancies(
        self,
        job_id: str,
        target_system: Optional[TargetSystem] = None
    ) -> List[Discrepancy]:
        """Recupere les divergences d'un job."""
        discrepancies = ReconciliationService._discrepancies.get(job_id, [])
        if target_system:
            discrepancies = [d for d in discrepancies if d.target_system == target_system.value]
        return discrepancies

    async def resolve_discrepancies(
        self,
        job_id: str,
        action: str,
        discrepancy_ids: Optional[List[str]],
        resolved_by: str
    ) -> Dict[str, Any]:
        """
        Resout les divergences en utilisant MidPoint comme hub central.

        Actions:
        - use_midpoint: Assigne le role MidPoint pour provisionner vers le systeme cible
        - use_target: Importe les donnees du systeme cible vers MidPoint
        - ignore: Marque comme resolu sans action
        - delete_orphan: Supprime le compte orphelin du systeme cible
        """
        resolved_count = 0
        errors = []
        actions_taken = []

        discrepancies = await self.get_discrepancies(job_id)
        if discrepancy_ids:
            discrepancies = [d for d in discrepancies if d.id in discrepancy_ids]

        for disc in discrepancies:
            try:
                if action == "use_midpoint":
                    # Use MidPoint roles to provision to target system
                    if disc.discrepancy_type == "missing_in_target":
                        # Assign the appropriate role to trigger provisioning
                        role_oid = ROLE_OIDS.get(disc.target_system)
                        success = False

                        if role_oid and disc.midpoint_value:
                            user_oid = disc.midpoint_value.get("id") or disc.account_id
                            try:
                                success = await self.midpoint_connector.assign_role(user_oid, role_oid)
                                if success:
                                    actions_taken.append({
                                        "account": disc.account_id,
                                        "action": f"Assigned role {disc.target_system} to user",
                                        "role_oid": role_oid
                                    })
                            except Exception as role_error:
                                logger.warning(
                                    "Role assignment failed, falling back to direct connector",
                                    user_oid=user_oid,
                                    role_oid=role_oid,
                                    error=str(role_error)
                                )
                                success = False

                        # Fallback: use connector directly if role assignment failed or not available
                        if not success:
                            connector = self.connector_factory.get_connector(disc.target_system)
                            await connector.create_account(disc.account_id, disc.midpoint_value)
                            actions_taken.append({
                                "account": disc.account_id,
                                "action": f"Created account directly in {disc.target_system}"
                            })

                    elif disc.discrepancy_type == "attribute_mismatch":
                        # Update attributes from MidPoint to target
                        connector = self.connector_factory.get_connector(disc.target_system)
                        # Extract the actual MidPoint account data
                        mp_account = disc.midpoint_value.get("account", {}) if disc.midpoint_value else {}
                        mismatches = disc.midpoint_value.get("mismatches", []) if disc.midpoint_value else []

                        # Build update data from mismatches (use MidPoint values)
                        update_data = {}
                        for mismatch in mismatches:
                            attr = mismatch.get("attribute")
                            mp_value = mismatch.get("midpoint_value")
                            if attr and mp_value is not None:
                                update_data[attr] = mp_value

                        # Also include the full account data for context
                        update_data.update(mp_account)

                        await connector.update_account(disc.account_id, update_data)
                        actions_taken.append({
                            "account": disc.account_id,
                            "action": f"Updated attributes in {disc.target_system}",
                            "attributes": [m.get("attribute") for m in mismatches]
                        })

                elif action == "use_target":
                    # Import from target to MidPoint
                    if disc.discrepancy_type == "missing_in_midpoint" and disc.target_value:
                        # Create user in MidPoint from target data
                        target_data = disc.target_value
                        username = target_data.get("login") or target_data.get("uid") or target_data.get("name") or f"imported_{disc.account_id}"

                        attributes = {
                            "firstname": target_data.get("givenName") or target_data.get("name", "").split()[0] if target_data.get("name") else "Unknown",
                            "lastname": target_data.get("sn") or (target_data.get("name", "").split()[-1] if len(target_data.get("name", "").split()) > 1 else "User"),
                            "email": target_data.get("mail") or target_data.get("email") or target_data.get("login"),
                        }

                        result = await self.midpoint_connector.create_account(username, attributes)

                        # Assign appropriate role to link to the target system
                        if result.get("oid"):
                            role_oid = ROLE_OIDS.get(disc.target_system)
                            if role_oid:
                                await self.midpoint_connector.assign_role(result["oid"], role_oid)

                        actions_taken.append({
                            "account": username,
                            "action": f"Imported to MidPoint from {disc.target_system}",
                            "oid": result.get("oid")
                        })
                    else:
                        # Update existing MidPoint user
                        await self.midpoint_client.update_account(disc.account_id, disc.target_value)
                        actions_taken.append({
                            "account": disc.account_id,
                            "action": "Updated MidPoint from target"
                        })

                elif action == "delete_orphan":
                    # Delete orphan account from target system
                    if disc.discrepancy_type == "missing_in_midpoint":
                        connector = self.connector_factory.get_connector(disc.target_system)
                        await connector.delete_account(disc.account_id)
                        actions_taken.append({
                            "account": disc.account_id,
                            "action": f"Deleted orphan from {disc.target_system}"
                        })

                elif action == "ignore":
                    actions_taken.append({
                        "account": disc.account_id,
                        "action": "Ignored"
                    })

                disc.resolved = True
                disc.resolved_at = datetime.utcnow()
                resolved_count += 1

            except Exception as e:
                logger.error(
                    "Failed to resolve discrepancy",
                    discrepancy_id=disc.id,
                    action=action,
                    error=str(e)
                )
                errors.append({
                    "discrepancy_id": disc.id,
                    "account_id": disc.account_id,
                    "target_system": disc.target_system,
                    "error": str(e)
                })

        logger.info(
            "Discrepancies resolution completed",
            job_id=job_id,
            action=action,
            resolved=resolved_count,
            errors=len(errors),
            resolved_by=resolved_by
        )

        return {
            "resolved": resolved_count,
            "total_processed": len(discrepancies),
            "errors": errors,
            "actions": actions_taken
        }

    async def sync_cache(
        self,
        target_systems: Optional[List[TargetSystem]] = None
    ) -> None:
        """Synchronise le cache des comptes."""
        targets = target_systems or [TargetSystem.LDAP, TargetSystem.SQL, TargetSystem.ODOO]

        for target in targets:
            connector = self.connector_factory.get_connector(target.value)
            accounts = await connector.list_accounts()

            for account in accounts:
                state = TargetAccountState(
                    account_id=account.get("id"),
                    target_system=target,
                    target_account_id=account.get("uid", account.get("username")),
                    attributes=json.dumps(account),
                    is_active=account.get("active", True),
                    last_sync_at=datetime.utcnow()
                )
                # Upsert

        logger.info("Cache synchronized", targets=[t.value for t in targets])

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Recupere les statistiques du cache."""
        return {
            "total_accounts": 0,
            "by_system": {},
            "last_sync": None
        }
