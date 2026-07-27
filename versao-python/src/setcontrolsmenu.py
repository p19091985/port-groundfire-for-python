from typing import TYPE_CHECKING
from .menu import Menu
from .buttons import TextButton
from .common import GameState
import pygame

if TYPE_CHECKING:
    from .game import Game
    from .controls import Controls

class SetControlsMenu(Menu):
    NUM_OF_CONTROLS = 11
    
    LINKED_CONTROLS = [
        -1, 2, 1, -1, -1, 6, 5, 8, 7, 10, 9
    ]
    
    CONTROL_STRINGS = [
        "Fire Weapon", "Change Weapon Up", "Change Weapon Down",
        "Use Jump Jets", "Use Shield",
        "Move Tank Left", "Move Tank Right",
        "Rotate Gun Left", "Rotate Gun Right",
        "Increase Gun Power", "Decrease Gun Power"
    ]
    
    AXIS_NAMES = [
        "Joystick/Pad Right", "Joystick/Pad Left",
        "Joystick/Pad Up", "Joystick/Pad Down",
        "Axis 3 (-)", "Axis 3 (+)",
        "Axis 4 (-)", "Axis 4 (+)"
    ]

    def __init__(self, game: 'Game', layout: int):
        super().__init__(game)
        self._layout = layout
        self._controls = game.get_controls()
        
        self._control_buttons = [None] * self.NUM_OF_CONTROLS
        self._control_key = [0] * self.NUM_OF_CONTROLS
        
        for i in range(self.NUM_OF_CONTROLS):
            self._control_buttons[i] = TextButton(self, -3.0, 5.0 - i * 0.8, 0.5, self.CONTROL_STRINGS[i])
            self._control_key[i] = self._controls.get_control(layout, i)
            
        self._reset_button = TextButton(self, 0.0, -5.0, 0.7, "Reset To Defaults")
        self._done_button = TextButton(self, 0.0, -6.0, 0.7, "Done")
        
        self._waiting_for_key = -1
        
    def update(self, time: float) -> int:
        self.update_background(time)
        
        for i in range(self.NUM_OF_CONTROLS):
             if self._control_buttons[i].update():
                 self._waiting_for_key = i
                 for j in range(self.NUM_OF_CONTROLS):
                     self._control_buttons[j].enable(False)
                     
        if self._waiting_for_key != -1:
            if self._layout < 2:
                found_key = -1
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.event.post(event)
                        break
                    
                    if event.type == pygame.KEYDOWN:
                        found_key = event.key
                        break
                        
                if found_key != -1:
                    self._control_key[self._waiting_for_key] = found_key
                    self._waiting_for_key = -1
                    for j in range(self.NUM_OF_CONTROLS):
                        self._control_buttons[j].enable(True)
            else:
                joy_idx = self._layout - 2
                found = False
                interface = self._game.get_interface()
                
                for b in range(16):
                    if interface.get_joystick_button(joy_idx, b):
                        if self._control_key[self._waiting_for_key] >= 100 and \
                           self.LINKED_CONTROLS[self._waiting_for_key] != -1:
                               self._control_key[self.LINKED_CONTROLS[self._waiting_for_key]] = -1
                        
                        self._control_key[self._waiting_for_key] = b
                        found = True
                        break
                
                if not found:
                    for a in range(8):
                        val = interface.get_joystick_axis(joy_idx, a)
                        if val > 0.5:
                            self._control_key[self._waiting_for_key] = 100 + (a * 2)
                            linked = self.LINKED_CONTROLS[self._waiting_for_key]
                            if linked != -1: self._control_key[linked] = 101 + (a * 2)
                            found = True
                            break
                        elif val < -0.5:
                            self._control_key[self._waiting_for_key] = 101 + (a * 2)
                            linked = self.LINKED_CONTROLS[self._waiting_for_key]
                            if linked != -1: self._control_key[linked] = 100 + (a * 2)
                            found = True
                            break
                            
                if found:
                    self._waiting_for_key = -1
                    for j in range(self.NUM_OF_CONTROLS):
                        self._control_buttons[j].enable(True)
                        
        if self._done_button.update():
            for i in range(self.NUM_OF_CONTROLS):
                self._controls.set_control(self._layout, i, self._control_key[i])
            return GameState.CONTROLLERS_MENU
            
        if self._reset_button.update():
            self._controls.reset_to_default(self._layout)
            for i in range(self.NUM_OF_CONTROLS):
                self._control_key[i] = self._controls.get_control(self._layout, i)
                
        return GameState.CURRENT_STATE

    def draw(self):
        self.draw_background()
        boxes = [
            [(-7.0, -4.0), (7.0, -4.0), (7.0, 6.0), (-7.0, 6.0)],
            [(-7.0, -6.6), (7.0, -6.6), (7.0, -4.4), (-7.0, -4.4)]
        ]
        dark = (0, 0, 0, 128)
        for b in boxes:
            self.draw_game_polygon(b, dark)
            
        brown = (153, 76, 0, 128)
        
        for i in range(self.NUM_OF_CONTROLS):
            y_top = 5.3 - i * 0.8
            y_bot = 4.6 - i * 0.8
            lb = [(-6.0, y_top), (0.0, y_top), (0.0, y_bot), (-6.0, y_bot)]
            rb = [(0.1, y_top), (6.0, y_top), (6.0, y_bot), (0.1, y_bot)]
            self.draw_game_polygon(lb, brown)
            self.draw_game_polygon(rb, brown)
            
        bb1 = [(-4.0, -5.4), (4.0, -5.4), (4.0, -4.6), (-4.0, -4.6)]
        bb2 = [(-4.0, -6.4), (4.0, -6.4), (4.0, -5.6), (-4.0, -5.6)]
        self.draw_game_polygon(bb1, brown)
        self.draw_game_polygon(bb2, brown)

        title = f"Editing Keyboard Layout {self._layout + 1}" if self._layout < 2 else f"Editing Joystick Layout {self._layout - 1}"
        self._ui.draw_centered_text(0.0, 6.5, title, style=self._ui.style(0.6, (1.0, 1.0, 1.0), shadow=True))
        
        if self._waiting_for_key != -1:
            self._ui.draw_centered_text(
                0.0,
                -4.0,
                f"Press Button for '{self.CONTROL_STRINGS[self._waiting_for_key]}'",
                style=self._ui.style(0.6, (0.5, 0.5, 0.5), shadow=True),
            )

        value_style = self._ui.style(0.5, (0.0, 1.0, 1.0), spacing=0.4)
        for i in range(self.NUM_OF_CONTROLS):
            key = self._control_key[i]
            txt = "<Undefined>"
            
            if self._layout < 2:
                if key > 0:
                    txt = pygame.key.name(key)
            else:
                if key == -1: txt = "<Undefined>"
                elif key < 100: txt = f"Joy Button {key + 1}"
                else: 
                     idx = key - 100
                     if idx < len(self.AXIS_NAMES):
                         txt = self.AXIS_NAMES[idx]
                     else:
                         txt = f"Axis {idx}"
            
            self._ui.draw_centered_text(3.0, 4.7 - i * 0.8, txt, style=value_style)
            
        for i in range(self.NUM_OF_CONTROLS):
            self._control_buttons[i].draw()
            
        self._reset_button.draw()
        self._done_button.draw()
