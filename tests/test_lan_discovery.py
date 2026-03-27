import unittest

from src.groundfire.gameplay.match_controller import MatchController
from src.groundfire.network.lan import LanDiscoveryService, LanServerBrowser
from src.groundfire.network.messages import LanServerAnnouncement


class LanDiscoveryTests(unittest.TestCase):
    def test_announcement_round_trip_and_browser_expiry(self):
        controller = MatchController(session_id="session-1", seed=11)
        controller.join_player("Alice")
        service = LanDiscoveryService()
        browser = LanServerBrowser(expiry_seconds=3.0)

        announcement = service.build_announcement(
            controller.match_state,
            server_name="Groundfire LAN",
            map_seed=11,
            max_players=8,
            requires_password=False,
            server_port=27015,
        )
        decoded = service.decode_announcement(service.encode_announcement(announcement))

        self.assertTrue(browser.record_announcement(decoded, ("192.168.0.10", 27016), now=0.0))
        self.assertEqual(len(browser.get_servers(now=1.0)), 1)
        self.assertEqual(len(browser.get_servers(now=3.5)), 0)

    def test_browser_rejects_protocol_mismatch(self):
        browser = LanServerBrowser(expected_protocol_version=1)
        incompatible = LanServerAnnouncement(
            server_name="Other",
            session_id="session-x",
            map_seed=1,
            current_round=1,
            player_count=1,
            max_players=8,
            requires_password=False,
            server_port=27015,
            protocol_version=2,
        )

        self.assertFalse(browser.record_announcement(incompatible, ("10.0.0.2", 27016), now=0.0))


if __name__ == "__main__":
    unittest.main()
