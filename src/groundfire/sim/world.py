from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .registry import EntityRegistry
from .terrain import TerrainState


@dataclass(frozen=True)
class TerrainPatch:
    patch_id: int
    chunk_index: int
    operation: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReplicatedEntityState:
    entity_id: int
    entity_type: str
    position: tuple[float, float]
    velocity: tuple[float, float] = (0.0, 0.0)
    angle: float = 0.0
    owner_player: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorldState:
    seed: int = 0
    width: float = 11.0
    height: float = 15.0
    entity_registry: EntityRegistry = field(default_factory=EntityRegistry)
    terrain: TerrainState = field(init=False)
    terrain_revision: int = 0
    _next_patch_id: int = 1
    _pending_terrain_patches: list[TerrainPatch] = field(default_factory=list)

    def __post_init__(self):
        self.terrain = TerrainState.generate(seed=self.seed, width=self.width)
        self.terrain_revision = self.terrain.revision

    def queue_terrain_patch(self, chunk_index: int, operation: str, **payload) -> TerrainPatch:
        revision = int(payload.get("revision", self.terrain_revision + 1))
        patch = TerrainPatch(
            patch_id=self._next_patch_id,
            chunk_index=chunk_index,
            operation=operation,
            payload=dict(payload),
        )
        self._next_patch_id += 1
        self.terrain_revision = revision
        self._pending_terrain_patches.append(patch)
        return patch

    def apply_explosion(
        self,
        world_x: float,
        world_y: float,
        radius: float,
        *,
        caused_by: int | None = None,
    ) -> TerrainPatch | None:
        changed_vertices = self.terrain.apply_explosion(world_x, radius)
        if not changed_vertices:
            return None

        self.terrain_revision = self.terrain.revision
        return self.queue_terrain_patch(
            chunk_index=self._chunk_from_world_x(world_x),
            operation="explosion",
            centre=(round(world_x, 4), round(world_y, 4)),
            radius=radius,
            caused_by=caused_by,
            revision=self.terrain.revision,
            changed_vertices=changed_vertices,
        )

    def apply_patch(self, patch: TerrainPatch):
        self.terrain.apply_patch(patch.payload)
        self.terrain_revision = self.terrain.revision

    def drain_terrain_patches(self) -> tuple[TerrainPatch, ...]:
        drained = tuple(self._pending_terrain_patches)
        self._pending_terrain_patches.clear()
        return drained

    def snapshot_entities(self) -> tuple[ReplicatedEntityState, ...]:
        return self.entity_registry.snapshot()

    def snapshot_terrain_profile(self) -> tuple[float, ...]:
        return self.terrain.snapshot_profile()

    def _chunk_from_world_x(self, world_x: float) -> int:
        normalized = (world_x + (self.width / 2.0)) / max(self.width, 0.0001)
        return max(0, min(self.terrain.chunk_count - 1, int(normalized * self.terrain.chunk_count)))
