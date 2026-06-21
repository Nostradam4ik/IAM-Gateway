"""
API endpoints pour l'intégration MidPoint.

MidPoint est l'orchestrateur central IAM qui gère:
- Les utilisateurs (identités)
- Les rôles et leurs assignments
- Les ressources (LDAP, Odoo, Keycloak, SQL, etc.)
- Le provisioning vers les systèmes cibles
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import structlog

from app.connectors.midpoint_connector import MidPointConnector
from app.core.security import get_current_user, require_role
from app.models.iam import MidpointRoleList, MidpointResourceList

logger = structlog.get_logger()
router = APIRouter(prefix="/midpoint", tags=["MidPoint"])

# Pydantic models
class UserCreate(BaseModel):
    username: str
    firstname: str
    lastname: str
    email: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    employee_id: Optional[str] = None
    password: Optional[str] = None

class UserUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None

class RoleAssignment(BaseModel):
    user_id: str
    role_id: str

# Singleton connector
_connector: Optional[MidPointConnector] = None

def get_connector() -> MidPointConnector:
    global _connector
    if _connector is None:
        _connector = MidPointConnector()
    return _connector


# ==================== Users ====================

@router.get("/users")
async def list_users(
    _: dict = Depends(get_current_user)
):
    """Liste tous les utilisateurs depuis MidPoint."""
    try:
        connector = get_connector()
        users = await connector.list_accounts()
        return {
            "total": len(users),
            "users": users
        }
    except Exception as e:
        logger.error("Failed to list MidPoint users", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur MidPoint: {str(e)}")


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    _: dict = Depends(get_current_user)
):
    """Récupère les détails d'un utilisateur depuis MidPoint."""
    try:
        connector = get_connector()
        user = await connector.get_account(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        # Get user's shadows (accounts in target systems)
        shadows = await connector.get_user_shadows(user_id)
        user["shadows"] = shadows

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get MidPoint user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur MidPoint: {str(e)}")


@router.post("/users")
async def create_user(
    user: UserCreate,
    _: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """Crée un nouvel utilisateur dans MidPoint."""
    try:
        connector = get_connector()

        attributes = {
            "firstname": user.firstname,
            "lastname": user.lastname,
            "email": user.email,
            "department": user.department,
            "title": user.title,
            "employee_id": user.employee_id,
        }

        if user.password:
            attributes["password"] = user.password

        # Remove None values
        attributes = {k: v for k, v in attributes.items() if v is not None}

        result = await connector.create_account(user.username, attributes)

        logger.info("User created in MidPoint", username=user.username)
        return result

    except Exception as e:
        logger.error("Failed to create MidPoint user", username=user.username, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur création: {str(e)}")


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user: UserUpdate,
    _: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """Met à jour un utilisateur dans MidPoint."""
    try:
        connector = get_connector()

        attributes = user.model_dump(exclude_none=True)
        if not attributes:
            raise HTTPException(status_code=400, detail="Aucun attribut à mettre à jour")

        result = await connector.update_account(user_id, attributes)

        logger.info("User updated in MidPoint", user_id=user_id)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update MidPoint user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur mise à jour: {str(e)}")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    _: dict = Depends(require_role(["admin"]))
):
    """Supprime un utilisateur de MidPoint (et de tous les systèmes cibles)."""
    try:
        connector = get_connector()
        success = await connector.delete_account(user_id)

        if success:
            logger.info("User deleted from MidPoint", user_id=user_id)
            return {"success": True, "message": "Utilisateur supprimé"}
        else:
            raise HTTPException(status_code=500, detail="Échec de la suppression")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete MidPoint user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur suppression: {str(e)}")


@router.post("/users/{user_id}/disable")
async def disable_user(
    user_id: str,
    _: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """Désactive un utilisateur dans MidPoint."""
    try:
        connector = get_connector()
        success = await connector.disable_account(user_id)

        if success:
            return {"success": True, "message": "Utilisateur désactivé"}
        else:
            raise HTTPException(status_code=500, detail="Échec de la désactivation")

    except Exception as e:
        logger.error("Failed to disable user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/users/{user_id}/enable")
async def enable_user(
    user_id: str,
    _: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """Active un utilisateur dans MidPoint."""
    try:
        connector = get_connector()
        success = await connector.enable_account(user_id)

        if success:
            return {"success": True, "message": "Utilisateur activé"}
        else:
            raise HTTPException(status_code=500, detail="Échec de l'activation")

    except Exception as e:
        logger.error("Failed to enable user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ==================== Roles ====================

@router.get("/roles", response_model=MidpointRoleList)
async def list_roles(
    _: dict = Depends(get_current_user)
):
    """Liste tous les rôles depuis MidPoint."""
    try:
        connector = get_connector()
        roles = await connector.get_roles()
        return {
            "total": len(roles),
            "roles": roles
        }
    except Exception as e:
        logger.error("Failed to list MidPoint roles", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur MidPoint: {str(e)}")


@router.post("/users/{user_id}/roles/{role_id}")
async def assign_role(
    user_id: str,
    role_id: str,
    _: dict = Depends(require_role(["admin"]))
):
    """Assigne un rôle à un utilisateur."""
    try:
        connector = get_connector()
        await connector.assign_role(user_id, role_id)
        logger.info("Role assigned", user_id=user_id, role_id=role_id)
        return {"success": True, "message": "Rôle assigné avec succès"}

    except Exception as e:
        error_msg = str(e)
        # Parse MidPoint error for user-friendly message
        if "Name attribute cannot be null" in error_msg:
            error_msg = "L'utilisateur n'a pas de nom/prénom valide pour créer un compte LDAP"
        elif "Configuration error" in error_msg:
            error_msg = f"Erreur de configuration MidPoint: {error_msg}"

        logger.error("Failed to assign role", user_id=user_id, role_id=role_id, error=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role(
    user_id: str,
    role_id: str,
    _: dict = Depends(require_role(["admin"]))
):
    """Retire un rôle d'un utilisateur."""
    try:
        connector = get_connector()
        success = await connector.remove_role(user_id, role_id)

        if success:
            logger.info("Role removed", user_id=user_id, role_id=role_id)
            return {"success": True, "message": "Rôle retiré"}
        else:
            raise HTTPException(status_code=500, detail="Échec du retrait")

    except Exception as e:
        logger.error("Failed to remove role", user_id=user_id, role_id=role_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/users/{user_id}/roles")
async def get_user_roles(
    user_id: str,
    _: dict = Depends(get_current_user)
):
    """Récupère les rôles d'un utilisateur."""
    try:
        connector = get_connector()
        roles = await connector.get_user_roles(user_id)
        return {"user_id": user_id, "roles": roles}
    except Exception as e:
        logger.error("Failed to get user roles", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ==================== Resources ====================

@router.get("/resources", response_model=MidpointResourceList)
async def list_resources(
    _: dict = Depends(get_current_user)
):
    """Liste toutes les ressources (systèmes cibles) configurées dans MidPoint."""
    try:
        connector = get_connector()
        resources = await connector.get_resources()
        return {
            "total": len(resources),
            "resources": resources
        }
    except Exception as e:
        logger.error("Failed to list MidPoint resources", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur MidPoint: {str(e)}")


@router.get("/users/{user_id}/shadows")
async def get_user_shadows(
    user_id: str,
    _: dict = Depends(get_current_user)
):
    """
    Récupère les comptes (shadows) d'un utilisateur dans les systèmes cibles.

    Un shadow représente le compte de l'utilisateur dans un système externe
    (LDAP, Odoo, Keycloak, etc.)
    """
    try:
        connector = get_connector()
        shadows = await connector.get_user_shadows(user_id)
        return {
            "user_id": user_id,
            "shadows": shadows
        }
    except Exception as e:
        logger.error("Failed to get user shadows", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ==================== Health ====================

@router.get("/health")
async def check_midpoint_health(
    _: dict = Depends(get_current_user)
):
    """Vérifie la connexion à MidPoint."""
    try:
        connector = get_connector()
        connected = await connector.test_connection()

        return {
            "status": "connected" if connected else "disconnected",
            "url": connector.url
        }
    except Exception as e:
        logger.error("MidPoint health check failed", error=str(e))
        return {
            "status": "error",
            "error": str(e)
        }
