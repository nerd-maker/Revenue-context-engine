from alembic import op

def upgrade():
    tables = ['signals', 'account_contexts', 'actions', 'audit_logs', 'consents']
    for table in tables:
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
                FOR ALL TO app_user
                USING (tenant_id = current_setting('app.tenant_id')::uuid);
            ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
        """)
    op.execute("""
        CREATE ROLE IF NOT EXISTS app_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
    """)
    op.execute("""
        -- In production, configure DATABASE_URL to use app_user
        -- postgresql://app_user:password@host:5432/revenue_context
    """)

def downgrade():
    tables = ['signals', 'account_contexts', 'actions', 'audit_logs', 'consents']
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute("DROP ROLE IF EXISTS app_user")
