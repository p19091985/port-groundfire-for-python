"""Reusable native-Python networking helpers for small games.

This package intentionally depends only on the Python standard library so it can
be copied into another project and wired to that game's own message classes.
"""

from .browser import ServerBook, ServerListEntry
from .codec import JsonDataclassCodec, decode_envelope, encode_envelope, to_plain
from .discovery import DiscoveredServer, DiscoveryService, ServerBrowser
from .master import (
    DEFAULT_MASTER_PORT,
    MasterQuery,
    MasterServerAddress,
    MasterServerApp,
    MasterServerClient,
    MasterServerDirectory,
    parse_master_server_address,
)
from .server import NativeServerLoop, ServerLoopConfig
from .transport import Datagram, DatagramEndpoint

__all__ = [
    "DEFAULT_MASTER_PORT",
    "Datagram",
    "DatagramEndpoint",
    "DiscoveredServer",
    "DiscoveryService",
    "JsonDataclassCodec",
    "MasterQuery",
    "MasterServerAddress",
    "MasterServerApp",
    "MasterServerClient",
    "MasterServerDirectory",
    "NativeServerLoop",
    "ServerBook",
    "ServerBrowser",
    "ServerListEntry",
    "ServerLoopConfig",
    "decode_envelope",
    "encode_envelope",
    "parse_master_server_address",
    "to_plain",
]
