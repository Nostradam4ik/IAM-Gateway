"""
Modeles pour la gestion dynamique des connecteurs.
Permet aux administrateurs de configurer les connecteurs via l'interface.
"""
from sqlmodel import SQLModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
import uuid


class ConnectorType(str, Enum):
    """Types principaux de connecteurs."""
    SQL = "sql"
    LDAP = "ldap"
    REST = "rest"
    ERP = "erp"


class ConnectorSubtype(str, Enum):
    """Sous-types specifiques de connecteurs."""
    # SQL
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    MARIADB = "mariadb"
    # LDAP
    OPENLDAP = "openldap"
    ACTIVE_DIRECTORY = "active_directory"
    FREEIPA = "freeipa"
    # REST API
    KEYCLOAK = "keycloak"
    FIREBASE = "firebase"
    GLPI = "glpi"
    GENERIC_REST = "generic_rest"
    # ERP
    ODOO = "odoo"
    SAP = "sap"


class HealthStatus(str, Enum):
    """Statut de sante d'un connecteur."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    TESTING = "testing"


# Schemas de configuration par type
CONNECTOR_CONFIG_SCHEMAS = {
    ConnectorSubtype.POSTGRESQL: {
        "type": "object",
        "required": ["host", "port", "database", "username", "password"],
        "properties": {
            "host": {"type": "string", "title": "Host", "default": "localhost"},
            "port": {"type": "integer", "title": "Port", "default": 5432},
            "database": {"type": "string", "title": "Base de donnees"},
            "username": {"type": "string", "title": "Utilisateur"},
            "password": {"type": "string", "title": "Mot de passe", "format": "password"},
            "ssl_mode": {"type": "string", "title": "Mode SSL", "enum": ["disable", "allow", "prefer", "require"], "default": "prefer"}
        }
    },
    ConnectorSubtype.MYSQL: {
        "type": "object",
        "required": ["host", "port", "database", "username", "password"],
        "properties": {
            "host": {"type": "string", "title": "Host", "default": "localhost"},
            "port": {"type": "integer", "title": "Port", "default": 3306},
            "database": {"type": "string", "title": "Base de donnees"},
            "username": {"type": "string", "title": "Utilisateur"},
            "password": {"type": "string", "title": "Mot de passe", "format": "password"},
            "ssl_enabled": {"type": "boolean", "title": "SSL Active", "default": False}
        }
    },
    ConnectorSubtype.ORACLE: {
        "type": "object",
        "required": ["host", "port", "service_name", "username", "password"],
        "properties": {
            "host": {"type": "string", "title": "Host", "default": "localhost"},
            "port": {"type": "integer", "title": "Port", "default": 1521},
            "service_name": {"type": "string", "title": "Service Name"},
            "username": {"type": "string", "title": "Utilisateur"},
            "password": {"type": "string", "title": "Mot de passe", "format": "password"}
        }
    },
    ConnectorSubtype.SQLSERVER: {
        "type": "object",
        "required": ["host", "port", "database", "username", "password"],
        "properties": {
            "host": {"type": "string", "title": "Host", "default": "localhost"},
            "port": {"type": "integer", "title": "Port", "default": 1433},
            "database": {"type": "string", "title": "Base de donnees"},
            "username": {"type": "string", "title": "Utilisateur"},
            "password": {"type": "string", "title": "Mot de passe", "format": "password"},
            "driver": {"type": "string", "title": "Driver ODBC", "default": "ODBC Driver 17 for SQL Server"}
        }
    },
    ConnectorSubtype.OPENLDAP: {
        "type": "object",
        "required": ["host", "port", "bind_dn", "bind_password", "base_dn"],
        "properties": {
            "host": {"type": "string", "title": "Host LDAP", "default": "localhost"},
            "port": {"type": "integer", "title": "Port", "default": 389},
            "bind_dn": {"type": "string", "title": "Bind DN", "placeholder": "cn=admin,dc=example,dc=com"},
            "bind_password": {"type": "string", "title": "Mot de passe Bind", "format": "password"},
            "base_dn": {"type": "string", "title": "Base DN", "placeholder": "dc=example,dc=com"},
            "use_ssl": {"type": "boolean", "title": "Utiliser SSL", "default": False},
            "use_starttls": {"type": "boolean", "title": "Utiliser StartTLS", "default": False},
            "users_ou": {"type": "string", "title": "OU Utilisateurs", "default": "ou=users"},
            "groups_ou": {"type": "string", "title": "OU Groupes", "default": "ou=groups"}
        }
    },
    ConnectorSubtype.ACTIVE_DIRECTORY: {
        "type": "object",
        "required": ["host", "port", "bind_dn", "bind_password", "base_dn"],
        "properties": {
            "host": {"type": "string", "title": "Serveur AD"},
            "port": {"type": "integer", "title": "Port", "default": 389},
            "bind_dn": {"type": "string", "title": "Bind DN (UPN)", "placeholder": "admin@domain.local"},
            "bind_password": {"type": "string", "title": "Mot de passe", "format": "password"},
            "base_dn": {"type": "string", "title": "Base DN", "placeholder": "DC=domain,DC=local"},
            "use_ssl": {"type": "boolean", "title": "Utiliser SSL (LDAPS)", "default": False},
            "domain": {"type": "string", "title": "Domaine", "placeholder": "domain.local"}
        }
    },
    ConnectorSubtype.KEYCLOAK: {
        "type": "object",
        "required": ["server_url", "realm", "client_id", "client_secret"],
        "properties": {
            "server_url": {"type": "string", "title": "URL Serveur", "format": "uri", "placeholder": "https://keycloak.example.com"},
            "realm": {"type": "string", "title": "Realm", "default": "master"},
            "client_id": {"type": "string", "title": "Client ID"},
            "client_secret": {"type": "string", "title": "Client Secret", "format": "password"},
            "admin_username": {"type": "string", "title": "Admin Username (optionnel)"},
            "admin_password": {"type": "string", "title": "Admin Password", "format": "password"},
            "verify_ssl": {"type": "boolean", "title": "Verifier SSL", "default": True}
        }
    },
    ConnectorSubtype.FIREBASE: {
        "type": "object",
        "required": ["project_id", "service_account_json"],
        "properties": {
            "project_id": {"type": "string", "title": "Project ID"},
            "service_account_json": {"type": "string", "title": "Service Account JSON", "format": "textarea"}
        }
    },
    ConnectorSubtype.GLPI: {
        "type": "object",
        "required": ["url", "app_token", "user_token"],
        "properties": {
            "url": {"type": "string", "title": "URL GLPI", "format": "uri"},
            "app_token": {"type": "string", "title": "App Token", "format": "password"},
            "user_token": {"type": "string", "title": "User Token", "format": "password"}
        }
    },
    ConnectorSubtype.GENERIC_REST: {
        "type": "object",
        "required": ["base_url", "auth_type"],
        "properties": {
            "base_url": {"type": "string", "title": "URL de base", "format": "uri"},
            "auth_type": {"type": "string", "title": "Type d'authentification", "enum": ["none", "basic", "bearer", "api_key"], "default": "none"},
            "username": {"type": "string", "title": "Utilisateur (pour basic)"},
            "password": {"type": "string", "title": "Mot de passe (pour basic)", "format": "password"},
            "api_key": {"type": "string", "title": "Cle API", "format": "password"},
            "api_key_header": {"type": "string", "title": "Header de la cle API", "default": "X-API-Key"},
            "bearer_token": {"type": "string", "title": "Token Bearer", "format": "password"},
            "timeout": {"type": "integer", "title": "Timeout (secondes)", "default": 30},
            "verify_ssl": {"type": "boolean", "title": "Verifier SSL", "default": True}
        }
    },
    ConnectorSubtype.ODOO: {
        "type": "object",
        "required": ["url", "database", "username", "password"],
        "properties": {
            "url": {"type": "string", "title": "URL Odoo", "format": "uri", "placeholder": "http://odoo:8069"},
            "database": {"type": "string", "title": "Base de donnees"},
            "username": {"type": "string", "title": "Utilisateur"},
            "password": {"type": "string", "title": "Mot de passe / API Key", "format": "password"},
            "timeout": {"type": "integer", "title": "Timeout (secondes)", "default": 30}
        }
    }
}

# Mapping type -> subtypes
CONNECTOR_TYPE_SUBTYPES = {
    ConnectorType.SQL: [ConnectorSubtype.POSTGRESQL, ConnectorSubtype.MYSQL, ConnectorSubtype.ORACLE, ConnectorSubtype.SQLSERVER, ConnectorSubtype.MARIADB],
    ConnectorType.LDAP: [ConnectorSubtype.OPENLDAP, ConnectorSubtype.ACTIVE_DIRECTORY, ConnectorSubtype.FREEIPA],
    ConnectorType.REST: [ConnectorSubtype.KEYCLOAK, ConnectorSubtype.FIREBASE, ConnectorSubtype.GLPI, ConnectorSubtype.GENERIC_REST],
    ConnectorType.ERP: [ConnectorSubtype.ODOO, ConnectorSubtype.SAP]
}

# Informations sur les types de connecteurs
CONNECTOR_TYPE_INFO = {
    ConnectorSubtype.POSTGRESQL: {"name": "PostgreSQL", "icon": "database", "description": "Base de donnees PostgreSQL"},
    ConnectorSubtype.MYSQL: {"name": "MySQL", "icon": "database", "description": "Base de donnees MySQL"},
    ConnectorSubtype.ORACLE: {"name": "Oracle", "icon": "database", "description": "Base de donnees Oracle"},
    ConnectorSubtype.SQLSERVER: {"name": "SQL Server", "icon": "database", "description": "Microsoft SQL Server"},
    ConnectorSubtype.MARIADB: {"name": "MariaDB", "icon": "database", "description": "Base de donnees MariaDB"},
    ConnectorSubtype.OPENLDAP: {"name": "OpenLDAP", "icon": "users", "description": "Serveur OpenLDAP"},
    ConnectorSubtype.ACTIVE_DIRECTORY: {"name": "Active Directory", "icon": "users", "description": "Microsoft Active Directory"},
    ConnectorSubtype.FREEIPA: {"name": "FreeIPA", "icon": "users", "description": "Red Hat FreeIPA"},
    ConnectorSubtype.KEYCLOAK: {"name": "Keycloak", "icon": "shield", "description": "Keycloak IAM"},
    ConnectorSubtype.FIREBASE: {"name": "Firebase", "icon": "flame", "description": "Google Firebase Auth"},
    ConnectorSubtype.GLPI: {"name": "GLPI", "icon": "server", "description": "GLPI IT Management"},
    ConnectorSubtype.GENERIC_REST: {"name": "API REST", "icon": "globe", "description": "API REST generique"},
    ConnectorSubtype.ODOO: {"name": "Odoo", "icon": "box", "description": "ERP Odoo"},
    ConnectorSubtype.SAP: {"name": "SAP", "icon": "building", "description": "SAP ERP (bientot)"}
}


# Request/Response Schemas
class ConnectorCreate(BaseModel):
    """Schema pour creer un connecteur."""
    name: str
    connector_type: ConnectorType
    connector_subtype: ConnectorSubtype
    display_name: str
    description: Optional[str] = None
    configuration: Dict[str, Any]
    is_active: bool = True


class ConnectorUpdate(BaseModel):
    """Schema pour modifier un connecteur."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ConnectorResponse(BaseModel):
    """Schema de reponse pour un connecteur."""
    id: str
    name: str
    connector_type: ConnectorType
    connector_subtype: ConnectorSubtype
    display_name: str
    description: Optional[str]
    is_active: bool
    configuration: Dict[str, Any]  # Credentials masques
    last_health_status: HealthStatus
    last_health_check: Optional[datetime]
    last_health_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class ConnectorListResponse(BaseModel):
    """Schema pour la liste des connecteurs."""
    id: str
    name: str
    connector_type: ConnectorType
    connector_subtype: ConnectorSubtype
    display_name: str
    description: Optional[str] = None
    is_active: bool
    configuration: Dict[str, Any]  # Credentials masques
    last_health_status: HealthStatus
    last_health_check: Optional[datetime]


class ConnectorTestRequest(BaseModel):
    """Schema pour tester une config avant sauvegarde."""
    connector_type: ConnectorType
    connector_subtype: ConnectorSubtype
    configuration: Dict[str, Any]


class ConnectorTestResult(BaseModel):
    """Resultat d'un test de connexion."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None


class ConnectorTypeInfo(BaseModel):
    """Information sur un type de connecteur."""
    type: ConnectorType
    subtype: ConnectorSubtype
    name: str
    icon: str
    description: str
    config_schema: Dict[str, Any]
