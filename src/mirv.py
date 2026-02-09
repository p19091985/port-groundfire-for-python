from .entity import Entity
from .trail import Trail
from .shell import Shell
from .inifile import ReadIniFile

class Mirv(Entity):
    OPTION_Fragments = 5
    OPTION_Spread = 0.2

    def __init__(self, game, player, x_launch, y_launch, x_launch_vel, y_launch_vel, launch_time, size, damage):
        super().__init__(game)
        self._player = player
        self._x_launch = x_launch
        self._y_launch = y_launch
        self._x_launch_vel = x_launch_vel
        self._y_launch_vel = y_launch_vel
        self._launch_time = launch_time
        self._size = size
        self._damage = damage
        
        self._x = x_launch
        self._y = y_launch
        
        self._trail = Trail(game, self._x, self._y)
        self._game.add_entity(self._trail)
        
        # Apex calculation
        # y = y0 + vy*t - 5t^2. Apex when vy - 10t = 0 => t = vy/10.
        # But wait, original code says: _apexTime = _launchTime + _yLaunchVel / 10.0f;
        # Valid assumption for gravity=10.
        self._apex_time = launch_time + y_launch_vel / 10.0

    @staticmethod
    def read_settings(settings: ReadIniFile):
        Mirv.OPTION_Fragments = settings.get_int("Mirv", "Fragments", 5)
        Mirv.OPTION_Spread = settings.get_float("Mirv", "Spread", 0.2)

    def draw(self):
        # Draw as tiny triangle (same as Shell)
        if not self._game.get_interface(): return
        
        p1 = self._game.get_interface().game_to_screen(self._x + 0.00, self._y + 0.018)
        p2 = self._game.get_interface().game_to_screen(self._x + 0.03, self._y - 0.018)
        p3 = self._game.get_interface().game_to_screen(self._x - 0.03, self._y - 0.018)
        
        import pygame
        pygame.draw.polygon(self._game.get_interface()._window, (255, 255, 255), [p1, p2, p3])

    def update(self, time):
        old_x = self._x
        old_y = self._y
        
        current_time = self._game.get_time()
        
        if current_time > self._apex_time:
            # Split
            split_time = self._apex_time - self._launch_time
            
            # Position at split
            self._x = split_time * self._x_launch_vel + self._x_launch
            self._y = split_time * (self._y_launch_vel - 5.0 * split_time) + self._y_launch
            
            for i in range(Mirv.OPTION_Fragments):
                # Spread logic
                # fragXvel = _xLaunchVel + (_xLaunchVel * OPTION_Spread * (i - ((Frag-1)/2.0)))
                offset = float(i) - ((Mirv.OPTION_Fragments - 1) / 2.0)
                frag_x_vel = self._x_launch_vel + (self._x_launch_vel * Mirv.OPTION_Spread * offset)
                
                fragment = Shell(self._game, self._player, self._x, self._y,
                                 frag_x_vel, 0.0, self._apex_time,
                                 self._size, self._damage, False)
                self._game.add_entity(fragment)
                
            self._trail.lay_trail(self._x, self._y)
            self._trail.set_inactive()
            return False # Consume MIRV
            
        # Normal update
        time_since_launch = current_time - self._launch_time
        self._x = time_since_launch * self._x_launch_vel + self._x_launch
        self._y = time_since_launch * (self._y_launch_vel - 5.0 * time_since_launch) + self._y_launch
        
        landscape = self._game.get_landscape()
        w = landscape.get_landscape_width() if landscape else 10.0
        
        if self._x > w or self._x < -w:
            self._trail.lay_trail(self._x, self._y)
            self._trail.set_inactive()
            return False
            
        if landscape:
            coll = landscape.ground_collision(old_x, old_y, self._x, self._y)
            if coll[0]:
                self._trail.lay_trail(coll[1], coll[2])
                self.explode(coll[1], coll[2], -1)
                return False
                
        self._trail.lay_trail(self._x, self._y)
        
        players = self._game.get_players()
        for i, p in enumerate(players):
            if p and p.get_tank():
                if p.get_tank().intersect_tank(old_x, old_y, self._x, self._y):
                    self.explode(self._x, self._y, i)
                    return False
        
        return True

    def explode(self, x, y, hit_tank):
        self._trail.set_inactive()
        self._game.explosion(x, y, self._size, self._damage, hit_tank, 1, False, self._player)
        return False
