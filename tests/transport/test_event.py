import pytest

from scrabble.game.api import GameStartEvent, GameStartParams
from scrabble.serializers.transport.msg import WebsocketMessageSchema
from scrabble.transport import EventMessage, EventMessagePayload, EventStatus


@pytest.mark.parametrize("event,status", [
    (GameStartEvent(sequence=1, timestamp=10, params=GameStartParams(player_to_start="user1")), EventStatus.REQUESTED),
])
def test_event_request_serializer(event, status):
    event_msg = EventMessage(payload=EventMessagePayload(event=event), status=status)
    dumped = WebsocketMessageSchema().dump(event_msg)
    assert WebsocketMessageSchema().load(dumped) == event_msg


@pytest.mark.parametrize("username", ["qu", "", "empty"])
def test_auth_request_msg_serializer(username, auth_msg_request_obj, dumped_auth_msg_request):
    dumped = WebsocketMessageSchema().dump(auth_msg_request_obj(username))
    assert dumped == dumped_auth_msg_request(username)
    assert WebsocketMessageSchema().load(dumped) == auth_msg_request_obj(username)


@pytest.mark.parametrize("ok", [True, False])
def test_auth_response_msg_serializer(ok, auth_msg_response_obj, dumped_auth_msg_response):
    dumped = WebsocketMessageSchema().dump(auth_msg_response_obj(ok))
    assert dumped == dumped_auth_msg_response(ok)
    assert WebsocketMessageSchema().load(dumped) == auth_msg_response_obj(ok)
