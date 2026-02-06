"""
API pour la gestion des synchronisations planifiees.
Permet de configurer des taches automatiques Odoo -> MidPoint.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import structlog

from app.core.security import get_current_user, require_role
from app.services.scheduler_service import sync_scheduler

router = APIRouter()
logger = structlog.get_logger()


# ==================== Models ====================

class DailySyncConfig(BaseModel):
    """Configuration pour une synchronisation quotidienne."""
    job_id: str = Field(..., description="Identifiant unique du job")
    hour: int = Field(..., ge=0, le=23, description="Heure d'execution (0-23)")
    minute: int = Field(0, ge=0, le=59, description="Minute d'execution (0-59)")
    enabled: bool = Field(True, description="Activer le job")


class IntervalSyncConfig(BaseModel):
    """Configuration pour une synchronisation par intervalle."""
    job_id: str = Field(..., description="Identifiant unique du job")
    hours: int = Field(0, ge=0, le=24, description="Intervalle en heures")
    minutes: int = Field(30, ge=0, le=59, description="Intervalle en minutes")
    enabled: bool = Field(True, description="Activer le job")


class CronSyncConfig(BaseModel):
    """Configuration pour une synchronisation cron."""
    job_id: str = Field(..., description="Identifiant unique du job")
    cron_expression: str = Field(..., description="Expression cron (min hour day month dow)")
    enabled: bool = Field(True, description="Activer le job")


class ContractCheckConfig(BaseModel):
    """Configuration pour la verification des contrats expires."""
    job_id: str = Field(..., description="Identifiant unique du job")
    hour: int = Field(6, ge=0, le=23, description="Heure d'execution (0-23)")
    minute: int = Field(0, ge=0, le=59, description="Minute d'execution (0-59)")
    enabled: bool = Field(True, description="Activer le job")


class ToggleJobRequest(BaseModel):
    """Request pour activer/desactiver un job."""
    enabled: bool


# ==================== Endpoints ====================

@router.get("/jobs", response_model=Dict[str, Any])
async def get_scheduled_jobs(
    current_user: dict = Depends(get_current_user)
):
    """
    Liste toutes les taches planifiees.
    """
    jobs = sync_scheduler.get_all_jobs()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(jobs),
        "jobs": jobs
    }


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_scheduled_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Recupere les details d'une tache planifiee.
    """
    job = sync_scheduler.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.post("/jobs/daily", response_model=Dict[str, Any])
async def create_daily_sync(
    config: DailySyncConfig,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Cree une synchronisation quotidienne a une heure specifique.

    Exemple: Synchroniser tous les jours a 2h00 du matin.
    """
    try:
        result = sync_scheduler.add_daily_sync(
            job_id=config.job_id,
            hour=config.hour,
            minute=config.minute,
            enabled=config.enabled
        )

        logger.info(
            "Daily sync job created",
            job_id=config.job_id,
            time=f"{config.hour:02d}:{config.minute:02d}",
            user=current_user.get("username")
        )

        return {
            "message": f"Synchronisation quotidienne configuree pour {config.hour:02d}:{config.minute:02d}",
            "job": result
        }

    except Exception as e:
        logger.error("Failed to create daily sync", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/interval", response_model=Dict[str, Any])
async def create_interval_sync(
    config: IntervalSyncConfig,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Cree une synchronisation par intervalle de temps.

    Exemple: Synchroniser toutes les 2 heures.
    """
    if config.hours == 0 and config.minutes == 0:
        raise HTTPException(
            status_code=400,
            detail="L'intervalle doit etre superieur a 0"
        )

    try:
        result = sync_scheduler.add_interval_sync(
            job_id=config.job_id,
            hours=config.hours,
            minutes=config.minutes,
            enabled=config.enabled
        )

        interval_str = ""
        if config.hours > 0:
            interval_str += f"{config.hours}h "
        if config.minutes > 0:
            interval_str += f"{config.minutes}min"

        logger.info(
            "Interval sync job created",
            job_id=config.job_id,
            interval=interval_str.strip(),
            user=current_user.get("username")
        )

        return {
            "message": f"Synchronisation configuree toutes les {interval_str.strip()}",
            "job": result
        }

    except Exception as e:
        logger.error("Failed to create interval sync", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/cron", response_model=Dict[str, Any])
async def create_cron_sync(
    config: CronSyncConfig,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Cree une synchronisation avec une expression cron avancee.

    Format: minute heure jour mois jour_semaine
    Exemples:
    - "0 2 * * *" = Tous les jours a 2h00
    - "0 */4 * * *" = Toutes les 4 heures
    - "0 9 * * 1-5" = Tous les jours ouvrables a 9h00
    - "30 8,12,18 * * *" = A 8h30, 12h30 et 18h30
    """
    # Validate cron expression format
    parts = config.cron_expression.split()
    if len(parts) < 5:
        raise HTTPException(
            status_code=400,
            detail="Expression cron invalide. Format: minute heure jour mois jour_semaine"
        )

    try:
        result = sync_scheduler.add_cron_sync(
            job_id=config.job_id,
            cron_expression=config.cron_expression,
            enabled=config.enabled
        )

        logger.info(
            "Cron sync job created",
            job_id=config.job_id,
            cron=config.cron_expression,
            user=current_user.get("username")
        )

        return {
            "message": f"Synchronisation cron configuree: {config.cron_expression}",
            "job": result
        }

    except Exception as e:
        logger.error("Failed to create cron sync", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/toggle", response_model=Dict[str, Any])
async def toggle_job(
    job_id: str,
    request: ToggleJobRequest,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Active ou desactive une tache planifiee.
    """
    result = sync_scheduler.toggle_job(job_id, request.enabled)

    if not result:
        raise HTTPException(status_code=404, detail="Job not found")

    status = "active" if request.enabled else "desactive"
    logger.info(
        f"Job {status}",
        job_id=job_id,
        user=current_user.get("username")
    )

    return {
        "message": f"Job {status}",
        "job": result
    }


@router.post("/jobs/{job_id}/run", response_model=Dict[str, Any])
async def run_job_now(
    job_id: str,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Execute immediatement une tache planifiee.
    Utile pour tester ou forcer une synchronisation.
    """
    success = sync_scheduler.run_job_now(job_id)

    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    logger.info(
        "Manual job execution triggered",
        job_id=job_id,
        user=current_user.get("username")
    )

    return {
        "message": "Synchronisation demarree",
        "job_id": job_id,
        "triggered_at": datetime.utcnow().isoformat()
    }


@router.delete("/jobs/{job_id}", response_model=Dict[str, Any])
async def delete_job(
    job_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    """
    Supprime une tache planifiee.
    """
    success = sync_scheduler.remove_job(job_id)

    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already deleted")

    logger.info(
        "Job deleted",
        job_id=job_id,
        user=current_user.get("username")
    )

    return {
        "message": "Job supprime",
        "job_id": job_id
    }


@router.get("/history", response_model=Dict[str, Any])
async def get_sync_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Recupere l'historique des synchronisations executees.
    """
    history = sync_scheduler.get_sync_history(limit)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(history),
        "history": history
    }


# ==================== Presets ====================

@router.post("/presets/workday", response_model=Dict[str, Any])
async def create_workday_sync(
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Cree une synchronisation automatique pour les jours ouvrables.
    Execute a 8h00, 12h00 et 18h00 du lundi au vendredi.
    """
    try:
        # Morning sync
        sync_scheduler.add_cron_sync(
            job_id="workday-morning",
            cron_expression="0 8 * * 1-5",
            enabled=True
        )

        # Noon sync
        sync_scheduler.add_cron_sync(
            job_id="workday-noon",
            cron_expression="0 12 * * 1-5",
            enabled=True
        )

        # Evening sync
        sync_scheduler.add_cron_sync(
            job_id="workday-evening",
            cron_expression="0 18 * * 1-5",
            enabled=True
        )

        logger.info(
            "Workday sync preset created",
            user=current_user.get("username")
        )

        return {
            "message": "Synchronisation jours ouvrables configuree (8h, 12h, 18h)",
            "jobs": ["workday-morning", "workday-noon", "workday-evening"]
        }

    except Exception as e:
        logger.error("Failed to create workday preset", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presets/nightly", response_model=Dict[str, Any])
async def create_nightly_sync(
    hour: int = Query(2, ge=0, le=23, description="Heure de la synchronisation nocturne"),
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Cree une synchronisation nocturne quotidienne.
    Par defaut a 2h00 du matin.
    """
    try:
        result = sync_scheduler.add_daily_sync(
            job_id="nightly-sync",
            hour=hour,
            minute=0,
            enabled=True
        )

        logger.info(
            "Nightly sync preset created",
            hour=hour,
            user=current_user.get("username")
        )

        return {
            "message": f"Synchronisation nocturne configuree a {hour:02d}:00",
            "job": result
        }

    except Exception as e:
        logger.error("Failed to create nightly preset", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presets/hourly", response_model=Dict[str, Any])
async def create_hourly_sync(
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Cree une synchronisation toutes les heures.
    """
    try:
        result = sync_scheduler.add_interval_sync(
            job_id="hourly-sync",
            hours=1,
            minutes=0,
            enabled=True
        )

        logger.info(
            "Hourly sync preset created",
            user=current_user.get("username")
        )

        return {
            "message": "Synchronisation horaire configuree",
            "job": result
        }

    except Exception as e:
        logger.error("Failed to create hourly preset", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Contract Check ====================

@router.post("/jobs/contract-check", response_model=Dict[str, Any])
async def create_contract_check(
    config: ContractCheckConfig,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Cree une verification quotidienne des contrats expires.

    Cette tache verifie les contrats expires et desactive automatiquement
    les comptes des employes dont le contrat a expire.
    """
    try:
        result = sync_scheduler.add_contract_check(
            job_id=config.job_id,
            hour=config.hour,
            minute=config.minute,
            enabled=config.enabled
        )

        logger.info(
            "Contract check job created",
            job_id=config.job_id,
            time=f"{config.hour:02d}:{config.minute:02d}",
            user=current_user.get("username")
        )

        return {
            "message": f"Verification des contrats configuree pour {config.hour:02d}:{config.minute:02d}",
            "job": result
        }

    except Exception as e:
        logger.error("Failed to create contract check", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/history", response_model=Dict[str, Any])
async def get_contract_check_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Recupere l'historique des verifications de contrats.
    """
    from app.services.scheduler_service import scheduler_store

    history = scheduler_store.get("contract_check_history", [])

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(history[:limit]),
        "history": history[:limit]
    }
