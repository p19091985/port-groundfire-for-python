"""Vendor headless companion into versao-godot/runtime/headless/ (ST04).

Fonte (desenvolvimento): runtime Python em <repo>/versao-python e rede canônica
em <repo>/groundfire-online-service/src/groundfire_net.
Destino versionado (standalone): <repo>/versao-godot/runtime/headless/.

Uso (a partir da raiz do repo em desenvolvimento):
    python versao-godot/scripts/vendor_headless.py
    python versao-godot/scripts/vendor_headless.py --check

O modo --check falha quando a copia versionada diverge da fonte
(gate de divergencia, ST06). A copia dispensa pygame: o servidor e o
gateway usam apenas stdlib + codigo vendored. Adaptacoes Godot explicitas
em _source_bytes preservam a referencia Python. Comparacao ignora
CRLF/LF (checkout Windows vs Linux).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

EDITION_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = EDITION_DIR.parent
PYTHON_EDITION = REPO_ROOT / "versao-python"
NETWORK_SOURCE = REPO_ROOT / "groundfire-online-service" / "src" / "groundfire_net"
TARGET_DIR = EDITION_DIR / "runtime" / "headless"

WRAPPERS = ("__init__.py", "server.py")

NET_FILES = (
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


def _canonical(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(_canonical(data)).hexdigest()


def _source_bytes(src: Path) -> bytes:
    """Apply audited Godot gateway fixes without changing the Python edition."""
    data = _canonical(src.read_bytes())
    if src != NETWORK_SOURCE / "websocket_gateway.py":
        return data
    patches = (
        (
            b'                                spectator=bool(message.get("spectator", False)),\n',
            b'                                spectator=bool(message.get("spectator", False)),\n'
            b'                                is_computer=bool(message.get("is_computer", False)),\n',
        ),
        (
            b'            or _optional_boolean_field(message, "spectator")\n',
            b'            or _optional_boolean_field(message, "spectator")\n'
            b'            or _optional_boolean_field(message, "is_computer")\n',
        ),
        (
            b"            await writer.wait_closed()\n",
            b"            with contextlib.suppress(ConnectionError):\n                await writer.wait_closed()\n",
        ),
    )
    for before, after in patches:
        if data.count(before) != 1:
            raise ValueError("Gateway source changed; review Godot adaptations before vendoring")
        data = data.replace(before, after)
    return data


def _pairs() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for name in WRAPPERS:
        pairs.append((PYTHON_EDITION / "groundfire" / name, TARGET_DIR / "groundfire" / name))
    for name in NET_FILES:
        pairs.append((NETWORK_SOURCE / name, TARGET_DIR / "groundfire_net" / name))
    src_root = PYTHON_EDITION / "src" / "groundfire"
    for path in sorted(src_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        pairs.append((path, TARGET_DIR / "src" / "groundfire" / path.relative_to(src_root)))
    return pairs


def _manifest_path() -> Path:
    return EDITION_DIR / "runtime-manifest.json"


def main() -> int:
    check_only = "--check" in sys.argv[1:]
    pairs = _pairs()
    missing = [src for src, _ in pairs if not src.is_file()]
    if missing:
        print(f"fonte nao encontrada: {missing[0]}", file=sys.stderr)
        return 2
    if check_only:
        try:
            manifest = json.loads(_manifest_path().read_text(encoding="utf-8"))
            expected = manifest.get("headless", {})
        except (OSError, json.JSONDecodeError) as exc:
            print(f"manifesto ilegivel: {exc}", file=sys.stderr)
            return 1
        failed = False
        for src, dst in pairs:
            rel = dst.relative_to(TARGET_DIR).as_posix()
            if not dst.is_file():
                print(f"ausente no companion: runtime/headless/{rel}", file=sys.stderr)
                failed = True
                continue
            if _sha256(_source_bytes(src)) != _sha256(dst.read_bytes()):
                print(f"divergente: runtime/headless/{rel}", file=sys.stderr)
                failed = True
            want = expected.get(f"runtime/headless/{rel}")
            if want and _sha256(dst.read_bytes()) != want:
                print(f"manifesto desatualizado: runtime/headless/{rel}", file=sys.stderr)
                failed = True
        return 1 if failed else 0

    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    hashes: dict[str, str] = {}
    for src, dst in pairs:
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = _source_bytes(src)
        dst.write_bytes(data)
        rel = dst.relative_to(TARGET_DIR).as_posix()
        hashes[f"runtime/headless/{rel}"] = _sha256(data)
    (TARGET_DIR / "README.md").write_text(
        "Companion headless versionado (ST04): servidor LAN autoritativo + "
        "gateway/directory sem pygame.\n"
        "Regenerado por scripts/vendor_headless.py a partir da edicao Python; "
        "nao editar a mao.\n"
        "Execucao fonte: PYTHONPATH=runtime/headless:runtime/headless/src "
        "python -m groundfire.server\n",
        encoding="utf-8",
    )
    try:
        manifest = json.loads(_manifest_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        manifest = {"schema": 1, "edition": "versao-godot"}
    manifest["headless"] = hashes
    _manifest_path().write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"vendored {len(hashes)} arquivos em {TARGET_DIR}")
    print(f"manifesto atualizado: {_manifest_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
