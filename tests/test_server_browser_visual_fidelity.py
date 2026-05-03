import json
import importlib
import os
import struct
import sys
import unittest
from pathlib import Path

from groundfire_net.browser import ServerListEntry
from src.groundfire.ui.font import Font
from src.groundfire.ui.graphics import GameGraphics
from src.groundfire.ui.menus import CanonicalLocalMenu
from src.groundfire.ui.text import GameUI

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame  # noqa: E402


def _ensure_real_pygame():
    global pygame
    display = getattr(pygame, "display", None)
    if hasattr(display, "init") and hasattr(pygame, "image"):
        return pygame
    sys.modules.pop("pygame", None)
    pygame = importlib.import_module("pygame")
    return pygame


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = PROJECT_ROOT / "docs" / "references" / "server_browser"
MEASUREMENTS_PATH = REFERENCE_DIR / "measurements.json"
FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "server_browser_reference_data.json"


class ServerBrowserVisualFidelityTests(unittest.TestCase):
    def test_reference_images_exist_with_expected_png_dimensions(self):
        measurements = self._load_json(MEASUREMENTS_PATH)

        for reference in measurements["references"].values():
            path = REFERENCE_DIR / reference["file"]
            self.assertTrue(path.exists(), path)
            self.assertEqual(self._png_size(path), tuple(reference["size"]))

    def test_measurements_cover_every_attached_state(self):
        measurements = self._load_json(MEASUREMENTS_PATH)
        expected_states = {
            "find_servers_button",
            "internet_populated",
            "favorites_populated",
            "unique_populated",
            "history_empty",
            "lan_empty",
        }

        self.assertEqual(set(measurements["references"]), expected_states)
        for key, reference in measurements["references"].items():
            self.assertIn("size", reference, key)
            if key == "find_servers_button":
                self.assertIn("button_rect", reference)
                continue
            self.assertIn("window_rect", reference, key)
            self.assertIn("table_header_rect", reference, key)
            self.assertIn("scrollbar_rect", reference, key)
            self.assertIn("footer_rect", reference, key)
            self.assertIn("buttons", reference, key)
            self.assertIn("columns", reference, key)

    def test_reference_fixture_matches_expected_tab_counts(self):
        data = self._load_json(FIXTURE_PATH)

        internet_count = len(data["internet"]["seed_entries"]) + data["internet"]["generated_entries"]["count"]
        self.assertEqual(internet_count, data["internet"]["expected_count"])
        self.assertEqual(internet_count, 124)
        self.assertEqual(len(data["favorites"]), 5)
        self.assertEqual(len(data["unique"]), 4)
        self.assertEqual(data["history"], [])
        self.assertEqual(data["lan"], [])

    def test_measurement_rectangles_are_inside_their_reference_images(self):
        measurements = self._load_json(MEASUREMENTS_PATH)

        for key, reference in measurements["references"].items():
            width, height = reference["size"]
            for rect_key, rect in self._iter_rectangles(reference):
                with self.subTest(reference=key, rect=rect_key):
                    left, top, right, bottom = rect
                    self.assertGreaterEqual(left, 0)
                    self.assertGreaterEqual(top, 0)
                    self.assertLessEqual(right, width)
                    self.assertLessEqual(bottom, height)
                    self.assertLess(left, right)
                    self.assertLess(top, bottom)

    def test_rendered_browser_screenshots_keep_reference_layout_with_groundfire_theme(self):
        measurements = self._load_json(MEASUREMENTS_PATH)
        fixture = self._load_json(FIXTURE_PATH)
        comparison = measurements["visual_comparison"]
        self.assertEqual(comparison["titlebar_strategy"], "crop_window_rect")
        output_dir = PROJECT_ROOT / comparison["actual_output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)

        for state_key in comparison["states"]:
            with self.subTest(state=state_key):
                reference = measurements["references"][state_key]
                actual = self._render_browser_state(reference, state_key, fixture)
                actual_path = output_dir / f"{state_key}.png"
                pygame.image.save(actual, str(actual_path))

                expected = self._reference_crop(reference)
                self.assertEqual(actual.get_size(), expected.get_size(), actual_path)

                if state_key == "find_servers_button":
                    self._assert_find_servers_button_uses_classic_menu_style(actual)
                    continue

                self._assert_groundfire_browser_theme(actual)

    def _iter_rectangles(self, reference):
        for key, value in reference.items():
            if key.endswith("_rect") and isinstance(value, list):
                yield key, value
        for group_key in ("buttons", "columns"):
            for key, value in reference.get(group_key, {}).items():
                yield f"{group_key}.{key}", value

    def _png_size(self, path: Path) -> tuple[int, int]:
        with path.open("rb") as handle:
            header = handle.read(24)
        self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
        return struct.unpack(">II", header[16:24])

    def _load_json(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def _render_browser_state(self, reference, state_key: str, fixture):
        if state_key == "find_servers_button":
            return self._render_find_servers_button(reference)

        left, top, right, bottom = reference["window_rect"]
        game = _OffscreenMenuGame(right - left, bottom - top)
        menu = CanonicalLocalMenu()
        state = menu._build_initial_state(game, ai_players=1)
        state.screen = "servers"

        if state_key == "internet_populated":
            state.browser_tab = "internet"
            state.browser_entries = self._internet_entries(fixture)
        elif state_key == "favorites_populated":
            state.browser_tab = "favorites"
            state.browser_entries = self._fixture_entries(fixture["favorites"], source="favorite")
        elif state_key == "unique_populated":
            state.browser_tab = "unique"
            state.browser_entries = self._fixture_entries(fixture["unique"], source="internet")
        elif state_key == "history_empty":
            state.browser_tab = "history"
            state.browser_status = menu._empty_browser_message("history")
        elif state_key == "lan_empty":
            state.browser_tab = "lan"
            state.browser_status = menu._empty_browser_message("lan")
        else:
            raise AssertionError(f"Unsupported visual state: {state_key}")

        game.get_graphics().clear((0, 0, 0))
        menu._draw_screen(game, state, player_name="Alice")
        return game.get_interface().get_draw_surface().convert()

    def _render_find_servers_button(self, reference):
        game = _OffscreenMenuGame(640, 480)
        menu = CanonicalLocalMenu()
        state = menu._build_initial_state(game, ai_players=1)
        game.get_graphics().clear((0, 0, 0))
        rects = menu._draw_screen(game, state, player_name="Alice")
        rect = rects["find_servers"]
        point_a = game.get_interface().game_to_screen(rect[0], rect[1])
        point_b = game.get_interface().game_to_screen(rect[2], rect[3])
        left, top = min(point_a[0], point_b[0]), min(point_a[1], point_b[1])
        width, height = abs(point_b[0] - point_a[0]), abs(point_b[1] - point_a[1])
        crop = pygame.Surface((width, height)).convert()
        crop.blit(game.get_interface().get_draw_surface(), (0, 0), (left, top, width, height))
        return pygame.transform.smoothscale(crop, tuple(reference["size"])).convert()

    def _assert_find_servers_button_uses_classic_menu_style(self, surface):
        width, height = surface.get_size()
        total_pixels = width * height
        red_total = 0
        green_total = 0
        blue_total = 0
        for y in range(height):
            for x in range(width):
                pixel = surface.get_at((x, y))
                red_total += pixel.r
                green_total += pixel.g
                blue_total += pixel.b

        average_red = red_total / total_pixels
        average_green = green_total / total_pixels
        average_blue = blue_total / total_pixels
        self.assertGreater(average_red, 95.0)
        self.assertGreater(average_green, 45.0)
        self.assertLess(average_blue, 80.0)
        self.assertGreater(average_red, average_green)
        self.assertGreater(average_green, average_blue)

        for sample in ((8, height // 2), (width - 8, height // 2), (width // 2, 4)):
            pixel = surface.get_at(sample)
            self.assertGreater(pixel.r, pixel.g, sample)
            self.assertGreater(pixel.g, pixel.b, sample)
            self.assertLess(pixel.b, 70, sample)

        text_pixel = surface.get_at((width // 2, height // 2))
        self.assertGreater(text_pixel.r, 200)
        self.assertGreater(text_pixel.g, 200)
        self.assertGreater(text_pixel.b, 200)

    def _assert_groundfire_browser_theme(self, surface):
        width, height = surface.get_size()
        header_colour = self._average_region(surface, 0, int(height * 0.15), width, int(height * 0.19))
        body_colour = self._average_region(surface, 0, int(height * 0.38), width, int(height * 0.75))

        self.assertGreater(header_colour[0], header_colour[1])
        self.assertGreater(header_colour[1], header_colour[2])
        self.assertGreater(header_colour[0], 45.0)
        self.assertLess(header_colour[2], 70.0)

        self.assertLess(body_colour[0], 80.0)
        self.assertLessEqual(body_colour[1], body_colour[2] + 12.0)

    def _average_region(self, surface, left: int, top: int, right: int, bottom: int):
        red_total = 0
        green_total = 0
        blue_total = 0
        total_pixels = max(1, (right - left) * (bottom - top))
        for y in range(top, bottom):
            for x in range(left, right):
                pixel = surface.get_at((x, y))
                red_total += pixel.r
                green_total += pixel.g
                blue_total += pixel.b
        return (
            red_total / total_pixels,
            green_total / total_pixels,
            blue_total / total_pixels,
        )

    def _internet_entries(self, fixture):
        entries = list(self._fixture_entries(fixture["internet"]["seed_entries"], source="internet"))
        generated = fixture["internet"]["generated_entries"]
        games = generated["games"]
        maps = generated["maps"]
        for index in range(int(generated["count"])):
            entries.append(
                ServerListEntry(
                    name=f"{generated['name_prefix']} {index + 1:03d}",
                    host=f"10.0.{index // 255}.{index % 255}",
                    port=27015 + index,
                    game=games[index % len(games)],
                    map_name=maps[index % len(maps)],
                    player_count=index % 32,
                    max_players=32,
                    latency_ms=int(generated["latency_start"]) + index,
                    source="internet",
                )
            )
        return tuple(entries)

    def _fixture_entries(self, raw_entries, *, source: str):
        entries = []
        for index, raw in enumerate(raw_entries):
            players = raw.get("players", [0, 32])
            if players == "-":
                player_count, max_players = 0, 32
            else:
                player_count, max_players = int(players[0]), int(players[1])
            latency = raw.get("latency")
            entries.append(
                ServerListEntry(
                    name=str(raw["name"]),
                    host=f"127.0.{index // 255}.{index % 255}",
                    port=27015 + index,
                    game=str(raw.get("game", "Groundfire")),
                    map_name=str(raw.get("map", "-")),
                    player_count=player_count,
                    max_players=max_players,
                    latency_ms=None if latency == "-" else int(latency),
                    source=source,
                    description=str(raw.get("description", "")),
                )
            )
        return tuple(entries)

    def _reference_crop(self, reference):
        image = pygame.image.load(str(REFERENCE_DIR / reference["file"])).convert()
        rect = reference["window_rect"] if "window_rect" in reference else reference["button_rect"]
        left, top, right, bottom = rect
        crop = pygame.Surface((right - left, bottom - top)).convert()
        crop.blit(image, (0, 0), (left, top, right - left, bottom - top))
        return crop

    def _compare_surfaces(
        self,
        expected,
        actual,
        *,
        pixel_delta_threshold: int,
        major_pixel_delta_threshold: int,
    ):
        self.assertEqual(expected.get_size(), actual.get_size())
        width, height = expected.get_size()
        total_delta = 0
        over_threshold = 0
        over_major_threshold = 0
        total_pixels = width * height
        for y in range(height):
            for x in range(width):
                reference_pixel = expected.get_at((x, y))
                actual_pixel = actual.get_at((x, y))
                delta = (
                    abs(reference_pixel.r - actual_pixel.r)
                    + abs(reference_pixel.g - actual_pixel.g)
                    + abs(reference_pixel.b - actual_pixel.b)
                )
                total_delta += delta
                if delta > pixel_delta_threshold:
                    over_threshold += 1
                if delta > major_pixel_delta_threshold:
                    over_major_threshold += 1
        return {
            "average_delta": total_delta / total_pixels,
            "pixel_ratio_over_threshold": over_threshold / total_pixels,
            "pixel_ratio_over_major_threshold": over_major_threshold / total_pixels,
        }


class _OffscreenMenuInterface:
    def __init__(self, width: int, height: int):
        _ensure_real_pygame()
        pygame.init()
        pygame.display.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))
        self._width = width
        self._height = height
        self._fullscreen = False
        self._surface = pygame.Surface((width, height), pygame.SRCALPHA).convert()
        self._textures = {}
        self._mouse_x = 99.0
        self._mouse_y = 99.0
        for texture_id, relative_path in (
            (3, "data/fonts.png"),
            (6, "data/menuback.png"),
            (9, "data/logo.png"),
            (10, "data/addbutton.png"),
            (11, "data/removebutton.png"),
        ):
            path = PROJECT_ROOT / relative_path
            if path.exists():
                self._textures[texture_id] = pygame.image.load(str(path)).convert_alpha()

    def get_window_settings(self):
        return self._width, self._height, self._fullscreen

    def get_texture_surface(self, texture_id):
        return self._textures.get(texture_id)

    def get_mouse_pos(self):
        return self._mouse_x, self._mouse_y

    def get_mouse_button(self, _button):
        return False

    def game_to_screen(self, x, y):
        return (
            int((x + 10.0) / 20.0 * self._width),
            int((7.5 - y) / 15.0 * self._height),
        )

    def scale_len(self, length):
        return int(length * self._height / 15.0)

    def get_line_width(self):
        return 1

    def get_draw_surface(self):
        return self._surface

    def fill_surface(self, colour):
        self._surface.fill(colour)

    def blit_surface(self, surface, dest, *args, **kwargs):
        return self._surface.blit(surface, dest, *args, **kwargs)

    def draw_polygon(self, colour, points):
        pygame.draw.polygon(self._surface, colour, points)

    def draw_rect(self, colour, rect):
        pygame.draw.rect(self._surface, colour, rect)

    def draw_line(self, colour, start, end, width):
        pygame.draw.line(self._surface, colour, start, end, width)


class _OffscreenMenuGame:
    def __init__(self, width: int, height: int):
        self._interface = _OffscreenMenuInterface(width, height)
        self._graphics = GameGraphics(interface_provider=lambda: self._interface)
        self._font = Font(self._interface, 3)
        self._ui = GameUI(font_provider=lambda: self._font)

    def get_interface(self):
        return self._interface

    def get_graphics(self):
        return self._graphics

    def get_ui(self):
        return self._ui


if __name__ == "__main__":
    unittest.main()
