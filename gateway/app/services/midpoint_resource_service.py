"""
Service pour la creation automatique de Resources dans MidPoint.
Permet de synchroniser les connecteurs Gateway avec MidPoint.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
import json
import uuid

from app.models.connector import ConnectorType, ConnectorSubtype

logger = structlog.get_logger()


# ==================== CONNID CONNECTOR MAPPINGS ====================

# Mapping des sous-types Gateway vers les connecteurs ConnId de MidPoint
CONNECTOR_TO_CONNID_MAP = {
    # SQL Connectors
    ConnectorSubtype.POSTGRESQL: {
        "connid_bundle": "com.evolveum.polygon.connector.jdbc",
        "connid_type": "com.evolveum.polygon.connector.jdbc.JdbcConnector",
        "connid_version": "1.5.0.0",
        "object_class": "AccountObjectClass"
    },
    ConnectorSubtype.MYSQL: {
        "connid_bundle": "com.evolveum.polygon.connector.jdbc",
        "connid_type": "com.evolveum.polygon.connector.jdbc.JdbcConnector",
        "connid_version": "1.5.0.0",
        "object_class": "AccountObjectClass"
    },
    ConnectorSubtype.ORACLE: {
        "connid_bundle": "com.evolveum.polygon.connector.jdbc",
        "connid_type": "com.evolveum.polygon.connector.jdbc.JdbcConnector",
        "connid_version": "1.5.0.0",
        "object_class": "AccountObjectClass"
    },
    ConnectorSubtype.SQLSERVER: {
        "connid_bundle": "com.evolveum.polygon.connector.jdbc",
        "connid_type": "com.evolveum.polygon.connector.jdbc.JdbcConnector",
        "connid_version": "1.5.0.0",
        "object_class": "AccountObjectClass"
    },
    # LDAP Connectors
    ConnectorSubtype.OPENLDAP: {
        "connid_bundle": "com.evolveum.polygon.connector.ldap",
        "connid_type": "com.evolveum.polygon.connector.ldap.LdapConnector",
        "connid_version": "3.7",
        "object_class": "inetOrgPerson"
    },
    ConnectorSubtype.ACTIVE_DIRECTORY: {
        "connid_bundle": "com.evolveum.polygon.connector.ldap",
        "connid_type": "com.evolveum.polygon.connector.ldap.ad.AdLdapConnector",
        "connid_version": "3.7",
        "object_class": "user"
    },
    ConnectorSubtype.FREEIPA: {
        "connid_bundle": "com.evolveum.polygon.connector.ldap",
        "connid_type": "com.evolveum.polygon.connector.ldap.LdapConnector",
        "connid_version": "3.7",
        "object_class": "inetOrgPerson"
    },
    # REST Connectors
    ConnectorSubtype.KEYCLOAK: {
        "connid_bundle": "com.evolveum.polygon.connector.rest",
        "connid_type": "com.evolveum.polygon.connector.rest.RestConnector",
        "connid_version": "1.0",
        "object_class": "AccountObjectClass"
    },
    ConnectorSubtype.GENERIC_REST: {
        "connid_bundle": "com.evolveum.polygon.connector.rest",
        "connid_type": "com.evolveum.polygon.connector.rest.RestConnector",
        "connid_version": "1.0",
        "object_class": "AccountObjectClass"
    },
    # ERP Connectors - Using CSV/ScriptedSQL for Odoo
    ConnectorSubtype.ODOO: {
        "connid_bundle": "com.evolveum.polygon.connector.csv",
        "connid_type": "com.evolveum.polygon.connector.csv.CsvConnector",
        "connid_version": "2.6",
        "object_class": "AccountObjectClass"
    }
}

# Mapping des proprietes de configuration Gateway -> MidPoint
GATEWAY_TO_MIDPOINT_CONFIG = {
    ConnectorSubtype.POSTGRESQL: {
        "host": "jdbcHost",
        "port": "jdbcPort",
        "database": "jdbcDatabase",
        "username": "jdbcUsername",
        "password": "jdbcPassword",
        "_jdbc_driver": "org.postgresql.Driver",
        "_jdbc_url_template": "jdbc:postgresql://{host}:{port}/{database}"
    },
    ConnectorSubtype.MYSQL: {
        "host": "jdbcHost",
        "port": "jdbcPort",
        "database": "jdbcDatabase",
        "username": "jdbcUsername",
        "password": "jdbcPassword",
        "_jdbc_driver": "com.mysql.cj.jdbc.Driver",
        "_jdbc_url_template": "jdbc:mysql://{host}:{port}/{database}"
    },
    ConnectorSubtype.OPENLDAP: {
        "host": "host",
        "port": "port",
        "bind_dn": "bindDn",
        "bind_password": "bindPassword",
        "base_dn": "baseContext",
        "use_ssl": "ssl",
        "users_ou": "baseContextsToSynchronize"
    },
    ConnectorSubtype.ACTIVE_DIRECTORY: {
        "host": "host",
        "port": "port",
        "bind_dn": "bindDn",
        "bind_password": "bindPassword",
        "base_dn": "baseContext",
        "use_ssl": "ssl",
        "domain": "domain"
    },
    ConnectorSubtype.KEYCLOAK: {
        "server_url": "serviceAddress",
        "realm": "realm",
        "client_id": "clientId",
        "client_secret": "clientSecret",
        "admin_username": "username",
        "admin_password": "password"
    },
    ConnectorSubtype.ODOO: {
        "url": "serviceAddress",
        "database": "database",
        "username": "username",
        "password": "password"
    }
}


class MidPointResourceService:
    """
    Service pour creer et gerer les Resources MidPoint
    a partir des connecteurs configures dans le Gateway.
    """

    def __init__(self):
        from app.services.midpoint_client import MidPointClient
        self.midpoint_client = MidPointClient()

    async def create_resource_in_midpoint(
        self,
        connector_id: str,
        connector_name: str,
        connector_subtype: ConnectorSubtype,
        connector_config: Dict[str, Any],
        display_name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cree une Resource dans MidPoint basee sur la configuration du connecteur.

        Args:
            connector_id: ID du connecteur Gateway
            connector_name: Nom technique du connecteur
            connector_subtype: Sous-type du connecteur
            connector_config: Configuration du connecteur
            display_name: Nom d'affichage
            description: Description optionnelle

        Returns:
            Dict avec l'OID de la resource creee et le statut
        """
        try:
            # Verifier si le type de connecteur est supporte
            if connector_subtype not in CONNECTOR_TO_CONNID_MAP:
                return {
                    "success": False,
                    "error": f"Connector type {connector_subtype} not supported for MidPoint auto-creation",
                    "resource_oid": None
                }

            connid_info = CONNECTOR_TO_CONNID_MAP[connector_subtype]

            # Generer la configuration MidPoint
            midpoint_config = self._generate_midpoint_config(
                connector_subtype,
                connector_config,
                connid_info
            )

            # Construire l'objet Resource
            resource_object = self._build_resource_object(
                name=connector_name,
                display_name=display_name,
                description=description or f"Auto-created from Gateway connector {connector_id}",
                connector_subtype=connector_subtype,
                connid_info=connid_info,
                midpoint_config=midpoint_config
            )

            # Creer dans MidPoint via REST API
            result = await self._create_resource_via_api(resource_object)

            if result.get("success"):
                logger.info(
                    "Resource created in MidPoint",
                    connector_id=connector_id,
                    resource_oid=result.get("resource_oid"),
                    connector_type=connector_subtype.value
                )

            return result

        except Exception as e:
            logger.error(
                "Failed to create resource in MidPoint",
                connector_id=connector_id,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "resource_oid": None
            }

    def _generate_midpoint_config(
        self,
        connector_subtype: ConnectorSubtype,
        gateway_config: Dict[str, Any],
        connid_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convertit la configuration Gateway en configuration MidPoint.
        """
        config_mapping = GATEWAY_TO_MIDPOINT_CONFIG.get(connector_subtype, {})
        midpoint_config = {}

        for gateway_key, midpoint_key in config_mapping.items():
            if gateway_key.startswith("_"):
                # Valeurs speciales predefinies
                continue
            if gateway_key in gateway_config:
                midpoint_config[midpoint_key] = gateway_config[gateway_key]

        # Ajouter des valeurs speciales selon le type
        if connector_subtype in [ConnectorSubtype.POSTGRESQL, ConnectorSubtype.MYSQL]:
            jdbc_template = config_mapping.get("_jdbc_url_template", "")
            jdbc_driver = config_mapping.get("_jdbc_driver", "")

            if jdbc_template:
                midpoint_config["jdbcUrlTemplate"] = jdbc_template.format(
                    host=gateway_config.get("host", "localhost"),
                    port=gateway_config.get("port", 5432),
                    database=gateway_config.get("database", "")
                )
            if jdbc_driver:
                midpoint_config["jdbcDriver"] = jdbc_driver

        return midpoint_config

    def _build_resource_object(
        self,
        name: str,
        display_name: str,
        description: str,
        connector_subtype: ConnectorSubtype,
        connid_info: Dict[str, Any],
        midpoint_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Construit l'objet Resource au format MidPoint REST API.
        """
        # Configuration properties pour le connecteur
        config_properties = {}
        for key, value in midpoint_config.items():
            config_properties[key] = value

        resource = {
            "resource": {
                "name": name,
                "description": description,
                # Reference au type de connecteur
                "connectorRef": {
                    "type": "ConnectorType",
                    "filter": {
                        "equal": {
                            "path": "connectorType",
                            "value": connid_info["connid_type"]
                        }
                    }
                },
                # Configuration du connecteur
                "connectorConfiguration": {
                    "configurationProperties": config_properties
                },
                # Schema handling - auto-decouverte
                "schemaHandling": {
                    "objectType": [
                        {
                            "kind": "account",
                            "intent": "default",
                            "displayName": display_name,
                            "default": True,
                            "objectClass": connid_info.get("object_class", "AccountObjectClass"),
                            # Attributs de base
                            "attribute": self._get_default_attributes(connector_subtype)
                        }
                    ]
                },
                # Capabilities
                "capabilities": {
                    "configured": {
                        "activation": {
                            "status": {
                                "enabled": True
                            }
                        }
                    }
                },
                # Synchronization settings
                "synchronization": {
                    "objectSynchronization": [
                        {
                            "enabled": True,
                            "kind": "account",
                            "intent": "default",
                            "focusType": "UserType",
                            "correlation": [
                                {
                                    "q:equal": {
                                        "q:path": "name",
                                        "expression": {
                                            "path": "$account/attributes/uid"
                                        }
                                    }
                                }
                            ],
                            "reaction": [
                                {
                                    "situation": "linked",
                                    "synchronize": True
                                },
                                {
                                    "situation": "deleted",
                                    "action": "unlink"
                                },
                                {
                                    "situation": "unlinked",
                                    "action": "link"
                                },
                                {
                                    "situation": "unmatched",
                                    "action": "addFocus"
                                }
                            ]
                        }
                    ]
                }
            }
        }

        return resource

    def _get_default_attributes(self, connector_subtype: ConnectorSubtype) -> List[Dict[str, Any]]:
        """
        Retourne les attributs par defaut selon le type de connecteur.
        """
        if connector_subtype in [ConnectorSubtype.OPENLDAP, ConnectorSubtype.ACTIVE_DIRECTORY, ConnectorSubtype.FREEIPA]:
            return [
                {
                    "ref": "ri:uid",
                    "displayName": "Username",
                    "outbound": {
                        "strength": "strong",
                        "source": {"path": "$user/name"}
                    }
                },
                {
                    "ref": "ri:cn",
                    "displayName": "Full Name",
                    "outbound": {
                        "strength": "strong",
                        "source": {"path": "$user/fullName"}
                    }
                },
                {
                    "ref": "ri:sn",
                    "displayName": "Last Name",
                    "outbound": {
                        "strength": "strong",
                        "source": {"path": "$user/familyName"}
                    }
                },
                {
                    "ref": "ri:givenName",
                    "displayName": "First Name",
                    "outbound": {
                        "strength": "strong",
                        "source": {"path": "$user/givenName"}
                    }
                },
                {
                    "ref": "ri:mail",
                    "displayName": "Email",
                    "outbound": {
                        "strength": "strong",
                        "source": {"path": "$user/emailAddress"}
                    }
                }
            ]

        elif connector_subtype in [ConnectorSubtype.POSTGRESQL, ConnectorSubtype.MYSQL]:
            return [
                {
                    "ref": "ri:username",
                    "displayName": "Username",
                    "outbound": {
                        "strength": "strong",
                        "source": {"path": "$user/name"}
                    }
                },
                {
                    "ref": "ri:email",
                    "displayName": "Email",
                    "outbound": {
                        "strength": "strong",
                        "source": {"path": "$user/emailAddress"}
                    }
                },
                {
                    "ref": "ri:fullname",
                    "displayName": "Full Name",
                    "outbound": {
                        "strength": "strong",
                        "source": {"path": "$user/fullName"}
                    }
                }
            ]

        else:
            # Default attributes for other types
            return [
                {
                    "ref": "ri:username",
                    "displayName": "Username",
                    "outbound": {
                        "strength": "strong",
                        "source": {"path": "$user/name"}
                    }
                }
            ]

    async def _create_resource_via_api(self, resource_object: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cree la resource dans MidPoint via l'API REST.
        """
        try:
            import httpx
            from app.core.config import settings

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    f"{settings.MIDPOINT_URL}/ws/rest/resources",
                    json=resource_object,
                    auth=(settings.MIDPOINT_USERNAME, settings.MIDPOINT_PASSWORD),
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )

                if response.status_code in [200, 201]:
                    # Extraire l'OID de la reponse
                    location = response.headers.get("Location", "")
                    resource_oid = location.split("/")[-1] if location else None

                    # Si pas d'OID dans le header, essayer le body
                    if not resource_oid:
                        try:
                            data = response.json()
                            resource_oid = data.get("oid") or data.get("resource", {}).get("oid")
                        except Exception:
                            pass

                    return {
                        "success": True,
                        "resource_oid": resource_oid,
                        "message": "Resource created successfully in MidPoint"
                    }

                elif response.status_code == 409:
                    return {
                        "success": False,
                        "error": "Resource already exists in MidPoint",
                        "resource_oid": None
                    }

                else:
                    error_msg = response.text[:500] if response.text else f"HTTP {response.status_code}"
                    return {
                        "success": False,
                        "error": f"MidPoint API error: {error_msg}",
                        "resource_oid": None
                    }

        except Exception as e:
            logger.error("MidPoint API call failed", error=str(e))
            return {
                "success": False,
                "error": f"API call failed: {str(e)}",
                "resource_oid": None
            }

    async def update_resource_in_midpoint(
        self,
        resource_oid: str,
        connector_subtype: ConnectorSubtype,
        connector_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Met a jour une Resource existante dans MidPoint.
        """
        try:
            if connector_subtype not in CONNECTOR_TO_CONNID_MAP:
                return {
                    "success": False,
                    "error": f"Connector type {connector_subtype} not supported"
                }

            connid_info = CONNECTOR_TO_CONNID_MAP[connector_subtype]
            midpoint_config = self._generate_midpoint_config(
                connector_subtype,
                connector_config,
                connid_info
            )

            import httpx
            from app.core.config import settings

            # Construire le delta de modification
            modification = {
                "objectModification": {
                    "itemDelta": [
                        {
                            "modificationType": "replace",
                            "path": "connectorConfiguration/configurationProperties",
                            "value": midpoint_config
                        }
                    ]
                }
            }

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.patch(
                    f"{settings.MIDPOINT_URL}/ws/rest/resources/{resource_oid}",
                    json=modification,
                    auth=(settings.MIDPOINT_USERNAME, settings.MIDPOINT_PASSWORD),
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )

                if response.status_code in [200, 204]:
                    logger.info("Resource updated in MidPoint", resource_oid=resource_oid)
                    return {
                        "success": True,
                        "message": "Resource updated successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"MidPoint API error: {response.status_code}"
                    }

        except Exception as e:
            logger.error("Failed to update resource", resource_oid=resource_oid, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_resource_in_midpoint(self, resource_oid: str) -> Dict[str, Any]:
        """
        Supprime une Resource de MidPoint.
        """
        try:
            import httpx
            from app.core.config import settings

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.delete(
                    f"{settings.MIDPOINT_URL}/ws/rest/resources/{resource_oid}",
                    auth=(settings.MIDPOINT_USERNAME, settings.MIDPOINT_PASSWORD),
                    timeout=30.0
                )

                if response.status_code in [200, 204, 404]:
                    logger.info("Resource deleted from MidPoint", resource_oid=resource_oid)
                    return {
                        "success": True,
                        "message": "Resource deleted successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"MidPoint API error: {response.status_code}"
                    }

        except Exception as e:
            logger.error("Failed to delete resource", resource_oid=resource_oid, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def test_resource_in_midpoint(self, resource_oid: str) -> Dict[str, Any]:
        """
        Teste la connexion d'une Resource dans MidPoint.
        """
        try:
            import httpx
            from app.core.config import settings

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    f"{settings.MIDPOINT_URL}/ws/rest/resources/{resource_oid}/test",
                    auth=(settings.MIDPOINT_USERNAME, settings.MIDPOINT_PASSWORD),
                    headers={"Content-Type": "application/json"},
                    timeout=60.0
                )

                if response.status_code == 200:
                    try:
                        result = response.json()
                        status = result.get("status", "unknown")
                        return {
                            "success": status == "success",
                            "status": status,
                            "message": result.get("message", "Test completed"),
                            "details": result
                        }
                    except Exception:
                        return {
                            "success": True,
                            "status": "success",
                            "message": "Resource test passed"
                        }
                else:
                    return {
                        "success": False,
                        "status": "error",
                        "message": f"Test failed: HTTP {response.status_code}"
                    }

        except Exception as e:
            logger.error("Failed to test resource", resource_oid=resource_oid, error=str(e))
            return {
                "success": False,
                "status": "error",
                "message": str(e)
            }

    async def get_resource_status(self, resource_oid: str) -> Dict[str, Any]:
        """
        Recupere le statut d'une Resource MidPoint.
        """
        try:
            import httpx
            from app.core.config import settings

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{settings.MIDPOINT_URL}/ws/rest/resources/{resource_oid}",
                    auth=(settings.MIDPOINT_USERNAME, settings.MIDPOINT_PASSWORD),
                    headers={"Accept": "application/json"},
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    resource = data.get("resource", data)
                    return {
                        "exists": True,
                        "oid": resource.get("oid"),
                        "name": resource.get("name"),
                        "operationalState": resource.get("operationalState", {}),
                        "administrativeState": resource.get("administrativeState"),
                        "lastAvailabilityStatus": resource.get("lastAvailabilityStatus")
                    }
                elif response.status_code == 404:
                    return {
                        "exists": False,
                        "message": "Resource not found in MidPoint"
                    }
                else:
                    return {
                        "exists": False,
                        "error": f"HTTP {response.status_code}"
                    }

        except Exception as e:
            return {
                "exists": False,
                "error": str(e)
            }

    async def list_midpoint_resources(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les Resources configurees dans MidPoint.
        """
        try:
            import httpx
            from app.core.config import settings

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{settings.MIDPOINT_URL}/ws/rest/resources",
                    auth=(settings.MIDPOINT_USERNAME, settings.MIDPOINT_PASSWORD),
                    headers={"Accept": "application/json"},
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    resources = []

                    # Parser la reponse MidPoint
                    obj = data.get("object", {})
                    if isinstance(obj, dict):
                        items = obj.get("object", [])
                    else:
                        items = obj if isinstance(obj, list) else []

                    if not isinstance(items, list):
                        items = [items] if items else []

                    for item in items:
                        resource = item.get("resource", item)
                        resources.append({
                            "oid": resource.get("oid"),
                            "name": resource.get("name"),
                            "description": resource.get("description"),
                            "connectorRef": resource.get("connectorRef", {}).get("oid"),
                            "operationalState": resource.get("operationalState", {})
                        })

                    return resources

                return []

        except Exception as e:
            logger.error("Failed to list MidPoint resources", error=str(e))
            return []


# Instance singleton
midpoint_resource_service = MidPointResourceService()
