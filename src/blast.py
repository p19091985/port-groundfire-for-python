from .entity import Entity
import pygame

class Blast(Entity):
    # Static settings
    OPTION_BlastFadeRate = 0.1
    OPTION_WhiteoutFadeRate = 0.6

    def __init__(self, game, x, y, size, fade_away, white_out):
        super().__init__(game)
        self._x = x
        self._y = y
        self._size = size
        self._fade_away = fade_away
        self._white_out = white_out
        self._white_out_level = 1.0 if white_out else 0.0

    @staticmethod
    def read_settings(settings):
        Blast.OPTION_BlastFadeRate = settings.get_float("Effects", "BlastFadeRate", 0.1)
        Blast.OPTION_WhiteoutFadeRate = settings.get_float("Effects", "WhiteoutFadeRate", 0.6)

    def draw(self):
        # Draw Blast
        # Texture 0 is blast texture.
        tex = self._game.get_interface().get_texture_surface(0)
        if tex:
            # Blast size
            blast_size = self._size * 1.1
            target_px = self._game.get_interface().scale_len(blast_size * 2)
            
            if target_px > 0:
                scaled = pygame.transform.scale(tex, (target_px, target_px))
                alpha = int(self._fade_away * 255)
                if alpha < 0: alpha = 0
                scaled.set_alpha(alpha)
                
                sx, sy = self._game.get_interface().game_to_screen(self._x, self._y)
                rect = scaled.get_rect(center=(sx, sy))
                
                if self._game.get_interface()._window:
                     self._game.get_interface()._window.blit(scaled, rect)

        # Draw Whiteout
        if self._white_out:
            # Full screen white rectangle
            # Pygame surface with alpha
            w, h, _ = self._game.get_interface().get_window_settings()
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            
            alpha_val = int(self._white_out_level * 255)
            if alpha_val < 0: alpha_val = 0
            
            s.fill((255, 255, 255, alpha_val))
            self._game.get_interface()._window.blit(s, (0, 0))

    def update(self, time):
        self._fade_away -= time * Blast.OPTION_BlastFadeRate
        
        if self._white_out:
            self._white_out_level -= time * Blast.OPTION_WhiteoutFadeRate
            if self._white_out_level < 0.0:
                self._white_out = False
        
        if self._fade_away < 0.0:
            return False # Dead
            
        return True
