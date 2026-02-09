import math

# Constants
PI = 3.141592654

class GameState:
    CURRENT_STATE = 0
    MAIN_MENU = 1
    OPTION_MENU = 2
    CONTROLLERS_MENU = 3
    SET_CONTROLS_MENU = 4
    QUIT_MENU = 5
    SELECT_PLAYERS_MENU = 6
    ROUND_STARTING = 7
    ROUND_IN_ACTION = 8
    ROUND_FINISHING = 9
    PAUSE_MENU = 10
    ROUND_SCORE = 11
    SHOP_MENU = 12
    WINNER_MENU = 13
    EXITED = 14

def sqr(x: float) -> float:
    """
    x^2
    """
    return x * x

def deg_cos(angle: float) -> float:
    """
    Takes an angle in degrees and returns the cosine
    """
    return math.cos((angle / 180.0) * PI)

def deg_sin(angle: float) -> float:
    """
    Takes an angle in degrees and returns the sine
    """
    return math.sin((angle / 180.0) * PI)
