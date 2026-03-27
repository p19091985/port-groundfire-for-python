from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game

class Entity:
    def __init__(self, game: 'Game'):
        self._game = game
        self._entity_id: int | None = None
        self._x = 0.0
        self._y = 0.0

    def draw(self):
        raise NotImplementedError 

    def update(self, time: float) -> bool:
        raise NotImplementedError

    def do_pre_round(self):
        # By default, entity stays alive
        return True

    def do_post_round(self) -> bool:
        # By default signify that the entity was destroyed
        return False

    def set_position(self, x: float, y: float):
        self._x = x
        self._y = y

    def get_position(self):
        return self._x, self._y

    def assign_entity_id(self, entity_id: int):
        if self._entity_id is None:
            self._entity_id = entity_id

    def get_entity_id(self) -> int | None:
        return self._entity_id

    def get_entity_type(self) -> str:
        return self.__class__.__name__.lower()

    def get_render_state(self):
        return None

    def build_network_snapshot(self):
        from .networkstate import EntitySnapshot

        return EntitySnapshot(
            entity_id=-1 if self._entity_id is None else self._entity_id,
            entity_type=self.get_entity_type(),
            position=self.get_position(),
            payload={},
        )

    def texture(self, texture_number: int):
        if self._game.get_interface():
            self._game.get_interface().set_texture(texture_number)

    def get_graphics(self):
        return self._game.get_graphics()

    def get_visual_renderer(self):
        return self._game.get_visual_renderer()
