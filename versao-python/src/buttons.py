from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from .menu import Menu

class Button:
    def __init__(self, menu: 'Menu', x: float, y: float, size: float):
        self._menu = menu
        self._x = x
        self._y = y
        self._size = size
        
        self._normal_col = (1.0, 1.0, 1.0)
        self._selected_col = (1.0, 1.0, 0.0)
        self._disabled_col = (0.1, 0.1, 0.1) # 0.1 float -> ~25 int
        
        self._highlighted = False
        self._pressed = False
        self._disabled = False

    def enable(self, enable: bool):
        self._disabled = not enable
        self._pressed = False

    def update(self) -> bool:
        raise NotImplementedError

    def draw(self):
        raise NotImplementedError

class TextButton(Button):
    def __init__(self, menu: 'Menu', x: float, y: float, size: float, text: str):
        super().__init__(menu, x, y, size)
        self._text = text

    def draw(self):
        if self._disabled:
            colour = self._disabled_col
        elif self._highlighted:
            colour = self._selected_col
        else:
            colour = self._normal_col

        self._menu._ui.draw_centered_text(
            self._x,
            self._y - self._size / 2.0,
            self._text,
            style=self._menu._ui.style(self._size, colour, shadow=not self._disabled),
        )

    def update(self) -> bool:
        if not self._disabled:
            interface = self._menu._game.get_interface()
            mx, my = interface.get_mouse_pos()
            
            self._highlighted = False
            
            # Button is centered vertically at _y? 
            # In C++: _y + _size/2 > dy and _y - _size/2 < dy
            # So range is [_y - size/2, _y + size/2]
            
            if (self._y + self._size / 2.0) > my and (self._y - self._size / 2.0) < my:
                # Check Horizontal
                length = self._menu._ui.measure_text(
                    self._text,
                    style=self._menu._ui.style(self._size, self._normal_col),
                )
                
                if (self._x + length / 2.0) > mx and (self._x - length / 2.0) < mx:
                    self._highlighted = True
                    
                    if interface.get_mouse_button(0): # Left Click
                        self._pressed = True
                    elif self._pressed:
                        # Released
                        return True
                else:
                    self._pressed = False
            else:
                self._pressed = False
                
        return False

class GfxButton(Button):
    def __init__(self, menu: 'Menu', x: float, y: float, size: float, texture: int):
        super().__init__(menu, x, y, size)
        self._texture = texture
        self._disabled_col = (1.0, 1.0, 1.0) # Different default for Gfx buttons

    def update(self) -> bool:
        if not self._disabled:
            interface = self._menu._game.get_interface()
            mx, my = interface.get_mouse_pos()
            
            self._highlighted = False
            half_size = self._size / 2.0
            
            if (self._y + half_size) > my and (self._y - half_size) < my and \
               (self._x + half_size) > mx and (self._x - half_size) < mx:
                
                self._highlighted = True
                
                if interface.get_mouse_button(0):
                    self._pressed = True
                elif self._pressed:
                    return True
            else:
                self._pressed = False
                
        return False

    def draw(self):
        # In C++ this uses glColor4f with alpha.
        # Disabled: 0.2 alpha. Highlighted/Normal: 1.0 alpha.
        
        alpha = 255
        color = self._normal_col
        
        if self._disabled:
            color = self._disabled_col
            alpha = 51 # 0.2 * 255
        elif self._highlighted:
            color = self._selected_col
            
        # Draw Textured Quad
        # Pygame doesn't easily modulate texture color unless using specific blend flags
        # or creating a colored surface to multiply.
        
        interface = self._menu._game.get_interface()
        raw_tex_id = self._texture
        
        # We need to access the texture from interface.
        # Interface doesn't expose `get_texture` directly in my previous read?
        # I should check if I can access textures or if I need to implement `draw_texture_button`.
        
        # Assuming interface has access or I can use interface helpers.
        # Actually `interface.set_texture` in C++ binds GL texture.
        # In Python Interface, `_textures` is map.
        
        # Let's assume we can get it via standard Texture logic or simply blit.
        # But wait, Button logic needs to apply Color modulation (tint).
        
        # Simplified for now: just draw un-tinted texture if normal, or tinted if highlighted?
        # C++ tints: Yellow if highlighted. White if normal.
        
        self._menu._graphics.draw_texture_world_rect(
            raw_tex_id,
            self._x - self._size / 2.0,
            self._y + self._size / 2.0,
            self._x + self._size / 2.0,
            self._y - self._size / 2.0,
            alpha=alpha,
            tint=color,
        )
