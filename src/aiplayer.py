from .player import Player
from .tank import Tank
from .common import deg_sin, deg_cos, sqr, PI
import math
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .game import Game

class AIPlayer(Player):
    def __init__(self, game: 'Game', number: int, name: str, colour: tuple):
        super().__init__(game, number, name, colour)
        self._commands = [False] * 11
        
        self._target_tank: Optional[Tank] = None
        self._target_angle = 0.0
        self._target_last_x_pos = 0.0
        self._target_last_y_pos = 0.0
        self._target_power = 0.0
        
        self._shots_in_air = 0
        self._last_shot_x = 0.0
        self._last_shot_y = 0.0
        self._last_shot = False
        self._ignore_shot = False
        self._on_target = False
        self._aim_directly = False

    def is_computer(self) -> bool: return True

    def new_round(self):
        super().new_round()
        self._target_tank = None
        self._target_angle = 0.0
        self._target_power = 0.0
        
        self._on_target = False
        self._ignore_shot = False
        self._shots_in_air = 0
        self._last_shot = False

    def update(self, time: float = 0.0):
        # Clear commands BEFORE updating tank (avoids double-processing)
        for i in range(11):
            self._commands[i] = False

        state = self._game.get_game_state()
        
        if state == self._game.GameState.ROUND_IN_ACTION:
             self.compute_action()
        elif state == self._game.GameState.SHOP_MENU:
             # Placeholder for when ShopMenu is implemented
             current_menu = self._game.get_current_menu()
             if current_menu:
                 # Duck typing
                 if hasattr(current_menu, 'player_select_pos'):
                     if current_menu.player_select_pos[self._number] != 10:
                         self._commands[Player.CMD_GUNUP] = True
                     else:
                         self._commands[Player.CMD_FIRE] = True

        # C++ AIPlayer::update() does NOT call tank.update() — tank calls us, not reverse

    def get_command(self, command: int, start_time_ref=None) -> bool:
        if start_time_ref is not None and isinstance(start_time_ref, list) and len(start_time_ref) > 0:
            start_time_ref[0] = 0.0
        return self._commands[command]

    def record_fired(self):
        self._shots_in_air += 1

    def record_shot(self, x: float, y: float, hit_tank: int):
        self._shots_in_air -= 1
        
        players = self._game.get_players()
        
        # If we hit a tank and it's alive (requires players list access)
        hit_player = None
        if 0 <= hit_tank < len(players):
             hit_player = players[hit_tank]
        
        if hit_player and hit_player.get_tank().alive():
            if hit_tank == self._number:
                # Hit self
                self._target_tank = None
            elif not self._target_tank or hit_tank != self._target_tank.get_player()._number:
                # Hit wrong tank, switch target
                self._target_tank = hit_player.get_tank()
                self._target_last_x_pos = self._target_tank._x
                self._target_last_y_pos = self._target_tank._y
                self._on_target = True
            else:
                # Bullseye
                self._on_target = True
        else:
            if self._aim_directly:
                 self._aim_directly = False
                 self.guess_aim()
                 self._last_shot = False
            else:
                 if not self._ignore_shot:
                     if self._target_tank:
                         prev_x_dist = self._last_shot_x - self._target_tank._x
                         curr_x_dist = x - self._target_tank._x
                         
                         if self._last_shot and (
                             (curr_x_dist < 0.0 and prev_x_dist < 0.0 and curr_x_dist < prev_x_dist) or
                             (curr_x_dist > 0.0 and prev_x_dist > 0.0 and curr_x_dist > prev_x_dist)
                         ):
                             # Getting worse
                             self._target_angle /= 2.0
                             self._target_power += 2.0
                             if self._target_power > self._tank._gun_power_max:
                                 self._target_power = self._tank._gun_power_max
                             self._last_shot = False
                         else:
                             # Adjusting
                             if curr_x_dist < 0.0:
                                 self._target_angle += abs(deg_sin(self._target_angle)) * curr_x_dist * 4.0
                                 if self._target_angle < -self._tank._gun_angle_max:
                                     self._target_angle = -self._tank._gun_angle_max
                                     
                                 if self._target_tank._x < self._tank._x:
                                     self._target_power -= -curr_x_dist * 1.2 * (1 - deg_sin(abs(self._target_angle)))
                                 else:
                                     self._target_power += -curr_x_dist * 1.2 * (1 - deg_sin(abs(self._target_angle)))
                             else:
                                 # Landed right
                                 self._target_angle += abs(deg_sin(self._target_angle)) * curr_x_dist * 4.0
                                 if self._target_angle > self._tank._gun_angle_max:
                                     self._target_angle = self._tank._gun_angle_max
                                     
                                 if self._target_tank._x < self._tank._x:
                                     self._target_power += curr_x_dist * 1.2 * (1 - deg_sin(abs(self._target_angle)))
                                 else:
                                     self._target_power -= curr_x_dist * 1.2 * (1 - deg_sin(abs(self._target_angle)))
                                     
                             if self._target_power < self._tank._gun_power_min:
                                 self._target_power = self._tank._gun_power_min
                             elif self._target_power > self._tank._gun_power_max:
                                 self._target_power = self._tank._gun_power_max
                                 
                             self._last_shot = True
                         
                         self._on_target = False
                     else:
                          pass
                 else:
                     self._ignore_shot = False
                     
        self._last_shot_x = x
        self._last_shot_y = y

    def compute_action(self):
        if not self._target_tank:
            self.find_new_target()
            self.guess_aim()
        else:
            if self._target_tank._state == Tank.TANK_ALIVE:
                # Check if moved
                if (sqr(self._target_tank._x - self._target_last_x_pos) + 
                    sqr(self._target_tank._y - self._target_last_y_pos) > 4.0):
                    self._target_tank = None 
                else:
                    ready_to_fire = True
                    
                    angle_diff = self._tank._gun_angle - self._target_angle
                    if angle_diff > 1.0:
                        self._commands[Player.CMD_GUNRIGHT] = True
                        ready_to_fire = False
                    elif angle_diff < -1.0:
                        self._commands[Player.CMD_GUNLEFT] = True
                        ready_to_fire = False
                        
                    power_diff = self._tank._gun_power - self._target_power
                    if power_diff > 0.2:
                        self._commands[Player.CMD_GUNDOWN] = True
                        ready_to_fire = False
                    elif power_diff < -0.2:
                         self._commands[Player.CMD_GUNUP] = True
                         ready_to_fire = False
                         
                    if ready_to_fire and self._tank.ready_to_fire():
                        if self._aim_directly:
                             if (sqr(self._target_tank._x - self._target_last_x_pos) +
                                 sqr(self._target_tank._y - self._target_last_y_pos) > 0.04):
                                     ready_to_fire = False
                                     self.guess_aim()
                        
                        if ready_to_fire and self._shots_in_air == 0:
                            self._commands[Player.CMD_FIRE] = True
            else:
                self._target_tank = None
            
            if not self._target_tank:
                if self._shots_in_air > 0:
                    self._ignore_shot = True
                self._last_shot = False

    def guess_aim(self):
        if not self._target_tank: return

        x_diff = self._target_tank._x - self._tank._x
        
        if self._aim_directly:
            y_diff = self._target_tank._y - self._tank._y
            if y_diff > 0.2:
                 self._target_angle = -(math.atan(x_diff / y_diff) / PI) * 180.0
                 self._target_power = self._tank._gun_power_max
                 
                 if self._target_angle > self._tank._gun_angle_max or self._target_angle < -self._tank._gun_angle_max:
                     self._aim_directly = False
            else:
                self._aim_directly = False
        
        self._target_last_x_pos = self._target_tank._x
        self._target_last_y_pos = self._target_tank._y
        
        if not self._aim_directly:
            self._target_angle = -x_diff * 3.0
            self._target_power = 10.0
            
        if self._target_angle > self._tank._gun_angle_max: self._target_angle = self._tank._gun_angle_max
        if self._target_angle < -self._tank._gun_angle_max: self._target_angle = -self._tank._gun_angle_max

    def find_new_target(self):
        players = self._game.get_players()
        top_score = 0
        self._aim_directly = False
        
        for p in players:
            if not p: continue
            score = 0
            if p != self and p.get_tank()._state == Tank.TANK_ALIVE:
                enemy_tank = p.get_tank()
                
                sx, sy = self._tank.gun_launch_position()
                ex, ey, _ = enemy_tank.get_centre()
                
                landscape = self._game.get_landscape()
                if landscape:
                    coll = landscape.ground_collision(sx, sy, ex, ey)
                    if not coll[0]:
                        # LOS
                        score += 100
                        if enemy_tank._y > self._tank._y:
                            score += 50
                            self._aim_directly = True
                            
                score += 40 - int(2.0 * abs(enemy_tank._x - self._tank._x))
                
                if score >= top_score:
                    top_score = score
                    self._target_tank = enemy_tank
