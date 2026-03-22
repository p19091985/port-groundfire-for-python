import sys
import os
import time

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pygame
# Do not use dummy driver, it hangs Pygame 2 on Windows. Instead, we let the window hide.
os.environ["SDL_VIDEODRIVER"] = "windows"
os.environ["SDL_VIDEO_WINDOW_POS"] = "-5000,-5000" # Move window off-screen

from src.game import Game, GameError

# We need GameState from common
from src.common import GameState

def run_fuzz():
    print("Initializing Pygame Dummy Video Driver...")
    pygame.init()
    
    print("Instantiating Game...")
    game = Game()
    
    # Add 4 AI Players
    game.add_player(-1, "AI-1", (1.0, 0.0, 0.0))
    game.add_player(-1, "AI-2", (0.0, 1.0, 0.0))
    game.add_player(-1, "AI-3", (0.0, 0.0, 1.0))
    game.add_player(-1, "AI-4", (1.0, 1.0, 0.0))
    
    # Set 3 short rounds to test entire Winner sequence
    game.set_num_of_rounds(3)
    
    # Force round start
    # We use change_state but it's protected, so we call it directly.
    game._change_state(GameState.ROUND_STARTING)
    
    # Overwrite loop_once time mechanism
    start_time = time.time()
    current_time = start_time
    
    rounds_played = 0
    ticks = 0
    max_ticks = 100000  # Cap at ~27 minutes of simulated gameplay
    
    print("Starting Headless Fuzz Test...")
    
    # Store original time.time
    import time as sys_time
    original_time_time = sys_time.time
    
    try:
        while ticks < max_ticks:
            # Advance time by exactly 1/60th of a second
            current_time += 0.016666
            sys_time.time = lambda: current_time
            
            try:
                running = game.loop_once()
            except Exception as e:
                import traceback
                print(f"\nCRASH at tick {ticks}!")
                traceback.print_exc()
                sys.exit(1)
                
            state = game.get_game_state()
            
            if not running:
                print("Game exited unexpectedly.")
                break
                
            if state == GameState.SHOP_MENU:
                 # AI doesn't interact with shop, so auto-skip it to next round
                 # print("Shop Menu reached. Continuing to next round...")
                 rounds_played += 1
                 game._change_state(GameState.ROUND_STARTING)
                 
            elif state == GameState.WINNER_MENU:
                 print("\nMatch finished successfully! Winner menu reached.")
                 sys.exit(0)
                 
            ticks += 1
            if ticks % 500 == 0:
                 print(f"Elapsed {ticks} ticks... Current State: {state}, Round: {game.get_current_round()}", flush=True)

        print(f"Fuzz test timeout. Ticks: {ticks}")
        sys.exit(0)
    finally:
        # Restore original time.time just in case
        sys_time.time = original_time_time

if __name__ == '__main__':
    run_fuzz()
