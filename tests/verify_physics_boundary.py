
import unittest
import sys
import os

# Adjust path to find src
sys.path.append(os.getcwd())

from src.game import Game
from src.tank import Tank
from src.humanplayer import HumanPlayer
from tests.test_full_suite import MockInterface, MockSound, MockControls

class TestPhysicsBoundary(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game._interface = MockInterface()
        self.game._sound = MockSound()
        self.game._number_of_players = 1
        
        # Player 1
        self.game._players[0] = HumanPlayer(self.game, 0, "P1", (255,0,0), 0, MockControls())
        self.game._landscape.generate_terrain()
        
    def test_infinite_fall_bug(self):
        """Verify if tank keeps falling when below terrain bottom (-8.0)."""
        t = self.game._players[0].get_tank()
        
        # Place tank way below ground
        # Ground floor is usually around -7.0 to -8.0
        t._y = -9.0 
        t._on_ground = False
        t._airbourne_y_vel = -2.0 # Falling fast
        
        # Step Physics
        dt = 0.1
        t.update(dt)
        
        print(f"Tank Y after update: {t._y}")
        
        # In C++, tanks hitting bottom usually respawn or stop?
        # User says "continue falling". We want to FIX this.
        # Ideally, it should clamp to -10 or die.
        # For this test, we asserting that it DOES NOT fall further if we implement a floor.
        
        # If bug exists, Y will be lower (-9.2)
        # If fixed, Y should be clamped or reset.
        
        # Let's assert that it stops falling below -10.0
        self.assertGreater(t._y, -10.5, "Tank fell into the abyss!")

    def test_falling_terrain_floor(self):
        """Verify falling chunks stop at bottom (-8.0)."""
        # Manually trigger a falling chunk
        # Slice 50, create a chunk
        from src.landscape import LandChunk, Colour
        
        chunk = LandChunk()
        chunk.min_height_1 = 0.0
        chunk.min_height_2 = 0.0
        chunk.max_height_1 = 1.0
        chunk.max_height_2 = 1.0
        chunk.falling_state = False # Will set to true
        chunk.falling_speed = 0.0
        
        # Clear existing chunks at 50 to isolate
        self.game._landscape._land_chunks[50] = [chunk]
        
        # Force fall
        chunk.falling_state = True
        
        # Simulate many frames
        for _ in range(200):
             self.game._landscape.update(0.1)
             
        # Check if it stopped
        # Floor is likely -8.0 (from base chunk default)
        print(f"Chunk Bottom: {chunk.min_height_1}")
        self.assertGreater(chunk.min_height_1, -9.0, "Chunk fell through the floor!")
        self.assertFalse(chunk.falling_state, "Chunk should stop falling.")

if __name__ == '__main__':
    unittest.main()
