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
        client_args = parser.parse_args(
            ["--connect", "127.0.0.1:27015", "--once", "--ai-players", "2"]
        )
        server_args = root_server.build_parser().parse_args(["--ticks", "5"])
        master_args = root_master.build_parser().parse_args(["--ticks", "3"])

        self.assertEqual(client_args.connect, "127.0.0.1:27015")
        self.assertTrue(client_args.once)
        self.assertEqual(client_args.ai_players, 2)
        self.assertFalse(client_args.canonical_local)
        self.assertFalse(client_args.classic_local)
        self.assertEqual(server_args.ticks, 5)
        self.assertEqual(master_args.ticks, 3)
        self.assertIs(legacy_main.main, package_client.main)
        self.assertTrue(callable(package_server.main))
        self.assertTrue(callable(package_master.main))
        canonical_help = next(action.help for action in parser._actions if action.dest == "canonical_local")
        self.assertNotIn("in-progress", canonical_help)
        self.assertIn("classic local menu flow", canonical_help)
        self.assertTrue(hasattr(client_args, "server_public_key"))
        self.assertEqual(client_args.server_public_key.endswith("server_root_public.pem"), True)
        self.assertEqual(server_args.server_private_key.endswith("server_root_private.pem"), True)
        self.assertEqual(server_args.server_public_key.endswith("server_root_public.pem"), True)
        self.assertTrue(hasattr(client_args, "password"))
        self.assertTrue(hasattr(server_args, "password"))
        self.assertTrue(hasattr(server_args, "master_server"))

    def test_client_main_uses_canonical_menu_by_default(self):
        calls = []

        class SettingsStub:
            def get_string(self, _section, _entry, default):
                return default

        class ClientStub:
            def run_legacy_local(self, *, max_frames=None):
                calls.append(("legacy", max_frames))
                return 11

            def run_local(self, *, max_frames=None, player_name="Player", ai_players=1, show_menu=False):
                calls.append(("canonical", max_frames, player_name, ai_players, show_menu))
                return 22

            def connect(self, host, port, *, player_name="Player", password=""):
                calls.append(("connect", host, port, player_name, password))
                return None

            def run_connected(self, *, max_frames=None):
                calls.append(("connected", max_frames))
                return 33

            def close(self):
                calls.append(("close",))

        with (
            patch.object(package_client, "ClientApp", return_value=ClientStub()),
            patch.object(package_client, "ReadIniFile", return_value=SettingsStub()),
        ):
            result = package_client.main(["--once"])

        self.assertEqual(result, 22)
        self.assertEqual(calls[0], ("canonical", 1, "Player", 1, False))

    def test_client_main_can_force_classic_local(self):
        calls = []

        class ClientStub:
            def run_legacy_local(self, *, max_frames=None):
                calls.append(("legacy", max_frames))
                return 11

            def run_local(self, *, max_frames=None, player_name="Player", ai_players=1, show_menu=False):
                calls.append(("canonical", max_frames, player_name, ai_players, show_menu))
                return 22

            def connect(self, host, port, *, player_name="Player", password=""):
                calls.append(("connect", host, port, player_name, password))
                return None

            def run_connected(self, *, max_frames=None):
                calls.append(("connected", max_frames))
                return 33

            def close(self):
                calls.append(("close",))

        with patch.object(package_client, "ClientApp", return_value=ClientStub()):
            result = package_client.main(["--classic-local", "--once"])

        self.assertEqual(result, 11)
        self.assertEqual(calls[0], ("legacy", 1))

    def test_client_main_can_force_canonical_local(self):
        calls = []

        class ClientStub:
            def run_legacy_local(self, *, max_frames=None):
                calls.append(("legacy", max_frames))
                return 11

            def run_local(self, *, max_frames=None, player_name="Player", ai_players=1, show_menu=False):
                calls.append(("canonical", max_frames, player_name, ai_players, show_menu))
                return 22

            def connect(self, host, port, *, player_name="Player", password=""):
                calls.append(("connect", host, port, player_name, password))
                return None

            def run_connected(self, *, max_frames=None):
                calls.append(("connected", max_frames))
                return 33

            def close(self):
                calls.append(("close",))

        with patch.object(package_client, "ClientApp", return_value=ClientStub()):
            result = package_client.main(["--canonical-local", "--once"])

        self.assertEqual(result, 22)
        self.assertEqual(calls[0], ("canonical", 1, "Player", 1, False))

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
                    "--password",
                    "secret",
                    "--region",
                    "sa",
                    "--master-server",
                    "127.0.0.1:27017",
                    "--server-private-key",
                    "keys/private.pem",
                    "--server-public-key",
                    "keys/public.pem",
                ]
            )

        self.assertEqual(result, 44)
        self.assertEqual(created[0]["network_backend"], "udp")
        self.assertEqual(created[0]["secure_private_key_path"], "keys/private.pem")
        self.assertEqual(created[0]["secure_public_key_path"], "keys/public.pem")
        self.assertEqual(created[0]["password"], "secret")
        self.assertEqual(created[0]["region"], "sa")
        self.assertEqual(created[0]["master_servers"], ("127.0.0.1:27017",))
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
