from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import pygame


Rect = Tuple[int, int, int, int]


def _pygame_const(name: str, fallback: int) -> int:
    value = getattr(pygame, name, fallback)
    if value == 0:
        return fallback
    return value


_MOUSEBUTTONDOWN = getattr(pygame, "MOUSEBUTTONDOWN", 1025)
_MOUSEWHEEL = getattr(pygame, "MOUSEWHEEL", 1027)
_VIDEORESIZE = getattr(pygame, "VIDEORESIZE", 32769)
_KEYDOWN = getattr(pygame, "KEYDOWN", 768)
_K_UP = _pygame_const("K_UP", 273)
_K_DOWN = _pygame_const("K_DOWN", 274)
_K_RETURN = _pygame_const("K_RETURN", 13)
_K_TAB = _pygame_const("K_TAB", 9)


@dataclass(frozen=True)
class ServerBrowserEntry:
    server_id: str
    name: str
    game: str
    players: int
    max_players: int
    map_name: str
    latency: int
    favorite: bool = False
    has_history: bool = False
    lan: bool = False
    friends_online: int = 0
    spectate: bool = False

    @property
    def players_label(self) -> str:
        return f"{self.players}/{self.max_players}"


@dataclass(frozen=True)
class ServerBrowserAction:
    kind: str
    value: Optional[str] = None


class _FallbackFont:
    def __init__(self, size: int):
        self._size = max(8, int(size))

    def render(self, text: str, _antialias: bool, _colour):
        width = max(1, int(len(text) * self._size * 0.52))
        return pygame.Surface((width, self._size + 4), pygame.SRCALPHA)


class ServerBrowserUI:
    SKY_TOP = (65, 118, 178)
    SKY_BOTTOM = (102, 179, 230)
    STREAK_GOLD = (224, 199, 68)
    STREAK_BROWN = (153, 76, 0)
    DIAGONAL = (56, 97, 143)
    PANEL = (133, 82, 28)
    PANEL_ALT = (112, 67, 20)
    PANEL_LIGHT = (214, 166, 104)
    PANEL_DARK = (66, 34, 10)
    TEXT = (247, 238, 223)
    TEXT_DIM = (224, 208, 186)
    ACCENT = (255, 209, 112)
    DISABLED = (168, 146, 122)

    TABS = ("Internet", "Favorites", "History", "Spectate", "Lan", "Friends")
    EMPTY_MESSAGES = {
        "Internet": "There are no internet games listed on the master server that pass your filter settings.",
        "Favorites": "No favorite servers have been added yet.",
        "History": "You have not connected to any online matches yet.",
        "Spectate": "No servers are currently exposing a spectator slot.",
        "Lan": "No LAN servers were discovered on your local network.",
        "Friends": "No friends are currently playing online.",
    }

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        title: str = "Servers",
        servers: Optional[Sequence[ServerBrowserEntry]] = None,
    ):
        self._width = max(640, int(width))
        self._height = max(420, int(height))
        self._title = title
        self._active_tab = "Internet"
        self._servers: List[ServerBrowserEntry] = list(servers or [])
        self._selected_server_id: Optional[str] = None
        self._scroll_offset = 0
        self._hovered_server_id: Optional[str] = None
        self._status_message = ""
        self._status_timeout = 0.0
        self._animation_time = 0.0
        self._last_action: Optional[ServerBrowserAction] = None
        self._font_cache: Dict[Tuple[int, bool], object] = {}
        self._reconcile_selection()

    def resize(self, width: int, height: int) -> None:
        self._width = max(640, int(width))
        self._height = max(420, int(height))
        self._clamp_scroll()

    def update(self, dt: float) -> None:
        self._animation_time += max(0.0, dt)
        if self._status_timeout > 0.0:
            self._status_timeout = max(0.0, self._status_timeout - max(0.0, dt))
            if self._status_timeout == 0.0:
                self._status_message = ""

    def draw(self, surface) -> None:
        self._draw_background(surface)
        layout = self.get_layout_snapshot()
        self._draw_window(surface, layout)
        self._draw_title_bar(surface, layout)
        self._draw_tabs(surface, layout)
        self._draw_server_table(surface, layout)
        self._draw_footer(surface, layout)

    def draw_to_interface(self, interface) -> None:
        width, height, _fullscreen = interface.get_window_settings()
        self.resize(width, height)
        self.draw(interface._window)

    def set_servers(self, servers: Sequence[ServerBrowserEntry]) -> None:
        self._servers = list(servers)
        self._scroll_offset = 0
        self._reconcile_selection()

    def get_servers(self) -> List[ServerBrowserEntry]:
        return list(self._servers)

    def get_visible_servers(self) -> List[ServerBrowserEntry]:
        if self._active_tab == "Internet":
            return [server for server in self._servers if not server.lan]
        if self._active_tab == "Favorites":
            return [server for server in self._servers if server.favorite]
        if self._active_tab == "History":
            return [server for server in self._servers if server.has_history]
        if self._active_tab == "Spectate":
            return [server for server in self._servers if server.spectate]
        if self._active_tab == "Lan":
            return [server for server in self._servers if server.lan]
        if self._active_tab == "Friends":
            return [server for server in self._servers if server.friends_online > 0]
        return list(self._servers)

    def get_selected_server(self) -> Optional[ServerBrowserEntry]:
        for server in self.get_visible_servers():
            if server.server_id == self._selected_server_id:
                return server
        return None

    def get_active_tab(self) -> str:
        return self._active_tab

    def get_last_action(self) -> Optional[ServerBrowserAction]:
        return self._last_action

    def set_status_message(self, message: str, duration: float = 2.8) -> None:
        self._status_message = message
        self._status_timeout = max(0.0, duration)

    def activate_tab(self, tab_name: str) -> Optional[ServerBrowserAction]:
        if tab_name not in self.TABS or tab_name == self._active_tab:
            return None

        self._active_tab = tab_name
        self._scroll_offset = 0
        self._reconcile_selection()
        action = ServerBrowserAction("tab_changed", tab_name)
        self._last_action = action
        self.set_status_message(f"Switched to {tab_name}.", 1.4)
        return action

    def select_server(self, server_id: Optional[str]) -> Optional[ServerBrowserAction]:
        if server_id is None:
            self._selected_server_id = None
            return None

        for server in self.get_visible_servers():
            if server.server_id == server_id:
                self._selected_server_id = server_id
                action = ServerBrowserAction("server_selected", server_id)
                self._last_action = action
                self.set_status_message(
                    f"Selected {server.name} on {server.map_name} ({server.latency} ms).",
                    2.0,
                )
                return action
        return None

    def trigger_button(self, button_name: str) -> Optional[ServerBrowserAction]:
        action: Optional[ServerBrowserAction] = None

        if button_name == "Change filters":
            action = ServerBrowserAction("open_filters")
            self.set_status_message("Filter panel placeholder. Wire this to your online options later.")
        elif button_name == "Quick refresh":
            action = ServerBrowserAction("quick_refresh", self._active_tab)
            self.set_status_message(f"Refreshing visible servers in {self._active_tab.lower()}...")
        elif button_name == "Refresh all":
            action = ServerBrowserAction("refresh_all")
            self.set_status_message("Refreshing the full online server list...")
        elif button_name == "Connect":
            selected = self.get_selected_server()
            if selected is None:
                self.set_status_message("Select a server before connecting.", 1.8)
                return None
            action = ServerBrowserAction("connect", selected.server_id)
            self.set_status_message(f"Prepared connection to {selected.name}.")

        self._last_action = action
        return action

    def handle_event(self, event) -> Optional[ServerBrowserAction]:
        event_type = getattr(event, "type", None)
        if event_type == _VIDEORESIZE:
            self.resize(getattr(event, "w", self._width), getattr(event, "h", self._height))
            return None

        if event_type == _KEYDOWN:
            return self._handle_key_event(event)

        if event_type == _MOUSEWHEEL:
            self._scroll_offset -= int(getattr(event, "y", 0))
            self._clamp_scroll()
            return None

        if event_type != _MOUSEBUTTONDOWN:
            return None

        pos = getattr(event, "pos", None)
        button = getattr(event, "button", 1)
        if pos is None:
            return None

        if button == 4:
            self._scroll_offset -= 1
            self._clamp_scroll()
            return None
        if button == 5:
            self._scroll_offset += 1
            self._clamp_scroll()
            return None
        if button != 1:
            return None

        layout = self.get_layout_snapshot()

        if self._point_in_rect(pos, layout["close_button"]):
            action = ServerBrowserAction("close")
            self._last_action = action
            return action

        for tab_name, tab_rect in layout["tabs"].items():
            if self._point_in_rect(pos, tab_rect):
                return self.activate_tab(tab_name)

        for row in layout["rows"]:
            if self._point_in_rect(pos, row["rect"]):
                return self.select_server(row["server_id"])

        for button_name, button_rect in layout["buttons"].items():
            if self._point_in_rect(pos, button_rect):
                return self.trigger_button(button_name)

        return None

    def get_layout_snapshot(self) -> Dict[str, object]:
        width = self._width
        height = self._height
        margin_x = max(48, int(width * 0.065))
        margin_y = max(28, int(height * 0.06))
        window = self._rect(margin_x, margin_y, width - margin_x * 2, height - margin_y * 2)
        x, y, w, h = window

        title_bar = self._rect(x + 10, y + 10, w - 20, 30)
        close_button = self._rect(x + w - 32, y + 16, 18, 18)
        tabs_top = title_bar[1] + title_bar[3] + 10
        tab_widths = (84, 86, 74, 92, 68, 76)
        tabs: Dict[str, Rect] = {}
        tab_x = x + 12
        for tab_name, tab_width in zip(self.TABS, tab_widths):
            tabs[tab_name] = self._rect(tab_x, tabs_top, tab_width, 28)
            tab_x += tab_width - 2

        list_x = x + 10
        list_y = tabs_top + 34
        list_w = w - 20
        footer_h = 46
        header_h = 24
        body_h = max(120, h - (list_y - y) - footer_h - 20 - header_h)
        table_header = self._rect(list_x, list_y, list_w, header_h)
        table_body = self._rect(list_x, list_y + header_h, list_w, body_h)
        footer = self._rect(x + 10, y + h - footer_h - 10, w - 20, footer_h)

        visible_servers = self.get_visible_servers()
        row_height = 24
        max_rows = max(1, table_body[3] // row_height)
        rows: List[Dict[str, object]] = []
        self._clamp_scroll(max_rows)
        start_index = self._scroll_offset
        end_index = min(len(visible_servers), start_index + max_rows)
        for index, server in enumerate(visible_servers[start_index:end_index]):
            row_y = table_body[1] + index * row_height
            rows.append(
                {
                    "rect": self._rect(table_body[0] + 1, row_y + 1, table_body[2] - 14, row_height - 2),
                    "server_id": server.server_id,
                }
            )

        buttons: Dict[str, Rect] = {}
        left_button = self._rect(footer[0] + 8, footer[1] + 8, 138, 28)
        buttons["Change filters"] = left_button

        right_cursor = footer[0] + footer[2] - 8
        for button_name, button_width in (("Connect", 88), ("Refresh all", 102), ("Quick refresh", 106)):
            right_cursor -= button_width
            buttons[button_name] = self._rect(right_cursor, footer[1] + 8, button_width, 28)
            right_cursor -= 8

        status_rect = self._rect(left_button[0] + left_button[2] + 12, footer[1] + 7, right_cursor - (left_button[0] + left_button[2] + 18), 30)

        column_x = table_header[0]
        column_widths = (
            int(table_header[2] * 0.58),
            int(table_header[2] * 0.09),
            int(table_header[2] * 0.08),
            int(table_header[2] * 0.15),
            table_header[2] - int(table_header[2] * 0.58) - int(table_header[2] * 0.09) - int(table_header[2] * 0.08) - int(table_header[2] * 0.15),
        )
        columns = []
        labels = ("Servers", "Game", "Players", "Map", "Latency")
        for label, col_width in zip(labels, column_widths):
            columns.append({"label": label, "rect": self._rect(column_x, table_header[1], col_width, table_header[3])})
            column_x += col_width

        scrollbar = self._rect(table_body[0] + table_body[2] - 12, table_body[1], 12, table_body[3])

        return {
            "window": window,
            "title_bar": title_bar,
            "close_button": close_button,
            "tabs": tabs,
            "table_header": table_header,
            "table_body": table_body,
            "footer": footer,
            "buttons": buttons,
            "status_rect": status_rect,
            "rows": rows,
            "columns": columns,
            "scrollbar": scrollbar,
            "row_height": row_height,
            "max_rows": max_rows,
        }

    def _handle_key_event(self, event) -> Optional[ServerBrowserAction]:
        key = getattr(event, "key", None)
        visible_servers = self.get_visible_servers()
        if not visible_servers:
            return None

        selected_index = next(
            (index for index, server in enumerate(visible_servers) if server.server_id == self._selected_server_id),
            -1,
        )

        if key == _K_DOWN:
            selected_index = min(len(visible_servers) - 1, selected_index + 1)
            action = self.select_server(visible_servers[selected_index].server_id)
            self._ensure_selected_visible()
            return action

        if key == _K_UP:
            if selected_index == -1:
                selected_index = 0
            else:
                selected_index = max(0, selected_index - 1)
            action = self.select_server(visible_servers[selected_index].server_id)
            self._ensure_selected_visible()
            return action

        if key == _K_RETURN:
            return self.trigger_button("Connect")

        if key == _K_TAB:
            current_index = self.TABS.index(self._active_tab)
            next_tab = self.TABS[(current_index + 1) % len(self.TABS)]
            return self.activate_tab(next_tab)

        return None

    def _draw_background(self, surface) -> None:
        width, height = surface.get_size()
        surface.fill(self.SKY_TOP)

        for y in range(0, height, 2):
            blend = y / max(1, height)
            row_colour = (
                int(self.SKY_TOP[0] + (self.SKY_BOTTOM[0] - self.SKY_TOP[0]) * blend),
                int(self.SKY_TOP[1] + (self.SKY_BOTTOM[1] - self.SKY_TOP[1]) * blend),
                int(self.SKY_TOP[2] + (self.SKY_BOTTOM[2] - self.SKY_TOP[2]) * blend),
            )
            pygame.draw.line(surface, row_colour, (0, y), (width, y))

        beam_1 = [
            (0, int(height * 0.18)),
            (int(width * 0.24), int(height * 0.20)),
            (int(width * 0.19), int(height * 0.32)),
            (0, int(height * 0.30)),
        ]
        beam_2 = [
            (0, int(height * 0.82)),
            (int(width * 0.52), int(height * 0.80)),
            (int(width * 0.56), int(height * 0.86)),
            (0, int(height * 0.88)),
        ]
        pygame.draw.polygon(surface, self.STREAK_GOLD, beam_1)
        pygame.draw.polygon(surface, self.STREAK_BROWN, beam_2)

        for offset in range(-height, width, 40):
            start = (offset, height)
            end = (offset + int(height * 0.55), 0)
            pygame.draw.line(surface, self.DIAGONAL, start, end)

        watermark_rect = self._rect(int(width * 0.58), 12, int(width * 0.38), 86)
        self._draw_text(surface, "GROUNDFIRE ONLINE", watermark_rect, 54, self.TEXT, align="topleft")

    def _draw_window(self, surface, layout: Dict[str, object]) -> None:
        x, y, w, h = layout["window"]
        window_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        window_surface.fill((133, 82, 28, 224))
        surface.blit(window_surface, (x, y))
        self._draw_bevel_rect(surface, layout["window"], self.PANEL, self.PANEL_LIGHT, self.PANEL_DARK, outline=(49, 25, 7))

    def _draw_title_bar(self, surface, layout: Dict[str, object]) -> None:
        self._draw_bevel_rect(surface, layout["title_bar"], self.PANEL_ALT, self.PANEL_LIGHT, self.PANEL_DARK)
        x, y, _w, h = layout["title_bar"]
        icon_rect = self._rect(x + 8, y + 7, 14, 14)
        pygame.draw.rect(surface, self.TEXT, icon_rect, 1)
        pygame.draw.line(surface, self.TEXT, (icon_rect[0] + 3, icon_rect[1] + 7), (icon_rect[0] + 11, icon_rect[1] + 7))
        pygame.draw.line(surface, self.TEXT, (icon_rect[0] + 7, icon_rect[1] + 3), (icon_rect[0] + 7, icon_rect[1] + 11))
        self._draw_text(surface, self._title, self._rect(x + 28, y + 4, 180, h), 21, self.TEXT, bold=False)
        close_rect = layout["close_button"]
        self._draw_bevel_rect(surface, close_rect, self.PANEL, self.PANEL_LIGHT, self.PANEL_DARK)
        self._draw_text(surface, "x", close_rect, 18, self.TEXT, align="center")

    def _draw_tabs(self, surface, layout: Dict[str, object]) -> None:
        for tab_name, tab_rect in layout["tabs"].items():
            is_active = tab_name == self._active_tab
            fill = self.PANEL_ALT if is_active else self.PANEL
            light = self.ACCENT if is_active else self.PANEL_LIGHT
            dark = self.PANEL_DARK
            self._draw_bevel_rect(surface, tab_rect, fill, light, dark)
            text_colour = self.TEXT if is_active else self.TEXT_DIM
            self._draw_text(surface, tab_name, tab_rect, 18, text_colour, align="center")

    def _draw_server_table(self, surface, layout: Dict[str, object]) -> None:
        self._draw_bevel_rect(surface, layout["table_header"], self.PANEL_ALT, self.PANEL_LIGHT, self.PANEL_DARK)
        body_surface = pygame.Surface((layout["table_body"][2], layout["table_body"][3]), pygame.SRCALPHA)
        body_surface.fill((102, 60, 18, 202))
        surface.blit(body_surface, (layout["table_body"][0], layout["table_body"][1]))
        self._draw_bevel_rect(surface, layout["table_body"], self.PANEL, self.PANEL_LIGHT, self.PANEL_DARK)

        for column in layout["columns"]:
            rect = column["rect"]
            pygame.draw.line(
                surface,
                self.PANEL_LIGHT,
                (rect[0], rect[1] + rect[3] - 1),
                (rect[0] + rect[2], rect[1] + rect[3] - 1),
            )
            self._draw_text(surface, column["label"], self._rect(rect[0] + 6, rect[1] + 2, rect[2] - 10, rect[3]), 17, self.TEXT)

        visible_servers = self.get_visible_servers()
        columns = layout["columns"]
        start_index = self._scroll_offset
        selected = self.get_selected_server()

        if not visible_servers:
            self._draw_text(
                surface,
                self.EMPTY_MESSAGES[self._active_tab],
                self._rect(layout["table_body"][0] + 8, layout["table_body"][1] + 8, layout["table_body"][2] - 24, 24),
                19,
                self.TEXT_DIM,
            )
        else:
            for row_index, row in enumerate(layout["rows"]):
                server = visible_servers[start_index + row_index]
                row_rect = row["rect"]
                selected_row = selected is not None and selected.server_id == server.server_id
                fill = (175, 108, 31) if selected_row else (self.PANEL_ALT if row_index % 2 == 0 else self.PANEL)
                light = self.ACCENT if selected_row else self.PANEL_LIGHT
                dark = self.PANEL_DARK
                self._draw_bevel_rect(surface, row_rect, fill, light, dark)

                labels = (
                    server.name,
                    server.game,
                    server.players_label,
                    server.map_name,
                    f"{server.latency} ms",
                )
                for column, label in zip(columns, labels):
                    padding = 8 if column["label"] in ("Servers", "Map") else 6
                    self._draw_text(
                        surface,
                        label,
                        self._rect(column["rect"][0] + padding, row_rect[1] + 2, column["rect"][2] - padding * 2, row_rect[3]),
                        17,
                        self.TEXT,
                    )

        self._draw_scrollbar(surface, layout, len(visible_servers))

    def _draw_scrollbar(self, surface, layout: Dict[str, object], total_rows: int) -> None:
        self._draw_bevel_rect(surface, layout["scrollbar"], self.PANEL, self.PANEL_LIGHT, self.PANEL_DARK)
        max_rows = max(1, int(layout["max_rows"]))
        if total_rows <= max_rows:
            thumb_h = layout["scrollbar"][3] - 8
            thumb_y = layout["scrollbar"][1] + 4
        else:
            ratio = max_rows / float(total_rows)
            thumb_h = max(22, int((layout["scrollbar"][3] - 8) * ratio))
            track = layout["scrollbar"][3] - thumb_h - 8
            offset_ratio = self._scroll_offset / float(total_rows - max_rows)
            thumb_y = layout["scrollbar"][1] + 4 + int(track * offset_ratio)

        thumb = self._rect(layout["scrollbar"][0] + 2, thumb_y, layout["scrollbar"][2] - 4, thumb_h)
        self._draw_bevel_rect(surface, thumb, self.PANEL_ALT, self.ACCENT, self.PANEL_DARK)

    def _draw_footer(self, surface, layout: Dict[str, object]) -> None:
        self._draw_bevel_rect(surface, layout["footer"], self.PANEL_ALT, self.PANEL_LIGHT, self.PANEL_DARK)

        for button_name, button_rect in layout["buttons"].items():
            is_disabled = button_name == "Connect" and self.get_selected_server() is None
            fill = self.PANEL_ALT if not is_disabled else self.PANEL
            light = self.ACCENT if not is_disabled else self.PANEL_LIGHT
            dark = self.PANEL_DARK
            self._draw_bevel_rect(surface, button_rect, fill, light, dark)
            colour = self.TEXT if not is_disabled else self.DISABLED
            self._draw_text(surface, button_name, button_rect, 18, colour, align="center")

        self._draw_text(surface, "Groundfire", layout["status_rect"], 18, self.ACCENT)
        status = self._compose_status_text()
        status_rect = self._rect(layout["status_rect"][0] + 100, layout["status_rect"][1], layout["status_rect"][2] - 100, layout["status_rect"][3])
        self._draw_text(surface, status, status_rect, 17, self.TEXT_DIM)

    def _compose_status_text(self) -> str:
        if self._status_message:
            return self._status_message

        selected = self.get_selected_server()
        if selected is not None:
            return f"{selected.players_label} players on {selected.map_name} | {selected.latency} ms"

        visible = self.get_visible_servers()
        if not visible:
            return self.EMPTY_MESSAGES[self._active_tab]

        return f"{len(visible)} servers ready for browsing in {self._active_tab.lower()}."

    def _reconcile_selection(self) -> None:
        if self.get_selected_server() is None:
            self._selected_server_id = None
        self._clamp_scroll()

    def _ensure_selected_visible(self) -> None:
        visible_servers = self.get_visible_servers()
        if not visible_servers or self._selected_server_id is None:
            return

        layout = self.get_layout_snapshot()
        max_rows = max(1, int(layout["max_rows"]))
        selected_index = next(
            (index for index, server in enumerate(visible_servers) if server.server_id == self._selected_server_id),
            0,
        )
        if selected_index < self._scroll_offset:
            self._scroll_offset = selected_index
        elif selected_index >= self._scroll_offset + max_rows:
            self._scroll_offset = selected_index - max_rows + 1
        self._clamp_scroll(max_rows)

    def _clamp_scroll(self, max_rows: Optional[int] = None) -> None:
        visible_count = len(self.get_visible_servers())
        if max_rows is None:
            table_body_height = self.get_layout_snapshot()["table_body"][3]
            max_rows = max(1, table_body_height // 24)
        self._scroll_offset = max(0, min(self._scroll_offset, max(0, visible_count - max_rows)))

    def _draw_bevel_rect(self, surface, rect: Rect, fill, light, dark, outline=None) -> None:
        x, y, w, h = rect
        pygame.draw.rect(surface, fill, rect)
        pygame.draw.line(surface, light, (x, y), (x + w - 1, y))
        pygame.draw.line(surface, light, (x, y), (x, y + h - 1))
        pygame.draw.line(surface, dark, (x, y + h - 1), (x + w - 1, y + h - 1))
        pygame.draw.line(surface, dark, (x + w - 1, y), (x + w - 1, y + h - 1))
        if outline is not None:
            pygame.draw.rect(surface, outline, rect, 1)

    def _draw_text(self, surface, text: str, rect: Rect, size: int, colour, align: str = "topleft", bold: bool = False) -> None:
        text_surface = self._render_text(text, size, colour, bold=bold)
        text_width, text_height = text_surface.get_size()
        x, y, w, h = rect

        if align == "center":
            draw_x = x + (w - text_width) // 2
            draw_y = y + (h - text_height) // 2
        elif align == "topright":
            draw_x = x + w - text_width
            draw_y = y
        else:
            draw_x = x
            draw_y = y + max(0, (h - text_height) // 2)

        surface.blit(text_surface, (draw_x, draw_y))

    def _render_text(self, text: str, size: int, colour, bold: bool = False):
        font_module = getattr(pygame, "font", None)
        if font_module is None:
            return _FallbackFont(size).render(text, True, colour)

        try:
            if hasattr(font_module, "get_init") and hasattr(font_module, "init") and not font_module.get_init():
                font_module.init()
            cache_key = (int(size), bool(bold))
            font = self._font_cache.get(cache_key)
            if font is None:
                if hasattr(font_module, "SysFont"):
                    font = font_module.SysFont("Tahoma", int(size), bold=bold)
                elif hasattr(font_module, "Font"):
                    font = font_module.Font(None, int(size))
                else:
                    font = _FallbackFont(size)
                self._font_cache[cache_key] = font
            return font.render(text, True, colour)
        except Exception:
            return _FallbackFont(size).render(text, True, colour)

    @staticmethod
    def _point_in_rect(point: Tuple[int, int], rect: Rect) -> bool:
        px, py = point
        x, y, w, h = rect
        return x <= px < x + w and y <= py < y + h

    @staticmethod
    def _rect(x: int, y: int, w: int, h: int) -> Rect:
        return (int(x), int(y), max(1, int(w)), max(1, int(h)))


def run_server_browser_demo(window_size: Tuple[int, int] = (1366, 768)) -> int:
    pygame.init()
    if hasattr(pygame, "font") and hasattr(pygame.font, "init"):
        pygame.font.init()

    flags = getattr(pygame, "RESIZABLE", 0)
    window = pygame.display.set_mode(window_size, flags)
    pygame.display.set_caption("Groundfire Online Browser Preview")

    browser = ServerBrowserUI(window_size[0], window_size[1])
    clock = pygame.time.Clock() if hasattr(pygame, "time") and hasattr(pygame.time, "Clock") else None
    running = True

    while running:
        dt = 1.0 / 60.0
        if clock is not None:
            dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if getattr(event, "type", None) == getattr(pygame, "QUIT", 256):
                running = False
                continue
            browser.handle_event(event)

        browser.update(dt)
        browser.draw(window)
        pygame.display.flip()

    pygame.quit()
    return 0
