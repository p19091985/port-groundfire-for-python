from typing import TYPE_CHECKING
from .menu import Menu
from .player import Player
from .common import PI, GameState
import pygame
import math

if TYPE_CHECKING:
    from .game import Game

class WinnerMenu(Menu):
    def __init__(self, game: 'Game'):
        super().__init__(game)
        
        self._winners = []
        self._is_draw = False
        highest_score = -1
        
        players = game.get_players()
        for i in range(game.get_num_of_players()):
            if players[i]:
                if players[i].get_score() > highest_score:
                    highest_score = players[i].get_score()
                    self._winners = [players[i]]
                    self._is_draw = False
                elif players[i].get_score() == highest_score:
                    self._is_draw = True
                    self._winners.append(players[i])
                    
        self._spinning = 0.0
        
        if game.are_human_players():
            self._time_till_active = 2.0
        else:
            self._time_till_active = 4.0

    def update(self, time: float) -> int:
        self.update_background(time)
        
        if self._time_till_active <= 0.0:
            if not self._game.are_human_players():
                self._game.delete_players()
                return GameState.MAIN_MENU
                
            players = self._game.get_players()
            for i in range(self._game.get_num_of_players()):
                if players[i] and players[i].get_command(Player.CMD_FIRE):
                    self._game.delete_players()
                    return GameState.MAIN_MENU
        else:
            self._time_till_active -= time
            
        self._spinning -= time * 4.0
        return GameState.CURRENT_STATE
        
    def draw(self):
        self.draw_background()
        title_style = self._ui.style(0.6, (1.0, 1.0, 1.0), shadow=True)
        self._ui.draw_centered_text(0.0, 6.5, "Final Result", style=title_style)

        if self._is_draw:
            self._ui.draw_centered_text(0.0, 5.5, "It's a tie!", style=title_style)
        else:
            self._ui.draw_centered_text(0.0, 5.5, "We have a winner!", style=title_style)
            
        num_winners = len(self._winners)
        
        row = 0
        col = 0
        
        cols_count = (num_winners - 1) // 4
        
        w_in_row = num_winners if num_winners < 5 else 4
        col_start = -((w_in_row - 1) * 2.0)
        
        interface = self._game.get_interface()
        
        for i in range(num_winners):
            tank = self._winners[i].get_tank()
            r, g, b = tank.get_colour()
            
            x = col_start + row * 4.0
            y = (cols_count * 2.0) - col * 4.0
            
            t_pts = [(x - 1.5, y - 0.75), (x - 0.75, y + 0.75), (x + 0.75, y + 0.75), (x + 1.5, y - 0.75)]
            self.draw_game_polygon(t_pts, (r, g, b))
            
            self._ui.draw_centered_text(x, y - 1.2, self._winners[i].get_name(), style=self._ui.style(0.4, (1.0, 1.0, 1.0), spacing=0.35, shadow=True))
            
            txt = "Winner!"
            base_angle = self._spinning
            for char_idx, char in enumerate(txt):
                angle = base_angle - (char_idx * 0.2)
                self._draw_spinning_letter(x, y - 0.4, angle, char)
            
            row += 1
            if row > 3:
                row = 0
                col += 1
                rem = num_winners - (col * 4)
                w_in_row = rem if rem < 5 else 4
                col_start = -((w_in_row - 1) * 2.0)

    def _draw_spinning_letter(self, cx, cy, angle, char):
        deg = (angle / PI) * 180.0 - 90.0
        px = cx + math.cos(angle) * 1.8
        py = cy + math.sin(angle) * 1.8
        self._ui.draw_text(px, py, char, style=self._ui.style(0.6, (1.0, 1.0, 1.0), shadow=True, proportional=False, orientation=deg))
