from __future__ import annotations

from typing import TYPE_CHECKING

from .config import NetworkConfig
from .online_session import HybridNetworkSession
from .session import NetworkSession

if TYPE_CHECKING:
    from src.inifile import ReadIniFile


def build_network_session(settings: "ReadIniFile") -> NetworkSession:
    config = NetworkConfig.from_settings(settings)
    return HybridNetworkSession(config)
