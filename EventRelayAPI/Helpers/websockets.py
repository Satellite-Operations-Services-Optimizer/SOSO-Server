from fastapi import WebSocket
from typing import Optional

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, Optional[str]] = {}
        self.grouped_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, group_name: Optional[str]):
        await websocket.accept()
        self.active_connections.update({websocket: group_name})
        if group_name is not None:
            if group_name not in self.grouped_connections:
                self.grouped_connections[group_name] = set()
            group = self.grouped_connections[group_name]
            group.add(websocket)

    def disconnect(self, websocket: WebSocket):
        group_name = self.active_connections.pop(websocket)
        if group_name is None: return
        self.grouped_connections[group_name].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, group_name: Optional[str]):
        if group_name is None:
            connections = self.active_connections.keys()
        else:
            connections = self.grouped_connections[group_name]

        for connection in connections:
            await connection.send_text(message)