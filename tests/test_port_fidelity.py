import math
import os
import unittest
from unittest.mock import patch

from src.common import PI, deg_cos, deg_sin, sqr
from src.inifile import ReadIniFile
from src.machinegunround import MachineGunRound
from src.mirv import Mirv
from src.missile import Missile
from src.player import Player
from src.shell import Shell
from src.soundentity import SoundEntity
from src.tank import Tank
from src.weapons_impl import MachineGunWeapon
from tests.support import (
    PROJECT_ROOT,
    CommandPlayer,
    DummyGameForTank,
    RecordingWeapon,
)

SETTINGS = ReadIniFile(os.path.join(PROJECT_ROOT, "conf", "options.ini"))


class TankFidelityTests(unittest.TestCase):
    def setUp(self):
        self.player = CommandPlayer()
        self.game = DummyGameForTank(SETTINGS)
        self.tank = Tank(self.game, self.player, 0)
        self.player._tank = self.tank

    def test_common_math_matches_cpp_formulas(self):
        self.assertAlmostEqual(PI, 3.141592654)
        self.assertAlmostEqual(sqr(-3.5), 12.25)
        self.assertAlmostEqual(deg_cos(60.0), math.cos((60.0 / 180.0) * PI))
        self.assertAlmostEqual(deg_sin(-45.0), math.sin((-45.0 / 180.0) * PI))

    def test_get_centre_and_gun_launch_match_cpp(self):
        self.tank._x = 5.0
        self.tank._y = 2.0
        self.tank._tank_angle = 30.0
        self.tank._gun_angle = -20.0
        self.tank._gun_power = 12.0
        self.tank._airbourne_x_vel = 1.5
        self.tank._airbourne_y_vel = -0.5

        angle_rads = (self.tank._tank_angle / 180.0) * PI
        expected_cx = 5.0 - math.sin(angle_rads) * (self.tank._tank_size / 2.0)
        expected_cy = 2.0 + math.cos(angle_rads) * (self.tank._tank_size / 2.0)

        cx, cy, hit_range = self.tank.get_centre()
        self.assertAlmostEqual(cx, expected_cx)
        self.assertAlmostEqual(cy, expected_cy)
        self.assertAlmostEqual(hit_range, self.tank._tank_size * 0.75)

        launch_x, launch_y = self.tank.gun_launch_position()
        self.assertAlmostEqual(launch_x, cx + (-deg_sin(-20.0) * self.tank._tank_size * 1.2))
        self.assertAlmostEqual(launch_y, cy + (deg_cos(-20.0) * self.tank._tank_size * 1.2))

        vel_x, vel_y = self.tank.gun_launch_velocity()
        self.assertAlmostEqual(vel_x, 1.5 - deg_sin(-20.0) * 12.0)
        self.assertAlmostEqual(vel_y, -0.5 + deg_cos(-20.0) * 12.0)

    def test_machine_gun_launch_velocity_uses_fixed_weapon_speed(self):
        # Fidelity target: MachineGunWeapon.update() uses
        # gun_launch_velocity_at_power(MachineGunWeapon.OPTION_Speed).
        #
        # Machine Gun rounds ignore the tank's current gun power; the weapon has
        # its own fixed classic speed.
        weapon = self.tank._weapons[Tank.MACHINEGUN]
        weapon._quantity = 1
        weapon._available_quantity = 1
        weapon._cooldown = 0.0
        self.tank._firing = True
        self.tank._gun_angle = -20.0
        self.tank._airbourne_x_vel = 1.5
        self.tank._airbourne_y_vel = -0.5
        self.tank._gun_power = 1.0

        weapon.update(0.05)

        self.assertEqual(len(self.game._entities), 1)
        low_power_round = self.game._entities[0]
        expected_x = 1.5 - deg_sin(-20.0) * MachineGunWeapon.OPTION_Speed
        expected_y = -0.5 + deg_cos(-20.0) * MachineGunWeapon.OPTION_Speed
        self.assertAlmostEqual(low_power_round._x_launch_vel, expected_x)
        self.assertAlmostEqual(low_power_round._y_launch_vel, expected_y)

        self.game._entities.clear()
        weapon._quantity = 1
        weapon._available_quantity = 1
        weapon._cooldown = 0.0
        self.tank._gun_power = 20.0

        weapon.update(0.05)

        self.assertEqual(len(self.game._entities), 1)
        high_power_round = self.game._entities[0]
        self.assertAlmostEqual(high_power_round._x_launch_vel, expected_x)
        self.assertAlmostEqual(high_power_round._y_launch_vel, expected_y)

    def test_machine_gun_round_trajectory_uses_classic_gravity(self):
        # Fidelity target: MachineGunRound.update() uses the same classic
        # parabolic y formula as Shell.update(), including the 5.0 * t^2 term.
        self.game.get_players = lambda: []
        machine_gun_round = MachineGunRound(
            self.game,
            self.player,
            1.0,
            2.0,
            3.0,
            4.0,
            0.25,
            2,
        )

        self.game.set_time(0.75)

        self.assertTrue(machine_gun_round.update(0.05))
        time_since_launch = 0.5
        t_back = 0.49
        self.assertAlmostEqual(machine_gun_round._x, 1.0 + time_since_launch * 3.0)
        self.assertAlmostEqual(
            machine_gun_round._y,
            2.0 + time_since_launch * (4.0 - 5.0 * time_since_launch),
        )
        self.assertAlmostEqual(machine_gun_round._x_back, 1.0 + t_back * 3.0)
        self.assertAlmostEqual(
            machine_gun_round._y_back,
            2.0 + t_back * (4.0 - 5.0 * t_back),
        )

    def test_machine_gun_round_tank_hit_queues_classic_metal_sound(self):
        # Fidelity target: MachineGunRound.update() queues SoundEntity(..., 9,
        # False) for the classic metal clang before applying direct tank damage.
        game = self.game

        class HitTank:
            def __init__(self):
                self.damage_calls = []
                self.sound_seen_before_damage = False

            def intersect_tank(self, _old_x, _old_y, _x, _y):
                return True

            def do_damage(self, damage):
                self.sound_seen_before_damage = any(
                    isinstance(entity, SoundEntity)
                    and entity._sound is not None
                    and entity._sound._sound_id == 9
                    for entity in game._entities
                )
                self.damage_calls.append(damage)
                return False

        class HitPlayer:
            def __init__(self, tank):
                self._tank = tank

            def get_tank(self):
                return self._tank

        target_tank = HitTank()
        target_player = HitPlayer(target_tank)
        self.game.get_players = lambda: [target_player]
        machine_gun_round = MachineGunRound(
            self.game,
            self.player,
            1.0,
            2.0,
            3.0,
            4.0,
            0.25,
            2,
        )

        self.game.set_time(0.75)

        self.assertTrue(machine_gun_round.update(0.05))
        self.assertTrue(machine_gun_round._kill_next_frame)
        self.assertEqual(target_tank.damage_calls, [2])
        self.assertTrue(target_tank.sound_seen_before_damage)
        sound_entities = [
            entity for entity in self.game._entities if isinstance(entity, SoundEntity)
        ]
        self.assertEqual(len(sound_entities), 1)
        self.assertEqual(sound_entities[0]._sound._sound_id, 9)
        self.assertFalse(sound_entities[0]._looping)
        self.assertFalse(sound_entities[0]._sound._looping)

    def test_mirv_vertical_split_does_not_add_minimum_horizontal_spread(self):
        # Fidelity target: Mirv.update() fragment spread formula.
        #
        # Classic fragment x velocity is based only on the MIRV's launch x
        # velocity. A vertical launch therefore does not inject fan-out speed.
        original_fragments = Mirv.OPTION_Fragments
        original_spread = Mirv.OPTION_Spread
        Mirv.OPTION_Fragments = 5
        Mirv.OPTION_Spread = 0.2
        try:
            mirv = Mirv(
                self.game,
                self.player,
                1.0,
                2.0,
                0.0,
                10.0,
                0.0,
                0.3,
                20.0,
            )
            self.game.set_time(1.1)

            self.assertFalse(mirv.update(0.05))
            fragments = [entity for entity in self.game._entities if isinstance(entity, Shell)]
            self.assertEqual(len(fragments), 5)
            self.assertTrue(all(fragment._x_launch_vel == 0.0 for fragment in fragments))
            self.assertTrue(all(fragment._y_launch_vel == 0.0 for fragment in fragments))
        finally:
            Mirv.OPTION_Fragments = original_fragments
            Mirv.OPTION_Spread = original_spread

    def test_missile_powered_flight_uses_classic_angle_speed_formula(self):
        # Fidelity target: Missile.update() powered-flight branch.
        #
        # Classic missiles are driven by angle and
        # Missile.OPTION_Speed - cos(angle) while fuel remains.
        self.game.get_players = lambda: []
        missile = Missile(self.game, self.player, 1.0, 2.0, 30.0, 0.3, 40.0)

        self.assertTrue(missile.update(0.2))

        radians = math.radians(30.0)
        speed_factor = Missile.OPTION_Speed - math.cos(radians)
        self.assertAlmostEqual(missile._x, 1.0 - math.sin(radians) * speed_factor * 0.2)
        self.assertAlmostEqual(missile._y, 2.0 + math.cos(radians) * speed_factor * 0.2)
        self.assertAlmostEqual(missile._fuel, Missile.OPTION_FuelSupply - 0.2)
        self.assertAlmostEqual(missile._x_vel, 0.0)
        self.assertAlmostEqual(missile._y_vel, 0.0)

    def test_missile_powered_flight_does_not_clamp_low_speed_factor(self):
        # Fidelity target: Missile.update() powered-flight speed factor.
        #
        # The classic formula uses Missile.OPTION_Speed - cos(angle) directly,
        # even when that produces a negative powered velocity.
        original_speed = Missile.OPTION_Speed
        try:
            Missile.OPTION_Speed = 0.25
            self.game.get_players = lambda: []
            missile = Missile(self.game, self.player, 1.0, 2.0, 0.0, 0.3, 40.0)

            self.assertTrue(missile.update(0.2))

            speed_factor = Missile.OPTION_Speed - math.cos(0.0)
            self.assertLess(speed_factor, 0.0)
            self.assertAlmostEqual(missile._x, 1.0)
            self.assertAlmostEqual(missile._y, 2.0 + speed_factor * 0.2)
        finally:
            Missile.OPTION_Speed = original_speed

    def test_missile_exhaustion_starts_freefall_after_powered_frame(self):
        # Fidelity target: Missile.update() fuel exhaustion ordering.
        #
        # Classic missiles finish the current update with powered-flight motion,
        # then store that powered velocity for the later free-fall branch.
        self.game.get_players = lambda: []
        missile = Missile(self.game, self.player, 1.0, 2.0, 0.0, 0.3, 40.0)
        missile._fuel = 0.05

        self.assertTrue(missile.update(0.1))

        powered_speed = Missile.OPTION_Speed - math.cos(0.0)
        self.assertAlmostEqual(missile._x, 1.0)
        self.assertAlmostEqual(missile._y, 2.0 + powered_speed * 0.1)
        self.assertAlmostEqual(missile._fuel, -0.05)
        self.assertAlmostEqual(missile._x_vel, 0.0)
        self.assertAlmostEqual(missile._y_vel, powered_speed)

    def test_projectile_explosions_use_classic_death_sound_ids(self):
        # Fidelity target: Shell.explode()/Missile.explode() sound id routing.
        #
        # Classic shell/MIRV explosions use sound 1, missile death uses sound 6,
        # and whiteout shell explosions, used by Nukes, use sound 7.
        shell = Shell(self.game, self.player, 0.0, 0.0, 1.0, 1.0, 0.0, 0.25, 40.0, False)
        shell.explode(1.0, 2.0, -1)
        self.assertEqual(self.game._explosions[-1][5], 1)
        self.assertFalse(self.game._explosions[-1][6])

        nuke_shell = Shell(self.game, self.player, 0.0, 0.0, 1.0, 1.0, 0.0, 3.0, 90.0, True)
        nuke_shell.explode(2.0, 3.0, -1)
        self.assertEqual(self.game._explosions[-1][5], 7)
        self.assertTrue(self.game._explosions[-1][6])

        missile = Missile(self.game, self.player, 0.0, 0.0, 0.0, 0.3, 40.0)
        self.assertFalse(missile.explode(3.0, 4.0, -1))
        self.assertEqual(self.game._explosions[-1][5], 6)
        self.assertFalse(self.game._explosions[-1][6])

    def test_do_damage_keeps_tank_alive_at_exactly_zero(self):
        self.tank._health = 40.0
        self.assertFalse(self.tank.do_damage(40.0))
        self.assertEqual(self.tank._state, Tank.TANK_ALIVE)
        self.assertEqual(self.game._recorded_tank_deaths, 0)

        self.assertTrue(self.tank.do_damage(0.1))
        self.assertEqual(self.tank._state, Tank.TANK_DEAD)
        self.assertEqual(self.game._recorded_tank_deaths, 1)

    def test_do_pre_round_resets_cpp_state(self):
        self.tank._state = Tank.TANK_DEAD
        self.tank._gun_angle = 9.0
        self.tank._gun_angle_change_speed = 4.0
        self.tank._gun_power = 18.0
        self.tank._gun_power_change_speed = 7.0
        self.tank._tank_angle = 12.0
        self.tank._airbourne_x_vel = 3.0
        self.tank._airbourne_y_vel = 4.0
        self.tank._on_ground = True
        self.tank._health = 5.0
        self.tank._exhaust_time = -0.5
        self.tank._total_fuel = 2.0
        self.tank._fuel = 0.1
        self.tank._selected_weapon = Tank.MISSILES
        self.tank._switch_weapon_time = 1.0
        self.tank._firing = True

        weapons = [RecordingWeapon() for _ in range(Tank.MAX_WEAPONS)]
        self.tank._weapons = weapons

        self.assertTrue(self.tank.do_pre_round())
        self.assertEqual(self.tank._state, Tank.TANK_ALIVE)
        self.assertEqual(self.tank._gun_angle, 0.0)
        self.assertEqual(self.tank._gun_angle_change_speed, 0.0)
        self.assertEqual(self.tank._gun_power, 10.0)
        self.assertEqual(self.tank._gun_power_change_speed, 0.0)
        self.assertEqual(self.tank._tank_angle, 0.0)
        self.assertEqual(self.tank._airbourne_x_vel, 0.0)
        self.assertEqual(self.tank._airbourne_y_vel, 0.0)
        self.assertFalse(self.tank._on_ground)
        self.assertEqual(self.tank._health, self.tank._max_health)
        self.assertEqual(self.tank._exhaust_time, 0.0)
        self.assertEqual(self.tank._fuel, 1.0)
        self.assertEqual(self.tank._selected_weapon, Tank.SHELLS)
        self.assertEqual(self.tank._switch_weapon_time, 0.0)
        self.assertFalse(self.tank._firing)
        self.assertEqual(weapons[Tank.SHELLS].select_calls, 1)
        self.assertTrue(all(weapon.ammo_round_calls == 1 for weapon in weapons))

    def test_move_tank_passive_steep_slope_slide_matches_classic_direction(self):
        # Fidelity target: Tank.move_tank() passive slope branch.
        #
        # With no left/right input, a tank resting on a slope steeper than 30
        # degrees slides by the classic signed angle term. Positive tank angle
        # moves left; negative tank angle moves right.
        self.tank._state = Tank.TANK_ALIVE
        self.tank._on_ground = True
        self.tank._x = 1.0
        self.tank._y = 2.0
        self.tank._tank_angle = 31.0

        self.tank.move_tank(1.0, False)

        expected_positive_delta = -(self.tank._movement_speed * (31.0 / 65.0))
        self.assertAlmostEqual(self.tank._x, 1.0 + math.cos(math.radians(31.0)) * expected_positive_delta)
        self.assertAlmostEqual(self.tank._y, 2.0 + math.sin(math.radians(31.0)) * expected_positive_delta)

        self.tank._x = 1.0
        self.tank._y = 2.0
        self.tank._tank_angle = -31.0

        self.tank.move_tank(1.0, False)

        expected_negative_delta = -(self.tank._movement_speed * (-31.0 / 65.0))
        self.assertAlmostEqual(self.tank._x, 1.0 + math.cos(math.radians(-31.0)) * expected_negative_delta)
        self.assertAlmostEqual(self.tank._y, 2.0 + math.sin(math.radians(-31.0)) * expected_negative_delta)

    def test_move_tank_ground_input_combines_with_signed_slope_term(self):
        # Fidelity target: Tank.move_tank() grounded left/right branch.
        #
        # Classic grounded movement does not merely slow both directions on a
        # slope. It adds the player's input term and the signed slope-slide term,
        # so moving downhill is faster than moving uphill on the same slope.
        self.tank._state = Tank.TANK_ALIVE
        self.tank._on_ground = True
        self.tank._x = 1.0
        self.tank._y = 2.0
        self.tank._tank_angle = 31.0
        self.tank._fuel = 0.5
        self.tank._total_fuel = 0.5

        self.player.commands = {Tank.CMD_TANKRIGHT: True}
        self.tank.move_tank(1.0, False)

        right_delta = self.tank._movement_speed - (self.tank._movement_speed * (31.0 / 65.0))
        self.assertAlmostEqual(self.tank._x, 1.0 + math.cos(math.radians(31.0)) * right_delta)
        self.assertAlmostEqual(self.tank._y, 2.0 + math.sin(math.radians(31.0)) * right_delta)
        self.assertAlmostEqual(self.tank._fuel, 0.5)
        self.assertAlmostEqual(self.tank._total_fuel, 0.5)

        self.tank._x = 1.0
        self.tank._y = 2.0
        self.player.commands = {Tank.CMD_TANKLEFT: True}
        self.tank.move_tank(1.0, False)

        left_delta = -self.tank._movement_speed - (self.tank._movement_speed * (31.0 / 65.0))
        self.assertAlmostEqual(self.tank._x, 1.0 + math.cos(math.radians(31.0)) * left_delta)
        self.assertAlmostEqual(self.tank._y, 2.0 + math.sin(math.radians(31.0)) * left_delta)

    def test_move_tank_airborne_without_boost_ignores_lateral_input(self):
        # Fidelity target: Tank.move_tank() airborne non-boost branch.
        #
        # Classic left/right commands only affect grounded movement or boost
        # rotation. Once airborne without boost, the tank follows stored velocity
        # and gravity; lateral input does not add air control or spend fuel.
        self.tank._state = Tank.TANK_ALIVE
        self.tank._on_ground = False
        self.tank._x = 1.0
        self.tank._y = 2.0
        self.tank._tank_angle = 12.0
        self.tank._airbourne_x_vel = 0.3
        self.tank._airbourne_y_vel = -0.4
        self.tank._fuel = 0.5
        self.tank._total_fuel = 0.5
        self.player.commands = {Tank.CMD_TANKRIGHT: True}

        self.tank.move_tank(0.5, False)

        expected_y_velocity = -0.4 - self.tank._tank_gravity * 0.5
        self.assertAlmostEqual(self.tank._airbourne_x_vel, 0.3)
        self.assertAlmostEqual(self.tank._airbourne_y_vel, expected_y_velocity)
        self.assertAlmostEqual(self.tank._x, 1.0 + 0.3 * 0.5)
        self.assertAlmostEqual(self.tank._y, 2.0 + expected_y_velocity * 0.5)
        self.assertAlmostEqual(self.tank._tank_angle, 12.0)
        self.assertAlmostEqual(self.tank._fuel, 0.5)
        self.assertAlmostEqual(self.tank._total_fuel, 0.5)

    def test_update_aligns_tank_tracks_using_classic_support_displacements(self):
        # Fidelity target: Tank.update() track-ground support branch.
        #
        # The classic tank does not simply copy a center slope value. It probes
        # left, center, and right track support through Landscape.move_to_ground,
        # then rotates by the bounded relative support displacement.
        class TrackStepLandscape:
            left_ground_y = 0.0
            mid_ground_y = 0.0
            right_ground_y = -0.06

            def move_to_ground(self, x, _y):
                if x < -0.01:
                    return self.left_ground_y
                if x > 0.01:
                    return self.right_ground_y
                return self.mid_ground_y

        landscape = TrackStepLandscape()
        self.game._landscape = landscape
        self.tank._state = Tank.TANK_ALIVE
        self.tank._on_ground = True
        self.tank._x = 0.0
        self.tank._y = 0.0
        self.tank._tank_angle = 0.0

        self.tank.update(0.0)

        self.assertTrue(self.tank._on_ground)
        self.assertAlmostEqual(self.tank._y, 0.0)
        self.assertAlmostEqual(self.tank._tank_angle, -4.5)

        landscape.left_ground_y = -0.06
        landscape.mid_ground_y = -0.06
        landscape.right_ground_y = -0.06
        self.tank._on_ground = True
        self.tank._x = 0.0
        self.tank._y = 0.0
        self.tank._tank_angle = 0.0

        self.tank.update(0.0)

        self.assertFalse(self.tank._on_ground)
        self.assertAlmostEqual(self.tank._y, 0.0)
        self.assertAlmostEqual(self.tank._tank_angle, 0.0)

    def test_update_gun_requires_release_before_second_shot(self):
        weapons = [RecordingWeapon() for _ in range(Tank.MAX_WEAPONS)]
        self.tank._weapons = weapons
        self.tank._selected_weapon = Tank.SHELLS

        self.player.commands = {Tank.CMD_FIRE: True}
        self.tank.update_gun(0.1)
        self.tank.update_gun(0.1)

        self.assertEqual(weapons[Tank.SHELLS].fire_calls, [(True, 0.0)])
        self.assertTrue(self.tank.is_firing())

        self.player.commands = {Tank.CMD_FIRE: False}
        self.tank.update_gun(0.1)
        self.assertEqual(weapons[Tank.SHELLS].fire_calls[-1], (False, 0.0))
        self.assertFalse(self.tank.is_firing())

        self.player.commands = {Tank.CMD_FIRE: True}
        self.tank.update_gun(0.1)
        self.assertEqual(
            weapons[Tank.SHELLS].fire_calls,
            [(True, 0.0), (False, 0.0), (True, 0.0)],
        )

    def test_update_gun_reselects_shell_when_weapon_runs_out(self):
        weapons = [RecordingWeapon() for _ in range(Tank.MAX_WEAPONS)]
        weapons[Tank.MISSILES] = RecordingWeapon([False])
        self.tank._weapons = weapons
        self.tank._selected_weapon = Tank.MISSILES

        self.player.commands = {Tank.CMD_FIRE: True}
        self.tank.update_gun(0.1)

        self.assertEqual(self.tank.get_selected_weapon(), Tank.SHELLS)
        self.assertEqual(weapons[Tank.SHELLS].select_calls, 1)
        self.assertFalse(self.tank.is_firing())

    def test_burn_uses_cpp_ground_smoke_values(self):
        captured = []

        class FakeSmoke:
            def __init__(self, game, x, y, x_vel, y_vel, texture, rotation, growth, fade_rate):
                captured.append((game, x, y, x_vel, y_vel, texture, rotation, growth, fade_rate))

        self.tank._on_ground = True
        self.tank._x = 1.0
        self.tank._y = 2.0
        self.tank._exhaust_time = -0.1

        with patch("src.tank.Smoke", FakeSmoke):
            self.tank.burn(0.1)

        self.assertEqual(len(captured), 1)
        _, x, y, x_vel, y_vel, texture, rotation, growth, fade_rate = captured[0]
        self.assertEqual((x, y), (1.0, 2.2))
        self.assertEqual((x_vel, y_vel), (0.0, 0.5))
        self.assertEqual((texture, rotation, growth, fade_rate), (5, 0.1, 0.3, 0.15))
        self.assertAlmostEqual(self.tank._exhaust_time, 0.9)

    def test_burn_uses_cpp_air_smoke_values(self):
        captured = []

        class FakeSmoke:
            def __init__(self, game, x, y, x_vel, y_vel, texture, rotation, growth, fade_rate):
                captured.append((game, x, y, x_vel, y_vel, texture, rotation, growth, fade_rate))

        self.tank._on_ground = False
        self.tank._x = 1.0
        self.tank._y = 2.0
        self.tank._exhaust_time = -0.1

        with patch("src.tank.Smoke", FakeSmoke):
            self.tank.burn(0.1)

        self.assertEqual(len(captured), 1)
        _, x, y, x_vel, y_vel, texture, rotation, growth, fade_rate = captured[0]
        self.assertEqual((x, y), (1.0, 2.0))
        self.assertEqual((x_vel, y_vel), (0.0, 0.5))
        self.assertEqual((texture, rotation, growth, fade_rate), (5, 0.1, 0.3, 0.3))
        self.assertAlmostEqual(self.tank._exhaust_time, -0.05)

    def test_move_tank_boost_uses_cpp_jump_jet_smoke_values(self):
        captured = []

        class FakeSmoke:
            def __init__(self, game, x, y, x_vel, y_vel, texture, rotation, growth, fade_rate):
                captured.append((game, x, y, x_vel, y_vel, texture, rotation, growth, fade_rate))

        self.tank._state = Tank.TANK_ALIVE
        self.tank._fuel = 1.0
        self.tank._total_fuel = 1.0
        self.tank._x = 1.0
        self.tank._y = 2.0
        self.tank._tank_angle = 30.0
        self.tank._airbourne_x_vel = 3.0
        self.tank._airbourne_y_vel = -4.0
        self.tank._exhaust_time = -0.1

        with patch("src.tank.Smoke", FakeSmoke):
            self.tank.move_tank(0.1, True)

        self.assertEqual(len(captured), 1)
        _, x, y, x_vel, y_vel, texture, rotation, growth, fade_rate = captured[0]
        self.assertEqual((x, y), (1.0, 2.0))
        self.assertAlmostEqual(x_vel, 3.0 + math.sin(math.radians(30.0)) * 2.0)
        self.assertAlmostEqual(y_vel, -4.0 - math.cos(math.radians(30.0)) * 2.0)
        self.assertEqual((texture, rotation, growth, fade_rate), (2, 0.0, 0.0, 2.5))
        self.assertAlmostEqual(self.tank._exhaust_time, -0.05)

    def test_render_state_and_network_snapshot_expose_visual_and_sync_data(self):
        self.tank.assign_entity_id(42)
        self.tank._x = 1.5
        self.tank._y = 2.5
        self.tank._gun_power = 12.0
        self.tank._fuel = 0.4

        render_state = self.tank.get_render_state()
        snapshot = self.tank.build_network_snapshot()

        self.assertEqual(render_state.entity_id, 42)
        self.assertEqual(render_state.entity_type, "tank")
        self.assertGreaterEqual(len(render_state.primitives), 3)
        self.assertEqual(snapshot.entity_id, 42)
        self.assertEqual(snapshot.payload["fuel"], 0.4)
        self.assertEqual(snapshot.payload["player_number"], 0)

    def test_get_colour_uses_player_colour_for_hud_and_rendering(self):
        self.player._colour = (12, 34, 56)
        self.tank._colour = (255, 255, 255)

        self.assertEqual(self.tank.get_colour(), (12, 34, 56))
        self.assertEqual(self.tank._colour, (12, 34, 56))

        self.tank.set_colour((90, 80, 70))

        self.assertEqual(self.player._colour, (90, 80, 70))
        self.assertEqual(self.tank.get_colour(), (90, 80, 70))


class AIPlayerFidelityTests(unittest.TestCase):
    """
    Fidelity target: src/aiplayer.py — record_shot() miss-correction loop
    and find_new_target() target-selection scoring.

    User-visible invariants:
    - AI progressively corrects angle by abs(sin(angle)) * x_dist * 4.0 and
      power by x_dist * 1.2 * (1 - sin(abs(angle))) each miss.
    - A "going-away" shot (two consecutive misses moving farther from target)
      halves the angle and adds 2.0 to power instead.
    - find_new_target awards +100 for a direct line-of-sight to an enemy, +50
      if the enemy is higher than the AI tank.

    Required validation: paired Python reference regressions confirming every
    constant in the correction loop.
    """

    def _make_game_and_ai(self):
        from src.aiplayer import AIPlayer
        from src.common import GameState as _GameState

        _game_state_initial = _GameState.ROUND_IN_ACTION

        class MockGame:
            def __init__(self):
                self.GameState = _GameState
                self._game_state = _game_state_initial
                self._players = [None] * 8
                self._entities = []

            def get_game_state(self):
                return self._game_state

            def get_settings(self):
                return SETTINGS

            def get_time(self):
                return 0.0

            def get_landscape(self):
                return None

            def get_players(self):
                return [p for p in self._players if p is not None]

            def add_entity(self, _e):
                self._entities.append(_e)

            def get_interface(self):
                return None

            def get_current_menu(self):
                return None

            def get_controls(self):
                return None

        game = MockGame()
        ai = AIPlayer(game, 0, "Bot", (255, 0, 0))
        ai._tank = Tank(DummyGameForTank(SETTINGS), CommandPlayer(), 0)
        ai._tank._gun_angle = 0.0
        ai._tank._gun_power = 10.0
        ai._tank._x = 0.0
        ai._tank._y = 0.0
        return game, ai


    def test_record_shot_miss_correction_angle_uses_four_constant(self):
        # Fidelity target: aiplayer.py:125 / 134
        # angle += abs(sin(angle)) * x_dist * 4.0
        # When shot lands short of the target (curr_x_dist < 0, target is to the
        # right), the AI nudges the angle left by 4 * abs(sin(angle)) * |dist|.
        # Setup: prev shot was farther short (x=2.5) so curr (x=3.0) is closer
        # → not going-away (curr_x_dist=-2.0 > prev_x_dist=-2.5) → normal branch.
        _game, ai = self._make_game_and_ai()

        # Target is to the right of the AI tank.
        class FakeTargetTank:
            _x = 5.0
            _y = 0.0
            _state = Tank.TANK_ALIVE

        initial_angle = 30.0
        ai._target_tank = FakeTargetTank()
        ai._target_last_x_pos = 5.0
        ai._target_last_y_pos = 0.0
        ai._target_angle = initial_angle
        ai._target_power = 10.0
        ai._tank._gun_angle = initial_angle
        ai._tank._gun_power = 10.0
        ai._last_shot = True
        ai._ignore_shot = False
        ai._aim_directly = False

        # prev miss at x=2.5 → prev_x_dist = -2.5
        # curr miss at x=3.0 → curr_x_dist = -2.0  (> -2.5, not going-away)
        ai._last_shot_x = 2.5
        ai._last_shot_y = 0.0
        ai.record_shot(3.0, 0.0, -1)  # -1 = miss, no tank hit

        curr_x_dist = 3.0 - 5.0  # = -2.0
        expected_angle_delta = abs(deg_sin(initial_angle)) * curr_x_dist * 4.0
        expected_angle = initial_angle + expected_angle_delta
        self.assertAlmostEqual(ai._target_angle, expected_angle, places=6)

    def test_record_shot_miss_correction_power_uses_1_2_constant(self):
        # Fidelity target: aiplayer.py:130-132
        # power += -curr_x_dist * 1.2 * (1 - sin(abs(angle)))  [target right, shot left]
        # Setup: prev shot was farther short so curr is closer → normal branch (not going-away).
        _game, ai = self._make_game_and_ai()

        class FakeTargetTank:
            _x = 5.0
            _y = 0.0
            _state = Tank.TANK_ALIVE

        initial_angle = 30.0
        initial_power = 10.0
        ai._target_tank = FakeTargetTank()
        ai._target_last_x_pos = 5.0
        ai._target_last_y_pos = 0.0
        ai._target_angle = initial_angle
        ai._target_power = initial_power
        ai._tank._gun_angle = initial_angle
        ai._tank._gun_power = initial_power
        ai._tank._x = 0.0
        ai._last_shot = True
        ai._ignore_shot = False
        ai._aim_directly = False
        # prev at x=2.5 → prev_x_dist = -2.5; curr at x=3.0 → curr_x_dist = -2.0 (> -2.5, not going-away)
        ai._last_shot_x = 2.5

        ai.record_shot(3.0, 0.0, -1)

        curr_x_dist = 3.0 - 5.0  # = -2.0
        # IMPORTANT: angle is updated FIRST in record_shot, so power correction
        # uses the already-updated target_angle, not the initial_angle.
        updated_angle = initial_angle + abs(deg_sin(initial_angle)) * curr_x_dist * 4.0
        # curr_x_dist < 0 and target (5.0) > ai (0.0) → power += -curr_x_dist * 1.2 * factor
        power_factor = 1 - deg_sin(abs(updated_angle))
        power_delta = -curr_x_dist * 1.2 * power_factor
        expected_power = initial_power + power_delta
        expected_power = max(ai._tank._gun_power_min, min(ai._tank._gun_power_max, expected_power))
        self.assertAlmostEqual(ai._target_power, expected_power, places=6)

    def test_record_shot_going_away_halves_angle_and_adds_power(self):
        # Fidelity target: aiplayer.py:114-122
        # Two consecutive shots move farther from the target in the same
        # direction → halve the angle and add 2.0 power.
        _game, ai = self._make_game_and_ai()

        class FakeTargetTank:
            _x = 5.0
            _y = 0.0
            _state = Tank.TANK_ALIVE

        ai._target_tank = FakeTargetTank()
        ai._target_last_x_pos = 5.0
        ai._target_last_y_pos = 0.0
        ai._tank._gun_angle = 30.0
        initial_angle = 40.0
        initial_power = 8.0
        ai._target_angle = initial_angle
        ai._target_power = initial_power
        ai._last_shot = True
        ai._ignore_shot = False
        ai._aim_directly = False

        # Both shots landed to the left of the target and prev_x_dist is more
        # negative than curr_x_dist (i.e. both < 0 and curr < prev).
        ai._last_shot_x = 3.5  # prev: dist = 3.5 - 5.0 = -1.5
        # curr at x=2.0: dist = 2.0 - 5.0 = -3.0 < -1.5 → going-away branch
        ai.record_shot(2.0, 0.0, -1)

        expected_angle = initial_angle / 2.0
        expected_power = min(ai._tank._gun_power_max, initial_power + 2.0)
        self.assertAlmostEqual(ai._target_angle, expected_angle, places=6)
        self.assertAlmostEqual(ai._target_power, expected_power, places=6)

    def test_record_shot_direct_hit_sets_on_target(self):
        # Fidelity target: aiplayer.py:93-102
        # When a shot hits an enemy tank, _on_target is set to True and
        # the target is updated to the hit player's tank.
        # Setup: AI number=1, enemy at players[0]. hit_tank=0 != ai._number=1
        # so the hit branches into the target-update code (not self-hit branch).
        _game, ai = self._make_game_and_ai()
        ai._number = 1  # avoid self-hit branch (hit_tank=0 != ai._number=1)

        class FakeEnemyTank:
            _x = 3.0
            _y = 0.0
            _state = Tank.TANK_ALIVE

            def alive(self):
                return True

        class FakeEnemyPlayer:
            _number = 0

            def get_tank(self):
                return enemy_tank

        enemy_tank = FakeEnemyTank()
        enemy_player = FakeEnemyPlayer()
        _game._players[0] = enemy_player

        ai._shots_in_air = 1
        # get_players() returns [enemy_player] → index 0 → hit_tank=0.
        # hit_tank(0) != ai._number(1) → enters target-update branch.
        ai.record_shot(3.0, 0.0, 0)

        self.assertTrue(ai._on_target)
        self.assertIs(ai._target_tank, enemy_tank)

    def test_find_new_target_scores_plus_100_for_direct_los(self):
        # Fidelity target: aiplayer.py:246-251
        # An enemy with a clear line-of-sight (no terrain collision) scores
        # +100. If also higher than the AI tank, scores an extra +50 and sets
        # aim_directly to True.
        _game, ai = self._make_game_and_ai()

        class LoSLandscape:
            def ground_collision(self, _x1, _y1, _x2, _y2):
                return (False, 0.0, 0.0)

        class FakeEnemyTank:
            _x = 2.0
            _y = 1.0
            _state = Tank.TANK_ALIVE

            def get_centre(self):
                return (self._x, self._y, 0.1875)

            def gun_launch_position(self):
                return (0.0, 0.0)

        enemy_tank = FakeEnemyTank()

        class FakeEnemy:
            def get_tank(self):
                return enemy_tank

        ai._tank._x = 0.0
        ai._tank._y = 0.0

        # Patch landscape to provide direct LoS.
        _game.get_landscape = lambda: LoSLandscape()
        _game._players[1] = FakeEnemy()

        # AI needs gun_launch_position accessible.
        ai._tank.gun_launch_position = lambda: (0.0, 0.0)

        ai.find_new_target()

        self.assertIs(ai._target_tank, enemy_tank)
        # aim_directly should be True when enemy is higher
        self.assertTrue(ai._aim_directly)


class ExplosionFidelityTests(unittest.TestCase):
    """
    Fidelity target: src/gamesession.py explosion() — quadratic splash damage
    falloff formula and direct-hit full-damage delivery.

    User-visible invariants:
    - A tank at the explosion centre (direct hit) always receives full damage.
    - Tanks in the splash radius receive damage * (1 - dist² / max_dist²).
    - Tanks outside the splash radius (squared_distance >= max_distance) receive
      no damage.
    - max_distance = (size + hit_range)², where hit_range = tank.get_centre()[2].

    Required validation: Python reference regressions confirming every constant.
    """

    def _run_explosion(self, *, blast_x, blast_y, blast_size, damage,
                       hit_tank_idx, tanks):
        """
        Run gamesession.explosion() and return the damage_calls list per tank.
        """
        from src.gamesession import GameSessionController

        class FakeBlast:
            def __init__(self, *args, **kwargs):
                pass

        class FakeSoundEntity:
            def __init__(self, *args, **kwargs):
                pass

        class FakeGame:
            _entity_list = []
            _players = [None] * 8
            _landscape = None

            def add_entity(self, _e):
                pass

            def queue_network_event(self, *_a, **_k):
                pass

        game = FakeGame()
        players_list = []
        for idx, tank in enumerate(tanks):
            class FakePlayer:
                def __init__(self, t):
                    self._tank = t

                def get_tank(self):
                    return self._tank

                def defeat(self, _p):
                    pass

            fp = FakePlayer(tank)
            game._players[idx] = fp
            players_list.append(fp)

        class FakePlayerRef:
            def defeat(self, _p):
                pass

        session = GameSessionController(
            human_player_factory=lambda *a, **k: None,
            ai_player_factory=lambda *a, **k: None,
            landscape_factory=lambda *a, **k: None,
            quake_factory=lambda *a, **k: None,
            blast_factory=lambda *a, **k: FakeBlast(*a, **k),
            sound_entity_factory=lambda *a, **k: FakeSoundEntity(*a, **k),
        )
        session.explosion(
            game, blast_x, blast_y, blast_size, damage, hit_tank_idx,
            0, False, FakePlayerRef()
        )
        return [tank.damage_calls for tank in tanks]

    def test_direct_hit_delivers_full_damage(self):
        # Fidelity target: gamesession.py:95-97
        # The tank at hit_tank_idx receives full damage without the splash falloff.
        from tests.support import ExplosionTank

        direct = ExplosionTank(x=0.0, y=0.0)
        nearby = ExplosionTank(x=0.1, y=0.0)

        results = self._run_explosion(
            blast_x=0.0, blast_y=0.0, blast_size=0.3, damage=40,
            hit_tank_idx=0, tanks=[direct, nearby]
        )

        self.assertEqual(results[0], [40])  # direct: full damage regardless of distance
        # nearby is also within splash radius; its damage should be less than 40
        if results[1]:
            self.assertLess(results[1][0], 40)

    def test_splash_damage_quadratic_falloff_formula(self):
        # Fidelity target: gamesession.py:101-104
        # scaled_damage = damage * (1.0 - squared_distance / max_distance)
        # where max_distance = (size + hit_range)^2.
        from tests.support import ExplosionTank

        blast_x = 0.0
        blast_y = 0.0
        size = 0.3
        damage = 40

        # Place a tank at x=0.2 with the classic hit_range=0.1875.
        hit_range = 0.1875
        tank_x = 0.2
        tank = ExplosionTank(x=tank_x, y=0.0, hit_range=hit_range)

        results = self._run_explosion(
            blast_x=blast_x, blast_y=blast_y, blast_size=size, damage=damage,
            hit_tank_idx=-1, tanks=[tank]
        )

        squared_distance = tank_x ** 2  # y=0 so dist² = dx²
        max_distance = (size + hit_range) ** 2
        expected_damage = damage * (1.0 - squared_distance / max_distance)

        self.assertEqual(len(results[0]), 1)
        self.assertAlmostEqual(results[0][0], expected_damage, places=5)

    def test_splash_damage_at_boundary_is_approximately_zero(self):
        # Fidelity target: gamesession.py:102-103
        # A tank positioned just at the edge of (size + hit_range) receives
        # approximately 0 damage (the formula gives exactly 0 at the boundary).
        from tests.support import ExplosionTank

        size = 0.3
        hit_range = 0.1875
        # Place at exactly the boundary distance.
        boundary_x = size + hit_range  # = 0.4875

        tank = ExplosionTank(x=boundary_x, y=0.0, hit_range=hit_range)
        results = self._run_explosion(
            blast_x=0.0, blast_y=0.0, blast_size=size, damage=40,
            hit_tank_idx=-1, tanks=[tank]
        )

        # At boundary: squared_distance == max_distance → damage = 0 → do_damage not called.
        self.assertEqual(results[0], [])

    def test_splash_damage_outside_radius_delivers_no_damage(self):
        # Fidelity target: gamesession.py:102-103 — the < check.
        # A tank beyond (size + hit_range) receives no damage at all.
        from tests.support import ExplosionTank

        tank = ExplosionTank(x=2.0, y=0.0)  # far outside any blast
        results = self._run_explosion(
            blast_x=0.0, blast_y=0.0, blast_size=0.3, damage=40,
            hit_tank_idx=-1, tanks=[tank]
        )

        self.assertEqual(results[0], [])


class PlayerAndSoundFidelityTests(unittest.TestCase):
    def test_end_round_matches_cpp_scoring_without_extra_post_round(self):
        game = DummyGameForTank(SETTINGS)
        player = Player(game, 0, "P1", (255, 255, 255))

        class FakeTank:
            def __init__(self):
                self.post_round_calls = 0

            def alive(self):
                return True

            def do_post_round(self):
                self.post_round_calls += 1

        leader = type("Leader", (), {"_leader": True})()
        regular = type("Regular", (), {"_leader": False})()

        fake_tank = FakeTank()
        player._tank = fake_tank
        player._defeated_players = [player, leader, regular]

        player.end_round()

        self.assertEqual(player.get_score(), 350)
        self.assertEqual(player.get_money(), 135)
        self.assertEqual(fake_tank.post_round_calls, 0)

    def test_sound_entity_can_be_marked_inactive(self):
        game = DummyGameForTank(SETTINGS)
        entity = SoundEntity(game, 0, True)
        self.assertTrue(entity.update(0.1))
        entity.set_inactive()
        self.assertFalse(entity.update(0.1))


class ScoreEconomyFidelityTests(unittest.TestCase):
    """
    Granular fidelity tests for Player.end_round() scoring and economy.

    Fidelity target: src/player.py:60-75
    C++/Python invariants:
    - Defeating a leader-flagged player: +200 score, +50 money.
    - Defeating a non-leader player:    +100 score, +50 money.
    - Self-defeat (defeated_player == self): -50 score, no money change.
    - Surviving (tank.alive()): +100 score, +25 money.
    - Stipend: always +10 money.
    - All four of the above accumulate in one end_round() call.

    Required validation: Each rule verified in isolation so a regression in one
    constant cannot be masked by another.
    """

    def _make_player(self, alive: bool = True):
        """Return a fresh Player with a fake tank whose alive() is controllable."""
        from src.player import Player

        game = DummyGameForTank(SETTINGS)
        player = Player(game, 0, "P1", (255, 255, 255))
        _alive = alive

        class FakeTank:
            def alive(self):
                return _alive

        player._tank = FakeTank()
        return player

    def test_end_round_only_stipend_when_no_defeats_and_dead(self):
        # Fidelity target: player.py:75 — stipend is unconditional.
        # A dead player with no defeats: score=0, money=10 (stipend only).
        player = self._make_player(alive=False)
        player._defeated_players = []
        player.end_round()

        self.assertEqual(player.get_score(), 0,
                         "Dead player with no defeats should score 0")
        self.assertEqual(player.get_money(), 10,
                         "Stipend of 10 credits always applies")

    def test_end_round_survival_adds_100_score_and_25_money(self):
        # Fidelity target: player.py:71-73
        # Surviving (alive) always adds 100 to score and 25 to money.
        player = self._make_player(alive=True)
        player._defeated_players = []
        player.end_round()

        self.assertEqual(player.get_score(), 100,
                         "Survival should add exactly 100 to score")
        self.assertEqual(player.get_money(), 35,
                         "Survival adds 25 money; stipend adds 10 → total 35")

    def test_end_round_defeat_non_leader_adds_100_score_and_50_money(self):
        # Fidelity target: player.py:67-69
        # Defeating a non-leader gives +100 score, +50 money (+ stipend).
        player = self._make_player(alive=False)
        enemy = type("Enemy", (), {"_leader": False})()
        player._defeated_players = [enemy]
        player.end_round()

        self.assertEqual(player.get_score(), 100,
                         "Killing non-leader gives 100 score")
        self.assertEqual(player.get_money(), 60,
                         "Killing non-leader gives 50 money + 10 stipend = 60")

    def test_end_round_defeat_leader_adds_200_score_and_50_money(self):
        # Fidelity target: player.py:64-66
        # Defeating a leader-flagged player gives +200 score, +50 money (+ stipend).
        player = self._make_player(alive=False)
        leader = type("Leader", (), {"_leader": True})()
        player._defeated_players = [leader]
        player.end_round()

        self.assertEqual(player.get_score(), 200,
                         "Killing leader gives 200 score")
        self.assertEqual(player.get_money(), 60,
                         "Killing leader gives 50 money + 10 stipend = 60")

    def test_end_round_self_defeat_subtracts_50_score_no_money(self):
        # Fidelity target: player.py:62-63
        # Self-defeat (player defeats themselves) subtracts 50 from score.
        # No money is added for self-defeat; only stipend applies.
        player = self._make_player(alive=False)
        player._defeated_players = [player]  # self-defeat
        player.end_round()

        self.assertEqual(player.get_score(), -50,
                         "Self-defeat should subtract exactly 50 from score")
        self.assertEqual(player.get_money(), 10,
                         "Self-defeat awards no defeat money; only stipend of 10")

    def test_end_round_multiple_defeats_accumulate_independently(self):
        # Fidelity target: player.py:60-75 full loop.
        # Defeating two non-leaders while alive: 2*100 score + 100 survival,
        # money = 2*50 + 25 survival + 10 stipend.
        player = self._make_player(alive=True)
        enemy1 = type("Enemy1", (), {"_leader": False})()
        enemy2 = type("Enemy2", (), {"_leader": False})()
        player._defeated_players = [enemy1, enemy2]
        player.end_round()

        self.assertEqual(player.get_score(), 300,
                         "Two non-leader kills + survival = 300 score")
        self.assertEqual(player.get_money(), 135,
                         "2×50 defeat + 25 survival + 10 stipend = 135 money")

    def test_end_round_all_four_rules_match_combined_expectation(self):
        # Fidelity target: player.py:60-75 — this mirrors test_end_round_matches_cpp
        # but asserts each component in sequence using known constants.
        # Defeats: self (-50 score, 0 money), leader (+200 score, +50 money),
        #          non-leader (+100 score, +50 money).
        # Survival: +100 score, +25 money.
        # Stipend: +10 money.
        # Total: -50+200+100+100=350 score; 0+50+50+25+10=135 money.
        player = self._make_player(alive=True)
        leader = type("Leader", (), {"_leader": True})()
        regular = type("Regular", (), {"_leader": False})()
        player._defeated_players = [player, leader, regular]
        player.end_round()

        self.assertEqual(player.get_score(), 350)
        self.assertEqual(player.get_money(), 135)

    def test_end_round_score_is_cumulative_across_rounds(self):
        # Fidelity target: player.py:63,65,68,72 all use += (accumulate across rounds).
        # Running end_round twice should double the awards when conditions repeat.
        player = self._make_player(alive=True)
        player._defeated_players = []

        player.end_round()
        self.assertEqual(player.get_score(), 100)   # survival round 1
        self.assertEqual(player.get_money(), 35)    # 25 survival + 10 stipend

        # Reset defeats for round 2, tank stays alive.
        player._defeated_players = []
        player.end_round()
        self.assertEqual(player.get_score(), 200)   # 100+100
        self.assertEqual(player.get_money(), 70)    # 35+35


class AIPlayerShopFidelityTests(unittest.TestCase):
    """
    Fidelity tests for the AI shop logic in src/aiplayer.py.

    Fidelity target: aiplayer.py:49-62 (AI shop update: press GUNUP until
    position==10 then FIRE to exit the shop).

    The classic C++ AI moves its cursor to position 10 (Done!) and then fires
    to exit; it does NOT buy any weapons — spending is handled elsewhere.

    Required validation: verify command output for each shop-position state.
    """

    def _make_ai_in_shop(self, select_pos: int):
        from src.aiplayer import AIPlayer
        from src.common import GameState

        class FakeMenu:
            def __init__(self, pos):
                self._player_select_pos = {0: pos}

        game = DummyGameForTank(SETTINGS)
        menu = FakeMenu(select_pos)
        game._menu = menu
        game._game_state = GameState.SHOP_MENU

        # Patch get_current_menu onto the dummy game.
        game.get_current_menu = lambda: game._menu
        game.get_players = lambda: game._players if hasattr(game, "_players") else [None] * 8

        ai = AIPlayer(game, 0, "Bot", (255, 0, 0))
        return game, ai

    def test_ai_shop_presses_gunup_when_not_at_done(self):
        # Fidelity target: aiplayer.py:56-57
        # When the AI's shop cursor is NOT at position 10 (Done!), the AI
        # presses GUNUP to cycle to Done! as quickly as possible.
        _game, ai = self._make_ai_in_shop(select_pos=3)
        ai.update(0.0)

        from src.player import Player
        self.assertTrue(ai.get_command(Player.CMD_GUNUP),
                        "AI in shop should press GUNUP when not at Done! (pos 10)")
        self.assertFalse(ai.get_command(Player.CMD_FIRE),
                         "AI in shop should not press FIRE until at Done!")

    def test_ai_shop_presses_fire_when_at_done(self):
        # Fidelity target: aiplayer.py:58-59
        # When the AI's shop cursor is at position 10 (Done!), the AI presses
        # FIRE to confirm and leave the shop.
        _game, ai = self._make_ai_in_shop(select_pos=10)
        ai.update(0.0)

        from src.player import Player
        self.assertFalse(ai.get_command(Player.CMD_GUNUP),
                         "AI at Done! should not press GUNUP")
        self.assertTrue(ai.get_command(Player.CMD_FIRE),
                        "AI at Done! should press FIRE to exit shop")

    def test_ai_shop_position_zero_is_not_done(self):
        # Position 0 is Machine Gun (first item), not Done! — AI should move up.
        _game, ai = self._make_ai_in_shop(select_pos=0)
        ai.update(0.0)

        from src.player import Player
        self.assertTrue(ai.get_command(Player.CMD_GUNUP),
                        "AI at position 0 (Machine Gun) should still move toward Done!")


class WeaponFidelityTests(unittest.TestCase):
    def setUp(self):
        class FakeGame:
            def __init__(self):
                self.time = 100.0
                self.entities = []
                self.interface = None
                self.sound = None
            def get_time(self): return self.time
            def add_entity(self, e): self.entities.append(e)
            def get_interface(self): return self.interface
            def get_sound(self): return self.sound
            def get_landscape(self): return None
            def get_players(self): return []
            def get_settings(self):
                class MockSettings:
                    def get_float(self, section, key, default): return default
                    def get_int(self, section, key, default): return default
                return MockSettings()
            def record_tank_death(self): pass
            def explosion(self, x, y, size, damage, hit_tank, type, is_missile, player):
                self.last_explosion = (x, y, size, damage, hit_tank, type, is_missile, player)
        
        class FakePlayer:
            def __init__(self, number):
                self._number = number
                self.fired_count = 0
            def record_fired(self): self.fired_count += 1
            def get_tank(self): return None
        
        class FakeTank:
            def __init__(self, player):
                self.player = player
                self.gun_angle = 45.0
            def get_player(self): return self.player
            def gun_launch_position(self): return (0.0, 5.0)
            def gun_launch_velocity(self): return (10.0, 10.0)
            def gun_launch_angle(self): return self.gun_angle
            def intersect_tank(self, old_x, old_y, new_x, new_y): return False

        self.game = FakeGame()
        self.player = FakePlayer(1)
        self.tank = FakeTank(self.player)

    def test_nuke_weapon_fire_consumes_inventory_and_spawns_whiteout_shell(self):
        from src.weapons_impl import NukeWeapon
        from src.shell import Shell
        from src.soundentity import SoundEntity
        
        nuke_weapon = NukeWeapon(self.game, self.tank)
        nuke_weapon._quantity = 1
        nuke_weapon._cooldown = 0.0
        
        result = nuke_weapon.fire(True, 0.0)
        self.assertFalse(result)
        self.assertEqual(nuke_weapon._quantity, 0)
        
        shells = [e for e in self.game.entities if isinstance(e, Shell)]
        sounds = [e for e in self.game.entities if isinstance(e, SoundEntity)]
        
        self.assertEqual(len(shells), 1)
        self.assertEqual(len(sounds), 1)
        
        self.assertTrue(shells[0]._white_out)
        self.assertEqual(shells[0]._damage, NukeWeapon.OPTION_Damage)

    def test_mirv_splits_into_exact_fragment_count_at_apex(self):
        from src.mirv import Mirv
        from src.shell import Shell
        
        mirv = Mirv(self.game, self.player, 0.0, 5.0, 10.0, 20.0, self.game.get_time(), 0.3, 20.0)
        # Apex time = launch_time + y_vel / 10.0 = 100.0 + 2.0 = 102.0
        self.assertAlmostEqual(mirv._apex_time, 102.0)
        
        # Advance game time to after apex
        self.game.time = 102.1
        alive = mirv.update(0.1)
        
        self.assertFalse(alive) # Consumed
        fragments = [e for e in self.game.entities if isinstance(e, Shell)]
        self.assertEqual(len(fragments), Mirv.OPTION_Fragments)

    def test_mirv_fragments_inherit_zero_vertical_velocity_and_spread_horizontally(self):
        from src.mirv import Mirv
        from src.shell import Shell
        
        mirv = Mirv(self.game, self.player, 0.0, 5.0, 10.0, 20.0, self.game.get_time(), 0.3, 20.0)
        self.game.time = 102.1
        mirv.update(0.1)
        
        fragments = [e for e in self.game.entities if isinstance(e, Shell)]
        self.assertEqual(len(fragments), Mirv.OPTION_Fragments)
        
        # Check velocities
        expected_x_vels = [6.0, 8.0, 10.0, 12.0, 14.0]
        
        for i, frag in enumerate(fragments):
            self.assertEqual(frag._y_launch_vel, 0.0)
            self.assertAlmostEqual(frag._x_launch_vel, expected_x_vels[i])

    def test_mirv_ground_collision_before_apex_explodes_without_splitting(self):
        from src.mirv import Mirv
        from src.shell import Shell
        
        mirv = Mirv(self.game, self.player, 0.0, 5.0, 10.0, 20.0, self.game.get_time(), 0.3, 20.0)
        
        class MockLandscape:
            def ground_collision(self, x1, y1, x2, y2):
                return (True, 5.0, 10.0) # Collision at (5, 10)
            def get_landscape_width(self):
                return 100.0
                
        self.game.get_landscape = lambda: MockLandscape()
        
        # Before apex
        self.game.time = 101.0
        alive = mirv.update(0.1)
        
        self.assertFalse(alive)
        self.assertTrue(hasattr(self.game, "last_explosion"))
        self.assertEqual(self.game.last_explosion[0], 5.0) # Hit x
        self.assertEqual(self.game.last_explosion[1], 10.0) # Hit y
        
        fragments = [e for e in self.game.entities if isinstance(e, Shell)]
        self.assertEqual(len(fragments), 0)

    def test_mirv_tank_collision_before_apex_explodes_without_splitting(self):
        from src.mirv import Mirv
        from src.shell import Shell
        
        mirv = Mirv(self.game, self.player, 0.0, 5.0, 10.0, 20.0, self.game.get_time(), 0.3, 20.0)
        
        class MockTargetPlayer:
            def __init__(self, tank): self.tank = tank
            def get_tank(self): return self.tank
            
        class MockTargetTank:
            def intersect_tank(self, old_x, old_y, x, y): return True
            
        target_tank = MockTargetTank()
        target_player = MockTargetPlayer(target_tank)
        
        # Game returns target player to test tank collision
        self.game.get_players = lambda: [target_player]
        
        self.game.time = 101.0
        alive = mirv.update(0.1)
        
        self.assertFalse(alive)
        self.assertTrue(hasattr(self.game, "last_explosion"))
        self.assertEqual(self.game.last_explosion[4], 0) # Hit tank index 0
        
        fragments = [e for e in self.game.entities if isinstance(e, Shell)]
        self.assertEqual(len(fragments), 0)

    def test_machine_gun_fire_starts_looped_audio_and_unselect_stops_it(self):
        from src.weapons_impl import MachineGunWeapon
        
        class MockSoundSource:
            def __init__(self, sound, sound_id, loop):
                self.sound_id = sound_id
                self.loop = loop
        
        class MockSound:
            def SoundSource(self, sound, sound_id, loop):
                return MockSoundSource(sound, sound_id, loop)
                
        self.game.sound = MockSound()
        
        mg = MachineGunWeapon(self.game, self.tank)
        mg._quantity = 50
        mg.set_ammo_for_round()
        
        # Fire
        result = mg.fire(True, 0.0)
        self.assertTrue(result)
        self.assertIsNotNone(mg._gun_source)
        self.assertEqual(mg._gun_source.sound_id, 8)
        self.assertTrue(mg._gun_source.loop)
        
        # Unselect
        mg.unselect()
        self.assertIsNone(mg._gun_source)

    def test_machine_gun_pre_shot_cancellation_stops_audio_before_firing(self):
        from src.weapons_impl import MachineGunWeapon
        
        mg = MachineGunWeapon(self.game, self.tank)
        mg._quantity = 50
        mg.set_ammo_for_round()
        
        class MockSoundSource:
            def __init__(self, sound, sound_id, loop): pass
        class MockSound:
            def SoundSource(self, sound, sound_id, loop): return MockSoundSource(sound, sound_id, loop)
        self.game.sound = MockSound()
        
        mg.fire(True, 0.0)
        self.assertIsNotNone(mg._gun_source)
        
        # Cancel fire without calling update() (no bullets spawned)
        mg.fire(False, 0.0)
        self.assertIsNone(mg._gun_source)

    def test_machine_gun_lethal_hit_stops_firing_and_audio(self):
        from src.tank import Tank
        
        # Give tank proper weapons
        tank = Tank(self.game, self.player, 0)
        tank._state = Tank.TANK_ALIVE
        tank._health = 10.0
        
        mg = tank.get_weapon(Tank.MACHINEGUN)
        mg._quantity = 50
        mg.set_ammo_for_round()
        
        tank._selected_weapon = Tank.MACHINEGUN
        
        # Fire
        tank._firing = True # Tank update_gun sets this when fire() returns True
        mg.fire(True, 0.0)
        
        # Take lethal damage
        tank.do_damage(20.0)
        
        self.assertEqual(tank._state, Tank.TANK_DEAD)
        self.assertFalse(tank._firing)
        self.assertIsNone(mg._gun_source)

    def test_ai_tactical_hold_fires_machine_gun_continuously(self):
        from src.aiplayer import AIPlayer
        from src.tank import Tank
        from src.player import Player
        
        ai = AIPlayer(self.game, 1, "AI", (255, 0, 0))
        tank = Tank(self.game, ai, 0)
        ai._tank = tank
        
        class MockTargetPlayer:
            def __init__(self, t): self.t = t
            def get_tank(self): return self.t
            
        target_tank = Tank(self.game, None, 1)
        target_tank.set_position(5.0, 0.0)
        target_tank._state = Tank.TANK_ALIVE
        
        # Set AI target
        ai._target_tank = target_tank
        ai._target_last_x_pos = target_tank._x
        ai._target_last_y_pos = target_tank._y
        ai._target_angle = 45.0
        ai._target_power = 10.0
        
        # Set gun exactly to target so ready_to_fire = True
        tank._gun_angle = 45.0
        tank._gun_power = 10.0
        
        # For MachineGun, ready_to_fire() depends on having ammo. Let's select it.
        tank._selected_weapon = Tank.MACHINEGUN
        mg = tank.get_weapon(Tank.MACHINEGUN)
        mg._quantity = 50
        mg.set_ammo_for_round()
        
        fire_commands_count = 0
        for i in range(10):
            # simulate Tank updating MG cooldown
            mg._cooldown = 0.0 # Force cooldown to 0.0 to simulate fast time or check AI logic
            ai.compute_action()
            if ai._commands[Player.CMD_FIRE]:
                fire_commands_count += 1
                
        # Since _shots_in_air remains 0, the AI should hold fire when cooldown allows it
        self.assertEqual(fire_commands_count, 10)

class ShopMenuEconomyFidelityTests(unittest.TestCase):
    def setUp(self):
        class MockSettings:
            def get_float(self, section, key, default): return default
            def get_int(self, section, key, default): return default
            
        class FakeGame:
            def __init__(self):
                self.settings = MockSettings()
                self.players = [None] * 8
                self.current_round = 0
                self.num_rounds = 5
            def get_settings(self): return self.settings
            def get_players(self): return self.players
            def get_current_round(self): return self.current_round
            def get_num_of_rounds(self): return self.num_rounds
            def get_font(self): return None
            def get_interface(self): return None
            def get_graphics(self): return None
            def get_sound(self): return None
            def get_ui(self): return None
            
        self.game = FakeGame()
        
        from src.player import Player
        from src.tank import Tank
        
        class MockPlayer(Player):
            def __init__(self, game):
                super().__init__(game, 0, "Test", (255, 255, 255))
                self.commands = [False] * 11
                
            def get_command(self, cmd, ref=None):
                return self.commands[cmd]
                
            def update(self): pass
            
        self.player = MockPlayer(self.game)
        self.tank = Tank(self.game, self.player, 0)
        self.player._tank = self.tank
        self.game.players[0] = self.player

    def test_shop_purchase_machine_gun_adds_50_ammo(self):
        from src.shopmenu import ShopMenu
        from src.player import Player
        from src.tank import Tank
        
        # Override update_background because it accesses graphics/UI that we didn't mock
        class MockShopMenu(ShopMenu):
            def update_background(self, time): pass
            
        shop = MockShopMenu(self.game)
        shop._player_select_delay[0] = -1.0 # ready for input
        shop._player_select_pos[0] = 0 # Machine Gun
        
        mg = self.tank.get_weapon(Tank.MACHINEGUN)
        cost = mg.get_cost()
        self.player.set_money(cost)
        initial_ammo = mg.get_ammo()
        
        self.player.commands[Player.CMD_FIRE] = True
        shop.update(0.0)
        
        self.assertEqual(self.player.get_money(), 0)
        self.assertEqual(mg.get_ammo(), initial_ammo + 50)
        self.assertEqual(shop._player_select_delay[0], 0.2)

    def test_shop_purchase_jump_jets_adds_one_total_fuel(self):
        from src.shopmenu import ShopMenu
        from src.player import Player
        
        class MockShopMenu(ShopMenu):
            def update_background(self, time): pass
            
        shop = MockShopMenu(self.game)
        shop._player_select_delay[0] = -1.0
        shop._player_select_pos[0] = 1 # Jump Jets
        
        cost = shop._jumpjets_cost
        self.player.set_money(cost)
        initial_fuel = self.tank.get_total_fuel()
        
        self.player.commands[Player.CMD_FIRE] = True
        shop.update(0.0)
        
        self.assertEqual(self.player.get_money(), 0)
        self.assertAlmostEqual(self.tank.get_total_fuel(), initial_fuel + 1.0)

    def test_shop_purchase_missiles_adds_5_ammo_and_nukes_mirvs_add_1(self):
        from src.shopmenu import ShopMenu
        from src.player import Player
        from src.tank import Tank
        
        class MockShopMenu(ShopMenu):
            def update_background(self, time): pass
            
        shop = MockShopMenu(self.game)
        
        for pos, w_idx, amount in [(2, Tank.MIRVS, 1), (3, Tank.MISSILES, 5), (4, Tank.NUKES, 1)]:
            shop._player_select_delay[0] = -1.0
            shop._player_select_pos[0] = pos
            weapon = self.tank.get_weapon(w_idx)
            self.player.set_money(weapon.get_cost())
            
            initial_ammo = weapon.get_ammo()
            self.player.commands[Player.CMD_FIRE] = True
            shop.update(0.0)
            
            self.assertEqual(self.player.get_money(), 0)
            self.assertEqual(weapon.get_ammo(), initial_ammo + amount)

    def test_shop_purchase_prevents_buy_without_sufficient_funds(self):
        from src.shopmenu import ShopMenu
        from src.player import Player
        from src.tank import Tank
        
        class MockShopMenu(ShopMenu):
            def update_background(self, time): pass
            
        shop = MockShopMenu(self.game)
        shop._player_select_delay[0] = -1.0
        shop._player_select_pos[0] = 0 # MG
        
        mg = self.tank.get_weapon(Tank.MACHINEGUN)
        cost = mg.get_cost()
        self.player.set_money(cost - 1) # Not enough
        initial_ammo = mg.get_ammo()
        
        self.player.commands[Player.CMD_FIRE] = True
        shop.update(0.0)
        
        # Money not deducted, ammo not added
        self.assertEqual(self.player.get_money(), cost - 1)
        self.assertEqual(mg.get_ammo(), initial_ammo)

    def test_shop_input_delay_prevents_duplicate_buy_actions(self):
        from src.shopmenu import ShopMenu
        from src.player import Player
        from src.tank import Tank
        
        class MockShopMenu(ShopMenu):
            def update_background(self, time): pass
            
        shop = MockShopMenu(self.game)
        shop._player_select_delay[0] = -1.0
        shop._player_select_pos[0] = 0
        
        mg = self.tank.get_weapon(Tank.MACHINEGUN)
        cost = mg.get_cost()
        self.player.set_money(cost * 2)
        initial_ammo = mg.get_ammo()
        
        self.player.commands[Player.CMD_FIRE] = True
        
        # Frame 1: Action triggers, delay becomes 0.2
        shop.update(0.0)
        self.assertEqual(self.player.get_money(), cost)
        self.assertEqual(mg.get_ammo(), initial_ammo + 50)
        
        # Frame 2: User holds FIRE, delay > 0, so no second purchase
        shop.update(0.05)
        self.assertEqual(self.player.get_money(), cost)
        self.assertEqual(mg.get_ammo(), initial_ammo + 50)

    def test_shop_done_position_marks_player_ready(self):
        from src.shopmenu import ShopMenu
        from src.player import Player
        from src.common import GameState
        
        class MockShopMenu(ShopMenu):
            def update_background(self, time): pass
            
        shop = MockShopMenu(self.game)
        shop._player_select_delay[0] = -1.0
        shop._player_select_pos[0] = 10 # Done!
        
        self.player.commands[Player.CMD_FIRE] = True
        
        state = shop.update(0.0)
        
        self.assertTrue(shop._player_done[0])
        # On the frame it was pressed, it returns CURRENT_STATE because still_players_in_shop was evaluated first.
        # On the next frame, it transitions to ROUND_STARTING.
        state2 = shop.update(0.0)
        self.assertEqual(state2, GameState.ROUND_STARTING)

class WinnerMenuFidelityTests(unittest.TestCase):
    def setUp(self):
        class FakeGame:
            def __init__(self):
                self.players = [None] * 8
                self.has_humans = True
                self.players_deleted = False
            def get_players(self): return self.players
            def get_num_of_players(self): return len(self.players)
            def are_human_players(self): return self.has_humans
            def delete_players(self): self.players_deleted = True
            
            def get_font(self): return None
            def get_interface(self): return None
            def get_graphics(self): return None
            def get_sound(self): return None
            def get_ui(self): return None
            
        self.game = FakeGame()
        
        class MockPlayer:
            def __init__(self, name, score):
                self.name = name
                self._score = score
                self.commands = [False] * 11
            def get_score(self): return self._score
            def get_command(self, cmd): return self.commands[cmd]
            
        self.MockPlayer = MockPlayer

    def test_winner_menu_identifies_single_winner(self):
        from src.winnermenu import WinnerMenu
        
        self.game.players[0] = self.MockPlayer("P1", 100)
        self.game.players[1] = self.MockPlayer("P2", 200)
        self.game.players[2] = self.MockPlayer("P3", 150)
        
        menu = WinnerMenu(self.game)
        
        self.assertFalse(menu._is_draw)
        self.assertEqual(len(menu._winners), 1)
        self.assertEqual(menu._winners[0].name, "P2")

    def test_winner_menu_identifies_tie_between_multiple_players(self):
        from src.winnermenu import WinnerMenu
        
        self.game.players[0] = self.MockPlayer("P1", 200)
        self.game.players[1] = self.MockPlayer("P2", 200)
        self.game.players[2] = self.MockPlayer("P3", 150)
        
        menu = WinnerMenu(self.game)
        
        self.assertTrue(menu._is_draw)
        self.assertEqual(len(menu._winners), 2)
        self.assertEqual(menu._winners[0].name, "P1")
        self.assertEqual(menu._winners[1].name, "P2")

    def test_winner_menu_activation_delay_is_2_seconds_for_humans_and_4_for_computers(self):
        from src.winnermenu import WinnerMenu
        
        self.game.has_humans = True
        menu_human = WinnerMenu(self.game)
        self.assertEqual(menu_human._time_till_active, 2.0)
        
        self.game.has_humans = False
        menu_cpu = WinnerMenu(self.game)
        self.assertEqual(menu_cpu._time_till_active, 4.0)

    def test_winner_menu_ignores_input_before_activation_delay(self):
        from src.winnermenu import WinnerMenu
        from src.player import Player
        from src.common import GameState
        
        self.game.players[0] = self.MockPlayer("P1", 100)
        self.game.players[0].commands[Player.CMD_FIRE] = True
        
        class MockWinnerMenu(WinnerMenu):
            def update_background(self, time): pass
            
        menu = MockWinnerMenu(self.game)
        
        # We pass 1.0 time, delay becomes 1.0 (since it starts at 2.0)
        state = menu.update(1.0)
        
        self.assertEqual(state, GameState.CURRENT_STATE)
        self.assertFalse(self.game.players_deleted)

    def test_winner_menu_computer_only_match_auto_exits_after_delay(self):
        from src.winnermenu import WinnerMenu
        from src.common import GameState
        
        self.game.has_humans = False
        
        class MockWinnerMenu(WinnerMenu):
            def update_background(self, time): pass
            
        menu = MockWinnerMenu(self.game)
        
        # Passes 4.0 seconds, delay goes <= 0, returns CURRENT_STATE
        state = menu.update(4.0)
        self.assertEqual(state, GameState.CURRENT_STATE)
        
        # Next frame it triggers MAIN_MENU
        state2 = menu.update(0.0)
        self.assertEqual(state2, GameState.MAIN_MENU)
        self.assertTrue(self.game.players_deleted)

    def test_winner_menu_human_match_requires_fire_input_to_exit(self):
        from src.winnermenu import WinnerMenu
        from src.player import Player
        from src.common import GameState
        
        self.game.players[0] = self.MockPlayer("P1", 100)
        self.game.has_humans = True
        
        class MockWinnerMenu(WinnerMenu):
            def update_background(self, time): pass
            
        menu = MockWinnerMenu(self.game)
        
        # Pass 2.0 seconds, delay goes <= 0. No FIRE input.
        state1 = menu.update(2.0)
        self.assertEqual(state1, GameState.CURRENT_STATE)
        self.assertFalse(self.game.players_deleted)
        
        # Now press FIRE
        self.game.players[0].commands[Player.CMD_FIRE] = True
        state2 = menu.update(0.0)
        self.assertEqual(state2, GameState.MAIN_MENU)
        self.assertTrue(self.game.players_deleted)

class ScoreMenuFidelityTests(unittest.TestCase):
    def setUp(self):
        import pygame
        self.original_get_pressed = pygame.key.get_pressed
        pygame.key.get_pressed = lambda: {pygame.K_SPACE: False, pygame.K_RETURN: False}
        
        class FakeGame:
            def __init__(self):
                self.players = [None] * 8
                self.has_humans = True
                self.num_rounds = 5
                self.current_round = 1
            def get_players(self): return self.players
            def get_num_of_players(self): return len(self.players)
            def are_human_players(self): return self.has_humans
            def get_num_of_rounds(self): return self.num_rounds
            def get_current_round(self): return self.current_round
            
            def get_font(self): return None
            def get_interface(self): return None
            def get_graphics(self): return None
            def get_sound(self): return None
            def get_ui(self): return None
            
        self.game = FakeGame()
        
        class MockPlayer:
            def __init__(self, name, score):
                self.name = name
                self._score = score
                self.commands = [False] * 11
                self.is_leader = False
            def get_score(self): return self._score
            def get_command(self, cmd, dummy=None): return self.commands[cmd]
            def set_leader(self, flag): self.is_leader = flag
            
        self.MockPlayer = MockPlayer

    def tearDown(self):
        import pygame
        pygame.key.get_pressed = self.original_get_pressed

    def test_score_menu_activation_delay_is_2_seconds_for_humans_and_4_for_computers(self):
        from src.scoremenu import ScoreMenu
        
        self.game.has_humans = True
        menu_human = ScoreMenu(self.game)
        self.assertEqual(menu_human._time_till_active, 2.0)
        
        self.game.has_humans = False
        menu_cpu = ScoreMenu(self.game)
        self.assertEqual(menu_cpu._time_till_active, 4.0)

    def test_score_menu_ignores_input_before_activation_delay(self):
        from src.scoremenu import ScoreMenu
        from src.player import Player
        from src.common import GameState
        
        self.game.players[0] = self.MockPlayer("P1", 100)
        self.game.players[0].commands[Player.CMD_FIRE] = True
        
        class MockScoreMenu(ScoreMenu):
            def update_background(self, time): pass
            
        menu = MockScoreMenu(self.game)
        
        state = menu.update(1.0)
        self.assertEqual(state, GameState.CURRENT_STATE)

    def test_score_menu_auto_advances_computer_only_match_after_delay(self):
        from src.scoremenu import ScoreMenu
        from src.common import GameState
        
        self.game.has_humans = False
        self.game.players[0] = self.MockPlayer("P1", 100)
        
        class MockScoreMenu(ScoreMenu):
            def update_background(self, time): pass
            
        menu = MockScoreMenu(self.game)
        
        # Passes exactly 4.0
        state2 = menu.update(4.0)
        self.assertEqual(state2, GameState.SHOP_MENU)

    def test_score_menu_human_match_requires_input_but_auto_advances_after_timeout(self):
        from src.scoremenu import ScoreMenu
        from src.common import GameState
        
        self.game.has_humans = True
        self.game.players[0] = self.MockPlayer("P1", 100)
        
        class MockScoreMenu(ScoreMenu):
            def update_background(self, time): pass
            
        menu = MockScoreMenu(self.game)
        
        # Passes 2.0 seconds, delay hits 0. No input.
        state1 = menu.update(2.0)
        self.assertEqual(state1, GameState.CURRENT_STATE)
        
        # Passes 9.9 seconds. _time_till_active is -9.9, so still waiting.
        state2 = menu.update(9.9)
        self.assertEqual(state2, GameState.CURRENT_STATE)
        
        # Passes 0.1 seconds, hits -10.0 (timeout)
        state3 = menu.update(0.1)
        self.assertEqual(state3, GameState.SHOP_MENU)

    def test_score_menu_assigns_leader_to_unique_highest_scorer(self):
        from src.scoremenu import ScoreMenu
        from src.player import Player
        
        self.game.players[0] = self.MockPlayer("P1", 100)
        self.game.players[1] = self.MockPlayer("P2", 200)
        self.game.players[2] = self.MockPlayer("P3", 150)
        self.game.players[0].commands[Player.CMD_FIRE] = True
        
        class MockScoreMenu(ScoreMenu):
            def update_background(self, time): pass
            
        menu = MockScoreMenu(self.game)
        # Advance so that input is accepted
        menu.update(2.0)
        
        # P2 is ordered_players[0]
        self.assertTrue(menu._ordered_players[0].is_leader)
        self.assertEqual(menu._ordered_players[0].name, "P2")
        self.assertFalse(menu._ordered_players[1].is_leader)
        self.assertFalse(menu._ordered_players[2].is_leader)

    def test_score_menu_removes_all_leaders_on_tie(self):
        from src.scoremenu import ScoreMenu
        from src.player import Player
        
        self.game.players[0] = self.MockPlayer("P1", 200)
        self.game.players[1] = self.MockPlayer("P2", 200)
        self.game.players[2] = self.MockPlayer("P3", 150)
        self.game.players[0].commands[Player.CMD_FIRE] = True
        
        class MockScoreMenu(ScoreMenu):
            def update_background(self, time): pass
            
        menu = MockScoreMenu(self.game)
        menu.update(2.0)
        
        self.assertFalse(menu._ordered_players[0].is_leader)
        self.assertFalse(menu._ordered_players[1].is_leader)
        self.assertFalse(menu._ordered_players[2].is_leader)

    def test_score_menu_transitions_to_winner_menu_on_last_round(self):
        from src.scoremenu import ScoreMenu
        from src.player import Player
        from src.common import GameState
        
        self.game.current_round = 5
        self.game.num_rounds = 5
        self.game.players[0] = self.MockPlayer("P1", 100)
        self.game.players[0].commands[Player.CMD_FIRE] = True
        
        class MockScoreMenu(ScoreMenu):
            def update_background(self, time): pass
            
        menu = MockScoreMenu(self.game)
        state = menu.update(2.0)
        
        self.assertEqual(state, GameState.WINNER_MENU)

if __name__ == "__main__":
    unittest.main()
