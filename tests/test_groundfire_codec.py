import unittest

from src.groundfire.network.codec import decode_json, decode_message, encode_json, encode_message
from src.groundfire.network.messages import ClientCommandEnvelope, JoinRequest, ServerSnapshotEnvelope
from src.groundfire.sim.match import MatchSnapshot, ReplicatedPlayerState
from src.groundfire.sim.world import ReplicatedEntityState, TerrainPatch


class GroundfireCodecTests(unittest.TestCase):
    def test_join_request_round_trips_password(self):
        request = JoinRequest(player_name="Alice", requested_slot=2, password="secret")

        self.assertEqual(decode_message(encode_message(request)), request)
        self.assertEqual(decode_json(encode_json(request)), request)

    def test_client_command_round_trips_through_native_json_bytes_and_text(self):
        envelope = ClientCommandEnvelope(
            session_id="session-1",
            player_number=2,
            client_sequence=7,
            acknowledged_snapshot_sequence=3,
            simulation_tick=42,
            issued_at=12.5,
            source="client:test",
            commands={"fire": True, "tankleft": True},
            session_token="token-abc",
        )

        self.assertEqual(decode_message(encode_message(envelope)), envelope)
        self.assertEqual(decode_json(encode_json(envelope)), envelope)

    def test_server_snapshot_round_trips_nested_state(self):
        snapshot = MatchSnapshot(
            authority="server",
            game_phase="round_in_action",
            current_round=2,
            num_rounds=10,
            simulation_tick=99,
            phase_ticks_remaining=45,
            round_winner_player_number=None,
            winner_player_number=None,
            players=(
                ReplicatedPlayerState(
                    player_number=0,
                    name="Alice",
                    score=120,
                    money=80,
                    connected=True,
                    tank_entity_id=1,
                    acknowledged_command_sequence=4,
                    acknowledged_snapshot_sequence=2,
                    is_leader=True,
                    selected_weapon="missile",
                    weapon_stocks=(("missile", 2), ("machinegun", 1)),
                    round_defeated_player_numbers=(1, 3),
                ),
            ),
            entities=(
                ReplicatedEntityState(
                    entity_id=1,
                    entity_type="tank",
                    position=(1.5, 2.0),
                    velocity=(0.0, 0.0),
                    angle=45.0,
                    owner_player=0,
                    payload={"health": 100},
                ),
            ),
        )
        envelope = ServerSnapshotEnvelope(
            session_id="session-1",
            snapshot_sequence=5,
            simulation_tick=99,
            acknowledged_command_sequences={0: 4},
            snapshot=snapshot,
            removed_entity_ids=(9,),
            removed_player_numbers=(3,),
            terrain_patches=(TerrainPatch(patch_id=3, chunk_index=7, operation="explosion", payload={"radius": 0.4}),),
            events=({"event_type": "weapon_fired", "payload": {"player_number": 0}},),
            snapshot_kind="delta",
            baseline_snapshot_sequence=3,
        )

        decoded = decode_message(encode_message(envelope))

        self.assertEqual(decoded.session_id, "session-1")
        self.assertEqual(decoded.snapshot_sequence, 5)
        self.assertEqual(decoded.snapshot.players[0].name, "Alice")
        self.assertEqual(decoded.snapshot.players[0].selected_weapon, "missile")
        self.assertEqual(decoded.snapshot.players[0].weapon_stocks[0], ("missile", 2))
        self.assertTrue(decoded.snapshot.players[0].is_leader)
        self.assertEqual(decoded.snapshot.players[0].round_defeated_player_numbers, (1, 3))
        self.assertEqual(decoded.snapshot.phase_ticks_remaining, 45)
        self.assertEqual(decoded.snapshot.entities[0].payload["health"], 100)
        self.assertEqual(decoded.removed_entity_ids, (9,))
        self.assertEqual(decoded.removed_player_numbers, (3,))
        self.assertEqual(decoded.terrain_patches[0].chunk_index, 7)
        self.assertEqual(decoded.events[0]["event_type"], "weapon_fired")
        self.assertEqual(decoded.snapshot_kind, "delta")
        self.assertEqual(decoded.baseline_snapshot_sequence, 3)


if __name__ == "__main__":
    unittest.main()
