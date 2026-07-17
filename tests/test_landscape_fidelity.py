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

    def test_drop_terrain_left_top_clamp_gates_both_bottom_edges(self):
        # Fidelity target: Landscape.drop_terrain() lines 653-668 (Python).
        #
        # The classic code clamps both top edges independently, but the two
        # bottom edges are both gated by max_height_1 after that clamp. If only
        # the left top reaches MIN_LAND_HEIGHT, even a still-raised right side
        # leaves both bottoms unchanged for that tick.
        landscape = Landscape(TerrainSettings(slices=1, width=1.0), 0.0)
        landscape._land_chunks = [[make_chunk(-6.9, -6.0, -8.0, -7.5)]]

        landscape.drop_terrain(0.2)

        result = landscape._land_chunks[0][0]
        self.assertEqual(result.max_height_1, -7.0)
        self.assertAlmostEqual(result.max_height_2, -6.2)
        self.assertEqual(result.min_height_1, -8.0)
        self.assertEqual(result.min_height_2, -7.5)

    def test_move_to_ground_at_angle_traces_across_slices(self):
        landscape = Landscape(TerrainSettings(slices=2, width=1.0), 0.0)
        landscape._land_chunks = [
            [make_chunk(0.0, 0.0, -1.0, -1.0)],
            [make_chunk(0.0, 0.0, -1.0, -1.0)],
        ]

        x, y = landscape.move_to_ground_at_angle(0.75, -0.5, -(math.pi / 4.0))

        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, -0.25)

    def test_move_to_ground_selects_lower_chunk_from_query_height(self):
        # Fidelity target: Landscape.move_to_ground() lines 438-458
        # (Python). The query y decides which stacked chunk can be landed on:
        # once the query is below an upper cap, the search skips that cap and
        # resolves against the lower chunk instead of always returning the
        # highest terrain surface.
        landscape = Landscape(TerrainSettings(slices=1, width=1.0), 0.0)
        landscape._land_chunks = [[
            make_chunk(8.0, 8.0, 6.0, 6.0),
            make_chunk(4.0, 4.0, 0.0, 0.0),
        ]]

        self.assertAlmostEqual(landscape.move_to_ground(0.0, 100.0), 8.0)
        self.assertAlmostEqual(landscape.move_to_ground(0.0, 7.0), 8.0)
        self.assertAlmostEqual(landscape.move_to_ground(0.0, 5.0), 4.0)
        self.assertAlmostEqual(landscape.move_to_ground(0.0, 2.0), 4.0)

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



    def test_update_multi_superblock_merge_landing_inherits_lower_motion(self):
        # Fidelity target: Landscape.update() lines 177-188, the branch where
        # end_super_idx != start_super_idx.
        #
        # A two-chunk linked superblock (cap linked to connector) falls as a unit.
        # When the connector's bottom reaches the lower resting chunk and both colours
        # match (uniform-colour blocks), the connector is deleted, the lower chunk's top
        # moves up to meet the connector's top, and the cap (superblock leader) inherits
        # the lower chunk's fall/speed/wait state.
        #
        # This is distinct from the single-chunk merge case (end_super_idx == start_super_idx)
        # already tested elsewhere in the fidelity suite.
        from src.landscape import Colour

        landscape = Landscape(TerrainSettings(slices=1, width=1.0, fall_acceleration=0.0), 0.0)

        # cap: top of superblock, linked to connector, falling with speed=60 so it
        # can cover the gap (connector.min=4.0, lower.max=4.0 → gap=0) in any tick.
        cap = make_chunk(max1=0.0, max2=0.0, min1=2.0, min2=2.0, linked=True)
        cap.falling_state = True
        cap.wait_for_fall_time = 0.0
        cap.falling_speed = 60.0
        # uniform colour → merge path
        cap.max_colour_1 = Colour(0.5, 0.5, 0.0)
        cap.max_colour_2 = Colour(0.5, 0.5, 0.0)
        cap.min_colour_1 = Colour(0.5, 0.5, 0.0)
        cap.min_colour_2 = Colour(0.5, 0.5, 0.0)

        # connector: bottom of superblock, not linked further, same falling state
        connector = make_chunk(max1=2.0, max2=2.0, min1=4.0, min2=4.0, linked=False)
        connector.falling_state = True
        connector.wait_for_fall_time = 0.0
        connector.falling_speed = 60.0
        connector.max_colour_1 = Colour(0.5, 0.5, 0.0)
        connector.max_colour_2 = Colour(0.5, 0.5, 0.0)
        connector.min_colour_1 = Colour(0.5, 0.5, 0.0)
        connector.min_colour_2 = Colour(0.5, 0.5, 0.0)

        # lower: resting chunk directly below connector, compatible uniform colour
        lower = make_chunk(max1=4.0, max2=4.0, min1=8.0, min2=8.0, linked=False)
        lower.falling_state = False
        lower.wait_for_fall_time = 0.0
        lower.falling_speed = 0.0
        lower.max_colour_1 = Colour(0.5, 0.5, 0.0)
        lower.max_colour_2 = Colour(0.5, 0.5, 0.0)
        lower.min_colour_1 = Colour(0.5, 0.5, 0.0)
        lower.min_colour_2 = Colour(0.5, 0.5, 0.0)

        landscape._land_chunks[0] = [cap, connector, lower]
        # connector.min (4.0) is already touching lower.max (4.0) → gap is zero.
        # A single update tick of any length causes both sides to be at rest immediately.
        landscape.update(0.01)

        chunks = landscape._land_chunks[0]
        # The connector is merged into the lower chunk and deleted; only cap + lower remain.
        self.assertEqual(len(chunks), 2, "connector should be deleted after merging into lower chunk")
        result_cap = chunks[0]
        result_lower = chunks[1]
        # lower.max absorbs connector.max (2.0)
        self.assertAlmostEqual(result_lower.max_height_1, 2.0,
                               msg="lower chunk top should be raised to connector's top")
        self.assertAlmostEqual(result_lower.max_height_2, 2.0,
                               msg="lower chunk top_2 should be raised to connector's top")
        # cap inherits the lower chunk's (now resting) state
        self.assertFalse(result_cap.falling_state,
                         msg="cap should inherit resting state from lower chunk after merge")
        self.assertAlmostEqual(result_cap.falling_speed, 0.0,
                               msg="cap speed should be reset from lower chunk's speed")
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.0,
                               msg="cap wait_for_fall_time should be reset from lower chunk")

    def test_update_non_merge_landing_links_and_inherits_resting_state(self):
        # Fidelity target: Landscape.update() lines 190-198 (Python), the else-branch after
        # the colour-match check (lines 170-172).
        #
        # When a falling chunk lands (both sides at rest) on a lower resting chunk whose
        # colour is NOT a uniform match, the landing chunk must NOT be deleted.  Instead:
        #   - chunks[end_super_idx].linked_to_next is set to True
        #   - chunks[start_super_idx] (the superblock leader) inherits the lower chunk's
        #     motion: falling_state=False, falling_speed=0.0, wait_for_fall_time=0.0
        #
        # This stops the fall cleanly without merging and without leaving the chunk in a
        # perpetually-falling state.
        from src.landscape import Colour

        landscape = Landscape(TerrainSettings(slices=1, width=1.0, fall_acceleration=0.0), 0.0)

        # falling chunk: two-colour (non-uniform) so merge path is excluded
        falling = make_chunk(max1=0.0, max2=0.0, min1=2.0, min2=2.0, linked=False)
        falling.falling_state = True
        falling.wait_for_fall_time = 0.0
        falling.falling_speed = 60.0
        falling.max_colour_1 = Colour(0.4, 0.4, 0.0)  # surface green
        falling.max_colour_2 = Colour(0.4, 0.4, 0.0)
        falling.min_colour_1 = Colour(0.8, 0.8, 0.0)  # base yellow — differs from max
        falling.min_colour_2 = Colour(0.8, 0.8, 0.0)

        # resting lower chunk: directly below (gap = 0), different colour from falling's bottom
        lower = make_chunk(max1=2.0, max2=2.0, min1=8.0, min2=8.0, linked=False)
        lower.falling_state = False
        lower.wait_for_fall_time = 0.0
        lower.falling_speed = 0.0
        lower.max_colour_1 = Colour(0.8, 0.8, 0.0)
        lower.max_colour_2 = Colour(0.8, 0.8, 0.0)
        lower.min_colour_1 = Colour(0.8, 0.8, 0.0)
        lower.min_colour_2 = Colour(0.8, 0.8, 0.0)

        landscape._land_chunks[0] = [falling, lower]
        # Gap is 0 → lands immediately on first tick.
        landscape.update(0.01)

        chunks = landscape._land_chunks[0]
        # The falling chunk should still exist (not deleted), linked to the lower chunk.
        self.assertEqual(len(chunks), 2, "falling chunk should remain (non-merge path)")
        result_falling = chunks[0]
        result_lower = chunks[1]

        # falling chunk links down to lower chunk
        self.assertTrue(result_falling.linked_to_next,
                        msg="landed chunk should be linked_to_next (non-merge path)")
        # leader inherits resting state from lower chunk
        self.assertFalse(result_falling.falling_state,
                         msg="landed chunk should inherit falling_state=False from lower chunk")
        self.assertAlmostEqual(result_falling.falling_speed, 0.0,
                               msg="landed chunk speed should be set to lower chunk's speed (0)")
        self.assertAlmostEqual(result_falling.wait_for_fall_time, 0.0,
                               msg="landed chunk wait should be set to lower chunk's wait (0)")
        # lower chunk is unchanged
        self.assertAlmostEqual(result_lower.max_height_1, 2.0,
                               msg="lower chunk top should be unchanged in non-merge path")

    def test_update_near_uniform_colours_do_not_merge_on_landing(self):
        # Fidelity target: Landscape.update() lines 170-172 (Python).
        #
        # The classic merge branch uses exact Colour equality. A falling chunk
        # whose top and bottom colours are close but not identical must take the
        # non-merge landing path: it links to the support and inherits the
        # support's motion instead of being deleted into it.
        from src.landscape import Colour

        landscape = Landscape(TerrainSettings(slices=1, width=1.0, fall_acceleration=0.0), 0.0)

        falling = make_chunk(max1=0.0, max2=0.0, min1=2.0, min2=2.0, linked=False)
        falling.falling_state = True
        falling.wait_for_fall_time = 0.0
        falling.falling_speed = 60.0
        falling.max_colour_1 = Colour(0.50, 0.50, 0.00)
        falling.max_colour_2 = Colour(0.50, 0.50, 0.00)
        falling.min_colour_1 = Colour(0.52, 0.50, 0.00)
        falling.min_colour_2 = Colour(0.52, 0.50, 0.00)

        lower = make_chunk(max1=2.0, max2=2.0, min1=8.0, min2=8.0, linked=False)
        lower.falling_state = False
        lower.wait_for_fall_time = 0.0
        lower.falling_speed = 0.0
        lower.max_colour_1 = Colour(0.52, 0.50, 0.00)
        lower.max_colour_2 = Colour(0.52, 0.50, 0.00)
        lower.min_colour_1 = Colour(0.52, 0.50, 0.00)
        lower.min_colour_2 = Colour(0.52, 0.50, 0.00)

        landscape._land_chunks[0] = [falling, lower]
        landscape.update(0.01)

        chunks = landscape._land_chunks[0]
        self.assertEqual(len(chunks), 2, "near-uniform colours should not merge in the classic branch")
        result_falling, result_lower = chunks
        self.assertTrue(result_falling.linked_to_next)
        self.assertFalse(result_falling.falling_state)
        self.assertAlmostEqual(result_falling.falling_speed, 0.0)
        self.assertAlmostEqual(result_falling.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result_lower.max_height_1, 2.0)

    def test_update_uniform_chunk_merges_with_falling_support_and_inherits_motion(self):
        # Fidelity target: Landscape.update() lines 169-188 (Python).
        #
        # The classic merge branch only checks that the landing chunk's own
        # vertical colours are uniform. It still merges when the lower support is
        # falling, and the merged terrain keeps that lower support's motion.
        from src.landscape import Colour

        landscape = Landscape(TerrainSettings(slices=1, width=1.0, fall_acceleration=0.0), 0.0)

        falling = make_chunk(max1=0.0, max2=0.0, min1=2.0, min2=2.0, linked=False)
        falling.falling_state = True
        falling.wait_for_fall_time = 0.0
        falling.falling_speed = 60.0
        falling.max_colour_1 = Colour(0.5, 0.5, 0.0)
        falling.max_colour_2 = Colour(0.5, 0.5, 0.0)
        falling.min_colour_1 = Colour(0.5, 0.5, 0.0)
        falling.min_colour_2 = Colour(0.5, 0.5, 0.0)

        support = make_chunk(max1=2.0, max2=2.0, min1=8.0, min2=8.0, linked=False)
        support.falling_state = True
        support.wait_for_fall_time = 0.25
        support.falling_speed = 42.0
        support.max_colour_1 = Colour(0.1, 0.2, 0.3)
        support.max_colour_2 = Colour(0.1, 0.2, 0.3)
        support.min_colour_1 = Colour(0.1, 0.2, 0.3)
        support.min_colour_2 = Colour(0.1, 0.2, 0.3)

        landscape._land_chunks[0] = [falling, support]
        landscape.update(0.01)

        chunks = landscape._land_chunks[0]
        self.assertEqual(len(chunks), 1, "uniform falling chunk should merge into falling support")
        result = chunks[0]
        self.assertAlmostEqual(result.max_height_1, 0.0)
        self.assertAlmostEqual(result.max_height_2, 0.0)
        self.assertAlmostEqual(result.min_height_1, 8.0)
        self.assertAlmostEqual(result.min_height_2, 8.0)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(result.falling_speed, 42.0)

    def test_update_uniform_multi_chunk_merge_with_falling_support_updates_leader(self):
        # Fidelity target: Landscape.update() lines 177-188 (Python).
        #
        # When the bottom chunk of a linked falling superblock merges into a
        # still-falling support, the superblock leader inherits that support's
        # motion after the bottom chunk is deleted.
        from src.landscape import Colour

        landscape = Landscape(TerrainSettings(slices=1, width=1.0, fall_acceleration=0.0), 0.0)

        cap = make_chunk(max1=0.0, max2=0.0, min1=2.0, min2=2.0, linked=True)
        cap.falling_state = True
        cap.wait_for_fall_time = 0.0
        cap.falling_speed = 60.0
        cap.max_colour_1 = Colour(0.5, 0.5, 0.0)
        cap.max_colour_2 = Colour(0.5, 0.5, 0.0)
        cap.min_colour_1 = Colour(0.5, 0.5, 0.0)
        cap.min_colour_2 = Colour(0.5, 0.5, 0.0)

        connector = make_chunk(max1=2.0, max2=2.0, min1=4.0, min2=4.0, linked=False)
        connector.falling_state = True
        connector.wait_for_fall_time = 0.0
        connector.falling_speed = 60.0
        connector.max_colour_1 = Colour(0.5, 0.5, 0.0)
        connector.max_colour_2 = Colour(0.5, 0.5, 0.0)
        connector.min_colour_1 = Colour(0.5, 0.5, 0.0)
        connector.min_colour_2 = Colour(0.5, 0.5, 0.0)

        support = make_chunk(max1=4.0, max2=4.0, min1=8.0, min2=8.0, linked=False)
        support.falling_state = True
        support.wait_for_fall_time = 0.25
        support.falling_speed = 42.0
        support.max_colour_1 = Colour(0.1, 0.2, 0.3)
        support.max_colour_2 = Colour(0.1, 0.2, 0.3)
        support.min_colour_1 = Colour(0.1, 0.2, 0.3)
        support.min_colour_2 = Colour(0.1, 0.2, 0.3)

        landscape._land_chunks[0] = [cap, connector, support]
        landscape.update(0.01)

        chunks = landscape._land_chunks[0]
        self.assertEqual(len(chunks), 2, "connector should merge into falling support")
        result_cap, result_support = chunks
        self.assertTrue(result_cap.linked_to_next)
        self.assertTrue(result_cap.falling_state)
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(result_cap.falling_speed, 42.0)
        self.assertAlmostEqual(result_support.max_height_1, 2.0)
        self.assertAlmostEqual(result_support.max_height_2, 2.0)
        self.assertTrue(result_support.falling_state)
        self.assertAlmostEqual(result_support.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(result_support.falling_speed, 42.0)

    def test_update_fall_wait_preserves_speed_and_defers_motion_for_whole_tick(self):
        # Fidelity target: Landscape.update() lines 137-139 (Python).
        #
        # While wait_for_fall_time is positive, the classic update path only subtracts
        # the current frame time. It does not move the chunk, does not accelerate it,
        # does not zero its existing falling_speed, and does not consume leftover time
        # if the wait crosses below zero during that frame.
        landscape = Landscape(TerrainSettings(slices=1, width=1.0, fall_acceleration=10.0), 0.0)
        falling = make_chunk(max1=0.0, max2=0.0, min1=2.0, min2=2.0, linked=False)
        falling.falling_state = True
        falling.wait_for_fall_time = 0.05
        falling.falling_speed = 42.0

        landscape._land_chunks[0] = [falling]
        landscape.update(0.08)

        result = landscape._land_chunks[0][0]
        self.assertAlmostEqual(result.max_height_1, 0.0,
                               msg="chunk should not move on the tick that only clears wait")
        self.assertAlmostEqual(result.min_height_1, 2.0,
                               msg="chunk bottom should not move while wait was positive at tick start")
        self.assertAlmostEqual(result.falling_speed, 42.0,
                               msg="falling speed should be preserved while waiting")
        self.assertAlmostEqual(result.wait_for_fall_time, -0.03,
                               msg="classic code subtracts time without clamping wait to zero")

        landscape.update(0.1)
        moved = landscape._land_chunks[0][0]
        self.assertAlmostEqual(moved.max_height_1, -4.2,
                               msg="the preserved speed should drive the next frame's fall")
        self.assertAlmostEqual(moved.falling_speed, 43.0,
                               msg="acceleration applies only on the later moving frame")

    def test_clip_slice_removed_linked_chunk_promotes_clipped_top_to_next_chunk(self):
        # Fidelity target: Landscape.clip_slice() lines 286-410 (Python).
        #
        # If a linked cap is fully removed, the following chunk inherits the cap's
        # already-clipped top height, not the original pre-blast top. This keeps the
        # exposed lower terrain edge aligned to the crater surface.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(1.0, 1.0, -1.0, -1.0, linked=True)
        base = make_chunk(-1.0, -1.0, -5.0, -5.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = 0.0
        blast_radius = 1.2
        expected_left_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)
        expected_right_top = landscape.clip_height(blast_x, blast_y, blast_radius, x2, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1, "fully clipped linked cap should be deleted")
        result_base = chunks[0]
        self.assertAlmostEqual(result_base.max_height_1, expected_left_top)
        self.assertAlmostEqual(result_base.max_height_2, expected_right_top)
        self.assertNotAlmostEqual(result_base.max_height_1, 1.0,
                                  msg="base top should not keep the removed cap's original top")

    def test_clip_slice_one_sided_top_cut_preserves_opposite_edge(self):
        # Fidelity target: Landscape.clip_slice() lines 280-288 (Python), the
        # top_code in (3, 6, 7) branch.
        #
        # When only the left top edge is inside the blast and the right top edge is
        # horizontally outside it, Python lowers only the left top edge to the
        # lower crater boundary. The opposite side and the bottom edge remain intact.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(0.0, 5.0, -5.0, -5.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = x1
        blast_y = 0.0
        blast_radius = 0.02
        expected_left_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.max_height_1, expected_left_top)
        self.assertAlmostEqual(result.max_height_2, 5.0)
        self.assertAlmostEqual(result.min_height_1, -5.0)
        self.assertAlmostEqual(result.min_height_2, -5.0)
        self.assertFalse(result.falling_state)

    def test_clip_slice_right_top_cut_preserves_opposite_edge(self):
        # Fidelity target: Landscape.clip_slice() lines 285-288 (Python), the
        # top_code in (9, 12, 13) branch.
        #
        # This is the right-edge mirror of the previous regression: if only the
        # right top edge is inside the blast and the left top edge is horizontally
        # outside it, Python lowers only the right top edge.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 0.0, -5.0, -5.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = x2
        blast_y = 0.0
        blast_radius = 0.02
        expected_right_top = landscape.clip_height(blast_x, blast_y, blast_radius, x2, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.max_height_1, 5.0)
        self.assertAlmostEqual(result.max_height_2, expected_right_top)
        self.assertAlmostEqual(result.min_height_1, -5.0)
        self.assertAlmostEqual(result.min_height_2, -5.0)
        self.assertFalse(result.falling_state)

    def test_clip_slice_top_code_6_cuts_left_top_without_inside_endpoint(self):
        # Fidelity target: Landscape.clip_slice() lines 280-284 (Python), the
        # top_code = 6 case (state2 = 1, state1 = 2).
        #
        # The classic endpoint-state logic still cuts the left top edge even
        # when neither top endpoint is inside the circular blast. This protects
        # the discrete Pygame branch from being replaced by a purely continuous
        # "middle graze means no-op" interpretation.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(0.0, -0.2, -5.0, -5.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = -0.1
        blast_radius = 0.06
        expected_left_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.max_height_1, expected_left_top)
        self.assertAlmostEqual(result.max_height_2, -0.2)
        self.assertAlmostEqual(result.min_height_1, -5.0)
        self.assertAlmostEqual(result.min_height_2, -5.0)
        self.assertFalse(result.falling_state)

    def test_clip_slice_top_code_9_cuts_right_top_without_inside_endpoint(self):
        # Fidelity target: Landscape.clip_slice() lines 285-288 (Python), the
        # top_code = 9 mirror of the previous regression.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(-0.2, 0.0, -5.0, -5.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = -0.1
        blast_radius = 0.06
        expected_right_top = landscape.clip_height(blast_x, blast_y, blast_radius, x2, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.max_height_1, -0.2)
        self.assertAlmostEqual(result.max_height_2, expected_right_top)
        self.assertAlmostEqual(result.min_height_1, -5.0)
        self.assertAlmostEqual(result.min_height_2, -5.0)
        self.assertFalse(result.falling_state)

    def test_clip_slice_top_cut_interpolates_edge_colour(self):
        # Fidelity target: Landscape.clip_slice() lines 280-284 and
        # Landscape.calculate_colour() lines 640-649 (Python).
        #
        # When a top edge is lowered by a crater, the classic renderer also
        # moves that edge's colour down the original vertical gradient. The
        # opposite edge and bottom colour stay untouched.
        from src.landscape import Colour

        landscape = Landscape(TerrainSettings(slices=20, width=100.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(0.0, 5.0, -5.0, -5.0, linked=False)
        chunk.max_colour_1 = Colour(0.2, 0.4, 0.6)
        chunk.min_colour_1 = Colour(0.8, 0.6, 0.4)
        chunk.max_colour_2 = Colour(0.1, 0.2, 0.3)
        chunk.min_colour_2 = Colour(0.7, 0.8, 0.9)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        expected_left_top = landscape.clip_height(x1, 0.0, 1.0, x1, False)

        landscape.clip_slice(target_slice, x1, 0.0, 1.0)

        result = landscape._land_chunks[target_slice][0]
        ratio = (expected_left_top - (-5.0)) / (0.0 - (-5.0))
        self.assertAlmostEqual(result.max_colour_1.r, 0.8 + (ratio * (0.2 - 0.8)))
        self.assertAlmostEqual(result.max_colour_1.g, 0.6 + (ratio * (0.4 - 0.6)))
        self.assertAlmostEqual(result.max_colour_1.b, 0.4 + (ratio * (0.6 - 0.4)))
        self.assertAlmostEqual(result.max_colour_2.r, 0.1)
        self.assertAlmostEqual(result.max_colour_2.g, 0.2)
        self.assertAlmostEqual(result.max_colour_2.b, 0.3)
        self.assertAlmostEqual(result.min_colour_1.r, 0.8)
        self.assertAlmostEqual(result.min_colour_1.g, 0.6)
        self.assertAlmostEqual(result.min_colour_1.b, 0.4)

    def test_clip_slice_bottom_cut_interpolates_edge_colour(self):
        # Fidelity target: Landscape.clip_slice() lines 342-356 and
        # Landscape.calculate_colour() lines 640-649 (Python).
        #
        # Bottom-edge cuts use the same original vertical gradient, but update
        # the min colour while leaving the top colour untouched.
        from src.landscape import Colour

        landscape = Landscape(TerrainSettings(slices=20, width=100.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -4.0, -5.0, linked=False)
        chunk.max_colour_1 = Colour(0.2, 0.4, 0.6)
        chunk.min_colour_1 = Colour(0.8, 0.6, 0.4)
        chunk.max_colour_2 = Colour(0.1, 0.2, 0.3)
        chunk.min_colour_2 = Colour(0.7, 0.8, 0.9)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        expected_left_bottom = landscape.clip_height(x1, -4.0, 1.0, x1, True)

        landscape.clip_slice(target_slice, x1, -4.0, 1.0)

        result = landscape._land_chunks[target_slice][0]
        ratio = (expected_left_bottom - (-4.0)) / (5.0 - (-4.0))
        self.assertAlmostEqual(result.min_colour_1.r, 0.8 + (ratio * (0.2 - 0.8)))
        self.assertAlmostEqual(result.min_colour_1.g, 0.6 + (ratio * (0.4 - 0.6)))
        self.assertAlmostEqual(result.min_colour_1.b, 0.4 + (ratio * (0.6 - 0.4)))
        self.assertAlmostEqual(result.max_colour_1.r, 0.2)
        self.assertAlmostEqual(result.max_colour_1.g, 0.4)
        self.assertAlmostEqual(result.max_colour_1.b, 0.6)
        self.assertAlmostEqual(result.min_colour_2.r, 0.7)
        self.assertAlmostEqual(result.min_colour_2.g, 0.8)
        self.assertAlmostEqual(result.min_colour_2.b, 0.9)

    def test_clip_slice_two_sided_top_cut_preserves_bottom_edge(self):
        # Fidelity target: Landscape.clip_slice() lines 291-298 (Python), the
        # top_code in (11, 14, 15) branch.
        #
        # When both top edges are inside the blast, Python lowers both top edges
        # to the lower crater boundary and leaves the bottom edge/resting state
        # untouched unless a separate bottom/split branch also applies.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(0.0, 0.0, -5.0, -5.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = 0.0
        blast_radius = 0.06
        expected_left_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)
        expected_right_top = landscape.clip_height(blast_x, blast_y, blast_radius, x2, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.max_height_1, expected_left_top)
        self.assertAlmostEqual(result.max_height_2, expected_right_top)
        self.assertAlmostEqual(result.min_height_1, -5.0)
        self.assertAlmostEqual(result.min_height_2, -5.0)
        self.assertFalse(result.falling_state)

    def test_clip_slice_linked_left_top_cut_preserves_support_link(self):
        # Fidelity target: Landscape.clip_slice() lines 280-288 and 408-415
        # (Python), a top-only cut on a linked cap.
        #
        # When only the cap's left top edge is clipped and no bottom endpoint is
        # cut, Python keeps the cap linked to its support. The support should not
        # inherit motion or detach just because the cap's top contour changed.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(0.0, 5.0, -5.0, -5.0, linked=True)
        base = make_chunk(-5.0, -5.0, -10.0, -10.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x1 = landscape.get_world_x_from_slice(target_slice)
        blast_x = x1
        blast_y = 0.0
        blast_radius = 0.02
        expected_left_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        result_cap, result_base = chunks
        self.assertAlmostEqual(result_cap.max_height_1, expected_left_top)
        self.assertAlmostEqual(result_cap.max_height_2, 5.0)
        self.assertAlmostEqual(result_cap.min_height_1, -5.0)
        self.assertAlmostEqual(result_cap.min_height_2, -5.0)
        self.assertTrue(result_cap.linked_to_next)
        self.assertFalse(result_cap.falling_state)
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result_cap.falling_speed, 0.0)
        self.assertAlmostEqual(result_base.max_height_1, -5.0)
        self.assertFalse(result_base.falling_state)

    def test_clip_slice_linked_right_top_cut_preserves_support_link(self):
        # Fidelity target: Landscape.clip_slice() lines 285-288 and 408-415
        # (Python), the right-edge mirror of the linked top-only cut.
        #
        # A one-sided right top cut should preserve the linked superblock exactly
        # like the left-edge case: only the top contour changes.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(5.0, 0.0, -5.0, -5.0, linked=True)
        base = make_chunk(-5.0, -5.0, -10.0, -10.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = x2
        blast_y = 0.0
        blast_radius = 0.02
        expected_right_top = landscape.clip_height(blast_x, blast_y, blast_radius, x2, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        result_cap, result_base = chunks
        self.assertAlmostEqual(result_cap.max_height_1, 5.0)
        self.assertAlmostEqual(result_cap.max_height_2, expected_right_top)
        self.assertAlmostEqual(result_cap.min_height_1, -5.0)
        self.assertAlmostEqual(result_cap.min_height_2, -5.0)
        self.assertTrue(result_cap.linked_to_next)
        self.assertFalse(result_cap.falling_state)
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result_cap.falling_speed, 0.0)
        self.assertAlmostEqual(result_base.max_height_1, -5.0)
        self.assertFalse(result_base.falling_state)

    def test_clip_slice_one_sided_linked_bottom_cut_detaches_support(self):
        # Fidelity target: Landscape.clip_slice() lines 342-356 (Python), the
        # bottom_code in (3, 9, 11) branch with state4 == 2.
        #
        # When only the left bottom edge of a linked chunk is clipped and the right
        # bottom edge is just outside/below the blast, Python also resolves the right
        # edge through clip_height before detaching the support. The cap becomes a
        # fresh falling chunk and the support inherits the previous superblock motion.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(0.0, 0.0, -6.0, -6.0, linked=True)
        base = make_chunk(-6.0, -6.0, -11.0, -11.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        blast_x = -0.1
        blast_y = -6.0
        blast_radius = 0.2
        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        result_cap, result_base = chunks
        self.assertAlmostEqual(result_cap.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result_cap.min_height_2, expected_right_bottom)
        self.assertFalse(result_cap.linked_to_next)
        self.assertTrue(result_cap.falling_state)
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result_cap.falling_speed, 0.0)
        self.assertFalse(result_base.falling_state)
        self.assertAlmostEqual(result_base.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result_base.falling_speed, 0.0)

    def test_clip_slice_linked_left_bottom_tangent_adjusts_uncut_right_side(self):
        # Fidelity target: Landscape.clip_slice() lines 342-356 (Python), the
        # bottom_code in (3, 9, 11) branch where state4 == 2.
        #
        # The blast cuts the linked cap's left bottom edge while the right bottom
        # edge is outside/above the blast. Python still resolves the uncut right
        # side through clip_height before detaching support.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(5.0, 5.0, -4.95, -4.8, linked=True)
        base = make_chunk(-6.0, -6.0, -11.0, -11.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = -0.02
        blast_y = -4.9
        blast_radius = 0.121
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        result_cap, result_base = chunks
        self.assertAlmostEqual(result_cap.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result_cap.min_height_2, expected_right_bottom)
        self.assertFalse(result_cap.linked_to_next)
        self.assertTrue(result_cap.falling_state)
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result_cap.falling_speed, 0.0)
        self.assertFalse(result_base.falling_state)
        self.assertAlmostEqual(result_base.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result_base.falling_speed, 0.0)

    def test_clip_slice_double_split(self):
        # Fidelity target: Landscape.clip_slice() lines 361-407 (Python).
        #
        # When a blast is entirely inside a tall chunk horizontally and vertically,
        # it cuts a hole right through it, splitting the chunk into an upper piece
        # and a lower piece.
        # The upper piece (new_chunk) has min_height set to the top of the crater,
        # linked_to_next=False, falling_state=False, and is placed before the lower piece.
        # The lower piece (chunk) has max_height set to the bottom of the crater,
        # and enters the classic fall pause.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -5.0, -5.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = 0.0
        blast_radius = 0.2

        expected_crater_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_crater_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2, "chunk should be split into 2 pieces")
        upper, lower = chunks

        # Verify upper chunk
        self.assertAlmostEqual(upper.max_height_1, 5.0)
        self.assertAlmostEqual(upper.min_height_1, expected_crater_top)
        self.assertTrue(upper.falling_state, "upper chunk should be falling")
        self.assertAlmostEqual(upper.wait_for_fall_time, 0.1)
        self.assertFalse(upper.linked_to_next)

        # Verify lower chunk
        self.assertAlmostEqual(lower.max_height_1, expected_crater_bottom)
        self.assertAlmostEqual(lower.min_height_1, -5.0)
        self.assertFalse(lower.falling_state, "lower chunk should not start falling")
        self.assertAlmostEqual(lower.wait_for_fall_time, 0.0)

    def test_clip_slice_linked_double_split_preserves_lower_support_link(self):
        # Fidelity target: Landscape.clip_slice() lines 361-407 and 408-415
        # (Python), the double-split branch on a linked cap.
        #
        # Splitting a linked cap detaches the upper piece and starts its classic
        # fall pause, but the original lower remainder keeps linked_to_next=True
        # so it remains connected to the support chunk underneath.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(5.0, 5.0, -5.0, -5.0, linked=True)
        base = make_chunk(-5.0, -5.0, -10.0, -10.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = 0.0
        blast_radius = 0.2

        expected_crater_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_crater_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 3)
        upper, lower, result_base = chunks

        self.assertAlmostEqual(upper.max_height_1, 5.0)
        self.assertAlmostEqual(upper.min_height_1, expected_crater_top)
        self.assertFalse(upper.linked_to_next)
        self.assertTrue(upper.falling_state)
        self.assertAlmostEqual(upper.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(upper.falling_speed, 0.0)

        self.assertAlmostEqual(lower.max_height_1, expected_crater_bottom)
        self.assertAlmostEqual(lower.min_height_1, -5.0)
        self.assertTrue(lower.linked_to_next)
        self.assertFalse(lower.falling_state)
        self.assertAlmostEqual(lower.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(lower.falling_speed, 0.0)

        self.assertAlmostEqual(result_base.max_height_1, -5.0)
        self.assertFalse(result_base.falling_state)

    def test_clip_slice_linked_support_split_starts_superblock_leader_falling(self):
        # Fidelity target: Landscape.clip_slice() lines 361-407 (Python).
        #
        # Splitting the lower chunk of a linked superblock is different from
        # splitting the leader/cap itself. Python inserts the upper support
        # remainder under the still-linked cap, starts the superblock leader's
        # classic fall pause, and leaves both support remainders individually
        # non-falling.
        landscape = Landscape(TerrainSettings(slices=20, width=100.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(90.0, 90.0, 60.0, 60.0, linked=True)
        support = make_chunk(60.0, 60.0, 30.0, 30.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, support]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = 45.0
        blast_radius = 7.0
        expected_upper_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_lower_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 3)
        result_cap, support_upper, support_lower = chunks

        self.assertAlmostEqual(result_cap.max_height_1, 90.0)
        self.assertAlmostEqual(result_cap.min_height_1, 60.0)
        self.assertTrue(result_cap.linked_to_next)
        self.assertTrue(result_cap.falling_state)
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result_cap.falling_speed, 0.0)

        self.assertAlmostEqual(support_upper.max_height_1, 60.0)
        self.assertAlmostEqual(support_upper.min_height_1, expected_upper_bottom)
        self.assertFalse(support_upper.linked_to_next)
        self.assertFalse(support_upper.falling_state)
        self.assertAlmostEqual(support_upper.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(support_upper.falling_speed, 0.0)

        self.assertAlmostEqual(support_lower.max_height_1, expected_lower_top)
        self.assertAlmostEqual(support_lower.min_height_1, 30.0)
        self.assertFalse(support_lower.linked_to_next)
        self.assertFalse(support_lower.falling_state)
        self.assertAlmostEqual(support_lower.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(support_lower.falling_speed, 0.0)

    def test_clip_slice_falling_linked_support_split_preserves_lower_motion(self):
        # Fidelity target: Landscape.clip_slice() lines 361-407 (Python).
        #
        # Splitting the support chunk under an already-falling linked cap leaves
        # the cap/superblock leader on its existing fall motion, keeps the upper
        # support remainder non-falling, and hands the old fall wait/speed to the
        # lower support remainder.
        landscape = Landscape(TerrainSettings(slices=20, width=100.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(90.0, 90.0, 60.0, 60.0, linked=True)
        cap.falling_state = True
        cap.wait_for_fall_time = 0.25
        cap.falling_speed = 42.0
        support = make_chunk(60.0, 60.0, 30.0, 30.0, linked=False)
        support.falling_state = True
        support.wait_for_fall_time = 0.25
        support.falling_speed = 42.0
        landscape._land_chunks[target_slice] = [cap, support]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = 45.0
        blast_radius = 7.0
        expected_upper_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_lower_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 3)
        result_cap, support_upper, support_lower = chunks

        self.assertTrue(result_cap.linked_to_next)
        self.assertTrue(result_cap.falling_state)
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(result_cap.falling_speed, 42.0)

        self.assertAlmostEqual(support_upper.max_height_1, 60.0)
        self.assertAlmostEqual(support_upper.min_height_1, expected_upper_bottom)
        self.assertFalse(support_upper.linked_to_next)
        self.assertFalse(support_upper.falling_state)
        self.assertAlmostEqual(support_upper.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(support_upper.falling_speed, 0.0)

        self.assertAlmostEqual(support_lower.max_height_1, expected_lower_top)
        self.assertAlmostEqual(support_lower.min_height_1, 30.0)
        self.assertFalse(support_lower.linked_to_next)
        self.assertTrue(support_lower.falling_state)
        self.assertAlmostEqual(support_lower.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(support_lower.falling_speed, 42.0)

    def test_clip_slice_falling_linked_support_split_uses_leader_motion(self):
        # Fidelity target: Landscape.clip_slice() lines 361-407 (Python).
        #
        # The classic split branch copies motion from the superblock leader,
        # not from the support chunk being split. If the linked cap is falling
        # and the support chunk itself is still marked resting, the lower
        # support remainder still inherits the cap's fall wait/speed.
        landscape = Landscape(TerrainSettings(slices=20, width=100.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(90.0, 90.0, 60.0, 60.0, linked=True)
        cap.falling_state = True
        cap.wait_for_fall_time = 0.25
        cap.falling_speed = 42.0
        support = make_chunk(60.0, 60.0, 30.0, 30.0, linked=False)
        support.falling_state = False
        support.wait_for_fall_time = 0.0
        support.falling_speed = 0.0
        landscape._land_chunks[target_slice] = [cap, support]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = 45.0
        blast_radius = 7.0
        expected_upper_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_lower_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 3)
        result_cap, support_upper, support_lower = chunks

        self.assertTrue(result_cap.linked_to_next)
        self.assertTrue(result_cap.falling_state)
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(result_cap.falling_speed, 42.0)

        self.assertAlmostEqual(support_upper.max_height_1, 60.0)
        self.assertAlmostEqual(support_upper.min_height_1, expected_upper_bottom)
        self.assertFalse(support_upper.linked_to_next)
        self.assertFalse(support_upper.falling_state)
        self.assertAlmostEqual(support_upper.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(support_upper.falling_speed, 0.0)

        self.assertAlmostEqual(support_lower.max_height_1, expected_lower_top)
        self.assertAlmostEqual(support_lower.min_height_1, 30.0)
        self.assertFalse(support_lower.linked_to_next)
        self.assertTrue(support_lower.falling_state)
        self.assertAlmostEqual(support_lower.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(support_lower.falling_speed, 42.0)

    def test_clip_slice_falling_double_split_preserves_lower_motion(self):
        # Fidelity target: Landscape.clip_slice() lines 361-407 (Python).
        #
        # Splitting an already-falling chunk creates a detached upper cap with a
        # fresh classic fall pause, while the original lower remainder keeps the
        # source falling motion. This is the motion handoff Godot must preserve
        # when craters hit terrain that is already moving.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -5.0, -5.0, linked=False)
        chunk.falling_state = True
        chunk.wait_for_fall_time = 0.25
        chunk.falling_speed = 42.0
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = 0.0
        blast_radius = 0.2
        expected_crater_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_crater_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        upper, lower = chunks
        self.assertAlmostEqual(upper.min_height_1, expected_crater_top)
        self.assertTrue(upper.falling_state)
        self.assertAlmostEqual(upper.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(upper.falling_speed, 0.0)
        self.assertAlmostEqual(lower.max_height_1, expected_crater_bottom)
        self.assertTrue(lower.falling_state)
        self.assertAlmostEqual(lower.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(lower.falling_speed, 42.0)

    def test_clip_slice_falling_linked_double_split_preserves_lower_support_motion(self):
        # Fidelity target: Landscape.clip_slice() lines 361-407 and 408-415
        # (Python).
        #
        # Splitting a linked cap that is already falling combines two classic
        # handoffs: the detached upper piece starts a fresh fall pause, while the
        # original lower remainder stays linked to its support and keeps the
        # source falling wait/speed.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(5.0, 5.0, -5.0, -5.0, linked=True)
        cap.falling_state = True
        cap.wait_for_fall_time = 0.25
        cap.falling_speed = 42.0
        base = make_chunk(-5.0, -5.0, -10.0, -10.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = (x1 + x2) / 2.0
        blast_y = 0.0
        blast_radius = 0.2
        expected_crater_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_crater_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 3)
        upper, lower, result_base = chunks
        self.assertAlmostEqual(upper.min_height_1, expected_crater_top)
        self.assertFalse(upper.linked_to_next)
        self.assertTrue(upper.falling_state)
        self.assertAlmostEqual(upper.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(upper.falling_speed, 0.0)
        self.assertAlmostEqual(lower.max_height_1, expected_crater_bottom)
        self.assertTrue(lower.linked_to_next)
        self.assertTrue(lower.falling_state)
        self.assertAlmostEqual(lower.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(lower.falling_speed, 42.0)
        self.assertFalse(result_base.falling_state)

    def test_clip_slice_one_sided_linked_bottom_cut_with_uncut_side_above_blast(self):
        # Fidelity target: Landscape.clip_slice() lines 308-321 (Python).
        #
        # When only the right bottom is cut (state4=3) and left bottom is above
        # the blast center (state3=2), Python also clips the left bottom to the top
        # of the crater at x1, detaches the linked support, and starts the superblock falling.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -4.8, -4.95, linked=True)
        base = make_chunk(-6.0, -6.0, -11.0, -11.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk, base]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = 0.08
        blast_y = -4.9
        blast_radius = 0.1

        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        result_cap, result_base = chunks
        self.assertAlmostEqual(result_cap.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result_cap.min_height_2, expected_right_bottom)
        self.assertFalse(result_cap.linked_to_next)
        self.assertTrue(result_cap.falling_state)
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.1)

    def test_clip_slice_linked_bottom_cut_on_both_sides_detaches_support(self):
        # Fidelity target: Landscape.clip_slice() lines 322-340 (Python), the
        # bottom_code in (7, 13, 15) branch.
        #
        # When both lower edges of a linked cap are clipped by the blast, Python
        # cuts both bottom heights, detaches the linked support, and starts the
        # cap falling after the classic fall pause.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(5.0, 5.0, -4.0, -4.0, linked=True)
        base = make_chunk(-5.0, -5.0, -10.0, -10.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        blast_x = -0.1
        blast_y = -6.0
        blast_radius = 2.05
        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        result_cap, result_base = chunks
        self.assertAlmostEqual(result_cap.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result_cap.min_height_2, expected_right_bottom)
        self.assertFalse(result_cap.linked_to_next)
        self.assertTrue(result_cap.falling_state)
        self.assertAlmostEqual(result_cap.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result_cap.falling_speed, 0.0)
        self.assertFalse(result_base.falling_state)
        self.assertAlmostEqual(result_base.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result_base.falling_speed, 0.0)

    def test_clip_slice_unlinked_bottom_code_15_cuts_both_bottom_edges(self):
        # Fidelity target: Landscape.clip_slice() lines 322-340 (Python), the
        # bottom_code = 15 case (state4 = 3, state3 = 3) without linked support.
        #
        # When both lower endpoints are inside the blast, Python cuts both
        # bottom heights and starts the chunk falling. With no linked support,
        # no lower chunk inherits motion and the result remains a single chunk.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -4.0, -4.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        blast_x = -0.1
        blast_y = -6.0
        blast_radius = 2.05
        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result.min_height_2, expected_right_bottom)
        self.assertFalse(result.linked_to_next)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_unlinked_bottom_code_7_cuts_both_bottom_edges(self):
        # Fidelity target: Landscape.clip_slice() lines 322-340 (Python), the
        # bottom_code = 7 case (state4 = 1, state3 = 3) without linked support.
        #
        # A left bottom endpoint inside the blast and a right bottom endpoint
        # below the blast center still take the two-sided bottom branch: both
        # bottom heights are clipped and the single chunk starts falling.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, 0.0, -1.05, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        blast_x = 0.0
        blast_y = 0.0
        blast_radius = 1.0
        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result.min_height_2, expected_right_bottom)
        self.assertFalse(result.linked_to_next)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_unlinked_bottom_code_13_cuts_both_bottom_edges(self):
        # Fidelity target: Landscape.clip_slice() lines 322-340 (Python), the
        # bottom_code = 13 case (state4 = 3, state3 = 1) without linked support.
        #
        # This mirrors bottom_code = 7: a left bottom endpoint below the blast
        # center and a right bottom endpoint inside the blast both resolve
        # through the two-sided bottom clipping branch.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -1.05, 0.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        blast_x = 0.0
        blast_y = 0.0
        blast_radius = 1.0
        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result.min_height_2, expected_right_bottom)
        self.assertFalse(result.linked_to_next)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_unlinked_right_bottom_cut_starts_chunk_falling(self):
        # Fidelity target: Landscape.clip_slice() lines 303-321 (Python), the
        # bottom_code in (6, 12, 14) branch without linked support.
        #
        # Cutting a non-linked chunk's right bottom edge still starts that chunk
        # falling after the classic fall pause; this is not only a linked-support
        # detachment rule.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -4.0, -4.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = x2
        blast_y = -4.0
        blast_radius = 0.02
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.min_height_1, -4.0)
        self.assertAlmostEqual(result.min_height_2, expected_right_bottom)
        self.assertFalse(result.linked_to_next)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_unlinked_left_bottom_cut_starts_chunk_falling(self):
        # Fidelity target: Landscape.clip_slice() lines 342-359 (Python), the
        # bottom_code in (3, 9, 11) branch without linked support.
        #
        # This mirrors the right-bottom case: cutting only the left bottom edge
        # of a non-linked chunk still starts the classic fall pause.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -4.0, -4.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        blast_x = x1
        blast_y = -4.0
        blast_radius = 0.02
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result.min_height_2, -4.0)
        self.assertFalse(result.linked_to_next)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_bottom_code_6(self):
        # Bottom code = 6: state4 = 1 (right bottom below blast center), state3 = 2 (left bottom above blast center).
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(5.0, 5.0, 1.05, -1.05, linked=True)
        base = make_chunk(-5.0, -5.0, -10.0, -10.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        blast_x = 0.0
        blast_y = 0.0
        blast_radius = 1.0
        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        result_cap, result_base = chunks
        self.assertAlmostEqual(result_cap.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result_cap.min_height_2, expected_right_bottom)
        self.assertFalse(result_cap.linked_to_next)
        self.assertTrue(result_cap.falling_state)

    def test_clip_slice_unlinked_bottom_code_6_keeps_above_left_bottom(self):
        # Fidelity target: Landscape.clip_slice() lines 303-321 (Python), the
        # bottom_code = 6 case (state4 = 1, state3 = 2) without linked support.
        #
        # Python clips the right bottom edge and starts the chunk falling. The
        # above-blast left bottom is only adjusted in the linked-support branch,
        # so an unlinked chunk preserves it.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, 1.05, -1.05, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        blast_x = 0.0
        blast_y = 0.0
        blast_radius = 1.0
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.min_height_1, 1.05)
        self.assertAlmostEqual(result.min_height_2, expected_right_bottom)
        self.assertFalse(result.linked_to_next)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_unlinked_bottom_code_12_keeps_out_of_range_left_bottom(self):
        # Fidelity target: Landscape.clip_slice() lines 303-321 (Python), the
        # bottom_code = 12 case (state4 = 3, state3 = 0).
        #
        # When only the right bottom edge of a non-linked chunk is inside the
        # blast and the left edge is horizontally outside the blast radius,
        # Python cuts the right bottom, starts the chunk falling, and leaves the
        # left bottom edge unchanged.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -4.0, -4.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = x2
        blast_y = -4.0
        blast_radius = 0.02
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.min_height_1, -4.0)
        self.assertAlmostEqual(result.min_height_2, expected_right_bottom)
        self.assertFalse(result.linked_to_next)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_unlinked_bottom_code_14_keeps_above_left_bottom(self):
        # Fidelity target: Landscape.clip_slice() lines 303-321 (Python), the
        # bottom_code = 14 case (state4 = 3, state3 = 2) without linked support.
        #
        # Python clips the right bottom edge and starts the chunk falling, but
        # only resolves the above-blast left bottom through clip_height inside
        # the linked-support branch. For an unlinked chunk, the left bottom edge
        # remains unchanged.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -4.8, -4.95, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = 0.08
        blast_y = -4.9
        blast_radius = 0.1
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.min_height_1, -4.8)
        self.assertAlmostEqual(result.min_height_2, expected_right_bottom)
        self.assertFalse(result.linked_to_next)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_unlinked_bottom_code_11_keeps_above_right_bottom(self):
        # Fidelity target: Landscape.clip_slice() lines 342-359 (Python), the
        # bottom_code = 11 case (state4 = 2, state3 = 3) without linked support.
        #
        # This mirrors the unlinked bottom_code = 14 case: Python clips the left
        # bottom edge and starts the chunk falling, but the above-blast right
        # bottom is only resolved through clip_height inside the linked-support
        # branch. For an unlinked chunk, the right bottom remains unchanged.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -4.95, -4.8, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        blast_x = 0.02
        blast_y = -4.9
        blast_radius = 0.1
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result.min_height_2, -4.8)
        self.assertFalse(result.linked_to_next)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_one_sided_removed_linked_cap_promotes_asymmetric_top(self):
        # Fidelity target: Landscape.clip_slice() lines 280-410 (Python), a
        # linked cap removed after a one-sided top/bottom right-edge cut.
        #
        # If the right edge of a thin linked cap is fully consumed while the
        # left edge is horizontally outside the blast, Python deletes the cap.
        # The support inherits the removed cap's untouched left top and the
        # clipped right top before continuing through the same crater pass.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(-3.99, -3.99, -4.0, -4.0, linked=True)
        base = make_chunk(-4.0, -4.0, -8.0, -8.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = x2
        blast_y = -4.0
        blast_radius = 0.02
        expected_base_right_top = landscape.clip_height(blast_x, blast_y, blast_radius, x2, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result_base = chunks[0]
        self.assertAlmostEqual(result_base.max_height_1, -3.99)
        self.assertAlmostEqual(result_base.max_height_2, expected_base_right_top)
        self.assertAlmostEqual(result_base.min_height_1, -8.0)
        self.assertAlmostEqual(result_base.min_height_2, -8.0)
        self.assertFalse(result_base.linked_to_next)
        self.assertFalse(result_base.falling_state)
        self.assertAlmostEqual(result_base.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result_base.falling_speed, 0.0)

    def test_clip_slice_removed_linked_cap_promotes_top_when_opposite_side_survives(self):
        # Fidelity target: Landscape.clip_slice() lines 280-410 (Python).
        #
        # Even if the left side of a linked cap is still a tall valid edge, a
        # fully consumed right edge invalidates and deletes the whole cap.
        # Python promotes the surviving left top and the clipped right top to
        # the support chunk before that support continues through the crater pass.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(5.0, -3.99, -4.0, -4.0, linked=True)
        base = make_chunk(-4.0, -4.0, -8.0, -8.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = x2
        blast_y = -4.0
        blast_radius = 0.02
        expected_base_right_top = landscape.clip_height(blast_x, blast_y, blast_radius, x2, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result_base = chunks[0]
        self.assertAlmostEqual(result_base.max_height_1, 5.0)
        self.assertAlmostEqual(result_base.max_height_2, expected_base_right_top)
        self.assertAlmostEqual(result_base.min_height_1, -8.0)
        self.assertAlmostEqual(result_base.min_height_2, -8.0)
        self.assertFalse(result_base.linked_to_next)
        self.assertFalse(result_base.falling_state)
        self.assertAlmostEqual(result_base.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result_base.falling_speed, 0.0)

    def test_clip_slice_falling_removed_linked_cap_promotes_motion_to_support(self):
        # Fidelity target: Landscape.clip_slice() lines 303-321 and 408-415
        # (Python).
        #
        # If a falling linked cap is fully consumed by a one-sided crater, the
        # support chunk inherits both the promoted top contour and the old
        # superblock fall motion.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(-3.99, -3.99, -4.0, -4.0, linked=True)
        cap.falling_state = True
        cap.wait_for_fall_time = 0.25
        cap.falling_speed = 42.0
        base = make_chunk(-4.0, -4.0, -8.0, -8.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = x2
        blast_y = -4.0
        blast_radius = 0.02
        expected_base_right_top = landscape.clip_height(blast_x, blast_y, blast_radius, x2, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result_base = chunks[0]
        self.assertAlmostEqual(result_base.max_height_1, -3.99)
        self.assertAlmostEqual(result_base.max_height_2, expected_base_right_top)
        self.assertFalse(result_base.linked_to_next)
        self.assertTrue(result_base.falling_state)
        self.assertAlmostEqual(result_base.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(result_base.falling_speed, 42.0)

    def test_clip_slice_left_sided_removed_linked_cap_promotes_asymmetric_top(self):
        # Fidelity target: Landscape.clip_slice() lines 280-410 (Python), the
        # left-edge mirror of the removed linked cap case above.
        #
        # If the left edge of a thin linked cap is fully consumed while the
        # right edge is horizontally outside the blast, Python deletes the cap.
        # The support inherits the clipped left top and the cap's untouched
        # right top before continuing through the same crater pass.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(-3.99, -3.99, -4.0, -4.0, linked=True)
        base = make_chunk(-4.0, -4.0, -8.0, -8.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x1 = landscape.get_world_x_from_slice(target_slice)
        blast_x = x1
        blast_y = -4.0
        blast_radius = 0.02
        expected_base_left_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result_base = chunks[0]
        self.assertAlmostEqual(result_base.max_height_1, expected_base_left_top)
        self.assertAlmostEqual(result_base.max_height_2, -3.99)
        self.assertAlmostEqual(result_base.min_height_1, -8.0)
        self.assertAlmostEqual(result_base.min_height_2, -8.0)
        self.assertFalse(result_base.linked_to_next)
        self.assertFalse(result_base.falling_state)
        self.assertAlmostEqual(result_base.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result_base.falling_speed, 0.0)

    def test_clip_slice_left_falling_removed_linked_cap_promotes_motion_to_support(self):
        # Fidelity target: Landscape.clip_slice() lines 342-359 and 408-415
        # (Python), the left-edge mirror of the falling removed linked cap.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(-3.99, -3.99, -4.0, -4.0, linked=True)
        cap.falling_state = True
        cap.wait_for_fall_time = 0.25
        cap.falling_speed = 42.0
        base = make_chunk(-4.0, -4.0, -8.0, -8.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x1 = landscape.get_world_x_from_slice(target_slice)
        blast_x = x1
        blast_y = -4.0
        blast_radius = 0.02
        expected_base_left_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result_base = chunks[0]
        self.assertAlmostEqual(result_base.max_height_1, expected_base_left_top)
        self.assertAlmostEqual(result_base.max_height_2, -3.99)
        self.assertFalse(result_base.linked_to_next)
        self.assertTrue(result_base.falling_state)
        self.assertAlmostEqual(result_base.wait_for_fall_time, 0.25)
        self.assertAlmostEqual(result_base.falling_speed, 42.0)

    def test_clip_slice_left_removed_linked_cap_promotes_top_when_opposite_side_survives(self):
        # Fidelity target: Landscape.clip_slice() lines 280-410 (Python).
        #
        # This mirrors the surviving-opposite-side removal case: if the left
        # side is fully consumed, Python deletes the whole linked cap even when
        # the right side is still a tall valid edge, then promotes the clipped
        # left top and surviving right top to the support chunk.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(-3.99, 5.0, -4.0, -4.0, linked=True)
        base = make_chunk(-4.0, -4.0, -8.0, -8.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        x1 = landscape.get_world_x_from_slice(target_slice)
        blast_x = x1
        blast_y = -4.0
        blast_radius = 0.02
        expected_base_left_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result_base = chunks[0]
        self.assertAlmostEqual(result_base.max_height_1, expected_base_left_top)
        self.assertAlmostEqual(result_base.max_height_2, 5.0)
        self.assertAlmostEqual(result_base.min_height_1, -8.0)
        self.assertAlmostEqual(result_base.min_height_2, -8.0)
        self.assertFalse(result_base.linked_to_next)
        self.assertFalse(result_base.falling_state)
        self.assertAlmostEqual(result_base.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result_base.falling_speed, 0.0)

    def test_clip_slice_bottom_code_9(self):
        # Bottom code = 9: state4 = 2 (right bottom above blast center), state3 = 1 (left bottom below blast center).
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(5.0, 5.0, -1.05, 1.05, linked=True)
        base = make_chunk(-5.0, -5.0, -10.0, -10.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        blast_x = 0.0
        blast_y = 0.0
        blast_radius = 1.0
        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)
        expected_right_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x2, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        result_cap, result_base = chunks
        self.assertAlmostEqual(result_cap.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result_cap.min_height_2, expected_right_bottom)
        self.assertFalse(result_cap.linked_to_next)
        self.assertTrue(result_cap.falling_state)

    def test_clip_slice_unlinked_bottom_code_9_keeps_above_right_bottom(self):
        # Fidelity target: Landscape.clip_slice() lines 342-359 (Python), the
        # bottom_code = 9 case (state4 = 2, state3 = 1) without linked support.
        #
        # This mirrors unlinked bottom_code = 6: Python clips the left bottom
        # edge, starts the chunk falling, and preserves the above-blast right
        # bottom because there is no linked support branch.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(5.0, 5.0, -1.05, 1.05, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        blast_x = 0.0
        blast_y = 0.0
        blast_radius = 1.0
        x1 = landscape.get_world_x_from_slice(target_slice)
        expected_left_bottom = landscape.clip_height(blast_x, blast_y, blast_radius, x1, True)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.min_height_1, expected_left_bottom)
        self.assertAlmostEqual(result.min_height_2, 1.05)
        self.assertFalse(result.linked_to_next)
        self.assertTrue(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.1)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_linked_superblock_right_edge_graze_is_skipped(self):
        # Fidelity target: Landscape.clip_slice() lines 270-275 (Python).
        #
        # If a blast only grazes the right-bottom edge of a linked cap while the
        # opposite top edge is horizontally outside the blast, Python skips the
        # whole linked superblock. The cap and its support stay linked and intact.
        landscape = Landscape(TerrainSettings(slices=20, width=100.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(10.0, 10.0, 30.0, 30.0, linked=True)
        base = make_chunk(30.0, 30.0, 90.0, 90.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        landscape.clip_slice(target_slice, 9.0, 28.0, 3.0)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        result_cap, result_base = chunks
        self.assertAlmostEqual(result_cap.max_height_1, 10.0)
        self.assertAlmostEqual(result_cap.max_height_2, 10.0)
        self.assertAlmostEqual(result_cap.min_height_1, 30.0)
        self.assertAlmostEqual(result_cap.min_height_2, 30.0)
        self.assertTrue(result_cap.linked_to_next)
        self.assertFalse(result_cap.falling_state)
        self.assertAlmostEqual(result_base.max_height_1, 30.0)
        self.assertAlmostEqual(result_base.min_height_1, 90.0)
        self.assertFalse(result_base.falling_state)

    def test_clip_slice_linked_superblock_edge_graze_skips_entire_chain(self):
        # Fidelity target: Landscape.clip_slice() lines 270-275 (Python).
        #
        # The skip guard advances over the whole linked superblock, not only the
        # first linked pair. A right-edge graze against the cap leaves the cap,
        # connector, and final support intact.
        landscape = Landscape(TerrainSettings(slices=20, width=100.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(10.0, 10.0, 30.0, 30.0, linked=True)
        connector = make_chunk(30.0, 30.0, 60.0, 60.0, linked=True)
        base = make_chunk(60.0, 60.0, 90.0, 90.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, connector, base]

        landscape.clip_slice(target_slice, 9.0, 28.0, 3.0)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 3)
        result_cap, result_connector, result_base = chunks
        self.assertAlmostEqual(result_cap.max_height_1, 10.0)
        self.assertAlmostEqual(result_cap.min_height_2, 30.0)
        self.assertTrue(result_cap.linked_to_next)
        self.assertFalse(result_cap.falling_state)
        self.assertAlmostEqual(result_connector.max_height_1, 30.0)
        self.assertAlmostEqual(result_connector.min_height_2, 60.0)
        self.assertTrue(result_connector.linked_to_next)
        self.assertFalse(result_connector.falling_state)
        self.assertAlmostEqual(result_base.max_height_1, 60.0)
        self.assertAlmostEqual(result_base.min_height_2, 90.0)
        self.assertFalse(result_base.linked_to_next)
        self.assertFalse(result_base.falling_state)

    def test_clip_slice_linked_superblock_left_edge_graze_is_skipped(self):
        # Fidelity target: Landscape.clip_slice() lines 270-275 (Python).
        #
        # This mirrors the right-edge skip guard: a left-bottom edge graze also
        # advances over the linked superblock without detaching or clipping it.
        landscape = Landscape(TerrainSettings(slices=20, width=100.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(10.0, 10.0, 30.0, 30.0, linked=True)
        base = make_chunk(30.0, 30.0, 90.0, 90.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, base]

        landscape.clip_slice(target_slice, 1.0, 28.0, 3.0)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 2)
        result_cap, result_base = chunks
        self.assertAlmostEqual(result_cap.max_height_1, 10.0)
        self.assertAlmostEqual(result_cap.max_height_2, 10.0)
        self.assertAlmostEqual(result_cap.min_height_1, 30.0)
        self.assertAlmostEqual(result_cap.min_height_2, 30.0)
        self.assertTrue(result_cap.linked_to_next)
        self.assertFalse(result_cap.falling_state)
        self.assertAlmostEqual(result_base.max_height_1, 30.0)
        self.assertAlmostEqual(result_base.min_height_1, 90.0)
        self.assertFalse(result_base.falling_state)

    def test_clip_slice_linked_superblock_left_edge_graze_skips_entire_chain(self):
        # Fidelity target: Landscape.clip_slice() lines 270-275 (Python).
        #
        # This mirrors the multi-chunk right-edge skip: a left-edge graze skips
        # every linked chunk in the superblock and leaves the final support
        # untouched.
        landscape = Landscape(TerrainSettings(slices=20, width=100.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        cap = make_chunk(10.0, 10.0, 30.0, 30.0, linked=True)
        connector = make_chunk(30.0, 30.0, 60.0, 60.0, linked=True)
        base = make_chunk(60.0, 60.0, 90.0, 90.0, linked=False)
        landscape._land_chunks[target_slice] = [cap, connector, base]

        landscape.clip_slice(target_slice, 1.0, 28.0, 3.0)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 3)
        result_cap, result_connector, result_base = chunks
        self.assertAlmostEqual(result_cap.max_height_1, 10.0)
        self.assertAlmostEqual(result_cap.min_height_1, 30.0)
        self.assertTrue(result_cap.linked_to_next)
        self.assertFalse(result_cap.falling_state)
        self.assertAlmostEqual(result_connector.max_height_2, 30.0)
        self.assertAlmostEqual(result_connector.min_height_1, 60.0)
        self.assertTrue(result_connector.linked_to_next)
        self.assertFalse(result_connector.falling_state)
        self.assertAlmostEqual(result_base.max_height_2, 60.0)
        self.assertAlmostEqual(result_base.min_height_1, 90.0)
        self.assertFalse(result_base.linked_to_next)
        self.assertFalse(result_base.falling_state)

    def test_clip_slice_one_sided_middle_crater_graze_is_noop(self):
        # Fidelity target: Landscape.clip_slice() lines 280-407 (Python).
        #
        # If a tiny blast intersects the middle of only one vertical slice edge
        # but neither the top nor bottom endpoint is inside the blast, the classic
        # endpoint-code clipping path leaves the chunk unchanged. This guards the
        # migrated Godot terrain against over-applying continuous interval clipping.
        landscape = Landscape(TerrainSettings(slices=20, width=2.0), 0.0) # slice width is 2.0 / 20 = 0.1
        target_slice = 10
        # x1 = 10 * 0.1 - 1.0 = 0.0
        # x2 = 11 * 0.1 - 1.0 = 0.1
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(10.0, 10.0, -10.0, -10.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        # blast_x = 0.01, blast_y = 0.0, radius = 0.05
        # blast horizontal range: [0.01 - 0.05, 0.01 + 0.05] = [-0.04, 0.06]
        # x1 = 0.0 is inside blast horizontal range
        # x2 = 0.1 is outside blast horizontal range
        landscape.clip_slice(target_slice, 0.01, 0.0, 0.05)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.max_height_1, 10.0)
        self.assertAlmostEqual(result.max_height_2, 10.0)
        self.assertAlmostEqual(result.min_height_1, -10.0)
        self.assertAlmostEqual(result.min_height_2, -10.0)
        self.assertFalse(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_right_sided_middle_crater_graze_is_noop(self):
        # Fidelity target: Landscape.clip_slice() lines 280-407 (Python).
        #
        # This is the right-edge mirror of the one-sided middle crater graze:
        # crossing only the middle of the right vertical slice edge is ignored
        # unless a top or bottom endpoint participates in the endpoint-code path.
        landscape = Landscape(TerrainSettings(slices=20, width=2.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(10.0, 10.0, -10.0, -10.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        landscape.clip_slice(target_slice, x2 - 0.01, 0.0, 0.05)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.max_height_1, 10.0)
        self.assertAlmostEqual(result.max_height_2, 10.0)
        self.assertAlmostEqual(result.min_height_1, -10.0)
        self.assertAlmostEqual(result.min_height_2, -10.0)
        self.assertFalse(result.falling_state)
        self.assertAlmostEqual(result.wait_for_fall_time, 0.0)
        self.assertAlmostEqual(result.falling_speed, 0.0)

    def test_clip_slice_top_code_11_keeps_below_right_top(self):
        # Fidelity target: Landscape.clip_slice() lines 291-298 (Python), the
        # top_code = 11 case (state2 = 2, state1 = 3).
        #
        # When the left top endpoint is inside the blast (state1 = 3) and the
        # right top endpoint is above the blast center (state2 = 2), Pygame
        # lowers both top edges to the crater bottom, discarding the top part
        # above the crater on both sides.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(1.0, 1.0, -5.0, -5.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = 0.02
        blast_y = 0.9
        blast_radius = 0.11
        expected_left_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)
        expected_right_top = landscape.clip_height(blast_x, blast_y, blast_radius, x2, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.max_height_1, expected_left_top)
        self.assertAlmostEqual(result.max_height_2, expected_right_top)
        self.assertAlmostEqual(result.min_height_1, -5.0)
        self.assertAlmostEqual(result.min_height_2, -5.0)
        self.assertFalse(result.falling_state)

    def test_clip_slice_top_code_14_keeps_below_left_top(self):
        # Fidelity target: Landscape.clip_slice() lines 291-298 (Python), the
        # top_code = 14 case (state2 = 3, state1 = 2).
        #
        # When the left top endpoint is above the blast center (state1 = 2) and
        # the right top endpoint is inside the blast (state2 = 3), Pygame
        # lowers both top edges to the crater bottom, discarding the top part
        # above the crater on both sides.
        landscape = Landscape(TerrainSettings(slices=20, width=1.0), 0.0)
        target_slice = 10
        landscape._land_chunks = [[] for _ in range(landscape._num_of_slices)]
        chunk = make_chunk(1.0, 1.0, -5.0, -5.0, linked=False)
        landscape._land_chunks[target_slice] = [chunk]

        x1 = landscape.get_world_x_from_slice(target_slice)
        x2 = landscape.get_world_x_from_slice(target_slice + 1)
        blast_x = 0.08
        blast_y = 0.9
        blast_radius = 0.11
        expected_left_top = landscape.clip_height(blast_x, blast_y, blast_radius, x1, False)
        expected_right_top = landscape.clip_height(blast_x, blast_y, blast_radius, x2, False)

        landscape.clip_slice(target_slice, blast_x, blast_y, blast_radius)

        chunks = landscape._land_chunks[target_slice]
        self.assertEqual(len(chunks), 1)
        result = chunks[0]
        self.assertAlmostEqual(result.max_height_1, expected_left_top)
        self.assertAlmostEqual(result.max_height_2, expected_right_top)
        self.assertAlmostEqual(result.min_height_1, -5.0)
        self.assertAlmostEqual(result.min_height_2, -5.0)
        self.assertFalse(result.falling_state)

    def test_ground_collision_vertical_drop(self):
        # Fidelity target: Landscape.ground_collision() lines 580-638 (Python)
        # Vertical drop within a single slice (index1 == index2).
        landscape = Landscape(TerrainSettings(slices=2, width=2.0), 0.0)
        landscape._land_chunks = [[make_chunk(0.0, 0.0, -5.0, -5.0)], [make_chunk(0.0, 0.0, -5.0, -5.0)]]
        
        hit, hit_x, hit_y = landscape.ground_collision(0.5, 2.0, 0.5, -2.0)
        self.assertTrue(hit)
        self.assertAlmostEqual(hit_x, 0.5)
        self.assertAlmostEqual(hit_y, 0.0)

    def test_ground_collision_left_to_right(self):
        # Fidelity target: Landscape.ground_collision() lines 584-608 (Python)
        # Trajectory spanning multiple slices left to right.
        landscape = Landscape(TerrainSettings(slices=3, width=3.0), 0.0)
        landscape._land_chunks = [
            [make_chunk(2.0, 2.0, -5.0, -5.0)], 
            [make_chunk(2.0, 2.0, -5.0, -5.0)], 
            [make_chunk(2.0, 2.0, -5.0, -5.0)]
        ]
        
        # Shoot from x=0.5, y=3.0 down to x=2.5, y=1.0. Terrain is at y=2.0.
        # Should hit in the middle slice where y crosses 2.0.
        hit, hit_x, hit_y = landscape.ground_collision(0.5, 3.0, 2.5, 1.0)
        self.assertTrue(hit)
        self.assertAlmostEqual(hit_y, 2.0)
        self.assertAlmostEqual(hit_x, 1.5)

    def test_ground_collision_right_to_left(self):
        # Fidelity target: Landscape.ground_collision() lines 610-634 (Python)
        # Trajectory spanning multiple slices right to left.
        landscape = Landscape(TerrainSettings(slices=3, width=3.0), 0.0)
        landscape._land_chunks = [
            [make_chunk(2.0, 2.0, -5.0, -5.0)], 
            [make_chunk(2.0, 2.0, -5.0, -5.0)], 
            [make_chunk(2.0, 2.0, -5.0, -5.0)]
        ]
        
        hit, hit_x, hit_y = landscape.ground_collision(2.5, 3.0, 0.5, 1.0)
        self.assertTrue(hit)
        self.assertAlmostEqual(hit_y, 2.0)
        self.assertAlmostEqual(hit_x, 1.5)

    def test_ground_collision_misses_terrain(self):
        # Fidelity target: Landscape.ground_collision() lines 580-638 (Python)
        landscape = Landscape(TerrainSettings(slices=2, width=2.0), 0.0)
        landscape._land_chunks = [[make_chunk(0.0, 0.0, -5.0, -5.0)], [make_chunk(0.0, 0.0, -5.0, -5.0)]]
        
        hit, hit_x, hit_y = landscape.ground_collision(0.5, 5.0, 1.5, 4.0)
        self.assertFalse(hit)

    def test_ground_collision_single_slice_angle(self):
        # Fidelity target: Landscape.ground_collision()
        landscape = Landscape(TerrainSettings(slices=2, width=2.0), 0.0)
        landscape._land_chunks = [[make_chunk(0.0, 0.0, -5.0, -5.0)], [make_chunk(0.0, 0.0, -5.0, -5.0)]]
        
        # Shoot across from x=0.2, y=1.0 to x=0.8, y=-1.0. Still within slice 0.
        hit, hit_x, hit_y = landscape.ground_collision(0.2, 1.0, 0.8, -1.0)
        self.assertTrue(hit)
        self.assertAlmostEqual(hit_y, 0.0)

    def test_move_to_ground_no_chunk_returns_min_land_height(self):
        # Fidelity target: Landscape.move_to_ground()
        landscape = Landscape(TerrainSettings(slices=2, width=2.0), 0.0)
        landscape._land_chunks = [[], []]
        
        from src.landscape import MIN_LAND_HEIGHT
        height = landscape.move_to_ground(0.5, 0.0)
        self.assertAlmostEqual(height, 0.0)
        
        height_out = landscape.move_to_ground(-1000.0, 0.0)
        self.assertAlmostEqual(height_out, MIN_LAND_HEIGHT)

    def test_move_to_ground_at_angle_positive_angle(self):
        # Fidelity target: Landscape.move_to_ground_at_angle() lines 461-506 (Python)
        # Hits chunk edge with angle > 0 (traces left)
        landscape = Landscape(TerrainSettings(slices=2, width=2.0), 0.0)
        landscape._land_chunks = [
            [make_chunk(2.0, 4.0, -5.0, -5.0)],
            [make_chunk(4.0, 2.0, -5.0, -5.0)]
        ]
        
        x, y = landscape.move_to_ground_at_angle(1.5, 0.0, math.pi / 4.0)
        self.assertAlmostEqual(x, -2.0)
        self.assertAlmostEqual(y, 1.75)

    def test_move_to_ground_at_angle_negative_angle(self):
        # Fidelity target: Landscape.move_to_ground_at_angle()
        # Hits chunk edge with angle < 0 (traces right)
        landscape = Landscape(TerrainSettings(slices=2, width=2.0), 0.0)
        landscape._land_chunks = [
            [make_chunk(2.0, 4.0, -5.0, -5.0)],
            [make_chunk(4.0, 2.0, -5.0, -5.0)]
        ]
        
        x, y = landscape.move_to_ground_at_angle(0.5, 0.0, -math.pi / 4.0)
        self.assertAlmostEqual(x, 2.0)
        self.assertAlmostEqual(y, 0.75)

if __name__ == "__main__":
    unittest.main()
