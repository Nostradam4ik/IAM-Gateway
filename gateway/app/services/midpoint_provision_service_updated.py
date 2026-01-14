"""
Service de Provisioning via MidPoint
Toutes les opérations passent par MidPoint comme hub central IAM
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import structlog
import httpx

from app.models.provision import (
    ProvisioningRequest,
    ProvisioningOperation,
    OperationStatus
)
from app.core.config import settings

logger = structlog.get_logger()


class MidPointProvisionService:
    """
    Service de provisioning qui passe TOUT par MidPoint.

    Architecture:
    Odoo → Gateway IAM → MidPoint → LDAP/PostgreSQL

    Au lieu de:
    Odoo → Gateway IAM → LDAP/PostgreSQL (direct)
    """

    def __init__(self):
        self.midpoint_url = settings.MIDPOINT_URL
        self.midpoint_user = settings.MIDPOINT_USER
        self.midpoint_password = settings.MIDPOINT_PASSWORD

    async def create_user_in_midpoint(
        self,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crée un utilisateur dans MidPoint.
        MidPoint se charge ensuite de provisionner vers LDAP et PostgreSQL
        via ses connecteurs configurés.

        Args:
            user_data: Données utilisateur (nom, email, département, etc.)

        Returns:
            Résultat de la création avec OID MidPoint
        """
        logger.info("Creating user in MidPoint", user_data=user_data)

        # Construire l'objet UserType pour MidPoint
        midpoint_user = self._build_midpoint_user(user_data)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.midpoint_url}/ws/rest/users",
                    auth=(self.midpoint_user, self.midpoint_password),
                    json=midpoint_user,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )

                if response.status_code == 201:
                    # MidPoint a créé l'utilisateur
                    # Les connecteurs MidPoint provisionnent automatiquement vers LDAP et PostgreSQL
                    oid = response.headers.get("Location", "").split("/")[-1]

                    logger.info(
                        "User created in MidPoint successfully",
                        oid=oid,
                        username=user_data.get("username")
                    )

                    return {
                        "success": True,
                        "oid": oid,
                        "status": "created_in_midpoint",
                        "message": "User created in MidPoint. Automatic provisioning to LDAP and PostgreSQL triggered."
                    }
                else:
                    logger.error(
                        "Failed to create user in MidPoint",
                        status_code=response.status_code,
                        response=response.text
                    )
                    return {
                        "success": False,
                        "error": f"MidPoint returned {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error("Error creating user in MidPoint", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def update_user_in_midpoint(
        self,
        oid: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Met à jour un utilisateur dans MidPoint.
        MidPoint propage les modifications vers LDAP et PostgreSQL.
        """
        logger.info("Updating user in MidPoint", oid=oid, updates=updates)

        # Construire le patch MidPoint
        modifications = self._build_midpoint_modifications(updates)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.midpoint_url}/ws/rest/users/{oid}",
                    auth=(self.midpoint_user, self.midpoint_password),
                    json={"objectModification": modifications},
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )

                if response.status_code == 204:
                    logger.info("User updated in MidPoint successfully", oid=oid)
                    return {
                        "success": True,
                        "oid": oid,
                        "status": "updated_in_midpoint",
                        "message": "User updated in MidPoint. Changes propagated to LDAP and PostgreSQL."
                    }
                else:
                    logger.error(
                        "Failed to update user in MidPoint",
                        status_code=response.status_code,
                        response=response.text
                    )
                    return {
                        "success": False,
                        "error": f"MidPoint returned {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error("Error updating user in MidPoint", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_user_in_midpoint(
        self,
        oid: str
    ) -> Dict[str, Any]:
        """
        Supprime (ou désactive) un utilisateur dans MidPoint.
        MidPoint supprime/désactive dans LDAP et PostgreSQL.
        """
        logger.info("Deleting user in MidPoint", oid=oid)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.midpoint_url}/ws/rest/users/{oid}",
                    auth=(self.midpoint_user, self.midpoint_password),
                    timeout=30.0
                )

                if response.status_code == 204:
                    logger.info("User deleted in MidPoint successfully", oid=oid)
                    return {
                        "success": True,
                        "oid": oid,
                        "status": "deleted_in_midpoint",
                        "message": "User deleted in MidPoint. Removed from LDAP and PostgreSQL."
                    }
                else:
                    logger.error(
                        "Failed to delete user in MidPoint",
                        status_code=response.status_code,
                        response=response.text
                    )
                    return {
                        "success": False,
                        "error": f"MidPoint returned {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error("Error deleting user in MidPoint", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def assign_role_in_midpoint(
        self,
        oid: str,
        role_oid: str
    ) -> Dict[str, Any]:
        """
        Assigne un rôle à un utilisateur dans MidPoint.
        Le rôle déclenche automatiquement le provisioning vers les systèmes cibles.

        Exemple: Rôle "LDAP User" → provisionne vers LDAP
                 Rôle "Database User" → provisionne vers PostgreSQL
        """
        logger.info("Assigning role in MidPoint", user_oid=oid, role_oid=role_oid)

        assignment = {
            "assignment": {
                "targetRef": {
                    "oid": role_oid,
                    "type": "RoleType"
                }
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.midpoint_url}/ws/rest/users/{oid}/assignments",
                    auth=(self.midpoint_user, self.midpoint_password),
                    json=assignment,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )

                if response.status_code in [200, 201, 204]:
                    logger.info("Role assigned in MidPoint successfully", user_oid=oid, role_oid=role_oid)
                    return {
                        "success": True,
                        "user_oid": oid,
                        "role_oid": role_oid,
                        "status": "role_assigned",
                        "message": "Role assigned. Provisioning triggered by MidPoint."
                    }
                else:
                    logger.error(
                        "Failed to assign role in MidPoint",
                        status_code=response.status_code,
                        response=response.text
                    )
                    return {
                        "success": False,
                        "error": f"MidPoint returned {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error("Error assigning role in MidPoint", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_provisioning_via_midpoint(
        self,
        operation: ProvisioningOperation,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Point d'entrée principal: exécute le provisioning VIA MidPoint.

        Flow:
        1. Gateway reçoit la demande
        2. Gateway crée/update l'utilisateur dans MidPoint
        3. MidPoint provisionne automatiquement vers LDAP et PostgreSQL
        4. Gateway retourne le résultat

        Args:
            operation: Opération de provisioning
            user_data: Données utilisateur

        Returns:
            Résultat global avec statuts MidPoint, LDAP, PostgreSQL
        """
        logger.info(
            "Starting provisioning via MidPoint",
            operation_id=operation.id,
            operation_type=operation.operation_type
        )

        result = {
            "operation_id": operation.id,
            "status": "in_progress",
            "midpoint": {},
            "targets": {}
        }

        try:
            # Étape 1: Créer/Updater dans MidPoint
            if operation.operation_type == "CREATE":
                midpoint_result = await self.create_user_in_midpoint(user_data)
            elif operation.operation_type == "UPDATE":
                oid = user_data.get("oid")
                if not oid:
                    # Rechercher l'OID par username
                    oid = await self._find_user_oid(user_data.get("username"))
                midpoint_result = await self.update_user_in_midpoint(oid, user_data)
            elif operation.operation_type == "DELETE":
                oid = user_data.get("oid") or await self._find_user_oid(user_data.get("username"))
                midpoint_result = await self.delete_user_in_midpoint(oid)
            else:
                raise ValueError(f"Unknown operation type: {operation.operation_type}")

            result["midpoint"] = midpoint_result

            # Étape 2: MidPoint provisionne automatiquement vers les cibles
            # On attend un peu pour que le provisioning se fasse
            import asyncio
            await asyncio.sleep(2)

            # Étape 3: Vérifier les statuts sur les systèmes cibles
            if midpoint_result.get("success"):
                oid = midpoint_result.get("oid")
                target_status = await self._check_provisioning_status(oid)
                result["targets"] = target_status
                result["status"] = "completed"
                operation.status = OperationStatus.COMPLETED
            else:
                result["status"] = "failed"
                operation.status = OperationStatus.FAILED

            operation.result_data = json.dumps(result)
            operation.updated_at = datetime.utcnow()

            logger.info(
                "Provisioning via MidPoint completed",
                operation_id=operation.id,
                status=result["status"]
            )

            return result

        except Exception as e:
            logger.error(
                "Error during provisioning via MidPoint",
                operation_id=operation.id,
                error=str(e)
            )
            result["status"] = "error"
            result["error"] = str(e)
            operation.status = OperationStatus.FAILED
            operation.result_data = json.dumps(result)
            return result

    def _build_midpoint_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Construit un objet UserType MidPoint à partir des données utilisateur."""
        return {
            "user": {
                "name": user_data.get("username"),
                "fullName": f"{user_data.get('firstname', '')} {user_data.get('lastname', '')}",
                "givenName": user_data.get("firstname"),
                "familyName": user_data.get("lastname"),
                "emailAddress": user_data.get("email"),
                "employeeNumber": user_data.get("employee_id"),
                "organizationalUnit": user_data.get("department"),
                "telephoneNumber": user_data.get("phone"),
                "activation": {
                    "administrativeStatus": "enabled"
                }
            }
        }

    def _build_midpoint_modifications(self, updates: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Construit les modifications MidPoint."""
        modifications = []

        mapping = {
            "email": "emailAddress",
            "firstname": "givenName",
            "lastname": "familyName",
            "department": "organizationalUnit",
            "phone": "telephoneNumber"
        }

        for key, value in updates.items():
            midpoint_key = mapping.get(key, key)
            modifications.append({
                "modificationType": "replace",
                "path": midpoint_key,
                "value": value
            })

        return modifications

    async def _find_user_oid(self, username: str) -> Optional[str]:
        """Recherche l'OID d'un utilisateur par son username."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.midpoint_url}/ws/rest/users",
                    auth=(self.midpoint_user, self.midpoint_password),
                    params={"query": f"name = '{username}'"},
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    users = data.get("object", [])
                    if users:
                        return users[0].get("oid")
        except Exception as e:
            logger.error("Error finding user OID", username=username, error=str(e))

        return None

    async def _check_provisioning_status(self, oid: str) -> Dict[str, Any]:
        """Vérifie le statut du provisioning sur les systèmes cibles."""
        # Interroger MidPoint pour voir les comptes liés (shadow objects)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.midpoint_url}/ws/rest/users/{oid}/linkedObjects",
                    auth=(self.midpoint_user, self.midpoint_password),
                    timeout=30.0
                )

                if response.status_code == 200:
                    shadows = response.json().get("shadow", [])

                    status = {}
                    for shadow in shadows:
                        resource_name = shadow.get("resourceRef", {}).get("name", "unknown")
                        shadow_status = shadow.get("activation", {}).get("administrativeStatus", "unknown")
                        status[resource_name] = {
                            "status": shadow_status,
                            "oid": shadow.get("oid")
                        }

                    return status
        except Exception as e:
            logger.error("Error checking provisioning status", oid=oid, error=str(e))

        return {}
