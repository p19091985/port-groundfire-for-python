from .entity import Entity
from .networkstate import EntitySnapshot
from .renderprimitives import EntityRenderState, FullscreenOverlayPrimitive, TextureCenteredPrimitive

class Blast(Entity):
    # Static settings
    OPTION_BlastFadeRate = 0.1
    OPTION_WhiteoutFadeRate = 0.6

    def __init__(self, game, x, y, size, fade_away, white_out):
        super().__init__(game)
        self._x = x
        self._y = y
        self._size = size
        self._fade_away = fade_away
        self._white_out = white_out
        self._white_out_level = 1.0 if white_out else 0.0

    @staticmethod
    def read_settings(settings):
        Blast.OPTION_BlastFadeRate = settings.get_float("Effects", "BlastFadeRate", 0.1)
        Blast.OPTION_WhiteoutFadeRate = settings.get_float("Effects", "WhiteoutFadeRate", 0.6)

    def draw(self):
        graphics = self.get_graphics()
        # Draw Blast
        # Texture 0 is blast texture.
        if self._game.get_interface().get_texture_surface(0):
            # Blast size
            blast_size = self._size * 1.1
            alpha = max(0, int(self._fade_away * 255))
            graphics.draw_texture_centered(0, self._x, self._y, blast_size * 2.0, alpha=alpha)

        # Draw Whiteout
        if self._white_out:
            alpha_val = max(0, int(self._white_out_level * 255))
            graphics.draw_fullscreen_overlay((255, 255, 255, alpha_val))

    def get_render_state(self):
        primitives = []
        interface = self._game.get_interface()
        if interface and interface.get_texture_surface(0):
            blast_size = self._size * 1.1
            primitives.append(
                TextureCenteredPrimitive(
                    texture_id=0,
                    x=self._x,
                    y=self._y,
                    width=blast_size * 2.0,
                    alpha=max(0, int(self._fade_away * 255)),
                )
            )

        if self._white_out:
            primitives.append(
                FullscreenOverlayPrimitive(
                    colour=(255, 255, 255, max(0, int(self._white_out_level * 255)))
                )
            )

        return EntityRenderState(
            entity_id=self.get_entity_id(),
            entity_type=self.get_entity_type(),
            primitives=tuple(primitives),
            metadata={"size": self._size, "fade_away": self._fade_away, "white_out": self._white_out},
        )

    def build_network_snapshot(self):
        return EntitySnapshot(
            entity_id=-1 if self.get_entity_id() is None else self.get_entity_id(),
            entity_type=self.get_entity_type(),
            position=self.get_position(),
            payload={
                "size": self._size,
                "fade_away": self._fade_away,
                "white_out": self._white_out,
                "white_out_level": self._white_out_level,
            },
        )

    def update(self, time):
        self._fade_away -= time * Blast.OPTION_BlastFadeRate
        
        if self._white_out:
            self._white_out_level -= time * Blast.OPTION_WhiteoutFadeRate
            if self._white_out_level < 0.0:
                self._white_out = False
        
        if self._fade_away < 0.0:
            return False # Dead
            
        return True
