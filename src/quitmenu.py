from typing import TYPE_CHECKING
from .menu import Menu
from .buttons import TextButton
from .common import GameState
import pygame

if TYPE_CHECKING:
    from .game import Game

class QuitMenu(Menu):
    def __init__(self, game: 'Game'):
        super().__init__(game)
        
        self._yes = TextButton(self, 0.0, -5.0, 0.7, "Yes")
        self._no = TextButton(self, 0.0, -6.0, 0.7, "No")

    def update(self, time: float) -> int:
        self.update_background(time)
        
        if self._yes.update():
            return GameState.EXITED
            
        if self._no.update():
            return GameState.MAIN_MENU
            
        return GameState.CURRENT_STATE

    def draw(self):
        self.draw_background()
        interface = self._game.get_interface()
        
        logo = interface.get_texture_image(9)
        if logo:
            p1 = interface.game_to_screen(-8.0, 4.0)
            p2 = interface.game_to_screen(8.0, 0.0)
            w, h = p2[0] - p1[0], p2[1] - p1[1]
            if w > 0 and h > 0:
                s = pygame.transform.scale(logo, (int(w), int(h)))
                interface._window.blit(s, p1)
                
        black_pts = [(-7.0, -6.6), (7.0, -6.6), (7.0, -3.4), (-7.0, -3.4)]
        self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in black_pts], (0, 0, 0, 128))
        
        brown_pts1 = [(-4.0, -5.4), (4.0, -5.4), (4.0, -4.6), (-4.0, -4.6)]
        brown_pts2 = [(-4.0, -6.4), (4.0, -6.4), (4.0, -5.6), (-4.0, -5.6)]
        
        self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in brown_pts1], (153, 76, 0, 128))
        self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in brown_pts2], (153, 76, 0, 128))
        
        font = self._game.get_font()
        font.set_size(0.7, 0.7, 0.6)
        font.set_colour((1.0, 1.0, 1.0))
        font.print_centred_at(0.0, -4.35, "Are you sure?")
        
        self._yes.draw()
        self._no.draw()

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
