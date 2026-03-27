from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from ..network.messages import ServerSnapshotEnvelope
from ..sim.match import MatchSnapshot, ReplicatedPlayerState
from ..sim.terrain import TerrainState
from ..sim.world import ReplicatedEntityState
from ..ui import ClientMenuRenderer
from .entity_visual import EntityVisualRenderer
from .hud import WeaponHudRenderer
from .primitives import EntityRenderState, PolygonPrimitive, RectPrimitive, RenderPrimitive
from .terrain import TerrainRenderStateBuilder


@dataclass
class ReplicatedMatchScene:
    snapshot_sequence: int = 0
    snapshot: MatchSnapshot | None = None
    terrain: TerrainState | None = None
    events: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    local_player_number: int | None = None
    snapshot_kind: str = "full"
    baseline_snapshot_sequence: int | None = None
    authoritative_snapshot: MatchSnapshot | None = None

    def apply_snapshot_envelope(
        self,
        envelope: ServerSnapshotEnvelope,
        *,
        local_player_number: int | None = None,
    ) -> bool:
        return self.apply_resolved_snapshot(
            envelope.snapshot,
            snapshot_sequence=envelope.snapshot_sequence,
            terrain_patches=envelope.terrain_patches,
            events=envelope.events,
            local_player_number=local_player_number,
            snapshot_kind=envelope.snapshot_kind,
            baseline_snapshot_sequence=envelope.baseline_snapshot_sequence,
            authoritative_snapshot=envelope.snapshot,
        )

    def apply_resolved_snapshot(
        self,
        snapshot: MatchSnapshot,
        *,
        snapshot_sequence: int,
        terrain_patches=(),
        events: tuple[dict[str, Any], ...] = (),
        local_player_number: int | None = None,
        snapshot_kind: str = "full",
        baseline_snapshot_sequence: int | None = None,
        authoritative_snapshot: MatchSnapshot | None = None,
    ) -> bool:
        if snapshot_sequence <= self.snapshot_sequence:
            return False

        terrain = self._build_terrain_from_snapshot(snapshot)
        if snapshot.terrain_profile:
            self.terrain = terrain
        else:
            if self.terrain is None or self.terrain.seed != snapshot.seed or self.terrain.width != snapshot.world_width:
                self.terrain = terrain
            for patch in terrain_patches:
                self.terrain.apply_patch(patch.payload)

        self.snapshot_sequence = snapshot_sequence
        self.snapshot = snapshot
        self.authoritative_snapshot = authoritative_snapshot or snapshot
        self.events = events
        self.local_player_number = local_player_number
        self.snapshot_kind = snapshot_kind
        self.baseline_snapshot_sequence = baseline_snapshot_sequence
        return True

    def replace_snapshot(self, snapshot: MatchSnapshot, *, local_player_number: int | None = None):
        self.snapshot = snapshot
        if local_player_number is not None:
            self.local_player_number = local_player_number

    def restore_authoritative_snapshot(self):
        if self.authoritative_snapshot is not None:
            self.snapshot = self.authoritative_snapshot

    def get_players(self) -> tuple[ReplicatedPlayerState, ...]:
        if self.snapshot is None:
            return ()
        return self.snapshot.players

    def get_entities(self) -> tuple[ReplicatedEntityState, ...]:
        if self.snapshot is None:
            return ()
        return self.snapshot.entities

    def get_entity_by_id(self, entity_id: int | None) -> ReplicatedEntityState | None:
        if entity_id is None:
            return None
        for entity in self.get_entities():
            if entity.entity_id == entity_id:
                return entity
        return None

    def _build_terrain_from_snapshot(self, snapshot: MatchSnapshot) -> TerrainState:
        if snapshot.terrain_profile:
            return TerrainState(
                seed=snapshot.seed,
                width=snapshot.world_width,
                revision=snapshot.terrain_revision,
                heights=list(snapshot.terrain_profile),
            )
        return TerrainState.generate(seed=snapshot.seed, width=snapshot.world_width)


@dataclass(frozen=True)
class ReplicatedRenderFrame:
    terrain_primitives: tuple[RenderPrimitive, ...]
    entity_states: tuple[EntityRenderState, ...]
    hud_primitives: tuple[RenderPrimitive, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


class ReplicatedEntityRenderStateBuilder:
    def build_entity_states(self, scene: ReplicatedMatchScene) -> tuple[EntityRenderState, ...]:
        states = []
        for entity in sorted(scene.get_entities(), key=lambda item: item.entity_id):
            states.append(self.build_entity_state(scene, entity))
        return tuple(states)

    def build_entity_state(self, scene: ReplicatedMatchScene, entity: ReplicatedEntityState) -> EntityRenderState:
        if entity.entity_type == "tank":
            return self._build_tank_state(scene, entity)
        if entity.entity_type in {"shell", "missile", "machinegun", "mirv", "nuke"}:
            return self._build_projectile_state(scene, entity)

        return EntityRenderState(
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
            primitives=(
                RectPrimitive(
                    entity.position[0] - 0.05,
                    entity.position[1] + 0.05,
                    entity.position[0] + 0.05,
                    entity.position[1] - 0.05,
                    (255, 255, 255),
                ),
            ),
            metadata=dict(entity.payload),
        )

    def _build_tank_state(self, scene: ReplicatedMatchScene, entity: ReplicatedEntityState) -> EntityRenderState:
        size = float(entity.payload.get("size", 0.25))
        x, y = entity.position
        body_angle = float(entity.payload.get("tank_angle", 0.0))
        gun_angle = float(entity.payload.get("gun_angle", entity.angle))
        alive = bool(entity.payload.get("alive", True))
        colour = self._resolve_colour(scene, entity)
        if not alive:
            colour = self._dim_colour(colour)

        body_points = tuple(
            self._transform_point(px, py, x, y, body_angle)
            for px, py in (
                (-size, 0.0),
                (-(size / 2.0), size),
                ((size / 2.0), size),
                (size, 0.0),
            )
        )
        centre_x = x
        centre_y = y + (size / 2.0)
        arrow_length = size * 2.0
        shaft_points = tuple(
            self._transform_point(px, py, centre_x, centre_y, gun_angle)
            for px, py in ((-0.05, size * 1.2), (-0.05, arrow_length), (0.05, arrow_length), (0.05, size * 1.2))
        )
        head_points = tuple(
            self._transform_point(px, py, centre_x, centre_y, gun_angle)
            for px, py in ((-0.12, arrow_length), (0.0, arrow_length + 0.18), (0.12, arrow_length))
        )

        primitives = [PolygonPrimitive(points=body_points, colour=colour)]
        if alive:
            primitives.extend(
                (
                    PolygonPrimitive(points=shaft_points, colour=(0, 255, 0, 150)),
                    PolygonPrimitive(points=head_points, colour=(0, 255, 0, 150)),
                )
            )

        return EntityRenderState(
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
            primitives=tuple(primitives),
            metadata=dict(entity.payload),
        )

    def _build_projectile_state(self, scene: ReplicatedMatchScene, entity: ReplicatedEntityState) -> EntityRenderState:
        x, y = entity.position
        size = float(entity.payload.get("size", 0.06))
        colour = self._resolve_colour(scene, entity)
        angle = entity.angle
        if entity.velocity != (0.0, 0.0):
            angle = math.degrees(math.atan2(entity.velocity[1], entity.velocity[0]))
        points = tuple(
            self._transform_point(px, py, x, y, angle)
            for px, py in ((size, 0.0), (-size, size / 2.0), (-size, -(size / 2.0)))
        )
        return EntityRenderState(
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
            primitives=(PolygonPrimitive(points=points, colour=colour),),
            metadata=dict(entity.payload),
        )

    def _resolve_colour(self, scene: ReplicatedMatchScene, entity: ReplicatedEntityState) -> tuple[int, int, int]:
        if "colour" in entity.payload:
            raw = entity.payload["colour"]
            return (int(raw[0]), int(raw[1]), int(raw[2]))

        owner = entity.owner_player
        for player in scene.get_players():
            if player.player_number == owner:
                return player.colour
        return (255, 255, 255)

    def _transform_point(self, lx: float, ly: float, tx: float, ty: float, angle_deg: float) -> tuple[float, float]:
        radians = math.radians(angle_deg)
        cos_value = math.cos(radians)
        sin_value = math.sin(radians)
        return (
            tx + (lx * cos_value) - (ly * sin_value),
            ty + (lx * sin_value) + (ly * cos_value),
        )

    def _dim_colour(self, colour: tuple[int, int, int]) -> tuple[int, int, int]:
        return (
            max(25, int(colour[0] * 0.35)),
            max(25, int(colour[1] * 0.35)),
            max(25, int(colour[2] * 0.35)),
        )


class ReplicatedSceneRenderer:
    def __init__(
        self,
        *,
        terrain_builder: TerrainRenderStateBuilder | None = None,
        entity_builder: ReplicatedEntityRenderStateBuilder | None = None,
        visual_renderer: EntityVisualRenderer | None = None,
        menu_renderer: ClientMenuRenderer | None = None,
        weapon_hud_renderer: WeaponHudRenderer | None = None,
    ):
        self._terrain_builder = terrain_builder or TerrainRenderStateBuilder()
        self._entity_builder = entity_builder or ReplicatedEntityRenderStateBuilder()
        self._visual_renderer = visual_renderer or EntityVisualRenderer()
        self._menu_renderer = menu_renderer or ClientMenuRenderer()
        self._weapon_hud_renderer = weapon_hud_renderer or WeaponHudRenderer()

    def build_frame(
        self,
        scene: ReplicatedMatchScene,
        *,
        local_player_number: int | None = None,
    ) -> ReplicatedRenderFrame:
        terrain_primitives = self._terrain_builder.build_primitives(scene.terrain) if scene.terrain is not None else ()
        entity_states = self._entity_builder.build_entity_states(scene)
        hud_primitives = self._build_hud_primitives(scene, local_player_number=local_player_number)
        snapshot = scene.snapshot
        metadata = {
            "game_phase": getattr(snapshot, "game_phase", "lobby"),
            "current_round": getattr(snapshot, "current_round", 0),
            "num_rounds": getattr(snapshot, "num_rounds", 0),
            "phase_ticks_remaining": getattr(snapshot, "phase_ticks_remaining", 0),
            "round_winner_player_number": getattr(snapshot, "round_winner_player_number", None),
            "winner_player_number": getattr(snapshot, "winner_player_number", None),
            "terrain_revision": getattr(snapshot, "terrain_revision", 0),
            "local_player_number": local_player_number,
            "snapshot_kind": scene.snapshot_kind,
            "baseline_snapshot_sequence": scene.baseline_snapshot_sequence,
        }
        return ReplicatedRenderFrame(
            terrain_primitives=terrain_primitives,
            entity_states=entity_states,
            hud_primitives=hud_primitives,
            metadata=metadata,
        )

    def render(
        self,
        game,
        scene: ReplicatedMatchScene,
        *,
        local_player_number: int | None = None,
    ) -> ReplicatedRenderFrame:
        frame = self.build_frame(scene, local_player_number=local_player_number)
        self.render_frame(game, frame, snapshot=scene.snapshot)
        return frame

    def render_frame(
        self,
        game,
        frame: ReplicatedRenderFrame,
        *,
        snapshot: MatchSnapshot | None = None,
    ) -> ReplicatedRenderFrame:
        self._visual_renderer.render_primitives(game, frame.terrain_primitives)
        for entity_state in frame.entity_states:
            self._visual_renderer.render_state(game, entity_state)
        self._visual_renderer.render_primitives(game, frame.hud_primitives)

        if hasattr(game, "get_ui") and snapshot is not None:
            self._menu_renderer.draw_player_strip(game, snapshot)
            self._menu_renderer.draw_match_overlay(
                game,
                snapshot,
                local_player_number=frame.metadata.get("local_player_number"),
            )

        return frame

    def _build_hud_primitives(
        self,
        scene: ReplicatedMatchScene,
        *,
        local_player_number: int | None = None,
    ) -> tuple[RenderPrimitive, ...]:
        primitives: list[RenderPrimitive] = []
        for player in scene.get_players():
            tank = scene.get_entity_by_id(player.tank_entity_id)
            if tank is None:
                continue

            health = float(tank.payload.get("health", 100.0))
            fuel = float(tank.payload.get("fuel", 0.0))
            alive = bool(tank.payload.get("alive", True))
            start_of_bar = -10.0 + (2.5 * player.player_number) + 0.1
            start_bar_x = start_of_bar + 0.1
            end_bar_x = start_bar_x + 2.1 * (health / 100.0)
            end_fuel_x = start_bar_x + 2.1 * fuel
            panel_colour = (128, 230, 153, 76)

            hr = min(255, int((1.0 - (health / 200.0)) * 255))
            hg = min(255, int((0.5 + (health / 200.0)) * 255))
            fr = min(255, int((0.5 - (fuel * 0.5)) * 255))
            fb = min(255, int((0.5 + (fuel * 0.5)) * 255))
            tank_colour = player.colour if alive else self._entity_builder._dim_colour(player.colour)

            primitives.extend(
                (
                    PolygonPrimitive(
                        points=(
                            (start_of_bar, 7.4),
                            (start_of_bar + 2.3, 7.4),
                            (start_of_bar + 2.3, 6.6),
                            (start_of_bar, 6.6),
                        ),
                        colour=panel_colour,
                    ),
                    PolygonPrimitive(
                        points=(
                            (start_of_bar + 0.15, 7.0),
                            (start_of_bar + 0.00, 6.7),
                            (start_of_bar + 0.60, 6.7),
                            (start_of_bar + 0.45, 7.0),
                        ),
                        colour=tank_colour,
                    ),
                )
            )

            if end_bar_x > start_bar_x:
                primitives.append(RectPrimitive(start_bar_x, 7.4, end_bar_x, 7.3, (hr, hg, 128)))
            if end_fuel_x > start_bar_x:
                primitives.append(RectPrimitive(start_bar_x, 7.2, end_fuel_x, 7.1, (fr, 128, fb)))
            primitives.extend(
                self._weapon_hud_renderer.build_snapshot_primitives(
                    player.selected_weapon,
                    player.weapon_stocks,
                    start_of_bar + 0.7,
                )
            )

        return tuple(primitives)
