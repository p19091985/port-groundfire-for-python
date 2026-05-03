from __future__ import annotations

import argparse
from pathlib import Path

from .app.server import ServerApp
from .network.messages import DEFAULT_DISCOVERY_PORT, DEFAULT_GAME_PORT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NETWORK_DIR = PROJECT_ROOT / "conf" / "network"
DEFAULT_SERVER_PRIVATE_KEY_PATH = DEFAULT_NETWORK_DIR / "server_root_private.pem"
DEFAULT_SERVER_PUBLIC_KEY_PATH = DEFAULT_NETWORK_DIR / "server_root_public.pem"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Groundfire authoritative headless server.")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=DEFAULT_GAME_PORT, help="Gameplay UDP port.")
    parser.add_argument("--discovery-port", type=int, default=DEFAULT_DISCOVERY_PORT, help="LAN discovery UDP port.")
    parser.add_argument("--ticks", type=int, default=0, help="If set, run only this many simulation ticks.")
    parser.add_argument("--server-name", default="Groundfire Server", help="Name announced to clients.")
    parser.add_argument("--password", default="", help="Require this password before accepting players.")
    parser.add_argument("--region", default="world", help="Region announced to browsers and master servers.")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    server = ServerApp(
        host=args.host,
        port=args.port,
        discovery_port=args.discovery_port,
        server_name=args.server_name,
        password=args.password,
        region=args.region,
        secure=not args.insecure,
        master_servers=tuple(args.master_server),
        network_backend="udp",
        secure_private_key_path=args.server_private_key,
        secure_public_key_path=args.server_public_key,
    )
    try:
        return server.run(max_ticks=args.ticks or None)
    finally:
        server.close()


if __name__ == "__main__":
    raise SystemExit(main())
