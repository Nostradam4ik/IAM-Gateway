"""
Connecteur MidPoint - Hub central IAM

Ce connecteur permet d'utiliser MidPoint comme systeme central
pour toutes les operations de provisioning. MidPoint gere ensuite
la propagation vers les systemes cibles (LDAP, Odoo, SQL, etc.)
via ses propres connecteurs configures.
"""
from typing import Dict, Any, Optional, List
import httpx
import structlog

from app.connectors.base import BaseConnector
from app.core.config import settings

logger = structlog.get_logger()


class MidPointConnector(BaseConnector):
    """
    Connecteur pour MidPoint comme hub central IAM.

    Toutes les operations passent par MidPoint qui:
    1. Stocke l'identite dans son repository
    2. Propage les changements vers les systemes cibles (Resources)
    3. Gere les workflows d'approbation
    4. Maintient l'audit trail
    """

    def __init__(
        self,
        url: str = None,
        username: str = None,
        password: str = None,
        timeout: float = 60.0
    ):
        super().__init__()
        self.url = url or settings.MIDPOINT_URL
        self.username = username or settings.MIDPOINT_USER
        self.password = password or settings.MIDPOINT_PASSWORD
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authentication."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.url,
                auth=(self.username, self.password),
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def test_connection(self) -> bool:
        """Test connection to MidPoint."""
        try:
            client = self._get_client()
            response = await client.get("/ws/rest/self")
            success = response.status_code == 200

            if success:
                logger.info("MidPoint connection successful", url=self.url)
            else:
                logger.warning(
                    "MidPoint connection failed",
                    status_code=response.status_code,
                    response=response.text[:200]
                )
            return success

        except Exception as e:
            logger.error("MidPoint connection error", error=str(e))
            return False

    async def create_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new user in MidPoint.

        MidPoint will automatically provision to configured Resources
        (LDAP, Odoo, SQL, etc.) based on its mappings and roles.

        Args:
            account_id: Unique identifier (used as 'name' in MidPoint)
            attributes: User attributes

        Returns:
            Dict with created user details including MidPoint OID
        """
        try:
            client = self._get_client()

            # Build MidPoint user object
            user_object = self._build_user_object(account_id, attributes)

            logger.info(
                "Creating user in MidPoint",
                account_id=account_id,
                attributes=list(attributes.keys())
            )

            response = await client.post(
                "/ws/rest/users",
                json=user_object
            )

            if response.status_code in [200, 201]:
                # Extract OID from response or location header
                result = response.json() if response.text else {}
                oid = result.get("oid") or self._extract_oid_from_location(response)

                logger.info(
                    "User created in MidPoint",
                    account_id=account_id,
                    oid=oid
                )

                return {
                    "success": True,
                    "oid": oid,
                    "account_id": account_id,
                    "message": "User created in MidPoint - provisioning to targets initiated"
                }
            else:
                error_msg = response.text[:500]
                logger.error(
                    "Failed to create user in MidPoint",
                    account_id=account_id,
                    status_code=response.status_code,
                    error=error_msg
                )
                raise Exception(f"MidPoint create failed: {response.status_code} - {error_msg}")

        except httpx.HTTPError as e:
            logger.error("HTTP error creating user", account_id=account_id, error=str(e))
            raise

    async def update_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a user in MidPoint.

        Changes will propagate to all linked Resources.

        Args:
            account_id: User OID or name
            attributes: Attributes to update

        Returns:
            Dict with update result
        """
        try:
            client = self._get_client()

            # First, find the user by name if account_id is not an OID
            oid = await self._resolve_oid(account_id)
            if not oid:
                raise Exception(f"User not found: {account_id}")

            # Build modification object for MidPoint
            modifications = self._build_modifications(attributes)

            logger.info(
                "Updating user in MidPoint",
                account_id=account_id,
                oid=oid,
                modifications=len(modifications)
            )

            response = await client.post(
                f"/ws/rest/users/{oid}",
                json={
                    "@ns": "http://midpoint.evolveum.com/xml/ns/public/common/api-types-3",
                    "objectModification": {
                        "itemDelta": modifications
                    }
                },
                params={"options": "raw"}
            )

            if response.status_code in [200, 204]:
                logger.info("User updated in MidPoint", account_id=account_id, oid=oid)
                return {
                    "success": True,
                    "oid": oid,
                    "account_id": account_id,
                    "message": "User updated - changes propagating to targets"
                }
            else:
                error_msg = response.text[:500]
                logger.error(
                    "Failed to update user",
                    account_id=account_id,
                    status_code=response.status_code,
                    error=error_msg
                )
                raise Exception(f"MidPoint update failed: {response.status_code}")

        except httpx.HTTPError as e:
            logger.error("HTTP error updating user", account_id=account_id, error=str(e))
            raise

    async def delete_account(self, account_id: str) -> bool:
        """
        Delete a user from MidPoint.

        This will also deprovision from all linked Resources.

        Args:
            account_id: User OID or name

        Returns:
            True if deletion successful
        """
        try:
            client = self._get_client()

            oid = await self._resolve_oid(account_id)
            if not oid:
                logger.warning("User not found for deletion", account_id=account_id)
                return True  # Already doesn't exist

            logger.info("Deleting user from MidPoint", account_id=account_id, oid=oid)

            response = await client.delete(f"/ws/rest/users/{oid}")

            if response.status_code in [200, 204]:
                logger.info("User deleted from MidPoint", account_id=account_id, oid=oid)
                return True
            else:
                logger.error(
                    "Failed to delete user",
                    account_id=account_id,
                    status_code=response.status_code
                )
                return False

        except Exception as e:
            logger.error("Error deleting user", account_id=account_id, error=str(e))
            return False

    async def disable_account(self, account_id: str) -> bool:
        """
        Disable a user in MidPoint.

        Sets administrativeStatus to 'disabled'.
        MidPoint will propagate this to Resources.

        Args:
            account_id: User OID or name

        Returns:
            True if successful
        """
        try:
            result = await self.update_account(
                account_id,
                {"administrativeStatus": "disabled"}
            )
            return result.get("success", False)
        except Exception as e:
            logger.error("Error disabling user", account_id=account_id, error=str(e))
            return False

    async def enable_account(self, account_id: str) -> bool:
        """
        Enable a user in MidPoint.

        Sets administrativeStatus to 'enabled'.

        Args:
            account_id: User OID or name

        Returns:
            True if successful
        """
        try:
            result = await self.update_account(
                account_id,
                {"administrativeStatus": "enabled"}
            )
            return result.get("success", False)
        except Exception as e:
            logger.error("Error enabling user", account_id=account_id, error=str(e))
            return False

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user details from MidPoint.

        Args:
            account_id: User OID or name

        Returns:
            User details dict or None if not found
        """
        try:
            client = self._get_client()

            oid = await self._resolve_oid(account_id)
            if not oid:
                return None

            response = await client.get(f"/ws/rest/users/{oid}")

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return self._parse_user(response.json())

        except Exception as e:
            logger.error("Error getting user", account_id=account_id, error=str(e))
            return None

    async def list_accounts(self) -> List[Dict[str, Any]]:
        """
        List all users from MidPoint.

        Returns:
            List of user details
        """
        try:
            client = self._get_client()

            response = await client.get(
                "/ws/rest/users",
                params={"options": "raw"}
            )
            response.raise_for_status()

            data = response.json()
            users = data.get("object", [])

            return [self._parse_user(u) for u in users]

        except Exception as e:
            logger.error("Error listing users", error=str(e))
            return []

    async def assign_role(self, account_id: str, role_id: str) -> bool:
        """
        Assign a role to a user.

        Roles in MidPoint drive provisioning - assigning a role
        can trigger account creation in Resources.

        Args:
            account_id: User OID or name
            role_id: Role OID or name

        Returns:
            True if successful
        """
        try:
            client = self._get_client()

            user_oid = await self._resolve_oid(account_id)
            role_oid = await self._resolve_role_oid(role_id)

            if not user_oid or not role_oid:
                raise Exception(f"User or role not found: {account_id}, {role_id}")

            # Create assignment
            assignment = {
                "@ns": "http://midpoint.evolveum.com/xml/ns/public/common/api-types-3",
                "objectModification": {
                    "itemDelta": [{
                        "modificationType": "add",
                        "path": "assignment",
                        "value": [{
                            "targetRef": {
                                "oid": role_oid,
                                "type": "RoleType"
                            }
                        }]
                    }]
                }
            }

            response = await client.patch(
                f"/ws/rest/users/{user_oid}",
                json=assignment
            )

            success = response.status_code in [200, 204]
            if success:
                logger.info("Role assigned", user=account_id, role=role_id)
            else:
                logger.error("Failed to assign role", status=response.status_code, response=response.text[:200])

            return success

        except Exception as e:
            logger.error("Error assigning role", error=str(e))
            return False

    async def remove_role(self, account_id: str, role_id: str) -> bool:
        """
        Remove a role from a user.

        Args:
            account_id: User OID or name
            role_id: Role OID or name

        Returns:
            True if successful
        """
        try:
            client = self._get_client()

            user_oid = await self._resolve_oid(account_id)
            role_oid = await self._resolve_role_oid(role_id)

            if not user_oid or not role_oid:
                return False

            # Remove assignment
            modification = {
                "@ns": "http://midpoint.evolveum.com/xml/ns/public/common/api-types-3",
                "objectModification": {
                    "itemDelta": [{
                        "modificationType": "delete",
                        "path": "assignment",
                        "value": [{
                            "targetRef": {
                                "oid": role_oid,
                                "type": "RoleType"
                            }
                        }]
                    }]
                }
            }

            response = await client.post(
                f"/ws/rest/users/{user_oid}",
                json=modification
            )

            return response.status_code in [200, 204]

        except Exception as e:
            logger.error("Error removing role", error=str(e))
            return False

    async def get_roles(self) -> List[Dict[str, Any]]:
        """Get all roles from MidPoint."""
        try:
            client = self._get_client()
            response = await client.get("/ws/rest/roles")
            response.raise_for_status()

            data = response.json()
            # MidPoint JSON structure: data["object"]["object"] is the list
            obj_wrapper = data.get("object", {})
            if isinstance(obj_wrapper, dict):
                roles = obj_wrapper.get("object", [])
            else:
                roles = obj_wrapper if isinstance(obj_wrapper, list) else []

            if not isinstance(roles, list):
                roles = [roles]

            result = []
            for r in roles:
                if isinstance(r, dict):
                    result.append({
                        "oid": r.get("oid"),
                        "name": r.get("name"),
                        "displayName": r.get("displayName"),
                        "description": r.get("description")
                    })
            return result

        except Exception as e:
            logger.error("Error getting roles", error=str(e))
            return []

    async def get_user_roles(self, account_id: str) -> List[str]:
        """
        Get roles assigned to a user.

        Args:
            account_id: User OID or name

        Returns:
            List of role OIDs
        """
        try:
            user = await self.get_account(account_id)
            if not user:
                return []
            return user.get("roles", [])
        except Exception as e:
            logger.error("Error getting user roles", error=str(e))
            return []

    async def get_resources(self) -> List[Dict[str, Any]]:
        """
        Get all Resources (target systems) configured in MidPoint.

        Returns:
            List of resource details
        """
        try:
            client = self._get_client()
            response = await client.get("/ws/rest/resources")
            response.raise_for_status()

            data = response.json()
            # MidPoint JSON structure: data["object"]["object"] is the list
            obj_wrapper = data.get("object", {})
            if isinstance(obj_wrapper, dict):
                resources = obj_wrapper.get("object", [])
            else:
                resources = obj_wrapper if isinstance(obj_wrapper, list) else []

            if not isinstance(resources, list):
                resources = [resources]

            result = []
            for r in resources:
                if isinstance(r, dict):
                    connector_ref = r.get("connectorRef", {})
                    result.append({
                        "oid": r.get("oid"),
                        "name": r.get("name"),
                        "description": r.get("description"),
                        "connectorType": connector_ref.get("type") if isinstance(connector_ref, dict) else None,
                        "status": r.get("operationalState", {}).get("lastAvailabilityStatus")
                    })
            return result

        except Exception as e:
            logger.error("Error getting resources", error=str(e))
            return []

    async def get_user_shadows(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get all shadow accounts (projections) for a user.

        Shadows represent the user's accounts in target Resources.

        Args:
            account_id: User OID or name

        Returns:
            List of shadow details
        """
        try:
            client = self._get_client()

            oid = await self._resolve_oid(account_id)
            if not oid:
                return []

            response = await client.get(
                f"/ws/rest/users/{oid}/shadows"
            )

            if response.status_code != 200:
                return []

            data = response.json()
            shadows = data.get("object", [])

            return [{
                "oid": s.get("oid"),
                "resourceOid": s.get("shadow", s).get("resourceRef", {}).get("oid"),
                "kind": s.get("shadow", s).get("kind"),
                "intent": s.get("shadow", s).get("intent"),
                "name": s.get("shadow", s).get("name")
            } for s in shadows]

        except Exception as e:
            logger.error("Error getting shadows", error=str(e))
            return []

    # ==================== Private Helper Methods ====================

    async def _resolve_oid(self, account_id: str) -> Optional[str]:
        """Resolve account_id to MidPoint OID."""
        # If it looks like an OID, use directly
        if self._is_oid(account_id):
            return account_id

        # Otherwise search by name
        try:
            client = self._get_client()

            search_query = {
                "query": {
                    "filter": {
                        "equal": {
                            "path": "name",
                            "value": account_id
                        }
                    }
                }
            }

            response = await client.post(
                "/ws/rest/users/search",
                json=search_query
            )

            if response.status_code == 200:
                data = response.json()
                # MidPoint JSON structure: data["object"]["object"] is the list
                obj_wrapper = data.get("object", {})
                if isinstance(obj_wrapper, dict):
                    users = obj_wrapper.get("object", [])
                else:
                    users = obj_wrapper if isinstance(obj_wrapper, list) else []

                if not isinstance(users, list):
                    users = [users]

                if users and isinstance(users[0], dict):
                    return users[0].get("oid")

            return None

        except Exception as e:
            logger.error("Error resolving OID", account_id=account_id, error=str(e))
            return None

    async def _resolve_role_oid(self, role_id: str) -> Optional[str]:
        """Resolve role name to OID."""
        if self._is_oid(role_id):
            return role_id

        try:
            client = self._get_client()

            search_query = {
                "query": {
                    "filter": {
                        "equal": {
                            "path": "name",
                            "value": role_id
                        }
                    }
                }
            }

            response = await client.post(
                "/ws/rest/roles/search",
                json=search_query
            )

            if response.status_code == 200:
                data = response.json()
                # MidPoint JSON structure: data["object"]["object"] is the list
                obj_wrapper = data.get("object", {})
                if isinstance(obj_wrapper, dict):
                    roles = obj_wrapper.get("object", [])
                else:
                    roles = obj_wrapper if isinstance(obj_wrapper, list) else []

                if not isinstance(roles, list):
                    roles = [roles]

                if roles and isinstance(roles[0], dict):
                    return roles[0].get("oid")

            return None

        except Exception as e:
            logger.error("Error resolving role OID", role_id=role_id, error=str(e))
            return None

    def _is_oid(self, value: str) -> bool:
        """Check if value looks like a MidPoint OID (UUID format)."""
        if not value:
            return False
        # MidPoint OIDs are UUIDs
        parts = value.split("-")
        return len(parts) == 5 and len(value) == 36

    def _build_user_object(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build MidPoint user object from attributes."""
        user = {
            "name": account_id,
            "activation": {
                "administrativeStatus": attributes.get("administrativeStatus", "enabled")
            }
        }

        # Map common attributes
        attr_mapping = {
            "firstname": "givenName",
            "first_name": "givenName",
            "givenName": "givenName",
            "lastname": "familyName",
            "last_name": "familyName",
            "familyName": "familyName",
            "email": "emailAddress",
            "emailAddress": "emailAddress",
            "employeeNumber": "employeeNumber",
            "employee_id": "employeeNumber",
            "department": "organizationalUnit",
            "organizationalUnit": "organizationalUnit",
            "title": "title",
            "description": "description",
            "telephoneNumber": "telephoneNumber",
            "phone": "telephoneNumber"
        }

        for src_attr, mp_attr in attr_mapping.items():
            if src_attr in attributes and attributes[src_attr]:
                user[mp_attr] = attributes[src_attr]

        # Build fullName if not provided
        if "fullName" not in user:
            first = user.get("givenName", "")
            last = user.get("familyName", "")
            if first or last:
                user["fullName"] = f"{first} {last}".strip()

        # Handle password
        if "password" in attributes:
            user["credentials"] = {
                "password": {
                    "value": {
                        "clearValue": attributes["password"]
                    }
                }
            }

        return {"user": user}

    def _build_modifications(self, attributes: Dict[str, Any]) -> List[Dict]:
        """Build MidPoint modification deltas."""
        modifications = []

        attr_mapping = {
            "firstname": "givenName",
            "first_name": "givenName",
            "lastname": "familyName",
            "last_name": "familyName",
            "email": "emailAddress",
            "department": "organizationalUnit",
            "administrativeStatus": "activation/administrativeStatus"
        }

        for key, value in attributes.items():
            mp_path = attr_mapping.get(key, key)

            modifications.append({
                "modificationType": "replace",
                "path": mp_path,
                "value": [value] if not isinstance(value, list) else value
            })

        return modifications

    def _parse_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse MidPoint user response to simplified format."""
        props = user_data.get("user", user_data)

        # Extract role assignments
        roles = []
        assignments = props.get("assignment", [])
        if not isinstance(assignments, list):
            assignments = [assignments]
        for a in assignments:
            if isinstance(a, dict):
                target_ref = a.get("targetRef", {})
                if target_ref.get("type") == "RoleType":
                    roles.append(target_ref.get("oid"))

        activation = props.get("activation", {})

        return {
            "oid": props.get("oid"),
            "name": props.get("name"),
            "fullName": props.get("fullName"),
            "firstname": props.get("givenName"),
            "lastname": props.get("familyName"),
            "email": props.get("emailAddress"),
            "employeeNumber": props.get("employeeNumber"),
            "department": props.get("organizationalUnit"),
            "title": props.get("title"),
            "description": props.get("description"),
            "telephoneNumber": props.get("telephoneNumber"),
            "active": activation.get("administrativeStatus") == "enabled",
            "administrativeStatus": activation.get("administrativeStatus"),
            "roles": roles
        }

    def _extract_oid_from_location(self, response: httpx.Response) -> Optional[str]:
        """Extract OID from Location header after creation."""
        location = response.headers.get("Location", "")
        if location:
            # Location format: .../users/{oid}
            parts = location.rstrip("/").split("/")
            if parts:
                return parts[-1]
        return None
