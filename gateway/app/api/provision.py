"""
API de provisionnement - Point d'entree pour MidPoint
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
import json
import structlog
from datetime import datetime

from app.models.provision import (
    ProvisioningRequest,
    ProvisioningResponse,
    ProvisioningOperation,
    OperationStatus,
    TargetSystem
)
from app.core.security import get_current_user
from app.core.database import get_session
from app.services.provision_service import ProvisionService
from app.services.rule_engine import RuleEngine
from app.services.workflow_service import WorkflowService
from app.services.audit_service import AuditService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/", response_model=ProvisioningResponse)
async def provision_account(
    request: ProvisioningRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Execute une operation de provisionnement multi-cibles.

    - Valide la requete entrante
    - Applique les regles dynamiques pour calculer les attributs
    - Declenche le workflow d'approbation si necessaire
    - Execute le provisionnement sur les systemes cibles
    - Retourne le resultat consolide
    """
    logger.info(
        "Provisioning request received",
        operation=request.operation,
        account_id=request.account_id,
        targets=request.target_systems,
        user=current_user["username"]
    )

    provision_service = ProvisionService(session)
    rule_engine = RuleEngine(session)
    workflow_service = WorkflowService(session)
    audit_service = AuditService(session)

    try:
        # Create operation record
        operation = await provision_service.create_operation(
            request=request,
            created_by=current_user["username"]
        )

        # Log audit event
        await audit_service.log_provision_request(operation, current_user)

        # Apply rules to calculate attributes
        calculated_attrs = await rule_engine.calculate_attributes(
            attributes=request.attributes,
            target_systems=request.target_systems,
            policy_id=request.policy_id
        )

        # Check if workflow approval is needed
        if request.require_approval:
            workflow_instance = await workflow_service.start_pre_workflow(
                operation_id=operation.id,
                context={
                    "account_id": request.account_id,
                    "operation": request.operation,
                    "calculated_attributes": calculated_attrs
                }
            )

            return ProvisioningResponse(
                status=OperationStatus.AWAITING_APPROVAL,
                operation_id=operation.id,
                calculated_attributes=calculated_attrs,
                message=f"Workflow d'approbation demarre. Instance: {workflow_instance.id}",
                timestamp=datetime.utcnow()
            )

        # Execute provisioning
        result = await provision_service.execute_provisioning(
            operation=operation,
            calculated_attributes=calculated_attrs
        )

        # Log success
        await audit_service.log_provision_success(operation, result)

        return ProvisioningResponse(
            status=OperationStatus.SUCCESS,
            operation_id=operation.id,
            calculated_attributes=calculated_attrs,
            message="Provisionnement termine avec succes sur tous les systemes cibles",
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error("Provisioning failed", error=str(e), operation_id=operation.id if operation else None)

        # Attempt rollback
        if operation:
            background_tasks.add_task(
                provision_service.rollback_operation,
                operation.id
            )
            await audit_service.log_provision_failure(operation, str(e))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Provisioning failed: {str(e)}"
        )


@router.get("/{operation_id}", response_model=ProvisioningResponse)
async def get_operation_status(
    operation_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere le statut d'une operation de provisionnement."""
    provision_service = ProvisionService(session)
    operation = await provision_service.get_operation(operation_id)

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation {operation_id} not found"
        )

    calculated_attrs = json.loads(operation.calculated_attributes) if operation.calculated_attributes else {}

    return ProvisioningResponse(
        status=operation.status,
        operation_id=operation.id,
        calculated_attributes=calculated_attrs,
        message=operation.error_message or "Operation en cours",
        timestamp=operation.updated_at
    )


@router.post("/{operation_id}/rollback")
async def rollback_operation(
    operation_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Annule une operation de provisionnement (rollback)."""
    provision_service = ProvisionService(session)
    audit_service = AuditService(session)

    operation = await provision_service.get_operation(operation_id)
    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation {operation_id} not found"
        )

    if operation.status not in [OperationStatus.SUCCESS, OperationStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed operations can be rolled back"
        )

    result = await provision_service.rollback_operation(operation_id)
    await audit_service.log_rollback(operation, current_user)

    return {"message": "Rollback executed", "result": result}


@router.get("/", response_model=List[ProvisioningResponse])
async def list_operations(
    account_id: Optional[str] = None,
    status: Optional[OperationStatus] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Liste les operations de provisionnement."""
    provision_service = ProvisionService(session)
    operations = await provision_service.list_operations(
        account_id=account_id,
        status=status,
        limit=limit,
        offset=offset
    )

    return [
        ProvisioningResponse(
            status=op.status,
            operation_id=op.id,
            calculated_attributes=json.loads(op.calculated_attributes) if op.calculated_attributes else {},
            message=op.error_message or "",
            timestamp=op.updated_at
        )
        for op in operations
    ]
