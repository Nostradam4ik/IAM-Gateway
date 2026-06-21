"""
Webhooks API - Receives notifications from MidPoint
Handles automatic provisioning to Keycloak
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends, status
from typing import Dict, Any, Optional
from pydantic import BaseModel
import hmac
import hashlib
import secrets as _secrets
import httpx
import structlog
import os

from app.core.config import settings
from app.core.security import require_role

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
logger = structlog.get_logger()

# Configuration Keycloak
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "gateway")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")


class UserChangeEvent(BaseModel):
    """Event received from MidPoint when a user changes"""
    event: str
    operation: str
    user: Dict[str, Any]


class KeycloakProvisioner:
    """Handles provisioning to Keycloak"""

    def __init__(self):
        self.base_url = KEYCLOAK_URL
        self.realm = KEYCLOAK_REALM
        self.admin_user = KEYCLOAK_ADMIN_USER
        self.admin_password = KEYCLOAK_ADMIN_PASSWORD
        self._token: Optional[str] = None

    async def get_token(self) -> str:
        """Get admin token from Keycloak"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/realms/master/protocol/openid-connect/token",
                data={
                    "username": self.admin_user,
                    "password": self.admin_password,
                    "grant_type": "password",
                    "client_id": "admin-cli"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                self._token = data.get("access_token")
                return self._token
            else:
                logger.error("Failed to get Keycloak token", status=response.status_code)
                raise HTTPException(status_code=500, detail="Failed to get Keycloak token")

    async def user_exists(self, username: str) -> Optional[str]:
        """Check if user exists in Keycloak, return user ID if exists"""
        token = await self.get_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/users",
                params={"username": username, "exact": "true"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                users = response.json()
                if users:
                    return users[0].get("id")
            return None

    async def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a user in Keycloak"""
        token = await self.get_token()
        username = user_data.get("name") or user_data.get("username")

        keycloak_user = {
            "username": username,
            "email": user_data.get("email") or f"{username}@example.com",
            "firstName": user_data.get("givenName") or "",
            "lastName": user_data.get("familyName") or "",
            "enabled": True,
            "emailVerified": True,
            "credentials": [{
                "type": "password",
                "value": _secrets.token_urlsafe(24),
                "temporary": True
            }]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/admin/realms/{self.realm}/users",
                json=keycloak_user,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )

            if response.status_code == 201:
                logger.info("User created in Keycloak", username=username)
                return True
            elif response.status_code == 409:
                logger.info("User already exists in Keycloak", username=username)
                return True
            else:
                logger.error("Failed to create user in Keycloak",
                           username=username, status=response.status_code,
                           response=response.text[:200])
                return False

    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Update a user in Keycloak"""
        token = await self.get_token()
        username = user_data.get("name") or user_data.get("username")

        keycloak_user = {
            "email": user_data.get("email") or f"{username}@example.com",
            "firstName": user_data.get("givenName") or "",
            "lastName": user_data.get("familyName") or "",
            "enabled": True
        }

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}",
                json=keycloak_user,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )

            if response.status_code == 204:
                logger.info("User updated in Keycloak", username=username)
                return True
            else:
                logger.error("Failed to update user in Keycloak",
                           username=username, status=response.status_code)
                return False

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user from Keycloak"""
        token = await self.get_token()

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 204:
                logger.info("User deleted from Keycloak", user_id=user_id)
                return True
            else:
                logger.error("Failed to delete user from Keycloak", user_id=user_id)
                return False

    async def provision_user(self, user_data: Dict[str, Any], operation: str) -> Dict[str, Any]:
        """Provision user to Keycloak based on operation type"""
        username = user_data.get("name") or user_data.get("username")

        if not username:
            return {"success": False, "error": "No username provided"}

        # Skip system users
        if username in ["administrator", "midpoint"]:
            logger.info("Skipping system user", username=username)
            return {"success": True, "skipped": True}

        try:
            existing_user_id = await self.user_exists(username)

            if operation.lower() in ["add", "create"]:
                if existing_user_id:
                    # User exists, update instead
                    success = await self.update_user(existing_user_id, user_data)
                else:
                    success = await self.create_user(user_data)

            elif operation.lower() in ["modify", "update"]:
                if existing_user_id:
                    success = await self.update_user(existing_user_id, user_data)
                else:
                    # User doesn't exist, create
                    success = await self.create_user(user_data)

            elif operation.lower() == "delete":
                if existing_user_id:
                    success = await self.delete_user(existing_user_id)
                else:
                    success = True  # Already doesn't exist

            else:
                logger.warning("Unknown operation", operation=operation)
                success = False

            return {"success": success, "username": username, "operation": operation}

        except Exception as e:
            logger.exception("Error provisioning to Keycloak", error=str(e))
            return {"success": False, "error": str(e)}


# Global provisioner instance
keycloak_provisioner = KeycloakProvisioner()


async def process_user_change(user_event: UserChangeEvent):
    """Background task to process user change"""
    logger.info("Processing MidPoint webhook",
               event_type=user_event.event,
               operation=user_event.operation,
               username=user_event.user.get("name"))

    result = await keycloak_provisioner.provision_user(user_event.user, user_event.operation)
    logger.info("Keycloak provisioning result", **result)


async def verify_midpoint_signature(request: Request) -> None:
    """
    Authentifie un webhook entrant de MidPoint via HMAC-SHA256.

    MidPoint doit signer le corps brut de la requete avec un secret partage
    (settings.MIDPOINT_WEBHOOK_SECRET) et envoyer la signature hex dans l'en-tete
    X-MidPoint-Signature. La verification se fait en temps constant AVANT tout
    traitement, afin qu'un appelant non authentifie ne puisse pas creer/modifier/
    supprimer des comptes Keycloak.
    """
    # Lire le corps une seule fois (mis en cache pour request.json() du handler)
    body = await request.body()
    secret = settings.MIDPOINT_WEBHOOK_SECRET

    if not secret:
        if settings.DEBUG:
            logger.warning(
                "MIDPOINT_WEBHOOK_SECRET non configure - verification ignoree (DEBUG uniquement)"
            )
            return
        logger.error("MIDPOINT_WEBHOOK_SECRET non configure - webhook rejete")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook authentication not configured",
        )

    signature = request.headers.get("X-MidPoint-Signature", "")
    if signature.startswith("sha256="):
        signature = signature.split("=", 1)[1]

    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        logger.warning("Signature de webhook MidPoint invalide")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )


@router.post("/midpoint/user-change", dependencies=[Depends(verify_midpoint_signature)])
async def midpoint_user_change_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint for MidPoint user change notifications.

    MidPoint sends notifications when users are created, modified, or deleted.
    This endpoint triggers automatic provisioning to Keycloak.
    """
    try:
        body = await request.json()
        logger.info("Received MidPoint webhook", body=body)

        event = UserChangeEvent(**body)

        # Process in background to respond quickly to MidPoint
        background_tasks.add_task(process_user_change, event)

        return {
            "status": "accepted",
            "message": "User change event received, processing in background"
        }

    except Exception as e:
        logger.exception("Error processing webhook", error=str(e))
        raise HTTPException(status_code=400, detail=f"Invalid webhook payload: {str(e)}")


@router.post("/midpoint/sync-all")
async def sync_all_to_keycloak(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Manually trigger synchronization of all MidPoint users to Keycloak.

    This is useful for initial sync or recovery scenarios.
    """
    logger.info("Manual sync all to Keycloak triggered")

    # This would fetch all users from MidPoint and sync to Keycloak
    # For now, return a message indicating manual sync should use the script

    return {
        "status": "info",
        "message": "For full sync, use: python3 scripts/midpoint_to_keycloak_sync.py --sync"
    }


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint"""
    return {"status": "healthy", "service": "webhooks"}
