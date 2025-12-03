"""
Modeles pour l'audit et les logs
"""
from sqlmodel import SQLModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class AuditEventType(str, Enum):
    """Type d'evenement d'audit."""
    PROVISION_REQUEST = "provision_request"
    PROVISION_SUCCESS = "provision_success"
    PROVISION_FAILURE = "provision_failure"
    PROVISION_ROLLBACK = "provision_rollback"
    RULE_EXECUTION = "rule_execution"
    RULE_UPDATE = "rule_update"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_APPROVAL = "workflow_approval"
    WORKFLOW_REJECTION = "workflow_rejection"
    WORKFLOW_COMPLETE = "workflow_complete"
    RECONCILIATION_START = "reconciliation_start"
    RECONCILIATION_COMPLETE = "reconciliation_complete"
    CONFIG_CHANGE = "config_change"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    AI_QUERY = "ai_query"
    SYSTEM_ERROR = "system_error"


class AuditSeverity(str, Enum):
    """Severite d'un evenement."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Database Models
class AuditLog(SQLModel, table=True):
    """Log d'audit pour tracabilite."""
    __tablename__ = "audit_logs"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    event_type: AuditEventType
    severity: AuditSeverity = Field(default=AuditSeverity.INFO)
    operation_id: Optional[str] = Field(default=None, index=True)
    account_id: Optional[str] = Field(default=None, index=True)
    target_system: Optional[str] = None
    actor: Optional[str] = None
    action: str
    details: str  # JSON
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class VectorLogEntry(SQLModel, table=True):
    """Entree de log pour recherche vectorielle."""
    __tablename__ = "vector_log_entries"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    audit_log_id: str = Field(index=True)
    summary: str  # Human readable summary
    vector_id: Optional[str] = None  # ID in vector store
    embedding_model: str = "all-MiniLM-L6-v2"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemState(SQLModel, table=True):
    """Etat du systeme (bouton rouge, etc.)."""
    __tablename__ = "system_states"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None


# Response Schemas
class AuditLogResponse(SQLModel):
    """Reponse de log d'audit."""
    id: str
    event_type: AuditEventType
    severity: AuditSeverity
    operation_id: Optional[str]
    account_id: Optional[str]
    target_system: Optional[str]
    actor: Optional[str]
    action: str
    details: Dict[str, Any]
    created_at: datetime


class AuditSearchRequest(SQLModel):
    """Requete de recherche d'audit."""
    query: Optional[str] = None  # Semantic search
    event_types: Optional[List[AuditEventType]] = None
    account_id: Optional[str] = None
    operation_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


class AuditSearchResponse(SQLModel):
    """Reponse de recherche d'audit."""
    total: int
    results: List[AuditLogResponse]
    semantic_matches: Optional[List[Dict[str, Any]]] = None
