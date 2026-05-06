from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from ..gameplay.constants import WEAPON_SPECS
from ..input.commands import PlayerCommand
from ..sim.match import MatchSnapshot, ReplicatedPlayerState


class _ClassicThemeMixin:
    _background_scroll = 0.0
    _background_scroll_speed = 0.0025
    _brown_fill = (153, 76, 0, 180)
    _panel_fill = (0, 0, 0, 128)
    _bright_text = (255, 255, 255)
    _cyan_text = (0, 255, 255)
    _gold_text = (255, 255, 0)
    _muted_text = (76, 76, 76)

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

    def _draw_player_menu_tank_icon(self, game, row_y: float, colour: tuple[int, int, int]):
        if not hasattr(game, "get_graphics"):
            return
        game.get_graphics().draw_world_polygon(
            (
                (-7.0, row_y + 0.2),
                (-6.6, row_y + 0.2),
                (-6.4, row_y - 0.2),
                (-7.2, row_y - 0.2),
            ),
            colour,
        )

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
        if snapshot.game_phase == "lobby":
            self._draw_lobby_overlay(game, snapshot)
            return

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

    def _draw_lobby_overlay(self, game, snapshot: MatchSnapshot):
        ui = game.get_ui()
        player_count = len(snapshot.players)
        count_label = f"{player_count} player{'s' if player_count != 1 else ''} connected"

        self._draw_panel(game, -7.2, 2.45, 7.2, -4.65, fill=(0, 0, 0, 150))
        self._draw_panel(game, -7.2, 2.45, 7.2, 1.55, fill=(30, 10, 52, 210))
        self._draw_panel(game, -7.2, 1.6, 7.2, 1.42, fill=(153, 76, 0, 210))
        ui.draw_centered_text(
            0.0,
            1.83,
            "Waiting for Server",
            style=ui.style(0.58, self._bright_text, spacing=0.46, shadow=True),
        )

        self._draw_panel(game, -2.7, 1.03, 2.7, 0.25, fill=(0, 70, 78, 190))
        ui.draw_centered_text(
            0.0,
            0.52,
            count_label,
            style=ui.style(0.36, self._cyan_text, spacing=0.26, shadow=True),
        )
        ui.draw_centered_text(
            0.0,
            -0.1,
            "The host will start the match",
            style=ui.style(0.28, (210, 230, 245), spacing=0.2, shadow=True),
        )

        ui.draw_centered_text(
            0.0,
            -0.62,
            "Online Lobby",
            style=ui.style(0.28, self._gold_text, spacing=0.22, shadow=True),
        )
        self._draw_lobby_player_cards(game, snapshot.players)

    def _draw_lobby_player_cards(self, game, players: tuple[ReplicatedPlayerState, ...]):
        if not players:
            self._draw_panel(game, -3.6, -1.2, 3.6, -2.05, fill=(0, 0, 0, 105))
            game.get_ui().draw_centered_text(
                0.0,
                -1.6,
                "No players connected yet",
                style=game.get_ui().style(0.26, (210, 230, 245), spacing=0.2, shadow=True),
            )
            return

        for index, player in enumerate(players[:8]):
            column = index % 2
            row = index // 2
            left = -6.25 if column == 0 else 0.35
            right = -0.35 if column == 0 else 6.25
            top = -0.95 - (row * 0.9)
            self._draw_lobby_player_card(game, player, left, top, right, top - 0.68)

        overflow_count = len(players) - 8
        if overflow_count > 0:
            game.get_ui().draw_centered_text(
                0.0,
                -4.25,
                f"+{overflow_count} more waiting",
                style=game.get_ui().style(0.24, self._cyan_text, spacing=0.18, shadow=True),
            )

    def _draw_lobby_player_card(
        self,
        game,
        player: ReplicatedPlayerState,
        left: float,
        top: float,
        right: float,
        bottom: float,
    ):
        ui = game.get_ui()
        graphics = game.get_graphics()
        fill = (0, 0, 0, 118) if player.connected else (20, 20, 20, 92)
        status = "AI" if player.is_computer else "Human"
        status_colour = self._gold_text if player.is_computer else self._cyan_text
        if not player.connected:
            status = "Offline"
            status_colour = (170, 170, 170)

        self._draw_panel(game, left, top, right, bottom, fill=fill)
        graphics.draw_world_rect(left, top, left + 0.12, bottom, player.colour + (220,))
        self._draw_tank_icon(game, left + 0.52, bottom + 0.22, player.colour, size=0.18)
        ui.printf(
            left + 0.9,
            top - 0.25,
            "%s",
            player.name,
            style=ui.style(0.22, self._bright_text, spacing=0.16, shadow=True),
        )
        ui.printf(
            left + 0.9,
            bottom + 0.13,
            "%d pts  $%d",
            player.score,
            player.money,
            style=ui.style(0.17, (200, 215, 230), spacing=0.12, shadow=True),
        )
        ui.draw_centered_text(
            right - 0.72,
            top - 0.41,
            status,
            style=ui.style(0.18, status_colour, spacing=0.12, shadow=True),
        )

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
    requested_slot: int | None = None
    launch_target: str | None = None
    persist_mode: bool = True
