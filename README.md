# Scrabble

This is an implementation of a popular game [Scrabble](https://en.wikipedia.org/wiki/Scrabble). 

## Technical 

This project utilizes Python [asyncio](https://docs.python.org/3/library/asyncio.html) library.
Clients talk to each other via websockets through the server.
Currently, the clients can send messages only to the server directly, which can publish its message or answer back.
The server tracks clients' connection state and verifies players' moves (right now it autoapproves them).
Clients and the server exchange information via messages, which are split into game events and other messages.
Game events define all changes of the game state, non-game messages include messages of player connection/disconnection, authorization.

In order to play the game, there should be the following roles set up:
- The server. It will be the publisher of messages and admin panel (it will create new games, start the games with some parameters).
- The players. Each player has a GUI to interact with and a client connected to it and the server.
GUI object will send user actions to the server via its own client and vice versa.

Player's GUI object and the client run in a single process, but in different threads. The server requires its own process.

While the server is running, every client can authorize to play a particular game (specified by `game_id`).
Before `GameInitEvent` is emitted, all connected to the game players will be playing it.
During the game in case some player gets disconnected, it can still reconnect to the game.

Each game is recorded (flushed to the file at `/tmp`) with its own ID.
In case anything happens and the server fails, it can then reload the saved the game and continue.

### Prerequisites

- Unix OS (tested on MacOS)
- at least [Python3.7](https://www.python.org/downloads/)

### Installation

1. Install [poetry](https://python-poetry.org/docs/#installation).
1. Install project dependencies `poetry install`.

[Start](#client-server) the game.

## Rules

In this game 2+ players score points by placing tiles with letters onto a game board (usually divided into a 15x15 grid of squares, but in this game it can be anything, which can fit the screen).
The tiles must form words that, in crossword fashion, read left to right in rows or downward in columns, and be included in a standard dictionary or lexicon.

### Points

Each letter is worth **1** point.
The number of points awarded for the word is the sum of its letters' points, i.e. its length.
Thus, the word _word_ adds **4** points to the player, who inserted it.

Additionally, the board is marked with _bonus_ squares, which multiply the number of points awarded.
They are highlighted on the board and each of them specifies the multiplier.
_Bonus_ squares multiply the number of points of the word, which was first placed onto it.
So, if the player _PlayerA_ first inserted a word _word_ with letter _r_ to appear on a _bonus_ square with multiplier **3**, then he is awarded with **12** points.
If after that player _PlayerB_ inserts another word _scrabble_ with _r_ at the same _bonus_ square, then he is awarded only with **7** points.
In case a single word intersects with multiple bonuses, their values are summed together and result in the final bonus.
Thus, a single word _sun_ having letter _s_ at bonus **2** and _n_ at bonus **4** would result in **18** points.

### Sequence of play

Before the game starts, the players (or admin) should decide on the initial word to be placed at the center of the board.
After that, each player is given a set of **7** letters.
Thereafter, any move is made by using one or more player's tiles to place a word on the board.
This word **must** use one or more tiles already on the board and **must** use at least 1 player letter. 

On each turn, the player has four options:
1. Exchange any number of tiles he has for an equal number from the bag, scoring nothing.
1. Play at least one tile on the board, adding the value of all words formed to the player's cumulative score.
1. Do 1. and 2. 

If the player sets tiles on the board, he will be given back the same number of new letters.
So after each move each player will end up having 7 letters to play.

One of the players starts the game, and then the others do their moves one by one.

### End of the game

The game continues until one of the players firstly reaches some fixed number of points agreed in advance.

## Terminal client

### Modes

GUI of the game represents a terminal window with key shortcuts to do the moves.
When playing, the player is in one of the following modes:
- _VIEW_ mode. This mode is the default mode, meaning that quiting the other ones will bring you back to the _VIEW_ mode.
Here the player can move the cursor using [navigation keys](#navigation-keys),
go to the _CONFIRMATION_ mode by pressing **s** to confirm the move (if it's his turn right now),
insert the words to the board by pressing **i** and selecting the direction of insertion (**j** or **KEY_DOWN** for down and **l** or **KEY_RIGHT** for right) and go to the _INSERT_ mode (if it's his turn right now),
mark some of his letters for exchange (proceeding to the _DELETE_PLAYER_LETTERS_ mode) by pressing **d** (available only when it's his turn right now).
Moreover, the player can type **c**, which will cancel all existing progress (already inserted words and marked letters for exchange).
- _INSERT_ mode. It is turned on by pressing **i** and selecting the direction of insertion from the _VIEW_ mode.
In this mode the player can type the letters to be inserted to the current cursor's cell.
Only letters from the player's set or existing letters on the board are allowed.
After finishing inserting the words, [quit the mode](#quit-the-mode).
In order to clear recently inserted letters, press **BACKSPACE**.
- _DELETE_PLAYER_LETTERS_ mode. It is started by pressing **d** from the _VIEW_ mode.
The player can select the letters from his set to be exchanged (simply by typing the corresponding letters).
- _APPEND_PLAYER_LETTERS_ mode. It is triggered by pressing **a** from the _VIEW_ mode.
The player can select the letters from his set already marked to be exchanged and cancels it.
So, if the player first marked letters "a", "b" and "c" for exchange, but then from this mode typed "a" and "b", then only letter "c" will be exchanged.
- _CONFIRMATION_ mode. To start this mode, press **s** from the _VIEW_ mode.
- This will suggest a choice of "yes" (**y**) and "no" (**n**) to apply the changes or not.

#### Quit the mode

In order to leave the mode, press **ESC**. This will bring you back to the default _VIEW_ mode.

### Navigation keys

To navigate through the board, use the following Vim-like set of keys:
- **h** - move cursor left 1 cell.
- **j** - move cursor down 1 cell.
- **k** - move cursor up 1 cell.
- **l** - move cursor right 1 cell.

However, regular arrow keys are available for these goals as well.

## Client-server

The game should be hosted on a server, which should be available for connection by other players. The game has a simple CLI:

    $ poetry run python run_cmd.py -h
    usage: scrabble [-h] {host,player} ...

    Scrabble game

    positional arguments:
      {host,player}
        host         Server part
        player       Player part

    optional arguments:
      -h, --help     show this help message and exit

`host` part is for the server - it requires host and port to run on.
Additionally, all games are persisted on the filesystem, thus the server can load one of the previous games (by `--load <game_id>`).
`player` subcommand waits `username` (it should be unique in the game), host and port of the server to connect to.
The host waits until all players get connected, and then starts the game by typing `start <initial_word>` - all players will see an update with initialized grid.
Status of connected/disconnected players are drawn in different colors (green and red) of their usernames.

So a simple game with two players would look like this:

The server:

    $ poetry run python run_cmd.py host 100.10.20.30 5678 --load 100

Player1:

    $ poetry run python run_cmd.py player user1 100 100.10.20.30 5678

Player2:

    $ poetry run python run_cmd.py player user1 100 100.10.20.30 5678
