
import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game import Game
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()

class TestGravityStart(unittest.TestCase):
    def test_gravity_during_start(self):
        game = Game()
        game.add_player(0, "P1", (255,0,0))
        game.set_num_of_rounds(1)
        game._change_state(Game.GameState.ROUND_STARTING)
        
        p1 = game._players[0]
        tank = p1.get_tank()
        
        # Initial pos (should be high)
        x_start, y_start = tank.get_position()
        self.assertAlmostEqual(y_start, 10.0)
        
        # Run 10 frames
        for _ in range(10):
            game.loop_once()
            
        x_new, y_new = tank.get_position()
        print(f"Start Y: {y_start}, End Y: {y_new}")
        
        # Should have fallen
        self.assertLess(y_new, y_start, "Tank did not fall during ROUND_STARTING!")
        
if __name__ == '__main__':
    unittest.main()
