from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable


class PlayerCommand(IntEnum):
    FIRE = 0
    WEAPONUP = 1
    WEAPONDOWN = 2
    JUMPJETS = 3
    SHIELD = 4
    TANKLEFT = 5
    TANKRIGHT = 6
    GUNLEFT = 7
    GUNRIGHT = 8
    GUNUP = 9
    GUNDOWN = 10


ALL_PLAYER_COMMANDS = tuple(PlayerCommand)


@dataclass(frozen=True)
class PlayerIntentFrame:
    commands: tuple[bool, ...]
    source: str
    simulation_time: float = 0.0

    @classmethod
    def empty(cls, *, source: str = "none", simulation_time: float = 0.0):
        return cls(tuple(False for _ in ALL_PLAYER_COMMANDS), source, simulation_time)

    @classmethod
    def from_iterable(cls, commands: Iterable[bool], *, source: str, simulation_time: float = 0.0):
        values = tuple(bool(value) for value in commands)
        if len(values) < len(ALL_PLAYER_COMMANDS):
            values = values + tuple(False for _ in range(len(ALL_PLAYER_COMMANDS) - len(values)))
        return cls(values[: len(ALL_PLAYER_COMMANDS)], source, simulation_time)

    def is_pressed(self, command: int | PlayerCommand) -> bool:
        command_index = int(command)
        if 0 <= command_index < len(self.commands):
            return self.commands[command_index]
        return False

    def to_dict(self) -> dict[str, bool]:
        return {command.name.lower(): self.is_pressed(command) for command in ALL_PLAYER_COMMANDS}


class PlayerIntentQueue:
    def __init__(self):
        self._frames: list[PlayerIntentFrame] = []

    def publish(self, frame: PlayerIntentFrame):
        self._frames.append(frame)

    def latest(self) -> PlayerIntentFrame | None:
        if not self._frames:
            return None
        return self._frames[-1]

    def drain(self) -> tuple[PlayerIntentFrame, ...]:
        drained = tuple(self._frames)
        self._frames.clear()
        return drained
