from __future__ import annotations

from ..sim.terrain import TerrainState
from .primitives import PolygonPrimitive, RectPrimitive


class TerrainRenderStateBuilder:
    SCREEN_LEFT = -10.0
    SCREEN_RIGHT = 10.0
    SCREEN_TOP = 7.5
    SCREEN_BOTTOM = -7.5
    SKY_BANDS = 24
    TOP_LAYER_DEPTH = 1.0
    SCENARIO_PALETTES = {
        1: ((204, 204, 0), (153, 153, 0)),
        7: ((198, 210, 68), (113, 139, 54)),
        11: ((208, 190, 96), (132, 118, 45)),
        17: ((190, 174, 86), (116, 96, 54)),
        23: ((210, 166, 86), (148, 96, 36)),
    }

    def build_primitives(self, landscape) -> tuple[PolygonPrimitive | RectPrimitive, ...]:
        if isinstance(landscape, TerrainState):
            return self._build_canonical_terrain_primitives(landscape)
        if landscape is None or not hasattr(landscape, "_land_chunks"):
            return ()

        primitives = []
        for slice_idx in range(getattr(landscape, "_num_of_slices", 0)):
            x1 = landscape.get_world_x_from_slice(slice_idx)
            x2 = landscape.get_world_x_from_slice(slice_idx + 1)
            for chunk in landscape._land_chunks[slice_idx]:
                avg_r = (
                    chunk.min_colour_1.r + chunk.max_colour_1.r + chunk.max_colour_2.r + chunk.min_colour_2.r
                ) / 4.0
                avg_g = (
                    chunk.min_colour_1.g + chunk.max_colour_1.g + chunk.max_colour_2.g + chunk.min_colour_2.g
                ) / 4.0
                avg_b = (
                    chunk.min_colour_1.b + chunk.max_colour_1.b + chunk.max_colour_2.b + chunk.min_colour_2.b
                ) / 4.0
                primitives.append(
                    PolygonPrimitive(
                        points=(
                            (x1, chunk.min_height_1),
                            (x1, chunk.max_height_1),
                            (x2, chunk.max_height_2),
                            (x2, chunk.min_height_2),
                        ),
                        colour=(int(avg_r * 255), int(avg_g * 255), int(avg_b * 255)),
                    )
                )
        return tuple(primitives)

    def _build_canonical_terrain_primitives(
        self,
        terrain: TerrainState,
    ) -> tuple[PolygonPrimitive | RectPrimitive, ...]:
        primitives: list[PolygonPrimitive | RectPrimitive] = list(self._build_sky_gradient())
        base_colour, top_colour = self._scenario_palette(terrain.seed)
        base_bottom = min(self.SCREEN_BOTTOM, terrain.floor_height - self.TOP_LAYER_DEPTH)
        for vertex_index in range(terrain.chunk_count):
            x1 = terrain.vertex_world_x(vertex_index)
            x2 = terrain.vertex_world_x(vertex_index + 1)
            top_left = terrain.heights[vertex_index]
            top_right = terrain.heights[vertex_index + 1]
            shelf_left = max(base_bottom, top_left - self.TOP_LAYER_DEPTH)
            shelf_right = max(base_bottom, top_right - self.TOP_LAYER_DEPTH)
            primitives.append(
                PolygonPrimitive(
                    points=((x1, base_bottom), (x1, shelf_left), (x2, shelf_right), (x2, base_bottom)),
                    colour=base_colour,
                )
            )
            primitives.append(
                PolygonPrimitive(
                    points=((x1, shelf_left), (x1, top_left), (x2, top_right), (x2, shelf_right)),
                    colour=top_colour,
                )
            )
        return tuple(primitives)

    def _scenario_palette(self, seed: int) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        if seed in self.SCENARIO_PALETTES:
            return self.SCENARIO_PALETTES[seed]
        palette_values = tuple(self.SCENARIO_PALETTES.values())
        return palette_values[abs(int(seed)) % len(palette_values)]

    def _build_sky_gradient(self) -> tuple[RectPrimitive, ...]:
        primitives = []
        screen_height = self.SCREEN_TOP - self.SCREEN_BOTTOM
        band_height = screen_height / float(self.SKY_BANDS)
        for band in range(self.SKY_BANDS):
            ratio_top = band / float(self.SKY_BANDS)
            top = self.SCREEN_TOP - (band * band_height)
            bottom = top - band_height
            colour = (
                int((0.0 + (0.6 * ratio_top)) * 255),
                0,
                int(0.4 * 255),
            )
            primitives.append(
                RectPrimitive(
                    left=self.SCREEN_LEFT,
                    top=top,
                    right=self.SCREEN_RIGHT,
                    bottom=bottom,
                    colour=colour,
                )
            )
        return tuple(primitives)
