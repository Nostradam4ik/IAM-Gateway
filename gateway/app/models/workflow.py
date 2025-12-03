"""
Modeles pour les workflows d'approbation
"""
from sqlmodel import SQLModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class WorkflowType(str, Enum):
    """Type de workflow."""
    PRE_PROVISIONING = "pre_provisioning"
    POST_PROVISIONING = "post_provisioning"


class ApprovalStatus(str, Enum):
    """Statut d'une approbation."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApproverType(str, Enum):
    """Type d'approbateur."""
    USER = "user"
    ROLE = "role"
    GROUP = "group"
    MANAGER = "manager"
    DEPARTMENT_HEAD = "department_head"
    APP_OWNER = "app_owner"


# Request/Response Schemas
class WorkflowDefinition(SQLModel):
    """Definition d'un workflow."""
    name: str
    description: Optional[str] = None
    workflow_type: WorkflowType
    levels: List[Dict[str, Any]]  # List of approval levels
    timeout_hours: int = 72
    auto_approve_on_timeout: bool = False


class ApprovalRequest(SQLModel):
    """Requete d'approbation."""
    workflow_instance_id: str
    decision: ApprovalStatus
    comments: Optional[str] = None
    approver_id: str


class WorkflowInstanceResponse(SQLModel):
    """Reponse d'instance de workflow."""
    id: str
    workflow_id: str
    operation_id: str
    status: ApprovalStatus
    current_level: int
    total_levels: int
    pending_approvers: List[str]
    history: List[Dict[str, Any]]


# Database Models
class WorkflowConfig(SQLModel, table=True):
    """Configuration de workflow."""
    __tablename__ = "workflow_configs"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    workflow_type: WorkflowType
    levels: str  # JSON array of level configs
    timeout_hours: int = 72
    auto_approve_on_timeout: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowInstance(SQLModel, table=True):
    """Instance de workflow en cours."""
    __tablename__ = "workflow_instances"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workflow_id: str = Field(index=True)
    operation_id: str = Field(index=True)
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    current_level: int = 1
    total_levels: int
    context_data: str  # JSON with operation context
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ApprovalLevel(SQLModel, table=True):
    """Niveau d'approbation dans un workflow."""
    __tablename__ = "approval_levels"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workflow_instance_id: str = Field(index=True)
    level_number: int
    approver_type: ApproverType
    approver_ids: str  # JSON list of approver IDs
    required_approvals: int = 1
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalDecision(SQLModel, table=True):
    """Decision d'approbation."""
    __tablename__ = "approval_decisions"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    approval_level_id: str = Field(index=True)
    approver_id: str
    decision: ApprovalStatus
    comments: Optional[str] = None
    decided_at: datetime = Field(default_factory=datetime.utcnow)
