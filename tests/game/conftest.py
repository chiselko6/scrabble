from pytest import fixture

from scrabble.game import Player


@fixture
def gen_player():
    def gen(username, score, letters):
        return Player(username=username, score=score, letters=letters)

    return gen


@fixture
def gen_dumped_player():
    def gen(username, score, letters):
        return {"username": username, "score": score, "letters": letters}

    return gen
