from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Seed test account
    op.execute("""
        INSERT INTO account_contexts (id, account_id, signals, intent_score, risk_flags, next_best_action, updated_at)
        VALUES ('{id}', '{account_id}', '[]', 0.0, '{{}}', NULL, '{updated_at}')
    """.format(
        id=str(uuid.uuid4()),
        account_id="test-account-001",
        updated_at=datetime.utcnow().isoformat()
    ))
    # Seed ICP definition (as a consent)
    op.execute("""
        INSERT INTO consents (id, subject_id, granted_at, revoked_at, scope, source)
        VALUES ('{id}', '{subject_id}', '{granted_at}', NULL, 'ICP', 'seed')
    """.format(
        id=str(uuid.uuid4()),
        subject_id="test-account-001",
        granted_at=datetime.utcnow().isoformat()
    ))
    # Seed signal type weights (as audit log)
    op.execute("""
        INSERT INTO audit_logs (id, event_type, actor_id, payload, created_at, compliance_tag)
        VALUES ('{id}', 'seed_signal_weights', 'system', '{{"job_posting": 0.8, "crm_stage_change": 0.7, "web_visit": 0.3}}', '{created_at}', 'seed')
    """.format(
        id=str(uuid.uuid4()),
        created_at=datetime.utcnow().isoformat()
    ))

def downgrade():
    op.execute("DELETE FROM account_contexts WHERE account_id = 'test-account-001'")
    op.execute("DELETE FROM consents WHERE subject_id = 'test-account-001'")
    op.execute("DELETE FROM audit_logs WHERE event_type = 'seed_signal_weights'")
