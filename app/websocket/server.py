"""
WebSocket Server for Real-Time Updates

Broadcasts events to connected clients based on tenant ID.
Supports: action.proposed, intent.updated, signal.received
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import logging
import json
from app.api.main import app

logger = logging.getLogger("websocket")


class ConnectionManager:
    """Manages WebSocket connections grouped by tenant"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, tenant_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = []
        self.active_connections[tenant_id].append(websocket)
        logger.info(f"WebSocket connected for tenant {tenant_id}. Total connections: {len(self.active_connections[tenant_id])}")
    
    async def disconnect(self, websocket: WebSocket, tenant_id: str):
        """Remove a WebSocket connection"""
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].remove(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
        logger.info(f"WebSocket disconnected for tenant {tenant_id}")
    
    async def broadcast(self, tenant_id: str, message: dict):
        """
        Broadcast message to all connections for a tenant.
        
        Args:
            tenant_id: Tenant ID to broadcast to
            message: Message dict with 'type' and event data
        """
        if tenant_id not in self.active_connections:
            logger.debug(f"No active connections for tenant {tenant_id}")
            return
        
        disconnected = []
        for connection in self.active_connections[tenant_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection, tenant_id)
    
    async def send_to_connection(self, websocket: WebSocket, message: dict):
        """Send message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")


# Global connection manager
manager = ConnectionManager()


@app.websocket("/ws/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    """
    WebSocket endpoint for real-time updates.
    
    Clients connect to /ws/{tenant_id} and receive:
    - action.proposed: New action requires approval
    - intent.updated: Account intent score changed
    - signal.received: New signal ingested
    """
    await manager.connect(websocket, tenant_id)
    
    try:
        while True:
            # Receive messages from client (mainly for keepalive)
            data = await websocket.receive_text()
            
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
            else:
                logger.debug(f"Received message from client: {data}")
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket, tenant_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket, tenant_id)


# Helper function to broadcast from other parts of the app
async def broadcast_event(tenant_id: str, event_type: str, data: dict):
    """
    Broadcast an event to all WebSocket clients for a tenant.
    
    Usage:
        from app.websocket.server import broadcast_event
        
        await broadcast_event(
            tenant_id=account.tenant_id,
            event_type='action.proposed',
            data={'action_id': str(action.id), 'account_id': str(account.id)}
        )
    
    Args:
        tenant_id: Tenant ID
        event_type: Event type (action.proposed, intent.updated, signal.received)
        data: Event payload
    """
    message = {
        'type': event_type,
        **data
    }
    await manager.broadcast(tenant_id, message)
