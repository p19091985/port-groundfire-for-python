import json
import unittest

from src.commandintents import PlayerIntentFrame
from src.networkstate import EntitySnapshot, MatchNetworkStateBuilder, NetworkEvent


class EntityStub:
    def __init__(self, entity_id, entity_type="entity", position=(1.0, 2.0)):
        self._entity_id = entity_id
        self._entity_type = entity_type
        self._position = position

    def get_entity_id(self):
        return self._entity_id

    def get_entity_type(self):
        return self._entity_type

    def get_position(self):
        return self._position


class CustomSnapshotEntity(EntityStub):
    def build_network_snapshot(self):
        return EntitySnapshot(
            entity_id=self._entity_id,
            entity_type="custom",
            position=self._position,
            payload={"custom": True},
        )


class TankStub:
    def __init__(self, entity_id):
        self._entity_id = entity_id

    def get_entity_id(self):
        return self._entity_id


class PlayerStub:
    def __init__(self, number, *, computer=False):
        self._number = number
        self._tank = TankStub(number + 100)
        self._computer = computer
        self._intents = PlayerIntentFrame.from_iterable([number == 0], source="test", simulation_time=3.0)

    def get_name(self):
        return f"P{self._number}"

    def get_score(self):
        return 100 + self._number

    def get_money(self):
        return 50 + self._number

    def is_computer(self):
        return self._computer

    def get_tank(self):
        return self._tank

    def get_current_intents(self):
        return self._intents


class GameStub:
    def __init__(self):
        self._entity_list = [EntityStub(1, "shell"), CustomSnapshotEntity(2, position=(4.0, 5.0))]
        self._players = [PlayerStub(0), PlayerStub(1, computer=True)] + [None] * 6
        self._game_state = 7
        self._current_round = 2
        self._num_of_rounds = 10
        self._events = [NetworkEvent(event_type="round_started", payload={"round": 2})]

    def get_num_of_players(self):
        return 2

    def get_players(self):
        return self._players

    def get_game_state(self):
        return self._game_state

    def get_current_round(self):
        return self._current_round

    def get_num_of_rounds(self):
        return self._num_of_rounds

    def get_pending_network_events(self):
        return tuple(self._events)


class NetworkStateTests(unittest.TestCase):
    def test_builder_uses_entity_and_player_snapshots(self):
        builder = MatchNetworkStateBuilder()
        game = GameStub()

        snapshot = builder.build_snapshot(game)

        self.assertEqual(snapshot.authority, "server")
        self.assertEqual(snapshot.current_round, 2)
        self.assertEqual([entity.entity_type for entity in snapshot.entities], ["shell", "custom"])
        self.assertEqual(snapshot.entities[1].payload, {"custom": True})
        self.assertEqual(snapshot.players[0].tank_entity_id, 100)
        self.assertEqual(snapshot.players[0].intents["fire"], True)
        self.assertEqual(snapshot.players[1].is_computer, True)
        self.assertEqual(snapshot.events[0].event_type, "round_started")

    def test_builder_serializes_snapshot_to_json(self):
        builder = MatchNetworkStateBuilder()
        snapshot = builder.build_snapshot(GameStub())

        encoded = builder.serialize_snapshot(snapshot)
        decoded = json.loads(encoded)

        self.assertEqual(decoded["authority"], "server")
        self.assertEqual(decoded["entities"][0]["entity_id"], 1)
        self.assertEqual(decoded["players"][0]["name"], "P0")


if __name__ == "__main__":
    unittest.main()
