from __future__ import annotations

import argparse
from pathlib import Path

from .app.server import ServerApp
from .network.messages import DEFAULT_DISCOVERY_PORT, DEFAULT_GAME_PORT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NETWORK_DIR = PROJECT_ROOT / "conf" / "network"
DEFAULT_SERVER_PRIVATE_KEY_PATH = DEFAULT_NETWORK_DIR / "server_root_private.pem"
DEFAULT_SERVER_PUBLIC_KEY_PATH = DEFAULT_NETWORK_DIR / "server_root_public.pem"
MAP_PRESETS = {
    "classic": 1,
    "basin": 7,
    "ridge": 11,
    "crater": 17,
    "mesa": 23,
}


def parse_map_seed(value: str) -> int:
    raw = value.strip().lower().replace("_", "-")
    if raw.startswith("seed "):
        raw = raw[5:].strip()
    if raw in MAP_PRESETS:
        return MAP_PRESETS[raw]
    try:
        seed = int(raw)
    except ValueError as exc:
        names = ", ".join(sorted(MAP_PRESETS))
        raise argparse.ArgumentTypeError(f"map must be a positive seed or one of: {names}") from exc
    if seed <= 0:
        raise argparse.ArgumentTypeError("map seed must be greater than zero")
    return seed


def parse_player_count(value: str) -> int:
    try:
        count = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("max players must be an integer") from exc
    if not 1 <= count <= 32:
        raise argparse.ArgumentTypeError("max players must be between 1 and 32")
    return count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Groundfire authoritative headless server.")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=DEFAULT_GAME_PORT, help="Gameplay UDP port.")
    parser.add_argument("--discovery-port", type=int, default=DEFAULT_DISCOVERY_PORT, help="LAN discovery UDP port.")
    parser.add_argument("--ticks", type=int, default=0, help="If set, run only this many simulation ticks.")
    parser.add_argument("--rounds", "--num-rounds", dest="rounds", type=int, default=10, help="Number of match rounds.")
    parser.add_argument(
        "--map",
        "--map-seed",
        dest="map_seed",
        type=parse_map_seed,
        default=1,
        help="Terrain preset/seed announced as the server map.",
    )
    parser.add_argument("--max-players", type=parse_player_count, default=8, help="Maximum player slots.")
    parser.add_argument("--server-name", default="Groundfire Server", help="Name announced to clients.")
    parser.add_argument("--password", default="", help="Require this password before accepting players.")
    parser.add_argument("--rcon-password", default="", help="Remote admin password reserved for dedicated-server tools.")
    parser.add_argument("--region", default="world", help="Region announced to browsers and master servers.")
    parser.add_argument("--no-discovery", action="store_true", help="Disable LAN discovery announcements.")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Advertise this server as insecure in browser filters.",
    )
    parser.add_argument(
        "--master-server",
        action="append",
        default=[],
        help="Register with a Groundfire master server in host[:port] form. Can be used multiple times.",
    )
    parser.add_argument(
        "--server-private-key",
        default=str(DEFAULT_SERVER_PRIVATE_KEY_PATH),
        help="Deprecated compatibility option; native UDP server mode does not use key files.",
    )
    parser.add_argument(
        "--server-public-key",
        default=str(DEFAULT_SERVER_PUBLIC_KEY_PATH),
        help="Deprecated compatibility option; native UDP server mode does not use key files.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Accepted for compatibility; server is always headless.",
    )
    parser.add_argument(
        "--log-events",
        action="store_true",
        help="Print server, lobby, RCON and match events to stdout for launcher logs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    server = ServerApp(
        host=args.host,
        port=args.port,
        discovery_port=args.discovery_port,
        server_name=args.server_name,
        map_seed=args.map_seed,
        num_rounds=args.rounds,
        max_players=args.max_players,
        password=args.password,
        rcon_password=args.rcon_password,
        region=args.region,
        secure=not args.insecure,
        master_servers=tuple(args.master_server),
        enable_discovery=not args.no_discovery,
        network_backend="udp",
        secure_private_key_path=args.server_private_key,
        secure_public_key_path=args.server_public_key,
        event_logger=_print_server_event if args.log_events else None,
    )
    try:
        return server.run(max_ticks=args.ticks or None)
    finally:
        server.close()


def _print_server_event(message: str):
    print(f"[groundfire-server] {message}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
