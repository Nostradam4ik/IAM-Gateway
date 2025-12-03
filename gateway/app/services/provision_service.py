"""
Service de provisionnement multi-cibles
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import structlog

from app.models.provision import (
    ProvisioningRequest,
    ProvisioningOperation,
    OperationType,
    OperationStatus,
    TargetSystem,
    RollbackAction,
    TargetAccountState
)
from app.connectors.connector_factory import ConnectorFactory

logger = structlog.get_logger()


class ProvisionService:
    """
    Service principal de provisionnement.

    Orchestre les operations sur les systemes cibles avec:
    - Transactions atomiques
    - Rollback en cas d'erreur
    - Cache d'etat des comptes
    """

    def __init__(self, session):
        self.session = session
        self.connector_factory = ConnectorFactory()

    async def create_operation(
        self,
        request: ProvisioningRequest,
        created_by: str
    ) -> ProvisioningOperation:
        """Cree un enregistrement d'operation."""
        operation = ProvisioningOperation(
            correlation_id=request.correlation_id,
            operation_type=request.operation,
            account_id=request.account_id,
            status=OperationStatus.PENDING,
            target_systems=json.dumps([t.value for t in request.target_systems]),
            input_attributes=json.dumps(request.attributes),
            policy_id=request.policy_id,
            created_by=created_by
        )

        # Save to DB
        # self.session.add(operation)
        # await self.session.commit()

        logger.info(
            "Operation created",
            operation_id=operation.id,
            account_id=request.account_id,
            operation_type=request.operation
        )

        return operation

    async def execute_provisioning(
        self,
        operation: ProvisioningOperation,
        calculated_attributes: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute le provisionnement sur tous les systemes cibles.

        Args:
            operation: Operation de provisionnement
            calculated_attributes: Attributs calcules par systeme

        Returns:
            Resultat de l'execution
        """
        operation.status = OperationStatus.IN_PROGRESS
        operation.calculated_attributes = json.dumps(calculated_attributes)
        operation.updated_at = datetime.utcnow()

        target_systems = json.loads(operation.target_systems)
        results = {}
        rollback_actions = []

        try:
            for target in target_systems:
                logger.info(
                    "Provisioning to target",
                    operation_id=operation.id,
                    target=target
                )

                connector = self.connector_factory.get_connector(target)
                attrs = calculated_attributes.get(target, {})

                # Execute operation based on type
                if operation.operation_type == OperationType.CREATE:
                    result = await connector.create_account(
                        account_id=operation.account_id,
                        attributes=attrs
                    )
                    # Store rollback action
                    rollback_actions.append(RollbackAction(
                        operation_id=operation.id,
                        target_system=TargetSystem(target),
                        action_type="delete",
                        action_data=json.dumps({"account_id": operation.account_id})
                    ))

                elif operation.operation_type == OperationType.UPDATE:
                    result = await connector.update_account(
                        account_id=operation.account_id,
                        attributes=attrs
                    )

                elif operation.operation_type == OperationType.DELETE:
                    result = await connector.delete_account(
                        account_id=operation.account_id
                    )

                elif operation.operation_type == OperationType.DISABLE:
                    result = await connector.disable_account(
                        account_id=operation.account_id
                    )

                elif operation.operation_type == OperationType.ENABLE:
                    result = await connector.enable_account(
                        account_id=operation.account_id
                    )

                results[target] = result

                # Update account state cache
                await self._update_account_state(
                    account_id=operation.account_id,
                    target_system=target,
                    attributes=attrs,
                    is_active=operation.operation_type not in [
                        OperationType.DELETE, OperationType.DISABLE
                    ]
                )

            # All successful
            operation.status = OperationStatus.SUCCESS
            operation.completed_at = datetime.utcnow()

            logger.info(
                "Provisioning completed successfully",
                operation_id=operation.id,
                targets=target_systems
            )

            return {"success": True, "results": results}

        except Exception as e:
            logger.error(
                "Provisioning failed",
                operation_id=operation.id,
                error=str(e)
            )

            operation.status = OperationStatus.FAILED
            operation.error_message = str(e)

            # Execute rollback for completed targets
            await self._execute_rollback(rollback_actions)

            raise

    async def rollback_operation(self, operation_id: str) -> Dict[str, Any]:
        """Execute le rollback d'une operation."""
        operation = await self.get_operation(operation_id)
        if not operation:
            raise ValueError(f"Operation {operation_id} not found")

        logger.info("Starting rollback", operation_id=operation_id)

        # Get rollback actions
        # actions = await self._get_rollback_actions(operation_id)
        # await self._execute_rollback(actions)

        operation.status = OperationStatus.ROLLED_BACK
        operation.updated_at = datetime.utcnow()

        return {"rolled_back": True, "operation_id": operation_id}

    async def _execute_rollback(self, actions: List[RollbackAction]) -> None:
        """Execute les actions de rollback."""
        for action in reversed(actions):  # Reverse order
            if action.executed:
                continue

            try:
                connector = self.connector_factory.get_connector(action.target_system.value)
                action_data = json.loads(action.action_data)

                if action.action_type == "delete":
                    await connector.delete_account(action_data["account_id"])
                elif action.action_type == "restore":
                    await connector.create_account(
                        action_data["account_id"],
                        action_data.get("attributes", {})
                    )

                action.executed = True
                action.executed_at = datetime.utcnow()

                logger.info(
                    "Rollback action executed",
                    target=action.target_system,
                    action_type=action.action_type
                )

            except Exception as e:
                logger.error(
                    "Rollback action failed",
                    target=action.target_system,
                    error=str(e)
                )

    async def _update_account_state(
        self,
        account_id: str,
        target_system: str,
        attributes: Dict[str, Any],
        is_active: bool
    ) -> None:
        """Met a jour le cache d'etat du compte."""
        state = TargetAccountState(
            account_id=account_id,
            target_system=TargetSystem(target_system),
            target_account_id=attributes.get("uid", attributes.get("username", account_id)),
            attributes=json.dumps(attributes),
            is_active=is_active,
            last_sync_at=datetime.utcnow()
        )

        # Upsert in DB
        # ...

    async def get_operation(self, operation_id: str) -> Optional[ProvisioningOperation]:
        """Recupere une operation par ID."""
        # DB query
        return None

    async def list_operations(
        self,
        account_id: Optional[str] = None,
        status: Optional[OperationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProvisioningOperation]:
        """Liste les operations avec filtres."""
        # DB query
        return []

    async def continue_after_approval(self, operation_id: str) -> ProvisioningOperation:
        """Continue le provisionnement apres approbation."""
        operation = await self.get_operation(operation_id)
        if not operation:
            raise ValueError(f"Operation {operation_id} not found")

        calculated_attrs = json.loads(operation.calculated_attributes)
        await self.execute_provisioning(operation, calculated_attrs)

        return operation

    async def cancel_operation(self, operation_id: str, reason: str) -> None:
        """Annule une operation en attente."""
        operation = await self.get_operation(operation_id)
        if operation:
            operation.status = OperationStatus.REJECTED
            operation.error_message = reason
            operation.updated_at = datetime.utcnow()
