from .entity import Entity
from .common import PI, deg_sin, deg_cos
from .soundentity import SoundEntity
from .smoke import Smoke
from .weapons_impl import ShellWeapon, MachineGunWeapon, MirvWeapon, MissileWeapon, NukeWeapon
from .inifile import ReadIniFile
import math
import pygame

class Tank(Entity):
    # Enums
    TANK_ALIVE = 0
    TANK_DEAD = 1
    TANK_RESIGNED = 2

    SHELLS = 0
    MACHINEGUN = 1
    MIRVS = 2
    MISSILES = 3
    NUKES = 4
    MAX_WEAPONS = 5

    CMD_TANKLEFT = 5
    CMD_TANKRIGHT = 6
    CMD_JUMPJETS = 3
    CMD_WEAPONUP = 1
    CMD_WEAPONDOWN = 2
    CMD_FIRE = 0
    CMD_GUNLEFT = 7
    CMD_GUNRIGHT = 8
    CMD_GUNUP = 9
    CMD_GUNDOWN = 10

    def __init__(self, game, owner, stats_position):
        super().__init__(game)
        self._player = owner
        self._stats_position = stats_position
        
        settings = game.get_settings()
        
        self._gun_angle_max = settings.get_float("Tank", "MaxGunAngle", 75.0)
        self._gun_angle_max_change_speed = settings.get_float("Tank", "MaxGunAngleChangeSpeed", 75.0)
        self._gun_angle_change_acceleration = settings.get_float("Tank", "GunAngleChangeAcceleration", 60.0)
        self._gun_power_max = settings.get_float("Tank", "GunPowerMax", 20.0)
        self._gun_power_min = settings.get_float("Tank", "GunPowerMin", 1.0)
        self._gun_power_max_change_speed = settings.get_float("Tank", "GunPowerMaxChangeSpeed", 50.0)
        self._gun_power_change_acceleration = settings.get_float("Tank", "GunPowerChangeAcceleration", 20.0)
        
        self._movement_speed = settings.get_float("Tank", "MoveSpeed", 0.2)
        self._tank_size = settings.get_float("Tank", "Size", 0.25)
        self._tank_gravity = settings.get_float("Tank", "Gravity", 5.0)
        self._tank_boost = settings.get_float("Tank", "Boost", 7.0)
        
        self._ground_smoke_release_time = settings.get_float("Tank", "GroundSmokeReleaseTime", 1.0)
        self._air_smoke_release_time = settings.get_float("Tank", "AirSmokeReleaseTime", 0.05)
        self._fuel_usage_rate = settings.get_float("Tank", "FuelUsageRate", 0.2)
        
        self._weapons = [None] * Tank.MAX_WEAPONS
        self._weapons[Tank.SHELLS] = ShellWeapon(game, self)
        self._weapons[Tank.MACHINEGUN] = MachineGunWeapon(game, self)
        self._weapons[Tank.MIRVS] = MirvWeapon(game, self)
        self._weapons[Tank.MISSILES] = MissileWeapon(game, self)
        self._weapons[Tank.NUKES] = NukeWeapon(game, self)
        
        self._max_health = 100.0
        self._total_fuel = 0.0
        self._boosting = False
        self._boosting_sound = None
        
        self._state = Tank.TANK_ALIVE
        
        self._colour = (255, 255, 255)
        
        self._x = 0.0
        self._y = 0.0
        self._tank_angle = 0.0
        self._on_ground = True
        self._health = 100.0
        self._fuel = 0.0
        self._airbourne_x_vel = 0.0
        self._airbourne_y_vel = 0.0
        
        self._gun_angle = 0.0
        self._gun_angle_change_speed = 0.0
        self._gun_power = 10.0
        self._gun_power_change_speed = 0.0
        
        self._selected_weapon = Tank.SHELLS
        self._switch_weapon_time = 0.0
        self._firing = False
        self._exhaust_time = 0.0
        self._smoke_timer = 0.0

    def draw(self):
        if not self._game.get_interface():
            return

        interface = self._game.get_interface()
        
        def transform_point(lx, ly, tx, ty, angle_deg):
            rad = math.radians(angle_deg)
            c = math.cos(rad)
            s = math.sin(rad)
            rx = lx * c - ly * s
            ry = lx * s + ly * c
            return tx + rx, ty + ry
            
        points = []
        # Draw at actual position (no visual offset — matches C++)
        points.append(transform_point(-self._tank_size, 0.0, self._x, self._y, self._tank_angle))
        points.append(transform_point(-(self._tank_size/2.0), self._tank_size, self._x, self._y, self._tank_angle))
        points.append(transform_point((self._tank_size/2.0), self._tank_size, self._x, self._y, self._tank_angle))
        points.append(transform_point(self._tank_size, 0.0, self._x, self._y, self._tank_angle))
        
        screen_points = [interface.game_to_screen(p[0], p[1]) for p in points]
        
        if self._player:
            self._colour = self._player._colour
        
        color = self._colour
        if self._health < (self._max_health / 2.0):
             # Draw with texture/damage logic if needed (placeholder)
             pass
        
        pygame.draw.polygon(interface._window, color, screen_points)
        
        if self._state == Tank.TANK_ALIVE:
             # Calculate Visual Center at actual position (matches C++)
             cx, cy, _ = self.get_centre()
             arrow_length = (self._gun_power / 8.0) + (self._tank_size * 2)
             
             arrow_color = (0, 255, 0, 128) if self._weapons[self._selected_weapon].ready_to_fire() else (255, 0, 0, 128)
             
             # Shaft
             s_pts = []
             s_pts.append((-0.1, self._tank_size * 1.5))
             s_pts.append((-0.1, arrow_length))
             s_pts.append((0.1, arrow_length))
             s_pts.append((0.1, self._tank_size * 1.5))
             
             screen_s_pts = []
             for lx, ly in s_pts:
                 wx, wy = transform_point(lx, ly, cx, cy, self._gun_angle)
                 screen_s_pts.append(interface.game_to_screen(wx, wy))
             
             self._draw_transparent_poly(screen_s_pts, arrow_color)
                 
             # Head
             h_pts = []
             h_pts.append((-0.2, arrow_length))
             h_pts.append((0.0, arrow_length + (arrow_length / 4.0)))
             h_pts.append((0.2, arrow_length))
             
             screen_h_pts = []
             for lx, ly in h_pts:
                  wx, wy = transform_point(lx, ly, cx, cy, self._gun_angle)
                  screen_h_pts.append(interface.game_to_screen(wx, wy))
                  
             self._draw_transparent_poly(screen_h_pts, arrow_color)
             
             # Stats Panel
             start_of_bar = -10.0 + (2.5 * self._stats_position) + 0.1
             
             panel_rect = [
                 (start_of_bar, 7.4),
                 (start_of_bar + 2.3, 7.4),
                 (start_of_bar + 2.3, 6.6),
                 (start_of_bar, 6.6)
             ]
             screen_panel = [interface.game_to_screen(px, py) for px, py in panel_rect]
             self._draw_transparent_poly(screen_panel, (128, 230, 153, 76)) 
             
             # Energy Bar
             start_bar_x = start_of_bar + 0.1
             end_bar_x = start_bar_x + 2.1 * (self._health / 100.0)
             
             hr = min(255, int((1.0 - (self._health / 200.0)) * 255))
             hg = min(255, int((0.5 + (self._health / 200.0)) * 255))
             hb = 128
             
             p1 = interface.game_to_screen(start_bar_x, 7.4)
             p2 = interface.game_to_screen(end_bar_x, 7.3)
             
             rect_w = p2[0] - p1[0]
             rect_h = p2[1] - p1[1]
             if rect_w > 0:
                 pygame.draw.rect(interface._window, (hr, hg, hb), (p1[0], p1[1], rect_w, rect_h))
                 
             # Fuel Bar
             end_fuel_x = start_bar_x + 2.1 * self._fuel
             
             fr = min(255, int((0.5 - (self._fuel * 0.5)) * 255))
             fg = 128
             fb = min(255, int((0.5 + (self._fuel * 0.5)) * 255))
             
             p3 = interface.game_to_screen(start_bar_x, 7.2)
             p4 = interface.game_to_screen(end_fuel_x, 7.1)
             
             fw = p4[0] - p3[0]
             fh = p4[1] - p3[1]
             if fw > 0:
                  pygame.draw.rect(interface._window, (fr, fg, fb), (p3[0], p3[1], fw, fh))
                  
             # Small tank icon
             t_pts = [
                 (start_of_bar + 0.15, 7.0),
                 (start_of_bar + 0.00, 6.7),
                 (start_of_bar + 0.60, 6.7),
                 (start_of_bar + 0.45, 7.0)
             ]
             screen_t = [interface.game_to_screen(tx, ty) for tx, ty in t_pts]
             pygame.draw.polygon(interface._window, self._colour, screen_t)
             
             self._weapons[self._selected_weapon].draw_graphic(start_of_bar + 0.7)


    def _draw_transparent_poly(self, points, color):
        if not points: return
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w, h = max_x - min_x, max_y - min_y
        if w == 0 or h == 0: return
        
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        local_points = [(p[0] - min_x, p[1] - min_y) for p in points]
        pygame.draw.polygon(s, color, local_points)
        self._game.get_interface()._window.blit(s, (min_x, min_y))


    def update(self, time):
        # Update the owner player (used to make the AIs think) — C++ line 377
        self._player.update()
        
        boost = False
        if self._game.get_game_state() != self._game.GameState.ROUND_STARTING:
             dummy_time = 0.0
             boost = self._player.get_command(Tank.CMD_JUMPJETS, dummy_time)
             
        self.move_tank(time, boost)
        
        if self._state == Tank.TANK_ALIVE:
            if self._game.get_game_state() != self._game.GameState.ROUND_STARTING:
                 self.update_gun(time)
                 
                 if self._switch_weapon_time <= 0.0:
                     dummy = 0.0
                     w_left = self._player.get_command(Tank.CMD_WEAPONDOWN, dummy)
                     w_right = self._player.get_command(Tank.CMD_WEAPONUP, dummy)
                     
                     if w_left and not w_right:
                         self._weapons[self._selected_weapon].unselect()
                         self._firing = False
                         while True:
                             self._selected_weapon -= 1
                             if self._selected_weapon < 0: self._selected_weapon = Tank.MAX_WEAPONS - 1
                             if self._weapons[self._selected_weapon].select(): break
                         self._switch_weapon_time = 0.2
                         
                     if w_right and not w_left:
                         self._weapons[self._selected_weapon].unselect()
                         self._firing = False
                         while True:
                             self._selected_weapon += 1
                             if self._selected_weapon == Tank.MAX_WEAPONS: self._selected_weapon = 0
                             if self._weapons[self._selected_weapon].select(): break
                         self._switch_weapon_time = 0.2
                 else:
                     self._switch_weapon_time -= time
        else:
            self.burn(time)
            
        if self._x < -10.0:
            self._x = -10.0
            self._airbourne_x_vel = 0.0
        if self._x > 10.0:
            self._x = 10.0
            self._airbourne_x_vel = 0.0
            
        rad = math.radians(self._tank_angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        left_x = self._x - (self._tank_size / 2.0) * cos_a
        left_y = self._y - (self._tank_size / 2.0) * sin_a
        right_x = self._x + (self._tank_size / 2.0) * cos_a
        right_y = self._y + (self._tank_size / 2.0) * sin_a
        
        landscape = self._game.get_landscape()
        if landscape:
            left_ground_y = landscape.move_to_ground(left_x, left_y)
            right_ground_y = landscape.move_to_ground(right_x, right_y)
            mid_ground_y = landscape.move_to_ground(self._x, self._y)
            
            left_disp = left_ground_y - left_y
            right_disp = right_ground_y - right_y
            mid_disp = mid_ground_y - self._y
            
            rel_disp = 0.0
            max_disp = 0.0
            
            if mid_disp > left_disp and mid_disp > right_disp:
                if left_disp > right_disp:
                    rel_disp = left_disp - mid_disp
                else:
                    rel_disp = mid_disp - right_disp
                max_disp = mid_disp
            elif right_disp > left_disp:
                if (right_disp - left_disp) > (2.0 * (right_disp - mid_disp)):
                    rel_disp = mid_disp - right_disp
                else:
                    rel_disp = left_disp - right_disp
                max_disp = right_disp
            else:
                 if (left_disp - right_disp) > (2.0 * (left_disp - mid_disp)):
                     rel_disp = mid_disp - right_disp
                 else:
                     rel_disp = left_disp - right_disp
                 max_disp = left_disp
                 
            if max_disp < -0.05 or (boost and max_disp <= 0.0):
                self._on_ground = False
            else:
                self._on_ground = True
                self._airbourne_x_vel = 0.0
                self._airbourne_y_vel = 0.0
                
                if rel_disp > 0.1: rel_disp = 0.1
                if rel_disp < -0.1: rel_disp = -0.1
                
                self._tank_angle -= rel_disp * 75.0
                self._y += max_disp
                
        self._weapons[self._selected_weapon].update(time)
        return True

    def move_tank(self, time, boost):
        dummy = 0.0
        left = False
        right = False
        if self._game.get_game_state() != self._game.GameState.ROUND_STARTING:
            left = self._player.get_command(Tank.CMD_TANKLEFT, dummy)
            right = self._player.get_command(Tank.CMD_TANKRIGHT, dummy)
        
        move_x = 0.0
        move_y = 0.0
        
        rad = math.radians(self._tank_angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        if boost and self._state == Tank.TANK_ALIVE and self._fuel > 0.0:
            fuel_used = time * self._fuel_usage_rate
            self._total_fuel -= fuel_used
            self._fuel -= fuel_used
            
            if self._exhaust_time < 0.0:
                ex_x_vel = self._airbourne_x_vel + sin_a * 2.0
                ex_y_vel = self._airbourne_y_vel - cos_a * 2.0
                
                exhaust = Smoke(self._game, self._x, self._y, ex_x_vel, ex_y_vel,
                                2, 0.0, 0.0, 2.5)
                self._game.add_entity(exhaust)
                self._exhaust_time += 0.05
            else:
                self._exhaust_time -= time
                
            self._airbourne_y_vel += cos_a * self._tank_boost * time
            self._airbourne_x_vel -= sin_a * self._tank_boost * time
            
            if left and not right and self._tank_angle < 15.0:
                self._tank_angle += (90.0 * time)
            elif right and not left and self._tank_angle > -15.0:
                self._tank_angle -= (90.0 * time)
            else:
                if self._tank_angle < 0.0:
                    self._tank_angle += 90.0 * time
                    if self._tank_angle > 0.0: self._tank_angle = 0.0
                elif self._tank_angle > 0.0:
                    self._tank_angle -= 90.0 * time
                    if self._tank_angle < 0.0: self._tank_angle = 0.0

            if not self._boosting:
                self._boosting_sound = SoundEntity(self._game, 3, True)
                self._game.add_entity(self._boosting_sound)
                self._boosting = True
        
        elif self._boosting:
             self._boosting = False
             if self._boosting_sound:
                 self._boosting_sound.set_inactive()
                 self._boosting_sound = None

        if self._on_ground:
            moved = False
            if left and not right and self._state == Tank.TANK_ALIVE:
                move_x += cos_a * -self._movement_speed
                move_y += sin_a * -self._movement_speed
                moved = True
            
            if right and not left and self._state == Tank.TANK_ALIVE:
                move_x += cos_a * self._movement_speed
                move_y += sin_a * self._movement_speed
                moved = True
                
            if abs(self._tank_angle) > 30.0 or moved:
                move_x += cos_a * -(self._movement_speed * (self._tank_angle / 65.0))
                move_y += sin_a * -(self._movement_speed * (self._tank_angle / 65.0))
        else:
             self._airbourne_y_vel -= (self._tank_gravity * time)
             move_y = self._airbourne_y_vel
             move_x = self._airbourne_x_vel
             
        self._x += move_x * time
        self._y += move_y * time

    def update_gun(self, time):
        dummy = 0.0
        gun_left = self._player.get_command(Tank.CMD_GUNLEFT, dummy)
        gun_right = self._player.get_command(Tank.CMD_GUNRIGHT, dummy)
        more_power = self._player.get_command(Tank.CMD_GUNUP, dummy)
        less_power = self._player.get_command(Tank.CMD_GUNDOWN, dummy)
        fire = self._player.get_command(Tank.CMD_FIRE, dummy)
        
        if gun_left and not gun_right:
            self._gun_angle_change_speed += time * self._gun_angle_change_acceleration
            if self._gun_angle_change_speed > self._gun_angle_max_change_speed:
                self._gun_angle_change_speed = self._gun_angle_max_change_speed
        elif gun_right and not gun_left:
             self._gun_angle_change_speed -= time * self._gun_angle_change_acceleration
             if self._gun_angle_change_speed < -self._gun_angle_max_change_speed:
                 self._gun_angle_change_speed = -self._gun_angle_max_change_speed
        else:
             self._gun_angle_change_speed = 0.0
             
        self._gun_angle += time * self._gun_angle_change_speed
        if self._gun_angle < -self._gun_angle_max: self._gun_angle = -self._gun_angle_max
        if self._gun_angle > self._gun_angle_max: self._gun_angle = self._gun_angle_max
        
        if more_power and not less_power:
             self._gun_power_change_speed += time * self._gun_power_change_acceleration
             if self._gun_power_change_speed > self._gun_power_max_change_speed:
                 self._gun_power_change_speed = self._gun_power_max_change_speed
        elif less_power and not more_power:
             self._gun_power_change_speed -= time * self._gun_power_change_acceleration
             if self._gun_power_change_speed < -self._gun_power_max_change_speed:
                 self._gun_power_change_speed = -self._gun_power_max_change_speed
        else:
             self._gun_power_change_speed = 0.0
             
        self._gun_power += time * self._gun_power_change_speed
        if self._gun_power < self._gun_power_min: self._gun_power = self._gun_power_min
        if self._gun_power > self._gun_power_max: self._gun_power = self._gun_power_max
        
        self._firing = fire
        self._weapons[self._selected_weapon].fire(fire, time)

    def burn(self, time):
        if self._exhaust_time < 0.0:
            if self._on_ground:
                smoke = Smoke(self._game, self._x, self._y,
                              0.0, 0.5,
                              5, 0.1, 1.0, 0.3)
            else:
                smoke = Smoke(self._game, self._x, self._y,
                              0.0, 0.5,
                              5, 0.1, 0.3, 0.3)
            self._game.add_entity(smoke)
            if self._on_ground:
                self._exhaust_time += self._ground_smoke_release_time
            else:
                self._exhaust_time += self._air_smoke_release_time
        else:
            self._exhaust_time -= time

    def set_colour(self, c): self._colour = c
    def get_colour(self): return self._colour
    def get_player(self): return self._player
    def get_centre(self):
        angle_rads = (self._tank_angle / 180.0) * PI
        cx = self._x - math.sin(angle_rads) * (self._tank_size / 2.0)
        cy = self._y + math.cos(angle_rads) * (self._tank_size / 2.0)
        return cx, cy, self._tank_size * 0.75

    def set_position_on_ground(self, x):
        self._x = x
        if self._game.get_landscape():
            self._y = self._game.get_landscape().move_to_ground(x, 100.0)
        self._tank_angle = 0.0
        self._on_ground = True
        self._airbourne_x_vel = 0.0
        self._airbourne_y_vel = 0.0

    def intersect_tank(self, x1, y1, x2, y2):
        if self._state != Tank.TANK_ALIVE: return False
        
        near_tank = self._tank_size * 1.12
        if x1 < (self._x - near_tank) and x2 < (self._x - near_tank): return False
        if x1 > (self._x + near_tank) and x2 > (self._x + near_tank): return False
        if y1 < (self._y - near_tank) and y2 < (self._y - near_tank): return False
        if y1 > (self._y + near_tank) and y2 > (self._y + near_tank): return False
        
        rx1 = x1 - self._x
        ry1 = y1 - self._y
        rx2 = x2 - self._x
        ry2 = y2 - self._y
        
        angle_rads = -math.radians(self._tank_angle)
        cos_ang = math.cos(angle_rads)
        sin_ang = math.sin(angle_rads)
        
        tx1 = rx1 * cos_ang - ry1 * sin_ang
        ty1 = rx1 * sin_ang + ry1 * cos_ang
        tx2 = rx2 * cos_ang - ry2 * sin_ang
        ty2 = rx2 * sin_ang + ry2 * cos_ang
        
        x_len = tx2 - tx1
        y_len = ty2 - ty1
        
        horizontal = False
        m = 0.0
        c = 0.0
        
        if abs(x_len) > abs(y_len):
            m = y_len / x_len
            c = ty1 - m * tx1
            horizontal = True
        else:
            if y_len == 0.0: y_len = 0.00001
            m = x_len / y_len
            c = tx1 - m * ty1
            horizontal = False
            
        if (ty1 > 0.0 and ty2 < 0.0) or (ty1 < 0.0 and ty2 > 0.0):
            x_intersect = (-c / m) if horizontal else c
            if x_intersect > -self._tank_size and x_intersect < self._tank_size:
                return True
                
        if (ty1 > self._tank_size and ty2 < self._tank_size) or \
           (ty1 < self._tank_size and ty2 > self._tank_size):
               x_intersect = ((self._tank_size - c) / m) if horizontal else (self._tank_size * m + c)
               if x_intersect > -(self._tank_size / 2.0) and x_intersect < (self._tank_size / 2.0):
                   return True
        
        x_intersect = ((2 * self._tank_size - c) / (m - 2)) if horizontal else ((2 * m * self._tank_size + c) / (1 - 2 * m))
        
        on_segment = False
        if tx1 <= tx2:
             if tx1 <= x_intersect <= tx2: on_segment = True
        else:
             if tx2 <= x_intersect <= tx1: on_segment = True
             
        if on_segment and (x_intersect > -self._tank_size and x_intersect < (-self._tank_size / 2.0)):
            return True
            
        x_intersect = ((2 * self._tank_size - c) / (m + 2)) if horizontal else ((2 * m * self._tank_size + c) / (1 + 2 * m))
        
        on_segment = False
        if tx1 <= tx2:
             if tx1 <= x_intersect <= tx2: on_segment = True
        else:
             if tx2 <= x_intersect <= tx1: on_segment = True
             
        if on_segment and (x_intersect < self._tank_size and x_intersect > (self._tank_size / 2.0)):
            return True
            
        return False

    def do_damage(self, damage):
        self._health -= damage
        if self._health < 0.0 and self._state == Tank.TANK_ALIVE:
            self._health = 0.0
            self._state = Tank.TANK_DEAD
            self._game.record_tank_death()
            self._exhaust_time = -0.5
            if self._firing:
                self._weapons[self._selected_weapon].fire(False, 0.0)
                self._firing = False
            return True
        return False

    def do_pre_round(self):
        if self._state != Tank.TANK_RESIGNED:
            self._state = Tank.TANK_ALIVE
        
        self._gun_angle = 0.0
        self._gun_angle_change_speed = 0.0
        self._gun_power = 10.0
        self._gun_power_change_speed = 0.0
        self._tank_angle = 0.0
        self._airbourne_x_vel = 0.0
        self._airbourne_y_vel = 0.0
        self._on_ground = False
        self._health = self._max_health
        self._exhaust_time = 0.0
        self._fuel = self._total_fuel
        if self._fuel > 1.0:
            self._fuel = 1.0
        
        self._selected_weapon = Tank.SHELLS
        for w in self._weapons:
            w.set_ammo_for_round()
        self._weapons[self._selected_weapon].select()
        
        self._switch_weapon_time = 0.0
        self._firing = False
        return True

    def do_post_round(self):
        if self._firing:
            self._weapons[self._selected_weapon].fire(False, 0.0)
            self._firing = False
            
        if self._boosting_sound:
            self._boosting_sound.set_inactive()
            self._boosting_sound = None
            self._boosting = False
            
        return True

    def is_firing(self): return self._firing
    def ready_to_fire(self): return self._weapons[self._selected_weapon].ready_to_fire()
    
    def gun_launch_position(self):
        cx, cy, _ = self.get_centre()
        
        x = cx + (-deg_sin(self._gun_angle) * self._tank_size * 1.2)
        y = cy + ( deg_cos(self._gun_angle) * self._tank_size * 1.2)
        return x, y

    def gun_launch_velocity(self):
        vx = self._airbourne_x_vel - deg_sin(self._gun_angle) * self._gun_power
        vy = self._airbourne_y_vel + deg_cos(self._gun_angle) * self._gun_power
        return vx, vy

    def gun_launch_velocity_at_power(self, power):
        vx = self._airbourne_x_vel - deg_sin(self._gun_angle) * power
        vy = self._airbourne_y_vel + deg_cos(self._gun_angle) * power
        return vx, vy

    def gun_launch_angle(self): return self._gun_angle
    
    def get_weapon(self, index): return self._weapons[index]
    def get_selected_weapon(self): return self._selected_weapon

    def alive(self):
        return self._state == Tank.TANK_ALIVE

    def set_position(self, x, y):
        self._x = x
        self._y = y
        self._tank_angle = 0.0
        self._on_ground = False # Assume air if explicit set
        self._airbourne_x_vel = 0.0
        self._airbourne_y_vel = 0.0

    def damage(self, amount, attacker):
        killed = self.do_damage(amount)
        if killed and attacker:
             attacker.defeat(self._player)
