from .entity import Entity
from .networkstate import EntitySnapshot
from .renderprimitives import EntityRenderState, PolygonPrimitive
from .trail import Trail
from typing import TYPE_CHECKING
import math

if TYPE_CHECKING:
    from .player import Player

class Shell(Entity):
    def __init__(self, game, player, x_launch, y_launch, x_launch_vel, y_launch_vel, launch_time, size, damage, white_out):
        super().__init__(game)
        self._player = player
        self._x_launch = x_launch
        self._y_launch = y_launch
        self._x_launch_vel = x_launch_vel
        self._y_launch_vel = y_launch_vel
        self._launch_time = launch_time
        self._size = size
        self._damage = damage
        self._white_out = white_out
        
        self._x = x_launch
        self._y = y_launch
        
        self._trail = Trail(game, self._x, self._y)
        self._game.add_entity(self._trail)

    def draw(self):
        # Draw as tiny triangle
        if not self._game.get_interface(): return

        # White plain color
        # Interface doesn't expose raw GL.
        # We need to map local coords to screen coords.
        
        # Tri: (0, 0.018), (0.03, -0.018), (-0.03, -0.018)
        # These are in game units relative to self._x, self._y
        
        self.get_graphics().draw_world_polygon(
            [
                (self._x + 0.00, self._y + 0.018),
                (self._x + 0.03, self._y - 0.018),
                (self._x - 0.03, self._y - 0.018),
            ],
            (255, 255, 255),
        )

    def get_render_state(self):
        return EntityRenderState(
            entity_id=self.get_entity_id(),
            entity_type=self.get_entity_type(),
            primitives=(
                PolygonPrimitive(
                    points=(
                        (self._x + 0.00, self._y + 0.018),
                        (self._x + 0.03, self._y - 0.018),
                        (self._x - 0.03, self._y - 0.018),
                    ),
                    colour=(255, 255, 255),
                ),
            ),
            metadata={"size": self._size, "damage": self._damage, "white_out": self._white_out},
        )

    def build_network_snapshot(self):
        return EntitySnapshot(
            entity_id=-1 if self.get_entity_id() is None else self.get_entity_id(),
            entity_type=self.get_entity_type(),
            position=self.get_position(),
            payload={
                "size": self._size,
                "damage": self._damage,
                "white_out": self._white_out,
                "player_number": getattr(self._player, "_number", None),
            },
        )

    def update(self, time):
        old_x = self._x
        old_y = self._y
        
        time_since_launch = self._game.get_time() - self._launch_time
        
        # Trajectory physics: x = vt + x0, y = vt - 0.5gt^2 + y0 ?
        # C++: _y = timeSinceLaunch * (_yLaunchVel - 5.0f * timeSinceLaunch) + _yLaunch;
        # 5.0f * t * t effectively means 0.5 * g * t^2 where g=10.
        
        self._x = time_since_launch * self._x_launch_vel + self._x_launch
        self._y = time_since_launch * (self._y_launch_vel - 5.0 * time_since_launch) + self._y_launch
        
        landscape = self._game.get_landscape()
        landscape_width = landscape.get_landscape_width() if landscape else 10.0
        
        # Out of bounds
        if self._x > landscape_width or self._x < -landscape_width:
            self._trail.lay_trail(self._x, self._y)
            self._trail.set_inactive()
            if self._player:
                self._player.record_shot(self._x, self._y, -1)
            return False
            
        # Ground Collision
        if landscape:
            coll_res = landscape.ground_collision(old_x, old_y, self._x, self._y)
            if coll_res[0]:
                 cx, cy = coll_res[1], coll_res[2]
                 self._trail.lay_trail(cx, cy)
                 self.explode(cx, cy, -1)
                 return False

        self._trail.lay_trail(self._x, self._y)
        
        # Tank Collision
        players = self._game.get_players()
        for i, p in enumerate(players):
            if p and p.get_tank():
                if p.get_tank().intersect_tank(old_x, old_y, self._x, self._y):
                    self.explode(self._x, self._y, i)
                    return False
        
        return True

    def explode(self, x, y, hit_tank_idx):
        self._trail.set_inactive()
        
        self._game.explosion(x, y, self._size, self._damage, hit_tank_idx, 
                             7 if self._white_out else 1, self._white_out, self._player)
        
        if self._player:
            self._player.record_shot(x, y, hit_tank_idx)
            
        # Suicide implies deletion in update loop return false
