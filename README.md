```
     _______.  ______ .______           ___      .______   .______    __       _______
    /       | /      ||   _  \         /   \     |   _  \  |   _  \  |  |     |   ____|
   |   (----`|  ,----'|  |_)  |       /  ^  \    |  |_)  | |  |_)  | |  |     |  |__
    \   \    |  |     |      /       /  /_\  \   |   _  <  |   _  <  |  |     |   __|
.----)   |   |  `----.|  |\  \----. /  _____  \  |  |_)  | |  |_)  | |  `----.|  |____
|_______/     \______|| _| `._____|/__/     \__\ |______/  |______/  |_______||_______|
```

This is a custom implementation of a popular game [Scrabble](https://en.wikipedia.org/wiki/Scrabble). 

![User field preview](./static/field.png)

## Technical 

This project utilizes Python [asyncio](https://docs.python.org/3/library/asyncio.html) library.
Clients talk to each other via websockets through the server, thus the system is centralized.
Currently, the clients can send messages only to the server directly, which can publish their messages to other clients or answer back.
The server tracks clients' connection state and verifies players' moves (right now it autoapproves them, there is no verification of inserted words).
Clients and the server exchange information via messages, which are split into game events and non-game messages.
Game events define all changes of the game state, non-game messages include messages of player connection/disconnection, authorization.

In order to play the game, there should be the following roles set up:
- The server. It will be the publisher of messages and admin panel (it will create new games, start the games with some parameters).
- The players. Each player has a GUI to interact with and a client connected to it and the server.

Player's GUI object and the client run in a single process, but in different threads. The server requires its own process.

While the server is running, every client can authorize to play a particular game (specified by `game_id`).
Before `GameInitEvent` is emitted, all players connected to the game (anytime before) will be playing it.
In case any player gets disconnected during the game, it can still reconnect back.

Each game is recorded (flushed to the file at `/tmp/scrabble`) with its own ID.
In case anything happens and the server fails, it can then reload the saved the game and continue.

### Prerequisites

- Unix OS (tested on MacOS)
- at least [Python3.7](https://www.python.org/downloads/)

### Installation

1. Install [poetry](https://python-poetry.org/docs/#installation).
1. Install project dependencies `poetry install`.

[Start](#client-server) the game.

## Rules

In this game 2+ players score points by placing tiles with letters onto a game board (usually divided into a 15x15 grid of squares, but in this game it can be anything, which can fit the screen - with current default 20x20).
The tiles must form words that, in crossword fashion, are to read left to right in rows or downward in columns, and be included in a standard dictionary or lexicon.

### Points

Each letter is worth **1** point.
The number of points awarded for the word is the sum of its letters' points, i.e. its length.
Thus, the word _word_ adds **4** points to the player, who inserted it.

Additionally, the board is marked with _bonus_ squares, which multiply the number of points awarded.
They are highlighted on the board and each of them specifies the multiplier.
_Bonus_ squares multiply the number of points of the word, which was first placed onto it.
So, if the player _PlayerA_ first inserted a word _word_ with letter _r_ to appear on a _bonus_ square with multiplier **3**, then he is awarded with **12** points.
If after that player _PlayerB_ inserts another word _scrabble_ with _r_ at the same _bonus_ square, then he is awarded only with **7** points.

In case a single word intersects multiple bonuses, their values are summed together and result in the final bonus.
Thus, a single word _sun_ having letter _s_ at bonus **2** and _n_ at bonus **4** would result in **18** points.

Additional bonus of **5** points is scored when a player places all his letters onto the board in a single move.

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

As of now two languages are supported: `en` and `ru`.
Each language defines:
- alphabet
- letter distribution
- control keys

In the next sections control keys will be specified in the form of "**\<english letter\>**(**\<russion letter\>**)".

### Modes

GUI of the game represents a terminal window with key shortcuts to do the moves.
When playing, the player is in one of the following modes:
* _VIEW_ mode. This mode is the default mode, meaning that quiting the other ones will bring you back to the _VIEW_ mode.
In this mode the player can do the following:
    - move the cursor using [navigation keys](#navigation-keys);
    - go to the _CONFIRMATION_ mode by pressing **s**(**с**) to confirm/save the move (if it's his turn right now);
    - insert the words to the board by pressing **i**(**в**) and selecting the direction of insertion:
        * **j** or **KEY_DOWN** for down or,
        * **l** or **KEY_RIGHT** for right.
    - go to the _INSERT_ mode (if it's his turn right now);
    - mark some of his letters for exchange (proceeding to the _DELETE_PLAYER_LETTERS_ mode) by pressing **d**(**у**) (available only when it's his turn right now);
    - cancel all existing progress (already inserted workds and marked letters for exchange) by typing **c**(**о**).
* _INSERT_ mode. It is turned on by pressing **i**(**в**) and selecting the direction of insertion from the _VIEW_ mode.
In this mode the player can type the letters to be inserted to the current cursor's cell.
Only letters from the player's set or existing letters on the board are allowed.
After finishing inserting the words, [quit the mode](#quit-the-mode).
In order to clear recently inserted letters, press **BACKSPACE**.
* _DELETE_PLAYER_LETTERS_ mode. It is started by pressing **d**(**у**) from the _VIEW_ mode.
The player can select the letters from his set to be exchanged by typing the corresponding letters.
* _APPEND_PLAYER_LETTERS_ mode. It is triggered by pressing **a**(**м**) from the _VIEW_ mode.
The player can select the letters from his set already marked to be exchanged and cancel it.
So, if the player first marked letters "a", "b" and "c" for exchange, but then from this mode typed "a" and "b", then only letter "c" will be exchanged.
* _CONFIRMATION_ mode. To start this mode, press **s**(**с**) from the _VIEW_ mode.
This will suggest a choice of "yes" (**y**(**д**)) and "no" (**n**(**н**)) to apply the changes or not.

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

The game should be hosted on a server, which should be available for connection by other players.

### Local server

For the local server the game can use an existing CLI:

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

So a regular game with two players would look like this:

The server:

    $ poetry run python run_cmd.py host 100.10.20.30 5678 --load 100

And follow the server help:
```
new - Initialize new game
start <game_id> <initial_word> [lang=en] - Start specified game with initial word (without spaces) and use language <lang> (available "ru" and "en")
load <game_id> - Load and start specified game
disconnect <game_id> <player> - Disconnect specified player
```

Player1:

    $ poetry run python run_cmd.py player user1 100 100.10.20.30 5678

Player2:

    $ poetry run python run_cmd.py player user1 100 100.10.20.30 5678

### Web-server

Another option is to deploy a separate web-server, which will be hosting all games.
Such server will be running using [Flask](https://flask.palletsprojects.com/en/1.1.x/) and accept unauthorized requests "as admin".
Such requests control the game flow (game creation, start).

To start the application on a web-server, run the following:

    $ env FLASK_APP=app.py poetry run python -m flask run

Admin endpoints:
- `/new` - create a new game. Response will contain a single integer with a created game id.
- `/start/<game_id>/<init_word>` - start a particular game with initial word `<init_word>`.
- `/load/<game_id>` - load and continue a particular game.

### ngrok

If you'd like to play a game with your friends away from your local network and you don't have a web-server configured, you may use [ngrok](https://ngrok.com/) tool.
**ngrok** acts as a proxy-server for your host with public URL.
**ngrok**'s free plan limits are enough for the game.
All you need to do is to [install](https://dashboard.ngrok.com/get-started/setup) the client, and then [execute](https://ngrok.com/docs#tcp) it with specifying the port you run the host on: 
    
    ./ngrok tcp <port>

This will start a console window with the traffic state.
From that information you need to select the public URL your process is proxied to - it is written in the section _Forwarding_ (it looks like _tcp://6.tcp.ngrok.io:12321_).
Copy that URL and send it to your friends.
Now when connecting to your host, they need to specify it:

    $ poetry run python run_cmd.py player user1 100 tcp://6.tcp.ngrok.io 12321

#### Docker way

To run the app in docker, do the following:

Run the server (mounting will allow to get access to the logs and game events on the host machine):

    $ docker build -t scrabble:latest .
    $ docker run --rm -it -p 5678:5678 --mount type=bind,source="$(pwd)"/__logs__,target=/tmp/scrabble/ scrabble:latest python run_cmd.py host --port 5678 --host 0.0.0.0

Run the client (mounting will allow to collect client logs for debugging):

    $ docker build -t scrabble:latest .
    $ docker run --rm -it --network host --mount type=bind,source="$(pwd)"/__logs__,target=/tmp/scrabble/ scrabble:latest python run_cmd.py player <username> <game_id> <server_host> <server_port>

## Debug

The game writes down its logs into a logfile (at `/tmp/scrabble/logs.txt`) - it includes user GUI actions (keys pressed).
Additionally, it is easy to "replay" the whole game having its "game" file (stored at `/tmp/scrabble/{game_id}_events.json`).
This is achieved by `replay` mode:

    $ poetry run python run_cmd.py replay -h
    usage: scrabble replay [-h] [--sequence SEQUENCE] [--player PLAYER]
                           game_id events_file

    positional arguments:
      game_id              Game ID
      events_file          File with game events

    optional arguments:
      -h, --help           show this help message and exit
      --sequence SEQUENCE  Event sequence to stop at
      --player PLAYER      Player of the game

Starting the game in this mode will apply all or some events from the file.
Specifying a particular `player` will unlock the ability to interact with the board as if being that player in the game.
