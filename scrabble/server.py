import asyncio
import json
from typing import MutableMapping, Optional, Tuple, cast

import websockets
from websockets.server import WebSocketServerProtocol

from scrabble.serializers.transport.msg import WebsocketMessageSchema
from scrabble.transport.msg import (AuthMessageRequest, AuthMessageResponse, AuthMessageResponsePayload,
                                    EndConnectionMessage, EndConnectionPayload, NewConnectionMessage,
                                    NewConnectionPayload, WebsocketMessage)


class Server:

    def __init__(self, *, on_new_conn=None, on_end_conn=None, on_new_msg=None):
        self._players_to_connections: MutableMapping[str, WebSocketServerProtocol] = {}
        self._connections_to_players: MutableMapping[WebSocketServerProtocol, str] = {}
        self._tasks_by_player: MutableMapping[str, asyncio.Task] = {}

        self._on_new_conn = on_new_conn
        self._on_end_conn = on_end_conn
        self._on_new_msg = on_new_msg

    def to_ws_msg(self, msg: WebsocketMessage) -> str:
        return json.dumps(WebsocketMessageSchema().dump(msg))

    def from_ws_msg(self, raw_msg: str) -> WebsocketMessage:
        return WebsocketMessageSchema().load(json.loads(raw_msg))

    def disconnect(self, player: str) -> None:
        self._tasks_by_player[player].cancel()

    async def register(self, ws: WebSocketServerProtocol, path: str) -> Tuple[bool, str]:
        ws_msg = await ws.recv()
        auth_msg = self.from_ws_msg(cast(str, ws_msg))
        assert isinstance(auth_msg, AuthMessageRequest)

        username = auth_msg.payload.username
        if username in self._players_to_connections:
            print('Duplicated client')
            await self.send(ws, AuthMessageResponse(payload=AuthMessageResponsePayload(ok=False)))

            return False, username
        else:
            self._players_to_connections[username] = ws
            self._connections_to_players[ws] = username

            if self._on_new_conn is not None:
                self._on_new_conn(username)

            answer = AuthMessageResponse(payload=AuthMessageResponsePayload(ok=True))
            await self.send(ws, answer)

            new_conn_msg = NewConnectionMessage(payload=NewConnectionPayload(username=username))
            await self.publish(new_conn_msg, except_conn=ws)

            current_connections_futures = []
            for player in self._players_to_connections:
                if player != username:
                    new_conn_msg = NewConnectionMessage(payload=NewConnectionPayload(username=player))
                    current_connections_futures.append(self.send(ws, new_conn_msg))
            if current_connections_futures:
                await asyncio.wait(current_connections_futures)

            return True, username

    async def unregister(self, ws: WebSocketServerProtocol, path: str) -> None:
        username = self._connections_to_players[ws]

        del self._connections_to_players[ws]
        del self._players_to_connections[username]
        del self._tasks_by_player[username]

        end_conn_msg = EndConnectionMessage(payload=EndConnectionPayload(username=username))
        await self.publish(end_conn_msg, except_conn=ws)

        if self._on_end_conn is not None:
            self._on_end_conn(username)

    async def publish(self, msg: WebsocketMessage, *, except_conn=None) -> None:
        futures = [conn.send(self.to_ws_msg(msg)) for conn in self._connections_to_players if conn != except_conn]
        if futures:
            await asyncio.wait(futures)

    async def send(self, conn: WebSocketServerProtocol, msg: WebsocketMessage) -> None:
        await conn.send(self.to_ws_msg(msg))

    async def send_player(self, player: str, msg: WebsocketMessage) -> None:
        conn = self._players_to_connections[player]
        await self.send(conn, msg)

    async def start(self, host: Optional[str] = None, port: int = 5678) -> None:
        server = await websockets.serve(self.serve, host, port, ping_interval=1, ping_timeout=2)
        print('Started', server, host, port)

    async def _recv(self, conn: WebSocketServerProtocol) -> None:
        try:
            async for raw_msg in conn:
                msg = self.from_ws_msg(cast(str, raw_msg))
                print('Recv', msg)

                if self._on_new_msg is not None:
                    self._on_new_msg(self._connections_to_players[conn], msg)
        except Exception as e:
            print(f'Error raised {e}')

    async def serve(self, websocket: WebSocketServerProtocol, path: str) -> None:
        ok, username = await self.register(websocket, path)
        if ok:
            try:
                task = asyncio.Task(self._recv(websocket))
                self._tasks_by_player[username] = task
                await task
            finally:
                await self.unregister(websocket, path)

    async def stop(self) -> None:
        for player in list(self._players_to_connections):
            self.disconnect(player)

        futures = [client.wait_closed() for client in self._connections_to_players]
        if futures:
            await asyncio.wait(futures, return_when=asyncio.ALL_COMPLETED)
