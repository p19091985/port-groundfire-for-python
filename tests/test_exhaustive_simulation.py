import unittest

from tests.support import CommandPlayer, DummySoundManager, FlatLandscape

from src.machinegunround import MachineGunRound
from src.mirv import Mirv
from src.missile import Missile
from src.shell import Shell


class ProjectileGame:
    def __init__(self, landscape=None):
        self._landscape = landscape or FlatLandscape()
        self._players = [None] * 8
        self._entities = []
        self._explosions = []
        self._time = 0.0
        self._sound = DummySoundManager()

    def add_entity(self, entity):
        self._entities.append(entity)

    def get_landscape(self):
        return self._landscape

    def get_players(self):
        return self._players

    def set_players(self, players):
        self._players = list(players) + [None] * (8 - len(players))

    def get_time(self):
        return self._time

    def set_time(self, value):
        self._time = value

    def explosion(self, *args):
        self._explosions.append(args)

    def get_interface(self):
        return None

    def get_sound(self):
        return self._sound


class HitTank:
    def __init__(self, intersect=False, lethal=False):
        self._intersect = intersect
        self._lethal = lethal
        self.damage_calls = []

    def intersect_tank(self, _x1, _y1, _x2, _y2):
        return self._intersect

    def do_damage(self, damage):
        self.damage_calls.append(damage)
        return self._lethal


class HitPlayer:
    def __init__(self, tank):
        self._tank = tank

    def get_tank(self):
        return self._tank


class ProjectileSimulationTests(unittest.TestCase):
    def test_shell_reports_miss_when_it_leaves_the_map(self):
        game = ProjectileGame(FlatLandscape(width=1.0))
        player = CommandPlayer()
        shell = Shell(game, player, 0.0, 0.0, 2.0, 0.0, 0.0, 0.25, 40.0, False)
        game.set_time(1.0)

        self.assertFalse(shell.update(0.1))
        self.assertEqual(len(player.recorded_shots), 1)
        self.assertEqual(player.recorded_shots[0][2], -1)
        self.assertEqual(game._explosions, [])

    def test_shell_ground_impact_triggers_game_explosion(self):
        landscape = FlatLandscape()
        landscape.collisions.append((True, 0.3, -0.2))
        game = ProjectileGame(landscape)
        player = CommandPlayer()
        shell = Shell(game, player, 0.0, 0.0, 1.0, 1.0, 0.0, 0.25, 40.0, False)
        game.set_time(0.2)

        self.assertFalse(shell.update(0.1))
        self.assertEqual(len(game._explosions), 1)
        self.assertEqual(game._explosions[0][4], -1)
        self.assertEqual(player.recorded_shots[-1][2], -1)

    def test_missile_explode_matches_cpp_and_does_not_record_shot(self):
        game = ProjectileGame()
        player = CommandPlayer()
        missile = Missile(game, player, 0.0, 0.0, 0.0, 0.3, 40.0)

        self.assertFalse(missile.explode(1.0, 2.0, -1))
        self.assertEqual(len(game._explosions), 1)
        self.assertEqual(player.recorded_shots, [])

    def test_mirv_splits_into_shell_fragments_at_apex(self):
        game = ProjectileGame()
        player = CommandPlayer()
        mirv = Mirv(game, player, 0.0, 0.0, 2.0, 10.0, 0.0, 0.3, 30.0)
        game.set_time(mirv._apex_time + 0.01)

        self.assertFalse(mirv.update(0.1))
        fragments = [entity for entity in game._entities if isinstance(entity, Shell)]
        self.assertEqual(len(fragments), Mirv.OPTION_Fragments)

    def test_machine_gun_round_dies_next_frame_after_ground_hit_without_recording_shot(self):
        landscape = FlatLandscape()
        landscape.collisions.append((True, 0.4, -0.1))
        game = ProjectileGame(landscape)
        player = CommandPlayer()
        round_ = MachineGunRound(game, player, 0.0, 0.0, 3.0, 2.0, 0.0, 2.0)
        game.set_time(0.2)

        self.assertTrue(round_.update(0.1))
        self.assertTrue(round_._kill_next_frame)
        self.assertEqual(player.recorded_shots, [])

        self.assertFalse(round_.update(0.1))

    def test_machine_gun_round_credits_kill_without_record_shot_side_effect(self):
        game = ProjectileGame()
        player = CommandPlayer()
        target_tank = HitTank(intersect=True, lethal=True)
        target_player = HitPlayer(target_tank)
        game.set_players([target_player])
        round_ = MachineGunRound(game, player, 0.0, 0.0, 3.0, 2.0, 0.0, 2.0)
        game.set_time(0.2)

        self.assertTrue(round_.update(0.1))
        self.assertEqual(player.defeated, [target_player])
        self.assertEqual(player.recorded_shots, [])


if __name__ == "__main__":
    unittest.main()
