import asyncio
import json
from typing import Callable, Optional, cast

import websockets

from scrabble.serializers.transport.msg import WebsocketMessageSchema
from scrabble.transport.msg import AuthMessageRequest, AuthMessageRequestPayload, AuthMessageResponse, WebsocketMessage


class Client:

    def __init__(self, username: str, *,
                 on_new_msg: Optional[Callable[[WebsocketMessage], None]] = None,
                 on_connected: Optional[Callable[[], None]] = None,
                 on_disconnected: Optional[Callable[[], None]] = None):
        self._username = username
        self._on_new_msg = on_new_msg
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected

    def to_ws_msg(self, msg: WebsocketMessage) -> str:
        return json.dumps(WebsocketMessageSchema().dump(msg))

    def from_ws_msg(self, raw_msg: str) -> WebsocketMessage:
        return WebsocketMessageSchema().load(json.loads(raw_msg))

    async def send(self, msg: WebsocketMessage) -> None:
        await self._server.send(self.to_ws_msg(msg))

    async def _consume(self) -> None:
        try:
            while True:
                async for raw_msg in self._server:
                    msg = self.from_ws_msg(cast(str, raw_msg))
                    print('Recv', msg)
                    if self._on_new_msg is not None:
                        self._on_new_msg(msg)
        except websockets.exceptions.ConnectionClosedError:
            print('Server closed')

    async def start(self, addr) -> None:
        host, port = addr

        while True:
            try:
                async with websockets.connect(f'ws://{host}:{port}') as ws:
                    if self._on_connected is not None:
                        self._on_connected()
                    self._server = ws

                    await self.send(AuthMessageRequest(AuthMessageRequestPayload(username=self._username)))
                    raw_response = await ws.recv()
                    response_msg = self.from_ws_msg(cast(str, raw_response))
                    if isinstance(response_msg, AuthMessageResponse) and response_msg.payload.ok:
                        print('Authorized')
                        await self._consume()
                    else:
                        print("Couldn't authorize")
                        break

                    print('Disconnected')
            except Exception as e:
                print(f'Exception raised {e}')
                await asyncio.sleep(2)
            finally:
                if self._on_disconnected is not None:
                    self._on_disconnected()

    async def stop(self) -> None:
        await self._server.close()
        await self._server.wait_closed()
