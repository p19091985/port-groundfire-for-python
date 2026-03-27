from dataclasses import replace
import types
import unittest

from tests.support import install_fake_pygame

install_fake_pygame()

import pygame

from interface_net.server import DedicatedServerUI


def _center(rect):
    return (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)


class DedicatedServerUITests(unittest.TestCase):
    def test_server_only_starts_after_clicking_start_in_panel(self):
        ui = DedicatedServerUI(1100, 760)
        self.addCleanup(ui.shutdown)
        layout = ui.get_layout_snapshot()

        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["fields"]["server_name"]), button=1))
        ui.handle_event(types.SimpleNamespace(type=768, key=8, unicode=""))
        ui.handle_event(types.SimpleNamespace(type=768, key=8, unicode=""))
        ui.handle_event(types.SimpleNamespace(type=768, key=8, unicode=""))
        ui.handle_event(types.SimpleNamespace(type=768, key=71, unicode="X"))

        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["fields"]["udp_port"]), button=1))
        for _ in range(5):
            ui.handle_event(types.SimpleNamespace(type=768, key=8, unicode=""))
        for char in "0":
            ui.handle_event(types.SimpleNamespace(type=768, key=49, unicode=char))

        panel_action = ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["buttons"]["Open Panel"]), button=1))

        self.assertEqual(panel_action.kind, "open_panel")
        self.assertEqual(ui.get_mode(), "panel")
        self.assertFalse(ui.is_server_running())
        self.assertEqual(ui.get_settings().udp_port, "0")
        self.assertTrue(ui.get_settings().server_name.endswith("X"))

        layout = ui.get_layout_snapshot()
        start_action = ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["control_buttons"]["Start"]), button=1))

        self.assertEqual(start_action.kind, "start_server")
        self.assertTrue(ui.is_server_running())
        self.assertEqual(ui.get_mode(), "panel")

    def test_dropdowns_and_checkbox_change_launch_settings(self):
        ui = DedicatedServerUI(1100, 760)
        self.addCleanup(ui.shutdown)
        layout = ui.get_layout_snapshot()
        original = ui.get_settings()

        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["fields"]["game"]), button=1))
        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["fields"]["map_name"]), button=1))
        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["fields"]["network"]), button=1))
        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["fields"]["max_players"]), button=1))
        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["fields"]["rounds"]), button=1))
        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["checkbox"]), button=1))

        updated = ui.get_settings()
        self.assertNotEqual(updated.game, original.game)
        self.assertNotEqual(updated.map_name, original.map_name)
        self.assertEqual(updated.network, "Lan")
        self.assertNotEqual(updated.max_players, original.max_players)
        self.assertNotEqual(updated.rounds, original.rounds)
        self.assertNotEqual(updated.secure, original.secure)

    def test_panel_tabs_can_be_changed_and_edit_returns_to_creator(self):
        ui = DedicatedServerUI(1100, 760)
        self.addCleanup(ui.shutdown)
        ui._settings = replace(ui.get_settings(), udp_port="0")
        ui.open_control_panel()
        layout = ui.get_layout_snapshot()
        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["control_buttons"]["Start"]), button=1))
        layout = ui.get_layout_snapshot()

        tab_action = ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["tabs"]["Configure"]), button=1))
        self.assertEqual(tab_action.kind, "panel_tab_changed")
        self.assertEqual(ui.get_active_panel_tab(), "Configure")

        layout = ui.get_layout_snapshot()
        edit_action = ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["edit_button"]), button=1))
        self.assertEqual(edit_action.kind, "edit_server")
        self.assertEqual(ui.get_mode(), "create")

    def test_draw_works_in_both_modes(self):
        ui = DedicatedServerUI(1100, 760)
        self.addCleanup(ui.shutdown)
        ui._settings = replace(ui.get_settings(), udp_port="0")
        surface = pygame.Surface((1100, 760))
        ui.draw(surface)
        ui.open_control_panel()
        ui.draw(surface)
        layout = ui.get_layout_snapshot()
        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["control_buttons"]["Start"]), button=1))
        ui.draw(surface)

    def test_panel_layout_stays_inside_smaller_windows(self):
        ui = DedicatedServerUI(700, 520)
        self.addCleanup(ui.shutdown)
        ui._settings = replace(ui.get_settings(), udp_port="0")
        ui.open_control_panel()
        window = ui.get_layout_snapshot()["window"]
        self.assertGreaterEqual(window[0], 0)
        self.assertGreaterEqual(window[1], 0)

    def test_restart_and_stop_buttons_control_server_lifecycle(self):
        ui = DedicatedServerUI(1100, 760)
        self.addCleanup(ui.shutdown)
        ui._settings = replace(ui.get_settings(), udp_port="0")
        ui.open_control_panel()
        layout = ui.get_layout_snapshot()

        ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["control_buttons"]["Start"]), button=1))
        self.assertTrue(ui.is_server_running())

        layout = ui.get_layout_snapshot()
        restart_action = ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["control_buttons"]["Restart"]), button=1))
        self.assertEqual(restart_action.kind, "restart_server")
        self.assertTrue(ui.is_server_running())

        layout = ui.get_layout_snapshot()
        stop_action = ui.handle_event(types.SimpleNamespace(type=1025, pos=_center(layout["control_buttons"]["Stop"]), button=1))
        self.assertEqual(stop_action.kind, "stop_server")
        self.assertFalse(ui.is_server_running())


if __name__ == "__main__":
    unittest.main()
