from .entity import Entity
import math
import pygame
from .common import sqr, PI # Assuming common defines these

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
            
            w_px = self._game.get_interface().scale_len(width_units)
            h_px = self._game.get_interface().scale_len(total_h)
            
            if w_px <= 0 or h_px <= 0: continue
            
            # Scale
            scaled = pygame.transform.scale(tex, (w_px, h_px))
            
            # Rotate
            rotated = pygame.transform.rotate(scaled, -seg.angle)
            
            # Alpha
            alpha = int(seg.fade_away * 255)
            if alpha < 0: alpha = 0
            rotated.set_alpha(alpha)
            
            # Position
            # Segment x,y is center of rotation?
            # C++: glTranslatef (seg->x, seg->y, -6.0f); glRotatef...
            # The verts are relative to (0,0). (0,0) is roughly top-center of the quad?
            # Top Y is 0.2. Bottom Y is -0.2-len.
            # Center of the quad logic is: Ymid = (0.2 + (-0.2 - len))/2 = -len/2.
            # So the visual Quad is shifted down by len/2 relative to seg->x,y.
            
            # Correct Pygame rotation center logic:
            # We must map (0, -len/2) rotated by angle to screen, then blit center.
            
            # Let's simplify: map seg.x, seg.y to screen.
            sx, sy = self._game.get_interface().game_to_screen(seg.x, seg.y)
            
            # But the pivot point in C++ glRotate is (0,0,0).
            # The quad is drawn relative to that pivot.
            # Since the quad verts are not centered on 0,0, rotation swings it.
            # Center of Quad geometry: X=0, Y=-len/2.
            # So it pivots around a point 0.2 units below its top edge ??
            
            # Actually easier:
            # Just rotate the surface. The center of the Pygame surface corresponds to the center of the image.
            # We need to align the "pivot" (0,0 in local coords) with (seg.x, seg.y) on screen.
            # In local coords, (0,0) is... where?
            # Verts Y range: [0.2, -0.2-len].
            # 0.0 is inside this range.
            # 0.0 is 0.2 units from the top edge. 
            # Total height H = 0.4+len.
            # 0.0 is at (0.2 / H) fraction from top.
            
            # This is complex in Pygame without vector math.
            # Using simple center blit for now might look slightly off but acceptable.
            
            rect = rotated.get_rect(center=(sx, sy))
            self._game.get_interface()._window.blit(rotated, rect)

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
