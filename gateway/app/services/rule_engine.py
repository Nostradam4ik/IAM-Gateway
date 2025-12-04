"""
Moteur de regles dynamiques pour le calcul des attributs
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import time
from jinja2 import Environment, BaseLoader, sandbox
import structlog

from app.models.rules import (
    Rule, RuleDefinition, RuleVersion, PolicyConfig,
    RuleType, RuleStatus, RuleTestResponse
)
from app.models.provision import TargetSystem

logger = structlog.get_logger()


class SafeJinjaEnvironment(sandbox.SandboxedEnvironment):
    """Environnement Jinja2 securise pour l'execution des regles."""

    def __init__(self):
        super().__init__(loader=BaseLoader())
        # Add safe built-in functions
        self.globals.update({
            'lower': str.lower,
            'upper': str.upper,
            'capitalize': str.capitalize,
            'strip': str.strip,
            'replace': str.replace,
            'split': str.split,
            'join': str.join,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'now': datetime.utcnow,
            'date_format': lambda d, f: d.strftime(f) if d else '',
        })
        # Add custom filters
        self.filters.update({
            'normalize_name': self._normalize_name,
            'generate_login': self._generate_login,
            'generate_email': self._generate_email,
            'extract_domain': self._extract_domain,
            'slugify': self._slugify,
        })

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalise un nom (enleve accents, lowercase)."""
        import unicodedata
        normalized = unicodedata.normalize('NFKD', name)
        ascii_name = normalized.encode('ASCII', 'ignore').decode('ASCII')
        return ascii_name.lower().strip()

    @staticmethod
    def _generate_login(firstname: str, lastname: str, employee_id: str = "") -> str:
        """Genere un login standardise."""
        fn = SafeJinjaEnvironment._normalize_name(firstname)
        ln = SafeJinjaEnvironment._normalize_name(lastname)
        login = f"{fn}.{ln}"
        if employee_id:
            login = f"{login}.{employee_id}"
        return login

    @staticmethod
    def _generate_email(login: str, domain: str) -> str:
        """Genere une adresse email."""
        return f"{login}@{domain}"

    @staticmethod
    def _extract_domain(email: str) -> str:
        """Extrait le domaine d'une adresse email."""
        if '@' in email:
            return email.split('@')[1]
        return ""

    @staticmethod
    def _slugify(text: str) -> str:
        """Convertit un texte en slug."""
        import re
        text = SafeJinjaEnvironment._normalize_name(text)
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')


class RuleEngine:
    """
    Moteur de regles pour le calcul dynamique des attributs.

    Supporte:
    - Expressions Jinja2 securisees
    - Regles de mapping, aggregation, calcul
    - Versioning des regles
    - Tests de regles
    """

    def __init__(self, session):
        self.session = session
        self.jinja_env = SafeJinjaEnvironment()
        self._rules_cache = {}

    async def calculate_attributes(
        self,
        attributes: Dict[str, Any],
        target_systems: List[TargetSystem],
        policy_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calcule les attributs pour chaque systeme cible.

        Args:
            attributes: Attributs source depuis MidPoint
            target_systems: Liste des systemes cibles
            policy_id: ID de la politique a appliquer

        Returns:
            Dict avec attributs calcules par systeme cible
        """
        results = {}

        # Load applicable rules
        rules = await self._get_applicable_rules(target_systems, policy_id)

        for target in target_systems:
            target_name = target.value if isinstance(target, TargetSystem) else target
            results[target_name] = {}

            # Get rules for this target, sorted by priority
            target_rules = sorted(
                [r for r in rules if r.target_system == target_name],
                key=lambda r: r.priority,
                reverse=True
            )

            # Build context with source attributes
            context = {**attributes}

            # Apply each rule
            for rule in target_rules:
                try:
                    value = self._execute_rule(rule, context)
                    results[target_name][rule.target_attribute] = value
                    # Add to context for subsequent rules
                    context[rule.target_attribute] = value

                except Exception as e:
                    logger.error(
                        "Rule execution failed",
                        rule_id=rule.id,
                        rule_name=rule.name,
                        error=str(e)
                    )
                    # Continue with other rules

        logger.info(
            "Attributes calculated",
            targets=list(results.keys()),
            attribute_counts={t: len(v) for t, v in results.items()}
        )

        return results

    def _execute_rule(self, rule: Rule, context: Dict[str, Any]) -> Any:
        """Execute une regle individuelle."""
        # Check conditions first
        if rule.conditions:
            conditions = json.loads(rule.conditions)
            if not self._evaluate_conditions(conditions, context):
                return None

        # Render expression with Jinja2
        try:
            template = self.jinja_env.from_string(rule.expression)
            result = template.render(**context)

            # Try to convert to appropriate type
            if result.lower() in ('true', 'false'):
                return result.lower() == 'true'
            try:
                return int(result)
            except ValueError:
                try:
                    return float(result)
                except ValueError:
                    return result

        except Exception as e:
            raise ValueError(f"Rule '{rule.name}' execution error: {str(e)}")

    def _evaluate_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evalue les conditions d'une regle."""
        for key, expected in conditions.items():
            actual = context.get(key)

            if isinstance(expected, dict):
                # Complex condition
                op = expected.get('op', 'eq')
                value = expected.get('value')

                if op == 'eq' and actual != value:
                    return False
                elif op == 'ne' and actual == value:
                    return False
                elif op == 'in' and actual not in value:
                    return False
                elif op == 'contains' and value not in str(actual):
                    return False
                elif op == 'exists' and (actual is None) == value:
                    return False
            else:
                # Simple equality
                if actual != expected:
                    return False

        return True

    async def _get_applicable_rules(
        self,
        target_systems: List[TargetSystem],
        policy_id: Optional[str] = None
    ) -> List[Rule]:
        """Recupere les regles applicables."""
        # For now, return mock rules - replace with DB query
        return await self._get_default_rules(target_systems)

    async def _get_default_rules(self, target_systems: List[TargetSystem]) -> List[Rule]:
        """Retourne les regles par defaut."""
        rules = []

        for target in target_systems:
            target_name = target.value if isinstance(target, TargetSystem) else target

            if target_name in ("LDAP", "AD"):
                rules.extend([
                    Rule(
                        id="rule-ldap-login",
                        name="LDAP Login Generator",
                        rule_type=RuleType.CALCULATION,
                        target_system=target_name,
                        source_attributes=json.dumps(["firstname", "lastname"]),
                        target_attribute="uid",
                        expression="{{ firstname | normalize_name }}.{{ lastname | normalize_name }}",
                        priority=100
                    ),
                    Rule(
                        id="rule-ldap-cn",
                        name="LDAP Common Name",
                        rule_type=RuleType.MAPPING,
                        target_system=target_name,
                        source_attributes=json.dumps(["firstname", "lastname"]),
                        target_attribute="cn",
                        expression="{{ firstname }} {{ lastname }}",
                        priority=90
                    ),
                    Rule(
                        id="rule-ldap-mail",
                        name="LDAP Email",
                        rule_type=RuleType.CALCULATION,
                        target_system=target_name,
                        source_attributes=json.dumps(["uid"]),
                        target_attribute="mail",
                        expression="{{ uid }}@example.com",
                        priority=80
                    ),
                ])

            elif target_name == "SQL":
                rules.extend([
                    Rule(
                        id="rule-sql-username",
                        name="SQL Username",
                        rule_type=RuleType.CALCULATION,
                        target_system=target_name,
                        source_attributes=json.dumps(["account_id"]),
                        target_attribute="username",
                        expression="{{ account_id }}",
                        priority=100
                    ),
                    Rule(
                        id="rule-sql-email",
                        name="SQL Email",
                        rule_type=RuleType.MAPPING,
                        target_system=target_name,
                        source_attributes=json.dumps(["email"]),
                        target_attribute="email",
                        expression="{{ email }}",
                        priority=95
                    ),
                    Rule(
                        id="rule-sql-firstname",
                        name="SQL First Name",
                        rule_type=RuleType.MAPPING,
                        target_system=target_name,
                        source_attributes=json.dumps(["first_name"]),
                        target_attribute="first_name",
                        expression="{{ first_name }}",
                        priority=94
                    ),
                    Rule(
                        id="rule-sql-lastname",
                        name="SQL Last Name",
                        rule_type=RuleType.MAPPING,
                        target_system=target_name,
                        source_attributes=json.dumps(["last_name"]),
                        target_attribute="last_name",
                        expression="{{ last_name }}",
                        priority=93
                    ),
                    Rule(
                        id="rule-sql-department",
                        name="SQL Department",
                        rule_type=RuleType.MAPPING,
                        target_system=target_name,
                        source_attributes=json.dumps(["department"]),
                        target_attribute="department",
                        expression="{{ department }}",
                        priority=92
                    ),
                    Rule(
                        id="rule-sql-role",
                        name="SQL Default Role",
                        rule_type=RuleType.MAPPING,
                        target_system=target_name,
                        source_attributes=json.dumps(["department"]),
                        target_attribute="role",
                        expression="{% if department == 'IT' %}ADMIN{% else %}APP_USER{% endif %}",
                        priority=90
                    ),
                ])

            elif target_name == "ODOO":
                rules.extend([
                    Rule(
                        id="rule-odoo-login",
                        name="Odoo Login",
                        rule_type=RuleType.CALCULATION,
                        target_system=target_name,
                        source_attributes=json.dumps(["email"]),
                        target_attribute="login",
                        expression="{{ email }}",
                        priority=100
                    ),
                    Rule(
                        id="rule-odoo-active",
                        name="Odoo Active Status",
                        rule_type=RuleType.MAPPING,
                        target_system=target_name,
                        source_attributes=json.dumps([]),
                        target_attribute="active",
                        expression="true",
                        priority=90
                    ),
                ])

        return rules

    async def test_rule(
        self,
        rule_id: str,
        test_data: Dict[str, Any]
    ) -> RuleTestResponse:
        """Teste une regle avec des donnees d'exemple."""
        start_time = time.time()

        rule = await self.get_rule(rule_id)
        if not rule:
            return RuleTestResponse(
                success=False,
                input_data=test_data,
                output_value=None,
                error=f"Rule {rule_id} not found",
                execution_time_ms=0
            )

        try:
            result = self._execute_rule(rule, test_data)
            execution_time = (time.time() - start_time) * 1000

            return RuleTestResponse(
                success=True,
                input_data=test_data,
                output_value=result,
                error=None,
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return RuleTestResponse(
                success=False,
                input_data=test_data,
                output_value=None,
                error=str(e),
                execution_time_ms=execution_time
            )

    async def create_rule(
        self,
        definition: RuleDefinition,
        created_by: str
    ) -> Rule:
        """Cree une nouvelle regle."""
        rule = Rule(
            name=definition.name,
            description=definition.description,
            rule_type=definition.rule_type,
            target_system=definition.target_system,
            source_attributes=json.dumps(definition.source_attributes),
            target_attribute=definition.target_attribute,
            expression=definition.expression,
            priority=definition.priority,
            conditions=json.dumps(definition.conditions) if definition.conditions else None,
            created_by=created_by
        )

        # Save to DB (simplified)
        # await self.session.add(rule)
        # await self.session.commit()

        return rule

    async def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Recupere une regle par ID."""
        # Simplified - replace with DB query
        default_rules = await self._get_default_rules([
            TargetSystem.LDAP, TargetSystem.SQL, TargetSystem.ODOO
        ])
        for rule in default_rules:
            if rule.id == rule_id:
                return rule
        return None

    async def update_rule(
        self,
        rule_id: str,
        definition: RuleDefinition,
        updated_by: str
    ) -> Rule:
        """Met a jour une regle existante."""
        # Implementation DB
        pass

    async def delete_rule(self, rule_id: str) -> None:
        """Supprime une regle (soft delete)."""
        # Implementation DB
        pass

    async def list_rules(
        self,
        target_system: Optional[str] = None,
        rule_type: Optional[RuleType] = None,
        status: Optional[RuleStatus] = None
    ) -> List[Rule]:
        """Liste les regles avec filtres."""
        rules = await self._get_default_rules([
            TargetSystem.LDAP, TargetSystem.SQL, TargetSystem.ODOO
        ])

        if target_system:
            rules = [r for r in rules if r.target_system == target_system]
        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]

        return rules

    async def get_rule_versions(self, rule_id: str) -> List[RuleVersion]:
        """Recupere les versions d'une regle."""
        return []

    async def restore_version(self, rule_id: str, version: int) -> Rule:
        """Restaure une version de regle."""
        pass

    async def list_policies(self) -> List[PolicyConfig]:
        """Liste les politiques."""
        return []

    async def create_policy(
        self,
        policy: PolicyConfig,
        created_by: str
    ) -> PolicyConfig:
        """Cree une nouvelle politique."""
        return policy

    async def get_policy(self, policy_id: str) -> Optional[PolicyConfig]:
        """Recupere une politique."""
        return None
