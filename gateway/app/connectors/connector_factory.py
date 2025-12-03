"""
Factory pour les connecteurs
"""
from typing import Dict
import structlog

from app.connectors.base import BaseConnector
from app.connectors.ldap_connector import LDAPConnector
from app.connectors.sql_connector import SQLConnector
from app.connectors.odoo_connector import OdooConnector

logger = structlog.get_logger()


class ConnectorFactory:
    """
    Factory pour creer et gerer les connecteurs.

    Maintient un cache des connecteurs pour reutilisation.
    """

    _connectors: Dict[str, BaseConnector] = {}

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

        # Create new connector
        connector = self._create_connector(target)
        self._connectors[target] = connector

        logger.info("Connector created", target=target, type=connector.__class__.__name__)
        return connector

    def _create_connector(self, target: str) -> BaseConnector:
        """Create a new connector instance."""
        if target in ("LDAP", "AD"):
            return LDAPConnector()

        elif target == "SQL":
            return SQLConnector()

        elif target == "ODOO":
            return OdooConnector()

        elif target == "GLPI":
            # Placeholder for GLPI connector
            raise NotImplementedError("GLPI connector not yet implemented")

        elif target == "KEYCLOAK":
            # Placeholder for Keycloak connector
            raise NotImplementedError("Keycloak connector not yet implemented")

        elif target == "FIREBASE":
            # Placeholder for Firebase connector
            raise NotImplementedError("Firebase connector not yet implemented")

        else:
            raise ValueError(f"Unknown target system: {target}")

    def get_available_connectors(self) -> list:
        """Return list of available connector types."""
        return [
            {"name": "LDAP", "status": "available", "description": "LDAP/OpenLDAP directory"},
            {"name": "AD", "status": "available", "description": "Active Directory"},
            {"name": "SQL", "status": "available", "description": "SQL Database (PostgreSQL, MySQL)"},
            {"name": "ODOO", "status": "available", "description": "Odoo ERP via XML-RPC"},
            {"name": "GLPI", "status": "planned", "description": "GLPI Ticketing System"},
            {"name": "KEYCLOAK", "status": "planned", "description": "Keycloak Identity Provider"},
            {"name": "FIREBASE", "status": "planned", "description": "Google Firebase"},
        ]

    async def test_all_connectors(self) -> Dict[str, Dict[str, any]]:
        """Test connectivity to all configured connectors."""
        results = {}

        for target in ["LDAP", "SQL", "ODOO"]:
            try:
                connector = self.get_connector(target)
                connected = await connector.test_connection()
                results[target] = {
                    "status": "connected" if connected else "failed",
                    "error": None
                }
            except Exception as e:
                results[target] = {
                    "status": "error",
                    "error": str(e)
                }

        return results

    def clear_cache(self):
        """Clear connector cache."""
        self._connectors.clear()
