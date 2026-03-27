from typing import TYPE_CHECKING
from .menu import Menu
from .buttons import TextButton
from .common import GameState

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
        self.draw_texture_rect(9, -8.0, 4.0, 8.0, 0.0)
        self.draw_game_polygon([(-7.0, -6.6), (7.0, -6.6), (7.0, -3.4), (-7.0, -3.4)], (0, 0, 0, 128))

        btn_bg_color = (153, 76, 0, 255)
        self.draw_game_polygon([(-4.0, -4.4), (4.0, -4.4), (4.0, -3.6), (-4.0, -3.6)], btn_bg_color)
        self.draw_game_polygon([(-4.0, -5.4), (4.0, -5.4), (4.0, -4.6), (-4.0, -4.6)], btn_bg_color)
        self.draw_game_polygon([(-4.0, -6.4), (4.0, -6.4), (4.0, -5.6), (-4.0, -5.6)], btn_bg_color)

        text_style = self._ui.style(0.4, (1.0, 1.0, 1.0), spacing=0.35, shadow=True)
        self._ui.draw_centered_text(0.0, 0.0, "0.25 (Python Port)", style=text_style)
        self._ui.draw_centered_text(0.0, -0.5, "www.groundfire.net", style=text_style)
        self._ui.draw_centered_text(0.0, -2.5, "Copyright Tom Russell 2004", style=text_style)
        self._ui.draw_centered_text(0.0, -2.9, "All Rights Reserved", style=text_style)
        
        self._start_button.draw()
        self._options_button.draw()
        self._quit_button.draw()
