from __future__ import annotations

import json
import shlex
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO


class GroundfireEventLogger:
    """Callable event sink for human-readable or JSON Lines diagnostics."""

    def __init__(
        self,
        component: str,
        *,
        stream: TextIO | None = None,
        json_lines: bool = False,
        run_id: str | None = None,
    ):
        self.component = component
        self.stream = stream or sys.stdout
        self.json_lines = json_lines
        self.run_id = run_id or uuid.uuid4().hex

    def __call__(self, message: str) -> None:
        if self.json_lines:
            self.stream.write(json.dumps(parse_event_message(message, self.component, self.run_id), sort_keys=True))
            self.stream.write("\n")
        else:
            self.stream.write(f"[{self.component}] {message}\n")
        self.stream.flush()


class EventLogFile:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._handle: TextIO | None = None

    def __enter__(self) -> TextIO:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")
        return self._handle

    def __exit__(self, *_exc_info) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


def parse_event_message(message: str, component: str, run_id: str) -> dict[str, object]:
    tokens = _split_message(message)
    event = tokens[0] if tokens else "event"
    fields: dict[str, object] = {}
    for token in tokens[1:]:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        if key:
            fields[key] = _coerce_value(value)
    return {
        "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "level": "info",
        "component": component,
        "event": event,
        "run_id": run_id,
        "message": message,
        "fields": fields,
    }


def _split_message(message: str) -> list[str]:
    try:
        return shlex.split(message)
    except ValueError:
        return message.split()


def _coerce_value(value: str) -> object:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "none":
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value
