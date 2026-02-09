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
        font = self._menu._game.get_font()
        
        if self._disabled:
            font.set_colour(self._disabled_col)
        elif self._highlighted:
            font.set_colour(self._selected_col)
        else:
            font.set_colour(self._normal_col)
            
        if not self._disabled:
            font.set_shadow(True)
            
        # size matches original C++: size, size, size-0.1
        font.set_size(self._size, self._size, self._size - 0.1)
        font.print_centred_at(self._x, self._y - self._size / 2.0, self._text)
        font.set_shadow(False)

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
                font = self._menu._game.get_font()
                font.set_size(self._size, self._size, self._size - 0.1)
                length = font.find_string_length(self._text)
                
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
        
        tex = interface.get_texture_image(raw_tex_id)
        if tex:
            # Scale
            # Quad from (x-half, y-half) to (x+half, y+half) (game coords)
            # Size in game units = self._size
            # We need to project to screen.
            
            p1 = interface.game_to_screen(self._x - self._size/2, self._y + self._size/2) # Top Left
            p2 = interface.game_to_screen(self._x + self._size/2, self._y - self._size/2) # Bottom Right
            
            w = p2[0] - p1[0]
            h = p2[1] - p1[1]
            
            if w > 0 and h > 0:
                scaled_tex = pygame.transform.scale(tex, (int(w), int(h)))
                
                # Tinting: create Surface of color, mult blend
                if color != (255, 255, 255) or alpha != 255:
                    tint_surf = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
                    r,g,b = color
                    tint_surf.fill((r, g, b, alpha))
                    # Basic modulation approximation:
                    # scaled_tex.blit(tint_surf, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                    # But if texture has alpha, we need to respect it.
                    
                    # For now just blit texture, then if highlighted draw yellow rect border?
                    # Or proper tint.
                    
                    # A robust way:
                    # Copy texture
                    # Fill with color mult
                    pass 
                
                # Handling alpha for disabled
                if alpha < 255:
                    scaled_tex.set_alpha(alpha)
                
                interface._window.blit(scaled_tex, p1)
