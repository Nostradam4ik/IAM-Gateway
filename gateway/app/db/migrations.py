"""
Script de migration et initialisation de la base de donnees Gateway IAM.

Ce module cree toutes les tables PostgreSQL necessaires au fonctionnement :
    - provisioning_operations : historique des operations de provisionnement
    - audit_logs : journal d'audit avec recherche vectorielle
    - reconciliation_jobs : jobs de reconciliation (comparaison source/cible)
    - workflows : instances de workflows d'approbation multi-niveaux
    - rules : regles de mapping d'attributs (Jinja2)
    - connector_configurations : connecteurs configures dynamiquement
    - gateway_users : utilisateurs de la gateway avec niveaux de droits
    - system_states : etats systeme (ex: provisioning_enabled)

Les colonnes sont alignees avec memory_store.py pour la coherence du cache.
Les enums PostgreSQL (operationtype, operationstatus, etc.) sont crees en premier.
Les ALTER TABLE ajoutent les colonnes manquantes aux tables existantes (idempotent).
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
import sys
import bcrypt

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.config import settings


async def create_enums(conn):
    """Create PostgreSQL enums used by memory_store."""
    enums = [
        ("operationtype", ["CREATE", "UPDATE", "DELETE", "DISABLE", "ENABLE", "ASSIGN_ROLE", "REVOKE_ROLE", "SYNC"]),
        ("operationstatus", ["PENDING", "IN_PROGRESS", "SUCCESS", "FAILED", "AWAITING_APPROVAL", "APPROVED", "REJECTED", "ROLLED_BACK"]),
        ("auditeventtype", ["PROVISION", "RECONCILIATION", "WORKFLOW", "AUTH", "SYSTEM", "ERROR"]),
        ("auditseverity", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    ]
    for enum_name, values in enums:
        values_str = ", ".join(f"'{v}'" for v in values)
        try:
            await conn.execute(text(f"""
                DO $$ BEGIN
                    CREATE TYPE {enum_name} AS ENUM ({values_str});
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
        except Exception:
            pass


async def create_tables():
    """Create all database tables aligned with memory_store.py."""
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

    async with engine.begin() as conn:
        # Create enums first
        await create_enums(conn)

        # ==========================================
        # Provisioning Operations Table
        # Colonnes alignees avec memory_store.py:
        #   SELECT: id, correlation_id, operation_type, status, target_systems,
        #           account_id, input_attributes, calculated_attributes,
        #           error_message, created_at, updated_at
        #   INSERT: id, correlation_id, operation_type (CAST operationtype),
        #           status (CAST operationstatus), target_systems, account_id,
        #           input_attributes, calculated_attributes, error_message, created_at, updated_at
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS provisioning_operations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                correlation_id VARCHAR(100),
                operation_type operationtype NOT NULL DEFAULT 'CREATE',
                status operationstatus NOT NULL DEFAULT 'PENDING',
                source_system VARCHAR(100),
                target_systems VARCHAR(500),
                account_id VARCHAR(255),
                identity_type VARCHAR(50),
                input_attributes JSONB,
                calculated_attributes JSONB,
                error_message TEXT,
                rollback_data JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # ==========================================
        # Audit Logs Table
        # Colonnes alignees avec memory_store.py:
        #   SELECT: id, created_at, event_type, target_system, account_id,
        #           action, severity, actor, details
        #   INSERT: id, created_at, event_type (CAST auditeventtype),
        #           target_system, account_id, action,
        #           severity (CAST auditseverity), actor, details
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                event_type auditeventtype NOT NULL DEFAULT 'SYSTEM',
                source_system VARCHAR(100),
                target_system VARCHAR(100),
                account_id VARCHAR(255),
                operation_id UUID,
                action VARCHAR(100) NOT NULL DEFAULT '-',
                severity auditseverity DEFAULT 'INFO',
                status VARCHAR(50),
                actor VARCHAR(255),
                actor_ip VARCHAR(50),
                details JSONB,
                changes JSONB,
                error_details JSONB
            )
        """))

        # ==========================================
        # Reconciliation Jobs Table
        # Colonnes alignees avec memory_store.py:
        #   SELECT: id, status, started_at, completed_at,
        #           total_users, processed_users, discrepancies_found, targets
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reconciliation_jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                target_system VARCHAR(100),
                targets JSONB DEFAULT '[]',
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                total_users INTEGER DEFAULT 0,
                processed_users INTEGER DEFAULT 0,
                discrepancies_found INTEGER DEFAULT 0,
                total_accounts INTEGER DEFAULT 0,
                matched_accounts INTEGER DEFAULT 0,
                unmatched_gateway INTEGER DEFAULT 0,
                unmatched_target INTEGER DEFAULT 0,
                discrepancy_details JSONB,
                error_message TEXT,
                triggered_by VARCHAR(100)
            )
        """))

        # ==========================================
        # Workflows Table
        # Colonnes alignees avec memory_store.py save_workflow/load
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS workflows (
                id VARCHAR(100) PRIMARY KEY,
                workflow_id VARCHAR(255),
                operation_id VARCHAR(255),
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                current_level INTEGER DEFAULT 1,
                total_levels INTEGER DEFAULT 1,
                user_name VARCHAR(255),
                operation_name VARCHAR(255),
                pending_approvers TEXT,
                context JSONB DEFAULT '{}',
                approve_token VARCHAR(255),
                reject_token VARCHAR(255),
                email_sent BOOLEAN DEFAULT false,
                decided_at TIMESTAMP WITH TIME ZONE,
                decided_by VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # ==========================================
        # Account State Cache Table
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS account_state_cache (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                identity_id VARCHAR(255) NOT NULL,
                target_system VARCHAR(100) NOT NULL,
                target_account_id VARCHAR(255),
                state JSONB NOT NULL,
                last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_provisioned_at TIMESTAMP WITH TIME ZONE,
                is_synchronized BOOLEAN DEFAULT true,
                UNIQUE(identity_id, target_system)
            )
        """))

        # ==========================================
        # Provisioning Rules Table
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rules (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                target_system VARCHAR(100) NOT NULL,
                rule_type VARCHAR(50) DEFAULT 'attribute_mapping',
                identity_type VARCHAR(50) NOT NULL DEFAULT 'employee',
                priority INTEGER DEFAULT 100,
                is_active BOOLEAN DEFAULT true,
                conditions JSONB,
                attribute_mappings JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                version INTEGER DEFAULT 1
            )
        """))

        # Rule Versions Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rule_versions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                rule_id UUID,
                version INTEGER NOT NULL,
                name VARCHAR(255),
                attribute_mappings JSONB,
                conditions JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                change_description TEXT
            )
        """))

        # Rollback Actions Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rollback_actions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                operation_id UUID,
                target_system VARCHAR(100),
                action_type VARCHAR(50),
                previous_state JSONB,
                new_state JSONB,
                status VARCHAR(50) DEFAULT 'pending',
                executed_at TIMESTAMP WITH TIME ZONE,
                error_message TEXT
            )
        """))

        # Target Account States Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS target_account_states (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                operation_id UUID,
                target_system VARCHAR(100),
                account_id VARCHAR(255),
                status VARCHAR(50),
                attributes JSONB,
                error_message TEXT,
                provisioned_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # Discrepancies Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS discrepancies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                job_id UUID,
                identity_id VARCHAR(255),
                target_system VARCHAR(100),
                discrepancy_type VARCHAR(50),
                gateway_value JSONB,
                target_value JSONB,
                resolved BOOLEAN DEFAULT false,
                resolved_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # ==========================================
        # Workflow Configurations Table
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS workflow_configs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                trigger_type VARCHAR(50) NOT NULL,
                trigger_conditions JSONB,
                approval_levels JSONB NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100)
            )
        """))

        # Workflow Instances Table (legacy)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS workflow_instances (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_config_id UUID,
                operation_id UUID,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                current_level INTEGER DEFAULT 1,
                request_data JSONB,
                approvals JSONB,
                started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP WITH TIME ZONE,
                expires_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # Approval Levels Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS approval_levels (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_config_id UUID,
                level INTEGER NOT NULL,
                approver_type VARCHAR(50),
                approver_role VARCHAR(100),
                timeout_hours INTEGER DEFAULT 48,
                auto_approve_on_timeout BOOLEAN DEFAULT false
            )
        """))

        # Approval Decisions Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS approval_decisions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_instance_id UUID,
                level INTEGER NOT NULL,
                approver_id VARCHAR(255) NOT NULL,
                approver_name VARCHAR(255),
                decision VARCHAR(50) NOT NULL,
                comments TEXT,
                decided_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # ==========================================
        # Gateway Users Table
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gateway_users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(100) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) NOT NULL DEFAULT 'viewer',
                roles JSONB DEFAULT '[]'::jsonb,
                permission_level INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP WITH TIME ZONE
            )
        """))

        # Approval Roles Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS approval_roles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                role_name VARCHAR(100) NOT NULL UNIQUE,
                display_name VARCHAR(255) NOT NULL,
                description TEXT,
                approval_level INTEGER NOT NULL DEFAULT 1,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # ==========================================
        # Connector Configurations Table
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS connector_configurations (
                id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                connector_type VARCHAR(50) NOT NULL,
                connector_subtype VARCHAR(50) NOT NULL,
                display_name VARCHAR(255) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT true,
                configuration JSONB NOT NULL DEFAULT '{}',
                last_health_status VARCHAR(50) DEFAULT 'unknown',
                last_health_check TIMESTAMP WITH TIME ZONE,
                last_health_error TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                midpoint_resource_oid VARCHAR(255),
                midpoint_sync_status VARCHAR(50) DEFAULT 'not_synced',
                midpoint_last_sync TIMESTAMP WITH TIME ZONE,
                midpoint_sync_error TEXT
            )
        """))

        # ==========================================
        # AI Configuration Table
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_configuration (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                provider VARCHAR(50),
                model VARCHAR(100),
                api_key_hash VARCHAR(255),
                settings JSONB DEFAULT '{}',
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # ==========================================
        # Policy Configs Table
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS policy_configs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL UNIQUE,
                policy_type VARCHAR(50),
                conditions JSONB,
                actions JSONB,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # ==========================================
        # System States Table
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS system_states (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                key VARCHAR(255) NOT NULL UNIQUE,
                value JSONB,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # ==========================================
        # Vector Log Entries (for Qdrant indexing)
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vector_log_entries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                audit_log_id UUID,
                qdrant_point_id VARCHAR(255),
                embedding_text TEXT,
                indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # ==========================================
        # App Users / Profiles / Permissions
        # ==========================================
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS app_users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(100) UNIQUE,
                email VARCHAR(255),
                permission_level INTEGER DEFAULT 1,
                department VARCHAR(100),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS app_profiles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID,
                profile_data JSONB,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS app_user_permissions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID,
                resource VARCHAR(255),
                permission VARCHAR(50),
                granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # ==========================================
        # Migration: Add missing columns to existing tables
        # ==========================================
        alter_statements = [
            # provisioning_operations: add memory_store columns
            "ALTER TABLE provisioning_operations ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(100)",
            "ALTER TABLE provisioning_operations ADD COLUMN IF NOT EXISTS target_systems VARCHAR(500)",
            "ALTER TABLE provisioning_operations ADD COLUMN IF NOT EXISTS account_id VARCHAR(255)",
            "ALTER TABLE provisioning_operations ADD COLUMN IF NOT EXISTS input_attributes JSONB",
            # audit_logs: add memory_store columns
            "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS account_id VARCHAR(255)",
            "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS severity auditseverity DEFAULT 'INFO'",
            # reconciliation_jobs: add memory_store columns
            "ALTER TABLE reconciliation_jobs ADD COLUMN IF NOT EXISTS total_users INTEGER DEFAULT 0",
            "ALTER TABLE reconciliation_jobs ADD COLUMN IF NOT EXISTS processed_users INTEGER DEFAULT 0",
            "ALTER TABLE reconciliation_jobs ADD COLUMN IF NOT EXISTS discrepancies_found INTEGER DEFAULT 0",
            "ALTER TABLE reconciliation_jobs ADD COLUMN IF NOT EXISTS targets JSONB DEFAULT '[]'",
            # gateway_users: add permission_level
            "ALTER TABLE gateway_users ADD COLUMN IF NOT EXISTS permission_level INTEGER DEFAULT 1",
            # midpoint columns for connectors
            "ALTER TABLE connector_configurations ADD COLUMN IF NOT EXISTS midpoint_resource_oid VARCHAR(255)",
            "ALTER TABLE connector_configurations ADD COLUMN IF NOT EXISTS midpoint_sync_status VARCHAR(50) DEFAULT 'not_synced'",
            "ALTER TABLE connector_configurations ADD COLUMN IF NOT EXISTS midpoint_last_sync TIMESTAMP WITH TIME ZONE",
            "ALTER TABLE connector_configurations ADD COLUMN IF NOT EXISTS midpoint_sync_error TEXT",
        ]
        for alter_sql in alter_statements:
            try:
                await conn.execute(text(alter_sql))
            except Exception:
                pass

        # ==========================================
        # Create indexes
        # ==========================================
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_operations_correlation ON provisioning_operations(correlation_id)",
            "CREATE INDEX IF NOT EXISTS idx_operations_status ON provisioning_operations(status)",
            "CREATE INDEX IF NOT EXISTS idx_operations_account ON provisioning_operations(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_operations_created ON provisioning_operations(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cache_identity ON account_state_cache(identity_id)",
            "CREATE INDEX IF NOT EXISTS idx_rules_target ON rules(target_system)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_created ON workflows(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_audit_account ON audit_logs(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_logs(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_logs(severity)",
            "CREATE INDEX IF NOT EXISTS idx_connectors_type ON connector_configurations(connector_type)",
            "CREATE INDEX IF NOT EXISTS idx_connectors_midpoint ON connector_configurations(midpoint_resource_oid)",
            "CREATE INDEX IF NOT EXISTS idx_recon_status ON reconciliation_jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_vector_audit ON vector_log_entries(audit_log_id)",
        ]
        for index_sql in indexes:
            try:
                await conn.execute(text(index_sql))
            except Exception:
                pass

        print("All tables created successfully!")

    await engine.dispose()


async def seed_data():
    """Seed initial data."""
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

    async with engine.begin() as conn:
        # Hash the default admin password using bcrypt directly
        admin_password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert default admin user (password: admin123)
        await conn.execute(text("""
            INSERT INTO gateway_users (username, email, password_hash, full_name, role, roles)
            VALUES (
                :username,
                :email,
                :password_hash,
                :full_name,
                :role,
                :roles
            )
            ON CONFLICT (username) DO NOTHING
        """), {
            "username": "admin",
            "email": "admin@gateway.local",
            "password_hash": admin_password_hash,
            "full_name": "Administrator",
            "role": "admin",
            "roles": '["admin", "iam_engineer"]'
        })

        # Insert sample provisioning rule for LDAP
        await conn.execute(text("""
            INSERT INTO rules (name, description, target_system, identity_type, attribute_mappings)
            VALUES (
                'ldap_employee_default',
                'Default LDAP provisioning rule for employees',
                'ldap',
                'employee',
                '{
                    "uid": "{{ employee_id }}",
                    "cn": "{{ first_name }} {{ last_name }}",
                    "sn": "{{ last_name }}",
                    "givenName": "{{ first_name }}",
                    "mail": "{{ email }}",
                    "displayName": "{{ first_name }} {{ last_name }}"
                }'::jsonb
            )
            ON CONFLICT (name) DO NOTHING
        """))

        # Insert sample workflow configuration
        await conn.execute(text("""
            INSERT INTO workflow_configs (name, description, trigger_type, trigger_conditions, approval_levels)
            VALUES (
                'new_employee_approval',
                'Approval workflow for new employee provisioning',
                'pre_provisioning',
                '{"operation_types": ["create"], "identity_types": ["employee"]}'::jsonb,
                '[
                    {
                        "level": 1,
                        "name": "Manager Approval",
                        "approver_type": "manager",
                        "timeout_hours": 48,
                        "auto_approve_on_timeout": false
                    },
                    {
                        "level": 2,
                        "name": "IT Approval",
                        "approver_type": "role",
                        "approver_role": "it_admin",
                        "timeout_hours": 24,
                        "auto_approve_on_timeout": true
                    }
                ]'::jsonb
            )
            ON CONFLICT (name) DO NOTHING
        """))

        print("Seed data inserted successfully!")

    await engine.dispose()


async def main():
    """Run migrations."""
    print("Starting database migrations...")
    await create_tables()
    print("\nSeeding initial data...")
    await seed_data()
    print("\nMigrations completed!")


if __name__ == "__main__":
    asyncio.run(main())
