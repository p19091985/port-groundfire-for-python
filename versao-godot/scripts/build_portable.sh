#!/usr/bin/env bash
# ST06: build da edicao Godot (export desktop/web + companion) dentro da edicao.
set -Eeuo pipefail
EDITION_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$EDITION_DIR/scripts/launcher_common.sh"
godot_launcher_require_project
GODOT_BIN_FOUND=$(godot_launcher_find_binary)
echo "[build] Exportando Linux/Desktop para runtime/linux/ com $GODOT_BIN_FOUND"
"$GODOT_BIN_FOUND" --headless --path "$GODOT_LAUNCHER_PROJECT" --export-release "Linux Desktop" "$EDITION_DIR/runtime/linux/Groundfire.x86_64"
echo "[build] Exportando Web para runtime/web/"
"$GODOT_BIN_FOUND" --headless --path "$GODOT_LAUNCHER_PROJECT" --export-release "Web" "$EDITION_DIR/runtime/web/index.html"
echo "[build] Vendorizando headless:"
python3 "$EDITION_DIR/scripts/vendor_headless.py"
python3 "$EDITION_DIR/scripts/generate_runtime_manifest.py"
echo "[build] OK. ZIP com versao-godot/ no topo para distribuir."
