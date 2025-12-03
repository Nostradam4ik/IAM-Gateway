"""
API de gestion des workflows d'approbation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import structlog

from app.models.workflow import (
    WorkflowConfig,
    WorkflowInstance,
    WorkflowDefinition,
    ApprovalRequest,
    WorkflowInstanceResponse,
    ApprovalStatus,
    ApprovalDecision
)
from app.core.security import get_current_user, require_role
from app.core.database import get_session
from app.services.workflow_service import WorkflowService
from app.services.provision_service import ProvisionService
from app.services.audit_service import AuditService

router = APIRouter()
logger = structlog.get_logger()


@router.get("/configs", response_model=List[WorkflowConfig])
async def list_workflow_configs(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Liste toutes les configurations de workflow."""
    workflow_service = WorkflowService(session)
    return await workflow_service.list_configs()


@router.post("/configs", response_model=WorkflowConfig)
async def create_workflow_config(
    config: WorkflowDefinition,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Cree une nouvelle configuration de workflow."""
    workflow_service = WorkflowService(session)
    return await workflow_service.create_config(config)


@router.get("/configs/{config_id}", response_model=WorkflowConfig)
async def get_workflow_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere une configuration de workflow."""
    workflow_service = WorkflowService(session)
    config = await workflow_service.get_config(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow config {config_id} not found"
        )
    return config


@router.put("/configs/{config_id}", response_model=WorkflowConfig)
async def update_workflow_config(
    config_id: str,
    config: WorkflowDefinition,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Met a jour une configuration de workflow."""
    workflow_service = WorkflowService(session)
    return await workflow_service.update_config(config_id, config)


# Workflow instances
@router.get("/instances", response_model=List[WorkflowInstanceResponse])
async def list_workflow_instances(
    status: Optional[ApprovalStatus] = None,
    approver_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Liste les instances de workflow."""
    workflow_service = WorkflowService(session)
    return await workflow_service.list_instances(
        status=status,
        approver_id=approver_id or current_user["username"],
        limit=limit,
        offset=offset
    )


@router.get("/instances/pending")
async def get_pending_approvals(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere les approbations en attente pour l'utilisateur courant."""
    workflow_service = WorkflowService(session)
    return await workflow_service.get_pending_approvals(current_user["username"])


@router.get("/instances/{instance_id}", response_model=WorkflowInstanceResponse)
async def get_workflow_instance(
    instance_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere les details d'une instance de workflow."""
    workflow_service = WorkflowService(session)
    instance = await workflow_service.get_instance(instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow instance {instance_id} not found"
        )
    return instance


@router.post("/instances/{instance_id}/approve")
async def approve_workflow(
    instance_id: str,
    request: ApprovalRequest,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Approuve une etape de workflow."""
    workflow_service = WorkflowService(session)
    provision_service = ProvisionService(session)
    audit_service = AuditService(session)

    # Verify user is allowed to approve
    instance = await workflow_service.get_instance(instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow instance {instance_id} not found"
        )

    if not await workflow_service.can_approve(instance_id, current_user["username"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to approve this workflow"
        )

    # Record approval
    result = await workflow_service.record_decision(
        instance_id=instance_id,
        approver_id=current_user["username"],
        decision=ApprovalStatus.APPROVED,
        comments=request.comments
    )

    await audit_service.log_workflow_approval(instance_id, current_user, request.comments)

    # Check if workflow is complete
    if result.get("workflow_complete"):
        # Continue provisioning
        operation = await provision_service.continue_after_approval(
            instance.operation_id
        )
        logger.info(
            "Provisioning continued after approval",
            operation_id=instance.operation_id,
            instance_id=instance_id
        )

    return result


@router.post("/instances/{instance_id}/reject")
async def reject_workflow(
    instance_id: str,
    request: ApprovalRequest,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Rejette une etape de workflow."""
    workflow_service = WorkflowService(session)
    provision_service = ProvisionService(session)
    audit_service = AuditService(session)

    instance = await workflow_service.get_instance(instance_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow instance {instance_id} not found"
        )

    if not await workflow_service.can_approve(instance_id, current_user["username"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to reject this workflow"
        )

    result = await workflow_service.record_decision(
        instance_id=instance_id,
        approver_id=current_user["username"],
        decision=ApprovalStatus.REJECTED,
        comments=request.comments
    )

    await audit_service.log_workflow_rejection(instance_id, current_user, request.comments)

    # Cancel the operation
    await provision_service.cancel_operation(
        instance.operation_id,
        reason=f"Rejected by {current_user['username']}: {request.comments}"
    )

    return result


@router.post("/instances/{instance_id}/cancel")
async def cancel_workflow(
    instance_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Annule un workflow en cours (admin only)."""
    workflow_service = WorkflowService(session)

    result = await workflow_service.cancel_instance(instance_id)

    return {"message": f"Workflow {instance_id} cancelled", "result": result}


@router.get("/instances/{instance_id}/history")
async def get_workflow_history(
    instance_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere l'historique des decisions d'un workflow."""
    workflow_service = WorkflowService(session)
    return await workflow_service.get_history(instance_id)
