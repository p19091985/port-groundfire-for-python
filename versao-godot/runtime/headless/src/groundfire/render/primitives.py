from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PolygonPrimitive:
    points: tuple[tuple[float, float], ...]
    colour: tuple[int | float, ...]


@dataclass(frozen=True)
class RectPrimitive:
    left: float
    top: float
    right: float
    bottom: float
    colour: tuple[int | float, ...]


@dataclass(frozen=True)
class LinePrimitive:
    start: tuple[float, float]
    end: tuple[float, float]
    colour: tuple[int | float, ...]
    width: int | None = None


@dataclass(frozen=True)
class TextureRectPrimitive:
    texture_id: int
    left: float
    top: float
    right: float
    bottom: float
    alpha: int | None = None
    tint: tuple[int | float, ...] | None = None
    src_rect: tuple[int, int, int, int] | None = None


@dataclass(frozen=True)
class TextureCenteredPrimitive:
    texture_id: int
    x: float
    y: float
    width: float
    height: float | None = None
    alpha: int | None = None
    rotation: float = 0.0
    tint: tuple[int | float, ...] | None = None


@dataclass(frozen=True)
class FullscreenOverlayPrimitive:
    colour: tuple[int | float, ...]


RenderPrimitive = (
    PolygonPrimitive
    | RectPrimitive
    | LinePrimitive
    | TextureRectPrimitive
    | TextureCenteredPrimitive
    | FullscreenOverlayPrimitive
)


@dataclass(frozen=True)
class EntityRenderState:
    entity_id: int | None
    entity_type: str
    primitives: tuple[RenderPrimitive, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)
