import argparse
from threading import Thread

from scrabble.engine import ClientEngine, ServerEngine


def init_parser():
    parser = argparse.ArgumentParser(description='Scrabble game', prog='scrabble')
    subparsers = parser.add_subparsers(required=True)

    server = subparsers.add_parser('host', help='Server part')
    server.add_argument('--port', type=str, help='Server port', default='5678')
    server.add_argument('--host', type=str, help='Server host', default=None)
    server.add_argument('--load', type=str, help='Load specific game by its ID', dest='game_id')
    server.set_defaults(app='host')

    client = subparsers.add_parser('player', help='Player part')
    client.add_argument('username', type=str, help='Player username')
    client.add_argument('host', type=str, help='Host address or IP to connect')
    client.add_argument('port', type=int, help='Host port to connect')
    client.add_argument('--debug', action='store_true', help='Show debug messages while playing')
    client.set_defaults(app='player')

    return parser


if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()

    if args.app == 'host':
        server_engine = ServerEngine(game_id=args.game_id)
        server_engine.run(host=args.host, port=args.port)
    elif args.app == 'player':
        client_engine = ClientEngine(args.username, debug=args.debug)

        t = Thread(target=client_engine.run, args=(args.host, args.port))
        t.start()
        t.join()
