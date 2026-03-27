import socket
import tempfile
import time
import unittest

from tests.support import install_fake_pygame

install_fake_pygame()

from interface_net.lan_client import LanClient
from interface_net.server.lan_server import DedicatedLanServer


def _reserve_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class LanConnectionTests(unittest.TestCase):
    def test_client_discovers_server_and_match_starts_with_two_players(self):
        discovery_port = _reserve_udp_port()
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = f"{temp_dir}/dedicated_server.log"
            server = DedicatedLanServer(
                host="127.0.0.1",
                port=0,
                server_name="Groundfire LAN Test",
                map_name="Depot",
                max_players=8,
                secure=True,
                discovery_port=discovery_port,
                countdown_seconds=0.15,
                log_path=log_path,
            )

            try:
                server.start()

                browser_client = LanClient()
                discovered = []
                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline and not discovered:
                    discovered = browser_client.discover_lan(
                        timeout=0.1,
                        discovery_port=discovery_port,
                        targets=("127.0.0.1",),
                    )

                self.assertEqual(len(discovered), 1)
                self.assertEqual(discovered[0].snapshot.server_name, "Groundfire LAN Test")
                self.assertEqual(discovered[0].snapshot.map_name, "Depot")
                self.assertEqual(discovered[0].snapshot.network, "Lan")
                self.assertEqual(discovered[0].snapshot.current_players, 0)

                host = discovered[0].snapshot.host
                port = discovered[0].snapshot.port

                client_one = LanClient()
                result_one = client_one.connect(host=host, port=port, client_name="Patrik LAN Client")

                self.assertEqual(result_one.status, "ok")
                self.assertEqual(result_one.server_name, "Groundfire LAN Test")
                self.assertEqual(result_one.map_name, "Depot")
                self.assertEqual(result_one.network, "Lan")
                self.assertEqual(result_one.max_players, 8)
                self.assertEqual(result_one.current_players, 1)
                self.assertTrue(result_one.secure)
                self.assertEqual(result_one.client_name, "Patrik LAN Client")
                self.assertEqual(result_one.lobby_state, "waiting")
                self.assertFalse(result_one.match_started)
                self.assertEqual(result_one.rounds, 10)

                client_two = LanClient()
                result_two = client_two.connect(host=host, port=port, client_name="Second Player")

                self.assertEqual(result_two.status, "ok")
                self.assertEqual(result_two.current_players, 2)
                self.assertIn(result_two.lobby_state, ("countdown", "started"))
                self.assertIn("Patrik LAN Client", result_two.players)
                self.assertIn("Second Player", result_two.players)

                started_status = result_two
                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline and not started_status.match_started:
                    time.sleep(0.03)
                    started_status = client_two.get_lobby_status(
                        host=host,
                        port=port,
                        player_id=result_two.player_id,
                        timeout=0.3,
                    )

                self.assertTrue(started_status.match_started)
                self.assertEqual(started_status.lobby_state, "started")
                self.assertGreaterEqual(started_status.current_players, 2)
                self.assertTrue(bool(started_status.match_id))
                self.assertGreaterEqual(started_status.landscape_seed, 1)
                self.assertGreaterEqual(started_status.tank_seed, 1)
                self.assertIn("Patrik LAN Client", server.get_connected_clients())
                self.assertIn("Second Player", server.get_connected_clients())
                self.assertTrue(server.get_server_info().match_started)

                sync_one = client_one.sync_frame(
                    host=host,
                    port=port,
                    player_id=result_one.player_id,
                    frame_index=0,
                    commands=[True] + [False] * 10,
                    current_round=1,
                )
                sync_two = client_two.sync_frame(
                    host=host,
                    port=port,
                    player_id=result_two.player_id,
                    frame_index=0,
                    commands=[False, True] + [False] * 9,
                    current_round=1,
                )

                self.assertEqual(sync_one.status, "ok")
                self.assertEqual(sync_two.status, "ok")
                self.assertIn(result_one.slot_index, sync_two.commands_by_slot)
                self.assertTrue(sync_two.commands_by_slot[result_one.slot_index][0])
            finally:
                server.stop()

            with open(log_path, "r", encoding="utf-8") as handle:
                log_contents = handle.read()

            self.assertIn("Starting server 'Groundfire LAN Test'", log_contents)
            self.assertIn("Player 'Patrik LAN Client' joined", log_contents)
            self.assertIn("Player 'Second Player' joined", log_contents)
            self.assertIn("Match countdown started", log_contents)
            self.assertIn("Match ", log_contents)
            self.assertIn("Dedicated server stopped.", log_contents)


if __name__ == "__main__":
    unittest.main()
