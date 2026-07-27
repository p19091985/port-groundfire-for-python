#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
TARGET="$SCRIPT_DIR/versao-python/iniciar-server.sh"

if [[ ! -f "$TARGET" ]]; then
    printf 'Falha: launcher Python nao encontrado: %s\n' "$TARGET" >&2
    exit 1
fi

exec "$TARGET" "$@"
