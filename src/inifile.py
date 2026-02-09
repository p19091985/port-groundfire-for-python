import os

class ReadIniFile:
    def __init__(self, config_file: str):
        self._entries = {} # type: dict[str, str]
        
        if not os.path.exists(config_file):
            return

        try:
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                in_section = ""
                for line in f:
                    # getline in C++ removes the delimiter (newline), so we rstrip it.
                    line = line.rstrip('\n')
                    
                    if not line:
                        continue
                    
                    # Ignore comment lines - strict check at index 0 as in C++
                    if line[0] == '#' or line[0] == ';':
                        continue
                    
                    # A new section
                    if line[0] == '[':
                        end_pos = line.find(']')
                        if end_pos != -1:
                            # C++: substr(1, find(']') - 1);
                            # find returns index, so length is index - 1.
                            # substr(start, length).
                            # Python slice: [start : start + length] -> [1 : 1 + (end_pos - 1)] -> [1 : end_pos]
                            in_section = line[1:end_pos]
                        continue
                    
                    # Get a value
                    pos_equal = line.find('=')
                    if pos_equal != -1:
                        name = line[:pos_equal]
                        value = line[pos_equal+1:]
                        
                        # Strip whitespace from beginning and end
                        name = name.strip(" \t")
                        value = value.strip(" \t")
                        
                        # Insert entry
                        self._entries[f"{in_section}/{name}"] = value
        except IOError:
            # If file cannot be opened, we just return (as C++ does)
            pass

    def get_float(self, section: str, entry: str, default_value: float) -> float:
        """Returns an ini file entry as a floating point number."""
        key = f"{section}/{entry}"
        if key in self._entries:
            try:
                return float(self._entries[key])
            except ValueError:
                return default_value
        return default_value

    def get_int(self, section: str, entry: str, default_value: int) -> int:
        """Returns an ini file entry as an integer number."""
        key = f"{section}/{entry}"
        if key in self._entries:
            try:
                return int(self._entries[key])
            except ValueError:
                return default_value
        return default_value

    def get_string(self, section: str, entry: str, default_value: str) -> str:
        """Returns an ini file entry as a string."""
        key = f"{section}/{entry}"
        return self._entries.get(key, default_value)


class WriteIniFile:
    def __init__(self):
        self._entries = {} # type: dict[str, dict[str, str]]

    def add_section(self, section: str):
        if section not in self._entries:
            self._entries[section] = {}

    def put_float(self, section: str, entry: str, value: float) -> bool:
        if section not in self._entries:
            return False
        # Matches C++ snprintf(buffer, 16, "%f", value)
        self._entries[section][entry] = f"{value:f}"
        return True

    def put_int(self, section: str, entry: str, value: int) -> bool:
        if section not in self._entries:
            return False
        self._entries[section][entry] = str(value)
        return True

    def put_string(self, section: str, entry: str, value: str) -> bool:
        if section not in self._entries:
            return False
        self._entries[section][entry] = value
        return True

    def write(self, config_file: str) -> None:
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                for section_name, section_data in self._entries.items():
                    f.write(f"[{section_name}]\n")
                    for key, value in section_data.items():
                        f.write(f"{key}={value}\n")
                    f.write("\n")
        except IOError:
            pass
