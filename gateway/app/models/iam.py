"""
Modeles Pydantic des objets IAM (representation MidPoint).

Ces modeles donnent un contrat type aux objets manipules par le hub MidPoint
et exposes par l'API. Ils refletent la structure canonique d'un objet MidPoint
telle qu'utilisee dans le projet de reference :

  - UserType : name, fullName, givenName, familyName, emailAddress,
    employeeNumber, organizationalUnit, title, telephoneNumber, activation,
    assignment[] (cf. user-jdupont.xml)
  - assignment -> construction(resourceRef, kind, intent) pour un compte cible,
    ou targetRef(RoleType) pour un role
  - RoleType / ResourceType / ShadowType (projections vers les systemes cibles)

Les champs sont optionnels et les champs additionnels ignores : les modeles
restent un sur-ensemble tolerant de ce que renvoient les connecteurs
(MidPointConnector._parse_user / get_roles / get_resources / get_user_shadows),
afin de pouvoir servir de response_model sans casser les formes existantes.
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ActivationStatus(str, Enum):
    """administrativeStatus d'un objet MidPoint."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class ObjectRef(BaseModel):
    """Reference MidPoint (targetRef / resourceRef) : oid + type."""
    model_config = ConfigDict(extra="ignore")

    oid: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None


class Assignment(BaseModel):
    """
    Assignment MidPoint : soit un role (targetRef RoleType), soit un compte
    cible (construction resourceRef + kind/intent).
    """
    model_config = ConfigDict(extra="ignore")

    targetRef: Optional[ObjectRef] = None
    resourceRef: Optional[ObjectRef] = None
    kind: Optional[str] = None
    intent: Optional[str] = None


class MidpointShadow(BaseModel):
    """Shadow = projection d'un utilisateur dans une Resource cible."""
    model_config = ConfigDict(extra="ignore")

    oid: Optional[str] = None
    resourceOid: Optional[str] = None
    kind: Optional[str] = None
    intent: Optional[str] = None
    name: Optional[str] = None


class MidpointUser(BaseModel):
    """Identite MidPoint (UserType) sous forme simplifiee."""
    model_config = ConfigDict(extra="ignore")

    oid: Optional[str] = None
    name: Optional[str] = None
    fullName: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    employeeNumber: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    telephoneNumber: Optional[str] = None
    active: Optional[bool] = None
    administrativeStatus: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    shadows: Optional[List[MidpointShadow]] = None


class MidpointRole(BaseModel):
    """Role MidPoint (RoleType)."""
    model_config = ConfigDict(extra="ignore")

    oid: Optional[str] = None
    name: Optional[str] = None
    displayName: Optional[str] = None
    description: Optional[str] = None


class MidpointResource(BaseModel):
    """Resource MidPoint = systeme cible (LDAP, Odoo, SQL, Keycloak...)."""
    model_config = ConfigDict(extra="ignore")

    oid: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    connectorType: Optional[str] = None
    status: Optional[str] = None


class MidpointUserList(BaseModel):
    total: int = 0
    users: List[MidpointUser] = Field(default_factory=list)


class MidpointRoleList(BaseModel):
    total: int = 0
    roles: List[MidpointRole] = Field(default_factory=list)


class MidpointResourceList(BaseModel):
    total: int = 0
    resources: List[MidpointResource] = Field(default_factory=list)
