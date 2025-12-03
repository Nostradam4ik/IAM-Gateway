"""
API de l'agent IA pour assistance au provisionnement
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
import structlog

from app.core.security import get_current_user
from app.core.database import get_session
from app.services.ai_agent import AIAgent
from app.services.audit_service import AuditService
from app.models.ai import (
    AIQueryRequest,
    AIQueryResponse,
    MappingSuggestionRequest,
    MappingSuggestionResponse,
    MappingSuggestion,
    ConnectorGenerationRequest,
    ConnectorGenerationResponse,
    ErrorAnalysisRequest,
    ErrorAnalysisResponse
)

router = APIRouter()
logger = structlog.get_logger()


@router.post("/query", response_model=AIQueryResponse)
async def query_ai_assistant(
    request: AIQueryRequest,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Interroge l'agent IA pour assistance.

    L'agent peut aider avec:
    - Questions sur le provisionnement
    - Suggestions de regles de mapping
    - Diagnostic de problemes
    - Generation de scripts de connecteurs
    """
    ai_agent = AIAgent(session)
    audit_service = AuditService(session)

    logger.info(
        "AI query received",
        user=current_user["username"],
        query_length=len(request.query)
    )

    try:
        response = await ai_agent.process_query(
            query=request.query,
            context=request.context,
            conversation_id=request.conversation_id,
            user=current_user["username"]
        )

        await audit_service.log_ai_query(
            query=request.query,
            response_summary=response.response[:200],
            user=current_user
        )

        return response

    except Exception as e:
        logger.error("AI query failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI query failed: {str(e)}"
        )


@router.post("/suggest-mappings", response_model=List[MappingSuggestion])
async def suggest_attribute_mappings(
    request: MappingSuggestionRequest,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Suggere des mappings d'attributs entre une source et un systeme cible.

    Utilise l'IA pour analyser les schemas et proposer des correspondances
    intelligentes avec des transformations si necessaire.
    """
    ai_agent = AIAgent(session)

    try:
        suggestions = await ai_agent.suggest_mappings(
            source_schema=request.source_schema,
            target_system=request.target_system,
            existing_mappings=request.existing_mappings
        )

        return suggestions

    except Exception as e:
        logger.error("Mapping suggestion failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mapping suggestion failed: {str(e)}"
        )


@router.post("/generate-connector")
async def generate_connector_code(
    request: ConnectorGenerationRequest,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Genere le code squelette d'un nouveau connecteur.

    L'IA analyse la description du systeme cible et genere:
    - Code Python du connecteur
    - Configuration YAML
    - Tests unitaires de base
    """
    ai_agent = AIAgent(session)

    try:
        generated = await ai_agent.generate_connector(
            system_type=request.target_system_type,
            description=request.system_description,
            api_docs=request.api_documentation,
            sample_data=request.sample_data
        )

        return generated

    except Exception as e:
        logger.error("Connector generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connector generation failed: {str(e)}"
        )


@router.post("/analyze-error")
async def analyze_provisioning_error(
    operation_id: str,
    error_message: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Analyse une erreur de provisionnement et suggere des solutions.
    """
    ai_agent = AIAgent(session)

    analysis = await ai_agent.analyze_error(
        operation_id=operation_id,
        error_message=error_message
    )

    return analysis


@router.post("/explain-rule")
async def explain_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """
    Explique une regle en langage naturel.
    """
    ai_agent = AIAgent(session)

    explanation = await ai_agent.explain_rule(rule_id)

    return {"rule_id": rule_id, "explanation": explanation}


@router.get("/conversations/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Recupere l'historique d'une conversation avec l'IA."""
    ai_agent = AIAgent(session)
    return await ai_agent.get_conversation(conversation_id)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Supprime une conversation."""
    ai_agent = AIAgent(session)
    await ai_agent.delete_conversation(conversation_id)
    return {"message": f"Conversation {conversation_id} deleted"}
