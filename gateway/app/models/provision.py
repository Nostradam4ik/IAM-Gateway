"""
Modeles pour les operations de provisionnement
"""
from sqlmodel import SQLModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class OperationType(str, Enum):
    """Type d'operation de provisionnement."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    DISABLE = "disable"
    ENABLE = "enable"


class OperationStatus(str, Enum):
    """Statut d'une operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class TargetSystem(str, Enum):
    """Systemes cibles disponibles."""
    LDAP = "LDAP"
    AD = "AD"
    SQL = "SQL"
    ODOO = "ODOO"
    GLPI = "GLPI"
    KEYCLOAK = "KEYCLOAK"
    FIREBASE = "FIREBASE"


# Request/Response Schemas
class ProvisioningRequest(SQLModel):
    """Requete de provisionnement depuis MidPoint."""
    operation: OperationType
    target_systems: List[TargetSystem]
    account_id: str
    attributes: Dict[str, Any]
    policy_id: Optional[str] = None
    correlation_id: Optional[str] = None
    require_approval: Optional[bool] = False


class ProvisioningResponse(SQLModel):
    """Reponse de provisionnement vers MidPoint."""
    status: OperationStatus
    operation_id: str
    calculated_attributes: Dict[str, Dict[str, Any]]
    message: str
    timestamp: datetime
    errors: Optional[List[Dict[str, str]]] = None


# Database Models
class ProvisioningOperation(SQLModel, table=True):
    """Operation de provisionnement en base."""
    __tablename__ = "provisioning_operations"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    correlation_id: Optional[str] = Field(default=None, index=True)
    operation_type: OperationType
    account_id: str = Field(index=True)
    status: OperationStatus = Field(default=OperationStatus.PENDING)
    target_systems: str  # JSON string of target systems
    input_attributes: str  # JSON string
    calculated_attributes: Optional[str] = None  # JSON string
    policy_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None


class TargetAccountState(SQLModel, table=True):
    """Etat cache des comptes dans les systemes cibles."""
    __tablename__ = "target_account_states"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    account_id: str = Field(index=True)
    target_system: TargetSystem
    target_account_id: str
    attributes: str  # JSON string
    is_active: bool = True
    last_sync_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # Unique constraint on account_id + target_system
        pass


class RollbackAction(SQLModel, table=True):
    """Actions de rollback pour une operation."""
    __tablename__ = "rollback_actions"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    operation_id: str = Field(index=True)
    target_system: TargetSystem
    action_type: str
    action_data: str  # JSON string
    executed: bool = False
    executed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
