"""
API de gestion des niveaux de droits (1-5)
Systeme de permissions hierarchique pour les utilisateurs
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import structlog

from app.core.security import get_current_user, require_role
from app.core.memory_store import memory_store

router = APIRouter()
logger = structlog.get_logger()


# Definition des niveaux de droits
PERMISSION_LEVELS = {
    1: {
        "name": "Visiteur",
        "description": "Acces minimal - Consultation uniquement",
        "color": "#6b7280",  # gray
        "permissions": [
            "view_dashboard",
            "view_own_profile"
        ],
        "examples": ["Stagiaire", "Visiteur externe", "Consultant temporaire"]
    },
    2: {
        "name": "Utilisateur",
        "description": "Acces standard - Consultation et actions basiques",
        "color": "#3b82f6",  # blue
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
        "color": "#10b981",  # green
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
        "color": "#f59e0b",  # amber
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
        "color": "#8b5cf6",  # purple
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


# Donnees demo des utilisateurs avec leurs niveaux
def _init_demo_permissions():
    """Initialise les permissions demo."""
    demo_users = [
        # Niveau 1 - Visiteurs
        {"user_id": "stage001", "username": "lucas.stagiaire", "full_name": "Lucas Martin", "department": "IT", "level": 1},
        {"user_id": "visit001", "username": "marie.visiteur", "full_name": "Marie Dupont", "department": "External", "level": 1},

        # Niveau 2 - Utilisateurs
        {"user_id": "emp001", "username": "jean.dupont", "full_name": "Jean Dupont", "department": "IT", "level": 2},
        {"user_id": "emp002", "username": "sophie.petit", "full_name": "Sophie Petit", "department": "IT", "level": 2},
        {"user_id": "emp003", "username": "hugo.durand", "full_name": "Hugo Durand", "department": "IT", "level": 2},
        {"user_id": "emp004", "username": "marie.martin", "full_name": "Marie Martin", "department": "HR", "level": 2},
        {"user_id": "emp005", "username": "pierre.bernard", "full_name": "Pierre Bernard", "department": "Finance", "level": 2},
        {"user_id": "emp006", "username": "emma.richard", "full_name": "Emma Richard", "department": "Marketing", "level": 2},
        {"user_id": "emp007", "username": "lucas.robert", "full_name": "Lucas Robert", "department": "Sales", "level": 2},
        {"user_id": "emp008", "username": "camille.simon", "full_name": "Camille Simon", "department": "R&D", "level": 2},

        # Niveau 3 - Operateurs
        {"user_id": "op001", "username": "antoine.girard", "full_name": "Antoine Girard", "department": "IT", "level": 3},
        {"user_id": "op002", "username": "lea.leroy", "full_name": "Lea Leroy", "department": "HR", "level": 3},
        {"user_id": "op003", "username": "thomas.moreau", "full_name": "Thomas Moreau", "department": "Finance", "level": 3},
        {"user_id": "op004", "username": "charlotte.morel", "full_name": "Charlotte Morel", "department": "Marketing", "level": 3},

        # Niveau 4 - Managers
        {"user_id": "mgr001", "username": "julie.moreau", "full_name": "Julie Moreau", "department": "IT", "level": 4},
        {"user_id": "mgr002", "username": "claire.bonnet", "full_name": "Claire Bonnet", "department": "HR", "level": 4},
        {"user_id": "mgr003", "username": "philippe.mercier", "full_name": "Philippe Mercier", "department": "Finance", "level": 4},
        {"user_id": "mgr004", "username": "maxime.faure", "full_name": "Maxime Faure", "department": "Sales", "level": 4},

        # Niveau 5 - Chefs de departement
        {"user_id": "dir001", "username": "nicolas.leroux", "full_name": "Nicolas Leroux", "department": "IT", "level": 5},
        {"user_id": "dir002", "username": "nathalie.fournier", "full_name": "Nathalie Fournier", "department": "HR", "level": 5},
        {"user_id": "dir003", "username": "christine.roux", "full_name": "Christine Roux", "department": "Finance", "level": 5},
        {"user_id": "dir004", "username": "alexandre.laurent", "full_name": "Alexandre Laurent", "department": "Sales", "level": 5},
        {"user_id": "dir005", "username": "sebastien.morin", "full_name": "Sebastien Morin", "department": "R&D", "level": 5},
    ]

    return demo_users


# Cache pour les permissions
_permissions_cache = None

def get_permissions_cache():
    global _permissions_cache
    if _permissions_cache is None:
        _permissions_cache = _init_demo_permissions()
    return _permissions_cache


@router.get("/levels", response_model=List[PermissionLevel])
async def get_permission_levels(
    current_user: dict = Depends(get_current_user)
):
    """
    Recupere tous les niveaux de droits disponibles avec leur description.
    """
    users = get_permissions_cache()

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
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Liste tous les utilisateurs avec leurs niveaux de droits.
    Filtrable par niveau et/ou departement.
    """
    users = get_permissions_cache()

    result = []
    for user in users:
        # Filtres
        if level is not None and user["level"] != level:
            continue
        if department is not None and user["department"].lower() != department.lower():
            continue

        level_info = PERMISSION_LEVELS[user["level"]]
        result.append(UserPermission(
            user_id=user["user_id"],
            username=user["username"],
            full_name=user["full_name"],
            department=user["department"],
            level=user["level"],
            level_name=level_info["name"],
            permissions=level_info["permissions"],
            assigned_by="admin",
            assigned_at="2024-01-15T10:00:00"
        ))

    return result


@router.get("/users/{user_id}", response_model=UserPermission)
async def get_user_permission(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Recupere les droits d'un utilisateur specifique.
    """
    users = get_permissions_cache()

    for user in users:
        if user["user_id"] == user_id or user["username"] == user_id:
            level_info = PERMISSION_LEVELS[user["level"]]
            return UserPermission(
                user_id=user["user_id"],
                username=user["username"],
                full_name=user["full_name"],
                department=user["department"],
                level=user["level"],
                level_name=level_info["name"],
                permissions=level_info["permissions"],
                assigned_by="admin",
                assigned_at="2024-01-15T10:00:00"
            )

    raise HTTPException(status_code=404, detail="Utilisateur non trouve")


@router.post("/assign", response_model=Dict[str, Any])
async def assign_permission_level(
    assignment: PermissionAssignment,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Assigne un niveau de droits a un utilisateur.
    Necessite les droits admin ou iam_engineer.
    """
    if assignment.level < 1 or assignment.level > 5:
        raise HTTPException(status_code=400, detail="Le niveau doit etre entre 1 et 5")

    users = get_permissions_cache()

    for user in users:
        if user["user_id"] == assignment.user_id:
            old_level = user["level"]
            user["level"] = assignment.level

            # Log audit
            memory_store.add_audit_log({
                "type": "permission_change",
                "action": "assign_level",
                "user_id": assignment.user_id,
                "old_level": old_level,
                "new_level": assignment.level,
                "reason": assignment.reason,
                "actor": current_user["username"]
            })

            logger.info(
                "Permission level assigned",
                user_id=assignment.user_id,
                old_level=old_level,
                new_level=assignment.level,
                by=current_user["username"]
            )

            return {
                "status": "success",
                "message": f"Niveau {assignment.level} assigne a {assignment.user_id}",
                "old_level": old_level,
                "new_level": assignment.level
            }

    raise HTTPException(status_code=404, detail="Utilisateur non trouve")


@router.get("/stats", response_model=Dict[str, Any])
async def get_permissions_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Statistiques sur la distribution des niveaux de droits.
    """
    users = get_permissions_cache()

    # Comptage par niveau
    level_counts = {i: 0 for i in range(1, 6)}
    dept_counts = {}

    for user in users:
        level_counts[user["level"]] += 1
        dept = user["department"]
        if dept not in dept_counts:
            dept_counts[dept] = {i: 0 for i in range(1, 6)}
        dept_counts[dept][user["level"]] += 1

    return {
        "total_users": len(users),
        "by_level": [
            {
                "level": level,
                "name": PERMISSION_LEVELS[level]["name"],
                "count": count,
                "percentage": round(count / len(users) * 100, 1) if users else 0,
                "color": PERMISSION_LEVELS[level]["color"]
            }
            for level, count in level_counts.items()
        ],
        "by_department": [
            {
                "department": dept,
                "levels": levels,
                "total": sum(levels.values())
            }
            for dept, levels in dept_counts.items()
        ]
    }


@router.get("/check/{user_id}/{permission}")
async def check_user_permission(
    user_id: str,
    permission: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Verifie si un utilisateur a une permission specifique.
    """
    users = get_permissions_cache()

    for user in users:
        if user["user_id"] == user_id or user["username"] == user_id:
            level_info = PERMISSION_LEVELS[user["level"]]
            has_permission = permission in level_info["permissions"]

            return {
                "user_id": user_id,
                "permission": permission,
                "has_permission": has_permission,
                "user_level": user["level"],
                "level_name": level_info["name"]
            }

    raise HTTPException(status_code=404, detail="Utilisateur non trouve")
