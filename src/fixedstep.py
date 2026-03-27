from __future__ import annotations


class FixedStepRunner:
    def __init__(self, *, step: float, max_substeps: int = 8):
        if step <= 0.0:
            raise ValueError("step must be positive")
        if max_substeps < 1:
            raise ValueError("max_substeps must be at least 1")

        self._step = float(step)
        self._max_substeps = int(max_substeps)
        self._accumulator = 0.0

    def reset(self):
        self._accumulator = 0.0

    def consume(self, frame_delta: float) -> list[float]:
        if frame_delta > 0.0:
            self._accumulator += frame_delta

        steps: list[float] = []
        while self._accumulator + 1.0e-9 >= self._step and len(steps) < self._max_substeps:
            steps.append(self._step)
            self._accumulator -= self._step

        if len(steps) == self._max_substeps and self._accumulator > self._step:
            self._accumulator = self._step

        return steps

    def get_accumulator(self) -> float:
        return self._accumulator

    def get_step(self) -> float:
        return self._step
