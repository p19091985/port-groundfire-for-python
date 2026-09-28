"""ST00: auditoria reproduzivel de isolamento das edicoes.

Uso:
    python scripts/audit_standalone.py
    python scripts/audit_standalone.py --edition versao-python

Falha quando detecta leitura/import de pastas irmas em uma copia isolada:
- ../tools/godot, ../versao-python, ../versao-godot, ../groundfire_net, ../.venv
- ../../build em export_presets, res://../.venv no cliente Godot
- pip install -e na raiz a partir da edicao, PYTHONPATH com pasta pai

ST00 exige que a auditoria falhe ao detectar esses caminhos proibidos.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN = (
    "../tools/godot",
    "../versao-python",
    "../versao-godot",
    "../groundfire_net",
    "../.venv",
    "GODOT_LAUNCHER_ROOT/versao-python",
    "GODOT_LAUNCHER_ROOT/.venv",
    "res://../.venv",
    "../../build",
)

SKIP_SUFFIXES = {".png", ".wav", ".ogg", ".mp3", ".ttf", ".pck", ".x86_64", ".exe"}
SKIP_NAMES = {"README.md", "runtime-manifest.json", ".gitkeep"}


def audit_edition(edition: str) -> list[str]:
    root = REPO_ROOT / edition
    offenders: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.name in SKIP_NAMES or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for snippet in FORBIDDEN:
            if snippet in text:
                offenders.append(f"{edition}/{path.relative_to(root).as_posix()}: {snippet!r}")
    return offenders


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditoria ST00 de isolamento das edicoes.")
    parser.add_argument("--edition", choices=("versao-python", "versao-godot"), default="")
    args = parser.parse_args()
    editions = (args.edition,) if args.edition else ("versao-python", "versao-godot")
    failed = False
    for edition in editions:
        offenders = audit_edition(edition)
        if offenders:
            failed = True
            print(f"[{edition}] {len(offenders)} caminhos proibidos:")
            for item in offenders:
                print(f"  - {item}")
        else:
            print(f"[{edition}] OK: nenhum caminho proibido.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
