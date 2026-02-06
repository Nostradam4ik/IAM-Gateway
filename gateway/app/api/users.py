"""
API de gestion des utilisateurs Gateway.
Permet de creer, modifier et assigner des roles aux utilisateurs.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
import structlog

from app.core.security import get_current_user, require_role
from app.core.database import get_session
from app.services.user_service import UserService, APPROVAL_ROLES, ACCESS_ROLES, ALL_ROLES

router = APIRouter()
logger = structlog.get_logger()


class UserCreate(BaseModel):
    """Schema pour creer un utilisateur."""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    roles: List[str] = ["viewer"]


class UserUpdate(BaseModel):
    """Schema pour modifier un utilisateur."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema de reponse utilisateur."""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    role: str
    roles: List[str]
    is_active: bool
    created_at: Optional[str]
    last_login: Optional[str] = None


class RoleInfo(BaseModel):
    """Information sur un role."""
    name: str
    display_name: str
    description: str
    level: int
    category: str = "approval"  # "approval" ou "access"


@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Liste tous les utilisateurs Gateway."""
    user_service = UserService(session)
    users = await user_service.list_all_users()
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Cree un nouvel utilisateur Gateway."""
    user_service = UserService(session)

    # Verifier si l'utilisateur existe deja
    existing = await user_service.get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"L'utilisateur '{user_data.username}' existe deja"
        )

    # Creer l'utilisateur
    new_user = await user_service.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        roles=user_data.roles
    )

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la creation de l'utilisateur"
        )

    logger.info("User created", username=user_data.username, by=current_user.get("username"))

    return UserResponse(
        id=new_user["id"],
        username=new_user["username"],
        email=new_user["email"],
        full_name=new_user["full_name"],
        role=new_user["role"],
        roles=new_user["roles"],
        is_active=True,
        created_at=new_user["created_at"]
    )


@router.get("/roles", response_model=List[RoleInfo])
async def list_available_roles(
    current_user: dict = Depends(get_current_user)
):
    """Liste tous les roles disponibles (acces + approbation)."""
    roles = []
    # D'abord les roles d'acces
    for name, info in ACCESS_ROLES.items():
        roles.append(RoleInfo(
            name=name,
            display_name=info["display_name"],
            description=info["description"],
            level=info["level"],
            category=info["category"]
        ))
    # Ensuite les roles d'approbation
    for name, info in APPROVAL_ROLES.items():
        roles.append(RoleInfo(
            name=name,
            display_name=info["display_name"],
            description=info["description"],
            level=info["level"],
            category=info["category"]
        ))
    # Trier: d'abord par categorie (access avant approval), puis par level
    return sorted(roles, key=lambda r: (0 if r.category == "access" else 1, r.level))


@router.get("/by-role/{role}", response_model=List[UserResponse])
async def get_users_by_role(
    role: str,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"])),
    session=Depends(get_session)
):
    """Recupere tous les utilisateurs ayant un role specifique."""
    user_service = UserService(session)
    users = await user_service.get_users_by_role(role)

    return [
        UserResponse(
            id=u["id"],
            username=u["username"],
            email=u["email"],
            full_name=u.get("full_name"),
            role=u["role"],
            roles=u.get("roles", []),
            is_active=True,
            created_at=None
        )
        for u in users
    ]


@router.get("/emails-by-role/{role}")
async def get_emails_by_role(
    role: str,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"])),
    session=Depends(get_session)
):
    """Recupere les emails de tous les utilisateurs ayant un role specifique."""
    user_service = UserService(session)
    emails = await user_service.get_emails_by_role(role)

    return {
        "role": role,
        "count": len(emails),
        "emails": emails
    }


@router.get("/approval-chain/{workflow_type}")
async def get_approval_chain(
    workflow_type: str = "full",
    current_user: dict = Depends(require_role(["admin", "iam_engineer"])),
    session=Depends(get_session)
):
    """
    Recupere la chaine d'approbation complete pour un type de workflow.

    Args:
        workflow_type: 'full' (Manager->RH->IT), 'manager_only', ou 'rh_it'
    """
    if workflow_type not in ["full", "manager_only", "rh_it"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workflow_type doit etre 'full', 'manager_only' ou 'rh_it'"
        )

    user_service = UserService(session)
    chain = await user_service.get_approval_chain_emails(workflow_type)

    # Formater la reponse
    levels = []
    role_names = {
        1: "Manager" if workflow_type != "rh_it" else "RH Manager",
        2: "RH Manager" if workflow_type == "full" else "IT Admin",
        3: "IT Admin"
    }

    for level, emails in chain.items():
        levels.append({
            "level": level,
            "role_name": role_names.get(level, f"Niveau {level}"),
            "approvers_count": len(emails),
            "emails": emails
        })

    return {
        "workflow_type": workflow_type,
        "total_levels": len(chain),
        "levels": levels
    }


@router.get("/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Recupere un utilisateur par son nom d'utilisateur."""
    user_service = UserService(session)
    user = await user_service.get_user_by_username(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur '{username}' non trouve"
        )

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        role=user["role"],
        roles=user.get("roles", []),
        is_active=user["is_active"],
        created_at=None
    )


@router.put("/{username}/roles")
async def update_user_roles(
    username: str,
    roles: List[str],
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Met a jour les roles d'un utilisateur."""
    user_service = UserService(session)

    # Verifier que l'utilisateur existe
    user = await user_service.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur '{username}' non trouve"
        )

    # Mettre a jour les roles
    success = await user_service.update_user_roles(username, roles)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise a jour des roles"
        )

    logger.info("User roles updated", username=username, roles=roles, by=current_user.get("username"))

    return {
        "status": "updated",
        "username": username,
        "roles": roles
    }


@router.delete("/{username}")
async def delete_user(
    username: str,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Desactive un utilisateur."""
    if username == current_user.get("username"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte"
        )

    user_service = UserService(session)
    success = await user_service.delete_user(username)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur '{username}' non trouve"
        )

    logger.info("User deleted", username=username, by=current_user.get("username"))

    return {"status": "deleted", "username": username}
