"""
Service de gestion des connecteurs dynamiques.
Permet de creer, modifier, supprimer et tester des connecteurs via l'interface.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid
import time
import structlog
from sqlalchemy import text

from app.models.connector import (
    ConnectorType, ConnectorSubtype, HealthStatus,
    ConnectorCreate, ConnectorUpdate, ConnectorResponse,
    ConnectorListResponse, ConnectorTestResult, ConnectorTypeInfo,
    CONNECTOR_CONFIG_SCHEMAS, CONNECTOR_TYPE_SUBTYPES, CONNECTOR_TYPE_INFO
)
from app.core.config import settings

logger = structlog.get_logger()


class ConnectorManagementService:
    """Service de gestion des connecteurs."""

    def __init__(self, session):
        self.session = session

    def _mask_credentials(self, config: Dict[str, Any], subtype: ConnectorSubtype) -> Dict[str, Any]:
        """Masque les credentials dans la configuration."""
        schema = CONNECTOR_CONFIG_SCHEMAS.get(subtype, {})
        properties = schema.get("properties", {})
        masked = {}

        for key, value in config.items():
            prop_schema = properties.get(key, {})
            if prop_schema.get("format") == "password" and value:
                masked[key] = "••••••••"
            else:
                masked[key] = value

        return masked

    async def list_connectors(
        self,
        connector_type: Optional[ConnectorType] = None,
        is_active: Optional[bool] = None
    ) -> List[ConnectorListResponse]:
        """Liste tous les connecteurs."""
        query = "SELECT id, name, connector_type, connector_subtype, display_name, description, is_active, configuration, last_health_status, last_health_check FROM connector_configurations WHERE 1=1"
        params = {}

        if connector_type:
            query += " AND connector_type = :connector_type"
            params["connector_type"] = connector_type.value

        if is_active is not None:
            query += " AND is_active = :is_active"
            params["is_active"] = is_active

        query += " ORDER BY display_name ASC"

        result = await self.session.execute(text(query), params)
        rows = result.fetchall()

        connectors = []
        for row in rows:
            subtype = ConnectorSubtype(row[3])
            config = row[7] if row[7] else {}
            masked_config = self._mask_credentials(config, subtype)

            connectors.append(ConnectorListResponse(
                id=row[0],
                name=row[1],
                connector_type=ConnectorType(row[2]),
                connector_subtype=subtype,
                display_name=row[4],
                description=row[5],
                is_active=row[6],
                configuration=masked_config,
                last_health_status=HealthStatus(row[8]) if row[8] else HealthStatus.UNKNOWN,
                last_health_check=row[9]
            ))

        return connectors

    async def get_connector(self, connector_id: str) -> Optional[ConnectorResponse]:
        """Recupere un connecteur par ID."""
        result = await self.session.execute(text("""
            SELECT id, name, connector_type, connector_subtype, display_name, description,
                   is_active, configuration, last_health_status, last_health_check,
                   last_health_error, created_at, updated_at, created_by
            FROM connector_configurations
            WHERE id = :id
        """), {"id": connector_id})

        row = result.fetchone()
        if not row:
            return None

        subtype = ConnectorSubtype(row[3])
        config = row[7] if isinstance(row[7], dict) else json.loads(row[7]) if row[7] else {}
        masked_config = self._mask_credentials(config, subtype)

        return ConnectorResponse(
            id=row[0],
            name=row[1],
            connector_type=ConnectorType(row[2]),
            connector_subtype=subtype,
            display_name=row[4],
            description=row[5],
            is_active=row[6],
            configuration=masked_config,
            last_health_status=HealthStatus(row[8]) if row[8] else HealthStatus.UNKNOWN,
            last_health_check=row[9],
            last_health_error=row[10],
            created_at=row[11],
            updated_at=row[12],
            created_by=row[13]
        )

    async def get_connector_config(self, connector_id: str) -> Optional[Dict[str, Any]]:
        """Recupere la configuration complete (non masquee) d'un connecteur."""
        result = await self.session.execute(text("""
            SELECT configuration FROM connector_configurations WHERE id = :id
        """), {"id": connector_id})

        row = result.fetchone()
        if not row:
            return None

        return row[0] if isinstance(row[0], dict) else json.loads(row[0]) if row[0] else {}

    async def create_connector(
        self,
        data: ConnectorCreate,
        created_by: str
    ) -> ConnectorResponse:
        """Cree un nouveau connecteur."""
        connector_id = f"conn-{str(uuid.uuid4())[:8]}"

        await self.session.execute(text("""
            INSERT INTO connector_configurations
            (id, name, connector_type, connector_subtype, display_name, description,
             is_active, configuration, last_health_status, created_at, updated_at, created_by)
            VALUES (:id, :name, :connector_type, :connector_subtype, :display_name, :description,
                    :is_active, CAST(:configuration AS jsonb), :health_status, :created_at, :updated_at, :created_by)
        """), {
            "id": connector_id,
            "name": data.name,
            "connector_type": data.connector_type.value,
            "connector_subtype": data.connector_subtype.value,
            "display_name": data.display_name,
            "description": data.description,
            "is_active": data.is_active,
            "configuration": json.dumps(data.configuration),
            "health_status": HealthStatus.UNKNOWN.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": created_by
        })

        await self.session.commit()
        logger.info("Connector created", connector_id=connector_id, name=data.name)

        return await self.get_connector(connector_id)

    async def update_connector(
        self,
        connector_id: str,
        data: ConnectorUpdate,
        updated_by: str
    ) -> Optional[ConnectorResponse]:
        """Met a jour un connecteur."""
        # Construire la requete dynamiquement
        updates = ["updated_at = :updated_at"]
        params = {"id": connector_id, "updated_at": datetime.utcnow()}

        if data.display_name is not None:
            updates.append("display_name = :display_name")
            params["display_name"] = data.display_name

        if data.description is not None:
            updates.append("description = :description")
            params["description"] = data.description

        if data.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if data.configuration is not None:
            # Fusionner avec la config existante pour garder les passwords non modifies
            existing_config = await self.get_connector_config(connector_id)
            if existing_config:
                for key, value in data.configuration.items():
                    if value != "••••••••":  # Ne pas ecraser si masque
                        existing_config[key] = value
                updates.append("configuration = CAST(:configuration AS jsonb)")
                params["configuration"] = json.dumps(existing_config)

        query = f"UPDATE connector_configurations SET {', '.join(updates)} WHERE id = :id"
        await self.session.execute(text(query), params)
        await self.session.commit()

        logger.info("Connector updated", connector_id=connector_id)
        return await self.get_connector(connector_id)

    async def delete_connector(self, connector_id: str) -> bool:
        """Supprime un connecteur."""
        result = await self.session.execute(text("""
            DELETE FROM connector_configurations WHERE id = :id
        """), {"id": connector_id})
        await self.session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info("Connector deleted", connector_id=connector_id)
        return deleted

    async def toggle_connector(self, connector_id: str, is_active: bool) -> Optional[ConnectorResponse]:
        """Active ou desactive un connecteur."""
        await self.session.execute(text("""
            UPDATE connector_configurations
            SET is_active = :is_active, updated_at = :updated_at
            WHERE id = :id
        """), {
            "id": connector_id,
            "is_active": is_active,
            "updated_at": datetime.utcnow()
        })
        await self.session.commit()

        logger.info("Connector toggled", connector_id=connector_id, is_active=is_active)
        return await self.get_connector(connector_id)

    async def test_connection(self, connector_id: str) -> ConnectorTestResult:
        """Teste la connexion d'un connecteur existant."""
        connector = await self.get_connector(connector_id)
        if not connector:
            return ConnectorTestResult(
                success=False,
                message="Connecteur non trouve"
            )

        config = await self.get_connector_config(connector_id)
        return await self.test_connection_preview(
            connector.connector_type,
            connector.connector_subtype,
            config
        )

    async def test_connection_preview(
        self,
        connector_type: ConnectorType,
        connector_subtype: ConnectorSubtype,
        configuration: Dict[str, Any]
    ) -> ConnectorTestResult:
        """Teste une configuration avant sauvegarde."""
        start_time = time.time()

        try:
            if connector_type == ConnectorType.SQL:
                result = await self._test_sql_connection(connector_subtype, configuration)
            elif connector_type == ConnectorType.LDAP:
                result = await self._test_ldap_connection(connector_subtype, configuration)
            elif connector_type == ConnectorType.REST:
                result = await self._test_rest_connection(connector_subtype, configuration)
            elif connector_type == ConnectorType.ERP:
                result = await self._test_erp_connection(connector_subtype, configuration)
            else:
                result = ConnectorTestResult(
                    success=False,
                    message=f"Type de connecteur non supporte: {connector_type}"
                )

            result.response_time_ms = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return ConnectorTestResult(
                success=False,
                message=f"Erreur: {str(e)}",
                response_time_ms=int((time.time() - start_time) * 1000)
            )

    async def _test_sql_connection(
        self,
        subtype: ConnectorSubtype,
        config: Dict[str, Any]
    ) -> ConnectorTestResult:
        """Teste une connexion SQL."""
        try:
            if subtype == ConnectorSubtype.POSTGRESQL:
                import asyncpg
                conn = await asyncpg.connect(
                    host=config.get("host", "localhost"),
                    port=config.get("port", 5432),
                    database=config.get("database"),
                    user=config.get("username"),
                    password=config.get("password"),
                    timeout=10
                )
                version = await conn.fetchval("SELECT version()")
                await conn.close()
                return ConnectorTestResult(
                    success=True,
                    message="Connexion PostgreSQL reussie",
                    details={"version": version[:50] if version else "Unknown"}
                )

            elif subtype in [ConnectorSubtype.MYSQL, ConnectorSubtype.MARIADB]:
                import aiomysql
                conn = await aiomysql.connect(
                    host=config.get("host", "localhost"),
                    port=config.get("port", 3306),
                    db=config.get("database"),
                    user=config.get("username"),
                    password=config.get("password"),
                    connect_timeout=10
                )
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT VERSION()")
                    version = await cursor.fetchone()
                conn.close()
                return ConnectorTestResult(
                    success=True,
                    message=f"Connexion {subtype.value} reussie",
                    details={"version": version[0] if version else "Unknown"}
                )

            else:
                return ConnectorTestResult(
                    success=False,
                    message=f"Test non implemente pour {subtype.value}"
                )

        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Echec connexion SQL: {str(e)}"
            )

    async def _test_ldap_connection(
        self,
        subtype: ConnectorSubtype,
        config: Dict[str, Any]
    ) -> ConnectorTestResult:
        """Teste une connexion LDAP."""
        try:
            from ldap3 import Server, Connection, ALL

            server = Server(
                config.get("host", "localhost"),
                port=config.get("port", 389),
                use_ssl=config.get("use_ssl", False),
                get_info=ALL
            )

            conn = Connection(
                server,
                user=config.get("bind_dn"),
                password=config.get("bind_password"),
                auto_bind=True
            )

            # Test recherche
            base_dn = config.get("base_dn")
            conn.search(base_dn, "(objectClass=*)", size_limit=1)

            server_info = str(server.info)[:100] if server.info else "Unknown"
            conn.unbind()

            return ConnectorTestResult(
                success=True,
                message="Connexion LDAP reussie",
                details={"server_info": server_info, "base_dn": base_dn}
            )

        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Echec connexion LDAP: {str(e)}"
            )

    async def _test_rest_connection(
        self,
        subtype: ConnectorSubtype,
        config: Dict[str, Any]
    ) -> ConnectorTestResult:
        """Teste une connexion REST API."""
        try:
            import aiohttp

            base_url = config.get("base_url", "").rstrip("/")
            auth_type = config.get("auth_type", "none")
            timeout = aiohttp.ClientTimeout(total=config.get("timeout", 30))
            verify_ssl = config.get("verify_ssl", True)

            headers = {}

            if auth_type == "bearer":
                headers["Authorization"] = f"Bearer {config.get('bearer_token', '')}"
            elif auth_type == "api_key":
                header_name = config.get("api_key_header", "X-API-Key")
                headers[header_name] = config.get("api_key", "")

            auth = None
            if auth_type == "basic":
                auth = aiohttp.BasicAuth(
                    config.get("username", ""),
                    config.get("password", "")
                )

            # Endpoint de test selon le subtype
            if subtype == ConnectorSubtype.KEYCLOAK:
                test_url = f"{base_url}/realms/{config.get('realm', 'master')}"
            elif subtype == ConnectorSubtype.GLPI:
                test_url = f"{base_url}/apirest.php/initSession"
            else:
                test_url = base_url

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    test_url,
                    headers=headers,
                    auth=auth,
                    ssl=verify_ssl
                ) as response:
                    if response.status < 400:
                        return ConnectorTestResult(
                            success=True,
                            message=f"Connexion REST reussie (HTTP {response.status})",
                            details={"url": test_url, "status": response.status}
                        )
                    else:
                        return ConnectorTestResult(
                            success=False,
                            message=f"Erreur HTTP {response.status}",
                            details={"url": test_url, "status": response.status}
                        )

        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Echec connexion REST: {str(e)}"
            )

    async def _test_erp_connection(
        self,
        subtype: ConnectorSubtype,
        config: Dict[str, Any]
    ) -> ConnectorTestResult:
        """Teste une connexion ERP."""
        try:
            if subtype == ConnectorSubtype.ODOO:
                import xmlrpc.client

                url = config.get("url", "").rstrip("/")
                db = config.get("database")
                username = config.get("username")
                password = config.get("password")

                # Test authentification
                common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
                version = common.version()

                uid = common.authenticate(db, username, password, {})
                if uid:
                    return ConnectorTestResult(
                        success=True,
                        message="Connexion Odoo reussie",
                        details={"version": version.get("server_version", "Unknown"), "uid": uid}
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message="Authentification Odoo echouee"
                    )

            else:
                return ConnectorTestResult(
                    success=False,
                    message=f"Test non implemente pour {subtype.value}"
                )

        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message=f"Echec connexion ERP: {str(e)}"
            )

    async def update_health_status(
        self,
        connector_id: str,
        status: HealthStatus,
        error: Optional[str] = None
    ) -> None:
        """Met a jour le statut de sante d'un connecteur."""
        await self.session.execute(text("""
            UPDATE connector_configurations
            SET last_health_status = :status,
                last_health_check = :check_time,
                last_health_error = :error
            WHERE id = :id
        """), {
            "id": connector_id,
            "status": status.value,
            "check_time": datetime.utcnow(),
            "error": error
        })
        await self.session.commit()

    def get_connector_types(self) -> List[ConnectorTypeInfo]:
        """Retourne la liste des types de connecteurs disponibles."""
        types = []

        for conn_type, subtypes in CONNECTOR_TYPE_SUBTYPES.items():
            for subtype in subtypes:
                info = CONNECTOR_TYPE_INFO.get(subtype, {})
                schema = CONNECTOR_CONFIG_SCHEMAS.get(subtype, {})

                types.append(ConnectorTypeInfo(
                    type=conn_type,
                    subtype=subtype,
                    name=info.get("name", subtype.value),
                    icon=info.get("icon", "database"),
                    description=info.get("description", ""),
                    config_schema=schema
                ))

        return types

    async def run_health_checks(self) -> Dict[str, ConnectorTestResult]:
        """Execute les tests de sante sur tous les connecteurs actifs."""
        connectors = await self.list_connectors(is_active=True)
        results = {}

        for connector in connectors:
            try:
                result = await self.test_connection(connector.id)
                status = HealthStatus.HEALTHY if result.success else HealthStatus.UNHEALTHY
                error = None if result.success else result.message

                await self.update_health_status(connector.id, status, error)
                results[connector.id] = result

            except Exception as e:
                logger.error("Health check failed", connector_id=connector.id, error=str(e))
                await self.update_health_status(connector.id, HealthStatus.UNHEALTHY, str(e))
                results[connector.id] = ConnectorTestResult(
                    success=False,
                    message=str(e)
                )

        return results
