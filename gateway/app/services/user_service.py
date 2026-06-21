"""
Service de gestion des utilisateurs Gateway.
Permet de recuperer les utilisateurs par role pour les workflows d'approbation.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.core.security import get_password_hash_async

logger = structlog.get_logger()


class UserService:
    """Service pour gerer les utilisateurs Gateway."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        Recupere tous les utilisateurs actifs ayant un role specifique.

        Args:
            role: Le nom du role (ex: 'manager', 'rh_manager', 'it_admin')

        Returns:
            Liste des utilisateurs avec ce role
        """
        try:
            # Chercher dans le champ 'roles' (JSONB array) et aussi dans 'role' (string legacy)
            # Note: On utilise cast() pour le JSONB car ::jsonb interfere avec les parametres
            role_json = f'["{role}"]'
            result = await self.session.execute(text("""
                SELECT id, username, email, full_name, role, roles
                FROM gateway_users
                WHERE is_active = true
                AND (
                    role = :role
                    OR roles @> cast(:role_json as jsonb)
                )
                ORDER BY username
            """), {
                "role": role,
                "role_json": role_json
            })

            rows = result.fetchall()
            users = []
            for row in rows:
                users.append({
                    "id": str(row[0]),
                    "username": row[1],
                    "email": row[2],
                    "full_name": row[3],
                    "role": row[4],
                    "roles": row[5] or []
                })

            return users

        except Exception as e:
            logger.error("Failed to get users by role", role=role, error=str(e))
            return []

    async def get_emails_by_role(self, role: str) -> List[str]:
        """
        Recupere les emails de tous les utilisateurs ayant un role specifique.

        Args:
            role: Le nom du role

        Returns:
            Liste des adresses email
        """
        users = await self.get_users_by_role(role)
        return [u["email"] for u in users if u.get("email")]

    async def get_approval_chain_emails(self, workflow_type: str = "full") -> Dict[str, List[str]]:
        """
        Recupere les emails pour chaque niveau d'approbation selon le type de workflow.

        Args:
            workflow_type: 'full', 'manager_only', ou 'rh_it'

        Returns:
            Dict avec les emails par niveau: {1: [...], 2: [...], 3: [...]}
        """
        chain = {}

        if workflow_type == "full":
            # Manager -> RH -> IT Admin
            chain[1] = await self.get_emails_by_role("manager")
            chain[2] = await self.get_emails_by_role("rh_manager")
            chain[3] = await self.get_emails_by_role("it_admin")
        elif workflow_type == "manager_only":
            # Manager uniquement
            chain[1] = await self.get_emails_by_role("manager")
        elif workflow_type == "rh_it":
            # RH -> IT Admin
            chain[1] = await self.get_emails_by_role("rh_manager")
            chain[2] = await self.get_emails_by_role("it_admin")

        return chain

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = None,
        roles: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Cree un nouvel utilisateur Gateway.

        Args:
            username: Nom d'utilisateur unique
            email: Adresse email unique
            password: Mot de passe en clair (sera hashe)
            full_name: Nom complet
            roles: Liste des roles

        Returns:
            L'utilisateur cree ou None si erreur
        """
        try:
            # Hash du mot de passe (hors de la boucle d'evenements - bcrypt bloque)
            password_hash = await get_password_hash_async(password)

            # Role principal = premier role de la liste
            primary_role = roles[0] if roles else "viewer"

            result = await self.session.execute(text("""
                INSERT INTO gateway_users (username, email, password_hash, full_name, role, roles)
                VALUES (:username, :email, :password_hash, :full_name, :role, :roles::jsonb)
                RETURNING id, username, email, full_name, role, roles, created_at
            """), {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "full_name": full_name or username,
                "role": primary_role,
                "roles": str(roles or []).replace("'", '"')
            })

            row = result.fetchone()
            await self.session.commit()

            if row:
                return {
                    "id": str(row[0]),
                    "username": row[1],
                    "email": row[2],
                    "full_name": row[3],
                    "role": row[4],
                    "roles": row[5] or [],
                    "created_at": row[6].isoformat() if row[6] else None
                }
            return None

        except Exception as e:
            logger.error("Failed to create user", username=username, error=str(e))
            await self.session.rollback()
            return None

    async def update_user_roles(self, username: str, roles: List[str]) -> bool:
        """
        Met a jour les roles d'un utilisateur.

        Args:
            username: Nom d'utilisateur
            roles: Nouvelle liste de roles

        Returns:
            True si mis a jour, False sinon
        """
        try:
            primary_role = roles[0] if roles else "viewer"

            result = await self.session.execute(text("""
                UPDATE gateway_users
                SET roles = :roles::jsonb,
                    role = :role
                WHERE username = :username
                RETURNING id
            """), {
                "username": username,
                "role": primary_role,
                "roles": str(roles).replace("'", '"')
            })

            await self.session.commit()
            return result.fetchone() is not None

        except Exception as e:
            logger.error("Failed to update user roles", username=username, error=str(e))
            await self.session.rollback()
            return False

    async def list_all_users(self) -> List[Dict[str, Any]]:
        """Liste tous les utilisateurs actifs."""
        try:
            result = await self.session.execute(text("""
                SELECT id, username, email, full_name, role, roles, is_active, created_at, last_login
                FROM gateway_users
                ORDER BY username
            """))

            rows = result.fetchall()
            users = []
            for row in rows:
                users.append({
                    "id": str(row[0]),
                    "username": row[1],
                    "email": row[2],
                    "full_name": row[3],
                    "role": row[4],
                    "roles": row[5] or [],
                    "is_active": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "last_login": row[8].isoformat() if row[8] else None
                })

            return users

        except Exception as e:
            logger.error("Failed to list users", error=str(e))
            return []

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Recupere un utilisateur par son nom d'utilisateur."""
        try:
            result = await self.session.execute(text("""
                SELECT id, username, email, full_name, role, roles, is_active, password_hash
                FROM gateway_users
                WHERE username = :username
            """), {"username": username})

            row = result.fetchone()
            if row:
                return {
                    "id": str(row[0]),
                    "username": row[1],
                    "email": row[2],
                    "full_name": row[3],
                    "role": row[4],
                    "roles": row[5] or [],
                    "is_active": row[6],
                    "password_hash": row[7]
                }
            return None

        except Exception as e:
            logger.error("Failed to get user", username=username, error=str(e))
            return None

    async def delete_user(self, username: str) -> bool:
        """Supprime (desactive) un utilisateur."""
        try:
            result = await self.session.execute(text("""
                UPDATE gateway_users
                SET is_active = false
                WHERE username = :username
                RETURNING id
            """), {"username": username})

            await self.session.commit()
            return result.fetchone() is not None

        except Exception as e:
            logger.error("Failed to delete user", username=username, error=str(e))
            await self.session.rollback()
            return False


# Liste des roles d'approbation disponibles (pour la chaine d'approbation)
APPROVAL_ROLES = {
    "manager": {
        "display_name": "Manager",
        "description": "Responsable hierarchique - Premier niveau d'approbation",
        "level": 1,
        "category": "approval"
    },
    "rh_manager": {
        "display_name": "Responsable RH",
        "description": "Gestionnaire des ressources humaines - Deuxieme niveau",
        "level": 2,
        "category": "approval"
    },
    "it_admin": {
        "display_name": "Administrateur IT",
        "description": "Administrateur technique - Dernier niveau d'approbation",
        "level": 3,
        "category": "approval"
    },
    "security_officer": {
        "display_name": "Responsable Securite",
        "description": "Pour les comptes a privilege eleve",
        "level": 2,
        "category": "approval"
    }
}

# Liste des roles d'acces a l'application Gateway
ACCESS_ROLES = {
    "admin": {
        "display_name": "Administrateur",
        "description": "Acces complet a toutes les fonctionnalites",
        "level": 0,
        "category": "access"
    },
    "iam_engineer": {
        "display_name": "Ingenieur IAM",
        "description": "Gestion des identites et des acces",
        "level": 0,
        "category": "access"
    },
    "director": {
        "display_name": "Directeur",
        "description": "Vision strategique et supervision",
        "level": 0,
        "category": "access"
    },
    "viewer": {
        "display_name": "Lecteur",
        "description": "Consultation uniquement, aucune modification",
        "level": 0,
        "category": "access"
    }
}

# Tous les roles combines
ALL_ROLES = {**ACCESS_ROLES, **APPROVAL_ROLES}
