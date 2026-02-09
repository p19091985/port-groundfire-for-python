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
        interface = self._game.get_interface()
        
        dark = (0, 0, 0, 128)
        brown = (153, 76, 0, 128)
        
        boxes = [
            [(-7.0, 3.2), (7.0, 3.2), (7.0, 6.0), (-7.0, 6.0)],
            [(-7.0, -5.2), (7.0, -5.2), (7.0, 2.8), (-7.0, 2.8)],
            [(-7.0, -6.6), (7.0, -6.6), (7.0, -5.4), (-7.0, -5.4)]
        ]
        
        for b in boxes:
            self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in b], dark)
            
        brown_boxes = [
            [(-4.0, -6.4), (4.0, -6.4), (4.0, -5.6), (-4.0, -5.6)],
            [(-6.4, 3.4), (6.4, 3.4), (6.4, 4.1), (-6.4, 4.1)],
            [(-6.4, 4.2), (6.4, 4.2), (6.4, 4.9), (-6.4, 4.9)]
        ]
        
        for b in brown_boxes:
            self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in b], brown)
            
        for i in range(8):
             y_base = 0.75 - i * 0.8
             pts = [(-6.4, y_base), (6.4, y_base), (6.4, y_base + 0.7), (-6.4, y_base + 0.7)]
             self._draw_transparent_poly([interface.game_to_screen(x,y) for x,y in pts], brown)
             
        font = self._game.get_font()
        font.set_shadow(True)
        font.set_size(0.6, 0.6, 0.5)
        font.set_colour((1.0, 1.0, 1.0))
        font.print_centred_at(0.0, 6.5, "Set Controls")
        
        font.set_shadow(False)
        font.set_size(0.4, 0.4, 0.3)
        font.set_colour((0.5, 0.5, 0.5))
        
        font.print_centred_at(0.0, 2.2, "Joystick")
        font.print_centred_at(0.0, 1.8, "layout number")
        font.print_centred_at(4.5, 2.2, "Change")
        font.print_centred_at(4.5, 1.8, "joystick layout")
        
        font.print_centred_at(2.0, 5.4, "Change")
        font.print_centred_at(2.0, 5.0, "keyboard layout")
        
        font.set_size(0.6, 0.6, 0.5)
        font.set_colour((0.0, 1.0, 1.0))
        font.print_centred_at(-2.0, 4.3, "Keyboard 1")
        font.print_centred_at(-2.0, 3.5, "Keyboard 2")
        
        font.set_colour((0.5, 0.5, 0.5))
        connected_joys = len(self._joysticks)
        for i in range(connected_joys, 8):
            font.print_centred_at(-4.6, 0.8 - i*0.8, f"Joystick {i+1}")
            font.print_centred_at(2.0, 0.8 - i*0.8, "<<Not Connected>>")
            
        for i in range(connected_joys):
            font.set_size(0.6, 0.6, 0.5)
            font.set_colour((0.0, 1.0, 1.0))
            font.print_centred_at(-4.6, 0.8 - i*0.8, f"Joystick {i+1}")
            self._joysticks[i].layout.draw()
            self._joysticks[i].define.draw()
            
        self._keyboard[0].draw()
        self._keyboard[1].draw()
        self._back_button.draw()

    def _draw_transparent_poly(self, points, color):
        if not points: return
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w, h = max_x - min_x, max_y - min_y
        if w < 1 or h < 1: return
        
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        local_points = [(p[0] - min_x, p[1] - min_y) for p in points]
        pygame.draw.polygon(s, color, local_points)
        self._game.get_interface()._window.blit(s, (min_x, min_y))
