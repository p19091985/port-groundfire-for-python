from typing import TYPE_CHECKING
from .menu import Menu
from .buttons import TextButton
from .common import GameState
import pygame

if TYPE_CHECKING:
    from .game import Game

class MainMenu(Menu):
    def __init__(self, game: 'Game'):
        super().__init__(game)
        
        self._start_button = TextButton(self, 0.0, -4.0, 0.7, "Start Game")
        self._options_button = TextButton(self, 0.0, -5.0, 0.7, "Options")
        self._quit_button = TextButton(self, 0.0, -6.0, 0.7, "Quit")

    def update(self, time: float) -> int:
        self.update_background(time)
        
        if self._start_button.update():
            return GameState.SELECT_PLAYERS_MENU
        
        if self._options_button.update():
            return GameState.OPTION_MENU
            
        if self._quit_button.update():
            return GameState.QUIT_MENU
            
        return GameState.CURRENT_STATE

    def draw(self):
        self.draw_background()
        
        interface = self._game.get_interface()
        logo_tex = interface.get_texture_image(9)
        
        if logo_tex:
            p1 = interface.game_to_screen(-8.0, 4.0)
            p2 = interface.game_to_screen(8.0, 0.0)
            
            w = p2[0] - p1[0]
            h = p2[1] - p1[1]
            
            if w > 0 and h > 0:
                scaled_logo = pygame.transform.scale(logo_tex, (int(w), int(h)))
                interface._window.blit(scaled_logo, p1)
        
        box_pts = [
            (-7.0, -6.6),
            ( 7.0, -6.6),
            ( 7.0, -3.4),
            (-7.0, -3.4)
        ]
        screen_box = [interface.game_to_screen(x, y) for x, y in box_pts]
        self._draw_transparent_poly(screen_box, (0, 0, 0, 128))
        
        btn_bg_color = (153, 76, 0, 255)
        
        b1_pts = [(-4.0, -4.4), (4.0, -4.4), (4.0, -3.6), (-4.0, -3.6)]
        self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in b1_pts], btn_bg_color)
        
        b2_pts = [(-4.0, -5.4), (4.0, -5.4), (4.0, -4.6), (-4.0, -4.6)]
        self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in b2_pts], btn_bg_color)
        
        b3_pts = [(-4.0, -6.4), (4.0, -6.4), (4.0, -5.6), (-4.0, -5.6)]
        self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in b3_pts], btn_bg_color)
        
        font = self._game.get_font()
        font.set_size(0.4, 0.4, 0.35)
        font.set_colour((1.0, 1.0, 1.0))
        font.set_shadow(True)
        
        version_str = "0.25 (Python Port)"
        font.print_centred_at(0.0, 0.0, version_str)
        font.print_centred_at(0.0, -0.5, "www.groundfire.net")
        font.print_centred_at(0.0, -2.5, "Copyright Tom Russell 2004")
        font.print_centred_at(0.0, -2.9, "All Rights Reserved")
        font.set_shadow(False)
        
        self._start_button.draw()
        self._options_button.draw()
        self._quit_button.draw()

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
