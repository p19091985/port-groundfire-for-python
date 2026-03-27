from __future__ import annotations

import getpass
import socket
from typing import Dict, Optional

import pygame

from .lan_client import LanClient, LanConnectionResult, LanDiscoveredServer
from .online_match import OnlineMatchSetup
from .server_browser_ui import ServerBrowserAction, ServerBrowserEntry, ServerBrowserUI


class NetworkClientInterface(ServerBrowserUI):
    DISCOVERY_INTERVAL = 1.5
    LOBBY_POLL_INTERVAL = 0.5

    def __init__(self, width: int = 1280, height: int = 720, settings=None):
        super().__init__(width=width, height=height, title="Find Servers", servers=[])
        self._active_tab = "Lan"
        self._lan_client = LanClient()
        default_name = f"{getpass.getuser()}@{socket.gethostname()}"
        self._client_name = default_name
        self._online_ai_enabled = False
        if settings is not None:
            self._client_name = settings.get_string("Network", "ClientName", default_name).strip() or default_name
            self._online_ai_enabled = settings.get_int("Network", "OnlineAIEnabled", 0) != 0
        self._known_servers: Dict[str, LanDiscoveredServer] = {}
        self._discovery_elapsed = self.DISCOVERY_INTERVAL
        self._lobby_elapsed = 0.0
        self._connected_lobby: Optional[LanConnectionResult] = None
        self._pending_match_setup: Optional[OnlineMatchSetup] = None
        self._refresh_lan_servers()

    def update(self, dt: float) -> None:
        super().update(dt)

        if self._connected_lobby is not None:
            self._lobby_elapsed += dt
            if self._lobby_elapsed >= self.LOBBY_POLL_INTERVAL:
                self._lobby_elapsed = 0.0
                self._poll_lobby()
            return

        if self.get_active_tab() != "Lan":
            return

        self._discovery_elapsed += dt
        if self._discovery_elapsed >= self.DISCOVERY_INTERVAL:
            self._refresh_lan_servers()

    def activate_tab(self, tab_name: str):
        action = super().activate_tab(tab_name)
        if tab_name == "Lan" and self._connected_lobby is None:
            self._refresh_lan_servers()
        return action

    def trigger_button(self, button_name: str):
        if self._connected_lobby is not None:
            if button_name in ("Quick refresh", "Refresh all"):
                self._poll_lobby()
                return None
            if button_name == "Connect":
                self.leave_lobby()
                return None
            return super().trigger_button(button_name)

        if button_name in ("Quick refresh", "Refresh all"):
            self._refresh_lan_servers()
            return None

        if button_name == "Change filters":
            self._online_ai_enabled = not self._online_ai_enabled
            self.set_status_message(self._build_ai_toggle_message(), 2.2)
            action = ServerBrowserAction("toggle_online_ai", "on" if self._online_ai_enabled else "off")
            self._last_action = action
            return action

        if button_name == "Connect":
            selected = self.get_selected_server()
            if selected is None:
                self.set_status_message("Select a LAN server before connecting.", 1.8)
                return None

            discovered = self._known_servers.get(selected.server_id)
            if discovered is None:
                self.set_status_message("The selected LAN server is no longer available.", 1.8)
                self._refresh_lan_servers()
                return None

            try:
                result = self._lan_client.connect(
                    host=discovered.snapshot.host,
                    port=discovered.snapshot.port,
                    client_name=self._client_name,
                    use_ai=self._online_ai_enabled,
                )
            except OSError:
                self.set_status_message("Failed to reach the selected LAN server.", 2.0)
                self._refresh_lan_servers()
                return None

            if result.status != "ok":
                self.set_status_message("Failed to join the selected LAN server.", 2.0)
                return None

            self._connected_lobby = result
            self._lobby_elapsed = 0.0
            self.set_status_message(f"Connected to {result.server_name}. Waiting in lobby...", 2.4)
            if result.match_started:
                self._queue_match_setup(result)
            return None

        return super().trigger_button(button_name)

    def handle_event(self, event):
        action = super().handle_event(event)
        if action is not None and action.kind == "close" and self._connected_lobby is not None:
            self.leave_lobby()
            return action
        return action

    def draw(self, surface) -> None:
        if self._connected_lobby is None:
            super().draw(surface)
            return

        self._draw_background(surface)
        layout = self.get_layout_snapshot()
        self._draw_window(surface, layout)
        self._draw_title_bar(surface, layout)
        self._draw_connected_lobby(surface, layout)
        self._draw_connected_footer(surface, layout)

    def shutdown(self) -> None:
        self.leave_lobby()

    def consume_match_setup(self) -> Optional[OnlineMatchSetup]:
        match_setup = self._pending_match_setup
        self._pending_match_setup = None
        return match_setup

    def is_online_ai_enabled(self) -> bool:
        return self._online_ai_enabled

    def leave_lobby(self) -> None:
        if self._connected_lobby is None:
            return

        try:
            self._lan_client.leave(
                self._connected_lobby.host,
                self._connected_lobby.port,
                self._connected_lobby.player_id,
            )
        except OSError:
            pass

        self._connected_lobby = None
        self._pending_match_setup = None
        self._lobby_elapsed = 0.0
        self._refresh_lan_servers()
        self.set_status_message("Left the LAN lobby.", 1.4)

    def _refresh_lan_servers(self) -> None:
        try:
            discovered = self._lan_client.discover_lan()
        except OSError:
            discovered = []
            self.set_status_message("Unable to scan the local network right now.", 1.8)

        self._known_servers = {server.server_id: server for server in discovered}
        entries = [
            ServerBrowserEntry(
                server_id=server.server_id,
                name=server.snapshot.server_name,
                game="Groundfire",
                players=server.snapshot.current_players,
                max_players=server.snapshot.max_players,
                map_name=server.snapshot.map_name,
                latency=server.latency_ms,
                lan=True,
            )
            for server in discovered
        ]
        self.set_servers(entries)
        self._discovery_elapsed = 0.0
        if entries:
            self.set_status_message(f"{len(entries)} LAN server(s) discovered.")
        else:
            self.set_status_message("No LAN servers available right now.", 1.6)

    def _poll_lobby(self) -> None:
        if self._connected_lobby is None:
            return

        try:
            result = self._lan_client.get_lobby_status(
                self._connected_lobby.host,
                self._connected_lobby.port,
                self._connected_lobby.player_id,
            )
        except OSError:
            self.set_status_message("Lost connection to the LAN server.", 2.0)
            self._connected_lobby = None
            self._refresh_lan_servers()
            return

        if result.status != "ok":
            self.set_status_message("Lost connection to the LAN server.", 2.0)
            self._connected_lobby = None
            self._refresh_lan_servers()
            return

        self._connected_lobby = result
        if result.match_started:
            self._queue_match_setup(result)

    def _queue_match_setup(self, result: LanConnectionResult) -> None:
        if self._pending_match_setup is not None:
            return
        if not result.match_id or result.slot_index < 0 or not result.player_slots:
            self.set_status_message("The LAN match started, but the setup data is incomplete.", 2.0)
            return
        self._pending_match_setup = OnlineMatchSetup.from_connection_result(result)
        self.set_status_message("Match started. Launching Groundfire online battle...", 2.6)

    def _draw_connected_lobby(self, surface, layout) -> None:
        assert self._connected_lobby is not None
        header = layout["table_header"]
        body = layout["table_body"]

        self._draw_bevel_rect(surface, header, self.PANEL_ALT, self.PANEL_LIGHT, self.PANEL_DARK)
        self._draw_text(surface, "Lobby", header, 18, self.TEXT)

        lobby_surface = pygame.Surface((body[2], body[3]), pygame.SRCALPHA)
        lobby_surface.fill((102, 60, 18, 202))
        surface.blit(lobby_surface, (body[0], body[1]))
        self._draw_bevel_rect(surface, body, self.PANEL, self.PANEL_LIGHT, self.PANEL_DARK)

        info_rows = [
            ("Server", self._connected_lobby.server_name),
            ("Map", self._connected_lobby.map_name),
            ("Network", self._connected_lobby.network),
            ("Address", f"{self._connected_lobby.host}:{self._connected_lobby.port}"),
            ("Rounds", str(self._connected_lobby.rounds)),
            ("Client AI", "Enabled" if self._online_ai_enabled else "Disabled"),
            ("Players", f"{self._connected_lobby.current_players}/{self._connected_lobby.max_players}"),
            ("State", self._format_lobby_state()),
        ]

        row_y = body[1] + 10
        for label, value in info_rows:
            self._draw_text(surface, label, self._rect(body[0] + 10, row_y, 110, 22), 18, self.TEXT_DIM)
            self._draw_text(surface, value, self._rect(body[0] + 120, row_y, body[2] - 130, 22), 18, self.TEXT)
            row_y += 28

        self._draw_text(surface, "Waiting Players", self._rect(body[0] + 10, row_y + 6, body[2] - 20, 24), 18, self.ACCENT)
        row_y += 34

        players = self._connected_lobby.players or (self._client_name,)
        for player_name in players:
            row_rect = self._rect(body[0] + 10, row_y, body[2] - 20, 26)
            self._draw_bevel_rect(surface, row_rect, self.PANEL_ALT, self.PANEL_LIGHT, self.PANEL_DARK)
            self._draw_text(surface, player_name, self._rect(row_rect[0] + 8, row_rect[1], row_rect[2] - 16, row_rect[3]), 18, self.TEXT)
            row_y += 30

    def _draw_connected_footer(self, surface, layout) -> None:
        assert self._connected_lobby is not None
        self._draw_bevel_rect(surface, layout["footer"], self.PANEL_ALT, self.PANEL_LIGHT, self.PANEL_DARK)
        self._draw_text(surface, "Groundfire", layout["status_rect"], 18, self.ACCENT)
        status = "Press Esc to leave the lobby." if not self._connected_lobby.match_started else "Match ready. Waiting for gameplay handoff."
        status_rect = self._rect(layout["status_rect"][0] + 100, layout["status_rect"][1], layout["status_rect"][2] - 100, layout["status_rect"][3])
        self._draw_text(surface, status, status_rect, 17, self.TEXT_DIM)

    def _draw_footer(self, surface, layout) -> None:
        self._draw_bevel_rect(surface, layout["footer"], self.PANEL_ALT, self.PANEL_LIGHT, self.PANEL_DARK)

        for button_name, button_rect in layout["buttons"].items():
            is_disabled = button_name == "Connect" and self.get_selected_server() is None
            fill = self.PANEL_ALT if not is_disabled else self.PANEL
            light = self.ACCENT if not is_disabled else self.PANEL_LIGHT
            dark = self.PANEL_DARK
            self._draw_bevel_rect(surface, button_rect, fill, light, dark)
            colour = self.TEXT if not is_disabled else self.DISABLED
            self._draw_text(surface, self._get_footer_button_label(button_name), button_rect, 18, colour, align="center")

        self._draw_text(surface, "Groundfire", layout["status_rect"], 18, self.ACCENT)
        status_rect = self._rect(layout["status_rect"][0] + 100, layout["status_rect"][1], layout["status_rect"][2] - 100, layout["status_rect"][3])
        self._draw_text(surface, self._compose_status_text(), status_rect, 17, self.TEXT_DIM)

    def _compose_status_text(self) -> str:
        status = super()._compose_status_text()
        ai_label = "AI online: ON" if self._online_ai_enabled else "AI online: OFF"
        if status:
            return f"{ai_label} | {status}"
        return ai_label

    def _get_footer_button_label(self, button_name: str) -> str:
        if button_name == "Change filters":
            return "AI: ON" if self._online_ai_enabled else "AI: OFF"
        return button_name

    def _build_ai_toggle_message(self) -> str:
        if self._online_ai_enabled:
            return "Online AI enabled. This client will join LAN servers with AI control."
        return "Online AI disabled. This client will join LAN servers with manual control."

    def _format_lobby_state(self) -> str:
        assert self._connected_lobby is not None
        if self._connected_lobby.match_started:
            return "Match started"
        if self._connected_lobby.lobby_state == "countdown":
            return f"Starting in {self._connected_lobby.countdown_seconds}s"
        return "Waiting for at least 2 players"
