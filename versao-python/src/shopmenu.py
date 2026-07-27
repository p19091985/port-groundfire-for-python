from typing import TYPE_CHECKING
from .menu import Menu
from .player import Player
from .tank import Tank
from .common import GameState
import pygame

if TYPE_CHECKING:
    from .game import Game

class ShopMenu(Menu):
    def __init__(self, game: 'Game'):
        super().__init__(game)
        
        self._player_select_pos = [0] * 8
        self._player_select_delay = [0.4] * 8
        self._player_done = [False] * 8
        self._line_lit = [False] * 11
        
        settings = game.get_settings()
        self._jumpjets_cost = settings.get_int("Price", "Jumpjets", 50)
        
    def update(self, time: float) -> int:
        self.update_background(time)
        
        players = self._game.get_players()
        still_players_in_shop = False
        
        for i in range(8):
            if players[i] is not None and not self._player_done[i]:
                still_players_in_shop = True
                
                if self._player_select_delay[i] < 0.0:
                    players[i].update()
                    
                    if players[i].get_command(Player.CMD_GUNUP):
                        self._player_select_pos[i] -= 1
                        if self._player_select_pos[i] == -1: self._player_select_pos[i] = 10
                        self._player_select_delay[i] = 0.2
                        
                    elif players[i].get_command(Player.CMD_GUNDOWN):
                        self._player_select_pos[i] += 1
                        if self._player_select_pos[i] == 11: self._player_select_pos[i] = 0
                        self._player_select_delay[i] = 0.2
                        
                    elif players[i].get_command(Player.CMD_FIRE):
                         tank = players[i].get_tank()
                         pos = self._player_select_pos[i]
                         money = players[i].get_money()
                         
                         if pos == 0:
                             cost = tank.get_weapon(Tank.MACHINEGUN).get_cost()
                             if money >= cost:
                                 players[i].set_money(money - cost)
                                 tank.get_weapon(Tank.MACHINEGUN).add_amount(50)
                         elif pos == 1:
                             if money >= self._jumpjets_cost:
                                 players[i].set_money(money - self._jumpjets_cost)
                                 tank.set_total_fuel(tank.get_total_fuel() + 1.0)
                         elif pos == 2:
                             cost = tank.get_weapon(Tank.MIRVS).get_cost()
                             if money >= cost:
                                 players[i].set_money(money - cost)
                                 tank.get_weapon(Tank.MIRVS).add_amount(1)
                         elif pos == 3:
                             cost = tank.get_weapon(Tank.MISSILES).get_cost()
                             if money >= cost:
                                 players[i].set_money(money - cost)
                                 tank.get_weapon(Tank.MISSILES).add_amount(5)
                         elif pos == 4:
                             cost = tank.get_weapon(Tank.NUKES).get_cost()
                             if money >= cost:
                                 players[i].set_money(money - cost)
                                 tank.get_weapon(Tank.NUKES).add_amount(1)
                         elif pos == 10:
                             self._player_done[i] = True
                             
                         self._player_select_delay[i] = 0.2
                else:
                    self._player_select_delay[i] -= time
                    
                self._line_lit[self._player_select_pos[i]] = True
                
        if still_players_in_shop:
            return GameState.CURRENT_STATE
        else:
            return GameState.ROUND_STARTING

    def draw(self):
        self.draw_background()
        
        interface = self._game.get_interface()
        players = self._game.get_players()
        
        for i in range(8):
            if players[i] is not None and not self._player_done[i]:
                bar_col = (76, 25, 25, 128)
                polys = []
                if i % 2 == 0:
                     polys.append([(-9.4 + i*1.5, 5.6), (-9.4 + i*1.5, 4.9), (-6.6 + i*1.5, 4.9), (-6.6 + i*1.5, 5.6)])
                     polys.append([(-9.4 + i*1.5, -5.3), (-9.4 + i*1.5, 4.9), (-8.1 + i*1.5, 4.9), (-8.1 + i*1.5, -5.3)])
                else:
                    polys.append([(-10.9 + i*1.5, -5.5), (-10.9 + i*1.5, -6.2), (-8.1 + i*1.5, -6.2), (-8.1 + i*1.5, -5.5)])
                    polys.append([(-9.4 + i*1.5, -5.5), (-9.4 + i*1.5, 4.7), (-8.1 + i*1.5, 4.7), (-8.1 + i*1.5, -5.5)])
                    
                for pts in polys:
                    self.draw_game_polygon(pts, bar_col)
                    
                pos = self._player_select_pos[i]
                if self._line_lit[pos]:
                     v = pos * 0.8
                     high_col = (255, 255, 255, 25)
                     h_pts = [(-9.4, 3.8 - v), (-9.4, 4.6 - v), (9.4, 4.6 - v), (9.4, 3.8 - v)]
                     self.draw_game_polygon(h_pts, high_col)
                     self._line_lit[pos] = False

        for i in range(8):
            if players[i] is not None and not self._player_done[i]:
                 tank = players[i].get_tank()
                 c = tank.get_colour()
                 v = self._player_select_pos[i] * 0.8
                 t_pts = [(-9.35 + i*1.5, 3.9 - v), (-9.05 + i*1.5, 4.5 - v), (-8.45 + i*1.5, 4.5 - v), (-8.15 + i*1.5, 3.9 - v)]
                 self.draw_game_polygon(t_pts, c)
                 
                 pos = self._player_select_pos[i]
                 cx = -9.4 + i*1.5
                 cy = 3.7 - v

                 if pos == 0: self._draw_bars(cx, cy, tank.get_weapon(Tank.MACHINEGUN).get_ammo() / 50.0)
                 elif pos == 1: self._draw_bars(cx, cy, tank.get_total_fuel())
                 elif pos == 2: self._ui.draw_centered_text(cx + 0.65, cy - 0.2, f"x{tank.get_weapon(Tank.MIRVS).get_ammo()}", style=self._ui.style(0.3, (255, 255, 255), spacing=0.25))
                 elif pos == 3: self._ui.draw_centered_text(cx + 0.65, cy - 0.2, f"x{tank.get_weapon(Tank.MISSILES).get_ammo()}", style=self._ui.style(0.3, (255, 255, 255), spacing=0.25))
                 elif pos == 4: self._ui.draw_centered_text(cx + 0.65, cy - 0.2, f"x{tank.get_weapon(Tank.NUKES).get_ammo()}", style=self._ui.style(0.3, (255, 255, 255), spacing=0.25))

        self._ui.draw_centered_text(
            0.0,
            6.5,
            f"Round {self._game.get_current_round() + 1} of {self._game.get_num_of_rounds()}",
            style=self._ui.style(0.6, (255, 255, 255), shadow=True),
        )
        
        ref_tank = None
        for p in players:
             if p: 
                 ref_tank = p.get_tank()
                 break
        
        if ref_tank:
            nuke_cost = ref_tank.get_weapon(Tank.NUKES).get_cost()
            missile_cost = ref_tank.get_weapon(Tank.MISSILES).get_cost()
            mirv_cost = ref_tank.get_weapon(Tank.MIRVS).get_cost()
            mg_cost = ref_tank.get_weapon(Tank.MACHINEGUN).get_cost()
        else:
            nuke_cost = 0; missile_cost = 0; mirv_cost = 0; mg_cost = 0

        bright_style = self._ui.style(0.4, (230, 230, 230), spacing=0.3, shadow=True)
        self._ui.draw_centered_text(4.0, 5.0, "Cost", style=bright_style)
        self._ui.draw_centered_text(7.0, 5.0, "Item", style=bright_style)
        
        items = [("Machine Gun", mg_cost), ("Jump Jet", self._jumpjets_cost), ("Mirvs", mirv_cost), ("Missiles", missile_cost), ("Nukes", nuke_cost)]
        y = 4.0
        for name, cost in items:
            self._ui.draw_centered_text(7.0, y, name, style=bright_style)
            self._ui.draw_centered_text(4.0, y, f"${cost}", style=bright_style)
            y -= 0.8
            
        muted_style = self._ui.style(0.4, (76, 76, 76), spacing=0.3, shadow=True)
        gray_items = [("Rolling Mines", 50), ("Airstrike", 100), ("Death's Head", 200), ("Hover Coil", 150), ("Corbomite", 20)]
        for name, cost in gray_items:
             self._ui.draw_centered_text(7.0, y, name, style=muted_style)
             self._ui.draw_centered_text(4.0, y, f"${cost}", style=muted_style)
             y -= 0.8
             
        self._ui.draw_centered_text(7.0, -4.0, "Done!", style=bright_style)

        money_style = self._ui.style(0.35, (230, 230, 230), spacing=0.275, shadow=True)
        for i in range(8):
             if players[i] is not None and not self._player_done[i]:
                 if i % 2 == 0:
                     self._ui.draw_centered_text(-8.0 + i*1.5, 5.1, f"${players[i].get_money()}", style=money_style)
                 else:
                     self._ui.draw_centered_text(-9.5 + i*1.5, -6.0, f"${players[i].get_money()}", style=money_style)

    def _draw_bars(self, x: float, y: float, num_bars: float):
        interface = self._game.get_interface()
        col = (255, 255, 255)
        i = 0
        while num_bars > 0.0:
            length = 1.3 if num_bars > 1.0 else 1.3 * num_bars
            num_bars -= 1.0
            pts = [(x, y - 0.2*i + 0.15), (x, y - 0.2*i), (x + length, y - 0.2*i), (x + length, y - 0.2*i + 0.15)]
            self.draw_game_polygon(pts, col)
            i += 1
