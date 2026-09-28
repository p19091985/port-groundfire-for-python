from __future__ import annotations

import time
from collections.abc import Callable


class HeadlessRuntime:
    def __init__(
        self,
        *,
        time_source: Callable[[], float] | None = None,
        sleep_func: Callable[[float], None] | None = None,
    ):
        self._time_source = time_source or time.monotonic
        self._sleep_func = sleep_func or time.sleep

    def now(self) -> float:
        return float(self._time_source())

    def sleep(self, duration: float):
        if duration > 0.0:
            self._sleep_func(duration)
