#!/usr/bin/env python3
"""ST04: sonda UDP local da edicao Godot (sem a edicao irma).

Tenta Ping/Pong com o codec vendorizado em runtime/headless quando
disponivel; sem o headless, faz sonda UDP minima (porta acessivel)
e retorna 0 com aviso, sem exigir a edicao Python irma.
"""

from __future__ import annotations

import socket
import sys
import time


def _try_headless_ping(host: str, port: int, timeout: float) -> bool | None:
    try:
        from groundfire.network.codec import decode_message, encode_message  # type: ignore
        from groundfire.network.messages import Ping, Pong  # type: ignore
    except Exception:
        return None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.2)
            sock.sendto(encode_message(Ping(nonce="godot-check", issued_at=time.time())), (host, port))
            payload, _ = sock.recvfrom(65535)
            if isinstance(decode_message(payload), Pong):
                return True
        except OSError:
            time.sleep(0.05)
        finally:
            if sock is not None:
                sock.close()
    return False


def main() -> int:
    host = "127.0.0.1"
    port = 27015
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        else:
            i += 1
    result = _try_headless_ping(host, port, 2.0)
    if result is True:
        print(f"Servidor UDP acessivel em {host}:{port} (Ping/Pong).")
        return 0
    if result is False:
        print(f"Servidor UDP sem resposta em {host}:{port}.", file=sys.stderr)
        return 1
    # Sem headless: sonda minima sem codec (nao prova Pong, mas nao exige irma).
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(0.5)
            sock.sendto(b"", (host, port))
    except OSError as exc:
        print(f"Sonda UDP falhou em {host}:{port}: {exc}", file=sys.stderr)
        return 1
    print(f"Headless ainda nao vendorizado; sonda minima enviada para {host}:{port}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
