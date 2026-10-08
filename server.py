"""DirectChat signaling relay prototype. No message history or database."""
import asyncio
import json
import os
import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="DirectChat Signaling", version="0.1.0")
clients = {}
lock = asyncio.Lock()
CODE = re.compile(r"^[A-Z0-9]{8,32}$")

@app.get("/")
def health():
    return {"service": "DirectChat Signaling", "status": "ok", "storage": "none"}

@app.websocket("/ws/{user_code}")
async def signaling(websocket: WebSocket, user_code: str):
    code = user_code.upper()
    if not CODE.fullmatch(code):
        await websocket.close(code=1008, reason="Invalid user code")
        return
    await websocket.accept()
    async with lock:
        old = clients.get(code)
        clients[code] = websocket
    if old and old is not websocket:
        try:
            await old.close(code=4001, reason="Replaced by a new session")
        except Exception:
            pass
    await websocket.send_json({"type": "ready", "code": code})
    try:
        while True:
            raw = await websocket.receive_text()
            if len(raw) > 65536:
                await websocket.send_json({"type":"error", "message":"Payload too large"})
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type":"error", "message":"Invalid JSON"})
                continue
            if not isinstance(data, dict) or data.get("type") not in {"offer", "answer", "ice", "hangup", "ping"}:
                await websocket.send_json({"type":"error", "message":"Unsupported signaling type"})
                continue
            if data["type"] == "ping":
                await websocket.send_json({"type":"pong"})
                continue
            target = str(data.get("to", "")).upper()
            if not CODE.fullmatch(target) or target == code:
                await websocket.send_json({"type":"error", "message":"Invalid recipient"})
                continue
            async with lock:
                peer = clients.get(target)
            if peer is None:
                await websocket.send_json({"type":"peer_offline", "to":target})
                continue
            # Only transiently relay signaling payload. Never log or persist it.
            await peer.send_json({"type":data["type"], "from":code, "payload":data.get("payload")})
            await websocket.send_json({"type":"relayed", "to":target})
    except WebSocketDisconnect:
        pass
    finally:
        async with lock:
            if clients.get(code) is websocket:
                clients.pop(code, None)
