from __future__ import annotations

from ..core.pygame import load_pygame_module
from ..ui.interface import Interface

KEYBOARD_DEVICE = 0
JOYSTICK_DEVICE = 1

NUM_OF_CONTROLS = 11


def _default_commands(pygame_module):
    return [
        [
            pygame_module.K_SPACE,
            pygame_module.K_o,
            pygame_module.K_u,
            pygame_module.K_i,
            pygame_module.K_k,
            pygame_module.K_j,
            pygame_module.K_l,
            pygame_module.K_a,
            pygame_module.K_d,
            pygame_module.K_w,
            pygame_module.K_s,
        ],
        [
            pygame_module.K_RCTRL,
            pygame_module.K_KP_8,
            pygame_module.K_KP_5,
            pygame_module.K_KP_6,
            pygame_module.K_KP_4,
            pygame_module.K_LEFT,
            pygame_module.K_RIGHT,
            pygame_module.K_DELETE,
            pygame_module.K_PAGEDOWN,
            pygame_module.K_HOME,
            pygame_module.K_END,
        ],
        [0, 2, 1, 3, 4, 6, 7, 101, 100, 102, 103],
    ]


class Controls:
    def __init__(self, interface: Interface, *, pygame_module=None):
        self._interface = interface
        self._pygame = load_pygame_module(pygame_module)
        defaults = _default_commands(self._pygame)

        self._controller_layout = [0] * 10
        self._layouts = []
        for index in range(10):
            default_index = index if index < 2 else 2
            device_type = KEYBOARD_DEVICE if index < 2 else JOYSTICK_DEVICE
            self._layouts.append(
                {
                    "device_type": device_type,
                    "command": list(defaults[default_index]),
                }
            )

        self._controller_layout[0] = 0
        self._controller_layout[1] = 1
        for index in range(2, 10):
            self._controller_layout[index] = 2

    def get_command(self, controller, command_id):
        layout_idx = self._controller_layout[controller]
        layout = self._layouts[layout_idx]
        mapped_val = layout["command"][command_id]

        if layout["device_type"] == KEYBOARD_DEVICE:
            return self._interface.get_key(mapped_val)

        if mapped_val >= 100:
            axis = (mapped_val - 100) // 2
            direction = (mapped_val - 100) % 2
            reading = self._interface.get_joystick_axis(controller - 2, axis)
            if direction == 0 and reading >= 0.5:
                return True
            if direction == 1 and reading <= -0.5:
                return True
            return False

        return self._interface.get_joystick_button(controller - 2, mapped_val)

    def set_layout(self, controller, layout_num):
        self._controller_layout[controller] = layout_num

    def get_layout(self, controller):
        return self._controller_layout[controller]

    def set_control(self, layout_idx, command_id, control_id):
        self._layouts[layout_idx]["command"][command_id] = control_id

    def get_control(self, layout_idx, command_id):
        return self._layouts[layout_idx]["command"][command_id]

    def reset_to_default(self, layout_idx):
        defaults_idx = layout_idx if layout_idx < 2 else 2
        self._layouts[layout_idx]["command"] = list(_default_commands(self._pygame)[defaults_idx])
