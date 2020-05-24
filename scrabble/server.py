import asyncio
import json

import websockets

from scrabble.serializers.transport.msg import WebsocketMessageSchema
from scrabble.transport.msg import AuthMessageRequest, AuthMessageResponse, AuthMessageResponsePayload, WebsocketMessage


class Server:

    def __init__(self, *, on_new_conn=None, on_end_conn=None):
        self._players_to_connections = {}
        self._connections_to_players = {}
        self._on_new_conn = on_new_conn
        self._on_end_conn = on_end_conn
        self._last_time_conn_checked = {}

    def to_ws_msg(self, msg: WebsocketMessage) -> str:
        return json.dumps(WebsocketMessageSchema().dump(msg))

    def from_ws_msg(self, raw_msg: str) -> WebsocketMessage:
        return WebsocketMessageSchema().load(json.loads(raw_msg))

    async def register(self, ws, path):
        ws_msg = await ws.recv()
        auth_msg = self.from_ws_msg(ws_msg)
        assert isinstance(auth_msg, AuthMessageRequest)

        username = auth_msg.payload.username
        if username in self._players_to_connections:
            print('Duplicated client')
            await self.send(ws, AuthMessageResponse(payload=AuthMessageResponsePayload(ok=False)))
        else:
            self._players_to_connections[username] = ws
            self._connections_to_players[ws] = username
            print('Connected', username)

            if self._on_new_conn is not None:
                self._on_new_conn(username)

            answer = AuthMessageResponse(payload=AuthMessageResponsePayload(ok=True))
            await self.send(ws, answer)

    def unregister(self, ws, path):
        username = self._connections_to_players[ws]
        print('Disconnected', username)

        del self._connections_to_players[ws]
        del self._players_to_connections[username]

        if self._on_end_conn is not None:
            self._on_end_conn(username)

    async def publish(self, msg: WebsocketMessage) -> None:
        await asyncio.wait([conn.send(self.to_ws_msg(msg)) for conn in self._connections_to_players])

    async def send(self, conn, msg: WebsocketMessage) -> None:
        await conn.send(self.to_ws_msg(msg))

    async def start(self, host=None, port='5678'):
        server = await websockets.serve(self.serve, host, port, ping_interval=1, ping_timeout=2)
        print('Started', server)

    async def _recv(self, conn) -> None:
        while True:
            async for raw_msg in conn:
                msg = self.from_ws_msg(raw_msg)
                print('Recv', msg)

    async def serve(self, websocket, path):
        await self.register(websocket, path)
        try:
            futures = [
                self._recv(websocket),
            ]

            done, pending = await asyncio.wait(futures, return_when=asyncio.ALL_COMPLETED)
        finally:
            self.unregister(websocket, path)

    async def stop(self):
        futures = [client.wait_closed() for client in self._connections_to_players]
        await asyncio.wait(futures, return_when=asyncio.ALL_COMPLETED)
