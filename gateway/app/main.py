"""
Gateway IAM - Point d'entree principal
Passerelle de provisionnement multi-cibles avec IA
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.api import provision, rules, workflow, reconcile, ai_assistant, admin
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the application."""
    setup_logging()
    logger.info("Starting Gateway IAM", version=app.version)
    await init_db()
    yield
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(provision.router, prefix="/api/v1/provision", tags=["Provisionnement"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["Regles"])
app.include_router(workflow.router, prefix="/api/v1/workflow", tags=["Workflow"])
app.include_router(reconcile.router, prefix="/api/v1/reconcile", tags=["Reconciliation"])
app.include_router(ai_assistant.router, prefix="/api/v1/ai", tags=["Agent IA"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"])


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
