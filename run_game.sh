#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$SCRIPT_DIR
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
VERSION_CHECK='import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)'
RUNTIME_CHECK='import sys, pygame; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)'

test_interpreter() {
    interpreter=$1
    code=$2

    "$interpreter" -c "$code" >/dev/null 2>&1
}

find_python() {
    for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1 && test_interpreter "$candidate" "$VERSION_CHECK"; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    return 1
}

ensure_venv() {
    if [ -x "$VENV_PYTHON" ] && test_interpreter "$VENV_PYTHON" "$RUNTIME_CHECK"; then
        return 0
    fi

    if [ -x "$VENV_PYTHON" ]; then
        echo "Ambiente virtual existente ausente de dependencias ou com Python incompativel. Reconfigurando..."
    else
        echo "Ambiente virtual nao encontrado. Instalando dependencias..."
    fi

    PYTHON_BIN=$(find_python) || {
        echo "Python compativel nao encontrado no PATH." >&2
        echo "Use Python 3.10, 3.11, 3.12 ou 3.13." >&2
        return 1
    }

    echo "Usando interpretador: $PYTHON_BIN"

    if [ -x "$VENV_PYTHON" ] && ! test_interpreter "$VENV_PYTHON" "$VERSION_CHECK"; then
        echo "Ambiente virtual existente usa um Python incompativel. Recriando a .venv..."
        rm -rf "$PROJECT_DIR/.venv"
    fi

    if [ ! -x "$VENV_PYTHON" ]; then
        echo "Criando ambiente virtual..."
        "$PYTHON_BIN" -m venv "$PROJECT_DIR/.venv"
    fi

    echo "Atualizando pip..."
    "$VENV_PYTHON" -m pip install --upgrade pip

    echo "Instalando dependencias..."
    "$VENV_PYTHON" -m pip install -r "$PROJECT_DIR/requirements.txt"

    if [ ! -x "$VENV_PYTHON" ] || ! test_interpreter "$VENV_PYTHON" "$RUNTIME_CHECK"; then
        echo "Falha: o ambiente virtual nao foi criado corretamente." >&2
        return 1
    fi
}

ensure_venv
exec "$VENV_PYTHON" "$PROJECT_DIR/src/main.py"
