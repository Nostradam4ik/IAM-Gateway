"""
API de gestion des connecteurs dynamiques.
Permet aux administrateurs de configurer les connecteurs via l'interface.
Inclut la creation automatique des Resources dans MidPoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from app.models.connector import (
    ConnectorType, ConnectorSubtype, ConnectorCreate, ConnectorUpdate,
    ConnectorResponse, ConnectorListResponse, ConnectorTestRequest,
    ConnectorTestResult, ConnectorTypeInfo, MidPointSyncStatus
)
from app.core.security import get_current_user, require_role
from app.core.database import get_session
from app.services.connector_management_service import ConnectorManagementService
from app.services.midpoint_resource_service import midpoint_resource_service

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
    """
    Cree un nouveau connecteur.
    Si auto_create_in_midpoint=True, cree automatiquement la Resource dans MidPoint.
    """
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

        # Auto-create in MidPoint if requested
        if getattr(data, 'auto_create_in_midpoint', True):
            try:
                midpoint_result = await midpoint_resource_service.create_resource_in_midpoint(
                    connector_id=connector.id,
                    connector_name=data.name,
                    connector_subtype=data.connector_subtype,
                    connector_config=data.configuration,
                    display_name=data.display_name,
                    description=data.description
                )

                if midpoint_result.get("success"):
                    # Update connector with MidPoint info
                    await service.update_midpoint_sync_status(
                        connector_id=connector.id,
                        resource_oid=midpoint_result.get("resource_oid"),
                        sync_status=MidPointSyncStatus.SYNCED,
                        error=None
                    )
                    logger.info(
                        "Resource created in MidPoint",
                        connector_id=connector.id,
                        resource_oid=midpoint_result.get("resource_oid")
                    )
                else:
                    await service.update_midpoint_sync_status(
                        connector_id=connector.id,
                        resource_oid=None,
                        sync_status=MidPointSyncStatus.SYNC_ERROR,
                        error=midpoint_result.get("error")
                    )
                    logger.warning(
                        "Failed to create Resource in MidPoint",
                        connector_id=connector.id,
                        error=midpoint_result.get("error")
                    )

                # Refresh connector to get updated fields
                connector = await service.get_connector(connector.id)

            except Exception as mp_error:
                logger.error(
                    "MidPoint sync failed",
                    connector_id=connector.id,
                    error=str(mp_error)
                )
                await service.update_midpoint_sync_status(
                    connector_id=connector.id,
                    resource_oid=None,
                    sync_status=MidPointSyncStatus.SYNC_ERROR,
                    error=str(mp_error)
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


# ==================== MidPoint Sync Endpoints ====================

@router.post("/{connector_id}/sync-to-midpoint")
async def sync_connector_to_midpoint(
    connector_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """
    Synchronise un connecteur avec MidPoint.
    Cree ou met a jour la Resource correspondante dans MidPoint.
    """
    service = ConnectorManagementService(session)

    connector = await service.get_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connecteur {connector_id} non trouve"
        )

    try:
        # Update status to syncing
        await service.update_midpoint_sync_status(
            connector_id=connector_id,
            resource_oid=connector.midpoint_resource_oid,
            sync_status=MidPointSyncStatus.SYNCING,
            error=None
        )

        # Get full configuration (unmasked)
        full_config = await service.get_connector_config(connector_id)

        if connector.midpoint_resource_oid:
            # Update existing resource
            result = await midpoint_resource_service.update_resource_in_midpoint(
                resource_oid=connector.midpoint_resource_oid,
                connector_subtype=connector.connector_subtype,
                connector_config=full_config
            )
        else:
            # Create new resource
            result = await midpoint_resource_service.create_resource_in_midpoint(
                connector_id=connector_id,
                connector_name=connector.name,
                connector_subtype=connector.connector_subtype,
                connector_config=full_config,
                display_name=connector.display_name,
                description=connector.description
            )

        if result.get("success"):
            await service.update_midpoint_sync_status(
                connector_id=connector_id,
                resource_oid=result.get("resource_oid") or connector.midpoint_resource_oid,
                sync_status=MidPointSyncStatus.SYNCED,
                error=None
            )
            logger.info(
                "Connector synced to MidPoint",
                connector_id=connector_id,
                resource_oid=result.get("resource_oid"),
                user=current_user["username"]
            )
            return {
                "success": True,
                "message": "Connecteur synchronise avec MidPoint",
                "resource_oid": result.get("resource_oid") or connector.midpoint_resource_oid
            }
        else:
            await service.update_midpoint_sync_status(
                connector_id=connector_id,
                resource_oid=connector.midpoint_resource_oid,
                sync_status=MidPointSyncStatus.SYNC_ERROR,
                error=result.get("error")
            )
            return {
                "success": False,
                "message": "Echec de la synchronisation",
                "error": result.get("error")
            }

    except Exception as e:
        logger.error("Sync to MidPoint failed", connector_id=connector_id, error=str(e))
        await service.update_midpoint_sync_status(
            connector_id=connector_id,
            resource_oid=connector.midpoint_resource_oid,
            sync_status=MidPointSyncStatus.SYNC_ERROR,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{connector_id}/midpoint-status")
async def get_midpoint_resource_status(
    connector_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Recupere le statut de la Resource MidPoint correspondante.
    """
    service = ConnectorManagementService(session)

    connector = await service.get_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connecteur {connector_id} non trouve"
        )

    if not connector.midpoint_resource_oid:
        return {
            "synced": False,
            "message": "Connecteur non synchronise avec MidPoint",
            "sync_status": connector.midpoint_sync_status.value if connector.midpoint_sync_status else "not_synced"
        }

    # Get status from MidPoint
    status_result = await midpoint_resource_service.get_resource_status(
        connector.midpoint_resource_oid
    )

    return {
        "synced": status_result.get("exists", False),
        "resource_oid": connector.midpoint_resource_oid,
        "sync_status": connector.midpoint_sync_status.value if connector.midpoint_sync_status else "unknown",
        "last_sync": connector.midpoint_last_sync.isoformat() if connector.midpoint_last_sync else None,
        "midpoint_status": status_result
    }


@router.post("/{connector_id}/test-midpoint-resource")
async def test_midpoint_resource(
    connector_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """
    Teste la connexion de la Resource MidPoint.
    """
    service = ConnectorManagementService(session)

    connector = await service.get_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connecteur {connector_id} non trouve"
        )

    if not connector.midpoint_resource_oid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connecteur non synchronise avec MidPoint"
        )

    result = await midpoint_resource_service.test_resource_in_midpoint(
        connector.midpoint_resource_oid
    )

    logger.info(
        "MidPoint resource tested",
        connector_id=connector_id,
        resource_oid=connector.midpoint_resource_oid,
        success=result.get("success"),
        user=current_user["username"]
    )

    return result


@router.delete("/{connector_id}/midpoint-resource")
async def delete_midpoint_resource(
    connector_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """
    Supprime la Resource MidPoint correspondante.
    """
    service = ConnectorManagementService(session)

    connector = await service.get_connector(connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connecteur {connector_id} non trouve"
        )

    if not connector.midpoint_resource_oid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connecteur non synchronise avec MidPoint"
        )

    result = await midpoint_resource_service.delete_resource_in_midpoint(
        connector.midpoint_resource_oid
    )

    if result.get("success"):
        # Clear MidPoint info from connector
        await service.update_midpoint_sync_status(
            connector_id=connector_id,
            resource_oid=None,
            sync_status=MidPointSyncStatus.NOT_SYNCED,
            error=None
        )
        logger.info(
            "MidPoint resource deleted",
            connector_id=connector_id,
            user=current_user["username"]
        )
        return {"success": True, "message": "Resource MidPoint supprimee"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Echec de la suppression")
        )


@router.get("/midpoint/resources")
async def list_midpoint_resources(
    current_user: dict = Depends(get_current_user)
):
    """
    Liste toutes les Resources configurees dans MidPoint.
    """
    resources = await midpoint_resource_service.list_midpoint_resources()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(resources),
        "resources": resources
    }
