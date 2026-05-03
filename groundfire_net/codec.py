from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, Callable


Decoder = Callable[[str, dict[str, Any]], object]


class JsonDataclassCodec:
    """Small message codec using UTF-8 JSON and dataclass payloads.

    The game owns the typed decoder because message classes are game-specific.
    """

    def __init__(self, decoder: Decoder):
        self._decoder = decoder

    def encode(self, message: object) -> bytes:
        return encode_envelope(message).encode("utf-8")

    def decode(self, payload: bytes) -> object:
        return decode_envelope(payload.decode("utf-8"), self._decoder)

    def encode_text(self, message: object) -> str:
        return encode_envelope(message)

    def decode_text(self, payload: str) -> object:
        return decode_envelope(payload, self._decoder)


def encode_envelope(message: object) -> str:
    return json.dumps(
        {
            "message_type": type(message).__name__,
            "payload": to_plain(message),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def decode_envelope(payload: str, decoder: Decoder) -> object:
    decoded = json.loads(payload)
    return decoder(str(decoded["message_type"]), decoded["payload"])


def to_plain(value: object):
    if is_dataclass(value):
        return {key: to_plain(raw) for key, raw in asdict(value).items()}
    if isinstance(value, tuple):
        return [to_plain(item) for item in value]
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_plain(raw) for key, raw in value.items()}
    return value
