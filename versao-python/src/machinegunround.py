from .entity import Entity
from .networkstate import EntitySnapshot
from .renderprimitives import EntityRenderState, LinePrimitive
from .soundentity import SoundEntity

class MachineGunRound(Entity):
    def __init__(self, game, player, x_launch, y_launch, x_launch_vel, y_launch_vel, launch_time, damage):
        super().__init__(game)
        self._player = player
        self._x_launch = x_launch
        self._y_launch = y_launch
        self._x_launch_vel = x_launch_vel
        self._y_launch_vel = y_launch_vel
        self._launch_time = launch_time
        self._damage = damage
        
        self._x = x_launch
        self._y = y_launch
        self._x_back = x_launch
        self._y_back = y_launch
        
        self._kill_next_frame = False

    def draw(self):
        # Draw as line
        if not self._game.get_interface(): return
        
        self.get_graphics().draw_world_line((self._x_back, self._y_back), (self._x, self._y), (255, 255, 255))

    def get_render_state(self):
        return EntityRenderState(
            entity_id=self.get_entity_id(),
            entity_type=self.get_entity_type(),
            primitives=(
                LinePrimitive(
                    start=(self._x_back, self._y_back),
                    end=(self._x, self._y),
                    colour=(255, 255, 255),
                ),
            ),
            metadata={"damage": self._damage, "kill_next_frame": self._kill_next_frame},
        )

    def build_network_snapshot(self):
        return EntitySnapshot(
            entity_id=-1 if self.get_entity_id() is None else self.get_entity_id(),
            entity_type=self.get_entity_type(),
            position=self.get_position(),
            payload={
                "back_position": (self._x_back, self._y_back),
                "damage": self._damage,
                "kill_next_frame": self._kill_next_frame,
                "player_number": getattr(self._player, "_number", None),
            },
        )

    def update(self, time):
        if self._kill_next_frame:
            return False
            
        old_x = self._x
        old_y = self._y
        
        time_since_launch = self._game.get_time() - self._launch_time
        
        self._x = time_since_launch * self._x_launch_vel + self._x_launch
        self._y = time_since_launch * (self._y_launch_vel - 5.0 * time_since_launch) + self._y_launch
        
        # Back position
        t_back = time_since_launch - 0.01
        if t_back < 0.0: t_back = 0.0
        
        self._x_back = t_back * self._x_launch_vel + self._x_launch
        self._y_back = t_back * (self._y_launch_vel - 5.0 * t_back) + self._y_launch
        
        landscape = self._game.get_landscape()
        w = landscape.get_landscape_width() if landscape else 10.0
        
        if self._x > w or self._x < -w:
            self._kill_next_frame = True
            return True
            
        if landscape:
            coll = landscape.ground_collision(old_x, old_y, self._x, self._y)
            if coll[0]:
                self._x = coll[1]
                self._y = coll[2]
                self._kill_next_frame = True
                return True
                
        players = self._game.get_players()
        for i, p in enumerate(players):
            if p and p.get_tank():
                 if p.get_tank().intersect_tank(old_x, old_y, self._x, self._y):
                     # Hit
                     clang = SoundEntity(self._game, 9, False)
                     self._game.add_entity(clang)
                     
                     if p.get_tank().do_damage(self._damage):
                         self._player.defeat(p)
                     self._kill_next_frame = True
                     break
                     
        return True
