"""
API de gestion des workflows d'approbation
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
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
from app.core.memory_store import memory_store

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


@router.get("/approve-by-email")
async def approve_workflow_by_email(
    token: str = Query(..., description="Token d'approbation"),
    workflow_id: str = Query(..., description="ID du workflow"),
    action: str = Query(..., description="Action: approve ou reject"),
    session=Depends(get_session)
):
    """
    Endpoint d'approbation par email.
    Permet au manager d'approuver ou rejeter directement via le lien email.
    Retourne une page HTML de confirmation.
    """
    if action not in ["approve", "reject"]:
        return HTMLResponse(
            content=_generate_error_page("Action invalide. Utilisez 'approve' ou 'reject'."),
            status_code=400
        )

    workflow_service = WorkflowService(session)
    provision_service = ProvisionService(session)

    # Traiter l'approbation
    result = await workflow_service.approve_by_token(
        workflow_id=workflow_id,
        token=token,
        action=action
    )

    if not result.get("success"):
        return HTMLResponse(
            content=_generate_error_page(result.get("error", "Erreur inconnue")),
            status_code=400
        )

    # Si approuve, continuer le provisionnement
    if action == "approve":
        workflow = memory_store.get_workflow(workflow_id)
        if workflow:
            operation_id = workflow.get("operation_id")
            if operation_id:
                try:
                    await provision_service.continue_after_approval(operation_id)
                    logger.info("Provisioning continued after email approval", operation_id=operation_id)
                except Exception as e:
                    logger.error("Failed to continue provisioning", error=str(e))

    # Generer page de confirmation
    return HTMLResponse(
        content=_generate_success_page(action, result),
        status_code=200
    )


def _generate_success_page(action: str, result: dict) -> str:
    """Genere une page HTML de succes."""
    action_text = "approuvee" if action == "approve" else "rejetee"
    action_color = "#22c55e" if action == "approve" else "#ef4444"
    icon = "✓" if action == "approve" else "✗"

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>IAM Gateway - Demande {action_text}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 100%;
            text-align: center;
            overflow: hidden;
        }}
        .header {{
            background: {action_color};
            color: white;
            padding: 40px;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 16px;
        }}
        .title {{
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }}
        .content {{
            padding: 40px;
        }}
        .message {{
            color: #475569;
            font-size: 16px;
            line-height: 1.6;
        }}
        .workflow-id {{
            background: #f1f5f9;
            padding: 10px 16px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 14px;
            color: #64748b;
            margin-top: 20px;
        }}
        .btn {{
            display: inline-block;
            background: #3b82f6;
            color: white;
            padding: 12px 32px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 24px;
            transition: background 0.2s;
        }}
        .btn:hover {{
            background: #2563eb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">{icon}</div>
            <h1 class="title">Demande {action_text.capitalize()}</h1>
        </div>
        <div class="content">
            <p class="message">
                {result.get('message', f'La demande a ete {action_text} avec succes.')}
            </p>
            <div class="workflow-id">
                ID: {result.get('workflow_id', 'N/A')}
            </div>
            <a href="http://localhost:3000/dashboard/workflows" class="btn">
                Voir le tableau de bord
            </a>
        </div>
    </div>
</body>
</html>
"""


def _generate_error_page(error: str) -> str:
    """Genere une page HTML d'erreur."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>IAM Gateway - Erreur</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 100%;
            text-align: center;
            overflow: hidden;
        }}
        .header {{
            background: #ef4444;
            color: white;
            padding: 40px;
        }}
        .icon {{ font-size: 64px; margin-bottom: 16px; }}
        .title {{ font-size: 24px; font-weight: bold; margin: 0; }}
        .content {{ padding: 40px; }}
        .error-message {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #991b1b;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .btn {{
            display: inline-block;
            background: #3b82f6;
            color: white;
            padding: 12px 32px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">⚠</div>
            <h1 class="title">Erreur</h1>
        </div>
        <div class="content">
            <div class="error-message">{error}</div>
            <a href="http://localhost:3000/dashboard/workflows" class="btn">
                Retour au tableau de bord
            </a>
        </div>
    </div>
</body>
</html>
"""
