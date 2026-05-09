#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
GODOT_BIN="${GODOT_BIN:-$ROOT_DIR/tools/godot/Godot_v4.6.2-stable_linux.x86_64}"
TARGET="${1:-all}"
GODOT_TEMPLATE_VERSION="4.6.2.stable"
GODOT_TEMPLATE_DIR="${GODOT_TEMPLATE_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/godot/export_templates/$GODOT_TEMPLATE_VERSION}"
GODOT_TEMPLATE_PACKAGE_URL="${GODOT_TEMPLATE_PACKAGE_URL:-https://github.com/godotengine/godot/releases/download/4.6.2-stable/Godot_v4.6.2-stable_export_templates.tpz}"

if [[ ! -x "$GODOT_BIN" ]]; then
    printf 'Godot executable not found: %s\n' "$GODOT_BIN" >&2
    printf 'Set GODOT_BIN or install Godot locally under tools/godot/.\n' >&2
    exit 1
fi

case "$TARGET" in
    all|linux|web) ;;
    *)
        printf 'Usage: %s [all|linux|web]\n' "$0" >&2
        exit 2
        ;;
esac

require_template() {
    local path="$1"
    local label="$2"
    if [[ ! -f "$path" ]]; then
        printf 'Missing Godot %s export template: %s\n' "$label" "$path" >&2
        printf 'Install Godot export templates %s into:\n  %s\n' "$GODOT_TEMPLATE_VERSION" "$GODOT_TEMPLATE_DIR" >&2
        printf 'Official package:\n  %s\n' "$GODOT_TEMPLATE_PACKAGE_URL" >&2
        exit 3
    fi
}

if [[ "$TARGET" == "all" || "$TARGET" == "linux" ]]; then
    require_template "$GODOT_TEMPLATE_DIR/linux_release.x86_64" "Linux"
fi

if [[ "$TARGET" == "all" || "$TARGET" == "web" ]]; then
    require_template "$GODOT_TEMPLATE_DIR/web_nothreads_release.zip" "Web"
fi

"$ROOT_DIR/scripts/validate_godot.sh"
mkdir -p "$ROOT_DIR/build/godot" "$ROOT_DIR/build/godot-web"

if [[ "$TARGET" == "all" || "$TARGET" == "linux" ]]; then
    "$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --export-release "Linux Desktop"
fi

if [[ "$TARGET" == "all" || "$TARGET" == "web" ]]; then
    "$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --export-release "Web"
fi
