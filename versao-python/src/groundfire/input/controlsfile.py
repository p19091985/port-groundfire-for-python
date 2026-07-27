from __future__ import annotations

from pathlib import Path

CMD_NAMES = [
    "Fire",
    "WeaponUp",
    "WeaponDown",
    "JumpJets",
    "Shield",
    "TankLeft",
    "TankRight",
    "GunLeft",
    "GunRight",
    "GunUp",
    "GunDown",
]
NUM_OF_CONTROLS = len(CMD_NAMES)

LAYOUT_NAMES = [
    "Keyboard1",
    "Keyboard2",
    "JoyLayout1",
    "JoyLayout2",
    "JoyLayout3",
    "JoyLayout4",
    "JoyLayout5",
    "JoyLayout6",
    "JoyLayout7",
    "JoyLayout8",
]

JOYSTICKS = [
    "Joystick1",
    "Joystick2",
    "Joystick3",
    "Joystick4",
    "Joystick5",
    "Joystick6",
    "Joystick7",
    "Joystick8",
]


class ControlsFile:
    def __init__(self, controls, file_name: str):
        self._controls = controls
        self._file_name = file_name

    def read_file(self) -> bool:
        path = Path(self._file_name)
        if not path.exists():
            return False
        try:
            tokens = path.read_text(encoding="utf-8").split()
        except OSError:
            return False
        if not tokens:
            return False

        iterator = iter(tokens)

        def get_token():
            return next(iterator)

        try:
            token = get_token()
            if token != "[":
                return False
            if get_token() != "Joysticks":
                return False
            if get_token() != "]":
                return False

            while True:
                first = get_token()
                if first == "[":
                    break
                if first not in JOYSTICKS:
                    return False
                layout_map = JOYSTICKS.index(first)
                if get_token() != "=":
                    return False
                self._controls.set_layout(layout_map + 2, int(get_token()) + 1)

            current_tag = first
            while current_tag == "[":
                layout_name = get_token()
                if layout_name not in LAYOUT_NAMES:
                    return False
                layout_num = LAYOUT_NAMES.index(layout_name)
                if get_token() != "]":
                    return False
                while True:
                    try:
                        cmd_token = get_token()
                    except StopIteration:
                        return True
                    if cmd_token == "[":
                        current_tag = cmd_token
                        break
                    if cmd_token not in CMD_NAMES:
                        return False
                    if get_token() != "=":
                        return False
                    self._controls.set_control(layout_num, CMD_NAMES.index(cmd_token), int(get_token()))
        except (OSError, StopIteration, ValueError):
            return False

        return True

    def write_file(self) -> bool:
        path = Path(self._file_name)
        try:
            with path.open("w", encoding="utf-8") as handle:
                handle.write("[ Joysticks ]\n\n")
                for index in range(8):
                    handle.write(f"{JOYSTICKS[index]} = {self._controls.get_layout(index + 2) - 1}\n")
                for layout_index in range(10):
                    handle.write(f"\n[ {LAYOUT_NAMES[layout_index]} ]\n\n")
                    for command_index in range(NUM_OF_CONTROLS):
                        handle.write(
                            f"{CMD_NAMES[command_index]} = {self._controls.get_control(layout_index, command_index)}\n"
                        )
            return True
        except OSError:
            return False
