
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from sqlalchemy.orm import Session

Base = declarative_base()

# Defense-in-depth: Add tenant_id filter to all queries (RLS is primary)
@event.listens_for(Session, "do_orm_execute")
def add_tenant_filter(execute_state):
	"""
	Automatically add tenant_id filter to all queries (defense-in-depth).
	RLS at database level is primary security, this is backup.
	"""
	if not execute_state.is_select:
		return
	# Get tenant_id from session info
	if not hasattr(execute_state.session, "info"):
		return
	tenant_id = execute_state.session.info.get("tenant_id")
	if not tenant_id:
		return
	# NOTE: Actual filter logic must be implemented per-model or via custom query class.
	# This is a placeholder for defense-in-depth. RLS is the true isolation.
