from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("omnidesk.realtime")

router = APIRouter()


class RealtimeHub:
    """Manages WebSocket connections and broadcasts real-time events to all
    connected clients."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
        logger.debug("WebSocket client connected (total=%d)", len(self._clients))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)
        logger.debug("WebSocket client disconnected (total=%d)", len(self._clients))

    async def broadcast(self, payload: dict) -> None:
        async with self._lock:
            clients = list(self._clients)

        stale: list[WebSocket] = []
        for websocket in clients:
            try:
                await websocket.send_text(json.dumps(payload, ensure_ascii=False))
            except Exception:
                stale.append(websocket)

        if stale:
            async with self._lock:
                for websocket in stale:
                    self._clients.discard(websocket)


hub = RealtimeHub()


@router.websocket("/ws/inbox")
async def ws_inbox(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        await websocket.send_text(json.dumps({"type": "ready"}, ensure_ascii=False))
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                break
    finally:
        await hub.disconnect(websocket)
