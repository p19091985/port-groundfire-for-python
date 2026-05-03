from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from groundfire_net.browser import ServerBook, ServerListEntry

from ..gameplay.constants import PLAYER_COLOURS, WEAPON_SPECS
from ..input.commands import PlayerCommand
from ..network.browser import GroundfireServerScanner, default_server_book_path
from ..sim.match import MatchSnapshot, ReplicatedPlayerState

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class _ClassicThemeMixin:
    _background_scroll = 0.0
    _background_scroll_speed = 0.0025
    _brown_fill = (153, 76, 0, 180)
    _panel_fill = (0, 0, 0, 128)
    _bright_text = (255, 255, 255)
    _cyan_text = (0, 255, 255)
    _gold_text = (255, 255, 0)
    _muted_text = (76, 76, 76)
    _browser_frame_fill = (0, 0, 0, 145)
    _browser_body_fill = (0, 0, 0, 120)
    _browser_header_fill = (153, 76, 0, 150)
    _browser_dialog_fill = (0, 0, 0, 205)
    _browser_input_fill = (0, 0, 0, 170)
    _browser_text = (235, 240, 245)
    _browser_dim_text = (190, 215, 230)
    _browser_selected_fill = (153, 76, 0, 135)
    _browser_hover_fill = (153, 76, 0, 80)

    def _advance_background(self):
        self.__class__._background_scroll += self._background_scroll_speed
        if self.__class__._background_scroll >= 1.0:
            self.__class__._background_scroll -= 1.0

    def _draw_background(self, game):
        if not hasattr(game, "get_graphics"):
            return
        self._advance_background()
        graphics = game.get_graphics()
        interface = game.get_interface()
        get_texture_surface = getattr(interface, "get_texture_surface", None)
        texture = None if not callable(get_texture_surface) else get_texture_surface(6)
        if texture is None:
            graphics.fill_screen((100, 180, 230))
            return
        offset_x = int(self.__class__._background_scroll * texture.get_width())
        offset_y = int(self.__class__._background_scroll * texture.get_height())
        graphics.draw_tiled_texture(
            6,
            tint=(102, 179, 230),
            offset_px=(offset_x, offset_y),
            fallback_fill=(100, 180, 230),
        )

    def _draw_logo(self, game, *, top: float = 4.0, bottom: float = 0.0):
        if not hasattr(game, "get_graphics"):
            return
        interface = game.get_interface()
        graphics = game.get_graphics()
        get_texture_surface = getattr(interface, "get_texture_surface", None)
        if callable(get_texture_surface) and get_texture_surface(9) is not None:
            graphics.draw_texture_world_rect(9, -8.0, top, 8.0, bottom)
            return
        ui = game.get_ui()
        ui.draw_centered_text(
            0.0,
            (top + bottom) / 2.0 + 0.6,
            "GROUNDFIRE",
            style=ui.style(1.3, self._gold_text, shadow=True),
        )

    def _draw_panel(self, game, left: float, top: float, right: float, bottom: float, *, fill=None):
        if not hasattr(game, "get_graphics"):
            return
        game.get_graphics().draw_world_rect(left, top, right, bottom, fill or self._panel_fill)

    def _draw_tank_icon(self, game, x: float, y: float, colour: tuple[int, int, int], *, size: float = 0.35):
        if not hasattr(game, "get_graphics"):
            return
        points = (
            (x - size, y - (size * 0.3)),
            (x - (size * 0.5), y + size),
            (x + (size * 0.5), y + size),
            (x + size, y - (size * 0.3)),
        )
        game.get_graphics().draw_world_polygon(points, colour)

    def _draw_bar(self, game, centre_y: float, *, fill=None):
        self._draw_panel(game, -4.0, centre_y + 0.4, 4.0, centre_y - 0.4, fill=fill or self._brown_fill)

    def _button_style(self, game, *, highlighted: bool):
        colour = self._gold_text if highlighted else self._bright_text
        return game.get_ui().style(0.7, colour, spacing=0.6, shadow=True)

    def _measure_text_width(self, game, text: str, *, size: float) -> float:
        return game.get_ui().measure_text(text, style=game.get_ui().style(size, self._bright_text, spacing=size - 0.1))

    def _text_button_highlighted(self, game, *, text: str, x: float, y: float, size: float) -> bool:
        mouse_x, mouse_y = game.get_interface().get_mouse_pos()
        width = self._measure_text_width(game, text, size=size)
        return (
            (y + size / 2.0) > mouse_y
            and (y - size / 2.0) < mouse_y
            and (x - width / 2.0) < mouse_x < (x + width / 2.0)
        )

    def _draw_text_button(self, game, *, text: str, x: float, y: float, size: float, fill=None):
        highlighted = self._text_button_highlighted(game, text=text, x=x, y=y, size=size)
        if fill is not None:
            self._draw_bar(game, y, fill=fill)
        game.get_ui().draw_centered_text(
            x,
            y - (size / 2.0),
            text,
            style=self._button_style(game, highlighted=highlighted),
        )
        return highlighted

    def _rank_label(self, index: int) -> str:
        if index == 0:
            return "1st"
        if index == 1:
            return "2nd"
        if index == 2:
            return "3rd"
        return f"{index + 1}th"

    def _phase_seconds_remaining(self, snapshot: MatchSnapshot) -> float:
        return max(0.0, float(snapshot.phase_ticks_remaining) / 60.0)

    def _weapon_ammo_text(self, player: ReplicatedPlayerState) -> str:
        ammo_map = {weapon: amount for weapon, amount in player.weapon_stocks}
        if player.selected_weapon == "shell":
            return "INF"
        return str(ammo_map.get(player.selected_weapon, 0))

    def _player_name(self, snapshot: MatchSnapshot, player_number: int | None) -> str | None:
        if player_number is None:
            return None
        for player in snapshot.players:
            if player.player_number == player_number:
                return player.name
        return f"Player {player_number + 1}"

    def _local_player(self, snapshot: MatchSnapshot, local_player_number: int | None) -> ReplicatedPlayerState | None:
        for player in snapshot.players:
            if player.player_number == local_player_number:
                return player
        return None

    def _ordered_players(self, snapshot: MatchSnapshot) -> tuple[ReplicatedPlayerState, ...]:
        return tuple(sorted(snapshot.players, key=lambda player: (-player.score, player.player_number)))


class ClientMenuRenderer(_ClassicThemeMixin):
    _shop_disabled_items = (
        ("Rolling Mines", 50),
        ("Airstrike", 100),
        ("Death's Head", 200),
        ("Hover Coil", 150),
        ("Corbomite", 20),
    )

    def draw_status_overlay(self, game, text: str):
        if not hasattr(game, "get_graphics"):
            ui = game.get_ui()
            ui.draw_centered_text(0.0, 0.4, "Groundfire Online", style=ui.style(0.6, self._bright_text, shadow=True))
            ui.draw_centered_text(0.0, -0.1, text, style=ui.style(0.3, (180, 220, 255), shadow=True))
            return

        self._draw_background(game)
        self._draw_logo(game)
        self._draw_panel(game, -7.0, -3.4, 7.0, -6.6)
        self._draw_text_button(game, text="Connecting", x=0.0, y=-4.35, size=0.7)
        game.get_ui().draw_centered_text(
            0.0,
            -5.7,
            text,
            style=game.get_ui().style(0.45, self._bright_text, spacing=0.35, shadow=True),
        )

    def draw_title_overlay(self, game, title: str, subtitle: str):
        if not hasattr(game, "get_graphics"):
            ui = game.get_ui()
            ui.draw_centered_text(0.0, 1.2, title, style=ui.style(0.9, self._bright_text, shadow=True))
            ui.draw_centered_text(0.0, 0.2, subtitle, style=ui.style(0.28, (186, 222, 255), shadow=True))
            return

        self._draw_background(game)
        self._draw_logo(game)
        self._draw_panel(game, -7.0, -3.4, 7.0, -6.6)
        game.get_ui().draw_centered_text(
            0.0,
            -4.35,
            title,
            style=game.get_ui().style(0.7, self._bright_text, spacing=0.6, shadow=True),
        )
        game.get_ui().draw_centered_text(
            0.0,
            -5.7,
            subtitle,
            style=game.get_ui().style(0.45, self._bright_text, spacing=0.35, shadow=True),
        )

    def draw_player_strip(self, game, snapshot: MatchSnapshot):
        ui = game.get_ui()
        for player in snapshot.players:
            start_of_bar = -10.0 + (2.5 * player.player_number) + 0.1
            self._draw_panel(game, start_of_bar, 7.4, start_of_bar + 2.3, 6.6, fill=(128, 230, 153, 76))
            ui.printf(
                start_of_bar + 0.05,
                6.1,
                "%s %dpts $%d",
                player.name,
                player.score,
                player.money,
                style=ui.style(0.22, player.colour if player.connected else (180, 180, 180), spacing=0.18, shadow=True),
            )
            ui.printf(
                start_of_bar + 0.05,
                5.75,
                "%s %s",
                player.selected_weapon.upper(),
                self._weapon_ammo_text(player),
                style=ui.style(0.18, self._bright_text, spacing=0.18, shadow=True),
            )

    def draw_match_overlay(self, game, snapshot: MatchSnapshot, *, local_player_number: int | None = None):
        if snapshot.game_phase == "round_starting":
            self._draw_panel(game, -7.0, 1.0, 7.0, -2.0)
            game.get_ui().draw_centered_text(
                0.0,
                0.5,
                f"Round {snapshot.current_round}",
                style=game.get_ui().style(0.6, self._bright_text, shadow=True),
            )
            game.get_ui().draw_centered_text(
                0.0,
                -0.5,
                "Get Ready",
                style=game.get_ui().style(0.6, self._bright_text, shadow=True),
            )
            return

        if snapshot.game_phase == "round_finishing":
            winner_name = self._player_name(snapshot, snapshot.round_winner_player_number)
            title = f"{winner_name} wins the round" if winner_name is not None else "Round Over"
            self._draw_panel(game, -7.0, 1.0, 7.0, -2.0)
            game.get_ui().draw_centered_text(
                0.0,
                0.2,
                title,
                style=game.get_ui().style(0.6, self._bright_text, shadow=True),
            )
            game.get_ui().draw_centered_text(
                0.0,
                -0.9,
                f"Next round in {self._phase_seconds_remaining(snapshot):.1f}s",
                style=game.get_ui().style(0.35, self._bright_text, spacing=0.28, shadow=True),
            )
            return

        if snapshot.game_phase == "score":
            self._draw_score_overlay(game, snapshot)
            return

        if snapshot.game_phase == "shop":
            self._draw_shop_overlay(game, snapshot, local_player_number=local_player_number)
            return

        if snapshot.game_phase == "winner":
            self._draw_winner_overlay(game, snapshot)

    def _draw_score_overlay(self, game, snapshot: MatchSnapshot):
        ui = game.get_ui()
        players = self._ordered_players(snapshot)
        heading_style = ui.style(0.5, (230, 230, 230), spacing=0.4, shadow=True)
        score_style = ui.style(0.5, self._bright_text, spacing=0.4, shadow=True)
        name_style = ui.style(0.3, self._bright_text, spacing=0.2)
        players_by_number = {player.player_number: player for player in snapshot.players}

        ui.draw_centered_text(-6.3, 6.5, "Player", style=heading_style)
        ui.draw_centered_text(0.0, 6.5, "Scoring for Round", style=heading_style)
        ui.draw_centered_text(6.9, 6.5, "Total Score", style=heading_style)

        for index, player in enumerate(players[:8]):
            y_top = 6.0 - (index * 1.6)
            y_center = 5.1 - (index * 1.6)
            self._draw_panel(game, -8.0, y_top, -4.8, y_top - 1.3, fill=(0, 0, 0, 128))
            self._draw_panel(game, -4.5, y_top, 4.5, y_top - 1.3, fill=(0, 0, 0, 128))
            self._draw_panel(game, 4.8, y_top, 9.0, y_top - 1.3, fill=(0, 0, 0, 128))
            rank_label = self._rank_label(index)
            if index > 0 and player.score == players[index - 1].score:
                rank_label = " = "
            ui.draw_centered_text(
                -9.0,
                y_center,
                rank_label,
                style=heading_style,
            )
            self._draw_tank_icon(game, -6.4, y_top - 0.8, player.colour)
            ui.draw_centered_text(-6.4, y_top - 1.15, player.name, style=name_style)
            ui.draw_centered_text(6.9, y_top - 0.9, str(player.score), style=score_style)
            self._draw_score_round_detail(game, player, players_by_number, y_top)

    def _draw_score_round_detail(
        self,
        game,
        player: ReplicatedPlayerState,
        players_by_number: dict[int, ReplicatedPlayerState],
        y_top: float,
    ):
        x_pos = 0.0
        for defeated_player_number in player.round_defeated_player_numbers:
            defeated_player = players_by_number.get(defeated_player_number)
            if defeated_player is None:
                continue
            self._draw_tank_icon(game, -3.55 + x_pos, y_top - 0.82, defeated_player.colour, size=0.24)
            if defeated_player.is_leader:
                game.get_graphics().draw_world_rect(-3.7 + x_pos, y_top - 0.3, -3.6 + x_pos, y_top - 0.9, (128, 128, 128))
                game.get_graphics().draw_world_rect(
                    -3.6 + x_pos,
                    y_top - 0.3,
                    -2.9 + x_pos,
                    y_top - 0.75,
                    defeated_player.colour,
                )
            x_pos += 1.3

    def _draw_shop_overlay(self, game, snapshot: MatchSnapshot, *, local_player_number: int | None = None):
        ui = game.get_ui()
        player = self._local_player(snapshot, local_player_number)
        self._draw_panel(game, -9.4, 6.8, 9.4, -4.8)
        ui.draw_centered_text(0.0, 6.55, "Shop Phase", style=ui.style(0.6, self._bright_text, shadow=True))
        ui.draw_centered_text(
            0.0,
            5.8,
            f"Round {snapshot.current_round + 1} of {snapshot.num_rounds}",
            style=ui.style(0.6, self._bright_text, shadow=True),
        )
        bright_style = ui.style(0.4, (230, 230, 230), spacing=0.3, shadow=True)
        muted_style = ui.style(0.4, self._muted_text, spacing=0.3, shadow=True)
        ui.draw_centered_text(4.0, 5.0, "Cost", style=bright_style)
        ui.draw_centered_text(7.0, 5.0, "Item", style=bright_style)

        items = (
            ("machinegun", "Machine Gun"),
            ("jumpjets", "Jump Jet"),
            ("mirv", "Mirvs"),
            ("missile", "Missiles"),
            ("nuke", "Nukes"),
        )
        y = 4.0
        for weapon_key, label in items:
            selected = player is not None and player.selected_weapon == weapon_key
            if selected:
                self._draw_panel(game, 2.8, y + 0.35, 9.0, y - 0.45, fill=(153, 76, 0, 128))
            cost = self._weapon_cost(weapon_key)
            ui.draw_centered_text(7.0, y, label, style=bright_style)
            ui.draw_centered_text(4.0, y, f"${cost}", style=bright_style)
            y -= 0.8

        for label, cost in self._shop_disabled_items:
            ui.draw_centered_text(7.0, y, label, style=muted_style)
            ui.draw_centered_text(4.0, y, f"${cost}", style=muted_style)
            y -= 0.8

        ui.draw_centered_text(7.0, -4.0, "Done!", style=bright_style)

        if player is not None:
            ui.draw_centered_text(
                -3.0,
                5.0,
                f"{player.name} ${player.money}",
                style=ui.style(0.5, player.colour, spacing=0.38, shadow=True),
            )
            ui.draw_centered_text(
                -3.0,
                4.2,
                f"Selected: {player.selected_weapon.upper()}",
                style=ui.style(0.35, self._bright_text, spacing=0.25, shadow=True),
            )
            ui.draw_centered_text(
                -3.0,
                3.4,
                f"Ammo: {self._weapon_ammo_text(player)}",
                style=ui.style(0.35, self._bright_text, spacing=0.25, shadow=True),
            )
            ui.draw_centered_text(
                -3.0,
                2.4,
                "Use weapon up/down to choose and fire to buy",
                style=ui.style(0.28, self._cyan_text, spacing=0.2, shadow=True),
            )

    def _draw_winner_overlay(self, game, snapshot: MatchSnapshot):
        ui = game.get_ui()
        winners = [
            player
            for player in self._ordered_players(snapshot)
            if snapshot.winner_player_number is None or player.player_number == snapshot.winner_player_number
        ]
        is_draw = len(winners) > 1
        title = "It's a tie!" if is_draw else "We have a winner!"
        ui.draw_centered_text(0.0, 6.5, "Final Result", style=ui.style(0.6, self._bright_text, shadow=True))
        ui.draw_centered_text(0.0, 5.5, title, style=ui.style(0.6, self._bright_text, shadow=True))

        row = 0
        col = 0
        cols_count = (len(winners) - 1) // 4 if winners else 0
        winners_in_row = len(winners) if len(winners) < 5 else 4
        col_start = -((winners_in_row - 1) * 2.0)

        for player in winners:
            x = col_start + (row * 4.0)
            y = (cols_count * 2.0) - (col * 4.0)
            self._draw_tank_icon(game, x, y, player.colour, size=1.5)
            ui.draw_centered_text(
                x,
                y - 1.2,
                player.name,
                style=ui.style(0.45, self._bright_text, spacing=0.35, shadow=True),
            )
            ui.draw_centered_text(
                x,
                y - 2.0,
                "Winner!",
                style=ui.style(0.55, self._bright_text, spacing=0.45, shadow=True),
            )
            row += 1
            if row > 3:
                row = 0
                col += 1
                remaining = len(winners) - (col * 4)
                winners_in_row = remaining if remaining < 5 else 4
                col_start = -((winners_in_row - 1) * 2.0)

    def _weapon_cost(self, weapon_key: str) -> int:
        if weapon_key == "jumpjets":
            return 50
        if weapon_key not in WEAPON_SPECS:
            return 0
        return int(cast(int, WEAPON_SPECS[weapon_key]["cost"]))


@dataclass(frozen=True)
class LocalPlayerConfig:
    slot: int
    name: str
    is_human: bool
    controller: int
    colour: tuple[int, int, int]


@dataclass(frozen=True)
class LocalMenuSelection:
    action: str
    ai_players: int
    num_rounds: int = 10
    players: tuple[LocalPlayerConfig, ...] = ()
    local_controller: int = 0
    requested_slot: int | None = 0
    launch_target: str | None = None
    persist_mode: bool = True
    connect_host: str = ""
    connect_port: int = 0
    connect_password: str = ""
    connect_entry: ServerListEntry | None = None


@dataclass
class _LocalPlayerState:
    enabled: bool
    name: str
    is_human: bool = True
    controller: int = 0


@dataclass
class _LocalMenuState:
    screen: str
    players: list[_LocalPlayerState]
    num_rounds: int
    resolution_index: int
    fullscreen: bool
    status_message: str = ""
    browser_tab: str = "internet"
    browser_entries: tuple[ServerListEntry, ...] = ()
    selected_server_index: int = 0
    browser_status: str = "No servers have been queried yet."
    browser_scroll_index: int = 0
    browser_sort_column: str = "latency"
    browser_sort_desc: bool = False
    browser_show_all: bool = False
    browser_filter_text: str = ""
    browser_filter_show_full: bool = True
    browser_filter_show_empty: bool = True
    browser_filter_show_passworded: bool = True
    browser_filter_secure_only: bool = False
    browser_filter_region: str = ""
    browser_filter_max_latency: int | None = None
    add_server_value: str = "127.0.0.1:27015"
    connect_password_value: str = ""
    pending_connect_endpoint: str = ""
    last_clicked_server_index: int = -1
    last_clicked_server_time: float = 0.0
    browser_scroll_dragging: bool = False
    browser_scroll_drag_offset: float = 0.0


class CanonicalLocalMenu(_ClassicThemeMixin):
    _resolutions = (
        (640, 480),
        (800, 600),
        (1024, 768),
        (1280, 960),
        (1280, 1024),
        (1600, 1200),
    )
    _round_options = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50)
    _row_y_positions = tuple(3.5 - (index * 0.8) for index in range(8))
    _controller_labels = (
        "Keyboard1",
        "Keyboard2",
        "Joystick1",
        "Joystick2",
        "Joystick3",
        "Joystick4",
        "Joystick5",
        "Joystick6",
        "Joystick7",
        "Joystick8",
    )
    _browser_tabs = (
        ("internet", "Internet"),
        ("favorites", "Favorites"),
        ("unique", "Unique"),
        ("history", "History"),
        ("lan", "Lan"),
    )
    _browser_max_rows = 24
    _browser_max_latency_options: tuple[int | None, ...] = (None, 50, 100, 150, 250, 500)
    _browser_region_options = ("", "world", "na", "sa", "eu", "asia", "local")

    def __init__(self, *, server_scanner_factory=None):
        self._server_scanner_factory = server_scanner_factory

    def run(
        self,
        game,
        *,
        player_name: str,
        ai_players: int = 1,
        max_frames: int | None = None,
    ) -> LocalMenuSelection:
        interface = game.get_interface()
        interface.enable_mouse(True)
        frames = 0
        state = self._build_initial_state(game, ai_players=ai_players)
        server_scanner: GroundfireServerScanner | None = None
        last_left_pressed = False
        last_fire_pressed = [False] * len(self._controller_labels)

        try:
            while max_frames is None or frames < max_frames:
                game.get_clock().tick()
                if interface.should_close():
                    return LocalMenuSelection("quit", self._ai_player_count(state), state.num_rounds)

                set_caption = getattr(interface, "set_window_caption", None)
                if callable(set_caption):
                    set_caption("Groundfire")

                self._apply_fire_auto_join(game, state, last_fire_pressed)
                if state.screen in {"servers", "server_filters", "add_server", "server_password"}:
                    server_scanner = self._ensure_server_scanner(server_scanner)
                    self._refresh_server_entries(state, server_scanner)

                get_events = getattr(interface, "get_input_events", None)
                if callable(get_events):
                    key_names_getter = getattr(interface, "get_key_names", None)
                    key_names = key_names_getter() if callable(key_names_getter) else {}
                    selection = self._handle_input_events(
                        state,
                        tuple(get_events()),
                        key_names,
                        server_scanner=server_scanner,
                    )
                    if selection is not None:
                        return selection

                left_pressed = bool(interface.get_mouse_button(0))
                clicked = left_pressed and not last_left_pressed

                interface.start_draw()
                try:
                    rects = self._draw_screen(game, state, player_name=player_name)
                finally:
                    interface.end_draw()

                mouse_x, mouse_y = interface.get_mouse_pos()
                if (
                    state.screen == "servers"
                    and left_pressed
                    and state.browser_scroll_dragging
                ):
                    self._drag_browser_scrollbar(state, rects, mouse_y)
                elif not left_pressed:
                    state.browser_scroll_dragging = False
                if clicked:
                    selection = self._handle_click(game, state, rects, mouse_x, mouse_y, server_scanner=server_scanner)
                    if selection is not None:
                        return selection

                last_left_pressed = left_pressed
                frames += 1

            return LocalMenuSelection("quit", self._ai_player_count(state), state.num_rounds)
        finally:
            if server_scanner is not None:
                server_scanner.close()
            interface.enable_mouse(False)

    def _build_initial_state(self, game, *, ai_players: int) -> _LocalMenuState:
        width, height, fullscreen = game.get_interface().get_window_settings()
        players = [
            _LocalPlayerState(
                enabled=(index == 0),
                name=f"Player {index + 1}",
                is_human=True,
                controller=min(index, len(self._controller_labels) - 1),
            )
            for index in range(8)
        ]
        for index in range(min(max(0, ai_players), 7)):
            players[index + 1].enabled = True
            players[index + 1].is_human = False
        return _LocalMenuState(
            screen="main",
            players=players,
            num_rounds=10,
            resolution_index=self._find_resolution_index(width, height),
            fullscreen=bool(fullscreen),
        )

    def _ensure_server_scanner(
        self,
        server_scanner: GroundfireServerScanner | None,
    ) -> GroundfireServerScanner:
        if server_scanner is not None:
            return server_scanner
        if self._server_scanner_factory is not None:
            scanner = self._server_scanner_factory()
        else:
            scanner = GroundfireServerScanner(
                server_book=ServerBook(default_server_book_path(PROJECT_ROOT)),
            )
        scanner.open()
        scanner.refresh()
        refresh_masters = getattr(scanner, "refresh_master_servers", None)
        if callable(refresh_masters):
            refresh_masters(timeout=0.02)
        return scanner

    def _refresh_server_entries(
        self,
        state: _LocalMenuState,
        scanner: GroundfireServerScanner,
        *,
        raw_entries: tuple[ServerListEntry, ...] | None = None,
        status: str | None = None,
    ):
        if raw_entries is None:
            raw_entries = (
                scanner.all_entries()
                if state.browser_show_all
                else scanner.entries_for_tab(state.browser_tab)
            )
        self._set_browser_entries(state, raw_entries, status=status)

    def _set_browser_entries(
        self,
        state: _LocalMenuState,
        entries: tuple[ServerListEntry, ...],
        *,
        status: str | None = None,
    ):
        state.browser_entries = self._filtered_browser_entries(entries, state)
        self._clamp_browser_selection(state)
        if state.browser_entries:
            if status is not None:
                state.browser_status = status
            elif self._browser_status_is_placeholder(state.browser_status):
                state.browser_status = ""
            return
        state.browser_status = status or self._empty_browser_message(state)

    def _draw_screen(
        self,
        game,
        state: _LocalMenuState,
        *,
        player_name: str,
    ) -> dict[str, tuple[float, float, float, float]]:
        self._draw_background(game)
        if state.screen == "main":
            return self._draw_main_menu(game)
        if state.screen == "options":
            return self._draw_options_menu(game, state)
        if state.screen == "select_players":
            return self._draw_select_players_menu(game, state)
        if state.screen == "quit":
            return self._draw_quit_menu(game)
        if state.screen in {"servers", "server_filters", "add_server", "server_password"}:
            return self._draw_server_browser(game, state)
        self._draw_logo(game)
        return {}

    def _draw_main_menu(self, game) -> dict[str, tuple[float, float, float, float]]:
        self._draw_logo(game)
        self._draw_panel(game, -7.0, -3.05, 7.0, -7.15)
        rects = {
            "start": (-4.0, -3.25, 4.0, -4.05),
            "find_servers": (-4.0, -4.15, 4.0, -4.95),
            "options": (-4.0, -5.05, 4.0, -5.85),
            "quit": (-4.0, -5.95, 4.0, -6.75),
        }
        for key, y, label in (
            ("start", -3.65, "Start Game"),
            ("find_servers", -4.55, "Find Servers"),
            ("options", -5.45, "Options"),
            ("quit", -6.35, "Quit"),
        ):
            self._draw_text_button(game, text=label, x=0.0, y=y, size=0.7, fill=self._brown_fill)

        ui = game.get_ui()
        ui.draw_centered_text(
            0.0,
            0.0,
            "0.25 (Python Port)",
            style=ui.style(0.4, self._bright_text, spacing=0.35, shadow=True),
        )
        ui.draw_centered_text(
            0.0,
            -0.5,
            "www.groundfire.net",
            style=ui.style(0.4, self._bright_text, spacing=0.35, shadow=True),
        )
        ui.draw_centered_text(
            0.0,
            -2.5,
            "Copyright Tom Russell 2004",
            style=ui.style(0.4, self._bright_text, spacing=0.35, shadow=True),
        )
        ui.draw_centered_text(
            0.0,
            -2.9,
            "All Rights Reserved",
            style=ui.style(0.4, self._bright_text, spacing=0.35, shadow=True),
        )
        return rects

    def _draw_server_browser(
        self,
        game,
        state: _LocalMenuState,
    ) -> dict[str, tuple[float, float, float, float]]:
        ui = game.get_ui()
        rects: dict[str, tuple[float, float, float, float]] = {
            "close_servers": (9.35, 7.05, 9.8, 6.55),
            "change_filters": (-9.7, -5.95, -7.8, -6.55),
            "connect": (8.55, -5.95, 9.75, -6.55),
            "open_all": (5.9, -6.75, 9.55, -7.15),
            "scroll_up": (9.55, 4.85, 9.75, 4.45),
            "scroll_down": (9.55, -5.45, 9.75, -5.85),
        }
        mouse_x, mouse_y = game.get_interface().get_mouse_pos()
        left_down = self._mouse_left_down(game)

        self._draw_panel(game, -9.95, 7.35, 9.95, -7.35, fill=self._browser_frame_fill)
        self._draw_panel(game, -9.75, 6.55, 9.75, -6.95, fill=self._browser_body_fill)
        ui.draw_text(-9.55, 6.82, "Servers", style=ui.style(0.42, self._bright_text, spacing=0.2, shadow=True))
        ui.draw_centered_text(9.58, 6.47, "x", style=ui.style(0.45, self._bright_text, shadow=True))

        tab_left = -9.75
        for tab_key, label in self._browser_tabs:
            width = 1.45 if tab_key != "favorites" else 1.65
            rect = (tab_left, 6.05, tab_left + width, 5.45)
            rects[f"tab_{tab_key}"] = rect
            active = state.browser_tab == tab_key
            hovered = self._contains(rect, mouse_x, mouse_y)
            fill = self._tab_fill(active=active, hovered=hovered, pressed=hovered and left_down)
            self._draw_panel(game, rect[0], rect[1], rect[2], rect[3], fill=fill)
            ui.draw_text(
                rect[0] + 0.12,
                rect[3] + 0.1,
                label,
                style=ui.style(
                    0.25,
                    self._gold_text if state.browser_tab == tab_key else self._bright_text,
                    spacing=0.1,
                    shadow=True,
                ),
            )
            tab_left += width + 0.05

        table_left, table_right = -9.75, 9.55
        header_top, header_bottom = 5.25, 4.85
        self._draw_panel(game, table_left, header_top, table_right, header_bottom, fill=self._browser_header_fill)
        columns = self._browser_columns_for_tab(state.browser_tab)
        for column in columns:
            key, label, left, right = column
            rects[f"sort_{key}"] = (left, header_top, right, header_bottom)
            suffix = ""
            if state.browser_sort_column == key:
                suffix = " v" if state.browser_sort_desc else " ^"
            ui.draw_text(
                left + 0.07,
                4.92,
                label + suffix,
                style=ui.style(0.22, self._bright_text, spacing=0.09, shadow=True),
            )

        row_y = 4.48
        visible_entries = state.browser_entries[
            state.browser_scroll_index : state.browser_scroll_index + self._browser_max_rows
        ]
        for offset, entry in enumerate(visible_entries):
            index = state.browser_scroll_index + offset
            selected = index == state.selected_server_index
            row_top = row_y + 0.22
            row_bottom = row_y - 0.2
            rects[f"server_row_{index}"] = (table_left, row_top, table_right, row_bottom)
            if selected:
                self._draw_panel(game, table_left, row_top, table_right, row_bottom, fill=self._browser_selected_fill)
            elif self._contains(rects[f"server_row_{index}"], mouse_x, mouse_y):
                self._draw_panel(game, table_left, row_top, table_right, row_bottom, fill=self._browser_hover_fill)
            text_colour = self._bright_text if selected else self._browser_text
            small = ui.style(0.2, text_colour, spacing=0.08, shadow=True)
            self._draw_browser_row(game, entry, columns, row_y, style=small)
            row_y -= 0.42

        if not state.browser_entries and state.browser_status:
            ui.draw_text(
                -9.55,
                4.35,
                state.browser_status,
                style=ui.style(0.26, self._bright_text, spacing=0.11, shadow=True),
            )

        self._draw_browser_scrollbar(game, state, rects)

        if state.browser_status and state.browser_entries:
            ui.draw_text(
                -9.55,
                -5.65,
                self._shorten(state.browser_status, 92),
                style=ui.style(0.2, self._browser_dim_text, spacing=0.08, shadow=True),
            )

        if state.browser_tab == "favorites":
            rects["add_favorite"] = (3.0, -5.95, 5.4, -6.55)
            rects["add_server"] = (5.5, -5.95, 7.1, -6.55)
            rects["refresh"] = (7.2, -5.95, 8.45, -6.55)
            self._draw_browser_button(
                game,
                rects["add_favorite"],
                "Add Current Server",
                enabled=bool(state.browser_entries),
            )
            self._draw_browser_button(game, rects["add_server"], "Add a Server", enabled=True)
            self._draw_browser_button(game, rects["refresh"], "Refresh", enabled=True)
        elif state.browser_tab in {"history", "lan"}:
            rects["refresh"] = (7.1, -5.95, 8.45, -6.55)
            self._draw_browser_button(game, rects["refresh"], "Refresh", enabled=True)
        else:
            rects["add_favorite"] = (3.0, -5.95, 5.0, -6.55)
            rects["quick_refresh"] = (5.1, -5.95, 6.65, -6.55)
            rects["refresh_all"] = (6.75, -5.95, 8.45, -6.55)
            self._draw_browser_button(
                game,
                rects["add_favorite"],
                "Add Favorite",
                enabled=bool(state.browser_entries),
            )
            self._draw_browser_button(
                game,
                rects["quick_refresh"],
                "Quick refresh",
                enabled=bool(state.browser_entries),
            )
            self._draw_browser_button(game, rects["refresh_all"], "Refresh all", enabled=True)

        self._draw_browser_button(game, rects["change_filters"], "Change filters", enabled=True)
        self._draw_browser_button(game, rects["connect"], "Connect", enabled=bool(state.browser_entries))
        ui.draw_text(
            6.15,
            -7.08,
            "Open the list of all servers (5300+)",
            style=ui.style(0.2, self._cyan_text, spacing=0.08, shadow=True),
        )
        self._draw_resize_grip(game)
        if state.screen == "server_filters":
            rects.update(self._draw_filter_dialog(game, state))
        elif state.screen == "add_server":
            rects.update(self._draw_add_server_dialog(game, state))
        elif state.screen == "server_password":
            rects.update(self._draw_password_dialog(game, state))
        return rects

    def _browser_columns_for_tab(self, tab: str) -> tuple[tuple[str, str, float, float], ...]:
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

    def _draw_browser_row(self, game, entry: ServerListEntry, columns, y: float, *, style):
        ui = game.get_ui()
        values = {
            "name": self._server_display_name(entry),
            "description": entry.description,
            "game": entry.game,
            "players": f"{entry.player_count}/{entry.max_players}",
            "map": entry.map_name,
            "latency": "-" if entry.latency_ms is None else str(entry.latency_ms),
            "last_played": entry.last_played or "-",
        }
        for key, _label, left, right in columns:
            width_chars = max(4, int((right - left) * 5.0))
            ui.draw_text(left + 0.07, y - 0.12, self._shorten(values.get(key, ""), width_chars), style=style)

    def _server_display_name(self, entry: ServerListEntry) -> str:
        prefix = "[P] " if entry.requires_password else ""
        return prefix + entry.name

    def _draw_browser_scrollbar(self, game, state: _LocalMenuState, rects):
        mouse_x, mouse_y = game.get_interface().get_mouse_pos()
        left_down = self._mouse_left_down(game)
        self._draw_panel(game, 9.55, 4.85, 9.75, -5.85, fill=(0, 0, 0, 135))
        self._draw_panel(
            game,
            *rects["scroll_up"],
            fill=self._browser_control_fill(
                enabled=True,
                hovered=self._contains(rects["scroll_up"], mouse_x, mouse_y),
                pressed=left_down and self._contains(rects["scroll_up"], mouse_x, mouse_y),
            ),
        )
        self._draw_panel(
            game,
            *rects["scroll_down"],
            fill=self._browser_control_fill(
                enabled=True,
                hovered=self._contains(rects["scroll_down"], mouse_x, mouse_y),
                pressed=left_down and self._contains(rects["scroll_down"], mouse_x, mouse_y),
            ),
        )
        ui = game.get_ui()
        ui.draw_centered_text(9.65, 4.47, "^", style=ui.style(0.2, self._bright_text, spacing=0.08))
        ui.draw_centered_text(9.65, -5.82, "v", style=ui.style(0.2, self._bright_text, spacing=0.08))
        max_scroll = max(0, len(state.browser_entries) - self._browser_max_rows)
        if max_scroll <= 0:
            thumb = (9.57, 4.35, 9.73, -5.35)
        else:
            track_top = 4.35
            track_bottom = -5.35
            track_height = track_top - track_bottom
            visible_fraction = self._browser_max_rows / max(1, len(state.browser_entries))
            thumb_height = max(0.65, track_height * visible_fraction)
            travel = max(0.0, track_height - thumb_height)
            thumb_top = track_top - travel * (state.browser_scroll_index / max_scroll)
            thumb = (9.57, thumb_top, 9.73, thumb_top - thumb_height)
        rects["scroll_thumb"] = thumb
        thumb_hovered = self._contains(thumb, mouse_x, mouse_y) or state.browser_scroll_dragging
        self._draw_panel(
            game,
            *thumb,
            fill=self._browser_control_fill(
                enabled=True,
                hovered=thumb_hovered,
                pressed=left_down and thumb_hovered,
            ),
        )

    def _draw_filter_dialog(self, game, state: _LocalMenuState) -> dict[str, tuple[float, float, float, float]]:
        ui = game.get_ui()
        rects = {
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
        self._draw_panel(game, -5.8, 3.3, 5.8, -4.5, fill=self._browser_dialog_fill)
        self._draw_panel(game, -5.8, 3.3, 5.8, 2.45, fill=self._browser_header_fill)
        ui.draw_text(-5.35, 2.8, "Filters", style=ui.style(0.38, self._bright_text, spacing=0.16, shadow=True))
        ui.draw_text(-5.25, 1.55, "Server / map", style=ui.style(0.26, self._bright_text, spacing=0.11))
        self._draw_text_field(game, rects["filter_text"], state.browser_filter_text, active=True)
        self._draw_checkbox(game, rects["filter_full"], state.browser_filter_show_full, "Show full servers")
        self._draw_checkbox(game, rects["filter_empty"], state.browser_filter_show_empty, "Show empty servers")
        self._draw_checkbox(
            game,
            rects["filter_password"],
            state.browser_filter_show_passworded,
            "Show passworded servers",
        )
        self._draw_checkbox(game, rects["filter_secure"], state.browser_filter_secure_only, "Secure servers only")
        ui.draw_text(-5.25, -1.8, "Region", style=ui.style(0.26, self._bright_text, spacing=0.11))
        self._draw_browser_button(
            game,
            rects["filter_region"],
            self._region_filter_label(state.browser_filter_region),
            enabled=True,
        )
        ui.draw_text(-5.25, -2.8, "Maximum latency", style=ui.style(0.26, self._bright_text, spacing=0.11))
        latency_label = self._latency_filter_label(state.browser_filter_max_latency)
        self._draw_browser_button(game, rects["filter_latency"], latency_label, enabled=True)
        self._draw_browser_button(game, rects["filter_clear"], "Clear", enabled=True)
        self._draw_browser_button(game, rects["filter_ok"], "Apply", enabled=True)
        self._draw_browser_button(game, rects["filter_cancel"], "Close", enabled=True)
        return rects

    def _draw_add_server_dialog(self, game, state: _LocalMenuState) -> dict[str, tuple[float, float, float, float]]:
        ui = game.get_ui()
        rects = {
            "add_server_text": (-4.7, 0.85, 4.7, 0.2),
            "add_server_ok": (1.3, -1.05, 3.2, -1.65),
            "add_server_cancel": (3.35, -1.05, 5.15, -1.65),
        }
        self._draw_panel(game, -5.8, 2.45, 5.8, -2.3, fill=self._browser_dialog_fill)
        self._draw_panel(game, -5.8, 2.45, 5.8, 1.55, fill=self._browser_header_fill)
        ui.draw_text(-5.35, 1.9, "Add a Server", style=ui.style(0.38, self._bright_text, spacing=0.16, shadow=True))
        ui.draw_text(-5.15, 0.35, "Address", style=ui.style(0.26, self._bright_text, spacing=0.11))
        self._draw_text_field(game, rects["add_server_text"], state.add_server_value, active=True)
        self._draw_browser_button(game, rects["add_server_ok"], "Add", enabled=True)
        self._draw_browser_button(game, rects["add_server_cancel"], "Cancel", enabled=True)
        return rects

    def _draw_password_dialog(self, game, state: _LocalMenuState) -> dict[str, tuple[float, float, float, float]]:
        ui = game.get_ui()
        rects = {
            "password_text": (-4.7, 0.85, 4.7, 0.2),
            "password_ok": (1.3, -1.05, 3.2, -1.65),
            "password_cancel": (3.35, -1.05, 5.15, -1.65),
        }
        self._draw_panel(game, -5.8, 2.45, 5.8, -2.3, fill=self._browser_dialog_fill)
        self._draw_panel(game, -5.8, 2.45, 5.8, 1.55, fill=self._browser_header_fill)
        ui.draw_text(-5.35, 1.9, "Server Password", style=ui.style(0.38, self._bright_text, spacing=0.16, shadow=True))
        ui.draw_text(-5.15, 0.35, state.pending_connect_endpoint, style=ui.style(0.24, self._bright_text, spacing=0.1))
        masked = "*" * len(state.connect_password_value)
        self._draw_text_field(game, rects["password_text"], masked, active=True)
        self._draw_browser_button(game, rects["password_ok"], "Connect", enabled=True)
        self._draw_browser_button(game, rects["password_cancel"], "Cancel", enabled=True)
        return rects

    def _draw_text_field(self, game, rect, text: str, *, active: bool):
        left, top, right, bottom = rect
        fill = self._browser_input_fill if active else (0, 0, 0, 120)
        self._draw_panel(game, left, top, right, bottom, fill=fill)
        shown = self._shorten(text or "", max(8, int((right - left) * 6.0)))
        game.get_ui().draw_text(
            left + 0.15,
            bottom + 0.14,
            shown + ("_" if active else ""),
            style=game.get_ui().style(0.26, self._bright_text, spacing=0.1),
        )

    def _draw_checkbox(self, game, rect, checked: bool, label: str):
        left, top, right, bottom = rect
        self._draw_panel(game, left, top, right, bottom, fill=self._browser_input_fill)
        if checked:
            game.get_ui().draw_centered_text(
                (left + right) / 2.0,
                bottom + 0.08,
                "x",
                style=game.get_ui().style(0.3, self._gold_text, spacing=0.1),
            )
        game.get_ui().draw_text(
            right + 0.25,
            bottom + 0.1,
            label,
            style=game.get_ui().style(0.25, self._bright_text, spacing=0.1),
        )

    def _draw_browser_button(self, game, rect, label: str, *, enabled: bool):
        mouse_x, mouse_y = game.get_interface().get_mouse_pos()
        hovered = enabled and self._contains(rect, mouse_x, mouse_y)
        fill = self._browser_control_fill(
            enabled=enabled,
            hovered=hovered,
            pressed=hovered and self._mouse_left_down(game),
        )
        text = self._bright_text if enabled else self._muted_text
        left, top, right, bottom = rect
        self._draw_panel(game, left, top, right, bottom, fill=fill)
        game.get_ui().draw_centered_text(
            (left + right) / 2.0,
            bottom + 0.1,
            label,
            style=game.get_ui().style(0.22, text, spacing=0.09, shadow=enabled),
        )

    def _browser_control_fill(self, *, enabled: bool, hovered: bool, pressed: bool):
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

    def _mouse_left_down(self, game) -> bool:
        getter = getattr(game.get_interface(), "get_mouse_button", None)
        return bool(getter(0)) if callable(getter) else False

    def _draw_resize_grip(self, game):
        x0, y0 = 9.52, -7.18
        for offset in (0.0, 0.12, 0.24):
            self._draw_panel(
                game,
                x0 + offset,
                y0 + 0.02,
                x0 + offset + 0.22,
                y0 - 0.03,
                fill=(255, 255, 255, 170),
            )

    def _shorten(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[: max(1, max_chars - 1)] + "..."

    def _draw_options_menu(
        self,
        game,
        state: _LocalMenuState,
    ) -> dict[str, tuple[float, float, float, float]]:
        ui = game.get_ui()
        self._draw_panel(game, -7.0, 3.0, 7.0, -3.0)
        self._draw_panel(game, -7.0, -4.4, 7.0, -6.6)
        self._draw_panel(game, -6.0, 1.4, 6.0, 0.6, fill=(153, 76, 0, 128))
        self._draw_panel(game, -6.0, 0.4, 6.0, -0.4, fill=(153, 76, 0, 128))
        self._draw_panel(game, -6.0, -0.6, 6.0, -1.4, fill=(153, 76, 0, 128))

        ui.draw_centered_text(0.0, 6.5, "Options", style=ui.style(0.6, self._bright_text, shadow=True))
        label_style = ui.style(0.6, self._cyan_text)
        ui.draw_centered_text(-3.0, 0.7, "Resolution:", style=label_style)
        ui.draw_centered_text(-3.0, -0.3, "Screen Mode:", style=label_style)

        rects = {
            "resolution_prev": (1.0, 1.3, 1.6, 0.7),
            "resolution_next": (4.4, 1.3, 5.0, 0.7),
            "mode_prev": (1.0, 0.3, 1.6, -0.3),
            "mode_next": (4.4, 0.3, 5.0, -0.3),
            "set_controls": (-4.0, -0.6, 4.0, -1.4),
            "apply": (-4.0, -4.6, 4.0, -5.4),
            "back": (-4.0, -5.6, 4.0, -6.4),
        }
        self._draw_cycle_control(
            game,
            value=self._resolution_label(state.resolution_index),
            center_x=3.0,
            center_y=1.0,
            left_rect=rects["resolution_prev"],
            right_rect=rects["resolution_next"],
        )
        self._draw_cycle_control(
            game,
            value="Fullscreen" if state.fullscreen else "Windowed",
            center_x=3.0,
            center_y=0.0,
            left_rect=rects["mode_prev"],
            right_rect=rects["mode_next"],
        )
        self._draw_text_button(game, text="Set Controls", x=0.0, y=-1.0, size=0.6, fill=None)
        self._draw_text_button(game, text="Apply", x=0.0, y=-5.0, size=0.7, fill=self._brown_fill)
        self._draw_text_button(game, text="Back", x=0.0, y=-6.0, size=0.7, fill=self._brown_fill)
        if state.status_message:
            ui.draw_centered_text(
                0.0,
                -2.3,
                state.status_message,
                style=ui.style(0.28, self._bright_text, spacing=0.2, shadow=True),
            )
        return rects

    def _draw_select_players_menu(
        self,
        game,
        state: _LocalMenuState,
    ) -> dict[str, tuple[float, float, float, float]]:
        ui = game.get_ui()
        ui.draw_centered_text(0.0, 6.5, "Select Players", style=ui.style(0.6, self._bright_text, shadow=True))
        ui.draw_centered_text(
            0.0,
            5.5,
            "Add a player by clicking on a '+' icon or press the 'Fire' Button on any Controller",
            style=ui.style(0.4, self._bright_text, spacing=0.35, shadow=True),
        )

        for pts, colour in (
            ([(-7.0, -6.6), (7.0, -6.6), (7.0, -3.4), (-7.0, -3.4)], (0, 0, 0, 128)),
            ([(-4.0, -4.4), (4.0, -4.4), (4.0, -3.6), (-4.0, -3.6)], (153, 76, 0, 128)),
            ([(-4.0, -5.4), (4.0, -5.4), (4.0, -4.6), (-4.0, -4.6)], (153, 76, 0, 128)),
            ([(-4.0, -6.4), (4.0, -6.4), (4.0, -5.6), (-4.0, -5.6)], (153, 76, 0, 128)),
            ([(-9.0, -2.6), (9.0, -2.6), (9.0, 4.7), (-9.0, 4.7)], (0, 0, 0, 128)),
        ):
            game.get_graphics().draw_world_polygon(pts, colour)

        rects: dict[str, tuple[float, float, float, float]] = {
            "rounds_prev": (1.15, -3.7, 1.75, -4.3),
            "rounds_next": (4.25, -3.7, 4.85, -4.3),
            "start": (-4.0, -4.6, 4.0, -5.4),
            "back": (-4.0, -5.6, 4.0, -6.4),
        }

        for index, y in enumerate(self._row_y_positions):
            player = state.players[index]
            enabled = player.enabled
            if enabled:
                self._draw_panel(game, -8.8, y + 0.3, 8.8, y - 0.3, fill=(153, 76, 0, 128))

            tank_colour = self._player_colour(game, index)
            if not enabled:
                tank_colour = (
                    max(0, tank_colour[0] // 4),
                    max(0, tank_colour[1] // 4),
                    max(0, tank_colour[2] // 4),
                )
            self._draw_tank_icon(game, -6.8, y + 0.1, tank_colour, size=0.38)

            add_rect = self._icon_rect(-8.5, y, size=0.6)
            remove_rect = self._icon_rect(-7.8, y, size=0.6)
            rects[f"add_{index}"] = add_rect
            rects[f"remove_{index}"] = remove_rect
            self._draw_icon_button(game, add_rect, texture_id=10, fallback="+", enabled=not enabled)
            self._draw_icon_button(game, remove_rect, texture_id=11, fallback="-", enabled=enabled)

            if enabled:
                ui.draw_text(
                    -6.0,
                    y - 0.2,
                    player.name,
                    style=ui.style(0.5, self._bright_text, spacing=0.4),
                )
                mode_left, mode_right = self._selector_arrow_rects(1.6, y, width=3.0, size=0.5)
                controller_left, controller_right = self._selector_arrow_rects(6.4, y, width=3.2, size=0.5)
                rects[f"mode_prev_{index}"] = mode_left
                rects[f"mode_next_{index}"] = mode_right
                rects[f"controller_prev_{index}"] = controller_left
                rects[f"controller_next_{index}"] = controller_right
                self._draw_selector(
                    game,
                    value="Human" if player.is_human else "Computer",
                    center_x=1.6,
                    center_y=y,
                    size=0.5,
                    left_rect=mode_left,
                    right_rect=mode_right,
                    enabled=True,
                )
                self._draw_selector(
                    game,
                    value=self._controller_label(player.controller),
                    center_x=6.4,
                    center_y=y,
                    size=0.5,
                    left_rect=controller_left,
                    right_rect=controller_right,
                    enabled=player.is_human,
                )

        header_style = ui.style(0.3, self._cyan_text, spacing=0.25)
        ui.draw_centered_text(-8.0, 4.3, "Add/Remove", style=header_style)
        ui.draw_centered_text(-8.0, 4.0, "Player", style=header_style)
        ui.draw_centered_text(-4.0, 4.1, "Name", style=header_style)
        ui.draw_centered_text(1.6, 4.1, "Controlled by", style=header_style)
        ui.draw_centered_text(6.3, 4.1, "Controller", style=header_style)
        ui.draw_centered_text(
            -2.0,
            -4.35,
            "Rounds :",
            style=ui.style(0.7, self._bright_text, spacing=0.6, shadow=True),
        )
        self._draw_cycle_control(
            game,
            value=str(state.num_rounds),
            center_x=2.0,
            center_y=-4.0,
            left_rect=rects["rounds_prev"],
            right_rect=rects["rounds_next"],
        )
        start_fill = self._brown_fill if self._total_players(state) > 1 else (60, 60, 60, 128)
        self._draw_text_button(game, text="Start!", x=0.0, y=-5.0, size=0.7, fill=start_fill)
        self._draw_text_button(game, text="Back", x=0.0, y=-6.0, size=0.7, fill=self._brown_fill)
        return rects

    def _draw_quit_menu(self, game) -> dict[str, tuple[float, float, float, float]]:
        self._draw_logo(game)
        self._draw_panel(game, -7.0, -3.4, 7.0, -6.6)
        rects = {
            "yes": (-4.0, -4.6, 4.0, -5.4),
            "no": (-4.0, -5.6, 4.0, -6.4),
        }
        self._draw_text_button(game, text="Yes", x=0.0, y=-5.0, size=0.7, fill=self._brown_fill)
        self._draw_text_button(game, text="No", x=0.0, y=-6.0, size=0.7, fill=self._brown_fill)
        game.get_ui().draw_centered_text(
            0.0,
            -4.35,
            "Are you sure?",
            style=game.get_ui().style(0.7, self._bright_text, spacing=0.6, shadow=True),
        )
        return rects

    def _draw_cycle_control(self, game, *, value: str, center_x: float, center_y: float, left_rect, right_rect):
        ui = game.get_ui()
        self._draw_icon_button(game, left_rect, texture_id=11, fallback="<", enabled=True)
        self._draw_icon_button(game, right_rect, texture_id=10, fallback=">", enabled=True)
        ui.draw_centered_text(
            center_x,
            center_y - 0.35,
            value,
            style=ui.style(0.55, self._bright_text, spacing=0.4, shadow=True),
        )

    def _draw_icon_button(self, game, rect, *, texture_id: int, fallback: str, enabled: bool):
        left, top, right, bottom = rect
        fill = (153, 76, 0, 128) if enabled else (60, 60, 60, 96)
        self._draw_panel(game, left, top, right, bottom, fill=fill)
        get_texture_surface = getattr(game.get_interface(), "get_texture_surface", None)
        if enabled and callable(get_texture_surface) and get_texture_surface(texture_id) is not None:
            game.get_graphics().draw_texture_world_rect(texture_id, left, top, right, bottom)
            return
        game.get_ui().draw_centered_text(
            (left + right) / 2.0,
            bottom + 0.02,
            fallback,
            style=game.get_ui().style(0.5, self._bright_text if enabled else self._muted_text, shadow=True),
        )

    def _handle_click(
        self,
        game,
        state: _LocalMenuState,
        rects: dict[str, tuple[float, float, float, float]],
        mouse_x: float,
        mouse_y: float,
        *,
        server_scanner: GroundfireServerScanner | None = None,
    ) -> LocalMenuSelection | None:
        if state.screen == "main":
            if self._contains(rects.get("start"), mouse_x, mouse_y):
                state.screen = "select_players"
            elif self._contains(rects.get("find_servers"), mouse_x, mouse_y):
                state.screen = "servers"
                state.browser_status = "Searching for Groundfire servers..."
            elif self._contains(rects.get("options"), mouse_x, mouse_y):
                state.screen = "options"
            elif self._contains(rects.get("quit"), mouse_x, mouse_y):
                state.screen = "quit"
            return None

        if state.screen == "servers":
            return self._handle_server_browser_click(state, rects, mouse_x, mouse_y, server_scanner=server_scanner)

        if state.screen == "server_filters":
            return self._handle_filter_click(state, rects, mouse_x, mouse_y, server_scanner=server_scanner)

        if state.screen == "add_server":
            return self._handle_add_server_click(state, rects, mouse_x, mouse_y, server_scanner=server_scanner)

        if state.screen == "server_password":
            return self._handle_password_click(state, rects, mouse_x, mouse_y, server_scanner=server_scanner)

        if state.screen == "options":
            if self._contains(rects.get("resolution_prev"), mouse_x, mouse_y):
                state.resolution_index = (state.resolution_index - 1) % len(self._resolutions)
                state.status_message = ""
            elif self._contains(rects.get("resolution_next"), mouse_x, mouse_y):
                state.resolution_index = (state.resolution_index + 1) % len(self._resolutions)
                state.status_message = ""
            elif self._contains(rects.get("mode_prev"), mouse_x, mouse_y) or self._contains(
                rects.get("mode_next"), mouse_x, mouse_y
            ):
                state.fullscreen = not state.fullscreen
                state.status_message = ""
            elif self._contains(rects.get("set_controls"), mouse_x, mouse_y):
                return LocalMenuSelection(
                    "classic",
                    self._ai_player_count(state),
                    state.num_rounds,
                    players=self._player_configs(game, state),
                    launch_target="controllers",
                    persist_mode=False,
                )
            elif self._contains(rects.get("apply"), mouse_x, mouse_y):
                self._apply_options(game, state)
                state.status_message = "Graphics settings applied."
            elif self._contains(rects.get("back"), mouse_x, mouse_y):
                state.status_message = ""
                state.screen = "main"
            return None

        if state.screen == "select_players":
            for index in range(8):
                if not state.players[index].enabled and self._contains(rects.get(f"add_{index}"), mouse_x, mouse_y):
                    self._enable_player(state, index)
                    return None
                if state.players[index].enabled and self._contains(rects.get(f"remove_{index}"), mouse_x, mouse_y):
                    state.players[index].enabled = False
                    return None
                if self._contains(rects.get(f"mode_prev_{index}"), mouse_x, mouse_y) or self._contains(
                    rects.get(f"mode_next_{index}"), mouse_x, mouse_y
                ):
                    if state.players[index].enabled:
                        self._toggle_player_type(state, index)
                    return None
                if self._contains(rects.get(f"controller_prev_{index}"), mouse_x, mouse_y):
                    if state.players[index].enabled and state.players[index].is_human:
                        self._cycle_player_controller(state, index, -1)
                    return None
                if self._contains(rects.get(f"controller_next_{index}"), mouse_x, mouse_y):
                    if state.players[index].enabled and state.players[index].is_human:
                        self._cycle_player_controller(state, index, 1)
                    return None
            if self._contains(rects.get("rounds_prev"), mouse_x, mouse_y):
                state.num_rounds = self._cycle_rounds(state.num_rounds, -1)
            elif self._contains(rects.get("rounds_next"), mouse_x, mouse_y):
                state.num_rounds = self._cycle_rounds(state.num_rounds, 1)
            elif self._contains(rects.get("start"), mouse_x, mouse_y) and self._total_players(state) > 1:
                return self._build_selection(game, state)
            elif self._contains(rects.get("back"), mouse_x, mouse_y):
                state.screen = "main"
            return None

        if state.screen == "quit":
            if self._contains(rects.get("yes"), mouse_x, mouse_y):
                return LocalMenuSelection("quit", self._ai_player_count(state), state.num_rounds)
            if self._contains(rects.get("no"), mouse_x, mouse_y):
                state.screen = "main"
        return None

    def _handle_server_browser_click(
        self,
        state: _LocalMenuState,
        rects: dict[str, tuple[float, float, float, float]],
        mouse_x: float,
        mouse_y: float,
        *,
        server_scanner: GroundfireServerScanner | None = None,
    ) -> LocalMenuSelection | None:
        if self._contains(rects.get("close_servers"), mouse_x, mouse_y):
            state.screen = "main"
            return None

        for tab, _label in self._browser_tabs:
            if self._contains(rects.get(f"tab_{tab}"), mouse_x, mouse_y):
                state.browser_tab = tab
                state.selected_server_index = 0
                state.browser_scroll_index = 0
                state.browser_show_all = False
                state.browser_status = ""
                self._refresh_browser_from_scanner(state, server_scanner)
                return None

        for column_key in ("name", "description", "game", "players", "map", "latency", "last_played"):
            if self._contains(rects.get(f"sort_{column_key}"), mouse_x, mouse_y):
                self._set_browser_sort(state, column_key)
                self._clamp_browser_selection(state)
                return None

        if self._contains(rects.get("scroll_up"), mouse_x, mouse_y):
            self._scroll_browser(state, -1)
            return None
        if self._contains(rects.get("scroll_down"), mouse_x, mouse_y):
            self._scroll_browser(state, 1)
            return None
        if self._contains((9.55, 4.35, 9.75, -5.35), mouse_x, mouse_y):
            thumb = rects.get("scroll_thumb")
            if thumb is not None and self._contains(thumb, mouse_x, mouse_y):
                state.browser_scroll_dragging = True
                state.browser_scroll_drag_offset = thumb[1] - mouse_y
                return None
            if thumb is None or not self._contains(thumb, mouse_x, mouse_y):
                direction = (
                    -self._browser_max_rows
                    if thumb is not None and mouse_y > thumb[1]
                    else self._browser_max_rows
                )
                self._scroll_browser(state, direction)
                return None

        for index in range(state.browser_scroll_index, len(state.browser_entries)):
            if self._contains(rects.get(f"server_row_{index}"), mouse_x, mouse_y):
                now = time.monotonic()
                was_double_click = (
                    state.last_clicked_server_index == index
                    and (now - state.last_clicked_server_time) <= 0.35
                )
                state.selected_server_index = index
                state.last_clicked_server_index = index
                state.last_clicked_server_time = now
                self._clamp_browser_selection(state)
                if was_double_click:
                    return self._connect_selected_server(state, server_scanner)
                return None

        if self._contains(rects.get("change_filters"), mouse_x, mouse_y):
            state.screen = "server_filters"
            return None

        if self._contains(rects.get("open_all"), mouse_x, mouse_y):
            state.browser_show_all = True
            state.browser_tab = "unique"
            state.selected_server_index = 0
            state.browser_scroll_index = 0
            self._refresh_browser_from_scanner(
                state,
                server_scanner,
                status="Showing the list of all servers (5300+).",
            )
            return None

        if self._contains(rects.get("add_server"), mouse_x, mouse_y):
            state.screen = "add_server"
            if not state.add_server_value:
                state.add_server_value = "127.0.0.1:27015"
            return None

        if self._contains(rects.get("refresh_all"), mouse_x, mouse_y) or self._contains(
            rects.get("refresh"),
            mouse_x,
            mouse_y,
        ):
            self._refresh_all_browser_entries(state, server_scanner)
            return None

        if self._contains(rects.get("quick_refresh"), mouse_x, mouse_y):
            self._quick_refresh_selected_server(state, server_scanner)
            return None

        selected = self._selected_server_entry(state)
        if selected is None:
            return None

        if self._contains(rects.get("add_favorite"), mouse_x, mouse_y):
            if server_scanner is not None:
                server_scanner.add_favorite(selected)
                self._refresh_browser_from_scanner(
                    state,
                    server_scanner,
                    status=f"Added {selected.endpoint} to Favorites.",
                )
            return None

        if self._contains(rects.get("connect"), mouse_x, mouse_y):
            return self._connect_selected_server(state, server_scanner)

        return None

    def _handle_filter_click(
        self,
        state: _LocalMenuState,
        rects: dict[str, tuple[float, float, float, float]],
        mouse_x: float,
        mouse_y: float,
        *,
        server_scanner: GroundfireServerScanner | None = None,
    ) -> LocalMenuSelection | None:
        if self._contains(rects.get("close_servers"), mouse_x, mouse_y):
            state.screen = "main"
            return None
        elif self._contains(rects.get("filter_full"), mouse_x, mouse_y):
            state.browser_filter_show_full = not state.browser_filter_show_full
        elif self._contains(rects.get("filter_empty"), mouse_x, mouse_y):
            state.browser_filter_show_empty = not state.browser_filter_show_empty
        elif self._contains(rects.get("filter_password"), mouse_x, mouse_y):
            state.browser_filter_show_passworded = not state.browser_filter_show_passworded
        elif self._contains(rects.get("filter_secure"), mouse_x, mouse_y):
            state.browser_filter_secure_only = not state.browser_filter_secure_only
        elif self._contains(rects.get("filter_region"), mouse_x, mouse_y):
            state.browser_filter_region = self._next_region_filter(state.browser_filter_region)
        elif self._contains(rects.get("filter_latency"), mouse_x, mouse_y):
            state.browser_filter_max_latency = self._next_latency_filter(state.browser_filter_max_latency)
        elif self._contains(rects.get("filter_clear"), mouse_x, mouse_y):
            state.browser_filter_text = ""
            state.browser_filter_show_full = True
            state.browser_filter_show_empty = True
            state.browser_filter_show_passworded = True
            state.browser_filter_secure_only = False
            state.browser_filter_region = ""
            state.browser_filter_max_latency = None
        elif self._contains(rects.get("filter_ok"), mouse_x, mouse_y):
            state.screen = "servers"
            state.selected_server_index = 0
            state.browser_scroll_index = 0
        elif self._contains(rects.get("filter_cancel"), mouse_x, mouse_y):
            state.screen = "servers"
        else:
            return None
        self._refresh_browser_from_scanner(state, server_scanner)
        return None

    def _handle_add_server_click(
        self,
        state: _LocalMenuState,
        rects: dict[str, tuple[float, float, float, float]],
        mouse_x: float,
        mouse_y: float,
        *,
        server_scanner: GroundfireServerScanner | None = None,
    ) -> LocalMenuSelection | None:
        if self._contains(rects.get("close_servers"), mouse_x, mouse_y):
            state.screen = "main"
            return None
        if self._contains(rects.get("add_server_ok"), mouse_x, mouse_y):
            self._add_manual_server_from_state(state, server_scanner)
            return None
        if self._contains(rects.get("add_server_cancel"), mouse_x, mouse_y):
            state.screen = "servers"
            return None
        return None

    def _handle_password_click(
        self,
        state: _LocalMenuState,
        rects: dict[str, tuple[float, float, float, float]],
        mouse_x: float,
        mouse_y: float,
        *,
        server_scanner: GroundfireServerScanner | None = None,
    ) -> LocalMenuSelection | None:
        if self._contains(rects.get("close_servers"), mouse_x, mouse_y):
            state.screen = "main"
            return None
        if self._contains(rects.get("password_ok"), mouse_x, mouse_y):
            return self._connect_selected_server(state, server_scanner, allow_password_prompt=False)
        if self._contains(rects.get("password_cancel"), mouse_x, mouse_y):
            state.screen = "servers"
            state.connect_password_value = ""
            state.pending_connect_endpoint = ""
            return None
        return None

    def _handle_input_events(
        self,
        state: _LocalMenuState,
        events,
        key_names: dict[str, int],
        *,
        server_scanner: GroundfireServerScanner | None = None,
    ) -> LocalMenuSelection | None:
        for event in events:
            key = getattr(event, "key", None)
            wheel_y = getattr(event, "y", None)
            if key is None and wheel_y is not None and state.screen == "servers":
                self._scroll_browser(state, -int(wheel_y))
                continue
            if key is None:
                continue
            if state.screen == "servers":
                selection = self._handle_browser_key(state, key, key_names, server_scanner=server_scanner)
                if selection is not None:
                    return selection
            elif state.screen == "server_filters":
                self._handle_filter_key(state, event, key, key_names, server_scanner=server_scanner)
            elif state.screen == "add_server":
                self._handle_add_server_key(state, event, key, key_names, server_scanner=server_scanner)
            elif state.screen == "server_password":
                selection = self._handle_password_key(state, event, key, key_names, server_scanner=server_scanner)
                if selection is not None:
                    return selection
        return None

    def _handle_browser_key(
        self,
        state: _LocalMenuState,
        key: int,
        key_names: dict[str, int],
        *,
        server_scanner: GroundfireServerScanner | None,
    ) -> LocalMenuSelection | None:
        if self._is_key(key, key_names, "escape"):
            state.screen = "main"
        elif self._is_key(key, key_names, "up"):
            state.selected_server_index -= 1
            self._clamp_browser_selection(state)
        elif self._is_key(key, key_names, "down"):
            state.selected_server_index += 1
            self._clamp_browser_selection(state)
        elif self._is_key(key, key_names, "pageup"):
            state.selected_server_index -= self._browser_max_rows
            self._clamp_browser_selection(state)
        elif self._is_key(key, key_names, "pagedown"):
            state.selected_server_index += self._browser_max_rows
            self._clamp_browser_selection(state)
        elif self._is_key(key, key_names, "tab"):
            self._cycle_browser_tab(state, 1)
            self._refresh_browser_from_scanner(state, server_scanner)
        elif self._is_key(key, key_names, "enter"):
            return self._connect_selected_server(state, server_scanner)
        return None

    def _handle_filter_key(
        self,
        state: _LocalMenuState,
        event,
        key: int,
        key_names: dict[str, int],
        *,
        server_scanner: GroundfireServerScanner | None,
    ):
        if self._is_key(key, key_names, "escape"):
            state.screen = "servers"
        elif self._is_key(key, key_names, "enter"):
            state.screen = "servers"
            state.selected_server_index = 0
            state.browser_scroll_index = 0
        elif self._is_key(key, key_names, "backspace"):
            state.browser_filter_text = state.browser_filter_text[:-1]
        else:
            state.browser_filter_text = self._append_printable_text(state.browser_filter_text, event, max_length=48)
        self._refresh_browser_from_scanner(state, server_scanner)

    def _handle_add_server_key(
        self,
        state: _LocalMenuState,
        event,
        key: int,
        key_names: dict[str, int],
        *,
        server_scanner: GroundfireServerScanner | None,
    ):
        if self._is_key(key, key_names, "escape"):
            state.screen = "servers"
        elif self._is_key(key, key_names, "enter"):
            self._add_manual_server_from_state(state, server_scanner)
        elif self._is_key(key, key_names, "backspace"):
            state.add_server_value = state.add_server_value[:-1]
        else:
            state.add_server_value = self._append_printable_text(state.add_server_value, event, max_length=64)

    def _handle_password_key(
        self,
        state: _LocalMenuState,
        event,
        key: int,
        key_names: dict[str, int],
        *,
        server_scanner: GroundfireServerScanner | None,
    ) -> LocalMenuSelection | None:
        if self._is_key(key, key_names, "escape"):
            state.screen = "servers"
            state.connect_password_value = ""
            state.pending_connect_endpoint = ""
        elif self._is_key(key, key_names, "enter"):
            return self._connect_selected_server(state, server_scanner, allow_password_prompt=False)
        elif self._is_key(key, key_names, "backspace"):
            state.connect_password_value = state.connect_password_value[:-1]
        else:
            state.connect_password_value = self._append_printable_text(
                state.connect_password_value,
                event,
                max_length=64,
            )
        return None

    def _refresh_browser_from_scanner(
        self,
        state: _LocalMenuState,
        scanner: GroundfireServerScanner | None,
        *,
        status: str | None = None,
    ):
        if scanner is None:
            self._set_browser_entries(state, state.browser_entries, status=status)
            return
        self._refresh_server_entries(state, scanner, status=status)

    def _refresh_all_browser_entries(
        self,
        state: _LocalMenuState,
        scanner: GroundfireServerScanner | None,
    ):
        if scanner is None:
            state.browser_status = "Server scanner is not available."
            return
        if state.browser_show_all:
            base_entries = scanner.all_entries()
            entries = tuple(scanner.refresh_entry(entry, timeout=0.02) for entry in base_entries)
            for entry in entries:
                update_entry = getattr(scanner, "update_entry", None)
                if callable(update_entry):
                    update_entry(entry)
        else:
            entries = scanner.refresh_tab(state.browser_tab)
        self._set_browser_entries(state, entries, status=f"Refreshed {len(entries)} server(s).")

    def _quick_refresh_selected_server(
        self,
        state: _LocalMenuState,
        scanner: GroundfireServerScanner | None,
    ):
        selected = self._selected_server_entry(state)
        if selected is None:
            return
        if scanner is None:
            state.browser_status = "Server scanner is not available."
            return
        refreshed = scanner.refresh_entry(selected, timeout=0.05)
        update_entry = getattr(scanner, "update_entry", None)
        if callable(update_entry):
            update_entry(refreshed)
        entries = list(state.browser_entries)
        entries[state.selected_server_index] = refreshed
        self._set_browser_entries(state, tuple(entries), status=f"Refreshed {selected.endpoint}.")
        self._select_endpoint(state, refreshed.endpoint)

    def _add_manual_server_from_state(
        self,
        state: _LocalMenuState,
        scanner: GroundfireServerScanner | None,
    ):
        target = state.add_server_value.strip()
        if not target:
            state.browser_status = "Type a server address first."
            return
        if scanner is None:
            state.browser_status = "Server scanner is not available."
            state.screen = "servers"
            return
        try:
            entry = scanner.add_manual_server(target)
        except ValueError as exc:
            state.browser_status = str(exc)
            return
        state.browser_tab = "favorites"
        state.browser_show_all = False
        state.screen = "servers"
        self._refresh_browser_from_scanner(state, scanner, status=f"Added {entry.endpoint} to Favorites.")
        self._select_endpoint(state, entry.endpoint)

    def _connect_selected_server(
        self,
        state: _LocalMenuState,
        scanner: GroundfireServerScanner | None,
        *,
        allow_password_prompt: bool = True,
    ) -> LocalMenuSelection | None:
        selected = self._selected_server_entry(state)
        if selected is None:
            return None
        if selected.requires_password and allow_password_prompt:
            state.screen = "server_password"
            state.connect_password_value = ""
            state.pending_connect_endpoint = selected.endpoint
            return None
        return LocalMenuSelection(
            "connect",
            self._ai_player_count(state),
            state.num_rounds,
            connect_host=selected.host,
            connect_port=selected.port,
            connect_password=state.connect_password_value,
            connect_entry=selected,
            persist_mode=False,
        )

    def _selected_server_entry(self, state: _LocalMenuState) -> ServerListEntry | None:
        if not state.browser_entries:
            return None
        index = max(0, min(state.selected_server_index, len(state.browser_entries) - 1))
        return state.browser_entries[index]

    def _filtered_browser_entries(
        self,
        entries: tuple[ServerListEntry, ...],
        state: _LocalMenuState | None = None,
    ) -> tuple[ServerListEntry, ...]:
        if state is None:
            return tuple(
                sorted(entries, key=lambda entry: (entry.latency_ms is None, entry.latency_ms or 9999, entry.name))
            )

        filtered = tuple(entry for entry in entries if self._browser_entry_matches_filters(entry, state))
        return tuple(
            sorted(
                filtered,
                key=lambda entry: self._browser_sort_value(entry, state),
                reverse=state.browser_sort_desc,
            )
        )

    def _browser_entry_matches_filters(self, entry: ServerListEntry, state: _LocalMenuState) -> bool:
        needle = state.browser_filter_text.strip().lower()
        if needle:
            haystack = " ".join(
                (
                    entry.name,
                    entry.description,
                    entry.game,
                    entry.map_name,
                    entry.endpoint,
                )
            ).lower()
            if needle not in haystack:
                return False
        if not state.browser_filter_show_full and entry.player_count >= entry.max_players:
            return False
        if not state.browser_filter_show_empty and entry.player_count <= 0:
            return False
        if not state.browser_filter_show_passworded and entry.requires_password:
            return False
        if state.browser_filter_secure_only and not entry.secure:
            return False
        if state.browser_filter_region and entry.region.lower() != state.browser_filter_region.lower():
            return False
        if state.browser_filter_max_latency is not None:
            if entry.latency_ms is None or entry.latency_ms > state.browser_filter_max_latency:
                return False
        return True

    def _browser_sort_value(self, entry: ServerListEntry, state: _LocalMenuState):
        column = state.browser_sort_column
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

    def _empty_browser_message(self, state_or_tab) -> str:
        if not isinstance(state_or_tab, str):
            state = state_or_tab
            if not self._browser_filters_are_default(state):
                return "No servers match the current filters."
            if state.browser_show_all:
                return "No known native Groundfire servers are in the list."
            tab = state.browser_tab
        else:
            tab = state_or_tab
        if tab == "history":
            return "No servers have been played recently."
        if tab == "lan":
            return "No internet games responded to the query."
        if tab == "favorites":
            return "No favorite servers have been added."
        return "No internet games responded to the query."

    def _browser_filters_are_default(self, state: _LocalMenuState) -> bool:
        return (
            not state.browser_filter_text
            and state.browser_filter_show_full
            and state.browser_filter_show_empty
            and state.browser_filter_show_passworded
            and not state.browser_filter_secure_only
            and not state.browser_filter_region
            and state.browser_filter_max_latency is None
        )

    def _browser_status_is_placeholder(self, status: str) -> bool:
        return not status or status.startswith("No ") or status.startswith("Searching ")

    def _set_browser_sort(self, state: _LocalMenuState, column_key: str):
        if state.browser_sort_column == column_key:
            state.browser_sort_desc = not state.browser_sort_desc
        else:
            state.browser_sort_column = column_key
            state.browser_sort_desc = column_key in {"players", "last_played"}
        state.browser_entries = self._filtered_browser_entries(state.browser_entries, state)

    def _clamp_browser_selection(self, state: _LocalMenuState):
        if not state.browser_entries:
            state.selected_server_index = 0
            state.browser_scroll_index = 0
            return
        max_index = len(state.browser_entries) - 1
        state.selected_server_index = max(0, min(state.selected_server_index, max_index))
        max_scroll = max(0, len(state.browser_entries) - self._browser_max_rows)
        state.browser_scroll_index = max(0, min(state.browser_scroll_index, max_scroll))
        if state.selected_server_index < state.browser_scroll_index:
            state.browser_scroll_index = state.selected_server_index
        elif state.selected_server_index >= state.browser_scroll_index + self._browser_max_rows:
            state.browser_scroll_index = state.selected_server_index - self._browser_max_rows + 1

    def _scroll_browser(self, state: _LocalMenuState, rows: int):
        if not state.browser_entries:
            return
        max_scroll = max(0, len(state.browser_entries) - self._browser_max_rows)
        state.browser_scroll_index = max(0, min(max_scroll, state.browser_scroll_index + rows))
        if state.selected_server_index < state.browser_scroll_index:
            state.selected_server_index = state.browser_scroll_index
        elif state.selected_server_index >= state.browser_scroll_index + self._browser_max_rows:
            state.selected_server_index = min(
                len(state.browser_entries) - 1,
                state.browser_scroll_index + self._browser_max_rows - 1,
            )

    def _drag_browser_scrollbar(
        self,
        state: _LocalMenuState,
        rects: dict[str, tuple[float, float, float, float]],
        mouse_y: float,
    ):
        max_scroll = max(0, len(state.browser_entries) - self._browser_max_rows)
        thumb = rects.get("scroll_thumb")
        if max_scroll <= 0 or thumb is None:
            return
        track_top = 4.35
        track_bottom = -5.35
        thumb_height = thumb[1] - thumb[3]
        travel = max(0.0001, (track_top - track_bottom) - thumb_height)
        desired_top = mouse_y + state.browser_scroll_drag_offset
        desired_top = max(track_bottom + thumb_height, min(track_top, desired_top))
        ratio = (track_top - desired_top) / travel
        state.browser_scroll_index = max(0, min(max_scroll, int(round(ratio * max_scroll))))
        if state.selected_server_index < state.browser_scroll_index:
            state.selected_server_index = state.browser_scroll_index
        elif state.selected_server_index >= state.browser_scroll_index + self._browser_max_rows:
            state.selected_server_index = min(
                len(state.browser_entries) - 1,
                state.browser_scroll_index + self._browser_max_rows - 1,
            )

    def _select_endpoint(self, state: _LocalMenuState, endpoint: str):
        for index, entry in enumerate(state.browser_entries):
            if entry.endpoint == endpoint:
                state.selected_server_index = index
                self._clamp_browser_selection(state)
                return

    def _cycle_browser_tab(self, state: _LocalMenuState, direction: int):
        tabs = tuple(tab for tab, _label in self._browser_tabs)
        try:
            current = tabs.index(state.browser_tab)
        except ValueError:
            current = 0
        state.browser_tab = tabs[(current + direction) % len(tabs)]
        state.browser_show_all = False
        state.selected_server_index = 0
        state.browser_scroll_index = 0

    def _next_latency_filter(self, value: int | None) -> int | None:
        try:
            index = self._browser_max_latency_options.index(value)
        except ValueError:
            index = 0
        return self._browser_max_latency_options[(index + 1) % len(self._browser_max_latency_options)]

    def _latency_filter_label(self, value: int | None) -> str:
        return "Any" if value is None else f"{value} ms"

    def _next_region_filter(self, value: str) -> str:
        try:
            index = self._browser_region_options.index(value)
        except ValueError:
            index = 0
        return self._browser_region_options[(index + 1) % len(self._browser_region_options)]

    def _region_filter_label(self, value: str) -> str:
        return "All regions" if not value else value.upper()

    def _append_printable_text(self, text: str, event, *, max_length: int) -> str:
        if len(text) >= max_length:
            return text
        character = getattr(event, "unicode", "")
        if not isinstance(character, str) or len(character) != 1:
            return text
        if 32 <= ord(character) <= 126:
            return text + character
        return text

    def _is_key(self, key: int, key_names: dict[str, int], name: str) -> bool:
        return key_names.get(name) == key

    def _apply_options(self, game, state: _LocalMenuState):
        width, height = self._resolutions[state.resolution_index]
        game.get_interface().change_window(width, height, state.fullscreen)
        settings_path_getter = getattr(game, "get_settings_path", None)
        if not callable(settings_path_getter):
            return
        settings_path = settings_path_getter()
        from ..core.settings import set_ini_value

        set_ini_value(settings_path, "Graphics", "ScreenWidth", str(width))
        set_ini_value(settings_path, "Graphics", "ScreenHeight", str(height))
        set_ini_value(settings_path, "Graphics", "Fullscreen", "1" if state.fullscreen else "0")

    def _find_resolution_index(self, width: int, height: int) -> int:
        for index, (candidate_width, candidate_height) in enumerate(self._resolutions):
            if candidate_width == width and candidate_height == height:
                return index
        return 0

    def _resolution_label(self, resolution_index: int) -> str:
        width, height = self._resolutions[resolution_index]
        return f"{width} x {height}"

    def _cycle_rounds(self, current_rounds: int, direction: int) -> int:
        try:
            index = self._round_options.index(current_rounds)
        except ValueError:
            index = 1
        index = (index + direction) % len(self._round_options)
        return self._round_options[index]

    def _player_colour(self, game, player_index: int) -> tuple[int, int, int]:
        settings = getattr(game, "get_settings", lambda: None)()
        if settings is not None and hasattr(settings, "get_float"):
            red = settings.get_float("Colours", f"Tank{player_index + 1}red", PLAYER_COLOURS[player_index][0] / 255.0)
            green = settings.get_float(
                "Colours",
                f"Tank{player_index + 1}green",
                PLAYER_COLOURS[player_index][1] / 255.0,
            )
            blue = settings.get_float(
                "Colours",
                f"Tank{player_index + 1}blue",
                PLAYER_COLOURS[player_index][2] / 255.0,
            )
            return (int(red * 255), int(green * 255), int(blue * 255))
        return PLAYER_COLOURS[player_index % len(PLAYER_COLOURS)]

    def _ai_player_count(self, state: _LocalMenuState) -> int:
        return sum(1 for player in state.players if player.enabled and not player.is_human)

    def _total_players(self, state: _LocalMenuState) -> int:
        return sum(1 for player in state.players if player.enabled)

    def _icon_rect(self, center_x: float, center_y: float, *, size: float) -> tuple[float, float, float, float]:
        half = size / 2.0
        return (center_x - half, center_y + half, center_x + half, center_y - half)

    def _contains(self, rect: tuple[float, float, float, float] | None, x: float, y: float) -> bool:
        if rect is None:
            return False
        left, top, right, bottom = rect
        return left <= x <= right and bottom <= y <= top

    def _selector_arrow_rects(
        self,
        center_x: float,
        center_y: float,
        *,
        width: float,
        size: float,
    ) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
        half_width = width / 2.0
        half_size = size / 2.0
        arrow_width = min(0.55, width / 3.0)
        left_rect = (center_x - half_width, center_y + half_size, center_x - half_width + arrow_width, center_y - half_size)
        right_rect = (center_x + half_width - arrow_width, center_y + half_size, center_x + half_width, center_y - half_size)
        return left_rect, right_rect

    def _draw_selector(
        self,
        game,
        *,
        value: str,
        center_x: float,
        center_y: float,
        size: float,
        left_rect,
        right_rect,
        enabled: bool,
    ):
        ui = game.get_ui()
        self._draw_icon_button(game, left_rect, texture_id=11, fallback="<", enabled=enabled)
        self._draw_icon_button(game, right_rect, texture_id=10, fallback=">", enabled=enabled)
        ui.draw_centered_text(
            center_x,
            center_y - (size / 2.0) + 0.02,
            value,
            style=ui.style(
                size,
                self._bright_text if enabled else self._muted_text,
                spacing=max(0.2, size - 0.15),
                shadow=enabled,
            ),
        )

    def _controller_label(self, controller: int) -> str:
        return self._controller_labels[controller % len(self._controller_labels)]

    def _enable_player(self, state: _LocalMenuState, player_index: int, *, controller: int | None = None):
        player = state.players[player_index]
        player.enabled = True
        player.is_human = True
        if controller is None:
            controller = self._next_available_controller(state, player_index, direction=1)
        player.controller = controller

    def _apply_fire_auto_join(self, game, state: _LocalMenuState, last_fire_pressed: list[bool]):
        if state.screen != "select_players" or not hasattr(game, "get_controls"):
            return

        interface = game.get_interface()
        if not hasattr(interface, "num_of_controllers"):
            return

        controller_count = min(len(self._controller_labels), max(0, int(interface.num_of_controllers())))
        controls = game.get_controls()
        for controller in range(controller_count):
            pressed = bool(controls.get_command(controller, int(PlayerCommand.FIRE)))
            if pressed and not last_fire_pressed[controller] and not self._controller_in_use(state, controller):
                self._join_controller(state, controller)
            last_fire_pressed[controller] = pressed

        for controller in range(controller_count, len(last_fire_pressed)):
            last_fire_pressed[controller] = False

    def _join_controller(self, state: _LocalMenuState, controller: int):
        for player_index, player in enumerate(state.players):
            if player.enabled:
                continue
            self._enable_player(state, player_index, controller=controller)
            return

    def _controller_in_use(self, state: _LocalMenuState, controller: int, *, exclude_index: int | None = None) -> bool:
        for index, player in enumerate(state.players):
            if exclude_index is not None and index == exclude_index:
                continue
            if player.enabled and player.is_human and player.controller == controller:
                return True
        return False

    def _next_available_controller(self, state: _LocalMenuState, player_index: int, *, direction: int) -> int:
        current_controller = state.players[player_index].controller % len(self._controller_labels)
        candidate = current_controller
        for _ in range(len(self._controller_labels)):
            if not self._controller_in_use(state, candidate, exclude_index=player_index):
                return candidate
            candidate = (candidate + direction) % len(self._controller_labels)
        return current_controller

    def _cycle_player_controller(self, state: _LocalMenuState, player_index: int, direction: int):
        player = state.players[player_index]
        candidate = (player.controller + direction) % len(self._controller_labels)
        for _ in range(len(self._controller_labels)):
            if not self._controller_in_use(state, candidate, exclude_index=player_index):
                player.controller = candidate
                return
            candidate = (candidate + direction) % len(self._controller_labels)

    def _toggle_player_type(self, state: _LocalMenuState, player_index: int):
        player = state.players[player_index]
        player.is_human = not player.is_human
        if player.is_human:
            player.controller = self._next_available_controller(state, player_index, direction=1)

    def _player_configs(self, game, state: _LocalMenuState) -> tuple[LocalPlayerConfig, ...]:
        configs = []
        for index, player in enumerate(state.players):
            if not player.enabled:
                continue
            configs.append(
                LocalPlayerConfig(
                    slot=index,
                    name=player.name,
                    is_human=player.is_human,
                    controller=player.controller,
                    colour=self._player_colour(game, index),
                )
            )
        return tuple(configs)

    def _build_selection(self, game, state: _LocalMenuState) -> LocalMenuSelection:
        players = self._player_configs(game, state)
        ai_players = sum(1 for player in players if not player.is_human)
        human_players = tuple(player for player in players if player.is_human)
        if len(human_players) == 1:
            human_player = human_players[0]
            return LocalMenuSelection(
                "start",
                ai_players,
                state.num_rounds,
                players=players,
                local_controller=human_player.controller,
                requested_slot=human_player.slot,
                persist_mode=False,
            )

        return LocalMenuSelection(
            "classic",
            ai_players,
            state.num_rounds,
            players=players,
            local_controller=human_players[0].controller if human_players else 0,
            requested_slot=human_players[0].slot if human_players else None,
            launch_target="configured_start",
            persist_mode=False,
        )
