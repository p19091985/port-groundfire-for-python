import unittest
from unittest.mock import patch

import groundfire.client as root_client
import groundfire.master as root_master
import groundfire.server as root_server
import src.groundfire.client as package_client
import src.groundfire.master as package_master
import src.groundfire.server as package_server
import src.main as legacy_main


class GroundfireEntrypointTests(unittest.TestCase):
    def test_root_and_package_entrypoints_expose_main_and_parser(self):
        parser = root_client.build_parser()
        client_args = parser.parse_args(["--connect", "127.0.0.1:27015", "--once"])
        server_args = root_server.build_parser().parse_args(["--ticks", "5", "--rounds", "20"])
        master_args = root_master.build_parser().parse_args(["--ticks", "3"])

        self.assertEqual(client_args.connect, "127.0.0.1:27015")
        self.assertTrue(client_args.once)
        self.assertFalse(client_args.computer_player)
        self.assertFalse(client_args.headless_client)
        self.assertFalse(client_args.log_network_events)
        self.assertFalse(hasattr(client_args, "canonical_local"))
        self.assertFalse(hasattr(client_args, "classic_local"))
        self.assertEqual(server_args.ticks, 5)
        self.assertEqual(server_args.rounds, 20)
        self.assertFalse(server_args.log_events)
        self.assertEqual(master_args.ticks, 3)
        self.assertIs(legacy_main.main, package_client.main)
        self.assertTrue(callable(package_server.main))
        self.assertTrue(callable(package_master.main))
        self.assertTrue(hasattr(client_args, "server_public_key"))
        self.assertEqual(client_args.server_public_key.endswith("server_root_public.pem"), True)
        self.assertEqual(server_args.server_private_key.endswith("server_root_private.pem"), True)
        self.assertEqual(server_args.server_public_key.endswith("server_root_public.pem"), True)
        self.assertTrue(hasattr(client_args, "password"))
        self.assertTrue(hasattr(server_args, "password"))
        self.assertTrue(hasattr(server_args, "master_server"))

    def test_client_main_uses_classic_local_flow_by_default(self):
        calls = []

        class ClientStub:
            def run_legacy_local(self, *, max_frames=None):
                calls.append(("legacy", max_frames))
                return 11

            def run_local(self, **_kwargs):
                raise AssertionError("Local entrypoint should use the classic flow.")

            def connect(self, host, port, *, player_name="Player", password=""):
                calls.append(("connect", host, port, player_name, password))
                return None

            def run_connected(self, *, max_frames=None):
                calls.append(("connected", max_frames))
                return 33

            def close(self):
                calls.append(("close",))

        with patch.object(package_client, "ClientApp", return_value=ClientStub()):
            result = package_client.main(["--once"])

        self.assertEqual(result, 11)
        self.assertEqual(calls[0], ("legacy", 1))

    def test_client_main_connect_uses_native_backend_configuration(self):
        created = []
        calls = []

        class ClientStub:
            def connect(self, host, port, *, player_name="Player", password=""):
                calls.append(("connect", host, port, player_name, password))
                return None

            def run_connected(self, *, max_frames=None):
                calls.append(("connected", max_frames))
                return 33

            def close(self):
                calls.append(("close",))

        def make_client(**kwargs):
            created.append(kwargs)
            return ClientStub()

        with patch.object(package_client, "ClientApp", side_effect=make_client):
            result = package_client.main(
                ["--connect", "127.0.0.1:27015", "--server-public-key", "keys/server.pem", "--once"]
            )

        self.assertEqual(result, 33)
        self.assertEqual(created[0]["network_backend"], "udp")
        self.assertEqual(created[0]["secure_server_public_key_path"], "keys/server.pem")
        self.assertEqual(calls[0], ("connect", "127.0.0.1", 27015, "Player", ""))

    def test_client_main_connect_can_join_as_computer_player(self):
        calls = []

        class ClientStub:
            def connect(self, host, port, *, player_name="Player", password="", is_computer=False):
                calls.append(("connect", host, port, player_name, password, is_computer))
                return None

            def run_connected(self, *, max_frames=None):
                calls.append(("connected", max_frames))
                return 34

            def close(self):
                calls.append(("close",))

        with patch.object(package_client, "ClientApp", return_value=ClientStub()):
            result = package_client.main(
                [
                    "--connect",
                    "127.0.0.1:27015",
                    "--player-name",
                    "CPU LAN 1",
                    "--computer-player",
                    "--once",
                ]
            )

        self.assertEqual(result, 34)
        self.assertEqual(calls[0], ("connect", "127.0.0.1", 27015, "CPU LAN 1", "", True))

    def test_client_main_connect_can_run_headless_with_event_logging(self):
        created = []
        calls = []

        class ClientStub:
            def connect(self, host, port, *, player_name="Player", password="", is_computer=False):
                calls.append(("connect", host, port, player_name, password, is_computer))
                return None

            def run_headless_connected(self, *, join_timeout=5.0, keepalive_seconds=0.0):
                calls.append(("headless", join_timeout, keepalive_seconds))
                return 35

            def close(self):
                calls.append(("close",))

        def make_client(**kwargs):
            created.append(kwargs)
            return ClientStub()

        with patch.object(package_client, "ClientApp", side_effect=make_client):
            result = package_client.main(
                [
                    "--connect",
                    "127.0.0.1:27015",
                    "--computer-player",
                    "--headless-client",
                    "--join-timeout",
                    "3.5",
                    "--keepalive-seconds",
                    "1.25",
                    "--log-network-events",
                ]
            )

        self.assertEqual(result, 35)
        self.assertTrue(callable(created[0]["event_logger"]))
        self.assertEqual(calls[0], ("connect", "127.0.0.1", 27015, "Player", "", True))
        self.assertEqual(calls[1], ("headless", 3.5, 1.25))

    def test_client_main_headless_once_ignores_keepalive(self):
        calls = []

        class ClientStub:
            def connect(self, host, port, *, player_name="Player", password="", is_computer=False):
                calls.append(("connect", host, port, player_name, password, is_computer))
                return None

            def run_headless_connected(self, *, join_timeout=5.0, keepalive_seconds=0.0):
                calls.append(("headless", join_timeout, keepalive_seconds))
                return 36

            def close(self):
                calls.append(("close",))

        with patch.object(package_client, "ClientApp", return_value=ClientStub()):
            result = package_client.main(
                [
                    "--connect",
                    "127.0.0.1:27015",
                    "--headless-client",
                    "--join-timeout",
                    "2.0",
                    "--keepalive-seconds",
                    "99",
                    "--once",
                ]
            )

        self.assertEqual(result, 36)
        self.assertEqual(calls[1], ("headless", 2.0, 0.0))

    def test_server_main_uses_native_backend_configuration(self):
        created = []
        calls = []

        class ServerStub:
            def run(self, *, max_ticks=None):
                calls.append(("run", max_ticks))
                return 44

            def close(self):
                calls.append(("close",))

        def make_server(**kwargs):
            created.append(kwargs)
            return ServerStub()

        with patch.object(package_server, "ServerApp", side_effect=make_server):
            result = package_server.main(
                [
                    "--ticks",
                    "5",
                    "--rounds",
                    "20",
                    "--password",
                    "secret",
                    "--map",
                    "ridge",
                    "--max-players",
                    "12",
                    "--rcon-password",
                    "admin",
                    "--region",
                    "sa",
                    "--no-discovery",
                    "--master-server",
                    "127.0.0.1:27017",
                    "--server-private-key",
                    "keys/private.pem",
                    "--server-public-key",
                    "keys/public.pem",
                    "--log-events",
                ]
            )

        self.assertEqual(result, 44)
        self.assertEqual(created[0]["network_backend"], "udp")
        self.assertEqual(created[0]["secure_private_key_path"], "keys/private.pem")
        self.assertEqual(created[0]["secure_public_key_path"], "keys/public.pem")
        self.assertEqual(created[0]["password"], "secret")
        self.assertEqual(created[0]["map_seed"], 11)
        self.assertEqual(created[0]["max_players"], 12)
        self.assertEqual(created[0]["rcon_password"], "admin")
        self.assertEqual(created[0]["num_rounds"], 20)
        self.assertEqual(created[0]["region"], "sa")
        self.assertEqual(created[0]["master_servers"], ("127.0.0.1:27017",))
        self.assertFalse(created[0]["enable_discovery"])
        self.assertTrue(callable(created[0]["event_logger"]))
        self.assertEqual(calls[0], ("run", 5))

    def test_master_main_uses_native_master_server(self):
        created = []
        calls = []

        class MasterStub:
            def open(self):
                calls.append(("open",))

            def poll(self, *, timeout=0.0):
                calls.append(("poll", timeout))

            def close(self):
                calls.append(("close",))

        def make_master(**kwargs):
            created.append(kwargs)
            return MasterStub()

        with patch.object(package_master, "MasterServerApp", side_effect=make_master):
            result = package_master.main(["--host", "127.0.0.1", "--port", "27018", "--ticks", "2"])

        self.assertEqual(result, 0)
        self.assertEqual(created[0], {"host": "127.0.0.1", "port": 27018})
        self.assertEqual(calls, [("open",), ("poll", 0.05), ("poll", 0.05), ("close",)])


if __name__ == "__main__":
    unittest.main()
