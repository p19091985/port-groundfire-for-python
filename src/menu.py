from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game


class Menu:
    _background_scroll = 0.0
    BACKGROUND_SCROLL_SPEED = 0.1

    def __init__(self, game: 'Game'):
        self._game = game
        self._font = game.get_font()
        self._interface = game.get_interface()
        self._graphics = game.get_graphics()
        self._ui = game.get_ui()

    def update(self, time: float) -> int:
        raise NotImplementedError

    def draw(self):
        raise NotImplementedError

    def update_background(self, time: float):
        Menu._background_scroll += time * Menu.BACKGROUND_SCROLL_SPEED
        if Menu._background_scroll > 1.0:
            Menu._background_scroll -= 1.0

    def draw_background(self):
        # Texture 6 is usually "menuback"
        # C++ uses GL_TEXTURE_2D with scroll on UVs.
        # [-10, -7.5] to [10, 7.5] is the quad.
        
        # Pygame implementation: 
        # Tile the background or scroll it.
        # Since it's a repeated texture (UV 0..1 becomes larger or scrolled),
        # Texture coord is scroll .. 10+scroll? No, in C++ it was:
        # 0: scroll, scroll
        # 1: 10+scroll, scroll
        # etc.
        # This implies the texture repeats 10 times horizontally?
        # Actually (10.0f + _backgroundScroll).
        # So yes, it repeats.
        
        # In Pygame, drawing a scrolling tiled background is a bit manual.
        # A simpler faithful approximation: Draw a localized background if possible, or skip strict texture scrolling if too complex for now,
        # BUT user wanted "Faithful".
        
        # We can blit a pattern.
        # Calculate offset in pixels based on scroll (0..1)
        # Scroll moves the texture "left" or "up"?
        # C++: UV (10 + scroll)
        # If scroll increases, UV increases, texture moves Left.
        texture = self._interface.get_texture_image(6)
        if texture is None:
            self._graphics.fill_screen((100, 180, 230))
            return

        off_x = int(Menu._background_scroll * texture.get_width())
        off_y = int(Menu._background_scroll * texture.get_height())
        self._graphics.draw_tiled_texture(6, tint=(102, 179, 230), offset_px=(off_x, off_y), fallback_fill=(100, 180, 230))

    def draw_game_polygon(self, points, color):
        self._graphics.draw_world_polygon(points, color)

    def draw_texture_rect(self, texture_id: int, left: float, top: float, right: float, bottom: float):
        self._graphics.draw_texture_world_rect(texture_id, left, top, right, bottom)
