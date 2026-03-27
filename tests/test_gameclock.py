import unittest

from src.gameclock import GameClock


class FakeTimeSource:
    def __init__(self, values):
        self._values = list(values)
        self._last = self._values[-1]

    def __call__(self):
        if self._values:
            self._last = self._values.pop(0)
        return self._last


class GameClockTests(unittest.TestCase):
    def test_tick_clamps_large_frames_and_accumulates_simulation_time(self):
        clock = GameClock(time_source=FakeTimeSource([10.0, 10.5, 10.55]), max_frame_time=0.1)
        clock.reset()

        first = clock.tick()
        second = clock.tick()

        self.assertAlmostEqual(first.raw_delta, 0.5)
        self.assertAlmostEqual(first.delta, 0.1)
        self.assertAlmostEqual(first.simulation_time, 0.1)
        self.assertAlmostEqual(second.raw_delta, 0.05)
        self.assertAlmostEqual(second.delta, 0.05)
        self.assertAlmostEqual(second.simulation_time, 0.15)

    def test_tick_ignores_negative_time_jumps(self):
        clock = GameClock(time_source=FakeTimeSource([20.0, 19.5]), max_frame_time=0.1)
        clock.reset()

        tick = clock.tick()

        self.assertEqual(tick.raw_delta, 0.0)
        self.assertEqual(tick.delta, 0.0)
        self.assertEqual(tick.simulation_time, 0.0)

    def test_fps_is_reported_after_sample_window(self):
        values = [0.0]
        current = 0.0
        for _ in range(21):
            current += 0.05
            values.append(current)

        clock = GameClock(time_source=FakeTimeSource(values), fps_sample_size=20)
        clock.reset()

        last_tick = None
        for _ in range(21):
            last_tick = clock.tick()

        self.assertIsNotNone(last_tick)
        self.assertAlmostEqual(last_tick.fps, 20.0, places=4)


if __name__ == "__main__":
    unittest.main()
