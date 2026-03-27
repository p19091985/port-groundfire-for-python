import unittest

from src.common import GameState
from src.gamesimulation import GameSimulationController


class InterfaceStub:
    def __init__(self, escape=False):
        self.escape = escape

    def get_key(self, key):
        return self.escape and key == 27


class ClockStub:
    def __init__(self):
        self.values = []

    def set_time(self, value):
        self.values.append(value)


class StepperStub:
    def __init__(self, steps):
        self.steps = list(steps)

    def consume(self, _frame_dt):
        return tuple(self.steps)


class LandscapeStub:
    def __init__(self):
        self.updates = []

    def update(self, dt):
        self.updates.append(dt)


class EntityStub:
    def __init__(self, *results):
        self.results = list(results or [True])
        self.updates = []

    def update(self, dt):
        self.updates.append(dt)
        if len(self.results) == 1:
            return self.results[0]
        return self.results.pop(0)


class GameStub:
    def __init__(self):
        self._landscape = LandscapeStub()
        self._entity_list = []
        self.removed = []
        self._new_state = GameState.CURRENT_STATE
        self._game_state = GameState.ROUND_IN_ACTION
        self._state_countdown = 0.0
        self._end_round_calls = 0
        self._round_stepper = StepperStub([0.02, 0.02])
        self.clock = ClockStub()
        self.interface = InterfaceStub()
        self.pygame_module = type("PygameStub", (), {"K_ESCAPE": 27})

    def remove_entity(self, entity):
        self.removed.append(entity)
        self._entity_list.remove(entity)

    def get_interface(self):
        return self.interface

    def get_clock(self):
        return self.clock

    def _end_round(self):
        self._end_round_calls += 1


class GameSimulationControllerTests(unittest.TestCase):
    def test_update_round_updates_landscape_and_removes_dead_entities(self):
        controller = GameSimulationController()
        game = GameStub()
        alive = EntityStub(True)
        dead = EntityStub(False)
        game._entity_list = [alive, dead]

        controller.update_round(game, 0.05)

        self.assertEqual(game._landscape.updates, [0.05])
        self.assertEqual(alive.updates, [0.05])
        self.assertEqual(dead.updates, [0.05])
        self.assertEqual(game.removed, [dead])

    def test_update_round_transitions_to_quit_menu_on_escape(self):
        controller = GameSimulationController()
        game = GameStub()
        game.interface.escape = True

        controller.update_round(game, 0.01)

        self.assertEqual(game._new_state, GameState.QUIT_MENU)

    def test_simulate_round_frame_advances_clock_through_fixed_steps(self):
        controller = GameSimulationController()
        game = GameStub()
        game._entity_list = [EntityStub(True, True)]

        controller.simulate_round_frame(game, 0.04, 10.0)

        self.assertEqual(game.clock.values, [10.02, 10.04, 10.04])

    def test_simulate_round_step_changes_round_state_when_countdown_expires(self):
        controller = GameSimulationController()
        game = GameStub()
        game._game_state = GameState.ROUND_STARTING
        game._state_countdown = 0.01

        controller.simulate_round_step(game, 0.02)

        self.assertEqual(game._new_state, GameState.ROUND_IN_ACTION)

    def test_simulate_round_step_ends_round_when_finish_countdown_expires(self):
        controller = GameSimulationController()
        game = GameStub()
        game._game_state = GameState.ROUND_FINISHING
        game._state_countdown = 0.01

        controller.simulate_round_step(game, 0.02)

        self.assertEqual(game._end_round_calls, 1)


if __name__ == "__main__":
    unittest.main()
