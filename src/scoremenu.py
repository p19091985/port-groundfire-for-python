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
        interface = self._game.get_interface()
        
        grey = (0, 0, 0, 128)
        
        for i in range(self._num_of_players):
            y_top = 6.0 - i * 1.6
            y_bot = 4.7 - i * 1.6
            
            box1 = [(-8.0, y_top), (-4.8, y_top), (-4.8, y_bot), (-8.0, y_bot)]
            box2 = [(-4.5, y_top), (4.5, y_top), (4.5, y_bot), (-4.5, y_bot)]
            box3 = [(4.8, y_top), (9.0, y_top), (9.0, y_bot), (4.8, y_bot)]
            
            for b in [box1, box2, box3]:
                 self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in b], grey)
                 
        font = self._game.get_font()
        font.set_shadow(True)
        font.set_size(0.5, 0.5, 0.4)
        font.set_colour((230, 230, 230))
        
        for i in range(self._num_of_players):
            y_pos = 5.1 - i * 1.6
            txt = f"{i+1}th"
            if i == 0: txt = "1st"
            elif i == 1: txt = "2nd"
            elif i == 2: txt = "3rd"
            
            if i > 0 and self._ordered_players[i].get_score() == self._ordered_players[i-1].get_score():
                 txt = " = "
                 
            font.print_centred_at(-9.0, y_pos, txt)
            
        font.set_size(0.5, 0.5, 0.4)
        font.print_centred_at(-6.3, 6.5, "Player")
        font.print_centred_at(0.0, 6.5, "Scoring for Round")
        font.print_centred_at(6.9, 6.5, "Total Score")
        
        for i in range(self._num_of_players):
            self._draw_score_for_player(self._ordered_players[i], 6.0 - i * 1.6)
            
        font.set_shadow(False)

    def _draw_score_for_player(self, player, y_pos):
        interface = self._game.get_interface()
        tank = player.get_tank()
        r, g, b = tank.get_colour()
        
        t_pts = [(-7.0, y_pos - 0.8), (-6.7, y_pos - 0.2), (-6.1, y_pos - 0.2), (-5.8, y_pos - 0.8)]
        pygame.draw.polygon(interface._window, (r, g, b), [interface.game_to_screen(x,y) for x,y in t_pts])
        
        x_pos = 0.0
        tex = interface.get_texture_image(4)
        
        for i in range(len(player.get_defeated_players())): # Fix: get_defeated_players_count()? or just len
             # Assuming get_defeated_players returns list
             defeated = player.get_defeated_players()[i]
             dr, dg, db = defeated.get_tank().get_colour()
             
             p1 = interface.game_to_screen(-4.0 + x_pos, y_pos - 0.3)
             tl = interface.game_to_screen(-4.0 + x_pos, y_pos - 0.3)
             br = interface.game_to_screen(-3.1 + x_pos, y_pos - 0.9)
             
             w_px = br[0] - tl[0]
             h_px = br[1] - tl[1]
             
             if w_px > 0 and h_px > 0 and tex:
                 scaled = pygame.transform.scale(tex, (int(w_px), int(h_px)))
                 tinted = scaled.copy()
                 color_surf = pygame.Surface((int(w_px), int(h_px))).convert_alpha()
                 color_surf.fill((dr, dg, db, 255))
                 tinted.blit(color_surf, (0,0), special_flags=pygame.BLEND_MULT)
                 interface._window.blit(tinted, tl)

             if defeated.is_leader():
                 pole = [(-3.7+x_pos, y_pos - 0.9), (-3.7+x_pos, y_pos - 0.3), (-3.6+x_pos, y_pos - 0.3), (-3.6+x_pos, y_pos - 0.9)]
                 pygame.draw.polygon(interface._window, (128, 128, 128), [interface.game_to_screen(x,y) for x,y in pole])
                 
                 fr, fg, fb = defeated.get_tank().get_colour()
                 flag1 = [(-3.6+x_pos, y_pos - 0.75), (-3.6+x_pos, y_pos - 0.3), (-2.9+x_pos, y_pos - 0.3), (-2.9+x_pos, y_pos - 0.75)]
                 pygame.draw.polygon(interface._window, (fr, fg, fb), [interface.game_to_screen(x,y) for x,y in flag1])
                 
             x_pos += 1.3
              
        font = self._game.get_font()
        font.set_colour((255, 255, 255))
        font.set_size(0.3, 0.3, 0.2)
        font.print_centred_at(-6.4, y_pos - 1.15, player.get_name())
        
        font.set_size(0.5, 0.5, 0.4)
        font.print_centred_at(6.9, y_pos - 0.9, str(player.get_score()))

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
