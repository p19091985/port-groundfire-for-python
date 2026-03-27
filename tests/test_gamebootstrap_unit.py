import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.gamebootstrap import GameBootstrapper


class SettingsStub:
    def get_int(self, section, key, default):
        values = {
            ("Graphics", "ScreenWidth"): 1024,
            ("Graphics", "ScreenHeight"): 768,
            ("Graphics", "Fullscreen"): 1,
            ("Graphics", "ShowFPS"): 1,
        }
        return values.get((section, key), default)


class InterfaceStub:
    def __init__(self, width, height, fullscreen):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.defined_textures = None
        self.loaded_textures = []

    def define_textures(self, count):
        self.defined_textures = count

    def load_texture(self, filename, texture_id):
        self.loaded_textures.append((texture_id, Path(filename).name))
        return True


class ControlsFileStub:
    def __init__(self, controls, file_name):
        self.controls = controls
        self.file_name = file_name
        self.read_calls = 0

    def read_file(self):
        self.read_calls += 1


class FontStub:
    def __init__(self, interface, texture_id):
        self.interface = interface
        self.texture_id = texture_id


class SoundStub:
    def __init__(self, count):
        self.count = count
        self.loaded = []

    def load_sound(self, sound_id, file_name):
        self.loaded.append((sound_id, Path(file_name).name))


class FlowStub:
    def __init__(self):
        self.enter_calls = []

    def enter_state(self, game, new_state, prev_state):
        self.enter_calls.append((game, new_state, prev_state))
        game._current_menu = "main-menu"


class ClockStub:
    def __init__(self):
        self.reset_calls = 0

    def reset(self):
        self.reset_calls += 1


class GameStub:
    def __init__(self):
        self._clock = ClockStub()
        self._current_menu = None

    def get_clock(self):
        return self._clock


class GameBootstrapperTests(unittest.TestCase):
    def test_bootstrap_initializes_game_services_and_reads_static_settings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data = root / "data"
            data.mkdir()

            for name in ("blast.png", "fonts.png", "quake.wav"):
                (data / name).write_bytes(b"x")

            manifest = root / "assets.json"
            manifest.write_text(
                json.dumps(
                    {
                        "textures": [
                            {"id": 0, "key": "blast", "candidates": ["data/blast.png"]},
                            {"id": 3, "key": "font_atlas", "candidates": ["data/fonts.png"]},
                        ],
                        "sounds": [
                            {"id": 2, "key": "quake", "candidates": ["data/quake.wav"]},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            settings_loader = Mock(return_value=SettingsStub())
            controls_factory = Mock(return_value="controls")
            flow = FlowStub()
            reader = Mock()

            bootstrapper = GameBootstrapper(
                settings_loader=settings_loader,
                interface_factory=InterfaceStub,
                controls_factory=controls_factory,
                controls_file_factory=ControlsFileStub,
                font_factory=FontStub,
                sound_factory=SoundStub,
                audio_error_cls=RuntimeError,
                flow_controller=flow,
                project_root=root,
                asset_manifest_path=manifest,
                static_settings_readers=[reader],
            )
            game = GameStub()

            bootstrapper.bootstrap(game)

            settings_loader.assert_called_once_with("conf/options.ini")
            self.assertEqual((game._width, game._height, game._fullscreen), (1024, 768, True))
            self.assertEqual(game._show_fps, True)
            self.assertEqual(game._interface.defined_textures, 4)
            self.assertEqual(game._interface.loaded_textures, [(0, "blast.png"), (3, "fonts.png")])
            self.assertEqual(game._font.texture_id, 3)
            self.assertEqual(game._sound.loaded, [(2, "quake.wav")])
            self.assertEqual(game._controls, "controls")
            self.assertEqual(game._controls_file.file_name, "conf/controls.ini")
            self.assertEqual(game._controls_file.read_calls, 1)
            self.assertEqual(flow.enter_calls[0][1:], (1, 1))
            self.assertEqual(game._current_menu, "main-menu")
            self.assertEqual(game.get_clock().reset_calls, 1)
            reader.assert_called_once_with(game._settings)


if __name__ == "__main__":
    unittest.main()
