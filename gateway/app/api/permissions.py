"""
API de gestion des niveaux de droits (1-5)
Systeme de permissions hierarchique pour les utilisateurs
Persiste dans la table gateway_users (colonne permission_level)
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.security import get_current_user, require_role
from app.core.database import get_session
from app.core.memory_store import memory_store

router = APIRouter()
logger = structlog.get_logger()


# Definition des niveaux de droits (constantes de reference)
PERMISSION_LEVELS = {
    1: {
        "name": "Visiteur",
        "description": "Acces minimal - Consultation uniquement",
        "color": "#6b7280",
        "permissions": [
            "view_dashboard",
            "view_own_profile"
        ],
        "examples": ["Stagiaire", "Visiteur externe", "Consultant temporaire"]
    },
    2: {
        "name": "Utilisateur",
        "description": "Acces standard - Consultation et actions basiques",
        "color": "#3b82f6",
        "permissions": [
            "view_dashboard",
            "view_own_profile",
            "view_operations",
            "create_request",
            "view_own_requests"
        ],
        "examples": ["Employe", "Technicien", "Assistant"]
    },
    3: {
        "name": "Operateur",
        "description": "Acces etendu - Gestion des operations courantes",
        "color": "#10b981",
        "permissions": [
            "view_dashboard",
            "view_own_profile",
            "view_operations",
            "create_request",
            "view_own_requests",
            "view_all_requests",
            "approve_level1",
            "view_reports",
            "export_data"
        ],
        "examples": ["Chef d'equipe", "Superviseur", "Coordinateur"]
    },
    4: {
        "name": "Manager",
        "description": "Acces avance - Validation et gestion d'equipe",
        "color": "#f59e0b",
        "permissions": [
            "view_dashboard",
            "view_own_profile",
            "view_operations",
            "create_request",
            "view_own_requests",
            "view_all_requests",
            "approve_level1",
            "approve_level2",
            "view_reports",
            "export_data",
            "manage_team",
            "view_audit_logs",
            "configure_rules"
        ],
        "examples": ["Manager", "Responsable RH", "Chef de projet"]
    },
    5: {
        "name": "Chef de Departement",
        "description": "Acces maximum (non-admin) - Gestion complete du departement",
        "color": "#8b5cf6",
        "permissions": [
            "view_dashboard",
            "view_own_profile",
            "view_operations",
            "create_request",
            "view_own_requests",
            "view_all_requests",
            "approve_level1",
            "approve_level2",
            "approve_level3",
            "view_reports",
            "export_data",
            "manage_team",
            "view_audit_logs",
            "configure_rules",
            "manage_department",
            "view_all_departments",
            "approve_budget",
            "strategic_decisions"
        ],
        "examples": ["Directeur", "Chef de departement", "VP"]
    }
}


class UserPermission(BaseModel):
    """Schema pour les permissions utilisateur."""
    user_id: str
    username: str
    full_name: str
    department: str
    level: int
    level_name: str
    permissions: List[str]
    assigned_by: str
    assigned_at: str


class PermissionAssignment(BaseModel):
    """Schema pour assigner un niveau de droits."""
    user_id: str
    level: int
    reason: Optional[str] = None


class PermissionLevel(BaseModel):
    """Schema pour un niveau de droits."""
    level: int
    name: str
    description: str
    color: str
    permissions: List[str]
    examples: List[str]
    user_count: int = 0


async def _get_users_from_db(session: AsyncSession, level: Optional[int] = None) -> List[Dict[str, Any]]:
    """Recupere les utilisateurs depuis gateway_users avec leur permission_level."""
    query = """
        SELECT id, username, full_name, email, permission_level, created_at
        FROM gateway_users
        WHERE is_active = true
    """
    params = {}

    if level is not None:
        query += " AND permission_level = :level"
        params["level"] = level

    query += " ORDER BY permission_level DESC, username ASC"

    result = await session.execute(text(query), params)
    rows = result.fetchall()

    users = []
    for row in rows:
        users.append({
            "user_id": str(row[0]),
            "username": row[1] or "",
            "full_name": row[2] or row[1] or "",
            "email": row[3] or "",
            "level": row[4] if row[4] is not None else 1,
            "created_at": row[5].isoformat() if row[5] else ""
        })
    return users


@router.get("/levels", response_model=List[PermissionLevel])
async def get_permission_levels(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Recupere tous les niveaux de droits disponibles avec leur description.
    """
    users = await _get_users_from_db(session)

    levels = []
    for level_num, level_info in PERMISSION_LEVELS.items():
        user_count = len([u for u in users if u["level"] == level_num])
        levels.append(PermissionLevel(
            level=level_num,
            name=level_info["name"],
            description=level_info["description"],
            color=level_info["color"],
            permissions=level_info["permissions"],
            examples=level_info["examples"],
            user_count=user_count
        ))

    return levels


@router.get("/users", response_model=List[UserPermission])
async def get_users_permissions(
    level: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Liste tous les utilisateurs avec leurs niveaux de droits.
    Filtrable par niveau.
    """
    users = await _get_users_from_db(session, level=level)

    result = []
    for user in users:
        perm_level = user["level"]
        if perm_level < 1 or perm_level > 5:
            perm_level = 1

        level_info = PERMISSION_LEVELS[perm_level]
        result.append(UserPermission(
            user_id=user["user_id"],
            username=user["username"],
            full_name=user["full_name"],
            department="",
            level=perm_level,
            level_name=level_info["name"],
            permissions=level_info["permissions"],
            assigned_by="system",
            assigned_at=user["created_at"]
        ))

    return result


@router.get("/users/{user_id}", response_model=UserPermission)
async def get_user_permission(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Recupere les droits d'un utilisateur specifique.
    """
    result = await session.execute(text("""
        SELECT id, username, full_name, email, permission_level, created_at
        FROM gateway_users
        WHERE (CAST(id AS TEXT) = :uid OR username = :uid)
        AND is_active = true
    """), {"uid": user_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")

    perm_level = row[4] if row[4] is not None else 1
    if perm_level < 1 or perm_level > 5:
        perm_level = 1

    level_info = PERMISSION_LEVELS[perm_level]
    return UserPermission(
        user_id=str(row[0]),
        username=row[1] or "",
        full_name=row[2] or row[1] or "",
        department="",
        level=perm_level,
        level_name=level_info["name"],
        permissions=level_info["permissions"],
        assigned_by="system",
        assigned_at=row[5].isoformat() if row[5] else ""
    )


@router.post("/assign", response_model=Dict[str, Any])
async def assign_permission_level(
    assignment: PermissionAssignment,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"])),
    session: AsyncSession = Depends(get_session)
):
    """
    Assigne un niveau de droits a un utilisateur.
    Necessite les droits admin ou iam_engineer.
    Persiste dans la table gateway_users.
    """
    if assignment.level < 1 or assignment.level > 5:
        raise HTTPException(status_code=400, detail="Le niveau doit etre entre 1 et 5")

    # Recuperer le niveau actuel
    result = await session.execute(text("""
        SELECT id, username, permission_level
        FROM gateway_users
        WHERE (CAST(id AS TEXT) = :uid OR username = :uid)
        AND is_active = true
    """), {"uid": assignment.user_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")

    old_level = row[2] if row[2] is not None else 1
    user_id_db = str(row[0])
    username = row[1]

    # Mettre a jour en base
    await session.execute(text("""
        UPDATE gateway_users
        SET permission_level = :level
        WHERE id = CAST(:uid AS UUID)
    """), {"level": assignment.level, "uid": user_id_db})
    await session.commit()

    # Log audit
    memory_store.add_audit_log({
        "type": "permission_change",
        "action": "assign_level",
        "user_id": user_id_db,
        "username": username,
        "old_level": old_level,
        "new_level": assignment.level,
        "reason": assignment.reason,
        "actor": current_user.get("username", current_user.get("sub", "system"))
    })

    logger.info(
        "Permission level assigned",
        user_id=user_id_db,
        username=username,
        old_level=old_level,
        new_level=assignment.level,
        by=current_user.get("username", "system")
    )

    return {
        "status": "success",
        "message": f"Niveau {assignment.level} assigne a {username}",
        "old_level": old_level,
        "new_level": assignment.level
    }


@router.get("/stats", response_model=Dict[str, Any])
async def get_permissions_stats(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Statistiques sur la distribution des niveaux de droits.
    """
    users = await _get_users_from_db(session)

    level_counts = {i: 0 for i in range(1, 6)}
    for user in users:
        lvl = user["level"]
        if 1 <= lvl <= 5:
            level_counts[lvl] += 1

    total = len(users)

    return {
        "total_users": total,
        "by_level": [
            {
                "level": level,
                "name": PERMISSION_LEVELS[level]["name"],
                "count": count,
                "percentage": round(count / total * 100, 1) if total > 0 else 0,
                "color": PERMISSION_LEVELS[level]["color"]
            }
            for level, count in level_counts.items()
        ]
    }


@router.get("/check/{user_id}/{permission}")
async def check_user_permission(
    user_id: str,
    permission: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Verifie si un utilisateur a une permission specifique.
    """
    result = await session.execute(text("""
        SELECT id, username, permission_level
        FROM gateway_users
        WHERE (CAST(id AS TEXT) = :uid OR username = :uid)
        AND is_active = true
    """), {"uid": user_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")

    perm_level = row[2] if row[2] is not None else 1
    if perm_level < 1 or perm_level > 5:
        perm_level = 1

    level_info = PERMISSION_LEVELS[perm_level]
    has_permission = permission in level_info["permissions"]

    return {
        "user_id": str(row[0]),
        "permission": permission,
        "has_permission": has_permission,
        "user_level": perm_level,
        "level_name": level_info["name"]
    }
