"""ST02/ST05: resolucao central de caminhos da edicao standalone.

Ordem de precedencia: variaveis dos launchers (GROUNDFIRE_EDITION_DIR /
GROUNDFIRE_USERDATA_DIR) > executavel congelado (PyInstaller onedir em
<edicao>/runtime/<plataforma>/<binario>) > layout de fontes em
desenvolvimento. Nao importa nenhum modulo do jogo (seguro em boot).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def edition_dir() -> Path:
    """Raiz da edicao versao-python/, em fonte ou pacote portatil."""
    override = os.environ.get("GROUNDFIRE_EDITION_DIR")
    if override:
        return Path(override)
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        if len(exe.parents) >= 3:
            return exe.parents[2]
        return exe.parent
    return Path(__file__).resolve().parents[3]


def userdata_dir() -> Path:
    """Diretorio portatil de dados (preferencias, saves, logs, livro)."""
    override = os.environ.get("GROUNDFIRE_USERDATA_DIR")
    if override:
        return Path(override)
    return edition_dir() / "userdata"
