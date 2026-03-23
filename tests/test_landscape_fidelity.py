import math
import unittest

from tests.support import install_fake_pygame

install_fake_pygame()

from src.landscape import LandChunk, Landscape


class TerrainSettings:
    def __init__(self, slices=20, width=1.0, fall_pause=0.1, fall_acceleration=5.0):
        self._ints = {("Terrain", "Slices"): slices}
        self._floats = {
            ("Terrain", "Width"): width,
            ("Terrain", "FallPause"): fall_pause,
            ("Terrain", "FallAcceleration"): fall_acceleration,
        }

    def get_int(self, section, entry, default):
        return self._ints.get((section, entry), default)

    def get_float(self, section, entry, default):
        return self._floats.get((section, entry), default)


def make_chunk(max1, max2, min1, min2, linked=False):
    chunk = LandChunk()
    chunk.max_height_1 = max1
    chunk.max_height_2 = max2
    chunk.min_height_1 = min1
    chunk.min_height_2 = min2
    chunk.linked_to_next = linked
    return chunk


class LandscapeFidelityTests(unittest.TestCase):
    def test_drop_terrain_clamps_top_before_moving_bottom(self):
        landscape = Landscape(TerrainSettings(slices=2, width=1.0), 0.0)
        landscape._land_chunks = [[make_chunk(-6.9, -6.9, -8.0, -8.0)], [make_chunk(-6.0, -6.0, -7.0, -7.0)]]

        landscape.drop_terrain(0.2)

        first = landscape._land_chunks[0][0]
        self.assertEqual(first.max_height_1, -7.0)
        self.assertEqual(first.max_height_2, -7.0)
        self.assertEqual(first.min_height_1, -8.0)
        self.assertEqual(first.min_height_2, -8.0)

    def test_move_to_ground_at_angle_traces_across_slices(self):
        landscape = Landscape(TerrainSettings(slices=2, width=1.0), 0.0)
        landscape._land_chunks = [
            [make_chunk(0.0, 0.0, -1.0, -1.0)],
            [make_chunk(0.0, 0.0, -1.0, -1.0)],
        ]

        x, y = landscape.move_to_ground_at_angle(0.75, -0.5, -(math.pi / 4.0))

        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, -0.25)

    def test_clip_slice_splits_chunk_and_marks_upper_piece_as_falling(self):
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        landscape._land_chunks[target_slice] = [make_chunk(1.0, 1.0, -1.0, -1.0)]

        landscape.clip_slice(target_slice, 0.05, 0.0, 0.2)

        self.assertEqual(len(landscape._land_chunks[target_slice]), 2)
        upper, lower = landscape._land_chunks[target_slice]
        self.assertTrue(upper.falling_state)
        self.assertFalse(lower.falling_state)
        self.assertGreater(upper.min_height_1, 0.0)
        self.assertLess(lower.max_height_1, 0.0)


if __name__ == "__main__":
    unittest.main()
