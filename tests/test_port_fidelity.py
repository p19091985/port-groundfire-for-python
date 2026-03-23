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
from src.player import Player
from src.soundentity import SoundEntity
from src.tank import Tank


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
