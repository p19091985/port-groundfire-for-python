from typing import TYPE_CHECKING
from .menu import Menu
from .buttons import TextButton
from .selector import Selector
from .common import GameState
import pygame

if TYPE_CHECKING:
    from .game import Game
    from .controls import Controls

class JoystickEntry:
    def __init__(self):
        self.layout = None 
        self.define = None 

class ControllerMenu(Menu):
    def __init__(self, game: 'Game'):
        super().__init__(game)
        
        self._controls = game.get_controls()
        
        self._keyboard = [None, None]
        self._keyboard[0] = TextButton(self, 2.0, 4.6, 0.5, "Edit Layout")
        self._keyboard[1] = TextButton(self, 2.0, 3.8, 0.5, "Edit Layout")
        
        total_ctrls = 2 + pygame.joystick.get_count()
        self._joysticks = []
        
        for i in range(total_ctrls - 2):
            entry = JoystickEntry()
            entry.layout = Selector(self, 0.0, 1.1 - (i * 0.8), 3.3, 0.5)
            entry.define = TextButton(self, 4.5, 1.1 - (i * 0.8), 0.5, "Edit Layout")
            
            for l in range(1, 9):
                entry.layout.add_option(f"Layout {l}")
                
            current_layout = self._controls.get_layout(i + 2)
            entry.layout.set_option(current_layout - 2)
            
            self._joysticks.append(entry)
            
        self._back_button = TextButton(self, 0.0, -6.0, 0.7, "Back")

    def update(self, time: float) -> int:
        self.update_background(time)
        
        for i in range(2):
            if self._keyboard[i].update():
                self._game.set_active_controller(i)
                return GameState.SET_CONTROLS_MENU
                
        for i in range(len(self._joysticks)):
            self._joysticks[i].layout.update()
            
            if self._joysticks[i].define.update():
                layout = self._joysticks[i].layout.get_option()
                self._game.set_active_controller(layout + 2)
                return GameState.SET_CONTROLS_MENU
                
        if self._back_button.update():
            for i in range(len(self._joysticks)):
                self._controls.set_layout(i + 2, self._joysticks[i].layout.get_option() + 2)
                
            self._game.get_controls_file().write_file()
            return GameState.OPTION_MENU
            
        return GameState.CURRENT_STATE

    def draw(self):
        self.draw_background()
        dark = (0, 0, 0, 128)
        brown = (153, 76, 0, 128)
        
        boxes = [
            [(-7.0, 3.2), (7.0, 3.2), (7.0, 6.0), (-7.0, 6.0)],
            [(-7.0, -5.2), (7.0, -5.2), (7.0, 2.8), (-7.0, 2.8)],
            [(-7.0, -6.6), (7.0, -6.6), (7.0, -5.4), (-7.0, -5.4)]
        ]
        
        for b in boxes:
            self.draw_game_polygon(b, dark)
            
        brown_boxes = [
            [(-4.0, -6.4), (4.0, -6.4), (4.0, -5.6), (-4.0, -5.6)],
            [(-6.4, 3.4), (6.4, 3.4), (6.4, 4.1), (-6.4, 4.1)],
            [(-6.4, 4.2), (6.4, 4.2), (6.4, 4.9), (-6.4, 4.9)]
        ]
        
        for b in brown_boxes:
            self.draw_game_polygon(b, brown)
            
        for i in range(8):
             y_base = 0.75 - i * 0.8
             pts = [(-6.4, y_base), (6.4, y_base), (6.4, y_base + 0.7), (-6.4, y_base + 0.7)]
             self.draw_game_polygon(pts, brown)

        self._ui.draw_centered_text(0.0, 6.5, "Set Controls", style=self._ui.style(0.6, (1.0, 1.0, 1.0), shadow=True))
        info_style = self._ui.style(0.4, (0.5, 0.5, 0.5), spacing=0.3)
        self._ui.draw_centered_text(0.0, 2.2, "Joystick", style=info_style)
        self._ui.draw_centered_text(0.0, 1.8, "layout number", style=info_style)
        self._ui.draw_centered_text(4.5, 2.2, "Change", style=info_style)
        self._ui.draw_centered_text(4.5, 1.8, "joystick layout", style=info_style)
        self._ui.draw_centered_text(2.0, 5.4, "Change", style=info_style)
        self._ui.draw_centered_text(2.0, 5.0, "keyboard layout", style=info_style)

        keyboard_style = self._ui.style(0.6, (0.0, 1.0, 1.0))
        self._ui.draw_centered_text(-2.0, 4.3, "Keyboard 1", style=keyboard_style)
        self._ui.draw_centered_text(-2.0, 3.5, "Keyboard 2", style=keyboard_style)

        disconnected_style = self._ui.style(0.5, (0.5, 0.5, 0.5), spacing=0.4)
        connected_joys = len(self._joysticks)
        for i in range(connected_joys, 8):
            self._ui.draw_centered_text(-4.6, 0.8 - i*0.8, f"Joystick {i+1}", style=disconnected_style)
            self._ui.draw_centered_text(2.0, 0.8 - i*0.8, "<<Not Connected>>", style=disconnected_style)
            
        for i in range(connected_joys):
            self._ui.draw_centered_text(-4.6, 0.8 - i*0.8, f"Joystick {i+1}", style=keyboard_style)
            self._joysticks[i].layout.draw()
            self._joysticks[i].define.draw()
            
        self._keyboard[0].draw()
        self._keyboard[1].draw()
        self._back_button.draw()
