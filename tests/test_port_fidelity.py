import math
import os
import unittest
from unittest.mock import patch

from tests.support import (
    PROJECT_ROOT,
    CommandPlayer,
    DummyGameForTank,
    RecordingWeapon,
)

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


if __name__ == "__main__":
    unittest.main()
