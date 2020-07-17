import asyncio
import json
from dataclasses import dataclass
from typing import Callable, MutableMapping, Optional, Tuple, cast

import websockets
from websockets.server import WebSocketServerProtocol

from scrabble.serializers.transport.msg import WebsocketMessageSchema

from .msg import (AuthMessageRequest, AuthMessageResponse, AuthMessageResponsePayload, EndConnectionMessage,
                  EndConnectionPayload, NewConnectionMessage, NewConnectionPayload, WebsocketMessage)

__all__ = [
    'Server',
    'PlayerConnection',
    'PlayerConnectionID',
    'ConnectionCallback',
    'WebsocketMessageCallback',
]

PlayerConnectionID = Tuple[str, int]
ConnectionCallback = Callable[[PlayerConnectionID], None]
WebsocketMessageCallback = Callable[[PlayerConnectionID, WebsocketMessage], None]


@dataclass
class PlayerConnection:
    username: str
    game_id: int
    conn: Optional[WebSocketServerProtocol] = None

    @property
    def player_id(self) -> PlayerConnectionID:
        return self.username, self.game_id

    def __hash__(self) -> int:
        return hash(self.player_id)


class Server:

    def __init__(self, *,
                 on_new_conn: Optional[ConnectionCallback] = None,
                 on_end_conn: Optional[ConnectionCallback] = None,
                 on_new_msg: Optional[WebsocketMessageCallback] = None):
        self._players_to_connections: MutableMapping[PlayerConnectionID, WebSocketServerProtocol] = {}
        self._connections_to_players: MutableMapping[WebSocketServerProtocol, PlayerConnectionID] = {}
        self._tasks_by_player: MutableMapping[PlayerConnectionID, asyncio.Task] = {}

        self._on_new_conn = on_new_conn
        self._on_end_conn = on_end_conn
        self._on_new_msg = on_new_msg

    def to_ws_msg(self, msg: WebsocketMessage) -> str:
        return json.dumps(WebsocketMessageSchema().dump(msg))

    def from_ws_msg(self, raw_msg: str) -> WebsocketMessage:
        return WebsocketMessageSchema().load(json.loads(raw_msg))

    def disconnect(self, player_id: PlayerConnectionID) -> None:
        self._tasks_by_player[player_id].cancel()

    def add_player_conn(self, player_id: PlayerConnectionID, conn: WebSocketServerProtocol) -> None:
        self._players_to_connections[player_id] = conn
        self._connections_to_players[conn] = player_id

    def remove_player_conn(self, player_id: PlayerConnectionID) -> None:
        conn = self._players_to_connections[player_id]

        del self._connections_to_players[conn]
        del self._players_to_connections[player_id]

    async def register(self, ws: WebSocketServerProtocol, path: str) -> Tuple[bool, PlayerConnection]:
        ws_msg = await ws.recv()
        auth_msg = self.from_ws_msg(cast(str, ws_msg))
        assert isinstance(auth_msg, AuthMessageRequest)

        player_conn = PlayerConnection(username=auth_msg.payload.username,
                                       game_id=auth_msg.payload.game_id,
                                       conn=ws)
        player_id = player_conn.player_id
        username, game_id = player_id

        if player_id in self._players_to_connections:
            print('Duplicated client')
            await self.send(ws, AuthMessageResponse(payload=AuthMessageResponsePayload(ok=False)))

            return False, player_conn
        else:
            self.add_player_conn(player_id, ws)

            if self._on_new_conn is not None:
                try:
                    self._on_new_conn(player_id)
                except Exception as e:
                    print(f'Exception raised during new player registration: {repr(e)}')

                    answer = AuthMessageResponse(payload=AuthMessageResponsePayload(ok=False))
                    await self.send(ws, answer)

                    self.remove_player_conn(player_id)

                    player_conn.conn = None
                    return False, player_conn

            answer = AuthMessageResponse(payload=AuthMessageResponsePayload(ok=True))
            await self.send(ws, answer)

            # publish new connection to current players
            new_conn_msg = NewConnectionMessage(payload=NewConnectionPayload(username=username))
            await self.publish_to_game(new_conn_msg, game_id, except_conn=ws)

            # send existing connections to current player
            current_connections_futures = []
            for existing_username, existing_game_id in self._players_to_connections:
                if existing_game_id == game_id and existing_username != username:
                    new_conn_msg = NewConnectionMessage(payload=NewConnectionPayload(username=existing_username))
                    current_connections_futures.append(self.send(ws, new_conn_msg))
            if current_connections_futures:
                await asyncio.wait(current_connections_futures)

            return True, player_conn

    async def unregister(self, ws: WebSocketServerProtocol, path: str) -> None:
        player_id = self._connections_to_players[ws]
        username, game_id = player_id

        self.remove_player_conn(player_id)
        del self._tasks_by_player[player_id]

        end_conn_msg = EndConnectionMessage(payload=EndConnectionPayload(username=username))
        await self.publish_to_game(end_conn_msg, game_id, except_conn=ws)

        if self._on_end_conn is not None:
            self._on_end_conn(player_id)

    async def publish(self, msg: WebsocketMessage, *,
                      except_conn: Optional[WebSocketServerProtocol] = None) -> None:
        futures = [
            conn.send(self.to_ws_msg(msg))
            for conn in self._connections_to_players
            if conn != except_conn
        ]
        if futures:
            await asyncio.wait(futures)

    async def publish_to_game(self, msg: WebsocketMessage, game_id: int, *,
                              except_conn: Optional[WebSocketServerProtocol] = None) -> None:
        futures = [
            conn.send(self.to_ws_msg(msg))
            for conn, player_id in self._connections_to_players.items()
            if conn != except_conn and player_id[1] == game_id
        ]
        if futures:
            await asyncio.wait(futures)

    async def send(self, conn: WebSocketServerProtocol, msg: WebsocketMessage) -> None:
        await conn.send(self.to_ws_msg(msg))

    async def send_player(self, player_id: PlayerConnectionID, msg: WebsocketMessage) -> None:
        conn = self._players_to_connections[player_id]
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
            print(f'Error raised {repr(e)}')

    async def serve(self, websocket: WebSocketServerProtocol, path: str) -> None:
        ok, player_conn = await self.register(websocket, path)
        if ok:
            try:
                task = asyncio.Task(self._recv(websocket))
                self._tasks_by_player[player_conn.player_id] = task
                await task
            finally:
                await self.unregister(websocket, path)

    async def stop(self) -> None:
        for player_id in list(self._players_to_connections):
            self.disconnect(player_id)

        futures = [client.wait_closed() for client in self._connections_to_players]
        if futures:
            await asyncio.wait(futures, return_when=asyncio.ALL_COMPLETED)
