import argparse
from threading import Thread

from scrabble.engine import ClientEngine, ServerEngine


def init_parser():
    parser = argparse.ArgumentParser(description='Scrabble game', prog='scrabble')
    subparsers = parser.add_subparsers(required=True)

    server = subparsers.add_parser('host', help='Server part')
    server.add_argument('--port', type=str, help='Server port', default='5678')
    server.add_argument('--host', type=str, help='Server host', default=None)
    server.set_defaults(app='host')

    client = subparsers.add_parser('player', help='Player part')
    client.add_argument('username', type=str, help='Player username')
    client.add_argument('game_id', type=int, help='Game ID')
    client.add_argument('host', type=str, help='Host address or IP to connect')
    client.add_argument('port', type=int, help='Host port to connect')
    client.add_argument('--debug', action='store_true', help='Show debug messages while playing')
    client.set_defaults(app='player')

    return parser


if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()

    if args.app == 'host':
        server_engine = ServerEngine()
        server_engine.run_with_cmd(host=args.host, port=args.port)
    elif args.app == 'player':
        client_engine = ClientEngine(args.username, args.game_id, debug=args.debug)

        t = Thread(target=client_engine.run, args=(args.host, args.port))
        t.start()
        t.join()
