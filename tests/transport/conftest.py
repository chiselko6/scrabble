from pytest import fixture

from scrabble.transport.msg import (AuthMessageRequest, AuthMessageRequestPayload, AuthMessageResponse,
                                    AuthMessageResponsePayload)


@fixture
def auth_msg_request_obj():
    def gen(username):
        return AuthMessageRequest(payload=AuthMessageRequestPayload(username=username))

    return gen


@fixture
def dumped_auth_msg_request():
    def gen(username):
        return {"type": "auth_request", "payload": {"username": username}}

    return gen


@fixture
def auth_msg_response_obj():
    def gen(ok):
        return AuthMessageResponse(payload=AuthMessageResponsePayload(ok=ok))

    return gen


@fixture
def dumped_auth_msg_response():
    def gen(ok):
        return {"type": "auth_response", "payload": {"ok": ok}}

    return gen
