from typing import TYPE_CHECKING
import pygame

from .renderprimitives import RectPrimitive, TextureRectPrimitive

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

    def get_graphic_primitives(self, x: float) -> tuple[object, ...]:
        return ()

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
        icon_rect = self._get_icon_source_rect(icon_number)
        if icon_rect is None:
            return
        self._game.get_graphics().draw_subtexture_world_rect(7, icon_rect, x, 7.0, x + 0.3, 6.7)

    def _build_icon_primitive(self, x: float, icon_number: int):
        icon_rect = self._get_icon_source_rect(icon_number)
        if icon_rect is None:
            return None
        return TextureRectPrimitive(
            texture_id=7,
            src_rect=(icon_rect.x, icon_rect.y, icon_rect.w, icon_rect.h),
            left=x,
            top=7.0,
            right=x + 0.3,
            bottom=6.7,
        )

    def _build_ammo_bar_primitives(self, x: float, count: int, *, width: float = 0.15, step: float = 0.2):
        primitives = []
        for i in range(count):
            bar_x = x + i * step + 0.40
            primitives.append(RectPrimitive(bar_x, 6.9, bar_x + width, 6.8, (255, 255, 255)))
        return tuple(primitives)

    def _get_icon_source_rect(self, icon_number: int):
        tex = self._game.get_interface().get_texture_surface(7) if self._game.get_interface() else None
        if not tex:
            return None

        row = icon_number // 4
        col = icon_number % 4
        tsw, tsh = tex.get_size()
        u_start = col * (tsw / 4)
        v_start = row * (tsh / 4)
        u_width = tsw / 4
        v_height = tsh / 4
        return pygame.Rect(int(u_start), int(v_start), int(u_width), int(v_height))
