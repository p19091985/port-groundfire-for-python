from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .world import ReplicatedEntityState


class EntityRegistry:
    def __init__(self):
        self._entities: dict[int, "ReplicatedEntityState"] = {}
        self._next_entity_id = 1

    def create(
        self,
        entity_type: str,
        *,
        position: tuple[float, float] = (0.0, 0.0),
        velocity: tuple[float, float] = (0.0, 0.0),
        angle: float = 0.0,
        owner_player: int | None = None,
        payload: dict | None = None,
        entity_id: int | None = None,
    ):
        from .world import ReplicatedEntityState

        resolved_id = self._claim_entity_id(entity_id)
        entity = ReplicatedEntityState(
            entity_id=resolved_id,
            entity_type=entity_type,
            position=position,
            velocity=velocity,
            angle=angle,
            owner_player=owner_player,
            payload=dict(payload or {}),
        )
        self._entities[resolved_id] = entity
        return entity

    def replace(self, entity: "ReplicatedEntityState"):
        self._entities[entity.entity_id] = entity
        if entity.entity_id >= self._next_entity_id:
            self._next_entity_id = entity.entity_id + 1
        return entity

    def get(self, entity_id: int) -> "ReplicatedEntityState | None":
        return self._entities.get(entity_id)

    def remove(self, entity_id: int) -> "ReplicatedEntityState | None":
        return self._entities.pop(entity_id, None)

    def all(self) -> tuple["ReplicatedEntityState", ...]:
        return tuple(self._entities[entity_id] for entity_id in sorted(self._entities))

    def snapshot(self) -> tuple["ReplicatedEntityState", ...]:
        return self.all()

    def clear(self):
        self._entities.clear()
        self._next_entity_id = 1

    def _claim_entity_id(self, entity_id: int | None) -> int:
        if entity_id is None:
            entity_id = self._next_entity_id
            self._next_entity_id += 1
            return entity_id

        if entity_id >= self._next_entity_id:
            self._next_entity_id = entity_id + 1
        return entity_id
