import os
from threading import Thread

from flask import Flask, current_app

from scrabble.engine import ServerEngine

app = Flask(__name__)

app.config['PORT'] = os.environ.get('PORT', 5678)


@app.before_first_request
def start_server():
    engine = ServerEngine()

    t = Thread(target=engine.run, args=(None, app.config['PORT']))
    t.start()

    current_app.engine = engine


@app.route('/')
def home():
    return 'Welcome to Scrabble!'


@app.route('/new')
def init_game():
    game_id = current_app.engine.init_new_game()

    return str(game_id)


@app.route('/start/<int:game_id>/<init_word>')
def start_game(game_id: int, init_word: str):
    current_app.engine.start_game(game_id, init_word)

    return 'OK'


@app.route('/load/<int:game_id>')
def load_game(game_id: int):
    current_app.engine.load_game(game_id)

    return 'OK'


@app.route('/healthcheck')
def healthcheck():
    return 'OK'
