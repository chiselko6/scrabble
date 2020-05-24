import json

import websockets

from scrabble.serializers.transport.msg import WebsocketMessageSchema
from scrabble.transport.msg import AuthMessageRequest, AuthMessageRequestPayload, AuthMessageResponse, WebsocketMessage


class Client:

    def __init__(self, username: str):
        self._server = None
        self._username = username

    def to_ws_msg(self, msg: WebsocketMessage) -> str:
        return json.dumps(WebsocketMessageSchema().dump(msg))

    def from_ws_msg(self, raw_msg: str) -> WebsocketMessage:
        return WebsocketMessageSchema().load(json.loads(raw_msg))

    async def send(self, msg: WebsocketMessage) -> None:
        await self._server.send(self.to_ws_msg(msg))

    async def _consume(self) -> None:
        while True:
            async for raw_msg in self._server:
                msg = self.from_ws_msg(raw_msg)
                print('Recv', msg)

    async def start(self, addr) -> None:
        host, port = addr

        while True:
            async with websockets.connect(f'ws://{host}:{port}') as ws:
                print('Connected')
                self._server = ws

                await self.send(AuthMessageRequest(AuthMessageRequestPayload(username=self._username)))
                raw_response = await ws.recv()
                response_msg = self.from_ws_msg(raw_response)
                if isinstance(response_msg, AuthMessageResponse) and response_msg.payload.ok:
                    print('Authorized')
                    await self._consume()
                else:
                    print("Couldn't authorize")
                    break

            print('Disconnected')

    async def stop(self) -> None:
        await self._server.wait_closed()
