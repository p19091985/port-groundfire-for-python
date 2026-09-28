"""ST06: gera runtime-manifest.json com SHA-256 da edicao Godot.

Uso:
    python scripts/generate_runtime_manifest.py  (dentro de versao-godot/)

Percorre godot/, scripts/ e runtime/ (exceto .venv, logs, userdata/).
Impede export com caminhos absolutos ou symlinks externos.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EDITION_DIR = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("godot", "scripts", "runtime")
SKIP_NAMES = {".venv", "__pycache__", "logs", "userdata", ".git", ".godot"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest_path = EDITION_DIR / "runtime-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        manifest = {"schema": 1, "edition": "versao-godot"}
    files: dict[str, str] = {}
    errors: list[str] = []
    for dirname in SCAN_DIRS:
        root = EDITION_DIR / dirname
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if any(part in SKIP_NAMES for part in path.relative_to(EDITION_DIR).parts):
                continue
            if path.is_symlink() and not str(path.resolve()).startswith(str(EDITION_DIR)):
                errors.append(f"symlink externo: {path.relative_to(EDITION_DIR).as_posix()}")
                continue
            rel = path.relative_to(EDITION_DIR).as_posix()
            files[rel] = _sha256(path)
    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        return 1
    manifest["schema"] = 1
    manifest["edition"] = "versao-godot"
    manifest["version"] = manifest.get("version", "0.25.0")
    manifest["files"] = files
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"manifesto atualizado: {len(files)} arquivos em {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
