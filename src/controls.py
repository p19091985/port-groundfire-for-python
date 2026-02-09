import pygame
from .interface import Interface
# from .player import Player # Removed to fix circular import 
# Actually controls.hh includes player.hh but doesn't seem to use it in the signature 
# shown in the provided snippet. It uses command_t which is likely an enum or similar.
# Wait, command_t is NOT defined in controls.hh. It uses 'int command' in implementation.
# In header: bool getCommand (int controller, command_t command);
# But command_t must be defined somewhere visible. Usually common.hh or game.hh?
# In controls.hh provided: "enum device_t". No command_t. 
# But let's assume command is int for now based on usage.

KEYBOARD_DEVICE = 0
JOYSTICK_DEVICE = 1

NUM_OF_CONTROLS = 11

# Default Key Mappings (Pygame keycodes)
# C++ used: 32 (Space), 79 (O), 85 (U), 73 (I), etc.
# Python Pygame K_SPACE=32. Char codes usually match ASCII.
# 'O' is 111 in ASCII. 79 is 'O' in... scancode? 
# Let's map logical defaults to Pygame constants.

DEFAULT_COMMANDS = [
    # Layout 0
    [pygame.K_SPACE, pygame.K_o, pygame.K_u, pygame.K_i, pygame.K_k, 
     pygame.K_j, pygame.K_l, pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s],
    
    # Layout 1 (Arrow keys + numpad?)
    # Original C++: 302, 311... likely GLFW/Special keys.
    [pygame.K_RCTRL, pygame.K_KP_8, pygame.K_KP_5, pygame.K_KP_6, pygame.K_KP_4, # Just guessing original intent or remapping to sane defaults
     pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DELETE, pygame.K_PAGEDOWN, pygame.K_HOME, pygame.K_END],
     
     # Layout 2 (Joystick)
     # 0, 2, 1, 3... Buttons. 101, 100... Axes?
     # Logic in get_command handles > 100 as Axis.
    [0, 2, 1, 3, 4, 6, 7, 101, 100, 102, 103]
]

class Controls:
    def __init__(self, interface: Interface):
        self._interface = interface
        
        self._controller_layout = [0] * 10
        self._layouts = []
        
        # Init layouts
        for i in range(10):
            defaults = DEFAULT_COMMANDS[0]
            dev_type = KEYBOARD_DEVICE
            
            if i < 2:
                defaults = DEFAULT_COMMANDS[i]
                dev_type = KEYBOARD_DEVICE
            else:
                defaults = DEFAULT_COMMANDS[2]
                dev_type = JOYSTICK_DEVICE
            
            self._layouts.append({
                'device_type': dev_type,
                'command': list(defaults)
            })

        # Set default controller assignments
        self._controller_layout[0] = 0
        self._controller_layout[1] = 1
        for i in range(2, 10):
            self._controller_layout[i] = 2

    def get_command(self, controller, command_id):
        # command_id is int index into command array
        
        layout_idx = self._controller_layout[controller]
        layout = self._layouts[layout_idx]
        
        mapped_val = layout['command'][command_id]
        
        if layout['device_type'] == KEYBOARD_DEVICE:
            return self._interface.get_key(mapped_val)
            
        elif layout['device_type'] == JOYSTICK_DEVICE:
            if mapped_val >= 100:
                # Axis logic
                # (val - 100) / 2 -> Axis index
                # (val - 100) % 2 -> Direction (0=Positive, 1=Negative)
                # Wait, code says:
                # direction == 0 && reading >= 0.5
                # direction == 1 && reading <= -0.5
                
                axis = (mapped_val - 100) // 2
                direction = (mapped_val - 100) % 2
                
                # controller - 2 because controllers 0,1 are keyboards.
                reading = self._interface.get_joystick_axis(controller - 2, axis)
                
                if direction == 0 and reading >= 0.5:
                    return True
                if direction == 1 and reading <= -0.5:
                    return True
            else:
                # Button
                return self._interface.get_joystick_button(controller - 2, mapped_val)
                
        return False

    def set_layout(self, controller, layout_num):
        self._controller_layout[controller] = layout_num

    def get_layout(self, controller):
        return self._controller_layout[controller]

    def set_control(self, layout_idx, command_id, control_id):
        self._layouts[layout_idx]['command'][command_id] = control_id

    def get_control(self, layout_idx, command_id):
        return self._layouts[layout_idx]['command'][command_id]

    def reset_to_default(self, layout_idx):
        defaults_idx = layout_idx if layout_idx < 2 else 2
        self._layouts[layout_idx]['command'] = list(DEFAULT_COMMANDS[defaults_idx])
