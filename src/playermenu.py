from typing import TYPE_CHECKING
from .menu import Menu
from .buttons import TextButton, GfxButton
from .selector import Selector
from .player import Player
from .common import GameState
import pygame

if TYPE_CHECKING:
    from .game import Game

class PlayerMenuEntry:
    def __init__(self):
        self.enabled = False
        self.name = ""
        self.colour = (255, 255, 255)
        self.add_button = None
        self.remove_button = None
        self.human_ai_selector = None
        self.controller = None

class PlayerMenu(Menu):
    def __init__(self, game: 'Game'):
        super().__init__(game)
        
        
        self._number_of_rounds = Selector(self, 2.0, -4.0, 2.0, 0.7)
        for r in ["5", "10", "15", "20", "25", "30", "35", "40", "45", "50"]:
            self._number_of_rounds.add_option(r)
            
        self._start_button = TextButton(self, 0.0, -5.0, 0.7, "Start!")
        self._back_button = TextButton(self, 0.0, -6.0, 0.7, "Back")
        
        self._players = [PlayerMenuEntry() for _ in range(8)]
        
        for i in range(8):
            self._players[i].add_button = GfxButton(self, -8.5, 3.5 - i * 0.8, 0.6, 10)
            self._players[i].remove_button = GfxButton(self, -7.8, 3.5 - i * 0.8, 0.6, 11)
            self._players[i].remove_button.enable(False)
            
            self._players[i].human_ai_selector = Selector(self, 1.6, 3.5 - i * 0.8, 3.0, 0.5)
            self._players[i].human_ai_selector.add_option("Human")
            self._players[i].human_ai_selector.add_option("Computer")
            self._players[i].human_ai_selector.enable(False)
            
            self._players[i].controller = Selector(self, 6.4, 3.5 - i * 0.8, 3.2, 0.5)
            self._players[i].controller.add_option("Keyboard1")
            self._players[i].controller.add_option("Keyboard2")
            for j in range(1, 9):
                self._players[i].controller.add_option(f"Joystick{j}")
                
            self._players[i].controller.enable(False)
            
        self._players_joined = 0
        self._start_button.enable(False)
        
        self._get_player_colours_and_names() # Call after initializing _players

    def _get_player_colours_and_names(self):
        settings = self._game.get_settings()
        for i in range(8):
            self._players[i].name = f"Player {i+1}"
            r = settings.get_float("Colours", f"Tank{i+1}red", 0.0)
            g = settings.get_float("Colours", f"Tank{i+1}green", 0.0)
            b = settings.get_float("Colours", f"Tank{i+1}blue", 0.0)
            self._players[i].colour = (int(r * 255), int(g * 255), int(b * 255))

    def update(self, time: float) -> int:
        self.update_background(time)
        
        self._number_of_rounds.update()
        
        if self._start_button.update():
            self._add_players()
            rounds = (1 + self._number_of_rounds.get_option()) * 5
            self._game.set_num_of_rounds(rounds)
            return GameState.ROUND_STARTING
            
        if self._back_button.update():
            return GameState.MAIN_MENU
            
        for i in range(8):
            p = self._players[i]
            
            if p.add_button.update():
                p.enabled = True
                p.add_button.enable(False)
                p.remove_button.enable(True)
                p.human_ai_selector.enable(True)
                
                if p.human_ai_selector.get_option() == 0:
                    p.controller.enable(True)
                    self._select_available_controller(i, 1)
                    
                self._players_joined += 1
                if self._players_joined > 1:
                    self._start_button.enable(True)
                    
            if p.remove_button.update():
                p.enabled = False
                p.add_button.enable(True)
                p.remove_button.enable(False)
                p.human_ai_selector.enable(False)
                p.controller.enable(False)
                
                self._players_joined -= 1
                if self._players_joined < 2:
                    self._start_button.enable(False)
                    
            if p.human_ai_selector.update():
                opt = p.human_ai_selector.get_option()
                if opt == 0:
                    p.controller.enable(True)
                    self._select_available_controller(i, 1)
                else:
                    p.controller.enable(False)
                    
            direction = p.controller.update()
            if direction != 0:
                self._select_available_controller(i, direction)
                
        controls = self._game.get_controls()
        for i in range(10):
             if controls.get_command(i, Player.CMD_FIRE):
                 found = False
                 for j in range(8):
                     if self._players[j].enabled and \
                        self._players[j].human_ai_selector.get_option() == 0 and \
                        self._players[j].controller.get_option() == i:
                        found = True
                        break
                 
                 if not found:
                     if self._players_joined < 8:
                         for j in range(8):
                             if not self._players[j].enabled:
                                 p = self._players[j]
                                 p.enabled = True
                                 p.add_button.enable(False)
                                 p.remove_button.enable(True)
                                 p.human_ai_selector.enable(True)
                                 p.human_ai_selector.set_option(0)
                                 p.controller.enable(True)
                                 p.controller.set_option(i)
                                 
                                 self._players_joined += 1
                                 if self._players_joined > 1:
                                     self._start_button.enable(True)
                                 break
                                 
        return GameState.CURRENT_STATE

    def _select_available_controller(self, player_idx, direction):
        controller_idx = self._players[player_idx].controller.get_option()
        
        while True:
            current_controller = controller_idx
            
            conflict = False
            for i in range(8):
                if i != player_idx and self._players[i].enabled and \
                   self._players[i].human_ai_selector.get_option() == 0 and \
                   self._players[i].controller.get_option() == current_controller:
                   
                   conflict = True
                   current_controller += direction
                   
                   if current_controller == -1: current_controller = 9
                   elif current_controller == 10: current_controller = 0
                   break
            
            if conflict:
                controller_idx = current_controller
            else:
                break
        
        self._players[player_idx].controller.set_option(controller_idx)

    def _add_players(self):
        for i in range(8):
            if self._players[i].enabled:
                ctrl = -1
                if self._players[i].human_ai_selector.get_option() == 0:
                    ctrl = self._players[i].controller.get_option()
                
                self._game.add_player(ctrl, self._players[i].name, self._players[i].colour)

    def draw(self):
        self.draw_background()
        
        font = self._game.get_font()
        font.set_shadow(True)
        font.set_size(0.6, 0.6, 0.5)
        font.set_colour((1.0, 1.0, 1.0))
        font.print_centred_at(0.0, 6.5, "Select Players")
        
        font.set_size(0.4, 0.4, 0.35)
        font.print_centred_at(0.0, 5.5, "Add a player by clicking on a '+' icon or press the 'Fire' Button on any Controller")
        
        interface = self._game.get_interface()
        
        poly_list = [
            ([(-7.0, -6.6), (7.0, -6.6), (7.0, -3.4), (-7.0, -3.4)], (0, 0, 0, 128)),
            ([(-4.0, -4.4), (4.0, -4.4), (4.0, -3.6), (-4.0, -3.6)], (153, 76, 0, 128)),
            ([(-4.0, -5.4), (4.0, -5.4), (4.0, -4.6), (-4.0, -4.6)], (153, 76, 0, 128)),
            ([(-4.0, -6.4), (4.0, -6.4), (4.0, -5.6), (-4.0, -5.6)], (153, 76, 0, 128)),
            ([(-9.0, -2.6), (9.0, -2.6), (9.0, 4.7), (-9.0, 4.7)], (0, 0, 0, 128))
        ]
        
        for pts, col in poly_list:
            sc_pts = [interface.game_to_screen(x,y) for x,y in pts]
            self._draw_transparent_poly(sc_pts, col)
            
        for i in range(8):
            if self._players[i].enabled:
                row_pts = [(-8.8, 3.2 - i*0.8), (8.8, 3.2 - i*0.8), (8.8, 3.8 - i*0.8), (-8.8, 3.8 - i*0.8)]
                self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in row_pts], (153, 76, 0, 128))
                
                c = self._players[i].colour
            else:
                c = self._players[i].colour
                c = (c[0]//4, c[1]//4, c[2]//4)
                
            t_pts = [
               (-7.0, 3.7 - i*0.8),
               (-6.6, 3.7 - i*0.8),
               (-6.4, 3.3 - i*0.8),
               (-7.2, 3.3 - i*0.8)
            ]
            
            sc_t_pts = [interface.game_to_screen(x,y) for x,y in t_pts]
            pygame.draw.polygon(interface._window, c, sc_t_pts)
            
        font.set_size(0.5, 0.5, 0.4)
        font.set_colour((1.0, 1.0, 1.0))
        for i in range(8):
            if self._players[i].enabled:
                 font.print_at(-6.0, 3.3 - i*0.8, self._players[i].name)
                 
        font.set_size(0.3, 0.3, 0.25)
        font.set_colour((0.0, 1.0, 1.0))
        font.print_centred_at(-8.0, 4.3, "Add/Remove")
        font.print_centred_at(-8.0, 4.0, "Player")
        font.print_centred_at(-4.0, 4.1, "Name")
        font.print_centred_at(1.6, 4.1, "Controlled by")
        font.print_centred_at(6.3, 4.1, "Controller")
        
        font.set_size(0.7, 0.7, 0.6)
        font.set_colour((1.0, 1.0, 1.0))
        font.print_centred_at(-2.0, -4.35, "Rounds :")
        font.set_shadow(False)
        
        for i in range(8):
            self._players[i].add_button.draw()
            self._players[i].remove_button.draw()
            self._players[i].human_ai_selector.draw()
            self._players[i].controller.draw()
            
        self._number_of_rounds.draw()
        self._start_button.draw()
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
