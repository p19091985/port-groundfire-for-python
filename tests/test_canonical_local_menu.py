import unittest
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory

from groundfire_net.browser import ServerListEntry
from src.gameui import GameUI
from src.groundfire.core.settings import ReadIniFile
from src.groundfire.ui.menus import CanonicalLocalMenu


class FontStub:
    def __init__(self):
        self.centred_calls = []
        self.text_calls = []

    def set_shadow(self, _value):
        return None

    def set_proportional(self, _value):
        return None

    def set_orientation(self, _value):
        return None

    def set_size(self, *_args):
        return None

    def set_colour(self, _colour):
        return None

    def print_centred_at(self, *args):
        self.centred_calls.append(args)

    def print_at(self, *args):
        self.text_calls.append(args)

    def printf(self, *args):
        return None

    def find_string_length(self, text):
        return max(1.0, len(text) * 0.18)


class GraphicsStub:
    def __init__(self):
        self.rect_calls = []

    def fill_screen(self, *_args, **_kwargs):
        return None

    def draw_tiled_texture(self, *_args, **_kwargs):
        return None

    def draw_texture_world_rect(self, *_args, **_kwargs):
        return None

    def draw_world_rect(self, *args, **_kwargs):
        self.rect_calls.append(args)

    def draw_world_polygon(self, *_args, **_kwargs):
        return None


class InterfaceStub:
    def __init__(self, *, width=1024, height=768, fullscreen=False):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.change_calls = []
        self.mouse_pos = (99.0, 99.0)
        self.mouse_buttons = (False, False, False)

    def get_window_settings(self):
        return self.width, self.height, self.fullscreen

    def get_texture_surface(self, _texture_id):
        return None

    def get_mouse_pos(self):
        return self.mouse_pos

    def get_mouse_button(self, button):
        if 0 <= button < len(self.mouse_buttons):
            return self.mouse_buttons[button]
        return False

    def change_window(self, width, height, fullscreen):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.change_calls.append((width, height, fullscreen))


class MenuGameStub:
    def __init__(self, settings_path: Path):
        self.font = FontStub()
        self.ui = GameUI(font_provider=lambda: self.font)
        self.graphics = GraphicsStub()
        self.interface = InterfaceStub()
        self._settings_path = settings_path
        self._settings = ReadIniFile(str(settings_path))

    def get_ui(self):
        return self.ui

    def get_graphics(self):
        return self.graphics

    def get_interface(self):
        return self.interface

    def get_settings(self):
        return self._settings

    def get_settings_path(self):
        return self._settings_path


class ServerScannerStub:
    def __init__(self, entries=()):
        self.entries = tuple(entries)
        self.favorites = []
        self.history = []
        self.updated = []
        self.refreshed_tabs = []

    def entries_for_tab(self, tab):
        if tab == "favorites":
            return tuple(self.favorites)
        if tab == "history":
            return tuple(self.history)
        return self.entries

    def all_entries(self):
        return tuple(self.entries) + tuple(self.favorites) + tuple(self.history)

    def refresh_tab(self, tab):
        self.refreshed_tabs.append(tab)
        return tuple(entry.with_updates(latency_ms=12) for entry in self.entries_for_tab(tab))

    def refresh_entry(self, entry, *, timeout=0.05):
        return entry.with_updates(latency_ms=7)

    def update_entry(self, entry):
        self.updated.append(entry)

    def add_favorite(self, entry):
        self.favorites.insert(0, entry.with_updates(source="favorite"))

    def add_manual_server(self, target):
        host, raw_port = target.rsplit(":", 1) if ":" in target else (target, "27015")
        entry = ServerListEntry(name=target, host=host, port=int(raw_port), source="favorite")
        self.favorites.insert(0, entry)
        return entry

    def record_history(self, entry):
        self.history.insert(0, entry.with_updates(source="history"))


class CanonicalLocalMenuTests(unittest.TestCase):
    def test_draws_classic_main_menu_screen(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)

            menu._draw_screen(game, state, player_name="Alice")

            texts = self._drawn_texts(game)
            self.assertIn("Start Game", texts)
            self.assertIn("Find Servers", texts)
            self.assertIn("Options", texts)
            self.assertIn("Quit", texts)
            self.assertIn("0.25 (Python Port)", texts)

    def test_find_servers_uses_main_menu_button_geometry(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)

            rects = menu._draw_screen(game, state, player_name="Alice")

            start_left, start_top, start_right, start_bottom = rects["start"]
            find_left, find_top, find_right, find_bottom = rects["find_servers"]
            self.assertEqual((find_left, find_right), (start_left, start_right))
            self.assertAlmostEqual(find_top - find_bottom, start_top - start_bottom)

    def test_find_servers_opens_server_browser_screen(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["find_servers"]
            selection = menu._handle_click(game, state, rects, (left + right) / 2.0, (top + bottom) / 2.0)

            self.assertIsNone(selection)
            self.assertEqual(state.screen, "servers")

    def test_server_browser_draws_tabs_and_can_select_connect(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            state.browser_entries = (
                ServerListEntry(
                    name="Groundfire LAN",
                    host="127.0.0.1",
                    port=27015,
                    player_count=1,
                    max_players=8,
                    map_name="seed 1",
                    latency_ms=42,
                ),
            )

            rects = menu._draw_screen(game, state, player_name="Alice")
            texts = [call[2] for call in game.font.centred_calls] + [call[2] for call in game.font.text_calls]

            self.assertIn("Servers", texts)
            self.assertIn("Internet", texts)
            self.assertIn("Favorites", texts)
            self.assertIn("Connect", texts)
            left, top, right, bottom = rects["connect"]
            selection = menu._handle_click(game, state, rects, (left + right) / 2.0, (top + bottom) / 2.0)

            self.assertIsNotNone(selection)
            self.assertEqual(selection.action, "connect")
            self.assertEqual(selection.connect_host, "127.0.0.1")
            self.assertEqual(selection.connect_port, 27015)

    def test_server_browser_adds_manual_favorite_from_dialog(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            scanner = ServerScannerStub()
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            state.browser_tab = "favorites"

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["add_server"]
            menu._handle_click(
                game,
                state,
                rects,
                (left + right) / 2.0,
                (top + bottom) / 2.0,
                server_scanner=scanner,
            )
            state.add_server_value = "example.test:27017"
            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["add_server_ok"]
            menu._handle_click(
                game,
                state,
                rects,
                (left + right) / 2.0,
                (top + bottom) / 2.0,
                server_scanner=scanner,
            )

            self.assertEqual(state.screen, "servers")
            self.assertEqual(state.browser_tab, "favorites")
            self.assertEqual(scanner.favorites[0].endpoint, "example.test:27017")

    def test_server_browser_filters_sorts_and_scrolls_entries(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            entries = tuple(
                ServerListEntry(
                    name=f"Server {index:02d}",
                    host="127.0.0.1",
                    port=27015 + index,
                    player_count=index % 8,
                    max_players=8,
                    latency_ms=100 - index,
                    map_name="keep" if index == 25 else "other",
                )
                for index in range(30)
            )

            menu._set_browser_entries(state, entries)
            state.browser_filter_text = "keep"
            menu._set_browser_entries(state, entries)
            self.assertEqual([entry.port for entry in state.browser_entries], [27040])

            state.browser_filter_text = ""
            state.browser_filter_secure_only = True
            menu._set_browser_entries(state, entries[:1] + (entries[1].with_updates(secure=False),) + entries[2:])
            self.assertNotIn(27016, [entry.port for entry in state.browser_entries])

            state.browser_filter_secure_only = False
            state.browser_filter_region = "sa"
            entries_with_region = (entries[0].with_updates(region="sa"), entries[1].with_updates(region="eu"))
            menu._set_browser_entries(state, entries_with_region)
            self.assertEqual([entry.region for entry in state.browser_entries], ["sa"])

            state.browser_filter_region = ""
            state.browser_sort_column = "players"
            state.browser_sort_desc = True
            menu._set_browser_entries(state, entries)
            self.assertGreaterEqual(state.browser_entries[0].player_count, state.browser_entries[-1].player_count)

            menu._scroll_browser(state, 3)
            self.assertEqual(state.browser_scroll_index, 3)

    def test_server_browser_refreshes_selected_entry(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            entry = ServerListEntry(name="Remote", host="10.0.0.2", port=27015, latency_ms=99)
            scanner = ServerScannerStub((entry,))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            menu._set_browser_entries(state, (entry,))

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["quick_refresh"]
            menu._handle_click(
                game,
                state,
                rects,
                (left + right) / 2.0,
                (top + bottom) / 2.0,
                server_scanner=scanner,
            )

            self.assertEqual(state.browser_entries[0].latency_ms, 7)
            self.assertEqual(scanner.updated[0].endpoint, "10.0.0.2:27015")

    def test_server_browser_prompts_for_password_before_connecting_to_locked_server(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            scanner = ServerScannerStub()
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            state.browser_entries = (
                ServerListEntry(
                    name="Locked",
                    host="127.0.0.1",
                    port=27015,
                    requires_password=True,
                ),
            )

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["connect"]
            selection = menu._handle_click(
                game,
                state,
                rects,
                (left + right) / 2.0,
                (top + bottom) / 2.0,
                server_scanner=scanner,
            )
            self.assertIsNone(selection)
            self.assertEqual(state.screen, "server_password")

            state.connect_password_value = "secret"
            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["password_ok"]
            selection = menu._handle_click(
                game,
                state,
                rects,
                (left + right) / 2.0,
                (top + bottom) / 2.0,
                server_scanner=scanner,
            )

            self.assertIsNotNone(selection)
            self.assertEqual(selection.connect_password, "secret")

    def test_server_browser_double_click_connects_selected_row(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            scanner = ServerScannerStub()
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            state.browser_entries = (
                ServerListEntry(name="Loopback", host="127.0.0.1", port=27015),
            )

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["server_row_0"]
            x = (left + right) / 2.0
            y = (top + bottom) / 2.0
            first = menu._handle_click(game, state, rects, x, y, server_scanner=scanner)
            second = menu._handle_click(game, state, rects, x, y, server_scanner=scanner)

            self.assertIsNone(first)
            self.assertIsNotNone(second)
            self.assertEqual(second.action, "connect")
            self.assertEqual(second.connect_host, "127.0.0.1")

    def test_server_browser_scroll_track_moves_a_page(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            state.browser_entries = tuple(
                ServerListEntry(name=f"Server {index}", host="127.0.0.1", port=27015 + index)
                for index in range(40)
            )

            rects = menu._draw_screen(game, state, player_name="Alice")
            menu._handle_click(game, state, rects, 9.65, -4.0)

            self.assertEqual(state.browser_scroll_index, 16)

    def test_server_browser_scroll_thumb_drags_to_matching_position(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            state.browser_entries = tuple(
                ServerListEntry(name=f"Server {index}", host="127.0.0.1", port=27015 + index)
                for index in range(80)
            )

            rects = menu._draw_screen(game, state, player_name="Alice")
            thumb = rects["scroll_thumb"]
            menu._handle_click(game, state, rects, (thumb[0] + thumb[2]) / 2.0, (thumb[1] + thumb[3]) / 2.0)
            menu._drag_browser_scrollbar(state, rects, -4.75)

            self.assertTrue(state.browser_scroll_dragging)
            self.assertGreater(state.browser_scroll_index, 40)
            self.assertLessEqual(state.browser_scroll_index, len(state.browser_entries) - menu._browser_max_rows)

    def test_server_browser_reference_texts_match_attached_screens(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"

            menu._draw_screen(game, state, player_name="Alice")
            texts = [call[2] for call in game.font.text_calls]

            self.assertIn("Open the list of all servers (5300+)", texts)
            self.assertEqual(menu._empty_browser_message("lan"), "No internet games responded to the query.")

    def test_server_browser_hover_and_pressed_buttons_use_distinct_fill(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            state.browser_entries = (
                ServerListEntry(name="Loopback", host="127.0.0.1", port=27015),
            )

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["refresh_all"]
            game.interface.mouse_pos = ((left + right) / 2.0, (top + bottom) / 2.0)
            game.interface.mouse_buttons = (True, False, False)
            game.graphics.rect_calls.clear()
            menu._draw_screen(game, state, player_name="Alice")

            self.assertIn((112, 55, 0, 230), [call[-1] for call in game.graphics.rect_calls])

    def test_server_browser_reference_tabs_have_expected_columns_buttons_and_empty_messages(self):
        expectations = {
            "internet": {
                "columns": ("Servers", "Game", "Players", "Map", "Latency"),
                "buttons": ("Add Favorite", "Quick refresh", "Refresh all", "Change filters", "Connect"),
                "message": "No internet games responded to the query.",
            },
            "favorites": {
                "columns": ("Servers", "Game", "Players", "Map", "Latency"),
                "buttons": ("Add Current Server", "Add a Server", "Refresh", "Change filters", "Connect"),
                "message": "No favorite servers have been added.",
            },
            "unique": {
                "columns": ("Servers", "Server description", "Game", "Players", "Map", "Latency"),
                "buttons": ("Add Favorite", "Quick refresh", "Refresh all", "Change filters", "Connect"),
                "message": "No internet games responded to the query.",
            },
            "history": {
                "columns": ("Servers", "Game", "Players", "Map", "Latency", "Last played"),
                "buttons": ("Refresh", "Change filters", "Connect"),
                "message": "No servers have been played recently.",
            },
            "lan": {
                "columns": ("Servers", "Game", "Players", "Map", "Latency"),
                "buttons": ("Refresh", "Change filters", "Connect"),
                "message": "No internet games responded to the query.",
            },
        }

        with TemporaryDirectory() as temp_dir:
            for tab, expected in expectations.items():
                with self.subTest(tab=tab):
                    game = self._make_game(Path(temp_dir))
                    menu = CanonicalLocalMenu()
                    state = menu._build_initial_state(game, ai_players=1)
                    state.screen = "servers"
                    state.browser_tab = tab
                    state.browser_status = menu._empty_browser_message(tab)

                    menu._draw_screen(game, state, player_name="Alice")
                    texts = self._drawn_texts(game)

                    for label in expected["columns"]:
                        self.assertTrue(
                            any(text == label or text.startswith(f"{label} ") for text in texts),
                            label,
                        )
                    for label in expected["buttons"]:
                        self.assertIn(label, texts)
                    self.assertIn(expected["message"], texts)
                    self.assertIn("Open the list of all servers (5300+)", texts)

    def test_server_browser_open_all_link_switches_to_unique_and_combines_all_sources(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            internet = ServerListEntry(name="Internet", host="127.0.0.1", port=27015, latency_ms=30)
            favorite = ServerListEntry(name="Favorite", host="127.0.0.1", port=27016, source="favorite", latency_ms=20)
            history = ServerListEntry(name="History", host="127.0.0.1", port=27017, source="history", latency_ms=10)
            scanner = ServerScannerStub((internet,))
            scanner.favorites.append(favorite)
            scanner.history.append(history)
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            menu._set_browser_entries(state, (internet,))

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["open_all"]
            menu._handle_click(
                game,
                state,
                rects,
                (left + right) / 2.0,
                (top + bottom) / 2.0,
                server_scanner=scanner,
            )

            self.assertTrue(state.browser_show_all)
            self.assertEqual(state.browser_tab, "unique")
            self.assertEqual(
                {entry.endpoint for entry in state.browser_entries},
                {internet.endpoint, favorite.endpoint, history.endpoint},
            )
            self.assertEqual(state.browser_status, "Showing the list of all servers (5300+).")

    def test_server_browser_add_current_server_to_favorites(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            selected = ServerListEntry(name="Public", host="127.0.0.1", port=27015, latency_ms=25)
            scanner = ServerScannerStub((selected,))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            menu._set_browser_entries(state, (selected,))

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["add_favorite"]
            menu._handle_click(
                game,
                state,
                rects,
                (left + right) / 2.0,
                (top + bottom) / 2.0,
                server_scanner=scanner,
            )

            self.assertEqual(scanner.favorites[0].endpoint, selected.endpoint)
            self.assertEqual(scanner.favorites[0].source, "favorite")

    def test_server_browser_filters_apply_to_favorites_history_and_lan_sources(self):
        matching = ServerListEntry(
            name="Needle Server",
            host="127.0.0.1",
            port=27015,
            map_name="arena",
            region="sa",
            latency_ms=40,
        )
        other = ServerListEntry(
            name="Other Server",
            host="127.0.0.1",
            port=27016,
            map_name="dust",
            region="eu",
            latency_ms=80,
        )

        with TemporaryDirectory() as temp_dir:
            for tab in ("favorites", "history", "lan"):
                with self.subTest(tab=tab):
                    game = self._make_game(Path(temp_dir))
                    scanner = ServerScannerStub((matching, other))
                    scanner.favorites = [matching.with_updates(source="favorite"), other.with_updates(source="favorite")]
                    scanner.history = [matching.with_updates(source="history"), other.with_updates(source="history")]
                    menu = CanonicalLocalMenu()
                    state = menu._build_initial_state(game, ai_players=1)
                    state.screen = "servers"
                    state.browser_tab = tab
                    state.browser_filter_text = "needle"
                    state.browser_filter_region = "sa"
                    state.browser_filter_max_latency = 50

                    menu._refresh_browser_from_scanner(state, scanner)

                    self.assertEqual([entry.endpoint for entry in state.browser_entries], [matching.endpoint])

    def test_server_browser_keyboard_navigation_tabs_and_enter_connects(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            entries = tuple(
                ServerListEntry(name=f"Server {index}", host="127.0.0.1", port=27015 + index)
                for index in range(30)
            )
            scanner = ServerScannerStub(entries)
            scanner.favorites.append(ServerListEntry(name="Favorite", host="127.0.0.1", port=28000, source="favorite"))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            menu._set_browser_entries(state, entries)
            key_names = {"down": 1, "pagedown": 2, "tab": 3, "enter": 4}

            menu._handle_browser_key(state, 1, key_names, server_scanner=scanner)
            self.assertEqual(state.selected_server_index, 1)
            menu._handle_browser_key(state, 2, key_names, server_scanner=scanner)
            self.assertEqual(state.selected_server_index, 25)

            expected_port = state.browser_entries[state.selected_server_index].port
            selection = menu._handle_browser_key(state, 4, key_names, server_scanner=scanner)
            self.assertIsNotNone(selection)
            self.assertEqual(selection.connect_port, expected_port)

            menu._handle_browser_key(state, 3, key_names, server_scanner=scanner)
            self.assertEqual(state.browser_tab, "favorites")
            self.assertEqual(state.browser_entries[0].endpoint, "127.0.0.1:28000")

    def test_server_browser_filter_text_input_and_wheel_scroll_are_handled(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            scanner = ServerScannerStub(
                tuple(
                    ServerListEntry(name=f"Server {index}", host="127.0.0.1", port=27015 + index)
                    for index in range(40)
                )
            )
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "servers"
            menu._set_browser_entries(state, scanner.entries)
            key_names = {"backspace": 1, "enter": 2}

            menu._handle_input_events(
                state,
                (SimpleNamespace(y=-3),),
                key_names,
                server_scanner=scanner,
            )
            self.assertEqual(state.browser_scroll_index, 3)

            state.screen = "server_filters"
            menu._handle_input_events(
                state,
                (
                    SimpleNamespace(key=99, unicode="S"),
                    SimpleNamespace(key=99, unicode="e"),
                    SimpleNamespace(key=1, unicode=""),
                ),
                key_names,
                server_scanner=scanner,
            )
            self.assertEqual(state.browser_filter_text, "S")

    def _drawn_texts(self, game: MenuGameStub) -> list[str]:
        return [call[2] for call in game.font.centred_calls] + [call[2] for call in game.font.text_calls]

    def test_draws_classic_options_screen(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "options"

            menu._draw_screen(game, state, player_name="Alice")

            centred_texts = [call[2] for call in game.font.centred_calls]
            self.assertIn("Options", centred_texts)
            self.assertIn("Resolution:", centred_texts)
            self.assertIn("Screen Mode:", centred_texts)
            self.assertIn("Set Controls", centred_texts)
            self.assertIn("Apply", centred_texts)
            self.assertIn("Back", centred_texts)

    def test_draws_classic_select_players_screen(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=2)
            state.screen = "select_players"

            menu._draw_screen(game, state, player_name="Alice")

            centred_texts = [call[2] for call in game.font.centred_calls]
            left_texts = [call[2] for call in game.font.text_calls]
            self.assertIn("Select Players", centred_texts)
            self.assertIn("Controlled by", centred_texts)
            self.assertIn("Rounds :", centred_texts)
            self.assertIn("Start!", centred_texts)
            self.assertIn("Back", centred_texts)
            self.assertIn("Player 1", left_texts)
            self.assertIn("Keyboard1", centred_texts)

    def test_draws_classic_quit_confirmation_screen(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "quit"

            menu._draw_screen(game, state, player_name="Alice")

            texts = [call[2] for call in game.font.centred_calls]
            self.assertIn("Are you sure?", texts)
            self.assertIn("Yes", texts)
            self.assertIn("No", texts)

    def test_apply_options_updates_window_and_persists_settings(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.resolution_index = 2
            state.fullscreen = True

            menu._apply_options(game, state)

            self.assertEqual(game.interface.change_calls, [(1024, 768, True)])
            settings_text = game.get_settings_path().read_text(encoding="utf-8")
            self.assertIn("ScreenWidth=1024", settings_text)
            self.assertIn("ScreenHeight=768", settings_text)
            self.assertIn("Fullscreen=1", settings_text)

    def test_set_controls_routes_to_classic_controller_menu(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "options"

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["set_controls"]
            selection = menu._handle_click(game, state, rects, (left + right) / 2.0, (top + bottom) / 2.0)

            self.assertIsNotNone(selection)
            self.assertEqual(selection.action, "classic")
            self.assertEqual(selection.launch_target, "controllers")
            self.assertFalse(selection.persist_mode)

    def test_multi_human_start_falls_back_to_classic_runtime(self):
        with TemporaryDirectory() as temp_dir:
            game = self._make_game(Path(temp_dir))
            menu = CanonicalLocalMenu()
            state = menu._build_initial_state(game, ai_players=1)
            state.screen = "select_players"
            state.players[1].is_human = True
            state.players[1].controller = 1

            rects = menu._draw_screen(game, state, player_name="Alice")
            left, top, right, bottom = rects["start"]
            selection = menu._handle_click(game, state, rects, (left + right) / 2.0, (top + bottom) / 2.0)

            self.assertIsNotNone(selection)
            self.assertEqual(selection.action, "classic")
            self.assertEqual(selection.launch_target, "configured_start")
            self.assertFalse(selection.persist_mode)

    def _make_game(self, temp_dir: Path) -> MenuGameStub:
        settings_path = temp_dir / "options.ini"
        settings_path.write_text(
            "[Graphics]\nScreenWidth=640\nScreenHeight=480\nFullscreen=0\n",
            encoding="utf-8",
        )
        return MenuGameStub(settings_path)


if __name__ == "__main__":
    unittest.main()
