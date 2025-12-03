"""
Modèles de données pour l'agent IA
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class AIQueryRequest(BaseModel):
    """Requete a l'agent IA."""
    query: str
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None


class AIQueryResponse(BaseModel):
    """Reponse de l'agent IA."""
    response: str
    suggested_actions: Optional[List[Dict[str, Any]]] = None
    conversation_id: str
    confidence: float


class MappingSuggestion(BaseModel):
    """Suggestion de mapping d'attribut."""
    source_attribute: str
    target_attribute: str
    transformation: Optional[str] = None
    confidence: float
    rationale: str


class MappingSuggestionRequest(BaseModel):
    """Requete de suggestion de mapping."""
    source_attributes: List[str]
    target_system: str
    target_schema: List[str]
    identity_type: Optional[str] = "employee"


class MappingSuggestionResponse(BaseModel):
    """Reponse avec suggestions de mapping."""
    suggestions: List[MappingSuggestion]
    completeness_score: float
    warnings: Optional[List[str]] = None


class ConnectorGenerationRequest(BaseModel):
    """Requete de generation de connecteur."""
    target_system: str
    connection_params: Dict[str, Any]
    operations: List[str]  # create, update, delete, read
    authentication_type: str


class ConnectorGenerationResponse(BaseModel):
    """Reponse avec code du connecteur."""
    connector_code: str
    usage_instructions: str
    dependencies: List[str]
    warnings: Optional[List[str]] = None


class ErrorAnalysisRequest(BaseModel):
    """Requete d'analyse d'erreur."""
    error_message: str
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    operation_type: Optional[str] = None


class ErrorAnalysisResponse(BaseModel):
    """Reponse avec analyse d'erreur."""
    root_cause: str
    suggested_fixes: List[str]
    related_issues: Optional[List[str]] = None
    confidence: float
