import pytest

from scrabble.game import Player
from scrabble.serializers.player import PlayerSchema


@pytest.mark.parametrize("username,score,letters", [("qu", 0, []), ("user1", 40, ['a', 'b', 'c'])])
def test_player_serializer(username, score, letters, gen_player, gen_dumped_player):
    player = gen_player(username, score, letters)
    dumped = PlayerSchema().dump(player)
    assert dumped == gen_dumped_player(username, score, letters)
    assert PlayerSchema().load(dumped) == player


def test_player_score(gen_player):
    player = gen_player("username", 0, [])
    assert player.score == 0

    player.add_score(100)
    assert player.score == 100

    with pytest.raises(ValueError):
        player.add_score(-101)


def test_player_letters(gen_player):
    player = gen_player("username", 0, [])
    assert player.letters == []

    letters = ['a', 'b', 'c', 'd', 'c', 'b', 'a']
    player.fulfil_letters(letters)
    assert player.letters == letters

    with pytest.raises(ValueError):
        player.fulfil_letters(letters)
    assert player.letters == letters

    player.play_letters(['a', 'b'])
    letters.remove('a')
    letters.remove('b')
    assert player.letters == letters

    with pytest.raises(ValueError):
        player.fulfil_letters(['b', 'dd'])
    assert player.letters == letters

    with pytest.raises(ValueError):
        player.play_letters(['a', 'a', 'a'])
    assert player.letters == letters

    player.fulfil_letters(['y', 'd'])
    assert player.letters == letters + ['y', 'd']
