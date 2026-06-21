"""
Configuration de la Gateway IAM via variables d'environnement.

Utilise pydantic-settings pour charger automatiquement les variables
d'environnement et le fichier .env. Valeurs par defaut pour dev local.

Sections :
  - Application : APP_NAME, DEBUG, SECRET_KEY
  - Database : DATABASE_URL (PostgreSQL asyncpg)
  - Redis : REDIS_URL (cache, sessions, token blacklist)
  - LDAP : host, port, bind DN, base DN
  - SQL Target : base cible pour le provisionnement
  - Odoo : URL, DB, user, password (XML-RPC)
  - MidPoint : URL, user, password, MIDPOINT_ENABLED flag
  - Qdrant : URL (recherche semantique audit)
  - Email/SMTP : configuration envoi notifications
"""
import secrets as _secrets
import warnings
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from typing import List


# Known insecure placeholder secret values that must never reach production.
_INSECURE_SECRETS = frozenset({
    "",
    "change-me-in-production",
    "change-me-in-production-use-openssl-rand-hex-32",
    "your-secret-key-change-in-production",
    "jwt-secret-key-change-in-production",
    "jwt-secret-change-in-production",
})


class Settings(BaseSettings):
    """Configuration principale de l'application."""

    # Application
    APP_NAME: str = "Gateway IAM"
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str = Field(default="")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://gateway:gateway@localhost:5434/gateway"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # MidPoint - Hub central IAM
    MIDPOINT_URL: str = Field(default="http://midpoint-core:8080/midpoint")
    MIDPOINT_USER: str = Field(default="administrator")
    MIDPOINT_PASSWORD: str = Field(default="5ecr3t")
    MIDPOINT_ENABLED: bool = Field(default=True)  # Use MidPoint as central hub
    MIDPOINT_VERIFY_SSL: bool = Field(default=True)  # Verify TLS certs on MidPoint REST calls
    MIDPOINT_WEBHOOK_SECRET: str = Field(default="")  # HMAC shared secret for inbound MidPoint webhooks

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
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"]
    )

    # JWT
    JWT_SECRET_KEY: str = Field(default="")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MINUTES: int = Field(default=60)
    JWT_ISSUER: str = Field(default="iam-gateway")
    JWT_AUDIENCE: str = Field(default="iam-gateway")
    # Password hashing
    BCRYPT_ROUNDS: int = Field(default=12)

    # Workflow
    WORKFLOW_DEFAULT_TIMEOUT_HOURS: int = Field(default=72)
    WORKFLOW_MAX_LEVELS: int = Field(default=5)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    # Email / SMTP
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    FROM_EMAIL: str = Field(default="noreply@iam-gateway.local")
    BASE_URL: str = Field(default="http://localhost:8000")
    DEV_MODE: bool = Field(default=False)

    @model_validator(mode="after")
    def _enforce_secret_strength(self) -> "Settings":
        """
        Fail fast in production when signing secrets are missing or weak.

        In DEBUG mode an ephemeral strong secret is generated so local dev and
        tests still work without committing real secrets; in non-DEBUG mode a
        missing or placeholder secret raises at startup, so no insecure default
        can silently ship to production and enable JWT forgery.
        """
        for name in ("SECRET_KEY", "JWT_SECRET_KEY"):
            value = getattr(self, name) or ""
            if value not in _INSECURE_SECRETS and len(value) >= 32:
                continue
            if self.DEBUG:
                setattr(self, name, _secrets.token_urlsafe(48))
                warnings.warn(
                    f"{name} was unset/weak; generated an ephemeral DEBUG secret. "
                    f"Set a strong {name} via the environment for any real deployment.",
                    stacklevel=2,
                )
            else:
                raise RuntimeError(
                    f"{name} must be set to a strong random value (>= 32 chars) when DEBUG is false. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
                )
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
