from __future__ import annotations

from typing import Any, Callable

from ..core.pygame import PygameBackend


class GameGraphics:
    def __init__(self, *, interface_provider: Callable[[], object | None], pygame_module=None):
        self._interface_provider = interface_provider
        self._backend = PygameBackend.create(pygame_module)
        self._pygame: Any = self._backend.pygame

    def clear(self, colour=(0, 0, 0)):
        self._fill_surface(self._rgb(colour))

    def fill_screen(self, colour):
        self.clear(colour)

    def draw_world_polygon(self, points, colour):
        interface = self._get_interface()
        self.draw_screen_polygon([interface.game_to_screen(x, y) for x, y in points], colour)

    def draw_screen_polygon(self, points, colour):
        rgba = self._rgba(colour)
        if rgba[3] < 255:
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            width = max_x - min_x
            height = max_y - min_y

            if width < 1 or height < 1:
                return

            surface = self._pygame.Surface((width, height), self._pygame.SRCALPHA)
            local_points = [(point[0] - min_x, point[1] - min_y) for point in points]
            self._pygame.draw.polygon(surface, rgba, local_points)
            self._blit_surface(surface, (min_x, min_y))
            return

        self._draw_polygon(rgba[:3], points)

    def draw_world_rect(self, left: float, top: float, right: float, bottom: float, colour):
        interface = self._get_interface()
        p1 = interface.game_to_screen(left, top)
        p2 = interface.game_to_screen(right, bottom)
        x = min(p1[0], p2[0])
        y = min(p1[1], p2[1])
        width = abs(p2[0] - p1[0])
        height = abs(p2[1] - p1[1])
        self.draw_screen_rect((x, y, width, height), colour)

    def draw_screen_rect(self, rect, colour):
        rgba = self._rgba(colour)
        if rgba[3] < 255:
            surface = self._pygame.Surface((rect[2], rect[3]), self._pygame.SRCALPHA)
            surface.fill(rgba)
            self._blit_surface(surface, (rect[0], rect[1]))
            return

        self._draw_rect(rgba[:3], rect)

    def draw_world_line(self, start, end, colour, *, width: int | None = None):
        interface = self._get_interface()
        p1 = interface.game_to_screen(*start)
        p2 = interface.game_to_screen(*end)
        line_width = width if width is not None else getattr(interface, "get_line_width", lambda: 1)()
        self._draw_line(self._rgb(colour), p1, p2, line_width)

    def draw_texture_world_rect(
        self,
        texture_id: int,
        left: float,
        top: float,
        right: float,
        bottom: float,
        *,
        alpha: int | None = None,
        tint=None,
    ):
        self.draw_surface_world_rect(
            self._get_interface().get_texture_surface(texture_id),
            left,
            top,
            right,
            bottom,
            alpha=alpha,
            tint=tint,
        )

    def draw_subtexture_world_rect(
        self,
        texture_id: int,
        src_rect,
        left: float,
        top: float,
        right: float,
        bottom: float,
        *,
        alpha: int | None = None,
        tint=None,
    ):
        texture = self._get_interface().get_texture_surface(texture_id)
        if texture is None:
            return

        surface = texture.subsurface(src_rect).copy()
        self.draw_surface_world_rect(surface, left, top, right, bottom, alpha=alpha, tint=tint)

    def draw_surface_world_rect(
        self,
        surface,
        left: float,
        top: float,
        right: float,
        bottom: float,
        *,
        alpha: int | None = None,
        tint=None,
    ):
        if surface is None:
            return

        interface = self._get_interface()
        p1 = interface.game_to_screen(left, top)
        p2 = interface.game_to_screen(right, bottom)
        width = abs(p2[0] - p1[0])
        height = abs(p2[1] - p1[1])
        if width <= 0 or height <= 0:
            return

        scaled = self._pygame.transform.scale(surface, (int(width), int(height)))
        scaled = self._apply_tint_and_alpha(scaled, tint=tint, alpha=alpha)
        self._blit_surface(scaled, (min(p1[0], p2[0]), min(p1[1], p2[1])))

    def draw_texture_centered(
        self,
        texture_id: int,
        x: float,
        y: float,
        width_units: float,
        height_units: float | None = None,
        *,
        alpha: int | None = None,
        rotation: float = 0.0,
        tint=None,
    ):
        self.draw_surface_centered(
            self._get_interface().get_texture_surface(texture_id),
            x,
            y,
            width_units,
            height_units,
            alpha=alpha,
            rotation=rotation,
            tint=tint,
        )

    def draw_surface_centered(
        self,
        surface,
        x: float,
        y: float,
        width_units: float,
        height_units: float | None = None,
        *,
        alpha: int | None = None,
        rotation: float = 0.0,
        tint=None,
    ):
        if surface is None:
            return

        interface = self._get_interface()
        width_px = interface.scale_len(width_units)
        height_px = interface.scale_len(width_units if height_units is None else height_units)
        if width_px <= 0 or height_px <= 0:
            return

        output = self._pygame.transform.scale(surface, (int(width_px), int(height_px)))
        output = self._apply_tint_and_alpha(output, tint=tint, alpha=alpha)

        if rotation != 0.0:
            output = self._pygame.transform.rotate(output, rotation)
            if alpha is not None:
                output.set_alpha(alpha)

        center = interface.game_to_screen(x, y)
        rect = output.get_rect(center=center)
        self._blit_surface(output, rect)

    def draw_fullscreen_overlay(self, colour):
        width, height, _ = self._get_interface().get_window_settings()
        overlay = self._pygame.Surface((width, height), self._pygame.SRCALPHA)
        overlay.fill(self._rgba(colour))
        self._blit_surface(overlay, (0, 0))

    def blit_surface(self, surface, dest):
        self._blit_surface(surface, dest)

    def blit_texture(self, texture_id: int, dest):
        texture = self._get_interface().get_texture_surface(texture_id)
        if texture is None:
            return
        self.blit_surface(texture, dest)

    def draw_tiled_texture(self, texture_id: int, *, tint=None, offset_px=(0, 0), fallback_fill=None):
        texture = self._get_interface().get_texture_surface(texture_id)
        if texture is None:
            if fallback_fill is not None:
                self.fill_screen(fallback_fill)
            return

        tile = texture.copy()
        tile = self._apply_tint_and_alpha(tile, tint=tint, alpha=None)

        screen_w, screen_h, _ = self._get_interface().get_window_settings()
        tile_w = tile.get_width()
        tile_h = tile.get_height()
        if tile_w <= 0 or tile_h <= 0:
            return

        off_x = offset_px[0] % tile_w
        off_y = offset_px[1] % tile_h

        for y in range(-off_y, screen_h, tile_h):
            for x in range(-off_x, screen_w, tile_w):
                self._blit_surface(tile, (x, y))

    def _apply_tint_and_alpha(self, surface, *, tint=None, alpha: int | None):
        output = surface.copy()
        if tint is not None:
            tint_rgba = self._rgba(tint)
            tint_surface = self._pygame.Surface(output.get_size(), self._pygame.SRCALPHA)
            tint_surface.fill((tint_rgba[0], tint_rgba[1], tint_rgba[2], 255))
            output.blit(tint_surface, (0, 0), special_flags=self._pygame.BLEND_RGBA_MULT)
        if alpha is not None:
            output.set_alpha(alpha)
        return output

    def _get_interface(self):
        interface = self._interface_provider()
        if interface is None:
            raise RuntimeError("GameGraphics interface is not initialized yet.")
        return interface

    def _get_window(self):
        interface = self._get_interface()
        if hasattr(interface, "get_draw_surface"):
            return interface.get_draw_surface()
        return interface._window

    def _fill_surface(self, colour):
        interface = self._get_interface()
        if hasattr(interface, "fill_surface"):
            interface.fill_surface(colour)
            return
        self._get_window().fill(colour)

    def _blit_surface(self, surface, dest):
        interface = self._get_interface()
        if hasattr(interface, "blit_surface"):
            interface.blit_surface(surface, dest)
            return
        self._get_window().blit(surface, dest)

    def _draw_polygon(self, colour, points):
        interface = self._get_interface()
        if hasattr(interface, "draw_polygon"):
            interface.draw_polygon(colour, points)
            return
        self._pygame.draw.polygon(self._get_window(), colour, points)

    def _draw_rect(self, colour, rect):
        interface = self._get_interface()
        if hasattr(interface, "draw_rect"):
            interface.draw_rect(colour, rect)
            return
        self._pygame.draw.rect(self._get_window(), colour, rect)

    def _draw_line(self, colour, start, end, width):
        interface = self._get_interface()
        if hasattr(interface, "draw_line"):
            interface.draw_line(colour, start, end, width)
            return
        self._pygame.draw.line(self._get_window(), colour, start, end, width)

    def _rgb(self, colour):
        rgba = self._rgba(colour)
        return rgba[:3]

    def _rgba(self, colour):
        if len(colour) == 4:
            return tuple(self._channel(value) for value in colour)
        return tuple(self._channel(value) for value in colour) + (255,)

    def _channel(self, value):
        if isinstance(value, float) and 0.0 <= value <= 1.0:
            return int(value * 255)
        return int(value)


def get_interface_graphics(interface) -> GameGraphics:
    graphics = getattr(interface, "_graphics_helper", None)
    if graphics is None:
        graphics = GameGraphics(interface_provider=lambda: interface)
        setattr(interface, "_graphics_helper", graphics)
    return graphics
