#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

if [ -n "${GF_SERVICE_PYTHON:-}" ]; then
    PYTHON_BIN=$GF_SERVICE_PYTHON
elif command -v python3 >/dev/null 2>&1 && python3 -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >/dev/null 2>&1; then
    PYTHON_BIN=python3
else
    PYTHON_BIN=python
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 || ! "$PYTHON_BIN" -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >/dev/null 2>&1; then
    echo "Python 3.10 ou superior não foi encontrado." >&2
    exit 3
fi

if [ ! -d .venv ]; then
    "$PYTHON_BIN" -m venv .venv
fi

if [ -x .venv/bin/python ]; then
    VENV_PYTHON=.venv/bin/python
elif [ -x .venv/Scripts/python.exe ]; then
    VENV_PYTHON=.venv/Scripts/python.exe
else
    echo "O ambiente virtual local está incompleto." >&2
    exit 3
fi

if ! "$VENV_PYTHON" -c "import fastapi, uvicorn, argon2, gf_service" >/dev/null 2>&1; then
    "$VENV_PYTHON" -m pip install --disable-pip-version-check -r requirements.lock
    "$VENV_PYTHON" -m pip install --disable-pip-version-check -e . --no-deps
fi

if [ "${1:-}" = "test" ]; then
    shift
    if ! "$VENV_PYTHON" -c "import pytest, httpx" >/dev/null 2>&1; then
        "$VENV_PYTHON" -m pip install --disable-pip-version-check -r requirements-test.lock
    fi
    exec "$VENV_PYTHON" -m pytest "$@"
fi

exec "$VENV_PYTHON" -m gf_service "$@"
