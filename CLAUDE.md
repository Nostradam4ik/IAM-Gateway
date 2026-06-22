# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An intelligent multi-target IAM provisioning gateway (SAE student project "Projet 3"). A FastAPI backend (`gateway/app`) + React admin UI (`gateway/frontend`) sit in front of **MidPoint** (the central IAM hub) and a set of target systems (OpenLDAP, Odoo ERP, PostgreSQL "intranet", Keycloak). The gateway adds a dynamic rule engine, multi-level approval workflows, reconciliation, scheduled syncs, an AI assistant, and semantic audit search.

The codebase is primarily **French** (comments, docstrings, log messages, some UI). Match that when editing. Per `README.md`, generated documents/deliverables should credit `achibani@gmail.com` as co-author.

## Commands

Everything runs through Docker Compose. There is no Makefile.

```bash
# Full stack, staged startup (DBs → IAM services → gateway → frontend) with health checks
./start.sh                 # add --reset to recreate containers (keeps volumes), --logs to tail
docker compose up -d       # plain start; docker compose down [--remove-orphans] to stop

# Database schema + seed (NOT auto-run on container start — must be invoked once)
./scripts/init-db.sh                                   # runs migrations inside the gateway container
docker compose exec -T gateway python -m app.db.migrations   # equivalent, direct

# Backend local dev (Python 3.11; needs Postgres/Redis/etc reachable — see config.py defaults / .env)
cd gateway && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000              # API at :8000, Swagger at /docs, health at /health

# Frontend (Vite dev server on :3000, proxies /api → :8000)
cd gateway/frontend && npm install
npm run dev          # dev server
npm run build        # tsc typecheck + vite build
npm run lint         # eslint (max-warnings 0)
npm run test         # vitest (no test files currently exist)

# MidPoint integration smoke test (requires the stack running)
python scripts/tests/test_midpoint_integration.py
```

There is **no backend test suite** and no Python linter configured. `scripts/` holds many one-off bash/python helpers for CSV→MidPoint imports and Odoo/Keycloak sync demos.

### Service ports

API `8000` · Frontend `3000` · MidPoint `8080` · Odoo `8069` · Keycloak `8081` · phpLDAPadmin `8088` · OpenLDAP `10389`/`10636` · Redis `6379` · Qdrant `6333`/`6334`. Postgres instances are split: gateway `5434`, MidPoint `5433`, intranet `55432`. Default API login is `admin` / `admin123` (seeded in `gateway_users` and mirrored in `admin.py` `TEMP_USERS`; the banner in `start.sh` saying `admin/admin` is wrong for the API).

## Architecture

### Dual provisioning mode — this is the key design decision

`settings.MIDPOINT_ENABLED` (default `True`) switches between two entirely different provisioning paths:

- **Hub mode (default):** `services/midpoint_provision_service.py`. The gateway only talks to MidPoint; MidPoint owns identities and propagates to target systems via **roles** (target system → role name, e.g. `LDAP → "ldap-user"`, see `_map_targets_to_roles`). Shadows/reconciliation are MidPoint's job.
- **Legacy direct mode:** `services/provision_service.py`. The gateway writes directly to each target connector, tracks operations with manual **rollback actions**, and maintains its own account-state cache.

`continue_after_approval` in `provision_service.py` does both: it first tries MidPoint, then falls back to direct connector writes.

### MemoryStore — hybrid in-memory cache over Postgres (`core/memory_store.py`)

A thread-safe **singleton** that is the read path for operations, audit logs, reconciliation jobs, and workflows. On startup (`ensure_cache_loaded`) it bulk-loads recent rows from Postgres into in-memory dicts/lists. Writes update the cache immediately and persist to Postgres **fire-and-forget** via `_run_async` (errors are logged, not raised). Consequences to keep in mind:

- API reads come from the cache, **not** live SQL — data can lag a failed async write.
- It uses **raw `text()` SQL** with hard-coded column lists and explicit Postgres enum casts (`CAST(:x AS operationstatus)`). The column lists in `memory_store.py` must stay aligned with the `CREATE TABLE` statements in `db/migrations.py`. Changing a table means editing both places (and the enum lists).

### Schema management — raw SQL, not Alembic

Two mechanisms coexist:
- `core/database.py` `init_db()` runs `SQLModel.metadata.create_all` on app startup (from the `app/models/*` SQLModel classes).
- `db/migrations.py` is the authoritative idempotent migration script (`CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` + enum creation + indexes + seed data). Run it manually after first boot. The `app/models/*` SQLModel definitions and the migrations SQL are maintained by hand and can drift — trust `migrations.py` for the live schema.

### Connectors (`connectors/`)

`BaseConnector` (ABC) defines the uniform async account CRUD interface. `ConnectorFactory` resolves a target name to an instance and caches it:
- **Static** connectors come from `config.py` env settings: `MidPointConnector`, `LDAPConnector`, `SQLConnector`, `OdooConnector`.
- **Dynamic** connectors are loaded from the `connector_configurations` DB table into a generic `DynamicConnector` that dispatches by `connector_type` (`sql`/`ldap`/`rest`/`erp`). GLPI, Keycloak, Firebase are intentionally `NotImplementedError` as static — they must be added at runtime via the Connectors page (dynamic). After changing connector configs, call `ConnectorFactory.invalidate_cache()`.

### Rule engine (`services/rule_engine.py`)

Attribute mapping via **sandboxed Jinja2** (`SafeJinjaEnvironment`, a `SandboxedEnvironment` with custom filters like `normalize_name`, `generate_login`, `slugify`). Rules run per target system, sorted by descending `priority`, each rule's output fed into the context for later rules. **Caveat:** most persistence methods here are stubs returning hard-coded `_get_default_rules` mocks — the `rules` DB table exists and is seeded, but the engine is not fully wired to it yet. Verify before assuming a rule edit persists.

### Auth & security (`core/security.py`, `api/admin.py`)

JWT (HS256) issued at `POST /api/v1/admin/token`. Each token carries a unique `jti`; logout/revocation works by blacklisting the `jti` in Redis (`get_current_user` checks the blacklist on every request). RBAC via `require_role([...])` dependency. Two user stores currently coexist: the `gateway_users` table and an in-memory `TEMP_USERS` dict in `admin.py` (lazy bcrypt hashing) — be aware both exist when touching auth.

### App startup (`main.py` lifespan)

Order matters: logging → Postgres (`init_db`) → MemoryStore cache load → Redis (sessions/blacklist) → Qdrant (semantic audit search) → APScheduler. Redis and Qdrant degrade gracefully if unavailable. Each API module under `api/` is a router mounted under `/api/v1/<area>`; the area-to-router map lives at the bottom of `main.py`.

### Other moving parts

- **Workflows** (`services/workflow_service.py`, `api/workflow.py`): multi-level approval, email-based with `approve_token`/`reject_token`; config in `WORKFLOW_MAX_LEVELS` / `WORKFLOW_DEFAULT_TIMEOUT_HOURS`.
- **Scheduler** (`services/scheduler_service.py`): APScheduler `AsyncIOScheduler` with in-memory job store; drives Odoo→MidPoint syncs, department→role auto-assignment (`DEPARTMENT_ROLE_MAPPING`), and expired-contract handling.
- **Webhooks** (`api/webhooks.py`): inbound MidPoint notifications that re-provision to Keycloak via its admin REST API. Mounted at `/api/v1/webhooks` (no extra prefix in `main.py`).
- **MidPoint XML config** lives in `infrastructure/midpoint/` (resources, roles, object templates, Groovy connector scripts for Odoo). These are imported into MidPoint, not used by the Python code directly.

### Frontend (`gateway/frontend`)

React 18 + Vite + TypeScript. State: Zustand (`store/auth.ts`) + TanStack Query. UI: Tailwind + Radix + Monaco (rule editing) + i18n (`en`/`fr`/`uk`). All HTTP goes through `src/lib/api.ts` — a single Axios instance that injects the JWT and redirects to `/login` on 401; add new endpoints there. Routing in `App.tsx`: public `/` and `/login`, everything else under a `PrivateRoute`-guarded `/dashboard/*`.
