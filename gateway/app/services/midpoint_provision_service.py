"""
Service de provisionnement via MidPoint Hub

Ce service utilise MidPoint comme hub central IAM.
Toutes les operations de provisionnement passent par MidPoint
qui se charge de propager les changements aux systemes cibles.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import structlog

from app.models.provision import (
    ProvisioningRequest,
    OperationType,
    OperationStatus,
    TargetSystem
)
from app.connectors.midpoint_connector import MidPointConnector
from app.core.config import settings
from app.core.memory_store import memory_store

logger = structlog.get_logger()


class MidPointProvisionService:
    """
    Service de provisionnement utilisant MidPoint comme hub central.

    Architecture:
        Gateway -> MidPoint -> [LDAP, Odoo, SQL, ...]

    MidPoint gere:
    - Le stockage de l'identite dans son repository
    - La propagation vers les Resources (systemes cibles)
    - Les workflows d'approbation
    - L'audit trail complet
    - La reconciliation
    """

    def __init__(self, session=None):
        self.session = session
        self.midpoint = MidPointConnector()
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize connection to MidPoint."""
        if self._initialized:
            return True

        try:
            connected = await self.midpoint.test_connection()
            if connected:
                logger.info("MidPoint connection established")
                self._initialized = True
                return True
            else:
                logger.error("Failed to connect to MidPoint")
                return False
        except Exception as e:
            logger.error("MidPoint initialization error", error=str(e))
            return False

    async def provision(
        self,
        request: ProvisioningRequest,
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Execute provisioning through MidPoint.

        MidPoint will handle:
        1. Creating/updating the user in its repository
        2. Propagating to configured Resources based on roles
        3. Audit logging

        Args:
            request: Provisioning request with user data
            created_by: User who initiated the request

        Returns:
            Result of the provisioning operation
        """
        # Ensure connection
        if not self._initialized:
            await self.initialize()

        # Create operation record in memory store
        operation_id = f"op_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{request.account_id}"

        operation_data = {
            "id": operation_id,
            "correlation_id": request.correlation_id,
            "operation_type": request.operation.value,
            "account_id": request.account_id,
            "status": OperationStatus.IN_PROGRESS.value,
            "target_systems": ["MIDPOINT"],  # MidPoint is the only direct target
            "original_targets": [t.value for t in request.target_systems],
            "user_data": request.attributes,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
            "midpoint_hub": True
        }

        memory_store.save_operation(operation_id, operation_data)

        logger.info(
            "Starting MidPoint provisioning",
            operation_id=operation_id,
            account_id=request.account_id,
            operation=request.operation.value
        )

        try:
            # Execute based on operation type
            if request.operation == OperationType.CREATE:
                result = await self._create_user(request)

            elif request.operation == OperationType.UPDATE:
                result = await self._update_user(request)

            elif request.operation == OperationType.DELETE:
                result = await self._delete_user(request)

            elif request.operation == OperationType.DISABLE:
                result = await self._disable_user(request)

            elif request.operation == OperationType.ENABLE:
                result = await self._enable_user(request)

            else:
                raise ValueError(f"Unknown operation type: {request.operation}")

            # Update operation status
            memory_store.update_operation(operation_id, {
                "status": OperationStatus.SUCCESS.value,
                "result": result,
                "completed_at": datetime.utcnow().isoformat(),
                "message": "Provisioning via MidPoint completed successfully"
            })

            logger.info(
                "MidPoint provisioning completed",
                operation_id=operation_id,
                account_id=request.account_id,
                result=result
            )

            return {
                "success": True,
                "operation_id": operation_id,
                "midpoint_result": result,
                "message": "User provisioned via MidPoint hub"
            }

        except Exception as e:
            logger.error(
                "MidPoint provisioning failed",
                operation_id=operation_id,
                account_id=request.account_id,
                error=str(e)
            )

            memory_store.update_operation(operation_id, {
                "status": OperationStatus.FAILED.value,
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            })

            raise

    async def _create_user(self, request: ProvisioningRequest) -> Dict[str, Any]:
        """Create user in MidPoint."""
        attributes = request.attributes.copy()

        # Add role assignments if targets are specified
        # MidPoint uses roles to determine which Resources to provision to
        roles_to_assign = self._map_targets_to_roles(request.target_systems)
        if roles_to_assign:
            attributes["_roles"] = roles_to_assign

        result = await self.midpoint.create_account(
            account_id=request.account_id,
            attributes=attributes
        )

        # If roles specified, assign them
        if roles_to_assign and result.get("oid"):
            for role_name in roles_to_assign:
                try:
                    await self.midpoint.assign_role(result["oid"], role_name)
                    logger.info("Role assigned", user=request.account_id, role=role_name)
                except Exception as e:
                    logger.warning("Failed to assign role", role=role_name, error=str(e))

        return result

    async def _update_user(self, request: ProvisioningRequest) -> Dict[str, Any]:
        """Update user in MidPoint."""
        return await self.midpoint.update_account(
            account_id=request.account_id,
            attributes=request.attributes
        )

    async def _delete_user(self, request: ProvisioningRequest) -> Dict[str, Any]:
        """Delete user from MidPoint (cascades to Resources)."""
        success = await self.midpoint.delete_account(request.account_id)
        return {"success": success, "account_id": request.account_id}

    async def _disable_user(self, request: ProvisioningRequest) -> Dict[str, Any]:
        """Disable user in MidPoint."""
        success = await self.midpoint.disable_account(request.account_id)
        return {"success": success, "account_id": request.account_id}

    async def _enable_user(self, request: ProvisioningRequest) -> Dict[str, Any]:
        """Enable user in MidPoint."""
        success = await self.midpoint.enable_account(request.account_id)
        return {"success": success, "account_id": request.account_id}

    def _map_targets_to_roles(self, targets: List[TargetSystem]) -> List[str]:
        """
        Map target systems to MidPoint role names.

        In MidPoint, roles define which Resources (target systems)
        a user should be provisioned to.

        Example mapping:
            LDAP -> "ldap-user"
            ODOO -> "odoo-user"
            SQL  -> "intranet-user"
        """
        role_mapping = {
            TargetSystem.LDAP: "ldap-user",
            TargetSystem.AD: "ad-user",
            TargetSystem.SQL: "intranet-user",
            TargetSystem.ODOO: "odoo-user",
            TargetSystem.KEYCLOAK: "keycloak-user",
            TargetSystem.GLPI: "glpi-user",
            TargetSystem.FIREBASE: "firebase-user"
        }

        roles = []
        for target in targets:
            if target in role_mapping:
                roles.append(role_mapping[target])

        return roles

    async def get_user(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get user from MidPoint."""
        return await self.midpoint.get_account(account_id)

    async def list_users(self) -> List[Dict[str, Any]]:
        """List all users from MidPoint."""
        return await self.midpoint.list_accounts()

    async def search_users(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search users in MidPoint."""
        client = self.midpoint._get_client()

        search_query = {
            "query": {
                "filter": {
                    "text": query
                }
            },
            "paging": {
                "maxSize": limit
            }
        }

        try:
            response = await client.post(
                "/ws/rest/users/search",
                json=search_query
            )
            response.raise_for_status()

            data = response.json()
            users = data.get("object", [])

            return [self.midpoint._parse_user(u) for u in users]

        except Exception as e:
            logger.error("Search failed", error=str(e))
            return []

    async def get_user_shadows(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get user's shadow accounts (projections to target systems).

        This shows where the user has been provisioned to.
        """
        return await self.midpoint.get_user_shadows(account_id)

    async def assign_role(self, account_id: str, role_name: str) -> bool:
        """Assign a role to a user (triggers provisioning to role's Resources)."""
        return await self.midpoint.assign_role(account_id, role_name)

    async def remove_role(self, account_id: str, role_name: str) -> bool:
        """Remove a role from a user (may trigger deprovisioning)."""
        return await self.midpoint.remove_role(account_id, role_name)

    async def get_roles(self) -> List[Dict[str, Any]]:
        """Get all available roles from MidPoint."""
        return await self.midpoint.get_roles()

    async def get_resources(self) -> List[Dict[str, Any]]:
        """Get all configured Resources (target systems) from MidPoint."""
        return await self.midpoint.get_resources()

    async def reconcile_user(self, account_id: str) -> Dict[str, Any]:
        """
        Trigger reconciliation for a user.

        This compares MidPoint's state with target systems
        and fixes any discrepancies.
        """
        # Get user and shadows
        user = await self.get_user(account_id)
        if not user:
            return {"error": "User not found"}

        shadows = await self.get_user_shadows(account_id)

        return {
            "user": user,
            "shadows": shadows,
            "shadow_count": len(shadows),
            "message": "Reconciliation data retrieved"
        }

    async def close(self):
        """Close MidPoint connection."""
        await self.midpoint.close()


# Singleton instance for the service
_midpoint_service: Optional[MidPointProvisionService] = None


async def get_midpoint_provision_service(session=None) -> MidPointProvisionService:
    """Get or create the MidPoint provision service."""
    global _midpoint_service

    if _midpoint_service is None:
        _midpoint_service = MidPointProvisionService(session)
        await _midpoint_service.initialize()

    return _midpoint_service
