#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import random
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


def _capture_server_browser(path: Path, width: int, height: int) -> None:
    from groundfire_net.browser import ServerListEntry
    from src.common import GameState

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
        _save_surface(game, path)
    finally:
        _close_game(game)


def _capture_local_match(path: Path, width: int, height: int) -> None:
    from src.common import GameState

    random.seed(1401)
    game = _new_game(width, height)
    try:
        game.add_player(0, "Player", (255, 0, 255))
        game.add_player(-1, "Enemy", (255, 128, 0))
        game.set_num_of_rounds(5)
        game._change_state(GameState.ROUND_STARTING)
        game.get_interface().enable_mouse(False)
        game._game_state = GameState.ROUND_IN_ACTION
        game._new_state = GameState.CURRENT_STATE
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture authoritative Pygame visual references for Godot fidelity work.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=768)
    args = parser.parse_args()

    capture_references(args.output_dir, args.width, args.height)
    print(f"Pygame references written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
