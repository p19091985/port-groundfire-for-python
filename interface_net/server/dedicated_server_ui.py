from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple

import pygame

from .lan_server import DedicatedLanServer
from .theme import (
    GROUND_ACCENT,
    GROUND_DISABLED,
    GROUND_PANEL,
    GROUND_PANEL_ALT,
    GROUND_PANEL_DARK,
    GROUND_PANEL_LIGHT,
    GROUND_TEXT,
    GROUND_TEXT_DIM,
    draw_bevel_rect,
    draw_text,
    paint_dedicated_server_background,
    point_in_rect,
    pygame_const,
    rect,
)


Rect = Tuple[int, int, int, int]

_MOUSEBUTTONDOWN = pygame_const("MOUSEBUTTONDOWN", 1025)
_VIDEORESIZE = pygame_const("VIDEORESIZE", 32769)
_KEYDOWN = pygame_const("KEYDOWN", 768)
_K_RETURN = pygame_const("K_RETURN", 13)
_K_ESCAPE = pygame_const("K_ESCAPE", 27)
_K_BACKSPACE = pygame_const("K_BACKSPACE", 8)
_K_DELETE = pygame_const("K_DELETE", 127)
_K_TAB = pygame_const("K_TAB", 9)


@dataclass(frozen=True)
class ServerLaunchSettings:
    game: str = "Groundfire"
    server_name: str = "Groundfire Dedicated"
    map_name: str = "Canyon"
    network: str = "Lan"
    max_players: int = 12
    rounds: int = 10
    udp_port: str = "27016"
    rcon_password: str = ""
    secure: bool = True


@dataclass(frozen=True)
class DedicatedServerAction:
    kind: str
    value: Optional[str] = None


class DedicatedServerUI:
    PANEL_TABS = ("Main", "Configure", "Statistics", "Players", "Bans", "Console")
    GAME_OPTIONS = ("Groundfire", "Groundfire Classic", "Groundfire Test")
    MAP_OPTIONS = ("Canyon", "Depot", "Quarry", "Night Ridge", "Dust Basin")
    NETWORK_OPTIONS = ("Lan",)
    PLAYER_OPTIONS = (4, 8, 12, 16)
    ROUND_OPTIONS = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50)

    def __init__(
        self,
        width: int = 1024,
        height: int = 720,
        settings: Optional[ServerLaunchSettings] = None,
    ):
        self._width = max(700, int(width))
        self._height = max(520, int(height))
        self._settings = settings or ServerLaunchSettings()
        self._mode = "create"
        self._active_panel_tab = "Main"
        self._font_cache: Dict[Tuple[int, bool], object] = {}
        self._focused_field: Optional[str] = None
        self._server_running = False
        self._players_connected = 0
        self._uptime_seconds = 0.0
        self._status_message = "Configure your dedicated server."
        self._status_timeout = 0.0
        self._last_action: Optional[DedicatedServerAction] = None
        self._lan_server: Optional[DedicatedLanServer] = None
        self._lobby_state = "waiting"
        self._countdown_seconds_remaining = 0
        self._player_names: List[str] = []
        self._server_address = "127.0.0.1"
        self._console_lines: List[str] = [
            "Server console ready.",
            "No active session running.",
        ]
        self._config_values = {
            "Time limit": "30",
            "Win limit (rounds)": "0",
            "Round limit (rounds)": "0",
            "Time per round (minutes)": "5",
            "Freeze time (seconds)": "0",
            "Buy time (minutes)": "1.5",
            "Starting money": "800",
            "Footsteps": "Enabled",
            "Death camera type": "Spectate anyone",
            "Disable chase/death cam (fade to black)": "Disabled",
            "Friendly fire": "Disabled",
            "Kill team killers round after TK": "Disabled",
            "Kick idle and team killing players (3 TKs)": "Enabled",
            "Kick hostage killers (kills allowed, 0 is off)": "13",
            "Allow flashlight": "Enabled",
        }

    def resize(self, width: int, height: int) -> None:
        self._width = max(700, int(width))
        self._height = max(520, int(height))

    def update(self, dt: float) -> None:
        if self._server_running:
            self._uptime_seconds += max(0.0, dt)
            self._sync_server_runtime()

        if self._status_timeout > 0.0:
            self._status_timeout = max(0.0, self._status_timeout - max(0.0, dt))
            if self._status_timeout == 0.0:
                self._status_message = ""

    def draw(self, surface) -> None:
        paint_dedicated_server_background(surface)
        if self._mode == "create":
            self._draw_create_mode(surface)
        else:
            self._draw_panel_mode(surface)

    def draw_to_interface(self, interface) -> None:
        width, height, _fullscreen = interface.get_window_settings()
        self.resize(width, height)
        self.draw(interface._window)

    def handle_event(self, event) -> Optional[DedicatedServerAction]:
        event_type = getattr(event, "type", None)
        if event_type == _VIDEORESIZE:
            self.resize(getattr(event, "w", self._width), getattr(event, "h", self._height))
            return None

        if self._mode == "create":
            return self._handle_create_event(event)
        return self._handle_panel_event(event)

    def get_mode(self) -> str:
        return self._mode

    def is_server_running(self) -> bool:
        return self._server_running

    def get_active_panel_tab(self) -> str:
        return self._active_panel_tab

    def get_settings(self) -> ServerLaunchSettings:
        return replace(self._settings)

    def get_last_action(self) -> Optional[DedicatedServerAction]:
        return self._last_action

    def open_control_panel(self) -> DedicatedServerAction:
        self._mode = "panel"
        self._active_panel_tab = "Main"
        self._focused_field = None
        if self._server_running:
            self._status_message = f"{self._settings.server_name} is online."
        else:
            self._status_message = "Server configured. Click Start to bring it online."
        self._status_timeout = 2.0
        action = DedicatedServerAction("open_panel")
        self._last_action = action
        return action

    def shutdown(self) -> None:
        if self._lan_server is not None:
            self._lan_server.stop()
            self._lan_server = None
        self._server_running = False
        self._players_connected = 0
        self._lobby_state = "offline"
        self._countdown_seconds_remaining = 0
        self._player_names = []
        self._server_address = "Offline"

    def get_layout_snapshot(self) -> Dict[str, object]:
        if self._mode == "create":
            return self._create_layout()
        return self._panel_layout()

    def start_server(self) -> DedicatedServerAction:
        if self._server_running:
            self._status_message = "Server is already online."
            self._status_timeout = 1.6
            action = DedicatedServerAction("start_server", self._settings.server_name)
            self._last_action = action
            return action

        udp_port = "".join(ch for ch in self._settings.udp_port if ch.isdigit()) or "27016"
        if self._lan_server is not None:
            self._lan_server.stop()
            self._lan_server = None

        self._settings = replace(
            self._settings,
            server_name=self._settings.server_name.strip() or "Groundfire Dedicated",
            udp_port=udp_port[:5],
        )
        self._console_lines = []
        self._lan_server = DedicatedLanServer(
            host="0.0.0.0",
            port=int(self._settings.udp_port),
            server_name=self._settings.server_name,
            map_name=self._settings.map_name,
            max_players=self._settings.max_players,
            secure=self._settings.secure,
            rounds=self._settings.rounds,
            network=self._settings.network,
            log_callback=self._append_console_line,
        )
        self._lan_server.start()
        self._server_running = True
        self._mode = "panel"
        self._active_panel_tab = "Main"
        self._focused_field = None
        self._uptime_seconds = 0.0
        self._append_console_line(f"Server log file: {self._lan_server.get_log_path()}")
        self._players_connected = 0
        self._status_message = f"{self._settings.server_name} started successfully."
        self._status_timeout = 3.0
        self._sync_server_runtime()
        action = DedicatedServerAction("start_server", self._settings.server_name)
        self._last_action = action
        return action

    def restart_server(self) -> DedicatedServerAction:
        if self._lan_server is not None:
            self._lan_server.stop()
            self._lan_server = None
        self._server_running = False
        self._players_connected = 0
        self._lobby_state = "offline"
        self._countdown_seconds_remaining = 0
        self._player_names = []
        self._server_address = "Offline"
        self.start_server()
        self._console_lines.append("Restart completed. Dedicated server recycled successfully.")
        self._status_message = f"{self._settings.server_name} restarted successfully."
        self._status_timeout = 2.4
        action = DedicatedServerAction("restart_server", self._settings.server_name)
        self._last_action = action
        return action

    def stop_server(self) -> DedicatedServerAction:
        if self._lan_server is not None:
            self._lan_server.stop()
            self._lan_server = None
        self._server_running = False
        self._players_connected = 0
        self._uptime_seconds = 0.0
        self._lobby_state = "offline"
        self._countdown_seconds_remaining = 0
        self._player_names = []
        self._server_address = "Offline"
        self._mode = "panel"
        self._active_panel_tab = "Main"
        self._append_console_line("Dedicated server stopped. Click Start to host again.")
        self._status_message = "Server stopped."
        self._status_timeout = 1.8
        action = DedicatedServerAction("stop_server", self._settings.server_name)
        self._last_action = action
        return action

    def _append_console_line(self, line: str) -> None:
        normalized = str(line).strip()
        if not normalized:
            return
        self._console_lines.append(normalized)
        if len(self._console_lines) > 80:
            self._console_lines = self._console_lines[-80:]

    def _handle_create_event(self, event) -> Optional[DedicatedServerAction]:
        event_type = getattr(event, "type", None)
        if event_type == _KEYDOWN:
            return self._handle_create_key(event)

        if event_type != _MOUSEBUTTONDOWN:
            return None

        pos = getattr(event, "pos", None)
        button = getattr(event, "button", 1)
        if pos is None or button != 1:
            return None

        layout = self._create_layout()
        self._focused_field = None

        for field_name in ("game", "map_name", "network", "max_players", "rounds"):
            if point_in_rect(pos, layout["fields"][field_name]):
                return self._cycle_field(field_name)

        for field_name in ("server_name", "udp_port", "rcon_password"):
            if point_in_rect(pos, layout["fields"][field_name]):
                self._focused_field = field_name
                return None

        if point_in_rect(pos, layout["checkbox"]):
            self._settings = replace(self._settings, secure=not self._settings.secure)
            self._status_message = "Secure mode enabled." if self._settings.secure else "Secure mode disabled."
            self._status_timeout = 1.5
            action = DedicatedServerAction("toggle_secure", str(self._settings.secure))
            self._last_action = action
            return action

        if point_in_rect(pos, layout["buttons"]["Open Panel"]):
            return self.open_control_panel()

        if point_in_rect(pos, layout["buttons"]["Cancel"]):
            if self._server_running:
                self._mode = "panel"
                action = DedicatedServerAction("return_to_panel")
                self._last_action = action
                return action
            action = DedicatedServerAction("cancel")
            self._last_action = action
            self._status_message = "Server creation cancelled."
            self._status_timeout = 1.6
            return action

        return None

    def _handle_create_key(self, event) -> Optional[DedicatedServerAction]:
        key = getattr(event, "key", None)
        if key == _K_ESCAPE:
            if self._server_running:
                self._mode = "panel"
                action = DedicatedServerAction("return_to_panel")
                self._last_action = action
                return action
            return DedicatedServerAction("cancel")

        if key == _K_RETURN:
            return self.open_control_panel()

        if key == _K_TAB:
            ordered = ("server_name", "udp_port", "rcon_password")
            if self._focused_field not in ordered:
                self._focused_field = ordered[0]
                return None
            index = ordered.index(self._focused_field)
            self._focused_field = ordered[(index + 1) % len(ordered)]
            return None

        if self._focused_field is None:
            return None

        current_value = getattr(self._settings, self._focused_field)
        if key in (_K_BACKSPACE, _K_DELETE):
            updated = current_value[:-1]
        else:
            incoming = getattr(event, "unicode", "")
            if not incoming or not incoming.isprintable():
                return None
            if self._focused_field == "udp_port" and not incoming.isdigit():
                return None
            max_length = 32 if self._focused_field != "udp_port" else 5
            updated = (current_value + incoming)[:max_length]

        self._settings = replace(self._settings, **{self._focused_field: updated})
        action = DedicatedServerAction("field_changed", self._focused_field)
        self._last_action = action
        return action

    def _handle_panel_event(self, event) -> Optional[DedicatedServerAction]:
        event_type = getattr(event, "type", None)
        if event_type == _KEYDOWN:
            key = getattr(event, "key", None)
            if key == _K_TAB:
                current_index = self.PANEL_TABS.index(self._active_panel_tab)
                next_tab = self.PANEL_TABS[(current_index + 1) % len(self.PANEL_TABS)]
                return self._switch_panel_tab(next_tab)
            if key == _K_ESCAPE:
                self._mode = "create"
                action = DedicatedServerAction("edit_server")
                self._last_action = action
                return action
            return None

        if event_type != _MOUSEBUTTONDOWN:
            return None

        pos = getattr(event, "pos", None)
        button = getattr(event, "button", 1)
        if pos is None or button != 1:
            return None

        layout = self._panel_layout()
        for tab_name, tab_rect in layout["tabs"].items():
            if point_in_rect(pos, tab_rect):
                return self._switch_panel_tab(tab_name)

        edit_rect = layout.get("edit_button")
        if edit_rect is not None and point_in_rect(pos, edit_rect):
            self._mode = "create"
            action = DedicatedServerAction("edit_server")
            self._last_action = action
            self._status_message = "Editing server settings."
            self._status_timeout = 2.0
            return action

        control_buttons = layout.get("control_buttons", {})
        start_rect = control_buttons.get("Start")
        if start_rect is not None and point_in_rect(pos, start_rect):
            if self._server_running:
                self._status_message = "Server is already online."
                self._status_timeout = 1.5
                return None
            return self.start_server()

        restart_rect = control_buttons.get("Restart")
        if restart_rect is not None and point_in_rect(pos, restart_rect):
            if not self._server_running:
                self._status_message = "Start the server before using Restart."
                self._status_timeout = 1.5
                return None
            return self.restart_server()

        stop_rect = control_buttons.get("Stop")
        if stop_rect is not None and point_in_rect(pos, stop_rect):
            if not self._server_running:
                self._status_message = "Server is already offline."
                self._status_timeout = 1.5
                return None
            return self.stop_server()

        return None

    def _switch_panel_tab(self, tab_name: str) -> Optional[DedicatedServerAction]:
        if tab_name == self._active_panel_tab:
            return None
        self._active_panel_tab = tab_name
        action = DedicatedServerAction("panel_tab_changed", tab_name)
        self._last_action = action
        self._status_message = f"{tab_name} tab opened."
        self._status_timeout = 1.4
        return action

    def _cycle_field(self, field_name: str) -> DedicatedServerAction:
        if field_name == "game":
            updated = self._next_option(self.GAME_OPTIONS, self._settings.game)
            self._settings = replace(self._settings, game=updated)
        elif field_name == "map_name":
            updated = self._next_option(self.MAP_OPTIONS, self._settings.map_name)
            self._settings = replace(self._settings, map_name=updated)
        elif field_name == "network":
            updated = self._next_option(self.NETWORK_OPTIONS, self._settings.network)
            self._settings = replace(self._settings, network=updated)
        elif field_name == "rounds":
            updated = self._next_option(tuple(str(v) for v in self.ROUND_OPTIONS), str(self._settings.rounds))
            self._settings = replace(self._settings, rounds=int(updated))
        else:
            updated = self._next_option(tuple(str(v) for v in self.PLAYER_OPTIONS), str(self._settings.max_players))
            self._settings = replace(self._settings, max_players=int(updated))

        action = DedicatedServerAction("field_changed", field_name)
        self._last_action = action
        self._status_message = f"{field_name.replace('_', ' ').title()} updated."
        self._status_timeout = 1.2
        return action

    def _draw_create_mode(self, surface) -> None:
        layout = self._create_layout()
        draw_bevel_rect(surface, layout["window"], GROUND_PANEL, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK, outline=(49, 25, 7))
        draw_bevel_rect(surface, layout["title_bar"], GROUND_PANEL_ALT, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)
        draw_text(surface, self._font_cache, "Start Dedicated Server", layout["title_bar"], 22, GROUND_TEXT)
        draw_text(surface, self._font_cache, "x", layout["close_button"], 18, GROUND_TEXT, align="center")

        for label, field_name in (
            ("Game", "game"),
            ("Server Name", "server_name"),
            ("Map", "map_name"),
            ("Network", "network"),
            ("Max. players", "max_players"),
            ("Rounds", "rounds"),
            ("UDP Port", "udp_port"),
            ("RCON Password", "rcon_password"),
        ):
            label_rect = layout["labels"][field_name]
            field_rect = layout["fields"][field_name]
            draw_text(surface, self._font_cache, label, label_rect, 19, GROUND_TEXT_DIM, align="right")
            self._draw_input(surface, field_rect, self._field_display_value(field_name), field_name == self._focused_field, field_name in ("game", "map_name", "network", "max_players", "rounds"), placeholder="Coloque a senha aqui" if field_name == "rcon_password" else "")

        self._draw_checkbox(surface, layout["checkbox"], self._settings.secure)
        draw_text(surface, self._font_cache, "Secure (anti-cheat)", layout["checkbox_label"], 19, GROUND_TEXT_DIM)

        for button_name, button_rect in layout["buttons"].items():
            fill = GROUND_PANEL_ALT if button_name == "Open Panel" else GROUND_PANEL
            draw_bevel_rect(surface, button_rect, fill, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)
            draw_text(surface, self._font_cache, button_name, button_rect, 20, GROUND_TEXT, align="center")

        draw_text(surface, self._font_cache, self._status_message or "Ready to start a new session.", layout["status_rect"], 17, GROUND_TEXT_DIM)

    def _draw_panel_mode(self, surface) -> None:
        layout = self._panel_layout()
        draw_bevel_rect(surface, layout["window"], GROUND_PANEL, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK, outline=(49, 25, 7))

        for tab_name, tab_rect in layout["tabs"].items():
            active = tab_name == self._active_panel_tab
            fill = GROUND_PANEL_ALT if active else GROUND_PANEL
            light = GROUND_ACCENT if active else GROUND_PANEL_LIGHT
            draw_bevel_rect(surface, tab_rect, fill, light, GROUND_PANEL_DARK)
            colour = GROUND_TEXT if active else GROUND_TEXT_DIM
            draw_text(surface, self._font_cache, tab_name, tab_rect, 18, colour, align="center")

        if self._active_panel_tab == "Main":
            self._draw_info_box(surface, layout["summary"]["game"], "Game", self._settings.game)
            self._draw_info_box(surface, layout["summary"]["players"], "Players", f"{self._players_connected} / {self._settings.max_players}")
            address_value = self._server_address if self._server_address == "Offline" else f"{self._server_address}:{self._settings.udp_port}"
            self._draw_info_box(surface, layout["summary"]["address"], "IP Address", address_value)
            self._draw_info_box(surface, layout["summary"]["uptime"], "Uptime", self._format_uptime())

        if self._active_panel_tab in ("Main", "Configure", "Statistics", "Players", "Bans"):
            self._draw_table(surface, layout)
        else:
            self._draw_console(surface, layout)

        if layout.get("edit_button") is not None:
            draw_bevel_rect(surface, layout["edit_button"], GROUND_PANEL_ALT, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)
            draw_text(surface, self._font_cache, "Edit...", layout["edit_button"], 19, GROUND_TEXT, align="center")

        for button_name, button_rect in layout.get("control_buttons", {}).items():
            enabled = not (
                (button_name == "Start" and self._server_running)
                or (button_name in ("Restart", "Stop") and not self._server_running)
            )
            fill = GROUND_PANEL_ALT if enabled else GROUND_PANEL
            text_colour = GROUND_TEXT if enabled else GROUND_DISABLED
            draw_bevel_rect(surface, button_rect, fill, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)
            draw_text(surface, self._font_cache, button_name, button_rect, 19, text_colour, align="center")

        draw_text(surface, self._font_cache, self._status_message or "Server control panel ready.", layout["status_rect"], 17, GROUND_TEXT_DIM)

    def _draw_input(self, surface, field_rect: Rect, value: str, focused: bool, dropdown: bool, placeholder: str = "") -> None:
        fill = GROUND_PANEL if not focused else GROUND_PANEL_ALT
        light = GROUND_ACCENT if focused else GROUND_PANEL_LIGHT
        draw_bevel_rect(surface, field_rect, fill, light, GROUND_PANEL_DARK)
        if value:
            draw_text(surface, self._font_cache, value, field_rect, 19, GROUND_TEXT)
        elif placeholder:
            draw_text(surface, self._font_cache, placeholder, field_rect, 19, GROUND_DISABLED)

        if dropdown:
            arrow_rect = rect(field_rect[0] + field_rect[2] - 18, field_rect[1] + 7, 12, field_rect[3] - 14)
            pygame.draw.line(surface, GROUND_TEXT, (arrow_rect[0], arrow_rect[1]), (arrow_rect[0] + 5, arrow_rect[1] + 5))
            pygame.draw.line(surface, GROUND_TEXT, (arrow_rect[0] + 10, arrow_rect[1]), (arrow_rect[0] + 5, arrow_rect[1] + 5))

    def _draw_checkbox(self, surface, target: Rect, checked: bool) -> None:
        draw_bevel_rect(surface, target, GROUND_PANEL, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)
        if checked:
            pygame.draw.line(surface, GROUND_TEXT, (target[0] + 3, target[1] + target[3] // 2), (target[0] + 7, target[1] + target[3] - 4))
            pygame.draw.line(surface, GROUND_TEXT, (target[0] + 7, target[1] + target[3] - 4), (target[0] + target[2] - 3, target[1] + 3))

    def _draw_info_box(self, surface, target: Dict[str, Rect], label: str, value: str) -> None:
        draw_text(surface, self._font_cache, label, target["label"], 18, GROUND_TEXT_DIM, align="right")
        draw_bevel_rect(surface, target["value"], GROUND_PANEL, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)
        draw_text(surface, self._font_cache, value, target["value"], 18, GROUND_TEXT)

    def _draw_table(self, surface, layout: Dict[str, object]) -> None:
        header = layout["table_header"]
        draw_bevel_rect(surface, header, GROUND_PANEL_ALT, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)
        draw_text(surface, self._font_cache, "Variable", layout["header_columns"]["variable"], 18, GROUND_TEXT)
        draw_text(surface, self._font_cache, "Value", layout["header_columns"]["value"], 18, GROUND_TEXT)

        body_surface = pygame.Surface((layout["table_body"][2], layout["table_body"][3]), pygame.SRCALPHA)
        body_surface.fill((102, 60, 18, 202))
        surface.blit(body_surface, (layout["table_body"][0], layout["table_body"][1]))
        draw_bevel_rect(surface, layout["table_body"], GROUND_PANEL, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)

        rows = self._panel_rows()
        for index, row in enumerate(rows):
            row_rect = rect(layout["table_body"][0] + 1, layout["table_body"][1] + 1 + index * layout["row_height"], layout["table_body"][2] - 2, layout["row_height"] - 1)
            fill = GROUND_PANEL_ALT if index % 2 == 0 else GROUND_PANEL
            draw_bevel_rect(surface, row_rect, fill, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)
            draw_text(surface, self._font_cache, row[0], rect(row_rect[0] + 4, row_rect[1], layout["columns"]["variable"], row_rect[3]), 18, GROUND_TEXT)
            draw_text(surface, self._font_cache, row[1], rect(layout["table_body"][0] + layout["columns"]["variable"] + 6, row_rect[1], layout["columns"]["value"] - 10, row_rect[3]), 18, GROUND_TEXT)

    def _draw_console(self, surface, layout: Dict[str, object]) -> None:
        draw_bevel_rect(surface, layout["table_header"], GROUND_PANEL_ALT, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)
        draw_text(surface, self._font_cache, "Console", layout["table_header"], 18, GROUND_TEXT)

        console_surface = pygame.Surface((layout["table_body"][2], layout["table_body"][3]), pygame.SRCALPHA)
        console_surface.fill((82, 48, 15, 224))
        surface.blit(console_surface, (layout["table_body"][0], layout["table_body"][1]))
        draw_bevel_rect(surface, layout["table_body"], GROUND_PANEL, GROUND_PANEL_LIGHT, GROUND_PANEL_DARK)

        for index, line in enumerate(self._console_lines[-10:]):
            line_rect = rect(layout["table_body"][0] + 6, layout["table_body"][1] + 6 + index * 22, layout["table_body"][2] - 12, 20)
            draw_text(surface, self._font_cache, line, line_rect, 17, GROUND_TEXT_DIM)

    def _panel_rows(self) -> List[Tuple[str, str]]:
        if self._active_panel_tab == "Main":
            password_display = f'"{self._settings.rcon_password}"' if self._settings.rcon_password else '"-"'
            address_value = self._server_address if self._server_address == "Offline" else f"{self._server_address}:{self._settings.udp_port}"
            return [
                ("Server Name", self._settings.server_name),
                ("Map", self._settings.map_name),
                ("Network", self._settings.network),
                ("Rounds", str(self._settings.rounds)),
                ("Address", address_value),
                ("Lobby State", self._format_server_state()),
                ("Players Waiting", ", ".join(self._player_names) if self._player_names else "-"),
                ("RCON Password", password_display),
            ]
        if self._active_panel_tab == "Configure":
            return list(self._config_values.items())
        if self._active_panel_tab == "Statistics":
            return [
                ("Rounds hosted", "0"),
                ("Map changes", "0"),
                ("Peak players", str(self._players_connected)),
                ("Secure mode", "Enabled" if self._settings.secure else "Disabled"),
                ("Match rounds", str(self._settings.rounds)),
                ("Packets in / out", "0 / 0"),
                ("Tick state", "Stable"),
                ("Countdown", f"{self._countdown_seconds_remaining}s" if self._lobby_state == "countdown" else "-"),
            ]
        if self._active_panel_tab == "Players":
            rows = [("Connected", f"{self._players_connected} / {self._settings.max_players}")]
            if self._player_names:
                rows.extend((f"Player {index + 1}", player_name) for index, player_name in enumerate(self._player_names))
            else:
                rows.append(("Status", "No players connected"))
            return rows
        if self._active_panel_tab == "Bans":
            return [
                ("Ban list", "Empty"),
                ("Auto-kick list", "Clear"),
            ]
        return []

    def _sync_server_runtime(self) -> None:
        if self._lan_server is None:
            return
        snapshot = self._lan_server.get_lobby_snapshot()
        self._players_connected = snapshot.current_players
        self._lobby_state = snapshot.lobby_state
        self._countdown_seconds_remaining = snapshot.countdown_seconds
        self._player_names = list(snapshot.players)
        self._server_address = snapshot.host
        if snapshot.match_started:
            self._status_message = "Match started. New clients should wait for the next round."
            self._status_timeout = max(self._status_timeout, 1.0)

    def _format_server_state(self) -> str:
        if not self._server_running:
            return "Offline"
        if self._lobby_state == "started":
            return "Match started"
        if self._lobby_state == "countdown":
            return f"Starting in {self._countdown_seconds_remaining}s"
        return "Waiting for at least 2 players"

    def _create_layout(self) -> Dict[str, object]:
        window = rect((self._width - 380) // 2, (self._height - 468) // 2, 380, 468)
        x, y, w, _h = window
        title_bar = rect(x + 10, y + 10, w - 20, 28)
        close_button = rect(x + w - 30, y + 12, 16, 16)
        label_x = x + 16
        field_x = x + 134
        full_w = w - (field_x - x) - 24
        small_w = 104
        row_y = y + 56
        row_gap = 38
        labels = {
            "game": rect(label_x, row_y, 108, 28),
            "server_name": rect(label_x, row_y + row_gap, 108, 28),
            "map_name": rect(label_x, row_y + row_gap * 2, 108, 28),
            "network": rect(label_x, row_y + row_gap * 3, 108, 28),
            "max_players": rect(label_x, row_y + row_gap * 4, 108, 28),
            "rounds": rect(label_x, row_y + row_gap * 5, 108, 28),
            "udp_port": rect(label_x, row_y + row_gap * 6, 108, 28),
            "rcon_password": rect(label_x, row_y + row_gap * 7, 108, 28),
        }
        fields = {
            "game": rect(field_x, row_y, full_w, 28),
            "server_name": rect(field_x, row_y + row_gap, full_w, 28),
            "map_name": rect(field_x, row_y + row_gap * 2, full_w, 28),
            "network": rect(field_x, row_y + row_gap * 3, full_w, 28),
            "max_players": rect(field_x, row_y + row_gap * 4, small_w, 28),
            "rounds": rect(field_x, row_y + row_gap * 5, small_w, 28),
            "udp_port": rect(field_x, row_y + row_gap * 6, small_w, 28),
            "rcon_password": rect(field_x, row_y + row_gap * 7, full_w, 28),
        }
        checkbox = rect(field_x, row_y + row_gap * 8 + 4, 14, 14)
        checkbox_label = rect(field_x + 18, row_y + row_gap * 8 - 2, full_w, 22)
        buttons = {
            "Open Panel": rect(x + 118, y + 426, 112, 30),
            "Cancel": rect(x + 238, y + 426, 80, 30),
        }
        status_rect = rect(x + 14, y + 394, w - 28, 22)
        return {
            "window": window,
            "title_bar": title_bar,
            "close_button": close_button,
            "labels": labels,
            "fields": fields,
            "checkbox": checkbox,
            "checkbox_label": checkbox_label,
            "buttons": buttons,
            "status_rect": status_rect,
        }

    def _panel_layout(self) -> Dict[str, object]:
        panel_w = min(720, self._width - 24)
        panel_h = min(560, self._height - 24)
        window = rect((self._width - panel_w) // 2, (self._height - panel_h) // 2, panel_w, panel_h)
        x, y, w, h = window
        tab_widths = {
            "Main": 68,
            "Configure": 110,
            "Statistics": 104,
            "Players": 86,
            "Bans": 70,
            "Console": 88,
        }
        tabs: Dict[str, Rect] = {}
        tab_x = x + 10
        for tab_name in self.PANEL_TABS:
            tabs[tab_name] = rect(tab_x, y + 10, tab_widths[tab_name], 28)
            tab_x += tab_widths[tab_name] - 2

        summary = {}
        if self._active_panel_tab == "Main":
            summary_y = y + 56
            summary["game"] = {"label": rect(x + 16, summary_y, 82, 24), "value": rect(x + 104, summary_y, 164, 24)}
            summary["players"] = {"label": rect(x + 280, summary_y, 64, 24), "value": rect(x + 348, summary_y, 118, 24)}
            summary["address"] = {"label": rect(x + 16, summary_y + 34, 82, 24), "value": rect(x + 104, summary_y + 34, 250, 24)}
            summary["uptime"] = {"label": rect(x + 374, summary_y + 34, 66, 24), "value": rect(x + 446, summary_y + 34, 120, 24)}
            table_y = y + 136
        else:
            table_y = y + 52

        table_header = rect(x + 16, table_y, w - 50, 24)
        table_body = rect(x + 16, table_y + 24, w - 50, h - (table_y - y) - 90)
        row_height = max(22, min(27, max(1, (table_body[3] - 2) // max(1, len(self._panel_rows())))))
        header_columns = {
            "variable": rect(table_header[0], table_header[1], int(table_header[2] * 0.48), table_header[3]),
            "value": rect(table_header[0] + int(table_header[2] * 0.48), table_header[1], table_header[2] - int(table_header[2] * 0.48), table_header[3]),
        }
        columns = {
            "variable": header_columns["variable"][2],
            "value": header_columns["value"][2],
        }

        edit_button = None
        if self._active_panel_tab in ("Main", "Configure"):
            edit_button = rect(x + 16, y + h - 48, 94, 28)

        control_buttons = {
            "Start": rect(x + 126, y + h - 48, 82, 28),
            "Restart": rect(x + 214, y + h - 48, 92, 28),
            "Stop": rect(x + 312, y + h - 48, 74, 28),
        }

        status_rect = rect(x + 396, y + h - 46, w - 410, 24)

        return {
            "window": window,
            "tabs": tabs,
            "summary": summary,
            "table_header": table_header,
            "table_body": table_body,
            "header_columns": header_columns,
            "columns": columns,
            "row_height": row_height,
            "edit_button": edit_button,
            "control_buttons": control_buttons,
            "status_rect": status_rect,
        }

    def _field_display_value(self, field_name: str) -> str:
        if field_name == "game":
            return self._settings.game
        if field_name == "server_name":
            return self._settings.server_name
        if field_name == "map_name":
            return self._settings.map_name
        if field_name == "network":
            return self._settings.network
        if field_name == "max_players":
            return str(self._settings.max_players)
        if field_name == "rounds":
            return str(self._settings.rounds)
        if field_name == "udp_port":
            return self._settings.udp_port
        if field_name == "rcon_password":
            return self._settings.rcon_password
        return ""

    def _format_uptime(self) -> str:
        total_seconds = int(self._uptime_seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def _next_option(options: Tuple[str, ...], current: str) -> str:
        if current not in options:
            return options[0]
        index = options.index(current)
        return options[(index + 1) % len(options)]
