import os
import unittest

from tests.support import CommandPlayer, DummyGameForTank, PROJECT_ROOT

from src.entityadapters import EntityAdapterRegistry
from src.entityvisual import EntityVisualRenderer
from src.inifile import ReadIniFile
from src.renderprimitives import EntityRenderState, PolygonPrimitive
from src.tank import Tank


SETTINGS = ReadIniFile(os.path.join(PROJECT_ROOT, "conf", "options.ini"))


class EntityAdaptersTests(unittest.TestCase):
    def test_registry_builds_world_only_tank_render_state(self):
        game = DummyGameForTank(SETTINGS)
        player = CommandPlayer()
        tank = Tank(game, player, 0)
        player._tank = tank
        tank.assign_entity_id(7)
        tank._gun_power = 12.0

        registry = EntityAdapterRegistry()
        render_state = registry.build_render_state(game, tank)
        snapshot = registry.build_snapshot(game, tank)

        self.assertEqual(render_state.entity_id, 7)
        self.assertEqual(render_state.entity_type, "tank")
        self.assertEqual(len(render_state.primitives), 3)
        self.assertEqual(snapshot.payload["selected_weapon"], 0)
        self.assertEqual(snapshot.payload["player_number"], 0)

    def test_visual_renderer_prefers_external_state_builder(self):
        class EntityStub:
            def get_render_state(self):
                raise AssertionError("legacy entity render path should not be used")

        built = EntityRenderState(entity_id=1, entity_type="stub", primitives=(PolygonPrimitive(points=((0, 0), (1, 0), (0, 1)), colour=(255, 255, 255)),))

        class BuilderStub:
            def build_render_state(self, _game, _entity):
                return built

        class GraphicsStub:
            def __init__(self):
                self.polygons = []

            def draw_world_polygon(self, points, colour):
                self.polygons.append((points, colour))

        class GameStub:
            def __init__(self):
                self.graphics = GraphicsStub()

            def get_graphics(self):
                return self.graphics

        renderer = EntityVisualRenderer(state_builder=BuilderStub())
        game = GameStub()

        self.assertTrue(renderer.render_entity(game, EntityStub()))
        self.assertEqual(game.graphics.polygons, [(((0, 0), (1, 0), (0, 1)), (255, 255, 255))])


if __name__ == "__main__":
    unittest.main()
