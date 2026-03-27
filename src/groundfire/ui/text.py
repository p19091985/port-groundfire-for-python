from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class TextStyle:
    x_size: float
    y_size: float
    x_spacing: float
    colour: tuple
    shadow: bool = False
    proportional: bool = True
    orientation: float = 0.0


class GameUI:
    def __init__(self, *, font_provider: Callable[[], object | None]):
        self._font_provider = font_provider

    @staticmethod
    def style(
        size: float,
        colour: tuple,
        *,
        y_size: float | None = None,
        spacing: float | None = None,
        shadow: bool = False,
        proportional: bool = True,
        orientation: float = 0.0,
    ) -> TextStyle:
        return TextStyle(
            x_size=size,
            y_size=size if y_size is None else y_size,
            x_spacing=(size - 0.1) if spacing is None else spacing,
            colour=colour,
            shadow=shadow,
            proportional=proportional,
            orientation=orientation,
        )

    def draw_text(self, x: float, y: float, text: str, *, style: TextStyle):
        font = self._configure_font(style)
        try:
            font.print_at(x, y, text)
        finally:
            self._restore_font(font)

    def draw_centered_text(self, x: float, y: float, text: str, *, style: TextStyle):
        font = self._configure_font(style)
        try:
            font.print_centred_at(x, y, text)
        finally:
            self._restore_font(font)

    def printf(self, x: float, y: float, fmt: str, *args, style: TextStyle):
        font = self._configure_font(style)
        try:
            font.printf(x, y, fmt, *args)
        finally:
            self._restore_font(font)

    def measure_text(self, text: str, *, style: TextStyle) -> float:
        font = self._configure_font(style)
        try:
            return font.find_string_length(text)
        finally:
            self._restore_font(font)

    def _configure_font(self, style: TextStyle):
        font = self._get_font()
        font.set_shadow(style.shadow)
        font.set_proportional(style.proportional)
        font.set_orientation(style.orientation)
        font.set_size(style.x_size, style.y_size, style.x_spacing)
        font.set_colour(style.colour)
        return font

    def _restore_font(self, font):
        font.set_shadow(False)
        font.set_proportional(True)
        font.set_orientation(0.0)

    def _get_font(self):
        font = self._font_provider()
        if font is None:
            raise RuntimeError("GameUI font is not initialized yet.")
        return font
