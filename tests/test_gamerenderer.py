import unittest

from src.common import GameState
from src.gamerenderer import GameRenderer
from src.gameui import GameUI


class InterfaceStub:
    def __init__(self):
        self.start_draw_calls = 0
        self.end_draw_calls = 0

    def start_draw(self):
        self.start_draw_calls += 1

    def end_draw(self):
        self.end_draw_calls += 1


class FontStub:
    def __init__(self):
        self.shadow_calls = []
        self.proportional_calls = []
        self.orientation_calls = []
        self.size_calls = []
        self.colour_calls = []
        self.centred_calls = []
        self.text_calls = []
        self.printf_calls = []

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

    def print_at(self, *args):
        self.text_calls.append(args)

    def printf(self, *args):
        self.printf_calls.append(args)


class DrawStub:
    def __init__(self):
        self.draw_calls = 0

    def draw(self):
        self.draw_calls += 1


class VisualRendererStub:
    def __init__(self):
        self.rendered_entities = []
        self.handled_ids = set()

    def render_entity(self, _game, entity):
        self.rendered_entities.append(entity)
        return id(entity) in self.handled_ids


class HudRendererStub:
    def __init__(self):
        self.round_hud_calls = 0
        self.round_start_overlay_calls = []
        self.fps_calls = []

    def render_round_hud(self, _game):
        self.round_hud_calls += 1

    def render_round_start_overlay(self, game):
        self.round_start_overlay_calls.append(game.get_current_round())

    def render_fps(self, _game, fps):
        self.fps_calls.append(fps)


class GameStub:
    def __init__(self, *, state, menu=None, landscape=None, entities=None, show_fps=False, current_round=1):
        self._game_state = state
        self._current_menu = menu
        self._landscape = landscape
        self._entity_list = list(entities or [])
        self._show_fps = show_fps
        self._current_round = current_round
        self.interface = InterfaceStub()
        self.font = FontStub()
        self.ui = GameUI(font_provider=lambda: self.font)
        self.visual_renderer = VisualRendererStub()
        self.hud_renderer = HudRendererStub()

    def get_game_state(self):
        return self._game_state

    def get_current_menu(self):
        return self._current_menu

    def get_landscape(self):
        return self._landscape

    def get_interface(self):
        return self.interface

    def get_current_round(self):
        return self._current_round

    def get_ui(self):
        return self.ui

    def get_visual_renderer(self):
        return self.visual_renderer

    def get_hud_renderer(self):
        return self.hud_renderer


class GameRendererTests(unittest.TestCase):
    def test_render_frame_draws_menu_and_fps_overlay(self):
        renderer = GameRenderer()
        menu = DrawStub()
        game = GameStub(state=GameState.MAIN_MENU, menu=menu, show_fps=True)

        renderer.render_frame(game, fps=87.5)

        self.assertEqual(game.interface.start_draw_calls, 1)
        self.assertEqual(game.interface.end_draw_calls, 1)
        self.assertEqual(menu.draw_calls, 1)
        self.assertEqual(game.hud_renderer.fps_calls, [87.5])

    def test_render_frame_draws_round_entities_and_round_start_overlay(self):
        renderer = GameRenderer()
        landscape = DrawStub()
        entities = [DrawStub(), DrawStub()]
        game = GameStub(
            state=GameState.ROUND_STARTING,
            landscape=landscape,
            entities=entities,
            current_round=4,
        )

        renderer.render_frame(game, fps=0.0)

        self.assertEqual(game.interface.start_draw_calls, 1)
        self.assertEqual(game.interface.end_draw_calls, 1)
        self.assertEqual(landscape.draw_calls, 1)
        self.assertEqual([entity.draw_calls for entity in entities], [1, 1])
        self.assertEqual(game.hud_renderer.round_hud_calls, 1)
        self.assertEqual(game.hud_renderer.round_start_overlay_calls, [4])

    def test_render_frame_prefers_visual_renderer_for_entities_with_render_state(self):
        renderer = GameRenderer()
        handled = DrawStub()
        fallback = DrawStub()
        game = GameStub(state=GameState.ROUND_IN_ACTION, landscape=DrawStub(), entities=[handled, fallback])
        game.visual_renderer.handled_ids.add(id(handled))

        renderer.render_frame(game, fps=0.0)

        self.assertEqual(game.visual_renderer.rendered_entities, [handled, fallback])
        self.assertEqual(handled.draw_calls, 0)
        self.assertEqual(fallback.draw_calls, 1)
        self.assertEqual(game.hud_renderer.round_hud_calls, 1)

    def test_render_frame_skips_round_overlay_for_active_rounds(self):
        renderer = GameRenderer()
        game = GameStub(state=GameState.ROUND_IN_ACTION, landscape=DrawStub(), entities=[DrawStub()])

        renderer.render_frame(game, fps=12.0)

        self.assertEqual(game.hud_renderer.round_start_overlay_calls, [])
        self.assertEqual(game.hud_renderer.fps_calls, [])


if __name__ == "__main__":
    unittest.main()
