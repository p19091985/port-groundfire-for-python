from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, cast

from ..gameplay.constants import (
    TANK_FUEL_STEP,
    TANK_GUN_STEP,
    TANK_MAX_FUEL,
    TANK_MOVE_STEP,
    WEAPON_ORDER,
    WEAPON_SPECS,
)
from ..sim.match import MatchSnapshot, ReplicatedPlayerState
from ..sim.world import ReplicatedEntityState
from .messages import (
    ClientCommandEnvelope,
    DisconnectNotice,
    HelloAccept,
    JoinAccept,
    JoinReject,
    ServerEventEnvelope,
    ServerSnapshotEnvelope,
)


@dataclass
class ClientReplicatedState:
    session_id: str | None = None
    player_number: int | None = None
    session_token: str | None = None
    server_name: str | None = None
    join_reject_reason: str | None = None
    disconnect_reason: str | None = None
    latest_snapshot_sequence: int = 0
    latest_snapshot: MatchSnapshot | None = None
    authoritative_snapshot: MatchSnapshot | None = None
    predicted_snapshot: MatchSnapshot | None = None
    latest_events: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    latest_terrain_patches: tuple = field(default_factory=tuple)
    latest_snapshot_kind: str = "full"
    latest_baseline_snapshot_sequence: int | None = None
    acknowledged_command_sequences: dict[int, int] = field(default_factory=dict)
    _pending_commands: list[ClientCommandEnvelope] = field(default_factory=list)
    _next_client_sequence: int = 1

    def apply_hello_accept(self, accept: HelloAccept):
        self.server_name = accept.server_name

    def apply_join_accept(self, accept: JoinAccept):
        self.session_id = accept.session_id
        self.player_number = accept.player_number
        self.session_token = accept.session_token
        self.join_reject_reason = None
        self.disconnect_reason = None
        self._pending_commands.clear()
        self.latest_snapshot_sequence = 0
        self.latest_snapshot = None
        self.authoritative_snapshot = None
        self.predicted_snapshot = None

    def apply_join_reject(self, reject: JoinReject):
        self.join_reject_reason = reject.reason

    def apply_disconnect(self, notice: DisconnectNotice):
        self.disconnect_reason = notice.reason or "disconnected"
        self.session_id = None
        self.player_number = None
        self.session_token = None
        self._pending_commands.clear()
        self.latest_snapshot_sequence = 0
        self.latest_snapshot = None
        self.authoritative_snapshot = None
        self.predicted_snapshot = None

    def apply_snapshot(self, envelope: ServerSnapshotEnvelope) -> bool:
        if envelope.snapshot_sequence <= self.latest_snapshot_sequence:
            return False

        if envelope.snapshot_kind == "delta":
            if self.latest_snapshot is None:
                return False
            if envelope.baseline_snapshot_sequence != self.latest_snapshot_sequence:
                return False
            merged_snapshot = self._merge_delta_snapshot(self.latest_snapshot, envelope)
        else:
            merged_snapshot = envelope.snapshot

        self.latest_snapshot_sequence = envelope.snapshot_sequence
        self.latest_snapshot = merged_snapshot
        self.authoritative_snapshot = merged_snapshot
        self.latest_events = envelope.events
        self.latest_terrain_patches = envelope.terrain_patches
        self.latest_snapshot_kind = envelope.snapshot_kind
        self.latest_baseline_snapshot_sequence = envelope.baseline_snapshot_sequence
        self.acknowledged_command_sequences = dict(envelope.acknowledged_command_sequences)
        self.join_reject_reason = None
        self.disconnect_reason = None
        self._reconcile_pending_commands()
        self.predicted_snapshot = self._build_predicted_snapshot()
        return True

    def apply_events(self, envelope: ServerEventEnvelope):
        self.latest_events = envelope.events

    def get_pending_commands(self) -> tuple[ClientCommandEnvelope, ...]:
        return tuple(self._pending_commands)

    def get_render_snapshot(self) -> MatchSnapshot | None:
        return self.predicted_snapshot or self.latest_snapshot

    def build_command_envelope(
        self,
        commands: dict[str, bool],
        *,
        issued_at: float,
        source: str,
        simulation_tick: int,
    ) -> ClientCommandEnvelope:
        if self.session_id is None or self.player_number is None:
            raise RuntimeError("Client session is not established.")

        envelope = ClientCommandEnvelope(
            session_id=self.session_id,
            player_number=self.player_number,
            client_sequence=self._next_client_sequence,
            acknowledged_snapshot_sequence=self.latest_snapshot_sequence or None,
            simulation_tick=simulation_tick,
            issued_at=issued_at,
            source=source,
            commands=dict(commands),
            session_token=self.session_token,
        )
        self._next_client_sequence += 1
        self._pending_commands.append(envelope)
        self.predicted_snapshot = self._build_predicted_snapshot()
        return envelope

    def _reconcile_pending_commands(self):
        if self.player_number is None:
            return

        acknowledged_sequence = self.acknowledged_command_sequences.get(self.player_number, 0)
        if acknowledged_sequence <= 0:
            return

        self._pending_commands = [
            envelope
            for envelope in self._pending_commands
            if envelope.client_sequence > acknowledged_sequence
        ]

    def _merge_delta_snapshot(self, base_snapshot: MatchSnapshot, envelope: ServerSnapshotEnvelope) -> MatchSnapshot:
        player_map = {player.player_number: player for player in base_snapshot.players}
        entity_map = {entity.entity_id: entity for entity in base_snapshot.entities}

        for player_number in envelope.removed_player_numbers:
            player_map.pop(player_number, None)
        for entity_id in envelope.removed_entity_ids:
            entity_map.pop(entity_id, None)

        for player in envelope.snapshot.players:
            player_map[player.player_number] = player
        for entity in envelope.snapshot.entities:
            entity_map[entity.entity_id] = entity

        terrain_profile = envelope.snapshot.terrain_profile or base_snapshot.terrain_profile
        return replace(
            base_snapshot,
            authority=envelope.snapshot.authority,
            game_phase=envelope.snapshot.game_phase,
            current_round=envelope.snapshot.current_round,
            num_rounds=envelope.snapshot.num_rounds,
            simulation_tick=envelope.snapshot.simulation_tick,
            phase_ticks_remaining=envelope.snapshot.phase_ticks_remaining,
            round_winner_player_number=envelope.snapshot.round_winner_player_number,
            winner_player_number=envelope.snapshot.winner_player_number,
            seed=envelope.snapshot.seed,
            world_width=envelope.snapshot.world_width,
            terrain_revision=envelope.snapshot.terrain_revision,
            terrain_profile=terrain_profile,
            players=tuple(player_map[player_number] for player_number in sorted(player_map)),
            entities=tuple(entity_map[entity_id] for entity_id in sorted(entity_map)),
        )

    def _build_predicted_snapshot(self) -> MatchSnapshot | None:
        snapshot = self.authoritative_snapshot or self.latest_snapshot
        if snapshot is None or self.player_number is None:
            return None

        predicted = snapshot
        for envelope in self._pending_commands:
            if envelope.player_number != self.player_number:
                continue
            predicted = self._predict_command(predicted, envelope.commands)
        return predicted

    def _predict_command(self, snapshot: MatchSnapshot, commands: dict[str, bool]) -> MatchSnapshot:
        player_map = {player.player_number: player for player in snapshot.players}
        entity_map = {entity.entity_id: entity for entity in snapshot.entities}
        player_number = self.player_number
        if player_number is None:
            return snapshot

        player = player_map.get(player_number)
        if player is None or player.tank_entity_id is None:
            return snapshot

        tank = entity_map.get(player.tank_entity_id)
        if tank is None or tank.entity_type != "tank":
            return snapshot

        selected_weapon = self._predict_selected_weapon(player, commands)
        player = replace(player, selected_weapon=selected_weapon)

        if snapshot.game_phase == "shop":
            player = self._predict_shop_purchase(player, commands)
            tank = replace(
                tank,
                payload={**tank.payload, "selected_weapon": player.selected_weapon, "last_commands": dict(commands)},
            )
        elif snapshot.game_phase == "round_in_action":
            tank, player = self._predict_round_action(snapshot, tank, player, commands)
        else:
            tank = replace(
                tank,
                payload={
                    **tank.payload,
                    "selected_weapon": player.selected_weapon,
                    "last_commands": dict(commands),
                },
            )

        player_map[player.player_number] = player
        entity_map[tank.entity_id] = tank
        return replace(
            snapshot,
            players=tuple(player_map[player_number] for player_number in sorted(player_map)),
            entities=tuple(entity_map[entity_id] for entity_id in sorted(entity_map)),
        )

    def _predict_selected_weapon(self, player: ReplicatedPlayerState, commands: dict[str, bool]) -> str:
        try:
            selected_index = WEAPON_ORDER.index(player.selected_weapon)
        except ValueError:
            selected_index = 0
        if commands.get("weaponup"):
            selected_index = (selected_index + 1) % len(WEAPON_ORDER)
        elif commands.get("weapondown"):
            selected_index = (selected_index - 1) % len(WEAPON_ORDER)
        return WEAPON_ORDER[selected_index]

    def _predict_shop_purchase(self, player: ReplicatedPlayerState, commands: dict[str, bool]) -> ReplicatedPlayerState:
        if not commands.get("fire") or player.selected_weapon == "shell":
            return player

        spec = WEAPON_SPECS[player.selected_weapon]
        cost = self._spec_int(spec, "cost")
        if player.money < cost:
            return player

        stocks = self._weapon_stock_map(player.weapon_stocks)
        stocks[player.selected_weapon] = stocks.get(player.selected_weapon, 0) + self._spec_int(spec, "bundle")
        return replace(
            player,
            money=player.money - cost,
            weapon_stocks=self._weapon_stock_tuple(stocks),
        )

    def _predict_round_action(
        self,
        snapshot: MatchSnapshot,
        tank: ReplicatedEntityState,
        player: ReplicatedPlayerState,
        commands: dict[str, bool],
    ) -> tuple[ReplicatedEntityState, ReplicatedPlayerState]:
        payload = dict(tank.payload)
        x, y = tank.position
        gun_angle = float(payload.get("gun_angle", tank.angle))
        fuel = max(0.0, float(payload.get("fuel", TANK_MAX_FUEL)))
        alive = bool(payload.get("alive", True))
        moved = False

        if alive and commands.get("tankleft") and fuel > 0.0:
            x -= TANK_MOVE_STEP
            moved = True
        if alive and commands.get("tankright") and fuel > 0.0:
            x += TANK_MOVE_STEP
            moved = True
        if commands.get("gunleft") or commands.get("gunup"):
            gun_angle = min(180.0, gun_angle + TANK_GUN_STEP)
        if commands.get("gunright") or commands.get("gundown"):
            gun_angle = max(0.0, gun_angle - TANK_GUN_STEP)

        x_limit = (snapshot.world_width / 2.0) - 0.25
        x = max(-x_limit, min(x_limit, x))
        if moved:
            fuel = max(0.0, fuel - TANK_FUEL_STEP)

        player = self._predict_weapon_fire(player, commands)
        tank = replace(
            tank,
            position=(x, y),
            angle=gun_angle,
            payload={
                **payload,
                "fuel": fuel,
                "gun_angle": gun_angle,
                "selected_weapon": player.selected_weapon,
                "last_commands": dict(commands),
            },
        )
        return tank, player

    def _predict_weapon_fire(
        self,
        player: ReplicatedPlayerState,
        commands: dict[str, bool],
    ) -> ReplicatedPlayerState:
        if not commands.get("fire"):
            return player

        selected_weapon = player.selected_weapon
        if selected_weapon == "shell":
            return player

        stocks = self._weapon_stock_map(player.weapon_stocks)
        remaining = stocks.get(selected_weapon, 0)
        if remaining <= 0:
            return replace(player, selected_weapon="shell")

        stocks[selected_weapon] = remaining - 1
        next_selected_weapon = selected_weapon if stocks[selected_weapon] > 0 else "shell"
        return replace(
            player,
            selected_weapon=next_selected_weapon,
            weapon_stocks=self._weapon_stock_tuple(stocks),
        )

    def _weapon_stock_map(self, weapon_stocks: tuple[tuple[str, int], ...]) -> dict[str, int]:
        stocks = {weapon: 0 for weapon in WEAPON_ORDER}
        stocks["shell"] = -1
        for weapon, amount in weapon_stocks:
            stocks[str(weapon)] = int(amount)
        return stocks

    def _weapon_stock_tuple(self, stocks: dict[str, int]) -> tuple[tuple[str, int], ...]:
        return tuple((weapon, int(stocks.get(weapon, 0))) for weapon in WEAPON_ORDER if weapon != "shell")

    def _spec_int(self, spec: dict[str, object], key: str) -> int:
        return int(cast(int | float | str, spec.get(key, 0)))
