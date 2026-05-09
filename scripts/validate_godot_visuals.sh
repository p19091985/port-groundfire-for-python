#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
GODOT_BIN="${GODOT_BIN:-$ROOT_DIR/tools/godot/Godot_v4.6.2-stable_linux.x86_64}"
MODE="${1:---check}"

case "$MODE" in
    --check)
        UPDATE_GOLDENS=0
        ;;
    --update-goldens)
        UPDATE_GOLDENS=1
        ;;
    *)
        printf 'Usage: %s [--check|--update-goldens]\n' "$0" >&2
        exit 2
        ;;
esac

if [[ ! -x "$GODOT_BIN" ]]; then
    printf 'Godot executable not found: %s\n' "$GODOT_BIN" >&2
    printf 'Set GODOT_BIN or install Godot locally under tools/godot/.\n' >&2
    exit 1
fi

if [[ "$UPDATE_GOLDENS" == "1" ]]; then
    GODOT_VISUAL_UPDATE=1 "$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --script res://tests/visual_golden_check.gd
else
    "$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --script res://tests/visual_golden_check.gd
fi
