from typing import TYPE_CHECKING
from .menu import Menu
from .selector import Selector
from .buttons import TextButton
from .common import GameState
import pygame

if TYPE_CHECKING:
    from .game import Game

class OptionMenu(Menu):
    def __init__(self, game: 'Game'):
        super().__init__(game)
        
        self._resolutions = Selector(self, 3.0, 1.0, 4.0, 0.6)
        self._resolutions.add_option("640 x 480")
        self._resolutions.add_option("800 x 600")
        self._resolutions.add_option("1024 x 768")
        self._resolutions.add_option("1280 x 960")
        self._resolutions.add_option("1280 x 1024")
        self._resolutions.add_option("1600 x 1200")
        
        self._screen_mode = Selector(self, 3.0, 0.0, 4.0, 0.6)
        self._screen_mode.add_option("Fullscreen")
        self._screen_mode.add_option("Windowed")
        
        w, h, fs = game.get_interface().get_window_settings()
        
        if h == 480: self._resolutions.set_option(0)
        elif h == 600: self._resolutions.set_option(1)
        elif h == 768: self._resolutions.set_option(2)
        elif h == 960: self._resolutions.set_option(3)
        elif h == 1200: self._resolutions.set_option(5)
        else:
             if h == 1024: self._resolutions.set_option(4)
        
        self._screen_mode.set_option(0 if fs else 1) 
        
        self._define_controls = TextButton(self, 0.0, -1.0, 0.6, "Set Controls")
        self._apply_button = TextButton(self, 0.0, -5.0, 0.7, "Apply")
        self._back_button = TextButton(self, 0.0, -6.0, 0.7, "Back")

    def update(self, time: float) -> int:
        self.update_background(time)
        
        self._resolutions.update()
        self._screen_mode.update()
        
        if self._define_controls.update():
            return GameState.CONTROLLERS_MENU
            
        if self._apply_button.update():
            fullscreen = (self._screen_mode.get_option() == 0)
            res_opt = self._resolutions.get_option()
            
            w, h = 640, 480
            if res_opt == 0: w, h = 640, 480
            elif res_opt == 1: w, h = 800, 600
            elif res_opt == 2: w, h = 1024, 768
            elif res_opt == 3: w, h = 1280, 960
            elif res_opt == 4: w, h = 1280, 1024
            elif res_opt == 5: w, h = 1600, 1200
            
            self._game.get_interface().change_window(w, h, fullscreen)
        
        if self._back_button.update():
            return GameState.MAIN_MENU
            
        return GameState.CURRENT_STATE
    
    def draw(self):
        self.draw_background()
        
        interface = self._game.get_interface()
        
        black_boxes = [
            [(-7.0, -3.0), (7.0, -3.0), (7.0, 3.0), (-7.0, 3.0)],
            [(-7.0, -6.6), (7.0, -6.6), (7.0, -4.4), (-7.0, -4.4)]
        ]
        
        for pts in black_boxes:
            screen_pts = [interface.game_to_screen(x, y) for x, y in pts]
            self._draw_transparent_poly(screen_pts, (0, 0, 0, 128))
            
        brown = (153, 76, 0, 128)
        brown_boxes = [
            [(-4.0, -5.4), (4.0, -5.4), (4.0, -4.6), (-4.0, -4.6)],
            [(-4.0, -6.4), (4.0, -6.4), (4.0, -5.6), (-4.0, -5.6)],
            [(-6.0, 0.6), (6.0, 0.6), (6.0, 1.4), (-6.0, 1.4)],
            [(-6.0, -0.4), (6.0, -0.4), (6.0, 0.4), (-6.0, 0.4)],
            [(-6.0, -1.4), (6.0, -1.4), (6.0, -0.6), (-6.0, -0.6)]
        ]
        
        for pts in brown_boxes:
             screen_pts = [interface.game_to_screen(x, y) for x, y in pts]
             self._draw_transparent_poly(screen_pts, brown)
             
        font = self._game.get_font()
        font.set_colour((1.0, 1.0, 1.0))
        font.set_size(0.6, 0.6, 0.5)
        font.print_centred_at(0.0, 6.5, "Options")
        
        font.set_colour((0.0, 1.0, 1.0))
        font.set_size(0.6, 0.6, 0.5)
        
        font.print_centred_at(-3.0, 0.7, "Resolution:")
        font.print_centred_at(-3.0, -0.3, "Screen Mode:")
        
        self._resolutions.draw()
        self._screen_mode.draw()
        
        self._define_controls.draw()
        self._apply_button.draw()
        self._back_button.draw()

    def _draw_transparent_poly(self, points, color):
        if not points: return
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w, h = max_x - min_x, max_y - min_y
        if w < 1 or h < 1: return
        
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        local_points = [(p[0] - min_x, p[1] - min_y) for p in points]
        pygame.draw.polygon(s, color, local_points)
        self._game.get_interface()._window.blit(s, (min_x, min_y))
