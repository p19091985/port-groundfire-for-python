from .entity import Entity
import pygame
from .common import sqr # common.py must have sqr or math
import math

# Need to ensure drawing logic.
# Smoke rotates and scales a texture.
# Pygame: blit with rotation and scaling.

class Smoke(Entity):
    def __init__(self, game, x, y, x_vel, y_vel, texture_id, rotation_rate, growth_rate, fade_rate):
        super().__init__(game)
        self._x = x
        self._y = y
        self._x_vel = x_vel
        self._y_vel = y_vel
        self._texture_id = texture_id
        self._rotation_rate = rotation_rate
        self._growth_rate = growth_rate
        self._fade_rate = fade_rate
        
        self._size = 0.25
        self._fade_away = 0.7
        self._rotate = 0.0

    def draw(self):
        # Retrieve texture
        if not self._game.get_interface():
            return
            
        tex = self._game.get_interface().get_texture_surface(self._texture_id)
        if not tex:
            return
            
        # Prepare surface
        # 1. Scale
        # In OpenGL size=0.25 means width is 0.5 (from -size to size).
        # We need to convert game unit size to pixels.
        # scale_len gives pixel dimension.
        # But wait, original is quad (-size to size), so width is size*2
        
        target_size_px = self._game.get_interface().scale_len(self._size * 2)
        if target_size_px <= 0: return

        # Scale texture
        scaled_surf = pygame.transform.scale(tex, (target_size_px, target_size_px))
        
        # 2. Rotate
        # Pygame rotation expands the rect, so we need to handle centering.
        rotated_surf = pygame.transform.rotate(scaled_surf, -self._rotate) # Pygame angle is counter-clockwise? OpenGLglRotate is usually CCW for Z axis.
        # Check sign. glRotate(angle, 0,0,1).
        
        # 3. Alpha
        # FadeAway 0.7 -> 0.0
        alpha = int(self._fade_away * 255)
        if alpha < 0: alpha = 0
        rotated_surf.set_alpha(alpha)
        
        # 4. Position
        # _x, _y is center in Game Units.
        screen_x, screen_y = self._game.get_interface().game_to_screen(self._x, self._y)
        
        # Blit centered
        rect = rotated_surf.get_rect(center=(screen_x, screen_y))
        
        # Blending? GL_MODULATE + GL_BLEND usually means standard alpha blending.
        # Pygame blit uses alpha by default if source has alpha.
        # "Modulate" implies multiply color. Smoke is usually grey/white.
        # If we need additive blending (fire), we'd use special flags. 
        # But default smoke is usually alpha-over.
        
        self._game.get_interface()._window.blit(rotated_surf, rect)

    def update(self, time):
        self._rotate += time * self._rotation_rate
        self._size += time * self._growth_rate
        self._fade_away -= time * self._fade_rate
        
        self._x += (self._x_vel * time)
        self._y += (self._y_vel * time)
        
        if self._fade_away < 0.0:
            return False # Dead
        
        return True
