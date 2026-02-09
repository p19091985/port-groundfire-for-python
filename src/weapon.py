from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from .game import Game
    from .tank import Tank

class Weapon:
    def __init__(self, game: 'Game', owner_tank: 'Tank'):
        self._game = game
        self._owner_tank = owner_tank
        self._cost = 0
        self._cooldown = 0.0
        self._quantity = 0
        self._available_quantity = 0 # _quantityAvailable in cc
        self._firing = False
        self._last_shot_time = 0.0
        self._cooldown_time = 0.0

    def fire(self, firing: bool, time: float) -> bool:
        raise NotImplementedError

    def update(self, time: float):
        raise NotImplementedError

    def select(self) -> bool:
        raise NotImplementedError

    def draw_graphic(self, x: float):
        raise NotImplementedError

    def set_ammo_for_round(self):
        pass

    def unselect(self):
        pass

    def ready_to_fire(self) -> bool:
        return self._cooldown <= 0.0

    def get_ammo(self) -> int:
        return self._quantity

    def add_amount(self, amount: int):
        self._quantity += amount

    def get_cost(self) -> int:
        return self._cost

    def set_cost(self, cost: int):
        self._cost = cost

    def texture(self, texture_number: int):
        if self._game.get_interface():
            self._game.get_interface().set_texture(texture_number)

    def draw_icon(self, x: float, icon_number: int):
        if not self._game.get_interface(): return
        
        row = icon_number // 4
        col = icon_number % 4
        
        # Texture 7 is weapon icons
        tex = self._game.get_interface().get_texture_surface(7)
        if not tex: return
        
        # UV mapping
        # Each icon is 0.25 x 0.25 in UV space.
        # Pixel coords:
        tsw, tsh = tex.get_size()
        u1 = col * 0.25
        v1 = 1.0 - (row * 0.25) # Top (GL Y is bottom-up)
        # GL: (u, v) -> (0, 1) is top left in Pygame? 
        # OpenGL (0,0) is bottom-left usually. Pygame (0,0) is top-left.
        # Original code uses GL so v=1.0 is top.
        # Pygame surface: (0,0) top. 
        # So v=1.0 maps to y=0 in Pygame? No.
        # We need to flip V for Pygame sub-surface rect logic.
        # row*0.25 is top.
        
        u_start = col * (tsw / 4)
        v_start = row * (tsh / 4)
        u_width = tsw / 4
        v_height = tsh / 4
        
        # Original: (x, 7.0) top, (x+0.3, 6.7) bottom?
        # Quad (x, 7.0f, 0.0) -> v=1-(row*0.25)
        # Quad (x, 6.7f ...) -> v=0.75-(row*0.25)
        
        icon_rect = pygame.Rect(int(u_start), int(v_start), int(u_width), int(v_height))
        sub_surf = tex.subsurface(icon_rect)
        
        # Dest rect
        # x is provided. Y is 6.7 to 7.0. Width 0.3. Height 0.3.
        # Convert game coords to screen.
        
        # Interface.game_to_screen handles Y flip.
        # Top-Left of icon in Game Units: (x, 7.0)
        sx, sy = self._game.get_interface().game_to_screen(x, 7.0)
        
        # Scale 0.3 game units to pixels
        px_size = self._game.get_interface().scale_len(0.3)
        
        scaled = pygame.transform.scale(sub_surf, (px_size, px_size))
        
        self._game.get_interface()._window.blit(scaled, (sx, sy))
