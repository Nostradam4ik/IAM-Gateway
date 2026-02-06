"""
Service de gestion des workflows d'approbation multi-niveaux.

Chaine d'approbation:
1. Manager (responsable direct de l'employe)
2. RH Manager (responsable RH)
3. IT Admin (administrateur IT)
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import uuid
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
from app.core.memory_store import memory_store
from app.services.email_service import email_service

logger = structlog.get_logger()


# Configuration des niveaux d'approbation par defaut
DEFAULT_APPROVAL_LEVELS = [
    {
        "level": 1,
        "name": "Manager",
        "description": "Approbation du manager direct",
        "approver_type": "manager",
        "role_required": "manager",
        "timeout_hours": 48,
        "auto_approve_on_timeout": False,
        "required_approvals": 1
    },
    {
        "level": 2,
        "name": "RH Manager",
        "description": "Validation par les Ressources Humaines",
        "approver_type": "role",
        "role_required": "rh_manager",
        "timeout_hours": 48,
        "auto_approve_on_timeout": False,
        "required_approvals": 1
    },
    {
        "level": 3,
        "name": "IT Admin",
        "description": "Approbation finale par l'equipe IT",
        "approver_type": "role",
        "role_required": "it_admin",
        "timeout_hours": 24,
        "auto_approve_on_timeout": True,
        "required_approvals": 1
    }
]

# Note: Les approbateurs sont maintenant recuperes dynamiquement
# via le UserService depuis la base de donnees gateway_users


class WorkflowService:
    """
    Service de gestion des workflows d'approbation multi-niveaux.

    Supporte:
    - 3 niveaux d'approbation: Manager → RH → IT Admin
    - Notifications email a chaque niveau (recuperes par role depuis la DB)
    - Tokens securises pour approbation par email
    - Historique complet des decisions
    - Timeout et auto-approbation configurables
    """

    def __init__(self, session=None):
        self.session = session
        self._user_service = None

    async def _get_user_service(self):
        """Recupere le UserService pour obtenir les emails par role."""
        if self._user_service is None and self.session:
            from app.services.user_service import UserService
            self._user_service = UserService(self.session)
        return self._user_service

    async def _get_emails_by_role(self, role: str) -> List[str]:
        """
        Recupere les emails des utilisateurs ayant un role specifique.
        Utilise le UserService pour interroger la base de donnees.
        """
        user_service = await self._get_user_service()
        if user_service:
            emails = await user_service.get_emails_by_role(role)
            if emails:
                return emails

        # Fallback si pas de session ou pas d'utilisateurs trouves
        fallback_emails = {
            "manager": ["admin@gateway.local"],
            "rh_manager": ["admin@gateway.local"],
            "it_admin": ["admin@gateway.local"],
        }
        return fallback_emails.get(role, ["admin@gateway.local"])

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
        return [
            WorkflowConfig(
                id="wf-multi-level-approval",
                name="Approbation multi-niveaux (Manager → RH → IT)",
                workflow_type=WorkflowType.PRE_PROVISIONING,
                levels=json.dumps(DEFAULT_APPROVAL_LEVELS),
                timeout_hours=120,
                description="Workflow d'approbation standard a 3 niveaux"
            ),
            WorkflowConfig(
                id="wf-manager-only",
                name="Approbation manager uniquement",
                workflow_type=WorkflowType.PRE_PROVISIONING,
                levels=json.dumps([DEFAULT_APPROVAL_LEVELS[0]]),
                timeout_hours=48,
                description="Approbation simple par le manager"
            ),
            WorkflowConfig(
                id="wf-rh-it",
                name="Approbation RH + IT",
                workflow_type=WorkflowType.PRE_PROVISIONING,
                levels=json.dumps([DEFAULT_APPROVAL_LEVELS[1], DEFAULT_APPROVAL_LEVELS[2]]),
                timeout_hours=72,
                description="Approbation RH puis IT (sans manager)"
            )
        ]

    async def create_multi_level_approval_workflow(
        self,
        operation_id: str,
        user_data: Dict[str, Any],
        manager_email: str,
        requester: str,
        workflow_type: str = "full"  # "full", "manager_only", "rh_it"
    ) -> Dict[str, Any]:
        """
        Cree un workflow d'approbation multi-niveaux.

        Args:
            operation_id: ID de l'operation de provisioning
            user_data: Donnees de l'utilisateur a creer
            manager_email: Email du manager direct
            requester: Qui a fait la demande
            workflow_type: Type de workflow ("full", "manager_only", "rh_it")

        Returns:
            Dict avec workflow_id et statut
        """
        workflow_id = f"wf-{str(uuid.uuid4())[:8]}"

        # Selectionner les niveaux selon le type
        if workflow_type == "manager_only":
            levels = [DEFAULT_APPROVAL_LEVELS[0]]
        elif workflow_type == "rh_it":
            levels = [DEFAULT_APPROVAL_LEVELS[1], DEFAULT_APPROVAL_LEVELS[2]]
        else:  # full
            levels = DEFAULT_APPROVAL_LEVELS.copy()

        # Calculer le timeout total
        total_timeout_hours = sum(l.get("timeout_hours", 48) for l in levels)
        timeout = datetime.utcnow() + timedelta(hours=total_timeout_hours)

        # Preparer le contexte
        context = {
            **user_data,
            "manager_email": manager_email,
            "requester": requester,
        }

        user_name = f"{user_data.get('firstname', '')} {user_data.get('lastname', '')}".strip() or user_data.get('account_id', 'Unknown')

        # Structure pour stocker les decisions de chaque niveau
        level_decisions = {}
        for level in levels:
            level_num = level["level"]
            level_decisions[str(level_num)] = {
                "level": level_num,
                "name": level["name"],
                "status": "pending" if level_num == 1 else "waiting",
                "approver_type": level["approver_type"],
                "role_required": level.get("role_required"),
                "decided_by": None,
                "decided_at": None,
                "comments": None,
                "tokens": {}
            }

        # Determiner le premier approbateur
        first_level = levels[0]
        if first_level["approver_type"] == "manager":
            first_approver_email = manager_email
        else:
            # Chercher les approbateurs par role depuis la base de donnees
            role = first_level.get("role_required", "")
            approvers = await self._get_emails_by_role(role)
            first_approver_email = approvers[0] if approvers else "admin@gateway.local"

        workflow_data = {
            "id": workflow_id,
            "workflow_id": "wf-multi-level-approval",
            "workflow_type": workflow_type,
            "operation_id": operation_id,
            "status": "pending",
            "current_level": 1,
            "total_levels": len(levels),
            "levels": levels,
            "level_decisions": level_decisions,
            "user_name": user_name,
            "operation_name": f"Creation compte: {user_data.get('account_id', 'N/A')}",
            "pending_approvers": [first_approver_email],
            "context": context,
            "history": [],
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": timeout.isoformat(),
        }

        # Envoyer notification email au premier approbateur
        email_result = await self._send_level_notification(
            workflow_id=workflow_id,
            workflow_data=workflow_data,
            level=1,
            approver_email=first_approver_email,
            user_data=user_data,
            requester=requester
        )

        # Stocker les tokens
        level_decisions["1"]["tokens"] = {
            "approve_token": email_result.get("approve_token"),
            "reject_token": email_result.get("reject_token"),
            "approver_email": first_approver_email
        }
        workflow_data["level_decisions"] = level_decisions
        workflow_data["email_sent"] = email_result.get("sent", False)

        # Ajouter a l'historique
        workflow_data["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "workflow_created",
            "level": 1,
            "details": f"Workflow cree, notification envoyee a {first_approver_email}",
            "email_sent": email_result.get("sent", False)
        })

        memory_store.save_workflow(workflow_id, workflow_data)

        logger.info(
            "Multi-level approval workflow created",
            workflow_id=workflow_id,
            operation_id=operation_id,
            total_levels=len(levels),
            first_approver=first_approver_email,
            email_sent=email_result.get("sent")
        )

        return {
            "workflow_id": workflow_id,
            "status": "pending",
            "current_level": 1,
            "total_levels": len(levels),
            "email_sent": email_result.get("sent", False),
            "message": f"Workflow cree avec {len(levels)} niveaux. Notification envoyee a {first_approver_email}"
        }

    async def _send_level_notification(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any],
        level: int,
        approver_email: str,
        user_data: Dict[str, Any],
        requester: str
    ) -> Dict[str, Any]:
        """
        Envoie une notification email pour un niveau specifique.
        """
        level_info = None
        for l in workflow_data.get("levels", []):
            if l["level"] == level:
                level_info = l
                break

        level_name = level_info["name"] if level_info else f"Niveau {level}"
        total_levels = workflow_data.get("total_levels", 3)

        # Utiliser le service email avec le contexte du niveau
        enhanced_user_data = {
            **user_data,
            "approval_level": level,
            "approval_level_name": level_name,
            "total_levels": total_levels,
        }

        result = await email_service.send_multilevel_approval_request(
            workflow_id=workflow_id,
            approver_email=approver_email,
            user_data=enhanced_user_data,
            requester=requester,
            level=level,
            level_name=level_name,
            total_levels=total_levels
        )

        return result

    async def approve_level(
        self,
        workflow_id: str,
        approver_id: str,
        approver_email: str,
        comments: Optional[str] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approuve le niveau actuel du workflow.

        Si tous les niveaux sont approuves, le workflow est complete.
        Sinon, passe au niveau suivant et envoie notification.
        """
        workflow = memory_store.get_workflow(workflow_id)
        if not workflow:
            return {"success": False, "error": "Workflow non trouve"}

        if workflow.get("status") != "pending":
            return {"success": False, "error": f"Workflow deja traite (statut: {workflow.get('status')})"}

        current_level = workflow.get("current_level", 1)

        # Verifier le token si fourni
        if token:
            level_decisions = workflow.get("level_decisions", {})
            level_tokens = level_decisions.get(str(current_level), {}).get("tokens", {})
            if level_tokens.get("approve_token") != token:
                return {"success": False, "error": "Token invalide"}

        # Marquer le niveau comme approuve
        level_decisions = workflow.get("level_decisions", {})
        if str(current_level) in level_decisions:
            level_decisions[str(current_level)]["status"] = "approved"
            level_decisions[str(current_level)]["decided_by"] = approver_email
            level_decisions[str(current_level)]["decided_at"] = datetime.utcnow().isoformat()
            level_decisions[str(current_level)]["comments"] = comments

        # Ajouter a l'historique
        levels = workflow.get("levels", [])
        level_name = "Niveau " + str(current_level)
        for l in levels:
            if l["level"] == current_level:
                level_name = l["name"]
                break

        workflow["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "level_approved",
            "level": current_level,
            "level_name": level_name,
            "approver": approver_email,
            "comments": comments
        })

        total_levels = workflow.get("total_levels", 1)

        if current_level >= total_levels:
            # Workflow complete - tous les niveaux approuves
            workflow["status"] = "approved"
            workflow["completed_at"] = datetime.utcnow().isoformat()
            workflow["history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": "workflow_approved",
                "details": "Tous les niveaux ont ete approuves"
            })

            memory_store.save_workflow(workflow_id, workflow)

            # Notifier le demandeur
            context = workflow.get("context", {})
            requester_email = context.get("email")
            if requester_email:
                await email_service.send_workflow_complete_notification(
                    user_email=requester_email,
                    user_data=context,
                    approved=True,
                    workflow_id=workflow_id
                )

            # Si c'est une synchronisation Odoo, executer la creation du compte
            if context.get("source") == "odoo":
                await self._execute_odoo_sync(workflow_id, context)

            logger.info(
                "Workflow fully approved",
                workflow_id=workflow_id,
                total_levels=total_levels
            )

            return {
                "success": True,
                "workflow_id": workflow_id,
                "action": "approved",
                "status": "approved",
                "workflow_complete": True,
                "message": f"Workflow approuve (niveau final {current_level}/{total_levels})"
            }

        # Passer au niveau suivant
        next_level = current_level + 1
        workflow["current_level"] = next_level

        # Mettre a jour le statut du niveau suivant
        if str(next_level) in level_decisions:
            level_decisions[str(next_level)]["status"] = "pending"

        # Determiner l'approbateur du niveau suivant
        next_level_info = None
        for l in levels:
            if l["level"] == next_level:
                next_level_info = l
                break

        if next_level_info:
            if next_level_info["approver_type"] == "manager":
                next_approver_email = workflow.get("context", {}).get("manager_email", "admin@gateway.local")
            else:
                # Chercher les approbateurs par role depuis la base de donnees
                role = next_level_info.get("role_required", "")
                approvers = await self._get_emails_by_role(role)
                next_approver_email = approvers[0] if approvers else "admin@gateway.local"

            workflow["pending_approvers"] = [next_approver_email]

            # Envoyer notification au niveau suivant
            email_result = await self._send_level_notification(
                workflow_id=workflow_id,
                workflow_data=workflow,
                level=next_level,
                approver_email=next_approver_email,
                user_data=workflow.get("context", {}),
                requester=workflow.get("context", {}).get("requester", "admin")
            )

            # Stocker les tokens du nouveau niveau
            level_decisions[str(next_level)]["tokens"] = {
                "approve_token": email_result.get("approve_token"),
                "reject_token": email_result.get("reject_token"),
                "approver_email": next_approver_email
            }

            workflow["history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": "level_notification_sent",
                "level": next_level,
                "level_name": next_level_info["name"],
                "approver": next_approver_email,
                "email_sent": email_result.get("sent", False)
            })

        workflow["level_decisions"] = level_decisions
        memory_store.save_workflow(workflow_id, workflow)

        logger.info(
            "Level approved, moving to next",
            workflow_id=workflow_id,
            completed_level=current_level,
            next_level=next_level
        )

        return {
            "success": True,
            "workflow_id": workflow_id,
            "action": "approved",
            "status": "pending",
            "workflow_complete": False,
            "current_level": next_level,
            "total_levels": total_levels,
            "message": f"Niveau {current_level} approuve, passage au niveau {next_level}/{total_levels}"
        }

    async def reject_level(
        self,
        workflow_id: str,
        approver_id: str,
        approver_email: str,
        comments: Optional[str] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rejette le workflow au niveau actuel.
        Le workflow entier est rejete.
        """
        workflow = memory_store.get_workflow(workflow_id)
        if not workflow:
            return {"success": False, "error": "Workflow non trouve"}

        if workflow.get("status") != "pending":
            return {"success": False, "error": f"Workflow deja traite (statut: {workflow.get('status')})"}

        current_level = workflow.get("current_level", 1)

        # Verifier le token si fourni
        if token:
            level_decisions = workflow.get("level_decisions", {})
            level_tokens = level_decisions.get(str(current_level), {}).get("tokens", {})
            if level_tokens.get("reject_token") != token:
                return {"success": False, "error": "Token invalide"}

        # Marquer le niveau comme rejete
        level_decisions = workflow.get("level_decisions", {})
        if str(current_level) in level_decisions:
            level_decisions[str(current_level)]["status"] = "rejected"
            level_decisions[str(current_level)]["decided_by"] = approver_email
            level_decisions[str(current_level)]["decided_at"] = datetime.utcnow().isoformat()
            level_decisions[str(current_level)]["comments"] = comments

        # Obtenir le nom du niveau
        levels = workflow.get("levels", [])
        level_name = "Niveau " + str(current_level)
        for l in levels:
            if l["level"] == current_level:
                level_name = l["name"]
                break

        # Marquer le workflow comme rejete
        workflow["status"] = "rejected"
        workflow["completed_at"] = datetime.utcnow().isoformat()
        workflow["rejected_at_level"] = current_level
        workflow["rejected_by"] = approver_email
        workflow["rejection_comments"] = comments

        workflow["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "level_rejected",
            "level": current_level,
            "level_name": level_name,
            "approver": approver_email,
            "comments": comments
        })

        workflow["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "workflow_rejected",
            "details": f"Rejete au niveau {current_level} ({level_name}) par {approver_email}"
        })

        workflow["level_decisions"] = level_decisions
        memory_store.save_workflow(workflow_id, workflow)

        # Notifier le demandeur
        context = workflow.get("context", {})
        requester_email = context.get("email")
        if requester_email:
            await email_service.send_workflow_complete_notification(
                user_email=requester_email,
                user_data=context,
                approved=False,
                workflow_id=workflow_id,
                rejection_reason=comments,
                rejected_by=approver_email,
                rejected_at_level=level_name
            )

        logger.info(
            "Workflow rejected",
            workflow_id=workflow_id,
            rejected_at_level=current_level,
            rejected_by=approver_email
        )

        return {
            "success": True,
            "workflow_id": workflow_id,
            "action": "rejected",
            "status": "rejected",
            "workflow_complete": True,
            "rejected_at_level": current_level,
            "message": f"Workflow rejete au niveau {current_level} ({level_name})"
        }

    async def approve_by_token(
        self,
        workflow_id: str,
        token: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Approuve ou rejette un workflow via un token email.
        """
        workflow = memory_store.get_workflow(workflow_id)
        if not workflow:
            return {"success": False, "error": "Workflow non trouve"}

        if workflow.get("status") != "pending":
            return {"success": False, "error": f"Workflow deja traite (statut: {workflow.get('status')})"}

        current_level = workflow.get("current_level", 1)
        level_decisions = workflow.get("level_decisions", {})
        level_tokens = level_decisions.get(str(current_level), {}).get("tokens", {})

        approver_email = level_tokens.get("approver_email", "email_link")

        if action == "approve":
            if level_tokens.get("approve_token") == token:
                return await self.approve_level(
                    workflow_id=workflow_id,
                    approver_id="email_link",
                    approver_email=approver_email,
                    comments="Approuve via lien email",
                    token=token
                )
            else:
                return {"success": False, "error": "Token d'approbation invalide"}

        elif action == "reject":
            if level_tokens.get("reject_token") == token:
                return await self.reject_level(
                    workflow_id=workflow_id,
                    approver_id="email_link",
                    approver_email=approver_email,
                    comments="Rejete via lien email",
                    token=token
                )
            else:
                return {"success": False, "error": "Token de rejet invalide"}

        return {"success": False, "error": "Action invalide"}

    # Methodes de compatibilite avec l'ancien code
    async def create_approval_workflow(
        self,
        operation_id: str,
        user_data: Dict[str, Any],
        manager_email: str,
        requester: str
    ) -> Dict[str, Any]:
        """
        Cree un workflow d'approbation (methode de compatibilite).
        Utilise maintenant le workflow multi-niveaux.
        """
        return await self.create_multi_level_approval_workflow(
            operation_id=operation_id,
            user_data=user_data,
            manager_email=manager_email,
            requester=requester,
            workflow_type="full"
        )

    async def start_pre_workflow(
        self,
        operation_id: str,
        context: Dict[str, Any]
    ) -> WorkflowInstance:
        """Demarre un workflow pre-provisionnement."""
        manager_email = context.get("manager_email", "admin@gateway.local")
        requester = context.get("requester", "admin")

        result = await self.create_multi_level_approval_workflow(
            operation_id=operation_id,
            user_data=context,
            manager_email=manager_email,
            requester=requester,
            workflow_type="full"
        )

        workflow = memory_store.get_workflow(result["workflow_id"])
        timeout = datetime.utcnow() + timedelta(hours=120)

        return WorkflowInstance(
            id=result["workflow_id"],
            workflow_id="wf-multi-level-approval",
            operation_id=operation_id,
            status=ApprovalStatus.PENDING,
            current_level=1,
            total_levels=result.get("total_levels", 3),
            context_data=json.dumps(context),
            expires_at=timeout
        )

    async def start_post_workflow(
        self,
        operation_id: str,
        context: Dict[str, Any]
    ) -> WorkflowInstance:
        """Demarre un workflow post-provisionnement."""
        return await self.start_pre_workflow(operation_id, context)

    async def get_instance(self, instance_id: str) -> Optional[WorkflowInstanceResponse]:
        """Recupere les details d'une instance."""
        wf = memory_store.get_workflow(instance_id)
        if not wf:
            return None

        return WorkflowInstanceResponse(
            id=wf.get("id", instance_id),
            workflow_id=wf.get("workflow_id", "wf-multi-level-approval"),
            operation_id=wf.get("operation_id", ""),
            status=ApprovalStatus(wf.get("status", "pending")),
            current_level=wf.get("current_level", 1),
            total_levels=wf.get("total_levels", 3),
            pending_approvers=wf.get("pending_approvers", []),
            history=wf.get("history", []),
            created_at=wf.get("created_at"),
            user_name=wf.get("user_name", ""),
            operation_name=wf.get("operation_name", "")
        )

    async def list_instances(
        self,
        status: Optional[ApprovalStatus] = None,
        approver_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkflowInstanceResponse]:
        """Liste les instances de workflow."""
        status_str = status.value if status else None
        workflows = memory_store.list_workflows(status=status_str, limit=limit, offset=offset)

        result = []
        for wf in workflows:
            result.append(WorkflowInstanceResponse(
                id=wf.get("id", ""),
                workflow_id=wf.get("workflow_id", "wf-multi-level-approval"),
                operation_id=wf.get("operation_id", ""),
                status=ApprovalStatus(wf.get("status", "pending")),
                current_level=wf.get("current_level", 1),
                total_levels=wf.get("total_levels", 3),
                pending_approvers=wf.get("pending_approvers", []),
                history=wf.get("history", []),
                created_at=wf.get("created_at"),
                user_name=wf.get("user_name", ""),
                operation_name=wf.get("operation_name", "")
            ))
        return result

    async def get_pending_approvals(self, user_id: str, user_role: str = None) -> List[Dict[str, Any]]:
        """
        Recupere les approbations en attente pour un utilisateur.

        Filtre par role:
        - manager: voit les demandes niveau 1
        - rh_manager: voit les demandes niveau 2
        - it_admin/admin: voit les demandes niveau 3
        """
        workflows = memory_store.list_workflows(status="pending")
        result = []

        for wf in workflows:
            current_level = wf.get("current_level", 1)
            pending_approvers = wf.get("pending_approvers", [])

            # Verifier si l'utilisateur peut approuver ce niveau
            can_approve = False

            # Verifier par email
            if user_id in pending_approvers:
                can_approve = True

            # Verifier par role
            if user_role:
                levels = wf.get("levels", [])
                for level in levels:
                    if level["level"] == current_level:
                        required_role = level.get("role_required", "")
                        if user_role == required_role or user_role == "admin":
                            can_approve = True
                        break

            # Admin voit tout
            if user_role == "admin" or user_id == "admin":
                can_approve = True

            if can_approve:
                level_name = "Niveau " + str(current_level)
                for l in wf.get("levels", []):
                    if l["level"] == current_level:
                        level_name = l["name"]
                        break

                result.append({
                    "id": wf.get("id"),
                    "operation_id": wf.get("operation_id"),
                    "operation_name": wf.get("operation_name", "Operation"),
                    "user_name": wf.get("user_name", "Unknown"),
                    "current_level": current_level,
                    "current_level_name": level_name,
                    "total_levels": wf.get("total_levels", 3),
                    "pending_approvers": pending_approvers,
                    "created_at": wf.get("created_at"),
                    "context": wf.get("context", {})
                })

        return result

    async def get_workflow_details(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupere les details complets d'un workflow incluant l'historique.
        """
        wf = memory_store.get_workflow(workflow_id)
        if not wf:
            return None

        # Ajouter des infos formatees pour l'affichage
        levels_status = []
        for level in wf.get("levels", []):
            level_num = level["level"]
            decision = wf.get("level_decisions", {}).get(str(level_num), {})
            levels_status.append({
                "level": level_num,
                "name": level["name"],
                "description": level.get("description", ""),
                "status": decision.get("status", "waiting"),
                "decided_by": decision.get("decided_by"),
                "decided_at": decision.get("decided_at"),
                "comments": decision.get("comments"),
                "approver_type": level.get("approver_type"),
                "role_required": level.get("role_required")
            })

        return {
            **wf,
            "levels_status": levels_status
        }

    async def can_approve(self, instance_id: str, user_id: str) -> bool:
        """Verifie si un utilisateur peut approuver."""
        wf = memory_store.get_workflow(instance_id)
        if not wf:
            return False

        if wf.get("status") != "pending":
            return False

        pending_approvers = wf.get("pending_approvers", [])
        return user_id in pending_approvers or user_id == "admin"

    async def record_decision(
        self,
        instance_id: str,
        approver_id: str,
        decision: ApprovalStatus,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enregistre une decision d'approbation."""
        if decision == ApprovalStatus.APPROVED:
            return await self.approve_level(
                workflow_id=instance_id,
                approver_id=approver_id,
                approver_email=approver_id,
                comments=comments
            )
        elif decision == ApprovalStatus.REJECTED:
            return await self.reject_level(
                workflow_id=instance_id,
                approver_id=approver_id,
                approver_email=approver_id,
                comments=comments
            )

        return {"success": False, "error": "Decision invalide"}

    async def cancel_instance(self, instance_id: str) -> Dict[str, Any]:
        """Annule une instance de workflow."""
        wf = memory_store.get_workflow(instance_id)
        if wf:
            wf["status"] = "cancelled"
            wf["history"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": "workflow_cancelled",
                "details": "Workflow annule manuellement"
            })
            memory_store.save_workflow(instance_id, wf)

        logger.info("Workflow cancelled", instance_id=instance_id)
        return {"cancelled": True}

    async def get_history(self, instance_id: str) -> List[Dict[str, Any]]:
        """Recupere l'historique des decisions."""
        wf = memory_store.get_workflow(instance_id)
        if wf:
            return wf.get("history", [])
        return []

    async def _execute_odoo_sync(self, workflow_id: str, context: Dict[str, Any]) -> None:
        """
        Execute la creation du compte MidPoint apres approbation complete.
        Appele automatiquement quand un workflow Odoo est entierement approuve.
        """
        try:
            from app.services.midpoint_client import MidPointClient

            client = MidPointClient()

            user_data = {
                "username": context.get("account_id"),
                "firstname": context.get("firstname"),
                "lastname": context.get("lastname"),
                "email": context.get("email"),
                "department": context.get("department"),
                "title": context.get("job_title"),
            }

            midpoint_result = await client.create_account(user_data)

            # Update workflow with execution result
            workflow = memory_store.get_workflow(workflow_id)
            if workflow:
                workflow["executed"] = True
                workflow["executed_at"] = datetime.utcnow().isoformat()
                workflow["midpoint_oid"] = midpoint_result.get("oid") if midpoint_result else None
                workflow["history"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "account_created",
                    "details": f"Compte cree automatiquement dans MidPoint: {context.get('account_id')}"
                })
                memory_store.save_workflow(workflow_id, workflow)

            logger.info(
                "Odoo sync executed after approval",
                workflow_id=workflow_id,
                username=context.get("account_id"),
                midpoint_oid=midpoint_result.get("oid") if midpoint_result else None
            )

        except Exception as e:
            logger.error(
                "Failed to execute Odoo sync after approval",
                workflow_id=workflow_id,
                error=str(e)
            )
            # Update workflow with error
            workflow = memory_store.get_workflow(workflow_id)
            if workflow:
                workflow["executed"] = False
                workflow["execution_error"] = str(e)
                workflow["history"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "account_creation_failed",
                    "details": f"Erreur lors de la creation: {str(e)[:100]}"
                })
                memory_store.save_workflow(workflow_id, workflow)

    async def check_expired_workflows(self) -> None:
        """Verifie et traite les workflows expires."""
        workflows = memory_store.list_workflows(status="pending")
        now = datetime.utcnow()

        for wf in workflows:
            expires_at = wf.get("expires_at")
            if expires_at:
                expire_time = datetime.fromisoformat(expires_at.replace("Z", "+00:00").replace("+00:00", ""))
                if now > expire_time:
                    # Verifier si auto-approve est active pour le niveau actuel
                    current_level = wf.get("current_level", 1)
                    levels = wf.get("levels", [])

                    for level in levels:
                        if level["level"] == current_level:
                            if level.get("auto_approve_on_timeout", False):
                                # Auto-approuver
                                await self.approve_level(
                                    workflow_id=wf["id"],
                                    approver_id="system_timeout",
                                    approver_email="system@gateway.local",
                                    comments="Auto-approuve apres timeout"
                                )
                            else:
                                # Marquer comme expire
                                wf["status"] = "expired"
                                wf["history"].append({
                                    "timestamp": now.isoformat(),
                                    "action": "workflow_expired",
                                    "level": current_level,
                                    "details": "Workflow expire sans approbation"
                                })
                                memory_store.save_workflow(wf["id"], wf)
                            break
