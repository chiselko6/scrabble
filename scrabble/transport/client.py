import asyncio
import json
from typing import Callable, Optional, Tuple, cast

import websockets

from scrabble.serializers.transport.msg import WebsocketMessageSchema

from .msg import AuthMessageRequest, AuthMessageRequestPayload, AuthMessageResponse, WebsocketMessage

__all__ = [
    'Client',
    'ConnectionCallback',
    'WebsocketMessageCallback',
]

ConnectionCallback = Callable[[], None]
WebsocketMessageCallback = Callable[[WebsocketMessage], None]


class Client:

    def __init__(self, username: str, game_id: int, *,
                 on_new_msg: Optional[WebsocketMessageCallback] = None,
                 on_connected: Optional[ConnectionCallback] = None,
                 on_disconnected: Optional[ConnectionCallback] = None):
        self._username = username
        self._game_id = game_id

        self._on_new_msg = on_new_msg
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected

        self._running = True

    def to_ws_msg(self, msg: WebsocketMessage) -> str:
        return json.dumps(WebsocketMessageSchema().dump(msg))

    def from_ws_msg(self, raw_msg: str) -> WebsocketMessage:
        return WebsocketMessageSchema().load(json.loads(raw_msg))

    async def send(self, msg: WebsocketMessage) -> None:
        await self._server.send(self.to_ws_msg(msg))

    async def _consume(self) -> None:
        try:
            async for raw_msg in self._server:
                msg = self.from_ws_msg(cast(str, raw_msg))
                print('Recv', msg)
                if self._on_new_msg is not None:
                    self._on_new_msg(msg)
        except websockets.exceptions.ConnectionClosedError:
            print('Server closed unexpectedly')
        except websockets.exceptions.ConnectionClosedOK:
            print('Server closed successfully')

    async def start(self, addr: Tuple[str, int]) -> None:
        host, port = addr

        while self._running:
            try:
                async with websockets.connect(f'ws://{host}:{port}') as ws:
                    if self._on_connected is not None:
                        self._on_connected()
                    self._server = ws

                    await self.send(AuthMessageRequest(AuthMessageRequestPayload(username=self._username,
                                                                                 game_id=self._game_id)))
                    raw_response = await ws.recv()
                    response_msg = self.from_ws_msg(cast(str, raw_response))
                    if isinstance(response_msg, AuthMessageResponse) and response_msg.payload.ok:
                        print('Authorized')
                        self._conn_task = asyncio.Task(self._consume())
                        await self._conn_task
                    else:
                        print("Couldn't authorize")
                        break

                    print('Disconnected')
            except asyncio.CancelledError:
                await ws.close()
                break
            except Exception as e:
                print(f'Exception raised {e}')
                await asyncio.sleep(2)
            finally:
                if self._on_disconnected is not None:
                    self._on_disconnected()

    def stop(self) -> None:
        if hasattr(self, '_conn_task'):
            self._conn_task.cancel()
        self._running = False