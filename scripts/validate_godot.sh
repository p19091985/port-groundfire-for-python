#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
GODOT_BIN="${GODOT_BIN:-$ROOT_DIR/tools/godot/Godot_v4.6.2-stable_linux.x86_64}"

if [[ ! -x "$GODOT_BIN" ]]; then
    printf 'Godot executable not found: %s\n' "$GODOT_BIN" >&2
    printf 'Set GODOT_BIN or install Godot locally under tools/godot/.\n' >&2
    exit 1
fi

"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --import
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/platform_capabilities.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/groundfire_theme.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/control_settings.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/browser_store.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/network_adapter.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/websocket_client.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/server_directory.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/terrain_model.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/tank_state.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/weapon_inventory.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/local_match_hud.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/local_match.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/online_match.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/main.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --check-only --script res://scripts/server_browser.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --script res://tests/browser_store_check.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --script res://tests/server_directory_check.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --script res://tests/terrain_collision_check.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --script res://tests/local_match_fidelity_check.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --script res://tests/online_reliability_check.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --script res://tests/runtime_smoke_check.gd
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --scene res://scenes/main.tscn --quit-after 3
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --scene res://scenes/local_match.tscn --quit-after 3
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --scene res://scenes/online_match.tscn --quit-after 3
