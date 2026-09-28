#!/bin/sh
if [ -z "${BASH_VERSION:-}" ]; then
    exec /usr/bin/env bash "$0" "$@"
fi
set -Eeuo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/scripts/launcher_common.sh"
godot_launcher_configure_python

export PYTHONPATH="$GODOT_EDITION_DIR/runtime/headless:$GODOT_EDITION_DIR/runtime/headless/src${PYTHONPATH:+:$PYTHONPATH}"
cmd=("$GROUNDFIRE_LAUNCHER_PYTHON" -m groundfire.server --log-events)
declare -a user_args=()
has_server_name=0
dry_run=0
while (($#)); do
    case "$1" in
        -A|--auto|--cli) shift ;;
        --menu) printf 'O servidor Godot nao tem menu local; use --help para opcoes.\n' >&2; exit 2 ;;
        --dry-run) dry_run=1; shift ;;
        --server-name) has_server_name=1; user_args+=("$1"); shift ;;
        *) user_args+=("$1"); shift ;;
    esac
done
((has_server_name == 0)) && cmd+=(--server-name 'Groundfire Godot LAN')
cmd+=("${user_args[@]}")

# ST04: companion congelado quando presente (portatil, sem Python).
if [[ "${GROUNDFIRE_FORCE_SOURCE:-0}" != "1" ]]; then
    runtime_server=""
    case "$(uname -s 2>/dev/null || printf unknown)" in
        Linux*) runtime_server="$GODOT_EDITION_DIR/runtime/linux/groundfire-server" ;;
        MINGW*|MSYS*|CYGWIN*) runtime_server="$GODOT_EDITION_DIR/runtime/windows/groundfire-server.exe" ;;
    esac
    if [[ -n "$runtime_server" && -x "$runtime_server" ]]; then
        cmd=("$runtime_server" "${cmd[@]:3}")
    fi
fi

if ((dry_run)); then
    display_cmd=("${cmd[@]}")
    for ((index = 0; index + 1 < ${#display_cmd[@]}; index++)); do
        if [[ "${display_cmd[index]}" == "--password" || "${display_cmd[index]}" == "--rcon-password" ]]; then
            display_cmd[index + 1]='<redacted>'
        fi
    done
    printf 'DRY-RUN server:'
    printf ' %q' "${display_cmd[@]}"
    printf '\n'
    exit 0
fi

# A edicao Godot usa o servidor autoritativo Python em primeiro plano.
exec "${cmd[@]}"
