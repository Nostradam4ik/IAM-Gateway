"""
Database migrations and initialization script for Gateway IAM.
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


async def create_tables():
    """Create all database tables."""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # Provisioning Operations Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS provisioning_operations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                request_id VARCHAR(100) NOT NULL,
                operation_type VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                source_system VARCHAR(100),
                target_system VARCHAR(100) NOT NULL,
                identity_type VARCHAR(50) NOT NULL,
                identity_id VARCHAR(255) NOT NULL,
                attributes JSONB,
                calculated_attributes JSONB,
                error_message TEXT,
                rollback_data JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # Account State Cache Table
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

        # Provisioning Rules Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS provisioning_rules (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                target_system VARCHAR(100) NOT NULL,
                identity_type VARCHAR(50) NOT NULL,
                priority INTEGER DEFAULT 100,
                is_active BOOLEAN DEFAULT true,
                conditions JSONB,
                attribute_mappings JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                version INTEGER DEFAULT 1
            )
        """))

        # Workflow Configurations Table
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

        # Workflow Instances Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS workflow_instances (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_config_id UUID REFERENCES workflow_configs(id),
                operation_id UUID REFERENCES provisioning_operations(id),
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                current_level INTEGER DEFAULT 1,
                request_data JSONB,
                approvals JSONB,
                started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP WITH TIME ZONE,
                expires_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # Approval Decisions Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS approval_decisions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_instance_id UUID REFERENCES workflow_instances(id),
                level INTEGER NOT NULL,
                approver_id VARCHAR(255) NOT NULL,
                approver_name VARCHAR(255),
                decision VARCHAR(50) NOT NULL,
                comments TEXT,
                decided_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Audit Logs Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                event_type VARCHAR(100) NOT NULL,
                source_system VARCHAR(100),
                target_system VARCHAR(100),
                identity_id VARCHAR(255),
                operation_id UUID,
                action VARCHAR(100) NOT NULL,
                status VARCHAR(50),
                actor VARCHAR(255),
                actor_ip VARCHAR(50),
                details JSONB,
                changes JSONB,
                error_details JSONB
            )
        """))

        # Reconciliation Jobs Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reconciliation_jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                target_system VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                total_accounts INTEGER DEFAULT 0,
                matched_accounts INTEGER DEFAULT 0,
                unmatched_gateway INTEGER DEFAULT 0,
                unmatched_target INTEGER DEFAULT 0,
                discrepancies INTEGER DEFAULT 0,
                discrepancy_details JSONB,
                error_message TEXT,
                triggered_by VARCHAR(100)
            )
        """))

        # Users Table (for gateway authentication)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gateway_users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(100) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) NOT NULL DEFAULT 'viewer',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP WITH TIME ZONE
            )
        """))

        # API Keys Table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                key_hash VARCHAR(255) NOT NULL UNIQUE,
                user_id UUID REFERENCES gateway_users(id),
                permissions JSONB,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE,
                last_used_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_operations_request_id ON provisioning_operations(request_id)",
            "CREATE INDEX IF NOT EXISTS idx_operations_status ON provisioning_operations(status)",
            "CREATE INDEX IF NOT EXISTS idx_operations_identity ON provisioning_operations(identity_id)",
            "CREATE INDEX IF NOT EXISTS idx_operations_created ON provisioning_operations(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cache_identity ON account_state_cache(identity_id)",
            "CREATE INDEX IF NOT EXISTS idx_rules_target ON provisioning_rules(target_system)",
            "CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflow_instances(status)",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_identity ON audit_logs(identity_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_logs(event_type)",
        ]
        for index_sql in indexes:
            await conn.execute(text(index_sql))

        print("All tables created successfully!")

    await engine.dispose()


async def seed_data():
    """Seed initial data."""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # Hash the default admin password using bcrypt directly
        admin_password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert default admin user (password: admin123)
        await conn.execute(text("""
            INSERT INTO gateway_users (username, email, password_hash, full_name, role)
            VALUES (
                :username,
                :email,
                :password_hash,
                :full_name,
                :role
            )
            ON CONFLICT (username) DO NOTHING
        """), {
            "username": "admin",
            "email": "admin@gateway.local",
            "password_hash": admin_password_hash,
            "full_name": "Administrator",
            "role": "admin"
        })

        # Insert sample provisioning rule for LDAP
        await conn.execute(text("""
            INSERT INTO provisioning_rules (name, description, target_system, identity_type, attribute_mappings)
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
                    "mail": "{{ email | default(first_name | lower ~ ''.'' ~ last_name | lower ~ ''@example.com'') }}",
                    "displayName": "{{ first_name }} {{ last_name }}",
                    "employeeNumber": "{{ employee_id }}",
                    "department": "{{ department | default(''General'') }}",
                    "title": "{{ job_title | default(''Employee'') }}"
                }'::jsonb
            )
            ON CONFLICT (name) DO NOTHING
        """))

        # Insert sample provisioning rule for SQL Intranet
        await conn.execute(text("""
            INSERT INTO provisioning_rules (name, description, target_system, identity_type, attribute_mappings)
            VALUES (
                'intranet_employee_default',
                'Default Intranet SQL provisioning rule for employees',
                'sql_intranet',
                'employee',
                '{
                    "username": "{{ first_name | lower }}.{{ last_name | lower }}",
                    "email": "{{ email }}",
                    "first_name": "{{ first_name }}",
                    "last_name": "{{ last_name }}",
                    "department": "{{ department }}",
                    "job_title": "{{ job_title }}",
                    "employee_id": "{{ employee_id }}"
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
