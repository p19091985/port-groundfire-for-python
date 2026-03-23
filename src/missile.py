from .entity import Entity
from .trail import Trail
from .common import PI
import math
import pygame
# from .controls import Controls # Removed to fix circular import

class Missile(Entity):
    
    OPTION_FuelSupply = 3.0
    OPTION_SteerSensitivity = 300.0
    OPTION_Speed = 9.0

    def __init__(self, game, player, x, y, angle, size, damage):
        super().__init__(game)
        self._player = player
        self._x = x
        self._y = y
        self._angle = angle
        self._size = size
        self._damage = damage
        
        self._angle_change = 0.0
        self._fuel = Missile.OPTION_FuelSupply
        self._x_vel = 0.0
        self._y_vel = 0.0
        
        self._trail = Trail(game, self._x, self._y)
        self._game.add_entity(self._trail)
        
        self._missile_sound = None
        if self._game.get_sound():
             # Sound 4 is missile flying
             self._missile_sound = self._game.get_sound().SoundSource(self._game.get_sound(), 4, True)

    def __del__(self):
        # Stop sound
        # In Python __del__ is unreliable, but we try.
        pass

    @staticmethod
    def read_settings(settings):
        Missile.OPTION_FuelSupply = settings.get_float("Missile", "Fuel", 3.0)
        Missile.OPTION_SteerSensitivity = settings.get_float("Missile", "SteerSensitivity", 300.0)
        Missile.OPTION_Speed = settings.get_float("Missile", "Speed", 9.0)

    def draw(self):
        # Draw missile triangle
        # Same logic as Shell but rotated
        # Verts from C++:
        # (-0.08, 0), (0, 0.08), (0.08, 0)
        # (-0.08, -0.16)... various parts making a rocket shape.
        
        # We can implement a simple shape or sprite.
        # Let's draw a white polygon representing the rocket.
        # Main body: tri (-0.08, 0), (0, 0.08), (0.08, 0) is the tip?
        # Let's make a Surface for the missile and rotate it.
        
        # 0.16 width approx 8-10 pixels?
        
        if not self._game.get_interface(): return
        
        # We'll use a predefined shape for simplicity in MVP or draw dynamic poly.
        # Dynamic poly with rotation is math heavy every frame.
        # Better: create a cached surface if possible, or just math it.
        # Given "Port fiel", math it.
        
        pts = [
            (-0.08, 0.0), (0.0, 0.08), (0.08, 0.0), # Tip
            (-0.08, -0.16), (0.08, -0.16), # Base
            # Fins...
        ]
        # Simplified rocket shape:
        # Tip (0, 0.08), Left (-0.08, -0.16), Right (0.08, -0.16).
        # Center of rotation is (0,0).
        
        screen_pts = []
        rad = math.radians(self._angle) # Angle is in degrees? C++ glRotate uses degrees.
        # math.cos/sin take radians.
        # Rotation logic: 
        # C++ glRotate(_angle, 0,0,1). Z-axis rotation. CCW.
        # NewX = x * cos - y * sin
        # NewY = x * sin + y * cos
        
        import math
        cos_a = math.cos(math.radians(self._angle))
        sin_a = math.sin(math.radians(self._angle))
        
        # Define the shape vertices relative to 0,0
        raw_verts = [
            (0.0, 0.08), (-0.08, 0.0), (-0.08, -0.16),
            (0.08, -0.16), (0.08, 0.0)
        ]
        
        for rx, ry in raw_verts:
             # Rotate
             tx = rx * cos_a - ry * sin_a
             ty = rx * sin_a + ry * cos_a
             
             # Translate to world
             wx = self._x + tx
             wy = self._y + ty
             
             screen_pts.append(self._game.get_interface().game_to_screen(wx, wy))
             
        pygame.draw.polygon(self._game.get_interface()._window, (255, 255, 255), screen_pts)

    def update(self, time):
        old_x = self._x
        old_y = self._y
        
        if self._fuel < 0.0:
            # Free fall
            self._x += self._x_vel * time
            self._y += self._y_vel * time
            self._y_vel -= 10.0 * time # Gravity
        else:
            # Powered flight
            # getCommand returns bool.
            if self._player:
                # C++ uses CMD_GUNLEFT/RIGHT to steer missiles
                from .player import Player
                dummy = [0.0]
                steer_left = self._player.get_command(Player.CMD_GUNLEFT, dummy)
                steer_right = self._player.get_command(Player.CMD_GUNRIGHT, dummy)
                
                if steer_left and not steer_right:
                    self._angle_change += Missile.OPTION_SteerSensitivity * time
                    if self._angle_change > 500.0: self._angle_change = 500.0
                elif not steer_left and steer_right:
                    self._angle_change -= Missile.OPTION_SteerSensitivity * time
                    if self._angle_change < -500.0: self._angle_change = -500.0
                else:
                    # Straighten out
                    if self._angle_change > 0.0:
                        self._angle_change -= 3 * Missile.OPTION_SteerSensitivity * time
                        if self._angle_change < 0.0: self._angle_change = 0.0
                    elif self._angle_change < 0.0:
                        self._angle_change += 3 * Missile.OPTION_SteerSensitivity * time
                        if self._angle_change > 0.0: self._angle_change = 0.0
            
            self._angle += time * self._angle_change
            
            # Move
            # _x -= time * sin(angle) * (Speed - cos(angle)) 
            # Note: C++ uses sin((angle/180)*PI).
            rad = (self._angle / 180.0) * PI
            speed_factor = (Missile.OPTION_Speed - math.cos(rad)) # Wait, (Speed - cos)? 
            # Original: (OPTION_Speed - cos(...)) 
            # This logic seems to imply speed varies by angle? Or just quirky physics.
            
            vx = -math.sin(rad) * speed_factor
            vy = math.cos(rad) * speed_factor
            
            self._x += time * vx
            self._y += time * vy
            
        landscape = self._game.get_landscape()
        w = landscape.get_landscape_width() if landscape else 10.0
        
        # Out of bounds
        if self._x > w or self._x < -w:
            if self._fuel >= 0.0: self._trail.set_inactive()
            return False # Die
            
        # Ground
        if landscape:
            coll = landscape.ground_collision(old_x, old_y, self._x, self._y)
            if coll[0]:
                if self._fuel >= 0.0:
                    self._trail.lay_trail(coll[1], coll[2])
                self.explode(coll[1], coll[2], -1)
                return False
                
        # Fuel check
        if self._fuel >= 0.0:
            self._trail.lay_trail(self._x, self._y)
            self._fuel -= time
            if self._fuel < 0.0:
                # Run out
                rad = (self._angle / 180.0) * PI
                speed_factor = (Missile.OPTION_Speed - math.cos(rad))
                self._x_vel = -math.sin(rad) * speed_factor
                self._y_vel = math.cos(rad) * speed_factor
                
                self._trail.set_inactive()
                self._missile_sound = None # Stop sound
                
        # Tank collision
        players = self._game.get_players()
        for i, p in enumerate(players):
            if p and p.get_tank():
                if p.get_tank().intersect_tank(old_x, old_y, self._x, self._y):
                    self.explode(self._x, self._y, i)
                    return False
        
        return True

    def explode(self, x, y, hit_tank):
        self._game.explosion(x, y, self._size, self._damage, hit_tank, 6, False, self._player)
        if self._fuel >= 0:
            self._trail.set_inactive()
        return False
