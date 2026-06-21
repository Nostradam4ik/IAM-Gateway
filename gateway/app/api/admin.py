"""
API d'administration de la Gateway IAM.

Ce module gere :
    - Authentification : login OAuth2 avec generation de tokens JWT
    - Gestion de sessions : logout via blacklist Redis des JTI
    - Statut systeme : verification en temps reel de LDAP, MidPoint, Redis
    - Arret d'urgence : desactivation immediate du provisionnement
    - Reprise : reactivation du provisionnement apres un arret
    - Audit : recherche et consultation des logs d'audit
    - Configuration : recuperation de la config gateway (sans secrets)
    - Metriques : statistiques d'operations et de workflows

Authentification :
    Utilise un store temporaire en memoire (TEMP_USERS) avec hachage bcrypt lazy.
    Les mots de passe ne sont haches qu'a la premiere utilisation pour eviter
    le cout du hachage au demarrage.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import timedelta
import structlog

from app.core.security import (
    get_current_user,
    require_role,
    create_access_token,
    verify_password,
    get_password_hash
)
from app.core.config import settings
from app.core.database import get_session
from app.core.memory_store import memory_store
from app.core.redis_client import redis_client
from app.services.audit_service import AuditService
from app.models.audit import AuditSearchRequest, AuditSearchResponse

router = APIRouter()
logger = structlog.get_logger()


# =============================================================================
# STORE TEMPORAIRE D'UTILISATEURS
# En production, remplacer par une requete vers la table gateway_users.
# Les mots de passe sont stockes en clair ici et haches a la premiere utilisation
# (lazy hashing) pour eviter le cout du bcrypt au demarrage.
# =============================================================================
_TEMP_USER_PASSWORDS = {
    "admin": "admin123",
    "operator": "operator123"
}

TEMP_USERS = {
    "admin": {
        "username": "admin",
        "password_hash": None,  # Will be lazily hashed
        "roles": ["admin", "iam_engineer"]
    },
    "operator": {
        "username": "operator",
        "password_hash": None,  # Will be lazily hashed
        "roles": ["operator"]
    }
}

def _ensure_password_hashed(username: str):
    """Lazily hash password on first use."""
    if TEMP_USERS[username]["password_hash"] is None:
        TEMP_USERS[username]["password_hash"] = get_password_hash(_TEMP_USER_PASSWORDS[username])


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str
    roles: List[str] = ["operator"]


class UserResponse(BaseModel):
    username: str
    roles: List[str]


class SystemStatusResponse(BaseModel):
    provisioning_enabled: bool
    services_status: Dict[str, str]
    pending_operations: int
    pending_approvals: int
    last_reconciliation: Optional[str]


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Authentification et obtention d'un token JWT."""
    user = TEMP_USERS.get(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ensure password is hashed
    _ensure_password_hashed(form_data.username)

    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "roles": user["roles"]},
        expires_delta=access_token_expires
    )

    logger.info("User logged in", username=form_data.username)

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Recupere les informations de l'utilisateur connecte."""
    return UserResponse(
        username=current_user["username"],
        roles=current_user["roles"]
    )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user)
):
    """Deconnexion - revoque le token JWT via Redis blacklist."""
    jti = current_user.get("jti")
    if jti:
        ttl = settings.JWT_EXPIRE_MINUTES * 60
        await redis_client.blacklist_token(jti, ttl_seconds=ttl)
        logger.info("User logged out", username=current_user["username"])

    return {"status": "success", "message": "Deconnecte avec succes"}


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere le statut global du systeme."""
    audit_service = AuditService(session)

    # Recuperer l'etat du provisionnement depuis la table system_states
    # Si "false", le systeme est en arret d'urgence (aucune operation traitee)
    provisioning_enabled = await audit_service.get_system_state("provisioning_enabled", "true")

    # Verifier le statut Redis reel (ping)
    redis_health = await redis_client.health_check()
    redis_status = redis_health.get("status", "unknown")

    # Verifier LDAP reel - tente un bind LDAP pour confirmer la connexion
    ldap_status = "error"
    try:
        from app.connectors.ldap_connector import LDAPConnector
        ldap = LDAPConnector()
        await ldap.test_connection()
        ldap_status = "healthy"
    except Exception:
        pass  # En cas d'erreur, le statut reste "error"

    # Verifier MidPoint reel - appel REST /ws/rest/self avec auth basique
    midpoint_status = "error"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0, verify=settings.MIDPOINT_VERIFY_SSL) as client:
            resp = await client.get(
                f"{settings.MIDPOINT_URL}/ws/rest/self",
                auth=(settings.MIDPOINT_USER, settings.MIDPOINT_PASSWORD)
            )
            if resp.status_code in (200, 240):
                midpoint_status = "healthy"
    except Exception:
        pass  # MidPoint non joignable ou authentification echouee

    return SystemStatusResponse(
        provisioning_enabled=provisioning_enabled == "true",
        services_status={
            "database": "healthy",
            "redis": redis_status,
            "ldap": ldap_status,
            "midpoint": midpoint_status
        },
        pending_operations=0,
        pending_approvals=0,
        last_reconciliation=None
    )


@router.post("/emergency-stop")
async def emergency_stop(
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """
    BOUTON ROUGE - Desactive immediatement le provisionnement.

    Toutes les operations en cours sont suspendues.
    Les nouvelles requetes sont rejetees.
    """
    audit_service = AuditService(session)

    await audit_service.set_system_state(
        key="provisioning_enabled",
        value="false",
        updated_by=current_user["username"]
    )

    await audit_service.log_config_change(
        action="emergency_stop",
        user=current_user,
        details={"reason": "Emergency stop activated"}
    )

    logger.warning(
        "EMERGENCY STOP ACTIVATED",
        user=current_user["username"]
    )

    return {
        "status": "stopped",
        "message": "Provisioning system disabled. All operations suspended."
    }


@router.post("/resume")
async def resume_provisioning(
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Reactive le systeme de provisionnement."""
    audit_service = AuditService(session)

    await audit_service.set_system_state(
        key="provisioning_enabled",
        value="true",
        updated_by=current_user["username"]
    )

    await audit_service.log_config_change(
        action="resume_provisioning",
        user=current_user,
        details={"reason": "System resumed"}
    )

    logger.info(
        "Provisioning system resumed",
        user=current_user["username"]
    )

    return {"status": "active", "message": "Provisioning system re-enabled"}


@router.post("/audit/search", response_model=AuditSearchResponse)
async def search_audit_logs(
    request: AuditSearchRequest,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recherche dans les logs d'audit."""
    audit_service = AuditService(session)
    return await audit_service.search_logs(request)


@router.get("/audit/recent")
async def get_recent_audit_logs(
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere les logs d'audit recents."""
    # Return from memory store
    return memory_store.get_recent_logs(limit)


@router.get("/config")
async def get_gateway_config(
    current_user: dict = Depends(require_role(["admin"]))
):
    """Recupere la configuration actuelle de la gateway (sans secrets)."""
    return {
        "midpoint_url": settings.MIDPOINT_URL,
        "ldap_host": settings.LDAP_HOST,
        "ldap_port": settings.LDAP_PORT,
        "odoo_url": settings.ODOO_URL,
        "keycloak_url": settings.KEYCLOAK_URL,
        "workflow_default_timeout": settings.WORKFLOW_DEFAULT_TIMEOUT_HOURS,
        "workflow_max_levels": settings.WORKFLOW_MAX_LEVELS
    }


@router.get("/connectors/status")
async def get_connectors_status(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Verifie le statut de connexion de tous les connecteurs."""
    from app.connectors.ldap_connector import LDAPConnector
    from app.connectors.sql_connector import SQLConnector
    from app.connectors.odoo_connector import OdooConnector

    statuses = {}

    # Test LDAP
    try:
        ldap = LDAPConnector()
        await ldap.test_connection()
        statuses["ldap"] = {"status": "connected", "error": None}
    except Exception as e:
        statuses["ldap"] = {"status": "error", "error": str(e)}

    # Test SQL
    try:
        sql = SQLConnector()
        await sql.test_connection()
        statuses["sql"] = {"status": "connected", "error": None}
    except Exception as e:
        statuses["sql"] = {"status": "error", "error": str(e)}

    # Test Odoo
    try:
        odoo = OdooConnector()
        await odoo.test_connection()
        statuses["odoo"] = {"status": "connected", "error": None}
    except Exception as e:
        statuses["odoo"] = {"status": "error", "error": str(e)}

    return statuses


@router.get("/metrics")
async def get_metrics(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere les metriques de la gateway."""
    audit_service = AuditService(session)

    return await audit_service.get_metrics()
