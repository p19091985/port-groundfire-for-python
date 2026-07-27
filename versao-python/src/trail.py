from .entity import Entity
from .networkstate import EntitySnapshot
import math
from .common import sqr, PI # Assuming common defines these
from .renderprimitives import EntityRenderState, TextureCenteredPrimitive

class Segment:
    def __init__(self, x, y, fade_away, length, angle):
        self.x = x
        self.y = y
        self.fade_away = fade_away
        self.length = length
        self.angle = angle

LAY_DISTANCE_SQUARED = 0.04

class Trail(Entity):
    OPTION_TrailFadeRate = 0.2

    def __init__(self, game, start_x, start_y):
        super().__init__(game)
        self._last_x = start_x
        self._last_y = start_y
        self._active = True
        self._trail_segment_list = []

    @staticmethod
    def read_settings(settings):
        Trail.OPTION_TrailFadeRate = settings.get_float("Effects", "TrailFadeRate", 0.2)

    def draw(self):
        # Texture 1 is trail
        tex = self._game.get_interface().get_texture_surface(1)
        if not tex: return
        
        # Each segment is drawn as a quad.
        # Original: 
        # Quad width (-0.1 to 0.1) -> 0.2 units.
        # Height (-0.2-len to 0.2).
        
        # Pygame scaling/rotation for each segment:
        
        width_units = 0.2
        # Length varies per segment but base height (-0.2 to 0.2) + length?
        # Verts: 
        # (-0.1, -0.2 - len)
        # ( 0.1, -0.2 - len)
        # ( 0.1,  0.2)
        # (-0.1,  0.2)
        # Total height = 0.4 + len
        
        for seg in self._trail_segment_list:
            total_h = 0.4 + seg.length
            
            alpha = max(0, int(seg.fade_away * 255))
            self.get_graphics().draw_texture_centered(
                1,
                seg.x,
                seg.y,
                width_units,
                total_h,
                alpha=alpha,
                rotation=-seg.angle,
            )

    def get_render_state(self):
        primitives = []
        for seg in self._trail_segment_list:
            primitives.append(
                TextureCenteredPrimitive(
                    texture_id=1,
                    x=seg.x,
                    y=seg.y,
                    width=0.2,
                    height=0.4 + seg.length,
                    alpha=max(0, int(seg.fade_away * 255)),
                    rotation=-seg.angle,
                )
            )

        return EntityRenderState(
            entity_id=self.get_entity_id(),
            entity_type=self.get_entity_type(),
            primitives=tuple(primitives),
            metadata={"active": self._active, "segment_count": len(self._trail_segment_list)},
        )

    def build_network_snapshot(self):
        return EntitySnapshot(
            entity_id=-1 if self.get_entity_id() is None else self.get_entity_id(),
            entity_type=self.get_entity_type(),
            position=(self._last_x, self._last_y),
            payload={
                "active": self._active,
                "segment_count": len(self._trail_segment_list),
            },
        )

    def update(self, time):
        # Filter list in place
        new_list = []
        for seg in self._trail_segment_list:
            seg.fade_away -= Trail.OPTION_TrailFadeRate * time
            if seg.fade_away >= 0.0:
                new_list.append(seg)
        self._trail_segment_list = new_list
        
        if not self._active and not self._trail_segment_list:
            return False # Dead
            
        return True

    def lay_trail(self, x, y):
        x_diff = x - self._last_x
        y_diff = y - self._last_y
        dist_sq = sqr(x_diff) + sqr(y_diff)
        
        while dist_sq > LAY_DISTANCE_SQUARED:
            factor = 0.2 / math.sqrt(dist_sq)
            self._last_x += x_diff * factor
            self._last_y += y_diff * factor
            
            new_seg = Segment(self._last_x, self._last_y, 0.8, 0.2, 0.0)
            
            # Angle
            dist = math.sqrt(dist_sq)
            # acos domain check?
            val = y_diff / dist
            if val > 1.0: val = 1.0
            elif val < -1.0: val = -1.0
            
            if x_diff > 0.0:
                new_seg.angle = -math.acos(val) * (180.0 / PI)
            elif x_diff < 0.0:
                new_seg.angle = math.acos(val) * (180.0 / PI)
            else:
                new_seg.angle = 0.0
                
            self._trail_segment_list.append(new_seg)
            
            x_diff = x - self._last_x
            y_diff = y - self._last_y
            dist_sq = sqr(x_diff) + sqr(y_diff)

    def set_inactive(self):
        self._active = False
