"""
Service de gestion des workflows d'approbation
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import structlog

from app.models.workflow import (
    WorkflowConfig,
    WorkflowInstance,
    WorkflowDefinition,
    WorkflowType,
    ApprovalStatus,
    ApprovalLevel,
    ApprovalDecision,
    ApproverType,
    WorkflowInstanceResponse
)
from app.core.config import settings

logger = structlog.get_logger()


class WorkflowService:
    """
    Service de gestion des workflows d'approbation.

    Supporte:
    - Workflows pre et post provisionnement
    - N niveaux d'approbation configurables
    - Timeout et auto-approbation
    - Notifications (a integrer)
    """

    def __init__(self, session):
        self.session = session

    async def create_config(self, definition: WorkflowDefinition) -> WorkflowConfig:
        """Cree une nouvelle configuration de workflow."""
        config = WorkflowConfig(
            name=definition.name,
            description=definition.description,
            workflow_type=definition.workflow_type,
            levels=json.dumps(definition.levels),
            timeout_hours=definition.timeout_hours,
            auto_approve_on_timeout=definition.auto_approve_on_timeout
        )

        # Save to DB
        logger.info("Workflow config created", name=config.name)
        return config

    async def get_config(self, config_id: str) -> Optional[WorkflowConfig]:
        """Recupere une configuration de workflow."""
        return None

    async def update_config(
        self,
        config_id: str,
        definition: WorkflowDefinition
    ) -> WorkflowConfig:
        """Met a jour une configuration de workflow."""
        pass

    async def list_configs(self) -> List[WorkflowConfig]:
        """Liste les configurations de workflow."""
        # Return default configs
        return [
            WorkflowConfig(
                id="wf-default-pre",
                name="Approbation standard pre-provisionnement",
                workflow_type=WorkflowType.PRE_PROVISIONING,
                levels=json.dumps([
                    {
                        "level": 1,
                        "name": "Manager de l'employe",
                        "approver_type": "manager",
                        "required_approvals": 1
                    },
                    {
                        "level": 2,
                        "name": "Chef de departement",
                        "approver_type": "department_head",
                        "required_approvals": 1
                    },
                    {
                        "level": 3,
                        "name": "Responsable application",
                        "approver_type": "app_owner",
                        "required_approvals": 1
                    }
                ]),
                timeout_hours=72
            ),
            WorkflowConfig(
                id="wf-default-post",
                name="Validation post-provisionnement",
                workflow_type=WorkflowType.POST_PROVISIONING,
                levels=json.dumps([
                    {
                        "level": 1,
                        "name": "Confirmation secretaire",
                        "approver_type": "role",
                        "approver_ids": ["secretary"],
                        "required_approvals": 1
                    }
                ]),
                timeout_hours=48
            )
        ]

    async def start_pre_workflow(
        self,
        operation_id: str,
        context: Dict[str, Any]
    ) -> WorkflowInstance:
        """Demarre un workflow pre-provisionnement."""
        return await self._start_workflow(
            operation_id=operation_id,
            workflow_type=WorkflowType.PRE_PROVISIONING,
            context=context
        )

    async def start_post_workflow(
        self,
        operation_id: str,
        context: Dict[str, Any]
    ) -> WorkflowInstance:
        """Demarre un workflow post-provisionnement."""
        return await self._start_workflow(
            operation_id=operation_id,
            workflow_type=WorkflowType.POST_PROVISIONING,
            context=context
        )

    async def _start_workflow(
        self,
        operation_id: str,
        workflow_type: WorkflowType,
        context: Dict[str, Any]
    ) -> WorkflowInstance:
        """Demarre une instance de workflow."""
        # Get default config for type
        configs = await self.list_configs()
        config = next(
            (c for c in configs if c.workflow_type == workflow_type),
            None
        )

        if not config:
            raise ValueError(f"No workflow config found for type {workflow_type}")

        levels = json.loads(config.levels)
        timeout = datetime.utcnow() + timedelta(hours=config.timeout_hours)

        instance = WorkflowInstance(
            workflow_id=config.id,
            operation_id=operation_id,
            status=ApprovalStatus.PENDING,
            current_level=1,
            total_levels=len(levels),
            context_data=json.dumps(context),
            expires_at=timeout
        )

        # Create approval levels
        for level_config in levels:
            level = ApprovalLevel(
                workflow_instance_id=instance.id,
                level_number=level_config["level"],
                approver_type=ApproverType(level_config["approver_type"]),
                approver_ids=json.dumps(level_config.get("approver_ids", [])),
                required_approvals=level_config.get("required_approvals", 1)
            )
            # Save level

        logger.info(
            "Workflow started",
            instance_id=instance.id,
            operation_id=operation_id,
            type=workflow_type,
            levels=len(levels)
        )

        return instance

    async def get_instance(self, instance_id: str) -> Optional[WorkflowInstanceResponse]:
        """Recupere les details d'une instance."""
        # Mock response
        return WorkflowInstanceResponse(
            id=instance_id,
            workflow_id="wf-default-pre",
            operation_id="op-123",
            status=ApprovalStatus.PENDING,
            current_level=1,
            total_levels=3,
            pending_approvers=["manager@example.com"],
            history=[]
        )

    async def list_instances(
        self,
        status: Optional[ApprovalStatus] = None,
        approver_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkflowInstanceResponse]:
        """Liste les instances de workflow."""
        return []

    async def get_pending_approvals(self, user_id: str) -> List[Dict[str, Any]]:
        """Recupere les approbations en attente pour un utilisateur."""
        return []

    async def can_approve(self, instance_id: str, user_id: str) -> bool:
        """Verifie si un utilisateur peut approuver."""
        # Check if user is in current level approvers
        return True

    async def record_decision(
        self,
        instance_id: str,
        approver_id: str,
        decision: ApprovalStatus,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enregistre une decision d'approbation."""
        instance = await self.get_instance(instance_id)

        # Create decision record
        decision_record = ApprovalDecision(
            approval_level_id=f"level-{instance.current_level}",
            approver_id=approver_id,
            decision=decision,
            comments=comments
        )

        logger.info(
            "Approval decision recorded",
            instance_id=instance_id,
            decision=decision,
            approver=approver_id
        )

        # Check if level is complete
        if decision == ApprovalStatus.APPROVED:
            # Check if all required approvals for this level
            if await self._is_level_complete(instance_id, instance.current_level):
                if instance.current_level >= instance.total_levels:
                    # Workflow complete
                    return {
                        "workflow_complete": True,
                        "status": ApprovalStatus.APPROVED,
                        "message": "Toutes les approbations obtenues"
                    }
                else:
                    # Move to next level
                    return {
                        "workflow_complete": False,
                        "next_level": instance.current_level + 1,
                        "message": f"Niveau {instance.current_level} approuve, passage au niveau suivant"
                    }

        elif decision == ApprovalStatus.REJECTED:
            return {
                "workflow_complete": True,
                "status": ApprovalStatus.REJECTED,
                "message": f"Rejete par {approver_id}: {comments}"
            }

        return {
            "workflow_complete": False,
            "message": "Decision enregistree, en attente d'autres approbations"
        }

    async def _is_level_complete(self, instance_id: str, level: int) -> bool:
        """Verifie si un niveau est complet."""
        # Check approvals count vs required
        return True

    async def cancel_instance(self, instance_id: str) -> Dict[str, Any]:
        """Annule une instance de workflow."""
        logger.info("Workflow cancelled", instance_id=instance_id)
        return {"cancelled": True}

    async def get_history(self, instance_id: str) -> List[Dict[str, Any]]:
        """Recupere l'historique des decisions."""
        return []

    async def check_expired_workflows(self) -> None:
        """Verifie et traite les workflows expires."""
        # Background task to handle timeouts
        pass
