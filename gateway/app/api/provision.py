"""
API de provisionnement - Point d'entree pour MidPoint

Ce module gere le provisionnement des utilisateurs.
Quand MIDPOINT_ENABLED=True, toutes les operations passent par MidPoint
qui se charge de propager aux systemes cibles.
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
from app.core.config import settings
from app.core.memory_store import memory_store
from app.services.provision_service import ProvisionService
from app.services.midpoint_provision_service import MidPointProvisionService, get_midpoint_provision_service
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
    Execute une operation de provisionnement.

    Si MIDPOINT_ENABLED=True (defaut):
        Gateway -> MidPoint -> [LDAP, Odoo, SQL, ...]
        MidPoint gere la propagation vers les systemes cibles.

    Sinon:
        Gateway -> [LDAP, Odoo, SQL, ...] directement
    """
    logger.info(
        "Provisioning request received",
        operation=request.operation,
        account_id=request.account_id,
        targets=request.target_systems,
        user=current_user["username"],
        midpoint_enabled=settings.MIDPOINT_ENABLED
    )

    # Use MidPoint as hub if enabled
    if settings.MIDPOINT_ENABLED:
        return await _provision_via_midpoint(request, current_user, session)

    # Legacy: direct provisioning to targets
    return await _provision_direct(request, background_tasks, current_user, session)


async def _provision_via_midpoint(
    request: ProvisioningRequest,
    current_user: dict,
    session
) -> ProvisioningResponse:
    """
    Provision via MidPoint hub.

    MidPoint handles:
    - User storage in its repository
    - Propagation to configured Resources (LDAP, Odoo, SQL)
    - Workflow approvals
    - Audit logging
    """
    try:
        midpoint_service = await get_midpoint_provision_service(session)

        result = await midpoint_service.provision(
            request=request,
            created_by=current_user["username"]
        )

        # Add audit log
        memory_store.add_audit_log({
            "type": "provision",
            "action": request.operation.value,
            "account_id": request.account_id,
            "actor": current_user["username"],
            "target_systems": ["MIDPOINT"],
            "original_targets": [t.value for t in request.target_systems],
            "status": "success",
            "midpoint_hub": True
        })

        return ProvisioningResponse(
            status=OperationStatus.SUCCESS,
            operation_id=result.get("operation_id", ""),
            calculated_attributes={"midpoint": result.get("midpoint_result", {})},
            message=result.get("message", "Provisionnement via MidPoint termine"),
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error("MidPoint provisioning failed", error=str(e))

        memory_store.add_audit_log({
            "type": "provision",
            "action": request.operation.value,
            "account_id": request.account_id,
            "actor": current_user["username"],
            "status": "failed",
            "error": str(e),
            "midpoint_hub": True
        })

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MidPoint provisioning failed: {str(e)}"
        )


async def _provision_direct(
    request: ProvisioningRequest,
    background_tasks: BackgroundTasks,
    current_user: dict,
    session
) -> ProvisioningResponse:
    """
    Legacy: Direct provisioning to target systems.

    Used when MIDPOINT_ENABLED=False.
    """
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
        # Include account_id in attributes for rule engine
        enriched_attributes = {**request.attributes, "account_id": request.account_id}
        calculated_attrs = await rule_engine.calculate_attributes(
            attributes=enriched_attributes,
            target_systems=request.target_systems,
            policy_id=request.policy_id
        )

        # Check if workflow approval is needed
        if request.require_approval:
            # Extraire l'email du manager des attributs
            manager_email = request.attributes.get("manager_email", "")

            if manager_email:
                # Creer un workflow simplifie avec notification email
                user_data = {
                    **request.attributes,
                    "account_id": request.account_id,
                }
                workflow_result = await workflow_service.create_approval_workflow(
                    operation_id=operation.id,
                    user_data=user_data,
                    manager_email=manager_email,
                    requester=current_user["username"]
                )

                # Sauvegarder l'operation avec statut pending
                memory_store.save_operation(operation.id, {
                    "operation_id": operation.id,
                    "account_id": request.account_id,
                    "operation": request.operation.value,
                    "status": "awaiting_approval",
                    "target_systems": [t.value for t in request.target_systems],
                    "user_data": request.attributes,
                    "calculated_attributes": calculated_attrs,
                    "created_by": current_user["username"],
                    "workflow_id": workflow_result.get("workflow_id"),
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Add audit log
                memory_store.add_audit_log({
                    "type": "workflow",
                    "action": "approval_requested",
                    "account_id": request.account_id,
                    "actor": current_user["username"],
                    "target_systems": [t.value for t in request.target_systems],
                    "status": "pending",
                    "manager_email": manager_email
                })

                return ProvisioningResponse(
                    status=OperationStatus.AWAITING_APPROVAL,
                    operation_id=operation.id,
                    calculated_attributes=calculated_attrs,
                    message=f"Demande en attente d'approbation. Email envoye a {manager_email}",
                    timestamp=datetime.utcnow()
                )
            else:
                # Workflow standard sans email
                workflow_instance = await workflow_service.start_pre_workflow(
                    operation_id=operation.id,
                    context={
                        "account_id": request.account_id,
                        "operation": request.operation,
                        "calculated_attributes": calculated_attrs,
                        **request.attributes
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

        # Save operation to memory store
        memory_store.save_operation(operation.id, {
            "operation_id": operation.id,
            "account_id": request.account_id,
            "operation": request.operation.value,
            "status": "success",
            "target_systems": [t.value for t in request.target_systems],
            "calculated_attributes": calculated_attrs,
            "created_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat()
        })

        # Add audit log
        memory_store.add_audit_log({
            "type": "provision",
            "action": "create",
            "account_id": request.account_id,
            "actor": current_user["username"],
            "target_systems": [t.value for t in request.target_systems],
            "status": "success"
        })

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


@router.get("/")
async def list_operations(
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Liste les operations de provisionnement."""
    operations = memory_store.list_operations(
        account_id=account_id,
        status=status,
        limit=limit,
        offset=offset
    )

    return [
        {
            "operation_id": op.get("operation_id"),
            "account_id": op.get("account_id"),
            "status": op.get("status"),
            "calculated_attributes": op.get("calculated_attributes", {}),
            "user_data": op.get("user_data", {}),
            "target_systems": op.get("target_systems", []),
            "message": op.get("message", ""),
            "timestamp": op.get("timestamp")
        }
        for op in operations
    ]


@router.put("/{operation_id}")
async def update_operation(
    operation_id: str,
    request: ProvisioningRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Met a jour un utilisateur existant.
    Modifie les attributs dans les systemes cibles.
    """
    logger.info(
        "Update request received",
        operation_id=operation_id,
        account_id=request.account_id,
        targets=request.target_systems,
        user=current_user["username"]
    )

    provision_service = ProvisionService(session)
    rule_engine = RuleEngine(session)
    audit_service = AuditService(session)

    # Get existing operation
    existing_op = memory_store.get_operation(operation_id)
    if not existing_op:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation {operation_id} not found"
        )

    try:
        # Create new operation for update
        operation = await provision_service.create_operation(
            request=request,
            created_by=current_user["username"]
        )

        # Calculate new attributes
        enriched_attributes = {**request.attributes, "account_id": request.account_id}
        calculated_attrs = await rule_engine.calculate_attributes(
            attributes=enriched_attributes,
            target_systems=request.target_systems,
            policy_id=request.policy_id
        )

        # Execute update provisioning
        result = await provision_service.execute_provisioning(
            operation=operation,
            calculated_attributes=calculated_attrs
        )

        # Update memory store
        memory_store.save_operation(operation.id, {
            "operation_id": operation.id,
            "account_id": request.account_id,
            "operation": "update",
            "status": "success",
            "target_systems": [t.value for t in request.target_systems],
            "user_data": request.attributes,
            "calculated_attributes": calculated_attrs,
            "created_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat()
        })

        # Add audit log
        memory_store.add_audit_log({
            "type": "provision",
            "action": "update",
            "account_id": request.account_id,
            "actor": current_user["username"],
            "target_systems": [t.value for t in request.target_systems],
            "status": "success"
        })

        return {
            "status": "success",
            "operation_id": operation.id,
            "message": "Utilisateur mis a jour avec succes",
            "calculated_attributes": calculated_attrs
        }

    except Exception as e:
        logger.error("Update failed", error=str(e), operation_id=operation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/{operation_id}")
async def delete_operation(
    operation_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Supprime un utilisateur des systemes cibles.
    """
    logger.info(
        "Delete request received",
        operation_id=operation_id,
        user=current_user["username"]
    )

    provision_service = ProvisionService(session)

    # Get existing operation
    existing_op = memory_store.get_operation(operation_id)
    if not existing_op:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation {operation_id} not found"
        )

    account_id = existing_op.get("account_id")
    target_systems = existing_op.get("target_systems", [])
    calculated_attrs = existing_op.get("calculated_attributes", {})

    errors = []
    deleted_systems = []

    try:
        # Delete from each target system
        for target in target_systems:
            try:
                connector = provision_service._get_connector(target)
                if connector:
                    # Get the account identifier for each system
                    target_attrs = calculated_attrs.get(target, {})
                    account_identifier = target_attrs.get("uid") or target_attrs.get("username") or account_id

                    await connector.delete_account(account_identifier)
                    deleted_systems.append(target)
                    logger.info(f"Deleted from {target}", account_id=account_identifier)
            except Exception as e:
                errors.append(f"{target}: {str(e)}")
                logger.error(f"Failed to delete from {target}", error=str(e))

        # Update operation status
        new_status = "deleted" if not errors else "partially_deleted"
        memory_store.update_operation(operation_id, {
            "status": new_status,
            "message": f"Supprime de: {', '.join(deleted_systems)}" + (f". Erreurs: {', '.join(errors)}" if errors else ""),
            "updated_at": datetime.utcnow().isoformat()
        })

        # Add audit log
        memory_store.add_audit_log({
            "type": "provision",
            "action": "delete",
            "account_id": account_id,
            "actor": current_user["username"],
            "target_systems": deleted_systems,
            "status": "success" if not errors else "partial"
        })

        return {
            "status": "success" if not errors else "partial",
            "message": f"Utilisateur supprime de {len(deleted_systems)} systeme(s)",
            "deleted_from": deleted_systems,
            "errors": errors if errors else None
        }

    except Exception as e:
        logger.error("Delete failed", error=str(e), operation_id=operation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )


# ==================== MidPoint-specific endpoints ====================

@router.get("/midpoint/users")
async def list_midpoint_users(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """List all users from MidPoint."""
    if not settings.MIDPOINT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MidPoint is not enabled"
        )

    midpoint_service = await get_midpoint_provision_service(session)
    users = await midpoint_service.list_users()

    return {"users": users, "count": len(users)}


@router.get("/midpoint/users/{account_id}")
async def get_midpoint_user(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Get a specific user from MidPoint with their shadow accounts."""
    if not settings.MIDPOINT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MidPoint is not enabled"
        )

    midpoint_service = await get_midpoint_provision_service(session)

    user = await midpoint_service.get_user(account_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {account_id} not found in MidPoint"
        )

    # Get shadow accounts (projections to target systems)
    shadows = await midpoint_service.get_user_shadows(account_id)

    return {
        "user": user,
        "shadows": shadows,
        "provisioned_to": len(shadows)
    }


@router.get("/midpoint/roles")
async def list_midpoint_roles(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """List all roles from MidPoint."""
    if not settings.MIDPOINT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MidPoint is not enabled"
        )

    midpoint_service = await get_midpoint_provision_service(session)
    roles = await midpoint_service.get_roles()

    return {"roles": roles, "count": len(roles)}


@router.post("/midpoint/users/{account_id}/roles/{role_name}")
async def assign_role_to_user(
    account_id: str,
    role_name: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Assign a role to a user (triggers provisioning to role's Resources)."""
    if not settings.MIDPOINT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MidPoint is not enabled"
        )

    midpoint_service = await get_midpoint_provision_service(session)
    success = await midpoint_service.assign_role(account_id, role_name)

    if success:
        memory_store.add_audit_log({
            "type": "role_assignment",
            "action": "assign",
            "account_id": account_id,
            "role": role_name,
            "actor": current_user["username"],
            "status": "success"
        })
        return {"success": True, "message": f"Role {role_name} assigned to {account_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign role {role_name}"
        )


@router.delete("/midpoint/users/{account_id}/roles/{role_name}")
async def remove_role_from_user(
    account_id: str,
    role_name: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Remove a role from a user (may trigger deprovisioning)."""
    if not settings.MIDPOINT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MidPoint is not enabled"
        )

    midpoint_service = await get_midpoint_provision_service(session)
    success = await midpoint_service.remove_role(account_id, role_name)

    if success:
        memory_store.add_audit_log({
            "type": "role_assignment",
            "action": "remove",
            "account_id": account_id,
            "role": role_name,
            "actor": current_user["username"],
            "status": "success"
        })
        return {"success": True, "message": f"Role {role_name} removed from {account_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove role {role_name}"
        )


@router.get("/midpoint/resources")
async def list_midpoint_resources(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """List all configured Resources (target systems) in MidPoint."""
    if not settings.MIDPOINT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MidPoint is not enabled"
        )

    midpoint_service = await get_midpoint_provision_service(session)
    resources = await midpoint_service.get_resources()

    return {"resources": resources, "count": len(resources)}


@router.get("/midpoint/status")
async def midpoint_status(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Check MidPoint connection status."""
    from app.connectors.midpoint_connector import MidPointConnector

    connector = MidPointConnector()
    connected = await connector.test_connection()
    await connector.close()

    return {
        "enabled": settings.MIDPOINT_ENABLED,
        "connected": connected,
        "url": settings.MIDPOINT_URL,
        "user": settings.MIDPOINT_USER
    }
