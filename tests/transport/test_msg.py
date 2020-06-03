import pytest

from scrabble.serializers.transport.msg import WebsocketMessageSchema


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


@pytest.mark.parametrize("username", ["qu", "", "empty"])
def test_new_connection_msg_serializer(username, new_connection_msg_obj, dumped_new_connection_msg):
    dumped = WebsocketMessageSchema().dump(new_connection_msg_obj(username))
    assert dumped == dumped_new_connection_msg(username)
    assert WebsocketMessageSchema().load(dumped) == new_connection_msg_obj(username)


@pytest.mark.parametrize("username", ["qu", "", "empty"])
def test_end_connection_msg_serializer(username, end_connection_msg_obj, dumped_end_connection_msg):
    dumped = WebsocketMessageSchema().dump(end_connection_msg_obj(username))
    assert dumped == dumped_end_connection_msg(username)
    assert WebsocketMessageSchema().load(dumped) == end_connection_msg_obj(username)
