"""
Connecteur Odoo via XML-RPC
"""
from typing import Dict, Any, Optional, List
import xmlrpc.client
import structlog

from app.connectors.base import BaseConnector
from app.core.config import settings

logger = structlog.get_logger()


class OdooConnector(BaseConnector):
    """
    Connecteur pour Odoo ERP via XML-RPC.

    Supporte:
    - Creation/modification/suppression d'utilisateurs
    - Gestion des contacts (res.partner)
    - Gestion des groupes d'acces
    """

    def __init__(self):
        super().__init__()
        self.url = settings.ODOO_URL
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USER
        self.password = settings.ODOO_PASSWORD
        self._uid = None

    def _authenticate(self) -> int:
        """Authenticate with Odoo and get user ID."""
        if self._uid:
            return self._uid

        common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self._uid = common.authenticate(self.db, self.username, self.password, {})

        if not self._uid:
            raise Exception("Odoo authentication failed")

        return self._uid

    def _get_models(self):
        """Get Odoo models proxy."""
        return xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

    def _execute(self, model: str, method: str, *args):
        """Execute Odoo RPC call."""
        uid = self._authenticate()
        models = self._get_models()
        return models.execute_kw(
            self.db, uid, self.password,
            model, method, list(args)
        )

    async def test_connection(self) -> bool:
        """Test Odoo connectivity."""
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            version = common.version()
            logger.info("Odoo connected", version=version.get('server_version'))
            return True
        except Exception as e:
            logger.error("Odoo connection test failed", error=str(e))
            return False

    async def create_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Odoo user account."""
        try:
            # First create a contact (res.partner)
            partner_data = {
                'name': f"{attributes.get('firstname', '')} {attributes.get('lastname', '')}".strip() or account_id,
                'email': attributes.get('email') or attributes.get('login'),
                'phone': attributes.get('phone'),
                'is_company': False,
            }

            partner_id = self._execute('res.partner', 'create', [partner_data])

            # Then create user linked to partner
            user_data = {
                'name': partner_data['name'],
                'login': attributes.get('login') or attributes.get('email') or account_id,
                'partner_id': partner_id,
                'active': attributes.get('active', True),
            }

            # Add groups if specified
            if attributes.get('groups'):
                user_data['groups_id'] = [(6, 0, attributes['groups'])]

            user_id = self._execute('res.users', 'create', [user_data])

            logger.info("Odoo account created", user_id=user_id, login=user_data['login'])

            return {
                "id": user_id,
                "partner_id": partner_id,
                "login": user_data['login'],
                "status": "created"
            }

        except Exception as e:
            logger.error("Failed to create Odoo account", error=str(e))
            raise

    async def update_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update Odoo user account."""
        try:
            # Find user by login
            user = await self.get_account(account_id)
            if not user:
                raise Exception(f"User {account_id} not found in Odoo")

            user_id = user['id']
            update_data = {}

            # Map attributes
            if 'firstname' in attributes or 'lastname' in attributes:
                name = f"{attributes.get('firstname', '')} {attributes.get('lastname', '')}".strip()
                if name:
                    update_data['name'] = name

            if 'email' in attributes:
                update_data['login'] = attributes['email']

            if 'active' in attributes:
                update_data['active'] = attributes['active']

            if update_data:
                self._execute('res.users', 'write', [[user_id], update_data])

            # Update partner if needed
            if user.get('partner_id') and ('email' in attributes or 'phone' in attributes):
                partner_data = {}
                if 'email' in attributes:
                    partner_data['email'] = attributes['email']
                if 'phone' in attributes:
                    partner_data['phone'] = attributes['phone']

                if partner_data:
                    self._execute('res.partner', 'write', [[user['partner_id']], partner_data])

            logger.info("Odoo account updated", user_id=user_id)
            return {"id": user_id, "status": "updated"}

        except Exception as e:
            logger.error("Failed to update Odoo account", error=str(e))
            raise

    async def delete_account(self, account_id: str) -> bool:
        """Delete Odoo user account."""
        try:
            user = await self.get_account(account_id)
            if not user:
                logger.warning("Odoo user not found for deletion", login=account_id)
                return True

            # Deactivate instead of delete (Odoo best practice)
            self._execute('res.users', 'write', [[user['id']], {'active': False}])

            logger.info("Odoo account deactivated", user_id=user['id'])
            return True

        except Exception as e:
            logger.error("Failed to delete Odoo account", error=str(e))
            return False

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get Odoo user account."""
        try:
            # Search by login or ID
            domain = ['|', ('login', '=', account_id), ('id', '=', int(account_id) if account_id.isdigit() else 0)]

            users = self._execute(
                'res.users', 'search_read',
                [domain],
                {'fields': ['id', 'name', 'login', 'email', 'active', 'partner_id', 'groups_id']}
            )

            if users:
                user = users[0]
                return {
                    "id": user['id'],
                    "name": user['name'],
                    "login": user['login'],
                    "email": user.get('email'),
                    "active": user['active'],
                    "partner_id": user['partner_id'][0] if user.get('partner_id') else None,
                    "groups": user.get('groups_id', [])
                }
            return None

        except Exception as e:
            logger.error("Failed to get Odoo account", error=str(e))
            return None

    async def list_accounts(self) -> List[Dict[str, Any]]:
        """List all Odoo user accounts."""
        try:
            users = self._execute(
                'res.users', 'search_read',
                [[]],
                {'fields': ['id', 'name', 'login', 'active']}
            )

            return [
                {
                    "id": u['id'],
                    "name": u['name'],
                    "login": u['login'],
                    "active": u['active']
                }
                for u in users
            ]

        except Exception as e:
            logger.error("Failed to list Odoo accounts", error=str(e))
            return []

    async def disable_account(self, account_id: str) -> bool:
        """Disable Odoo user account."""
        try:
            result = await self.update_account(account_id, {"active": False})
            return result.get("status") == "updated"
        except Exception:
            return False

    async def enable_account(self, account_id: str) -> bool:
        """Enable Odoo user account."""
        try:
            result = await self.update_account(account_id, {"active": True})
            return result.get("status") == "updated"
        except Exception:
            return False

    async def add_to_group(self, account_id: str, group_id: str) -> bool:
        """Add user to Odoo group."""
        try:
            user = await self.get_account(account_id)
            if not user:
                raise Exception(f"User {account_id} not found")

            # Add group (4 = add relation)
            self._execute(
                'res.users', 'write',
                [[user['id']], {'groups_id': [(4, int(group_id))]}]
            )

            logger.info("User added to Odoo group", user_id=user['id'], group_id=group_id)
            return True

        except Exception as e:
            logger.error("Failed to add user to group", error=str(e))
            return False

    async def remove_from_group(self, account_id: str, group_id: str) -> bool:
        """Remove user from Odoo group."""
        try:
            user = await self.get_account(account_id)
            if not user:
                raise Exception(f"User {account_id} not found")

            # Remove group (3 = remove relation)
            self._execute(
                'res.users', 'write',
                [[user['id']], {'groups_id': [(3, int(group_id))]}]
            )

            logger.info("User removed from Odoo group", user_id=user['id'], group_id=group_id)
            return True

        except Exception as e:
            logger.error("Failed to remove user from group", error=str(e))
            return False

    async def get_groups(self, account_id: str) -> List[str]:
        """Get groups for Odoo user."""
        try:
            user = await self.get_account(account_id)
            if user:
                return [str(g) for g in user.get('groups', [])]
            return []
        except Exception:
            return []

    async def get_available_groups(self) -> List[Dict[str, Any]]:
        """Get all available Odoo groups."""
        try:
            groups = self._execute(
                'res.groups', 'search_read',
                [[]],
                {'fields': ['id', 'name', 'full_name']}
            )
            return groups
        except Exception as e:
            logger.error("Failed to get Odoo groups", error=str(e))
            return []
