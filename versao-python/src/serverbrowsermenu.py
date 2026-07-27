from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from groundfire_net.browser import ServerBook, ServerListEntry

from .common import GameState
from .menu import Menu
from .groundfire.network.browser import GroundfireServerScanner, default_server_book_path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class _BrowserState:
    tab: str = "internet"
    entries: tuple[ServerListEntry, ...] = ()
    selected_index: int = 0
    scroll_index: int = 0
    status: str = "Searching for Groundfire servers..."
    sort_column: str = "latency"
    sort_desc: bool = False
    show_all: bool = False
    filter_text: str = ""
    show_full: bool = True
    show_empty: bool = True
    show_passworded: bool = True
    secure_only: bool = False
    region: str = ""
    max_latency: int | None = None
    add_server_value: str = "127.0.0.1:27015"
    password_value: str = ""
    pending_endpoint: str = ""
    join_as_computer: bool = False
    dialog: str = ""
    last_clicked_index: int = -1
    last_clicked_time: float = 0.0
    dragging_scrollbar: bool = False
    drag_offset: float = 0.0


class ServerBrowserMenu(Menu):
    _tabs = (
        ("internet", "Internet"),
        ("favorites", "Favorites"),
        ("unique", "Unique"),
        ("history", "History"),
        ("lan", "Lan"),
    )
    _max_rows = 24
    _latency_options: tuple[int | None, ...] = (None, 50, 100, 150, 250, 500)
    _region_options = ("", "world", "na", "sa", "eu", "asia", "local")
    _bright_text = (255, 255, 255)
    _cyan_text = (0, 255, 255)
    _gold_text = (255, 255, 0)
    _muted_text = (76, 76, 76)
    _brown_fill = (153, 76, 0, 180)
    _frame_fill = (0, 0, 0, 145)
    _body_fill = (0, 0, 0, 120)
    _header_fill = (153, 76, 0, 150)
    _dialog_fill = (0, 0, 0, 205)
    _input_fill = (0, 0, 0, 170)
    _row_text = (235, 240, 245)
    _dim_text = (190, 215, 230)
    _selected_fill = (153, 76, 0, 135)
    _hover_fill = (153, 76, 0, 80)

    def __init__(self, game):
        super().__init__(game)
        self._state = _BrowserState()
        self._scanner: GroundfireServerScanner | None = None
        self._scanner_error = ""
        self._last_left_pressed = False
        self._open_scanner()

    def close(self):
        scanner = self._scanner
        self._scanner = None
        if scanner is not None:
            scanner.close()

    def update(self, time_delta: float) -> int:
        self.update_background(time_delta)
        self._refresh_entries()
        input_state = self._handle_input_events()
        if input_state is not None:
            return input_state

        left_pressed = bool(self._interface.get_mouse_button(0))
        mouse_x, mouse_y = self._interface.get_mouse_pos()
        rects = self._rects()

        if left_pressed and self._state.dragging_scrollbar:
            self._drag_scrollbar(rects, mouse_y)
        elif not left_pressed:
            self._state.dragging_scrollbar = False

        clicked = left_pressed and not self._last_left_pressed
        self._last_left_pressed = left_pressed
        if clicked:
            return self._handle_click(rects, mouse_x, mouse_y)

        return GameState.CURRENT_STATE

    def draw(self):
        self.draw_background()
        rects = self._rects()
        state = self._state
        ui = self._ui

        self._draw_panel(-9.95, 7.35, 9.95, -7.35, self._frame_fill)
        self._draw_panel(-9.75, 6.55, 9.75, -6.95, self._body_fill)
        ui.draw_text(-9.55, 6.82, "Servers", style=ui.style(0.42, self._bright_text, spacing=0.2, shadow=True))
        ui.draw_centered_text(9.58, 6.47, "x", style=ui.style(0.45, self._bright_text, shadow=True))

        mouse_x, mouse_y = self._interface.get_mouse_pos()
        left_down = bool(self._interface.get_mouse_button(0))
        for tab_key, label in self._tabs:
            rect = rects[f"tab_{tab_key}"]
            active = state.tab == tab_key
            hovered = self._contains(rect, mouse_x, mouse_y)
            self._draw_panel(*rect, self._tab_fill(active=active, hovered=hovered, pressed=hovered and left_down))
            ui.draw_text(
                rect[0] + 0.12,
                rect[3] + 0.1,
                label,
                style=ui.style(
                    0.25,
                    self._gold_text if active else self._bright_text,
                    spacing=0.1,
                    shadow=True,
                ),
            )

        columns = self._columns_for_tab(state.tab)
        header_top, header_bottom = 5.25, 4.85
        self._draw_panel(-9.75, header_top, 9.55, header_bottom, self._header_fill)
        for key, label, left, right in columns:
            suffix = ""
            if state.sort_column == key:
                suffix = " v" if state.sort_desc else " ^"
            ui.draw_text(
                left + 0.07,
                4.92,
                label + suffix,
                style=ui.style(0.22, self._bright_text, spacing=0.09, shadow=True),
            )

        self._draw_rows(rects, columns)
        self._draw_scrollbar(rects)
        self._draw_footer(rects)

        if state.dialog == "filters":
            self._draw_filter_dialog(rects)
        elif state.dialog == "add":
            self._draw_add_server_dialog(rects)
        elif state.dialog == "join":
            self._draw_join_dialog(rects)

    def _open_scanner(self):
        try:
            self._scanner = GroundfireServerScanner(
                server_book=ServerBook(default_server_book_path(PROJECT_ROOT)),
            )
            self._scanner.open()
            self._scanner.refresh()
            self._scanner.refresh_master_servers(timeout=0.02)
        except OSError as exc:
            self._scanner = None
            self._scanner_error = str(exc)
            self._state.status = f"Server scanner is not available: {exc}"

    def _refresh_entries(
        self,
        *,
        raw_entries: tuple[ServerListEntry, ...] | None = None,
        status: str | None = None,
    ):
        state = self._state
        scanner = self._scanner
        if scanner is None:
            if self._scanner_error:
                state.status = f"Server scanner is not available: {self._scanner_error}"
            return
        if raw_entries is None:
            raw_entries = scanner.all_entries() if state.show_all else scanner.entries_for_tab(state.tab)
        state.entries = self._filtered_entries(raw_entries)
        self._clamp_selection()
        if state.entries:
            if status is not None:
                state.status = status
            elif self._status_is_placeholder(state.status):
                state.status = ""
            return
        state.status = status or self._empty_message()

    def _rects(self) -> dict[str, tuple[float, float, float, float]]:
        rects: dict[str, tuple[float, float, float, float]] = {
            "close": (9.35, 7.05, 9.8, 6.55),
            "filters": (-9.7, -5.95, -7.8, -6.55),
            "connect": (8.55, -5.95, 9.75, -6.55),
            "open_all": (5.9, -6.75, 9.55, -7.15),
            "scroll_up": (9.55, 4.85, 9.75, 4.45),
            "scroll_down": (9.55, -5.45, 9.75, -5.85),
        }
        tab_left = -9.75
        for tab_key, _label in self._tabs:
            width = 1.45 if tab_key != "favorites" else 1.65
            rects[f"tab_{tab_key}"] = (tab_left, 6.05, tab_left + width, 5.45)
            tab_left += width + 0.05
        for key, _label, left, right in self._columns_for_tab(self._state.tab):
            rects[f"sort_{key}"] = (left, 5.25, right, 4.85)
        row_y = 4.48
        for index in range(
            self._state.scroll_index,
            min(len(self._state.entries), self._state.scroll_index + self._max_rows),
        ):
            rects[f"row_{index}"] = (-9.75, row_y + 0.22, 9.55, row_y - 0.2)
            row_y -= 0.42
        self._add_action_rects(rects)
        self._add_dialog_rects(rects)
        return rects

    def _add_action_rects(self, rects):
        tab = self._state.tab
        if tab == "favorites":
            rects["add_favorite"] = (3.0, -5.95, 5.4, -6.55)
            rects["add_server"] = (5.5, -5.95, 7.1, -6.55)
            rects["refresh"] = (7.2, -5.95, 8.45, -6.55)
        elif tab in {"history", "lan"}:
            rects["refresh"] = (7.1, -5.95, 8.45, -6.55)
        else:
            rects["add_favorite"] = (3.0, -5.95, 5.0, -6.55)
            rects["quick_refresh"] = (5.1, -5.95, 6.65, -6.55)
            rects["refresh_all"] = (6.75, -5.95, 8.45, -6.55)

    def _add_dialog_rects(self, rects):
        if self._state.dialog == "filters":
            rects.update(
                {
                    "filter_text": (-3.1, 2.0, 4.9, 1.4),
                    "filter_full": (-4.8, 0.85, -4.25, 0.3),
                    "filter_empty": (-4.8, 0.05, -4.25, -0.5),
                    "filter_password": (-4.8, -0.75, -4.25, -1.3),
                    "filter_secure": (-4.8, -1.55, -4.25, -2.1),
                    "filter_region": (1.0, -1.35, 4.1, -1.95),
                    "filter_latency": (1.0, -2.35, 4.1, -2.95),
                    "filter_clear": (4.25, -2.35, 5.55, -2.95),
                    "filter_ok": (1.15, -3.45, 3.0, -4.05),
                    "filter_cancel": (3.15, -3.45, 5.0, -4.05),
                }
            )
        elif self._state.dialog == "add":
            rects.update(
                {
                    "add_text": (-4.7, 0.85, 4.7, 0.2),
                    "add_ok": (1.3, -1.05, 3.2, -1.65),
                    "add_cancel": (3.35, -1.05, 5.15, -1.65),
                }
            )
        elif self._state.dialog == "join":
            rects.update(
                {
                    "join_password_text": (-4.7, 1.05, 4.7, 0.4),
                    "join_human_radio": (-4.7, -0.1, -1.2, -0.75),
                    "join_ai_radio": (0.3, -0.1, 3.8, -0.75),
                    "join_connect": (0.85, -2.25, 2.7, -2.85),
                    "join_cancel": (2.85, -2.25, 4.65, -2.85),
                }
            )

    def _draw_rows(self, rects, columns):
        ui = self._ui
        mouse_x, mouse_y = self._interface.get_mouse_pos()
        row_y = 4.48
        visible = self._state.entries[self._state.scroll_index : self._state.scroll_index + self._max_rows]
        for offset, entry in enumerate(visible):
            index = self._state.scroll_index + offset
            rect = rects[f"row_{index}"]
            selected = index == self._state.selected_index
            if selected:
                self._draw_panel(*rect, self._selected_fill)
            elif self._contains(rect, mouse_x, mouse_y):
                self._draw_panel(*rect, self._hover_fill)
            style = ui.style(0.2, self._bright_text if selected else self._row_text, spacing=0.08, shadow=True)
            values = {
                "name": ("[P] " if entry.requires_password else "") + entry.name,
                "description": entry.description,
                "game": entry.game,
                "players": f"{entry.player_count}/{entry.max_players}",
                "map": entry.map_name,
                "latency": "-" if entry.latency_ms is None else str(entry.latency_ms),
                "last_played": entry.last_played or "-",
            }
            for key, _label, left, right in columns:
                max_chars = max(4, int((right - left) * 5.0))
                ui.draw_text(left + 0.07, row_y - 0.12, self._shorten(values.get(key, ""), max_chars), style=style)
            row_y -= 0.42

        if not self._state.entries and self._state.status:
            ui.draw_text(
                -9.55,
                4.35,
                self._state.status,
                style=ui.style(0.26, self._bright_text, spacing=0.11, shadow=True),
            )

    def _draw_scrollbar(self, rects):
        mouse_x, mouse_y = self._interface.get_mouse_pos()
        left_down = bool(self._interface.get_mouse_button(0))
        self._draw_panel(9.55, 4.85, 9.75, -5.85, (0, 0, 0, 135))
        self._draw_panel(
            *rects["scroll_up"],
            self._control_fill(True, self._contains(rects["scroll_up"], mouse_x, mouse_y), left_down),
        )
        self._draw_panel(
            *rects["scroll_down"],
            self._control_fill(True, self._contains(rects["scroll_down"], mouse_x, mouse_y), left_down),
        )
        self._ui.draw_centered_text(9.65, 4.47, "^", style=self._ui.style(0.2, self._bright_text, spacing=0.08))
        self._ui.draw_centered_text(9.65, -5.82, "v", style=self._ui.style(0.2, self._bright_text, spacing=0.08))
        thumb = self._scroll_thumb()
        rects["scroll_thumb"] = thumb
        hovered = self._contains(thumb, mouse_x, mouse_y) or self._state.dragging_scrollbar
        self._draw_panel(*thumb, self._control_fill(True, hovered, left_down and hovered))

    def _draw_footer(self, rects):
        state = self._state
        if state.status and state.entries:
            self._ui.draw_text(
                -9.55,
                -5.65,
                self._shorten(state.status, 92),
                style=self._ui.style(0.2, self._dim_text, spacing=0.08, shadow=True),
            )

        if state.tab == "favorites":
            self._draw_button(rects["add_favorite"], "Add Current Server", enabled=bool(state.entries))
            self._draw_button(rects["add_server"], "Add a Server", enabled=True)
            self._draw_button(rects["refresh"], "Refresh", enabled=True)
        elif state.tab in {"history", "lan"}:
            self._draw_button(rects["refresh"], "Refresh", enabled=True)
        else:
            self._draw_button(rects["add_favorite"], "Add Favorite", enabled=bool(state.entries))
            self._draw_button(rects["quick_refresh"], "Quick refresh", enabled=bool(state.entries))
            self._draw_button(rects["refresh_all"], "Refresh all", enabled=True)

        self._draw_button(rects["filters"], "Change filters", enabled=True)
        self._draw_button(rects["connect"], "Connect", enabled=bool(state.entries))
        self._ui.draw_text(
            6.15,
            -7.08,
            "Open the list of all servers",
            style=self._ui.style(0.2, self._cyan_text, spacing=0.08, shadow=True),
        )
        self._draw_resize_grip()

    def _draw_filter_dialog(self, rects):
        ui = self._ui
        state = self._state
        self._draw_panel(-5.8, 3.3, 5.8, -4.5, self._dialog_fill)
        self._draw_panel(-5.8, 3.3, 5.8, 2.45, self._header_fill)
        ui.draw_text(-5.35, 2.8, "Filters", style=ui.style(0.38, self._bright_text, spacing=0.16, shadow=True))
        ui.draw_text(-5.25, 1.55, "Server / map", style=ui.style(0.26, self._bright_text, spacing=0.11))
        self._draw_text_field(rects["filter_text"], state.filter_text, active=True)
        self._draw_checkbox(rects["filter_full"], state.show_full, "Show full servers")
        self._draw_checkbox(rects["filter_empty"], state.show_empty, "Show empty servers")
        self._draw_checkbox(rects["filter_password"], state.show_passworded, "Show passworded servers")
        self._draw_checkbox(rects["filter_secure"], state.secure_only, "Secure servers only")
        ui.draw_text(-5.25, -1.8, "Region", style=ui.style(0.26, self._bright_text, spacing=0.11))
        self._draw_button(rects["filter_region"], self._region_label(), enabled=True)
        ui.draw_text(-5.25, -2.8, "Maximum latency", style=ui.style(0.26, self._bright_text, spacing=0.11))
        self._draw_button(rects["filter_latency"], self._latency_label(), enabled=True)
        self._draw_button(rects["filter_clear"], "Clear", enabled=True)
        self._draw_button(rects["filter_ok"], "Apply", enabled=True)
        self._draw_button(rects["filter_cancel"], "Close", enabled=True)

    def _draw_add_server_dialog(self, rects):
        ui = self._ui
        self._draw_panel(-5.8, 2.45, 5.8, -2.3, self._dialog_fill)
        self._draw_panel(-5.8, 2.45, 5.8, 1.55, self._header_fill)
        ui.draw_text(-5.35, 1.9, "Add a Server", style=ui.style(0.38, self._bright_text, spacing=0.16, shadow=True))
        ui.draw_text(-5.15, 0.35, "Address", style=ui.style(0.26, self._bright_text, spacing=0.11))
        self._draw_text_field(rects["add_text"], self._state.add_server_value, active=True)
        self._draw_button(rects["add_ok"], "Add", enabled=True)
        self._draw_button(rects["add_cancel"], "Cancel", enabled=True)

    def _draw_join_dialog(self, rects):
        ui = self._ui
        selected = self._selected_entry()
        requires_password = bool(selected.requires_password) if selected is not None else False
        self._draw_panel(-5.8, 2.7, 5.8, -3.3, self._dialog_fill)
        self._draw_panel(-5.8, 2.7, 5.8, 1.8, self._header_fill)
        ui.draw_text(-5.35, 2.15, "Join Server", style=ui.style(0.38, self._bright_text, spacing=0.16, shadow=True))
        ui.draw_text(-5.15, 1.15, self._state.pending_endpoint, style=ui.style(0.24, self._bright_text, spacing=0.1))
        if requires_password:
            ui.draw_text(-5.15, 0.55, "Password", style=ui.style(0.24, self._bright_text, spacing=0.1))
            self._draw_text_field(rects["join_password_text"], "*" * len(self._state.password_value), active=True)
        else:
            ui.draw_text(
                -5.15,
                0.45,
                "Player type",
                style=ui.style(0.24, self._dim_text, spacing=0.1),
            )
        self._draw_radio_button(rects["join_human_radio"], "Human", checked=not self._state.join_as_computer)
        self._draw_radio_button(rects["join_ai_radio"], "AI", checked=self._state.join_as_computer)
        self._draw_button(rects["join_connect"], "Connect", enabled=True)
        self._draw_button(rects["join_cancel"], "Cancel", enabled=True)

    def _handle_click(self, rects, mouse_x: float, mouse_y: float) -> int:
        state = self._state
        if self._contains(rects.get("close"), mouse_x, mouse_y):
            self.close()
            return GameState.MAIN_MENU

        if state.dialog == "filters":
            self._handle_filter_click(rects, mouse_x, mouse_y)
            return GameState.CURRENT_STATE
        if state.dialog == "add":
            self._handle_add_click(rects, mouse_x, mouse_y)
            return GameState.CURRENT_STATE
        if state.dialog == "join":
            self._handle_join_click(rects, mouse_x, mouse_y)
            return GameState.CURRENT_STATE

        for tab, _label in self._tabs:
            if self._contains(rects.get(f"tab_{tab}"), mouse_x, mouse_y):
                state.tab = tab
                state.show_all = False
                state.selected_index = 0
                state.scroll_index = 0
                state.status = ""
                self._refresh_entries()
                return GameState.CURRENT_STATE

        for column_key in ("name", "description", "game", "players", "map", "latency", "last_played"):
            if self._contains(rects.get(f"sort_{column_key}"), mouse_x, mouse_y):
                self._set_sort(column_key)
                return GameState.CURRENT_STATE

        if self._contains(rects.get("scroll_up"), mouse_x, mouse_y):
            self._scroll(-1)
            return GameState.CURRENT_STATE
        if self._contains(rects.get("scroll_down"), mouse_x, mouse_y):
            self._scroll(1)
            return GameState.CURRENT_STATE
        if self._contains((9.55, 4.35, 9.75, -5.35), mouse_x, mouse_y):
            thumb = self._scroll_thumb()
            if self._contains(thumb, mouse_x, mouse_y):
                state.dragging_scrollbar = True
                state.drag_offset = thumb[1] - mouse_y
            else:
                self._scroll(-self._max_rows if mouse_y > thumb[1] else self._max_rows)
            return GameState.CURRENT_STATE

        for index in range(state.scroll_index, min(len(state.entries), state.scroll_index + self._max_rows)):
            if self._contains(rects.get(f"row_{index}"), mouse_x, mouse_y):
                now = time.monotonic()
                double_click = state.last_clicked_index == index and (now - state.last_clicked_time) <= 0.35
                state.selected_index = index
                state.last_clicked_index = index
                state.last_clicked_time = now
                self._clamp_selection()
                if double_click:
                    self._connect_selected()
                return GameState.CURRENT_STATE

        if self._contains(rects.get("filters"), mouse_x, mouse_y):
            state.dialog = "filters"
        elif self._contains(rects.get("open_all"), mouse_x, mouse_y):
            state.show_all = True
            state.tab = "unique"
            state.selected_index = 0
            state.scroll_index = 0
            self._refresh_entries(status="Showing the list of all known servers.")
        elif self._contains(rects.get("add_server"), mouse_x, mouse_y):
            state.dialog = "add"
        elif self._contains(rects.get("refresh_all"), mouse_x, mouse_y) or self._contains(
            rects.get("refresh"),
            mouse_x,
            mouse_y,
        ):
            self._refresh_all()
        elif self._contains(rects.get("quick_refresh"), mouse_x, mouse_y):
            self._quick_refresh_selected()
        elif self._contains(rects.get("add_favorite"), mouse_x, mouse_y):
            self._add_selected_favorite()
        elif self._contains(rects.get("connect"), mouse_x, mouse_y):
            self._connect_selected()

        return GameState.CURRENT_STATE

    def _handle_filter_click(self, rects, mouse_x: float, mouse_y: float):
        state = self._state
        if self._contains(rects.get("filter_full"), mouse_x, mouse_y):
            state.show_full = not state.show_full
        elif self._contains(rects.get("filter_empty"), mouse_x, mouse_y):
            state.show_empty = not state.show_empty
        elif self._contains(rects.get("filter_password"), mouse_x, mouse_y):
            state.show_passworded = not state.show_passworded
        elif self._contains(rects.get("filter_secure"), mouse_x, mouse_y):
            state.secure_only = not state.secure_only
        elif self._contains(rects.get("filter_region"), mouse_x, mouse_y):
            state.region = self._next_value(self._region_options, state.region)
        elif self._contains(rects.get("filter_latency"), mouse_x, mouse_y):
            state.max_latency = self._next_value(self._latency_options, state.max_latency)
        elif self._contains(rects.get("filter_clear"), mouse_x, mouse_y):
            state.filter_text = ""
            state.show_full = True
            state.show_empty = True
            state.show_passworded = True
            state.secure_only = False
            state.region = ""
            state.max_latency = None
        elif self._contains(rects.get("filter_ok"), mouse_x, mouse_y):
            state.dialog = ""
            state.selected_index = 0
            state.scroll_index = 0
        elif self._contains(rects.get("filter_cancel"), mouse_x, mouse_y):
            state.dialog = ""
        self._refresh_entries()

    def _handle_add_click(self, rects, mouse_x: float, mouse_y: float):
        if self._contains(rects.get("add_ok"), mouse_x, mouse_y):
            self._add_manual_server()
        elif self._contains(rects.get("add_cancel"), mouse_x, mouse_y):
            self._state.dialog = ""

    def _handle_join_click(self, rects, mouse_x: float, mouse_y: float):
        if self._contains(rects.get("join_human_radio"), mouse_x, mouse_y):
            self._state.join_as_computer = False
        elif self._contains(rects.get("join_ai_radio"), mouse_x, mouse_y):
            self._state.join_as_computer = True
        elif self._contains(rects.get("join_connect"), mouse_x, mouse_y):
            self._finish_connect_selected()
        elif self._contains(rects.get("join_cancel"), mouse_x, mouse_y):
            self._state.dialog = ""
            self._state.password_value = ""
            self._state.pending_endpoint = ""

    def _handle_input_events(self) -> int | None:
        get_events = getattr(self._interface, "get_input_events", None)
        get_key_names = getattr(self._interface, "get_key_names", None)
        if not callable(get_events) or not callable(get_key_names):
            return None
        key_names = get_key_names()
        for event in get_events():
            key = getattr(event, "key", None)
            wheel_y = getattr(event, "y", None)
            if key is None and wheel_y is not None and self._state.dialog == "":
                self._scroll(-int(wheel_y))
                continue
            if key is None:
                continue
            if self._state.dialog == "filters":
                self._handle_filter_key(event, key, key_names)
            elif self._state.dialog == "add":
                self._handle_add_key(event, key, key_names)
            elif self._state.dialog == "join":
                self._handle_join_key(event, key, key_names)
            else:
                requested_state = self._handle_browser_key(key, key_names)
                if requested_state is not None:
                    return requested_state
        return None

    def _handle_browser_key(self, key: int, key_names: dict[str, int]) -> int | None:
        if self._is_key(key, key_names, "escape"):
            self.close()
            return GameState.MAIN_MENU
        elif self._is_key(key, key_names, "up"):
            self._state.selected_index -= 1
            self._clamp_selection()
        elif self._is_key(key, key_names, "down"):
            self._state.selected_index += 1
            self._clamp_selection()
        elif self._is_key(key, key_names, "pageup"):
            self._state.selected_index -= self._max_rows
            self._clamp_selection()
        elif self._is_key(key, key_names, "pagedown"):
            self._state.selected_index += self._max_rows
            self._clamp_selection()
        elif self._is_key(key, key_names, "tab"):
            self._cycle_tab()
            self._refresh_entries()
        elif self._is_key(key, key_names, "enter"):
            self._connect_selected()
        return None

    def _handle_filter_key(self, event, key: int, key_names: dict[str, int]):
        if self._is_key(key, key_names, "escape"):
            self._state.dialog = ""
        elif self._is_key(key, key_names, "enter"):
            self._state.dialog = ""
            self._state.selected_index = 0
            self._state.scroll_index = 0
        elif self._is_key(key, key_names, "backspace"):
            self._state.filter_text = self._state.filter_text[:-1]
        else:
            self._state.filter_text = self._append_printable(self._state.filter_text, event, max_length=48)
        self._refresh_entries()

    def _handle_add_key(self, event, key: int, key_names: dict[str, int]):
        if self._is_key(key, key_names, "escape"):
            self._state.dialog = ""
        elif self._is_key(key, key_names, "enter"):
            self._add_manual_server()
        elif self._is_key(key, key_names, "backspace"):
            self._state.add_server_value = self._state.add_server_value[:-1]
        else:
            self._state.add_server_value = self._append_printable(self._state.add_server_value, event, max_length=64)

    def _handle_join_key(self, event, key: int, key_names: dict[str, int]):
        if self._is_key(key, key_names, "escape"):
            self._state.dialog = ""
            self._state.password_value = ""
            self._state.pending_endpoint = ""
        elif self._is_key(key, key_names, "enter"):
            self._finish_connect_selected()
        elif self._is_key(key, key_names, "backspace"):
            self._state.password_value = self._state.password_value[:-1]
        else:
            self._state.password_value = self._append_printable(self._state.password_value, event, max_length=64)

    def _refresh_all(self):
        scanner = self._scanner
        if scanner is None:
            self._state.status = "Server scanner is not available."
            return
        if self._state.show_all:
            base_entries = scanner.all_entries()
            entries = tuple(scanner.refresh_entry(entry, timeout=0.02) for entry in base_entries)
            for entry in entries:
                scanner.update_entry(entry)
        else:
            entries = scanner.refresh_tab(self._state.tab)
        self._refresh_entries(raw_entries=entries, status=f"Refreshed {len(entries)} server(s).")

    def _quick_refresh_selected(self):
        selected = self._selected_entry()
        scanner = self._scanner
        if selected is None:
            return
        if scanner is None:
            self._state.status = "Server scanner is not available."
            return
        refreshed = scanner.refresh_entry(selected, timeout=0.05)
        scanner.update_entry(refreshed)
        entries = list(self._state.entries)
        entries[self._state.selected_index] = refreshed
        self._refresh_entries(raw_entries=tuple(entries), status=f"Refreshed {selected.endpoint}.")
        self._select_endpoint(refreshed.endpoint)

    def _add_selected_favorite(self):
        selected = self._selected_entry()
        scanner = self._scanner
        if selected is None or scanner is None:
            return
        scanner.add_favorite(selected)
        self._refresh_entries(status=f"Added {selected.endpoint} to Favorites.")

    def _add_manual_server(self):
        scanner = self._scanner
        target = self._state.add_server_value.strip()
        if not target:
            self._state.status = "Type a server address first."
            return
        if scanner is None:
            self._state.status = "Server scanner is not available."
            self._state.dialog = ""
            return
        try:
            entry = scanner.add_manual_server(target)
        except ValueError as exc:
            self._state.status = str(exc)
            return
        self._state.tab = "favorites"
        self._state.show_all = False
        self._state.dialog = ""
        self._refresh_entries(status=f"Added {entry.endpoint} to Favorites.")
        self._select_endpoint(entry.endpoint)

    def _connect_selected(self):
        selected = self._verified_selected_entry()
        if selected is None:
            return
        self._state.dialog = "join"
        self._state.password_value = ""
        self._state.pending_endpoint = selected.endpoint
        self._state.join_as_computer = False

    def _finish_connect_selected(self):
        selected = self._selected_entry()
        if selected is None:
            return
        self.close()
        self._game.request_online_connect(
            host=selected.host,
            port=selected.port,
            password=self._state.password_value,
            entry=selected,
            is_computer=self._state.join_as_computer,
        )

    def _verified_selected_entry(self) -> ServerListEntry | None:
        selected = self._selected_entry()
        if selected is None:
            return None
        scanner = self._scanner
        if scanner is None:
            self._state.status = "Server scanner is not available."
            return None

        refreshed = scanner.refresh_entry(selected, timeout=0.08)
        if refreshed.latency_ms is None:
            self._replace_selected_entry(refreshed)
            self._state.status = f"{selected.endpoint} did not respond. Start the server or refresh the list."
            return None

        scanner.update_entry(refreshed)
        self._replace_selected_entry(refreshed)
        self._state.status = f"{selected.endpoint} responded in {refreshed.latency_ms} ms."
        return refreshed

    def _replace_selected_entry(self, entry: ServerListEntry):
        if not self._state.entries:
            return
        index = max(0, min(self._state.selected_index, len(self._state.entries) - 1))
        entries = list(self._state.entries)
        entries[index] = entry
        self._state.entries = tuple(entries)

    def _selected_entry(self) -> ServerListEntry | None:
        if not self._state.entries:
            return None
        index = max(0, min(self._state.selected_index, len(self._state.entries) - 1))
        return self._state.entries[index]

    def _filtered_entries(self, entries: tuple[ServerListEntry, ...]) -> tuple[ServerListEntry, ...]:
        filtered = tuple(entry for entry in entries if self._entry_matches_filters(entry))
        return tuple(sorted(filtered, key=self._sort_value, reverse=self._state.sort_desc))

    def _entry_matches_filters(self, entry: ServerListEntry) -> bool:
        state = self._state
        needle = state.filter_text.strip().lower()
        if needle:
            haystack = " ".join((entry.name, entry.description, entry.game, entry.map_name, entry.endpoint)).lower()
            if needle not in haystack:
                return False
        if not state.show_full and entry.player_count >= entry.max_players:
            return False
        if not state.show_empty and entry.player_count <= 0:
            return False
        if not state.show_passworded and entry.requires_password:
            return False
        if state.secure_only and not entry.secure:
            return False
        if state.region and entry.region.lower() != state.region.lower():
            return False
        if state.max_latency is not None and (entry.latency_ms is None or entry.latency_ms > state.max_latency):
            return False
        return True

    def _sort_value(self, entry: ServerListEntry):
        column = self._state.sort_column
        if column == "name":
            return entry.name.lower()
        if column == "description":
            return entry.description.lower()
        if column == "game":
            return entry.game.lower()
        if column == "players":
            return (entry.player_count, entry.max_players, entry.name.lower())
        if column == "map":
            return entry.map_name.lower()
        if column == "last_played":
            return entry.last_played.lower()
        return (entry.latency_ms is None, entry.latency_ms or 9999, entry.name.lower())

    def _set_sort(self, column: str):
        state = self._state
        if state.sort_column == column:
            state.sort_desc = not state.sort_desc
        else:
            state.sort_column = column
            state.sort_desc = column in {"players", "last_played"}
        state.entries = self._filtered_entries(state.entries)
        self._clamp_selection()

    def _columns_for_tab(self, tab: str) -> tuple[tuple[str, str, float, float], ...]:
        if tab == "unique":
            return (
                ("name", "Servers", -9.55, -2.85),
                ("description", "Server description", -2.85, 4.75),
                ("game", "Game", 4.75, 6.4),
                ("players", "Players", 6.4, 7.25),
                ("map", "Map", 7.25, 8.55),
                ("latency", "Latency", 8.55, 9.55),
            )
        if tab == "history":
            return (
                ("name", "Servers", -9.55, 4.2),
                ("game", "Game", 4.2, 5.95),
                ("players", "Players", 5.95, 6.85),
                ("map", "Map", 6.85, 7.95),
                ("latency", "Latency", 7.95, 8.75),
                ("last_played", "Last played", 8.75, 9.55),
            )
        return (
            ("name", "Servers", -9.55, 4.75),
            ("game", "Game", 4.75, 6.4),
            ("players", "Players", 6.4, 7.25),
            ("map", "Map", 7.25, 8.55),
            ("latency", "Latency", 8.55, 9.55),
        )

    def _empty_message(self) -> str:
        state = self._state
        if not self._filters_are_default():
            return "No servers match the current filters."
        if state.tab == "history":
            return "No servers have been played recently."
        if state.tab == "favorites":
            return "No favorite servers have been added."
        if state.tab == "lan":
            return "No LAN games responded to the query."
        return "No internet games responded to the query."

    def _filters_are_default(self) -> bool:
        state = self._state
        return (
            not state.filter_text
            and state.show_full
            and state.show_empty
            and state.show_passworded
            and not state.secure_only
            and not state.region
            and state.max_latency is None
        )

    def _status_is_placeholder(self, status: str) -> bool:
        return not status or status.startswith("No ") or status.startswith("Searching ")

    def _clamp_selection(self):
        state = self._state
        if not state.entries:
            state.selected_index = 0
            state.scroll_index = 0
            return
        state.selected_index = max(0, min(state.selected_index, len(state.entries) - 1))
        max_scroll = max(0, len(state.entries) - self._max_rows)
        state.scroll_index = max(0, min(state.scroll_index, max_scroll))
        if state.selected_index < state.scroll_index:
            state.scroll_index = state.selected_index
        elif state.selected_index >= state.scroll_index + self._max_rows:
            state.scroll_index = state.selected_index - self._max_rows + 1

    def _scroll(self, rows: int):
        if not self._state.entries:
            return
        max_scroll = max(0, len(self._state.entries) - self._max_rows)
        self._state.scroll_index = max(0, min(max_scroll, self._state.scroll_index + rows))
        if self._state.selected_index < self._state.scroll_index:
            self._state.selected_index = self._state.scroll_index
        elif self._state.selected_index >= self._state.scroll_index + self._max_rows:
            self._state.selected_index = min(
                len(self._state.entries) - 1,
                self._state.scroll_index + self._max_rows - 1,
            )

    def _drag_scrollbar(self, rects, mouse_y: float):
        max_scroll = max(0, len(self._state.entries) - self._max_rows)
        thumb = rects.get("scroll_thumb") or self._scroll_thumb()
        if max_scroll <= 0:
            return
        track_top = 4.35
        track_bottom = -5.35
        thumb_height = thumb[1] - thumb[3]
        travel = max(0.0001, (track_top - track_bottom) - thumb_height)
        desired_top = max(track_bottom + thumb_height, min(track_top, mouse_y + self._state.drag_offset))
        self._state.scroll_index = max(0, min(max_scroll, int(round(((track_top - desired_top) / travel) * max_scroll))))
        self._clamp_selection()

    def _scroll_thumb(self) -> tuple[float, float, float, float]:
        max_scroll = max(0, len(self._state.entries) - self._max_rows)
        if max_scroll <= 0:
            return (9.57, 4.35, 9.73, -5.35)
        track_top = 4.35
        track_bottom = -5.35
        track_height = track_top - track_bottom
        visible_fraction = self._max_rows / max(1, len(self._state.entries))
        thumb_height = max(0.65, track_height * visible_fraction)
        travel = max(0.0, track_height - thumb_height)
        thumb_top = track_top - travel * (self._state.scroll_index / max_scroll)
        return (9.57, thumb_top, 9.73, thumb_top - thumb_height)

    def _select_endpoint(self, endpoint: str):
        for index, entry in enumerate(self._state.entries):
            if entry.endpoint == endpoint:
                self._state.selected_index = index
                self._clamp_selection()
                return

    def _cycle_tab(self):
        tabs = tuple(tab for tab, _label in self._tabs)
        current = tabs.index(self._state.tab) if self._state.tab in tabs else 0
        self._state.tab = tabs[(current + 1) % len(tabs)]
        self._state.show_all = False
        self._state.selected_index = 0
        self._state.scroll_index = 0

    def _draw_panel(self, left: float, top: float, right: float, bottom: float, fill):
        self._graphics.draw_world_rect(left, top, right, bottom, fill)

    def _draw_button(self, rect, label: str, *, enabled: bool):
        mouse_x, mouse_y = self._interface.get_mouse_pos()
        hovered = enabled and self._contains(rect, mouse_x, mouse_y)
        pressed = hovered and bool(self._interface.get_mouse_button(0))
        self._draw_panel(*rect, self._control_fill(enabled, hovered, pressed))
        self._ui.draw_centered_text(
            (rect[0] + rect[2]) / 2.0,
            rect[3] + 0.1,
            label,
            style=self._ui.style(
                0.22,
                self._bright_text if enabled else self._muted_text,
                spacing=0.09,
                shadow=enabled,
            ),
        )

    def _draw_text_field(self, rect, text: str, *, active: bool):
        self._draw_panel(*rect, self._input_fill if active else (0, 0, 0, 120))
        shown = self._shorten(text or "", max(8, int((rect[2] - rect[0]) * 6.0)))
        self._ui.draw_text(
            rect[0] + 0.15,
            rect[3] + 0.14,
            shown + ("_" if active else ""),
            style=self._ui.style(0.26, self._bright_text, spacing=0.1),
        )

    def _draw_checkbox(self, rect, checked: bool, label: str):
        self._draw_panel(*rect, self._input_fill)
        if checked:
            self._ui.draw_centered_text(
                (rect[0] + rect[2]) / 2.0,
                rect[3] + 0.08,
                "x",
                style=self._ui.style(0.3, self._gold_text, spacing=0.1),
            )
        self._ui.draw_text(
            rect[2] + 0.25,
            rect[3] + 0.1,
            label,
            style=self._ui.style(0.25, self._bright_text, spacing=0.1),
        )

    def _draw_radio_button(self, rect, label: str, *, checked: bool):
        mouse_x, mouse_y = self._interface.get_mouse_pos()
        hovered = self._contains(rect, mouse_x, mouse_y)
        fill = self._control_fill(True, hovered, hovered and bool(self._interface.get_mouse_button(0)))
        self._draw_panel(*rect, fill)
        mark = "(*)" if checked else "( )"
        self._ui.draw_text(
            rect[0] + 0.18,
            rect[3] + 0.14,
            f"{mark} {label}",
            style=self._ui.style(0.26, self._gold_text if checked else self._bright_text, spacing=0.1, shadow=True),
        )

    def _draw_resize_grip(self):
        x0, y0 = 9.52, -7.18
        for offset in (0.0, 0.12, 0.24):
            self._draw_panel(x0 + offset, y0 + 0.02, x0 + offset + 0.22, y0 - 0.03, (255, 255, 255, 170))

    def _control_fill(self, enabled: bool, hovered: bool, pressed: bool):
        if not enabled:
            return (35, 35, 35, 150)
        if pressed:
            return (112, 55, 0, 230)
        if hovered:
            return (190, 95, 0, 215)
        return self._brown_fill

    def _tab_fill(self, *, active: bool, hovered: bool, pressed: bool):
        if pressed:
            return (112, 55, 0, 230)
        if active:
            return (153, 76, 0, 210)
        if hovered:
            return (153, 76, 0, 165)
        return (0, 0, 0, 115)

    def _next_value(self, options, value):
        try:
            index = options.index(value)
        except ValueError:
            index = 0
        return options[(index + 1) % len(options)]

    def _latency_label(self) -> str:
        return "Any" if self._state.max_latency is None else f"{self._state.max_latency} ms"

    def _region_label(self) -> str:
        return "All regions" if not self._state.region else self._state.region.upper()

    def _append_printable(self, text: str, event, *, max_length: int) -> str:
        if len(text) >= max_length:
            return text
        character = getattr(event, "unicode", "")
        if isinstance(character, str) and len(character) == 1 and 32 <= ord(character) <= 126:
            return text + character
        return text

    def _is_key(self, key: int, key_names: dict[str, int], name: str) -> bool:
        return key_names.get(name) == key

    def _contains(self, rect: tuple[float, float, float, float] | None, x: float, y: float) -> bool:
        if rect is None:
            return False
        left, top, right, bottom = rect
        return left <= x <= right and bottom <= y <= top

    def _shorten(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[: max(1, max_chars - 1)] + "..."
