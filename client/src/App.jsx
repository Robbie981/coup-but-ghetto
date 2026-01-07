import { useEffect, useRef, useState } from "react";

const WS_URL = "ws://localhost:8000";

export default function App() {
  const [name, setName] = useState("");
  const [connected, setConnected] = useState(false);
  const [state, setState] = useState(null);
  const wsRef = useRef(null);

  const connect = () => {
    const ws = new WebSocket(`${WS_URL}/ws/${name}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "state") {
        setState(msg.state);
      }

      if (msg.type === "error") {
        alert(msg.message);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
    };
  };

  const sendAction = (action, target = null) => {
    wsRef.current?.send(JSON.stringify({
      type: "action",
      action,
      target
    }));
  };

  const challenge = () => {
    wsRef.current?.send(JSON.stringify({ type: "challenge" }));
  };

  if (!connected) {
    return (
      <div style={{ padding: 20 }}>
        <h2>Join Game</h2>
        <input
          placeholder="Player name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button onClick={connect} disabled={!name}>
          Connect
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: 20 }}>
      <h2>You are {name}</h2>

      <h3>Phase: {state?.phase}</h3>
      <h3>Turn: {state?.current_player}</h3>

      <h3>Players</h3>
      <ul>
        {state?.players.map(p => (
          <li key={p.name}>
            {p.name} — 💰 {p.coins} — 
            Influences: {Array.isArray(p.influences)
              ? p.influences.join(", ")
              : p.influences}
            — Revealed: {p.revealed.join(", ")}
          </li>
        ))}
      </ul>

      {state?.current_player === name && (
        <>
          <h3>Actions</h3>
          <button onClick={() => sendAction("INCOME")}>Income</button>
          <button onClick={() => sendAction("FOREIGN_AID")}>Foreign Aid</button>
          <button onClick={() => sendAction("TAX")}>Tax</button>
        </>
      )}

      {state?.phase === "WAITING_FOR_CHALLENGE" && (
        <>
          <h3>Challenge?</h3>
          <button onClick={challenge}>Challenge</button>
        </>
      )}
    </div>
  );
}
