import argparse
from threading import Thread

from scrabble.engine import ClientEngine, ReplayEngine, ServerEngine


def init_parser():
    parser = argparse.ArgumentParser(description='Scrabble game', prog='scrabble')
    subparsers = parser.add_subparsers(required=True)

    server = subparsers.add_parser('host', help='Server part')
    server.add_argument('--port', type=str, help='Server port', default='5678')
    server.add_argument('--host', type=str, help='Server host', default=None)
    server.set_defaults(mode='host')

    client = subparsers.add_parser('player', help='Player part')
    client.add_argument('username', type=str, help='Player username')
    client.add_argument('game_id', type=int, help='Game ID')
    client.add_argument('host', type=str, help='Host address or IP to connect')
    client.add_argument('port', type=int, help='Host port to connect')
    client.add_argument('--debug', action='store_true', help='Show debug messages while playing')
    client.set_defaults(mode='player')

    tester = subparsers.add_parser('replay', help='Replay game events')
    tester.add_argument('game_id', type=int, help='Game ID')
    tester.add_argument('events_file', type=str, help='File with game events')
    tester.add_argument('--sequence', type=int, help='Event sequence to stop at')
    tester.add_argument('--player', type=str, default='__tester__', help='Player of the game')
    tester.set_defaults(mode='replay')

    return parser


if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()

    if args.mode == 'host':
        server_engine = ServerEngine()
        server_engine.run_with_cmd(host=args.host, port=args.port)
    elif args.mode == 'player':
        client_engine = ClientEngine(args.username, args.game_id, debug=args.debug)

        t = Thread(target=client_engine.run, args=(args.host, args.port))
        t.start()
        t.join()

    elif args.mode == 'replay':
        replay_engine = ReplayEngine(args.game_id, args.events_file, args.player,
                                     sequence=args.sequence)

        t = Thread(target=replay_engine.run)
        t.start()
        t.join()
