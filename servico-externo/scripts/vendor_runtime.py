from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SERVICE_ROOT.parent
PYTHON_ROOT = REPOSITORY_ROOT / "versao-python" / "src"

GROUNDFIRE_FILES = (
    "__init__.py",
    "server.py",
    "app/__init__.py",
    "app/server.py",
    "core/__init__.py",
    "core/clock.py",
    "core/headless.py",
    "core/settings.py",
    "gameplay/__init__.py",
    "gameplay/constants.py",
    "gameplay/match_controller.py",
    "network/__init__.py",
    "network/browser.py",
    "network/client_state.py",
    "network/codec.py",
    "network/lan.py",
    "network/messages.py",
    "sim/__init__.py",
    "sim/match.py",
    "sim/registry.py",
    "sim/terrain.py",
    "sim/world.py",
)

GROUNDIFRE_NET_FILES = (
    "__init__.py",
    "browser.py",
    "codec.py",
    "directory_service.py",
    "discovery.py",
    "master.py",
    "observability.py",
    "server.py",
    "transport.py",
    "websocket_gateway.py",
)


def _copy(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    if source.name == "websocket_gateway.py":
        data = data.replace(b"from src.groundfire", b"from groundfire")
    destination.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    destination_root = SERVICE_ROOT / "src"
    for package in ("groundfire", "groundfire_net"):
        target = destination_root / package
        if target.exists():
            shutil.rmtree(target)

    manifest: dict[str, object] = {
        "schema": 1,
        "source_project": "Groundfire Python authoritative headless runtime",
        "files": {},
    }
    hashes: dict[str, str] = manifest["files"]  # type: ignore[assignment]
    for relative in GROUNDFIRE_FILES:
        source = PYTHON_ROOT / "groundfire" / relative
        target = destination_root / "groundfire" / relative
        hashes[f"src/groundfire/{relative}"] = _copy(source, target)
    for relative in GROUNDIFRE_NET_FILES:
        source = REPOSITORY_ROOT / "groundfire_net" / relative
        target = destination_root / "groundfire_net" / relative
        hashes[f"src/groundfire_net/{relative}"] = _copy(source, target)

    options_source = REPOSITORY_ROOT / "versao-python" / "conf" / "options.ini"
    options_target = SERVICE_ROOT / "conf" / "options.ini"
    hashes["conf/options.ini"] = _copy(options_source, options_target)

    encoded = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (SERVICE_ROOT / "runtime-manifest.json").write_text(encoded, encoding="utf-8", newline="\n")
    print(f"Vendored {len(hashes)} headless runtime files into {SERVICE_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
