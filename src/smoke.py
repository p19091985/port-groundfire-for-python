from .entity import Entity
from .networkstate import EntitySnapshot
from .renderprimitives import EntityRenderState, TextureCenteredPrimitive

# Need to ensure drawing logic.
# Smoke rotates and scales a texture.
# Pygame: blit with rotation and scaling.

class Smoke(Entity):
    def __init__(self, game, x, y, x_vel, y_vel, texture_id, rotation_rate, growth_rate, fade_rate):
        super().__init__(game)
        self._x = x
        self._y = y
        self._x_vel = x_vel
        self._y_vel = y_vel
        self._texture_id = texture_id
        self._rotation_rate = rotation_rate
        self._growth_rate = growth_rate
        self._fade_rate = fade_rate
        
        self._size = 0.25
        self._fade_away = 0.7
        self._rotate = 0.0

    def draw(self):
        # Retrieve texture
        if not self._game.get_interface():
            return
            
        tex = self._game.get_interface().get_texture_surface(self._texture_id)
        if not tex:
            return

        alpha = max(0, int(self._fade_away * 255))
        self.get_graphics().draw_texture_centered(
            self._texture_id,
            self._x,
            self._y,
            self._size * 2.0,
            alpha=alpha,
            rotation=-self._rotate,
        )

    def get_render_state(self):
        return EntityRenderState(
            entity_id=self.get_entity_id(),
            entity_type=self.get_entity_type(),
            primitives=(
                TextureCenteredPrimitive(
                    texture_id=self._texture_id,
                    x=self._x,
                    y=self._y,
                    width=self._size * 2.0,
                    alpha=max(0, int(self._fade_away * 255)),
                    rotation=-self._rotate,
                ),
            ),
            metadata={"size": self._size, "fade_away": self._fade_away},
        )

    def build_network_snapshot(self):
        return EntitySnapshot(
            entity_id=-1 if self.get_entity_id() is None else self.get_entity_id(),
            entity_type=self.get_entity_type(),
            position=self.get_position(),
            payload={
                "texture_id": self._texture_id,
                "rotation": self._rotate,
                "size": self._size,
                "fade_away": self._fade_away,
            },
        )

    def update(self, time):
        self._rotate += time * self._rotation_rate
        self._size += time * self._growth_rate
        self._fade_away -= time * self._fade_rate
        
        self._x += (self._x_vel * time)
        self._y += (self._y_vel * time)
        
        if self._fade_away < 0.0:
            return False # Dead
        
        return True
