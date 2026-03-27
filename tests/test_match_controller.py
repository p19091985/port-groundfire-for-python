import unittest

from src.groundfire.gameplay.match_controller import MatchController
from src.groundfire.network.messages import ClientCommandEnvelope


class MatchControllerTests(unittest.TestCase):
    def test_controller_is_deterministic_for_same_seed_and_commands(self):
        first = self._run_match(seed=7, session_id="shared-session")
        second = self._run_match(seed=7, session_id="shared-session")

        self.assertEqual(first.snapshot, second.snapshot)
        self.assertEqual(first.terrain_patches, second.terrain_patches)
        self.assertEqual(first.events, second.events)

    def test_fire_command_produces_snapshot_events_and_terrain_patch(self):
        controller = MatchController(session_id="session-1", seed=3)
        player, token = controller.join_player("Alice")
        self._advance_to_round_in_action(controller)
        controller.apply_command_envelope(
            ClientCommandEnvelope(
                session_id="session-1",
                player_number=player.player_number,
                client_sequence=1,
                acknowledged_snapshot_sequence=None,
                simulation_tick=0,
                issued_at=0.0,
                source="test",
                commands={"fire": True, "tankright": True},
                session_token=token.token,
            )
        )

        for _ in range(18):
            controller.step()

        envelope = controller.build_snapshot_envelope()
        tank = next(entity for entity in envelope.snapshot.entities if entity.entity_type == "tank")

        self.assertGreater(tank.position[0], -4.5)
        self.assertEqual(envelope.snapshot.seed, 3)
        self.assertGreater(len(envelope.snapshot.terrain_profile), 1)
        self.assertEqual(envelope.snapshot.players[0].colour, controller.PLAYER_COLOURS[0])
        self.assertTrue(any(event["event_type"] == "weapon_fired" for event in envelope.events))
        self.assertTrue(any(event["event_type"] == "terrain_patched" for event in envelope.events))
        self.assertEqual(envelope.terrain_patches[0].operation, "explosion")
        self.assertTrue(envelope.terrain_patches[0].payload["changed_vertices"])

    def test_destroyed_tank_finishes_round_and_advances_match_state(self):
        controller = MatchController(session_id="session-1", seed=3, num_rounds=2)
        alice, _alice_token = controller.join_player("Alice")
        bob, _bob_token = controller.join_player("Bob")
        self._advance_to_round_in_action(controller)

        bob_tank = controller.world_state.entity_registry.get(bob.tank_entity_id)
        controller.world_state.entity_registry.create(
            "shell",
            position=(bob_tank.position[0], bob_tank.position[1] + 0.1),
            velocity=(0.0, -0.5),
            owner_player=alice.player_number,
            payload={"ttl_ticks": 1, "blast_radius": 0.7, "blast_damage": 250.0, "gravity": 0.0, "size": 0.06},
        )

        controller.step()

        self.assertEqual(controller.match_state.game_phase, "round_finishing")
        self.assertEqual(controller.match_state.round_winner_player_number, alice.player_number)
        self.assertTrue(any(event["event_type"] == "tank_destroyed" for event in controller.match_state.drain_events()))

        for _ in range(controller.ROUND_FINISHING_TICKS):
            controller.step()

        self.assertEqual(controller.match_state.current_round, 1)
        self.assertEqual(controller.match_state.game_phase, "score")

        for _ in range(controller.SCORE_PHASE_TICKS):
            controller.step()

        self.assertEqual(controller.match_state.game_phase, "shop")

        for _ in range(controller.SHOP_PHASE_TICKS):
            controller.step()

        self.assertEqual(controller.match_state.current_round, 2)
        self.assertEqual(controller.match_state.game_phase, "round_starting")
        second_round_tank_ids = tuple(player.tank_entity_id for player in controller.match_state.player_slots.values())
        self.assertEqual(len(second_round_tank_ids), 2)
        self.assertEqual(controller.world_state.seed, 4)
        self.assertEqual(controller.match_state.phase_ticks_remaining, controller.ROUND_STARTING_TICKS)

    def test_last_round_emits_match_winner_in_snapshot(self):
        controller = MatchController(session_id="session-1", seed=4, num_rounds=1)
        alice, _alice_token = controller.join_player("Alice")
        bob, _bob_token = controller.join_player("Bob")
        self._advance_to_round_in_action(controller)

        bob_tank = controller.world_state.entity_registry.get(bob.tank_entity_id)
        controller.world_state.entity_registry.create(
            "shell",
            position=(bob_tank.position[0], bob_tank.position[1] + 0.1),
            velocity=(0.0, -0.5),
            owner_player=alice.player_number,
            payload={"ttl_ticks": 1, "blast_radius": 0.7, "blast_damage": 250.0, "gravity": 0.0, "size": 0.06},
        )

        controller.step()
        for _ in range(controller.ROUND_FINISHING_TICKS):
            controller.step()

        envelope = controller.build_snapshot_envelope()

        self.assertEqual(envelope.snapshot.game_phase, "winner")
        self.assertEqual(envelope.snapshot.winner_player_number, alice.player_number)
        self.assertEqual(envelope.snapshot.players[0].score, 100)
        self.assertEqual(envelope.snapshot.players[0].money, 85)

    def test_score_snapshot_tracks_round_defeats_and_previous_round_leader(self):
        controller = MatchController(session_id="session-1", seed=5, num_rounds=2)
        alice, _alice_token = controller.join_player("Alice")
        bob, _bob_token = controller.join_player("Bob")
        controller.match_state.update_player(bob.player_number, is_leader=True)
        self._advance_to_round_in_action(controller)

        bob_tank = controller.world_state.entity_registry.get(bob.tank_entity_id)
        controller.world_state.entity_registry.create(
            "shell",
            position=(bob_tank.position[0], bob_tank.position[1] + 0.1),
            velocity=(0.0, -0.5),
            owner_player=alice.player_number,
            payload={"ttl_ticks": 1, "blast_radius": 0.7, "blast_damage": 250.0, "gravity": 0.0, "size": 0.06},
        )

        controller.step()
        for _ in range(controller.ROUND_FINISHING_TICKS):
            controller.step()

        envelope = controller.build_snapshot_envelope()
        alice_snapshot = next(player for player in envelope.snapshot.players if player.player_number == alice.player_number)
        bob_snapshot = next(player for player in envelope.snapshot.players if player.player_number == bob.player_number)

        self.assertEqual(envelope.snapshot.game_phase, "score")
        self.assertEqual(alice_snapshot.round_defeated_player_numbers, (bob.player_number,))
        self.assertTrue(bob_snapshot.is_leader)

        for _ in range(controller.SCORE_PHASE_TICKS):
            controller.step()

        alice_updated = controller.match_state.get_player(alice.player_number)
        bob_updated = controller.match_state.get_player(bob.player_number)
        self.assertTrue(alice_updated.is_leader)
        self.assertFalse(bob_updated.is_leader)

    def test_shop_phase_allows_purchasing_selected_weapon(self):
        controller = MatchController(session_id="session-1", seed=8)
        alice, token = controller.join_player("Alice")
        controller.match_state.game_phase = "shop"
        controller.match_state.phase_ticks_remaining = controller.SHOP_PHASE_TICKS
        controller.match_state.update_player(alice.player_number, money=60, selected_weapon="missile")

        applied = controller.apply_command_envelope(
            ClientCommandEnvelope(
                session_id="session-1",
                player_number=alice.player_number,
                client_sequence=1,
                acknowledged_snapshot_sequence=None,
                simulation_tick=controller.match_state.simulation_tick,
                issued_at=0.0,
                source="test",
                commands={"fire": True},
                session_token=token.token,
            )
        )

        self.assertTrue(applied)
        updated = controller.match_state.get_player(alice.player_number)
        self.assertEqual(updated.money, 35)
        self.assertIn(("missile", 1), updated.weapon_stocks)

    def test_special_weapon_fire_spawns_cluster_projectiles(self):
        controller = MatchController(session_id="session-1", seed=9)
        alice, token = controller.join_player("Alice")
        controller.match_state.update_player(alice.player_number, selected_weapon="mirv", weapon_stocks=(("mirv", 1),))
        self._advance_to_round_in_action(controller)

        controller.apply_command_envelope(
            ClientCommandEnvelope(
                session_id="session-1",
                player_number=alice.player_number,
                client_sequence=1,
                acknowledged_snapshot_sequence=None,
                simulation_tick=controller.match_state.simulation_tick,
                issued_at=0.0,
                source="test",
                commands={"fire": True},
                session_token=token.token,
            )
        )

        entity_types = [entity.entity_type for entity in controller.world_state.entity_registry.snapshot()]
        self.assertEqual(entity_types.count("mirv"), 3)
        updated = controller.match_state.get_player(alice.player_number)
        self.assertEqual(updated.selected_weapon, "shell")

    def test_computer_player_generates_canonical_intents(self):
        controller = MatchController(session_id="session-1", seed=10)
        controller.join_player("Alice")
        ai_player, _token = controller.join_player("CPU", is_computer=True)
        self._advance_to_round_in_action(controller)

        for _ in range(10):
            controller.step()

        updated_ai = controller.match_state.get_player(ai_player.player_number)
        self.assertGreater(updated_ai.acknowledged_command_sequence, 0)

    def test_snapshot_sequence_emits_full_then_delta_with_baseline(self):
        controller = MatchController(session_id="session-1", seed=11)
        player, token = controller.join_player("Alice")
        self._advance_to_round_in_action(controller)

        while not controller.should_emit_snapshot():
            controller.step()
        first = controller.build_snapshot_envelope()

        controller.apply_command_envelope(
            ClientCommandEnvelope(
                session_id="session-1",
                player_number=player.player_number,
                client_sequence=1,
                acknowledged_snapshot_sequence=first.snapshot_sequence,
                simulation_tick=controller.match_state.simulation_tick,
                issued_at=1.0,
                source="test",
                commands={"fire": True},
                session_token=token.token,
            )
        )
        for _ in range(18):
            controller.step()
        while not controller.should_emit_snapshot():
            controller.step()
        second = controller.build_snapshot_envelope()

        self.assertEqual(first.snapshot_kind, "full")
        self.assertTrue(first.snapshot.terrain_profile)
        self.assertEqual(second.snapshot_kind, "delta")
        self.assertEqual(second.baseline_snapshot_sequence, first.snapshot_sequence)
        self.assertEqual(second.snapshot.terrain_profile, ())

    def test_delta_snapshot_only_sends_changed_entities_and_removed_ids(self):
        controller = MatchController(session_id="session-1", seed=12)
        player, token = controller.join_player("Alice")
        self._advance_to_round_in_action(controller)

        while not controller.should_emit_snapshot():
            controller.step()
        first = controller.build_snapshot_envelope()
        self.assertEqual(first.snapshot_kind, "full")
        self.assertTrue(first.snapshot.entities)

        controller.apply_command_envelope(
            ClientCommandEnvelope(
                session_id="session-1",
                player_number=player.player_number,
                client_sequence=1,
                acknowledged_snapshot_sequence=first.snapshot_sequence,
                simulation_tick=controller.match_state.simulation_tick,
                issued_at=1.0,
                source="test",
                commands={"fire": True},
                session_token=token.token,
            )
        )
        for _ in range(18):
            controller.step()
        while not controller.should_emit_snapshot():
            controller.step()
        second = controller.build_snapshot_envelope()

        self.assertEqual(second.snapshot_kind, "delta")
        self.assertEqual(second.baseline_snapshot_sequence, first.snapshot_sequence)
        self.assertTrue(second.snapshot.entities)
        self.assertTrue(second.removed_entity_ids or second.terrain_patches or second.events)

    def _run_match(self, *, seed: int, session_id: str):
        controller = MatchController(session_id=session_id, seed=seed)
        player, token = controller.join_player("Alice")
        self._advance_to_round_in_action(controller)
        commands = (
            {"tankright": True},
            {"gunup": True},
            {"fire": True},
            {"tankleft": True},
            {"gunright": True},
            {},
        )

        for sequence, command in enumerate(commands, start=1):
            controller.apply_command_envelope(
                ClientCommandEnvelope(
                    session_id=session_id,
                    player_number=player.player_number,
                    client_sequence=sequence,
                    acknowledged_snapshot_sequence=None,
                    simulation_tick=controller.match_state.simulation_tick,
                    issued_at=float(sequence),
                    source="test",
                    commands=command,
                    session_token=token.token,
                )
            )
            controller.step()

        while not controller.should_emit_snapshot():
            controller.step()

        return controller.build_snapshot_envelope()

    def _advance_to_round_in_action(self, controller: MatchController):
        while controller.match_state.game_phase != "round_in_action":
            controller.step()


if __name__ == "__main__":
    unittest.main()
