"""
API de Provisioning via MidPoint
Toutes les opérations passent par MidPoint comme hub central
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import structlog

from app.services.midpoint_provision_service_updated import MidPointProvisionService
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/provision-midpoint", tags=["Provisioning via MidPoint"])
logger = structlog.get_logger()


class CreateUserViaMidPointRequest(BaseModel):
    """Demande de création d'utilisateur via MidPoint"""
    username: str = Field(..., description="Nom d'utilisateur unique")
    firstname: str = Field(..., description="Prénom")
    lastname: str = Field(..., description="Nom de famille")
    email: str = Field(..., description="Email")
    employee_id: str | None = Field(None, description="ID employé")
    department: str | None = Field(None, description="Département")
    phone: str | None = Field(None, description="Téléphone")
    assign_roles: List[str] = Field(default_factory=list, description="OIDs des rôles à assigner")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "jdoe",
                "firstname": "John",
                "lastname": "Doe",
                "email": "john.doe@example.com",
                "employee_id": "EMP001",
                "department": "IT",
                "phone": "+33123456789",
                "assign_roles": ["role-ldap-user-oid", "role-db-user-oid"]
            }
        }


class UpdateUserViaMidPointRequest(BaseModel):
    """Demande de mise à jour d'utilisateur via MidPoint"""
    oid: str | None = Field(None, description="OID MidPoint de l'utilisateur (si connu)")
    username: str | None = Field(None, description="Username (si OID inconnu)")
    email: str | None = Field(None, description="Nouvel email")
    department: str | None = Field(None, description="Nouveau département")
    phone: str | None = Field(None, description="Nouveau téléphone")


class DeleteUserViaMidPointRequest(BaseModel):
    """Demande de suppression d'utilisateur via MidPoint"""
    oid: str | None = Field(None, description="OID MidPoint de l'utilisateur")
    username: str | None = Field(None, description="Username (si OID inconnu)")


class AssignRoleRequest(BaseModel):
    """Demande d'assignation de rôle"""
    user_oid: str = Field(..., description="OID de l'utilisateur")
    role_oid: str = Field(..., description="OID du rôle à assigner")


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user_via_midpoint(
    request: CreateUserViaMidPointRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Crée un utilisateur via MidPoint.

    **Flow**:
    1. Gateway IAM reçoit la demande
    2. Gateway crée l'utilisateur dans MidPoint
    3. MidPoint provisionne automatiquement vers:
       - OpenLDAP (si rôle LDAP assigné)
       - PostgreSQL (si rôle Database assigné)
    4. Gateway retourne le résultat avec les statuts

    **Avantages**:
    - Centralisation dans MidPoint
    - Gestion automatique des rôles
    - Audit centralisé
    - Rollback automatique en cas d'erreur
    """
    logger.info(
        "API: Creating user via MidPoint",
        username=request.username,
        requested_by=current_user.get("sub")
    )

    service = MidPointProvisionService()

    # Créer l'utilisateur dans MidPoint
    user_data = request.dict()
    roles_to_assign = user_data.pop("assign_roles", [])

    result = await service.create_user_in_midpoint(user_data)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user in MidPoint: {result.get('error')}"
        )

    oid = result.get("oid")

    # Assigner les rôles si spécifiés
    role_results = []
    if roles_to_assign and oid:
        for role_oid in roles_to_assign:
            role_result = await service.assign_role_in_midpoint(oid, role_oid)
            role_results.append(role_result)

    # Vérifier le provisioning vers les cibles
    import asyncio
    await asyncio.sleep(2)  # Laisser MidPoint provisionner

    target_status = await service._check_provisioning_status(oid)

    return {
        "success": True,
        "message": "User created in MidPoint and provisioned to target systems",
        "data": {
            "oid": oid,
            "username": request.username,
            "midpoint_status": "created",
            "roles_assigned": len(role_results),
            "target_systems": target_status
        }
    }


@router.patch("/users")
async def update_user_via_midpoint(
    request: UpdateUserViaMidPointRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Met à jour un utilisateur via MidPoint.

    MidPoint propage automatiquement les modifications vers LDAP et PostgreSQL.
    """
    logger.info(
        "API: Updating user via MidPoint",
        oid=request.oid,
        username=request.username,
        requested_by=current_user.get("sub")
    )

    if not request.oid and not request.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'oid' or 'username' must be provided"
        )

    service = MidPointProvisionService()

    # Trouver l'OID si nécessaire
    oid = request.oid
    if not oid and request.username:
        oid = await service._find_user_oid(request.username)
        if not oid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {request.username}"
            )

    # Préparer les modifications
    updates = {k: v for k, v in request.dict().items() if v is not None and k not in ['oid', 'username']}

    result = await service.update_user_in_midpoint(oid, updates)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user in MidPoint: {result.get('error')}"
        )

    # Vérifier le provisioning
    import asyncio
    await asyncio.sleep(2)
    target_status = await service._check_provisioning_status(oid)

    return {
        "success": True,
        "message": "User updated in MidPoint and changes propagated to target systems",
        "data": {
            "oid": oid,
            "midpoint_status": "updated",
            "target_systems": target_status
        }
    }


@router.delete("/users")
async def delete_user_via_midpoint(
    request: DeleteUserViaMidPointRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Supprime un utilisateur via MidPoint.

    MidPoint supprime automatiquement l'utilisateur de LDAP et PostgreSQL.
    """
    logger.info(
        "API: Deleting user via MidPoint",
        oid=request.oid,
        username=request.username,
        requested_by=current_user.get("sub")
    )

    if not request.oid and not request.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'oid' or 'username' must be provided"
        )

    service = MidPointProvisionService()

    # Trouver l'OID si nécessaire
    oid = request.oid
    if not oid and request.username:
        oid = await service._find_user_oid(request.username)
        if not oid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {request.username}"
            )

    result = await service.delete_user_in_midpoint(oid)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user in MidPoint: {result.get('error')}"
        )

    return {
        "success": True,
        "message": "User deleted in MidPoint and removed from target systems",
        "data": {
            "oid": oid,
            "midpoint_status": "deleted"
        }
    }


@router.post("/roles/assign")
async def assign_role_via_midpoint(
    request: AssignRoleRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Assigne un rôle à un utilisateur dans MidPoint.

    L'assignation d'un rôle déclenche automatiquement le provisioning:
    - Rôle LDAP → création du compte LDAP
    - Rôle Database → création du compte PostgreSQL
    """
    logger.info(
        "API: Assigning role via MidPoint",
        user_oid=request.user_oid,
        role_oid=request.role_oid,
        requested_by=current_user.get("sub")
    )

    service = MidPointProvisionService()
    result = await service.assign_role_in_midpoint(request.user_oid, request.role_oid)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign role in MidPoint: {result.get('error')}"
        )

    # Vérifier le provisioning après assignation de rôle
    import asyncio
    await asyncio.sleep(2)
    target_status = await service._check_provisioning_status(request.user_oid)

    return {
        "success": True,
        "message": "Role assigned in MidPoint and provisioning triggered",
        "data": {
            "user_oid": request.user_oid,
            "role_oid": request.role_oid,
            "target_systems": target_status
        }
    }


@router.get("/users/{oid}/status")
async def get_user_provisioning_status(
    oid: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Récupère le statut de provisioning d'un utilisateur sur tous les systèmes cibles.

    Retourne:
    - Statut dans MidPoint
    - Statut dans LDAP
    - Statut dans PostgreSQL
    """
    logger.info("API: Getting user provisioning status", oid=oid)

    service = MidPointProvisionService()
    target_status = await service._check_provisioning_status(oid)

    return {
        "success": True,
        "data": {
            "oid": oid,
            "target_systems": target_status
        }
    }
