from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ServerLoopConfig:
    tick_hz: float = 60.0
    max_ticks: int | None = None


class NativeServerLoop:
    """Tiny reusable fixed-rate server loop.

    The game supplies poll/step callbacks; this module only owns timing.
    """

    def __init__(
        self,
        *,
        poll_network: Callable[[], None],
        step_simulation: Callable[[], None],
        now: Callable[[], float],
        sleep: Callable[[float], None],
    ):
        self._poll_network = poll_network
        self._step_simulation = step_simulation
        self._now = now
        self._sleep = sleep

    def run(self, config: ServerLoopConfig = ServerLoopConfig()) -> int:
        ticks = 0
        tick_duration = 1.0 / float(config.tick_hz)
        while config.max_ticks is None or ticks < config.max_ticks:
            start = self._now()
            self._poll_network()
            self._step_simulation()
            ticks += 1
            elapsed = self._now() - start
            self._sleep(tick_duration - elapsed)
        return 0
