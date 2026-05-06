from __future__ import annotations

import argparse
import signal
from pathlib import Path

from .app.client import ClientApp
from .network.messages import DEFAULT_GAME_PORT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
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
    parser.add_argument(
        "--computer-player",
        action="store_true",
        help="Join a network server as a server-controlled computer player.",
    )
    parser.add_argument(
        "--headless-client",
        action="store_true",
        help="Connect without opening the Pygame client window; useful for automated LAN joins.",
    )
    parser.add_argument(
        "--join-timeout",
        type=float,
        default=5.0,
        help="Seconds to wait for JoinAccept in --headless-client mode.",
    )
    parser.add_argument(
        "--keepalive-seconds",
        type=float,
        default=0.0,
        help="Seconds to keep polling after a headless join succeeds.",
    )
    parser.add_argument(
        "--log-network-events",
        action="store_true",
        help="Print connection, join, rejection and disconnect events to stdout.",
    )
    parser.add_argument("--once", action="store_true", help="Run a single local frame or single connect attempt.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = ClientApp(
        network_backend="udp",
        secure_server_public_key_path=args.server_public_key,
        event_logger=_print_network_event if args.log_network_events else None,
    )
    _install_shutdown_signal_handlers()

    if args.connect:
        host, port = _parse_connect_target(args.connect)
        connect_options = {"player_name": args.player_name, "password": args.password}
        if args.computer_player:
            connect_options["is_computer"] = True
        client.connect(host, port, **connect_options)
        try:
            if args.headless_client:
                keepalive_seconds = 0.0 if args.once else args.keepalive_seconds
                return client.run_headless_connected(
                    join_timeout=args.join_timeout,
                    keepalive_seconds=keepalive_seconds,
                )
            return client.run_connected(max_frames=1 if args.once else None)
        finally:
            client.close()

    try:
        return client.run_legacy_local(max_frames=1 if args.once else None)
    finally:
        client.close()


def _parse_connect_target(target: str) -> tuple[str, int]:
    if ":" not in target:
        return target, DEFAULT_GAME_PORT
    host, raw_port = target.rsplit(":", 1)
    return host, int(raw_port)


def _print_network_event(message: str):
    print(f"[groundfire-client] {message}", flush=True)


def _install_shutdown_signal_handlers():
    def _exit_from_signal(signum, _frame):
        raise SystemExit(128 + int(signum))

    for signal_name in ("SIGINT", "SIGTERM"):
        current_signal = getattr(signal, signal_name, None)
        if current_signal is not None:
            try:
                signal.signal(current_signal, _exit_from_signal)
            except (OSError, RuntimeError, ValueError):
                continue


if __name__ == "__main__":
    raise SystemExit(main())
