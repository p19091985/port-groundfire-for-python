import pygame
import sys
import os
from .report import report, debug

# Exception class
class InterfaceError(Exception):
    pass

class Colour:
    def __init__(self, r=1.0, g=1.0, b=1.0):
        # Auto-normalize if values are in 0-255 range (heuristic: if any > 1.0)
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
        # Convert 0.0-1.0 float range to 0-255 int range
        return (int(self.r * 255), int(self.g * 255), int(self.b * 255))

class Interface:
    current_interface = None

    def __init__(self, width, height, fullscreen):
        Interface.current_interface = self
        
        self._fullscreen = fullscreen
        self._width = width
        self._height = height
        self._mouse_enabled = False
        self._mouse_x = 0.0
        self._mouse_y = 0.0
        
        self.offset_x = 0.0
        self.offset_y = 0.0

        # Line width logic from resizeView in interface.cc
        self._line_width = 1

        # Initialize Pygame
        pygame.init()
        
        flags = pygame.RESIZABLE
        if fullscreen:
            flags |= pygame.FULLSCREEN
            
        try:
            self._window = pygame.display.set_mode((width, height), flags)
            pygame.display.set_caption("Groundfire")
        except pygame.error as e:
            report(f"ERROR: Could not create window: {e}")
            raise InterfaceError()
            
        # Texture management
        self._textures = {} # Dict mapping texture_num to pygame.Surface
        self._texture_files = {} # Dict mapping texture_num to filename
        self._num_textures = 0
        self._current_texture = -1 # ID of currently 'bound' texture
        
        # Joystick init
        pygame.joystick.init()
        self._num_controllers = 2 + pygame.joystick.get_count()
        self._joysticks = [None] * 8
        
        # Initialize joysticks
        for i in range(pygame.joystick.get_count()):
            if i < 8:
                try:
                    joy = pygame.joystick.Joystick(i)
                    joy.init()
                    self._joysticks[i] = joy
                except:
                    pass

        # Initial calculation of line width
        self._update_line_width()

    def __del__(self):
        pygame.quit()

    def _update_line_width(self):
        # Logic from interface.cc resizeView
        if self._width < 700:
            self._line_width = 1
        elif self._width < 1100:
            self._line_width = 2
        else:
            self._line_width = 3

    def get_line_width(self):
        return self._line_width

    def start_draw(self):
        self._window.fill((0, 0, 0))

    def end_draw(self):
        if self._mouse_enabled:
            self.draw_mouse()
            
        pygame.display.flip()
        
        # Pump events to update input states
        pygame.event.pump()
        
        if self._mouse_enabled:
            mx, my = pygame.mouse.get_pos()
            # Convert screen pixels to game coordinates
            # Game coordinates: x [-10, 10], y [-7.5, 7.5] (inverted Y in 2D usually)
            
            # Map mx (0..width) to (-10..10)
            self._mouse_x = -10.0 + (mx / self._width) * 20.0
            
            # Map my (0..height) to (7.5..-7.5)
            # Pygame Y=0 -> +7.5
            # Pygame Y=H -> -7.5
            self._mouse_y = 7.5 - (my / self._height) * 15.0

    def should_close(self):
        for event in pygame.event.get(pygame.QUIT):
            return True
        return False

    def get_mouse_pos(self):
        return self._mouse_x, self._mouse_y

    def get_mouse_button(self, button):
        # button: 0=Left, 1=Right, 2=Middle usually in GLFW?
        # Pygame: 0=Left, 1=Middle, 2=Right
        pressed = pygame.mouse.get_pressed()
        if button == 0: return pressed[0]
        if button == 1: return pressed[2] # Map GLFW Right to Pygame Right
        if button == 2: return pressed[1]
        return False

    def get_key(self, keycode):
        keys = pygame.key.get_pressed()
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
            report(f"ERROR: Failed to load file '{filename}'")
            return False
            
        try:
            surface = pygame.image.load(filename).convert_alpha()
            self._textures[texture_num] = surface
            self._texture_files[texture_num] = filename
            return True
        except pygame.error as e:
            report(f"ERROR: Failed to load texture '{filename}': {e}")
            return False

    def set_texture(self, texture):
        self._current_texture = texture

    def get_texture_surface(self, texture_id):
        return self._textures.get(texture_id)

    def get_texture_image(self, texture_id):
        return self.get_texture_surface(texture_id)

    def get_window_settings(self):
        return self._width, self._height, self._fullscreen

    def enable_mouse(self, enable):
        self._mouse_enabled = enable
        # If we enable our custom mouse, we hide the system one.
        pygame.mouse.set_visible(not enable)

    def change_window(self, width, height, fullscreen):
        if (self._width != width or self._height != height or self._fullscreen != fullscreen):
            self._width = width
            self._height = height
            self._fullscreen = fullscreen
            
            flags = pygame.RESIZABLE
            if fullscreen:
                flags |= pygame.FULLSCREEN
                
            try:
                self._window = pygame.display.set_mode((width, height), flags)
            except pygame.error:
                report("Error: Could not change window")
                raise InterfaceError()
            
            self._update_line_width() # Update line width on resize

    def num_of_controllers(self):
        return self._num_controllers

    def offset_viewport(self, x_offset, y_offset):
        self.offset_x = x_offset
        self.offset_y = y_offset

    # --- Helper methods for converting coordinates ---
    def game_to_screen(self, x, y):
        # Apply offset first?
        # glOrtho (-10.0 + xOffset, 10.0 + xOffset, ...)
        
        scale_x = self._width / 20.0
        scale_y = self._height / 15.0 
        
        sx = (x - (-10.0 + self.offset_x)) * scale_x
        sy = self._height - (y - (-7.5 + self.offset_y)) * scale_y
        
        return int(sx), int(sy)
        
    def scale_len(self, length):
        return int(length * (self._width / 20.0))

    def draw_mouse(self):
        if 8 in self._textures:
            tex = self._textures[8]
            
            # C++ draws shadow first at offset
            # gameX - 0.06f, gameY - 0.06f
            sx_shad, sy_shad = self.game_to_screen(self._mouse_x - 0.06, self._mouse_y - 0.06)
            
            # Create shadow surface (black with alpha)
            # Efficient way: if texture has alpha, we can just blit it with special flags or create a shadow version once.
            # For now, let's just draw the main cursor to fix the hotspot issue first.
            # Shadow implementation can be added if needed, but user complained about "highlighting" functionality.
            
            # Draw Main Cursor
            # C++ translates to (gameX, gameY) and draws quad downwards.
            # So (gameX, gameY) is the TOP-LEFT of the cursor image.
            
            sx, sy = self.game_to_screen(self._mouse_x, self._mouse_y)
            
            # Pygame blit takes topleft by default.
            self._window.blit(tex, (sx, sy))
