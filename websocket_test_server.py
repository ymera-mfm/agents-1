#!/usr/bin/env python3
"""
Minimal WebSocket test server for testing load testing scripts
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import logging
from typing import List, Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YMERA WebSocket Test Server")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")


manager = ConnectionManager()


@app.get("/")
async def root():
    return {"status": "ok", "name": "YMERA Test Server"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "websocket_connections": len(manager.active_connections)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    subscriptions: Set[str] = set()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            
            elif message_type == "subscribe":
                channel = message.get("channel")
                subscriptions.add(channel)
                logger.info(f"Client subscribed to: {channel}")
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "channel": channel
                }))
            
            elif message_type == "unsubscribe":
                channel = message.get("channel")
                subscriptions.discard(channel)
                logger.info(f"Client unsubscribed from: {channel}")
                await websocket.send_text(json.dumps({
                    "type": "unsubscribed",
                    "channel": channel
                }))
            
            elif message_type == "agent_message":
                from_user = message.get("from")
                to_agent = message.get("to")
                payload = message.get("payload", {})
                original_timestamp = payload.get("timestamp")
                
                response = {
                    "type": "agent_response",
                    "from": to_agent,
                    "to": from_user,
                    "payload": {
                        "status": "processed",
                        "action": payload.get("action"),
                        "data": payload.get("data", {})
                    }
                }
                
                if original_timestamp:
                    response["timestamp"] = original_timestamp
                
                await websocket.send_text(json.dumps(response))
            
            elif message_type == "disconnect":
                logger.info("Client requested disconnect")
                await websocket.send_text(json.dumps({
                    "type": "disconnect_ack"
                }))
                break
            
            else:
                # Echo back
                await websocket.send_text(json.dumps({
                    "type": "message",
                    "data": message
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    print("Starting YMERA WebSocket Test Server...")
    print("Server will be available at: http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
