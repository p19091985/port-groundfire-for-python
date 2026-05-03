import threading
import time
import unittest

from groundfire_net.master import MasterServerApp, MasterServerClient, MasterServerDirectory, MasterServerAddress
from src.groundfire.app.client import ClientApp
from src.groundfire.app.server import ServerApp
from src.groundfire.network.browser import GroundfireServerScanner


class MasterServerIntegrationTests(unittest.TestCase):
    def test_server_registers_with_master_browser_finds_it_and_client_connects_with_password(self):
        master = MasterServerApp(host="127.0.0.1", port=0)
        master.open()
        master_stop = threading.Event()
        master_thread = self._run_master(master, master_stop)
        server = ServerApp(
            host="127.0.0.1",
            port=0,
            discovery_port=0,
            enable_discovery=False,
            server_name="Protected Public Groundfire",
            password="secret",
            region="sa",
            master_servers=(("127.0.0.1", master.get_bound_port()),),
            master_interval_seconds=0.05,
        )
        server.open()
        server_stop = threading.Event()
        server_thread = self._run_server(server, server_stop)
        scanner = GroundfireServerScanner(
            discovery_port=0,
            master_servers=(("127.0.0.1", master.get_bound_port()),),
        )
        bad_client = ClientApp()
        good_client = ClientApp()
        try:
            entries = ()
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                entries = scanner.refresh_tab("internet", timeout=0.05)
                if entries:
                    break

            self.assertEqual(len(entries), 1)
            entry = entries[0]
            self.assertEqual(entry.name, "Protected Public Groundfire")
            self.assertEqual(entry.region, "sa")
            self.assertTrue(entry.requires_password)
            self.assertTrue(entry.secure)
            self.assertIsNotNone(entry.latency_ms)

            bad_client.connect(entry.host, entry.port, player_name="Mallory", password="wrong")
            self._wait_for(lambda: bad_client.get_client_state().join_reject_reason == "bad_password", bad_client)

            good_client.connect(entry.host, entry.port, player_name="Alice", password="secret")
            self._wait_for(
                lambda: (
                    good_client.get_client_state().player_number == 0
                    and good_client.get_client_state().latest_snapshot is not None
                ),
                good_client,
            )

            self.assertEqual(good_client.get_client_state().server_name, "Protected Public Groundfire")
            self.assertEqual(good_client.get_client_state().latest_snapshot.players[0].name, "Alice")
        finally:
            bad_client.close()
            good_client.close()
            scanner.close()
            server_stop.set()
            server_thread.join(timeout=1.0)
            server.close()
            master_stop.set()
            master_thread.join(timeout=1.0)
            master.close()

    def test_direct_clients_can_connect_to_passworded_server_by_host_port_and_requested_slot(self):
        server = ServerApp(
            host="127.0.0.1",
            port=0,
            discovery_port=0,
            enable_discovery=False,
            password="slotpass",
        )
        server.open()
        server_stop = threading.Event()
        server_thread = self._run_server(server, server_stop)
        client = ClientApp()
        try:
            client.connect(
                "127.0.0.1",
                server.get_bound_port(),
                player_name="Slot Player",
                requested_slot=3,
                password="slotpass",
            )
            self._wait_for(
                lambda: client.get_client_state().player_number == 3
                and client.get_client_state().latest_snapshot is not None,
                client,
            )

            self.assertEqual(client.get_client_state().latest_snapshot.players[0].name, "Slot Player")
        finally:
            client.close()
            server_stop.set()
            server_thread.join(timeout=1.0)
            server.close()

    def test_master_directory_expires_stale_servers_without_mocks(self):
        now = [100.0]
        directory = MasterServerDirectory(ttl_seconds=1.0, now=lambda: now[0])
        master = MasterServerApp(host="127.0.0.1", port=0, directory=directory)
        master.open()
        stop = threading.Event()
        thread = self._run_master(master, stop)
        client = MasterServerClient()
        try:
            address = MasterServerAddress("127.0.0.1", master.get_bound_port())
            server = ServerApp(host="127.0.0.1", port=0, discovery_port=0, enable_discovery=False)
            server.open()
            registered = client.register(address, server._build_master_entry(), timeout=0.2)
            self.assertIsNotNone(registered)
            self.assertEqual(len(client.query(address, timeout=0.2)), 1)

            now[0] += 2.0
            self.assertEqual(client.query(address, timeout=0.2), ())
        finally:
            client.close()
            server.close()
            stop.set()
            thread.join(timeout=1.0)
            master.close()

    def _run_master(self, master: MasterServerApp, stop: threading.Event):
        def loop():
            while not stop.is_set():
                master.poll(timeout=0.005)

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        return thread

    def _run_server(self, server: ServerApp, stop: threading.Event):
        def loop():
            while not stop.is_set():
                server.poll_network(timeout=0.002)
                server.step()
                time.sleep(0.001)

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        return thread

    def _wait_for(self, predicate, *clients: ClientApp):
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            for client in clients:
                client.poll_network(timeout=0.01)
            if predicate():
                return
        self.fail("Timed out waiting for network condition.")


if __name__ == "__main__":
    unittest.main()
