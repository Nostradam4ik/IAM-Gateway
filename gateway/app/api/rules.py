"""
API de gestion des regles dynamiques
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import json
import structlog

from app.models.rules import (
    Rule,
    RuleDefinition,
    RuleTestRequest,
    RuleTestResponse,
    RuleStatus,
    RuleType,
    PolicyConfig
)
from app.core.security import get_current_user, require_role
from app.core.database import get_session
from app.services.rule_engine import RuleEngine
from app.services.audit_service import AuditService

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=List[Rule])
async def list_rules(
    target_system: Optional[str] = None,
    rule_type: Optional[RuleType] = None,
    status: Optional[RuleStatus] = None,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Liste toutes les regles disponibles."""
    rule_engine = RuleEngine(session)
    rules = await rule_engine.list_rules(
        target_system=target_system,
        rule_type=rule_type,
        status=status
    )
    return rules


@router.post("/", response_model=Rule)
async def create_rule(
    rule: RuleDefinition,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"])),
    session=Depends(get_session)
):
    """Cree une nouvelle regle de calcul."""
    rule_engine = RuleEngine(session)
    audit_service = AuditService(session)

    try:
        new_rule = await rule_engine.create_rule(
            definition=rule,
            created_by=current_user["username"]
        )

        await audit_service.log_rule_change(
            rule_id=new_rule.id,
            action="create",
            user=current_user["username"],
            details=rule.dict()
        )

        logger.info("Rule created", rule_id=new_rule.id, name=rule.name)
        return new_rule

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{rule_id}", response_model=Rule)
async def get_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere une regle par son ID."""
    rule_engine = RuleEngine(session)
    rule = await rule_engine.get_rule(rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )
    return rule


@router.put("/{rule_id}", response_model=Rule)
async def update_rule(
    rule_id: str,
    rule: RuleDefinition,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"])),
    session=Depends(get_session)
):
    """Met a jour une regle existante."""
    rule_engine = RuleEngine(session)
    audit_service = AuditService(session)

    existing = await rule_engine.get_rule(rule_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )

    updated_rule = await rule_engine.update_rule(
        rule_id=rule_id,
        definition=rule,
        updated_by=current_user["username"]
    )

    await audit_service.log_rule_change(
        rule_id=rule_id,
        action="update",
        user=current_user["username"],
        details={"old": existing.dict(), "new": rule.dict()}
    )

    return updated_rule


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Supprime une regle (soft delete)."""
    rule_engine = RuleEngine(session)
    audit_service = AuditService(session)

    existing = await rule_engine.get_rule(rule_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )

    await rule_engine.delete_rule(rule_id)

    await audit_service.log_rule_change(
        rule_id=rule_id,
        action="delete",
        user=current_user["username"],
        details={"rule_name": existing.name}
    )

    return {"message": f"Rule {rule_id} deleted"}


@router.post("/test", response_model=RuleTestResponse)
async def test_rule(
    request: RuleTestRequest,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Teste une regle avec des donnees d'exemple."""
    rule_engine = RuleEngine(session)

    result = await rule_engine.test_rule(
        rule_id=request.rule_id,
        test_data=request.test_data
    )

    return result


@router.get("/{rule_id}/versions")
async def get_rule_versions(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere l'historique des versions d'une regle."""
    rule_engine = RuleEngine(session)
    versions = await rule_engine.get_rule_versions(rule_id)
    return versions


@router.post("/{rule_id}/restore/{version}")
async def restore_rule_version(
    rule_id: str,
    version: int,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"])),
    session=Depends(get_session)
):
    """Restaure une version precedente d'une regle."""
    rule_engine = RuleEngine(session)
    audit_service = AuditService(session)

    restored = await rule_engine.restore_version(rule_id, version)

    await audit_service.log_rule_change(
        rule_id=rule_id,
        action="restore",
        user=current_user["username"],
        details={"restored_version": version}
    )

    return restored


# Policy endpoints
@router.get("/policies/", response_model=List[PolicyConfig])
async def list_policies(
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Liste toutes les politiques de provisionnement."""
    rule_engine = RuleEngine(session)
    return await rule_engine.list_policies()


@router.post("/policies/", response_model=PolicyConfig)
async def create_policy(
    policy: PolicyConfig,
    current_user: dict = Depends(require_role(["admin"])),
    session=Depends(get_session)
):
    """Cree une nouvelle politique."""
    rule_engine = RuleEngine(session)
    return await rule_engine.create_policy(policy, current_user["username"])


@router.get("/policies/{policy_id}", response_model=PolicyConfig)
async def get_policy(
    policy_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere une politique par son ID."""
    rule_engine = RuleEngine(session)
    policy = await rule_engine.get_policy(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found"
        )
    return policy
