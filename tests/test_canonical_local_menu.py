import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.gameui import GameUI
from src.groundfire.core.settings import ReadIniFile
from src.groundfire.ui.menus import CanonicalLocalMenu


class FontStub:
    def __init__(self):
        self.centred_calls = []
        self.text_calls = []

    def set_shadow(self, _value):
        return None

    def set_proportional(self, _value):
        return None

    def set_orientation(self, _value):
        return None

    def set_size(self, *_args):
        return None

    def set_colour(self, _colour):
        return None

    def print_centred_at(self, *args):
        self.centred_calls.append(args)

    def print_at(self, *args):
        self.text_calls.append(args)

    def printf(self, *args):
        return None

    def find_string_length(self, text):
        return max(1.0, len(text) * 0.18)


class GraphicsStub:
    def fill_screen(self, *_args, **_kwargs):
        return None

    def draw_tiled_texture(self, *_args, **_kwargs):
        return None

    def draw_texture_world_rect(self, *_args, **_kwargs):
        return None

    def draw_world_rect(self, *_args, **_kwargs):
        return None

    def draw_world_polygon(self, *_args, **_kwargs):
        return None


class InterfaceStub:
    def __init__(self, *, width=1024, height=768, fullscreen=False):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.change_calls = []

    def get_window_settings(self):
        return self.width, self.height, self.fullscreen

    def get_texture_surface(self, _texture_id):
        return None

    def get_mouse_pos(self):
        return (99.0, 99.0)

    def change_window(self, width, height, fullscreen):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.change_calls.append((width, height, fullscreen))


class MenuGameStub:
    def __init__(self, settings_path: Path):
        self.font = FontStub()
        self.ui = GameUI(font_provider=lambda: self.font)
        self.graphics = GraphicsStub()
        self.interface = InterfaceStub()
        self._settings_path = settings_path
        self._settings = ReadIniFile(str(settings_path))

    def get_ui(self):
        return self.ui

    def get_graphics(self):
        return self.graphics

    def get_interface(self):
        return self.interface

    def get_settings(self):
        return self._settings

    def get_settings_path(self):
        return self._settings_path


class CanonicalLocalMenuTests(unittest.TestCase):
    def test_draws_classic_main_menu_screen(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)

            menu._draw_screen(game, state, player_name="Alice")

            texts = [call[2] for call in game.font.centred_calls]
            self.assertIn("Start Game", texts)
            self.assertIn("Options", texts)
            self.assertIn("Quit", texts)
            self.assertIn("0.25 (Python Port)", texts)

    def test_draws_classic_options_screen(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "options"

            menu._draw_screen(game, state, player_name="Alice")

            centred_texts = [call[2] for call in game.font.centred_calls]
            self.assertIn("Options", centred_texts)
            self.assertIn("Resolution:", centred_texts)
            self.assertIn("Screen Mode:", centred_texts)
            self.assertIn("Set Controls", centred_texts)
            self.assertIn("Apply", centred_texts)
            self.assertIn("Back", centred_texts)

    def test_draws_classic_select_players_screen(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=2)
            state.screen = "select_players"

            menu._draw_screen(game, state, player_name="Alice")

            centred_texts = [call[2] for call in game.font.centred_calls]
            left_texts = [call[2] for call in game.font.text_calls]
            self.assertIn("Select Players", centred_texts)
            self.assertIn("Controlled by", centred_texts)
            self.assertIn("Rounds :", centred_texts)
            self.assertIn("Start!", centred_texts)
            self.assertIn("Back", centred_texts)
            self.assertIn("Player 1", left_texts)
            self.assertIn("Keyboard1", centred_texts)

    def test_draws_classic_quit_confirmation_screen(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "quit"

            menu._draw_screen(game, state, player_name="Alice")

            texts = [call[2] for call in game.font.centred_calls]
            self.assertIn("Are you sure?", texts)
            self.assertIn("Yes", texts)
            self.assertIn("No", texts)

    def test_apply_options_updates_window_and_persists_settings(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.resolution_index = 2
            state.fullscreen = True

            menu._apply_options(game, state)

            self.assertEqual(game.interface.change_calls, [(1024, 768, True)])
            settings_text = game.get_settings_path().read_text(encoding="utf-8")
            self.assertIn("ScreenWidth=1024", settings_text)
            self.assertIn("ScreenHeight=768", settings_text)
            self.assertIn("Fullscreen=1", settings_text)

    def test_set_controls_routes_to_classic_controller_menu(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "options"

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["set_controls"]
            selection = menu._handle_click(game, state, rects, (left + right) / 2.0, (top + bottom) / 2.0)

            self.assertIsNotNone(selection)
            self.assertEqual(selection.action, "classic")
            self.assertEqual(selection.launch_target, "controllers")
            self.assertFalse(selection.persist_mode)

    def test_multi_human_start_falls_back_to_classic_runtime(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "select_players"
            state.players[1].is_human = True
            state.players[1].controller = 1

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["start"]
            selection = menu._handle_click(game, state, rects, (left + right) / 2.0, (top + bottom) / 2.0)

            self.assertIsNotNone(selection)
            self.assertEqual(selection.action, "classic")
            self.assertEqual(selection.launch_target, "configured_start")
            self.assertFalse(selection.persist_mode)

    def _make_game(self, temp_dir: Path) -> MenuGameStub:
        settings_path = temp_dir / "options.ini"
        settings_path.write_text(
            "[Graphics]\nScreenWidth=640\nScreenHeight=480\nFullscreen=0\n",
            encoding="utf-8",
        )
        return MenuGameStub(settings_path)


if __name__ == "__main__":
    unittest.main()
