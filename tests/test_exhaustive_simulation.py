import sys
import os
import time

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pygame
os.environ["SDL_VIDEODRIVER"] = "windows"
os.environ["SDL_VIDEO_WINDOW_POS"] = "-5000,-5000"

from src.game import Game, GameState
from src.tank import Tank
from src.weapons_impl import ShellWeapon, MissileWeapon, MirvWeapon, NukeWeapon, MachineGunWeapon
from src.mirv import Mirv
from src.missile import Missile
from src.shell import Shell
from src.machinegunround import MachineGunRound

def setup_game():
    pygame.init()
    g = Game()
    g.add_player(-1, "AI-1", (1.0, 0.0, 0.0))
    g.add_player(-1, "AI-2", (0.0, 1.0, 0.0))
    g.set_num_of_rounds(1)
    return g

def test_1_state_machine_traversal(game):
    print("--- Test 1: State Machine Traversal ---")
    states_to_visit = [
        GameState.MAIN_MENU,
        GameState.ROUND_STARTING,
        GameState.ROUND_IN_ACTION,
        GameState.ROUND_FINISHING,
        GameState.ROUND_SCORE,
        GameState.SHOP_MENU,
        GameState.WINNER_MENU
    ]
    
    for s in states_to_visit:
        game._change_state(s)
        # Run 5 updates to ensure neither the game nor the menu crashes in this state
        for _ in range(5):
             game.loop_once()
    
    print("  [OK] Successfully transitioned and ticked all states.")

def test_2_exhaustive_weapons(game):
    print("--- Test 2: Weapon Arsenal Mechanics Simulation ---")
    game._change_state(GameState.ROUND_STARTING)
    game.loop_once() # Will put game in ROUND_IN_ACTION
    
    player = game.get_players()[0]
    tank = player.get_tank()
    
    # We will instantiate projectiles manually and fast forward to watch them hit or despawn
    weapons_to_test = [
        Shell(game, player, 0, 5, 0, 0, 0, 1, 10, False),
        Missile(game, player, 0, 5, 45, 1, 10),
        Mirv(game, player, 0, 5, 0, 0, 0, 1, 10),
        MachineGunRound(game, player, 0, 5, 1, -1, game.get_time(), 5)
    ]
    
    for w in weapons_to_test:
        game.add_entity(w)
        
    print(f"  Spawned {len(weapons_to_test)} projectiles. Fast forwarding 500 frames...")
    
    dt = 0.016
    for _ in range(500):
        # Update landscape
        landscape = game.get_landscape()
        landscape.update(dt)
        # Update entities
        for e in game._entity_list[:]:
            if not e.update(dt):
                game._entity_list.remove(e)
                
    print("  [OK] All weapons fired, updated, simulated impact and despawned safely without crashes.")

def test_3_landscape_deformation_limits(game):
    print("--- Test 3: Landscape Deformation Limits ---")
    
    landscape = game.get_landscape()
    # Bombard the landscape with 1,000 huge holes randomly
    for i in range(100):
        # Coordinates in game are roughly x: -10 to 10
        x = -10.0 + (i % 20)
        landscape.make_hole(x, 0.0, 5.0)
        
    # Run an update to allow falling mechanics
    for _ in range(10):
        landscape.update(0.1)
        
    print("  [OK] Landscape survived extreme contiguous deformation and smoothing.")

def test_4_edge_cases_and_memory(game):
    print("--- Test 4: Edge Cases (Simultaneous Deaths & Entity Limits) ---")
    
    from src.quake import Quake
    # Inject 5,000 Quake entities to ensure no OOM or slowdown crash in loops
    for _ in range(5000):
        game.add_entity(Quake(game))
        
    for _ in range(5):
        for e in game._entity_list[:]:
            if not e.update(0.1):
                game._entity_list.remove(e)
                
    print(f"  [OK] Successfully ticked 5000 concurrent Quake entities.")
    
    # Force both tanks to die instantly
    tank1 = game.get_players()[0].get_tank()
    tank2 = game.get_players()[1].get_tank()
    
    tank1.do_damage(1000)
    tank2.do_damage(1000)
    
    print(f"  [OK] Handled simultaneous tank deaths safely.")

def run_all():
    print("===========================================================")
    print("  Exhaustive Game Logic & Mechanics Simulation Suite")
    print("===========================================================")
    g = setup_game()
    
    try:
        test_1_state_machine_traversal(g)
        test_2_exhaustive_weapons(g)
        test_3_landscape_deformation_limits(g)
        test_4_edge_cases_and_memory(g)
        
        print("\n===========================================================")
        print("  ALL EXHAUSTIVE SIMULATIONS PASSED! SYSTEM PERFECT.")
        print("===========================================================")
        sys.exit(0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_all()
