"""
Connecteur SQL pour bases de donnees relationnelles
"""
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Boolean, DateTime
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import structlog

from app.connectors.base import BaseConnector
from app.core.config import settings

logger = structlog.get_logger()


class SQLConnector(BaseConnector):
    """
    Connecteur pour bases de donnees SQL (PostgreSQL, MySQL, etc.)

    Supporte:
    - Creation/modification/suppression dans table users
    - Gestion des permissions via table droits
    """

    def __init__(self, connection_url: str = None):
        super().__init__()
        self.connection_url = connection_url or settings.INTRANET_DB_URL
        self.engine = create_engine(self.connection_url)
        self.metadata = MetaData()

        # Define expected table schemas
        self.users_table = Table(
            'users', self.metadata,
            Column('id', String, primary_key=True),
            Column('username', String, unique=True),
            Column('email', String),
            Column('first_name', String),
            Column('last_name', String),
            Column('password_hash', String),
            Column('role', String, default='APP_USER'),
            Column('is_active', Boolean, default=True),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow)
        )

        self.permissions_table = Table(
            'permissions', self.metadata,
            Column('id', String, primary_key=True),
            Column('user_id', String),
            Column('permission_name', String),
            Column('granted_at', DateTime, default=datetime.utcnow),
            Column('granted_by', String)
        )

    async def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error("SQL connection test failed", error=str(e))
            return False

    async def create_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create user in SQL database."""
        try:
            username = attributes.get("username", account_id)
            with self.engine.connect() as conn:
                # Check if user exists by username
                result = conn.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": username}
                )
                if result.fetchone():
                    raise Exception(f"User {username} already exists")

                # Insert user (id is auto-generated SERIAL)
                insert_sql = text("""
                    INSERT INTO users (username, email, first_name, last_name, department, is_active, created_at)
                    VALUES (:username, :email, :first_name, :last_name, :department, :is_active, :created_at)
                    RETURNING id
                """)

                result = conn.execute(insert_sql, {
                    "username": username,
                    "email": attributes.get("email"),
                    "first_name": attributes.get("firstname", attributes.get("first_name")),
                    "last_name": attributes.get("lastname", attributes.get("last_name")),
                    "department": attributes.get("department"),
                    "is_active": True,
                    "created_at": datetime.utcnow()
                })

                new_id = result.fetchone()[0]
                conn.commit()

                logger.info("SQL account created", id=new_id, username=username)
                return {
                    "id": new_id,
                    "username": username,
                    "status": "created"
                }

        except SQLAlchemyError as e:
            logger.error("Failed to create SQL account", error=str(e))
            raise

    async def update_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user in SQL database."""
        try:
            with self.engine.connect() as conn:
                # Build dynamic update
                set_clauses = []
                params = {"id": account_id}

                field_mapping = {
                    "email": "email",
                    "firstname": "first_name",
                    "lastname": "last_name",
                    "first_name": "first_name",
                    "last_name": "last_name",
                    "role": "role",
                    "is_active": "is_active"
                }

                for key, value in attributes.items():
                    if key in field_mapping and value is not None:
                        db_field = field_mapping[key]
                        set_clauses.append(f"{db_field} = :{db_field}")
                        params[db_field] = value

                if not set_clauses:
                    return {"id": account_id, "status": "no_changes"}

                set_clauses.append("updated_at = :updated_at")
                params["updated_at"] = datetime.utcnow()

                update_sql = text(f"""
                    UPDATE users SET {', '.join(set_clauses)}
                    WHERE id = :id
                """)

                result = conn.execute(update_sql, params)
                conn.commit()

                if result.rowcount == 0:
                    raise Exception(f"User {account_id} not found")

                logger.info("SQL account updated", id=account_id)
                return {"id": account_id, "status": "updated"}

        except SQLAlchemyError as e:
            logger.error("Failed to update SQL account", error=str(e))
            raise

    async def delete_account(self, account_id: str) -> bool:
        """Delete user from SQL database."""
        try:
            with self.engine.connect() as conn:
                # Delete permissions first
                conn.execute(
                    text("DELETE FROM permissions WHERE user_id = :id"),
                    {"id": account_id}
                )

                # Delete user
                result = conn.execute(
                    text("DELETE FROM users WHERE id = :id"),
                    {"id": account_id}
                )

                conn.commit()

                if result.rowcount > 0:
                    logger.info("SQL account deleted", id=account_id)
                    return True
                else:
                    logger.warning("SQL account not found for deletion", id=account_id)
                    return True

        except SQLAlchemyError as e:
            logger.error("Failed to delete SQL account", error=str(e))
            return False

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get user from SQL database."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM users WHERE id = :id"),
                    {"id": account_id}
                )

                row = result.fetchone()
                if row:
                    return dict(row._mapping)
                return None

        except SQLAlchemyError as e:
            logger.error("Failed to get SQL account", error=str(e))
            return None

    async def list_accounts(self) -> List[Dict[str, Any]]:
        """List all users from SQL database."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT id, username, email, first_name, last_name, role, is_active FROM users")
                )

                return [dict(row._mapping) for row in result]

        except SQLAlchemyError as e:
            logger.error("Failed to list SQL accounts", error=str(e))
            return []

    async def disable_account(self, account_id: str) -> bool:
        """Disable user account."""
        try:
            result = await self.update_account(account_id, {"is_active": False})
            return result.get("status") == "updated"
        except Exception:
            return False

    async def enable_account(self, account_id: str) -> bool:
        """Enable user account."""
        try:
            result = await self.update_account(account_id, {"is_active": True})
            return result.get("status") == "updated"
        except Exception:
            return False

    async def add_permission(
        self,
        account_id: str,
        permission: str,
        granted_by: str = "system"
    ) -> bool:
        """Add permission to user."""
        try:
            import uuid
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO permissions (id, user_id, permission_name, granted_at, granted_by)
                        VALUES (:id, :user_id, :permission, :granted_at, :granted_by)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "user_id": account_id,
                        "permission": permission,
                        "granted_at": datetime.utcnow(),
                        "granted_by": granted_by
                    }
                )
                conn.commit()

                logger.info("Permission added", user=account_id, permission=permission)
                return True

        except SQLAlchemyError as e:
            logger.error("Failed to add permission", error=str(e))
            return False

    async def remove_permission(
        self,
        account_id: str,
        permission: str
    ) -> bool:
        """Remove permission from user."""
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        DELETE FROM permissions
                        WHERE user_id = :user_id AND permission_name = :permission
                    """),
                    {"user_id": account_id, "permission": permission}
                )
                conn.commit()

                logger.info("Permission removed", user=account_id, permission=permission)
                return True

        except SQLAlchemyError as e:
            logger.error("Failed to remove permission", error=str(e))
            return False

    async def get_permissions(self, account_id: str) -> List[str]:
        """Get permissions for user."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT permission_name FROM permissions WHERE user_id = :id"),
                    {"id": account_id}
                )
                return [row[0] for row in result]

        except SQLAlchemyError as e:
            logger.error("Failed to get permissions", error=str(e))
            return []

    async def ensure_tables_exist(self):
        """Create tables if they don't exist."""
        try:
            self.metadata.create_all(self.engine)
            logger.info("SQL tables ensured")
        except SQLAlchemyError as e:
            logger.error("Failed to create tables", error=str(e))
