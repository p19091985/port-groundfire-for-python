"""Vendor groundfire_net into versao-python/ (ST01).

Fonte compartilhada (desenvolvimento): <repo>/groundfire_net/
Destino versionado (standalone): <repo>/versao-python/groundfire_net/

Uso (a partir da raiz do repo em desenvolvimento):
    python versao-python/scripts/vendor_groundfire_net.py
    python versao-python/scripts/vendor_groundfire_net.py --check

O modo --check falha quando a copia versionada diverge da fonte,
funcionando como gate de divergencia (ST06). A copia versionada deve
existir antes de testar ou distribuir a pasta versao-python/ isolada.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

EDITION_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = EDITION_DIR.parent
SOURCE_DIR = REPO_ROOT / "groundfire_net"
TARGET_DIR = EDITION_DIR / "groundfire_net"

FILES = (
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(path: Path) -> str:
    # Compara conteudo ignorando CRLF/LF: o checkout Windows (autocrlf)
    # grava CRLF e o Linux grava LF no mesmo conteudo Python.
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def _manifest() -> dict:
    return json.loads((EDITION_DIR / "runtime-manifest.json").read_text(encoding="utf-8"))


def main() -> int:
    check_only = "--check" in sys.argv[1:]
    if not SOURCE_DIR.is_dir():
        print(f"fonte nao encontrada: {SOURCE_DIR}", file=sys.stderr)
        return 2
    if check_only:
        try:
            manifest = _manifest()
            files = manifest.get("groundfire_net", {})
        except (OSError, json.JSONDecodeError) as exc:
            print(f"manifesto ilegivel: {exc}", file=sys.stderr)
            return 1
        failed = False
        for name in FILES:
            src = SOURCE_DIR / name
            dst = TARGET_DIR / name
            if not dst.is_file():
                print(f"ausente na edicao: groundfire_net/{name}", file=sys.stderr)
                failed = True
                continue
            if _canonical_sha256(src) != _canonical_sha256(dst):
                print(f"divergente: groundfire_net/{name}", file=sys.stderr)
                failed = True
            expected = files.get(f"groundfire_net/{name}")
            if expected and _canonical_sha256(dst) != expected:
                print(f"manifesto desatualizado: groundfire_net/{name}", file=sys.stderr)
                failed = True
        return 1 if failed else 0

    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    TARGET_DIR.mkdir(parents=True)
    hashes: dict[str, str] = {}
    for name in FILES:
        src = SOURCE_DIR / name
        dst = TARGET_DIR / name
        dst.write_bytes(src.read_bytes())
        hashes[f"groundfire_net/{name}"] = _canonical_sha256(dst)
    print(f"vendored {len(hashes)} arquivos em {TARGET_DIR}")
    manifest_path = EDITION_DIR / "runtime-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        manifest = {"schema": 1, "edition": "versao-python"}
    manifest["groundfire_net"] = hashes
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"manifesto atualizado: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
