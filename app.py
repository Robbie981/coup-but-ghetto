from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
from typing import Dict

# import your engine
from game_engine.coup_engine import GameState, Action, Phase

app = FastAPI()

# ---- SINGLE GAME (MVP) ----
game = GameState(["steve", "sky"])
connections: Dict[str, WebSocket] = {}

# ---- HELPERS ----
def serialize_for(player_name: str):
    """
    Player-specific game state (hides influences)
    """
    state = {
        "phase": game.phase.name,
        "current_player": game.current_player().name,
        "players": [],
        "pending_action": game.pending_action.name if game.pending_action else None,
        "pending_actor": game.pending_actor.name if game.pending_actor else None,
        "pending_target": game.pending_target.name if game.pending_target else None,
    }

    for p in game.players:
        state["players"].append({
            "name": p.name,
            "coins": p.coins,
            "alive": p.alive,
            "influences": (
                [r.name for r in p.influences]
                if p.name == player_name
                else len(p.influences)
            ),
            "revealed": [r.name for r in p.revealed],
        })

    return state


async def broadcast():
    for name, ws in connections.items():
        await ws.send_json({
            "type": "state",
            "state": serialize_for(name)
        })


# ---- WEBSOCKET ----
@app.websocket("/ws/{player_name}")
async def websocket_endpoint(ws: WebSocket, player_name: str):
    await ws.accept()
    connections[player_name] = ws

    await broadcast()

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data) 

            try:
                if msg["type"] == "action":
                    game.apply_action(
                        actor_name=player_name,
                        action=Action[msg["action"]],
                        target_name=msg.get("target"),
                    )

                    if game.phase == Phase.RESOLUTION:
                        game.resolve_action()

                elif msg["type"] == "challenge":
                    game.apply_challenge(player_name)

            except Exception as e:
                await ws.send_json({
                    "type": "error",
                    "message": str(e)
                })

            await broadcast()

    except WebSocketDisconnect:
        connections.pop(player_name, None)
