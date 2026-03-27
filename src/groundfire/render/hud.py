from __future__ import annotations

from .entity_visual import EntityVisualRenderer
from .primitives import PolygonPrimitive, RectPrimitive, RenderPrimitive, TextureRectPrimitive


class WeaponHudRenderer:
    ICON_GRID_SIZE = 4
    ICON_CELL_SIZE = 16

    def build_primitives(self, game, weapon, x: float) -> tuple[RenderPrimitive, ...]:
        weapon_name = self._weapon_name(weapon)
        stocks: tuple[tuple[str, int], ...] = ()
        available_quantity = int(getattr(weapon, "_available_quantity", 0))
        if weapon_name:
            stocks = ((weapon_name, available_quantity),)
        return self.build_snapshot_primitives(weapon_name, stocks, x)

    def build_snapshot_primitives(
        self,
        weapon_name: str,
        weapon_stocks: tuple[tuple[str, int], ...],
        x: float,
    ) -> tuple[RenderPrimitive, ...]:
        weapon_name = weapon_name.lower()
        if weapon_name == "shell":
            return self._icon_only(x, 0)
        if weapon_name == "nuke":
            return self._icon_only(x, 1)
        if weapon_name == "machinegun":
            return self._machinegun(x, self._stock_amount(weapon_stocks, "machinegun"))
        if weapon_name == "mirv":
            return self._icon_only(x, 4)
        if weapon_name == "missile":
            return self._missiles(x, self._stock_amount(weapon_stocks, "missile"))
        return ()

    def _icon_only(self, x: float, icon_number: int) -> tuple[RenderPrimitive, ...]:
        primitive = self._build_icon_primitive(x, icon_number)
        return () if primitive is None else (primitive,)

    def _missiles(self, x: float, available_quantity: int) -> tuple[RenderPrimitive, ...]:
        primitive = self._build_icon_primitive(x, 10)
        if primitive is None:
            return ()
        bars = []
        for index in range(max(0, available_quantity)):
            gx = x + (index * 0.2) + 0.40
            bars.append(RectPrimitive(gx, 6.9, gx + 0.15, 6.8, (255, 255, 255)))
        return (primitive,) + tuple(bars)

    def _machinegun(self, x: float, available_quantity: int) -> tuple[RenderPrimitive, ...]:
        primitive = self._build_icon_primitive(x, 2)
        if primitive is None:
            return ()
        amount = float(available_quantity) / 50.0
        return (
            primitive,
            RectPrimitive(x + 0.40, 6.95, x + 0.40 + amount, 6.75, (255, 255, 255)),
        )

    def _build_icon_primitive(self, x: float, icon_number: int) -> TextureRectPrimitive:
        cell_width = self.ICON_CELL_SIZE
        cell_height = self.ICON_CELL_SIZE
        row = icon_number // 4
        col = icon_number % 4
        return TextureRectPrimitive(
            texture_id=7,
            src_rect=(int(col * cell_width), int(row * cell_height), cell_width, cell_height),
            left=x,
            top=7.0,
            right=x + 0.3,
            bottom=6.7,
        )

    def _stock_amount(self, weapon_stocks: tuple[tuple[str, int], ...], weapon_name: str) -> int:
        for current_weapon, amount in weapon_stocks:
            if current_weapon == weapon_name:
                return int(amount)
        return 0

    def _weapon_name(self, weapon) -> str:
        type_name = weapon.__class__.__name__.lower()
        for candidate in ("shell", "nuke", "machinegun", "mirv", "missile"):
            if candidate in type_name:
                return candidate
        return ""


class GameHudRenderer:
    def __init__(self, *, weapon_hud_renderer: WeaponHudRenderer | None = None):
        self._weapon_hud_renderer = weapon_hud_renderer or WeaponHudRenderer()

    def render_round_hud(self, game):
        visual_renderer = game.get_visual_renderer()
        for index in range(game.get_num_of_players()):
            player = game.get_players()[index]
            if player is None:
                continue
            tank = player.get_tank()
            if tank is None or not tank.alive() or not self._can_render_tank_hud(tank):
                continue
            visual_renderer.render_primitives(game, self._build_tank_hud_primitives(tank))

    def render_round_start_overlay(self, game):
        ui = game.get_ui()
        overlay_style = ui.style(0.6, (255, 255, 255), shadow=True)
        ui.draw_centered_text(0.0, 0.5, f"Round {game.get_current_round()}", style=overlay_style)
        ui.draw_centered_text(0.0, -0.5, "Get Ready", style=overlay_style)

    def render_fps(self, game, fps: float):
        game.get_ui().printf(
            -10.0,
            -7.3,
            "%.1f FPS",
            fps,
            style=game.get_ui().style(0.3, (128, 255, 51), spacing=0.25),
        )

    def _build_tank_hud_primitives(self, tank) -> tuple[RenderPrimitive, ...]:
        start_of_bar = -10.0 + (2.5 * tank._stats_position) + 0.1
        start_bar_x = start_of_bar + 0.1
        end_bar_x = start_bar_x + 2.1 * (tank._health / 100.0)
        end_fuel_x = start_bar_x + 2.1 * tank._fuel

        health_red = min(255, int((1.0 - (tank._health / 200.0)) * 255))
        health_green = min(255, int((0.5 + (tank._health / 200.0)) * 255))
        fuel_red = min(255, int((0.5 - (tank._fuel * 0.5)) * 255))
        fuel_blue = min(255, int((0.5 + (tank._fuel * 0.5)) * 255))

        primitives: list[RenderPrimitive] = [
            PolygonPrimitive(
                points=(
                    (start_of_bar, 7.4),
                    (start_of_bar + 2.3, 7.4),
                    (start_of_bar + 2.3, 6.6),
                    (start_of_bar, 6.6),
                ),
                colour=(128, 230, 153, 76),
            ),
            PolygonPrimitive(
                points=(
                    (start_of_bar + 0.15, 7.0),
                    (start_of_bar + 0.00, 6.7),
                    (start_of_bar + 0.60, 6.7),
                    (start_of_bar + 0.45, 7.0),
                ),
                colour=tank.get_colour(),
            ),
        ]

        if end_bar_x > start_bar_x:
            primitives.append(RectPrimitive(start_bar_x, 7.4, end_bar_x, 7.3, (health_red, health_green, 128)))

        if end_fuel_x > start_bar_x:
            primitives.append(RectPrimitive(start_bar_x, 7.2, end_fuel_x, 7.1, (fuel_red, 128, fuel_blue)))

        weapon = tank.get_weapon(tank.get_selected_weapon())
        primitives.extend(self._weapon_hud_renderer.build_primitives(tank._game, weapon, start_of_bar + 0.7))
        return tuple(primitives)

    def _can_render_tank_hud(self, tank) -> bool:
        return all(
            hasattr(tank, attribute)
            for attribute in (
                "_stats_position",
                "_health",
                "_fuel",
                "_game",
                "get_colour",
                "get_weapon",
                "get_selected_weapon",
            )
        )


class PygameEntityRenderer(EntityVisualRenderer):
    pass


class PygameHudRenderer(GameHudRenderer):
    pass


class HudRenderModelBuilder:
    def __init__(self, *, hud_renderer: GameHudRenderer | None = None):
        self._hud_renderer = hud_renderer or GameHudRenderer()

    def build_round_hud(self, game):
        primitives = []
        for index in range(game.get_num_of_players()):
            player = game.get_players()[index]
            if player is None:
                continue
            tank = player.get_tank()
            if tank is None or not tank.alive() or not self._hud_renderer._can_render_tank_hud(tank):
                continue
            primitives.extend(self._hud_renderer._build_tank_hud_primitives(tank))
        return tuple(primitives)
