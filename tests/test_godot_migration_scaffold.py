import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GODOT_ROOT = PROJECT_ROOT / "godot"


def test_godot_project_declares_main_scene_and_platform_autoload():
    project = (GODOT_ROOT / "project.godot").read_text(encoding="utf-8")

    assert 'run/main_scene="res://scenes/main.tscn"' in project
    assert 'config/server_directory_url=""' in project
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
    assert "return is_desktop()" in script
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
    assert 'preload("res://scripts/control_settings.gd")' in script
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
    assert "_connect_button.disabled = true" in script
    assert "func _on_row_gui_input" in script
    assert "func _on_row_hovered" in script
    assert "func _build_join_dialog" in script
    assert "func _show_join_dialog" in script
    assert "GroundfireTheme.modal_backdrop_style()" in script
    assert "_join_modal.visible = false" in script
    assert "func _add_selected_favorite" in script
    assert "func _refresh_online_directory" in script
    assert "func _request_online_directory" in script
    assert "func _load_directory_fallback" in script
    assert "ServerDirectory.should_retry_directory_request" in script
    assert "ServerDirectory.http_diagnostic" in script
    assert "func _load_browser_store" in script
    assert "BrowserStore.save_store" in script
    assert "NetworkAdapter.staged_connect_message" in script
    assert "WebSocketClient.new()" in script
    assert "func _on_websocket_status_changed" in script
    assert "func _on_websocket_message_received" in script
    assert "NetworkAdapter.transport_for_endpoint" in script
    assert "_show_online_match" in script


def test_browser_store_persists_favorites_and_history():
    script = (GODOT_ROOT / "scripts" / "browser_store.gd").read_text(encoding="utf-8")

    assert 'DEFAULT_STORE_PATH := "user://server_browser_store.json"' in script
    assert "static func load_store" in script
    assert "static func save_store" in script
    assert "static func remember_favorite" in script
    assert "static func remember_history" in script
    assert "MAX_HISTORY := 20" in script
    assert (GODOT_ROOT / "tests" / "browser_store_check.gd").exists()


def test_server_directory_separates_online_and_lan_entries():
    script = (GODOT_ROOT / "scripts" / "server_directory.gd").read_text(encoding="utf-8")
    data = json.loads((GODOT_ROOT / "data" / "server_directory.json").read_text(encoding="utf-8"))

    assert 'SOURCE_ONLINE := "online"' in script
    assert 'SOURCE_LAN := "lan"' in script
    assert 'DEFAULT_DIRECTORY_PATH := "res://data/server_directory.json"' in script
    assert 'SERVER_DIRECTORY_SETTING := "application/config/server_directory_url"' in script
    assert "DIRECTORY_SCHEMA_VERSION := 1" in script
    assert "static func configured_directory_url" in script
    assert "static func expected_schema" in script
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
    assert data["servers"][0]["endpoint"] == "wss://play.groundfire.local/servers/test"
    assert any(server["source"] == "lan" for server in data["servers"])
    assert any(server["endpoint"] == "127.0.0.1:27015" for server in data["servers"])
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
    assert "machine_gun" in local_match
    assert "missile" in local_match
    assert "_credits" in local_match
    assert "PHASE_PROJECTILE" in local_match
    assert "PHASE_SHOP" in local_match
    assert "func _fire_ai" in local_match
    assert "func _choose_ai_shot" in local_match
    assert "func _choose_ai_weapon" in local_match
    assert "func _direct_ai_shot" in local_match
    assert "func _has_direct_line_to_player" in local_match
    assert "func _simulate_ai_shell_miss" in local_match
    assert "func _distance_to_segment" in local_match
    assert "func _terrain_collision" in local_match
    assert "ground_collision" in local_match
    assert "func _apply_explosion" in local_match
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
    assert "func _draw_stat_bar" in hud
    assert "func _weapon_color" in hud
    assert "func _inventory_rows" in hud
    assert "func _format_ammo" in hud
    assert "func rebuild_with_seed" in terrain
    assert "func apply_crater" in terrain
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
    assert "func aim_at" in tank
    assert "func apply_damage" in tank
    assert "const MACHINE_GUN" in weapons
    assert "const NUKE" in weapons
    assert '"kind": "mirv"' in weapons
    assert "func consume_current" in weapons
    assert '"volley": 5' in weapons
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
    assert '"Credits %d"' in shop
    assert '"Buy %d"' in shop
    assert "continue_requested.emit()" in shop
    assert "buy_requested.emit(captured_name)" in shop
    assert 'TRANSPORT_WEBSOCKET := "websocket"' in network
    assert 'MESSAGE_HELLO := "hello"' in network
    assert 'MESSAGE_PING := "ping"' in network
    assert "static func command_from_local_match" in network
    assert "static func pong_message" in network
    assert "static func snapshot_message" in network
    assert "static func encode_message" in network
    assert "static func hello_message" in network
    assert "static func input_message" in network
    assert "static func parse_message" in network
    assert "static func staged_connect_message" in network
    assert "Connect target staged" in network
    assert "allow_udp" in network
    assert "WebSocketPeer.new()" in websocket
    assert "func connect_to_endpoint" in websocket
    assert "func send_input" in websocket
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

    assert 'name="Linux Desktop"' in presets
    assert 'platform="Linux"' in presets
    assert 'name="Web"' in presets
    assert 'platform="Web"' in presets
