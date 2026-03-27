import unittest

from src.commandintents import ALL_PLAYER_COMMANDS, PlayerCommand, PlayerIntentFrame, PlayerIntentQueue


class CommandIntentTests(unittest.TestCase):
    def test_frame_from_iterable_pads_missing_commands_and_exports_dict(self):
        frame = PlayerIntentFrame.from_iterable(
            [True, False, True],
            source="human:0",
            simulation_time=12.5,
        )

        self.assertTrue(frame.is_pressed(PlayerCommand.FIRE))
        self.assertFalse(frame.is_pressed(PlayerCommand.WEAPONUP))
        self.assertTrue(frame.is_pressed(PlayerCommand.WEAPONDOWN))
        self.assertEqual(len(frame.commands), len(ALL_PLAYER_COMMANDS))
        self.assertEqual(frame.to_dict()["fire"], True)
        self.assertEqual(frame.to_dict()["shield"], False)

    def test_queue_returns_latest_and_drain_clears_frames(self):
        queue = PlayerIntentQueue()
        frame_a = PlayerIntentFrame.empty(source="a", simulation_time=1.0)
        frame_b = PlayerIntentFrame.from_iterable([True], source="b", simulation_time=2.0)

        queue.publish(frame_a)
        queue.publish(frame_b)

        self.assertIs(queue.latest(), frame_b)
        self.assertEqual(queue.drain(), (frame_a, frame_b))
        self.assertIsNone(queue.latest())


if __name__ == "__main__":
    unittest.main()
