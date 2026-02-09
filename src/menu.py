from typing import TYPE_CHECKING
import pygame
from .common import PI

if TYPE_CHECKING:
    from .game import Game

class Menu:
    _background_scroll = 0.0
    BACKGROUND_SCROLL_SPEED = 0.1

    def __init__(self, game: 'Game'):
        self._game = game
        self._font = game.get_font()
        self._interface = game.get_interface()

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
        tex = self._interface.get_texture_image(6)
        if not tex:
            self._interface._window.fill((100, 180, 230)) # Fallback color
            return

        screen_w, screen_h, _ = self._interface.get_window_settings()
        
        tw = tex.get_width()
        th = tex.get_height()
        
        # Create tinted texture
        # Original seems to be Dark Blue-ish Cyan.
        # Approx (0.4, 0.4, 0.6) * 255 in C++?
        # C++ uses glColor3f(0.4f, 0.7f, 0.9f)
        tint_col = (102, 179, 230)
        
        tinted_tex = pygame.Surface((tw, th), pygame.SRCALPHA)
        tinted_tex.fill((*tint_col, 255))
        
        # We want to multiply texture by tint.
        # Assuming texture is grayscale/white pattern.
        # Blit texture onto color with MULT? 
        # Or blit color onto texture with MULT?
        # If texture has alpha, we need to preserve it.
        # Let's make a copy of texture and MULT blend the color over it.
        
        final_tex = tex.copy()
        final_tex.blit(tinted_tex, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Calculate offset in pixels based on scroll (0..1)
        # Scroll moves the texture "left" or "up"?
        # C++: UV (10 + scroll)
        # If scroll increases, UV increases, texture moves Left.
        
        off_x = int(Menu._background_scroll * tw) % tw
        off_y = int(Menu._background_scroll * th) % th
        
        # Draw from -off_x to screen_w, -off_y to screen_h
        # Ensure we cover the whole screen.
        for y in range(-off_y, screen_h, th):
            for x in range(-off_x, screen_w, tw):
                self._interface._window.blit(final_tex, (x, y))
