from typing import TYPE_CHECKING, List, Optional

from .commandintents import PlayerCommand, PlayerIntentFrame, PlayerIntentQueue
from .tank import Tank

if TYPE_CHECKING:
    from .game import Game


class Player:
    # Commands
    CMD_FIRE = int(PlayerCommand.FIRE)
    CMD_WEAPONUP = int(PlayerCommand.WEAPONUP)
    CMD_WEAPONDOWN = int(PlayerCommand.WEAPONDOWN)
    CMD_JUMPJETS = int(PlayerCommand.JUMPJETS)
    CMD_SHIELD = int(PlayerCommand.SHIELD)
    CMD_TANKLEFT = int(PlayerCommand.TANKLEFT)
    CMD_TANKRIGHT = int(PlayerCommand.TANKRIGHT)
    CMD_GUNLEFT = int(PlayerCommand.GUNLEFT)
    CMD_GUNRIGHT = int(PlayerCommand.GUNRIGHT)
    CMD_GUNUP = int(PlayerCommand.GUNUP)
    CMD_GUNDOWN = int(PlayerCommand.GUNDOWN)

    def __init__(self, game: "Game", number: int, name: str, colour: tuple):
        self._game = game
        self._number = number
        self._name = name
        self._colour = colour
        self._score = 0
        self._rounds_won = 0
        self._defeated_players = []
        self._money = 0
        self._leader = False
        self._intent_queue = PlayerIntentQueue()
        self._current_intents = PlayerIntentFrame.empty(source="init")

        self._tank = Tank(game, self, number)

    def get_tank(self) -> Tank:
        return self._tank

    def get_controller(self) -> int:
        return -1

    def get_command(self, command: int, start_time_ref: Optional[List[float]] = None) -> bool:
        if start_time_ref and len(start_time_ref) > 0:
            start_time_ref[0] = self._current_intents.simulation_time
        return self._current_intents.is_pressed(command)

    def record_shot(self, x: float, y: float, hit_tank: int):
        pass

    def record_fired(self):
        pass

    def new_round(self):
        self._defeated_players = []
        self.publish_intents(PlayerIntentFrame.empty(source="round_reset", simulation_time=self._get_simulation_time()))

    def end_round(self):
        for defeated_player in self._defeated_players:
            if defeated_player == self:
                self._score -= 50
            elif defeated_player._leader:
                self._score += 200
                self._money += 50
            else:
                self._score += 100
                self._money += 50

        if self._tank.alive():
            self._score += 100
            self._money += 25

        self._money += 10

    def update(self, time: float = 0.0):
        self.publish_intents(PlayerIntentFrame.empty(source="player", simulation_time=self._get_simulation_time()))

    def publish_intents(self, frame: PlayerIntentFrame):
        self._current_intents = frame
        self._intent_queue.publish(frame)

    def get_current_intents(self) -> PlayerIntentFrame:
        return self._current_intents

    def drain_intent_frames(self) -> tuple[PlayerIntentFrame, ...]:
        return self._intent_queue.drain()

    def defeat(self, dead_player: "Player"):
        self._defeated_players.append(dead_player)

    def set_name(self, name: str):
        self._name = name

    def get_name(self) -> str:
        return self._name

    def get_score(self) -> int:
        return self._score

    def get_money(self) -> int:
        return self._money

    def set_money(self, money: int):
        self._money = money

    def set_leader(self, leader: bool):
        self._leader = leader

    def is_leader(self) -> bool:
        return self._leader

    def is_computer(self) -> bool:
        return False

    def add_defeated_player(self, p):
        self._defeated_players.append(p)

    def get_defeated_players(self):
        return self._defeated_players

    def _get_simulation_time(self) -> float:
        if hasattr(self._game, "get_time"):
            return self._game.get_time()
        return 0.0
