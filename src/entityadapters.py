from __future__ import annotations

from collections.abc import Callable
import math

from .blast import Blast
from .machinegunround import MachineGunRound
from .mirv import Mirv
from .missile import Missile
from .networkstate import EntitySnapshot
from .renderprimitives import (
    EntityRenderState,
    FullscreenOverlayPrimitive,
    LinePrimitive,
    PolygonPrimitive,
    TextureCenteredPrimitive,
)
from .shell import Shell
from .smoke import Smoke
from .tank import Tank
from .trail import Trail


RenderBuilder = Callable[[object, object], EntityRenderState | None]
SnapshotBuilder = Callable[[object, object], EntitySnapshot]


class EntityAdapterRegistry:
    def __init__(self):
        self._render_builders: dict[type, RenderBuilder] = {}
        self._snapshot_builders: dict[type, SnapshotBuilder] = {}
        self._register_defaults()

    def register(
        self,
        entity_cls: type,
        *,
        render_builder: RenderBuilder | None = None,
        snapshot_builder: SnapshotBuilder | None = None,
    ):
        if render_builder is not None:
            self._render_builders[entity_cls] = render_builder
        if snapshot_builder is not None:
            self._snapshot_builders[entity_cls] = snapshot_builder

    def build_render_state(self, game, entity) -> EntityRenderState | None:
        builder = self._find_builder(self._render_builders, entity)
        if builder is not None:
            return builder(game, entity)

        state_getter = getattr(entity, "get_render_state", None)
        if state_getter is not None:
            return state_getter()
        return None

    def build_snapshot(self, game, entity) -> EntitySnapshot:
        builder = self._find_builder(self._snapshot_builders, entity)
        if builder is not None:
            return builder(game, entity)

        snapshot_builder = getattr(entity, "build_network_snapshot", None)
        if snapshot_builder is not None:
            return snapshot_builder()

        entity_id = entity.get_entity_id() if hasattr(entity, "get_entity_id") else -1
        entity_type = entity.get_entity_type() if hasattr(entity, "get_entity_type") else type(entity).__name__.lower()
        position = entity.get_position() if hasattr(entity, "get_position") else (0.0, 0.0)
        return EntitySnapshot(entity_id=entity_id, entity_type=entity_type, position=position, payload={})

    def _find_builder(self, mapping: dict[type, Callable], entity):
        for entity_cls in type(entity).__mro__:
            builder = mapping.get(entity_cls)
            if builder is not None:
                return builder
        return None

    def _register_defaults(self):
        self.register(Tank, render_builder=self._build_tank_render_state, snapshot_builder=self._build_tank_snapshot)
        self.register(Shell, render_builder=self._build_shell_render_state, snapshot_builder=self._build_shell_snapshot)
        self.register(Mirv, render_builder=self._build_mirv_render_state, snapshot_builder=self._build_mirv_snapshot)
        self.register(Missile, render_builder=self._build_missile_render_state, snapshot_builder=self._build_missile_snapshot)
        self.register(
            MachineGunRound,
            render_builder=self._build_machinegun_round_render_state,
            snapshot_builder=self._build_machinegun_round_snapshot,
        )
        self.register(Blast, render_builder=self._build_blast_render_state, snapshot_builder=self._build_blast_snapshot)
        self.register(Smoke, render_builder=self._build_smoke_render_state, snapshot_builder=self._build_smoke_snapshot)
        self.register(Trail, render_builder=self._build_trail_render_state, snapshot_builder=self._build_trail_snapshot)

    def _build_tank_render_state(self, _game, tank: Tank):
        colour = tank.get_colour()
        player = tank.get_player()
        if player is not None:
            colour = player._colour

        primitives = [
            PolygonPrimitive(
                points=tuple(
                    [
                        self._transform_point(-tank._tank_size, 0.0, tank._x, tank._y, tank._tank_angle),
                        self._transform_point(-(tank._tank_size / 2.0), tank._tank_size, tank._x, tank._y, tank._tank_angle),
                        self._transform_point((tank._tank_size / 2.0), tank._tank_size, tank._x, tank._y, tank._tank_angle),
                        self._transform_point(tank._tank_size, 0.0, tank._x, tank._y, tank._tank_angle),
                    ]
                ),
                colour=colour,
            )
        ]

        if tank.alive():
            cx, cy, _ = tank.get_centre()
            arrow_length = (tank._gun_power / 8.0) + (tank._tank_size * 2)
            arrow_colour = (
                (0, 255, 0, 128)
                if tank.get_weapon(tank.get_selected_weapon()).ready_to_fire()
                else (255, 0, 0, 128)
            )
            shaft_points = [
                self._transform_point(lx, ly, cx, cy, tank._gun_angle)
                for lx, ly in [(-0.1, tank._tank_size * 1.5), (-0.1, arrow_length), (0.1, arrow_length), (0.1, tank._tank_size * 1.5)]
            ]
            head_points = [
                self._transform_point(lx, ly, cx, cy, tank._gun_angle)
                for lx, ly in [(-0.2, arrow_length), (0.0, arrow_length + (arrow_length / 4.0)), (0.2, arrow_length)]
            ]
            primitives.extend(
                [
                    PolygonPrimitive(points=tuple(shaft_points), colour=arrow_colour),
                    PolygonPrimitive(points=tuple(head_points), colour=arrow_colour),
                ]
            )

        return EntityRenderState(
            entity_id=tank.get_entity_id(),
            entity_type=tank.get_entity_type(),
            primitives=tuple(primitives),
            metadata={"state": tank._state, "health": tank._health, "fuel": tank._fuel},
        )

    def _build_tank_snapshot(self, _game, tank: Tank):
        return EntitySnapshot(
            entity_id=-1 if tank.get_entity_id() is None else tank.get_entity_id(),
            entity_type=tank.get_entity_type(),
            position=tank.get_position(),
            payload={
                "state": tank._state,
                "health": tank._health,
                "fuel": tank._fuel,
                "gun_angle": tank._gun_angle,
                "gun_power": tank._gun_power,
                "tank_angle": tank._tank_angle,
                "selected_weapon": tank.get_selected_weapon(),
                "player_number": getattr(tank.get_player(), "_number", None),
            },
        )

    def _build_shell_render_state(self, _game, shell: Shell):
        return EntityRenderState(
            entity_id=shell.get_entity_id(),
            entity_type=shell.get_entity_type(),
            primitives=(
                PolygonPrimitive(
                    points=(
                        (shell._x + 0.00, shell._y + 0.018),
                        (shell._x + 0.03, shell._y - 0.018),
                        (shell._x - 0.03, shell._y - 0.018),
                    ),
                    colour=(255, 255, 255),
                ),
            ),
            metadata={"size": shell._size, "damage": shell._damage, "white_out": shell._white_out},
        )

    def _build_shell_snapshot(self, _game, shell: Shell):
        return EntitySnapshot(
            entity_id=-1 if shell.get_entity_id() is None else shell.get_entity_id(),
            entity_type=shell.get_entity_type(),
            position=shell.get_position(),
            payload={
                "size": shell._size,
                "damage": shell._damage,
                "white_out": shell._white_out,
                "player_number": getattr(shell._player, "_number", None),
            },
        )

    def _build_mirv_render_state(self, game, mirv: Mirv):
        return self._build_shell_render_state(game, mirv)

    def _build_mirv_snapshot(self, _game, mirv: Mirv):
        return EntitySnapshot(
            entity_id=-1 if mirv.get_entity_id() is None else mirv.get_entity_id(),
            entity_type=mirv.get_entity_type(),
            position=mirv.get_position(),
            payload={
                "size": mirv._size,
                "damage": mirv._damage,
                "fragments": Mirv.OPTION_Fragments,
                "player_number": getattr(mirv._player, "_number", None),
            },
        )

    def _build_missile_render_state(self, _game, missile: Missile):
        cos_a = math.cos(math.radians(missile._angle))
        sin_a = math.sin(math.radians(missile._angle))
        raw_verts = [(0.0, 0.08), (-0.08, 0.0), (-0.08, -0.16), (0.08, -0.16), (0.08, 0.0)]
        world_pts = []
        for rx, ry in raw_verts:
            tx = rx * cos_a - ry * sin_a
            ty = rx * sin_a + ry * cos_a
            world_pts.append((missile._x + tx, missile._y + ty))

        return EntityRenderState(
            entity_id=missile.get_entity_id(),
            entity_type=missile.get_entity_type(),
            primitives=(PolygonPrimitive(points=tuple(world_pts), colour=(255, 255, 255)),),
            metadata={"angle": missile._angle, "fuel": missile._fuel, "size": missile._size, "damage": missile._damage},
        )

    def _build_missile_snapshot(self, _game, missile: Missile):
        return EntitySnapshot(
            entity_id=-1 if missile.get_entity_id() is None else missile.get_entity_id(),
            entity_type=missile.get_entity_type(),
            position=missile.get_position(),
            payload={
                "angle": missile._angle,
                "fuel": missile._fuel,
                "size": missile._size,
                "damage": missile._damage,
                "player_number": getattr(missile._player, "_number", None),
            },
        )

    def _build_machinegun_round_render_state(self, _game, round_: MachineGunRound):
        return EntityRenderState(
            entity_id=round_.get_entity_id(),
            entity_type=round_.get_entity_type(),
            primitives=(
                LinePrimitive(
                    start=(round_._x_back, round_._y_back),
                    end=(round_._x, round_._y),
                    colour=(255, 255, 255),
                ),
            ),
            metadata={"damage": round_._damage, "kill_next_frame": round_._kill_next_frame},
        )

    def _build_machinegun_round_snapshot(self, _game, round_: MachineGunRound):
        return EntitySnapshot(
            entity_id=-1 if round_.get_entity_id() is None else round_.get_entity_id(),
            entity_type=round_.get_entity_type(),
            position=round_.get_position(),
            payload={
                "back_position": (round_._x_back, round_._y_back),
                "damage": round_._damage,
                "kill_next_frame": round_._kill_next_frame,
                "player_number": getattr(round_._player, "_number", None),
            },
        )

    def _build_blast_render_state(self, _game, blast: Blast):
        primitives = []
        interface = blast._game.get_interface()
        if interface and interface.get_texture_surface(0):
            blast_size = blast._size * 1.1
            primitives.append(
                TextureCenteredPrimitive(
                    texture_id=0,
                    x=blast._x,
                    y=blast._y,
                    width=blast_size * 2.0,
                    alpha=max(0, int(blast._fade_away * 255)),
                )
            )

        if blast._white_out:
            primitives.append(
                FullscreenOverlayPrimitive(
                    colour=(255, 255, 255, max(0, int(blast._white_out_level * 255)))
                )
            )

        return EntityRenderState(
            entity_id=blast.get_entity_id(),
            entity_type=blast.get_entity_type(),
            primitives=tuple(primitives),
            metadata={"size": blast._size, "fade_away": blast._fade_away, "white_out": blast._white_out},
        )

    def _build_blast_snapshot(self, _game, blast: Blast):
        return EntitySnapshot(
            entity_id=-1 if blast.get_entity_id() is None else blast.get_entity_id(),
            entity_type=blast.get_entity_type(),
            position=blast.get_position(),
            payload={
                "size": blast._size,
                "fade_away": blast._fade_away,
                "white_out": blast._white_out,
                "white_out_level": blast._white_out_level,
            },
        )

    def _build_smoke_render_state(self, _game, smoke: Smoke):
        return EntityRenderState(
            entity_id=smoke.get_entity_id(),
            entity_type=smoke.get_entity_type(),
            primitives=(
                TextureCenteredPrimitive(
                    texture_id=smoke._texture_id,
                    x=smoke._x,
                    y=smoke._y,
                    width=smoke._size * 2.0,
                    alpha=max(0, int(smoke._fade_away * 255)),
                    rotation=-smoke._rotate,
                ),
            ),
            metadata={"size": smoke._size, "fade_away": smoke._fade_away},
        )

    def _build_smoke_snapshot(self, _game, smoke: Smoke):
        return EntitySnapshot(
            entity_id=-1 if smoke.get_entity_id() is None else smoke.get_entity_id(),
            entity_type=smoke.get_entity_type(),
            position=smoke.get_position(),
            payload={
                "texture_id": smoke._texture_id,
                "rotation": smoke._rotate,
                "size": smoke._size,
                "fade_away": smoke._fade_away,
            },
        )

    def _build_trail_render_state(self, _game, trail: Trail):
        primitives = []
        for seg in trail._trail_segment_list:
            primitives.append(
                TextureCenteredPrimitive(
                    texture_id=1,
                    x=seg.x,
                    y=seg.y,
                    width=0.2,
                    height=0.4 + seg.length,
                    alpha=max(0, int(seg.fade_away * 255)),
                    rotation=-seg.angle,
                )
            )

        return EntityRenderState(
            entity_id=trail.get_entity_id(),
            entity_type=trail.get_entity_type(),
            primitives=tuple(primitives),
            metadata={"active": trail._active, "segment_count": len(trail._trail_segment_list)},
        )

    def _build_trail_snapshot(self, _game, trail: Trail):
        return EntitySnapshot(
            entity_id=-1 if trail.get_entity_id() is None else trail.get_entity_id(),
            entity_type=trail.get_entity_type(),
            position=(trail._last_x, trail._last_y),
            payload={"active": trail._active, "segment_count": len(trail._trail_segment_list)},
        )

    def _transform_point(self, lx, ly, tx, ty, angle_deg):
        rad = math.radians(angle_deg)
        c = math.cos(rad)
        s = math.sin(rad)
        rx = lx * c - ly * s
        ry = lx * s + ly * c
        return tx + rx, ty + ry
