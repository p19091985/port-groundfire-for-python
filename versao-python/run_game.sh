#!/usr/bin/env sh
# shellcheck shell=sh
# Groundfire Python edition — launcher standalone (ST01/ST02).
# Usa somente arquivos dentro desta pasta (versao-python/). Nao le ../,
# nao importa groundfire_net da raiz e nao usa .venv de outra pasta.
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
EDITION_DIR="$SCRIPT_DIR"
VENV_PYTHON="$EDITION_DIR/.venv/bin/python"
VENV_GROUNDFIRE="$EDITION_DIR/.venv/bin/groundfire"
USERDATA_DIR="${GROUNDFIRE_USERDATA_DIR:-$EDITION_DIR/userdata}"
VERSION_CHECK='import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 14) else 1)'
RUNTIME_CHECK='import os, sys; sys.path=[p for p in sys.path if p not in ("", os.getcwd())]; import pygame, groundfire_net; from importlib.metadata import version; version("groundfire"); raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 14) else 1)'

die() {
    echo "$1" >&2
    exit "${2:-1}"
}

check_userdata_writable() {
    mkdir -p "$USERDATA_DIR" 2>/dev/null || die "Erro: pasta userdata nao e gravavel: $USERDATA_DIR"
    if ! touch "$USERDATA_DIR/.writetest" 2>/dev/null; then
        die "Erro: pasta userdata nao e gravavel: $USERDATA_DIR"
    fi
    rm -f "$USERDATA_DIR/.writetest"
}

runtime_binary_for_platform() {
    # ST02: prefere binario portatil interno quando presente.
    os_name=$(uname -s 2>/dev/null || printf 'unknown')
    case "$os_name" in
        Linux*) printf '%s\n' "$EDITION_DIR/runtime/linux/Groundfire" ;;
        MINGW*|MSYS*|CYGWIN*) printf '%s\n' "$EDITION_DIR/runtime/windows/Groundfire.exe" ;;
        *) printf '%s\n' "$EDITION_DIR/runtime/linux/Groundfire" ;;
    esac
}

test_interpreter() {
    interpreter=$1
    code=$2
    "$interpreter" -c "$code" >/dev/null 2>&1
}

find_python() {
    for candidate in python3.14 python3.13 python3.12 python3.11 python3.10 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1 && test_interpreter "$candidate" "$VERSION_CHECK"; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

ensure_venv() {
    if [ -x "$VENV_PYTHON" ] && [ -x "$VENV_GROUNDFIRE" ] && test_interpreter "$VENV_PYTHON" "$RUNTIME_CHECK"; then
        return 0
    fi
    if [ -x "$VENV_PYTHON" ]; then
        echo "Ambiente virtual existente ausente do sistema, dependencias ou com Python incompativel. Reconfigurando..."
    else
        echo "Ambiente virtual nao encontrado. Instalando o sistema..."
    fi
    PYTHON_BIN=$(find_python) || die "Python compativel nao encontrado no PATH. Use Python 3.10, 3.11, 3.12, 3.13 ou 3.14."
    echo "Usando interpretador: $PYTHON_BIN"
    if [ -x "$VENV_PYTHON" ] && ! test_interpreter "$VENV_PYTHON" "$VERSION_CHECK"; then
        echo "Ambiente virtual existente usa um Python incompativel. Recriando a .venv..."
        rm -rf "$EDITION_DIR/.venv"
    fi
    if [ ! -x "$VENV_PYTHON" ]; then
        echo "Criando ambiente virtual..."
        "$PYTHON_BIN" -m venv "$EDITION_DIR/.venv"
    fi
    if [ "${GROUNDFIRE_SKIP_PIP_UPGRADE:-0}" = "1" ]; then
        echo "Upgrade de pip ignorado por GROUNDFIRE_SKIP_PIP_UPGRADE=1."
    else
        echo "Atualizando pip..."
        "$VENV_PYTHON" -m pip install --upgrade pip
    fi
    install_project
    if [ ! -x "$VENV_PYTHON" ] || [ ! -x "$VENV_GROUNDFIRE" ] || ! test_interpreter "$VENV_PYTHON" "$RUNTIME_CHECK"; then
        echo "Falha: o ambiente virtual nao foi criado corretamente." >&2
        return 1
    fi
}

install_project() {
    echo "Instalando Groundfire (edicao versao-python) em modo editavel..."
    if "$VENV_PYTHON" -m pip install --only-binary=pygame -e "$EDITION_DIR"; then
        return 0
    fi
    echo "Instalacao com wheel precompilado do pygame falhou. Tentando fallback generico..."
    "$VENV_PYTHON" -m pip install -e "$EDITION_DIR"
}

check_userdata_writable

# Pacote portatil (ST02): executa binario interno sem Python/pip/rede.
RUNTIME_BIN=$(runtime_binary_for_platform)
if [ -x "$RUNTIME_BIN" ] && [ "${GROUNDFIRE_FORCE_SOURCE:-0}" != "1" ]; then
    export GROUNDFIRE_EDITION_DIR="$EDITION_DIR"
    export GROUNDFIRE_USERDATA_DIR="$USERDATA_DIR"
    exec "$RUNTIME_BIN" "$@"
fi

ensure_venv
export PYTHONPATH="$EDITION_DIR:$EDITION_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
export GROUNDFIRE_EDITION_DIR="$EDITION_DIR"
export GROUNDFIRE_USERDATA_DIR="$USERDATA_DIR"
exec "$VENV_GROUNDFIRE" "$@"
