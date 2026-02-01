from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Add tenant_id (nullable)
    for table in [
        'accounts', 'signals', 'account_contexts', 'actions', 'audit_logs', 'consents',
        'laboratory.signals', 'laboratory.account_contexts', 'laboratory.actions', 'laboratory.experiment_cohorts']:
        op.add_column(table, sa.Column('tenant_id', sa.String, nullable=True))

    # Step 2: Backfill tenant_id for existing data (default tenant)
    op.execute("UPDATE accounts SET tenant_id = '00000000-0000-0000-0000-000000000000'")
    for table in ['signals', 'account_contexts', 'actions', 'audit_logs', 'consents']:
        op.execute(f"UPDATE {table} SET tenant_id = '00000000-0000-0000-0000-000000000000'")
    for table in ['laboratory.signals', 'laboratory.account_contexts', 'laboratory.actions', 'laboratory.experiment_cohorts']:
        op.execute(f"UPDATE {table} SET tenant_id = '00000000-0000-0000-0000-000000000000'")

    # Step 3: Set NOT NULL and add indexes
    for table in [
        'accounts', 'signals', 'account_contexts', 'actions', 'audit_logs', 'consents',
        'laboratory.signals', 'laboratory.account_contexts', 'laboratory.actions', 'laboratory.experiment_cohorts']:
        op.alter_column(table, 'tenant_id', nullable=False)
        op.create_index(f'ix_{table.replace(".", "_")}_tenant_id', table, ['tenant_id'])

    # Step 4: Enable RLS (manual step, but add policy here for reference)
    # Example for accounts table:
    op.execute("ALTER TABLE accounts ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation ON accounts FOR ALL TO PUBLIC USING (tenant_id = current_setting('app.tenant_id')::uuid)")

def downgrade():
    # Remove RLS and tenant_id columns/indexes
    op.execute("ALTER TABLE accounts DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON accounts")
    for table in [
        'accounts', 'signals', 'account_contexts', 'actions', 'audit_logs', 'consents',
        'laboratory.signals', 'laboratory.account_contexts', 'laboratory.actions', 'laboratory.experiment_cohorts']:
        op.drop_index(f'ix_{table.replace(".", "_")}_tenant_id', table_name=table)
        op.drop_column(table, 'tenant_id')
