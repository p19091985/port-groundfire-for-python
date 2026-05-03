from __future__ import annotations

import argparse
from pathlib import Path

from .app.client import ClientApp
from .core.settings import ReadIniFile
from .network.messages import DEFAULT_GAME_PORT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "conf" / "options.ini"
DEFAULT_NETWORK_DIR = PROJECT_ROOT / "conf" / "network"
DEFAULT_SERVER_PUBLIC_KEY_PATH = DEFAULT_NETWORK_DIR / "server_root_public.pem"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Groundfire client entrypoint.")
    parser.add_argument("--connect", default="", help="Connect to a server in host[:port] form.")
    parser.add_argument(
        "--server-public-key",
        default=str(DEFAULT_SERVER_PUBLIC_KEY_PATH),
        help="Deprecated compatibility option; native UDP online mode does not use external key files.",
    )
    parser.add_argument("--player-name", default="Player", help="Displayed player name.")
    parser.add_argument("--password", default="", help="Password used when connecting to a protected server.")
    parser.add_argument("--ai-players", type=int, default=1, help="Number of local AI opponents in local mode.")
    local_mode_group = parser.add_mutually_exclusive_group()
    local_mode_group.add_argument(
        "--canonical-local",
        action="store_true",
        help="Developer override to launch the modern local runtime through the classic local menu flow.",
    )
    local_mode_group.add_argument(
        "--classic-local",
        action="store_true",
        help="Force the classic local game flow for this launch.",
    )
    parser.add_argument("--once", action="store_true", help="Run a single local frame or single connect attempt.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = ClientApp(
        network_backend="udp",
        secure_server_public_key_path=args.server_public_key,
    )

    if args.connect:
        host, port = _parse_connect_target(args.connect)
        client.connect(host, port, player_name=args.player_name, password=args.password)
        try:
            return client.run_connected(max_frames=1 if args.once else None)
        finally:
            client.close()

    try:
        local_mode = _resolve_local_mode(args)
        if local_mode == "classic":
            return client.run_legacy_local(max_frames=1 if args.once else None)
        return client.run_local(
            max_frames=1 if args.once else None,
            player_name=args.player_name,
            ai_players=args.ai_players,
            show_menu=not args.once,
        )
    finally:
        client.close()


def _parse_connect_target(target: str) -> tuple[str, int]:
    if ":" not in target:
        return target, DEFAULT_GAME_PORT
    host, raw_port = target.rsplit(":", 1)
    return host, int(raw_port)


def _resolve_local_mode(args) -> str:
    if args.classic_local:
        return "classic"
    if args.canonical_local:
        return "canonical"
    settings = ReadIniFile(str(DEFAULT_SETTINGS_PATH))
    value = settings.get_string("Interface", "LocalMenuMode", "canonical").strip().lower()
    return "classic" if value == "classic" else "canonical"


if __name__ == "__main__":
    raise SystemExit(main())
