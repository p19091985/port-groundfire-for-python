from __future__ import annotations

from pathlib import Path

from ..assets import find_spec_by_key, load_texture_specs, resolve_asset_path
from ..core.pygame import PygameBackend
from .graphics import get_interface_graphics
from .interface import Colour, Interface

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ASSET_MANIFEST_PATH = PROJECT_ROOT / "conf" / "assets.json"


class FontError(Exception):
    pass


class Font:
    def __init__(self, interface: Interface, tex_num: int, *, pygame_module=None):
        self._interface = interface
        self._tex_num = tex_num
        self._colour = Colour(1.0, 1.0, 1.0)
        self._backend = PygameBackend.create(pygame_module)
        self._pygame = self._backend.pygame

        if self._interface.get_texture_surface(tex_num) is None:
            font_spec = find_spec_by_key(load_texture_specs(ASSET_MANIFEST_PATH), "font_atlas")
            font_path = None if font_spec is None else resolve_asset_path(font_spec.candidates, root=PROJECT_ROOT)
            if font_path is None or not self._interface.load_texture(str(font_path), tex_num):
                raise FontError()

        self._shadow = False
        self._proportional = True
        self._orientation = 0.0
        self._x_size = 1.0
        self._y_size = 1.0
        self._x_spacing = 1.0
        self._widths = [
            9, 9, 14, 18, 18, 27, 24, 8, 11, 11, 15, 18, 9, 9, 9, 8,
            18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 9, 9, 18, 18, 18, 17,
            20, 21, 21, 21, 21, 20, 18, 22, 22, 11, 18, 22, 18, 25, 22, 22,
            20, 22, 21, 20, 20, 22, 21, 27, 21, 21, 20, 11, 8, 11, 18, 14,
            9, 18, 18, 18, 18, 18, 11, 18, 18, 9, 9, 18, 9, 27, 18, 18,
            18, 18, 14, 17, 13, 18, 17, 25, 18, 17, 15, 11, 8, 11, 18, 17,
            18, 10, 8, 18, 14, 27, 18, 18, 9, 27, 20, 9, 27, 10, 20, 10,
            10, 8, 8, 14, 14, 14, 14, 27, 9, 26, 17, 9, 27, 10, 15, 21,
        ]
        while len(self._widths) < 128:
            self._widths.append(18)

    def set_size(self, x_size, y_size, x_spacing):
        self._x_size = x_size
        self._y_size = y_size
        self._x_spacing = x_spacing

    def set_colour(self, r, g=None, b=None):
        if isinstance(r, (tuple, list)):
            self._colour = Colour(*r[:3])
        else:
            self._colour = Colour(r, g, b)

    def set_proportional(self, proportional):
        self._proportional = proportional

    def set_shadow(self, shadow):
        self._shadow = shadow

    def set_orientation(self, orientation):
        self._orientation = orientation

    def printf(self, x, y, fmt, *args):
        text = fmt % args if args else fmt
        if self._shadow:
            self._print_string(x - self._x_size / 8.0, y - self._y_size / 8.0, text, True)
        self._print_string(x, y, text, False)

    def print_at(self, x, y, fmt, *args):
        self.printf(x, y, fmt, *args)

    def print_centred_at(self, x_centre, y, fmt, *args):
        text = fmt % args if args else fmt
        x = x_centre - (self.find_string_length(text) / 2.0)
        if self._shadow:
            self._print_string(x - self._x_size / 8.0, y - self._y_size / 8.0, text, True)
        self._print_string(x, y, text, False)

    def find_string_length(self, string):
        if self._proportional:
            width = 0.0
            for char in string:
                idx = ord(char) - 32
                width += self._widths[idx] if 0 <= idx < len(self._widths) else 18
            return (width / 24.0) * self._x_spacing
        return (len(string) - 1) * self._x_spacing + self._x_size

    def _print_string(self, x, y, string, shadow):
        tex_surface = self._interface.get_texture_surface(self._tex_num)
        if not tex_surface:
            return

        tex_w, tex_h = tex_surface.get_size()
        cell_w = tex_w / 16
        cell_h = tex_h / 16
        current_x = x
        text_color = (0, 0, 0, 100) if shadow else self._colour.to_tuple()
        scale_image = self._backend.get_scale_image()

        for char in string:
            ascii_val = ord(char)
            if ascii_val < 32:
                continue
            col = ascii_val % 16
            row = (ascii_val - 32) // 16
            src_y = row * cell_h
            if self._proportional:
                src_y += tex_h / 2
            rect = self._pygame.Rect(col * cell_w, src_y, cell_w, cell_h)
            try:
                char_surf = tex_surface.subsurface(rect).copy()
            except ValueError:
                continue

            if not shadow and text_color != (255, 255, 255):
                colour_surf = self._pygame.Surface(char_surf.get_size(), self._pygame.SRCALPHA)
                colour_surf.fill((*text_color[:3], 255))
                char_surf.blit(colour_surf, (0, 0), special_flags=self._pygame.BLEND_RGBA_MULT)
            elif shadow:
                colour_surf = self._pygame.Surface(char_surf.get_size(), self._pygame.SRCALPHA)
                colour_surf.fill((0, 0, 0, 100))
                char_surf.blit(colour_surf, (0, 0), special_flags=self._pygame.BLEND_RGBA_MULT)

            if self._orientation != 0.0:
                char_surf = self._pygame.transform.rotate(char_surf, self._orientation)

            w_px = self._interface.scale_len(self._x_size)
            h_px = self._interface.scale_len(self._y_size)
            if self._proportional:
                w_px = int(w_px * 0.8)

            char_surf = scale_image(char_surf, (int(w_px), int(h_px)))
            screen_x, screen_y = self._interface.game_to_screen(current_x, y)
            dest_y = screen_y - char_surf.get_height()
            get_interface_graphics(self._interface).blit_surface(char_surf, (screen_x, dest_y))

            if self._proportional:
                current_x += (self._widths[ascii_val - 32] / 24.0) * self._x_spacing
            else:
                current_x += self._x_spacing
