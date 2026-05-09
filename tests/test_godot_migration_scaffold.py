import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GODOT_ROOT = PROJECT_ROOT / "godot"


def test_godot_project_declares_main_scene_and_platform_autoload():
    project = (GODOT_ROOT / "project.godot").read_text(encoding="utf-8")

    assert 'run/main_scene="res://scenes/main.tscn"' in project
    assert 'config/server_directory_url=""' in project
    assert 'config/server_directory_environment="dev"' in project
    assert 'config/server_directory_url_dev=""' in project
    assert 'config/server_directory_url_staging=""' in project
    assert 'config/server_directory_url_production=""' in project
    assert 'PlatformCapabilities="*res://scripts/platform_capabilities.gd"' in project
    assert 'renderer/rendering_method="gl_compatibility"' in project
    assert "gf_aim_left" in project
    assert "gf_power_up" in project
    assert "gf_fire" in project
    assert "gf_weapon_next" in project
    assert "gf_pause" in project
    assert "gf_move_left" in project
    assert "gf_move_right" in project
    assert "gf_weapon_prev" in project
    assert "gf_jump" in project
    assert (GODOT_ROOT / "assets" / "logo.png").exists()
    assert (GODOT_ROOT / "assets" / "menuback.png").exists()


def test_groundfire_theme_defines_shared_visual_language():
    script = (GODOT_ROOT / "scripts" / "groundfire_theme.gd").read_text(encoding="utf-8")

    assert 'COLOR_BG := Color("#07131e")' in script
    assert 'COLOR_ACCENT := Color("#a85d00")' in script
    assert "static func panel_style" in script
    assert "static func apply_button" in script
    assert "static func row_style" in script
    assert "static func modal_backdrop_style" in script


def test_platform_capabilities_hide_native_networking_on_web():
    script = (GODOT_ROOT / "scripts" / "platform_capabilities.gd").read_text(encoding="utf-8")

    assert 'OS.has_feature("web")' in script
    assert 'FEATURE_LAN_DISCOVERY := "lan_discovery"' in script
    assert 'FEATURE_UDP_TRANSPORT := "udp_transport"' in script
    assert 'FEATURE_DEDICATED_SERVER_TOOLS := "dedicated_server_tools"' in script
    assert "static func supports_for_platform" in script
    assert "static func visible_server_browser_tabs_for" in script
    assert "static func hidden_features_for_platform" in script
    assert "return supports_for_platform(feature_name, is_web())" in script
    assert "return not web_build" in script
    assert 'tabs.append("LAN")' in script


def test_main_menu_uses_capabilities_to_hide_dedicated_server_tools():
    script = (GODOT_ROOT / "scripts" / "main.gd").read_text(encoding="utf-8")

    assert 'get_node("/root/PlatformCapabilities")' in script
    assert 'preload("res://scenes/local_match.tscn")' in script
    assert 'preload("res://scenes/online_match.tscn")' in script
    assert "_capabilities.supports(_capabilities.FEATURE_DEDICATED_SERVER_TOOLS)" in script
    assert "Dedicated server tools are desktop-only." in script
    assert "Web build: browser-safe online only." in script
    assert "ServerBrowserScene.instantiate()" in script
    assert "func _show_online_match" in script
    assert "func _show_options" in script
    assert 'preload("res://scripts/server_directory.gd")' in script
    assert 'preload("res://scripts/control_settings.gd")' in script
    assert 'preload("res://scripts/browser_store.gd")' in script
    assert 'preload("res://scripts/network_adapter.gd")' in script
    assert "ControlSettings.apply_saved_bindings()" in script
    assert "ControlSettings.action_names()" in script
    assert "ControlSettings.save_key_binding" in script
    assert "ControlSettings.save_gamepad_button_binding" in script
    assert "ControlSettings.save_gamepad_axis_binding" in script
    assert "ControlSettings.active_gamepad_device()" in script
    assert "ControlSettings.gamepad_profiles()" in script
    assert "ControlSettings.set_active_gamepad_device" in script
    assert "ControlSettings.gamepad_label(action_name)" in script
    assert "ControlSettings.conflict_labels()" in script
    assert "func _begin_key_capture" in script
    assert "func _begin_gamepad_capture" in script
    assert "InputEventJoypadButton" in script
    assert "InputEventJoypadMotion" in script
    assert "InputEventKey" in script
    assert "GAMEPAD_CAPTURE_CANCEL_BUTTON := JOY_BUTTON_BACK" in script
    assert "event.button_index == GAMEPAD_CAPTURE_CANCEL_BUTTON" in script
    assert "Back cancels." in script
    assert "ControlSettings.reset_defaults()" in script
    assert "ControlSettings.reset_gamepad_defaults()" in script
    assert "ScrollContainer.new()" in script
    assert "focus_mode = Control.FOCUS_ALL" in script
    assert "func _focus_first_button" in script
    assert "func _wire_vertical_focus" in script
    assert "focus_neighbor_top" in script
    assert "focus_neighbor_bottom" in script
    assert '"Reset Conflicting Bindings"' in script
    assert 'event.is_action_pressed("ui_cancel")' in script
    assert 'OPTIONS_PATH := "user://groundfire_options.cfg"' in script
    assert "func _load_options" in script
    assert "func _save_options" in script
    assert "func _apply_options" in script
    assert "ServerDirectory.SERVER_DIRECTORY_ENVIRONMENT_SETTING" in script
    assert "ServerDirectory.SERVER_DIRECTORY_DEV_URL_SETTING" in script
    assert "ServerDirectory.SERVER_DIRECTORY_STAGING_URL_SETTING" in script
    assert "ServerDirectory.SERVER_DIRECTORY_PRODUCTION_URL_SETTING" in script
    assert "_server_directory_environment" in script
    assert "_server_directory_override_url" in script
    assert "_server_directory_dev_url" in script
    assert "_server_directory_staging_url" in script
    assert "_server_directory_production_url" in script
    assert "func _load_server_directory_options" in script
    assert "func _apply_server_directory_options" in script
    assert "func _add_server_directory_options" in script
    assert "func _add_directory_url_option" in script
    assert "func _server_directory_error_label" in script
    assert "func _server_directory_preview_label" in script
    assert "using local fallback" in script
    assert '"server_directory"' in script
    assert '"Directory Environment"' in script
    assert '"Override URL"' in script
    assert '"Dev URL"' in script
    assert '"Staging URL"' in script
    assert '"Production URL"' in script
    assert "RESOLUTION_PRESETS" in script
    assert "_resolution_index" in script
    assert "Resolution" in script
    assert "func _add_resolution_selector" in script
    assert "func _selected_resolution" in script
    assert "DisplayServer.window_set_size" in script
    assert "AI_DIFFICULTIES" in script
    assert '"AI Difficulty"' in script
    assert '"ai_difficulty"' in script
    assert "func _add_ai_difficulty_selector" in script
    assert "func _show_dedicated_server_tools" in script
    assert "func _start_web_gateway" in script
    assert "func _run_browser_runtime_qa" in script
    assert '"gateway_endpoint"' in script
    assert '"auth_gateway_endpoint"' in script
    assert '"full_gateway_endpoint"' in script
    assert '"closed_gateway_endpoint"' in script
    assert '"banned_gateway_endpoint"' in script
    assert 'gateway_endpoint, "invalid_password", "password rejected"' in script
    assert 'auth_gateway_endpoint, "authentication_failed", "authentication was rejected"' in script
    assert 'full_gateway_endpoint, "server_full", "server is full"' in script
    assert 'closed_gateway_endpoint, "server_closed", "server is closed"' in script
    assert 'banned_gateway_endpoint, "banned", "access was rejected"' in script
    assert "real gateway %s status is shown" in script
    assert "gateway_join_failure" in script
    assert "func _qa_normalized_store_phase" in script
    assert "BROWSER_QA_STORE_PATH" in script
    assert "BrowserStore.save_store" in script
    assert "ServerDirectory.refresh_from_http" in script
    assert "func _qa_check_directory_cache_headers" in script
    assert "func _qa_header_value" in script
    assert '"directory_cache_control"' in script
    assert '"directory_etag"' in script
    assert '"directory_refresh_seconds"' in script
    assert "max-age=30" in script
    assert "must-revalidate" in script
    assert "window.__groundfireQaResult" in script
    assert '"browser_runtime"' in script
    assert '"seed" or phase == "verify"' in script
    assert "groundfire-web-gateway" in script
    assert "OS.create_process" in script
    assert "DisplayServer.window_set_vsync_mode" in script
    assert "AudioServer.set_bus_volume_db" in script
    assert "Show FPS" in script
    assert "Fullscreen" in script
    assert "VSync" in script
    assert "Audio Enabled" in script
    assert "Master Volume" in script
    assert "Screen Shake" in script
    assert "Camera Smoothing" in script
    assert "Mouse Aim" in script
    assert "func _add_slider_option" in script
    assert '"Keyboard"' in script
    assert '"Gamepad"' in script
    assert '"Gamepad Profile"' in script
    assert "func _add_gamepad_profile_selector" in script
    assert '"Reset Gamepad Defaults"' in script
    assert 'preload("res://assets/logo.png")' in script
    assert 'preload("res://assets/menuback.png")' in script
    assert "GroundfireTheme.apply_button" in script


def test_server_browser_has_web_safe_empty_state():
    script = (GODOT_ROOT / "scripts" / "server_browser.gd").read_text(encoding="utf-8")

    assert 'get_node("/root/PlatformCapabilities")' in script
    assert "_capabilities.visible_server_browser_tabs()" in script
    assert "LAN discovery is not available in web builds." in script
    assert '"Server"' in script
    assert '"Latency"' in script
    assert '"Change Filters"' in script
    assert '"No Password"' in script
    assert '"Open Slots"' in script
    assert "OptionButton.new()" in script
    assert "func _entry_has_open_slot" in script
    assert "func _sort_entries" in script
    assert '"Refresh All"' in script
    assert "GroundfireTheme.panel_style()" in script
    assert 'preload("res://scripts/browser_store.gd")' in script
    assert 'preload("res://scripts/server_directory.gd")' in script
    assert "ServerDirectory.browser_entries" in script
    assert "ServerDirectory.filter_for_tab" in script
    assert 'preload("res://scripts/network_adapter.gd")' in script
    assert 'preload("res://scripts/websocket_client.gd")' in script
    assert "_selected_index := -1" in script
    assert "_hovered_index := -1" in script
    assert "ScrollContainer.new()" in script
    assert "SCROLL_MODE_DISABLED" in script
    assert "TABLE_COLUMN_WIDTHS" in script
    assert "TABLE_HEADER_HEIGHT" in script
    assert "TABLE_ROW_HEIGHT" in script
    assert "func _column_width" in script
    assert "func _clear_table_rows" in script
    assert "func _render_table_message" in script
    assert "_connect_button.disabled = true" in script
    assert "func _on_row_gui_input" in script
    assert "func _on_row_hovered" in script
    assert "func _build_join_dialog" in script
    assert "func _show_join_dialog" in script
    assert "GroundfireTheme.modal_backdrop_style()" in script
    assert "_join_modal.visible = false" in script
    assert "_favorite_button" in script
    assert "_clear_history_button" in script
    assert "_undo_button" in script
    assert "_refresh_all_button" in script
    assert "_directory_loading := false" in script
    assert '"Clear History"' in script
    assert '"Undo"' in script
    assert "func _toggle_selected_favorite" in script
    assert "func _clear_history" in script
    assert "func _undo_last_browser_action" in script
    assert "func _copy_history_entries" in script
    assert "func _favorite_entries" in script
    assert "func _favorite_placeholder" in script
    assert "func _update_action_buttons" in script
    assert "var _action_buttons: Array[Button]" in script
    assert "var _filter_controls: Array[Control]" in script
    assert "func _wire_server_browser_focus" in script
    assert "func _wire_table_focus" in script
    assert "func _wire_join_modal_focus" in script
    assert "func _wire_horizontal_focus" in script
    assert "func _select_row" in script
    assert "func _on_row_focused" in script
    assert 'event.is_action_pressed("ui_accept")' in script
    assert "cell.focus_entered.connect" in script
    assert "old_child.queue_free()" in script
    assert 'event.is_action_pressed("ui_cancel")' in script
    assert "_join_connect_button.focus_neighbor_left" in script
    assert "_connect_button.focus_neighbor_right = _close_button.get_path()" in script
    assert "BrowserStore.forget_favorite" in script
    assert "BrowserStore.clear_history" in script
    assert '"Remove Favorite"' in script
    assert '"Saved Favorite"' in script
    assert '"Not in directory"' in script
    assert '"directory_status": "missing"' in script
    assert '"No favorites saved yet."' in script
    assert '"No favorites match the current filters."' in script
    assert '"No connection history yet."' in script
    assert "Press Undo to restore." in script
    assert '"Favorite restored: %s."' in script
    assert '"Connection history restored."' in script
    assert "func _refresh_online_directory" in script
    assert "func _request_online_directory" in script
    assert '"Online server directory is already loading."' in script
    assert '_refresh_all_button.text = "Loading..." if _directory_loading else "Refresh All"' in script
    assert "func _load_directory_fallback" in script
    assert "ServerDirectory.should_retry_directory_request" in script
    assert "ServerDirectory.http_diagnostic" in script
    assert "ServerDirectory.directory_diagnostic_from_body" in script
    assert "ServerDirectory.configured_directory_label" in script
    assert "Online server directory invalid or empty" in script
    assert "func _load_browser_store" in script
    assert "func _browser_filter_state" in script
    assert "_favorites.append(str(endpoint))" in script
    assert "_history.append(Dictionary(entry))" in script
    assert "BrowserStore.default_filters()" in script
    assert "BrowserStore.filter_state" in script
    assert "BrowserStore.save_store" in script
    assert "NetworkAdapter.staged_connect_message" in script
    assert "WebSocketClient.new()" in script
    assert "func _on_websocket_status_changed" in script
    assert "func _on_websocket_message_received" in script
    assert "NetworkAdapter.server_error_status_message" in script
    assert "NetworkAdapter.transport_for_endpoint" in script
    assert "_show_online_match" in script


def test_browser_store_persists_favorites_and_history():
    script = (GODOT_ROOT / "scripts" / "browser_store.gd").read_text(encoding="utf-8")

    assert 'DEFAULT_STORE_PATH := "user://server_browser_store.json"' in script
    assert "static func load_store" in script
    assert "static func save_store" in script
    assert "static func remember_favorite" in script
    assert "static func forget_favorite" in script
    assert "static func clear_history" in script
    assert "static func remember_history" in script
    assert "static func default_filters" in script
    assert "static func filter_state" in script
    assert "static func normalize_filters" in script
    assert '"filters"' in script
    assert '"sort_mode": "latency"' in script
    assert "MAX_HISTORY := 20" in script
    assert (GODOT_ROOT / "tests" / "browser_store_check.gd").exists()


def test_server_directory_separates_online_and_lan_entries():
    script = (GODOT_ROOT / "scripts" / "server_directory.gd").read_text(encoding="utf-8")
    data = json.loads((GODOT_ROOT / "data" / "server_directory.json").read_text(encoding="utf-8"))
    directory_doc = (PROJECT_ROOT / "docs" / "godot_server_directory_schema.md").read_text(encoding="utf-8")

    assert 'SOURCE_ONLINE := "online"' in script
    assert 'SOURCE_LAN := "lan"' in script
    assert 'DEFAULT_DIRECTORY_PATH := "res://data/server_directory.json"' in script
    assert 'SERVER_DIRECTORY_SETTING := "application/config/server_directory_url"' in script
    assert 'SERVER_DIRECTORY_ENVIRONMENT_SETTING := "application/config/server_directory_environment"' in script
    assert 'SERVER_DIRECTORY_DEV_URL_SETTING := "application/config/server_directory_url_dev"' in script
    assert 'SERVER_DIRECTORY_STAGING_URL_SETTING := "application/config/server_directory_url_staging"' in script
    assert 'SERVER_DIRECTORY_PRODUCTION_URL_SETTING := "application/config/server_directory_url_production"' in script
    assert 'ENVIRONMENT_DEV := "dev"' in script
    assert 'ENVIRONMENT_STAGING := "staging"' in script
    assert 'ENVIRONMENT_PRODUCTION := "production"' in script
    assert "DIRECTORY_ENVIRONMENTS" in script
    assert "DIRECTORY_SCHEMA_VERSION := 1" in script
    assert "REQUIRED_SERVER_FIELDS" in script
    assert "OPTIONAL_SERVER_FIELDS" in script
    assert "OPTIONAL_STRING_SERVER_FIELDS" in script
    assert '"auth_token"' in script
    assert "static func _copy_optional_fields" in script
    assert "static func configured_directory_url" in script
    assert "static func configured_directory_environment" in script
    assert "static func normalized_directory_environment" in script
    assert "static func directory_url_setting_for_environment" in script
    assert "static func directory_environment_urls" in script
    assert "static func is_valid_directory_url" in script
    assert "static func directory_url_error" in script
    assert "static func configured_directory_label" in script
    assert "invalid override URL; local fallback" in script
    assert "invalid URL; local fallback" in script
    assert "static func expected_schema" in script
    assert "static func validate_directory_payload" in script
    assert "static func directory_diagnostic_from_body" in script
    assert "static func _validate_server_entry" in script
    assert "static func _join_errors" in script
    assert "passworded must be boolean" in script
    assert "must be string" in script
    assert "endpoint must be ws:// or wss:// for online servers" in script
    assert "FileAccess.open" in script
    assert "static func refresh_from_http" in script
    assert "HTTP_TIMEOUT_SECONDS" in script
    assert "HTTP_RETRY_LIMIT" in script
    assert "static func should_retry_directory_request" in script
    assert "static func http_diagnostic" in script
    assert "static func entries_from_http_body" in script
    assert "JSON.parse_string" in script
    assert 'entry.get("source", "") != SOURCE_LAN' in script
    assert 'normalized == "internet"' in script
    assert 'normalized == "lan"' in script
    assert data["schema"] == 1
    assert data["servers"][0]["endpoint"] == "wss://play.groundfire.local/servers/test"
    assert data["servers"][0]["passworded"] is False
    assert data["servers"][0]["auth_token"] == "dev-directory-token"
    assert any(server["source"] == "lan" for server in data["servers"])
    assert any(server["endpoint"] == "127.0.0.1:27015" for server in data["servers"])
    assert "Current schema: `1`" in directory_doc
    assert "`auth_token`: string" in directory_doc
    assert "pre-provisioned development" in directory_doc
    assert "Online entries must use `ws://` or `wss://`" in directory_doc
    assert "fallback to `res://data/server_directory.json`" in directory_doc
    assert (GODOT_ROOT / "tests" / "server_directory_check.gd").exists()


def test_local_match_and_network_adapter_scaffolds_exist():
    local_match = (GODOT_ROOT / "scripts" / "local_match.gd").read_text(encoding="utf-8")
    hud = (GODOT_ROOT / "scripts" / "local_match_hud.gd").read_text(encoding="utf-8")
    shop = (GODOT_ROOT / "scripts" / "local_match_shop.gd").read_text(encoding="utf-8")
    terrain = (GODOT_ROOT / "scripts" / "terrain_model.gd").read_text(encoding="utf-8")
    tank = (GODOT_ROOT / "scripts" / "tank_state.gd").read_text(encoding="utf-8")
    weapons = (GODOT_ROOT / "scripts" / "weapon_inventory.gd").read_text(encoding="utf-8")
    network = (GODOT_ROOT / "scripts" / "network_adapter.gd").read_text(encoding="utf-8")
    websocket = (GODOT_ROOT / "scripts" / "websocket_client.gd").read_text(encoding="utf-8")

    assert (GODOT_ROOT / "scenes" / "local_match.tscn").exists()
    assert 'preload("res://scripts/terrain_model.gd")' in local_match
    assert "TURN_PLAYER" in local_match
    assert "func _cycle_weapon" in local_match
    assert "func _splash_damage" in local_match
    assert "func _rebuild_terrain_if_needed" in local_match
    assert 'preload("res://scripts/tank_state.gd")' in local_match
    assert 'preload("res://scripts/weapon_inventory.gd")' in local_match
    assert 'preload("res://scripts/local_match_shop.gd")' in local_match
    assert "var _player := TankState.new()" in local_match
    assert "var _inventory := WeaponInventory.new()" in local_match
    assert "var _enemy_inventory := WeaponInventory.new()" in local_match
    assert "gf_move_left" in local_match
    assert "gf_jump" in local_match
    assert "ui_cancel" in local_match
    assert "ui_accept" in local_match
    assert "InputEventMouseMotion" in local_match
    assert "InputEventMouseButton" in local_match
    assert "MOUSE_BUTTON_LEFT" in local_match
    assert "move_on_terrain" in local_match
    assert "func _build_pause_overlay" in local_match
    assert "func _set_paused" in local_match
    assert "func _restart_round" in local_match
    assert "func _return_to_main_menu" in local_match
    assert "func _open_options_from_pause" in local_match
    assert "_resume_button.grab_focus.call_deferred()" in local_match
    assert "button.focus_mode = Control.FOCUS_ALL" in local_match
    assert "focus_neighbor_top" in local_match
    assert "focus_neighbor_bottom" in local_match
    assert '"Paused"' in local_match
    assert '"Options"' in local_match
    assert '"Restart Round"' in local_match
    assert "func _fire_weapon" in local_match
    assert "func _spawn_mirv_children" in local_match
    assert "PROJECTILE_GRAVITY := 190.0" in local_match
    assert "MIRV_MIN_SPLIT_AGE := 0.25" in local_match
    assert "MISSILE_ANGLE_CHANGE_LIMIT := 500.0" in local_match
    assert "MISSILE_RECENTER_MULTIPLIER := 3.0" in local_match
    assert "MISSILE_AI_STEER_ANGLE_SCALE := 18.0" in local_match
    assert "MISSILE_MIN_SPEED := 1.0" in local_match
    assert "velocity.y += PROJECTILE_GRAVITY * step" in local_match
    assert "velocity.y += PROJECTILE_GRAVITY * delta" in local_match
    assert "split_age = max(MIRV_MIN_SPLIT_AGE, -velocity.y / PROJECTILE_GRAVITY)" in local_match
    assert '"split_age": split_age' in local_match
    assert 'projectile["expired"] = true' in local_match
    assert 'weapon.get("fragments", WeaponInventory.MIRV_FRAGMENTS)' in local_match
    assert 'weapon.get("spread", WeaponInventory.MIRV_SPREAD)' in local_match
    assert "velocity.x * spread * offset" in local_match
    assert "func _update_missile_projectile" in local_match
    assert "func _missile_steer_direction" in local_match
    assert "func _short_angle_delta" in local_match
    assert "min(MISSILE_ANGLE_CHANGE_LIMIT" in local_match
    assert "max(-MISSILE_ANGLE_CHANGE_LIMIT" in local_match
    assert "MISSILE_RECENTER_MULTIPLIER * steer_sensitivity * delta" in local_match
    assert "max(MISSILE_MIN_SPEED, velocity.length())" in local_match
    assert "delta_angle / MISSILE_AI_STEER_ANGLE_SCALE" in local_match
    assert '"fuel": missile_fuel' in local_match
    assert '"steer_sensitivity": float(weapon.get("steer_sensitivity", 300.0))' in local_match
    assert "inherited_velocity := Vector2.ZERO" in local_match
    assert "velocity_override: Variant = null" in local_match
    assert "+ inherited_velocity" in local_match
    assert "_player.launch_velocity(_player.gun_power, speed_multiplier)" in local_match
    assert "_enemy.launch_velocity(_enemy.gun_power, speed_multiplier)" in local_match
    assert "velocity = Vector2(velocity_override)" in local_match
    assert "func _update_machine_gun_projectile" in local_match
    assert "func _machine_gun_projectile_waits" in local_match
    assert "func _apply_machine_gun_damage" in local_match
    assert "func _finish_machine_gun_volley_if_needed" in local_match
    assert "func _has_projectile_kind" in local_match
    assert '"back_position": origin' in local_match
    assert 'weapon.get("volley", WeaponInventory.MACHINE_GUN_VOLLEY)' in local_match
    assert 'weapon.get("cooldown", WeaponInventory.MACHINE_GUN_COOLDOWN)' in local_match
    assert '"delay"' in local_match
    assert 'draw_line(back_position, projectile_position, Color.WHITE, 2.0)' in local_match
    assert "machine_gun" in local_match
    assert "missile" in local_match
    assert "_credits" in local_match
    assert "PHASE_PROJECTILE" in local_match
    assert "PHASE_SHOP" in local_match
    assert "func _fire_ai" in local_match
    assert "func _choose_ai_shot" in local_match
    assert "func _choose_ai_weapon" in local_match
    assert "AI_DIFFICULTY_EASY" in local_match
    assert "AI_DIFFICULTY_HARD" in local_match
    assert "WIND_MIN" in local_match
    assert "_wind_gust" in local_match
    assert "func _wind_acceleration" in local_match
    assert "func _shift_wind_for_turn" in local_match
    assert "func _roll_round_wind" in local_match
    assert "QUAKE_DURATION" in local_match
    assert "QUAKE_DROP_RATE" in local_match
    assert "QUAKE_TIME_TILL_FIRST := 90.0" in local_match
    assert "QUAKE_TIME_BETWEEN := 30.0" in local_match
    assert 'preload("res://assets/quake.wav")' in local_match
    assert "func _build_quake_audio" in local_match
    assert "quake_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD" in local_match
    assert "func _play_quake_audio" in local_match
    assert "func _stop_quake_audio" in local_match
    assert "_quake_active" in local_match
    assert "_quake_countdown" in local_match
    assert "func _update_quake" in local_match
    assert "_terrain.drop_terrain(delta * QUAKE_DROP_RATE)" in local_match
    assert '"quake_active": _quake_active' in local_match
    assert '"wind_effect": _wind_acceleration(0.0)' in local_match
    assert '"ai_difficulty"' in local_match
    assert "func _ai_angle_step" in local_match
    assert "func _ai_power_error" in local_match
    assert "func _direct_ai_shot" in local_match
    assert "func _has_direct_line_to_player" in local_match
    assert "func _simulate_ai_shell_miss" in local_match
    assert "func _distance_to_segment" in local_match
    assert "func _terrain_collision" in local_match
    assert "ground_collision" in local_match
    assert "func _apply_explosion" in local_match
    assert "func _weapon_white_out" in local_match
    assert "func _draw_whiteout_overlay" in local_match
    assert "func _whiteout_alpha" in local_match
    assert "NUKE_WHITEOUT_FADE_RATE := 0.6" in local_match
    assert "_spawn_explosion(position, blast_radius, _weapon_white_out(weapon))" in local_match
    assert '"white_out_level": 1.0 if white_out else 0.0' in local_match
    assert "if _enemy.state == TankState.STATE_DEAD" in local_match
    assert "elif _player.state == TankState.STATE_DEAD" in local_match
    assert "func _start_next_turn_or_round" in local_match
    assert "func _fire" in local_match
    assert "LocalMatchHud" in local_match
    assert "LocalMatchShop" in local_match
    assert "func _build_shop_overlay" in local_match
    assert "func _open_post_round_shop" in local_match
    assert "func _refresh_shop_overlay" in local_match
    assert "func _buy_shop_weapon" in local_match
    assert "func _continue_from_shop" in local_match
    assert "continue_requested.connect" in local_match
    assert "buy_requested.connect" in local_match
    assert '"reward": _shop_reward' in local_match
    assert "func set_snapshot" in hud
    assert '"player_wins"' in hud
    assert '"player_name"' in hud
    assert '"enemy_name"' in hud
    assert '"ammo"' in hud
    assert '"credits"' in hud
    assert '"inventory"' in hud
    assert "func _draw_weapon_inventory" in hud
    assert "func _draw_weapon_icon" in hud
    assert 'preload("res://assets/weaponicons.png")' in hud
    assert "func _weapon_icon_source_rect" in hud
    assert "func _weapon_icon_index" in hud
    assert "draw_texture_rect_region(WEAPON_ICONS" in hud
    assert "return 10" in hud
    assert "func _draw_stat_bar" in hud
    assert "HUD_MAX_WIDTH" in hud
    assert "INVENTORY_CHIP_WIDTH" in hud
    assert "func _draw_turn_banner" in hud
    assert "func _draw_gauge_row" in hud
    assert "func _draw_score_row" in hud
    assert "func _draw_value_chip" in hud
    assert "func _draw_gauge" in hud
    assert "func _draw_message_strip" in hud
    assert "func _phase_color" in hud
    assert "func _turn_color" in hud
    assert "func _format_ammo_label" in hud
    assert '"shop"' in hud
    assert "func _weapon_color" in hud
    assert "func _inventory_rows" in hud
    assert "func _format_ammo" in hud
    assert "func _wind_label" in hud
    assert '"Wind -> %d"' in hud
    assert "func _quake_label" in hud
    assert '"Quake!"' in hud
    assert "func rebuild_with_seed" in terrain
    assert "func apply_crater" in terrain
    assert "func drop_terrain" in terrain
    assert "CLASSIC_MIN_LAND_HEIGHT := -7.0" in terrain
    assert "TANK_EDGE_MARGIN := 30.0" in terrain
    assert "func playable_bounds" in terrain
    assert "return Vector2(TANK_EDGE_MARGIN, _width - TANK_EDGE_MARGIN)" in terrain
    assert "var _chunks: Array" in terrain
    assert "func _clip_slice" in terrain
    assert "func _subtract_interval" in terrain
    assert "func _vertical_color_at" in terrain
    assert "func _refresh_chunk_colors" in terrain
    assert "func _superblock_landing_gap" in terrain
    assert "func _merge_resting_superblocks" in terrain
    assert '"fill_color"' in terrain
    assert "func _landing_gap" in terrain
    assert "func ground_collision" in terrain
    assert "func _segment_polygon_collision" in terrain
    assert "func _segment_intersection" in terrain
    assert "func chunk_polygons" in terrain
    assert "func update(delta: float)" in terrain
    assert '"falling"' in terrain
    assert "_fall_acceleration" in terrain
    assert "func polygon_points" in terrain
    assert "func slope_angle_at" in terrain
    assert "_terrain.update(delta)" in local_match
    assert "chunk_polygons" in local_match
    assert "var _world_size" in local_match
    assert "var _camera_offset" in local_match
    assert "var _camera_zoom" in local_match
    assert "var _camera_shake" in local_match
    assert "var _camera_shake_offset" in local_match
    assert "RandomNumberGenerator.new()" in local_match
    assert "func _update_camera" in local_match
    assert "func _camera_subjects" in local_match
    assert "func _bounds_for_subjects" in local_match
    assert "func _constrain_camera_offset" in local_match
    assert "func _screen_to_world" in local_match
    assert "func _add_camera_shake" in local_match
    assert "func _update_camera_shake" in local_match
    assert "func _target_world_size" in local_match
    assert "func _draw_map_bounds" in local_match
    assert "func _draw_mouse_reticle" in local_match
    assert "func _load_gameplay_options" in local_match
    assert "_screen_shake_enabled" in local_match
    assert "_camera_smoothing" in local_match
    assert "_mouse_aim_enabled" in local_match
    assert "_mouse_world_position" in local_match
    assert "projectile_velocity.normalized()" in local_match
    assert "_add_camera_shake(crater_radius)" in local_match
    assert "draw_set_transform" in local_match
    assert "position.x > _world_size.x" in local_match
    assert "func move_on_terrain" in tank
    assert "func boost" in tank
    assert "func update_gun" in tank
    assert "GUN_ANGLE_MIN := 5.0" in tank
    assert "GUN_ANGLE_MAX := 175.0" in tank
    assert "GUN_ANGLE_DEFAULT := 45.0" in tank
    assert "GUN_ANGLE_CHANGE_ACCELERATION := 60.0" in tank
    assert "GUN_ANGLE_MAX_CHANGE_SPEED := 75.0" in tank
    assert "GUN_POWER_MIN := 5.0" in tank
    assert "GUN_POWER_MAX := 100.0" in tank
    assert "GUN_POWER_DEFAULT := 55.0" in tank
    assert "GUN_POWER_CHANGE_ACCELERATION := 20.0" in tank
    assert "GUN_POWER_MAX_CHANGE_SPEED := 50.0" in tank
    assert "TANK_MAX_HEALTH := 100" in tank
    assert "TANK_FULL_FUEL := 1.0" in tank
    assert "gun_angle = GUN_ANGLE_DEFAULT" in tank
    assert "gun_power = GUN_POWER_DEFAULT" in tank
    assert "health = TANK_MAX_HEALTH" in tank
    assert "fuel = TANK_FULL_FUEL" in tank
    assert "GUN_ANGLE_MIN, GUN_ANGLE_MAX" in tank
    assert "GUN_POWER_MIN, GUN_POWER_MAX" in tank
    assert "TANK_BOOST_ACCELERATION := 280.0" in tank
    assert "BOOST_FUEL_USAGE_RATE := 0.2" in tank
    assert "BOOST_TURN_RATE := 90.0" in tank
    assert "BOOST_TURN_LIMIT := 15.0" in tank
    assert "TANK_AIR_GRAVITY := 200.0" in tank
    assert "TANK_GROUND_DETACH_THRESHOLD := 2.0" in tank
    assert "TANK_MOVE_SPEED := 74.0" in tank
    assert "TANK_AIR_CONTROL_ACCELERATION := 60.0" in tank
    assert "TANK_GROUND_FUEL_USAGE_RATE := 0.13" in tank
    assert "TANK_AIR_STEER_FUEL_USAGE_RATE := 0.08" in tank
    assert "TANK_SLOPE_DRAG_SCALE := 65.0" in tank
    assert "TANK_MIN_SLOPE_MOVE_FACTOR := 0.35" in tank
    assert "TANK_PASSIVE_SLIDE_THRESHOLD := 30.0" in tank
    assert "airborne_velocity.y += TANK_AIR_GRAVITY * delta" in tank
    assert "ground_position.y > position.y + TANK_GROUND_DETACH_THRESHOLD" in tank
    assert "func _apply_passive_slope_slide" in tank
    assert "abs(ground_angle) <= TANK_PASSIVE_SLIDE_THRESHOLD" in tank
    assert "sign(ground_angle) * slide_speed * delta" in tank
    assert "func _constrain_to_terrain_bounds" in tank
    assert 'terrain.has_method("playable_bounds")' in tank
    assert "var bounds: Vector2 = terrain.playable_bounds()" in tank
    assert "airborne_velocity.x = 0.0" in tank
    assert "on_ground = false" in tank
    assert "airborne_velocity.x -= sin(radians) * TANK_BOOST_ACCELERATION * delta" in tank
    assert "airborne_velocity.y -= cos(radians) * TANK_BOOST_ACCELERATION * delta" in tank
    assert "func _update_boost_turn" in tank
    assert "gun_angle_change_speed = 0.0" in tank
    assert "gun_power_change_speed = 0.0" in tank
    assert "func aim_at" in tank
    assert "func launch_velocity" in tank
    assert "return airborne_velocity + Vector2(cos(radians), -sin(radians)) * power * speed_multiplier" in tank
    assert "func apply_damage" in tank
    assert "health < 0 and state == STATE_ALIVE" in tank
    assert "const MACHINE_GUN" in weapons
    assert "const NUKE" in weapons
    assert '"kind": "mirv"' in weapons
    assert "MIRV_ROUND_AMMO := 3" in weapons
    assert "MIRV_FRAGMENTS := 5" in weapons
    assert "MIRV_SPREAD := 0.2" in weapons
    assert '"ammo": MIRV_ROUND_AMMO' in weapons
    assert '"fragments": MIRV_FRAGMENTS' in weapons
    assert '"spread": MIRV_SPREAD' in weapons
    assert '"fuel": 3.0' in weapons
    assert '"steer_sensitivity": 300.0' in weapons
    assert '"damage": 2' in weapons
    assert '"blast": 0.0' in weapons
    assert '"direct_damage": true' in weapons
    assert "DEFAULT_AMMO_SPEND := 1" in weapons
    assert "MACHINE_GUN_ROUND_AMMO := 50" in weapons
    assert "MACHINE_GUN_VOLLEY := 5" in weapons
    assert "MACHINE_GUN_COOLDOWN := 0.1" in weapons
    assert '"ammo": MACHINE_GUN_ROUND_AMMO' in weapons
    assert '"cooldown": MACHINE_GUN_COOLDOWN' in weapons
    assert '"white_out": true' in weapons
    assert "func consume_current" in weapons
    assert '"volley": MACHINE_GUN_VOLLEY' in weapons
    assert 'current().get("volley", DEFAULT_AMMO_SPEND)' in weapons
    assert "func ammo_for" in weapons
    assert "func weapon_by_name" in weapons
    assert "func select_by_name" in weapons
    assert "func has_ammo" in weapons
    assert "func weapon_cost" in weapons
    assert "func ammo_pack_size" in weapons
    assert "func add_ammo" in weapons
    assert "func inventory_snapshot" in weapons
    assert '"selected"' in weapons
    assert '"inventory": _inventory.inventory_snapshot()' in local_match
    assert "signal continue_requested" in shop
    assert "signal buy_requested" in shop
    assert "func refresh" in shop
    assert "func _rebuild_weapon_rows" in shop
    assert "var _focus_buttons: Array[Button]" in shop
    assert "func _wire_vertical_focus" in shop
    assert "focus_neighbor_top" in shop
    assert "focus_neighbor_bottom" in shop
    assert '"Credits %d"' in shop
    assert '"Buy %d"' in shop
    assert "continue_requested.emit()" in shop
    assert "buy_requested.emit(captured_name)" in shop
    assert 'TRANSPORT_WEBSOCKET := "websocket"' in network
    assert 'MESSAGE_HELLO := "hello"' in network
    assert 'MESSAGE_PING := "ping"' in network
    assert "PROTOCOL_VERSION := 1" in network
    assert "FATAL_SERVER_ERRORS" in network
    assert "static func command_from_local_match" in network
    assert "static func pong_message" in network
    assert "static func snapshot_message" in network
    assert "static func encode_message" in network
    assert "static func hello_message" in network
    assert "static func join_message" in network
    assert "auth_token" in network
    assert "static func input_message" in network
    assert "static func parse_message" in network
    assert "static func server_supports_client_protocol" in network
    assert "static func protocol_status_message" in network
    assert "static func is_fatal_server_error" in network
    assert "static func server_error_status_message" in network
    assert '"invalid_password"' in network
    assert '"authentication_failed"' in network
    assert '"server_full"' in network
    assert '"Join failed: password rejected' in network
    assert "supported_protocols" in network
    assert "_protocol_support_label" in network
    assert "static func staged_connect_message" in network
    assert '"protocol": PROTOCOL_VERSION' in network
    assert '"missing_protocol"' in network
    assert '"protocol_mismatch"' in network
    assert '"expected_protocol"' in network
    assert "Connect target staged" in network
    assert "allow_udp" in network
    assert "WebSocketPeer.new()" in websocket
    assert "func connect_to_endpoint" in websocket
    assert "func send_input" in websocket
    assert "NetworkAdapter.join_message(player_name, password, auth_token)" in websocket
    assert "func is_websocket_connected" in websocket
    assert "func last_sequence" in websocket
    assert "_closed_reported" in websocket
    assert "NetworkAdapter.hello_message()" in websocket
    assert (GODOT_ROOT / "scenes" / "online_match.tscn").exists()
    assert (GODOT_ROOT / "tests" / "terrain_collision_check.gd").exists()


def test_online_match_scene_consumes_websocket_snapshots_and_sends_input():
    script = (GODOT_ROOT / "scripts" / "online_match.gd").read_text(encoding="utf-8")

    assert 'preload("res://scripts/websocket_client.gd")' in script
    assert "func setup" in script
    assert "connect_to_endpoint" in script
    assert "NetworkAdapter.MESSAGE_SNAPSHOT" in script
    assert "NetworkAdapter.MESSAGE_HELLO" in script
    assert "func _handle_protocol_hello" in script
    assert "func _fail_protocol_handshake" in script
    assert "func _fail_server_error" in script
    assert "func _is_protocol_error" in script
    assert "func _send_join_after_hello" in script
    assert "_auth_token" in script
    assert 'str(_entry.get("auth_token", ""))' in script
    assert "HELLO_TIMEOUT" in script
    assert "_server_protocol_ready" in script
    assert "_server_protocol_status" in script
    assert "NetworkAdapter.server_supports_client_protocol" in script
    assert "NetworkAdapter.protocol_status_message" in script
    assert "NetworkAdapter.is_fatal_server_error" in script
    assert "NetworkAdapter.server_error_status_message" in script
    assert "_fatal_server_failure" in script
    assert '"Protocol handshake failed: %s."' in script
    assert '"Snapshot ignored before protocol hello."' in script
    assert "send_input" in script
    assert "gf_aim_left" in script
    assert "gf_weapon_next" in script
    assert "func _draw_replicated_world" in script
    assert "func _draw_terrain_profile" in script
    assert "func _draw_entities" in script
    assert "func _draw_replicated_tank" in script
    assert "func _draw_replicated_projectile" in script
    assert "func _draw_players" in script
    assert "func _ingest_replicated_entities" in script
    assert "func _update_interpolation" in script
    assert "func _ingest_events" in script
    assert "func _update_effects" in script
    assert "RECONNECT_BASE_DELAY" in script
    assert "RECONNECT_MAX_ATTEMPTS" in script
    assert "PING_INTERVAL" in script
    assert "PREDICTION_MOVE_STEP" in script
    assert "func _schedule_reconnect" in script
    assert "func _update_reconnect" in script
    assert '"Reconnect"' in script
    assert '"Back"' in script
    assert "func _manual_reconnect" in script
    assert "func _return_to_main_menu" in script
    assert 'disconnect_from_endpoint("manual_reconnect")' in script
    assert "_pending_commands.clear()" in script
    assert "func _draw_network_diagnostics" in script
    assert "func _ingest_acknowledgements" in script
    assert "func _apply_local_prediction" in script
    assert "_last_latency_ms" in script
    assert "_pending_commands" in script
    assert "acknowledged_command_sequence" in script
    assert "match_snapshot" in script
    assert "terrain_profile" in script


def test_control_settings_persist_input_bindings():
    script = (GODOT_ROOT / "scripts" / "control_settings.gd").read_text(encoding="utf-8")

    assert 'SETTINGS_PATH := "user://groundfire_controls.cfg"' in script
    assert "DEFAULT_BINDINGS" in script
    assert "static func apply_saved_bindings" in script
    assert "static func save_key_binding" in script
    assert "static func save_gamepad_button_binding" in script
    assert "static func save_gamepad_axis_binding" in script
    assert "static func clear_gamepad_binding" in script
    assert "static func reset_defaults" in script
    assert "static func reset_gamepad_defaults" in script
    assert "static func active_gamepad_device" in script
    assert "static func set_active_gamepad_device" in script
    assert "static func gamepad_profiles" in script
    assert "static func action_names" in script
    assert "static func display_name" in script
    assert "static func key_label" in script
    assert "DEFAULT_GAMEPAD_BUTTONS" in script
    assert "DEFAULT_GAMEPAD_AXES" in script
    assert "GAMEPAD_PROFILE_SECTION" in script
    assert "GAMEPAD_ALL_DEVICES" in script
    assert "InputEventJoypadButton" in script
    assert "InputEventJoypadMotion" in script
    assert "static func gamepad_label" in script
    assert "static func conflict_labels" in script
    assert "gamepad_owners" in script
    assert '"gamepad"' in script
    assert "static func _apply_default_gamepad_binding" in script
    assert "static func _apply_saved_gamepad_binding" in script
    assert "static func _gamepad_section" in script
    assert "Input.get_connected_joypads()" in script
    assert '"gamepad_device_%d"' in script
    assert ".device = device_id" in script
    assert "InputMap.action_erase_events" in script


def test_migration_strategy_documents_web_feature_rule():
    doc = (PROJECT_ROOT / "docs" / "godot_migration_strategy.md").read_text(encoding="utf-8")

    assert "Godot 4 + GDScript" in doc
    assert "Hidden on web" in doc
    assert "LAN discovery" in doc
    assert "WebSocket/WebRTC" in doc


def test_godot_export_presets_exist_for_desktop_and_web():
    presets = (GODOT_ROOT / "export_presets.cfg").read_text(encoding="utf-8")
    export_script = (PROJECT_ROOT / "scripts" / "export_godot.sh").read_text(encoding="utf-8")
    package_script = (PROJECT_ROOT / "scripts" / "package_godot_release.sh").read_text(encoding="utf-8")
    visual_script = (PROJECT_ROOT / "scripts" / "validate_godot_visuals.sh").read_text(encoding="utf-8")
    qa_script = (PROJECT_ROOT / "scripts" / "qa_godot_web.sh").read_text(encoding="utf-8")
    validate_script = (PROJECT_ROOT / "scripts" / "validate_godot.sh").read_text(encoding="utf-8")
    visual_check = (GODOT_ROOT / "tests" / "visual_golden_check.gd").read_text(encoding="utf-8")
    runtime_smoke = (GODOT_ROOT / "tests" / "runtime_smoke_check.gd").read_text(encoding="utf-8")
    runtime_doc = (PROJECT_ROOT / "docs" / "godot_build_and_runtime.md").read_text(encoding="utf-8")

    assert 'name="Linux Desktop"' in presets
    assert 'platform="Linux"' in presets
    assert 'name="Web"' in presets
    assert 'platform="Web"' in presets
    assert 'exclude_filter="tests/*"' in presets
    assert "scripts/validate_godot.sh" in export_script
    assert "GODOT_TEMPLATE_DIR" in export_script
    assert "web_nothreads_release.zip" in export_script
    assert "linux_release.x86_64" in export_script
    assert '--export-release "Linux Desktop"' in export_script
    assert '--export-release "Web"' in export_script
    assert "runtime_smoke_check.gd" in validate_script
    assert "visible_server_browser_tabs_for(true)" in runtime_smoke
    assert "MainScene.instantiate()" in runtime_smoke
    assert "ServerBrowserScene.instantiate()" in runtime_smoke
    assert "LocalMatchScene.instantiate()" in runtime_smoke
    assert "OnlineMatchScene.instantiate()" in runtime_smoke
    assert "GROUNDFIRE_RELEASE_VERSION" in package_script
    assert "GROUNDFIRE_RELEASE_PREFIX" in package_script
    assert "GROUNDFIRE_RELEASE_NOTES" in package_script
    assert "pyproject.toml" in package_script
    assert "tomllib" in package_script
    assert "release_notes" in package_script
    assert "sha256" in package_script
    assert "GODOT_VISUAL_UPDATE=1" in visual_script
    assert "visual_golden_check.gd" in visual_script
    assert "qa=browser_runtime" in qa_script
    assert "store_phase=$phase" in qa_script
    assert "gateway_endpoint=ws://127.0.0.1:$gateway_port/qa-gateway" in qa_script
    assert "auth_gateway_endpoint=ws://127.0.0.1:$auth_gateway_port/qa-auth-gateway" in qa_script
    assert "full_gateway_endpoint=ws://127.0.0.1:$full_gateway_port/qa-full-gateway" in qa_script
    assert "closed_gateway_endpoint=ws://127.0.0.1:$closed_gateway_port/qa-closed-gateway" in qa_script
    assert "banned_gateway_endpoint=ws://127.0.0.1:$banned_gateway_port/qa-banned-gateway" in qa_script
    assert "-m groundfire_net.websocket_gateway" in qa_script
    assert "--password qa-secret" in qa_script
    assert "--auth-token qa-token" in qa_script
    assert "--max-players 1" in qa_script
    assert "SlotHolder" in qa_script
    assert "--closed" in qa_script
    assert "--ban-player GodotPlayer" in qa_script
    assert "browser_runtime_qa seed" in qa_script
    assert "browser_runtime_qa verify" in qa_script
    assert "GroundfireQAHandler" in qa_script
    assert "Cache-Control" in qa_script
    assert "X-Groundfire-Directory-Refresh" in qa_script
    assert "groundfire-qa-directory-v1" in qa_script
    assert "window.__groundfireQaResult" in qa_script
    assert "Browser runtime QA passed" in qa_script
    assert "server_directory.json" in qa_script
    assert "Run scripts/validate_godot_visuals.sh --update-goldens first" in visual_check
    assert "not FileAccess.file_exists(golden_path)" in visual_check
    assert "scripts/export_godot.sh all" in runtime_doc
    assert "scripts/package_godot_release.sh" in runtime_doc
    assert "scripts/validate_godot_visuals.sh --check" in runtime_doc
    assert "scripts/qa_godot_web.sh --check" in runtime_doc
    assert "Browser runtime QA" in runtime_doc
    assert "seed" in runtime_doc
    assert "verify" in runtime_doc
    assert "Cache-Control" in runtime_doc
    assert "ETag" in runtime_doc
    assert "X-Groundfire-Directory-Refresh" in runtime_doc
    assert "Release Verification" in runtime_doc
    assert "sha256sum --check" in runtime_doc
    assert "Signing policy" in runtime_doc
    assert "Browser Hosting" in runtime_doc
    assert "Distribution Notes" in runtime_doc
    assert "build/godot-web/index.html" in runtime_doc
