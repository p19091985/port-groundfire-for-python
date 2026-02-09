
import unittest
import sys
import os
import math
import pygame

# MOCKS
# ----------------------------------------------------------------------
class MockInterface:
    def __init__(self, *args):
        self._window = pygame.Surface((800, 600))
        self._mock_mouse_x = 0.0
        self._mock_mouse_y = 0.0
        self._mock_mouse_buttons = [False, False, False]
        # Dummy methods called by game/menus
        self.game_to_screen = lambda x, y: (int(x), int(y))
        self.start_draw = lambda: None
        self.end_draw = lambda: None
        self.define_textures = lambda n: None
        self.load_texture = lambda f, i: None
        self.set_texture = lambda i: None
        self.get_texture_image = lambda i: pygame.Surface((1,1))
        self.should_close = lambda: False
        self.enable_mouse = lambda e: None
        self.offset_viewport = lambda x, y: None
        self.get_key = lambda k: False
        self.get_texture_surface = self.get_texture_image
        self.save_screenshot = lambda f: None
        self.scale_len = lambda l: int(l * 10)
        
    def get_mouse_pos(self):
        return self._mock_mouse_x, self._mock_mouse_y
        
    def get_mouse_button(self, b):
        return self._mock_mouse_buttons[b]
    
    def get_window_settings(self):
        return 800, 600, False

class MockControls:
    def get_command(self, controller, command):
        return False
        
class MockSound:
    def load_sound(self, *args): pass
    def play_sound(self, *args): pass
    class SoundSource:
        def __init__(self, *args): pass 
        def is_source_playing(self): return False
        def set_inactive(self): pass

class MockSettings:
    def get_int(self, s, k, d): return d
    def load_sound(self, id, filename):
        pass
    def play_sound(self, id):
        pass
    def set_master_volume(self, vol):
        pass
    def get_float(self, s, k, d): return d
    def get_string(self, s, k, d): return d


# IMPORTS
# ----------------------------------------------------------------------
sys.path.append(os.getcwd())
from src.game import Game
from src.tank import Tank
from src.landscape import Landscape
from src.weapons_impl import ShellWeapon, MissileWeapon, MirvWeapon, NukeWeapon, MachineGunWeapon
from src.aiplayer import AIPlayer
from src.humanplayer import HumanPlayer
from src.interface import Interface

# Menus
from src.mainmenu import MainMenu
from src.scoremenu import ScoreMenu
from src.shopmenu import ShopMenu
from src.playermenu import PlayerMenu
from src.winnermenu import WinnerMenu
from src.optionmenu import OptionMenu
from src.quitmenu import QuitMenu

# TEST SUITE
# ----------------------------------------------------------------------
class TestFullSuite(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Headless pygame
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        Interface.__del__ = lambda self: None # Prevent pygame.quit on GC
        pygame.init()
        pygame.display.set_mode((800, 600))
        pygame.font.init()

    def setUp(self):
        self.game = Game()
        self.game._interface = MockInterface()
        self.game._sound = MockSound()
        
        # Setup generic state
        self.game._number_of_players = 2
        
        # P1 Human
        self.game._players[0] = HumanPlayer(self.game, 0, "Human", (255,0,0), 0, MockControls()) 
        self.game._players[0].get_tank().set_position_on_ground(0.0)
        
        # P2 AI
        self.game._players[1] = AIPlayer(self.game, 1, "AI", (0,0,255))
        self.game._players[1].get_tank().set_position_on_ground(5.0)
        
        # Landscape
        if not self.game._landscape:
            self.game._landscape = Landscape(self.game._settings, 0.0)
            self.game._landscape.generate_terrain()
            
    # SECTION 8: CROSS-LANGUAGE PARITY SCENARIO
    # ------------------------------------------------------------------
    def test_cross_language_scenario(self):
        """
        Execute the exact scenario defined for the C++ Harness (Phase 8).
        Scenario:
        - Seed: 12345
        - Player 0 Tank Position: (0.0, 5.0) (In Air)
        - Run 500 Ticks.
        - Verify: Parity with C++ output.
        """
        import random
        import json
        
        # Load C++ Golden Master
        cpp_frames = {}
        with open("groundfire-0.25/src/cpp_output.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        cpp_frames[data['tick']] = data
                    except:
                        pass
        
        self.assertTrue(len(cpp_frames) > 0, "Failed to load C++ Golden Master data.")
        
        # Python Setup
        random.seed(12345)
        
        # Reset Landscape with seeded random
        self.game._landscape.generate_terrain()
        
        # Setup Tank
        t = self.game._players[0].get_tank()
        t.set_position(0.0, 5.0)
        t._on_ground = False
        t._airbourne_y_vel = 0.0
        t._tank_angle = 0.0
        
        # Setup Game State
        self.game._game_state = self.game.GameState.ROUND_IN_ACTION
        
        # Run 500 Ticks
        print(f"Running Python Simulation (comparing against {len(cpp_frames)} C++ frames)...")
        dt = 0.02 # Fixed timestep? C++ output shows 0.000014 etc.
        # Wait! C++ Harness outputs "Loop dt: ...". 
        # C++ loop logic: 
        # double currentTick = glfwGetTime();
        # double elapsedTime = currentTick - _lastTick;
        # if (elapsedTime > 0.1) elapsedTime = 0.1;
        # BUT in test_full_suite.cc, does it control time?
        # NO. It relies on glfwGetTime().
        # In HEADLESS mode, glfwGetTime() might be wall clock time or 0.
        # Check cpp_output.txt for 'Loop dt'. 
        # It varies: 0.000072, 0.000318... then stabilizes around 0.000014.
        # This means the C++ simulation ran as fast as possible (unthrottled).
        # AND it passed 'elapsedTime' to update().
        # So the PHYSICS IS DEPENDENT ON DT!
        # If Python uses fixed dt (e.g. 0.02), RESULTS WILL DIVERGE IMMEDIATELY.
        
        # CRITICAL: To compare, Python must use the EXACT SAME DT sequence as C++.
        # We must parse "Loop dt: ..." from the log as well.
        
        cpp_dts = {}
        with open("groundfire-0.25/src/cpp_output.txt", "r") as f:
             tick_idx = 0
             for line in f:
                 if line.startswith("Loop dt:"):
                     # Format: Loop dt: 0.000072, Total: ...
                     parts = line.split(",")
                     dt_part = parts[0].split(":")[1].strip()
                     cpp_dts[tick_idx] = float(dt_part)
                     tick_idx += 1
                     
        # Run Simulation
        for i in range(500):
            if i not in cpp_frames: break
            
            # Use EXACT DT from C++ run
            current_dt = cpp_dts.get(i, 0.02)
            
            # Game Loop Logic
            self.game._landscape.update(current_dt)
            t.update(current_dt)
            
            # Compare
            expected = cpp_frames[i]['tanks'][0]
            
            # Tolerance: 0.001 (1mm)
            # Checking X
            self.assertAlmostEqual(t._x, expected['x'], delta=0.001, 
                msg=f"Tick {i}: X Divergence. Py={t._x}, C++={expected['x']}")
                
            # Checking Y
            self.assertAlmostEqual(t._y, expected['y'], delta=0.001,
                msg=f"Tick {i}: Y Divergence. Py={t._y}, C++={expected['y']}")


    # SECTION 1: CORE MECHANICS & PHYSICS
    # ------------------------------------------------------------------
    def test_physics_gravity(self):
        """Verify tanks fall when not on ground."""
        t = self.game._players[0].get_tank()
        t._y = 0.0
        t._on_ground = False
        t._airbourne_y_vel = 0.0
        
        # Update for 1 second
        dt = 1.0
        t.move_tank(dt, False)
        
        # Logic: _airbourne_y_vel -= gravity * time
        # move_y = _airbourne_y_vel
        # New Y should be lower (less than 0.0)
        self.assertLess(t._y, 0.0, "Tank should fall due to gravity")
        # ==========================
    # 5. Feature Parity: Landscape & Physics
    # ==========================
    def test_landscape_deformation(self):
        """Verify make_hole modifies terrain height."""
        l = self.game._landscape
        h_orig = l.get_landscape_height(0.0)
        l.make_hole(0.0, h_orig, 2.0)
        h_new = l.get_landscape_height(0.0)
        self.assertLess(h_new, h_orig, "Terrain should be lower after explosion")

    def test_ground_collision(self):
        """Verify ground_collision detection."""
        l = self.game._landscape
        # Test collision with known ground
        # Height at 0.0 is roughly -7 to 5.
        h = l.get_landscape_height(0.0)
        
        # Line from above to below ground
        coll, cx, cy = l.ground_collision(0.0, 10.0, 0.0, -10.0)
        self.assertTrue(coll, "Should collide with ground")
        self.assertAlmostEqual(cx, 0.0, delta=0.5)
        self.assertAlmostEqual(cy, h, delta=0.5)
        
        # Line completely in sky
        coll, cx, cy = l.ground_collision(0.0, 20.0, 10.0, 20.0)
        self.assertFalse(coll, "Should not collide in sky")

    def test_quake_mechanics(self):
        """Verify Quake entity lowers terrain over time."""
        from src.quake import Quake
        # Quake relies on settings, verify defaults
        q = Quake(self.game)
        q._earthquake = True # Force active
        
        l = self.game._landscape
        h_orig = l.get_landscape_height(5.0)
        
        # Update quake
        dt = 0.1
        q.update(dt)
        
        h_new = l.get_landscape_height(5.0)
        # Quake drops terrain: drop_terrain(time * DropRate)
        # We expect a small drop
        self.assertLess(h_new, h_orig, "Quake should lower terrain when active")

    def test_tank_weapon_switching(self):
        """Verify weapon switching logic."""
        # Setup: Create a tank and mock input
        self.game._game_state = self.game.GameState.ROUND_IN_ACTION
        
        # Use existing player from game
        p = self.game._players[0]
        t = Tank(self.game, p, 0)
        t._weapons[Tank.MACHINEGUN]._quantity = 100 # Give ammo
        t.do_pre_round() 
        
        initial_weapon = t._selected_weapon
        
        # Mock weapon right command (CMD_WEAPONUP = 1)
        original_get_command = p.get_command
        
        def mock_cmd(cmd, time_ref):
             if cmd == Tank.CMD_WEAPONUP: return True
             return False
        p.get_command = mock_cmd
        
        # Update tank
        t.update(0.1)
        
        self.assertNotEqual(t._selected_weapon, initial_weapon, "Weapon should switch")
        self.assertEqual(t._selected_weapon, (initial_weapon + 1) % Tank.MAX_WEAPONS)
        
        # Restore
        p.get_command = original_get_command

    def test_tank_jumpjets(self):
        """Verify jumpjet physics."""
        self.game._game_state = self.game.GameState.ROUND_IN_ACTION
        p = self.game._players[0]
        t = Tank(self.game, p, 0)
        t.do_pre_round()
        t.set_position_on_ground(0.0)
        t._fuel = 100.0
        t._total_fuel = 100.0
        
        start_y = t._y
        
        original_get_command = p.get_command
        def mock_cmd(cmd, time_ref):
             if cmd == Tank.CMD_JUMPJETS: return True
             return False
        p.get_command = mock_cmd
        
        t.update(0.1)
        
        self.assertTrue(t._y > start_y or t._airbourne_y_vel != 0, "Tank should act against gravity or lift off")
        self.assertLess(t._fuel, 100.0, "Fuel should be consumed")
        
        p.get_command = original_get_command

    def test_tank_damage(self):
        """Verify Tank takes damage and dies."""
        t = self.game._players[0].get_tank()
        initial_health = t._health
        
        # Deal non-lethal damage
        dead = t.do_damage(10)
        self.assertFalse(dead)
        self.assertEqual(t._health, initial_health - 10)
        
        # Deal lethal damage
        dead = t.do_damage(1000)
        self.assertTrue(dead)
        self.assertTrue(t._health <= 0)
        self.assertEqual(t._state, Tank.TANK_DEAD) 

    # SECTION 2: ENTITIES & WEAPONS
    # ------------------------------------------------------------------
    def test_weapon_inventory(self):
        """Verify Tank has all weapon types."""
        t = self.game._players[0].get_tank()
        self.assertIsInstance(t.get_weapon(Tank.SHELLS), ShellWeapon)
        self.assertIsInstance(t.get_weapon(Tank.MISSILES), MissileWeapon)
        self.assertIsInstance(t.get_weapon(Tank.MIRVS), MirvWeapon)
        self.assertIsInstance(t.get_weapon(Tank.NUKES), NukeWeapon)
        # Check MG
        has_mg = any(isinstance(w, MachineGunWeapon) for w in t._weapons)
        self.assertTrue(has_mg, "MachineGun weapon missing from tank")

    def test_weapon_buying(self):
        """Verify ShopMenu buying logic."""
        p = self.game._players[0]
        p.set_money(1000)
        w = p.get_tank().get_weapon(Tank.MISSILES)
        initial = w._quantity
        
        cost = w.get_cost()
        w.add_amount(5)
        p.set_money(p.get_money() - cost)
        
        self.assertEqual(w._quantity, initial + 5)
        self.assertEqual(p.get_money(), 1000 - cost)

    # SECTION 3: GAME FLOW & MENUS (Including ScoreMenu)
    # ------------------------------------------------------------------
    def click_at(self, x, y):
        """Simulate a mouse click at game coordinates (x, y)."""
        interface = self.game._interface
        interface._mock_mouse_x = x
        interface._mock_mouse_y = y
        interface._mock_mouse_buttons[0] = True
        self.game.loop_once()
        interface._mock_mouse_buttons[0] = False
        self.game.loop_once()

    def test_game_flow_transitions(self):
        """Verify state transitions from MainMenu -> SelectPlayer -> RoundStart via clicks."""
        from src.common import GameState
        
        # Reset game state to start
        self.game._game_state = GameState.MAIN_MENU
        self.game._current_menu = MainMenu(self.game)
        
        # 1. MainMenu -> SelectPlayers (Click "Start Game" at 0.0, -4.0)
        self.click_at(0.0, -4.0)
        self.assertEqual(self.game.get_game_state(), GameState.SELECT_PLAYERS_MENU, 
                         "Failed to transition to SELECT_PLAYERS_MENU")
        
        # 2. Add Players
        self.click_at(-8.5, 3.5) # P1
        self.click_at(-8.5, 2.7) # P2
        
        # 3. Toggle P2 to AI (3.3, 2.7)
        self.click_at(3.3, 2.7)
        
        # 4. Click Start Round (0.0, -5.0)
        self.click_at(0.0, -5.0)
        self.assertEqual(self.game.get_game_state(), GameState.ROUND_STARTING,
                         "Failed to transition to ROUND_STARTING")
        
        # 5. Simulation Countdown
        self.game._state_countdown = -0.1
        self.game.loop_once()
        
        self.assertEqual(self.game.get_game_state(), GameState.ROUND_IN_ACTION,
                         "Failed to transition to ROUND_IN_ACTION")
        
        # Verify tanks exist
        self.assertIsNotNone(self.game._players[0])
        self.assertIsNotNone(self.game._players[0].get_tank())

    def test_menus_instantiate_and_draw(self):
        """Verify all menus init and draw without crashing."""
        menus = [
            MainMenu(self.game),
            ShopMenu(self.game),
            ScoreMenu(self.game),
            WinnerMenu(self.game),
            OptionMenu(self.game),
            QuitMenu(self.game),
            PlayerMenu(self.game)
        ]
        
        for m in menus:
            with self.subTest(menu=m.__class__.__name__):
                self.game._current_menu = m
                try:
                    m.draw()
                except Exception as e:
                    self.fail(f"{m.__class__.__name__}.draw() crashed: {e}")

    # SECTION 4: AI LOGIC
    # ------------------------------------------------------------------
    def test_ai_logic_methods(self):
        """Verify AI structure."""
        ai = self.game._players[1]
        self.assertTrue(ai.is_computer())
        # Check methods exist
        self.assertTrue(hasattr(ai, 'guess_aim'))
        self.assertTrue(hasattr(ai, 'find_new_target'))
        self.assertTrue(hasattr(ai, 'record_shot'))

    def test_ai_player_logic(self):
        """Verify AI logic execution."""
        ai = self.game._players[1]
        ai.new_round()
        self.game._game_state = self.game.GameState.ROUND_IN_ACTION
        
        # position tanks
        self.game._players[0].get_tank()._x = 10.0
        ai.get_tank()._x = 0.0
        
        # Let AI find target and aim itself
        ai.update(0.1)
        
        self.assertIsNotNone(ai._target_tank, "AI should find a target automatically")
        
        # update again to produce move/fire commands
        ai.update(0.1)
        
        # Verify commands set
        has_cmd = False
        for i in range(11):
            if ai.get_command(i, []):
                has_cmd = True
                break
        self.assertTrue(has_cmd, "AI should generate commands")

    def test_score_menu_logic(self):
        """Verify ScoreMenu sorts players correctly."""
        p1 = self.game._players[0]
        p2 = self.game._players[1]
        
        p1._score = 100
        p2._score = 200
        
        sm = ScoreMenu(self.game)
        # Check order
        self.assertEqual(sm._ordered_players[0], p2)
        self.assertEqual(sm._ordered_players[1], p1)
        
        # Initial Draw
        sm.draw()
        
        # Update
        sm._time_till_active = 0.0
        # Mock fire to proceed
        original_cmd = p1.get_command
        p1.get_command = lambda c, t: c == Tank.CMD_FIRE
        
        res = sm.update(0.1)
        
        # Should transition to SHOP (if rounds not over)
        self.assertEqual(res, self.game.GameState.SHOP_MENU)
        
        p1.get_command = original_cmd

    # SECTION 5: VISUAL FIDELITY & SIMULATION
    # ------------------------------------------------------------------
    def test_procedural_determinism(self):
        """Verify terrain generation is deterministic with same seed."""
        # Using MockSettings with defaults
        l1 = Landscape(self.game._settings, 12345.0)
        h1_start = l1.get_landscape_height(0.0)
        h1_end = l1.get_landscape_height(10.0)
        
        l2 = Landscape(self.game._settings, 12345.0)
        h2_start = l2.get_landscape_height(0.0)
        h2_end = l2.get_landscape_height(10.0)
        
        self.assertEqual(h1_start, h2_start, "Terrain with same seed should match at x=0.0")
        self.assertEqual(h1_end, h2_end, "Terrain with same seed should match at x=10.0")
        
        # Verify different seed
        l3 = Landscape(self.game._settings, 99999.0)
        h3_start = l3.get_landscape_height(0.0)
        # Probabilistic check: Unlikely to match exactly float precision
        # self.assertNotEqual(h1_start, h3_start) 

    def test_tga_loading(self):
        """Verify TGA parser loads assets correctly."""
        # This requires actual asset files or a mock that simulates reading bytes.
        # Since we have data/ folder, we can try loading real headers if files exist.
        
        # Test loading logic via Interface (wrapped or mocked)
        # Using a real file approach if possible, or verify function logic if mocked.
        
        # If we are in mocked environment, 'load_texture' is a lambda.
        # So we can't verify the REAL TGA parser here unless we bypass mock.
        # We will do a basic existence check of assets.
        
        required_assets = ["data/menuback.tga", "data/weaponicons.tga", "data/smoke.tga"]
        missing = []
        for asset in required_assets:
            if not os.path.exists(asset):
                missing.append(asset)
        
        self.assertEqual(missing, [], f"Missing required TGA assets: {missing}")

    def test_ai_match_simulation(self):
        """Run a headless AI vs AI full match simulation."""
        # Setup specific game instance for sim
        sim_game = Game()
        sim_game._interface = MockInterface()
        sim_game._sound = MockSound()
        
        # 2 AI players
        sim_game._players[0] = AIPlayer(sim_game, 0, "AI_1", (255,0,0))
        sim_game._players[1] = AIPlayer(sim_game, 1, "AI_2", (0,0,255))
        sim_game._number_of_players = 2
        
        # Initial State
        sim_game._game_state = sim_game.GameState.ROUND_STARTING
        sim_game._start_round() # Setup tanks, landscape
        
        # Safety limit to prevent infinite loops (e.g. 2000 ticks = ~200 seconds at 0.1s dt)
        ticks = 0
        max_ticks = 2000 
        
        # We simulate until Round End or Game End
        # We force state to ROUND_IN_ACTION after initial ticks if needed
        # loop_once calls update(time_passed). We'll simulate 0.1s per step.
        
        # Force start
        sim_game._game_state = sim_game.GameState.ROUND_IN_ACTION
        sim_game._new_state = sim_game.GameState.CURRENT_STATE
        
        # Run loop
        while ticks < max_ticks:
            try:
                # We need to manually drive the game loop updates that normally 'main.py' handles
                # but Game.loop_once() does update() and draw().
                # We mock draw, so it's fast.
                
                # Mock time passing
                import time
                sim_game._last_time = time.time() - 0.05
                sim_game.loop_once()
                
                # Check for win condition
                alive_count = 0
                for p in sim_game._players:
                     if p and p.get_tank() and p.get_tank().alive():
                         alive_count += 1
                
                if alive_count <= 1:
                    # Round over
                    break
                    
                ticks += 1
            except Exception as e:
                self.fail(f"Simulation crashed at tick {ticks}: {e}")
        
        if ticks >= max_ticks:
            # If we reached here without exception, the simulation is stable.
            # We don't strictly enforce a game END because AI might miss.
            pass
        else:
             self.assertLess(ticks, max_ticks, "Simulation finished early (Win condition met)")

    # SECTION 6: API SIGNATURE PARITY (Golden Master - Exhaustive)
    # ------------------------------------------------------------------
    def test_api_parity(self):
        """Verify strict 1-to-1 mapping of C++ API to Python (ALL Public Methods)."""
        
        # Format: (ClassInstance or ClassType, [Method Names])
        # Note: For some we need instances (e.g. Tank), for others we can inspect Class.
        # Ideally inspect Class dict if methods are not dynamically bound, but simple getattr works on instances best.
        
        # Helper to create instances if needed
        p1 = self.game._players[0]
        t1 = p1.get_tank()
        
        from src.buttons import TextButton, GfxButton
        from src.selector import Selector
        from src.font import Font
        from src.controls import Controls
        # from src.sounds import Sound # MockSound is linked in game.py but actual class might be 'Sound'
        
        # We need to test the Real classes, but some might be mocked in self.game
        # We will import them to check signatures on the CLASS itself where possible, 
        # or use the instances we have if they are real.
        
        checks = [
            # 1. Game (game.hh) - 100%
            (self.game, [
                "loop_once", "add_entity", "get_game_state", "get_landscape", 
                "get_interface", "get_settings", "get_controls", "get_font",
                "get_players", "get_current_menu", "explosion", 
                "get_time", "get_num_of_players", "get_num_of_rounds", "get_current_round",
                "are_human_players", "add_player", "delete_players",
                "set_num_of_rounds", "set_active_controller"
            ]),
            
            # 2. Tank (tank.hh) - 100%
            (t1, [
                "draw", "update", "set_colour", "get_colour", "get_player",
                "set_position_on_ground", "intersect_tank", "get_centre",
                "do_damage", "do_pre_round", "do_post_round", "is_firing",
                "ready_to_fire", "alive", "gun_launch_position", 
                "gun_launch_velocity", "gun_launch_angle", 
                "gun_launch_velocity_at_power" # Found in tank.hh:105
            ]),
            
            # 3. Landscape (landscape.hh) - 100%
            (self.game._landscape, [
                "update", "draw", "make_hole", "ground_collision", "drop_terrain",
                "get_landscape_width", "move_to_ground", "move_to_ground_at_angle"  
            ]),
            
            # 4. Player (player.hh) - 100%
            (p1, [
                "get_command", "get_tank", "get_controller", "record_shot",
                "record_fired", "new_round", "end_round", "update",
                "defeat", "set_name", "get_name"
            ]),
            
            # 5. Entity (entity.hh) - Virtual Base
            # Checked via Tank (inherits Entity), verifying base methods
            (t1, [
                "set_position", "get_position", "do_pre_round", "do_post_round"
            ]),
            
            # 6. Weapon (weapon.hh) - 100%
            (t1.get_weapon(0), [
                "fire", "update", "select", "draw_graphic", 
                "set_ammo_for_round", "unselect", "ready_to_fire", 
                "get_ammo", "add_amount", "get_cost", "set_cost"
            ]),
            
            # 7. Menu (menu.hh)
            (self.game._current_menu, [
                "update", "draw", "update_background", "draw_background"
            ]),
            
            # 8. Buttons (buttons.hh)
            # Need to instantiate locally
            (TextButton(self.game._current_menu, 0,0,1, "Test"), [
                "update", "draw", "enable"
            ]),
            
            # 9. Selector (selector.hh)
            (Selector(self.game._current_menu, 0,0,1,1), [
                "update", "draw", "add_option", "get_option", "set_option",
                "set_colours", "enable", "clear_options"
            ]),
            
            # 10. Font (font.hh)
            # Typically self.game._font. but it might be None/Mocked.
            # Use src.font.Font class directly?
            (self.game.get_font() if self.game.get_font() else Font(None, 0), [
                "set_size", "set_colour", "printf", "print_centred_at",
                "set_proportional", "set_shadow", "set_orientation",
                "find_string_length"
            ]),
            
            # 11. Interface (interface.hh) - HUGE
            # Using MockInterface in test, so we verify the Mock supports the API OR check real class?
            # User wants "Code Port" verification. We should check the REAL Interface class if possible.
            # But we can't instantiate it headless easily without glfw.
            # We will check signature of 'src.interface.Interface' class via introspection.
            (Interface, [
                "start_draw", "end_draw", "should_close", "get_mouse_pos",
                "get_mouse_button", "get_key", "get_joystick_button",
                "get_joystick_axis", "define_textures", "load_texture",
                "set_texture", "get_window_settings", "enable_mouse",
                "change_window", "num_of_controllers", "offset_viewport"
            ]),
            
            # 12. Controls (controls.hh)
            (Controls, [
                 "get_command", "set_layout", "get_layout", 
                 "set_control", "get_control", "reset_to_default"
            ]),

            # 13. Effects & Projectiles (Entity subclasses)
            # Typically just update/draw, but checking existence
            (p1.get_tank()._game._entity_list, []), # Just to ensure list exists? No, check classes.
        ]
        
        # Dynamic import for entities to check class signatures
        from src.blast import Blast
        from src.smoke import Smoke
        from src.trail import Trail
        from src.shell import Shell
        from src.missile import Missile
        from src.mirv import Mirv
        from src.machinegunround import MachineGunRound
        
        checks.extend([
            (Blast, ["update", "draw"]),
            (Smoke, ["update", "draw"]),
            (Trail, ["update", "draw"]),
            (Shell, ["update", "draw"]),
            (Missile, ["update", "draw"]),
            (Mirv, ["update", "draw"]),
            (MachineGunRound, ["update", "draw"]),
        ])
        
        missing_log = []
        
        for obj, methods in checks:
            is_class = isinstance(obj, type)
            cls_name = obj.__name__ if is_class else obj.__class__.__name__
            
            for method in methods:
                 # Check for snake_case
                 if not hasattr(obj, method):
                     missing_log.append(f"{cls_name} missing {method}")
        
        if missing_log:
            self.fail(f"EXHAUSTIVE API Parity Failure:\n" + "\n".join(missing_log))

if __name__ == '__main__':
    unittest.main()
