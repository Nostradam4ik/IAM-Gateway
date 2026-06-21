"""
Gateway IAM - Point d'entree principal de l'application.

Ce module constitue le coeur de la passerelle de provisionnement multi-cibles.
Il configure l'application FastAPI, enregistre tous les routeurs (API endpoints),
gere le cycle de vie (demarrage/arret) des services externes, et expose les
endpoints de sante et racine.

Services geres au demarrage :
    1. PostgreSQL : base de donnees principale (operations, audit, workflows)
    2. MemoryStore : cache local charge depuis PostgreSQL pour lectures rapides
    3. Redis : cache distribue pour sessions JWT et blacklist de tokens
    4. Qdrant : moteur de recherche vectorielle pour logs d'audit semantique
    5. APScheduler : planificateur de taches periodiques (reconciliation, sync)
"""
import time
import uuid
import contextvars
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

# Import de tous les modules API definissant les routeurs REST
from app.api import provision, rules, workflow, reconcile, ai_assistant, admin, live_comparison, permissions, connectors, webhooks, midpoint, scheduler, ldap_groups, users
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.memory_store import memory_store
from app.core.redis_client import redis_client
from app.core.qdrant_store import qdrant_store
from app.services.scheduler_service import init_scheduler, shutdown_scheduler

logger = structlog.get_logger()

# Identifiant de correlation propage par requete (logs + en-tete X-Request-ID)
_request_id_ctx: contextvars.ContextVar = contextvars.ContextVar("request_id", default=None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire du cycle de vie de l'application (startup/shutdown).

    Utilise le pattern asynccontextmanager de FastAPI :
    - Code avant 'yield' = demarrage (initialisation des services)
    - Code apres 'yield' = arret (liberation des ressources)

    Ordre de demarrage : Logs -> PostgreSQL -> Cache -> Redis -> Qdrant -> Scheduler
    Ordre d'arret : Scheduler -> Redis
    """
    # --- PHASE DE DEMARRAGE ---
    setup_logging()
    logger.info("Starting Gateway IAM", version=app.version)
    # Initialiser PostgreSQL (creation des tables via migrations si besoin)
    await init_db()
    # Charger le cache local depuis PostgreSQL (operations, audits, workflows)
    # Cela evite des requetes SQL pour chaque lecture dans l'API
    await memory_store.ensure_cache_loaded()
    logger.info("Database cache loaded successfully")
    # Connecter Redis pour les sessions JWT et la blacklist de tokens revoques
    redis_ok = await redis_client.connect()
    logger.info("Redis connection", status="connected" if redis_ok else "unavailable")
    # Connecter Qdrant pour la recherche semantique dans les logs d'audit
    qdrant_ok = await qdrant_store.connect()
    logger.info("Qdrant connection", status="connected" if qdrant_ok else "unavailable")
    # Demarrer APScheduler pour les taches periodiques (sync Odoo->MidPoint, etc.)
    init_scheduler()
    logger.info("Scheduler initialized")
    yield  # L'application tourne ici jusqu'a l'arret
    # --- PHASE D'ARRET ---
    shutdown_scheduler()  # Arreter le scheduler (attendre fin des taches en cours)
    await redis_client.close()  # Fermer la connexion Redis
    logger.info("Shutting down Gateway IAM")


app = FastAPI(
    title="Gateway IAM - Passerelle de Provisionnement",
    description="""
    Passerelle intelligente pour le provisionnement multi-cibles des identites.

    ## Fonctionnalites
    * **Provisionnement multi-cibles** : AD/LDAP, SQL, Odoo, GLPI, Keycloak, Firebase
    * **Regles dynamiques** : Calcul d'attributs via YAML/JSON editables
    * **Workflow d'approbation** : Validation pre/post avec N niveaux
    * **Agent IA** : Assistance pour mapping et adaptation
    * **Reconciliation** : Synchronisation automatique avec MidPoint
    * **Audit** : Logs vectoriels avec recherche semantique
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS (Cross-Origin Resource Sharing)
# Necessaire pour que le frontend React (port 3000/80) communique avec le backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Genere/propage un X-Request-ID, le lie aux logs et journalise chaque requete."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    _request_id_ctx.set(request_id)
    clear_contextvars()
    bind_contextvars(request_id=request_id, method=request.method, path=request.url.path)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error("Unhandled exception", error=str(exc), duration_ms=duration_ms, exc_info=True)
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )
    response.headers["X-Request-ID"] = request_id
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info("request", status_code=response.status_code, duration_ms=duration_ms)
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Reponse d'erreur coherente pour les HTTPException (conserve 'detail')."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": _request_id_ctx.get()},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Reponse coherente pour les erreurs de validation (422)."""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "request_id": _request_id_ctx.get()},
    )


# =============================================================================
# ENREGISTREMENT DES ROUTEURS (ENDPOINTS API)
# Chaque routeur correspond a un module fonctionnel de la gateway.
# =============================================================================
app.include_router(provision.router, prefix="/api/v1/provision", tags=["Provisionnement"])  # CRUD comptes sur systemes cibles
app.include_router(rules.router, prefix="/api/v1/rules", tags=["Regles"])  # Regles de mapping d'attributs Jinja2
app.include_router(workflow.router, prefix="/api/v1/workflow", tags=["Workflow"])  # Approbation multi-niveaux
app.include_router(reconcile.router, prefix="/api/v1/reconcile", tags=["Reconciliation"])  # Sync et divergences
app.include_router(ai_assistant.router, prefix="/api/v1/ai", tags=["Agent IA"])  # Assistant IA (necessite cle API)
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"])  # Auth, statut, arret urgence
app.include_router(live_comparison.router, prefix="/api/v1/live", tags=["Comparaison Temps Reel"])  # Vue live Odoo/LDAP/SQL
app.include_router(permissions.router, prefix="/api/v1/permissions", tags=["Niveaux de Droits"])  # Niveaux 1-5
app.include_router(connectors.router, prefix="/api/v1/connectors", tags=["Connecteurs"])  # CRUD connecteurs dynamiques
app.include_router(webhooks.router, tags=["Webhooks MidPoint"])  # Notifications entrantes MidPoint
app.include_router(midpoint.router, prefix="/api/v1", tags=["MidPoint Orchestration"])  # Pilotage MidPoint REST
app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["Planification Sync"])  # Jobs APScheduler
app.include_router(ldap_groups.router, prefix="/api/v1", tags=["Groupes LDAP"])  # Gestion groupes LDAP
app.include_router(users.router, prefix="/api/v1/users", tags=["Gestion Utilisateurs"])  # CRUD utilisateurs gateway


@app.get("/health", tags=["Health"])
async def health_check():
    """Verification de l'etat de la gateway."""
    return {
        "status": "healthy",
        "version": app.version,
        "service": "Gateway IAM"
    }


@app.get("/", tags=["Root"])
async def root():
    """Point d'entree racine."""
    return {
        "message": "Gateway IAM - Passerelle de Provisionnement Multi-Cibles",
        "docs": "/docs",
        "health": "/health"
    }
