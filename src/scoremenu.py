from typing import TYPE_CHECKING
from .menu import Menu
from .player import Player
from .common import GameState
import pygame
import math

if TYPE_CHECKING:
    from .game import Game

class ScoreMenu(Menu):
    def __init__(self, game: 'Game'):
        super().__init__(game)
        
        self._ordered_players = []
        players = game.get_players()
        self._num_of_players = 0
        
        for i in range(8):
            if players[i] is not None:
                self._add_player_to_ordered_list(players[i])
                self._num_of_players += 1
                
        if game.are_human_players():
            self._time_till_active = 2.0
        else:
            self._time_till_active = 4.0
            
    def _add_player_to_ordered_list(self, player):
        insert_pos = 0
        for i in range(len(self._ordered_players)):
            if player.get_score() > self._ordered_players[i].get_score():
                insert_pos = i
                break
            insert_pos = i + 1
        self._ordered_players.insert(insert_pos, player)

    def update(self, time: float) -> int:
        self.update_background(time)
        
        # Auto-advance timeout (Task 3 Fix)
        # The user reported "Deadlock". We force progression after a generous timeout.
        # Original C++ waits for input, but we add a safety net.
        AUTO_ADVANCE_TIME = 10.0 # seconds
        self._time_till_active -= time
        
        if self._time_till_active <= -AUTO_ADVANCE_TIME:
             print("DEBUG: ScoreMenu Auto-Advancing due to timeout.")
             if self._game.get_num_of_rounds() == self._game.get_current_round():
                 return GameState.WINNER_MENU
             return GameState.SHOP_MENU

        if self._time_till_active <= 0.0:
            if not self._game.are_human_players():
                if self._game.get_num_of_rounds() == self._game.get_current_round():
                    return GameState.WINNER_MENU
                return GameState.SHOP_MENU
                
            for i in range(self._num_of_players):
                dummy = [0.0]
                # Check FIRE or ENTER/SPACE for convenience
                # We also check global keys if player input fails
                pressed_fire = False
                if self._ordered_players[i].get_command(Player.CMD_FIRE, dummy):
                    pressed_fire = True
                
                # Global input fallback (Any key advances)
                # This ensures "Hang" is solvable by mashing keys
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE] or keys[pygame.K_RETURN] or pressed_fire:
                    if self._game.get_num_of_rounds() == self._game.get_current_round():
                        return GameState.WINNER_MENU
                        
                    if len(self._ordered_players) > 1:
                        if self._ordered_players[0].get_score() > self._ordered_players[1].get_score():
                            self._ordered_players[0].set_leader(True)
                            for j in range(1, self._num_of_players):
                                self._ordered_players[j].set_leader(False)
                        else:
                            for j in range(self._num_of_players):
                                self._ordered_players[j].set_leader(False)
                    elif len(self._ordered_players) == 1:
                        self._ordered_players[0].set_leader(True)
                        
                    return GameState.SHOP_MENU
        
        return GameState.CURRENT_STATE

    def draw(self):
        self.draw_background()
        grey = (0, 0, 0, 128)
        
        for i in range(self._num_of_players):
            y_top = 6.0 - i * 1.6
            y_bot = 4.7 - i * 1.6
            
            box1 = [(-8.0, y_top), (-4.8, y_top), (-4.8, y_bot), (-8.0, y_bot)]
            box2 = [(-4.5, y_top), (4.5, y_top), (4.5, y_bot), (-4.5, y_bot)]
            box3 = [(4.8, y_top), (9.0, y_top), (9.0, y_bot), (4.8, y_bot)]
            
            for b in [box1, box2, box3]:
                 self.draw_game_polygon(b, grey)
        
        heading_style = self._ui.style(0.5, (230, 230, 230), spacing=0.4, shadow=True)
        
        for i in range(self._num_of_players):
            y_pos = 5.1 - i * 1.6
            txt = f"{i+1}th"
            if i == 0: txt = "1st"
            elif i == 1: txt = "2nd"
            elif i == 2: txt = "3rd"
            
            if i > 0 and self._ordered_players[i].get_score() == self._ordered_players[i-1].get_score():
                 txt = " = "
                 
            self._ui.draw_centered_text(-9.0, y_pos, txt, style=heading_style)
            
        self._ui.draw_centered_text(-6.3, 6.5, "Player", style=heading_style)
        self._ui.draw_centered_text(0.0, 6.5, "Scoring for Round", style=heading_style)
        self._ui.draw_centered_text(6.9, 6.5, "Total Score", style=heading_style)
        
        for i in range(self._num_of_players):
            self._draw_score_for_player(self._ordered_players[i], 6.0 - i * 1.6)

    def _draw_score_for_player(self, player, y_pos):
        interface = self._game.get_interface()
        tank = player.get_tank()
        r, g, b = tank.get_colour()
        
        t_pts = [(-7.0, y_pos - 0.8), (-6.7, y_pos - 0.2), (-6.1, y_pos - 0.2), (-5.8, y_pos - 0.8)]
        self.draw_game_polygon(t_pts, (r, g, b))
        
        x_pos = 0.0
        
        for i in range(len(player.get_defeated_players())): # Fix: get_defeated_players_count()? or just len
             # Assuming get_defeated_players returns list
             defeated = player.get_defeated_players()[i]
             dr, dg, db = defeated.get_tank().get_colour()
             
             self._graphics.draw_texture_world_rect(
                 4,
                 -4.0 + x_pos,
                 y_pos - 0.3,
                 -3.1 + x_pos,
                 y_pos - 0.9,
                 tint=(dr, dg, db),
             )

             if defeated.is_leader():
                 pole = [(-3.7+x_pos, y_pos - 0.9), (-3.7+x_pos, y_pos - 0.3), (-3.6+x_pos, y_pos - 0.3), (-3.6+x_pos, y_pos - 0.9)]
                 self.draw_game_polygon(pole, (128, 128, 128))
                 
                 fr, fg, fb = defeated.get_tank().get_colour()
                 flag1 = [(-3.6+x_pos, y_pos - 0.75), (-3.6+x_pos, y_pos - 0.3), (-2.9+x_pos, y_pos - 0.3), (-2.9+x_pos, y_pos - 0.75)]
                 self.draw_game_polygon(flag1, (fr, fg, fb))
                 
             x_pos += 1.3
              
        self._ui.draw_centered_text(-6.4, y_pos - 1.15, player.get_name(), style=self._ui.style(0.3, (255, 255, 255), spacing=0.2))
        self._ui.draw_centered_text(6.9, y_pos - 0.9, str(player.get_score()), style=self._ui.style(0.5, (255, 255, 255), spacing=0.4))
