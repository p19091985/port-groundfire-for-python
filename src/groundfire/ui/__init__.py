from __future__ import annotations

from importlib import import_module

__all__ = [
    "CanonicalLocalMenu",
    "ClientMenuRenderer",
    "GameGraphics",
    "GameUI",
    "LocalMenuSelection",
    "LocalPlayerConfig",
    "TextStyle",
]


def __getattr__(name: str):
    if name == "GameGraphics":
        return getattr(import_module("src.groundfire.ui.graphics"), name)
    if name in {"GameUI", "TextStyle"}:
        return getattr(import_module("src.groundfire.ui.text"), name)
    if name in {"CanonicalLocalMenu", "ClientMenuRenderer", "LocalMenuSelection", "LocalPlayerConfig"}:
        return getattr(import_module("src.groundfire.ui.menus"), name)
    raise AttributeError(name)
