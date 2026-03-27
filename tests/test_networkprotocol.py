import json
import unittest

from src.commandintents import PlayerIntentFrame
from src.networkprotocol import ClientServerEnvelopeBuilder
from src.networkstate import MatchSnapshot


class PlayerStub:
    def __init__(self, frames):
        self._frames = list(frames)

    def drain_intent_frames(self):
        frames = tuple(self._frames)
        self._frames.clear()
        return frames


class GameStub:
    def __init__(self):
        self._players = [
            PlayerStub(
                [
                    PlayerIntentFrame.from_iterable([True], source="human:0", simulation_time=1.0),
                    PlayerIntentFrame.from_iterable([False, True], source="human:0", simulation_time=2.0),
                ]
            ),
            PlayerStub([PlayerIntentFrame.empty(source="ai", simulation_time=3.0)]),
        ]
        self._num_of_players = 2
        self._session_id = "session-123"
        self._simulation_tick = 88

    def get_num_of_players(self):
        return self._num_of_players

    def get_players(self):
        return self._players

    def get_session_id(self):
        return self._session_id

    def get_simulation_tick(self):
        return self._simulation_tick


class NetworkProtocolTests(unittest.TestCase):
    def test_build_command_envelopes_drains_frames_and_increments_sequences(self):
        builder = ClientServerEnvelopeBuilder()
        game = GameStub()

        envelopes = builder.build_command_envelopes(game)
        encoded = builder.serialize_command_envelope(envelopes[0])

        self.assertEqual([env.client_sequence for env in envelopes], [1, 2, 1])
        self.assertEqual(envelopes[0].commands["fire"], True)
        self.assertEqual(envelopes[1].commands["weaponup"], True)
        self.assertEqual(envelopes[2].player_number, 1)
        self.assertEqual(json.loads(encoded)["session_id"], "session-123")
        self.assertEqual(game.get_players()[0].drain_intent_frames(), ())

    def test_build_snapshot_envelope_acknowledges_last_commands(self):
        builder = ClientServerEnvelopeBuilder()
        game = GameStub()
        builder.build_command_envelopes(game)
        snapshot = MatchSnapshot(
            authority="server",
            game_state=7,
            current_round=2,
            num_rounds=10,
            entities=(),
            players=(),
            events=(),
        )

        envelope = builder.build_snapshot_envelope(game, snapshot)
        encoded = builder.serialize_snapshot_envelope(envelope)

        self.assertEqual(envelope.snapshot_sequence, 1)
        self.assertEqual(envelope.acknowledged_command_sequences, {0: 2, 1: 1})
        self.assertEqual(json.loads(encoded)["simulation_tick"], 88)


if __name__ == "__main__":
    unittest.main()
