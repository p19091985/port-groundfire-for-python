from __future__ import annotations

import cProfile
from dataclasses import dataclass
from pathlib import Path
import pstats
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common import GameState
from src.gamesimulation import GameSimulationController


@dataclass
class DummyEntity:
    x: float = 0.0

    def update(self, dt: float) -> bool:
        self.x += dt
        return True


class DummyLandscape:
    def update(self, _dt: float):
        return None


class DummyInterface:
    def get_key(self, _key: int) -> bool:
        return False


class DummyClock:
    def __init__(self):
        self.current = 0.0

    def set_time(self, value: float):
        self.current = value


class DummyStepper:
    def __init__(self, step: float):
        self.step = step

    def consume(self, frame_dt: float):
        steps = int(frame_dt / self.step)
        return tuple(self.step for _ in range(steps))


class DummyGame:
    def __init__(self, entity_count: int = 64, step: float = 1.0 / 60.0):
        self._landscape = DummyLandscape()
        self._entity_list = [DummyEntity() for _ in range(entity_count)]
        self._new_state = GameState.CURRENT_STATE
        self._game_state = GameState.ROUND_IN_ACTION
        self._state_countdown = 0.0
        self._round_stepper = DummyStepper(step)
        self._clock = DummyClock()
        self._interface = DummyInterface()
        self.pygame_module = type("PygameStub", (), {"K_ESCAPE": 27})

    def get_interface(self):
        return self._interface

    def get_clock(self):
        return self._clock

    def remove_entity(self, entity):
        self._entity_list.remove(entity)

    def _end_round(self):
        self._new_state = GameState.ROUND_SCORE


def run_profile(frame_count: int = 600, entity_count: int = 64):
    controller = GameSimulationController()
    game = DummyGame(entity_count=entity_count)
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(frame_count):
        controller.simulate_round_frame(game, 1.0 / 30.0, game.get_clock().current)
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumtime")
    stats.print_stats(20)


if __name__ == "__main__":
    run_profile()
