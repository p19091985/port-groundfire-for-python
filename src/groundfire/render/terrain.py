from __future__ import annotations

from ..sim.terrain import TerrainState
from .primitives import PolygonPrimitive, RectPrimitive


class TerrainRenderStateBuilder:
    SCREEN_LEFT = -10.0
    SCREEN_RIGHT = 10.0
    SCREEN_TOP = 7.5
    SCREEN_BOTTOM = -7.5
    SKY_BANDS = 24

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
        for vertex_index in range(terrain.chunk_count):
            x1 = terrain.vertex_world_x(vertex_index)
            x2 = terrain.vertex_world_x(vertex_index + 1)
            top_left = terrain.heights[vertex_index]
            top_right = terrain.heights[vertex_index + 1]
            colour = self._canonical_terrain_colour(top_left, top_right, terrain.floor_height)
            primitives.append(
                PolygonPrimitive(
                    points=((x1, terrain.floor_height), (x1, top_left), (x2, top_right), (x2, terrain.floor_height)),
                    colour=colour,
                )
            )
        return tuple(primitives)

    def _canonical_terrain_colour(self, top_left: float, top_right: float, floor_height: float) -> tuple[int, int, int]:
        average_height = (top_left + top_right) / 2.0
        normalized = (average_height - floor_height) / max(0.0001, 8.0 - floor_height)
        normalized = max(0.0, min(1.0, normalized))
        r = int(105 + (normalized * 70))
        g = int(105 + (normalized * 70))
        b = int(0 + (normalized * 20))
        return (r, g, b)

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
