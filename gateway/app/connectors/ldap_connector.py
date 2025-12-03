"""
Connecteur LDAP/Active Directory
"""
from typing import Dict, Any, Optional, List
from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE
import structlog

from app.connectors.base import BaseConnector
from app.core.config import settings

logger = structlog.get_logger()


class LDAPConnector(BaseConnector):
    """
    Connecteur pour LDAP et Active Directory.

    Supporte:
    - Creation/modification/suppression de comptes
    - Gestion des groupes
    - Recherche d'utilisateurs
    """

    def __init__(self):
        super().__init__()
        self.server = Server(
            settings.LDAP_HOST,
            port=settings.LDAP_PORT,
            get_info=ALL
        )
        self.bind_dn = settings.LDAP_BIND_DN
        self.bind_password = settings.LDAP_BIND_PASSWORD
        self.base_dn = settings.LDAP_BASE_DN
        self.users_ou = f"ou=users,{self.base_dn}"
        self.groups_ou = f"ou=groups,{self.base_dn}"

    def _get_connection(self) -> Connection:
        """Get LDAP connection."""
        conn = Connection(
            self.server,
            user=self.bind_dn,
            password=self.bind_password,
            auto_bind=True
        )
        return conn

    async def test_connection(self) -> bool:
        """Test LDAP connectivity."""
        try:
            conn = self._get_connection()
            result = conn.bind()
            conn.unbind()
            return result
        except Exception as e:
            logger.error("LDAP connection test failed", error=str(e))
            return False

    async def create_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create LDAP user account."""
        conn = self._get_connection()

        try:
            dn = f"uid={attributes.get('uid', account_id)},{self.users_ou}"

            # Build LDAP attributes
            ldap_attrs = {
                'objectClass': ['inetOrgPerson', 'organizationalPerson', 'person', 'top'],
                'uid': attributes.get('uid', account_id),
                'cn': attributes.get('cn', f"{attributes.get('firstname', '')} {attributes.get('lastname', '')}".strip()),
                'sn': attributes.get('sn', attributes.get('lastname', account_id)),
                'givenName': attributes.get('givenName', attributes.get('firstname', '')),
            }

            # Add optional attributes
            if attributes.get('mail'):
                ldap_attrs['mail'] = attributes['mail']
            if attributes.get('userPassword'):
                ldap_attrs['userPassword'] = attributes['userPassword']
            if attributes.get('employeeNumber'):
                ldap_attrs['employeeNumber'] = attributes['employeeNumber']
            if attributes.get('departmentNumber'):
                ldap_attrs['departmentNumber'] = attributes['departmentNumber']

            result = conn.add(dn, attributes=ldap_attrs)

            if result:
                logger.info("LDAP account created", uid=ldap_attrs['uid'], dn=dn)
                return {
                    "dn": dn,
                    "uid": ldap_attrs['uid'],
                    "status": "created"
                }
            else:
                raise Exception(f"Failed to create LDAP account: {conn.result}")

        finally:
            conn.unbind()

    async def update_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update LDAP user account."""
        conn = self._get_connection()

        try:
            # Find user DN
            dn = await self._find_user_dn(account_id, conn)
            if not dn:
                raise Exception(f"User {account_id} not found")

            # Build modifications
            changes = {}
            attr_mapping = {
                'cn': 'cn',
                'firstname': 'givenName',
                'lastname': 'sn',
                'mail': 'mail',
                'email': 'mail',
                'employeeNumber': 'employeeNumber',
                'department': 'departmentNumber'
            }

            for key, value in attributes.items():
                ldap_attr = attr_mapping.get(key, key)
                if value is not None:
                    changes[ldap_attr] = [(MODIFY_REPLACE, [value])]

            if changes:
                result = conn.modify(dn, changes)
                if not result:
                    raise Exception(f"Failed to update: {conn.result}")

            logger.info("LDAP account updated", uid=account_id)
            return {"dn": dn, "status": "updated"}

        finally:
            conn.unbind()

    async def delete_account(self, account_id: str) -> bool:
        """Delete LDAP user account."""
        conn = self._get_connection()

        try:
            dn = await self._find_user_dn(account_id, conn)
            if not dn:
                logger.warning("User not found for deletion", uid=account_id)
                return True  # Consider success if not found

            result = conn.delete(dn)
            if result:
                logger.info("LDAP account deleted", uid=account_id)
                return True
            else:
                raise Exception(f"Failed to delete: {conn.result}")

        finally:
            conn.unbind()

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get LDAP user account."""
        conn = self._get_connection()

        try:
            conn.search(
                search_base=self.users_ou,
                search_filter=f"(uid={account_id})",
                search_scope=SUBTREE,
                attributes=['*']
            )

            if conn.entries:
                entry = conn.entries[0]
                return {
                    "dn": str(entry.entry_dn),
                    "uid": str(entry.uid) if hasattr(entry, 'uid') else None,
                    "cn": str(entry.cn) if hasattr(entry, 'cn') else None,
                    "givenName": str(entry.givenName) if hasattr(entry, 'givenName') else None,
                    "sn": str(entry.sn) if hasattr(entry, 'sn') else None,
                    "mail": str(entry.mail) if hasattr(entry, 'mail') else None,
                }
            return None

        finally:
            conn.unbind()

    async def list_accounts(self) -> List[Dict[str, Any]]:
        """List all LDAP user accounts."""
        conn = self._get_connection()

        try:
            conn.search(
                search_base=self.users_ou,
                search_filter="(objectClass=inetOrgPerson)",
                search_scope=SUBTREE,
                attributes=['uid', 'cn', 'mail', 'givenName', 'sn']
            )

            accounts = []
            for entry in conn.entries:
                accounts.append({
                    "id": str(entry.uid) if hasattr(entry, 'uid') else None,
                    "uid": str(entry.uid) if hasattr(entry, 'uid') else None,
                    "cn": str(entry.cn) if hasattr(entry, 'cn') else None,
                    "mail": str(entry.mail) if hasattr(entry, 'mail') else None,
                })

            return accounts

        finally:
            conn.unbind()

    async def disable_account(self, account_id: str) -> bool:
        """Disable LDAP account (AD specific or custom attribute)."""
        # For OpenLDAP, we might use a custom attribute
        # For AD, we would modify userAccountControl
        return await self.update_account(account_id, {"employeeType": "disabled"})

    async def enable_account(self, account_id: str) -> bool:
        """Enable LDAP account."""
        return await self.update_account(account_id, {"employeeType": "active"})

    async def add_to_group(self, account_id: str, group_id: str) -> bool:
        """Add user to LDAP group."""
        conn = self._get_connection()

        try:
            user_dn = await self._find_user_dn(account_id, conn)
            if not user_dn:
                raise Exception(f"User {account_id} not found")

            group_dn = f"cn={group_id},{self.groups_ou}"

            result = conn.modify(
                group_dn,
                {'member': [(MODIFY_ADD, [user_dn])]}
            )

            if result:
                logger.info("User added to group", user=account_id, group=group_id)
                return True
            else:
                raise Exception(f"Failed to add to group: {conn.result}")

        finally:
            conn.unbind()

    async def remove_from_group(self, account_id: str, group_id: str) -> bool:
        """Remove user from LDAP group."""
        conn = self._get_connection()

        try:
            user_dn = await self._find_user_dn(account_id, conn)
            if not user_dn:
                raise Exception(f"User {account_id} not found")

            group_dn = f"cn={group_id},{self.groups_ou}"

            result = conn.modify(
                group_dn,
                {'member': [(MODIFY_DELETE, [user_dn])]}
            )

            if result:
                logger.info("User removed from group", user=account_id, group=group_id)
                return True
            else:
                raise Exception(f"Failed to remove from group: {conn.result}")

        finally:
            conn.unbind()

    async def get_groups(self, account_id: str) -> List[str]:
        """Get groups for a user."""
        conn = self._get_connection()

        try:
            user_dn = await self._find_user_dn(account_id, conn)
            if not user_dn:
                return []

            conn.search(
                search_base=self.groups_ou,
                search_filter=f"(member={user_dn})",
                search_scope=SUBTREE,
                attributes=['cn']
            )

            return [str(entry.cn) for entry in conn.entries]

        finally:
            conn.unbind()

    async def _find_user_dn(self, account_id: str, conn: Connection) -> Optional[str]:
        """Find user DN by uid."""
        conn.search(
            search_base=self.users_ou,
            search_filter=f"(uid={account_id})",
            search_scope=SUBTREE,
            attributes=['dn']
        )

        if conn.entries:
            return str(conn.entries[0].entry_dn)
        return None
