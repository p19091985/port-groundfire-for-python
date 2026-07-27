from __future__ import annotations

from importlib import import_module

__all__ = [
    "EntityRenderState",
    "EntityVisualRenderer",
    "HudRenderModelBuilder",
    "FullscreenOverlayPrimitive",
    "LinePrimitive",
    "PolygonPrimitive",
    "PygameEntityRenderer",
    "PygameHudRenderer",
    "RectPrimitive",
    "ReplicatedEntityRenderStateBuilder",
    "ReplicatedMatchScene",
    "ReplicatedRenderFrame",
    "ReplicatedSceneRenderer",
    "RenderPrimitive",
    "TerrainRenderStateBuilder",
    "TextureCenteredPrimitive",
    "TextureRectPrimitive",
]


def __getattr__(name: str):
    if name in {"HudRenderModelBuilder", "PygameEntityRenderer", "PygameHudRenderer"}:
        return getattr(import_module("src.groundfire.render.hud"), name)
    if name == "EntityVisualRenderer":
        return getattr(import_module("src.groundfire.render.entity_visual"), name)
    if name in {
        "EntityRenderState",
        "FullscreenOverlayPrimitive",
        "LinePrimitive",
        "PolygonPrimitive",
        "RectPrimitive",
        "RenderPrimitive",
        "TextureCenteredPrimitive",
        "TextureRectPrimitive",
    }:
        return getattr(import_module("src.groundfire.render.primitives"), name)
    if name in {
        "ReplicatedEntityRenderStateBuilder",
        "ReplicatedMatchScene",
        "ReplicatedRenderFrame",
        "ReplicatedSceneRenderer",
    }:
        return getattr(import_module("src.groundfire.render.scene"), name)
    if name == "TerrainRenderStateBuilder":
        return getattr(import_module("src.groundfire.render.terrain"), name)
    raise AttributeError(name)
