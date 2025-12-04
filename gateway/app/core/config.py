"""
Configuration de la Gateway IAM
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """Configuration principale de l'application."""

    # Application
    APP_NAME: str = "Gateway IAM"
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://gateway:gateway@localhost:5434/gateway"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # MidPoint
    MIDPOINT_URL: str = Field(default="http://midpoint-core:8080/midpoint")
    MIDPOINT_USER: str = Field(default="administrator")
    MIDPOINT_PASSWORD: str = Field(default="Nost1")

    # LDAP/AD
    LDAP_HOST: str = Field(default="localhost")
    LDAP_PORT: int = Field(default=10389)
    LDAP_BIND_DN: str = Field(default="cn=admin,dc=example,dc=com")
    LDAP_BIND_PASSWORD: str = Field(default="secret")
    LDAP_BASE_DN: str = Field(default="dc=example,dc=com")

    # Odoo
    ODOO_URL: str = Field(default="http://localhost:8069")
    ODOO_DB: str = Field(default="odoo")
    ODOO_USER: str = Field(default="admin")
    ODOO_PASSWORD: str = Field(default="admin")

    # SQL Target (Intranet)
    INTRANET_DB_URL: str = Field(
        default="postgresql://intranet:intranet@localhost:55432/intranet"
    )

    # Keycloak
    KEYCLOAK_URL: str = Field(default="http://localhost:8081")
    KEYCLOAK_REALM: str = Field(default="gateway")
    KEYCLOAK_CLIENT_ID: str = Field(default="gateway-client")
    KEYCLOAK_CLIENT_SECRET: str = Field(default="")

    # OpenAI / AI
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo-preview")
    DEEPSEEK_API_KEY: str = Field(default="")

    # Vector Store
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )

    # JWT
    JWT_SECRET_KEY: str = Field(default="jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MINUTES: int = Field(default=60)

    # Workflow
    WORKFLOW_DEFAULT_TIMEOUT_HOURS: int = Field(default=72)
    WORKFLOW_MAX_LEVELS: int = Field(default=5)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
