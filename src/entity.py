from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game

class Entity:
    def __init__(self, game: 'Game'):
        self._game = game
        self._x = 0.0
        self._y = 0.0

    def draw(self):
        raise NotImplementedError 

    def update(self, time: float) -> bool:
        raise NotImplementedError

    def do_pre_round(self):
        # By default do nothing
        pass

    def do_post_round(self) -> bool:
        # By default signify that the entity was destroyed
        return False

    def set_position(self, x: float, y: float):
        self._x = x
        self._y = y

    def get_position(self):
        return self._x, self._y

    def texture(self, texture_number: int):
        if self._game.get_interface():
            self._game.get_interface().set_texture(texture_number)
