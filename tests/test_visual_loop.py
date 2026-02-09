
import pygame
import os
import sys

# Hack to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game import Game
from src.interface import Interface
from src.tank import Tank
from src.landscape import Landscape

def test_visual_tank():
    print("Initializing Visual Verification Loop...")
    
    # 1. Setup Headless-ish Game (using Dummy Interface if possible, or SDL videodriver dummy)
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    
    # Set window size
    w, h = 800, 600
    screen = pygame.display.set_mode((w, h))
    
    # 2. Initialize Game manually
    game = Game()
    # Mock Interface to use our screen?
    # Game creates its own Interface.
    # But since we set SDL_VIDEODRIVER=dummy, it created a dummy window.
    # We can access it via pygame.display.mn.surface? No, game.interface._window
    
    interface = game.get_interface()
    
    # 3. Add Player with DISTINCT Color
    # Red for P1
    game.add_player(0, "TestPlayer1", (255, 0, 0)) # Red
    p1 = game.get_players()[0]
    
    # 4. Generate Flat Terrain (or simple).
    # We can't easily force flat terrain without modding code, 
    # but we can place Tank at a known X where we check height.
    landscape = game.get_landscape()
    
    # 5. Place Tank
    tank = p1.get_tank()
    x_pos = 0.0
    tank.set_position_on_ground(x_pos) # Should set Y to ground level
    
    # 6. Render Frame
    game._draw_round()
    
    # 7. Analyze
    # Tank is at x=0.0.
    # Convert Game 0.0 to Screen coords.
    # game_to_screen(0.0, y)
    
    sx, sy = interface.game_to_screen(tank._x, tank._y)
    
    print(f"Tank Physics Pos: ({tank._x}, {tank._y})")
    print(f"Tank Logic Angle: {tank._tank_angle}")
    print(f"Tank Screen Pivot: ({sx}, {sy})")
    
    # We expect the Tank BODY to be drawn slightly ABOVE sy.
    # Because of +0.3 offset.
    # +0.3 in Game Y means HIGHER (smaller Screen Y if Y-up, wait).
    # Interface: sy = H - (y - off)*scale.
    # So Game Y+ goes Screen Y- (Up).
    # So tank should be drawn at sy_visual < sy_physics.
    
    # Check pixels around cx, cy.
    # We expect RED pixels (255, 0, 0).
    
    # We'll scan a small area around expected visual center.
    visual_y_game = tank._y + 0.3 + (tank._tank_size * 0.5)
    vx, vy = interface.game_to_screen(tank._x, visual_y_game)
    print(f"Expected Visual Center: ({vx}, {vy})")
    
    # Capture surface
    surf = interface._window
    
    red_found = False
    
    # Scan central area
    for dy in range(-10, 10):
        for dx in range(-10, 10):
            try:
                col = surf.get_at((vx + dx, vy + dy))
                if col.r > 200 and col.g < 50:
                    red_found = True
            except IndexError:
                pass

    if red_found:
        print("[SUCCESS] Red Tank Pixels Found!")
    else:
        print("[FAILURE] No Red Pixels found at visual center.")
        # Debug dump
        pygame.image.save(surf, "debug_failure.png")
        
    # Check Clipping
    # The bottom of the tank (visual) should be at game y = tank._y + 0.3.
    # The ground is at game y = tank._y.
    # Screen Y for Tank Bottom:
    bx, by_tank_bottom = interface.game_to_screen(tank._x, tank._y + 0.3)
    
    # Screen Y for Ground:
    gx, gy_ground = interface.game_to_screen(tank._x, tank._y)
    
    print(f"Screen Y Tank Bottom: {by_tank_bottom}")
    print(f"Screen Y Ground: {gy_ground}")
    
    # Since Y is inverted in screen (0 is top), higher Game Y = smaller Screen Y.
    # tank._y + 0.3 > tank._y.
    # So by_tank_bottom < gy_ground.
    # Tank pixels should start at by_tank_bottom and go UP (smaller Y).
    # Ground pixels should be at gy_ground (and below?).
    # So Tank should be strictly ABOVE Ground.
    if by_tank_bottom < gy_ground:
        print("[SUCCESS] Tank Visual Bottom is vertically ABOVE Ground Physics Level.")
    else:
        print("[FAILURE] Tank Visual Bottom is BELOW Ground Level (Clipping).")
        
    # Verify ACTUAL pixels
    # Check pixel at (bx, by_tank_bottom - 2). Should be RED.
    # Check pixel at (gx, gy_ground + 2). Should be GROUND COLOR (Green/Yellow).
    
    p_tank = surf.get_at((int(bx), int(by_tank_bottom) - 2))
    p_ground = surf.get_at((int(gx), int(gy_ground) + 2))
    
    print(f"Pixel at Tank Bottom-2: {p_tank}")
    print(f"Pixel at Ground+2: {p_ground}")
    
    if p_tank.r > 200:
        print("[SUCCESS] Visual Tank confirmed at correct height.")
    else:
        print("[FAILURE] Visual Tank NOT found where expected.")

if __name__ == "__main__":
    test_visual_tank()
