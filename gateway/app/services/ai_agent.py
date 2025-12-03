"""
Agent IA pour assistance au provisionnement
"""
from typing import List, Dict, Any, Optional
import json
import uuid
import structlog

from app.core.config import settings
from app.models.ai import AIQueryResponse, MappingSuggestion

logger = structlog.get_logger()


class AIAgent:
    """
    Agent IA integre pour assistance au provisionnement.

    Fonctionnalites:
    - Reponse aux questions sur le provisionnement
    - Suggestion de mappings d'attributs
    - Generation de code de connecteurs
    - Analyse d'erreurs
    - Explication de regles
    """

    def __init__(self, session):
        self.session = session
        self._conversations = {}  # In-memory store, replace with Redis
        self._client = None

    def _get_client(self):
        """Get OpenAI client lazily."""
        if self._client is None and settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        user: str = "anonymous"
    ) -> AIQueryResponse:
        """Traite une requete utilisateur."""
        conv_id = conversation_id or str(uuid.uuid4())

        # Get or create conversation
        if conv_id not in self._conversations:
            self._conversations[conv_id] = {
                "messages": [],
                "user": user
            }

        conversation = self._conversations[conv_id]

        # Build system prompt
        system_prompt = self._build_system_prompt(context)

        # Add user message
        conversation["messages"].append({
            "role": "user",
            "content": query
        })

        client = self._get_client()
        if client is None:
            # Mock response when no API key
            return AIQueryResponse(
                response=self._mock_response(query),
                suggested_actions=None,
                conversation_id=conv_id,
                confidence=0.8
            )

        try:
            # Call OpenAI
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *conversation["messages"]
                ],
                temperature=0.7,
                max_tokens=2000
            )

            assistant_message = response.choices[0].message.content

            # Store response
            conversation["messages"].append({
                "role": "assistant",
                "content": assistant_message
            })

            # Extract suggested actions if any
            suggested_actions = self._extract_actions(assistant_message)

            return AIQueryResponse(
                response=assistant_message,
                suggested_actions=suggested_actions,
                conversation_id=conv_id,
                confidence=0.9
            )

        except Exception as e:
            logger.error("AI query failed", error=str(e))
            return AIQueryResponse(
                response=f"Erreur lors du traitement de la requete: {str(e)}",
                suggested_actions=None,
                conversation_id=conv_id,
                confidence=0.0
            )

    def _build_system_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """Construit le prompt systeme."""
        base_prompt = """Tu es un assistant expert en gestion des identites et des acces (IAM).
Tu aides les utilisateurs a:
- Comprendre et configurer le provisionnement des comptes
- Creer des regles de mapping d'attributs
- Diagnostiquer les erreurs de provisionnement
- Configurer les workflows d'approbation
- Developper des connecteurs vers de nouveaux systemes

Tu as acces aux systemes suivants:
- MidPoint (gestionnaire central d'identites)
- LDAP/Active Directory
- Bases de donnees SQL (PostgreSQL)
- Odoo (ERP via XML-RPC)
- GLPI (ticketing)
- Keycloak (authentification)

Reponds de maniere claire et concise. Si tu proposes des actions, formate-les clairement."""

        if context:
            base_prompt += f"\n\nContexte actuel:\n{json.dumps(context, indent=2)}"

        return base_prompt

    def _mock_response(self, query: str) -> str:
        """Reponse mock quand pas de cle API."""
        query_lower = query.lower()

        if "mapping" in query_lower or "attribut" in query_lower:
            return """Pour creer un mapping d'attributs, vous pouvez utiliser l'interface web
ou definir les regles en YAML. Exemple:

```yaml
rules:
  - name: "Generate Login"
    target: LDAP
    expression: "{{ firstname | lower }}.{{ lastname | lower }}"
    target_attribute: uid
```

Les filtres disponibles incluent: lower, upper, normalize_name, slugify."""

        elif "workflow" in query_lower or "approbation" in query_lower:
            return """Les workflows d'approbation peuvent etre configures avec N niveaux:

1. Manager de l'employe
2. Chef de departement
3. Responsable de l'application

Chaque niveau peut avoir un timeout et des approbateurs specifiques.
Utilisez l'API /api/v1/workflow/configs pour creer une configuration."""

        elif "erreur" in query_lower or "error" in query_lower:
            return """Pour diagnostiquer une erreur de provisionnement:

1. Verifiez les logs d'audit via /api/v1/admin/audit/recent
2. Consultez le statut de l'operation via /api/v1/provision/{operation_id}
3. Verifiez la connectivite des systemes via /api/v1/admin/connectors/status

Les erreurs courantes incluent:
- Timeout de connexion LDAP
- Attributs manquants dans la requete
- Compte deja existant dans le systeme cible"""

        elif "connecteur" in query_lower or "connector" in query_lower:
            return """Pour creer un nouveau connecteur, implementez l'interface BaseConnector:

```python
from app.connectors.base import BaseConnector

class MonConnector(BaseConnector):
    async def create_account(self, account_id, attributes):
        # Implementation
        pass

    async def update_account(self, account_id, attributes):
        pass

    async def delete_account(self, account_id):
        pass
```

Enregistrez ensuite le connecteur dans ConnectorFactory."""

        else:
            return """Je suis l'assistant IAM. Je peux vous aider avec:

- Configuration des regles de mapping
- Workflows d'approbation
- Diagnostic d'erreurs
- Developpement de connecteurs
- Questions sur MidPoint et le provisionnement

Que souhaitez-vous savoir?"""

    def _extract_actions(self, response: str) -> Optional[List[Dict[str, Any]]]:
        """Extrait les actions suggerees de la reponse."""
        # Simple extraction - could be enhanced with structured output
        actions = []

        if "creer" in response.lower() or "create" in response.lower():
            actions.append({
                "type": "create",
                "description": "Creer une nouvelle ressource"
            })

        if "verifier" in response.lower() or "check" in response.lower():
            actions.append({
                "type": "verify",
                "description": "Verifier la configuration"
            })

        return actions if actions else None

    async def suggest_mappings(
        self,
        source_schema: Dict[str, Any],
        target_system: str,
        existing_mappings: Optional[List[Dict[str, Any]]] = None
    ) -> List[MappingSuggestion]:
        """Suggere des mappings d'attributs."""
        suggestions = []

        # Mappings connus
        common_mappings = {
            "LDAP": {
                "firstname": ("givenName", None),
                "lastname": ("sn", None),
                "email": ("mail", None),
                "displayName": ("cn", "{{ firstname }} {{ lastname }}"),
                "department": ("ou", None),
            },
            "SQL": {
                "firstname": ("first_name", None),
                "lastname": ("last_name", None),
                "email": ("email", None),
                "username": ("username", "{{ firstname | lower }}.{{ lastname | lower }}"),
            },
            "ODOO": {
                "name": ("name", "{{ firstname }} {{ lastname }}"),
                "email": ("login", None),
                "department": ("department_id", None),
            }
        }

        target_mappings = common_mappings.get(target_system, {})

        for source_attr in source_schema.get("attributes", []):
            attr_name = source_attr if isinstance(source_attr, str) else source_attr.get("name")

            if attr_name in target_mappings:
                target_attr, transform = target_mappings[attr_name]
                suggestions.append(MappingSuggestion(
                    source_attribute=attr_name,
                    target_attribute=target_attr,
                    transformation=transform,
                    confidence=0.95,
                    rationale=f"Mapping standard {attr_name} -> {target_attr}"
                ))
            else:
                # Suggest based on name similarity
                suggestions.append(MappingSuggestion(
                    source_attribute=attr_name,
                    target_attribute=attr_name.lower(),
                    transformation=None,
                    confidence=0.5,
                    rationale=f"Mapping par defaut base sur le nom"
                ))

        return suggestions

    async def generate_connector(
        self,
        system_type: str,
        description: str,
        api_docs: Optional[str] = None,
        sample_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Genere le code d'un nouveau connecteur."""
        template = '''"""
Connector for {system_type}
Generated by AI Agent
"""
from typing import Dict, Any, Optional, List
from app.connectors.base import BaseConnector
import structlog

logger = structlog.get_logger()


class {class_name}Connector(BaseConnector):
    """
    Connector for {description}
    """

    def __init__(self):
        super().__init__()
        # TODO: Initialize connection parameters
        self.base_url = ""
        self.api_key = ""

    async def test_connection(self) -> bool:
        """Test connectivity to the target system."""
        try:
            # TODO: Implement connection test
            return True
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return False

    async def create_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new account in the target system."""
        logger.info("Creating account", account_id=account_id)
        # TODO: Implement account creation
        return {{"id": account_id, "status": "created"}}

    async def update_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing account."""
        logger.info("Updating account", account_id=account_id)
        # TODO: Implement account update
        return {{"id": account_id, "status": "updated"}}

    async def delete_account(self, account_id: str) -> bool:
        """Delete an account from the target system."""
        logger.info("Deleting account", account_id=account_id)
        # TODO: Implement account deletion
        return True

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve account details."""
        logger.info("Getting account", account_id=account_id)
        # TODO: Implement account retrieval
        return None

    async def list_accounts(self) -> List[Dict[str, Any]]:
        """List all accounts in the target system."""
        # TODO: Implement account listing
        return []

    async def disable_account(self, account_id: str) -> bool:
        """Disable an account."""
        logger.info("Disabling account", account_id=account_id)
        # TODO: Implement account disable
        return True

    async def enable_account(self, account_id: str) -> bool:
        """Enable an account."""
        logger.info("Enabling account", account_id=account_id)
        # TODO: Implement account enable
        return True
'''

        class_name = system_type.replace("_", " ").title().replace(" ", "")

        code = template.format(
            system_type=system_type,
            class_name=class_name,
            description=description
        )

        config_template = f'''# Configuration for {system_type} connector
connector:
  type: {system_type}
  name: "{description}"
  enabled: true
  connection:
    base_url: ""
    api_key: ""
    timeout: 30
  mapping:
    # Define attribute mappings here
    uid: "id"
    name: "displayName"
'''

        test_template = f'''"""
Tests for {class_name}Connector
"""
import pytest
from app.connectors.{system_type}_connector import {class_name}Connector


@pytest.fixture
def connector():
    return {class_name}Connector()


@pytest.mark.asyncio
async def test_connection(connector):
    result = await connector.test_connection()
    assert result is True


@pytest.mark.asyncio
async def test_create_account(connector):
    result = await connector.create_account(
        "test-user",
        {{"name": "Test User", "email": "test@example.com"}}
    )
    assert result["status"] == "created"
'''

        return {
            "connector_code": code,
            "config_yaml": config_template,
            "test_code": test_template,
            "instructions": f"""
## Instructions pour integrer le connecteur {class_name}

1. Sauvegardez le code dans `gateway/app/connectors/{system_type}_connector.py`
2. Ajoutez la configuration dans `gateway/config/connectors/{system_type}.yaml`
3. Enregistrez le connecteur dans `ConnectorFactory`:

```python
from app.connectors.{system_type}_connector import {class_name}Connector

class ConnectorFactory:
    def get_connector(self, target: str):
        if target == "{system_type.upper()}":
            return {class_name}Connector()
```

4. Executez les tests: `pytest tests/connectors/test_{system_type}.py`
"""
        }

    async def analyze_error(
        self,
        operation_id: str,
        error_message: str
    ) -> Dict[str, Any]:
        """Analyse une erreur de provisionnement."""
        analysis = {
            "error": error_message,
            "probable_cause": "",
            "suggestions": [],
            "related_docs": []
        }

        error_lower = error_message.lower()

        if "connection" in error_lower or "timeout" in error_lower:
            analysis["probable_cause"] = "Probleme de connectivite reseau"
            analysis["suggestions"] = [
                "Verifier que le service cible est accessible",
                "Verifier les parametres de connexion (host, port)",
                "Verifier les regles firewall"
            ]

        elif "authentication" in error_lower or "401" in error_lower:
            analysis["probable_cause"] = "Echec d'authentification"
            analysis["suggestions"] = [
                "Verifier les credentials dans la configuration",
                "Verifier que le compte de service est actif",
                "Renouveler le token si expire"
            ]

        elif "already exists" in error_lower or "duplicate" in error_lower:
            analysis["probable_cause"] = "Le compte existe deja"
            analysis["suggestions"] = [
                "Utiliser l'operation UPDATE au lieu de CREATE",
                "Verifier l'unicite de l'identifiant",
                "Lancer une reconciliation"
            ]

        elif "not found" in error_lower or "404" in error_lower:
            analysis["probable_cause"] = "Ressource non trouvee"
            analysis["suggestions"] = [
                "Verifier que le compte existe dans le systeme cible",
                "Verifier l'identifiant utilise",
                "Synchroniser le cache des comptes"
            ]

        else:
            analysis["probable_cause"] = "Erreur non categorisee"
            analysis["suggestions"] = [
                "Consulter les logs detailles",
                "Contacter le support technique"
            ]

        return analysis

    async def explain_rule(self, rule_id: str) -> str:
        """Explique une regle en langage naturel."""
        # Get rule from DB
        # For now, mock explanation
        return f"""La regle {rule_id} effectue les operations suivantes:

1. Prend les attributs source (prenom, nom)
2. Applique une normalisation (suppression accents, minuscules)
3. Concatene avec un point pour former le login
4. Le resultat est assigne a l'attribut 'uid' dans LDAP

Exemple: Jean Dupont -> jean.dupont"""

    async def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Recupere l'historique d'une conversation."""
        return self._conversations.get(conversation_id, {"messages": []})

    async def delete_conversation(self, conversation_id: str) -> None:
        """Supprime une conversation."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
