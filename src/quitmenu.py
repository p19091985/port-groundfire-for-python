from typing import TYPE_CHECKING
from .menu import Menu
from .buttons import TextButton
from .common import GameState

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
        self.draw_texture_rect(9, -8.0, 4.0, 8.0, 0.0)
        self.draw_game_polygon([(-7.0, -6.6), (7.0, -6.6), (7.0, -3.4), (-7.0, -3.4)], (0, 0, 0, 128))
        self.draw_game_polygon([(-4.0, -5.4), (4.0, -5.4), (4.0, -4.6), (-4.0, -4.6)], (153, 76, 0, 128))
        self.draw_game_polygon([(-4.0, -6.4), (4.0, -6.4), (4.0, -5.6), (-4.0, -5.6)], (153, 76, 0, 128))
        self._ui.draw_centered_text(0.0, -4.35, "Are you sure?", style=self._ui.style(0.7, (1.0, 1.0, 1.0), spacing=0.6, shadow=True))
        
        self._yes.draw()
        self._no.draw()
