# IAM Gateway — Architecture

## 1. Project Overview

IAM Gateway is an intelligent, multi-target identity-provisioning gateway built with **FastAPI** (Python 3.11, async) and a **React** admin UI. It sits in front of **MidPoint** (the central IAM hub) and orchestrates the lifecycle of identities across downstream target systems — **OpenLDAP**, **Odoo ERP**, a PostgreSQL "intranet" application, and **Keycloak**. It exists to give an organization a single, rule-driven control plane for joiner/mover/leaver flows, multi-level approval workflows, reconciliation, scheduled HR synchronisation, and a searchable audit trail — instead of operating each target system by hand. The gateway can run in two modes: **MidPoint-hub mode** (the default, where MidPoint propagates to targets) or **legacy direct-connector mode** (where the gateway writes each target itself with rollback).

---

## 2. System Architecture Diagram

```
                          ┌───────────────────────────────────────────┐
                          │  React Admin UI (Vite → nginx)             │
                          │  http://localhost:3000                     │
                          └───────────────────────┬────────────────────┘
                                                  │ REST/HTTPS + JWT Bearer
                                                  │ (Vite proxy /api → :8000)
                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Gateway  ·  http://localhost:8000                    │
│   api/ (routes) → services/ (logic) → connectors/ (adapters) → MidPoint/LDAP/...   │
└───┬───────────┬───────────┬───────────┬────────────┬───────────┬──────────────────┘
    │ SQL       │ RESP       │ REST/gRPC │ REST       │ LDAP       │ XML-RPC
    │ (asyncpg) │            │           │ (httpx)    │ (ldap3)    │
    ▼           ▼            ▼           ▼            ▼            ▼
┌─────────┐ ┌────────┐ ┌──────────┐ ┌──────────────────┐ ┌──────────┐ ┌──────────┐
│gateway- │ │ Redis  │ │ Qdrant   │ │ MidPoint 4.4     │ │ OpenLDAP │ │ Odoo 17  │
│  db     │ │ :6379  │ │ :6333/4  │ │ :8080  (HUB)     │ │ :10389   │ │ :8069    │
│ :5434   │ │ JWT    │ │ semantic │ │ /ws/rest/*       │ │ inetOrg  │ │ XML-RPC  │
│ Postgres│ │ block- │ │ audit    │ │ Basic Auth       │ │ Person   │ │ res.users│
│ (cache) │ │ list + │ │ search   │ └───┬─────────┬────┘ └──────────┘ └──────────┘
└─────────┘ │ rate   │ └──────────┘     │ propagates (MidPoint connectors)
            │ limit  │                  │ LDAP / JDBC / scripted
            └────────┘     ┌────────────┼───────────────┬──────────────┐
                           ▼            ▼               ▼              ▼
                     ┌──────────┐ ┌──────────┐   ┌──────────────┐ ┌──────────┐
                     │ OpenLDAP │ │ Odoo DB  │   │ intranet-db  │ │midpoint- │
                     │          │ │ :odoo-db │   │ :55432 (SQL) │ │ postgres │
                     └──────────┘ └──────────┘   └──────────────┘ │ :5433    │
                                                                  └──────────┘
   ┌──────────────────────────────────────────────────────────────────────────┐
   │  MidPoint  ──(webhook, HMAC-SHA256)──►  Gateway /webhooks/midpoint/        │
   │            user-change  ──►  KeycloakProvisioner (REST admin API)  ──►      │
   │            Keycloak :8081  (keycloak-db Postgres, internal)                 │
   └──────────────────────────────────────────────────────────────────────────┘
```

**Protocol legend:** REST = HTTP/JSON, RESP = Redis protocol, LDAP = ldap3, XML-RPC = Odoo, SQL = asyncpg/SQLAlchemy. The gateway authenticates the browser with a **JWT Bearer**; it authenticates to MidPoint with **HTTP Basic**; MidPoint calls back into the gateway with an **HMAC-signed** webhook.

> The diagram lists the host-published instances. There are in total **five PostgreSQL** instances (gateway-db, midpoint-postgres, odoo-db, intranet-db, keycloak-db); odoo-db and keycloak-db are internal-only.

---

## 3. Component Descriptions

| Component | Port (host) | Role |
|---|---|---|
| **React Admin UI** | `3000` (nginx → `:80`) | SPA for operators: provisioning forms, rules editor (Monaco), workflows, reconciliation, connectors, MidPoint users, audit logs. Talks only to the gateway. |
| **FastAPI Gateway** | `8000` | The control plane. Exposes the REST API (`/api/v1/...`), enforces auth/RBAC, runs the rule engine, workflows, scheduler, and all connectors. Swagger at `/docs`. |
| **MidPoint 4.4** | `8080` | Central IAM hub. Owns the identity repository, propagates to its Resources (LDAP/Odoo/SQL), and performs reconciliation. The gateway drives it over `/ws/rest`. |
| **Keycloak 23** | `8081` (`→ :8080`) | OIDC identity provider for end-user SSO. Provisioned from MidPoint changes via the gateway webhook. Runs `start-dev`. |
| **OpenLDAP** | `10389` (`→ :389`), `10636` (LDAPS) | Directory of `inetOrgPerson` accounts and groups under `dc=example,dc=com`. A provisioning target. |
| **phpLDAPadmin** | `8088` (`→ :80`) | Web UI to inspect/manage LDAP. |
| **Odoo 17 (ERP)** | `8069` | HR source-of-truth (employees, departments, contracts) and a provisioning target. Driven over XML-RPC. |
| **gateway-db (Postgres 15)** | `127.0.0.1:5434` | Durable store for operations, audit logs, reconciliation jobs, workflows, connector configs, gateway users. |
| **midpoint-postgres (Postgres 15)** | `127.0.0.1:5433` | MidPoint's own repository. |
| **odoo-db / keycloak-db (Postgres 15)** | internal | Backing stores for Odoo and Keycloak. |
| **intranet-db (Postgres 15)** | `127.0.0.1:55432` | The "intranet" SQL application — a provisioning target reached by `SQLConnector`. |
| **Redis 7** | `127.0.0.1:6379` | JWT revocation blacklist (`blacklist:{jti}`) and atomic login rate-limiting. |
| **Qdrant** | `127.0.0.1:6333/6334` | Vector store; every audit log is indexed for semantic search. Degrades gracefully if down. |

---

## 4. Gateway Internal Architecture

The backend is a layered FastAPI application under `gateway/app/`. Requests flow **api → services → connectors → external systems**, with `core` and `models` as cross-cutting support.

```
gateway/app/
├── main.py        FastAPI app: lifespan startup, middleware, exception handlers, router mounts
├── api/           Route handlers (14 routers). Thin: parse/validate, enforce auth, call services
├── services/      Business logic: provisioning, rules, workflows, reconciliation, scheduler, audit, email
├── connectors/    External-system adapters behind a uniform async interface (BaseConnector)
├── models/        Pydantic / SQLModel data models (requests, responses, DB tables, IAM objects)
├── core/          Cross-cutting: config, security (JWT/RBAC), database session, Redis, Qdrant, logging, MemoryStore
└── db/            migrations.py — idempotent schema + seed (raw SQL, not Alembic)
```

- **`app/api/`** — One router per functional area, each mounted under `/api/v1/...` in `main.py`. Handlers depend on `get_current_user` / `require_role(...)` for auth and on `get_session` for a DB session.
- **`app/services/`** — Where the work happens. `MidPointProvisionService` (hub mode) and `ProvisionService` (direct mode); `RuleEngine` (sandboxed Jinja2 attribute mapping); `WorkflowService` (multi-level approvals); `ReconciliationService`; `ScheduledSyncService` (APScheduler jobs); `AuditService`; `EmailService`; `UserService`.
- **`app/connectors/`** — `BaseConnector` (ABC) defines the uniform async account CRUD contract. `ConnectorFactory` returns **static** connectors (`MidPointConnector`, `LDAPConnector`, `SQLConnector`, `OdooConnector`) from config, or **dynamic** connectors loaded from the `connector_configurations` table (`DynamicConnector`, dispatching by `sql`/`ldap`/`rest`/`erp`).
- **`app/models/`** — `provision.py` (operations, enums, request/response), `connector.py`, `rules.py`, `workflow.py`, `audit.py`, `ai.py`, and `iam.py` (typed MidPoint objects: `MidpointUser`, `MidpointRole`, `MidpointResource`, `Assignment`, `MidpointShadow`).
- **`app/core/`** — `config.py` (pydantic-settings with fail-fast secret validation), `security.py` (JWT create/verify, `require_role`, async bcrypt), `database.py` (async engine + pooled session), `redis_client.py`, `qdrant_store.py`, `logging.py` (structlog + request-id contextvars), `memory_store.py` (in-memory read cache over Postgres).
- **`app/db/`** — `migrations.py` creates the enums, tables, indexes and seed data; it is the authoritative live schema (run once after first boot).

**Startup sequence** (`main.py` lifespan): configure logging → `init_db()` (`SQLModel.create_all`) → load `MemoryStore` cache from Postgres → connect Redis → connect Qdrant → start APScheduler. **Middleware:** a request-context middleware assigns an `X-Request-ID`, binds it to structlog, logs method/path/status/latency, and converts unhandled errors into a generic 500. **Exception handlers** return a consistent `{"detail", "request_id"}` body for `HTTPException` and validation errors.

---

## 5. API Endpoints Reference

All routes are under `/api/v1`. **Auth column:** `Public` = none; `JWT` = any authenticated user (`get_current_user`); `RBAC:<roles>` = `require_role([...])`; `HMAC` = MidPoint webhook signature. Generated from the route decorators and their dependencies.

### admin.py — authentication, system status, audit, emergency stop
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/admin/token` | Public (rate-limited) | Log in, returns a JWT (DB-backed `gateway_users`). |
| GET | `/admin/me` | JWT | Current user identity + roles. |
| POST | `/admin/logout` | JWT | Revoke the token (Redis blacklist by `jti`). |
| GET | `/admin/status` | JWT | Live status of DB/Redis/LDAP/MidPoint. |
| POST | `/admin/emergency-stop` | RBAC: admin | Disable all provisioning ("red button"). |
| POST | `/admin/resume` | RBAC: admin | Re-enable provisioning. |
| POST | `/admin/audit/search` | JWT | Search audit logs. |
| GET | `/admin/audit/recent` | JWT | Recent audit log entries. |
| GET | `/admin/config` | RBAC: admin | Gateway config (no secrets). |
| GET | `/admin/connectors/status` | JWT | Per-connector connectivity. |
| GET | `/admin/metrics` | JWT | Operation/workflow metrics. |

### provision.py — provisioning operations & MidPoint orchestration
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/provision/` | RBAC: admin,iam_engineer | Provision an account (hub or direct mode). |
| GET | `/provision/{operation_id}` | JWT | Operation status. |
| POST | `/provision/{operation_id}/rollback` | RBAC: admin,iam_engineer | Roll back an operation. |
| GET | `/provision/` | JWT | List operations. |
| PUT | `/provision/{operation_id}` | RBAC: admin,iam_engineer | Update an account across targets. |
| DELETE | `/provision/{operation_id}` | RBAC: admin | Delete the account from targets. |
| GET | `/provision/midpoint/users` | JWT | List MidPoint users. |
| GET | `/provision/midpoint/users/{account_id}` | JWT | MidPoint user + shadows. |
| GET | `/provision/midpoint/roles` | JWT | List MidPoint roles. |
| POST | `/provision/midpoint/users/{account_id}/roles/{role_name}` | RBAC: admin | Assign a role. |
| DELETE | `/provision/midpoint/users/{account_id}/roles/{role_name}` | RBAC: admin | Remove a role. |
| GET | `/provision/midpoint/resources` | JWT | List Resources. |
| GET | `/provision/midpoint/status` | JWT | MidPoint connection status. |

### midpoint.py — direct MidPoint object management
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/midpoint/users` | JWT | List users. |
| GET | `/midpoint/users/{user_id}` | JWT | User detail + shadows. |
| POST | `/midpoint/users` | RBAC: admin,iam_engineer | Create user. |
| PUT | `/midpoint/users/{user_id}` | RBAC: admin,iam_engineer | Update user. |
| DELETE | `/midpoint/users/{user_id}` | RBAC: admin | Delete user (cascades to targets). |
| POST | `/midpoint/users/{user_id}/disable` | RBAC: admin,iam_engineer | Disable user. |
| POST | `/midpoint/users/{user_id}/enable` | RBAC: admin,iam_engineer | Enable user. |
| GET | `/midpoint/roles` | JWT | List roles (typed `MidpointRoleList`). |
| POST | `/midpoint/users/{user_id}/roles/{role_id}` | RBAC: admin | Assign role. |
| DELETE | `/midpoint/users/{user_id}/roles/{role_id}` | RBAC: admin | Remove role. |
| GET | `/midpoint/users/{user_id}/roles` | JWT | User's roles. |
| GET | `/midpoint/resources` | JWT | List Resources (typed `MidpointResourceList`). |
| GET | `/midpoint/users/{user_id}/shadows` | JWT | Shadow accounts (target projections). |
| GET | `/midpoint/health` | JWT | MidPoint reachability. |

### rules.py — attribute-mapping rule engine
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/rules/` | JWT | List rules. |
| POST | `/rules/` | RBAC: admin,iam_engineer | Create rule. |
| GET | `/rules/{rule_id}` | JWT | Rule detail. |
| PUT | `/rules/{rule_id}` | RBAC: admin,iam_engineer | Update rule. |
| DELETE | `/rules/{rule_id}` | RBAC: admin | Delete rule. |
| POST | `/rules/test` | JWT | Test a rule against sample data. |
| GET | `/rules/{rule_id}/versions` | JWT | Rule version history. |
| POST | `/rules/{rule_id}/restore/{version}` | RBAC: admin,iam_engineer | Restore a version. |
| GET | `/rules/policies/` | JWT | List policies. |
| POST | `/rules/policies/` | RBAC: admin | Create policy. |
| GET | `/rules/policies/{policy_id}` | JWT | Policy detail. |

### workflow.py — multi-level approval workflows
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/workflow/configs` | JWT | List workflow configs. |
| POST | `/workflow/configs` | RBAC: admin | Create config. |
| GET | `/workflow/configs/{config_id}` | JWT | Config detail. |
| PUT | `/workflow/configs/{config_id}` | RBAC: admin | Update config. |
| GET | `/workflow/instances` | JWT | List instances. |
| GET | `/workflow/instances/pending` | JWT | Pending approvals. |
| GET | `/workflow/instances/{instance_id}` | JWT | Instance detail. |
| POST | `/workflow/instances/{instance_id}/approve` | JWT (object check) | Approve (object-level `can_approve`). |
| POST | `/workflow/instances/{instance_id}/reject` | JWT (object check) | Reject. |
| POST | `/workflow/instances/{instance_id}/cancel` | RBAC: admin | Cancel. |
| GET | `/workflow/instances/{instance_id}/history` | JWT | Decision history. |
| GET | `/workflow/instances/{instance_id}/details` | JWT | Full details. |
| GET | `/workflow/approve-by-email` | Public (token) | Email approval via signed token in query. |

### reconcile.py — reconciliation jobs
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/reconcile/start` | RBAC: admin,iam_engineer | Start a reconciliation job. |
| GET | `/reconcile/status/{job_id}` | JWT | Job status. |
| GET | `/reconcile/jobs` | JWT | List jobs. |
| GET | `/reconcile/{job_id}/discrepancies` | JWT | Discrepancies found. |
| POST | `/reconcile/{job_id}/resolve` | RBAC: admin,iam_engineer | Resolve discrepancies. |
| POST | `/reconcile/sync-cache` | RBAC: admin | Refresh the account-state cache. |
| GET | `/reconcile/cache/stats` | JWT | Cache statistics. |

### connectors.py — dynamic connector management
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/connectors/` | JWT | List connectors. |
| GET | `/connectors/types` | JWT | Available connector types. |
| GET | `/connectors/health` | JWT | Health summary. |
| GET | `/connectors/{connector_id}` | JWT | Connector detail. |
| POST | `/connectors/` | RBAC: admin | Create connector. |
| PUT | `/connectors/{connector_id}` | RBAC: admin | Update connector. |
| DELETE | `/connectors/{connector_id}` | RBAC: admin | Delete connector. |
| POST | `/connectors/{connector_id}/test` | JWT | Test a stored connector. |
| POST | `/connectors/test-preview` | RBAC: admin | Test an unsaved config (SSRF-gated to admin). |
| POST | `/connectors/{connector_id}/toggle` | RBAC: admin | Enable/disable. |
| POST | `/connectors/health-check` | RBAC: admin | Run all health checks. |
| POST | `/connectors/{connector_id}/sync-to-midpoint` | RBAC: admin | Create matching MidPoint Resource. |
| GET | `/connectors/{connector_id}/midpoint-status` | JWT | MidPoint-sync status. |
| POST | `/connectors/{connector_id}/test-midpoint-resource` | RBAC: admin | Test the MidPoint Resource. |
| DELETE | `/connectors/{connector_id}/midpoint-resource` | RBAC: admin | Delete the MidPoint Resource. |
| GET | `/connectors/midpoint/resources` | JWT | List MidPoint Resources. |

### scheduler.py — APScheduler sync jobs
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/scheduler/jobs` | JWT | List scheduled jobs. |
| GET | `/scheduler/jobs/{job_id}` | JWT | Job detail. |
| POST | `/scheduler/jobs/daily` · `/interval` · `/cron` | RBAC: admin,iam_engineer | Create daily/interval/cron sync. |
| POST | `/scheduler/jobs/{job_id}/toggle` · `/run` | RBAC: admin,iam_engineer | Enable/disable or run now. |
| DELETE | `/scheduler/jobs/{job_id}` | RBAC: admin | Delete job. |
| GET | `/scheduler/history` · `/contracts/history` | JWT | Sync history. |
| POST | `/scheduler/presets/workday` · `/nightly` · `/hourly` | RBAC: admin,iam_engineer | Preset schedules. |
| POST | `/scheduler/jobs/contract-check` | RBAC: admin,iam_engineer | Contract-expiry check job. |

### users.py — gateway user administration
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/users/` | RBAC: admin | List gateway users. |
| POST | `/users/` | RBAC: admin | Create user. |
| GET | `/users/roles` | JWT | Available roles. |
| GET | `/users/by-role/{role}` · `/emails-by-role/{role}` | RBAC: admin,iam_engineer | Users/emails by role. |
| GET | `/users/approval-chain/{workflow_type}` | RBAC: admin,iam_engineer | Approval chain for a workflow type. |
| GET | `/users/{username}` | RBAC: admin | User detail. |
| PUT | `/users/{username}/roles` | RBAC: admin | Update roles. |
| DELETE | `/users/{username}` | RBAC: admin | Deactivate user. |

### permissions.py — permission levels (1–5)
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/permissions/levels` · `/users` · `/users/{user_id}` · `/stats` · `/check/{user_id}/{permission}` | JWT | Read permission levels / users / stats / checks. |
| POST | `/permissions/assign` | RBAC: admin,iam_engineer | Assign a permission level. |

### live_comparison.py — real-time cross-system view & Odoo→MidPoint sync
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/live/stats` · `/user/{identifier}` · `/odoo/contacts` · `/odoo/employees` · `/midpoint/users` · `/health-check` · `/odoo/employees-with-contracts` | JWT | Cross-system reads. |
| GET | `/live/compare` · `/sync/odoo-midpoint/compare` | RBAC: admin,iam_engineer | Compare systems. |
| POST | `/live/sync-user/{identifier}` · `/sync/odoo-to-midpoint` · `/sync/odoo-to-midpoint/with-approval` | RBAC: admin,iam_engineer | Sync into targets. |
| POST | `/live/sync/execute-approved/{workflow_id}` | RBAC: admin,it_admin | Execute an approved sync. |
| POST | `/live/account/{username}/disable` · `/enable` | RBAC: admin,iam_engineer | Disable/enable an account. |
| GET | `/live/contracts/expired` · `/contracts/expiring` | RBAC: admin,iam_engineer | Expired / expiring contracts. |

### ldap_groups.py — LDAP group membership
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/ldap/groups` · `/ldap/groups/{group_name}` · `/ldap/groups/users/search` · `/ldap/groups/user/{username}/memberships` | JWT | Read groups, members, memberships. |
| POST | `/ldap/groups/{group_name}/members` | RBAC: admin,iam_engineer | Add a member. |
| DELETE | `/ldap/groups/{group_name}/members/{username}` | RBAC: admin,iam_engineer | Remove a member. |

### webhooks.py — inbound MidPoint → Keycloak
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/webhooks/midpoint/user-change` | HMAC | MidPoint pushes a user change → provision to Keycloak. |
| POST | `/webhooks/midpoint/sync-all` | RBAC: admin | Manual full sync trigger. |
| GET | `/webhooks/health` | Public | Liveness. |

### ai_assistant.py — optional assistant (requires an API key; off by default)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/ai/query` · `/suggest-mappings` · `/generate-connector` · `/analyze-error` · `/explain-rule` | JWT | Assistant helpers for mapping/diagnostics. |
| GET/DELETE | `/ai/conversations/{conversation_id}` | JWT | Conversation history. |
| GET | `/ai/config` | JWT | Whether a provider is configured. |
| POST | `/ai/config` | RBAC: admin | Set the provider/model/API key. |

---

## 6. IAM Data Flow

### a) New employee provisioned (Odoo → MidPoint → LDAP → Keycloak)

1. **Source (Odoo).** A scheduled job (`ScheduledSyncService._execute_odoo_midpoint_sync`, or `POST /live/sync/odoo-to-midpoint`) pulls employees from Odoo via XML-RPC (`OdooConnector.list_employees` → `hr.employee`).
2. **Hub (MidPoint).** For each new employee the gateway calls `MidPointProvisionService.provision()` → `MidPointConnector.create_account()` → `POST /ws/rest/users`, building the MidPoint `UserType` (`name`, `givenName`, `familyName`, `emailAddress`, `employeeNumber`, …).
3. **Roles.** Target systems are mapped to MidPoint roles (`LDAP→ldap-user`, `ODOO→odoo-user`, `SQL→intranet-user`); the scheduler additionally maps department/title to department roles and LDAP groups. Assigning a role triggers MidPoint provisioning.
4. **Propagation (LDAP/SQL/Odoo).** MidPoint's own connectors create the projections (e.g. `uid=...,ou=users,dc=example,dc=com` in OpenLDAP). The user now has **shadow** accounts visible via `/midpoint/users/{id}/shadows`.
5. **Keycloak.** MidPoint emits a `user-change` notification → `POST /webhooks/midpoint/user-change` (HMAC-verified) → `KeycloakProvisioner` creates/updates the Keycloak user via the admin REST API (random temporary password, reset forced).
6. **Audit.** Each step is recorded by `AuditService`/`MemoryStore` and indexed in Qdrant.

### b) User deprovisioned

1. **Trigger.** `DELETE /provision/{operation_id}` or `DELETE /midpoint/users/{id}`, or the **contract-expiry** scheduler job (`_execute_contract_expiration_check`) detecting an expired Odoo contract.
2. **Hub.** `MidPointConnector.delete_account()` (`DELETE /ws/rest/users/{oid}`) or `disable_account()` (sets `activation/administrativeStatus = disabled`).
3. **Cascade.** MidPoint removes/disables the linked shadows in LDAP/Odoo/SQL.
4. **Keycloak.** The `delete`/`modify` webhook removes or disables the Keycloak account.
5. **Audit.** A `provision`/`delete` audit entry is written.

### c) Role assignment via workflow approval

1. **Request.** `POST /provision/` with `require_approval=true` and a `manager_email` (or `/midpoint/users/{id}/roles/{role}`).
2. **Workflow created.** `WorkflowService.create_approval_workflow()` records an operation in `awaiting_approval` state and generates per-level approve/reject tokens; **nothing is sent to MidPoint yet** (`midpoint_pending=True`).
3. **Notification.** `EmailService` sends the manager an email containing `/api/v1/workflow/approve-by-email?token=...` links (in `DEV_MODE` the email is logged, not sent).
4. **Decision.** The approver opens the link (or `POST /workflow/instances/{id}/approve`). The token is validated; multi-level chains advance level by level (`WORKFLOW_MAX_LEVELS`, default timeout `WORKFLOW_DEFAULT_TIMEOUT_HOURS`).
5. **Execution.** On final approval, `ProvisionService.continue_after_approval()` creates the user/assigns the role in MidPoint, which propagates to the targets; on rejection the operation is closed without provisioning.

---

## 7. Authentication & Security

### JWT
- Login (`POST /api/v1/admin/token`) verifies the password (bcrypt) against the **`gateway_users`** table via `UserService`. A built-in `admin`/`operator` fixture is honored **only when `DEBUG=true`**.
- `create_access_token` issues an **HS256** JWT containing `sub`, `roles`, `exp` (default 60 min), `iss`, `aud`, and a unique **`jti`**. `decode_token` verifies signature, expiry, issuer and audience and rejects the `none` algorithm.
- Logout / revocation: the `jti` is stored in Redis (`blacklist:{jti}`); `get_current_user` rejects any blacklisted token.
- The signing key is **mandatory in production**: `Settings` fails to start when `DEBUG=false` and `SECRET_KEY`/`JWT_SECRET_KEY` is missing, a known placeholder, or < 32 chars.

### Role hierarchy
Roles are stored per user (`gateway_users.roles`, JSONB) and checked by `require_role([...])`.

| Category | Roles | Typical capability |
|---|---|---|
| **Access** | `admin` | Full control: user/connector/rule admin, emergency stop, deletes, role grants. |
| | `iam_engineer` | Provisioning, rules, scheduler, LDAP groups, sync. |
| | `director` / `viewer` | Read-oriented. |
| **Approval** | `manager`, `rh_manager`, `it_admin`, `security_officer` | Workflow approval levels. |
| **Legacy/dev** | `operator` | In-code fixture, dev-only (`DEBUG`). |

Endpoint rule of thumb: **reads** require `JWT`; **state-changing** endpoints require `RBAC` (`admin` for deletes/role-management, `admin,iam_engineer` for most other writes) — see §5.

### Rate limiting on `/token`
`POST /admin/token` is throttled per **IP + username** (10 attempts / 5 minutes) using an atomic Redis Lua counter (`RedisClient.check_rate_limit`); exceeding it returns **429**. The limiter degrades open if Redis is unavailable (logged).

### RBAC enforcement & hardening
- Authorization is enforced in each handler's signature via `Depends(require_role([...]))`; there is no global bypass.
- The MidPoint webhook is authenticated with **HMAC-SHA256** over the raw body (`X-MidPoint-Signature`, `MIDPOINT_WEBHOOK_SECRET`), constant-time compared, fail-closed in production.
- Connector injection guards: LDAP filters/DNs are escaped (`escape_filter_chars`/`escape_rdn`); dynamic-SQL column identifiers are allow-listed.
- A request-ID middleware tags every request and unhandled errors return a generic 500 (no internal text leaked). CORS is restricted to explicit methods/headers with a per-environment origin allowlist.

---

## 8. Running Locally with Docker Desktop (Windows)

### Prerequisites
| Tool | Version |
|---|---|
| Docker Desktop (with WSL2 backend) | ≥ 4.x (Compose v2) |
| Git | ≥ 2.40 |
| (optional, local backend dev) Python | 3.11 |
| (optional, frontend dev) Node.js | 20.x |
| RAM | ~8 GB free for the full stack (MidPoint alone is allotted 3 GB) |

### Quick Start (minimal dev stack)
```bash
git clone https://github.com/Nostradam4ik/IAM-Gateway.git
cd IAM-Gateway
copy .env.example .env
# Edit .env and set strong SECRET_KEY and JWT_SECRET_KEY, e.g.:
#   python -c "import secrets; print(secrets.token_urlsafe(48))"
docker compose up gateway gateway-db redis --build
```
`gateway` declares `depends_on` for `gateway-db`, `redis` and `qdrant`, so Compose starts those automatically. The API comes up at **http://localhost:8000** (Swagger at `/docs`). In the dev Compose, `DEBUG` defaults to `true`, so if you skip the secret step an ephemeral key is generated and the stack still boots.

### Start All Services
```bash
docker compose up --build
# initialise the database schema + seed once (admin user, sample rule/workflow):
docker compose exec -T gateway python -m app.db.migrations
```
Or use the staged launcher: `./start.sh` (bash/WSL2).

### Service URLs & default credentials
| Service | URL | Default credentials |
|---|---|---|
| Gateway Frontend | http://localhost:3000 | `admin` / `admin123` (seeded `gateway_users`) |
| Gateway API / Swagger | http://localhost:8000 · `/docs` | JWT from `/api/v1/admin/token` |
| MidPoint | http://localhost:8080/midpoint | `administrator` / `5ecr3t` (forced change on first login) |
| Keycloak | http://localhost:8081 | `admin` / `admin` |
| Odoo | http://localhost:8069 | `admin` / `admin` |
| phpLDAPadmin | http://localhost:8088 | `cn=admin,dc=example,dc=com` / `secret` |
| Qdrant dashboard | http://localhost:6333/dashboard | — |

> These are **development defaults**. Rotate every credential and provide a real `.env` before any non-local deployment.

### Minimal dev stack vs full stack
- **Minimal (`gateway` + `gateway-db` + `redis` [+ `qdrant`]):** enough to run the API, log in, browse the UI, and exercise auth/rules/workflows logic. Provisioning calls that reach MidPoint will fail gracefully (MidPoint connections are lazy), so use this for backend/UI work.
- **Full (`docker compose up`):** adds MidPoint, OpenLDAP, Odoo, Keycloak and their databases — required for end-to-end provisioning, reconciliation, Odoo→MidPoint sync, and the Keycloak webhook flow.

---

## 9. Configuration Reference

From `.env.example` / `app/core/config.py`. "Required" means the app refuses to start without it when `DEBUG=false`.

| Variable | Description | Req/Opt | Default |
|---|---|---|---|
| `DEBUG` | Debug mode; enables SQL echo and in-code user fixture; auto-generates secrets. | Optional | `false` |
| `DEV_MODE` | Logs approval emails instead of sending; redacts SMTP. | Optional | `false` |
| `SECRET_KEY` | App secret. | **Required** (prod) | — |
| `JWT_SECRET_KEY` | JWT signing key (≥ 32 chars). | **Required** (prod) | — |
| `JWT_ALGORITHM` | JWT algorithm. | Optional | `HS256` |
| `JWT_EXPIRE_MINUTES` | Access-token lifetime. | Optional | `60` |
| `JWT_ISSUER` / `JWT_AUDIENCE` | Token `iss` / `aud` claims. | Optional | `iam-gateway` |
| `BCRYPT_ROUNDS` | bcrypt cost factor. | Optional | `12` |
| `MIDPOINT_WEBHOOK_SECRET` | HMAC secret for inbound MidPoint webhooks. | Optional* | — |
| `MIDPOINT_URL` | MidPoint REST base URL. | Optional | `http://midpoint-core:8080/midpoint` |
| `MIDPOINT_USER` / `MIDPOINT_PASSWORD` | MidPoint admin credentials. | Optional | `administrator` / `5ecr3t` |
| `MIDPOINT_ENABLED` | Hub mode vs direct-connector mode. | Optional | `true` |
| `MIDPOINT_VERIFY_SSL` | Verify TLS on MidPoint REST calls. | Optional | `true` |
| `DATABASE_URL` | Gateway Postgres (asyncpg) DSN. | Optional | `postgresql+asyncpg://gateway:gateway@gateway-db:5432/gateway` |
| `REDIS_URL` | Redis DSN. | Optional | `redis://redis:6379/0` |
| `QDRANT_HOST` / `QDRANT_PORT` | Qdrant location. | Optional | `qdrant` / `6333` |
| `LDAP_HOST` / `LDAP_PORT` | LDAP server. | Optional | `openldap` / `389` |
| `LDAP_BIND_DN` / `LDAP_BIND_PASSWORD` | LDAP bind identity. | Optional | `cn=admin,dc=example,dc=com` / `secret` |
| `LDAP_BASE_DN` | LDAP base context. | Optional | `dc=example,dc=com` |
| `ODOO_URL` / `ODOO_DB` / `ODOO_USER` / `ODOO_PASSWORD` | Odoo XML-RPC connection. | Optional | `http://odoo:8069` / `odoo` / `admin` / `admin` |
| `INTRANET_DB_URL` | SQL-target ("intranet") DSN. | Optional | `postgresql://intranet:intranet@intranet-db:5432/intranet` |
| `KEYCLOAK_URL` / `KEYCLOAK_REALM` | Keycloak base + realm. | Optional | `http://keycloak:8080` / `gateway` |
| `KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD` | Keycloak admin (webhook provisioning). | Optional | `admin` / `admin` |
| `OPENAI_API_KEY` / `OPENAI_MODEL` / `DEEPSEEK_API_KEY` | Optional assistant provider. | Optional | empty / `gpt-4-turbo-preview` |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `FROM_EMAIL` | Approval email delivery. | Optional | `smtp.gmail.com` / `587` / — / — / `noreply@iam-gateway.local` |
| `BASE_URL` | Public base URL for email links. | Optional | `http://localhost:8000` |
| `CORS_ORIGINS` | Allowed browser origins (JSON array). | Optional | `["http://localhost:3000", ...]` |

\* `MIDPOINT_WEBHOOK_SECRET` is required in production for the webhook to accept calls (it fails closed without it); in `DEBUG` the signature check is bypassed.

---

## 10. Project Roadmap

### Done — `security-hardening` branch (13 commits)
- Fail-fast secret validation; removed hardcoded default/inline secrets; DB pooling; stopped logging the seeded bcrypt hash.
- RBAC on every identity-mutating endpoint; DB-backed login (dev fixture gated to `DEBUG`).
- HMAC authentication on the MidPoint webhook; random Keycloak temp password.
- Fixed the `MIDPOINT_USERNAME` crash that silently broke all MidPoint resource ops.
- Injection fixes (LDAP filter/DN escaping, dynamic-SQL identifier allowlist); SSRF gating of `test-preview`.
- Moved blocking I/O (bcrypt, ldap3/xmlrpc connection tests, SMTP) off the event loop; JWT `iss`/`aud`.
- Strong-referenced background persistence tasks; brute-force rate limiting on `/token`.
- Request-ID middleware + centralized error handling; Docker hardening (healthcheck, non-root, pinned images, 127.0.0.1 datastore binding); pytest suite + GitHub Actions CI.

### Done — `iam-connector-improvements` branch (5 commits)
- MidPoint connector: TLS verification + transient-failure retry transport.
- LDAP connector: connect/receive timeouts + bind reconnection.
- Odoo connector: bounded XML-RPC timeouts + re-auth retry on stale session.
- Typed IAM object models (`app/models/iam.py`) wired onto the clean MidPoint list endpoints.
- Docker: memory limits on heavy services + restart policies on the databases.

### Remaining
- **Schema single-source-of-truth**: reconcile `SQLModel.create_all` vs `migrations.py` (adopt Alembic); align enum casing.
- **Implement stubbed persistence**: rule engine, audit log, workflow/provision config currently return mocks/no-ops in places.
- **Full async offload** of the LDAP/Odoo provisioning connectors (timeouts added; thread-offload pending).
- **JWT in HttpOnly cookies + refresh-token rotation** (currently `localStorage`; `iss`/`aud` already added).
- **TLS termination / reverse proxy**, secrets manager, audit-log immutability, and database backup/restore tooling.
- **Fix the AI request/response model mismatch** (`/ai/suggest-mappings`, `/generate-connector`) — optional feature, off by default.
