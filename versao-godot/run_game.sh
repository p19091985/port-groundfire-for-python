#!/bin/sh
if [ -z "${BASH_VERSION:-}" ]; then
    exec /usr/bin/env bash "$0" "$@"
fi
set -Eeuo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/scripts/launcher_common.sh"
godot_launcher_require_project
GODOT_EXECUTABLE=$(godot_launcher_find_binary)
exec "$GODOT_EXECUTABLE" --path "$GODOT_LAUNCHER_PROJECT" "$@"
