from __future__ import annotations

from pathlib import Path


class ReadIniFile:
    def __init__(self, config_file: str):
        self._entries: dict[str, str] = {}
        path = Path(config_file)
        if not path.exists():
            return

        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                section = ""
                for raw_line in handle:
                    line = raw_line.rstrip("\n")
                    if not line:
                        continue
                    if line[0] in {"#", ";"}:
                        continue
                    if line[0] == "[":
                        end_pos = line.find("]")
                        if end_pos != -1:
                            section = line[1:end_pos]
                        continue
                    pos_equal = line.find("=")
                    if pos_equal == -1:
                        continue
                    name = line[:pos_equal].strip(" \t")
                    value = line[pos_equal + 1 :].strip(" \t")
                    self._entries[f"{section}/{name}"] = value
        except OSError:
            return

    def get_float(self, section: str, entry: str, default_value: float) -> float:
        key = f"{section}/{entry}"
        if key in self._entries:
            try:
                return float(self._entries[key])
            except ValueError:
                return default_value
        return default_value

    def get_int(self, section: str, entry: str, default_value: int) -> int:
        key = f"{section}/{entry}"
        if key in self._entries:
            try:
                return int(self._entries[key])
            except ValueError:
                return default_value
        return default_value

    def get_string(self, section: str, entry: str, default_value: str) -> str:
        return self._entries.get(f"{section}/{entry}", default_value)


class WriteIniFile:
    def __init__(self):
        self._entries: dict[str, dict[str, str]] = {}

    def add_section(self, section: str):
        self._entries.setdefault(section, {})

    def put_float(self, section: str, entry: str, value: float) -> bool:
        if section not in self._entries:
            return False
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
        path = Path(config_file)
        try:
            with path.open("w", encoding="utf-8") as handle:
                for section_name, section_data in self._entries.items():
                    handle.write(f"[{section_name}]\n")
                    for key, value in section_data.items():
                        handle.write(f"{key}={value}\n")
                    handle.write("\n")
        except OSError:
            return


def set_ini_value(config_file: str | Path, section: str, entry: str, value: str) -> None:
    path = Path(config_file)
    lines: list[str]
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        lines = []

    section_header = f"[{section}]"
    entry_prefix = f"{entry}="
    output: list[str] = []
    in_target_section = False
    section_found = False
    entry_written = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_target_section and not entry_written:
                output.append(f"{entry}={value}")
                entry_written = True
            current_section = stripped[1:-1].strip()
            in_target_section = current_section == section
            if in_target_section:
                section_found = True
            output.append(line)
            continue

        if in_target_section and stripped.startswith(entry_prefix):
            output.append(f"{entry}={value}")
            entry_written = True
            continue

        output.append(line)

    if not section_found:
        if output and output[-1] != "":
            output.append("")
        output.append(section_header)
        output.append(f"{entry}={value}")
    elif in_target_section and not entry_written:
        output.append(f"{entry}={value}")

    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
