import types
import unittest

from tests.support import install_fake_pygame

install_fake_pygame()

import pygame

from interface_net import ServerBrowserEntry, ServerBrowserUI


def _center(rect):
    return (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)


class ServerBrowserUITests(unittest.TestCase):
    def _build_ui(self):
        servers = [
            ServerBrowserEntry("internet-1", "Internet Alpha", "Groundfire", 3, 8, "Canyon", 40, favorite=True),
            ServerBrowserEntry("fav-1", "Favorite Bravo", "Groundfire", 4, 8, "Depot", 20, favorite=True, friends_online=1),
            ServerBrowserEntry("history-1", "History Charlie", "Groundfire", 2, 8, "Quarry", 55, has_history=True),
            ServerBrowserEntry("spectate-1", "Spectate Delta", "Groundfire", 7, 8, "Dunes", 88, spectate=True),
            ServerBrowserEntry("lan-1", "LAN Echo", "Groundfire", 1, 4, "Garage", 3, lan=True),
        ]
        return ServerBrowserUI(1280, 720, servers=servers)

    def test_tabs_filter_the_correct_server_sets(self):
        ui = self._build_ui()

        self.assertEqual([server.server_id for server in ui.get_visible_servers()], ["internet-1", "fav-1", "history-1", "spectate-1"])

        ui.activate_tab("Favorites")
        self.assertEqual([server.server_id for server in ui.get_visible_servers()], ["internet-1", "fav-1"])

        ui.activate_tab("History")
        self.assertEqual([server.server_id for server in ui.get_visible_servers()], ["history-1"])

        ui.activate_tab("Spectate")
        self.assertEqual([server.server_id for server in ui.get_visible_servers()], ["spectate-1"])

        ui.activate_tab("Lan")
        self.assertEqual([server.server_id for server in ui.get_visible_servers()], ["lan-1"])

        ui.activate_tab("Friends")
        self.assertEqual([server.server_id for server in ui.get_visible_servers()], ["fav-1"])

    def test_selection_is_cleared_when_switching_to_a_tab_without_that_server(self):
        ui = self._build_ui()
        ui.select_server("internet-1")
        self.assertEqual(ui.get_selected_server().server_id, "internet-1")

        ui.activate_tab("Lan")
        self.assertIsNone(ui.get_selected_server())

    def test_mouse_clicks_switch_tabs_select_rows_and_trigger_connect(self):
        ui = self._build_ui()
        layout = ui.get_layout_snapshot()

        action = ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["tabs"]["Favorites"]), button=1))
        self.assertEqual(action.kind, "tab_changed")
        self.assertEqual(ui.get_active_tab(), "Favorites")

        layout = ui.get_layout_snapshot()
        row_click = ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["rows"][0]["rect"]), button=1))
        self.assertEqual(row_click.kind, "server_selected")
        self.assertEqual(ui.get_selected_server().server_id, "internet-1")

        connect_action = ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["buttons"]["Connect"]), button=1))
        self.assertEqual(connect_action.kind, "connect")
        self.assertEqual(connect_action.value, "internet-1")

    def test_close_button_emits_close_action(self):
        ui = self._build_ui()
        layout = ui.get_layout_snapshot()

        action = ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["close_button"]), button=1))
        self.assertEqual(action.kind, "close")

    def test_keyboard_navigation_selects_first_visible_server_when_none_is_selected(self):
        ui = self._build_ui()

        action = ui.handle_event(types.SimpleNamespace(type=768, key=274))
        self.assertEqual(action.kind, "server_selected")
        self.assertEqual(ui.get_selected_server().server_id, "internet-1")

    def test_draw_runs_against_a_basic_surface(self):
        ui = self._build_ui()
        surface = pygame.Surface((640, 480))
        ui.draw(surface)


if __name__ == "__main__":
    unittest.main()
