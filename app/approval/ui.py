try:
    from fastapi import APIRouter, Request
except ImportError:
    APIRouter = Request = None
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import AuditLog

router = APIRouter()

@router.get("/approval/ui", response_class=HTMLResponse)
async def approval_ui(request: Request):
    session: AsyncSession = request.state.db
    result = await session.execute(select(AuditLog).where(AuditLog.event_type == "send_email", AuditLog.compliance_tag == "proposed"))
    actions = [row[0] for row in result.fetchall()]
    html = """
    <html><head><title>Approval Queue</title></head><body>
    <h1>Pending Email Approvals</h1>
    <table border='1'><tr><th>Account</th><th>Email</th><th>Reasoning</th><th>Approve</th><th>Reject</th></tr>
    """
    for action in actions:
        payload = action.payload or {}
        html += f"<tr><td>{payload.get('account_name')}</td>"
        html += f"<td><pre>{payload.get('email')}</pre></td>"
        html += f"<td>{payload.get('reasoning')}</td>"
        html += f"<td><form method='post' action='/api/actions/{action.id}/approve'><button type='submit'>Approve</button></form></td>"
        html += f"<td><form method='post' action='/api/actions/{action.id}/reject'><input name='reason' placeholder='Reason'><button type='submit'>Reject</button></form></td></tr>"
    html += "</table></body></html>"
    return HTMLResponse(content=html)
