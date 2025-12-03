"""
API de reconciliation avec MidPoint
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import structlog

from app.models.provision import TargetSystem
from app.core.security import get_current_user, require_role
from app.core.database import get_session
from app.services.reconciliation_service import ReconciliationService
from app.services.audit_service import AuditService

router = APIRouter()
logger = structlog.get_logger()


class ReconciliationRequest(BaseModel):
    """Requete de reconciliation."""
    target_systems: Optional[List[TargetSystem]] = None
    account_ids: Optional[List[str]] = None
    full_sync: bool = False


class ReconciliationStatus(BaseModel):
    """Statut d'une reconciliation."""
    id: str
    status: str
    target_systems: List[str]
    total_accounts: int
    processed_accounts: int
    discrepancies_found: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    errors: List[dict] = []


class DiscrepancyReport(BaseModel):
    """Rapport de divergence."""
    account_id: str
    target_system: str
    discrepancy_type: str
    midpoint_value: Optional[dict]
    target_value: Optional[dict]
    recommendation: str


@router.post("/start", response_model=ReconciliationStatus)
async def start_reconciliation(
    request: ReconciliationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"])),
    session=Depends(get_session)
):
    """Demarre une reconciliation entre MidPoint et les systemes cibles."""
    recon_service = ReconciliationService(session)
    audit_service = AuditService(session)

    logger.info(
        "Starting reconciliation",
        targets=request.target_systems,
        full_sync=request.full_sync,
        user=current_user["username"]
    )

    # Create reconciliation job
    job = await recon_service.create_job(
        target_systems=request.target_systems,
        account_ids=request.account_ids,
        full_sync=request.full_sync,
        started_by=current_user["username"]
    )

    await audit_service.log_reconciliation_start(job.id, current_user)

    # Run reconciliation in background
    background_tasks.add_task(
        recon_service.run_reconciliation,
        job.id
    )

    return ReconciliationStatus(
        id=job.id,
        status="in_progress",
        target_systems=job.target_systems,
        total_accounts=0,
        processed_accounts=0,
        discrepancies_found=0,
        started_at=job.started_at
    )


@router.get("/status/{job_id}", response_model=ReconciliationStatus)
async def get_reconciliation_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere le statut d'une reconciliation."""
    recon_service = ReconciliationService(session)
    job = await recon_service.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reconciliation job {job_id} not found"
        )

    return job


@router.get("/jobs", response_model=List[ReconciliationStatus])
async def list_reconciliation_jobs(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Liste les jobs de reconciliation."""
    recon_service = ReconciliationService(session)
    return await recon_service.list_jobs(limit=limit, offset=offset)


@router.get("/{job_id}/discrepancies", response_model=List[DiscrepancyReport])
async def get_discrepancies(
    job_id: str,
    target_system: Optional[TargetSystem] = None,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere les divergences trouvees lors d'une reconciliation."""
    recon_service = ReconciliationService(session)
    return await recon_service.get_discrepancies(
        job_id=job_id,
        target_system=target_system
    )


@router.post("/{job_id}/resolve")
async def resolve_discrepancies(
    job_id: str,
    action: str,  # "use_midpoint", "use_target", "manual"
    discrepancy_ids: Optional[List[str]] = None,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"])),
    session=Depends(get_session)
):
    """Resout les divergences d'une reconciliation."""
    recon_service = ReconciliationService(session)
    audit_service = AuditService(session)

    if action not in ["use_midpoint", "use_target", "manual", "ignore"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use: use_midpoint, use_target, manual, ignore"
        )

    result = await recon_service.resolve_discrepancies(
        job_id=job_id,
        action=action,
        discrepancy_ids=discrepancy_ids,
        resolved_by=current_user["username"]
    )

    await audit_service.log_reconciliation_resolution(
        job_id=job_id,
        action=action,
        user=current_user
    )

    return result


@router.post("/sync-cache")
async def sync_account_cache(
    target_systems: Optional[List[TargetSystem]] = None,
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Synchronise le cache des comptes avec les systemes cibles."""
    recon_service = ReconciliationService(session)

    background_tasks.add_task(
        recon_service.sync_cache,
        target_systems
    )

    return {"message": "Cache sync started", "target_systems": target_systems}


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere les statistiques du cache des comptes."""
    recon_service = ReconciliationService(session)
    return await recon_service.get_cache_stats()
