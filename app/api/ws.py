import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.websocket import ws_manager
from app.db import database
from app.dependencies import get_user_from_token
from app.services.users import UserService

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/tasks")
async def tasks_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    raw_token = token
    if not raw_token:
        auth_header = websocket.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            raw_token = auth_header[7:].strip()

    if not raw_token or database.SessionLocal is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with database.SessionLocal() as session:
        user = await get_user_from_token(raw_token, UserService(session))

    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(user.id, websocket)
    await websocket.send_json(
        {
            "event": "connected",
            "user_id": user.id,
            "username": user.username,
        }
    )

    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"event": "pong"})
                continue

            try:
                parsed = json.loads(message)
                if isinstance(parsed, dict) and parsed.get("type") == "ping":
                    await websocket.send_json({"event": "pong"})
                    continue
            except json.JSONDecodeError:
                pass

            await websocket.send_json({"event": "ack", "message": message})
    except WebSocketDisconnect:
        await ws_manager.disconnect(user.id, websocket)
