from alembic import op

def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS laboratory")
    tables = [
        'signals',
        'account_contexts',
        'actions',
        'audit_logs',
        'consents',
        'accounts',
        'tenants',
        'integrations'
    ]
    for table in tables:
        op.execute(f"""
            CREATE TABLE laboratory.{table} (LIKE public.{table} INCLUDING ALL);
        """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'laboratory_user') THEN
                CREATE ROLE laboratory_user;
            END IF;
        END
        $$;
        GRANT USAGE ON SCHEMA laboratory TO laboratory_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA laboratory TO laboratory_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA laboratory TO laboratory_user;
        REVOKE ALL ON SCHEMA public FROM laboratory_user;
    """)
    import logging
    logging.getLogger("alembic.runtime.migration").info("Laboratory schema created with full isolation")

def downgrade():
    op.execute("DROP SCHEMA IF EXISTS laboratory CASCADE")
    op.execute("DROP ROLE IF EXISTS laboratory_user")
