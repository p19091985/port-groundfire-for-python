import unittest
from types import SimpleNamespace

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

    def test_interface_handles_resize_events_and_updates_projection(self):
        self.pygame.VIDEORESIZE = 32769
        self.pygame.KEYDOWN = 768
        set_mode_calls = []
        original_set_mode = self.pygame.display.set_mode
        original_get = self.pygame.event.get

        def set_mode(size, flags=0):
            set_mode_calls.append((tuple(size), flags))
            return self.pygame.Surface(size)

        def event_get(event_types):
            if self.pygame.VIDEORESIZE in event_types:
                return [SimpleNamespace(type=self.pygame.VIDEORESIZE, size=(1280, 720))]
            return []

        self.pygame.display.set_mode = set_mode
        self.pygame.event.get = event_get
        try:
            interface = Interface(640, 480, False, pygame_module=self.pygame)

            self.assertFalse(interface.should_close())
            self.assertEqual(interface.get_window_settings(), (1280, 720, False))
            self.assertEqual(interface.get_draw_surface().get_size(), (1280, 720))
            self.assertEqual(interface.game_to_screen(10.0, 7.5), (1280, 0))
            self.assertEqual(set_mode_calls[-1][0], (1280, 720))
        finally:
            self.pygame.display.set_mode = original_set_mode
            self.pygame.event.get = original_get

    def test_interface_accepts_window_resized_xy_events(self):
        self.pygame.WINDOWRESIZED = 32778
        self.pygame.KEYDOWN = 768
        original_get = self.pygame.event.get

        def event_get(event_types):
            if self.pygame.WINDOWRESIZED in event_types:
                return [SimpleNamespace(type=self.pygame.WINDOWRESIZED, x=1024, y=768)]
            return []

        self.pygame.event.get = event_get
        try:
            interface = Interface(640, 480, False, pygame_module=self.pygame)

            self.assertFalse(interface.should_close())
            self.assertEqual(interface.get_window_settings(), (1024, 768, False))
            self.assertEqual(interface.get_draw_surface().get_size(), (1024, 768))
        finally:
            self.pygame.event.get = original_get

    def test_interface_filters_resize_out_of_input_events(self):
        self.pygame.VIDEORESIZE = 32769
        self.pygame.KEYDOWN = 768
        original_get = self.pygame.event.get
        resize_event = SimpleNamespace(type=self.pygame.VIDEORESIZE, w=900, h=600)
        key_event = SimpleNamespace(type=self.pygame.KEYDOWN, key=1)

        def event_get(event_types):
            self.assertIn(self.pygame.VIDEORESIZE, event_types)
            return [resize_event, key_event]

        self.pygame.event.get = event_get
        try:
            interface = Interface(640, 480, False, pygame_module=self.pygame)

            self.assertEqual(interface.get_input_events(), (key_event,))
            self.assertEqual(interface.get_window_settings(), (900, 600, False))
        finally:
            self.pygame.event.get = original_get

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
