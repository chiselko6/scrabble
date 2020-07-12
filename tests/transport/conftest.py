from pytest import fixture

from scrabble.transport.msg import (AuthMessageRequest, AuthMessageRequestPayload, AuthMessageResponse,
                                    AuthMessageResponsePayload, EndConnectionMessage, EndConnectionPayload,
                                    NewConnectionMessage, NewConnectionPayload)


@fixture
def auth_msg_request_obj():
    def gen(username, game_id):
        return AuthMessageRequest(payload=AuthMessageRequestPayload(username=username, game_id=game_id))

    return gen


@fixture
def dumped_auth_msg_request():
    def gen(username, game_id):
        return {"type": "AUTH_REQUEST", "payload": {"username": username, "game_id": game_id}}

    return gen


@fixture
def auth_msg_response_obj():
    def gen(ok):
        return AuthMessageResponse(payload=AuthMessageResponsePayload(ok=ok))

    return gen


@fixture
def dumped_auth_msg_response():
    def gen(ok):
        return {"type": "AUTH_RESPONSE", "payload": {"ok": ok}}

    return gen


@fixture
def new_connection_msg_obj():
    def gen(username):
        return NewConnectionMessage(payload=NewConnectionPayload(username=username))

    return gen


@fixture
def dumped_new_connection_msg():
    def gen(username):
        return {"type": "NEW_CONNECTION", "payload": {"username": username}}

    return gen


@fixture
def end_connection_msg_obj():
    def gen(username):
        return EndConnectionMessage(payload=EndConnectionPayload(username=username))

    return gen


@fixture
def dumped_end_connection_msg():
    def gen(username):
        return {"type": "END_CONNECTION", "payload": {"username": username}}

    return gen
