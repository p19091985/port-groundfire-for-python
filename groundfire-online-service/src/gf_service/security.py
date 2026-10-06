from __future__ import annotations

import hashlib
import re
import secrets
import unicodedata

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_PASSWORD_HASHER = PasswordHasher(time_cost=3, memory_cost=65_536, parallelism=2)
_HANDLE_PATTERN = re.compile(r"^[a-z0-9_]{3,24}$")


def normalize_handle(value: str) -> str:
    handle = unicodedata.normalize("NFKC", value).strip().casefold()
    if not _HANDLE_PATTERN.fullmatch(handle):
        raise ValueError("handle must contain 3-24 lowercase letters, numbers or underscores")
    return handle


def validate_display_name(value: str) -> str:
    name = unicodedata.normalize("NFKC", value).strip()
    if not 1 <= len(name) <= 32 or any(unicodedata.category(char).startswith("C") for char in name):
        raise ValueError("display_name must contain 1-32 printable characters")
    return name


def validate_password(value: str) -> str:
    if len(value) < 10 or len(value) > 256:
        raise ValueError("password must contain 10-256 characters")
    return value


def hash_password(value: str) -> str:
    return _PASSWORD_HASHER.hash(validate_password(value))


def verify_password(encoded: str, value: str) -> bool:
    try:
        return _PASSWORD_HASHER.verify(encoded, value)
    except (VerifyMismatchError, InvalidHashError):
        return False


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(12)}"


def new_secret(bytes_count: int = 32) -> str:
    return secrets.token_urlsafe(bytes_count)


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
