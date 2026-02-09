
import unittest
import sys
import os
import pygame

# Adjust path to find src
sys.path.append(os.getcwd())

from src.game import Game
from tests.test_full_suite import MockInterface, MockSound, MockControls
from src.humanplayer import HumanPlayer

class TestVisualMatch(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game._interface = MockInterface()
        self.game._sound = MockSound()
        self.game._number_of_players = 1
        self.game._players[0] = HumanPlayer(self.game, 0, "P1", (255,0,0), 0, MockControls())
        self.game._landscape.generate_terrain()
        
    def test_screenshot_generation(self):
        """Generates a screenshot of the game state for manual inspection."""
        # Use real surface for screenshot if possible, but MockInterface uses dummy?
        # MockInterface in test_full_suite keeps a surface.
        
        # Force a draw
        self.game._draw_round()
        
        # Save
        if hasattr(self.game._interface, '_window'):
             pygame.image.save(self.game._interface._window, "test_visual_match.png")
             print("Saved test_visual_match.png")
             self.assertTrue(os.path.exists("test_visual_match.png"))
             
if __name__ == '__main__':
    unittest.main()
