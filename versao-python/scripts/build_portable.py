"""ST02/ST06: build do pacote portatil Python (PyInstaller onedir multi-EXE).

Uso (dentro de versao-python/, com a .venv local da edicao)::

    python scripts/build_portable.py --platform windows
    python scripts/build_portable.py --platform linux

Gera um unico diretorio compartilhado com os 5 executaveis (cliente,
servidor, master, gateway e directory) e instala o conteudo em
``runtime/<plataforma>/`` da propria edicao. O PyInstaller nao faz
cross-compile: o build de cada plataforma precisa rodar nela (para
Linux, rode este mesmo comando numa maquina/VM/WSL com Linux).

Apos gerar, rode ``scripts/generate_runtime_manifest.py`` e empacote o
ZIP com ``versao-python/`` como pasta superior.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

EDITION_DIR = Path(__file__).resolve().parents[1]
ENTRIES_DIR = EDITION_DIR / "scripts" / "portable"
BUILD_DIR = EDITION_DIR / "build"
WORK_DIR = BUILD_DIR / "work"
DIST_DIR = BUILD_DIR / "dist"
BUNDLE_NAME = "Groundfire"

# (nome do executavel, stem do stub em scripts/portable/).
ENTRIES: tuple[tuple[str, str], ...] = (
    ("Groundfire", "entry_client"),
    ("groundfire-server", "entry_server"),
    ("groundfire-master", "entry_master"),
    ("groundfire-web-gateway", "entry_gateway"),
    ("groundfire-directory", "entry_directory"),
)


def _host_platform() -> str:
    return "windows" if os.name == "nt" else "linux"


def _hidden_imports() -> list[str]:
    # Varredura deterministica do codigo da edicao + pacotes de terceiros
    # instalados (pygame_gui/pygame_menu sao importados via importlib).
    roots = (
        (EDITION_DIR / "groundfire", "groundfire"),
        (EDITION_DIR / "groundfire_net", "groundfire_net"),
        (EDITION_DIR / "src", "src"),
    )
    found: list[str] = []
    for root, top in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(root).with_suffix("")
            parts = [top, *[p for p in rel.parts if p != "__init__"]]
            found.append(".".join(parts))
    for pkg in ("pygame", "pygame_gui", "pygame_menu"):
        if importlib.util.find_spec(pkg) is not None:
            found.append(pkg)
    return sorted(set(found))


def _spec_source() -> str:
    entry_scripts = [str(ENTRIES_DIR / f"{stem}.py") for _, stem in ENTRIES]
    scripts_repr = "[" + ", ".join(repr(e) for e in entry_scripts) + "]"
    hidden_repr = "[" + ", ".join(repr(h) for h in _hidden_imports()) + "]"
    return f'''# -*- mode: python ; coding: utf-8 -*-
# Gerado por scripts/build_portable.py (ST02). Nao editar a mao.
from PyInstaller.utils.hooks import collect_data_files

EDITION = {str(EDITION_DIR)!r}
SRC = {str(EDITION_DIR / "src")!r}

_data = []
for _pkg in ("pygame_gui", "pygame_menu", "pygame"):
    try:
        _data += collect_data_files(_pkg)
    except Exception:
        pass

a = Analysis(
    {scripts_repr},
    pathex=[EDITION, SRC],
    binaries=[],
    datas=_data,
    hiddenimports={hidden_repr},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc", "doctest", "test", "setuptools"],
    noarchive=False,
)
pyz = PYZ(a.pure)


def _only(stem):
    matches = [s for s in a.scripts if s[0] == stem]
    assert matches, stem
    return matches


{_exe_blocks()}

coll = COLLECT(
    {", ".join(f"exe_{stem}" for _, stem in ENTRIES)},
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name={BUNDLE_NAME!r},
)
'''


def _exe_blocks() -> str:
    blocks = []
    for exe_name, stem in ENTRIES:
        blocks.append(
            f"exe_{stem} = EXE(\n"
            f"    pyz,\n"
            f"    _only({stem!r}),\n"
            f"    [],\n"
            f"    exclude_binaries=True,\n"
            f"    name={exe_name!r},\n"
            f"    debug=False,\n"
            f"    bootloader_ignore_signals=False,\n"
            f"    strip=False,\n"
            f"    upx=False,\n"
            f"    console=True,\n"
            f")"
        )
    return "\n\n\n".join(blocks)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build portatil da edicao Python.")
    parser.add_argument("--platform", choices=("linux", "windows"), default=_host_platform())
    args = parser.parse_args()

    host = _host_platform()
    if args.platform != host:
        print(
            f"[build] Plataforma {args.platform!r} pedida no host {host!r}: "
            "o PyInstaller nao faz cross-compile.",
            file=sys.stderr,
        )
        print(
            "[build] Para Linux, copie versao-python/ para uma maquina Linux, "
            "crie a .venv local, instale a edicao e rode este script com "
            "--platform linux.",
        )
        return 2
    if importlib.util.find_spec("PyInstaller") is None:
        print(
            "[build] PyInstaller nao encontrado nesta .venv. Instale com "
            "`pip install pyinstaller` dentro da .venv da edicao e repita.",
            file=sys.stderr,
        )
        return 2
    for _, stem in ENTRIES:
        stub = ENTRIES_DIR / f"{stem}.py"
        if not stub.is_file():
            print(f"[build] Stub ausente: {stub}", file=sys.stderr)
            return 2

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    spec_path = BUILD_DIR / "groundfire.spec"
    spec_path.write_text(_spec_source(), encoding="utf-8")
    print(f"[build] spec: {spec_path}")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--log-level",
        "WARN",
        "--workpath",
        str(WORK_DIR),
        "--distpath",
        str(DIST_DIR),
        str(spec_path),
    ]
    print("[build] executando PyInstaller (pode levar varios minutos)...")
    completed = subprocess.run(cmd, cwd=EDITION_DIR)
    if completed.returncode != 0:
        print("[build] PyInstaller falhou.", file=sys.stderr)
        return completed.returncode

    bundle = DIST_DIR / BUNDLE_NAME
    suffix = ".exe" if args.platform == "windows" else ""
    missing = [name for name, _ in ENTRIES if not (bundle / f"{name}{suffix}").is_file()]
    if missing:
        print(f"[build] Executaveis ausentes no bundle: {missing}", file=sys.stderr)
        return 1

    target = EDITION_DIR / "runtime" / args.platform
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(bundle, target)
    print(f"[build] Instalado em {target}")
    print("[build] Proximo passo: python scripts/generate_runtime_manifest.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
