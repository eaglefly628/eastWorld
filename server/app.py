"""FastAPI application — HTTP + WebSocket server for EastWorld."""

from __future__ import annotations

import json
import os
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from server.agent import create_backend
from server.models import Position
from server.world import (
    NPCS,
    PLAYERS,
    add_player,
    get_nearby_npc,
    get_world_state,
    remove_player,
)

app = FastAPI(title="EastWorld")

BACKEND_TYPE = os.environ.get("EASTWORLD_BACKEND", "mock")
agent_backend = create_backend(BACKEND_TYPE)

# Serve static files (frontend)
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Active WebSocket connections
connections: dict[str, WebSocket] = {}


async def broadcast(message: dict, exclude: str | None = None):
    """Send a message to all connected players."""
    data = json.dumps(message)
    for pid, ws in list(connections.items()):
        if pid != exclude:
            try:
                await ws.send_text(data)
            except Exception:
                pass


@app.get("/")
async def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    player_id = str(uuid.uuid4())[:8]
    player_name = None

    try:
        # Wait for join message with player name
        raw = await ws.receive_text()
        msg = json.loads(raw)
        if msg.get("type") != "join":
            await ws.close()
            return

        player_name = msg.get("name", f"Stranger-{player_id[:4]}")
        player = add_player(player_id, player_name)
        connections[player_id] = ws

        # Send initial world state
        await ws.send_text(json.dumps({
            "type": "init",
            "player_id": player_id,
            "world": get_world_state(),
        }))

        # Broadcast new player joined
        await broadcast({
            "type": "player_joined",
            "player": player.to_dict(),
        }, exclude=player_id)

        # Main message loop
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            await handle_message(player_id, msg)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error for player {player_id}: {e}")
    finally:
        connections.pop(player_id, None)
        remove_player(player_id)
        await broadcast({
            "type": "player_left",
            "player_id": player_id,
        })


async def handle_message(player_id: str, msg: dict):
    """Route incoming WebSocket messages."""
    msg_type = msg.get("type")
    player = PLAYERS.get(player_id)
    ws = connections.get(player_id)
    if not player or not ws:
        return

    if msg_type == "move":
        dx, dy = msg.get("dx", 0), msg.get("dy", 0)
        new_x = max(0, min(39, player.position.x + dx))
        new_y = max(0, min(29, player.position.y + dy))
        player.position = Position(new_x, new_y)

        # Broadcast movement
        await broadcast({
            "type": "player_moved",
            "player_id": player_id,
            "position": {"x": new_x, "y": new_y},
        })

        # Check if near an NPC
        npc = get_nearby_npc(player)
        if npc:
            await ws.send_text(json.dumps({
                "type": "near_npc",
                "npc_id": npc.id,
                "npc_name": npc.name,
                "greeting": npc.greeting,
            }))

    elif msg_type == "talk":
        npc_id = msg.get("npc_id")
        message = msg.get("message", "")
        npc = NPCS.get(npc_id)

        if not npc or not message:
            return

        # Generate NPC response
        response = await agent_backend.generate_response(
            npc, player.name, message
        )

        # Send response back to the talking player
        await ws.send_text(json.dumps({
            "type": "npc_response",
            "npc_id": npc_id,
            "npc_name": npc.name,
            "message": response,
        }))

        # Broadcast that a conversation is happening (others can see)
        await broadcast({
            "type": "conversation",
            "player_name": player.name,
            "npc_name": npc.name,
            "npc_id": npc_id,
        }, exclude=player_id)

    elif msg_type == "ping":
        await ws.send_text(json.dumps({"type": "pong"}))
