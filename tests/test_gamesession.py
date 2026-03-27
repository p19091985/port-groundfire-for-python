import unittest

from src.common import GameState
from src.gamesession import GameSessionController


class ClockStub:
    def __init__(self, sampled_now=10.0):
        self.sampled_now = sampled_now
        self.reset_calls = []

    def sample_now(self):
        return self.sampled_now

    def reset(self, now):
        self.reset_calls.append(now)


class TankStub:
    def __init__(self, *, alive=True, centre=(0.0, 0.0, 0.25), lethal=False):
        self._alive = alive
        self._centre = centre
        self._lethal = lethal
        self.damage_calls = []
        self.positions = []

    def alive(self):
        return self._alive

    def get_centre(self):
        return self._centre

    def do_damage(self, damage):
        self.damage_calls.append(damage)
        return self._lethal

    def set_position_on_ground(self, x):
        self.positions.append(x)


class PlayerStub:
    def __init__(self, name, tank, *, computer=False):
        self._name = name
        self._tank = tank
        self._computer = computer
        self.new_round_calls = 0
        self.end_round_calls = 0

    def get_tank(self):
        return self._tank

    def is_computer(self):
        return self._computer

    def new_round(self):
        self.new_round_calls += 1

    def end_round(self):
        self.end_round_calls += 1


class EntityStub:
    def __init__(self, *, pre_round=True, post_round=True):
        self.pre_round = pre_round
        self.post_round = post_round

    def do_pre_round(self):
        return self.pre_round

    def do_post_round(self):
        return self.post_round


class LandscapeStub:
    def __init__(self, settings, seed):
        self.settings = settings
        self.seed = seed
        self.holes = []

    def make_hole(self, x, y, size):
        self.holes.append((x, y, size))


class GameStub:
    def __init__(self):
        self._players = [None] * 8
        self._number_of_players = 0
        self._human_players = False
        self._entity_list = []
        self._number_of_active_tanks = 0
        self._current_round = 0
        self._new_state = GameState.CURRENT_STATE
        self._state_countdown = 0.0
        self._game_state = GameState.ROUND_IN_ACTION
        self._landscape = None
        self._settings = object()
        self._controls = object()
        self.clock = ClockStub()
        self.added_entities = []
        self.removed_entities = []
        self.queued_events = []
        self.registry_resets = 0
        self.network_resets = 0
        self.registered = 0

    def add_entity(self, entity):
        self.added_entities.append(entity)
        self._entity_list.append(entity)

    def remove_entity(self, entity):
        self.removed_entities.append(entity)
        self._entity_list.remove(entity)

    def reset_entity_registry(self):
        self.registry_resets += 1

    def reset_network_session(self):
        self.network_resets += 1

    def queue_network_event(self, event_type, **payload):
        self.queued_events.append((event_type, payload))

    def ensure_registered_entities(self):
        self.registered += 1

    def get_controls(self):
        return self._controls

    def get_settings(self):
        return self._settings

    def get_clock(self):
        return self.clock


class GameSessionControllerTests(unittest.TestCase):
    def setUp(self):
        self.created_blasts = []
        self.created_sounds = []
        self.created_quakes = []

        def human_factory(game, number, name, colour, controller, controls):
            self.assertIs(game.get_controls(), controls)
            player = PlayerStub(name, TankStub(), computer=False)
            player.controller = controller
            player.colour = colour
            player.number = number
            return player

        def ai_factory(_game, number, name, colour):
            player = PlayerStub(name, TankStub(), computer=True)
            player.colour = colour
            player.number = number
            return player

        def quake_factory(_game):
            quake = object()
            self.created_quakes.append(quake)
            return quake

        def blast_factory(*args):
            self.created_blasts.append(args)
            return ("blast", args)

        def sound_entity_factory(*args):
            self.created_sounds.append(args)
            return ("sound", args)

        class DeterministicRandom:
            @staticmethod
            def randint(_a, _b):
                return 0

        self.controller = GameSessionController(
            human_player_factory=human_factory,
            ai_player_factory=ai_factory,
            landscape_factory=LandscapeStub,
            quake_factory=quake_factory,
            blast_factory=blast_factory,
            sound_entity_factory=sound_entity_factory,
            rng=DeterministicRandom(),
        )

    def test_add_player_supports_human_and_ai(self):
        game = GameStub()

        self.controller.add_player(game, -1, "CPU", (1, 2, 3))
        self.controller.add_player(game, 2, "Human", (4, 5, 6))

        self.assertEqual(game._number_of_players, 2)
        self.assertTrue(game._players[0].is_computer())
        self.assertFalse(game._players[1].is_computer())
        self.assertTrue(game._human_players)
        self.assertEqual(len(game.added_entities), 2)

    def test_record_tank_death_transitions_to_round_finishing(self):
        game = GameStub()
        game._number_of_active_tanks = 2

        self.controller.record_tank_death(game)

        self.assertEqual(game._new_state, GameState.ROUND_FINISHING)
        self.assertEqual(game._state_countdown, 5.0)

    def test_start_round_creates_landscape_positions_tanks_and_resets_clock(self):
        game = GameStub()
        players = [
            PlayerStub("P1", TankStub(alive=True)),
            PlayerStub("P2", TankStub(alive=True)),
        ]
        game._players = players + [None] * 6
        game._number_of_players = 2
        survivor = EntityStub(pre_round=True)
        expired = EntityStub(pre_round=False)
        game._entity_list = [survivor, expired]

        self.controller.start_round(game)

        self.assertEqual(game._current_round, 1)
        self.assertIsInstance(game._landscape, LandscapeStub)
        self.assertEqual(game._landscape.seed, 10.0)
        self.assertEqual([player.new_round_calls for player in players], [1, 1])
        self.assertEqual(len(game._entity_list), 2)
        self.assertIn(survivor, game._entity_list)
        self.assertNotIn(expired, game._entity_list)
        self.assertEqual(players[0].get_tank().positions, [-5.0])
        self.assertEqual(players[1].get_tank().positions, [5.0])
        self.assertEqual(game._number_of_active_tanks, 2)
        self.assertEqual(game.clock.reset_calls, [10.0])
        self.assertEqual(len(self.created_quakes), 1)
        self.assertEqual(game.registered, 1)
        self.assertEqual(game.queued_events[-1][0], "round_started")

    def test_end_round_updates_players_and_cleans_entities(self):
        game = GameStub()
        players = [
            PlayerStub("P1", TankStub()),
            PlayerStub("P2", TankStub()),
        ]
        game._players = players + [None] * 6
        game._number_of_players = 2
        keep = EntityStub(post_round=True)
        drop = EntityStub(post_round=False)
        game._entity_list = [keep, drop]
        game._landscape = LandscapeStub(object(), 1.0)

        self.controller.end_round(game)

        self.assertEqual([player.end_round_calls for player in players], [1, 1])
        self.assertEqual(game._entity_list, [keep])
        self.assertIsNone(game._landscape)
        self.assertEqual(game._new_state, GameState.ROUND_SCORE)
        self.assertEqual(game.removed_entities, [drop])
        self.assertEqual(game.queued_events[-1][0], "round_finished")

    def test_explosion_creates_entities_and_applies_direct_and_splash_damage(self):
        game = GameStub()
        direct_tank = TankStub(centre=(0.0, 0.0, 0.25), lethal=True)
        splash_tank = TankStub(centre=(0.1, 0.0, 0.25), lethal=True)
        far_tank = TankStub(centre=(5.0, 0.0, 0.25), lethal=True)
        game._players = [
            PlayerStub("P1", direct_tank),
            PlayerStub("P2", splash_tank),
            PlayerStub("P3", far_tank),
            None,
            None,
            None,
            None,
            None,
        ]
        owner = type("Owner", (), {"defeat": lambda self, player: defeated.append(player)})()
        defeated = []
        game._landscape = LandscapeStub(object(), 1.0)

        self.controller.explosion(game, 0.0, 0.0, 0.5, 40.0, 0, 7, False, owner)

        self.assertEqual(game._landscape.holes, [(0.0, 0.0, 0.5)])
        self.assertEqual(len(self.created_blasts), 1)
        self.assertEqual(len(self.created_sounds), 1)
        self.assertEqual(direct_tank.damage_calls, [40.0])
        self.assertEqual(len(splash_tank.damage_calls), 1)
        self.assertEqual(far_tank.damage_calls, [])
        self.assertEqual(defeated, [game._players[0], game._players[1]])
        self.assertEqual(game.queued_events[-1][0], "explosion")

    def test_delete_players_resets_entity_registry(self):
        game = GameStub()

        self.controller.delete_players(game)

        self.assertEqual(game.registry_resets, 1)
        self.assertEqual(game.network_resets, 1)
        self.assertEqual(game.queued_events[-1][0], "players_deleted")


if __name__ == "__main__":
    unittest.main()
