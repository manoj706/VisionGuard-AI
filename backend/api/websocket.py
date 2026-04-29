from __future__ import annotations

import asyncio
import json
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from auth import verify_ws_token


router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        dead = []
        async with self._lock:
            for websocket in self._connections:
                try:
                    await websocket.send_text(json.dumps(message, default=str))
                except Exception:
                    dead.append(websocket)
            for websocket in dead:
                self._connections.discard(websocket)


@router.websocket("/ws/scene")
async def scene_socket(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    try:
        verify_ws_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    manager: ConnectionManager = websocket.app.state.connection_manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
