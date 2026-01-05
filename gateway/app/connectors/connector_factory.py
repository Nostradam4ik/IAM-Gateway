"""
Factory pour les connecteurs - Version dynamique
Charge les connecteurs depuis la base de donnees ou la configuration statique.
"""
from typing import Dict, Optional, Any
import structlog

from app.connectors.base import BaseConnector
from app.connectors.ldap_connector import LDAPConnector
from app.connectors.sql_connector import SQLConnector
from app.connectors.odoo_connector import OdooConnector
from app.connectors.midpoint_connector import MidPointConnector

logger = structlog.get_logger()


class DynamicConnector(BaseConnector):
    """
    Connecteur dynamique qui utilise une configuration chargee depuis la DB.
    """

    def __init__(self, name: str, connector_type: str, connector_subtype: str, config: Dict[str, Any]):
        self.name = name
        self.connector_type = connector_type
        self.connector_subtype = connector_subtype
        self.config = config
        self._connection = None

    async def provision(self, operation_type: str, user_data: dict) -> dict:
        """Provision basé sur le type de connecteur."""
        if self.connector_type == "sql":
            return await self._provision_sql(operation_type, user_data)
        elif self.connector_type == "ldap":
            return await self._provision_ldap(operation_type, user_data)
        elif self.connector_type == "rest":
            return await self._provision_rest(operation_type, user_data)
        elif self.connector_type == "erp":
            return await self._provision_erp(operation_type, user_data)
        else:
            raise NotImplementedError(f"Provisioning not implemented for type: {self.connector_type}")

    async def _provision_sql(self, operation_type: str, user_data: dict) -> dict:
        """Provision vers une base SQL dynamique."""
        import asyncpg

        conn = await self._get_sql_connection()
        try:
            if operation_type == "create":
                # Insert générique - peut être customisé via les règles
                columns = ", ".join(user_data.keys())
                placeholders = ", ".join(f"${i+1}" for i in range(len(user_data)))
                query = f"INSERT INTO users ({columns}) VALUES ({placeholders}) RETURNING id"
                result = await conn.fetchval(query, *user_data.values())
                return {"success": True, "id": result}
            elif operation_type == "update":
                user_id = user_data.pop("id", None)
                if not user_id:
                    return {"success": False, "error": "Missing user id"}
                sets = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(user_data.keys()))
                query = f"UPDATE users SET {sets} WHERE id = $1"
                await conn.execute(query, user_id, *user_data.values())
                return {"success": True, "updated": user_id}
            elif operation_type == "delete":
                user_id = user_data.get("id")
                await conn.execute("DELETE FROM users WHERE id = $1", user_id)
                return {"success": True, "deleted": user_id}
        finally:
            await conn.close()

        return {"success": False, "error": "Unknown operation"}

    async def _provision_ldap(self, operation_type: str, user_data: dict) -> dict:
        """Provision vers LDAP dynamique."""
        from ldap3 import Server, Connection, ALL, SUBTREE

        server = Server(
            self.config.get("host"),
            port=self.config.get("port", 389),
            use_ssl=self.config.get("use_ssl", False),
            get_info=ALL
        )

        conn = Connection(
            server,
            user=self.config.get("bind_dn"),
            password=self.config.get("bind_password"),
            auto_bind=True
        )

        try:
            base_dn = self.config.get("base_dn")
            users_ou = self.config.get("users_ou", "ou=users")

            if operation_type == "create":
                uid = user_data.get("uid") or user_data.get("username")
                dn = f"uid={uid},{users_ou},{base_dn}"

                attributes = {
                    "objectClass": ["inetOrgPerson", "posixAccount", "top"],
                    "cn": user_data.get("cn", f"{user_data.get('firstname', '')} {user_data.get('lastname', '')}"),
                    "sn": user_data.get("lastname", "Unknown"),
                    "uid": uid,
                    "uidNumber": str(user_data.get("uid_number", 10000)),
                    "gidNumber": str(user_data.get("gid_number", 10000)),
                    "homeDirectory": user_data.get("home_directory", f"/home/{uid}"),
                }

                if user_data.get("email"):
                    attributes["mail"] = user_data["email"]
                if user_data.get("firstname"):
                    attributes["givenName"] = user_data["firstname"]

                conn.add(dn, attributes=attributes)
                return {"success": conn.result["result"] == 0, "dn": dn}

            elif operation_type == "update":
                uid = user_data.get("uid") or user_data.get("username")
                dn = f"uid={uid},{users_ou},{base_dn}"

                changes = {}
                for key, value in user_data.items():
                    if key not in ["uid", "username"]:
                        changes[key] = [(MODIFY_REPLACE, [value])]

                if changes:
                    conn.modify(dn, changes)
                return {"success": True, "modified": dn}

            elif operation_type == "delete":
                uid = user_data.get("uid") or user_data.get("username")
                dn = f"uid={uid},{users_ou},{base_dn}"
                conn.delete(dn)
                return {"success": conn.result["result"] == 0, "deleted": dn}

        finally:
            conn.unbind()

        return {"success": False, "error": "Unknown operation"}

    async def _provision_rest(self, operation_type: str, user_data: dict) -> dict:
        """Provision vers API REST dynamique."""
        import httpx

        base_url = self.config.get("base_url")
        auth_type = self.config.get("auth_type", "none")

        headers = {"Content-Type": "application/json"}
        auth = None

        if auth_type == "basic":
            auth = (self.config.get("username"), self.config.get("password"))
        elif auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self.config.get('bearer_token')}"
        elif auth_type == "api_key":
            header_name = self.config.get("api_key_header", "X-API-Key")
            headers[header_name] = self.config.get("api_key")

        async with httpx.AsyncClient(verify=self.config.get("verify_ssl", True)) as client:
            if operation_type == "create":
                response = await client.post(f"{base_url}/users", json=user_data, headers=headers, auth=auth)
                return {"success": response.status_code in [200, 201], "response": response.json() if response.content else {}}
            elif operation_type == "update":
                user_id = user_data.pop("id", None)
                response = await client.put(f"{base_url}/users/{user_id}", json=user_data, headers=headers, auth=auth)
                return {"success": response.status_code == 200, "response": response.json() if response.content else {}}
            elif operation_type == "delete":
                user_id = user_data.get("id")
                response = await client.delete(f"{base_url}/users/{user_id}", headers=headers, auth=auth)
                return {"success": response.status_code in [200, 204]}

        return {"success": False, "error": "Unknown operation"}

    async def _provision_erp(self, operation_type: str, user_data: dict) -> dict:
        """Provision vers ERP (Odoo, SAP)."""
        if self.connector_subtype == "odoo":
            return await self._provision_odoo(operation_type, user_data)
        else:
            raise NotImplementedError(f"ERP subtype not implemented: {self.connector_subtype}")

    async def _provision_odoo(self, operation_type: str, user_data: dict) -> dict:
        """Provision vers Odoo."""
        import xmlrpc.client

        url = self.config.get("url")
        db = self.config.get("database")
        username = self.config.get("username")
        password = self.config.get("password")

        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})

        if not uid:
            return {"success": False, "error": "Authentication failed"}

        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        if operation_type == "create":
            partner_data = {
                "name": f"{user_data.get('firstname', '')} {user_data.get('lastname', '')}".strip(),
                "email": user_data.get("email"),
                "is_company": False,
            }
            partner_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [partner_data])
            return {"success": True, "partner_id": partner_id}

        elif operation_type == "update":
            partner_id = user_data.get("partner_id")
            partner_data = {k: v for k, v in user_data.items() if k != "partner_id"}
            models.execute_kw(db, uid, password, 'res.partner', 'write', [[partner_id], partner_data])
            return {"success": True, "updated": partner_id}

        elif operation_type == "delete":
            partner_id = user_data.get("partner_id")
            models.execute_kw(db, uid, password, 'res.partner', 'unlink', [[partner_id]])
            return {"success": True, "deleted": partner_id}

        return {"success": False, "error": "Unknown operation"}

    async def _get_sql_connection(self):
        """Crée une connexion SQL basée sur le subtype."""
        import asyncpg

        if self.connector_subtype in ["postgresql", "postgres"]:
            return await asyncpg.connect(
                host=self.config.get("host"),
                port=self.config.get("port", 5432),
                database=self.config.get("database"),
                user=self.config.get("username"),
                password=self.config.get("password"),
                ssl=self.config.get("ssl_mode", "prefer")
            )
        else:
            raise NotImplementedError(f"SQL subtype not yet implemented: {self.connector_subtype}")

    async def test_connection(self) -> bool:
        """Teste la connexion du connecteur dynamique."""
        try:
            if self.connector_type == "sql":
                conn = await self._get_sql_connection()
                await conn.execute("SELECT 1")
                await conn.close()
                return True

            elif self.connector_type == "ldap":
                from ldap3 import Server, Connection, ALL
                server = Server(
                    self.config.get("host"),
                    port=self.config.get("port", 389),
                    use_ssl=self.config.get("use_ssl", False),
                    get_info=ALL
                )
                conn = Connection(
                    server,
                    user=self.config.get("bind_dn"),
                    password=self.config.get("bind_password"),
                    auto_bind=True
                )
                conn.unbind()
                return True

            elif self.connector_type == "rest":
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        self.config.get("base_url"),
                        verify=self.config.get("verify_ssl", True)
                    )
                    return response.status_code < 500

            elif self.connector_type == "erp":
                if self.connector_subtype == "odoo":
                    import xmlrpc.client
                    common = xmlrpc.client.ServerProxy(f'{self.config.get("url")}/xmlrpc/2/common')
                    uid = common.authenticate(
                        self.config.get("database"),
                        self.config.get("username"),
                        self.config.get("password"),
                        {}
                    )
                    return uid is not None and uid > 0

            return False
        except Exception as e:
            logger.error("Connection test failed", connector=self.name, error=str(e))
            return False

    async def get_user(self, user_id: str) -> Optional[dict]:
        """Récupère un utilisateur."""
        # Implementation basique - à étendre selon le type
        return None

    async def search_users(self, query: dict) -> list:
        """Recherche des utilisateurs."""
        # Implementation basique - à étendre selon le type
        return []


class ConnectorFactory:
    """
    Factory pour creer et gerer les connecteurs.

    Supporte:
    - Connecteurs statiques (LDAP, SQL, Odoo depuis config.py)
    - Connecteurs dynamiques (depuis la base de données)
    """

    _connectors: Dict[str, BaseConnector] = {}
    _dynamic_configs: Dict[str, dict] = {}
    _cache_loaded: bool = False

    async def load_dynamic_connectors(self, session=None):
        """Charge les connecteurs dynamiques depuis la base de données."""
        if session is None:
            from app.core.database import get_session
            async for sess in get_session():
                session = sess
                break

        try:
            from sqlalchemy import text
            result = await session.execute(
                text("SELECT * FROM connector_configurations WHERE is_active = true")
            )
            rows = result.fetchall()

            for row in rows:
                row_dict = dict(row._mapping)
                self._dynamic_configs[row_dict["name"].upper()] = {
                    "id": row_dict["id"],
                    "name": row_dict["name"],
                    "connector_type": row_dict["connector_type"],
                    "connector_subtype": row_dict["connector_subtype"],
                    "configuration": row_dict["configuration"],
                    "display_name": row_dict["display_name"]
                }

            self._cache_loaded = True
            logger.info("Dynamic connectors loaded", count=len(rows))

        except Exception as e:
            logger.warning("Could not load dynamic connectors", error=str(e))

    def invalidate_cache(self):
        """Invalide le cache des connecteurs."""
        self._connectors.clear()
        self._dynamic_configs.clear()
        self._cache_loaded = False
        logger.info("Connector cache invalidated")

    def get_connector(self, target_system: str) -> BaseConnector:
        """
        Recupere ou cree un connecteur pour le systeme cible.

        Args:
            target_system: Nom du systeme cible (LDAP, AD, SQL, ODOO, etc.)

        Returns:
            Instance du connecteur appropriate
        """
        target = target_system.upper()

        # Return cached connector if exists
        if target in self._connectors:
            return self._connectors[target]

        # Check if dynamic connector exists
        if target in self._dynamic_configs:
            connector = self._create_dynamic_connector(target)
        else:
            # Fallback to static connector
            connector = self._create_static_connector(target)

        self._connectors[target] = connector
        logger.info("Connector created", target=target, type=connector.__class__.__name__)
        return connector

    def _create_dynamic_connector(self, target: str) -> BaseConnector:
        """Crée un connecteur dynamique depuis la configuration DB."""
        config = self._dynamic_configs[target]
        return DynamicConnector(
            name=config["name"],
            connector_type=config["connector_type"],
            connector_subtype=config["connector_subtype"],
            config=config["configuration"]
        )

    def _create_static_connector(self, target: str) -> BaseConnector:
        """Create a static connector instance from config.py."""
        if target == "MIDPOINT":
            return MidPointConnector()

        elif target in ("LDAP", "AD"):
            return LDAPConnector()

        elif target == "SQL":
            return SQLConnector()

        elif target == "ODOO":
            return OdooConnector()

        elif target == "GLPI":
            raise NotImplementedError("GLPI connector not configured. Add it via the Connectors page.")

        elif target == "KEYCLOAK":
            raise NotImplementedError("Keycloak connector not configured. Add it via the Connectors page.")

        elif target == "FIREBASE":
            raise NotImplementedError("Firebase connector not configured. Add it via the Connectors page.")

        else:
            raise ValueError(f"Unknown target system: {target}. Configure it via the Connectors page.")

    def get_available_connectors(self) -> list:
        """Return list of available connector types."""
        connectors = [
            {"name": "MIDPOINT", "status": "available", "description": "MidPoint IAM Hub (central)", "source": "static"},
            {"name": "LDAP", "status": "available", "description": "LDAP/OpenLDAP directory", "source": "static"},
            {"name": "AD", "status": "available", "description": "Active Directory", "source": "static"},
            {"name": "SQL", "status": "available", "description": "SQL Database (PostgreSQL, MySQL)", "source": "static"},
            {"name": "ODOO", "status": "available", "description": "Odoo ERP via XML-RPC", "source": "static"},
        ]

        # Add dynamic connectors
        for name, config in self._dynamic_configs.items():
            if name not in ["LDAP", "AD", "SQL", "ODOO"]:
                connectors.append({
                    "name": name,
                    "status": "available",
                    "description": config.get("display_name", name),
                    "source": "dynamic"
                })

        return connectors

    async def test_all_connectors(self) -> Dict[str, Dict[str, any]]:
        """Test connectivity to all configured connectors."""
        results = {}

        # Test static connectors
        for target in ["LDAP", "SQL", "ODOO"]:
            try:
                connector = self.get_connector(target)
                connected = await connector.test_connection()
                results[target] = {
                    "status": "connected" if connected else "failed",
                    "error": None,
                    "source": "static"
                }
            except Exception as e:
                results[target] = {
                    "status": "error",
                    "error": str(e),
                    "source": "static"
                }

        # Test dynamic connectors
        for name in self._dynamic_configs.keys():
            if name not in results:
                try:
                    connector = self.get_connector(name)
                    connected = await connector.test_connection()
                    results[name] = {
                        "status": "connected" if connected else "failed",
                        "error": None,
                        "source": "dynamic"
                    }
                except Exception as e:
                    results[name] = {
                        "status": "error",
                        "error": str(e),
                        "source": "dynamic"
                    }

        return results

    def clear_cache(self):
        """Clear connector cache."""
        self._connectors.clear()
