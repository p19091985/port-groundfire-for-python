from __future__ import annotations

import pygame

from .renderprimitives import RectPrimitive, TextureRectPrimitive
from .weapons_impl import MachineGunWeapon, MirvWeapon, MissileWeapon, NukeWeapon, ShellWeapon


class WeaponHudRenderer:
    def build_primitives(self, game, weapon, x: float) -> tuple[object, ...]:
        if isinstance(weapon, ShellWeapon):
            return self._icon_only(game, x, 0)
        if isinstance(weapon, NukeWeapon):
            return self._icon_only(game, x, 1)
        if isinstance(weapon, MachineGunWeapon):
            return self._machinegun(game, weapon, x)
        if isinstance(weapon, MirvWeapon):
            return self._icon_only(game, x, 4)
        if isinstance(weapon, MissileWeapon):
            return self._missiles(game, weapon, x)
        return ()

    def _icon_only(self, game, x: float, icon_number: int):
        primitive = self._build_icon_primitive(game, x, icon_number)
        return () if primitive is None else (primitive,)

    def _missiles(self, game, weapon: MissileWeapon, x: float):
        primitive = self._build_icon_primitive(game, x, 10)
        if primitive is None:
            return ()
        bars = []
        for i in range(weapon._available_quantity):
            gx = x + i * 0.2 + 0.40
            bars.append(RectPrimitive(gx, 6.9, gx + 0.15, 6.8, (255, 255, 255)))
        return (primitive,) + tuple(bars)

    def _machinegun(self, game, weapon: MachineGunWeapon, x: float):
        primitive = self._build_icon_primitive(game, x, 2)
        if primitive is None:
            return ()
        amt = weapon._available_quantity / 50.0
        return (
            primitive,
            RectPrimitive(x + 0.40, 6.95, x + 0.40 + amt, 6.75, (255, 255, 255)),
        )

    def _build_icon_primitive(self, game, x: float, icon_number: int):
        interface = game.get_interface()
        if interface is None:
            return None
        texture = interface.get_texture_surface(7)
        if texture is None:
            return None

        row = icon_number // 4
        col = icon_number % 4
        tsw, tsh = texture.get_size()
        src_rect = pygame.Rect(int(col * (tsw / 4)), int(row * (tsh / 4)), int(tsw / 4), int(tsh / 4))
        return TextureRectPrimitive(
            texture_id=7,
            src_rect=(src_rect.x, src_rect.y, src_rect.w, src_rect.h),
            left=x,
            top=7.0,
            right=x + 0.3,
            bottom=6.7,
        )
