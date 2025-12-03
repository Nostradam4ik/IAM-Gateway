"""
Client pour communication avec MidPoint
"""
from typing import Dict, Any, Optional, List
import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class MidPointClient:
    """
    Client pour l'API REST de MidPoint.

    Permet de:
    - Recuperer les utilisateurs
    - Mettre a jour les comptes
    - Gerer les roles et assignations
    """

    def __init__(self):
        self.base_url = settings.MIDPOINT_URL
        self.username = settings.MIDPOINT_USER
        self.password = settings.MIDPOINT_PASSWORD
        self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client with auth."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=(self.username, self.password),
                timeout=30.0,
                headers={"Content-Type": "application/json"}
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()

    async def test_connection(self) -> bool:
        """Test connection to MidPoint."""
        try:
            client = self._get_client()
            response = await client.get("/ws/rest/self")
            return response.status_code == 200
        except Exception as e:
            logger.error("MidPoint connection failed", error=str(e))
            return False

    async def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Retrieve all user accounts from MidPoint."""
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
            logger.error("Failed to get accounts from MidPoint", error=str(e))
            return []

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific user account."""
        try:
            client = self._get_client()
            response = await client.get(f"/ws/rest/users/{account_id}")

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return self._parse_user(response.json())

        except Exception as e:
            logger.error("Failed to get account", account_id=account_id, error=str(e))
            return None

    async def create_account(
        self,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new user in MidPoint."""
        try:
            client = self._get_client()

            user_object = self._build_user_object(attributes)

            response = await client.post(
                "/ws/rest/users",
                json=user_object
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error("Failed to create account in MidPoint", error=str(e))
            raise

    async def update_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing user in MidPoint."""
        try:
            client = self._get_client()

            # Build modification delta
            modifications = []
            for key, value in attributes.items():
                modifications.append({
                    "op": "replace",
                    "path": f"/{key}",
                    "value": value
                })

            response = await client.patch(
                f"/ws/rest/users/{account_id}",
                json={"modifications": modifications}
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error("Failed to update account", account_id=account_id, error=str(e))
            raise

    async def delete_account(self, account_id: str) -> bool:
        """Delete a user from MidPoint."""
        try:
            client = self._get_client()
            response = await client.delete(f"/ws/rest/users/{account_id}")
            return response.status_code in [200, 204]

        except Exception as e:
            logger.error("Failed to delete account", account_id=account_id, error=str(e))
            return False

    async def assign_role(
        self,
        account_id: str,
        role_id: str
    ) -> bool:
        """Assign a role to a user."""
        try:
            client = self._get_client()

            assignment = {
                "assignment": {
                    "targetRef": {
                        "oid": role_id,
                        "type": "RoleType"
                    }
                }
            }

            response = await client.post(
                f"/ws/rest/users/{account_id}/assignments",
                json=assignment
            )
            response.raise_for_status()

            logger.info("Role assigned", account_id=account_id, role_id=role_id)
            return True

        except Exception as e:
            logger.error("Failed to assign role", error=str(e))
            return False

    async def remove_role(
        self,
        account_id: str,
        role_id: str
    ) -> bool:
        """Remove a role from a user."""
        try:
            client = self._get_client()

            response = await client.delete(
                f"/ws/rest/users/{account_id}/assignments/{role_id}"
            )
            return response.status_code in [200, 204]

        except Exception as e:
            logger.error("Failed to remove role", error=str(e))
            return False

    async def get_roles(self) -> List[Dict[str, Any]]:
        """Get all roles from MidPoint."""
        try:
            client = self._get_client()
            response = await client.get("/ws/rest/roles")
            response.raise_for_status()

            data = response.json()
            return data.get("object", [])

        except Exception as e:
            logger.error("Failed to get roles", error=str(e))
            return []

    async def search_users(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search users in MidPoint."""
        try:
            client = self._get_client()

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

            response = await client.post(
                "/ws/rest/users/search",
                json=search_query
            )
            response.raise_for_status()

            data = response.json()
            users = data.get("object", [])

            return [self._parse_user(u) for u in users]

        except Exception as e:
            logger.error("Failed to search users", error=str(e))
            return []

    def _parse_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse MidPoint user object to simplified format."""
        props = user_data.get("user", user_data)

        return {
            "id": props.get("oid"),
            "name": props.get("name"),
            "fullName": props.get("fullName"),
            "firstname": props.get("givenName"),
            "lastname": props.get("familyName"),
            "email": props.get("emailAddress"),
            "employeeNumber": props.get("employeeNumber"),
            "department": props.get("organizationalUnit"),
            "title": props.get("title"),
            "active": props.get("activation", {}).get("administrativeStatus") == "enabled"
        }

    def _build_user_object(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Build MidPoint user object from attributes."""
        return {
            "user": {
                "name": attributes.get("username") or attributes.get("name"),
                "givenName": attributes.get("firstname"),
                "familyName": attributes.get("lastname"),
                "fullName": f"{attributes.get('firstname', '')} {attributes.get('lastname', '')}".strip(),
                "emailAddress": attributes.get("email"),
                "employeeNumber": attributes.get("employeeNumber"),
                "organizationalUnit": attributes.get("department"),
                "activation": {
                    "administrativeStatus": "enabled"
                }
            }
        }
