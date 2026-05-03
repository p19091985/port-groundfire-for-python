import socket
import threading
import time
import unittest
from tempfile import TemporaryDirectory

from groundfire_net.browser import ServerBook, ServerListEntry
from groundfire_net.transport import DatagramEndpoint
from src.groundfire.app.client import ClientApp
from src.groundfire.app.server import ServerApp
from src.groundfire.gameplay.match_controller import MatchController
from src.groundfire.network.browser import GroundfireServerScanner
from src.groundfire.network.lan import LanDiscoveryService


class ServerBrowserRealNetworkPathTests(unittest.TestCase):
    def test_lan_tab_receives_real_udp_announcement(self):
        discovery_port = self._free_udp_port()
        scanner = GroundfireServerScanner(discovery_port=discovery_port, master_servers=())
        sender = DatagramEndpoint(host="127.0.0.1", port=0)
        try:
            scanner.open()
            controller = MatchController(seed=7, max_players=8)
            service = LanDiscoveryService()
            announcement = service.build_announcement(
                controller.match_state,
                server_name="LAN Reference Server",
                map_seed=7,
                max_players=8,
                requires_password=False,
                server_port=27015,
                region="local",
            )

            sender.sendto(service.encode_announcement(announcement), ("127.0.0.1", discovery_port))
            deadline = time.monotonic() + 1.0
            entries = ()
            while time.monotonic() < deadline:
                entries = scanner.entries_for_tab("lan")
                if entries:
                    break
                time.sleep(0.01)

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].name, "LAN Reference Server")
            self.assertEqual(entries[0].region, "local")
        finally:
            sender.close()
            scanner.close()

    def test_lan_discovered_entry_connects_real_client(self):
        with TemporaryDirectory() as temp_dir:
            discovery_port = self._free_udp_port()
            scanner = GroundfireServerScanner(discovery_port=discovery_port, master_servers=())
            sender = DatagramEndpoint(host="127.0.0.1", port=0)
            server = ServerApp(
                host="127.0.0.1",
                port=0,
                discovery_port=0,
                enable_discovery=False,
                server_name="LAN Connect Groundfire",
                region="local",
            )
            server.open()
            stop = threading.Event()
            thread = self._run_server(server, stop)
            client = ClientApp(server_book_path=f"{temp_dir}/servers.json")
            try:
                scanner.open()
                service = LanDiscoveryService()
                announcement = service.build_announcement(
                    server.get_match_controller().match_state,
                    server_name="LAN Connect Groundfire",
                    map_seed=1,
                    max_players=8,
                    requires_password=False,
                    server_port=server.get_bound_port(),
                    region="local",
                )
                sender.sendto(service.encode_announcement(announcement), ("127.0.0.1", discovery_port))

                deadline = time.monotonic() + 1.0
                entries = ()
                while time.monotonic() < deadline:
                    entries = scanner.entries_for_tab("lan")
                    if entries:
                        break
                    time.sleep(0.01)

                self.assertEqual(len(entries), 1)
                client.connect(entries[0].host, entries[0].port, player_name="LAN Player", history_entry=entries[0])
                self._wait_for(lambda: client.get_client_state().player_number == 0, client)
                self.assertEqual(client.get_client_state().server_name, "LAN Connect Groundfire")
            finally:
                client.close()
                sender.close()
                scanner.close()
                stop.set()
                thread.join(timeout=1.0)
                server.close()

    def test_server_full_rejects_second_real_client(self):
        server = ServerApp(
            host="127.0.0.1",
            port=0,
            discovery_port=0,
            enable_discovery=False,
            max_players=1,
        )
        server.open()
        stop = threading.Event()
        thread = self._run_server(server, stop)
        alice = ClientApp()
        bob = ClientApp()
        try:
            port = server.get_bound_port()
            alice.connect("127.0.0.1", port, player_name="Alice")
            self._wait_for(lambda: alice.get_client_state().player_number == 0, alice)

            bob.connect("127.0.0.1", port, player_name="Bob")
            self._wait_for(
                lambda: bob.get_client_state().join_reject_reason == "server_full_or_slot_unavailable",
                bob,
            )
        finally:
            alice.close()
            bob.close()
            stop.set()
            thread.join(timeout=1.0)
            server.close()

    def test_favorites_and_history_entries_connect_real_clients(self):
        with TemporaryDirectory() as temp_dir:
            book_path = f"{temp_dir}/servers.json"
            server = ServerApp(
                host="127.0.0.1",
                port=0,
                discovery_port=0,
                enable_discovery=False,
                server_name="Favorite History Groundfire",
            )
            server.open()
            stop = threading.Event()
            thread = self._run_server(server, stop)
            scanner = GroundfireServerScanner(
                discovery_port=0,
                master_servers=(),
                server_book=ServerBook(book_path),
            )
            favorite_client = ClientApp(server_book_path=book_path)
            history_client = ClientApp(server_book_path=book_path)
            try:
                favorite = ServerListEntry(
                    name="Favorite History Groundfire",
                    host="127.0.0.1",
                    port=server.get_bound_port(),
                    source="internet",
                )
                scanner.add_favorite(favorite)
                favorite_entry = scanner.entries_for_tab("favorites")[0]

                self.assertEqual(ServerBook(book_path).get_history(), ())
                favorite_client.connect(
                    favorite_entry.host,
                    favorite_entry.port,
                    player_name="Favorite Player",
                    history_entry=favorite_entry,
                )
                self.assertEqual(ServerBook(book_path).get_history(), ())
                self._wait_for(lambda: favorite_client.get_client_state().player_number == 0, favorite_client)

                history = ServerBook(book_path).get_history()
                self.assertEqual(len(history), 1)
                self.assertEqual(history[0].endpoint, favorite_entry.endpoint)

                history_scanner = GroundfireServerScanner(
                    discovery_port=0,
                    master_servers=(),
                    server_book=ServerBook(book_path),
                )
                try:
                    self.assertEqual(history_scanner.entries_for_tab("history")[0].endpoint, favorite_entry.endpoint)

                    history_entry = history_scanner.entries_for_tab("history")[0]
                    history_client.connect(
                        history_entry.host,
                        history_entry.port,
                        player_name="History Player",
                        history_entry=history_entry,
                    )
                    self._wait_for(lambda: history_client.get_client_state().player_number == 1, history_client)
                finally:
                    history_scanner.close()
            finally:
                favorite_client.close()
                history_client.close()
                scanner.close()
                stop.set()
                thread.join(timeout=1.0)
                server.close()

    def test_rejected_password_connect_does_not_record_history(self):
        with TemporaryDirectory() as temp_dir:
            book_path = f"{temp_dir}/servers.json"
            server = ServerApp(
                host="127.0.0.1",
                port=0,
                discovery_port=0,
                enable_discovery=False,
                password="secret",
            )
            server.open()
            stop = threading.Event()
            thread = self._run_server(server, stop)
            client = ClientApp(server_book_path=book_path)
            try:
                entry = ServerListEntry(
                    name="Rejected Password Server",
                    host="127.0.0.1",
                    port=server.get_bound_port(),
                    requires_password=True,
                )
                client.connect(
                    entry.host,
                    entry.port,
                    player_name="Wrong Password",
                    password="bad",
                    history_entry=entry,
                )
                self._wait_for(lambda: client.get_client_state().join_reject_reason == "bad_password", client)

                self.assertEqual(ServerBook(book_path).get_history(), ())
            finally:
                client.close()
                stop.set()
                thread.join(timeout=1.0)
                server.close()

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

    def _free_udp_port(self) -> int:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])
        finally:
            sock.close()


if __name__ == "__main__":
    unittest.main()
