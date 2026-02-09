import pygame
from .interface import Interface, Colour

class FontError(Exception):
    pass

class Font:
    def __init__(self, interface: Interface, tex_num: int):
        self._interface = interface
        self._tex_num = tex_num
        self._colour = Colour(1.0, 1.0, 1.0)
        
        # Load the font texture via interface
        # "data/fonts.tga"
        if not self._interface.load_texture("data/fonts.tga", tex_num):
            raise FontError()
            
        self._shadow = False
        self._proportional = True
        self._orientation = 0.0
        
        self._x_size = 1.0
        self._y_size = 1.0
        self._x_spacing = 1.0
        
        # Original Widths table
        self._widths = [
             9,  9, 14, 18, 18, 27, 24,  8, 11, 11, 15, 18,
             9,  9,  9,  8, 18, 18, 18, 18, 18, 18, 18, 18,
            18, 18,  9,  9, 18, 18, 18, 17, 20, 21, 21, 21,
            21, 20, 18, 22, 22, 11, 18, 22, 18, 25, 22, 22,
            20, 22, 21, 20, 20, 22, 21, 27, 21, 21, 20, 11,
             8, 11, 18, 14,  9, 18, 18, 18, 18, 18, 11, 18,
            18,  9,  9, 18,  9, 27, 18, 18, 18, 18, 14, 17,
            13, 18, 17, 25, 18, 17, 15, 11,  8, 11, 18, 17,
            18, 10,  8, 18, 14, 27, 18, 18,  9, 27, 20,  9,
            27, 10, 20, 10, 10,  8,  8, 14, 14, 14, 14, 27,
             9, 26, 17,  9, 27, 10, 15, 21
        ]
        # Pad rest of 128
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
        if args:
            try:
                text = fmt % args
            except:
                text = fmt
        else:
            text = fmt
            
        if self._shadow:
            self._print_string(x - self._x_size / 8.0, y - self._y_size / 8.0, text, True)
            
        self._print_string(x, y, text, False)

    def print_at(self, x, y, fmt, *args):
        self.printf(x, y, fmt, *args)

    def print_centred_at(self, x_centre, y, fmt, *args):
        if args:
            try:
                text = fmt % args
            except:
                text = fmt
        else:
            text = fmt
            
        length = self.find_string_length(text)
        x = x_centre - (length / 2.0)
        
        if self._shadow:
            self._print_string(x - self._x_size / 8.0, y - self._y_size / 8.0, text, True)
            
        self._print_string(x, y, text, False)

    def find_string_length(self, string):
        width = 0.0
        if self._proportional:
            for char in string:
                idx = ord(char) - 32
                if 0 <= idx < len(self._widths):
                    width += self._widths[idx]
                else:
                    width += 18
            return (width / 24.0) * self._x_spacing
        else:
            return (len(string) - 1) * self._x_spacing + self._x_size

    def _print_string(self, x, y, string, shadow):
        # Retrieve the texture surface from Interface
        tex_surface = self._interface.get_texture_surface(self._tex_num)
        if not tex_surface:
            return
            
        # Overall texture dimensions
        tex_w, tex_h = tex_surface.get_size()
        
        # Grid is 16x16 chars.
        # Original code uses messy texture coords
        # float texX = (float)(string[i] % 16) / 16.0f;
        # float texY = 1.0f - ((float)((string[i] - 32) / 16) / 16.0f);
        
        # We need to extract subsurfaces.
        # Assuming 256x256 texture? Or generic?
        # A cell is w/16 wide, h/16 high.
        cell_w = tex_w / 16
        cell_h = tex_h / 16
        
        current_x = x
        
        # Prepare colour
        # Pygame surface coloring usually done by fill special_flags=BLEND_RGBA_MULT
        # But that's slow per char.
        # For optimization, we might cache chars. user asks for fidelity first.
        
        text_color = (0, 0, 0, 100) if shadow else self._colour.to_tuple()
        
        for char in string:
            ascii_val = ord(char)
            if ascii_val < 32: continue
            
            idx = ascii_val # Original uses % 16 on char, but row calc uses (char-32).
            # "string[i] % 16" -> Column
            col = ascii_val % 16
            # "(string[i] - 32) / 16" -> Row. Since texture Y is usually 0 at bottom in OpenGL, and top in Pygame...
            # Original: 1.0 - ... means texture origin at Bottom Left?
            # Interface.cc says: stbi_set_flip_vertically_on_load(1);
            # So texture is loaded upside down compared to standard image formats?
            # Or formatted for OpenGL.
            # If we load with pygame.image.load, it's Top-Left origin.
            
            # Let's assume standard grid layout starting from top-left for Pygame.
            row = (ascii_val - 32) // 16
            
            # Logic from C++: Proportional font uses bottom half of texture?
            # texY -= 0.5010f indicates it shifts down by half height.
            # In Pygame (Y down), this means adding half height.
            
            src_y = row * cell_h
            if self._proportional:
                src_y += (tex_h / 2) # Shift to bottom half
            
            # Extract char image
            # Warning: bounds check
            rect = pygame.Rect(col * cell_w, src_y, cell_w, cell_h)
            try:
                char_surf = tex_surface.subsurface(rect).copy()
            except ValueError:
                continue
                
            # Tint
            # Using fill with MULT for RGB tinting
            if not shadow:
                # White text doesn't need tinting if texture is white
                # But if color is not white:
                if text_color != (255, 255, 255):
                    # Create a solid color surface
                    colour_surf = pygame.Surface(char_surf.get_size(), pygame.SRCALPHA)
                    # Ensure we unpack only RGB if we append 255 explicitly, 
                    # OR check if text_color has 4 components.
                    # text_color comes from self._colour.to_tuple() which is 3 ints.
                    
                    rgb = text_color[:3]
                    colour_surf.fill((*rgb, 255))
                    char_surf.blit(colour_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            else:
                # Shadow - black + alpha
                colour_surf = pygame.Surface(char_surf.get_size(), pygame.SRCALPHA)
                colour_surf.fill((0, 0, 0, 100)) # Alpha 100
                char_surf.blit(colour_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # Rotation
            if self._orientation != 0.0:
                char_surf = pygame.transform.rotate(char_surf, self._orientation)

            # Scale to screen size
            # x_size is in Game Units.
            # We need to scale the surface to match the pixel size of x_size.
            # Interface helper: scale_len
            
            w_px = self._interface.scale_len(self._x_size)
            h_px = self._interface.scale_len(self._y_size)
            
            # If proportional, width might be smaller
            if self._proportional:
                # Original: width = _xSize * 0.8
                w_px = int(w_px * 0.8)
            
            char_surf = pygame.transform.smoothscale(char_surf, (int(w_px), int(h_px)))

            # Draw
            screen_x, screen_y = self._interface.game_to_screen(current_x, y)
             # Note: game_to_screen y returns Center? Top?
             # Original uses Bottom-Left usually for Font drawing logic?
             # "glVertex3f (charX, 0.0f, ...)" 
             # It draws a quad from (0,0) to (width, ySize).
             # So (x,y) passed to printString is Bottom-Left corner of text.
             
             # game_to_screen converts (x,y) to pixels.
             # In Pygame blit takes Top-Left.
             # If (x,y) is bottom-left in Game World, 
             # screen_y is the pixel coordinate of that bottom line.
             # So we need to subtract surface height to get Top-Left for blit.
             
            dest_y = screen_y - char_surf.get_height()
            
            self._interface._window.blit(char_surf, (screen_x, dest_y))
            
            if self._proportional:
                 shift = (self._widths[ascii_val - 32] / 24.0) * self._x_spacing
                 current_x += shift
            else:
                 current_x += self._x_spacing
