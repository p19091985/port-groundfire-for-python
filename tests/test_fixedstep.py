import unittest

from src.fixedstep import FixedStepRunner


class FixedStepRunnerTests(unittest.TestCase):
    def test_consume_returns_multiple_steps_and_keeps_remainder(self):
        runner = FixedStepRunner(step=0.02, max_substeps=8)

        steps = runner.consume(0.05)

        self.assertEqual(steps, [0.02, 0.02])
        self.assertAlmostEqual(runner.get_accumulator(), 0.01)

    def test_remainder_is_consumed_on_next_frame(self):
        runner = FixedStepRunner(step=0.02, max_substeps=8)
        runner.consume(0.05)

        steps = runner.consume(0.01)

        self.assertEqual(steps, [0.02])
        self.assertAlmostEqual(runner.get_accumulator(), 0.0, places=7)

    def test_spiral_of_death_is_capped(self):
        runner = FixedStepRunner(step=0.02, max_substeps=2)

        steps = runner.consume(0.20)

        self.assertEqual(steps, [0.02, 0.02])
        self.assertLessEqual(runner.get_accumulator(), runner.get_step())


if __name__ == "__main__":
    unittest.main()
