from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ClockTick:
    now: float
    raw_delta: float
    delta: float
    simulation_time: float
    fps: float


class GameClock:
    def __init__(
        self,
        time_source: Callable[[], float] | None = None,
        *,
        max_frame_time: float = 0.1,
        fps_sample_size: int = 20,
    ):
        self._time_source = time_source or time.perf_counter
        self._max_frame_time = max_frame_time
        self._fps_sample_size = fps_sample_size

        self._last_time: float | None = None
        self._simulation_time = 0.0
        self._frame_measure_count = fps_sample_size
        self._frame_measure_time = 0.0
        self._current_fps = 0.0

    def sample_now(self) -> float:
        return float(self._time_source())

    def prime(self, now: float | None = None) -> float:
        if now is None:
            now = self.sample_now()
        self._last_time = float(now)
        return self._last_time

    def reset(self, now: float | None = None, *, simulation_time: float = 0.0) -> float:
        sampled_now = self.prime(now)
        self._simulation_time = simulation_time
        self._frame_measure_count = self._fps_sample_size
        self._frame_measure_time = 0.0
        self._current_fps = 0.0
        return sampled_now

    def tick(self, now: float | None = None) -> ClockTick:
        if now is None:
            now = self.sample_now()
        now = float(now)

        if self._last_time is None:
            self._last_time = now

        raw_delta = now - self._last_time
        self._last_time = now

        if raw_delta < 0.0:
            raw_delta = 0.0

        delta = min(raw_delta, self._max_frame_time)
        self._simulation_time += delta

        if self._frame_measure_count == 0:
            if self._frame_measure_time > 0.0:
                self._current_fps = self._fps_sample_size / self._frame_measure_time
            self._frame_measure_time = 0.0
            self._frame_measure_count = self._fps_sample_size
        else:
            self._frame_measure_time += raw_delta
            self._frame_measure_count -= 1

        return ClockTick(
            now=now,
            raw_delta=raw_delta,
            delta=delta,
            simulation_time=self._simulation_time,
            fps=self._current_fps,
        )

    def get_time(self) -> float:
        return self._simulation_time

    def set_time(self, value: float):
        self._simulation_time = float(value)

    def get_fps(self) -> float:
        return self._current_fps

    def get_last_time(self) -> float | None:
        return self._last_time
