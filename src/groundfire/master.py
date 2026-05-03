from __future__ import annotations

import argparse

from groundfire_net.master import DEFAULT_MASTER_PORT, MasterServerApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Groundfire native master server.")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=DEFAULT_MASTER_PORT, help="Master server UDP port.")
    parser.add_argument("--ticks", type=int, default=0, help="If set, poll only this many iterations.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    master = MasterServerApp(host=args.host, port=args.port)
    try:
        master.open()
        ticks = args.ticks or None
        count = 0
        while ticks is None or count < ticks:
            master.poll(timeout=0.05)
            count += 1
        return 0
    finally:
        master.close()


if __name__ == "__main__":
    raise SystemExit(main())
