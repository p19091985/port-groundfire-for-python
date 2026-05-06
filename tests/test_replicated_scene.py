import unittest

from src.gameui import GameUI
from src.groundfire.network.messages import ServerSnapshotEnvelope
from src.groundfire.render.primitives import PolygonPrimitive, RectPrimitive
from src.groundfire.render.scene import ReplicatedMatchScene, ReplicatedSceneRenderer
from src.groundfire.render.terrain import TerrainRenderStateBuilder
from src.groundfire.sim.match import MatchSnapshot, ReplicatedPlayerState
from src.groundfire.sim.terrain import TerrainState
from src.groundfire.sim.world import ReplicatedEntityState, TerrainPatch


class ReplicatedSceneTests(unittest.TestCase):
    class FontStub:
        def __init__(self):
            self.centred_calls = []
            self.printf_calls = []

        def set_shadow(self, _value):
            return None

        def set_proportional(self, _value):
            return None

        def set_orientation(self, _value):
            return None

        def set_size(self, *_args):
            return None

        def set_colour(self, _colour):
            return None

        def print_centred_at(self, *args):
            self.centred_calls.append(args)

        def printf(self, *args):
            self.printf_calls.append(args)

    class GameStub:
        class GraphicsStub:
            def __init__(self):
                self.polygons = []
                self.rects = []

            def draw_world_polygon(self, points, colour, *_args, **_kwargs):
                self.polygons.append((tuple(points), colour))

            def draw_world_rect(self, left, top, right, bottom, colour, *_args, **_kwargs):
                self.rects.append(((left, top, right, bottom), colour))

            def draw_world_line(self, *_args, **_kwargs):
                return None

            def draw_subtexture_world_rect(self, *_args, **_kwargs):
                return None

            def draw_texture_world_rect(self, *_args, **_kwargs):
                return None

            def draw_texture_centered(self, *_args, **_kwargs):
                return None

            def draw_fullscreen_overlay(self, *_args, **_kwargs):
                return None

        def __init__(self):
            self.font = ReplicatedSceneTests.FontStub()
            self.ui = GameUI(font_provider=lambda: self.font)
            self.graphics = ReplicatedSceneTests.GameStub.GraphicsStub()

        def get_ui(self):
            return self.ui

        def get_graphics(self):
            return self.graphics

    def test_scene_builds_canonical_render_frame_from_snapshot(self):
        player_colour = (12, 34, 56)
        snapshot = MatchSnapshot(
            authority="server",
            game_phase="round_starting",
            current_round=4,
            num_rounds=10,
            simulation_tick=120,
            phase_ticks_remaining=60,
            players=(
                ReplicatedPlayerState(
                    player_number=0,
                    name="Alice",
                    tank_entity_id=1,
                    colour=player_colour,
                    selected_weapon="missile",
                    weapon_stocks=(("missile", 2),),
                ),
            ),
            entities=(
                ReplicatedEntityState(
                    entity_id=1,
                    entity_type="tank",
                    position=(1.0, 1.25),
                    angle=60.0,
                    owner_player=0,
                    payload={"health": 70.0, "fuel": 0.5, "gun_angle": 55.0, "size": 0.25, "colour": player_colour},
                ),
            ),
            seed=9,
            world_width=11.0,
            terrain_revision=2,
            terrain_profile=(-1.0, -0.75, -0.5),
        )
        envelope = ServerSnapshotEnvelope(
            session_id="session-1",
            snapshot_sequence=5,
            simulation_tick=120,
            acknowledged_command_sequences={0: 3},
            snapshot=snapshot,
            terrain_patches=(),
            events=({"event_type": "round_started", "payload": {"round": 4}},),
            snapshot_kind="full",
            baseline_snapshot_sequence=5,
        )
        scene = ReplicatedMatchScene()
        renderer = ReplicatedSceneRenderer()

        self.assertTrue(scene.apply_snapshot_envelope(envelope, local_player_number=0))
        frame = renderer.build_frame(scene, local_player_number=0)

        self.assertEqual(scene.terrain.revision, 2)
        self.assertGreaterEqual(len(frame.terrain_primitives), 2)
        self.assertEqual(frame.entity_states[0].primitives[0].colour, player_colour)
        self.assertTrue(any(getattr(primitive, "colour", None) == player_colour for primitive in frame.hud_primitives))
        self.assertEqual(frame.metadata["current_round"], 4)
        self.assertEqual(frame.metadata["game_phase"], "round_starting")
        self.assertEqual(frame.metadata["phase_ticks_remaining"], 60)
        self.assertEqual(frame.metadata["snapshot_kind"], "full")
        self.assertEqual(frame.metadata["baseline_snapshot_sequence"], 5)

    def test_multiplayer_terrain_uses_full_game_width_and_classic_layers(self):
        terrain = TerrainState(seed=1, width=20.0, heights=[-1.0, 0.0, -0.5])
        primitives = TerrainRenderStateBuilder().build_primitives(terrain)

        sky_primitives = [primitive for primitive in primitives if isinstance(primitive, RectPrimitive)]
        terrain_polygons = [primitive for primitive in primitives if isinstance(primitive, PolygonPrimitive)]

        self.assertEqual(len(sky_primitives), TerrainRenderStateBuilder.SKY_BANDS)
        self.assertEqual(terrain_polygons[0].points[0][0], -10.0)
        self.assertEqual(terrain_polygons[-1].points[2][0], 10.0)
        self.assertIn((204, 204, 0), [primitive.colour for primitive in terrain_polygons])
        self.assertIn((153, 153, 0), [primitive.colour for primitive in terrain_polygons])

    def test_multiplayer_terrain_palette_varies_by_scenario_seed(self):
        classic = TerrainRenderStateBuilder().build_primitives(
            TerrainState(seed=1, width=20.0, heights=[-1.0, 0.0])
        )
        basin = TerrainRenderStateBuilder().build_primitives(
            TerrainState(seed=7, width=20.0, heights=[-1.0, 0.0])
        )

        classic_colours = [primitive.colour for primitive in classic if isinstance(primitive, PolygonPrimitive)]
        basin_colours = [primitive.colour for primitive in basin if isinstance(primitive, PolygonPrimitive)]

        self.assertNotEqual(classic_colours, basin_colours)

    def test_multiplayer_tank_arrow_points_along_fire_angle(self):
        snapshot = MatchSnapshot(
            authority="server",
            game_phase="round_in_action",
            current_round=1,
            num_rounds=5,
            simulation_tick=1,
            players=(
                ReplicatedPlayerState(
                    player_number=0,
                    name="Alice",
                    tank_entity_id=1,
                    colour=(200, 100, 80),
                ),
            ),
            entities=(
                ReplicatedEntityState(
                    entity_id=1,
                    entity_type="tank",
                    position=(0.0, 0.0),
                    angle=0.0,
                    owner_player=0,
                    payload={"health": 100.0, "fuel": 1.0, "gun_angle": 0.0, "size": 0.25, "alive": True},
                ),
            ),
        )
        scene = ReplicatedMatchScene(snapshot=snapshot)
        renderer = ReplicatedSceneRenderer()

        frame = renderer.build_frame(scene, local_player_number=0)
        tank_state = frame.entity_states[0]
        body, _shaft, head = tank_state.primitives[:3]

        self.assertGreater(max(point[0] for point in head.points), max(point[0] for point in body.points))
        self.assertLess(max(point[1] for point in head.points), 0.5)

    def test_scene_applies_incremental_terrain_patch_without_full_profile(self):
        baseline = MatchSnapshot(
            authority="server",
            game_phase="round_in_action",
            current_round=1,
            num_rounds=10,
            simulation_tick=1,
            phase_ticks_remaining=120,
            players=(),
            entities=(),
            seed=5,
            world_width=11.0,
            terrain_revision=0,
            terrain_profile=(-1.0, -1.0, -1.0),
        )
        updated = MatchSnapshot(
            authority="server",
            game_phase="round_in_action",
            current_round=1,
            num_rounds=10,
            simulation_tick=2,
            phase_ticks_remaining=119,
            players=(),
            entities=(),
            seed=5,
            world_width=11.0,
            terrain_revision=1,
            terrain_profile=(),
        )
        patch = TerrainPatch(
            patch_id=1,
            chunk_index=0,
            operation="explosion",
            payload={"changed_vertices": ({"index": 1, "height": -2.5},), "revision": 1},
        )
        scene = ReplicatedMatchScene()

        scene.apply_snapshot_envelope(
            ServerSnapshotEnvelope(
                session_id="session-1",
                snapshot_sequence=1,
                simulation_tick=1,
                acknowledged_command_sequences={},
                snapshot=baseline,
            )
        )
        scene.apply_snapshot_envelope(
            ServerSnapshotEnvelope(
                session_id="session-1",
                snapshot_sequence=2,
                simulation_tick=2,
                acknowledged_command_sequences={},
                snapshot=updated,
                terrain_patches=(patch,),
            )
        )

        self.assertEqual(scene.terrain.heights[1], -2.5)
        self.assertEqual(scene.terrain.revision, 1)

    def test_renderer_draws_score_strip_and_winner_overlay_from_snapshot(self):
        snapshot = MatchSnapshot(
            authority="server",
            game_phase="winner",
            current_round=3,
            num_rounds=3,
            simulation_tick=180,
            phase_ticks_remaining=0,
            winner_player_number=0,
            players=(
                ReplicatedPlayerState(
                    player_number=0,
                    name="Alice",
                    score=300,
                    money=120,
                    tank_entity_id=1,
                    colour=(200, 100, 80),
                    selected_weapon="nuke",
                    weapon_stocks=(("nuke", 1),),
                ),
            ),
            entities=(
                ReplicatedEntityState(
                    entity_id=1,
                    entity_type="tank",
                    position=(0.0, 0.0),
                    owner_player=0,
                    payload={"health": 100.0, "fuel": 1.0, "gun_angle": 45.0, "size": 0.25, "alive": True},
                ),
            ),
        )
        scene = ReplicatedMatchScene(snapshot=snapshot)
        renderer = ReplicatedSceneRenderer()
        game = self.GameStub()

        frame = renderer.render(game, scene, local_player_number=0)

        self.assertEqual(frame.metadata["winner_player_number"], 0)
        self.assertTrue(any(call[2] == "Final Result" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "We have a winner!" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "Alice" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "%s %dpts $%d" for call in game.font.printf_calls))
        self.assertTrue(any(call[2] == "%s %s" for call in game.font.printf_calls))

    def test_renderer_draws_shop_overlay_for_local_player(self):
        snapshot = MatchSnapshot(
            authority="server",
            game_phase="shop",
            current_round=2,
            num_rounds=5,
            simulation_tick=60,
            phase_ticks_remaining=45,
            players=(
                ReplicatedPlayerState(
                    player_number=0,
                    name="Alice",
                    money=35,
                    colour=(200, 100, 80),
                    selected_weapon="missile",
                    weapon_stocks=(("missile", 1),),
                ),
            ),
            entities=(),
        )
        scene = ReplicatedMatchScene(snapshot=snapshot, local_player_number=0)
        renderer = ReplicatedSceneRenderer()
        game = self.GameStub()

        frame = renderer.render(game, scene, local_player_number=0)

        self.assertEqual(frame.metadata["game_phase"], "shop")
        self.assertTrue(any(call[2] == "Shop Phase" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "Rolling Mines" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "Done!" for call in game.font.centred_calls))

    def test_renderer_draws_polished_lobby_overlay_with_player_roles(self):
        snapshot = MatchSnapshot(
            authority="server",
            game_phase="lobby",
            current_round=0,
            num_rounds=5,
            simulation_tick=12,
            players=(
                ReplicatedPlayerState(
                    player_number=0,
                    name="Alice",
                    money=50,
                    colour=(230, 90, 80),
                ),
                ReplicatedPlayerState(
                    player_number=1,
                    name="CPU LAN 1",
                    money=50,
                    colour=(80, 160, 230),
                    is_computer=True,
                ),
            ),
            entities=(),
        )
        scene = ReplicatedMatchScene(snapshot=snapshot, local_player_number=0)
        renderer = ReplicatedSceneRenderer()
        game = self.GameStub()

        frame = renderer.render(game, scene, local_player_number=0)

        self.assertEqual(frame.metadata["game_phase"], "lobby")
        self.assertTrue(any(call[2] == "Waiting for Server" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "2 players connected" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "Online Lobby" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "Human" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "AI" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "%s" and call[3] == "Alice" for call in game.font.printf_calls))
        self.assertTrue(any(call[2] == "%s" and call[3] == "CPU LAN 1" for call in game.font.printf_calls))
        self.assertGreaterEqual(len(game.graphics.rects), 7)
        self.assertTrue(any(rect[1] == (230, 90, 80, 220) for rect in game.graphics.rects))

    def test_renderer_draws_classic_score_overlay_headings(self):
        snapshot = MatchSnapshot(
            authority="server",
            game_phase="score",
            current_round=2,
            num_rounds=5,
            simulation_tick=60,
            phase_ticks_remaining=45,
            players=(
                ReplicatedPlayerState(
                    player_number=0,
                    name="Alice",
                    score=100,
                    money=35,
                    colour=(200, 100, 80),
                    round_defeated_player_numbers=(1,),
                    selected_weapon="shell",
                ),
                ReplicatedPlayerState(
                    player_number=1,
                    name="CPU 1",
                    score=50,
                    money=35,
                    colour=(80, 140, 220),
                    is_leader=True,
                    selected_weapon="shell",
                ),
            ),
            entities=(),
        )
        scene = ReplicatedMatchScene(snapshot=snapshot, local_player_number=0)
        renderer = ReplicatedSceneRenderer()
        game = self.GameStub()

        renderer.render(game, scene, local_player_number=0)

        self.assertTrue(any(call[2] == "Scoring for Round" for call in game.font.centred_calls))
        self.assertTrue(any(call[2] == "Total Score" for call in game.font.centred_calls))
        self.assertFalse(any(call[2] == "Round detail pending runtime migration" for call in game.font.centred_calls))
        self.assertTrue(game.graphics.polygons)
        self.assertTrue(game.graphics.rects)

    def test_renderer_draws_winner_draw_state_like_classic_screen(self):
        snapshot = MatchSnapshot(
            authority="server",
            game_phase="winner",
            current_round=3,
            num_rounds=3,
            simulation_tick=180,
            phase_ticks_remaining=0,
            winner_player_number=None,
            players=(
                ReplicatedPlayerState(
                    player_number=0,
                    name="Alice",
                    score=300,
                    money=120,
                    colour=(200, 100, 80),
                ),
                ReplicatedPlayerState(
                    player_number=1,
                    name="CPU 1",
                    score=300,
                    money=120,
                    colour=(100, 160, 220),
                ),
            ),
            entities=(),
        )
        scene = ReplicatedMatchScene(snapshot=snapshot)
        renderer = ReplicatedSceneRenderer()
        game = self.GameStub()

        renderer.render(game, scene, local_player_number=0)

        self.assertTrue(any(call[2] == "It's a tie!" for call in game.font.centred_calls))
        self.assertGreaterEqual(sum(1 for call in game.font.centred_calls if call[2] == "Winner!"), 2)


if __name__ == "__main__":
    unittest.main()
