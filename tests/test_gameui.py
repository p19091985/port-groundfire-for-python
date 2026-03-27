import unittest

from src.gameui import GameUI


class FontStub:
    def __init__(self):
        self.shadow_calls = []
        self.proportional_calls = []
        self.orientation_calls = []
        self.size_calls = []
        self.colour_calls = []
        self.print_calls = []
        self.centred_calls = []
        self.printf_calls = []

    def set_shadow(self, value):
        self.shadow_calls.append(value)

    def set_proportional(self, value):
        self.proportional_calls.append(value)

    def set_orientation(self, value):
        self.orientation_calls.append(value)

    def set_size(self, *args):
        self.size_calls.append(args)

    def set_colour(self, colour):
        self.colour_calls.append(colour)

    def print_at(self, *args):
        self.print_calls.append(args)

    def print_centred_at(self, *args):
        self.centred_calls.append(args)

    def printf(self, *args):
        self.printf_calls.append(args)

    def find_string_length(self, text):
        return len(text) * 1.5


class GameUITests(unittest.TestCase):
    def test_draw_centered_text_applies_style_and_resets_font_state(self):
        font = FontStub()
        ui = GameUI(font_provider=lambda: font)

        ui.draw_centered_text(1.0, 2.0, "Hello", style=ui.style(0.6, (255, 255, 255), shadow=True, spacing=0.5))

        self.assertEqual(font.shadow_calls, [True, False])
        self.assertEqual(font.proportional_calls, [True, True])
        self.assertEqual(font.orientation_calls, [0.0, 0.0])
        self.assertEqual(font.size_calls, [(0.6, 0.6, 0.5)])
        self.assertEqual(font.colour_calls, [(255, 255, 255)])
        self.assertEqual(font.centred_calls, [(1.0, 2.0, "Hello")])

    def test_measure_text_uses_same_style_pipeline(self):
        font = FontStub()
        ui = GameUI(font_provider=lambda: font)

        result = ui.measure_text("ABCD", style=ui.style(0.4, (1.0, 1.0, 1.0), proportional=False))

        self.assertEqual(result, 6.0)
        self.assertEqual(font.shadow_calls, [False, False])
        self.assertEqual(font.proportional_calls, [False, True])
        self.assertEqual(font.orientation_calls, [0.0, 0.0])
        self.assertEqual(font.size_calls, [(0.4, 0.4, 0.30000000000000004)])

    def test_printf_formats_through_font(self):
        font = FontStub()
        ui = GameUI(font_provider=lambda: font)

        ui.printf(-10.0, -7.3, "%.1f FPS", 87.5, style=ui.style(0.3, (128, 255, 51), spacing=0.25))

        self.assertEqual(font.printf_calls, [(-10.0, -7.3, "%.1f FPS", 87.5)])
        self.assertEqual(font.shadow_calls, [False, False])
        self.assertEqual(font.colour_calls, [(128, 255, 51)])


if __name__ == "__main__":
    unittest.main()
