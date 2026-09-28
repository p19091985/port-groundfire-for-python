"""ST06: empacota uma edicao standalone em ZIP (pasta da edicao no topo).

Uso (a partir da raiz do repo):
    python scripts/package_edition.py versao-python
    python scripts/package_edition.py versao-godot --suffix windows

Gera dist/<edicao>-<versao>[-<sufixo>].zip + .sha256. Exclui caches e
ambientes locais (.venv, build/, __pycache__, logs/, .godot/) e
preserva o bit de execucao de runtime/linux/* e *.sh no ZIP.
"""

from __future__ import annotations

import argparse
import hashlib
import stat
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = REPO_ROOT / "dist"

EXCLUDE_DIRS = {".venv", "build", "__pycache__", "logs", ".godot", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
EXCLUDE_SUFFIXES = {".pyc"}


def _version(edition: Path) -> str:
    for line in (edition / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version"):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit(f"versao nao encontrada em {edition / 'pyproject.toml'}")


def _godot_version(edition: Path) -> str:
    import json

    manifest = json.loads((edition / "runtime-manifest.json").read_text(encoding="utf-8"))
    return str(manifest.get("version", "0.0.0"))


def _iter_files(edition: Path):
    for path in sorted(edition.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(edition)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if path.suffix in EXCLUDE_SUFFIXES or path.name in {".writetest", ".DS_Store"}:
            continue
        yield path, rel


def _is_executable(edition: Path, rel: Path) -> bool:
    parts = rel.parts
    if rel.suffix == ".sh":
        return True
    return len(parts) >= 3 and parts[0] == "runtime" and parts[1] == "linux"


def main() -> int:
    parser = argparse.ArgumentParser(description="Empacota edicao standalone em ZIP.")
    parser.add_argument("edition", choices=("versao-python", "versao-godot"))
    parser.add_argument("--suffix", default="")
    args = parser.parse_args()

    edition = REPO_ROOT / args.edition
    version = _version(edition) if args.edition == "versao-python" else _godot_version(edition)
    name = f"{args.edition}-{version}" + (f"-{args.suffix}" if args.suffix else "")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    out = DIST_DIR / f"{name}.zip"
    if out.exists():
        out.unlink()

    count = 0
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path, rel in _iter_files(edition):
            arcname = f"{edition.name}/{rel.as_posix()}"
            info = zipfile.ZipInfo(arcname)
            info.external_attr = (0o755 if _is_executable(edition, rel) else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
            count += 1
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    (DIST_DIR / f"{name}.zip.sha256").write_text(f"{digest}  {out.name}\n", encoding="utf-8")
    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"[zip] {out} ({count} arquivos, {size_mb:.1f} MB, sha256 {digest[:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
