import os

# Constants
CMD_NAMES = [
    "Fire", "WeaponUp", "WeaponDown", "JumpJets", "Shield",
    "TankLeft", "TankRight", "GunLeft", "GunRight", "GunUp", "GunDown"
]
NUM_OF_CONTROLS = len(CMD_NAMES)

LAYOUT_NAMES = [
    "Keyboard1", "Keyboard2",
    "JoyLayout1", "JoyLayout2", "JoyLayout3", "JoyLayout4",
    "JoyLayout5", "JoyLayout6", "JoyLayout7", "JoyLayout8"
]

JOYSTICKS = [
    "Joystick1", "Joystick2", "Joystick3", "Joystick4",
    "Joystick5", "Joystick6", "Joystick7", "Joystick8"
]

class ControlsFile:
    def __init__(self, controls, file_name: str):
        self._controls = controls
        self._file_name = file_name

    def read_file(self) -> bool:
        if not os.path.exists(self._file_name):
            return False
            
        try:
            with open(self._file_name, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError:
            return False
            
        # Tokenize by whitespace (simulating fscanf %s)
        tokens = content.split()
        if not tokens:
            return False
            
        iterator = iter(tokens)
        
        try:
            # Helper to safely get next token
            def get_token():
                return next(iterator)

            token = get_token()
            
            # Read first section: [ Joysticks ]
            if token != "[": return False
            token = get_token()
            if token != "Joysticks": return False
            token = get_token()
            if token != "]": return False
            
            # Read Joystick mappings
            # Loop until we hit the next section start "[" or EOF
            while True:
                try:
                    first = get_token()
                except StopIteration:
                    # EOF unexpectedly?
                    return True 
                
                if first == "[":
                    # Start of next section
                    break
                
                if first in JOYSTICKS:
                    layout_map = JOYSTICKS.index(first)
                    
                    eq = get_token()
                    if eq != "=": return False
                    
                    val_str = get_token()
                    try:
                        value = int(val_str)
                    except ValueError:
                        return False
                    
                    self._controls.set_layout(layout_map + 2, value + 1)
                else:
                    return False

            # Now we are at "[", read layouts
            current_tag = first 
            
            while True:
                if current_tag != "[": break
                
                layout_name = get_token()
                if layout_name not in LAYOUT_NAMES: return False
                layout_num = LAYOUT_NAMES.index(layout_name)
                
                closer = get_token()
                if closer != "]": return False
                
                # Read controls for this layout
                while True:
                    try:
                        cmd_token = get_token()
                    except StopIteration:
                        return True # End of file, success
                        
                    if cmd_token == "[":
                        current_tag = cmd_token
                        break # Start of next layout
                    
                    if cmd_token in CMD_NAMES:
                        cmd = CMD_NAMES.index(cmd_token)
                        
                        eq = get_token()
                        if eq != "=": return False
                        
                        val_str = get_token()
                        try:
                            value = int(val_str)
                        except ValueError:
                            return False
                        
                        self._controls.set_control(layout_num, cmd, value)
                    else:
                        return False
                        
        except StopIteration:
            pass # End of tokens
            
        return True

    def write_file(self) -> bool:
        try:
            with open(self._file_name, 'w', encoding='utf-8') as f:
                f.write("[ Joysticks ]\n\n")
                
                for i in range(8):
                    # +2 because 0 and 1 are keyboards
                    val = self._controls.get_layout(i + 2) - 1
                    f.write(f"{JOYSTICKS[i]} = {val}\n")
                    
                for i in range(10):
                    f.write(f"\n[ {LAYOUT_NAMES[i]} ]\n\n")
                    
                    for j in range(NUM_OF_CONTROLS):
                        val = self._controls.get_control(i, j)
                        f.write(f"{CMD_NAMES[j]} = {val}\n")
                        
            return True
        except IOError:
            return False
