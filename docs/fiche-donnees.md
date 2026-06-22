# Fiche d'architecture des données — IAM Gateway

> **Document** : Description de l'architecture de données (livrable *data architecture*)
> **Projet** : *Projet 3 — Passerelle de provisionnement IAM intelligente* (SAE S5/S6, BUT Informatique — UPEC, laboratoire LISSI)
> **Dépôt** : <https://github.com/Nostradam4ik/IAM-Gateway>
> **Co-auteur** (métadonnées, conformément au `README.md`) : `achibani@gmail.com` (Abdelghani Chibani)
> **Sources** : `gateway/app/models/*`, `db/migrations.py`, `core/database.py`, `core/redis_client.py`, `core/qdrant_store.py`, `core/memory_store.py`, `docker-compose.yml`

---

## 1. Introduction — Stratégie de persistance polyglotte

IAM Gateway met en œuvre une **persistance polyglotte** (*polyglot persistence*) : plutôt que de forcer toutes les données dans un seul moteur, chaque catégorie de données est confiée à la technologie **optimisée pour son motif d'accès**. Le projet déploie ainsi **trois familles de bases de données**, et jusqu'à **cinq instances PostgreSQL** (les hubs MidPoint/Odoo/Keycloak possédant chacun la leur, par autonomie de service) :

- **Relationnel (PostgreSQL)** — données structurées, transactionnelles et durables : opérations de provisionnement, journal d'audit, workflows, règles, utilisateurs, configurations de connecteurs. On y recherche l'intégrité (types, contraintes d'unicité, enums), les requêtes par clé/filtre et la durabilité.
- **Clé-valeur en mémoire (Redis)** — données **éphémères** à TTL et **opérations atomiques** : blacklist de jetons JWT révoqués, compteurs de *rate-limiting*, cache de sessions et de tokens de workflow. On y recherche la latence sub-milliseconde et l'atomicité (scripts Lua).
- **Vectoriel (Qdrant)** — index de **similarité** sur les logs d'audit, pour une recherche par proximité plutôt que par mots-clés exacts. On y recherche la recherche *approximate nearest neighbor* (ANN) par distance cosinus.

Le principe directeur : **le bon magasin pour la bonne charge**. Un compteur de *rate-limit* dans Redis (incrément atomique + expiration) serait inefficace en SQL ; une recherche par similarité dans PostgreSQL serait inadaptée ; et la traçabilité d'audit exige la durabilité relationnelle. Cette hétérogénéité est assumée et orchestrée par Docker Compose.

> **Note de fidélité** : aucune base **MongoDB** n'est présente dans le projet (ni service Compose, ni pilote dans `requirements.txt`). Le présent document décrit l'architecture réellement déployée : PostgreSQL, Redis et Qdrant.

---

## 2. Inventaire des bases de données

Valeurs relevées dans `docker-compose.yml`. Les datastores de la gateway sont liés à `127.0.0.1` (non exposés publiquement).

| Base | Type | Technologie | Version | Port (hôte) | Rôle principal |
|---|---|---|---|---|---|
| `gateway-db` | Relationnel | PostgreSQL | 15 | `127.0.0.1:5434` | Store applicatif de la gateway |
| `midpoint-postgres` | Relationnel | PostgreSQL | 15 | `127.0.0.1:5433` | Dépôt (repository) de MidPoint |
| `odoo-db` | Relationnel | PostgreSQL | 15 | interne | Backing d'Odoo ERP |
| `redis` | Clé-valeur | Redis | 7-alpine | `127.0.0.1:6379` | Blacklist JWT, rate-limit, cache |
| `qdrant` | Vectoriel | Qdrant | v1.12.4 | `127.0.0.1:6333/6334` | Recherche de similarité d'audit |
| ~~MongoDB~~ | — | *(absent)* | — | — | *(non utilisé)* |

| Base | Contenu stocké | Volume Docker | Restart policy | Mem limit |
|---|---|---|---|---|
| `gateway-db` | Opérations, audit, workflows, règles, users, connecteurs | `gateway_db_data` | `unless-stopped` | — |
| `midpoint-postgres` | Identités, rôles, resources, shadows MidPoint | `midpoint_postgres_data` | `unless-stopped` | — |
| `odoo-db` | Employés, contrats, partenaires Odoo | `odoo_db_data` | `unless-stopped` | — |
| `redis` | `blacklist:`, `rate:`, `session:`, `wf_token:`, `cache:` | `redis_data` | `unless-stopped` | — |
| `qdrant` | Collection vectorielle `audit_logs` | `qdrant_data` | `unless-stopped` | `1g` |

> Deux instances PostgreSQL 15 supplémentaires existent : `intranet-db` (cible SQL « intranet », `127.0.0.1:55432`, volume `intranet_db_data`) et `keycloak-db` (backing de Keycloak, interne, volume `keycloak_db_data`).

---

## 3. Modèle relationnel PostgreSQL — gateway-db

La couche `gateway/app/models/` définit des **modèles SQLModel** (SQLAlchemy + Pydantic). Les classes marquées `table=True` génèrent les tables ci-dessous. **Point d'architecture important** : les `id` sont des **UUID** (chaîne, `default_factory=uuid4`), les colonnes JSON sont stockées comme **chaînes JSON sérialisées** (champ `str`), et **aucune contrainte de clé étrangère n'est déclarée** au niveau ORM — les relations (`operation_id`, `rule_id`, `workflow_id`, …) sont **logiques**, matérialisées par des UUID indexés, non imposées par la base.

### 3.1 Table `provisioning_operations` (`ProvisioningOperation`)

| Colonne | Type SQLAlchemy | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK**, défaut uuid4 | Identifiant de l'opération |
| `correlation_id` | String | index, nullable | Corrélation (req. source) |
| `operation_type` | Enum `OperationType` | not null | create/update/delete/enable/disable |
| `account_id` | String | index, not null | Identité cible |
| `status` | Enum `OperationStatus` | défaut `PENDING` | Cycle de vie de l'opération |
| `target_systems` | String (JSON) | not null | Liste des cibles (JSON sérialisé) |
| `input_attributes` | String (JSON) | not null | Attributs source |
| `calculated_attributes` | String (JSON) | nullable | Attributs calculés par règle |
| `policy_id` | String | nullable | Politique appliquée |
| `error_message` | Text | nullable | Message d'erreur éventuel |
| `created_at` / `updated_at` | DateTime | défaut `utcnow` | Horodatages |
| `completed_at` | DateTime | nullable | Fin d'exécution |
| `created_by` | String | nullable | Auteur de la demande |

### 3.2 Table `target_account_states` (`TargetAccountState`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `account_id` | String | index | Identité gateway |
| `target_system` | Enum `TargetSystem` | not null | LDAP/AD/SQL/ODOO/… |
| `target_account_id` | String | not null | ID du compte côté cible |
| `attributes` | String (JSON) | not null | État des attributs |
| `is_active` | Boolean | défaut `true` | Compte actif ? |
| `last_sync_at` / `created_at` | DateTime | défaut `utcnow` | Horodatages |

### 3.3 Table `rollback_actions` (`RollbackAction`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `operation_id` | String | index | Opération concernée (logique) |
| `target_system` | Enum `TargetSystem` | not null | Cible de l'action |
| `action_type` | String | not null | Type d'action inverse |
| `action_data` | String (JSON) | not null | Données pour annuler |
| `executed` | Boolean | défaut `false` | Rollback exécuté ? |
| `executed_at` | DateTime | nullable | Horodatage d'exécution |
| `created_at` | DateTime | défaut `utcnow` | — |

### 3.4 Table `rules` (`Rule`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `name` | String | index | Nom de la règle |
| `description` | Text | nullable | — |
| `rule_type` | Enum `RuleType` | not null | mapping/calculation/validation/… |
| `target_system` | String | index | Système cible |
| `source_attributes` | String (JSON) | not null | Attributs d'entrée |
| `target_attribute` | String | not null | Attribut produit |
| `expression` | Text | not null | Expression **Jinja2** |
| `priority` | Integer | défaut `0` | Ordre d'exécution (desc.) |
| `conditions` | String (JSON) | nullable | Conditions d'application |
| `status` | Enum `RuleStatus` | défaut `ACTIVE` | active/inactive/draft/… |
| `version` | Integer | défaut `1` | Version courante |
| `created_at` / `updated_at` | DateTime | défaut `utcnow` | — |
| `created_by` | String | nullable | — |

### 3.5 Table `rule_versions` (`RuleVersion`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `rule_id` | String | index | Règle parente (logique) |
| `version` | Integer | not null | Numéro de version |
| `content` | String (JSON) | not null | Instantané de la règle |
| `change_description` | Text | nullable | Motif du changement |
| `created_at` | DateTime | défaut `utcnow` | — |
| `created_by` | String | nullable | — |

### 3.6 Table `policy_configs` (`PolicyConfig`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `name` | String | index, **unique** | Nom de la politique |
| `description` | Text | nullable | — |
| `target_systems` | String (JSON) | not null | Cibles couvertes |
| `rules` | String (JSON) | not null | IDs de règles regroupées |
| `workflow_config` | String (JSON) | nullable | Workflow associé |
| `is_default` | Boolean | défaut `false` | Politique par défaut ? |
| `status` | Enum `RuleStatus` | défaut `ACTIVE` | — |
| `created_at` / `updated_at` | DateTime | défaut `utcnow` | — |

### 3.7 Table `workflow_configs` (`WorkflowConfig`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `name` | String | index | Nom du template |
| `description` | Text | nullable | — |
| `workflow_type` | Enum `WorkflowType` | not null | pre/post_provisioning |
| `levels` | String (JSON) | not null | Niveaux d'approbation |
| `timeout_hours` | Integer | défaut `72` | Délai global |
| `auto_approve_on_timeout` | Boolean | défaut `false` | Auto-approbation |
| `is_active` | Boolean | défaut `true` | — |
| `created_at` / `updated_at` | DateTime | défaut `utcnow` | — |

### 3.8 Table `workflow_instances` (`WorkflowInstance`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `workflow_id` | String | index | Template appliqué (logique) |
| `operation_id` | String | index | Opération liée (logique) |
| `status` | Enum `ApprovalStatus` | défaut `PENDING` | pending/approved/rejected/… |
| `current_level` | Integer | défaut `1` | Niveau courant |
| `total_levels` | Integer | not null | Nombre de niveaux |
| `context_data` | String (JSON) | not null | Contexte de l'opération |
| `created_at` / `updated_at` | DateTime | défaut `utcnow` | — |
| `expires_at` / `completed_at` | DateTime | nullable | Expiration / fin |

### 3.9 Table `approval_levels` (`ApprovalLevel`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `workflow_instance_id` | String | index | Instance parente (logique) |
| `level_number` | Integer | not null | Rang du niveau |
| `approver_type` | Enum `ApproverType` | not null | user/role/group/manager/… |
| `approver_ids` | String (JSON) | not null | Approbateurs |
| `required_approvals` | Integer | défaut `1` | Quorum |
| `status` | Enum `ApprovalStatus` | défaut `PENDING` | — |
| `created_at` / `updated_at` | DateTime | défaut `utcnow` | — |

### 3.10 Table `approval_decisions` (`ApprovalDecision`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `approval_level_id` | String | index | Niveau concerné (logique) |
| `approver_id` | String | not null | Décideur |
| `decision` | Enum `ApprovalStatus` | not null | approved/rejected |
| `comments` | Text | nullable | Commentaire |
| `decided_at` | DateTime | défaut `utcnow` | Horodatage |

### 3.11 Table `audit_logs` (`AuditLog`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `event_type` | Enum `AuditEventType` | not null | provision_*, workflow_*, … |
| `severity` | Enum `AuditSeverity` | défaut `INFO` | debug→critical |
| `operation_id` | String | index, nullable | Opération liée |
| `account_id` | String | index, nullable | Identité concernée |
| `target_system` | String | nullable | Système concerné |
| `actor` | String | nullable | Auteur de l'action |
| `action` | String | not null | Libellé de l'action |
| `details` | String (JSON) | not null | Détails structurés |
| `ip_address` / `user_agent` | String | nullable | Contexte requête |
| `created_at` | DateTime | index, défaut `utcnow` | Horodatage |

### 3.12 Table `vector_log_entries` (`VectorLogEntry`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `audit_log_id` | String | index | Log d'audit indexé (logique) |
| `summary` | Text | not null | Texte vectorisé |
| `vector_id` | String | nullable | ID du point Qdrant |
| `embedding_model` | String | défaut `all-MiniLM-L6-v2` | Modèle d'embedding *prévu* |
| `created_at` | DateTime | défaut `utcnow` | — |

### 3.13 Table `system_states` (`SystemState`)

| Colonne | Type | Contraintes | Description |
|---|---|---|---|
| `id` | String (UUID) | **PK** | — |
| `key` | String | index, **unique** | Nom de l'état (ex. `provisioning_enabled`) |
| `value` | String | not null | Valeur courante |
| `updated_at` | DateTime | défaut `utcnow` | — |
| `updated_by` | String | nullable | Dernier modificateur |

> **Tables existant uniquement dans `migrations.py`** (pas de classe SQLModel correspondante, manipulées en SQL brut) : `gateway_users`, `connector_configurations`, `reconciliation_jobs`, `account_state_cache`, `discrepancies`, `workflows` (instances multi-niveaux réellement utilisées par `WorkflowService`/`memory_store`), `approval_roles`, `app_users`, `app_profiles`, `app_user_permissions`, `ai_configuration` ; `workflow_configs`/`workflow_instances` existent en DDL enrichie en plus de leurs classes SQLModel. La table **`gateway_users`** (clé du modèle utilisateur) y est définie : `id` UUID PK, `username`/`email` **UNIQUE NOT NULL**, `password_hash` NOT NULL, `full_name`, `role` (défaut `viewer`), `roles` **JSONB** (`'[]'`), `permission_level` (défaut 1), `is_active`, `created_at`, `last_login`.

### 3.14 Diagramme entité-relation (ERD)

Relations **logiques** (par UUID, non contraintes en base). Cardinalités indiquées.

```
┌────────────────────┐         ┌──────────────────────────┐
│ gateway_users      │         │ provisioning_operations  │
├────────────────────┤         ├──────────────────────────┤
│ PK id (UUID)       │  1   N  │ PK id (UUID)             │
│ username (UNIQUE)  │────────▶│ account_id (idx)         │
│ email (UNIQUE)     │ (logique│ operation_type (enum)    │
│ password_hash      │  via    │ status (enum)            │
│ role / roles(JSONB)│ created │ target_systems (JSON)    │
│ permission_level   │  _by /  │ input/calculated_attrs   │
│ is_active          │  actor) │ created_at / updated_at  │
└────────────────────┘         └───┬──────────┬───────┬───┘
                                   │1:N       │1:N    │1:N
                          ┌────────▼───┐ ┌────▼─────┐ ▼
                          │ rollback_  │ │ target_  │ ┌──────────────────────┐
                          │ actions    │ │ account_ │ │ workflow_instances   │
                          ├────────────┤ │ states   │ ├──────────────────────┤
                          │ PK id      │ ├──────────┤ │ PK id (UUID)         │
                          │ operation_ │ │ PK id    │ │ operation_id (idx)   │
                          │ id (idx)   │ │ account_ │ │ workflow_id (idx)    │
                          │ target_sys │ │ id (idx) │ │ status / current_lvl │
                          └────────────┘ └──────────┘ └───────┬──────────────┘
                                                              │1:N
┌────────────────┐ 1   N ┌────────────────┐          ┌───────▼─────────┐ 1  N ┌───────────────────┐
│ rules          │──────▶│ rule_versions  │          │ approval_levels │─────▶│ approval_decisions│
├────────────────┤(logiq)├────────────────┤          ├─────────────────┤      ├───────────────────┤
│ PK id (UUID)   │       │ PK id          │          │ PK id           │      │ PK id             │
│ name (idx)     │       │ rule_id (idx)  │          │ workflow_       │      │ approval_level_id │
│ target_system  │       │ version        │          │ instance_id(idx)│      │ approver_id       │
│ expression(j2) │       │ content (JSON) │          │ approver_type   │      │ decision (enum)   │
│ priority       │       └────────────────┘          └─────────────────┘      └───────────────────┘
└────────────────┘

┌────────────────────┐ 1   1 ┌────────────────────┐      ┌──────────────────────┐ 1  N ┌───────────────┐
│ audit_logs         │──────▶│ vector_log_entries │      │ reconciliation_jobs  │─────▶│ discrepancies │
├────────────────────┤(logiq)├────────────────────┤      ├──────────────────────┤(logiq├───────────────┤
│ PK id (UUID)       │       │ PK id              │      │ PK id (UUID)         │  via │ PK id         │
│ event_type (enum)  │       │ audit_log_id (idx) │      │ status / targets     │ job_ │ job_id        │
│ operation_id (idx) │       │ summary → Qdrant   │      │ total/processed_users│ id)  │ discrepancy_  │
│ account_id (idx)   │       │ vector_id          │      │ discrepancies_found  │      │ type / resolved│
└────────────────────┘       └────────────────────┘      └──────────────────────┘      └───────────────┘
```

### 3.15 Stratégie de migration

Deux mécanismes **coexistent** :
1. **`core/database.py` → `init_db()`** : au démarrage de l'application, `SQLModel.metadata.create_all` crée les tables à partir des classes SQLModel ci-dessus (`CREATE TABLE IF NOT EXISTS` implicite).
2. **`db/migrations.py`** : script **idempotent** et **autoritatif** pour le schéma vivant, exécuté manuellement (`docker compose exec -T gateway python -m app.db.migrations`). Il enchaîne : `create_enums` (4 enums PostgreSQL — `operationtype`, `operationstatus`, `auditeventtype`, `auditseverity`), `CREATE TABLE IF NOT EXISTS` (24 tables), `ALTER TABLE … ADD COLUMN IF NOT EXISTS` (ajouts de colonnes rétro-compatibles), `CREATE INDEX IF NOT EXISTS` (16 index), puis `seed_data` (utilisateur `admin` bcrypt, une règle LDAP d'exemple, une config de workflow à 2 niveaux).

> **Dérive de schéma assumée.** Les classes SQLModel et `migrations.py` sont maintenues à la main et **divergent** : p. ex. `audit_logs` possède en DDL `actor_ip`, `source_system`, `status`, `changes`, `error_details` (absents du SQLModel) ; les enums PostgreSQL sont en **MAJUSCULES** (`'CREATE'`) tandis que les enums Python sont en minuscules (`"create"`), d'où des `CAST(... AS operationtype)` et un `.upper()` dans `memory_store.py`. **`migrations.py` fait foi pour le schéma réel.**

### 3.16 Configuration du pool de connexions (`core/database.py`)

`create_async_engine` (pilote **asyncpg**) est configuré ainsi :

| Paramètre | Valeur | Rôle |
|---|---|---|
| `pool_size` | `10` | Connexions persistantes du pool |
| `max_overflow` | `20` | Connexions supplémentaires en pic |
| `pool_recycle` | `1800` (30 min) | Recyclage anti-coupures *idle* (proxy) |
| `pool_pre_ping` | `True` | Détecte/remplace une connexion morte (redémarrage PG) |
| `echo` | `settings.DEBUG` | Journalisation SQL en debug uniquement |
| `expire_on_commit` | `False` | Objets utilisables après commit |

---

## 4. Modèles Pydantic IAM (`app/models/iam.py`)

Ces modèles (Pydantic v2, `extra="ignore"`) **ne sont pas des tables** : ils typent les objets MidPoint exposés par l'API (sur-ensemble tolérant des formes renvoyées par `MidPointConnector`). MidPoint stocke ses objets dans son propre dépôt (`midpoint-postgres`).

### 4.1 `ActivationStatus` (Enum)
Reflète `activation/administrativeStatus` d'un objet MidPoint :
- `enabled` — compte actif (propagé/maintenu sur les cibles).
- `disabled` — compte désactivé (le *leaver* conserve son identité mais perd l'accès).
- `archived` — identité archivée (cycle de vie terminé).

### 4.2 `ObjectRef`
Référence MidPoint, correspond à un élément `<targetRef>` / `<resourceRef>` du XML.

| Champ | Type | Optionnel | Élément MidPoint |
|---|---|---|---|
| `oid` | str | oui | attribut `oid` de la référence |
| `type` | str | oui | `type` (ex. `RoleType`, `ResourceType`) |
| `name` | str | oui | nom résolu (commodité) |

### 4.3 `Assignment`
Un `<assignment>` MidPoint, **soit un rôle, soit un compte cible** :
- **Rôle** : `targetRef` (ObjectRef de type `RoleType`) → l'attribution d'un rôle déclenche le provisioning.
- **Compte cible** (*construction*) : `resourceRef` + `kind` + `intent` → projection directe sur une *Resource*.

| Champ | Type | Optionnel | Sens |
|---|---|---|---|
| `targetRef` | ObjectRef | oui | référence de rôle |
| `resourceRef` | ObjectRef | oui | référence de Resource |
| `kind` | str | oui | `account` / `entitlement` |
| `intent` | str | oui | variante de projection |

### 4.4 `MidpointShadow`
Un `<shadow>` = **projection** d'une identité dans une *Resource* (le compte réel côté LDAP/Odoo/SQL).

| Champ | Type | Optionnel | Sens |
|---|---|---|---|
| `oid` | str | oui | OID du shadow |
| `resourceOid` | str | oui | Resource hébergeant le compte |
| `kind` / `intent` | str | oui | type de projection |
| `name` | str | oui | nom du compte cible |

### 4.5 `MidpointUser`
Identité (`UserType`) simplifiée. Tous les champs sont **optionnels** (`extra="ignore"`) afin de tolérer les variations de réponses MidPoint sans casser le `response_model`.

| Champ | Type | Attribut MidPoint |
|---|---|---|
| `oid` | str? | `oid` |
| `name` | str? | `name` |
| `fullName` | str? | `fullName` |
| `firstname` | str? | `givenName` |
| `lastname` | str? | `familyName` |
| `email` | str? | `emailAddress` |
| `employeeNumber` | str? | `employeeNumber` |
| `department` | str? | `organizationalUnit` |
| `title` | str? | `title` |
| `telephoneNumber` | str? | `telephoneNumber` |
| `active` | bool? | `activation/administrativeStatus == enabled` |
| `administrativeStatus` | str? | `activation/administrativeStatus` |
| `roles` | List[str] | OIDs des `assignment/targetRef` (RoleType) |
| `shadows` | List[MidpointShadow]? | projections liées |

### 4.6 `MidpointRole` / `MidpointResource`
- **`MidpointRole`** (`RoleType`) : `oid`, `name`, `displayName`, `description`.
- **`MidpointResource`** (`ResourceType` = système cible) : `oid`, `name`, `description`, `connectorType` (← `connectorRef.type`), `status` (← `operationalState.lastAvailabilityStatus`).

### 4.7 Enveloppes de liste
`MidpointUserList` / `MidpointRoleList` / `MidpointResourceList` : un compteur `total: int` + la liste typée (`users` / `roles` / `resources`).

### 4.8 Exemples de réponses JSON

`MidpointUser` :
```json
{
  "oid": "f6a3...e21", "name": "jdupont", "fullName": "Jean Dupont",
  "firstname": "Jean", "lastname": "Dupont", "email": "jean.dupont@example.com",
  "employeeNumber": "E1024", "department": "Finance", "title": "Comptable",
  "telephoneNumber": "+33100000000", "active": true,
  "administrativeStatus": "enabled", "roles": ["a1b2...c3d4"], "shadows": null
}
```
`MidpointResource` et `MidpointResourceList` :
```json
{
  "total": 1,
  "resources": [
    {"oid": "9f0e...77", "name": "OpenLDAP", "description": "Annuaire",
     "connectorType": "com.evolveum.polygon.connector.ldap.LdapConnector",
     "status": "up"}
  ]
}
```

---

## 5. Cache Redis

Tous les motifs de clés (de `core/redis_client.py`). Type Redis : chaîne (`String`), éventuellement JSON sérialisé.

| Pattern de clé | Type | TTL | Contenu | Utilisé par |
|---|---|---|---|---|
| `blacklist:{jti}` | String (`"1"`) | `JWT_EXPIRE_MINUTES×60` (≈ 3600 s) | Marqueur de jeton révoqué | `security.py` (`get_current_user`), `admin.py` (`/logout`) |
| `rate:{key}` → `rate:login:{ip}:{username}` | String (compteur) | `window_seconds` (300 s) | Compteur de tentatives | `admin.py` (`/token`), via `check_rate_limit` (max 10) |
| `session:{username}` | String (JSON) | 3600 s | Données de session | `cache_user_session` |
| `wf_token:{token}` | String (JSON) | 259200 s (72 h) | Token d'approbation workflow | cache des tokens de workflow |
| `cache:{key}` | String | 300 s | Cache générique | `set_cache` / `get_cache` |

### 5.1 Rate-limiting atomique par script Lua

```lua
local c = redis.call('INCR', KEYS[1])
if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return c
```

- **Pourquoi Lua ?** Redis exécute un script Lua de manière **atomique** : `INCR` et `EXPIRE` ne forment qu'une seule opération indivisible. `check_rate_limit` renvoie « autorisé » tant que le compteur `≤ max_requests`.
- **Quel bug cela corrige.** Une implémentation naïve en deux commandes (`INCR` puis `EXPIRE`) comporte une **fenêtre de course** : si le processus s'interrompt entre les deux, la clé reste **sans TTL** et n'expire jamais — l'utilisateur resterait bloqué indéfiniment. Le script garantit que le TTL est posé exactement lors de la **première** incrémentation.
- **Dégradation contrôlée.** Si Redis est indisponible, `check_rate_limit` retourne `True` (*fail-open*) : la disponibilité du login prime sur la défense en profondeur, et l'incident est journalisé.

---

## 6. Base vectorielle Qdrant

### 6.1 Qu'est-ce qu'une base vectorielle ?
Une base vectorielle stocke des **vecteurs** (listes de nombres) et permet d'y rechercher les **plus proches voisins** selon une distance (similarité). Elle convient à la recherche « par sens » : on transforme un texte en vecteur, puis on retrouve les entrées dont le vecteur est le plus proche, indépendamment des mots exacts.

### 6.2 Collection et schéma (de `core/qdrant_store.py`)
- **Nom de la collection** : `audit_logs`.
- **Dimension des vecteurs** : `VECTOR_SIZE = 128`.
- **Métrique de distance** : **cosinus** (`Distance.COSINE`).
- **Payload indexé par point** : `event_type`, `action`, `account_id`, `target_system`, `actor`, `severity`, `created_at`, `summary`, `db_id`. L'identifiant de point est un UUID.
- **Cas d'usage** : recherche dans les logs d'audit pour l'assistant IAM (`POST /api/v1/admin/audit/search` avec un texte de requête) — retour des hits triés par `score` de similarité, filtrables par `event_type` / `severity`.

### 6.3 Vecteurs réellement stockés — note de fidélité
La fonction `_text_to_vector` **ne fait pas appel à un modèle d'embedding ML**. Elle construit un vecteur **déterministe de 128 dimensions par hachage** (`SHA-256` sur `"{texte}_{i}"`, valeurs normalisées puis normalisation L2). Le code le mentionne explicitement : *« Peut etre remplace par un modele d'embedding ML (ex: all-MiniLM-L6-v2) »*. Le champ `embedding_model = "all-MiniLM-L6-v2"` du modèle `VectorLogEntry` décrit donc une **intention**, non l'implémentation courante. **Conséquence** : la « recherche sémantique » se comporte aujourd'hui comme une similarité **lexicale déterministe** (mêmes textes → mêmes vecteurs) ; le passage à de vrais embeddings est un point d'évolution. L'infrastructure (collection, cosinus, dimension fixe, payload) est en place pour ce remplacement.

---

## 7. Stratégie de persistance et résilience

### 7.1 Cache hybride et persistance asynchrone (`memory_store.py`)
`MemoryStore` est un **singleton thread-safe** : au démarrage il charge en mémoire les lignes récentes (operations **500**, audit **1000**, jobs de réconciliation **100**, workflows **200**). Les **lectures** d'API sont servies depuis ce cache ; les **écritures** mettent à jour le cache immédiatement puis sont persistées en PostgreSQL de façon **asynchrone** (`INSERT … ON CONFLICT … DO UPDATE`, avec `CAST` vers les enums).

### 7.2 Correctif de persistance des tâches d'arrière-plan
`_run_async` conserve chaque tâche de persistance dans un **set `_pending_tasks` (référence forte)**. Sans cela, `asyncio` ne garde qu'une **référence faible** : une tâche non référencée peut être **collectée par le GC** en cours d'exécution, et l'écriture DB **perdue silencieusement**. Un `add_done_callback` retire la tâche du set à la fin et **journalise toute exception** au lieu de la perdre. (Correctif de la branche de durcissement, commit `6cf898d`.)

### 7.3 Volumes Docker : ce qui survit
Toutes les bases utilisent des **volumes nommés** (persistance hôte indépendante du cycle de vie des conteneurs) :

| Donnée | Volume nommé | Survit à `down` | Survit à `down -v` |
|---|---|---|---|
| gateway-db | `gateway_db_data` | ✅ | ❌ |
| midpoint-postgres | `midpoint_postgres_data` | ✅ | ❌ |
| odoo-db / keycloak-db / intranet-db | `*_db_data` | ✅ | ❌ |
| Redis | `redis_data` | ✅ | ❌ |
| Qdrant | `qdrant_data` | ✅ | ❌ |

- `docker compose down` : les conteneurs sont supprimés, **les volumes sont conservés** → aucune donnée perdue.
- `docker compose down -v` : les **volumes sont supprimés** → **toutes les données sont perdues** (bases vidées, blacklist Redis et collection Qdrant réinitialisées). Il faut alors relancer `migrations.py` (schéma + seed) après redémarrage.

### 7.4 Politiques de redémarrage
Toutes les bases de données déclarent `restart: unless-stopped` : elles redémarrent automatiquement après un crash ou un redémarrage de l'hôte (sauf arrêt explicite). Les *healthchecks* (`pg_isready`, `redis-cli ping`) permettent à Compose d'ordonner le démarrage des services dépendants une fois les bases prêtes.

---

*Document généré dans le cadre du Projet 3 — IAM Gateway (SAE S5/S6, UPEC). Co-auteur référencé : `achibani@gmail.com`. Tous les noms de colonnes, types, contraintes, TTL, dimensions et métriques sont issus du code (`app/models/*`, `db/migrations.py`, `core/*.py`) et de `docker-compose.yml`.*
