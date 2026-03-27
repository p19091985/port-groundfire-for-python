from __future__ import annotations

import math
import uuid
from dataclasses import replace
from typing import cast

from ..network.messages import (
    SIMULATION_HZ,
    SNAPSHOT_HZ,
    ClientCommandEnvelope,
    ServerEventEnvelope,
    ServerSnapshotEnvelope,
    SessionToken,
)
from ..sim.match import MatchSnapshot, MatchState, ReplicatedPlayerState
from ..sim.world import ReplicatedEntityState, WorldState
from .constants import (
    INITIAL_MONEY,
    PLAYER_COLOURS,
    PROJECTILE_ENTITY_TYPES,
    TANK_FUEL_STEP,
    TANK_GUN_STEP,
    TANK_MAX_FUEL,
    TANK_MAX_HEALTH,
    TANK_MOVE_STEP,
    TANK_SIZE,
    WEAPON_ORDER,
    WEAPON_SPECS,
)


class MatchController:
    PLAYER_COLOURS = PLAYER_COLOURS
    WEAPON_ORDER = WEAPON_ORDER
    WEAPON_SPECS = WEAPON_SPECS
    PROJECTILE_ENTITY_TYPES = PROJECTILE_ENTITY_TYPES
    INITIAL_MONEY = INITIAL_MONEY
    ROUND_STARTING_TICKS = SIMULATION_HZ * 2
    ROUND_FINISHING_TICKS = SIMULATION_HZ * 2
    SCORE_PHASE_TICKS = SIMULATION_HZ * 2
    SHOP_PHASE_TICKS = SIMULATION_HZ * 3
    ROUND_TIME_LIMIT_TICKS = SIMULATION_HZ * 25
    TANK_SIZE = TANK_SIZE
    TANK_MAX_HEALTH = TANK_MAX_HEALTH
    TANK_MAX_FUEL = TANK_MAX_FUEL
    FULL_SNAPSHOT_INTERVAL = 5
    INPUT_REPEAT_TICKS = 8
    AI_FIRE_INTERVAL_TICKS = 40

    def __init__(
        self,
        *,
        session_id: str | None = None,
        seed: int = 1,
        num_rounds: int = 10,
        max_players: int = 8,
    ):
        self.simulation_hz = SIMULATION_HZ
        self.snapshot_hz = SNAPSHOT_HZ
        self.snapshot_interval_ticks = max(1, self.simulation_hz // self.snapshot_hz)
        self.max_players = max_players
        self._base_seed = seed
        self.match_state = MatchState(session_id=session_id or uuid.uuid4().hex, num_rounds=num_rounds)
        self.world_state = WorldState(seed=seed)
        self._player_tokens: dict[int, SessionToken] = {}
        self._player_addresses: dict[int, tuple[str, int]] = {}
        self._acknowledged_commands: dict[int, int] = {}
        self._acknowledged_snapshots: dict[int, int] = {}
        self._next_ai_sequence_by_player: dict[int, int] = {}
        self._last_fire_tick_by_player: dict[int, int] = {}
        self._last_action_tick_by_player: dict[tuple[int, str], int] = {}
        self._next_snapshot_sequence = 1
        self._next_event_sequence = 1
        self._last_full_snapshot_sequence = 0
        self._last_emitted_snapshot: MatchSnapshot | None = None
        self._last_emitted_snapshot_sequence = 0

    def join_player(
        self,
        player_name: str,
        *,
        requested_slot: int | None = None,
        address: tuple[str, int] | None = None,
        is_computer: bool = False,
    ) -> tuple[ReplicatedPlayerState, SessionToken] | None:
        slot = self._resolve_player_slot(requested_slot)
        if slot is None:
            return None

        colour = self._player_colour_for_slot(slot)
        player = ReplicatedPlayerState(
            player_number=slot,
            name=player_name,
            money=self.INITIAL_MONEY,
            connected=True,
            is_computer=is_computer,
            colour=colour,
            is_leader=False,
            selected_weapon="shell",
            weapon_stocks=self._default_weapon_stocks(),
            round_defeated_player_numbers=(),
        )
        token = SessionToken(token=uuid.uuid4().hex, player_number=slot)
        self.match_state.upsert_player(player)
        self._player_tokens[slot] = token
        self._acknowledged_commands.setdefault(slot, 0)
        self._acknowledged_snapshots.setdefault(slot, 0)
        self._next_ai_sequence_by_player.setdefault(slot, 1)
        if address is not None:
            self._player_addresses[slot] = address

        if self.match_state.current_round == 0:
            self._start_round(1)
        else:
            self._spawn_player_tank(slot)

        self.match_state.queue_event("player_joined", player_number=slot, player_name=player_name)
        joined_player = self.match_state.get_player(slot)
        if joined_player is None:
            return None
        return joined_player, token

    def disconnect_player(self, player_number: int, *, session_token: str | None = None) -> bool:
        token = self._player_tokens.get(player_number)
        if token is None:
            return False
        if session_token is not None and token.token != session_token:
            return False

        self._player_tokens.pop(player_number, None)
        self._player_addresses.pop(player_number, None)
        self._acknowledged_commands.pop(player_number, None)
        self._acknowledged_snapshots.pop(player_number, None)
        self._next_ai_sequence_by_player.pop(player_number, None)
        self.match_state.remove_player(player_number)
        self.match_state.queue_event("player_disconnected", player_number=player_number)
        return True

    def remember_player_address(self, player_number: int, address: tuple[str, int]):
        self._player_addresses[player_number] = address

    def get_player_addresses(self) -> tuple[tuple[str, int], ...]:
        seen = set()
        ordered = []
        for player_number in sorted(self._player_addresses):
            address = self._player_addresses[player_number]
            if address not in seen:
                seen.add(address)
                ordered.append(address)
        return tuple(ordered)

    def apply_command_envelope(self, envelope: ClientCommandEnvelope) -> bool:
        if envelope.session_id != self.match_state.session_id:
            return False

        token = self._player_tokens.get(envelope.player_number)
        if token is None:
            return False
        if envelope.session_token is not None and envelope.session_token != token.token:
            return False

        player = self.match_state.get_player(envelope.player_number)
        if player is None:
            return False

        acknowledged_sequence = max(
            self._acknowledged_commands.get(envelope.player_number, 0),
            envelope.client_sequence,
        )
        acknowledged_snapshot = max(
            self._acknowledged_snapshots.get(envelope.player_number, 0),
            int(envelope.acknowledged_snapshot_sequence or 0),
        )
        self._acknowledged_commands[envelope.player_number] = acknowledged_sequence
        self._acknowledged_snapshots[envelope.player_number] = acknowledged_snapshot
        self.match_state.update_player(
            envelope.player_number,
            acknowledged_command_sequence=acknowledged_sequence,
            acknowledged_snapshot_sequence=acknowledged_snapshot,
        )

        commands = {str(key): bool(value) for key, value in envelope.commands.items()}
        self._apply_weapon_selection_commands(envelope.player_number, commands)

        if self.match_state.game_phase == "shop":
            self._apply_shop_commands(envelope.player_number, commands)
            self._sync_tank_payload(envelope.player_number, last_commands=commands)
            return True

        if self.match_state.game_phase != "round_in_action":
            self._sync_tank_payload(envelope.player_number, last_commands=commands)
            return True

        player = self.match_state.get_player(envelope.player_number)
        if player is None or player.tank_entity_id is None:
            return False

        tank = self.world_state.entity_registry.get(player.tank_entity_id)
        if tank is None:
            return False

        updated_tank = self._apply_player_commands(tank, envelope, commands)
        self.world_state.entity_registry.replace(updated_tank)
        return True

    def step(self):
        self.match_state.simulation_tick += 1

        if self.match_state.game_phase == "round_starting":
            self._step_round_starting()
            return

        if self.match_state.game_phase == "round_in_action":
            self._step_computer_players()
            self._step_projectiles()
            self._settle_alive_tanks_on_terrain()
            self._step_round_in_action_timer()
            if self.match_state.game_phase == "round_in_action":
                self._evaluate_round_state()
            return

        if self.match_state.game_phase == "round_finishing":
            if self._step_phase_timer():
                self._advance_after_round_finish()
            return

        if self.match_state.game_phase == "score":
            if self._step_phase_timer():
                self._begin_shop_phase()
            return

        if self.match_state.game_phase == "shop":
            self._step_computer_players()
            if self._step_phase_timer():
                self._start_round(self.match_state.current_round + 1)

    def should_emit_snapshot(self) -> bool:
        return self.match_state.simulation_tick > 0 and (
            self.match_state.simulation_tick % self.snapshot_interval_ticks == 0
        )

    def build_snapshot(self, *, include_terrain_profile: bool = True) -> MatchSnapshot:
        return self.match_state.snapshot(
            self.world_state.snapshot_entities(),
            seed=self.world_state.seed,
            world_width=self.world_state.width,
            terrain_revision=self.world_state.terrain_revision,
            terrain_profile=self.world_state.snapshot_terrain_profile() if include_terrain_profile else (),
        )

    def build_snapshot_envelope(self) -> ServerSnapshotEnvelope:
        full_snapshot = self._should_emit_full_snapshot() or self._last_emitted_snapshot is None
        authoritative_snapshot = self.build_snapshot(include_terrain_profile=False)
        events = self.match_state.drain_events()
        patches = self.world_state.drain_terrain_patches()
        snapshot_sequence = self._next_snapshot_sequence
        removed_entity_ids: tuple[int, ...] = ()
        removed_player_numbers: tuple[int, ...] = ()
        snapshot_kind = "full" if full_snapshot else "delta"
        baseline_snapshot_sequence: int | None

        if full_snapshot:
            snapshot = replace(
                authoritative_snapshot,
                terrain_profile=self.world_state.snapshot_terrain_profile(),
            )
            baseline_snapshot_sequence = snapshot_sequence
            self._last_full_snapshot_sequence = snapshot_sequence
        else:
            baseline_snapshot_sequence = self._last_emitted_snapshot_sequence or None
            snapshot, removed_entity_ids, removed_player_numbers = self._build_delta_snapshot(
                authoritative_snapshot,
                self._last_emitted_snapshot,
            )

        envelope = ServerSnapshotEnvelope(
            session_id=self.match_state.session_id,
            snapshot_sequence=snapshot_sequence,
            simulation_tick=self.match_state.simulation_tick,
            acknowledged_command_sequences=dict(self._acknowledged_commands),
            snapshot=snapshot,
            removed_entity_ids=removed_entity_ids,
            removed_player_numbers=removed_player_numbers,
            terrain_patches=patches,
            events=events,
            snapshot_kind=snapshot_kind,
            baseline_snapshot_sequence=baseline_snapshot_sequence,
        )
        self._next_snapshot_sequence += 1
        self._last_emitted_snapshot = authoritative_snapshot
        self._last_emitted_snapshot_sequence = snapshot_sequence
        return envelope

    def build_event_envelope(self, events: tuple[dict, ...]) -> ServerEventEnvelope | None:
        if not events:
            return None
        envelope = ServerEventEnvelope(
            session_id=self.match_state.session_id,
            event_sequence=self._next_event_sequence,
            simulation_tick=self.match_state.simulation_tick,
            events=events,
        )
        self._next_event_sequence += 1
        return envelope

    def _resolve_player_slot(self, requested_slot: int | None) -> int | None:
        if requested_slot is not None:
            if requested_slot not in self.match_state.player_slots and 0 <= requested_slot < self.max_players:
                return requested_slot
            return None

        for slot in range(self.max_players):
            if slot not in self.match_state.player_slots:
                return slot
        return None

    def _apply_player_commands(
        self,
        tank: ReplicatedEntityState,
        envelope: ClientCommandEnvelope,
        commands: dict[str, bool],
    ) -> ReplicatedEntityState:
        x, y = tank.position
        vx, vy = tank.velocity
        gun_angle = float(tank.payload.get("gun_angle", 45.0))
        fuel = max(0.0, float(tank.payload.get("fuel", self.TANK_MAX_FUEL)))
        moved = False

        if bool(tank.payload.get("alive", True)) and commands.get("tankleft") and fuel > 0.0:
            x -= TANK_MOVE_STEP
            moved = True
        if bool(tank.payload.get("alive", True)) and commands.get("tankright") and fuel > 0.0:
            x += TANK_MOVE_STEP
            moved = True
        if commands.get("gunleft") or commands.get("gunup"):
            gun_angle = min(180.0, gun_angle + TANK_GUN_STEP)
        if commands.get("gunright") or commands.get("gundown"):
            gun_angle = max(0.0, gun_angle - TANK_GUN_STEP)

        max_x = (self.world_state.width / 2.0) - 0.25
        x = max(-max_x, min(max_x, x))
        if moved:
            fuel = max(0.0, fuel - TANK_FUEL_STEP)
        y = self.world_state.terrain.height_at(x)

        _, active_weapon = self._ensure_selected_weapon_available(envelope.player_number)
        updated = replace(
            tank,
            position=(x, y),
            velocity=(vx, vy),
            angle=gun_angle,
            payload={
                **tank.payload,
                "fuel": fuel,
                "gun_angle": gun_angle,
                "last_commands": commands,
                "selected_weapon": active_weapon,
            },
        )

        should_fire = bool(tank.payload.get("alive", True)) and commands.get("fire")
        fired_this_tick = self._last_fire_tick_by_player.get(envelope.player_number)
        if should_fire and fired_this_tick != self.match_state.simulation_tick:
            self._last_fire_tick_by_player[envelope.player_number] = self.match_state.simulation_tick
            self._fire_weapon(
                envelope.player_number,
                active_weapon,
                x=x,
                y=y,
                gun_angle=gun_angle,
            )
            refreshed_player = self.match_state.get_player(envelope.player_number)
            updated = replace(
                updated,
                payload={
                    **updated.payload,
                    "selected_weapon": getattr(refreshed_player, "selected_weapon", active_weapon),
                },
            )

        return updated

    def _player_colour_for_slot(self, player_number: int) -> tuple[int, int, int]:
        return self.PLAYER_COLOURS[player_number % len(self.PLAYER_COLOURS)]

    def _start_round(self, round_number: int):
        self.world_state = WorldState(seed=self._base_seed + max(0, round_number - 1))
        self.match_state.current_round = round_number
        self.match_state.game_phase = "round_starting"
        self.match_state.phase_ticks_remaining = self.ROUND_STARTING_TICKS
        self.match_state.round_winner_player_number = None
        self.match_state.winner_player_number = None

        for player_number in sorted(self.match_state.player_slots):
            self.match_state.update_player(player_number, round_defeated_player_numbers=())

        for slot in sorted(self.match_state.player_slots):
            self._spawn_player_tank(slot)

        self.match_state.queue_event(
            "round_started",
            round_number=round_number,
            round_seed=self.world_state.seed,
            player_count=len(self.match_state.player_slots),
        )

    def _spawn_player_tank(self, player_number: int):
        player = self.match_state.get_player(player_number)
        if player is None:
            return

        ordered_slots = sorted(self.match_state.player_slots)
        slot_index = ordered_slots.index(player_number)
        spawn_x = self._spawn_x_for_index(slot_index, len(ordered_slots))
        spawn_y = self.world_state.terrain.height_at(spawn_x)
        tank = self.world_state.entity_registry.create(
            "tank",
            position=(spawn_x, spawn_y),
            owner_player=player_number,
            payload={
                "health": self.TANK_MAX_HEALTH,
                "fuel": self.TANK_MAX_FUEL,
                "gun_angle": 45.0,
                "last_commands": {},
                "name": player.name,
                "colour": player.colour,
                "size": self.TANK_SIZE,
                "alive": True,
                "selected_weapon": player.selected_weapon,
            },
        )
        self.match_state.update_player(player_number, tank_entity_id=tank.entity_id)

    def _spawn_x_for_index(self, index: int, total_players: int) -> float:
        if total_players <= 1:
            return 0.0

        spawn_width = self.world_state.width - 2.0
        start_x = -(spawn_width / 2.0)
        spacing = spawn_width / max(1, total_players - 1)
        return start_x + (spacing * index)

    def _step_round_starting(self):
        if self._step_phase_timer():
            self.match_state.game_phase = "round_in_action"
            self.match_state.phase_ticks_remaining = self.ROUND_TIME_LIMIT_TICKS
            self.match_state.queue_event("round_in_action", round_number=self.match_state.current_round)

    def _step_round_in_action_timer(self):
        if self._step_phase_timer():
            self._begin_round_finishing(reason="time_limit")

    def _step_projectiles(self):
        for entity in self.world_state.entity_registry.snapshot():
            if entity.entity_type not in self.PROJECTILE_ENTITY_TYPES:
                continue

            gravity = float(entity.payload.get("gravity", self.WEAPON_SPECS["shell"]["gravity"]))
            next_velocity = (
                entity.velocity[0],
                entity.velocity[1] - (gravity / self.simulation_hz),
            )
            next_x = entity.position[0] + (next_velocity[0] / self.simulation_hz)
            next_y = entity.position[1] + (next_velocity[1] / self.simulation_hz)
            ttl_ticks = int(entity.payload.get("ttl_ticks", 1)) - 1
            terrain_height = self.world_state.terrain.height_at(next_x)
            hit_tank = self._find_tank_hit(next_x, next_y)
            collided_with_terrain = next_y <= terrain_height
            updated = replace(
                entity,
                position=(next_x, next_y),
                velocity=next_velocity,
                payload={**entity.payload, "ttl_ticks": ttl_ticks},
            )
            self.world_state.entity_registry.replace(updated)

            if ttl_ticks > 0 and not collided_with_terrain and hit_tank is None:
                continue

            self.world_state.entity_registry.remove(entity.entity_id)
            impact_x = next_x
            impact_y = terrain_height if collided_with_terrain else next_y
            if hit_tank is not None:
                impact_x = hit_tank.position[0]
                impact_y = hit_tank.position[1] + (float(hit_tank.payload.get("size", self.TANK_SIZE)) / 2.0)

            patch = self.world_state.apply_explosion(
                impact_x,
                impact_y,
                float(entity.payload.get("blast_radius", self.WEAPON_SPECS["shell"]["blast_radius"])),
                caused_by=entity.owner_player,
            )
            if patch is not None:
                self.match_state.queue_event(
                    "terrain_patched",
                    patch_id=patch.patch_id,
                    entity_id=entity.entity_id,
                    player_number=entity.owner_player,
                )

            self._apply_explosion_damage(
                impact_x,
                impact_y,
                radius=float(entity.payload.get("blast_radius", self.WEAPON_SPECS["shell"]["blast_radius"])),
                damage=float(entity.payload.get("blast_damage", self.WEAPON_SPECS["shell"]["blast_damage"])),
                caused_by=entity.owner_player,
            )

    def _find_tank_hit(self, world_x: float, world_y: float) -> ReplicatedEntityState | None:
        for player_number in sorted(self.match_state.player_slots):
            player = self.match_state.player_slots[player_number]
            if player.tank_entity_id is None:
                continue
            tank = self.world_state.entity_registry.get(player.tank_entity_id)
            if tank is None or tank.entity_type != "tank":
                continue
            if not bool(tank.payload.get("alive", True)):
                continue

            size = float(tank.payload.get("size", self.TANK_SIZE))
            centre_x = tank.position[0]
            centre_y = tank.position[1] + (size / 2.0)
            if ((centre_x - world_x) ** 2 + (centre_y - world_y) ** 2) <= (size * size):
                return tank
        return None

    def _apply_explosion_damage(
        self,
        world_x: float,
        world_y: float,
        *,
        radius: float,
        damage: float,
        caused_by: int | None,
    ):
        max_distance_sq = max(0.0001, (radius + self.TANK_SIZE) ** 2)
        for player_number in sorted(self.match_state.player_slots):
            player = self.match_state.player_slots[player_number]
            if player.tank_entity_id is None:
                continue
            tank = self.world_state.entity_registry.get(player.tank_entity_id)
            if tank is None or tank.entity_type != "tank":
                continue
            if not bool(tank.payload.get("alive", True)):
                continue

            size = float(tank.payload.get("size", self.TANK_SIZE))
            centre_x = tank.position[0]
            centre_y = tank.position[1] + (size / 2.0)
            squared_distance = ((centre_x - world_x) ** 2) + ((centre_y - world_y) ** 2)
            if squared_distance > max_distance_sq:
                continue

            scaled_damage = max(0.0, damage * (1.0 - (squared_distance / max_distance_sq)))
            previous_health = float(tank.payload.get("health", self.TANK_MAX_HEALTH))
            next_health = max(0.0, previous_health - scaled_damage)
            destroyed = next_health <= 0.0
            updated_tank = replace(
                tank,
                payload={
                    **tank.payload,
                    "health": next_health,
                    "alive": not destroyed,
                },
            )
            self.world_state.entity_registry.replace(updated_tank)
            self.match_state.queue_event(
                "tank_damaged",
                player_number=player_number,
                entity_id=tank.entity_id,
                health=round(next_health, 4),
                damage=round(scaled_damage, 4),
            )
            if destroyed:
                self._record_defeat(caused_by, player_number)
                self.match_state.queue_event(
                    "tank_destroyed",
                    player_number=player_number,
                    entity_id=tank.entity_id,
                    caused_by=caused_by,
                )

    def _record_defeat(self, caused_by: int | None, defeated_player_number: int):
        if caused_by is None:
            return
        player = self.match_state.get_player(caused_by)
        if player is None:
            return
        defeated_players = list(player.round_defeated_player_numbers)
        defeated_players.append(defeated_player_number)
        self.match_state.update_player(
            caused_by,
            round_defeated_player_numbers=tuple(defeated_players),
        )

    def _settle_alive_tanks_on_terrain(self):
        for player_number in sorted(self.match_state.player_slots):
            player = self.match_state.player_slots[player_number]
            if player.tank_entity_id is None:
                continue
            tank = self.world_state.entity_registry.get(player.tank_entity_id)
            if tank is None or tank.entity_type != "tank":
                continue
            if not bool(tank.payload.get("alive", True)):
                continue

            x, _y = tank.position
            settled = replace(tank, position=(x, self.world_state.terrain.height_at(x)))
            self.world_state.entity_registry.replace(settled)

    def _step_phase_timer(self) -> bool:
        if self.match_state.phase_ticks_remaining <= 0:
            return True
        self.match_state.phase_ticks_remaining -= 1
        return self.match_state.phase_ticks_remaining <= 0

    def _evaluate_round_state(self):
        alive_players = self._alive_player_numbers()
        if len(self.match_state.player_slots) >= 2 and len(alive_players) <= 1 and self.match_state.current_round > 0:
            self._begin_round_finishing(reason="last_tank_standing")

    def _alive_player_numbers(self) -> tuple[int, ...]:
        alive_players: list[int] = []
        for player_number in sorted(self.match_state.player_slots):
            player = self.match_state.player_slots[player_number]
            if player.tank_entity_id is None:
                continue
            tank = self.world_state.entity_registry.get(player.tank_entity_id)
            if tank is None or tank.entity_type != "tank":
                continue
            if bool(tank.payload.get("alive", True)) and float(tank.payload.get("health", 0.0)) > 0.0:
                alive_players.append(player_number)
        return tuple(alive_players)

    def _begin_round_finishing(self, *, reason: str):
        if self.match_state.game_phase == "round_finishing":
            return

        winner_player_number = self._determine_round_winner()
        self.match_state.game_phase = "round_finishing"
        self.match_state.phase_ticks_remaining = self.ROUND_FINISHING_TICKS
        self.match_state.round_winner_player_number = winner_player_number
        self._apply_round_rewards(winner_player_number)
        self.match_state.queue_event(
            "round_finished",
            round_number=self.match_state.current_round,
            winner_player_number=winner_player_number,
            reason=reason,
        )

    def _determine_round_winner(self) -> int | None:
        alive_players = self._alive_player_numbers()
        if len(alive_players) == 1:
            return alive_players[0]

        ranked: list[tuple[float, int, int]] = []
        for player_number in sorted(self.match_state.player_slots):
            player = self.match_state.player_slots[player_number]
            tank = None
            if player.tank_entity_id is not None:
                tank = self.world_state.entity_registry.get(player.tank_entity_id)
            health = 0.0
            if tank is not None and tank.entity_type == "tank":
                health = float(tank.payload.get("health", 0.0))
            ranked.append((health, player.score, -player_number))

        if not ranked:
            return None

        winner_key = max(ranked)
        return -winner_key[2]

    def _apply_round_rewards(self, winner_player_number: int | None):
        for player_number in sorted(self.match_state.player_slots):
            player = self.match_state.player_slots[player_number]
            score = player.score
            money = player.money + 10
            if player_number == winner_player_number:
                score += 100
                money += 25
            self.match_state.update_player(player_number, score=score, money=money)

    def _advance_after_round_finish(self):
        if self.match_state.current_round >= self.match_state.num_rounds:
            self._finish_match()
            return

        self.match_state.game_phase = "score"
        self.match_state.phase_ticks_remaining = self.SCORE_PHASE_TICKS
        self.match_state.queue_event(
            "score_phase_started",
            round_number=self.match_state.current_round,
            next_round=self.match_state.current_round + 1,
        )

    def _begin_shop_phase(self):
        self._update_leader_flags()
        self.match_state.game_phase = "shop"
        self.match_state.phase_ticks_remaining = self.SHOP_PHASE_TICKS
        self.match_state.queue_event(
            "shop_started",
            round_number=self.match_state.current_round,
            next_round=self.match_state.current_round + 1,
        )

    def _update_leader_flags(self):
        if not self.match_state.player_slots:
            return

        ordered_players = [
            self.match_state.player_slots[player_number]
            for player_number in sorted(self.match_state.player_slots)
        ]
        ordered_players.sort(key=lambda player: (-player.score, player.player_number))
        unique_leader = len(ordered_players) == 1 or ordered_players[0].score > ordered_players[1].score
        leader_numbers = {ordered_players[0].player_number} if unique_leader else set()

        for player_number in sorted(self.match_state.player_slots):
            self.match_state.update_player(
                player_number,
                is_leader=player_number in leader_numbers,
            )

    def _finish_match(self):
        self.match_state.game_phase = "winner"
        self.match_state.phase_ticks_remaining = 0
        self.match_state.winner_player_number = self._determine_match_winner()
        self.match_state.queue_event(
            "match_won",
            player_number=self.match_state.winner_player_number,
            round_number=self.match_state.current_round,
        )

    def _determine_match_winner(self) -> int | None:
        if not self.match_state.player_slots:
            return None
        best_score = max((player.score, -player.player_number) for player in self.match_state.player_slots.values())
        return -best_score[1]

    def _default_weapon_stocks(self) -> tuple[tuple[str, int], ...]:
        return tuple((weapon, 0) for weapon in self.WEAPON_ORDER if weapon != "shell")

    def _weapon_stock_map(self, weapon_stocks: tuple[tuple[str, int], ...]) -> dict[str, int]:
        stocks = {weapon: 0 for weapon in self.WEAPON_ORDER}
        stocks["shell"] = -1
        for weapon, amount in weapon_stocks:
            stocks[str(weapon)] = int(amount)
        return stocks

    def _weapon_stock_tuple(self, stocks: dict[str, int]) -> tuple[tuple[str, int], ...]:
        return tuple((weapon, int(stocks.get(weapon, 0))) for weapon in self.WEAPON_ORDER if weapon != "shell")

    def _ensure_selected_weapon_available(self, player_number: int) -> tuple[ReplicatedPlayerState, str]:
        player = self.match_state.player_slots[player_number]
        selected_weapon = player.selected_weapon if player.selected_weapon in self.WEAPON_ORDER else "shell"
        stocks = self._weapon_stock_map(player.weapon_stocks)
        if selected_weapon != "shell" and stocks.get(selected_weapon, 0) <= 0:
            selected_weapon = "shell"
            self.match_state.update_player(player_number, selected_weapon=selected_weapon)
        player = self.match_state.player_slots[player_number]
        return player, selected_weapon

    def _apply_weapon_selection_commands(self, player_number: int, commands: dict[str, bool]):
        if commands.get("weaponup"):
            self._cycle_selected_weapon(player_number, 1)
        elif commands.get("weapondown"):
            self._cycle_selected_weapon(player_number, -1)

    def _cycle_selected_weapon(self, player_number: int, direction: int):
        if not self._action_ready(player_number, "weapon_cycle", self.INPUT_REPEAT_TICKS):
            return

        player = self.match_state.get_player(player_number)
        if player is None:
            return

        try:
            current_index = self.WEAPON_ORDER.index(player.selected_weapon)
        except ValueError:
            current_index = 0
        next_index = (current_index + direction) % len(self.WEAPON_ORDER)
        selected_weapon = self.WEAPON_ORDER[next_index]
        self.match_state.update_player(player_number, selected_weapon=selected_weapon)
        self._sync_tank_payload(player_number, selected_weapon=selected_weapon)
        self.match_state.queue_event("weapon_selected", player_number=player_number, weapon=selected_weapon)

    def _apply_shop_commands(self, player_number: int, commands: dict[str, bool]):
        if not commands.get("fire"):
            return
        if not self._action_ready(player_number, "shop_buy", self.INPUT_REPEAT_TICKS):
            return

        player = self.match_state.get_player(player_number)
        if player is None:
            return

        selected_weapon = player.selected_weapon
        if selected_weapon == "shell":
            return

        spec = self.WEAPON_SPECS[selected_weapon]
        weapon_cost = self._spec_int(spec, "cost")
        if player.money < weapon_cost:
            self.match_state.queue_event(
                "weapon_purchase_rejected",
                player_number=player_number,
                weapon=selected_weapon,
                money=player.money,
            )
            return

        stocks = self._weapon_stock_map(player.weapon_stocks)
        stocks[selected_weapon] = stocks.get(selected_weapon, 0) + self._spec_int(spec, "bundle")
        next_money = player.money - weapon_cost
        self.match_state.update_player(
            player_number,
            money=next_money,
            weapon_stocks=self._weapon_stock_tuple(stocks),
        )
        self.match_state.queue_event(
            "weapon_purchased",
            player_number=player_number,
            weapon=selected_weapon,
            money=next_money,
            ammo=stocks[selected_weapon],
        )

    def _fire_weapon(self, player_number: int, weapon_name: str, *, x: float, y: float, gun_angle: float):
        player = self.match_state.get_player(player_number)
        if player is None:
            return

        player, active_weapon = self._ensure_selected_weapon_available(player_number)
        weapon_name = active_weapon if weapon_name in self.WEAPON_SPECS else active_weapon
        spec = self.WEAPON_SPECS[weapon_name]
        stocks = self._weapon_stock_map(player.weapon_stocks)
        if weapon_name != "shell":
            remaining = stocks.get(weapon_name, 0)
            if remaining <= 0:
                weapon_name = "shell"
                spec = self.WEAPON_SPECS["shell"]
            else:
                stocks[weapon_name] = remaining - 1
                next_selected_weapon = weapon_name if stocks[weapon_name] > 0 else "shell"
                self.match_state.update_player(
                    player_number,
                    selected_weapon=next_selected_weapon,
                    weapon_stocks=self._weapon_stock_tuple(stocks),
                )
                self._sync_tank_payload(player_number, selected_weapon=next_selected_weapon)

        projectile_count = self._spec_int(spec, "projectile_count")
        spread = self._spec_float(spec, "spread")
        projectile_angles = [gun_angle]
        if projectile_count > 1:
            midpoint = (projectile_count - 1) / 2.0
            projectile_angles = [gun_angle + ((index - midpoint) * spread) for index in range(projectile_count)]

        for projectile_angle in projectile_angles:
            radians = math.radians(projectile_angle)
            self.world_state.entity_registry.create(
                self._spec_str(spec, "entity_type"),
                position=(x, y + 0.4),
                velocity=(
                    math.cos(radians) * self._spec_float(spec, "speed"),
                    math.sin(radians) * self._spec_float(spec, "speed"),
                ),
                angle=projectile_angle,
                owner_player=player_number,
                payload={
                    "weapon": weapon_name,
                    "ttl_ticks": self._spec_int(spec, "ttl_ticks"),
                    "blast_radius": self._spec_float(spec, "blast_radius"),
                    "blast_damage": self._spec_float(spec, "blast_damage"),
                    "gravity": self._spec_float(spec, "gravity"),
                    "size": self._spec_float(spec, "size"),
                },
            )

        refreshed_player = self.match_state.get_player(player_number)
        ammo_remaining = -1
        if refreshed_player is not None:
            ammo_remaining = self._weapon_stock_map(refreshed_player.weapon_stocks).get(weapon_name, -1)
        self.match_state.queue_event(
            "weapon_fired",
            player_number=player_number,
            weapon=weapon_name,
            ammo_remaining=ammo_remaining,
            simulation_tick=self.match_state.simulation_tick,
        )

    def _sync_tank_payload(self, player_number: int, **payload_updates):
        player = self.match_state.get_player(player_number)
        if player is None or player.tank_entity_id is None:
            return
        tank = self.world_state.entity_registry.get(player.tank_entity_id)
        if tank is None:
            return
        updated = replace(tank, payload={**tank.payload, **payload_updates})
        self.world_state.entity_registry.replace(updated)

    def _step_computer_players(self):
        for player_number in sorted(self.match_state.player_slots):
            player = self.match_state.player_slots[player_number]
            if not player.is_computer or not player.connected:
                continue
            if self.match_state.game_phase == "round_in_action":
                commands = self._build_ai_round_commands(player)
            elif self.match_state.game_phase == "shop":
                commands = self._build_ai_shop_commands(player)
            else:
                commands = {}
            if any(commands.values()):
                self._issue_ai_commands(player_number, commands)

    def _build_ai_round_commands(self, player: ReplicatedPlayerState) -> dict[str, bool]:
        tank = self._tank_for_player(player.player_number)
        target = self._select_ai_target(player.player_number)
        if tank is None or target is None or not bool(tank.payload.get("alive", True)):
            return {}

        commands: dict[str, bool] = {}
        desired_weapon = self._best_available_weapon(player)
        if player.selected_weapon != desired_weapon:
            commands[self._cycle_command_towards(player.selected_weapon, desired_weapon)] = True

        gun_angle = float(tank.payload.get("gun_angle", 45.0))
        desired_angle = self._estimate_ai_angle(tank, target)
        if desired_angle > gun_angle + 2.5:
            commands["gunup"] = True
        elif desired_angle < gun_angle - 2.5:
            commands["gundown"] = True

        dx = target.position[0] - tank.position[0]
        fuel = float(tank.payload.get("fuel", self.TANK_MAX_FUEL))
        if fuel > 0.15 and abs(dx) > 1.75:
            commands["tankright" if dx > 0.0 else "tankleft"] = True

        last_fire_tick = self._last_fire_tick_by_player.get(player.player_number, -self.AI_FIRE_INTERVAL_TICKS)
        if (
            abs(desired_angle - gun_angle) <= 6.0
            and (self.match_state.simulation_tick - last_fire_tick) >= self.AI_FIRE_INTERVAL_TICKS
        ):
            commands["fire"] = True

        return commands

    def _build_ai_shop_commands(self, player: ReplicatedPlayerState) -> dict[str, bool]:
        desired_weapon = self._best_affordable_shop_weapon(player)
        if desired_weapon is None:
            return {}
        if player.selected_weapon != desired_weapon:
            return {self._cycle_command_towards(player.selected_weapon, desired_weapon): True}
        return {"fire": True}

    def _issue_ai_commands(self, player_number: int, commands: dict[str, bool]):
        token = self._player_tokens.get(player_number)
        if token is None:
            return

        sequence = self._next_ai_sequence_by_player.get(player_number, 1)
        self._next_ai_sequence_by_player[player_number] = sequence + 1
        envelope = ClientCommandEnvelope(
            session_id=self.match_state.session_id,
            player_number=player_number,
            client_sequence=sequence,
            acknowledged_snapshot_sequence=self._last_full_snapshot_sequence or None,
            simulation_tick=self.match_state.simulation_tick,
            issued_at=float(self.match_state.simulation_tick) / float(self.simulation_hz),
            source="server:ai",
            commands=commands,
            session_token=token.token,
        )
        self.apply_command_envelope(envelope)

    def _tank_for_player(self, player_number: int) -> ReplicatedEntityState | None:
        player = self.match_state.get_player(player_number)
        if player is None or player.tank_entity_id is None:
            return None
        return self.world_state.entity_registry.get(player.tank_entity_id)

    def _select_ai_target(self, player_number: int) -> ReplicatedEntityState | None:
        source_tank = self._tank_for_player(player_number)
        if source_tank is None:
            return None

        best_target = None
        best_distance_sq = float("inf")
        for candidate_player in sorted(self.match_state.player_slots):
            if candidate_player == player_number:
                continue
            candidate_tank = self._tank_for_player(candidate_player)
            if candidate_tank is None or not bool(candidate_tank.payload.get("alive", True)):
                continue
            distance_sq = (
                (candidate_tank.position[0] - source_tank.position[0]) ** 2
                + (candidate_tank.position[1] - source_tank.position[1]) ** 2
            )
            if distance_sq < best_distance_sq:
                best_distance_sq = distance_sq
                best_target = candidate_tank
        return best_target

    def _estimate_ai_angle(self, source: ReplicatedEntityState, target: ReplicatedEntityState) -> float:
        dx = target.position[0] - source.position[0]
        dy = target.position[1] - source.position[1]
        loft = abs(dx) * 0.33
        desired_angle = math.degrees(math.atan2(dy + loft + 0.2, dx if dx != 0.0 else 0.001))
        return max(8.0, min(172.0, desired_angle))

    def _best_available_weapon(self, player: ReplicatedPlayerState) -> str:
        stocks = self._weapon_stock_map(player.weapon_stocks)
        for weapon in ("nuke", "mirv", "missile", "machinegun"):
            if stocks.get(weapon, 0) > 0:
                return weapon
        return "shell"

    def _best_affordable_shop_weapon(self, player: ReplicatedPlayerState) -> str | None:
        stocks = self._weapon_stock_map(player.weapon_stocks)
        goals = (("nuke", 1), ("mirv", 1), ("missile", 2), ("machinegun", 3))
        for weapon, minimum_stock in goals:
            spec = self.WEAPON_SPECS[weapon]
            if player.money >= self._spec_int(spec, "cost") and stocks.get(weapon, 0) < minimum_stock:
                return weapon
        return None

    def _cycle_command_towards(self, current_weapon: str, desired_weapon: str) -> str:
        try:
            current_index = self.WEAPON_ORDER.index(current_weapon)
        except ValueError:
            current_index = 0
        try:
            desired_index = self.WEAPON_ORDER.index(desired_weapon)
        except ValueError:
            desired_index = 0

        forward_distance = (desired_index - current_index) % len(self.WEAPON_ORDER)
        backward_distance = (current_index - desired_index) % len(self.WEAPON_ORDER)
        return "weaponup" if forward_distance <= backward_distance else "weapondown"

    def _action_ready(self, player_number: int, action_name: str, repeat_ticks: int) -> bool:
        key = (player_number, action_name)
        previous_tick = self._last_action_tick_by_player.get(key, -repeat_ticks)
        if (self.match_state.simulation_tick - previous_tick) < repeat_ticks:
            return False
        self._last_action_tick_by_player[key] = self.match_state.simulation_tick
        return True

    def _should_emit_full_snapshot(self) -> bool:
        if self._next_snapshot_sequence == 1:
            return True
        if self.match_state.game_phase in {"round_starting", "score", "shop", "winner"}:
            return True
        if self._last_full_snapshot_sequence == 0:
            return True
        return (self._next_snapshot_sequence - self._last_full_snapshot_sequence) >= self.FULL_SNAPSHOT_INTERVAL

    def _build_delta_snapshot(
        self,
        current: MatchSnapshot,
        previous: MatchSnapshot | None,
    ) -> tuple[MatchSnapshot, tuple[int, ...], tuple[int, ...]]:
        if previous is None:
            return current, (), ()

        previous_players = {player.player_number: player for player in previous.players}
        current_players = {player.player_number: player for player in current.players}
        changed_players = tuple(
            player
            for player_number, player in sorted(current_players.items())
            if previous_players.get(player_number) != player
        )
        removed_player_numbers = tuple(
            player_number
            for player_number in sorted(previous_players)
            if player_number not in current_players
        )

        previous_entities = {entity.entity_id: entity for entity in previous.entities}
        current_entities = {entity.entity_id: entity for entity in current.entities}
        changed_entities = tuple(
            entity
            for entity_id, entity in sorted(current_entities.items())
            if previous_entities.get(entity_id) != entity
        )
        removed_entity_ids = tuple(
            entity_id
            for entity_id in sorted(previous_entities)
            if entity_id not in current_entities
        )

        return (
            replace(
                current,
                players=changed_players,
                entities=changed_entities,
            ),
            removed_entity_ids,
            removed_player_numbers,
        )

    def _spec_int(self, spec: dict[str, object], key: str) -> int:
        return int(cast(int | float | str, spec.get(key, 0)))

    def _spec_float(self, spec: dict[str, object], key: str) -> float:
        return float(cast(int | float | str, spec.get(key, 0.0)))

    def _spec_str(self, spec: dict[str, object], key: str) -> str:
        return str(cast(str, spec.get(key, "")))
