from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
from typing import Dict, List, Optional

from game_engine.coup_engine import GameState, Action, Phase

app = FastAPI()

# ---- LOBBY / GAME STATE ----
connections: Dict[str, WebSocket] = {}
lobby_players: List[str] = []
game: Optional[GameState] = None
game_started = False


# ---- HELPERS ----
def serialize_for(player_name: str):
    if not game_started or not game:
        return {
            "phase": "LOBBY",
            "players": [{"name": p} for p in lobby_players]
        }

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
    global game, game_started

    await ws.accept()

    # Prevent duplicate names
    if player_name in connections:
        await ws.send_json({
            "type": "error",
            "message": "Name already taken"
        })
        await ws.close()
        return

    connections[player_name] = ws

    if not game_started:
        lobby_players.append(player_name)

    await broadcast()

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            try:
                # ---- START GAME ----
                if msg["type"] == "start_game":
                    if game_started:
                        raise Exception("Game already started")

                    if lobby_players[0] != player_name:
                        raise Exception("Only host can start the game")

                    if len(lobby_players) < 2:
                        raise Exception("Need at least 2 players")

                    game = GameState(lobby_players)
                    game_started = True

                # ---- GAME ACTIONS ----
                elif msg["type"] == "action":
                    if not game_started:
                        raise Exception("Game not started")

                    game.apply_action(
                        actor_name=player_name,
                        action=Action[msg["action"]],
                        target_name=msg.get("target"),
                    )

                    if game.phase == Phase.RESOLUTION:
                        game.resolve_action()

                elif msg["type"] == "challenge":
                    if not game_started:
                        raise Exception("Game not started")

                    game.apply_challenge(player_name)

            except Exception as e:
                await ws.send_json({
                    "type": "error",
                    "message": str(e)
                })

            await broadcast()

    except WebSocketDisconnect:
        connections.pop(player_name, None)

        if not game_started:
            lobby_players.remove(player_name)

        await broadcast()
