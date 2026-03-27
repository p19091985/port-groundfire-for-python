from __future__ import annotations

from typing import Dict, Tuple

import pygame


Rect = Tuple[int, int, int, int]

GROUND_SKY_TOP = (65, 118, 178)
GROUND_SKY_BOTTOM = (102, 179, 230)
GROUND_STREAK = (224, 199, 68)
GROUND_STREAK_DARK = (153, 76, 0)
GROUND_DIAGONAL = (56, 97, 143)
GROUND_PANEL = (133, 82, 28)
GROUND_PANEL_ALT = (112, 67, 20)
GROUND_PANEL_LIGHT = (214, 166, 104)
GROUND_PANEL_DARK = (66, 34, 10)
GROUND_TEXT = (247, 238, 223)
GROUND_TEXT_DIM = (224, 208, 186)
GROUND_ACCENT = (255, 209, 112)
GROUND_DISABLED = (168, 146, 122)


def pygame_const(name: str, fallback: int) -> int:
    value = getattr(pygame, name, fallback)
    if value == 0:
        return fallback
    return value


class _FallbackFont:
    def __init__(self, size: int):
        self._size = max(8, int(size))

    def render(self, text: str, _antialias: bool, _colour):
        width = max(1, int(len(text) * self._size * 0.52))
        return pygame.Surface((width, self._size + 4), pygame.SRCALPHA)


def rect(x: int, y: int, w: int, h: int) -> Rect:
    return (int(x), int(y), max(1, int(w)), max(1, int(h)))


def point_in_rect(point, target: Rect) -> bool:
    px, py = point
    x, y, w, h = target
    return x <= px < x + w and y <= py < y + h


def draw_bevel_rect(surface, target: Rect, fill, light, dark, outline=None) -> None:
    x, y, w, h = target
    pygame.draw.rect(surface, fill, target)
    pygame.draw.line(surface, light, (x, y), (x + w - 1, y))
    pygame.draw.line(surface, light, (x, y), (x, y + h - 1))
    pygame.draw.line(surface, dark, (x, y + h - 1), (x + w - 1, y + h - 1))
    pygame.draw.line(surface, dark, (x + w - 1, y), (x + w - 1, y + h - 1))
    if outline is not None:
        pygame.draw.rect(surface, outline, target, 1)


def draw_text(surface, font_cache: Dict[Tuple[int, bool], object], text: str, target: Rect, size: int, colour, align: str = "left", bold: bool = False) -> None:
    text_surface = render_text(font_cache, text, size, colour, bold)
    text_width, text_height = text_surface.get_size()
    x, y, w, h = target

    if align == "center":
        draw_x = x + (w - text_width) // 2
        draw_y = y + (h - text_height) // 2
    elif align == "right":
        draw_x = x + w - text_width - 2
        draw_y = y + (h - text_height) // 2
    else:
        draw_x = x + 4
        draw_y = y + max(0, (h - text_height) // 2)

    surface.blit(text_surface, (draw_x, draw_y))


def render_text(font_cache: Dict[Tuple[int, bool], object], text: str, size: int, colour, bold: bool = False):
    font_module = getattr(pygame, "font", None)
    if font_module is None:
        return _FallbackFont(size).render(text, True, colour)

    try:
        if hasattr(font_module, "get_init") and hasattr(font_module, "init") and not font_module.get_init():
            font_module.init()
        cache_key = (int(size), bool(bold))
        font = font_cache.get(cache_key)
        if font is None:
            if hasattr(font_module, "SysFont"):
                font = font_module.SysFont("Tahoma", int(size), bold=bold)
            elif hasattr(font_module, "Font"):
                font = font_module.Font(None, int(size))
            else:
                font = _FallbackFont(size)
            font_cache[cache_key] = font
        return font.render(text, True, colour)
    except Exception:
        return _FallbackFont(size).render(text, True, colour)


def paint_dedicated_server_background(surface, watermark: str = "DEDICATED SERVER") -> None:
    width, height = surface.get_size()
    surface.fill(GROUND_SKY_TOP)

    for y in range(0, height, 2):
        blend = y / max(1, height)
        row_colour = (
            int(GROUND_SKY_TOP[0] + (GROUND_SKY_BOTTOM[0] - GROUND_SKY_TOP[0]) * blend),
            int(GROUND_SKY_TOP[1] + (GROUND_SKY_BOTTOM[1] - GROUND_SKY_TOP[1]) * blend),
            int(GROUND_SKY_TOP[2] + (GROUND_SKY_BOTTOM[2] - GROUND_SKY_TOP[2]) * blend),
        )
        pygame.draw.line(surface, row_colour, (0, y), (width, y))

    panel_glow = pygame.Surface((width, height), pygame.SRCALPHA)
    panel_glow.fill((255, 214, 110, 18))
    surface.blit(panel_glow, (0, 0))

    beam_1 = [
        (0, int(height * 0.18)),
        (int(width * 0.22), int(height * 0.20)),
        (int(width * 0.18), int(height * 0.31)),
        (0, int(height * 0.29)),
    ]
    beam_2 = [
        (0, int(height * 0.83)),
        (int(width * 0.55), int(height * 0.80)),
        (int(width * 0.58), int(height * 0.87)),
        (0, int(height * 0.89)),
    ]
    pygame.draw.polygon(surface, GROUND_STREAK, beam_1)
    pygame.draw.polygon(surface, GROUND_STREAK_DARK, beam_2)

    for offset in range(-height, width, 34):
        pygame.draw.line(surface, GROUND_DIAGONAL, (offset, height), (offset + int(height * 0.48), 0))

    watermark_surface = render_text({}, watermark, 34, GROUND_TEXT)
    surface.blit(watermark_surface, (18, 10))
