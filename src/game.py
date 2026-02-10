from typing import TYPE_CHECKING, List, Optional
import math
import random
import pygame
import time

from .interface import Interface, Colour, InterfaceError
from .inifile import ReadIniFile
from .controls import Controls
from .controlsfile import ControlsFile
from .font import Font
from .sounds import Sound
from .landscape import Landscape
from .humanplayer import HumanPlayer
from .aiplayer import AIPlayer
from .blast import Blast
from .quake import Quake

# Menus
from .mainmenu import MainMenu
from .playermenu import PlayerMenu
from .optionmenu import OptionMenu
from .shopmenu import ShopMenu
from .scoremenu import ScoreMenu
from .quitmenu import QuitMenu
from .winnermenu import WinnerMenu
from .controllermenu import ControllerMenu
from .setcontrolsmenu import SetControlsMenu

if TYPE_CHECKING:
    from .entity import Entity
    from .player import Player
    from .menu import Menu

# Constants
VERSION = "v0.25 (Python Port)"

# Enum for Game States
from .common import GameState

class GameError(Exception):
    pass

class Game:
    GameState = GameState

    def __init__(self):
        self._entity_list: List['Entity'] = []
        self._game_state = GameState.MAIN_MENU
        self._new_state = GameState.MAIN_MENU
        self._state_countdown = 0.0
        self._number_of_active_tanks = 0
        
        # Default initialization values
        self._width = 640
        self._height = 480
        self._fullscreen = False
        
        # Systems
        try:
            # 1. IniFile
            self._settings = ReadIniFile("conf/options.ini")
            
            # Read Graphics
            if self._settings.get_string("Graphics", "Fullscreen", "no") == "yes":
                self._fullscreen = True
            
            res = self._settings.get_string("Graphics", "Resolution", "640x480")
            if "x" in res:
                self._width, self._height = map(int, res.split("x"))
            
            # 2. Interface
            self._interface = Interface(self._width, self._height, self._fullscreen)
            
            tex_map = {
                1: "data/landscape.bmp", # Missing
                2: "data/mask.bmp", # Missing
                3: "data/fonts.tga",
                4: "data/tank.tga", # Missing
                5: "data/highlight.tga", # Missing
                6: "data/menuback.tga",
                7: "data/clouds.tga", # Missing
                8: "data/cursor.tga", # Missing
                9: "data/logo.tga",
                10: "data/addbutton.tga",
                11: "data/removebutton.tga",
                # The following icons are likely sub-regions of weaponicons.tga in original C++, 
                # but if the port expects files, they are missing.
                # I will map them to weaponicons.tga for now to avoid crash, 
                # but the game logic needs to handle UVs if they are spritesheets.
                # However, interface.load_texture loads a whole image.
                # If these files don't exist, I should point to a placeholder or existing file to prevent crash.
                12: "data/weaponicons.tga",
                13: "data/weaponicons.tga",
                14: "data/weaponicons.tga",
                15: "data/weaponicons.tga",
                16: "data/weaponicons.tga",
                17: "data/weaponicons.tga",
                18: "data/weaponicons.tga",
                19: "data/smoke.tga",
                20: "data/explosion.tga", # Missing? No, blast.tga?
                21: "data/debris.tga", # Missing
                22: "data/flare.tga" # Missing
            }
            # Update: Correct mapping based on 'ls data':
            # blast.tga, damage.tga, exhaust.tga, fonts.tga, logo.tga, menuback.tga, smoke.tga, trail.tga, weaponicons.tga, addbutton, removebutton.
            # Missing: landscape.bmp, mask.bmp, tank.tga, highlight.tga, clouds, cursor, explosion, debris, flare.
            # C++ code likely generated some of these or they are missing from repo?
            # game.cc loadResources:
            # blast, trail, exhaust, damage, smoke, menuback, weaponicons, arrow (id 8!), logo, addbutton, removebutton.
            # It defines 12 textures. 0 to 11.
            # My python code defines 22?
            # It seems I ported 'Game' class adding many more textures that don't exist in C++ loadResources?
            # I should revert to C++ loadResources list.
            
            self._interface.define_textures(12)
            tex_map = {
                0: "data/blast.tga",
                1: "data/trail.tga",
                2: "data/exhaust.tga",
                # 3 unused? C++ skips 3? No, font is separate object using texture?
                # C++: _font = new cFont(&_interface, 3); -> Font uses texture ID 3.
                # But loadResources doesn't load id 3?
                # Ah, Font class probably loads it? No, Font takes global texture ID.
                # Wait, game.cc: loadTexture(..., 0), (..., 1), ...
                # It loads 0,1,2, 4,5,6,7,8,9,10,11. Skipping 3.
                # And then `_font = new cFont(..., 3)`.
                # So ID 3 must be loaded! Perhaps Font loads it?
                # Let's check Font.cc or Font.py.
                # In game.cc, it does NOT load texture 3 explicitly in loadResources.
                # Maybe C++ Font constructor loads it?
                
                # For this step, I will map what I have in 'ls data'.
                4: "data/damage.tga",
                5: "data/smoke.tga",
                6: "data/menuback.tga",
                7: "data/weaponicons.tga",
                8: "data/arrow.tga", # Cursor?
                9: "data/logo.tga",
                10: "data/addbutton.tga",
                11: "data/removebutton.tga"
            }
            # Font needs texture 3 "fonts.tga". I will load it manually here.
            tex_map[3] = "data/fonts.tga"

            for tid, fname in tex_map.items():
                if not self._interface.load_texture(fname, tid):
                     print(f"Warning: Failed to load {fname}")

            # 3. Controls
            self._controls = Controls(self._interface) # Controls needs interface
            self._controls_file = ControlsFile(self._controls, "conf/controls.ini")
            self._controls_file.read_file()
            
            # 4. Font
            self._font = Font(self._interface, 3)
            
            # 5. Sound
            self._sound = Sound(10)
            # Load sounds...
            # self._sound.set_master_volume(1.0) # Placeholder
            
            # C++ LoadSound calls:
            # 0: fireshell, 1: shelldeath, 2: quake, 3: jumpjets, 4: missile, 5: launch, 6: missiledeath, 7: nuke, 8: machinegun, 9: metal
            sound_map = {
                0: "data/fireshell.wav",
                1: "data/shelldeath.wav",
                2: "data/quake.wav",
                3: "data/jumpjets.wav",
                4: "data/missile.wav",
                5: "data/launchmissile.wav",
                6: "data/missiledeath.wav",
                7: "data/nuke.wav",
                8: "data/machinegun.wav",
                9: "data/metal.wav"
            }
            for sid, fname in sound_map.items():
                self._sound.load_sound(sid, fname)
            
            # Data/Landscape init
            # Start game with Main Menu
            self._current_menu = MainMenu(self)
            self._interface.enable_mouse(True)
            
            # Initial time
            self._time = time.time()
            self._last_time = self._time
            
        except InterfaceError:
            raise GameError("Failed to initialize game interface.")

        self._landscape = Landscape(self._settings, self._time)
        
        # Players
        self._players: List[Optional['Player']] = [None] * 8
        self._number_of_players = 0
        self._active_controller = 0
        self._num_of_rounds = 10
        self._current_round = 0
        
        # Round Transition logic
        self._round_end_timer = 0.0
        
    def __del__(self):
        # Save settings on exit?
        if hasattr(self, '_controls_file') and self._controls_file:
             try:
                 self._controls_file.write_file()
             except NameError:
                 pass
             
    # Accessors
    def get_game_state(self) -> int: return self._game_state
    def get_landscape(self) -> 'Landscape': return self._landscape
    def get_interface(self) -> Interface: return self._interface
    def get_settings(self) -> ReadIniFile: return self._settings
    def get_controls(self) -> Controls: return self._controls
    def get_controls_file(self) -> ControlsFile: return self._controls_file
    def get_font(self) -> Font: return self._font
    def get_sound(self) -> Sound: return self._sound
    def get_time(self) -> float: return self._time
    
    def add_entity(self, entity: 'Entity'):
        self._entity_list.append(entity)
        
    def get_players(self) -> List[Optional['Player']]: return self._players
    def get_num_of_players(self) -> int: return self._number_of_players
    def get_current_menu(self) -> Optional['Menu']: return self._current_menu
    
    def set_active_controller(self, idx: int): self._active_controller = idx
    def get_active_controller(self) -> int: return self._active_controller
    def set_num_of_rounds(self, rounds: int): self._num_of_rounds = rounds
    def get_num_of_rounds(self) -> int: return self._num_of_rounds
    def get_current_round(self) -> int: return self._current_round
    
    def add_player(self, controller: int, name: str, colour: tuple):
        if self._number_of_players < 8:
            if controller == -1:
                new_player = AIPlayer(self, self._number_of_players, name, colour)
            else:
                new_player = HumanPlayer(self, self._number_of_players, name, colour, controller, self._controls)
            self._players[self._number_of_players] = new_player
            # Add the player's tank entity to the list of entities (C++: addEntity(tank))
            self.add_entity(new_player.get_tank())
            self._number_of_players += 1
            
    def delete_players(self):
        self._players = [None] * 8
        self._number_of_players = 0
        self._current_round = 0
        self._entity_list = []
        self._human_players = False
        self._number_of_active_tanks = 0

    def are_human_players(self) -> bool:
        for i in range(self._number_of_players):
            if self._players[i] and not self._players[i].is_computer():
                return True
        return False

    def record_tank_death(self):
        """Called every time a tank dies. Determines when to end the round.
        Matches C++ recordTankDeath()."""
        self._number_of_active_tanks -= 1
        if self._number_of_active_tanks < 2 and self._game_state == self.GameState.ROUND_IN_ACTION:
            # Only one tank left, start a 5 second countdown to end of round
            self._game_state = self.GameState.ROUND_FINISHING
            self._state_countdown = 5.0

    def offset_viewport(self, x, y):
        if self._interface: self._interface.offset_viewport(x, y)

    def explosion(self, x, y, size, damage, hit_tank_idx, sound_id, white_out, player_ref):
        # Blow a hole in the terrain
        self._landscape.make_hole(x, y, size)
        
        # Create blast entity
        b = Blast(self, x, y, size, 0.8, white_out)
        self.add_entity(b)
        
        # Play explosion sound
        from .soundentity import SoundEntity
        blast_sound = SoundEntity(self, sound_id, False)
        self.add_entity(blast_sound)
        
        # Damage tanks (faithful to C++ logic)
        for i in range(8):
            if self._players[i] is None:
                break
            t = self._players[i].get_tank()
            
            if i == hit_tank_idx:
                # Direct hit: apply full damage
                if t.do_damage(damage):
                    player_ref.defeat(self._players[i])
            else:
                # Splash damage: scale by squared distance
                tank_x, tank_y, hit_range = t.get_centre()
                
                squared_distance = (tank_x - x)**2 + (tank_y - y)**2
                max_distance = (size + hit_range)**2
                
                if squared_distance < max_distance:
                    if t.do_damage(damage * (1.0 - squared_distance / max_distance)):
                        player_ref.defeat(self._players[i])

    # -------------------------------------------------------------------------
    # Main Loop
    # -------------------------------------------------------------------------
    def loop_once(self) -> bool:
        # Time management
        current_time = time.time()
        dt = current_time - self._last_time
        self._last_time = current_time
        self._time += dt
        
        # Max dt clamp to prevent physics explosion on lag
        if dt > 0.1: dt = 0.1
        
        # Check window close
        if self._interface.should_close():
             return False
             
        self._interface.start_draw()
        
        # State Machine
        if self._game_state != self.GameState.ROUND_IN_ACTION and \
           self._game_state != self.GameState.ROUND_FINISHING and \
           self._game_state != self.GameState.ROUND_STARTING:
             # Menu Handling
             if self._current_menu:
                 self._new_state = self._current_menu.update(dt)
                 self._current_menu.draw()
             else:
                 # Error?
                 self._new_state = self.GameState.MAIN_MENU

        elif self._game_state == self.GameState.ROUND_STARTING:
             # Update physics (tanks fall) and Draw Game
             self._update_round(dt)
             self._draw_round()
             
             # Draw Round Number text overlay
             self._interface.start_draw() # Set context if needed, but end_draw handles flip
             
             self._font.set_shadow(True)
             self._font.set_size(0.6, 0.6, 0.5)
             self._font.set_colour((255, 255, 255))
             self._font.print_centred_at(0.0, 0.5, f"Round {self._current_round}")
             self._font.print_centred_at(0.0, -0.5, "Get Ready")
             self._font.set_shadow(False)
             
             self._state_countdown -= dt
             if self._state_countdown < 0.0:
                 self._new_state = self.GameState.ROUND_IN_ACTION

        elif self._game_state == self.GameState.ROUND_FINISHING:
             # When all but one tank is dead, count down to end of round
             self._update_round(dt)
             self._draw_round()
             
             self._state_countdown -= dt
             if self._state_countdown < 0.0:
                 self._end_round()
                 self._game_state = self.GameState.ROUND_SCORE
                 self._current_menu = ScoreMenu(self)
                 self._interface.enable_mouse(True)

        elif self._game_state == self.GameState.ROUND_IN_ACTION:
            # Game Logic
            self._update_round(dt)
            self._draw_round()

        self._interface.end_draw()
        
        # State Transitions
        if self._new_state != self.GameState.CURRENT_STATE and self._new_state != self._game_state:
            self._change_state(self._new_state)
            
        return self._game_state != self.GameState.EXITED

    def _change_state(self, new_state):
        # Cleanup old state
        # (Nothing specific for now)
        
        prev_state = self._game_state
        self._game_state = new_state
        
        # Init new state
        if new_state == self.GameState.MAIN_MENU:
            if prev_state == self.GameState.PAUSE_MENU:
                 # Aborting game
                 self.delete_players()
            self._current_menu = MainMenu(self)
            self._interface.enable_mouse(True)
            self._interface.offset_viewport(0, 0)
            
        elif new_state == self.GameState.SELECT_PLAYERS_MENU:
            # Clear players if coming from Main Menu to start fresh
            if prev_state == self.GameState.MAIN_MENU:
                 pass # self.delete_players() called inside playermenu? No, playermenu manages it.
            self._current_menu = PlayerMenu(self)
            
        elif new_state == self.GameState.OPTION_MENU:
            self._current_menu = OptionMenu(self)
            
        elif new_state == self.GameState.CONTROLLERS_MENU:
            self._current_menu = ControllerMenu(self)
            
        elif new_state == self.GameState.SET_CONTROLS_MENU:
            self._current_menu = SetControlsMenu(self, self._active_controller)
            
        elif new_state == self.GameState.QUIT_MENU:
            self._current_menu = QuitMenu(self)
            
        elif new_state == self.GameState.SHOP_MENU:
            self._current_menu = ShopMenu(self)
            self._interface.enable_mouse(False) # Shop uses controls?
            # C++ ShopMenu uses Controls (UP/DOWN/FIRE).
            # But wait, python ShopMenu port update() handles input via players using controls.
            # So mouse is hidden. 
            pass
            
        elif new_state == self.GameState.ROUND_SCORE:
            self._current_menu = ScoreMenu(self)
            self._interface.enable_mouse(False)
            
        elif new_state == self.GameState.WINNER_MENU:
            self._current_menu = WinnerMenu(self)
            self._interface.enable_mouse(False)
            
        elif new_state == self.GameState.ROUND_STARTING:
            self._current_menu = None
            self._interface.enable_mouse(False)
            self._state_countdown = 2.0
            self._start_round()
            # Stay in ROUND_STARTING
            pass

    def _start_round(self):
        self._current_round += 1
        
        # Generate Terrain
        self._landscape.generate_terrain()
        
        # Call newRound() on all players (resets defeated lists, etc.)
        for i in range(self._number_of_players):
            if self._players[i]:
                self._players[i].new_round()
        
        # Call doPreRound() on all entities (resets tank state, etc.)
        for e in self._entity_list[:]:
            if not e.do_pre_round():
                self._entity_list.remove(e)
        
        # Place Tanks using Layout logic (C++ port)
        tank_order = []
        active_tanks = 0
        for i in range(self._number_of_players):
            if self._players[i]:
                tank_order.append(i)
                active_tanks += 1

        # Shuffle positions logic
        for _ in range(20):
             if active_tanks > 0:
                 t1 = random.randint(0, active_tanks - 1)
                 t2 = random.randint(0, active_tanks - 1)
                 tank_order[t1], tank_order[t2] = tank_order[t2], tank_order[t1]
        
        for i in range(active_tanks):
            p_idx = tank_order[i]
            tank = self._players[p_idx].get_tank()
            
            x_pos = -10.0 + (10.0 / active_tanks) + (i * (20.0 / active_tanks))
            tank.set_position_on_ground(x_pos)
            
        self._number_of_active_tanks = active_tanks
        
        # Add Quake entity at the front (always present for screen shake)
        # C++: _entityList.push_front(earthquake)
        self._entity_list.insert(0, Quake(self))
        
    def _update_round(self, dt):
        """Implements the part of the loop that occurs while a round is
        in progress. Matches C++ gameLoop()."""
        # Update landscape first, then entities (C++ order)
        self._landscape.update(dt)

        # Update entities — if update returns False, entity is dead
        for e in self._entity_list[:]:
            if not e.update(dt):
                self._entity_list.remove(e)

        # Input for Pause (Escape)
        if self._interface.get_key(pygame.K_ESCAPE):
            self._new_state = self.GameState.QUIT_MENU

    def _end_round(self):
        # Call endRound() on all players (calculates scores)
        for i in range(self._number_of_players):
            if self._players[i]:
                self._players[i].end_round()
        
        # Call doPostRound() on entities; remove those returning False
        for e in self._entity_list[:]:
            if not e.do_post_round():
                self._entity_list.remove(e)
                
        self._new_state = self.GameState.ROUND_SCORE

    def _draw_round(self):
        # Draw sky
        # Handled by Landscape.draw() for correct layering and aesthetics
        # self._interface._window.fill((100, 180, 230)) 
        pass
        
        # Draw Landscape (Sky + Terrain)
        
        # Background clouds?
        # Draw Landscape
        self._landscape.draw()
        
        # Draw Tanks
        for i in range(self._number_of_players):
            if self._players[i]:
                self._players[i].get_tank().draw()
                
        # Draw Entities
        for e in self._entity_list:
            e.draw()
