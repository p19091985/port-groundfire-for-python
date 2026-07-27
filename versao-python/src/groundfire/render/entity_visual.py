from __future__ import annotations

from .primitives import (
    EntityRenderState,
    FullscreenOverlayPrimitive,
    LinePrimitive,
    PolygonPrimitive,
    RectPrimitive,
    TextureCenteredPrimitive,
    TextureRectPrimitive,
)


class EntityVisualRenderer:
    def __init__(self, *, state_builder=None):
        self._state_builder = state_builder

    def render_entity(self, game, entity) -> bool:
        render_state = self.build_render_state(game, entity)
        if render_state is None:
            return False
        self.render_state(game, render_state)
        return True

    def render_state(self, game, render_state: EntityRenderState):
        self.render_primitives(game, render_state.primitives)

    def render_primitives(self, game, primitives):
        graphics = game.get_graphics()
        for primitive in primitives:
            if isinstance(primitive, PolygonPrimitive):
                graphics.draw_world_polygon(primitive.points, primitive.colour)
            elif isinstance(primitive, RectPrimitive):
                graphics.draw_world_rect(
                    primitive.left,
                    primitive.top,
                    primitive.right,
                    primitive.bottom,
                    primitive.colour,
                )
            elif isinstance(primitive, LinePrimitive):
                graphics.draw_world_line(primitive.start, primitive.end, primitive.colour, width=primitive.width)
            elif isinstance(primitive, TextureRectPrimitive):
                if primitive.src_rect is not None:
                    graphics.draw_subtexture_world_rect(
                        primitive.texture_id,
                        primitive.src_rect,
                        primitive.left,
                        primitive.top,
                        primitive.right,
                        primitive.bottom,
                        alpha=primitive.alpha,
                        tint=primitive.tint,
                    )
                else:
                    graphics.draw_texture_world_rect(
                        primitive.texture_id,
                        primitive.left,
                        primitive.top,
                        primitive.right,
                        primitive.bottom,
                        alpha=primitive.alpha,
                        tint=primitive.tint,
                    )
            elif isinstance(primitive, TextureCenteredPrimitive):
                graphics.draw_texture_centered(
                    primitive.texture_id,
                    primitive.x,
                    primitive.y,
                    primitive.width,
                    primitive.height,
                    alpha=primitive.alpha,
                    rotation=primitive.rotation,
                    tint=primitive.tint,
                )
            elif isinstance(primitive, FullscreenOverlayPrimitive):
                graphics.draw_fullscreen_overlay(primitive.colour)
            else:
                raise TypeError(f"Unsupported render primitive: {type(primitive)!r}")

    def build_render_state(self, game, entity):
        if self._state_builder is not None:
            return self._state_builder.build_render_state(game, entity)

        state_getter = getattr(entity, "get_render_state", None)
        if state_getter is None:
            return None
        return state_getter()
