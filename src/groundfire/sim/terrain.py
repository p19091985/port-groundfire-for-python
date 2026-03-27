from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

MIN_TERRAIN_HEIGHT = -7.0
MAX_TERRAIN_HEIGHT = 4.5
DEFAULT_TERRAIN_WIDTH = 11.0
DEFAULT_TERRAIN_CHUNK_COUNT = 64


@dataclass
class TerrainState:
    seed: int = 0
    width: float = DEFAULT_TERRAIN_WIDTH
    chunk_count: int = DEFAULT_TERRAIN_CHUNK_COUNT
    floor_height: float = MIN_TERRAIN_HEIGHT
    revision: int = 0
    heights: list[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.heights:
            self.heights = list(self._generate_heights(self.seed, self.chunk_count))
        elif len(self.heights) < 2:
            self.heights = [self.floor_height, self.floor_height]
            self.chunk_count = 1
        else:
            self.chunk_count = len(self.heights) - 1

    @classmethod
    def generate(
        cls,
        *,
        seed: int,
        width: float = DEFAULT_TERRAIN_WIDTH,
        chunk_count: int = DEFAULT_TERRAIN_CHUNK_COUNT,
    ) -> "TerrainState":
        return cls(seed=seed, width=width, chunk_count=chunk_count)

    def clone(self) -> "TerrainState":
        return TerrainState(
            seed=self.seed,
            width=self.width,
            chunk_count=self.chunk_count,
            floor_height=self.floor_height,
            revision=self.revision,
            heights=list(self.heights),
        )

    def snapshot_profile(self) -> tuple[float, ...]:
        return tuple(self.heights)

    def vertex_world_x(self, vertex_index: int) -> float:
        if self.chunk_count <= 0:
            return 0.0
        ratio = vertex_index / self.chunk_count
        return (-self.width / 2.0) + (ratio * self.width)

    def height_at(self, world_x: float) -> float:
        if self.chunk_count <= 0:
            return self.floor_height

        clamped_x = max(-self.width / 2.0, min(self.width / 2.0, world_x))
        slice_x = ((clamped_x + (self.width / 2.0)) / self.width) * self.chunk_count
        left_index = int(math.floor(slice_x))
        right_index = min(self.chunk_count, left_index + 1)
        if right_index == left_index:
            return self.heights[left_index]

        ratio = slice_x - left_index
        return (self.heights[left_index] * (1.0 - ratio)) + (self.heights[right_index] * ratio)

    def apply_explosion(
        self,
        world_x: float,
        radius: float,
        *,
        depth: float | None = None,
    ) -> tuple[dict[str, float | int], ...]:
        effective_radius = max(0.15, float(radius))
        effective_depth = float(depth if depth is not None else max(0.2, effective_radius * 0.75))
        changed_vertices: list[dict[str, float | int]] = []

        for vertex_index, current_height in enumerate(self.heights):
            vertex_x = self.vertex_world_x(vertex_index)
            distance = abs(vertex_x - world_x)
            if distance > effective_radius:
                continue

            falloff = 1.0 - (distance / effective_radius)
            new_height = max(self.floor_height, current_height - (effective_depth * falloff))
            new_height = round(new_height, 6)
            if new_height >= current_height:
                continue

            self.heights[vertex_index] = new_height
            changed_vertices.append({"index": vertex_index, "height": new_height})

        if changed_vertices:
            self.revision += 1

        return tuple(changed_vertices)

    def apply_patch(self, patch_payload: dict):
        for item in patch_payload.get("changed_vertices", ()):
            vertex_index = int(item["index"])
            if 0 <= vertex_index < len(self.heights):
                self.heights[vertex_index] = float(item["height"])
        self.revision = max(self.revision, int(patch_payload.get("revision", self.revision)))

    def _generate_heights(self, seed: int, chunk_count: int) -> tuple[float, ...]:
        rng = random.Random(seed)
        heights = []
        ridge = rng.uniform(-1.0, 1.25)

        for index in range(chunk_count + 1):
            ridge += rng.uniform(-0.18, 0.18)
            ridge = max(-2.5, min(1.75, ridge))
            ratio = index / max(chunk_count, 1)
            wave = math.sin((ratio * math.pi * 2.0) + seed) * 0.85
            detail = math.sin((ratio * math.pi * 5.0) + (seed * 0.37)) * 0.25
            height = ridge + wave + detail
            heights.append(max(MIN_TERRAIN_HEIGHT + 0.5, min(MAX_TERRAIN_HEIGHT, height)))

        return tuple(round(height, 6) for height in heights)
