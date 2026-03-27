import unittest
from unittest.mock import patch

from tests.support import FlowPlayer, install_fake_pygame

install_fake_pygame()

import pygame

from src.commandintents import PlayerIntentFrame
import src.blast as blast_module
import src.entity as entity_module
import src.game as game_module
import src.humanplayer as humanplayer_module
import src.mirv as mirv_module
import src.missile as missile_module
import src.quake as quake_module
import src.trail as trail_module
import src.weapons_impl as weapons_impl_module
from src.common import GameState
from src.fixedstep import FixedStepRunner


class RecordingInterface:
    def __init__(self, width, height, fullscreen):
        self._width = width
        self._height = height
        self._fullscreen = fullscreen
        self._mouse_enabled = False
        self._window = pygame.Surface((width, height))
        self.defined_textures = None
        self.loaded_textures = []
        self.start_draw_calls = 0

    def define_textures(self, count):
        self.defined_textures = count

    def load_texture(self, filename, texture_id):
        self.loaded_textures.append((texture_id, filename))
        return True

    def enable_mouse(self, enable):
        self._mouse_enabled = enable

    def offset_viewport(self, _x, _y):
        return None

    def should_close(self):
        return False

    def start_draw(self):
        self.start_draw_calls += 1

    def end_draw(self):
        return None

    def get_key(self, _key):
        return False

    def game_to_screen(self, x, y):
        return (int(x), int(y))

    def scale_len(self, length):
        return int(length * 10)

    def get_window_settings(self):
        return (self._width, self._height, self._fullscreen)

    def get_texture_surface(self, _texture_id):
        return pygame.Surface((32, 32))

    def get_texture_image(self, _texture_id):
        return pygame.Surface((32, 32))

    def set_texture(self, _texture):
        return None


class FakeFont:
    printf_calls = []

    def __init__(self, _interface, _texture_id):
        return None

    def set_shadow(self, _value):
        return None

    def set_size(self, *_args):
        return None

    def set_colour(self, _colour):
        return None

    def print_centred_at(self, *_args):
        return None

    def print_at(self, *_args):
        return None

    def set_orientation(self, _value):
        return None

    def set_proportional(self, _value):
        return None

    def printf(self, *_args):
        FakeFont.printf_calls.append(_args)
        return None


class RecordingSound:
    def __init__(self, _count):
        self.loaded = []

    def load_sound(self, sound_id, file_name):
        self.loaded.append((sound_id, file_name))


class FakeControls:
    def __init__(self, _interface):
        return None


class FakeControlsFile:
    def __init__(self, _controls, _file_name):
        return None

    def read_file(self):
        return None

    def write_file(self):
        return None


class FakeMenu:
    def __init__(self, *_args, **_kwargs):
        return None

    def update(self, _time):
        return GameState.CURRENT_STATE

    def draw(self):
        return None


class FakeLandscape:
    created_count = 0

    def __init__(self, _settings, seed):
        self.seed = seed
        FakeLandscape.created_count += 1

    def update(self, _dt):
        return None

    def draw(self):
        return None

    def get_landscape_width(self):
        return 11.0

    def move_to_ground(self, _x, _y):
        return 0.0


class FakeQuake:
    @staticmethod
    def read_settings(_settings):
        return None

    def __init__(self, _game):
        self.pre_round_calls = 0

    def update(self, _time):
        return True

    def draw(self):
        return None

    def do_pre_round(self):
        self.pre_round_calls += 1
        return True

    def do_post_round(self):
        return False


class GameBootstrapTests(unittest.TestCase):
    def setUp(self):
        FakeLandscape.created_count = 0
        FakeFont.printf_calls = []
        self.patchers = [
            patch.object(game_module, "Interface", RecordingInterface),
            patch.object(game_module, "Font", FakeFont),
            patch.object(game_module, "Sound", RecordingSound),
            patch.object(game_module, "Controls", FakeControls),
            patch.object(game_module, "ControlsFile", FakeControlsFile),
            patch.object(game_module, "MainMenu", FakeMenu),
            patch.object(game_module, "PlayerMenu", FakeMenu),
            patch.object(game_module, "OptionMenu", FakeMenu),
            patch.object(game_module, "ShopMenu", FakeMenu),
            patch.object(game_module, "ScoreMenu", FakeMenu),
            patch.object(game_module, "QuitMenu", FakeMenu),
            patch.object(game_module, "WinnerMenu", FakeMenu),
            patch.object(game_module, "ControllerMenu", FakeMenu),
            patch.object(game_module, "SetControlsMenu", FakeMenu),
            patch.object(game_module, "Landscape", FakeLandscape),
            patch.object(game_module, "Quake", FakeQuake),
        ]

        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_game_reads_static_settings_and_loads_manifest_assets(self):
        with (
            patch.object(blast_module.Blast, "read_settings") as blast_read,
            patch.object(trail_module.Trail, "read_settings") as trail_read,
            patch.object(missile_module.Missile, "read_settings") as missile_read,
            patch.object(mirv_module.Mirv, "read_settings") as mirv_read,
            patch.object(weapons_impl_module.ShellWeapon, "read_settings") as shell_read,
            patch.object(weapons_impl_module.NukeWeapon, "read_settings") as nuke_read,
            patch.object(weapons_impl_module.MissileWeapon, "read_settings") as missile_weapon_read,
            patch.object(weapons_impl_module.MirvWeapon, "read_settings") as mirv_weapon_read,
            patch.object(weapons_impl_module.MachineGunWeapon, "read_settings") as machinegun_read,
        ):
            game = game_module.Game()

        self.assertIsNone(game.get_landscape())
        self.assertIsNotNone(game.get_graphics())
        self.assertEqual(game.get_interface().defined_textures, 12)
        self.assertEqual(len(game.get_interface().loaded_textures), 12)
        self.assertEqual(len(game.get_sound().loaded), 10)

        for mocked_reader in (
            blast_read,
            trail_read,
            missile_read,
            mirv_read,
            shell_read,
            nuke_read,
            missile_weapon_read,
            mirv_weapon_read,
            machinegun_read,
        ):
            mocked_reader.assert_called_once_with(game.get_settings())

    def test_round_start_creates_landscape_once_and_round_start_draw_clears_once(self):
        game = game_module.Game()
        
        class RoundTank:
            def __init__(self):
                self.position_calls = []

            def alive(self):
                return True

            def do_pre_round(self):
                return True

            def do_post_round(self):
                return True

            def set_position_on_ground(self, x):
                self.position_calls.append(x)

            def update(self, _dt):
                return True

            def draw(self):
                return None

        class RoundPlayer:
            def __init__(self, name):
                self._name = name
                self._tank = RoundTank()
                self.new_round_calls = 0

            def get_tank(self):
                return self._tank

            def new_round(self):
                self.new_round_calls += 1

            def end_round(self):
                return None

        players = [RoundPlayer("P1"), RoundPlayer("P2")]
        game._players = players + [None] * 6
        game._number_of_players = len(players)
        game._entity_list = [player.get_tank() for player in players]

        game._change_state(GameState.ROUND_STARTING)
        self.assertEqual(FakeLandscape.created_count, 1)
        self.assertEqual(game.get_current_round(), 1)
        self.assertEqual(game.get_time(), 0.0)

        game._new_state = GameState.CURRENT_STATE
        game.get_interface().start_draw_calls = 0
        game.loop_once()
        self.assertEqual(game.get_interface().start_draw_calls, 1)

    def test_human_player_command_accepts_optional_timestamp_reference(self):
        class StubControls:
            def __init__(self):
                self.calls = []

            def get_command(self, controller, command):
                self.calls.append((controller, command))
                return True

        controls = StubControls()
        player = humanplayer_module.HumanPlayer.__new__(humanplayer_module.HumanPlayer)
        player._controller = 3
        player._controls = controls

        self.assertTrue(player.get_command(7))
        timestamp = [1.0]
        self.assertTrue(player.get_command(8, timestamp))
        self.assertEqual(timestamp[0], 0.0)
        self.assertEqual(controls.calls, [(3, 7), (3, 8)])

    def test_menu_loop_updates_flow_and_renders_menu_once(self):
        class RecordingMenu:
            def __init__(self):
                self.update_calls = []
                self.draw_calls = 0

            def update(self, dt):
                self.update_calls.append(dt)
                return GameState.CURRENT_STATE

            def draw(self):
                self.draw_calls += 1

        game = game_module.Game()
        menu = RecordingMenu()
        game._current_menu = menu
        game._game_state = GameState.MAIN_MENU
        game._new_state = GameState.CURRENT_STATE
        game.get_interface().start_draw_calls = 0

        game.loop_once()

        self.assertEqual(len(menu.update_calls), 1)
        self.assertEqual(menu.draw_calls, 1)
        self.assertEqual(game.get_interface().start_draw_calls, 1)

    def test_injected_time_source_clamps_frame_time_and_resets_on_round_start(self):
        class FakeTimeSource:
            def __init__(self, values):
                self._values = list(values)
                self._last = self._values[-1]

            def __call__(self):
                if self._values:
                    self._last = self._values.pop(0)
                return self._last

        time_source = FakeTimeSource([100.0, 100.4, 200.0, 200.05])
        game = game_module.Game(time_source=time_source)

        game.loop_once()
        self.assertAlmostEqual(game.get_time(), 0.1)

        game._change_state(GameState.ROUND_STARTING)
        self.assertEqual(game.get_time(), 0.0)
        self.assertEqual(game.get_landscape().seed, 200.0)

        game._new_state = GameState.CURRENT_STATE
        game.loop_once()
        self.assertAlmostEqual(game.get_time(), 0.05)

    def test_round_uses_fixed_substeps_and_preserves_accumulator_between_frames(self):
        class FakeTimeSource:
            def __init__(self, values):
                self._values = list(values)
                self._last = self._values[-1]

            def __call__(self):
                if self._values:
                    self._last = self._values.pop(0)
                return self._last

        class StepEntity:
            def __init__(self):
                self.update_calls = []

            def do_pre_round(self):
                return True

            def do_post_round(self):
                return True

            def update(self, dt):
                self.update_calls.append(dt)
                return True

            def draw(self):
                return None

        time_source = FakeTimeSource([1.0, 1.03, 1.04])
        stepper = FixedStepRunner(step=0.02, max_substeps=8)
        game = game_module.Game(time_source=time_source, round_stepper=stepper)
        entity = StepEntity()

        game._game_state = GameState.ROUND_IN_ACTION
        game._new_state = GameState.CURRENT_STATE
        game._entity_list = [entity]

        game.loop_once()
        self.assertEqual(entity.update_calls, [0.02])
        self.assertAlmostEqual(game.get_time(), 0.02)

        game._new_state = GameState.CURRENT_STATE
        game.loop_once()
        self.assertEqual(entity.update_calls, [0.02, 0.02])
        self.assertAlmostEqual(game.get_time(), 0.04)

    def test_round_starting_countdown_advances_in_fixed_steps(self):
        class FakeTimeSource:
            def __init__(self, values):
                self._values = list(values)
                self._last = self._values[-1]

            def __call__(self):
                if self._values:
                    self._last = self._values.pop(0)
                return self._last

        class RoundTank:
            def alive(self):
                return True

            def do_pre_round(self):
                return True

            def do_post_round(self):
                return True

            def set_position_on_ground(self, _x):
                return None

            def update(self, _dt):
                return True

            def draw(self):
                return None

        class RoundPlayer:
            def __init__(self):
                self._tank = RoundTank()

            def get_tank(self):
                return self._tank

            def new_round(self):
                return None

            def end_round(self):
                return None

        time_source = FakeTimeSource([5.0, 6.0, 6.02])
        stepper = FixedStepRunner(step=0.02, max_substeps=8)
        game = game_module.Game(time_source=time_source, round_stepper=stepper)
        game._players = [RoundPlayer(), None, None, None, None, None, None, None]
        game._number_of_players = 1
        game._entity_list = [game._players[0].get_tank()]

        game._change_state(GameState.ROUND_STARTING)
        game._state_countdown = 0.01
        game._new_state = GameState.CURRENT_STATE

        game.loop_once()
        self.assertEqual(game.get_game_state(), GameState.ROUND_IN_ACTION)

    def test_game_assigns_entity_ids_and_builds_network_snapshot(self):
        class MarkerEntity(entity_module.Entity):
            def draw(self):
                return None

            def update(self, _dt):
                return True

        game = game_module.Game()
        marker = MarkerEntity(game)

        game.add_entity(marker)
        snapshot = game.build_match_snapshot()

        self.assertIsNotNone(marker.get_entity_id())
        self.assertEqual(snapshot.entities[-1].entity_id, marker.get_entity_id())
        self.assertEqual(snapshot.events[-1].event_type, "entity_added")

    def test_game_builds_command_and_snapshot_envelopes(self):
        class TankStub:
            def __init__(self):
                self._entity_id = 123

            def get_entity_id(self):
                return self._entity_id

        class PlayerStub:
            def __init__(self):
                self._frames = [PlayerIntentFrame.from_iterable([True], source="human:0", simulation_time=1.5)]
                self._current = self._frames[-1]
                self._tank = TankStub()

            def drain_intent_frames(self):
                frames = tuple(self._frames)
                self._frames.clear()
                return frames

            def get_current_intents(self):
                return self._current

            def get_name(self):
                return "P1"

            def get_score(self):
                return 10

            def get_money(self):
                return 20

            def is_computer(self):
                return False

            def get_tank(self):
                return self._tank

        game = game_module.Game()
        game._players = [PlayerStub(), None, None, None, None, None, None, None]
        game._number_of_players = 1
        game.queue_network_event("round_started", round=1)

        command_envelopes = game.drain_command_envelopes()
        snapshot_envelope = game.build_snapshot_envelope()

        self.assertEqual(len(command_envelopes), 1)
        self.assertEqual(command_envelopes[0].commands["fire"], True)
        self.assertEqual(snapshot_envelope.snapshot_sequence, 1)
        self.assertEqual(snapshot_envelope.acknowledged_command_sequences, {0: 1})
        self.assertEqual(game.get_pending_network_events(), ())


if __name__ == "__main__":
    unittest.main()
