from typing import TYPE_CHECKING, List
import pygame

if TYPE_CHECKING:
    from .menu import Menu

class Selector:
    def __init__(self, menu: 'Menu', x: float, y: float, width: float, size: float):
        self._menu = menu
        self._x = x
        self._y = y
        self._width = width
        self._size = size
        
        self._highlighted = 0 # 0 none, 1 left, 2 right
        self._pressed = False
        self._current_option = 0
        self._disabled = False
        
        self._normal_col = (255, 255, 255)
        self._selected_col = (255, 255, 0)
        self._disabled_col = (255, 255, 255)
        
        self._options: List[str] = []

    def enable(self, enable: bool):
        self._disabled = not enable

    def set_colours(self, normal, selected, disabled):
        self._normal_col = normal
        self._selected_col = selected
        self._disabled_col = disabled

    def add_option(self, option: str):
        self._options.append(option)
        
    def get_option(self) -> int:
        return self._current_option
        
    def set_option(self, option: int):
        self._current_option = option

    def clear_options(self):
        self._current_option = 0
        self._options.clear()

    def update(self) -> int:
        if not self._disabled:
            interface = self._menu._game.get_interface()
            mx, my = interface.get_mouse_pos()
            
            self._highlighted = 0
            
            # Check Y bounds
            if (self._y + self._size/2.0) > my and (self._y - self._size/2.0) < my:
                # Left Arrow: [x - w/2 - size, x - w/2]
                left_btn_right = self._x - self._width/2.0
                left_btn_left = left_btn_right - self._size
                
                right_btn_left = self._x + self._width/2.0
                right_btn_right = right_btn_left + self._size
                
                if left_btn_right > mx and left_btn_left < mx:
                    self._highlighted = 1
                    if interface.get_mouse_button(0):
                        self._pressed = True
                    elif self._pressed:
                        self._current_option -= 1
                        if self._current_option == -1:
                             self._current_option = len(self._options) - 1
                        self._pressed = False
                        return -1 # Dec
                
                elif right_btn_right > mx and right_btn_left < mx:
                    self._highlighted = 2
                    if interface.get_mouse_button(0):
                        self._pressed = True
                    elif self._pressed:
                        self._current_option += 1
                        if self._current_option == len(self._options):
                            self._current_option = 0
                        self._pressed = False
                        return 1 # Inc
                else:
                    self._pressed = False
            else:
                self._pressed = False
                
        return 0

    def draw(self):
        self._draw_arrow(self._x - self._width/2.0, self._y, True, self._highlighted == 1)
        self._draw_arrow(self._x + self._width/2.0, self._y, False, self._highlighted == 2)
        
        if not self._disabled and self._options:
             font = self._menu._game.get_font()
             font.set_shadow(True)
             font.set_colour(self._normal_col)
             font.set_size(self._size, self._size, self._size - 0.1)
             
             if 0 <= self._current_option < len(self._options):
                 font.print_centred_at(self._x, self._y - self._size/2.0, self._options[self._current_option])
             
             font.set_shadow(False)

    def _draw_arrow(self, x, y, direction_left, highlighted):
        interface = self._menu._game.get_interface()
        
        color = self._normal_col
        alpha = 255
        
        if self._disabled:
            color = self._disabled_col
            alpha = 25 # 0.1
        elif highlighted:
            color = self._selected_col
            
        # Draw Triangle
        # Left: (x-size, y), (x, y+s/2), (x, y-s/2)
        # Right: (x+size, y), (x, y+s/2), (x, y-s/2)
        
        points = []
        if direction_left:
            points.append((x - self._size, y))
            points.append((x, y + self._size/2.0))
            points.append((x, y - self._size/2.0))
        else:
            points.append((x + self._size, y))
            points.append((x, y + self._size/2.0))
            points.append((x, y - self._size/2.0))
            
        screen_points = [interface.game_to_screen(px, py) for px, py in points]
        
        # Draw with alpha if needed (Pygame needs surface for alpha shapes usually)
        if alpha < 255:
            # Bounding box
            xs = [p[0] for p in screen_points]
            ys = [p[1] for p in screen_points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            w, h = max_x - min_x, max_y - min_y
            
            if w > 0 and h > 0:
                s = pygame.Surface((w, h), pygame.SRCALPHA)
                local_pts = [(p[0] - min_x, p[1] - min_y) for p in screen_points]
                pygame.draw.polygon(s, color + (alpha,), local_pts)
                interface._window.blit(s, (min_x, min_y))
        else:
            pygame.draw.polygon(interface._window, color, screen_points)
