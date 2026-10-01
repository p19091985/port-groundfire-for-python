#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "references" / "pygame_visual"


def _prepare_sdl() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def _new_game(width: int, height: int):
    from src.game import Game

    game = Game()
    game.get_interface().change_window(width, height, False)
    game.get_interface().enable_mouse(False)
    game._show_fps = False
    return game


def _save_surface(game, path: Path) -> None:
    import pygame

    game.get_renderer().render_frame(game, fps=60.0)
    pygame.image.save(game.get_interface().get_draw_surface(), str(path))


def _close_game(game) -> None:
    menu = game.get_current_menu()
    if menu is not None and hasattr(menu, "close"):
        menu.close()
    game.get_interface().close()


def _capture_main_menu(path: Path, width: int, height: int) -> None:
    game = _new_game(width, height)
    try:
        _save_surface(game, path)
    finally:
        _close_game(game)


def _capture_options(path: Path, width: int, height: int) -> None:
    from src.common import GameState

    game = _new_game(width, height)
    try:
        game._change_state(GameState.OPTION_MENU)
        game.get_interface().enable_mouse(False)
        _save_surface(game, path)
    finally:
        _close_game(game)


def _capture_menu_state(path: Path, width: int, height: int, state_name: str) -> None:
    from src.common import GameState

    game = _new_game(width, height)
    try:
        game._change_state(getattr(GameState, state_name))
        game.get_interface().enable_mouse(False)
        _save_surface(game, path)
    finally:
        _close_game(game)


def _capture_server_browser(path: Path, width: int, height: int, dialog: str = "") -> None:
    from src.common import GameState

    from groundfire_net.browser import ServerListEntry

    game = _new_game(width, height)
    try:
        game._change_state(GameState.SERVER_BROWSER_MENU)
        game.get_interface().enable_mouse(False)
        menu = game.get_current_menu()
        menu._state.entries = (
            ServerListEntry(
                name="Groundfire Online Test",
                host="127.0.0.1",
                port=8765,
                map_name="classic",
                player_count=2,
                max_players=8,
                latency_ms=42,
                source="internet",
                description="Browser-safe reference server",
            ),
            ServerListEntry(
                name="Groundfire SA Lobby",
                host="127.0.0.1",
                port=8766,
                map_name="mesa",
                player_count=0,
                max_players=12,
                latency_ms=88,
                source="internet",
                description="South America lobby",
            ),
        )
        menu._state.status = "2 server(s) listed for Internet."
        menu._state.selected_index = 0
        menu._state.scroll_index = 0
        menu._state.dialog = "join" if dialog == "password" else dialog
        if dialog in ("join", "password"):
            menu._state.pending_endpoint = "127.0.0.1:8765"
        if dialog == "password":
            from dataclasses import replace

            menu._state.entries = (replace(menu._state.entries[0], requires_password=True), *menu._state.entries[1:])
            menu._state.password_value = "secret"
        if dialog == "unavailable":
            from types import SimpleNamespace

            scanner = menu._scanner
            try:
                menu._scanner = SimpleNamespace(
                    refresh_entry=lambda entry, **kwargs: entry.with_updates(latency_ms=None)
                )
                menu._state.dialog = ""
                menu._connect_selected()
            finally:
                menu._scanner = scanner
        if dialog == "invalid_address":
            menu._state.dialog = "add"
            menu._state.add_server_value = "127.0.0.1:65536"
            menu._add_manual_server()
        _save_surface(game, path)
    finally:
        _close_game(game)


def _capture_local_match(path: Path, width: int, height: int, screen="local_match") -> None:
    from src.common import GameState

    game = _new_game(width, height)
    try:
        game.get_clock()._time_source = lambda: 1.401
        game.add_player(0, "Player", (255, 0, 255))
        game.add_player(1, "Enemy", (255, 128, 0))
        if screen == "winner_eight":
            for index in range(2, 8):
                game.add_player(-1, f"Player {index + 1}", (32 * index, 255 - 24 * index, 64 + 20 * index))
        game.set_num_of_rounds(5)
        game._change_state(GameState.ROUND_STARTING)
        game.get_interface().enable_mouse(False)
        game._game_state = GameState.ROUND_IN_ACTION
        game._new_state = GameState.CURRENT_STATE
        if screen == "shell_flight":
            from src.gamesimulation import GameSimulationController
            from src.shell import Shell

            tick = 0
            controls = game.get_controls()
            original_get_command = controls.get_command
            controls.get_command = lambda controller, command: controller == 0 and command == 0 and tick == 500
            try:
                simulation = GameSimulationController()
                for tick in range(1, 511):
                    game.set_time(tick / 60.0)
                    simulation.simulate_round_step(game, 1.0 / 60.0)
                if not any(isinstance(entity, Shell) for entity in game._entity_list):
                    raise RuntimeError("Shell flight capture did not launch a projectile")
            finally:
                controls.get_command = original_get_command
        if screen == "round_starting":
            game._game_state = GameState.ROUND_STARTING
        elif screen in ("score", "shop", "winner", "winner_eight", "shop_selected"):
            # Identical prepared presentation state, not a combat acceptance test.
            for index, player in enumerate(p for p in game.get_players() if p):
                player._score = 100 if index == 0 or screen == "winner_eight" else 0
                player.set_money(200)
            game._change_state(
                {
                    "score": GameState.ROUND_SCORE,
                    "shop": GameState.SHOP_MENU,
                    "winner": GameState.WINNER_MENU,
                    "winner_eight": GameState.WINNER_MENU,
                    "shop_selected": GameState.SHOP_MENU,
                }[screen]
            )
            if screen == "shop_selected":
                menu = game.get_current_menu()
                menu._player_select_pos[:2] = [0, 3]
                menu._line_lit[0] = menu._line_lit[3] = True
                game.get_players()[0].get_tank().get_weapon(1).add_amount(125)
                game.get_players()[1].get_tank().get_weapon(3).add_amount(5)
            game.get_interface().enable_mouse(False)
        _save_surface(game, path)
    finally:
        _close_game(game)


def capture_references(output_dir: Path, width: int, height: int) -> None:
    _prepare_sdl()
    output_dir.mkdir(parents=True, exist_ok=True)
    captures = {
        "main_menu.png": _capture_main_menu,
        "options.png": _capture_options,
        "server_browser.png": _capture_server_browser,
        "local_match.png": _capture_local_match,
    }
    for filename, capture in captures.items():
        capture(output_dir / filename, width, height)
    for dialog in ("filters", "add", "join", "password", "unavailable", "invalid_address"):
        _capture_server_browser(output_dir / f"server_{dialog}.png", width, height, dialog)
    for screen in ("round_starting", "score", "shop", "winner", "winner_eight", "shop_selected"):
        _capture_local_match(output_dir / f"{screen}.png", width, height, screen)
    for filename, state in {
        "quit.png": "QUIT_MENU",
        "local_match_setup.png": "SELECT_PLAYERS_MENU",
        "controllers.png": "CONTROLLERS_MENU",
        "keyboard_layout.png": "SET_CONTROLS_MENU",
    }.items():
        _capture_menu_state(output_dir / filename, width, height, state)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture authoritative Pygame visual references for Godot fidelity work."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--dynamic-only", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.dynamic_only:
        _prepare_sdl()
        args.output_dir.mkdir(parents=True, exist_ok=True)
        _capture_local_match(args.output_dir / "shell_flight.png", args.width, args.height, "shell_flight")
    else:
        capture_references(args.output_dir, args.width, args.height)
        # Pygame's renderer can fault natively after many Game instances on
        # Windows. Isolate the long running effect capture from menu captures.
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--dynamic-only", "--output-dir", str(args.output_dir),
             "--width", str(args.width), "--height", str(args.height)],
            check=True,
        )
    print(f"Pygame references written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
