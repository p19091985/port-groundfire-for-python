import unittest
from unittest.mock import patch

from tests.support import install_fake_pygame

install_fake_pygame()

import pygame

from src.gamegraphics import GameGraphics


class WindowStub:
    def __init__(self):
        self.fill_calls = []
        self.blit_calls = []

    def fill(self, colour):
        self.fill_calls.append(colour)

    def blit(self, surface, dest, *args, **kwargs):
        self.blit_calls.append((surface, dest, args, kwargs))


class InterfaceStub:
    def __init__(self):
        self._window = WindowStub()
        self._textures = {
            1: pygame.Surface((16, 16)),
            7: pygame.Surface((32, 32)),
        }

    def game_to_screen(self, x, y):
        return (int(x * 10), int(y * 10))

    def scale_len(self, length):
        return int(length * 10)

    def get_texture_surface(self, texture_id):
        return self._textures.get(texture_id)

    def get_window_settings(self):
        return (640, 480, False)

    def get_line_width(self):
        return 3


class GameGraphicsTests(unittest.TestCase):
    def test_draw_world_polygon_projects_to_screen(self):
        interface = InterfaceStub()
        graphics = GameGraphics(interface_provider=lambda: interface)

        with patch.object(pygame.draw, "polygon") as polygon:
            graphics.draw_world_polygon([(1.0, 2.0), (3.0, 4.0), (5.0, 6.0)], (255, 255, 255))

        polygon.assert_called_once_with(interface._window, (255, 255, 255), [(10, 20), (30, 40), (50, 60)])

    def test_draw_world_polygon_with_alpha_blits_surface(self):
        interface = InterfaceStub()
        graphics = GameGraphics(interface_provider=lambda: interface)

        graphics.draw_world_polygon([(1.0, 2.0), (3.0, 2.0), (3.0, 4.0)], (255, 255, 255, 64))

        self.assertEqual(len(interface._window.blit_calls), 1)

    def test_draw_texture_world_rect_scales_and_blits(self):
        interface = InterfaceStub()
        graphics = GameGraphics(interface_provider=lambda: interface)

        with patch.object(pygame.transform, "scale", return_value=pygame.Surface((20, 20))) as scale:
            graphics.draw_texture_world_rect(1, 1.0, 4.0, 3.0, 2.0, alpha=128, tint=(255, 0, 0))

        scale.assert_called_once()
        self.assertEqual(len(interface._window.blit_calls), 1)
        blitted_surface = interface._window.blit_calls[0][0]
        self.assertEqual(getattr(blitted_surface, "_alpha", None), 128)

    def test_draw_fullscreen_overlay_blits_screen_sized_surface(self):
        interface = InterfaceStub()
        graphics = GameGraphics(interface_provider=lambda: interface)

        graphics.draw_fullscreen_overlay((255, 255, 255, 120))

        self.assertEqual(len(interface._window.blit_calls), 1)
        overlay, dest, _, _ = interface._window.blit_calls[0]
        self.assertEqual(overlay.get_size(), (640, 480))
        self.assertEqual(dest, (0, 0))

    def test_draw_world_line_uses_interface_line_width_by_default(self):
        interface = InterfaceStub()
        graphics = GameGraphics(interface_provider=lambda: interface)

        with patch.object(pygame.draw, "line") as line:
            graphics.draw_world_line((1.0, 2.0), (3.0, 4.0), (255, 255, 255))

        line.assert_called_once_with(interface._window, (255, 255, 255), (10, 20), (30, 40), 3)

    def test_clear_and_primitives_can_use_interface_backend_methods(self):
        class BackendInterface(InterfaceStub):
            def __init__(self):
                super().__init__()
                self.fill_calls = []
                self.polygon_calls = []

            def fill_surface(self, colour):
                self.fill_calls.append(colour)

            def draw_polygon(self, colour, points):
                self.polygon_calls.append((colour, points))

        interface = BackendInterface()
        graphics = GameGraphics(interface_provider=lambda: interface)

        graphics.clear((1, 2, 3))
        graphics.draw_screen_polygon([(1, 2), (3, 4), (5, 6)], (255, 255, 255))

        self.assertEqual(interface.fill_calls, [(1, 2, 3)])
        self.assertEqual(interface.polygon_calls, [((255, 255, 255), [(1, 2), (3, 4), (5, 6)])])


if __name__ == "__main__":
    unittest.main()
