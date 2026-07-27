import json
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GODOT_ROOT = Path(os.environ.get("GODOT_PROJECT_DIR", PROJECT_ROOT / "versao-godot" / "godot"))
if not (GODOT_ROOT / "project.godot").exists() and (PROJECT_ROOT / "godot" / "project.godot").exists():
    GODOT_ROOT = PROJECT_ROOT / "godot"


def test_godot_project_declares_main_scene_and_platform_autoload():
    project = (GODOT_ROOT / "project.godot").read_text(encoding="utf-8")

    assert 'run/main_scene="res://scenes/main.tscn"' in project
    assert 'config/server_directory_url=""' in project
    assert 'config/server_directory_environment="dev"' in project
    assert 'config/server_directory_url_dev="http://127.0.0.1:27880/servers.json"' in project
    assert 'config/server_directory_url_staging="https://staging.groundfire.net/directory/servers.json"' in project
    assert 'config/server_directory_url_production="https://play.groundfire.net/directory/servers.json"' in project
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
    assert "gf_shield" in project
    assert (GODOT_ROOT / "assets" / "logo.png").exists()
    assert (GODOT_ROOT / "assets" / "menuback.png").exists()
    assert (GODOT_ROOT / "assets" / "jumpjets.wav").exists()
    assert (GODOT_ROOT / "assets" / "fireshell.wav").exists()
    assert (GODOT_ROOT / "assets" / "shelldeath.wav").exists()
    assert (GODOT_ROOT / "assets" / "launchmissile.wav").exists()
    assert (GODOT_ROOT / "assets" / "missile.wav").exists()
    assert (GODOT_ROOT / "assets" / "missiledeath.wav").exists()
    assert (GODOT_ROOT / "assets" / "machinegun.wav").exists()
    assert (GODOT_ROOT / "assets" / "metal.wav").exists()
    assert (GODOT_ROOT / "assets" / "nuke.wav").exists()


def test_groundfire_theme_defines_shared_visual_language():
    script = (GODOT_ROOT / "scripts" / "groundfire_theme.gd").read_text(encoding="utf-8")

    assert 'COLOR_BG := Color("#365e79")' in script
    assert 'COLOR_MENU_TILE_TINT := Color("#66b3e6")' in script
    assert 'COLOR_ACCENT := Color("#994c00")' in script
    assert "BUTTON_FONT_SIZE := 16" in script
    assert "BUTTON_BG_HOVER" in script
    assert "BUTTON_BG_DISABLED" in script
    assert "BUTTON_FONT_DISABLED" in script
    assert "BUTTON_BORDER" in script
    assert "CLASSIC_TEXT_SHADOW_COLOR" in script
    assert "CLASSIC_TEXT_OUTLINE_COLOR" in script
    assert "CLASSIC_TEXT_SHADOW_OFFSET_X := 3" in script
    assert "CLASSIC_TEXT_SHADOW_OFFSET_Y := 3" in script
    assert 'button.add_theme_stylebox_override("focus", button_style(true, true))' in script
    assert 'button.add_theme_color_override("font_hover_color", COLOR_WARN)' in script
    assert 'button.add_theme_color_override("font_hover_pressed_color", COLOR_WARN)' in script
    assert "static func panel_style" in script
    assert "static func classic_panel_style" in script
    assert "static func apply_button" in script
    assert "static func apply_classic_button" in script
    assert "static func apply_classic_text_effect" in script
    assert 'control.add_theme_color_override("font_shadow_color", CLASSIC_TEXT_SHADOW_COLOR)' in script
    assert 'control.add_theme_constant_override("shadow_offset_x", CLASSIC_TEXT_SHADOW_OFFSET_X)' in script
    assert "static func row_style" in script
    assert "static func modal_backdrop_style" in script


def test_classic_selector_matches_pygame_triangle_selector_contract():
    script_path = GODOT_ROOT / "scripts" / "classic_selector.gd"
    assert script_path.exists()
    script = script_path.read_text(encoding="utf-8")

    assert "extends Control" in script
    assert 'preload("res://scripts/groundfire_theme.gd")' in script
    assert "signal item_selected(index: int)" in script
    assert "var selected := 0" in script
    assert "var item_count := 0" in script
    assert "func add_item(text: String)" in script
    assert "func get_item_text(index: int)" in script
    assert "func select(index: int)" in script
    assert "func set_disabled(value: bool)" in script
    assert "focus_mode = Control.FOCUS_NONE if _disabled else Control.FOCUS_ALL" in script
    assert "mouse_filter = Control.MOUSE_FILTER_IGNORE if _disabled else Control.MOUSE_FILTER_STOP" in script
    assert "GroundfireTheme.apply_classic_text_effect(self)" in script
    assert "draw_colored_polygon" in script
    assert "Vector2(left_base - arrow_size, center_y)" in script
    assert "Vector2(right_base + arrow_size, center_y)" in script
    assert 'preload("res://scripts/classic_font.gd")' in script
    assert "ClassicFont.draw_text(" in script
    assert "func uses_classic_font_atlas() -> bool" in script
    assert "GroundfireTheme.COLOR_WARN" in script
    assert 'event.is_action_pressed("ui_left")' in script
    assert 'event.is_action_pressed("ui_right")' in script
    assert 'event.is_action_pressed("ui_accept")' in script
    assert "func _arrow_at(point: Vector2) -> int" in script
    assert "func _step(direction: int) -> void" in script
    assert "selected = wrapi(selected + direction, 0, _items.size())" in script
    assert "item_selected.emit(selected)" in script


def test_classic_font_atlas_renderer_ports_pygame_font_contract():
    font_script = (GODOT_ROOT / "scripts" / "classic_font.gd").read_text(encoding="utf-8")
    label_script = (GODOT_ROOT / "scripts" / "classic_label.gd").read_text(encoding="utf-8")
    button_script = (GODOT_ROOT / "scripts" / "classic_button.gd").read_text(encoding="utf-8")

    assert 'preload("res://assets/fonts.png")' in font_script
    assert "PROPORTIONAL_ROW_OFFSET := 8" in font_script
    assert "GLYPH_WIDTH_RATIO := 0.8" in font_script
    assert "static func measure" in font_script
    assert "static func draw_text" in font_script
    assert "draw_texture_rect_region" in font_script
    assert "text.unicode_at(index)" in font_script
    assert "float(_width_for_code(code)) / 24.0 * spacing" in font_script
    assert "extends Label" in label_script
    assert "func uses_classic_font_atlas() -> bool" in label_script
    assert "ClassicFont.draw_text(" in label_script
    assert "GroundfireTheme.CLASSIC_TEXT_SHADOW_COLOR" in label_script
    assert "extends Button" in button_script
    assert "func classic_hover_color() -> Color" in button_script
    assert 'add_theme_color_override("font_focus_color"' in button_script
    assert "GroundfireTheme.CLASSIC_TEXT_SHADOW_OFFSET_X" in button_script


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
    assert "Web build: browser-safe online only." in script
    assert "ServerBrowserScene.instantiate()" in script
    assert "func _show_online_match" in script
    assert "func _show_options" in script
    assert '"local_match_setup"' in script
    assert 'preload("res://scripts/server_directory.gd")' in script
    assert 'preload("res://scripts/control_settings.gd")' in script
    assert 'preload("res://scripts/browser_store.gd")' in script
    assert 'preload("res://scripts/network_adapter.gd")' in script
    assert 'preload("res://scripts/classic_selector.gd")' in script
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
    assert "func _classic_control_capture_prompt" in script
    assert '"Press Button for \'%s\'"' in script
    assert 'Select a control to rebind.' not in script
    assert script.count('_capture_prompt.text = ""') >= 2
    assert "Press a keyboard key" not in script
    assert "Press a gamepad button" not in script
    assert "InputEventJoypadButton" in script
    assert "InputEventJoypadMotion" in script
    assert "InputEventKey" in script
    assert "GAMEPAD_CAPTURE_CANCEL_BUTTON := JOY_BUTTON_BACK" in script
    assert "MENU_LOGO_MIN_WIDTH := 590.0" in script
    assert "MENU_LOGO_MAX_WIDTH := 920.0" in script
    assert "MENU_BUTTON_MIN_SIZE := Vector2(259.0, 34.0)" in script
    assert "MENU_BUTTON_MAX_SIZE := Vector2(414.0, 56.0)" in script
    assert "MENU_CONTENT_MAX_WIDTH := 920.0" in script
    assert "func _classic_logo_size" in script
    assert "func _classic_button_size" in script
    assert "GroundfireTheme.apply_label(label, int(round(float(font_size) * _menu_scale())), color, true)" in script
    assert "GroundfireTheme.apply_label(label, 34, GroundfireTheme.COLOR_TEXT, true)" in script
    assert "MENU_CLASSIC_PANEL_SIZE" in script
    assert "MENU_CLASSIC_BUTTON_SIZE" in script
    assert "func _add_classic_button_to" in script
    assert "func _set_classic_fullscreen_layout" in script
    assert "LOGO_TEXTURE.get_size()" in script
    assert "clamp(MENU_LOGO_BASE_SIZE.x * _menu_scale()" in script
    assert "clamp(scaled.x, MENU_BUTTON_MIN_SIZE.x, MENU_BUTTON_MAX_SIZE.x)" in script
    assert "event.button_index == GAMEPAD_CAPTURE_CANCEL_BUTTON" in script
    assert "Back cancels." not in script
    assert "ControlSettings.reset_defaults()" in script
    assert "ControlSettings.reset_gamepad_defaults()" in script
    assert "ScrollContainer.new()" in script
    assert "focus_mode = Control.FOCUS_ALL" in script
    assert "func _focus_first_button" in script
    assert "func _wire_vertical_focus" in script
    assert "func _wire_vertical_control_focus" in script
    assert "func _wire_horizontal_focus" in script
    assert "func _wire_options_focus" in script
    assert "if buttons.size() == 1:" in script
    assert "button.focus_neighbor_left = path" in script
    assert "button.focus_neighbor_right = path" in script
    assert "func _focusable_controls_in_tree" in script
    assert "func _collect_focusable_controls" in script
    assert "func _is_focusable_control" in script
    assert "var _paused_match_screen: Control" in script
    assert "func _show_options_for_paused_match" in script
    assert "func _return_to_paused_match" in script
    assert "func _discard_paused_match_screen" in script
    assert '_show_options(Callable(self, "_return_to_paused_match"))' in script
    assert "_show_options(back_callback)" in script
    assert (
        'var back_action := back_callback if back_callback.is_valid() else Callable(self, "_show_main_menu")' in script
    )
    assert "func _add_options_section" in script
    assert 'var video_section := _add_options_section(inner, "Video")' in script
    assert 'var audio_section := _add_options_section(inner, "Audio")' in script
    assert 'var gameplay_section := _add_options_section(inner, "Gameplay")' in script
    assert 'var online_section := _add_options_section(inner, "Online")' in script
    assert "var controls_section: VBoxContainer = null" in script
    assert 'controls_section = _add_options_section(inner, "Controls")' in script
    assert "OPTIONS_CLASSIC_ROW_SIZE" in script
    assert "func _add_classic_options_preset_rows" in script
    assert "func _add_classic_resolution_row(parent: Container) -> Control" in script
    assert "func _add_classic_screen_mode_row(parent: Container) -> Control" in script
    assert "ClassicSelector.new()" in script
    assert "selector.set_font_size" in script
    assert "selector.set_disabled(_capabilities != null and _capabilities.is_web())" in script
    assert "selector.add_item" in script
    assert "selector.item_selected.connect" in script
    assert '"Resolution:"' in script
    assert '"Screen Mode:"' in script
    assert '"Set Controls"' in script
    assert '"Apply"' in script
    assert (
        "GroundfireTheme.apply_label(label, int(round(float(OPTIONS_CLASSIC_ROW_FONT_SIZE) * _menu_scale())), "
        "GroundfireTheme.COLOR_CYAN, true)"
    ) in script
    assert "scroll.ensure_control_visible(controls_section)" in script
    assert "_focus_first_button(controls_section)" in script
    assert "_add_server_directory_options(online_section, false)" in script
    assert "_wire_options_focus(inner)" in script
    assert "if control is BaseButton:" in script
    assert "control is BaseButton and (control as BaseButton).disabled" in script
    assert "focus_neighbor_top" in script
    assert "focus_neighbor_bottom" in script
    assert "focus_neighbor_left" in script
    assert "focus_neighbor_right" in script
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
    assert "LOCAL_MATCH_ROUND_OPTIONS" in script
    assert "LOCAL_MATCH_DEFAULT_PLAYER_NAME" in script
    assert "LOCAL_MATCH_DEFAULT_ENEMY_NAME" in script
    assert "LOCAL_MATCH_NAME_MAX_LENGTH" in script
    assert "LOCAL_MATCH_MAX_PLAYERS := 8" in script
    assert "LOCAL_MATCH_CONTROLLER_LABELS" in script
    assert 'preload("res://assets/addbutton.png")' in script
    assert 'preload("res://assets/removebutton.png")' in script
    assert "var _local_match_setup_rows: Array[Dictionary]" in script
    assert "var _local_match_setup_back_button: Button" in script
    assert "var _local_match_setup_rounds: OptionButton" in script
    assert "func _local_match_setup_status_text" in script
    assert "Enable at least 2 players to start." in script
    assert "start_button.disabled = active_count < 2" in script
    assert '"%d players ready  Human %d  Computer %d"' in script
    assert "func _show_local_match_setup" in script
    assert '"Local Match Setup"' in script
    assert 'for header in ["Active", "Color", "Name", "Controlled by", "Controller"]' in script
    assert '"Human"' in script
    assert '"Computer"' in script
    assert "func _setup_name_line_edit" in script
    assert "line.max_length = LOCAL_MATCH_NAME_MAX_LENGTH" in script
    assert "func _local_match_setup_active_button" in script
    assert "TextureButton.new()" in script
    assert "button.texture_normal = ADD_BUTTON_TEXTURE" in script
    assert "button.texture_pressed = REMOVE_BUTTON_TEXTURE" in script
    assert "func _add_local_match_setup_row" in script
    assert "func _local_match_roster_snapshot" in script
    assert "func _next_available_local_match_controller" in script
    assert "func _wire_local_match_setup_focus" in script
    assert "func _wire_local_match_setup_vertical_column" in script
    assert "func _clear_focus_neighbors" in script
    assert "name.focus_mode = Control.FOCUS_ALL if enabled else Control.FOCUS_NONE" in script
    assert "if name != null and _is_focusable_control(name):" in script
    assert "if controller != null and _is_focusable_control(controller):" in script
    assert "_wire_local_match_setup_focus()" in script
    assert "if not start.disabled:" in script
    assert '"Rounds"' in script
    assert '"Start Match"' in script
    assert "func _start_local_match" in script
    assert '"roster": normalized_roster' in script
    assert "func _setup_name_or_default" in script
    assert "func _start_web_gateway" in script
    assert '"Join Password"' in script
    assert '"Auth Token"' in script
    assert '"Max Players"' in script
    assert '"Closed Joins"' in script
    assert '"Banned Players"' in script
    assert '"Stop Gateway"' in script
    assert '"Copy Endpoint"' in script
    assert '"Copy Command"' in script
    assert '"Connect endpoint: %s"' in script
    assert '"Command preview: %s"' in script
    assert "password_line.secret = true" in script
    assert "auth_token_line.secret = true" in script
    assert "var _dedicated_gateway_pid := 0" in script
    assert "var _dedicated_stop_button: Button" in script
    assert "var _dedicated_gateway_form_controls: Array[Control]" in script
    assert "var _dedicated_gateway_action_buttons: Array[Button]" in script
    assert 'var _dedicated_gateway_host := "127.0.0.1"' in script
    assert "var _dedicated_gateway_port := 8765" in script
    assert "var _dedicated_gateway_max_players := 0" in script
    assert "var _dedicated_gateway_closed := false" in script
    assert 'var _dedicated_gateway_banned_players := ""' in script
    assert "func _load_dedicated_gateway_options" in script
    assert 'config.set_value("dedicated_gateway", "host", _dedicated_gateway_host)' in script
    assert 'config.set_value("dedicated_gateway", "port", _dedicated_gateway_port)' in script
    assert 'config.set_value("dedicated_gateway", "max_players", _dedicated_gateway_max_players)' in script
    assert 'config.set_value("dedicated_gateway", "closed", _dedicated_gateway_closed)' in script
    assert 'config.set_value("dedicated_gateway", "banned_players", _dedicated_gateway_banned_players)' in script
    assert '"dedicated_gateway", "password"' not in script
    assert '"dedicated_gateway", "auth_token"' not in script
    assert '"ban_players": banned_line.text' in script
    assert "func _dedicated_gateway_config_from_controls" in script
    assert "func _wire_dedicated_gateway_focus" in script
    assert (
        "_dedicated_gateway_form_controls = [host_line, port_spin, password_line, auth_token_line, "
        "max_players_spin, closed_check, banned_line]" in script
    )
    assert (
        "_dedicated_gateway_action_buttons = [start, _dedicated_stop_button, copy_endpoint, copy_command, back]"
        in script
    )
    assert "if button != null and _is_focusable_control(button):" in script
    assert "_wire_dedicated_gateway_focus()" in script
    assert "func _gateway_args" in script
    assert "func _gateway_host" in script
    assert "func _gateway_port" in script
    assert "func _gateway_banned_players" in script
    assert "func _gateway_endpoint" in script
    assert "func _gateway_endpoint_host" in script
    assert "func _copy_gateway_endpoint" in script
    assert "func _copy_gateway_command" in script
    assert "func _gateway_command_preview" in script
    assert "func _gateway_policy_summary" in script
    assert '"Join policy: %s"' in script
    assert '"password %s"' in script
    assert '"auth %s"' in script
    assert '"joins %s"' in script
    assert '"bans %d"' in script
    assert "func _gateway_display_args" in script
    assert "func _shell_quote_arg" in script
    assert "DisplayServer.clipboard_set(endpoint)" in script
    assert "DisplayServer.clipboard_set(command)" in script
    assert "Gateway command copied with secrets masked." in script
    assert "groundfire-web-gateway" in script
    assert 'masked_value = "<password>"' in script
    assert 'masked_value = "<auth-token>"' in script
    assert 'return "ws://%s:%d"' in script
    assert 'host == "0.0.0.0" or host == "::"' in script
    assert 'return "[%s]" % host' in script
    assert "func _stop_web_gateway" in script
    assert "OS.kill(stopped_pid)" in script
    assert "Gateway already running with pid" in script
    assert "_dedicated_stop_button.disabled = false" in script
    assert "_dedicated_stop_button.disabled = true" in script
    assert 'args.append("--password")' in script
    assert 'args.append("--auth-token")' in script
    assert 'args.append("--max-players")' in script
    assert 'args.append("--closed")' in script
    assert 'args.append("--ban-player")' in script
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
    assert "func _qa_check_directory_not_modified" in script
    assert "ServerDirectory.http_etag(response_headers)" in script
    assert "ServerDirectory.HTTP_NOT_MODIFIED" in script
    assert "func _qa_header_value" in script
    assert '"directory_cache_control"' in script
    assert '"directory_etag"' in script
    assert '"directory_not_modified"' in script
    assert '"directory_refresh_seconds"' in script
    assert "max-age=30" in script
    assert "must-revalidate" in script
    assert "window.__groundfireQaResult" in script
    assert "window.__groundfireVisualReady" in script
    assert "func _publish_web_visual_ready" in script
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
    assert "var _mouse_aim_enabled := false" in script
    assert "func _add_slider_option" in script
    assert '"Keyboard"' in script
    assert '"Gamepad"' in script
    assert '"Gamepad Profile"' in script
    assert "func _add_gamepad_profile_selector" in script
    assert '"Reset To Defaults"' in script
    assert '"Reset Controls"' not in script
    assert '"Reset Gamepad Defaults"' in script
    assert 'preload("res://assets/logo.png")' in script
    assert 'preload("res://assets/menuback.png")' in script
    assert "MENU_REFERENCE_SIZE := Vector2(1024.0, 768.0)" in script
    assert "MENU_LOGO_BASE_SIZE := Vector2(819.0, 205.0)" in script
    assert "MENU_BUTTON_BASE_SIZE := Vector2(360.0, 48.0)" in script
    assert "func _menu_scale" in script
    assert "func _scaled_menu_size" in script
    assert "func _apply_menu_layout_metrics" in script
    assert "NOTIFICATION_RESIZED" in script
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
    assert "func _players_current_count" in script
    assert "func _players_max_count" in script
    assert "func _safe_int" in script
    assert "func _entry_tooltip" in script
    assert "func _selected_status" in script
    assert "cell.tooltip_text = _entry_tooltip(entry)" in script
    assert "func _sort_entries" in script
    assert '"Refresh All"' in script
    assert "GroundfireTheme.classic_panel_style()" in script
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
    assert "TABLE_MIN_TOTAL_WIDTH" in script
    assert "TABLE_SCROLL_MIN_HEIGHT" in script
    assert "func _apply_responsive_table_metrics" in script
    assert "TABLE_HORIZONTAL_SCROLL_MODE := ScrollContainer.SCROLL_MODE_DISABLED" in script
    assert "TABLE_VERTICAL_SCROLL_MODE := ScrollContainer.SCROLL_MODE_AUTO" in script
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
    assert '_directory_etag := ""' in script
    assert '_directory_cached_url := ""' in script
    assert "_directory_cached_entries: Array[Dictionary]" in script
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
    assert "func _focusable_action_buttons" in script
    assert "func _is_focusable_control" in script
    assert "func _clear_focus_neighbors" in script
    assert "_focusable_action_buttons(true)" in script
    assert "if control is BaseButton and (control as BaseButton).disabled:" in script
    assert "last_action.focus_neighbor_right = _close_button.get_path()" in script
    assert "_wire_server_browser_focus()" in script
    assert "_wire_table_focus()" in script
    assert "func _select_row" in script
    assert "func _on_row_focused" in script
    assert 'event.is_action_pressed("ui_accept")' in script
    assert "cell.focus_entered.connect" in script
    assert "old_child.queue_free()" in script
    assert 'event.is_action_pressed("ui_cancel")' in script
    assert "_join_connect_button.focus_neighbor_left" in script
    assert "_close_button.focus_neighbor_right = last_action.get_path()" in script
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
    assert "ServerDirectory.refresh_from_http(_http_request, url, etag)" in script
    assert "ServerDirectory.HTTP_NOT_MODIFIED" in script
    assert "func _load_directory_from_cache" in script
    assert "func _copy_entries" in script
    assert "ServerDirectory.http_etag(headers)" in script
    assert "Online server directory unchanged" in script
    assert "304 without a cached listing" in script
    assert "func _load_directory_fallback" in script
    assert "ServerDirectory.should_retry_directory_request" in script
    assert "ServerDirectory.http_diagnostic" in script
    assert "ServerDirectory.http_cache_diagnostic" in script
    assert "ServerDirectory.directory_diagnostic_from_body" in script
    assert "ServerDirectory.configured_directory_label" in script
    assert "TABLE_HEADER_BG" in script
    assert "func _table_header_style" in script
    assert "Online server directory loaded (%s%s)." in script
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
    assert "func _exit_tree" in script
    assert "_http_request.cancel_request()" in script
    assert '_websocket_client.disconnect_from_endpoint("server_browser_exit")' in script


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
    directory_doc = (PROJECT_ROOT / "docs" / "godot_migration_strategy.md").read_text(encoding="utf-8")

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
    assert '"session_token_url"' in script
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
    assert 'static func refresh_from_http(request: HTTPRequest, url: String, etag := "")' in script
    assert "HTTP_NOT_MODIFIED := 304" in script
    assert '"If-None-Match: %s"' in script
    assert "HTTP_TIMEOUT_SECONDS" in script
    assert "HTTP_RETRY_LIMIT" in script
    assert "static func should_retry_directory_request" in script
    assert "static func http_diagnostic" in script
    assert "static func http_cache_diagnostic" in script
    assert "static func http_etag" in script
    assert "static func _header_value" in script
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
    assert "`session_token_url`: string" in directory_doc
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
    assert "const WEAPON_SWITCH_DELAY := 0.2" in local_match
    assert "var _weapon_switch_delay_remaining := 0.0" in local_match
    assert "func _update_weapon_switch_delay" in local_match
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
    assert "gf_shield" in local_match
    assert "ui_cancel" in local_match
    assert "ui_accept" in local_match
    assert "InputEventMouseMotion" in local_match
    assert "InputEventMouseButton" in local_match
    assert "MOUSE_BUTTON_LEFT" in local_match
    assert "move_on_terrain" in local_match
    assert "func _build_pause_overlay" in local_match
    assert "func _set_paused" in local_match
    assert "focus_resume := true" in local_match
    assert "func _restart_round" in local_match
    assert "func _return_to_main_menu" in local_match
    assert "func _open_options_from_pause" in local_match
    assert "_show_options_for_paused_match" in local_match
    assert "_set_paused(true, false)" in local_match
    assert "_resume_button.grab_focus.call_deferred()" in local_match
    assert "button.focus_mode = Control.FOCUS_ALL" in local_match
    assert "focus_neighbor_top" in local_match
    assert "focus_neighbor_bottom" in local_match
    assert "button.focus_neighbor_left = path" in local_match
    assert "button.focus_neighbor_right = path" in local_match
    assert '"Paused"' in local_match
    assert '"Options"' in local_match
    assert '"Restart Round"' in local_match
    assert "func _fire_weapon" in local_match
    assert "func _spawn_mirv_children" in local_match
    assert "PROJECTILE_GRAVITY := 190.0" in local_match
    assert "TANK_GUN_ARROW_START_OFFSET := TankState.TANK_BODY_HALF_WIDTH * 1.5" in local_match
    assert "TANK_GUN_ARROW_BASE_LENGTH := TankState.TANK_BODY_HALF_WIDTH * 2.0" in local_match
    assert "TANK_GUN_ARROW_POWER_SCALE := TankState.TANK_BODY_HALF_WIDTH * 0.5" in local_match
    assert "TANK_GUN_ARROW_HEAD_TIP_SCALE := 1.25" in local_match
    assert "TANK_GUN_ARROW_SHAFT_HALF_WIDTH := TankState.TANK_BODY_HALF_WIDTH * 0.4" in local_match
    assert "TANK_GUN_ARROW_HEAD_HALF_WIDTH := TankState.TANK_BODY_HALF_WIDTH * 0.8" in local_match
    assert "MIRV_MIN_SPLIT_AGE := 0.25" in local_match
    assert "MISSILE_ANGLE_CHANGE_LIMIT := 500.0" in local_match
    assert "MISSILE_RECENTER_MULTIPLIER := 3.0" in local_match
    assert "MISSILE_AI_STEER_ANGLE_SCALE := 18.0" in local_match
    assert "MISSILE_MIN_SPEED" not in local_match
    assert "SCORE_ROUND_WIN_REWARD := 100" in local_match
    assert "SCORE_DEFEAT_LEADER_REWARD := 200" in local_match
    assert "SCORE_SELF_DEFEAT_PENALTY := -50" in local_match
    assert "SCORE_SURVIVAL_REWARD := 100" in local_match
    assert "CREDITS_ROUND_STIPEND := 10" in local_match
    assert "MATCH_TOTAL_ROUNDS := 5" in local_match
    assert 'PHASE_ROUND_STARTING := "round_starting"' in local_match
    assert "ROUND_STARTING_DELAY := 2.0" in local_match
    assert "var _round_start_delay := 0.0" in local_match
    assert "func _update_round_starting" in local_match
    assert "func setup(config: Dictionary)" in local_match
    assert "_requested_total_rounds" in local_match
    assert "var _player_name := TURN_PLAYER" in local_match
    assert "var _enemy_name := TURN_ENEMY" in local_match
    assert "var _configured_roster: Array[Dictionary]" in local_match
    assert "var _participants: Array[Dictionary]" in local_match
    assert 'for entry in Array(config.get("roster", []))' in local_match
    assert '_configured_roster.append(Dictionary(entry).duplicate(true))' in local_match
    assert "func _build_participants_from_roster" in local_match
    assert "func _participant_rows_snapshot" in local_match
    assert "func _participant_owner_for_index" in local_match
    assert "func _participant_name_for_owner" in local_match
    assert "func _score_leader_summary" in local_match
    assert "func _participant_hud_summary" in local_match
    assert "func _has_human_participants" in local_match
    assert "func _participant_tank" in local_match
    assert "func _participant_inventory" in local_match
    assert "func _participant_score" in local_match
    assert "func _participant_credits" in local_match
    assert "func _participant_wins" in local_match
    assert '"leader": bool(entry.get("leader", false))' in local_match
    assert "func _participant_is_leader_owner" in local_match
    assert "func _update_leader_flags" in local_match
    assert "func _living_participant_indices" in local_match
    assert "func _next_living_participant_index" in local_match
    assert "func _target_index_for_attacker" in local_match
    assert "func _set_turn_index" in local_match
    assert "func _record_round_defeat" in local_match
    assert (
        '_player_name = _setup_name_or_default(str(config.get("player_name", TURN_PLAYER)), TURN_PLAYER)'
        in local_match
    )
    assert '_enemy_name = _setup_name_or_default(str(config.get("enemy_name", TURN_ENEMY)), TURN_ENEMY)' in local_match
    assert "func _round_spawn_x" in local_match
    assert '"reset_round"' in local_match
    assert "MACHINE_GUN_AI_EASY_BURST := 3" in local_match
    assert "MACHINE_GUN_AI_NORMAL_BURST := 5" in local_match
    assert "MACHINE_GUN_AI_HARD_BURST := 8" in local_match
    assert "MACHINE_GUN_AI_FINISHER_BURST := 10" in local_match
    assert "MACHINE_GUN_TRACER_TRAIL_TIME := 0.01" in local_match
    assert "AI_SELF_DAMAGE_WEIGHT_HARD := 3.0" in local_match
    assert "AI_SELF_KILL_PENALTY := 1000.0" in local_match
    assert "AI_SHOP_PRIORITY" not in local_match
    assert "SCORE_HUMAN_ACTIVATION_DELAY := 2.0" in local_match
    assert "SCORE_COMPUTER_ACTIVATION_DELAY := 4.0" in local_match
    assert "SCORE_AUTO_ADVANCE_TIME := 10.0" in local_match
    assert "WINNER_HUMAN_ACTIVATION_DELAY := 2.0" in local_match
    assert "WINNER_COMPUTER_ACTIVATION_DELAY := 4.0" in local_match
    assert "SHOP_INITIAL_INPUT_DELAY := 0.4" in local_match
    assert "SHOP_ACTION_INPUT_DELAY := 0.2" in local_match
    assert "var _shop_finish_pending := false" in local_match
    assert "velocity.y += PROJECTILE_GRAVITY * step" in local_match
    assert "velocity.y += PROJECTILE_GRAVITY * delta" in local_match
    assert "split_age = max(MIRV_MIN_SPLIT_AGE, -velocity.y / PROJECTILE_GRAVITY)" in local_match
    assert '"split_age": split_age' in local_match
    assert "func _mirv_split_velocity" in local_match
    assert "var projectiles_this_step := _projectiles.duplicate()" in local_match
    assert 'var split_age: float = float(projectile.get("split_age", 0.8))' in local_match
    assert "var split_delta: float = clamp(split_age - previous_age, 0.0, delta)" in local_match
    assert "var split_position := previous_position + Vector2(split_velocity.x * split_delta, 0.0)" in local_match
    assert (
        "split_position.y = _ballistic_projectile_y_at(projectile, split_age, previous_position, velocity)"
        in local_match
    )
    assert "func _ballistic_projectile_y_at" in local_match
    assert 'projectile["expired"] = true' in local_match
    assert (
        "if position.x < 0.0 or position.x > _world_size.x:\n"
        '\t\t\t_lay_projectile_trail(projectile, position)\n'
        '\t\t\t_expire_projectile_without_explosion(projectile)\n'
        "\t\t\tcontinue\n"
        "\t\tvar terrain_collision := _terrain_collision(previous_position, position)"
        in local_match
    )
    assert 'TRAIL_TEXTURE := preload("res://assets/trail.png")' in local_match
    assert "func _lay_projectile_trail" in local_match
    assert "func _update_trail_segments" in local_match
    assert (
        "var terrain_collision := _terrain_collision(previous_position, position)\n"
        '\tif bool(terrain_collision["hit"]):\n'
        '\t\tprojectile["position"] = Vector2(terrain_collision["position"])\n'
        '\t\tprojectile["kill_next_frame"] = true\n'
        "\t\treturn\n"
        "\tvar target_owner := _segment_tank_hit_owner"
        in local_match
    )
    assert 'weapon.get("fragments", WeaponInventory.MIRV_FRAGMENTS)' in local_match
    assert 'weapon.get("spread", WeaponInventory.MIRV_SPREAD)' in local_match
    assert "var spread_step: float" in local_match
    assert "WeaponInventory.MIRV_MIN_FRAGMENT_SPREAD_SPEED" in local_match
    assert "velocity.x + (spread_step * offset)" in local_match
    assert "func _update_missile_projectile" in local_match
    assert "func _missile_applies_ballistic_acceleration" in local_match
    assert "func _missile_powered_velocity" in local_match
    assert "func _missile_steer_direction" in local_match
    assert "func _short_angle_delta" in local_match
    assert "min(MISSILE_ANGLE_CHANGE_LIMIT" in local_match
    assert "max(-MISSILE_ANGLE_CHANGE_LIMIT" in local_match
    assert "MISSILE_RECENTER_MULTIPLIER * steer_sensitivity * delta" in local_match
    assert "classic_speed - cos(radians)" in local_match
    assert "fuel_exhausted_this_frame" in local_match
    assert "delta_angle / MISSILE_AI_STEER_ANGLE_SCALE" in local_match
    assert '"fuel": missile_fuel' in local_match
    assert '"steer_sensitivity": float(weapon.get("steer_sensitivity", 300.0))' in local_match
    assert "inherited_velocity := Vector2.ZERO" in local_match
    assert "velocity_override: Variant = null" in local_match
    assert "+ inherited_velocity" in local_match
    assert 'tank.call("launch_velocity"' in local_match
    assert "velocity = Vector2(velocity_override)" in local_match
    assert "func _update_machine_gun_projectile" in local_match
    assert "func _machine_gun_projectile_position_at" in local_match
    assert "func _machine_gun_projectile_delta" in local_match
    assert "func _apply_machine_gun_damage" in local_match
    assert "func _finish_machine_gun_volley_if_needed" in local_match
    assert "func _begin_player_machine_gun_fire" in local_match
    assert "func _begin_enemy_machine_gun_fire" in local_match
    assert "func _update_machine_gun_fire" in local_match
    assert "func _spawn_machine_gun_round" in local_match
    assert "func _spawn_player_machine_gun_round" in local_match
    assert "func _unselect_machine_gun_and_cycle" in local_match
    assert "func _cancel_machine_gun_before_first_shot" in local_match
    assert "func _stop_machine_gun_after_lethal_hit" in local_match
    assert "func _expire_pending_machine_gun_rounds" in local_match
    assert "func _machine_gun_ai_burst_budget" in local_match
    assert "func _machine_gun_cooldown_time" in local_match
    assert "func _machine_gun_launch_power" in local_match
    assert "Machine Gun unselected. Weapon selected: %s." in local_match
    assert "_machine_gun_active" in local_match
    assert "_machine_gun_player_owned" in local_match
    assert "_machine_gun_ai_burst_remaining" in local_match
    assert 'inventory.call("consume_ammo", weapon_name, WeaponInventory.DEFAULT_AMMO_SPEND)' in local_match
    assert "func _has_projectile_kind" in local_match
    assert '"back_position": origin' in local_match
    assert '"launch_position": origin' in local_match
    assert '"launch_velocity": velocity' in local_match
    assert 'weapon.get("volley", WeaponInventory.MACHINE_GUN_VOLLEY)' in local_match
    assert 'weapon.get("cooldown", WeaponInventory.MACHINE_GUN_COOLDOWN)' in local_match
    assert "_machine_gun_cooldown = _machine_gun_cooldown_time(_machine_gun_weapon)" in local_match
    assert "while _machine_gun_cooldown < 0.0 and _machine_gun_fire_held:" in local_match
    assert "var frame_delay: float = max(0.0, delta + _machine_gun_cooldown)" in local_match
    assert '_projectiles[_projectiles.size() - 1]["delay"] = frame_delay' in local_match
    assert '_cancel_machine_gun_before_first_shot(_message)' in local_match
    assert '_cancel_machine_gun_before_first_shot("Machine Gun cancelled.")' in local_match
    assert '"delay"' in local_match
    assert "WeaponInventory.MACHINE_GUN_CLASSIC_POWER" in local_match
    assert 'draw_line(back_position, projectile_position, Color.WHITE, 2.0)' in local_match
    assert "_add_score_for_owner(owner, damage)" not in local_match
    assert "_add_credits_for_owner(owner, damage)" not in local_match
    assert "_record_round_defeat(owner, target_owner)" in local_match
    assert "machine_gun" in local_match
    assert "missile" in local_match
    assert "_credits" in local_match
    assert "var _enemy_score := 0" in local_match
    assert "PHASE_PROJECTILE" in local_match
    assert "PHASE_SHOP" in local_match
    assert "func _fire_ai" in local_match
    assert "func _choose_ai_shot" in local_match
    assert "func _choose_ai_weapon" in local_match
    assert "func _ai_weapon_candidates" in local_match
    assert "func _ai_weapon_projection" in local_match
    assert "func _ai_expected_player_damage" in local_match
    assert "func _ai_expected_self_damage" in local_match
    assert "func _ai_hit_quality" in local_match
    assert "func _ai_weapon_score_threshold" in local_match
    assert "func _ai_self_damage_weight" in local_match
    assert "func _ai_nuke_health_threshold" in local_match
    assert "AI_KILL_BONUS" in local_match
    assert 'inventory.call("ammo_for"' in local_match
    assert "AI_DIFFICULTY_EASY" in local_match
    assert "AI_DIFFICULTY_HARD" in local_match
    assert "WIND_MIN" in local_match
    assert "_wind_gust" in local_match
    assert "func _wind_acceleration" in local_match
    assert "func _shift_wind_for_turn" in local_match
    assert "func _roll_round_wind" in local_match
    assert "QUAKE_DURATION" in local_match
    assert "QUAKE_DROP_RATE" in local_match
    assert "QUAKE_TIME_TILL_FIRST := 60.0" in local_match
    assert "QUAKE_TIME_BETWEEN := 20.0" in local_match
    assert "QUAKE_SHAKE_AMPLITUDE := 0.05 * TankState.TANK_CLASSIC_WORLD_PIXEL_SCALE" in local_match
    assert "QUAKE_SHAKE_FREQUENCY := 50.0" in local_match
    assert 'preload("res://assets/quake.wav")' in local_match
    assert 'preload("res://assets/jumpjets.wav")' in local_match
    assert 'preload("res://assets/fireshell.wav")' in local_match
    assert 'preload("res://assets/shelldeath.wav")' in local_match
    assert 'preload("res://assets/launchmissile.wav")' in local_match
    assert 'preload("res://assets/missile.wav")' in local_match
    assert 'preload("res://assets/missiledeath.wav")' in local_match
    assert 'preload("res://assets/machinegun.wav")' in local_match
    assert 'preload("res://assets/metal.wav")' in local_match
    assert 'preload("res://assets/nuke.wav")' in local_match
    assert "func _build_quake_audio" in local_match
    assert "func _build_jump_jets_audio" in local_match
    assert "func _build_fire_shell_audio" in local_match
    assert "func _build_shell_death_audio" in local_match
    assert "func _build_launch_missile_audio" in local_match
    assert "func _build_missile_flight_audio" in local_match
    assert "func _build_missile_death_audio" in local_match
    assert "func _build_machine_gun_audio" in local_match
    assert "func _build_metal_hit_audio" in local_match
    assert "func _build_nuke_audio" in local_match
    assert "quake_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD" in local_match
    assert "jump_jets_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD" in local_match
    assert "fire_shell_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED" in local_match
    assert "shell_death_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED" in local_match
    assert "launch_missile_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED" in local_match
    assert "missile_flight_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD" in local_match
    assert "missile_death_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED" in local_match
    assert "machine_gun_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD" in local_match
    assert "metal_hit_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED" in local_match
    assert "nuke_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED" in local_match
    assert "func _play_quake_audio" in local_match
    assert "func _stop_quake_audio" in local_match
    assert "func _play_jump_jets_audio" in local_match
    assert "func _stop_jump_jets_audio" in local_match
    assert "func _tank_can_boost" in local_match
    assert "func _play_fire_shell_audio" in local_match
    assert "func _stop_fire_shell_audio" in local_match
    assert "func _play_shell_death_audio" in local_match
    assert "func _stop_shell_death_audio" in local_match
    assert "func _play_launch_missile_audio" in local_match
    assert "func _stop_launch_missile_audio" in local_match
    assert "func _play_missile_flight_audio" in local_match
    assert "func _stop_missile_flight_audio" in local_match
    assert "func _play_missile_death_audio" in local_match
    assert "func _stop_missile_death_audio" in local_match
    assert "func _sync_missile_flight_audio" in local_match
    assert "func _play_weapon_launch_audio" in local_match
    assert "func _play_machine_gun_audio" in local_match
    assert "func _stop_machine_gun_audio" in local_match
    assert "func _play_metal_hit_audio" in local_match
    assert "func _stop_metal_hit_audio" in local_match
    assert "func _play_nuke_audio" in local_match
    assert "func _stop_nuke_audio" in local_match
    assert "func _exit_tree" in local_match
    assert '_stop_quake_audio()' in local_match
    assert '_stop_jump_jets_audio()' in local_match
    assert '_stop_fire_shell_audio()' in local_match
    assert '_stop_shell_death_audio()' in local_match
    assert '_stop_launch_missile_audio()' in local_match
    assert '_stop_missile_flight_audio()' in local_match
    assert '_stop_missile_death_audio()' in local_match
    assert '_stop_machine_gun_audio()' in local_match
    assert '_stop_metal_hit_audio()' in local_match
    assert '_stop_nuke_audio()' in local_match
    assert "_quake_active" in local_match
    assert "_quake_countdown" in local_match
    assert "_jump_jets_active" in local_match
    assert "var _jump_jets_audio: AudioStreamPlayer" in local_match
    assert "var _fire_shell_audio: AudioStreamPlayer" in local_match
    assert "var _shell_death_audio: AudioStreamPlayer" in local_match
    assert "var _launch_missile_audio: AudioStreamPlayer" in local_match
    assert "var _missile_flight_audio: AudioStreamPlayer" in local_match
    assert "var _missile_death_audio: AudioStreamPlayer" in local_match
    assert "var _machine_gun_audio: AudioStreamPlayer" in local_match
    assert "var _metal_hit_audio: AudioStreamPlayer" in local_match
    assert "var _nuke_audio: AudioStreamPlayer" in local_match
    assert 'FireShellAudio' in local_match
    assert 'ShellDeathAudio' in local_match
    assert 'JumpJetsAudio' in local_match
    assert 'LaunchMissileAudio' in local_match
    assert 'MissileFlightAudio' in local_match
    assert 'MissileDeathAudio' in local_match
    assert 'MachineGunAudio' in local_match
    assert 'MetalHitAudio' in local_match
    assert 'NukeAudio' in local_match
    assert "_play_weapon_launch_audio(kind)" in local_match
    assert "func _play_explosion_death_audio" in local_match
    assert '_play_launch_missile_audio()' in local_match
    assert '_play_fire_shell_audio()' in local_match
    assert "_play_machine_gun_audio()" in local_match
    assert "_stop_machine_gun_audio()" in local_match
    assert "_play_jump_jets_audio()" in local_match
    assert "_play_nuke_audio()" in local_match
    assert "func _update_quake" in local_match
    assert "_terrain.drop_terrain(delta * QUAKE_DROP_RATE)" in local_match
    assert "func _update_quake_viewport_offset" in local_match
    assert "func _reset_quake_viewport_offset" in local_match
    assert "_camera_offset + _camera_shake_offset + _quake_viewport_offset" in local_match
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
    assert "func _segment_tank_hit_owner" in local_match
    assert 'ignored_owner := ""' in local_match
    assert "if owner == ignored_owner:" in local_match
    assert "func _segment_tank_hit_fraction" in local_match
    assert "func _apply_explosion" in local_match
    assert "direct_hit_owner" in local_match
    assert "func _explosion_damage_for_target" in local_match
    assert "_add_score_for_owner(owner, target_damage)" not in local_match
    assert "_add_credits_for_owner(owner, target_damage)" not in local_match
    assert "_record_round_defeat(owner, target_owner)" in local_match
    assert "func _weapon_white_out" in local_match
    assert "func _draw_whiteout_overlay" in local_match
    assert "func _whiteout_alpha" in local_match
    assert "NUKE_WHITEOUT_FADE_RATE := 0.6" in local_match
    assert "var white_out := _weapon_white_out(weapon)" in local_match
    assert "_play_explosion_death_audio(kind, white_out)" in local_match
    assert "_spawn_explosion(position, blast_radius, white_out)" in local_match
    assert '"white_out_level": 1.0 if white_out else 0.0' in local_match
    assert "var living := _living_participant_indices()" in local_match
    assert "if living.size() <= 1:" in local_match
    assert "func _start_next_turn_or_round" in local_match
    assert "func _fire" in local_match
    assert "LocalMatchHud" in local_match
    assert "LocalMatchShop" in local_match
    assert 'PHASE_SCORE := "score"' in local_match
    assert 'PHASE_WINNER := "winner"' in local_match
    assert "func _build_score_overlay" in local_match
    assert "ScoreOverlay" in local_match
    assert '"Scoring for Round"' in local_match
    assert "Continue to Shop" in local_match
    assert "func _open_round_score" in local_match
    assert "func _apply_classic_round_rewards" in local_match
    assert "_score_round_details[owner]" in local_match
    assert "_score_round_credits[owner]" in local_match
    assert "_participant_is_leader_owner(defeated_owner)" in local_match
    assert "Defeated %s leader +%d" in local_match
    assert "Survived +%d" in local_match
    assert "func _score_rows_snapshot" in local_match
    assert "rows.sort_custom(_score_row_before)" in local_match
    assert '"Round %d of %d  %d players  %s"' in local_match
    assert "func _score_rank_label" in local_match
    assert "func _score_round_detail_for" in local_match
    assert "func _score_activation_delay" in local_match
    assert "func _winner_activation_delay" in local_match
    assert "func _update_modal_activation" in local_match
    assert "if _phase == PHASE_SHOP and _shop_finish_pending:" in local_match
    assert "func _refresh_score_continue_button" in local_match
    assert "_score_continue_button.disabled = _score_continue_delay > 0.0" in local_match
    assert "_score_continue_delay <= -SCORE_AUTO_ADVANCE_TIME" in local_match
    assert "_shop_input_delay = SHOP_INITIAL_INPUT_DELAY" in local_match
    assert "_shop_input_delay = SHOP_ACTION_INPUT_DELAY" in local_match
    assert "_shop_finish_pending = true" in local_match
    assert '"input_locked": _shop_input_delay >= 0.0' in local_match
    assert "func _continue_from_score" in local_match
    assert "if _score_continue_delay > 0.0:" in local_match
    assert "_update_leader_flags()" in local_match
    assert (
        "if _is_final_round():\n"
        "\t\t_hide_score_overlay()\n"
        "\t\t_open_winner_overlay()\n"
        "\t\treturn\n"
        "\t_update_leader_flags()"
        in local_match
    )
    assert "func _hide_score_overlay" in local_match
    assert "func _build_winner_overlay" in local_match
    assert "func _wire_single_button_focus" in local_match
    assert "button.focus_neighbor_left = path" in local_match
    assert "button.focus_neighbor_right = path" in local_match
    assert (
        'if event.is_action_pressed("ui_accept") or event.is_action_pressed("gf_fire"):\n'
        "\t\t\t_continue_from_score()"
        in local_match
    )
    assert 'if event.is_action_pressed("gf_fire"):\n\t\t\t_return_to_main_menu()' in local_match
    assert (
        'if event.is_action_pressed("ui_accept") or event.is_action_pressed("gf_fire") '
        'or event.is_action_pressed("ui_cancel")'
        not in local_match
    )
    assert "WinnerOverlay" in local_match
    assert "var _winner_heading_label: Label" in local_match
    assert '_winner_heading_label.text = "Final Result"' in local_match
    assert 'const MENU_TILE := preload("res://assets/menuback.png")' in local_match
    assert 'var backdrop := Control.new()' in local_match
    assert '"WinnerMenuBackground"' in local_match
    assert "TextureRect.STRETCH_TILE" in local_match
    assert "GroundfireTheme.COLOR_MENU_TILE_TINT" in local_match
    assert "WINNER_BACKGROUND_SCROLL_SPEED := 0.1" in local_match
    assert "var _winner_exit_pending := false" in local_match
    assert "func _update_winner_background" in local_match
    assert "_winner_background_scroll += delta * WINNER_BACKGROUND_SCROLL_SPEED" in local_match
    assert "_winner_background.offset_left = -offset.x" in local_match
    assert "func _open_winner_overlay" in local_match
    assert "func _winner_rows_snapshot" in local_match
    assert "func _refresh_winner_continue_button" in local_match
    assert "_winner_main_menu_button.disabled = _winner_continue_delay > 0.0" in local_match
    assert (
        "if _winner_exit_pending or (not _has_human_participants() and _winner_continue_delay <= 0.0):"
        in local_match
    )
    assert "_winner_exit_pending = true" in local_match
    assert "_winner_main_menu_button.visible = false" in local_match
    assert "_winner_main_menu_button.focus_mode = Control.FOCUS_NONE" in local_match
    assert "_winner_main_menu_button.grab_focus.call_deferred()" not in local_match
    assert 'row["winner"] = int(row.get("score", 0)) == top_score' in local_match
    assert "Pygame WinnerMenu shows only winner cards" in local_match
    assert "_winner_summary_label.visible = false" in local_match
    assert "_winner_rows_container.visible = false" in local_match
    assert "func _winner_card_snapshots" in local_match
    assert '"Final result after %d rounds  %d players  Top score %d"' not in local_match
    assert "Continue to Final Result" in local_match
    assert "We have a winner!" in local_match
    assert "It's a tie!" in local_match
    assert "func _is_final_round" in local_match
    assert "func _build_shop_overlay" in local_match
    assert "func _open_post_round_shop" in local_match
    assert "func _refresh_shop_overlay" in local_match
    assert "func _buy_shop_weapon" in local_match
    assert "func _buy_jump_jet" in local_match
    assert '"Need $%d for %s."' in local_match
    assert "func _shop_items_snapshot" in local_match
    assert "func _prepare_shop_pass" in local_match
    assert "func _current_shop_participant_index" in local_match
    assert "func _advance_shop_participant" in local_match
    assert "func _shop_participant_name" in local_match
    assert "func _shop_inventory" in local_match
    assert "func _shop_credits" in local_match
    assert "func _set_shop_credits" in local_match
    assert "func _shop_fuel_reserve" in local_match
    assert "func _add_shop_fuel_reserve" in local_match
    assert 'SHOP_JUMP_JET := "Jump Jet"' in local_match
    assert "SHOP_JUMP_JET_COST := 50" in local_match
    assert "_add_shop_fuel_reserve(shopper_index, TankState.TANK_FUEL_PURCHASE_AMOUNT)" in local_match
    assert '"%d%% reserve"' in local_match
    assert "func _continue_from_shop" in local_match
    assert "func _finish_shop_and_start_next_round" in local_match
    assert "func _complete_computer_shop_passes" in local_match
    assert "func _run_computer_shop_for_participant" in local_match
    assert "_run_computer_shop_for_participant(shopper_index)" in local_match
    assert '"%s is done shopping."' in local_match
    assert "continue_requested.connect" in local_match
    assert "buy_requested.connect" in local_match
    assert '"reward": _shop_reward' in local_match
    assert '"round": min(_round + 1, _total_rounds)' in local_match
    assert '"total_rounds": _total_rounds' in local_match
    assert '"shopper_name": _shop_participant_name(shopper_index)' in local_match
    assert '"fuel_reserve": int(round(_shop_fuel_reserve(shopper_index) * 100.0))' in local_match
    assert '"shop_items": _shop_items_snapshot()' in local_match
    assert '"player_fuel_max": int(TankState.TANK_FULL_FUEL * 100.0)' in local_match
    assert '"player_fuel_reserve": int(round(float(active_tank.get("fuel_reserve")) * 100.0))' in local_match
    assert '"target_name": str(target_tank.get("name"))' in local_match
    assert '"target_hp": int(target_tank.get("health"))' in local_match
    assert '"target_wins": _participant_wins(_target_index)' in local_match
    assert '"participant_summary": _participant_hud_summary()' in local_match
    assert '"participants": _participant_rows_snapshot()' in local_match
    assert '"active_index": _turn_index' in local_match
    assert '"target_index": _target_index' in local_match
    assert '"health": tank_health' in local_match
    assert '"fuel": tank_fuel' in local_match
    assert '"weapon": weapon_name' in local_match
    assert "func _draw_tank_gun_arrow" in local_match
    assert "func _tank_gun_arrow_geometry" in local_match
    assert 'tank.call("tank_center")' in local_match
    assert "var shaft_start := center + direction * TANK_GUN_ARROW_START_OFFSET" in local_match
    assert "var head_tip := center + direction * (arrow_length * TANK_GUN_ARROW_HEAD_TIP_SCALE)" in local_match
    assert '"shaft_polygon": PackedVector2Array' in local_match
    assert '"head_polygon": PackedVector2Array' in local_match
    assert 'Color("#00ff0080")' in local_match
    assert "func _tank_weapon_ready" in local_match
    assert 'int(inventory.call("current_ammo")) == 0' in local_match
    assert 'inventory.call("is_current_ready")' in local_match
    assert "func set_snapshot" in hud
    assert '"player_wins"' in hud
    assert '"player_name"' in hud
    assert '"enemy_name"' in hud
    assert '"target_name"' in hud
    assert '"target_hp"' in hud
    assert '"target_wins"' in hud
    assert '"participant_summary"' in hud
    assert 'str(_snapshot.get("target_name", _snapshot.get("enemy_name", "Enemy")))' in hud
    assert '"player_fuel_max"' in hud
    assert '"player_fuel_reserve"' in hud
    assert '"Reserve"' in hud
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
    assert "ANGLE_MIN := -75.0" in hud
    assert "ANGLE_MAX := 75.0" in hud
    assert "POWER_MIN := 1.0" in hud
    assert "POWER_MAX := 20.0" in hud
    assert '"angle": 0' in hud
    assert '"power": 10' in hud
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
    assert "CLASSIC_HUD_SPACING := 2.5" in hud
    assert "CLASSIC_PANEL_COLOR := Color8(128, 230, 153, 76)" in hud
    assert "func _draw_classic_tank_hud" in hud
    assert "func _draw_classic_weapon_graphic" in hud
    assert "func _classic_health_color" in hud
    assert "func _classic_fuel_color" in hud
    assert "func _world_to_screen" in hud
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
    assert "func _should_skip_linked_superblock_clip" in terrain
    assert "func _blast_state_at_point" in terrain
    assert "func _clamped_blast_interval_for_chunk_side" in terrain
    assert "func _bottom_blast_state_for_chunk_side" in terrain
    assert "_world_height_to_screen(CLASSIC_MIN_LAND_HEIGHT)" in terrain
    assert "func _align_clipped_side_parts" in terrain
    assert "func _split_single_part_to_match" in terrain
    assert "func _vertical_color_at" in terrain
    assert "func _refresh_chunk_colors" in terrain
    assert "func _parts_preserve_chunk_bottom" in terrain
    assert "func _apply_detached_motion" in terrain
    assert "func _start_detached_fall" in terrain
    assert "func _apply_chunk_motion" in terrain
    assert "func _propagate_removed_linked_top" in terrain
    assert "func _superblock_start" in terrain
    assert "func _superblock_motion_for_index" in terrain
    assert 'elif bool(superblock_motion.get("falling", false))' in terrain
    assert "support_cut" in terrain
    assert "func _superblock_landing_gap" in terrain
    assert "func _superblock_landing_gaps" in terrain
    assert "func _settle_landed_superblock" in terrain
    assert "func _chunk_motion" in terrain
    assert "func _move_chunk_edges" in terrain
    assert "func _move_superblock_edges" in terrain
    assert "left_fall_amount" in terrain
    assert "right_fall_amount" in terrain
    assert "var next_speed: float" in terrain
    assert "speed + _fall_acceleration * delta" in terrain
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
    assert "func move_to_ground" in terrain
    assert "func _chunk_state_at_offset" in terrain
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
    assert 'preload("res://assets/arrow.png")' in local_match
    assert "func _mouse_cursor_draw_points" in local_match
    assert "func _mouse_cursor_draw_uvs" in local_match
    assert "func _sync_classic_mouse_cursor_mode" in local_match
    assert "func _restore_classic_mouse_cursor_mode" in local_match
    assert "Input.MOUSE_MODE_HIDDEN" in local_match
    assert "func _load_gameplay_options" in local_match
    assert "_screen_shake_enabled" in local_match
    assert "_camera_smoothing" in local_match
    assert "_mouse_aim_enabled" in local_match
    assert "var _mouse_aim_enabled := false" in local_match
    assert "_mouse_world_position" in local_match
    assert "projectile_velocity.normalized()" in local_match
    assert "_add_camera_shake(crater_radius)" in local_match
    assert "draw_set_transform" in local_match
    assert "position.x > _world_size.x" in local_match
    assert "var clamped_x: float = clampf(position.x, 0.0, _world_size.x)" in local_match
    assert "_terrain.height_at(clamped_x)" in local_match
    assert "position.y > _world_size.y + PROJECTILE_WORLD_MARGIN" in local_match
    assert "func move_on_terrain" in tank
    assert "func _ground_position_for_query" in tank
    assert 'terrain.has_method("move_to_ground")' in tank
    assert "func boost" in tank
    assert "func update_gun" in tank
    assert "GUN_ANGLE_MIN := -75.0" in tank
    assert "GUN_ANGLE_MAX := 75.0" in tank
    assert "GUN_ANGLE_DEFAULT := 0.0" in tank
    assert "GUN_ANGLE_CHANGE_ACCELERATION := 60.0" in tank
    assert "GUN_ANGLE_MAX_CHANGE_SPEED := 75.0" in tank
    assert "GUN_POWER_MIN := 1.0" in tank
    assert "GUN_POWER_MAX := 20.0" in tank
    assert "GUN_POWER_DEFAULT := 10.0" in tank
    assert "GUN_POWER_PIXEL_SCALE := 5.5" in tank
    assert "GUN_POWER_CHANGE_ACCELERATION := 20.0" in tank
    assert "GUN_POWER_MAX_CHANGE_SPEED := 50.0" in tank
    assert "TANK_MAX_HEALTH := 100" in tank
    assert "TANK_FULL_FUEL := 1.0" in tank
    assert "TANK_FUEL_PURCHASE_AMOUNT := 1.0" in tank
    assert "fuel_capacity := TANK_FULL_FUEL" in tank
    assert "fuel_reserve := TANK_FULL_FUEL" in tank
    assert "func add_fuel_capacity" in tank
    assert "func add_fuel_reserve" in tank
    assert "func _spend_fuel" in tank
    assert "gun_angle = GUN_ANGLE_DEFAULT" in tank
    assert "gun_power = GUN_POWER_DEFAULT" in tank
    assert "health = TANK_MAX_HEALTH" in tank
    assert "fuel = min(TANK_FULL_FUEL, fuel_reserve)" in tank
    assert '"fuel_reserve": fuel_reserve' in tank
    assert "GUN_ANGLE_MIN, GUN_ANGLE_MAX" in tank
    assert "GUN_POWER_MIN, GUN_POWER_MAX" in tank
    assert "TANK_BOOST_ACCELERATION := 133.0" in tank
    assert "BOOST_FUEL_USAGE_RATE := 0.2" in tank
    assert "BOOST_TURN_RATE := 90.0" in tank
    assert "BOOST_TURN_LIMIT := 15.0" in tank
    assert "TANK_AIR_GRAVITY := 95.0" in tank
    assert "TANK_GROUND_DETACH_THRESHOLD := 2.0" in tank
    assert "TANK_MOVE_SPEED := 74.0" in tank
    assert "TANK_SLOPE_DRAG_SCALE := 65.0" in tank
    assert "TANK_MIN_SLOPE_MOVE_FACTOR := 0.35" in tank
    assert "TANK_PASSIVE_SLIDE_THRESHOLD := 30.0" in tank
    assert "TANK_BODY_HALF_WIDTH := 26.0" in tank
    assert "TANK_CENTER_OFFSET := TANK_BODY_HALF_WIDTH * 0.5" in tank
    assert "GUN_LAUNCH_OFFSET := TANK_BODY_HALF_WIDTH * 1.2" in tank
    assert "airborne_velocity.y += TANK_AIR_GRAVITY * delta" in tank
    assert "ground_position.y > position.y + TANK_GROUND_DETACH_THRESHOLD" in tank
    assert "func _apply_passive_slope_slide" in tank
    assert "abs(ground_angle) <= TANK_PASSIVE_SLIDE_THRESHOLD" in tank
    assert "var horizontal_delta: float = cos(deg_to_rad(ground_angle)) * slide_speed * delta" in tank
    assert "position.x - sign(ground_angle) * horizontal_delta" in tank
    assert "if not on_ground:\n\t\treturn" in tank
    assert "var track_delta: float = (direction + slope_term) * TANK_MOVE_SPEED * delta" in tank
    assert "position.x + cos(deg_to_rad(tank_angle)) * track_delta" in tank
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
    assert "func gun_direction" in tank
    assert "func tank_center" in tank
    assert "-sin(radians) * TANK_CENTER_OFFSET" in tank
    assert "return tank_center() + gun_direction() * GUN_LAUNCH_OFFSET" in tank
    assert "func launch_velocity" in tank
    assert "return airborne_velocity + gun_direction() * power * GUN_POWER_PIXEL_SCALE * speed_multiplier" in tank
    assert "func apply_damage" in tank
    assert "health < 0 and state == STATE_ALIVE" in tank
    assert "GROUND_SMOKE_RELEASE_TIME := 1.0" in tank
    assert "AIR_SMOKE_RELEASE_TIME := 0.05" in tank
    assert "SMOKE_TEXTURE_ID := 5" in tank
    assert "GROUND_SMOKE_Y_OFFSET := 0.2" in tank
    assert "SMOKE_Y_VELOCITY := 0.5" in tank
    assert "SMOKE_ROTATION_RATE := 0.1" in tank
    assert "GROUND_SMOKE_GROWTH_RATE := 0.3" in tank
    assert "GROUND_SMOKE_FADE_RATE := 0.15" in tank
    assert "AIR_SMOKE_FADE_RATE := 0.3" in tank
    assert "BOOST_SMOKE_RELEASE_TIME := 0.05" in tank
    assert "BOOST_SMOKE_TEXTURE_ID := 2" in tank
    assert "BOOST_SMOKE_VELOCITY := 2.0" in tank
    assert "BOOST_SMOKE_FADE_RATE := 2.5" in tank
    assert "var exhaust_time := 0.0" in tank
    assert "exhaust_time = -0.5" in tank
    assert "func _update_smoke_particles" in local_match
    assert "func _update_tank_burn_smoke" in local_match
    assert "func _emit_tank_burn_smoke" in local_match
    assert "func _emit_jump_jet_smoke" in local_match
    assert (GODOT_ROOT / "assets" / "smoke.png").exists()
    assert 'preload("res://assets/smoke.png")' in local_match
    assert "func _draw_smoke_particle" in local_match
    assert "func _smoke_particle_draw_points" in local_match
    assert "func _smoke_particle_draw_uvs" in local_match
    assert "draw_polygon(" in local_match
    assert "SMOKE_TEXTURE" in local_match
    assert 'draw_circle(Vector2(smoke.get("position", Vector2.ZERO))' not in local_match
    assert "TankState.GROUND_SMOKE_RELEASE_TIME if on_ground else TankState.AIR_SMOKE_RELEASE_TIME" in local_match
    assert "TankState.BOOST_SMOKE_TEXTURE_ID" in local_match
    assert "TankState.BOOST_SMOKE_VELOCITY * TankState.GUN_POWER_PIXEL_SCALE" in local_match
    assert "const MACHINE_GUN" in weapons
    assert "const NUKE" in weapons
    assert '"kind": "mirv"' in weapons
    assert "LIMITED_WEAPON_INITIAL_STOCK := 0" in weapons
    assert "ROUND_STARTING_COOLDOWN_ADVANCE := 2.0" in weapons
    assert "SHELL_COOLDOWN := 4.0" in weapons
    assert "MIRV_ROUND_AMMO := 1" in weapons
    assert "MIRV_DAMAGE := 30" in weapons
    assert "MIRV_FRAGMENTS := 5" in weapons
    assert "MIRV_SPREAD := 0.2" in weapons
    assert '"ammo": LIMITED_WEAPON_INITIAL_STOCK, "shop_pack": MIRV_SHOP_PACK' in weapons
    assert '"damage": MIRV_DAMAGE' in weapons
    assert '"fragments": MIRV_FRAGMENTS' in weapons
    assert '"spread": MIRV_SPREAD' in weapons
    assert '"fuel": 3.0' in weapons
    assert '"steer_sensitivity": 300.0' in weapons
    assert '"powered_speed": MISSILE_CLASSIC_SPEED' in weapons
    assert '"damage": 2' in weapons
    assert '"blast": 0.0' in weapons
    assert '"direct_damage": true' in weapons
    assert "DEFAULT_AMMO_SPEND := 1" in weapons
    assert "MACHINE_GUN_ROUND_AMMO := 50" in weapons
    assert "MACHINE_GUN_VOLLEY := 5" in weapons
    assert "MACHINE_GUN_COOLDOWN := 0.1" in weapons
    assert "MACHINE_GUN_SHOP_PACK := 50" in weapons
    assert "MACHINE_GUN_TRACER_GRAVITY := 190.0" in weapons
    assert "MACHINE_GUN_CLASSIC_POWER := 25.0" in weapons
    assert "MIRV_MIN_FRAGMENT_SPREAD_SPEED := 0.0" in weapons
    assert "MIRV_SHOP_PACK := 1" in weapons
    assert "MIRV_COOLDOWN := 7.5" in weapons
    assert "MISSILE_SHOP_PACK := 5" in weapons
    assert "MISSILE_CLASSIC_SPEED := 9.0" in weapons
    assert "MISSILE_COOLDOWN := 5.0" in weapons
    assert "NUKE_SHOP_PACK := 1" in weapons
    assert "NUKE_COOLDOWN := 10.0" in weapons
    assert '"ammo": LIMITED_WEAPON_INITIAL_STOCK, "shop_pack": MACHINE_GUN_SHOP_PACK' in weapons
    assert '"shop_pack": MACHINE_GUN_SHOP_PACK' in weapons
    assert '"cooldown": MACHINE_GUN_COOLDOWN' in weapons
    assert '"cooldown": SHELL_COOLDOWN' in weapons
    assert '"cooldown": MIRV_COOLDOWN' in weapons
    assert '"cooldown": MISSILE_COOLDOWN' in weapons
    assert '"cooldown": NUKE_COOLDOWN' in weapons
    assert '"tracer_gravity": MACHINE_GUN_TRACER_GRAVITY' in weapons
    assert '"launch_power": MACHINE_GUN_CLASSIC_POWER' in weapons
    assert '"min_fragment_spread_speed": MIRV_MIN_FRAGMENT_SPREAD_SPEED' in weapons
    assert '"white_out": true' in weapons
    assert "func consume_current" in weapons
    assert "func consume_current_amount" in weapons
    assert "func consume_ammo" in weapons
    assert "func update_current_cooldown" in weapons
    assert "func is_current_ready" in weapons
    assert "func current_cooldown" in weapons
    assert "func select_shell" in weapons
    assert "select_shell()" in weapons
    assert '"volley": MACHINE_GUN_VOLLEY' in weapons
    assert 'current().get("volley", DEFAULT_AMMO_SPEND)' in weapons
    assert "func ammo_for" in weapons
    assert "func stock_for" in weapons
    assert "func weapon_by_name" in weapons
    assert "func select_by_name" in weapons
    assert "func has_ammo" in weapons
    assert "func weapon_cost" in weapons
    assert "func ammo_pack_size" in weapons
    assert 'weapon.get("shop_pack", weapon.get("ammo", 0))' in weapons
    assert "func add_ammo" in weapons
    assert "func inventory_snapshot" in weapons
    assert '"stock"' in weapons
    assert '"selected"' in weapons
    assert '"ammo": 0, "shop_pack": ROLLING_MINES_SHOP_PACK' in weapons
    assert '"ammo": 0, "shop_pack": AIRSTRIKE_SHOP_PACK' in weapons
    assert '"ammo": 0, "shop_pack": DEATHS_HEAD_SHOP_PACK' in weapons
    assert '"ammo": 0, "shop_pack": HOVER_COIL_SHOP_PACK' in weapons
    assert '"ammo": 0, "shop_pack": CORBOMITE_SHOP_PACK' in weapons
    assert '"inventory": _shop_inventory(shopper_index).inventory_snapshot()' in local_match
    assert "CLASSIC_DISABLED_SHOP_WEAPONS" in local_match
    assert "is not available in the classic shop" in local_match
    assert "signal continue_requested" in shop
    assert "signal buy_requested" in shop
    assert "func refresh" in shop
    assert "func _rebuild_weapon_rows" in shop
    assert "var _focus_buttons: Array[Button]" in shop
    assert "func _wire_vertical_focus" in shop
    assert "func _remember_shop_focus" in shop
    assert "func _restore_shop_focus" in shop
    assert '"shop_focus_name"' in shop
    assert 'var input_locked := bool(_state.get("input_locked", false))' in shop
    assert "_continue_button.disabled = input_locked" in shop
    assert "buy_button.disabled = input_locked or cost <= 0 or credits < cost" in shop
    assert "buy_button.disabled = input_locked or item_cost <= 0 or credits < item_cost" in shop
    assert "focus_neighbor_top" in shop
    assert "focus_neighbor_bottom" in shop
    assert "focus_neighbor_left" in shop
    assert "focus_neighbor_right" in shop
    assert '"Round %d of %d  Score %d  Reward %d"' in shop
    assert '"%s  Money %s  Fuel reserve %d%%"' in shop
    assert "Fuel reserve %d%%" in shop
    assert "func _format_money" in shop
    assert 'return "$%d" % value' in shop
    assert 'CLASSIC_BUY_ACTION_LABEL := "Buy"' in shop
    assert "_shop_button(CLASSIC_BUY_ACTION_LABEL)" in shop
    assert "func _cost_cell" in shop
    assert "CLASSIC_SHOP_DISPLAY_NAMES" in shop
    assert '"MIRV": "Mirvs"' in shop
    assert '"Missile": "Missiles"' in shop
    assert '"Nuke": "Nukes"' in shop
    assert "func _catalog_display_name" in shop
    assert 'label.text = _catalog_display_name(weapon_name)' in shop
    assert 'label.text = _catalog_display_name(item_name)' in shop
    assert '"classic_shop_stock"' in shop
    assert '"classic_shop_pack"' in shop
    assert "CLASSIC_LIMITED_STOCK_INDICATORS" in shop
    assert "func _selected_limited_stock_text" in shop
    assert 'return "x%d" % max(0, stock_amount)' in shop
    assert "func _selected_weapon_bar_value" in shop
    assert 'weapon_name != "Machine Gun"' in shop
    assert "float(stock_amount) / 50.0" in shop
    assert "func _selected_shop_item_bar_value" in shop
    assert 'item_name != "Jump Jet"' in shop
    assert 'float(_state.get("fuel_reserve", 100)) / 100.0' in shop
    assert "func _classic_bar_indicator" in shop
    assert '"classic_shop_indicator_kind"' in shop
    assert '"classic_shop_bar_value"' in shop
    assert '"classic_shop_bar_fraction"' in shop
    assert '"classic_shop_effect"' in shop
    assert '"classic_shop_current"' in shop
    assert "label.text = _format_money(cost)" in shop
    assert (
        "row.add_child(_cost_cell(cost, GroundfireTheme.COLOR_TEXT if selected else GroundfireTheme.COLOR_WARN))"
        in shop
    )
    assert (
        "row.add_child(_cost_cell(item_cost, GroundfireTheme.COLOR_TEXT if selected else GroundfireTheme.COLOR_WARN))"
        in shop
    )
    assert '"selected_position"' in shop
    assert '"classic_shop_selected"' in shop
    assert '"shop_items"' in shop
    assert "DISABLED_CLASSIC_ITEMS" in shop
    assert '"Rolling Mines"' in shop
    assert '"Airstrike"' in shop
    assert '"Death\'s Head"' in shop
    assert '"Hover Coil"' in shop
    assert '"Corbomite"' in shop
    assert "func _add_disabled_catalog_rows" in shop
    assert "func _disabled_shop_items" in shop
    assert '"Locked"' not in shop
    assert "Not migrated yet" not in shop
    assert "continue_requested.emit()" in shop
    assert "buy_requested.emit(captured_name)" in shop
    assert 'TRANSPORT_WEBSOCKET := "websocket"' in network
    assert 'MESSAGE_HELLO := "hello"' in network
    assert 'MESSAGE_PING := "ping"' in network
    assert "PROTOCOL_VERSION := 1" in network
    assert "MIN_SUPPORTED_PROTOCOL := 1" in network
    assert "MAX_SUPPORTED_PROTOCOL := PROTOCOL_VERSION" in network
    assert "SERVER_ERROR_CATEGORY_CREDENTIALS" in network
    assert "SERVER_ERROR_CATEGORY_CAPACITY" in network
    assert "SERVER_ERROR_CATEGORY_SERVER_STATE" in network
    assert "SERVER_ERROR_CATEGORY_ACCESS" in network
    assert "SERVER_ERROR_CATEGORY_MATCH" in network
    assert "SERVER_ERROR_CATEGORY_TRANSIENT" in network
    assert "SERVER_ERROR_CATEGORY_PROTOCOL" in network
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
    assert "static func client_supports_protocol" in network
    assert "static func negotiated_protocol" in network
    assert "static func server_supports_client_protocol" in network
    assert "static func protocol_status_message" in network
    assert "static func is_fatal_server_error" in network
    assert "static func server_error_category" in network
    assert "static func server_error_recovery_hint" in network
    assert "static func server_error_status_message" in network
    assert '"invalid_password"' in network
    assert '"authentication_failed"' in network
    assert '"server_full"' in network
    assert '"Join failed: password rejected' in network
    assert "Check credentials or request a fresh session token." in network
    assert "Wait for a slot or choose another server." in network
    assert "Update the client or choose a compatible server." in network
    assert "supported_protocols" in network
    assert "_protocol_support_label" in network
    assert "static func staged_connect_message" in network
    assert '"protocol": PROTOCOL_VERSION' in network
    assert '"missing_protocol"' in network
    assert '"protocol_mismatch"' in network
    assert '"expected_protocol"' in network
    assert "static func _server_supported_protocols" in network
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
    assert "func _exit_tree" in websocket
    assert 'NetworkAdapter.disconnect_message("node_exit")' in websocket
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
    assert "func _exit_tree" in script
    assert '_websocket_client.disconnect_from_endpoint("online_match_exit")' in script
    assert "_auth_token" in script
    assert 'str(_entry.get("auth_token", ""))' in script
    assert "_session_token_url" in script
    assert 'str(_entry.get("session_token_url", ""))' in script
    assert "func _request_session_token" in script
    assert "func _on_session_token_request_completed" in script
    assert "func _session_token_request_url" in script
    assert "func _has_session_auth_token" in script
    assert "_session_token_received = true" in script
    assert "Cache-Control: no-store" in script
    assert "player_name=%s" in script
    assert '"Session token received."' in script
    assert '"Join failed: session token response was cacheable."' in script
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
    assert "gf_shield" in script
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
    assert "func _mark_session_healthy" in script
    assert "_mark_session_healthy()" in script
    assert '"websocket_connected":\n\t\t_reconnect_timer = 0.0' in script
    assert '"websocket_connected":\n\t\t_reconnect_attempt = 0' not in script
    assert "PING_INTERVAL" in script
    assert "PREDICTION_MOVE_STEP" in script
    assert "INTERPOLATION_RATE" in script
    assert "LOCAL_RECONCILE_RATE" in script
    assert "PROJECTILE_EXTRAPOLATION_SECONDS" in script
    assert "func _schedule_reconnect" in script
    assert "func _update_reconnect" in script
    assert '"Reconnect"' in script
    assert '"Back"' in script
    assert "func _wire_overlay_focus" in script
    assert "_manual_reconnect_button.focus_neighbor_left = back_path" in script
    assert "_manual_reconnect_button.focus_neighbor_top = reconnect_path" in script
    assert "_back_button.focus_neighbor_right = reconnect_path" in script
    assert "_manual_reconnect_button.grab_focus.call_deferred()" in script
    assert "func _manual_reconnect" in script
    assert "func _return_to_main_menu" in script
    assert 'disconnect_from_endpoint("manual_reconnect")' in script
    assert "_pending_commands.clear()" in script
    assert "func _draw_network_diagnostics" in script
    assert "func _ingest_acknowledgements" in script
    assert "func _apply_local_prediction" in script
    assert "_last_prediction_error" in script
    assert '"prediction error: %.2f"' in script
    assert "_last_latency_ms" in script
    assert "_pending_commands" in script
    assert "acknowledged_command_sequence" in script
    assert "match_snapshot" in script
    assert "terrain_profile" in script


def test_control_settings_persist_input_bindings():
    script = (GODOT_ROOT / "scripts" / "control_settings.gd").read_text(encoding="utf-8")
    local_match = (GODOT_ROOT / "scripts" / "local_match.gd").read_text(encoding="utf-8")

    assert 'SETTINGS_PATH := "user://groundfire_controls.cfg"' in script
    assert "DEFAULT_BINDINGS" in script
    assert "static func apply_saved_bindings" in script
    assert "ACTION_ORDER" in script
    assert "CLASSIC_REBIND_ACTION_ORDER" in script
    assert "CLASSIC_LINKED_ACTIONS" in script
    assert "for action_name in CLASSIC_REBIND_ACTION_ORDER:" in script
    assert '"gf_fire"' in script
    assert '"gf_weapon_next"' in script
    assert '"gf_weapon_prev"' in script
    assert '"gf_shield"' in script
    assert '"gf_pause": KEY_ESCAPE' in script
    assert '"gf_pause": JOY_BUTTON_START' in script
    assert 'for action_name in ACTION_ORDER:' in script
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
    assert "CLASSIC_ACTION_DISPLAY_NAMES" in script
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
    assert "static func _set_saved_gamepad_none" in script
    assert "static func _saved_or_default_gamepad_binding_is_axis" in script
    assert "static func _gamepad_section" in script
    assert "Input.get_connected_joypads()" in script
    assert '"gamepad_device_%d"' in script
    assert ".device = device_id" in script
    assert "InputMap.action_erase_events" in script
    classic_keyboard_defaults = {
        "gf_fire": "KEY_SPACE",
        "gf_weapon_next": "KEY_O",
        "gf_weapon_prev": "KEY_U",
        "gf_jump": "KEY_I",
        "gf_shield": "KEY_K",
        "gf_move_left": "KEY_J",
        "gf_move_right": "KEY_L",
        "gf_aim_left": "KEY_A",
        "gf_aim_right": "KEY_D",
        "gf_power_up": "KEY_W",
        "gf_power_down": "KEY_S",
    }
    for action_name, key_name in classic_keyboard_defaults.items():
        assert f'"{action_name}": {key_name}' in script
        assert f'_ensure_key_action("{action_name}", {key_name})' in local_match
    classic_action_labels = [
        "Fire Weapon",
        "Change Weapon Up",
        "Change Weapon Down",
        "Use Jump Jets",
        "Use Shield",
        "Move Tank Left",
        "Move Tank Right",
        "Rotate Gun Left",
        "Rotate Gun Right",
        "Increase Gun Power",
        "Decrease Gun Power",
    ]
    for label in classic_action_labels:
        assert f'"{label}"' in script
    classic_linked_actions = {
        "gf_weapon_next": "gf_weapon_prev",
        "gf_weapon_prev": "gf_weapon_next",
        "gf_move_left": "gf_move_right",
        "gf_move_right": "gf_move_left",
        "gf_aim_left": "gf_aim_right",
        "gf_aim_right": "gf_aim_left",
        "gf_power_up": "gf_power_down",
        "gf_power_down": "gf_power_up",
    }
    for action_name, linked_action in classic_linked_actions.items():
        assert f'"{action_name}": "{linked_action}"' in script
    rebind_order = script.split("const CLASSIC_REBIND_ACTION_ORDER := [", 1)[1].split("]", 1)[0]
    assert '"gf_pause"' not in rebind_order
    classic_gamepad_button_defaults = {
        "gf_fire": 0,
        "gf_weapon_next": 2,
        "gf_weapon_prev": 1,
        "gf_jump": 3,
        "gf_shield": 4,
        "gf_move_left": 6,
        "gf_move_right": 7,
    }
    for action_name, button_index in classic_gamepad_button_defaults.items():
        assert f'"{action_name}": {button_index}' in script
    for axis_label in [
        "Joystick/Pad Right",
        "Joystick/Pad Left",
        "Joystick/Pad Up",
        "Joystick/Pad Down",
        "Axis 3 (-)",
        "Axis 3 (+)",
        "Axis 4 (-)",
        "Axis 4 (+)",
    ]:
        assert f'"{axis_label}"' in script
    assert 'CLASSIC_UNDEFINED_LABEL := "<Undefined>"' in script
    assert '"Unbound"' not in script
    assert '"No gamepad"' not in script
    assert '"Joy Button %d" % (button_index + 1)' in script
    assert '"Pad %d"' not in script
    assert '"Axis %d%s"' not in script
    assert 'binding_type == "none"' in script
    assert '"gf_power_up": {"axis": JOY_AXIS_LEFT_Y, "value": 1.0}' in script
    assert '"gf_power_down": {"axis": JOY_AXIS_LEFT_Y, "value": -1.0}' in script
    assert '"gf_move_left": {"axis": JOY_AXIS_RIGHT_X' not in script
    assert '"gf_move_right": {"axis": JOY_AXIS_RIGHT_X' not in script
    assert "Weapon Next" not in script
    assert "Weapon Prev" not in script
    assert 'KEY_TAB' not in script
    assert 'KEY_SHIFT' not in script


def test_migration_strategy_documents_web_feature_rule():
    doc = (PROJECT_ROOT / "docs" / "godot_migration_strategy.md").read_text(encoding="utf-8")

    assert "Godot 4 + GDScript" in doc
    assert "Hidden on web" in doc
    assert "LAN discovery" in doc
    assert "WebSocket/WebRTC" in doc


def test_migration_strategy_declares_compatibility_contract():
    doc = (PROJECT_ROOT / "docs" / "godot_migration_strategy.md").read_text(encoding="utf-8")
    contract_script = (PROJECT_ROOT / "scripts" / "validate_godot_migration_contract.py").read_text(encoding="utf-8")
    fidelity_script = (PROJECT_ROOT / "scripts" / "validate_godot_fidelity.sh").read_text(encoding="utf-8")

    assert "## Migration Compatibility Contract" in doc
    assert "This is now an evolution-first migration." in doc
    assert "`versao-python/` and `versao-godot/godot/` are the canonical editions" in doc
    assert "historical fidelity is comparison material rather than a hard product rule" in doc
    assert "Prefer modern, testable architecture over exact historical coupling" in doc
    assert "use SQLite for mutable runtime state where practical" in doc
    assert "Every migration implementation batch must name its reference material" in doc
    assert "### Compatibility Annotation Template" in doc
    assert "scripts/validate_godot_migration_contract.py" in doc
    assert "validate_godot_migration_contract.py" in fidelity_script
    assert "REQUIRED_GLOBAL_PHRASES" in contract_script
    assert "`versao-python/` and `versao-godot/godot/` are the canonical editions" in contract_script
    assert "PENDING_SECTION_HEADERS" in contract_script

    section_headers = (
        "### 1. Main Menu Visual Parity",
        "### 2. Server Browser Final Visual Parity",
        "### 3. Real Online Server Directory",
        "### 4. Local Match Gameplay Fidelity",
        "### 5. Input And HUD Completion",
        "### 6. Networked Gameplay Adapter",
        "### 7. Export And Runtime Validation",
    )
    compatibility_labels = (
        "`Reference material:`",
        "`User-visible contract:`",
        "`Allowed adaptation:`",
        "`Required validation:`",
    )
    legacy_labels = (
        "`Fidelity target:`",
        "`User-visible invariants:`",
        "`Allowed Godot adaptation:`",
        "`Required validation:`",
    )

    for header in section_headers:
        match = re.search(rf"^{re.escape(header)}\n(?P<body>.*?)(?=^### |^## |\Z)", doc, re.MULTILINE | re.DOTALL)
        assert match is not None
        body = match.group("body")
        labels = compatibility_labels if "Compatibility references:" in body else legacy_labels
        assert "Compatibility references:" in body or "Fidelity annotations:" in body
        for label in labels:
            assert label in body


def test_godot_export_presets_exist_for_desktop_and_web():
    presets = (GODOT_ROOT / "export_presets.cfg").read_text(encoding="utf-8")
    export_script = (PROJECT_ROOT / "scripts" / "export_godot.sh").read_text(encoding="utf-8")
    package_script = (PROJECT_ROOT / "scripts" / "package_godot_release.sh").read_text(encoding="utf-8")
    visual_script = (PROJECT_ROOT / "scripts" / "validate_godot_visuals.sh").read_text(encoding="utf-8")
    fidelity_script = (PROJECT_ROOT / "scripts" / "validate_godot_fidelity.sh").read_text(encoding="utf-8")
    qa_script = (PROJECT_ROOT / "scripts" / "qa_godot_web.sh").read_text(encoding="utf-8")
    hosted_verify_script = (PROJECT_ROOT / "scripts" / "verify_godot_hosted_deployment.py").read_text(
        encoding="utf-8"
    )
    pygame_reference_script = (PROJECT_ROOT / "scripts" / "capture_pygame_references.py").read_text(encoding="utf-8")
    validate_script = (PROJECT_ROOT / "scripts" / "validate_godot.sh").read_text(encoding="utf-8")
    visual_check = (GODOT_ROOT / "tests" / "visual_golden_check.gd").read_text(encoding="utf-8")
    runtime_smoke = (GODOT_ROOT / "tests" / "runtime_smoke_check.gd").read_text(encoding="utf-8")
    main_script = (GODOT_ROOT / "scripts" / "main.gd").read_text(encoding="utf-8")
    local_match_script = (GODOT_ROOT / "scripts" / "local_match.gd").read_text(encoding="utf-8")
    migration_doc = (PROJECT_ROOT / "docs" / "godot_migration_strategy.md").read_text(encoding="utf-8")

    assert 'name="Linux Desktop"' in presets
    assert 'platform="Linux"' in presets
    assert 'name="Web"' in presets
    assert 'platform="Web"' in presets
    assert 'exclude_filter="tests/*"' in presets
    assert "scripts/validate_godot.sh" in export_script
    assert "scripts/validate_godot.sh" in fidelity_script
    assert "res://tests/network_adapter_protocol_check.gd" in validate_script
    assert "res://tests/test_weapon_inventory_ammo.gd" in validate_script
    assert "scripts/validate_godot_migration_contract.py" in fidelity_script
    assert "test_godot_migration_scaffold.py" in fidelity_script
    assert "test_groundfire_net_module.py" in fidelity_script
    assert "test_hosted_deployment_verifier.py" in fidelity_script
    assert "test_replicated_scene.py" in fidelity_script
    assert "test_port_fidelity.py" in fidelity_script
    assert "test_landscape_fidelity.py" in fidelity_script
    assert "GODOT_TEMPLATE_DIR" in export_script
    assert "web_nothreads_release.zip" in export_script
    assert "linux_release.x86_64" in export_script
    assert '--export-release "Linux Desktop"' in export_script
    assert '--export-release "Web"' in export_script
    assert "classic_selector.gd" in validate_script
    assert "runtime_smoke_check.gd" in validate_script
    assert "visible_server_browser_tabs_for(true)" in runtime_smoke
    assert "MainScene.instantiate()" in runtime_smoke
    assert 'preload("res://scripts/classic_selector.gd")' in runtime_smoke
    assert "func _find_classic_selector_with_items" in runtime_smoke
    assert "func _check_main_menu_responsive_metrics" in runtime_smoke
    assert "func _check_menu_subscreen_responsive_metrics" in runtime_smoke
    assert 'main.call("_show_local_match_setup")' in runtime_smoke
    assert 'main.call("_show_dedicated_server_tools")' in runtime_smoke
    assert "Vector2i(1920, 720)" in runtime_smoke
    assert "ServerBrowserScene.instantiate()" in runtime_smoke
    assert "LocalMatchScene.instantiate()" in runtime_smoke
    assert "OnlineMatchScene.instantiate()" in runtime_smoke
    assert "func _free_node" in runtime_smoke
    assert 'node.call("_prepare_for_shutdown")' in runtime_smoke
    assert "await process_frame" in runtime_smoke
    assert "func _prepare_for_shutdown" in main_script
    assert "_prepare_screen_for_shutdown" in main_script
    assert "func _qa_directory_request" in main_script
    assert "func _qa_should_retry_directory_response" in main_script
    assert "session_gateway_endpoint" in main_script
    assert "func _qa_check_gateway_session_token_join" in main_script
    assert '"gateway_session_token_auth"' in main_script
    assert "signed session-token join fetched auth_token" in main_script
    assert "directory_http_status" in main_script
    assert "directory_body_prefix" in main_script
    assert "func _prepare_for_shutdown" in local_match_script
    assert "func _release_audio_stream" in local_match_script
    assert "player.stream = null" in local_match_script
    assert "GROUNDFIRE_RELEASE_VERSION" in package_script
    assert "GROUNDFIRE_RELEASE_PREFIX" in package_script
    assert "GROUNDFIRE_RELEASE_NOTES" in package_script
    assert "pyproject.toml" in package_script
    assert "tomllib" in package_script
    assert "release_notes" in package_script
    assert "sha256" in package_script
    assert 'PYTHON_BIN="${PYTHON_BIN_FALLBACK:-python}"' in package_script
    assert 'command -v "$PYTHON_BIN"' in package_script
    assert "GODOT_VISUAL_UPDATE=1" in visual_script
    assert "visual_golden_check.gd" in visual_script
    release_script = (PROJECT_ROOT / "scripts" / "validate_godot_release.sh").read_text(encoding="utf-8")
    assert "scripts/validate_godot_fidelity.sh" in release_script
    assert "scripts/qa_godot_web.sh --check" in release_script
    assert "scripts/package_godot_release.sh" in release_script
    assert "sha256sum --check" in release_script
    assert '"docs" / "references" / "pygame_visual"' in pygame_reference_script
    assert "_capture_main_menu" in pygame_reference_script
    assert "_capture_server_browser" in pygame_reference_script
    assert "_capture_local_match" in pygame_reference_script
    assert "qa=browser_runtime" in qa_script
    assert 'PYTHON_BIN="${PYTHON_BIN_FALLBACK:-python}"' in qa_script
    assert "store_phase=$phase" in qa_script
    assert "gateway_endpoint=ws://127.0.0.1:$gateway_port/qa-gateway" in qa_script
    assert "auth_gateway_endpoint=ws://127.0.0.1:$auth_gateway_port/qa-auth-gateway" in qa_script
    assert "full_gateway_endpoint=ws://127.0.0.1:$full_gateway_port/qa-full-gateway" in qa_script
    assert "closed_gateway_endpoint=ws://127.0.0.1:$closed_gateway_port/qa-closed-gateway" in qa_script
    assert "banned_gateway_endpoint=ws://127.0.0.1:$banned_gateway_port/qa-banned-gateway" in qa_script
    assert "session_gateway_endpoint=ws://127.0.0.1:$session_gateway_port/qa-session-gateway" in qa_script
    assert "session_token_url=http://127.0.0.1:$port/qa/session_token.json%3Fphase%3D$phase" in qa_script
    assert "-m groundfire_net.websocket_gateway" in qa_script
    assert "--password qa-secret" in qa_script
    assert "--auth-token qa-token" in qa_script
    assert "--session-secret qa-session-secret" in qa_script
    assert "--max-players 1" in qa_script
    assert "SlotHolder" in qa_script
    assert "--closed" in qa_script
    assert "--ban-player GodotPlayer" in qa_script
    assert "browser_runtime_qa seed" in qa_script
    assert "browser_runtime_qa verify" in qa_script
    assert "GroundfireQAHandler" in qa_script
    assert "def do_GET" in qa_script
    assert "If-None-Match" in qa_script
    assert "self.send_response(304)" in qa_script
    assert "Cache-Control" in qa_script
    assert "X-Groundfire-Directory-Refresh" in qa_script
    assert "groundfire-qa-directory-v1" in qa_script
    assert "/qa/session_token.json" in qa_script
    assert "generate_join_token(SESSION_SECRET, player_name" in qa_script
    assert 'capture local_match_setup "?screen=local_match_setup"' in qa_script

    assert '"local_match_setup"' in qa_script
    assert "missing_cases" in qa_script
    assert "Missing approved browser golden(s)" in qa_script
    assert "--update-goldens after reviewing against docs/references/pygame_visual/" in qa_script
    assert "window.__groundfireQaResult" in qa_script
    assert "Browser runtime QA passed" in qa_script
    assert "server_directory.json" in qa_script
    assert "server_directory.json%3Fphase%3D$phase" in qa_script
    assert "Run scripts/validate_godot_visuals.sh --update-goldens first" in visual_check
    assert "not FileAccess.file_exists(golden_path)" in visual_check
    assert "scripts/export_godot.sh all" in migration_doc
    assert "scripts/package_godot_release.sh" in migration_doc
    assert "scripts/validate_godot_visuals.sh --check" in migration_doc
    assert "scripts/validate_godot_fidelity.sh" in migration_doc
    assert "scripts/validate_godot_release.sh" in migration_doc
    assert "scripts/qa_godot_web.sh --check" in migration_doc
    assert "scripts/verify_godot_hosted_deployment.py" in migration_doc
    assert "scripts/capture_pygame_references.py" in migration_doc
    assert "groundfire-directory" in migration_doc
    assert "DEFAULT_WEB_URL" in hosted_verify_script
    assert "DEFAULT_DIRECTORY_URL" in hosted_verify_script
    assert "If-None-Match" in hosted_verify_script
    assert "application/wasm" in hosted_verify_script
    assert "embeds static auth_token" in hosted_verify_script
    assert "session_token_url must return Cache-Control: no-store" in hosted_verify_script
    assert "directory ETag must be quoted" in hosted_verify_script
    directory_service = (PROJECT_ROOT / "groundfire_net" / "directory_service.py").read_text(encoding="utf-8")
    assert "def directory_diagnostics" in directory_service
    assert "def _etag_matches" in directory_service
    assert 'candidate == "*"' in directory_service
    assert '"/session-token.json"' in directory_service
    assert '"session_tokens_disabled"' in directory_service
    assert '"Cache-Control", "no-store"' in directory_service
    assert "GROUNDFIRE_DIRECTORY_SESSION_SECRET" in directory_service
    assert "allow_static_auth_tokens" in directory_service
    assert "GROUNDFIRE_DIRECTORY_ALLOW_STATIC_AUTH_TOKENS" in directory_service
    assert "--allow-static-auth-tokens" in directory_service
    assert "auth_token is not allowed in public directory entries; use session_token_url" in directory_service
    assert "session_token_url must be http:// or https://" in directory_service
    assert '"/diagnostics.json"' in directory_service
    assert '"invalid_gateway_endpoint"' in directory_service
    assert "/session-token.json?player_name=GodotPlayer" in migration_doc
    assert "GROUNDFIRE_DIRECTORY_SESSION_SECRET" in migration_doc
    assert "--allow-static-auth-tokens" in migration_doc
    assert "GROUNDFIRE_DIRECTORY_ALLOW_STATIC_AUTH_TOKENS" in migration_doc
    assert "docs/references/pygame_visual/" in migration_doc
    assert "Pygame-style top status cards" in migration_doc
    assert "classic translucent per-tank gun arrow" in migration_doc
    assert "Godot Fidelity Audit" in migration_doc
    assert "Current Automated Coverage" in migration_doc
    assert "scripts/validate_godot_fidelity.sh" in migration_doc
    assert "Browser runtime QA" in migration_doc
    assert "seed" in migration_doc
    assert "verify" in migration_doc
    assert "Cache-Control" in migration_doc
    assert "ETag" in migration_doc
    assert "X-Groundfire-Directory-Refresh" in migration_doc
    assert "Release Verification" in migration_doc
    assert "sha256sum --check" in migration_doc
    assert "Signing policy" in migration_doc
    assert "Browser Hosting" in migration_doc
    assert "Distribution Notes" in migration_doc
    assert "build/godot-web/index.html" in migration_doc


def test_ci_has_godot_release_gate():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release_workflow = (PROJECT_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch" in workflow
    assert "run-godot-browser-qa" in workflow
    assert "package-godot" in workflow
    assert "sign-release" in workflow
    assert "godot-release-gate" in workflow
    assert 'GODOT_VERSION: "4.6.2"' in workflow
    assert "Godot_v${godot_tag}_linux.x86_64.zip" in workflow
    assert "Godot_v${godot_tag}_export_templates.tpz" in workflow
    assert "linux_release.x86_64" in workflow
    assert "web_nothreads_release.zip" in workflow
    assert "scripts/validate_godot_release.sh" in workflow
    assert "--browser-qa" in workflow
    assert "--package" in workflow
    assert "inputs.package-godot == 'true' || inputs.sign-release == 'true'" in workflow
    assert 'if [[ "$PACKAGE_GODOT" == "true" || "$SIGN_RELEASE" == "true" ]]; then' in workflow
    assert "Validate GPG signing secrets" in workflow
    assert "test -n \"$RELEASE_GPG_PRIVATE_KEY\"" in workflow
    assert "test -n \"$RELEASE_SIGN_KEY\"" in workflow
    assert "secrets.RELEASE_GPG_PRIVATE_KEY != '' || secrets.RELEASE_SIGN_KEY != ''" in release_workflow
    assert "Validate GPG signing secrets" in release_workflow
