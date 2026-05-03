from __future__ import annotations

import selectors
import socket
from dataclasses import dataclass


@dataclass(frozen=True)
class Datagram:
    payload: bytes
    address: tuple[str, int]


class DatagramEndpoint:
    """Non-blocking UDP endpoint built only on socket/selectors."""

    def __init__(
        self,
        *,
        host: str = "",
        port: int = 0,
        broadcast: bool = False,
        reuse_address: bool = False,
    ):
        self._selector = selectors.DefaultSelector()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if reuse_address:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if broadcast:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._socket.bind((host, port))
        self._socket.setblocking(False)
        self._selector.register(self._socket, selectors.EVENT_READ)
        self._closed = False

    @property
    def socket(self) -> socket.socket:
        return self._socket

    def get_bound_port(self) -> int:
        return int(self._socket.getsockname()[1])

    def sendto(self, payload: bytes, address: tuple[str, int]):
        self._socket.sendto(payload, address)

    def poll(self, *, timeout: float = 0.0, max_packet_size: int = 65535) -> tuple[Datagram, ...]:
        datagrams: list[Datagram] = []
        for key, _mask in self._selector.select(timeout):
            sock = key.fileobj
            try:
                while True:
                    payload, address = sock.recvfrom(max_packet_size)  # type: ignore[union-attr]
                    datagrams.append(Datagram(payload=payload, address=address))
            except BlockingIOError:
                continue
        return tuple(datagrams)

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self._selector.unregister(self._socket)
        except Exception:
            pass
        self._socket.close()
        self._selector.close()
