import unittest

from src.gamehudrenderer import GameHudRenderer
from src.groundfire.render.hud import WeaponHudRenderer
from src.groundfire.render.primitives import TextureRectPrimitive


class VisualRendererStub:
    def __init__(self):
        self.primitive_batches = []

    def render_primitives(self, _game, primitives):
        self.primitive_batches.append(tuple(primitives))


class FontStub:
    def __init__(self):
        self.centred_calls = []
        self.printf_calls = []
        self.shadow_calls = []
        self.proportional_calls = []
        self.orientation_calls = []
        self.size_calls = []
        self.colour_calls = []

    def set_shadow(self, value):
        self.shadow_calls.append(value)

    def set_proportional(self, value):
        self.proportional_calls.append(value)

    def set_orientation(self, value):
        self.orientation_calls.append(value)

    def set_size(self, *args):
        self.size_calls.append(args)

    def set_colour(self, colour):
        self.colour_calls.append(colour)

    def print_centred_at(self, *args):
        self.centred_calls.append(args)

    def printf(self, *args):
        self.printf_calls.append(args)


class UIStub:
    def __init__(self):
        from src.gameui import GameUI

        self.font = FontStub()
        self._ui = GameUI(font_provider=lambda: self.font)

    def style(self, *args, **kwargs):
        return self._ui.style(*args, **kwargs)

    def draw_centered_text(self, *args, **kwargs):
        return self._ui.draw_centered_text(*args, **kwargs)

    def printf(self, *args, **kwargs):
        return self._ui.printf(*args, **kwargs)


class WeaponStub:
    pass


class WeaponHudRendererStub:
    def __init__(self):
        self.calls = []

    def build_primitives(self, _game, weapon, x):
        self.calls.append((weapon, x))
        return ("weapon",)


class TankStub:
    def __init__(self, stats_position=0, alive=True):
        self._stats_position = stats_position
        self._health = 75.0
        self._fuel = 0.5
        self._game = object()
        self.weapon = WeaponStub()
        self._alive = alive

    def alive(self):
        return self._alive

    def get_colour(self):
        return (10, 20, 30)

    def get_weapon(self, _index):
        return self.weapon

    def get_selected_weapon(self):
        return 0


class PlayerStub:
    def __init__(self, tank):
        self.tank = tank

    def get_tank(self):
        return self.tank


class GameStub:
    def __init__(self, players=None):
        self.players = players or []
        self.visual_renderer = VisualRendererStub()
        self.ui = UIStub()
        self._current_round = 3

    def get_num_of_players(self):
        return len(self.players)

    def get_players(self):
        return self.players

    def get_visual_renderer(self):
        return self.visual_renderer

    def get_ui(self):
        return self.ui

    def get_current_round(self):
        return self._current_round


class GameHudRendererTests(unittest.TestCase):
    def test_weapon_hud_uses_sprite_sheet_cells_instead_of_whole_texture(self):
        renderer = WeaponHudRenderer()

        primitives = renderer.build_snapshot_primitives("shell", (("shell", 1),), -9.2)

        self.assertEqual(len(primitives), 1)
        self.assertIsInstance(primitives[0], TextureRectPrimitive)
        self.assertEqual(primitives[0].src_rect, (0, 0, 16, 16))

    def test_render_round_hud_builds_batches_only_for_alive_tanks(self):
        weapon_hud = WeaponHudRendererStub()
        renderer = GameHudRenderer(weapon_hud_renderer=weapon_hud)
        alive_tank = TankStub(stats_position=1, alive=True)
        dead_tank = TankStub(stats_position=2, alive=False)
        game = GameStub(players=[PlayerStub(alive_tank), PlayerStub(dead_tank)])
        alive_tank._game = game
        dead_tank._game = game

        renderer.render_round_hud(game)

        self.assertEqual(len(game.visual_renderer.primitive_batches), 1)
        self.assertEqual(weapon_hud.calls, [(alive_tank.weapon, -10.0 + (2.5 * 1) + 0.8)])
        self.assertIn("weapon", game.visual_renderer.primitive_batches[0])

    def test_render_round_start_overlay_and_fps_use_ui(self):
        renderer = GameHudRenderer()
        game = GameStub(players=[])

        renderer.render_round_start_overlay(game)
        renderer.render_fps(game, 91.5)

        self.assertEqual(
            game.ui.font.centred_calls,
            [
                (0.0, 0.5, "Round 3"),
                (0.0, -0.5, "Get Ready"),
            ],
        )
        self.assertEqual(game.ui.font.printf_calls, [(-10.0, -7.3, "%.1f FPS", 91.5)])


if __name__ == "__main__":
    unittest.main()
