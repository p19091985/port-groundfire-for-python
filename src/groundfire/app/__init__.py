from __future__ import annotations

from importlib import import_module

__all__ = [
    "CanonicalClientShell",
    "ClientApp",
    "ConnectedFrontFrame",
    "ConnectedFrontRuntime",
    "LocalFrontRuntime",
    "LocalCommandSampler",
    "ServerApp",
]


def __getattr__(name: str):
    if name == "ClientApp":
        return getattr(import_module("src.groundfire.app.client"), name)
    if name in {"ConnectedFrontFrame", "ConnectedFrontRuntime", "LocalCommandSampler"}:
        return getattr(import_module("src.groundfire.app.front"), name)
    if name == "LocalFrontRuntime":
        return getattr(import_module("src.groundfire.app.local"), name)
    if name == "CanonicalClientShell":
        return getattr(import_module("src.groundfire.app.shell"), name)
    if name == "ServerApp":
        return getattr(import_module("src.groundfire.app.server"), name)
    raise AttributeError(name)
