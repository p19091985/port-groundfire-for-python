#!/usr/bin/env python3
import sys
import os

# Ensure src is in path if running from root
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.game import Game, GameError
from src.report import report

def main():
    try:
        report("Starting Groundfire Python Port...")
        
        # Determine base path
        # If running as script, data should be relative to current dir usually
        # but let's just assume CWD is correct as per standard run.
        
        game = Game()
        
        report("Game Initialized. Entering Main Loop.")
        
        running = True
        while running:
             running = game.loop_once()
             
        report("Game Finished normally.")
        
    except GameError as e:
        report(f"FATAL ERROR: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        report("Interrupted by User.")
        sys.exit(0)
    except Exception as e:
        report(f"UNHANDLED EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

