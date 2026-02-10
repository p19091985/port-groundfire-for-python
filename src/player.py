from typing import TYPE_CHECKING, List
from .tank import Tank

if TYPE_CHECKING:
    from .game import Game

class Player:
    # Commands
    CMD_FIRE = 0
    CMD_WEAPONUP = 1
    CMD_WEAPONDOWN = 2
    CMD_JUMPJETS = 3
    CMD_SHIELD = 4
    CMD_TANKLEFT = 5
    CMD_TANKRIGHT = 6
    CMD_GUNLEFT = 7
    CMD_GUNRIGHT = 8
    CMD_GUNUP = 9
    CMD_GUNDOWN = 10

    def __init__(self, game: 'Game', number: int, name: str, colour: tuple):
        self._game = game
        self._number = number
        self._name = name
        self._colour = colour
        self._score = 0
        self._rounds_won = 0
        self._defeated_players = []
        self._money = 0
        self._leader = False
        
        self._tank = Tank(game, self, number)
        
    
    def get_tank(self) -> Tank:
        return self._tank
    
    def get_controller(self) -> int:
        return -1
        
    def get_command(self, command: int, start_time_ref: List[float]) -> bool:
        return False

    def record_shot(self, x: float, y: float, hit_tank: int):
        pass

    def record_fired(self):
        pass

    def new_round(self):
        self._defeated_players = []

    def end_round(self):
        self._tank.do_post_round()
        
        for defeated_player in self._defeated_players:
            if defeated_player == self:
                # Suicide
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
        # Base player update — override in subclasses for AI/human input
        # C++: virtual void update() — does NOT call tank.update()
        pass

    def defeat(self, dead_player: 'Player'):
        self._defeated_players.append(dead_player)

    def set_name(self, name: str):
        self._name = name

    def get_name(self) -> str:
        return self._name
        
    def get_score(self) -> int: return self._score
    def get_money(self) -> int: return self._money
    def set_money(self, money: int): self._money = money
    def set_leader(self, leader: bool): self._leader = leader
    def is_leader(self) -> bool: return self._leader
    def is_computer(self) -> bool: return False
    
    def add_defeated_player(self, p): self._defeated_players.append(p)
    def get_defeated_players(self): return self._defeated_players
