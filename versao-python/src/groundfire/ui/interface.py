from __future__ import annotations

import os

from ..core.pygame import PygameBackend


class InterfaceError(Exception):
    pass


class Colour:
    def __init__(self, r=1.0, g=1.0, b=1.0):
        if r > 1.0 or g > 1.0 or b > 1.0:
            self.r = r / 255.0
            self.g = g / 255.0
            self.b = b / 255.0
        else:
            self.r = r
            self.g = g
            self.b = b

    def __eq__(self, other):
        return self.r == other.r and self.g == other.g and self.b == other.b

    def to_tuple(self):
        return (int(self.r * 255), int(self.g * 255), int(self.b * 255))


class Interface:
    current_interface = None

    def __init__(self, width, height, fullscreen, *, pygame_module=None):
        from .graphics import get_interface_graphics

        Interface.current_interface = self
        self._backend = PygameBackend.create(pygame_module)
        self._pygame = self._backend.pygame
        self._fullscreen = fullscreen
        self._width = width
        self._height = height
        self._mouse_enabled = False
        self._mouse_x = 0.0
        self._mouse_y = 0.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._line_width = 1
        self._closed = False

        self._pygame.init()
        try:
            self._window = self._pygame.display.set_mode((width, height), self._display_flags(fullscreen))
            self._pygame.display.set_caption("Groundfire")
        except self._pygame.error as exc:
            raise InterfaceError() from exc

        self._textures = {}
        self._texture_files = {}
        self._num_textures = 0
        self._current_texture = -1

        self._pygame.joystick.init()
        self._num_controllers = 2 + self._pygame.joystick.get_count()
        self._joysticks = [None] * 8
        for index in range(self._pygame.joystick.get_count()):
            if index >= 8:
                break
            try:
                joystick = self._pygame.joystick.Joystick(index)
                joystick.init()
                self._joysticks[index] = joystick
            except Exception:
                pass

        self._update_line_width()
        get_interface_graphics(self)

    def __del__(self):
        self.close()

    def close(self):
        if getattr(self, "_closed", True):
            return
        self._closed = True
        if hasattr(self, "_pygame"):
            try:
                self._pygame.quit()
            except Exception:
                pass

    def _update_line_width(self):
        if self._width < 700:
            self._line_width = 1
        elif self._width < 1100:
            self._line_width = 2
        else:
            self._line_width = 3

    def get_line_width(self):
        return self._line_width

    def get_draw_surface(self):
        return self._window

    def fill_surface(self, colour):
        self._window.fill(colour)

    def blit_surface(self, surface, dest, *args, **kwargs):
        return self._window.blit(surface, dest, *args, **kwargs)

    def draw_polygon(self, colour, points):
        self._pygame.draw.polygon(self._window, colour, points)

    def draw_rect(self, colour, rect):
        self._pygame.draw.rect(self._window, colour, rect)

    def draw_line(self, colour, start, end, width):
        self._pygame.draw.line(self._window, colour, start, end, width)

    def start_draw(self):
        from .graphics import get_interface_graphics

        self._sync_window_size_from_surface()
        get_interface_graphics(self).clear((0, 0, 0))

    def end_draw(self):
        self._sync_window_size_from_surface()
        if self._mouse_enabled:
            self.draw_mouse()
        self._pygame.display.flip()
        self._pygame.event.pump()
        self._sync_window_size_from_surface()
        if self._mouse_enabled:
            mx, my = self._pygame.mouse.get_pos()
            self._mouse_x = -10.0 + (mx / self._width) * 20.0
            self._mouse_y = 7.5 - (my / self._height) * 15.0

    def should_close(self):
        for event in self._pygame.event.get(self._window_event_types(include_quit=True)):
            if getattr(event, "type", None) == self._pygame.QUIT:
                return True
            self._handle_window_event(event)
        return False

    def _window_event_types(self, *, include_quit: bool = False):
        event_types = []
        if include_quit:
            event_types.append(self._pygame.QUIT)
        for name in ("VIDEORESIZE", "WINDOWRESIZED", "WINDOWSIZECHANGED"):
            event_type = getattr(self._pygame, name, None)
            if event_type is not None:
                event_types.append(event_type)
        return event_types

    def _is_resize_event(self, event) -> bool:
        return getattr(event, "type", None) in set(self._window_event_types())

    def _handle_window_event(self, event):
        if not self._is_resize_event(event):
            return
        size = getattr(event, "size", None)
        if size is not None and len(size) >= 2:
            width, height = int(size[0]), int(size[1])
        elif hasattr(event, "w") and hasattr(event, "h"):
            width = int(event.w)
            height = int(event.h)
        elif hasattr(event, "x") and hasattr(event, "y"):
            width = int(event.x)
            height = int(event.y)
        else:
            width, height = self._current_display_size()
        self._resize_window(width, height, self._fullscreen)

    def _current_display_size(self):
        get_window_size = getattr(self._pygame.display, "get_window_size", None)
        if callable(get_window_size):
            width, height = get_window_size()
            return int(width), int(height)

        get_surface = getattr(self._pygame.display, "get_surface", None)
        if callable(get_surface):
            surface = get_surface()
            get_size = getattr(surface, "get_size", None)
            if callable(get_size):
                width, height = get_size()
                return int(width), int(height)

        return self._width, self._height

    def _sync_window_size_from_surface(self):
        get_size = getattr(self._window, "get_size", None)
        if not callable(get_size):
            return
        width, height = get_size()
        width = int(width)
        height = int(height)
        if width <= 0 or height <= 0:
            return
        if width == self._width and height == self._height:
            return
        self._width = width
        self._height = height
        self._update_line_width()

    def _display_flags(self, fullscreen: bool):
        flags = self._pygame.RESIZABLE
        if fullscreen:
            flags |= self._pygame.FULLSCREEN
        return flags

    def _resize_window(self, width: int, height: int, fullscreen: bool):
        width = max(320, int(width))
        height = max(240, int(height))
        if self._width == width and self._height == height and self._fullscreen == fullscreen:
            return
        self._width = width
        self._height = height
        self._fullscreen = fullscreen
        try:
            self._window = self._pygame.display.set_mode((width, height), self._display_flags(fullscreen))
        except self._pygame.error as exc:
            raise InterfaceError() from exc
        self._update_line_width()

    def get_input_events(self):
        event_types = [self._pygame.KEYDOWN]
        if hasattr(self._pygame, "MOUSEWHEEL"):
            event_types.append(self._pygame.MOUSEWHEEL)
        event_types.extend(self._window_event_types())
        input_events = []
        for event in self._pygame.event.get(event_types):
            if self._is_resize_event(event):
                self._handle_window_event(event)
            else:
                input_events.append(event)
        return tuple(input_events)

    def get_key_names(self):
        return {
            "backspace": self._pygame.K_BACKSPACE,
            "enter": self._pygame.K_RETURN,
            "escape": self._pygame.K_ESCAPE,
            "tab": self._pygame.K_TAB,
            "up": self._pygame.K_UP,
            "down": self._pygame.K_DOWN,
            "pageup": self._pygame.K_PAGEUP,
            "pagedown": self._pygame.K_PAGEDOWN,
        }

    def get_mouse_pos(self):
        return self._mouse_x, self._mouse_y

    def get_mouse_button(self, button):
        pressed = self._pygame.mouse.get_pressed()
        if button == 0:
            return pressed[0]
        if button == 1:
            return pressed[2]
        if button == 2:
            return pressed[1]
        return False

    def get_key(self, keycode):
        keys = self._pygame.key.get_pressed()
        if keycode < len(keys):
            return keys[keycode]
        return False

    def get_joystick_button(self, joy_device, button):
        if 0 <= joy_device < len(self._joysticks) and self._joysticks[joy_device]:
            if button < self._joysticks[joy_device].get_numbuttons():
                return self._joysticks[joy_device].get_button(button)
        return False

    def get_joystick_axis(self, joy_device, axis):
        if 0 <= joy_device < len(self._joysticks) and self._joysticks[joy_device]:
            if axis < self._joysticks[joy_device].get_numaxes():
                return self._joysticks[joy_device].get_axis(axis)
        return 0.0

    def define_textures(self, num_of_textures):
        self._num_textures = num_of_textures

    def load_texture(self, filename, texture_num):
        if not os.path.exists(filename):
            return False
        try:
            surface = self._pygame.image.load(filename).convert_alpha()
            self._textures[texture_num] = surface
            self._texture_files[texture_num] = filename
            return True
        except self._pygame.error:
            return False

    def set_texture(self, texture):
        self._current_texture = texture

    def get_texture_surface(self, texture_id):
        return self._textures.get(texture_id)

    def get_texture_image(self, texture_id):
        return self.get_texture_surface(texture_id)

    def get_window_settings(self):
        return self._width, self._height, self._fullscreen

    def set_window_caption(self, caption: str):
        self._pygame.display.set_caption(caption)

    def enable_mouse(self, enable):
        self._mouse_enabled = enable
        self._pygame.mouse.set_visible(not enable)

    def change_window(self, width, height, fullscreen):
        self._resize_window(width, height, fullscreen)

    def num_of_controllers(self):
        return self._num_controllers

    def offset_viewport(self, x_offset, y_offset):
        self.offset_x = x_offset
        self.offset_y = y_offset

    def game_to_screen(self, x, y):
        scale_x = self._width / 20.0
        scale_y = self._height / 15.0
        sx = (x - (-10.0 + self.offset_x)) * scale_x
        sy = self._height - (y - (-7.5 + self.offset_y)) * scale_y
        return int(sx), int(sy)

    def scale_len(self, length):
        return int(length * (self._width / 20.0))

    def draw_mouse(self):
        from .graphics import get_interface_graphics

        if 8 in self._textures:
            sx, sy = self.game_to_screen(self._mouse_x, self._mouse_y)
            get_interface_graphics(self).blit_texture(8, (sx, sy))
