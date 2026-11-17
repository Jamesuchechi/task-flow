import asyncio
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections keyed by user_id."""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[user_id].add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(user_id)
            if sockets is not None:
                sockets.discard(websocket)
                if not sockets:
                    del self._connections[user_id]

    async def send_to_user(
        self,
        user_id: int,
        event: str,
        data: Any = None,
    ) -> None:
        async with self._lock:
            sockets = list(self._connections.get(user_id, set()))

        if not sockets:
            return

        payload = {
            "event": event,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        stale: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)

        if stale:
            async with self._lock:
                user_sockets = self._connections.get(user_id)
                if user_sockets is not None:
                    for ws in stale:
                        user_sockets.discard(ws)
                    if not user_sockets:
                        del self._connections[user_id]

    async def active_connection_count(self) -> int:
        async with self._lock:
            return sum(len(sockets) for sockets in self._connections.values())


ws_manager = ConnectionManager()
