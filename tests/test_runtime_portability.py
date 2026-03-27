import unittest

from src.font import Font
from src.interface import Interface
from src.sounds import Sound
from tests.support import install_fake_pygame


class FontInterfaceStub:
    def __init__(self, pygame_module):
        self.surface = pygame_module.Surface((64, 64))
        self.blit_calls = []

    def get_texture_surface(self, _texture_id):
        return self.surface

    def load_texture(self, _filename, _texture_id):
        return True

    def scale_len(self, length):
        return max(1, int(length * 10))

    def game_to_screen(self, x, y):
        return (int(x), int(y))

    def blit_surface(self, surface, dest, *args, **kwargs):
        self.blit_calls.append((surface, dest, args, kwargs))
        return None

    def get_draw_surface(self):
        return self.surface


class RuntimePortabilityTests(unittest.TestCase):
    def setUp(self):
        self.pygame = install_fake_pygame()

    def test_interface_accepts_injected_pygame_module(self):
        interface = Interface(640, 480, False, pygame_module=self.pygame)

        self.assertEqual(interface.get_window_settings(), (640, 480, False))
        self.assertIsNotNone(interface.get_draw_surface())

    def test_sound_accepts_injected_pygame_module(self):
        sound = Sound(2, pygame_module=self.pygame)
        sound.load_sound(0, "dummy.wav")

        self.assertIsNotNone(sound._buffers[0])

    def test_font_accepts_injected_pygame_module(self):
        interface = FontInterfaceStub(self.pygame)
        font = Font(interface, 3, pygame_module=self.pygame)

        font.printf(0.0, 0.0, "A")

        self.assertTrue(interface.blit_calls)


if __name__ == "__main__":
    unittest.main()
