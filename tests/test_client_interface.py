import types
import unittest
from unittest.mock import patch

from tests.support import install_fake_pygame

install_fake_pygame()

from interface_net.client_interface import NetworkClientInterface
from interface_net.lan_client import LanConnectionResult, LanDiscoveredServer
from interface_net.lan_protocol import LanLobbySnapshot, LanPlayerDescriptor


def _build_discovered_server():
    snapshot = LanLobbySnapshot(
        server_name="Groundfire Dedicated",
        map_name="Canyon",
        network="Lan",
        host="127.0.0.1",
        port=27016,
        max_players=12,
        current_players=1,
        secure=True,
        players=("Host",),
        player_slots=(LanPlayerDescriptor(slot_index=0, name="Host", uses_ai=False),),
        rounds=10,
        lobby_state="waiting",
        countdown_seconds=0,
        match_started=False,
        match_id="",
        landscape_seed=0,
        tank_seed=0,
    )
    return LanDiscoveredServer(snapshot=snapshot, latency_ms=3)


def _build_connection_result():
    player_slots = (
        LanPlayerDescriptor(slot_index=0, name="Player", uses_ai=True),
        LanPlayerDescriptor(slot_index=1, name="Host", uses_ai=False),
    )
    return LanConnectionResult(
        status="ok",
        server_name="Groundfire Dedicated",
        map_name="Canyon",
        network="Lan",
        host="127.0.0.1",
        port=27016,
        max_players=12,
        current_players=2,
        secure=True,
        client_name="Player",
        player_id="player-1",
        slot_index=0,
        players=tuple(player.name for player in player_slots),
        player_slots=player_slots,
        rounds=10,
        lobby_state="waiting",
        countdown_seconds=0,
        match_started=False,
        match_id="",
        landscape_seed=0,
        tank_seed=0,
    )


class NetworkClientInterfaceTests(unittest.TestCase):
    def _build_settings(self):
        return types.SimpleNamespace(
            get_string=lambda *_args, **_kwargs: "Player",
            get_int=lambda *_args, **_kwargs: 0,
        )

    def test_toggle_button_enables_online_ai_and_updates_footer_label(self):
        discovered_server = _build_discovered_server()
        with patch("interface_net.client_interface.LanClient.discover_lan", return_value=[discovered_server]):
            ui = NetworkClientInterface(1280, 720, self._build_settings())

        self.assertFalse(ui.is_online_ai_enabled())
        self.assertEqual(ui._get_footer_button_label("Change filters"), "AI: OFF")

        action = ui.trigger_button("Change filters")

        self.assertEqual(action.kind, "toggle_online_ai")
        self.assertEqual(action.value, "on")
        self.assertTrue(ui.is_online_ai_enabled())
        self.assertEqual(ui._get_footer_button_label("Change filters"), "AI: ON")
        self.assertIn("Online AI enabled", ui._compose_status_text())

    def test_connect_uses_online_ai_flag_when_it_is_enabled(self):
        discovered_server = _build_discovered_server()
        connection_result = _build_connection_result()
        with patch("interface_net.client_interface.LanClient.discover_lan", return_value=[discovered_server]):
            ui = NetworkClientInterface(1280, 720, self._build_settings())

        ui.select_server(discovered_server.server_id)
        ui.trigger_button("Change filters")

        with patch("interface_net.client_interface.LanClient.connect", return_value=connection_result) as connect_mock:
            ui.trigger_button("Connect")

        connect_mock.assert_called_once_with(
            host="127.0.0.1",
            port=27016,
            client_name="Player",
            use_ai=True,
        )
        self.assertEqual(ui._connected_lobby.player_id, "player-1")
        self.assertTrue(ui.is_online_ai_enabled())


if __name__ == "__main__":
    unittest.main()
