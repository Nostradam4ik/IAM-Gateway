"""
API de gestion des connecteurs dynamiques.
Permet aux administrateurs de configurer les connecteurs via l'interface.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import structlog

from app.models.connector import (
    ConnectorType, ConnectorCreate, ConnectorUpdate,
    ConnectorResponse, ConnectorListResponse, ConnectorTestRequest,
    ConnectorTestResult, ConnectorTypeInfo
)
from app.core.security import get_current_user, require_role
from app.core.database import get_session
from app.services.connector_management_service import ConnectorManagementService

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=List[ConnectorListResponse])
async def list_connectors(
    connector_type: Optional[ConnectorType] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Liste tous les connecteurs configures."""
    service = ConnectorManagementService(session)
    return await service.list_connectors(
        connector_type=connector_type,
        is_active=is_active
    )


@router.get("/types", response_model=List[ConnectorTypeInfo])
async def get_connector_types(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Retourne la liste des types de connecteurs disponibles avec leurs schemas."""
    service = ConnectorManagementService(session)
    return service.get_connector_types()


@router.get("/health")
async def get_all_health_status(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Retourne le statut de sante de tous les connecteurs actifs."""
    service = ConnectorManagementService(session)
    connectors = await service.list_connectors(is_active=True)

    health_status = {}
    for connector in connectors:
        health_status[connector.name] = {
            "id": connector.id,
            "display_name": connector.display_name,
            "type": connector.connector_type.value,
            "subtype": connector.connector_subtype.value,
            "status": connector.last_health_status.value,
            "last_check": connector.last_health_check.isoformat() if connector.last_health_check else None
        }

    return health_status


@router.get("/{connector_id}", response_model=ConnectorResponse)
async def get_connector(
    connector_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere les details d'un connecteur."""
    service = ConnectorManagementService(session)
    connector = await service.get_connector(connector_id)

    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connecteur {connector_id} non trouve"
        )

    return connector


@router.post("/", response_model=ConnectorResponse)
async def create_connector(
    data: ConnectorCreate,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Cree un nouveau connecteur."""
    service = ConnectorManagementService(session)

    try:
        connector = await service.create_connector(
            data=data,
            created_by=current_user["username"]
        )
        logger.info(
            "Connector created",
            connector_id=connector.id,
            name=data.name,
            user=current_user["username"]
        )
        return connector

    except Exception as e:
        logger.error("Failed to create connector", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{connector_id}", response_model=ConnectorResponse)
async def update_connector(
    connector_id: str,
    data: ConnectorUpdate,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Met a jour un connecteur existant."""
    service = ConnectorManagementService(session)

    connector = await service.get_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connecteur {connector_id} non trouve"
        )

    try:
        updated = await service.update_connector(
            connector_id=connector_id,
            data=data,
            updated_by=current_user["username"]
        )
        logger.info(
            "Connector updated",
            connector_id=connector_id,
            user=current_user["username"]
        )
        return updated

    except Exception as e:
        logger.error("Failed to update connector", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{connector_id}")
async def delete_connector(
    connector_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Supprime un connecteur."""
    service = ConnectorManagementService(session)

    connector = await service.get_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connecteur {connector_id} non trouve"
        )

    deleted = await service.delete_connector(connector_id)
    if deleted:
        logger.info(
            "Connector deleted",
            connector_id=connector_id,
            user=current_user["username"]
        )
        return {"message": f"Connecteur {connector_id} supprime"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Echec de la suppression"
        )


@router.post("/{connector_id}/test", response_model=ConnectorTestResult)
async def test_connector(
    connector_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Teste la connexion d'un connecteur existant."""
    service = ConnectorManagementService(session)

    connector = await service.get_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connecteur {connector_id} non trouve"
        )

    result = await service.test_connection(connector_id)

    # Mettre a jour le statut de sante
    from app.models.connector import HealthStatus
    status_value = HealthStatus.HEALTHY if result.success else HealthStatus.UNHEALTHY
    error = None if result.success else result.message
    await service.update_health_status(connector_id, status_value, error)

    logger.info(
        "Connector tested",
        connector_id=connector_id,
        success=result.success,
        user=current_user["username"]
    )

    return result


@router.post("/test-preview", response_model=ConnectorTestResult)
async def test_connector_preview(
    data: ConnectorTestRequest,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Teste une configuration avant de la sauvegarder."""
    service = ConnectorManagementService(session)

    result = await service.test_connection_preview(
        connector_type=data.connector_type,
        connector_subtype=data.connector_subtype,
        configuration=data.configuration
    )

    logger.info(
        "Connector preview tested",
        connector_type=data.connector_type.value,
        connector_subtype=data.connector_subtype.value,
        success=result.success,
        user=current_user["username"]
    )

    return result


@router.post("/{connector_id}/toggle", response_model=ConnectorResponse)
async def toggle_connector(
    connector_id: str,
    is_active: bool,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Active ou desactive un connecteur."""
    service = ConnectorManagementService(session)

    connector = await service.get_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connecteur {connector_id} non trouve"
        )

    updated = await service.toggle_connector(connector_id, is_active)
    logger.info(
        "Connector toggled",
        connector_id=connector_id,
        is_active=is_active,
        user=current_user["username"]
    )

    return updated


@router.post("/health-check")
async def run_health_checks(
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Execute les tests de sante sur tous les connecteurs actifs."""
    service = ConnectorManagementService(session)

    results = await service.run_health_checks()

    summary = {
        "total": len(results),
        "healthy": sum(1 for r in results.values() if r.success),
        "unhealthy": sum(1 for r in results.values() if not r.success),
        "results": {
            conn_id: {
                "success": result.success,
                "message": result.message,
                "response_time_ms": result.response_time_ms
            }
            for conn_id, result in results.items()
        }
    }

    logger.info(
        "Health checks completed",
        total=summary["total"],
        healthy=summary["healthy"],
        unhealthy=summary["unhealthy"],
        user=current_user["username"]
    )

    return summary
