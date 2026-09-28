import time
import unittest

from src.groundfire.app.client import ClientApp
from src.groundfire.app.server import ServerApp


class OnlineMatchSimulationTests(unittest.TestCase):
    """Exercise the public UDP path as a small, deterministic live match."""

    def test_full_match_with_spectator_chat_drop_resume_and_rematch(self):
        server = ServerApp(
            host="127.0.0.1",
            port=0,
            discovery_port=0,
            enable_discovery=False,
            num_rounds=2,
            max_players=2,
            server_name="CS-style simulation",
        )
        alice = ClientApp()
        bob = ClientApp()
        spectator = ClientApp()
        rejected = ClientApp()
        clients = [alice, bob, spectator, rejected]
        phases: set[str] = set()
        try:
            server.open()
            port = server.get_bound_port()
            alice.connect("127.0.0.1", port, player_name="Alice")
            bob.connect("127.0.0.1", port, player_name="Bob")
            spectator.connect("127.0.0.1", port, player_name="Caster", spectator=True)
            rejected.connect("127.0.0.1", port, player_name="No Slot")

            self._wait_for(
                server,
                clients,
                lambda: (
                    alice.get_client_state().session_id is not None
                    and bob.get_client_state().session_id is not None
                    and spectator.get_client_state().session_id is not None
                    and rejected.get_client_state().join_reject_reason is not None
                ),
                phases,
            )
            self.assertEqual(len(server.get_match_controller().match_state.player_slots), 2)
            self.assertEqual(server.get_spectator_count(), 1)
            self.assertEqual(spectator.get_client_state().role, "spectator")
            self.assertEqual(spectator.get_client_state().player_number, -1)
            self.assertEqual(rejected.get_client_state().join_reject_reason, "server_full_or_slot_unavailable")
            with self.assertRaisesRegex(RuntimeError, "Spectators"):
                spectator.build_and_send_command_envelope({"fire": True})
            with self.assertRaisesRegex(RuntimeError, "Spectators"):
                spectator.set_lobby_ready(True)

            spectator.send_chat("  live   from spectator  ")
            self._wait_for(
                server,
                [alice, bob, spectator],
                lambda: spectator.get_last_command_result() is not None,
                phases,
            )
            self.assertTrue(spectator.get_last_command_result().accepted)

            alice.set_lobby_ready(True)
            bob.set_lobby_ready(True)
            self._wait_for(
                server,
                [alice, bob, spectator],
                lambda: (
                    spectator.get_client_state().latest_snapshot is not None
                    and spectator.get_client_state().latest_snapshot.game_phase == "round_in_action"
                ),
                phases,
            )
            self.assertIn("round_starting", phases)
            self.assertIn("round_in_action", phases)

            # A dropped player becomes disconnected after five simulated seconds,
            # while the other player and spectator keep receiving the match.
            bob.interrupt_network()
            for tick in range(330):
                if tick % 90 == 0:
                    alice.build_and_send_command_envelope({"tankright": tick % 180 == 0})
                self._pump(server, [alice, spectator], phases)
            bob_state = server.get_match_controller().match_state.get_player(1)
            self.assertIsNotNone(bob_state)
            self.assertFalse(bob_state.connected)

            bob.resume("127.0.0.1", port, player_name="Bob")
            self._wait_for(
                server,
                [alice, bob, spectator],
                lambda: bool(server.get_match_controller().match_state.get_player(1).connected),
                phases,
            )
            self._wait_for(
                server,
                [alice, bob, spectator],
                lambda: bob.get_client_state().latest_snapshot_kind == "full",
                phases,
            )

            # Let the authoritative 25-second round clock run to completion while
            # both players send keepalives through the real command channel.
            for tick in range(6000):
                if tick % 90 == 0:
                    alice.build_and_send_command_envelope({"gunup": tick % 180 == 0})
                    bob.build_and_send_command_envelope({"gundown": tick % 180 != 0})
                self._pump(server, [alice, bob, spectator], phases)
                if server.get_match_controller().match_state.game_phase == "winner":
                    break
            self.assertEqual(server.get_match_controller().match_state.game_phase, "winner")
            self._wait_for(
                server,
                [alice, bob, spectator],
                lambda: (
                    spectator.get_client_state().latest_snapshot is not None
                    and spectator.get_client_state().latest_snapshot.game_phase == "winner"
                ),
                phases,
            )
            self.assertIn("round_finishing", phases)
            self.assertIn("score", phases)
            self.assertEqual(spectator.get_client_state().latest_snapshot.game_phase, "winner")

            alice.request_rematch(True)
            bob.request_rematch(True)
            self._wait_for(
                server,
                [alice, bob, spectator],
                lambda: server.get_match_controller().match_state.game_phase != "winner",
                phases,
            )
            self.assertEqual(server.get_match_controller().match_state.current_round, 1)

            spectator.close()
            self._wait_for(server, [alice, bob], lambda: server.get_spectator_count() == 0, phases)
        finally:
            for client in clients:
                client.close()
            server.close()

    def _wait_for(self, server, clients, predicate, phases, timeout=3.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self._pump(server, clients, phases)
            if predicate():
                return
            time.sleep(0.001)
        self.fail("Timed out waiting for simulated online match condition.")

    def _pump(self, server, clients, phases):
        server.poll_network(timeout=0.0)
        server.step()
        for client in clients:
            client.poll_network(timeout=0.0)
            snapshot = client.get_client_state().latest_snapshot
            if snapshot is not None:
                phases.add(snapshot.game_phase)


if __name__ == "__main__":
    unittest.main()
