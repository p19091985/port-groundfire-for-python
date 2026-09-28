import unittest

from groundfire_net.browser import ServerListEntry
from src.serverbrowsermenu import ServerBrowserMenu, _BrowserState


class ScannerStub:
    def __init__(self, refreshed):
        self.refreshed = refreshed
        self.updated = []
        self.closed = False

    def refresh_entry(self, entry, *, timeout=0.05):
        return self.refreshed

    def update_entry(self, entry):
        self.updated.append(entry)

    def close(self):
        self.closed = True


class GameStub:
    def __init__(self):
        self.requests = []

    def request_online_connect(self, **kwargs):
        self.requests.append(kwargs)


class ServerBrowserMenuTests(unittest.TestCase):
    def test_connect_validation_blocks_stale_or_stopped_server(self):
        entry = ServerListEntry(name="Stopped", host="127.0.0.1", port=27015, latency_ms=25)
        stale = entry.with_updates(latency_ms=None)
        menu = ServerBrowserMenu.__new__(ServerBrowserMenu)
        menu._state = _BrowserState(entries=(entry,))
        menu._scanner = ScannerStub(stale)

        result = menu._verified_selected_entry()

        self.assertIsNone(result)
        self.assertIn("did not respond", menu._state.status)
        self.assertIsNone(menu._state.entries[0].latency_ms)

    def test_connect_validation_updates_live_server_latency(self):
        entry = ServerListEntry(name="Live", host="127.0.0.1", port=27015, latency_ms=None)
        live = entry.with_updates(latency_ms=12)
        scanner = ScannerStub(live)
        menu = ServerBrowserMenu.__new__(ServerBrowserMenu)
        menu._state = _BrowserState(entries=(entry,))
        menu._scanner = scanner

        result = menu._verified_selected_entry()

        self.assertEqual(result, live)
        self.assertEqual(menu._state.entries[0].latency_ms, 12)
        self.assertEqual(scanner.updated, [live])

    def test_connect_opens_player_type_choice_instead_of_joining_immediately(self):
        entry = ServerListEntry(name="Live", host="127.0.0.1", port=27015, latency_ms=None)
        live = entry.with_updates(latency_ms=12)
        scanner = ScannerStub(live)
        game = GameStub()
        menu = ServerBrowserMenu.__new__(ServerBrowserMenu)
        menu._state = _BrowserState(entries=(entry,))
        menu._scanner = scanner
        menu._game = game

        menu._connect_selected()

        self.assertEqual(menu._state.dialog, "join")
        self.assertEqual(menu._state.pending_endpoint, "127.0.0.1:27015")
        self.assertEqual(game.requests, [])
        self.assertFalse(scanner.closed)

    def test_join_as_ai_marks_one_connection_as_computer_player(self):
        entry = ServerListEntry(name="Live", host="127.0.0.1", port=27015, latency_ms=12)
        scanner = ScannerStub(entry)
        game = GameStub()
        menu = ServerBrowserMenu.__new__(ServerBrowserMenu)
        menu._state = _BrowserState(entries=(entry,), password_value="secret")
        menu._scanner = scanner
        menu._game = game

        menu._state.join_as_computer = True
        menu._finish_connect_selected()

        self.assertTrue(scanner.closed)
        self.assertEqual(
            game.requests,
            [
                {
                    "host": "127.0.0.1",
                    "port": 27015,
                    "password": "secret",
                    "entry": entry,
                    "is_computer": True,
                }
            ],
        )

    def test_spectate_tab_connects_read_only_without_using_ai_mode(self):
        entry = ServerListEntry(name="Live", host="127.0.0.1", port=27015, latency_ms=12)
        scanner = ScannerStub(entry)
        game = GameStub()
        menu = ServerBrowserMenu.__new__(ServerBrowserMenu)
        menu._state = _BrowserState(entries=(entry,), tab="spectate")
        menu._scanner = scanner
        menu._game = game

        menu._connect_selected()
        self.assertTrue(menu._state.join_as_spectator)
        menu._finish_connect_selected()

        self.assertTrue(scanner.closed)
        self.assertTrue(game.requests[0]["spectator"])
        self.assertFalse(game.requests[0]["is_computer"])

    def test_join_dialog_uses_radio_selection_before_connecting(self):
        entry = ServerListEntry(name="Live", host="127.0.0.1", port=27015, latency_ms=12)
        scanner = ScannerStub(entry)
        game = GameStub()
        menu = ServerBrowserMenu.__new__(ServerBrowserMenu)
        menu._state = _BrowserState(entries=(entry,), dialog="join")
        menu._scanner = scanner
        menu._game = game
        rects = {
            "join_human_radio": (-4.7, -0.1, -1.2, -0.75),
            "join_ai_radio": (0.3, -0.1, 3.8, -0.75),
            "join_connect": (0.85, -2.25, 2.7, -2.85),
            "join_cancel": (2.85, -2.25, 4.65, -2.85),
        }

        menu._handle_join_click(rects, 1.0, -0.4)

        self.assertTrue(menu._state.join_as_computer)
        self.assertEqual(game.requests, [])

        menu._handle_join_click(rects, 1.0, -2.5)

        self.assertEqual(game.requests[0]["is_computer"], True)

    def test_join_dialog_radio_can_switch_back_to_human(self):
        entry = ServerListEntry(name="Live", host="127.0.0.1", port=27015, latency_ms=12)
        menu = ServerBrowserMenu.__new__(ServerBrowserMenu)
        menu._state = _BrowserState(entries=(entry,), dialog="join", join_as_computer=True)
        rects = {
            "join_human_radio": (-4.7, -0.1, -1.2, -0.75),
            "join_ai_radio": (0.3, -0.1, 3.8, -0.75),
            "join_connect": (0.85, -2.25, 2.7, -2.85),
            "join_cancel": (2.85, -2.25, 4.65, -2.85),
        }

        menu._handle_join_click(rects, -3.0, -0.4)

        self.assertFalse(menu._state.join_as_computer)

    def test_random_server_selects_lowest_latency_open_passwordless_server(self):
        full = ServerListEntry(
            name="Full",
            host="127.0.0.1",
            port=27015,
            player_count=8,
            max_players=8,
            latency_ms=5,
        )
        passworded = ServerListEntry(
            name="Passworded",
            host="127.0.0.1",
            port=27016,
            requires_password=True,
            latency_ms=8,
        )
        best = ServerListEntry(name="Best", host="127.0.0.1", port=27017, player_count=3, latency_ms=20)
        slower = ServerListEntry(name="Slower", host="127.0.0.1", port=27018, latency_ms=40)
        scanner = ScannerStub(best)
        menu = ServerBrowserMenu.__new__(ServerBrowserMenu)
        menu._state = _BrowserState(entries=(full, passworded, best, slower))
        menu._scanner = scanner

        menu._connect_random_server()

        self.assertEqual(menu._state.selected_index, 2)
        self.assertEqual(menu._state.pending_endpoint, best.endpoint)
        self.assertEqual(menu._state.dialog, "join")


if __name__ == "__main__":
    unittest.main()
