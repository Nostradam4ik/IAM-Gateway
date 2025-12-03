"""
Service de reconciliation avec MidPoint
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import structlog
from pydantic import BaseModel

from app.models.provision import TargetSystem, TargetAccountState
from app.connectors.connector_factory import ConnectorFactory
from app.services.midpoint_client import MidPointClient

logger = structlog.get_logger()


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

    def __init__(self, session):
        self.session = session
        self.connector_factory = ConnectorFactory()
        self.midpoint_client = MidPointClient()

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

                    try:
                        # Get account from target
                        target_account = await connector.get_account(account["id"])

                        if target_account is None:
                            # Missing in target
                            discrepancies.append(Discrepancy(
                                id=f"disc-{len(discrepancies)}",
                                job_id=job_id,
                                account_id=account["id"],
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
                                    account_id=account["id"],
                                    target_system=target_system,
                                    discrepancy_type="attribute_mismatch",
                                    midpoint_value={"mismatches": mismatches},
                                    target_value=target_account,
                                    recommendation="Synchroniser les attributs depuis MidPoint"
                                ))

                    except Exception as e:
                        job.errors.append({
                            "account_id": account["id"],
                            "target": target_system,
                            "error": str(e)
                        })

                # Check for orphan accounts in target
                target_accounts = await connector.list_accounts()
                midpoint_ids = {a["id"] for a in midpoint_accounts}

                for target_acc in target_accounts:
                    if target_acc.get("id") not in midpoint_ids:
                        discrepancies.append(Discrepancy(
                            id=f"disc-{len(discrepancies)}",
                            job_id=job_id,
                            account_id=target_acc.get("id", "unknown"),
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
            # ...

            logger.info(
                "Reconciliation completed",
                job_id=job_id,
                total=job.total_accounts,
                discrepancies=job.discrepancies_found
            )

        except Exception as e:
            logger.error("Reconciliation failed", job_id=job_id, error=str(e))
            # Update job status
            job.status = "failed"
            job.errors.append({"error": str(e)})

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
        # DB query
        return None

    async def list_jobs(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List[ReconciliationJob]:
        """Liste les jobs de reconciliation."""
        return []

    async def get_discrepancies(
        self,
        job_id: str,
        target_system: Optional[TargetSystem] = None
    ) -> List[Discrepancy]:
        """Recupere les divergences d'un job."""
        return []

    async def resolve_discrepancies(
        self,
        job_id: str,
        action: str,
        discrepancy_ids: Optional[List[str]],
        resolved_by: str
    ) -> Dict[str, Any]:
        """Resout les divergences."""
        resolved_count = 0
        errors = []

        discrepancies = await self.get_discrepancies(job_id)
        if discrepancy_ids:
            discrepancies = [d for d in discrepancies if d.id in discrepancy_ids]

        for disc in discrepancies:
            try:
                if action == "use_midpoint":
                    # Sync from MidPoint to target
                    connector = self.connector_factory.get_connector(disc.target_system)
                    if disc.discrepancy_type == "missing_in_target":
                        await connector.create_account(
                            disc.account_id,
                            disc.midpoint_value
                        )
                    elif disc.discrepancy_type == "attribute_mismatch":
                        await connector.update_account(
                            disc.account_id,
                            disc.midpoint_value
                        )

                elif action == "use_target":
                    # Sync from target to MidPoint
                    await self.midpoint_client.update_account(
                        disc.account_id,
                        disc.target_value
                    )

                elif action == "ignore":
                    pass  # Just mark as resolved

                disc.resolved = True
                disc.resolved_at = datetime.utcnow()
                resolved_count += 1

            except Exception as e:
                errors.append({
                    "discrepancy_id": disc.id,
                    "error": str(e)
                })

        logger.info(
            "Discrepancies resolved",
            job_id=job_id,
            action=action,
            resolved=resolved_count,
            errors=len(errors)
        )

        return {
            "resolved": resolved_count,
            "errors": errors
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
