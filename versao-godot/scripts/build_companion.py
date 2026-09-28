"""ST04/ST06: build do companion headless Godot (PyInstaller onedir).

Uso (dentro de versao-godot/, com qualquer Python 3.10+ que tenha
PyInstaller; o companion usa apenas stdlib + codigo vendored)::

    python scripts/build_companion.py --platform windows
    python scripts/build_companion.py --platform linux

Gera os executaveis groundfire-server e groundfire-web-gateway em
``runtime/<plataforma>/`` da propria edicao, ao lado do jogo Godot
exportado. Sem cross-compile: cada plataforma builda na sua maquina.

Pre-requisito: scripts/vendor_headless.py (fontes em runtime/headless/).
Apos gerar, rode scripts/generate_runtime_manifest.py.
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
HEADLESS_DIR = EDITION_DIR / "runtime" / "headless"
ENTRIES_DIR = EDITION_DIR / "scripts" / "portable"
BUILD_DIR = EDITION_DIR / "build"
WORK_DIR = BUILD_DIR / "work-companion"
DIST_DIR = BUILD_DIR / "dist-companion"
BUNDLE_NAME = "Companion"

ENTRIES: tuple[tuple[str, str], ...] = (
    ("groundfire-server", "entry_server"),
    ("groundfire-web-gateway", "entry_gateway"),
)


def _host_platform() -> str:
    return "windows" if os.name == "nt" else "linux"


def _hidden_imports() -> list[str]:
    # Varredura deterministica: nao depende de import resolver no build.
    roots = (
        (HEADLESS_DIR / "groundfire", "groundfire"),
        (HEADLESS_DIR / "groundfire_net", "groundfire_net"),
        (HEADLESS_DIR / "src", "src"),
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
    return sorted(set(found))


def _spec_source() -> str:
    scripts = [(name, str(ENTRIES_DIR / f"{stem}.py")) for name, stem in ENTRIES]
    scripts_repr = "[" + ", ".join(repr(p) for _, p in scripts) + "]"
    hidden_repr = "[" + ", ".join(repr(h) for h in _hidden_imports()) + "]"
    exe_blocks = "\n\n\n".join(
        f"exe_{stem} = EXE(\n"
        f"    pyz,\n"
        f"    _only({stem!r}),\n"
        f"    [],\n"
        f"    exclude_binaries=True,\n"
        f"    name={name!r},\n"
        f"    debug=False,\n"
        f"    strip=False,\n"
        f"    upx=False,\n"
        f"    console=True,\n"
        f")"
        for name, stem in ENTRIES
    )
    exe_list = ", ".join(f"exe_{stem}" for _, stem in ENTRIES)
    return f'''# -*- mode: python ; coding: utf-8 -*-
# Gerado por scripts/build_companion.py (ST04). Nao editar a mao.
HEADLESS = {str(HEADLESS_DIR)!r}
SRC = {str(HEADLESS_DIR / "src")!r}

a = Analysis(
    {scripts_repr},
    pathex=[HEADLESS, SRC],
    binaries=[],
    datas=[],
    hiddenimports={hidden_repr},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc", "doctest", "test", "setuptools", "pygame", "pygame_gui"],
    noarchive=False,
)
pyz = PYZ(a.pure)


def _only(stem):
    matches = [s for s in a.scripts if s[0] == stem]
    assert matches, stem
    return matches


{exe_blocks}

coll = COLLECT(
    {exe_list},
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name={BUNDLE_NAME!r},
)
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Build do companion headless Godot.")
    parser.add_argument("--platform", choices=("linux", "windows"), default=_host_platform())
    args = parser.parse_args()

    host = _host_platform()
    if args.platform != host:
        print(
            f"[companion] Plataforma {args.platform!r} pedida no host {host!r}: "
            "o PyInstaller nao faz cross-compile.",
            file=sys.stderr,
        )
        return 2
    if importlib.util.find_spec("PyInstaller") is None:
        print("[companion] PyInstaller nao encontrado. Instale com `pip install pyinstaller`.", file=sys.stderr)
        return 2
    probe = HEADLESS_DIR / "groundfire_net" / "server.py"
    if not probe.is_file():
        print(f"[companion] Companion nao vendored. Rode scripts/vendor_headless.py primeiro ({probe}).", file=sys.stderr)
        return 2

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    spec_path = BUILD_DIR / "companion.spec"
    spec_path.write_text(_spec_source(), encoding="utf-8")
    print(f"[companion] spec: {spec_path}")
    cmd = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--log-level", "WARN", "--workpath", str(WORK_DIR),
        "--distpath", str(DIST_DIR), str(spec_path),
    ]
    print("[companion] executando PyInstaller...")
    completed = subprocess.run(cmd, cwd=EDITION_DIR)
    if completed.returncode != 0:
        print("[companion] PyInstaller falhou.", file=sys.stderr)
        return completed.returncode

    bundle = DIST_DIR / BUNDLE_NAME
    suffix = ".exe" if args.platform == "windows" else ""
    missing = [name for name, _ in ENTRIES if not (bundle / f"{name}{suffix}").is_file()]
    if missing:
        print(f"[companion] Executaveis ausentes no bundle: {missing}", file=sys.stderr)
        return 1

    target = EDITION_DIR / "runtime" / args.platform
    target.mkdir(parents=True, exist_ok=True)
    for name, _ in ENTRIES:
        shutil.copy2(bundle / f"{name}{suffix}", target / f"{name}{suffix}")
    internal_src = bundle / "_internal"
    internal_dst = target / "_internal"
    if internal_src.is_dir():
        if internal_dst.exists():
            shutil.rmtree(internal_dst)
        shutil.copytree(internal_src, internal_dst)
    print(f"[companion] Instalado em {target} (preserva o jogo Godot exportado)")
    print("[companion] Proximo passo: python scripts/generate_runtime_manifest.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
