from __future__ import annotations

import importlib
from dataclasses import dataclass

__all__ = ["PygameBackend", "load_pygame_module"]


def load_pygame_module(pygame_module=None):
    if pygame_module is not None:
        return pygame_module
    return importlib.import_module("pygame")


@dataclass(frozen=True)
class PygameBackend:
    pygame: object

    @classmethod
    def create(cls, pygame_module=None) -> "PygameBackend":
        return cls(load_pygame_module(pygame_module))

    def get_scale_image(self):
        return getattr(self.pygame.transform, "smoothscale", self.pygame.transform.scale)
