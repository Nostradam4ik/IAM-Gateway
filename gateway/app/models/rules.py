"""
Modeles pour les regles dynamiques
"""
from sqlmodel import SQLModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class RuleType(str, Enum):
    """Type de regle."""
    MAPPING = "mapping"
    AGGREGATION = "aggregation"
    CALCULATION = "calculation"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"


class RuleStatus(str, Enum):
    """Statut d'une regle."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


# Request/Response Schemas
class RuleDefinition(SQLModel):
    """Definition d'une regle."""
    name: str
    description: Optional[str] = None
    rule_type: RuleType
    target_system: str
    source_attributes: List[str]
    target_attribute: str
    expression: str  # Jinja2 or Python expression
    priority: int = 0
    conditions: Optional[Dict[str, Any]] = None


class RuleTestRequest(SQLModel):
    """Requete de test d'une regle."""
    rule_id: str
    test_data: Dict[str, Any]


class RuleTestResponse(SQLModel):
    """Reponse de test d'une regle."""
    success: bool
    input_data: Dict[str, Any]
    output_value: Any
    error: Optional[str] = None
    execution_time_ms: float


# Database Models
class Rule(SQLModel, table=True):
    """Regle de calcul d'attributs."""
    __tablename__ = "rules"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    rule_type: RuleType
    target_system: str = Field(index=True)
    source_attributes: str  # JSON list
    target_attribute: str
    expression: str
    priority: int = 0
    conditions: Optional[str] = None  # JSON
    status: RuleStatus = Field(default=RuleStatus.ACTIVE)
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


class RuleVersion(SQLModel, table=True):
    """Historique des versions des regles."""
    __tablename__ = "rule_versions"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    rule_id: str = Field(index=True)
    version: int
    content: str  # JSON snapshot of the rule
    change_description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


class PolicyConfig(SQLModel, table=True):
    """Configuration de politique de provisionnement."""
    __tablename__ = "policy_configs"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    target_systems: str  # JSON list
    rules: str  # JSON list of rule IDs
    workflow_config: Optional[str] = None  # JSON
    is_default: bool = False
    status: RuleStatus = Field(default=RuleStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
