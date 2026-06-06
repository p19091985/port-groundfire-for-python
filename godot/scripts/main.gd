extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const LocalMatchScene := preload("res://scenes/local_match.tscn")
const OnlineMatchScene := preload("res://scenes/online_match.tscn")
const ServerBrowserScene := preload("res://scenes/server_browser.tscn")
const ControlSettings := preload("res://scripts/control_settings.gd")
const ServerDirectory := preload("res://scripts/server_directory.gd")
const BrowserStore := preload("res://scripts/browser_store.gd")
const NetworkAdapter := preload("res://scripts/network_adapter.gd")
const LOGO_TEXTURE := preload("res://assets/logo.png")
const MENU_TILE := preload("res://assets/menuback.png")
const OPTIONS_PATH := "user://groundfire_options.cfg"
const BROWSER_QA_STORE_PATH := "user://qa_server_browser_store.json"
const GAMEPAD_CAPTURE_CANCEL_BUTTON := JOY_BUTTON_BACK
const MENU_REFERENCE_SIZE := Vector2(1024.0, 768.0)
const MENU_MIN_SCALE := 0.72
const MENU_MAX_SCALE := 1.15
const MENU_MARGIN_BASE := Vector2(34.0, 26.0)
const MENU_STACK_SEPARATION_BASE := 14
const MENU_LOGO_BASE_SIZE := Vector2(819.0, 205.0)
const MENU_PANEL_BASE_SIZE := Vector2(420.0, 330.0)
const MENU_BUTTON_BASE_SIZE := Vector2(360.0, 48.0)
const MENU_LOGO_MIN_WIDTH := 590.0
const MENU_LOGO_MAX_WIDTH := 920.0
const MENU_BUTTON_MIN_SIZE := Vector2(259.0, 34.0)
const MENU_BUTTON_MAX_SIZE := Vector2(414.0, 56.0)
const MENU_CONTENT_MAX_WIDTH := 920.0
const MENU_CLASSIC_TOP_SPACER := 150.0
const MENU_CLASSIC_COPY_SPACER := 80.0
const MENU_CLASSIC_PANEL_SPACER := 6.0
const MENU_CLASSIC_PANEL_SIZE := Vector2(718.0, 208.0)
const MENU_CLASSIC_BUTTON_SIZE := Vector2(410.0, 41.0)
const MENU_CLASSIC_BUTTON_FONT_SIZE := 30
const MENU_CLASSIC_SMALL_FONT_SIZE := 20
const OPTIONS_CLASSIC_PANEL_SIZE := Vector2(718.0, 500.0)
const OPTIONS_CLASSIC_TOP_SPACER := 76.0
const OPTIONS_CLASSIC_ROW_SIZE := Vector2(616.0, 41.0)
const OPTIONS_CLASSIC_LABEL_WIDTH := 302.0
const OPTIONS_CLASSIC_CONTROL_WIDTH := 306.0
const OPTIONS_CLASSIC_ROW_FONT_SIZE := 24
const RESOLUTION_PRESETS := [
	{"label": "640 x 480", "size": Vector2i(640, 480)},
	{"label": "800 x 600", "size": Vector2i(800, 600)},
	{"label": "1024 x 768", "size": Vector2i(1024, 768)},
	{"label": "1280 x 960", "size": Vector2i(1280, 960)},
	{"label": "1280 x 1024", "size": Vector2i(1280, 1024)},
	{"label": "1600 x 1200", "size": Vector2i(1600, 1200)},
]
const AI_DIFFICULTIES := ["easy", "normal", "hard"]
const LOCAL_MATCH_ROUND_OPTIONS := [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
const LOCAL_MATCH_DEFAULT_PLAYER_NAME := "Player"
const LOCAL_MATCH_DEFAULT_ENEMY_NAME := "Enemy"
const LOCAL_MATCH_NAME_MAX_LENGTH := 18
const LOCAL_MATCH_MAX_PLAYERS := 8
const LOCAL_MATCH_SLOT_TYPES := ["Human", "Computer"]
const LOCAL_MATCH_CONTROLLER_LABELS := [
	"Keyboard1",
	"Keyboard2",
	"Joystick1",
	"Joystick2",
	"Joystick3",
	"Joystick4",
	"Joystick5",
	"Joystick6",
	"Joystick7",
	"Joystick8",
]
const LOCAL_MATCH_PLAYER_COLORS := [
	Color("#ff00ff"),
	Color("#ff8000"),
	Color("#ffff00"),
	Color("#00ff00"),
	Color("#00ffff"),
	Color("#0000ff"),
	Color("#ff8080"),
	Color("#ffffff"),
]
const GATEWAY_EXECUTABLE_CANDIDATES := [
	"res://../.venv/bin/groundfire-web-gateway",
	"res://../.venv/Scripts/groundfire-web-gateway.exe",
]

var _content: MarginContainer
var _stack: VBoxContainer
var _screen: Control
var _paused_match_screen: Control
var _capabilities: Node
var _dedicated_status_label: Label
var _show_fps := false
var _fullscreen := false
var _resolution_index := 2
var _vsync_enabled := true
var _audio_enabled := true
var _master_volume := 1.0
var _screen_shake_enabled := true
var _camera_smoothing := 1.0
var _mouse_aim_enabled := false
var _ai_difficulty := "normal"
var _server_directory_environment := "dev"
var _server_directory_override_url := ""
var _server_directory_dev_url := ""
var _server_directory_staging_url := ""
var _server_directory_production_url := ""
var _capture_action := ""
var _capture_kind := ""
var _capture_prompt: Label
var _dedicated_gateway_pid := 0
var _dedicated_stop_button: Button
var _dedicated_gateway_form_controls: Array[Control] = []
var _dedicated_gateway_action_buttons: Array[Button] = []
var _dedicated_gateway_host := "127.0.0.1"
var _dedicated_gateway_port := 8765
var _dedicated_gateway_max_players := 0
var _dedicated_gateway_closed := false
var _dedicated_gateway_banned_players := ""
var _in_options := false
var _local_match_setup_rows: Array[Dictionary] = []
var _local_match_setup_status_label: Label
var _local_match_setup_start_button: Button
var _local_match_setup_back_button: Button
var _local_match_setup_rounds: OptionButton
var _classic_fullscreen_layout := false


func _ready() -> void:
	_capabilities = get_node("/root/PlatformCapabilities")
	ControlSettings.apply_saved_bindings()
	_load_options()
	_apply_options()
	_build_layout()
	set_process(true)
	_show_main_menu()
	_apply_web_start_screen.call_deferred()


func _exit_tree() -> void:
	_prepare_for_shutdown()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_apply_menu_layout_metrics()


func _process(_delta: float) -> void:
	if _show_fps:
		queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not _capture_action.is_empty():
		if _is_capture_cancel(event):
			_cancel_input_capture()
			get_viewport().set_input_as_handled()
			_show_options()
			return
		if _capture_kind == "keyboard" and event is InputEventKey and event.pressed and not event.echo:
			ControlSettings.save_key_binding(_capture_action, event.keycode)
			_cancel_input_capture()
			get_viewport().set_input_as_handled()
			_show_options()
			return
		if _capture_kind == "gamepad":
			if event is InputEventJoypadButton and event.pressed:
				ControlSettings.save_gamepad_button_binding(_capture_action, event.button_index)
				_cancel_input_capture()
				get_viewport().set_input_as_handled()
				_show_options()
				return
			if event is InputEventJoypadMotion and abs(event.axis_value) >= ControlSettings.CAPTURE_AXIS_THRESHOLD:
				ControlSettings.save_gamepad_axis_binding(_capture_action, event.axis, event.axis_value)
				_cancel_input_capture()
				get_viewport().set_input_as_handled()
				_show_options()
				return
		return
	if _in_options and event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		_show_main_menu()


func _build_layout() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	_content = MarginContainer.new()
	_content.name = "Content"
	_content.anchor_right = 1.0
	_content.anchor_bottom = 1.0
	add_child(_content)

	_stack = VBoxContainer.new()
	_stack.name = "Stack"
	_stack.alignment = BoxContainer.ALIGNMENT_CENTER
	_stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_content.add_child(_stack)
	_apply_menu_layout_metrics()


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), GroundfireTheme.COLOR_BG)
	var tile_size := MENU_TILE.get_size()
	for x in range(0, int(size.x) + int(tile_size.x), int(tile_size.x)):
		for y in range(0, int(size.y) + int(tile_size.y), int(tile_size.y)):
			draw_texture(MENU_TILE, Vector2(x, y), GroundfireTheme.COLOR_MENU_TILE_TINT)
	if _show_fps:
		draw_string(
			ThemeDB.fallback_font,
			Vector2(12.0, size.y - 12.0),
			"%d FPS" % Engine.get_frames_per_second(),
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			16,
			GroundfireTheme.COLOR_CYAN
		)


func _show_main_menu() -> void:
	_in_options = false
	_discard_paused_match_screen()
	_set_classic_fullscreen_layout(true)
	_stack.alignment = BoxContainer.ALIGNMENT_BEGIN
	_clear_content()
	var has_dedicated_tools: bool = bool(_capabilities.supports(_capabilities.FEATURE_DEDICATED_SERVER_TOOLS))
	var top_spacer: float = max(110.0, MENU_CLASSIC_TOP_SPACER - (28.0 if has_dedicated_tools else 0.0))
	var copy_spacer: float = max(12.0, MENU_CLASSIC_COPY_SPACER - (42.0 if has_dedicated_tools else 0.0))
	_add_spacer(_scaled_classic_value(top_spacer))
	_add_logo()
	_add_center_label("0.25 (Python Port)", MENU_CLASSIC_SMALL_FONT_SIZE)
	_add_center_label("www.groundfire.net", MENU_CLASSIC_SMALL_FONT_SIZE)
	_add_spacer(_scaled_classic_value(copy_spacer))
	_add_center_label("Copyright Tom Russell 2004", MENU_CLASSIC_SMALL_FONT_SIZE)
	_add_center_label("All Rights Reserved", MENU_CLASSIC_SMALL_FONT_SIZE)
	_add_spacer(_scaled_classic_value(MENU_CLASSIC_PANEL_SPACER))

	var classic_button_count := 4 + (1 if has_dedicated_tools else 0)
	var classic_panel_size := MENU_CLASSIC_PANEL_SIZE + Vector2(0.0, max(0, classic_button_count - 4) * 51.0)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", GroundfireTheme.classic_panel_style())
	panel.custom_minimum_size = _scaled_menu_size(classic_panel_size)
	panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_stack.add_child(panel)

	var menu := VBoxContainer.new()
	menu.alignment = BoxContainer.ALIGNMENT_BEGIN
	menu.add_theme_constant_override("separation", 10)
	panel.add_child(menu)
	var menu_buttons: Array[Button] = []
	menu_buttons.append(_add_classic_button_to(menu, "Start Game", _show_local_match_setup))
	menu_buttons.append(_add_classic_button_to(menu, "Find Servers", _on_find_servers))
	if has_dedicated_tools:
		menu_buttons.append(_add_classic_button_to(menu, "Dedicated Server", _on_dedicated_server))
	menu_buttons.append(_add_classic_button_to(menu, "Options", _on_options))
	menu_buttons.append(_add_classic_button_to(menu, "Quit", _on_quit))
	_wire_vertical_focus(menu_buttons)
	_focus_first_button(menu)


func _platform_summary() -> String:
	if _capabilities.is_web():
		return "Web build: browser-safe online only. LAN and local server tools are hidden."
	return "Desktop build: local, LAN, online, and dedicated server tools can be enabled."


func _apply_web_start_screen() -> void:
	if _capabilities == null or not _capabilities.is_web():
		return
	if not Engine.has_singleton("JavaScriptBridge"):
		return
	var qa_mode := _web_query_param("qa").to_lower()
	if qa_mode == "browser_runtime":
		_run_browser_runtime_qa.call_deferred(
			_web_query_param("directory_url"),
			_web_query_param("store_phase"),
			_web_query_param("gateway_endpoint"),
			_web_query_param("auth_gateway_endpoint"),
			_web_query_param("full_gateway_endpoint"),
			_web_query_param("closed_gateway_endpoint"),
			_web_query_param("banned_gateway_endpoint"),
			_web_query_param("session_gateway_endpoint"),
			_web_query_param("session_token_url"),
		)
		return
	var screen := _web_query_param("screen").to_lower()
	var visual_ready_screen := "main_menu"
	match screen:
		"options":
			_show_options()
			visual_ready_screen = "options"
		"setup", "local_setup", "local_match_setup":
			_show_local_match_setup()
			visual_ready_screen = "local_match_setup"
		"servers", "server_browser":
			_on_find_servers()
			visual_ready_screen = "server_browser"
		"local", "local_match":
			_start_local_match(LOCAL_MATCH_ROUND_OPTIONS[0])
			visual_ready_screen = "local_match"
	_publish_web_visual_ready.call_deferred(visual_ready_screen)


func _publish_web_visual_ready(screen_name: String) -> void:
	if _capabilities == null or not _capabilities.is_web():
		return
	if not Engine.has_singleton("JavaScriptBridge"):
		return
	await get_tree().process_frame
	await get_tree().process_frame
	var bridge = Engine.get_singleton("JavaScriptBridge")
	bridge.eval("window.__groundfireVisualReady = %s;" % JSON.stringify(screen_name), false)


func _web_query_param(name: String) -> String:
	if not Engine.has_singleton("JavaScriptBridge"):
		return ""
	var bridge = Engine.get_singleton("JavaScriptBridge")
	var expression := "new URLSearchParams(window.location.search).get(%s) || ''" % JSON.stringify(name)
	return str(bridge.eval(expression, true))


func _run_browser_runtime_qa(
	directory_url: String,
	store_phase := "",
	gateway_endpoint := "",
	auth_gateway_endpoint := "",
	full_gateway_endpoint := "",
	closed_gateway_endpoint := "",
	banned_gateway_endpoint := "",
	session_gateway_endpoint := "",
	session_token_url := "",
) -> void:
	var errors: Array[String] = []
	var details := {}
	var normalized_store_phase := _qa_normalized_store_phase(store_phase)
	_qa_expect(errors, _capabilities.is_web(), "running in a web build")
	_qa_expect(errors, not _capabilities.supports(_capabilities.FEATURE_LAN_DISCOVERY), "LAN discovery hidden on web")
	_qa_expect(errors, not _capabilities.supports(_capabilities.FEATURE_UDP_TRANSPORT), "UDP transport hidden on web")
	_qa_expect(errors, not _capabilities.supports(_capabilities.FEATURE_DEDICATED_SERVER_TOOLS), "dedicated tools hidden on web")
	_qa_expect(errors, not _capabilities.visible_server_browser_tabs().has("LAN"), "LAN tab hidden on web")
	_qa_check_browser_store(errors, details, normalized_store_phase)
	await _qa_check_http_directory(directory_url, errors, details)
	await _qa_check_online_error_flow(
		gateway_endpoint,
		auth_gateway_endpoint,
		full_gateway_endpoint,
		closed_gateway_endpoint,
		banned_gateway_endpoint,
		session_gateway_endpoint,
		session_token_url,
		errors,
		details,
	)
	if normalized_store_phase == "seed":
		await get_tree().create_timer(0.35).timeout
	_publish_browser_runtime_qa(errors, details)


func _qa_normalized_store_phase(value: String) -> String:
	var phase := value.to_lower().strip_edges()
	if phase == "seed" or phase == "verify":
		return phase
	return "single"


func _qa_check_browser_store(errors: Array[String], details: Dictionary, store_phase: String) -> void:
	var favorite_endpoint := "wss://qa.groundfire.local/runtime"
	var entry := {
		"name": "QA Runtime",
		"game": "Groundfire",
		"players": "2/8",
		"map": "QA Range",
		"latency": "12ms",
		"source": ServerDirectory.SOURCE_ONLINE,
		"endpoint": favorite_endpoint,
		"passworded": "false",
	}
	details["store_phase"] = store_phase
	if store_phase == "single" or store_phase == "seed":
		DirAccess.remove_absolute(BROWSER_QA_STORE_PATH)
		var favorites: Array[String] = BrowserStore.remember_favorite([], favorite_endpoint)
		var history: Array[Dictionary] = BrowserStore.remember_history([], entry)
		var filters := BrowserStore.filter_state("qa", true, true, "players")
		BrowserStore.save_store(favorites, history, filters, BROWSER_QA_STORE_PATH)
	var saved := BrowserStore.load_store(BROWSER_QA_STORE_PATH)
	var saved_favorites := Array(saved.get("favorites", []))
	var saved_history := Array(saved.get("history", []))
	var saved_filters := Dictionary(saved.get("filters", {}))
	_qa_expect(errors, saved_favorites.has(favorite_endpoint), "favorite persisted")
	_qa_expect(errors, saved_history.size() == 1, "history persisted")
	if not saved_history.is_empty() and typeof(saved_history[0]) == TYPE_DICTIONARY:
		_qa_expect(errors, str(Dictionary(saved_history[0]).get("endpoint", "")) == favorite_endpoint, "history endpoint round-tripped")
	_qa_expect(errors, str(saved_filters.get("text", "")) == "qa", "filter text persisted")
	_qa_expect(errors, bool(saved_filters.get("hide_passworded", false)), "password filter persisted")
	_qa_expect(errors, bool(saved_filters.get("hide_full", false)), "open-slot filter persisted")
	_qa_expect(errors, str(saved_filters.get("sort_mode", "")) == "players", "sort mode persisted")
	details["store_history_count"] = saved_history.size()
	if store_phase == "single" or store_phase == "verify":
		DirAccess.remove_absolute(BROWSER_QA_STORE_PATH)


func _qa_check_http_directory(directory_url: String, errors: Array[String], details: Dictionary) -> void:
	if directory_url.strip_edges().is_empty():
		errors.append("missing QA directory_url")
		return
	var response := await _qa_directory_request(directory_url)
	if _qa_should_retry_directory_response(response):
		await get_tree().create_timer(0.25).timeout
		response = await _qa_directory_request(directory_url)
	var start_error := int(response.get("start_error", OK))
	if start_error != OK:
		errors.append("directory HTTP request could not start: %d" % start_error)
		return
	var result := int(response.get("result", -1))
	var response_code := int(response.get("response_code", 0))
	var response_headers: PackedStringArray = response.get("headers", PackedStringArray())
	var body: PackedByteArray = response.get("body", PackedByteArray())
	details["directory_url"] = directory_url
	details["directory_http_result"] = result
	details["directory_http_status"] = response_code
	details["directory_body_size"] = body.size()
	details["directory_response_headers"] = Array(response_headers)
	if body.size() > 0:
		details["directory_body_prefix"] = body.get_string_from_utf8().left(160)
	_qa_expect(errors, result == HTTPRequest.RESULT_SUCCESS, "directory HTTP request succeeded")
	_qa_expect(errors, response_code >= 200 and response_code < 300, "directory HTTP status is 2xx")
	_qa_check_directory_cache_headers(response_headers, errors, details)
	await _qa_check_directory_not_modified(directory_url, ServerDirectory.http_etag(response_headers), errors, details)
	var entries := ServerDirectory.entries_from_http_body(body, false)
	var desktop_entries := ServerDirectory.entries_from_http_body(body, true)
	details["directory_entries_web"] = entries.size()
	details["directory_entries_desktop"] = desktop_entries.size()
	_qa_expect(errors, entries.size() == 2, "web directory loaded only online entries")
	_qa_expect(errors, desktop_entries.size() == 3, "desktop directory would include LAN entry")
	_qa_expect(errors, entries.all(func(entry: Dictionary) -> bool: return str(entry.get("source", "")) == ServerDirectory.SOURCE_ONLINE), "web directory filtered LAN entries")
	_qa_expect(errors, ServerDirectory.entries_from_http_body("not-json".to_utf8_buffer(), false).is_empty(), "invalid directory payload falls back to no entries")
	_qa_expect(errors, ServerDirectory.directory_diagnostic_from_body("not-json".to_utf8_buffer()) == "invalid JSON object", "invalid directory diagnostic is exposed")


func _qa_directory_request(directory_url: String, etag := "") -> Dictionary:
	var request := HTTPRequest.new()
	request.timeout = 5.0
	add_child(request)
	var start_error := ServerDirectory.refresh_from_http(request, directory_url, etag)
	if start_error != OK:
		request.queue_free()
		return {
			"start_error": start_error,
			"result": -1,
			"response_code": 0,
			"headers": PackedStringArray(),
			"body": PackedByteArray(),
		}
	var completed: Array = await request.request_completed
	request.queue_free()
	return {
		"start_error": OK,
		"result": int(completed[0]),
		"response_code": int(completed[1]),
		"headers": PackedStringArray(completed[2]),
		"body": PackedByteArray(completed[3]),
	}


func _qa_should_retry_directory_response(response: Dictionary) -> bool:
	if int(response.get("start_error", OK)) != OK:
		return true
	return ServerDirectory.should_retry_directory_request(
		int(response.get("result", -1)),
		int(response.get("response_code", 0)),
		0,
	)


func _qa_check_directory_cache_headers(headers: PackedStringArray, errors: Array[String], details: Dictionary) -> void:
	var cache_control := _qa_header_value(headers, "cache-control").to_lower()
	var etag := _qa_header_value(headers, "etag")
	var refresh_seconds := _qa_header_value(headers, "x-groundfire-directory-refresh")
	details["directory_cache_control"] = cache_control
	details["directory_etag"] = etag
	details["directory_refresh_seconds"] = refresh_seconds
	_qa_expect(errors, cache_control.contains("public"), "directory cache policy is public")
	_qa_expect(errors, cache_control.contains("max-age=30"), "directory cache max-age is 30 seconds")
	_qa_expect(errors, cache_control.contains("must-revalidate"), "directory cache policy revalidates")
	_qa_expect(errors, not etag.is_empty(), "directory ETag is present")
	_qa_expect(errors, refresh_seconds == "30", "directory refresh hint is 30 seconds")


func _qa_check_directory_not_modified(directory_url: String, etag: String, errors: Array[String], details: Dictionary) -> void:
	if etag.strip_edges().is_empty():
		errors.append("directory ETag is missing for conditional refresh")
		return
	var response := await _qa_directory_request(directory_url, etag)
	if _qa_should_retry_directory_response(response):
		await get_tree().create_timer(0.25).timeout
		response = await _qa_directory_request(directory_url, etag)
	var start_error := int(response.get("start_error", OK))
	if start_error != OK:
		errors.append("conditional directory HTTP request could not start: %d" % start_error)
		return
	var result := int(response.get("result", -1))
	var response_code := int(response.get("response_code", 0))
	details["directory_not_modified"] = response_code
	_qa_expect(errors, result == HTTPRequest.RESULT_SUCCESS, "conditional directory HTTP request succeeded")
	_qa_expect(errors, response_code == ServerDirectory.HTTP_NOT_MODIFIED, "directory conditional refresh returned 304")


func _qa_header_value(headers: PackedStringArray, header_name: String) -> String:
	var normalized_name := header_name.to_lower()
	for header in headers:
		var separator := header.find(":")
		if separator <= 0:
			continue
		var name := header.substr(0, separator).to_lower().strip_edges()
		if name == normalized_name:
			return header.substr(separator + 1).strip_edges()
	return ""


func _qa_check_online_error_flow(
	gateway_endpoint: String,
	auth_gateway_endpoint: String,
	full_gateway_endpoint: String,
	closed_gateway_endpoint: String,
	banned_gateway_endpoint: String,
	session_gateway_endpoint: String,
	session_token_url: String,
	errors: Array[String],
	details: Dictionary,
) -> void:
	var online_match := OnlineMatchScene.instantiate()
	online_match.setup({"endpoint": ""})
	add_child(online_match)
	await get_tree().process_frame
	_qa_expect(errors, str(online_match.get("_status")) == "Missing online endpoint.", "online match reports missing endpoints")
	var full_error := NetworkAdapter.error_message("server_full")
	online_match.call("_fail_server_error", NetworkAdapter.server_error_status_message(full_error), "server_full")
	_qa_expect(errors, bool(online_match.get("_fatal_server_failure")), "online match treats server_full as fatal")
	_qa_expect(errors, NetworkAdapter.is_fatal_server_error("invalid_password"), "invalid_password is fatal")
	_qa_expect(errors, NetworkAdapter.server_error_status_message(NetworkAdapter.error_message("invalid_password")).contains("password rejected"), "password rejection copy is available")
	details["online_error_status"] = str(online_match.get("_status"))
	online_match.queue_free()
	await _qa_check_gateway_join_failure(gateway_endpoint, "invalid_password", "password rejected", errors, details)
	await _qa_check_gateway_join_failure(auth_gateway_endpoint, "authentication_failed", "authentication was rejected", errors, details)
	await _qa_check_gateway_join_failure(full_gateway_endpoint, "server_full", "server is full", errors, details)
	await _qa_check_gateway_join_failure(closed_gateway_endpoint, "server_closed", "server is closed", errors, details)
	await _qa_check_gateway_join_failure(banned_gateway_endpoint, "banned", "access was rejected", errors, details)
	await _qa_check_gateway_session_token_join(session_gateway_endpoint, session_token_url, errors, details)


func _qa_check_gateway_join_failure(endpoint: String, expected_error: String, expected_status_copy: String, errors: Array[String], details: Dictionary) -> void:
	var detail_key := "gateway_%s_failure" % expected_error
	if endpoint.strip_edges().is_empty():
		details[detail_key] = "skipped"
		return
	var entry := {"endpoint": endpoint}
	if expected_error == "invalid_password":
		entry["password"] = "wrong"
	var gateway_match := OnlineMatchScene.instantiate()
	gateway_match.setup(entry)
	add_child(gateway_match)
	var deadline_msec := Time.get_ticks_msec() + 8000
	while Time.get_ticks_msec() < deadline_msec:
		await get_tree().process_frame
		var status := str(gateway_match.get("_status"))
		if bool(gateway_match.get("_fatal_server_failure")):
			details[detail_key] = status
			_qa_expect(errors, status.contains(expected_status_copy), "real gateway %s status is shown" % expected_error)
			_qa_expect(errors, float(gateway_match.get("_reconnect_timer")) <= 0.0, "real gateway fatal join error does not schedule reconnect")
			gateway_match.queue_free()
			return
	details[detail_key] = str(gateway_match.get("_status"))
	gateway_match.queue_free()
	errors.append("real gateway %s flow timed out" % expected_error)


func _qa_check_gateway_session_token_join(endpoint: String, session_token_url: String, errors: Array[String], details: Dictionary) -> void:
	var detail_key := "gateway_session_token_join"
	if endpoint.strip_edges().is_empty() or session_token_url.strip_edges().is_empty():
		details[detail_key] = "skipped"
		return
	var gateway_match := OnlineMatchScene.instantiate()
	gateway_match.setup({
		"endpoint": endpoint,
		"session_token_url": session_token_url,
	})
	add_child(gateway_match)
	var deadline_msec := Time.get_ticks_msec() + 10000
	while Time.get_ticks_msec() < deadline_msec:
		await get_tree().process_frame
		if bool(gateway_match.get("_fatal_server_failure")):
			details[detail_key] = str(gateway_match.get("_status"))
			gateway_match.queue_free()
			errors.append("real gateway signed session-token join failed")
			return
		var snapshot := Dictionary(gateway_match.get("_snapshot"))
		var status := str(snapshot.get("status", ""))
		if status == "joined" or status == "input":
			details["gateway_session_token_debug"] = gateway_match.call("_session_token_debug_state")
			var token_received := bool(gateway_match.call("_has_session_auth_token"))
			details[detail_key] = "joined"
			details["gateway_session_token_auth"] = "received" if token_received else "missing"
			_qa_expect(errors, token_received, "signed session-token join fetched auth_token")
			_qa_expect(errors, str(gateway_match.get("_session_token_url")) == session_token_url, "signed session-token URL was used")
			gateway_match.queue_free()
			return
	details[detail_key] = str(gateway_match.get("_status"))
	gateway_match.queue_free()
	errors.append("real gateway signed session-token join timed out")


func _qa_expect(errors: Array[String], condition: bool, message: String) -> void:
	if not condition:
		errors.append(message)


func _publish_browser_runtime_qa(errors: Array[String], details: Dictionary) -> void:
	var result := {
		"ok": errors.is_empty(),
		"errors": errors,
		"details": details,
	}
	var status_label := Label.new()
	status_label.text = "Browser runtime QA passed." if errors.is_empty() else "Browser runtime QA failed."
	GroundfireTheme.apply_label(status_label, 16, GroundfireTheme.COLOR_CYAN if errors.is_empty() else GroundfireTheme.COLOR_WARN)
	_stack.add_child(status_label)
	if Engine.has_singleton("JavaScriptBridge"):
		var bridge = Engine.get_singleton("JavaScriptBridge")
		bridge.eval("window.__groundfireQaResult = %s;" % JSON.stringify(result), false)


func _add_logo() -> void:
	var logo := TextureRect.new()
	logo.texture = LOGO_TEXTURE
	logo.expand_mode = TextureRect.EXPAND_FIT_WIDTH
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.custom_minimum_size = _classic_logo_size()
	logo.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_stack.add_child(logo)


func _add_spacer(height: float) -> Control:
	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(1.0, height)
	_stack.add_child(spacer)
	return spacer


func _add_spacer_to(parent: Container, height: float) -> Control:
	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(1.0, height)
	parent.add_child(spacer)
	return spacer


func _add_center_label(text: String, font_size := 18, color := GroundfireTheme.COLOR_TEXT) -> Label:
	var label := Label.new()
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	GroundfireTheme.apply_label(label, int(round(float(font_size) * _menu_scale())), color)
	_stack.add_child(label)
	return label


func _add_title(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	GroundfireTheme.apply_label(label, 34, GroundfireTheme.COLOR_TEXT)
	_stack.add_child(label)


func _add_subtitle(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(label, 18, GroundfireTheme.COLOR_CYAN)
	_stack.add_child(label)


func _add_button_to(parent: Container, text: String, callback: Callable, accent := false) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = _classic_button_size()
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(button, accent)
	button.pressed.connect(callback)
	parent.add_child(button)
	return button


func _add_classic_button_to(parent: Container, text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = _scaled_menu_size(MENU_CLASSIC_BUTTON_SIZE)
	button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_classic_button(button, int(round(float(MENU_CLASSIC_BUTTON_FONT_SIZE) * _menu_scale())))
	button.pressed.connect(callback)
	parent.add_child(button)
	return button


func _menu_scale() -> float:
	var viewport_size := get_viewport_rect().size
	if viewport_size.x <= 0.0 or viewport_size.y <= 0.0:
		viewport_size = MENU_REFERENCE_SIZE
	var scale: float = min(viewport_size.x / MENU_REFERENCE_SIZE.x, viewport_size.y / MENU_REFERENCE_SIZE.y)
	return clamp(scale, MENU_MIN_SCALE, MENU_MAX_SCALE)


func _scaled_menu_size(base_size: Vector2) -> Vector2:
	return Vector2(round(base_size.x * _menu_scale()), round(base_size.y * _menu_scale()))


func _scaled_classic_value(value: float) -> float:
	return round(value * _menu_scale())


func _classic_logo_size() -> Vector2:
	var texture_size: Vector2 = LOGO_TEXTURE.get_size()
	var texture_aspect: float = texture_size.x / max(texture_size.y, 1.0)
	var available_width: float = max(1.0, get_viewport_rect().size.x - MENU_MARGIN_BASE.x * 2.0)
	var max_width: float = min(MENU_LOGO_MAX_WIDTH, min(available_width, MENU_CONTENT_MAX_WIDTH))
	var width: float = clamp(MENU_LOGO_BASE_SIZE.x * _menu_scale(), MENU_LOGO_MIN_WIDTH, max_width)
	return Vector2(round(width), round(width / texture_aspect))


func _classic_button_size() -> Vector2:
	var scaled := _scaled_menu_size(MENU_BUTTON_BASE_SIZE)
	return Vector2(
		clamp(scaled.x, MENU_BUTTON_MIN_SIZE.x, MENU_BUTTON_MAX_SIZE.x),
		clamp(scaled.y, MENU_BUTTON_MIN_SIZE.y, MENU_BUTTON_MAX_SIZE.y)
	)


func _apply_menu_layout_metrics() -> void:
	if _content == null or _stack == null:
		return
	if _classic_fullscreen_layout:
		_content.add_theme_constant_override("margin_left", 0)
		_content.add_theme_constant_override("margin_top", 0)
		_content.add_theme_constant_override("margin_right", 0)
		_content.add_theme_constant_override("margin_bottom", 0)
		_stack.add_theme_constant_override("separation", 0)
		return
	var scale := _menu_scale()
	var margin_x := int(round(MENU_MARGIN_BASE.x * scale))
	var margin_y := int(round(MENU_MARGIN_BASE.y * scale))
	_content.add_theme_constant_override("margin_left", margin_x)
	_content.add_theme_constant_override("margin_top", margin_y)
	_content.add_theme_constant_override("margin_right", margin_x)
	_content.add_theme_constant_override("margin_bottom", margin_y)
	_stack.add_theme_constant_override("separation", int(round(MENU_STACK_SEPARATION_BASE * scale)))


func _set_classic_fullscreen_layout(enabled: bool) -> void:
	_classic_fullscreen_layout = enabled
	_apply_menu_layout_metrics()


func _add_disabled_note_to(parent: Container, text: String) -> void:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(label, 15, GroundfireTheme.COLOR_MUTED)
	parent.add_child(label)


func _clear_content() -> void:
	_dedicated_gateway_form_controls.clear()
	_dedicated_gateway_action_buttons.clear()
	_dedicated_stop_button = null
	_dedicated_status_label = null
	for child in _stack.get_children():
		_prepare_screen_for_shutdown(child)
		child.queue_free()
	_screen = null


func _prepare_screen_for_shutdown(screen: Node) -> void:
	if screen != null and is_instance_valid(screen) and screen.has_method("_prepare_for_shutdown"):
		screen.call("_prepare_for_shutdown")


func _prepare_for_shutdown() -> void:
	set_process(false)
	_prepare_screen_for_shutdown(_screen)
	_prepare_screen_for_shutdown(_paused_match_screen)


func _show_local_match_setup() -> void:
	_in_options = false
	_discard_paused_match_screen()
	_set_classic_fullscreen_layout(false)
	_stack.alignment = BoxContainer.ALIGNMENT_CENTER
	_local_match_setup_rows.clear()
	_clear_content()
	_add_logo()
	_add_subtitle("Local Match Setup")

	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(860, 570)
	panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style())
	_stack.add_child(panel)

	var inner := VBoxContainer.new()
	inner.add_theme_constant_override("separation", 12)
	panel.add_child(inner)

	var title := Label.new()
	title.text = "Match Setup"
	GroundfireTheme.apply_label(title, 24, GroundfireTheme.COLOR_TEXT)
	inner.add_child(title)

	var roster_panel := PanelContainer.new()
	roster_panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style(true))
	inner.add_child(roster_panel)

	var roster_grid := GridContainer.new()
	roster_grid.columns = 5
	roster_grid.add_theme_constant_override("h_separation", 10)
	roster_grid.add_theme_constant_override("v_separation", 6)
	roster_panel.add_child(roster_grid)
	for header in ["Active", "Color", "Name", "Controlled by", "Controller"]:
		_add_grid_header(roster_grid, header)
	for index in range(LOCAL_MATCH_MAX_PLAYERS):
		_add_local_match_setup_row(roster_grid, index)

	var rounds := OptionButton.new()
	rounds.custom_minimum_size = Vector2(220, 36)
	rounds.focus_mode = Control.FOCUS_ALL
	for option in LOCAL_MATCH_ROUND_OPTIONS:
		rounds.add_item(str(option))
		rounds.set_item_metadata(rounds.item_count - 1, option)
	_add_labeled_control(inner, "Rounds", rounds)

	_local_match_setup_status_label = Label.new()
	GroundfireTheme.apply_label(_local_match_setup_status_label, 14, GroundfireTheme.COLOR_CYAN)
	inner.add_child(_local_match_setup_status_label)

	var buttons := HBoxContainer.new()
	buttons.alignment = BoxContainer.ALIGNMENT_END
	buttons.add_theme_constant_override("separation", 10)
	inner.add_child(buttons)
	var start_callback := func() -> void:
		_start_local_match(int(rounds.get_item_metadata(rounds.selected)), _local_match_roster_snapshot())
	var start := _add_button_to(buttons, "Start Match", start_callback, true)
	_local_match_setup_start_button = start
	var back := _add_button_to(buttons, "Back", _show_main_menu)
	_local_match_setup_back_button = back
	_local_match_setup_rounds = rounds
	_sync_local_match_setup_state(start)
	var first_name := _local_match_setup_rows[0].get("name") as Control
	if first_name != null:
		first_name.grab_focus.call_deferred()


func _setup_name_line_edit(text: String) -> LineEdit:
	var line := _option_line_edit(text)
	line.custom_minimum_size = Vector2(220, 36)
	line.max_length = LOCAL_MATCH_NAME_MAX_LENGTH
	return line


func _add_local_match_setup_row(parent: GridContainer, index: int) -> void:
	var active := CheckButton.new()
	active.text = "P%d" % (index + 1)
	active.button_pressed = index < 2
	active.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(active)
	parent.add_child(active)

	var swatch := ColorRect.new()
	swatch.color = LOCAL_MATCH_PLAYER_COLORS[index]
	swatch.custom_minimum_size = Vector2(28.0, 24.0)
	parent.add_child(swatch)

	var name := _setup_name_line_edit(_local_match_default_name(index))
	name.custom_minimum_size = Vector2(170.0, 36.0)
	parent.add_child(name)

	var slot := OptionButton.new()
	slot.custom_minimum_size = Vector2(150.0, 36.0)
	slot.focus_mode = Control.FOCUS_ALL
	for label in LOCAL_MATCH_SLOT_TYPES:
		slot.add_item(label)
	slot.select(0 if index == 0 else 1)
	GroundfireTheme.apply_button(slot)
	parent.add_child(slot)

	var controller := OptionButton.new()
	controller.custom_minimum_size = Vector2(150.0, 36.0)
	controller.focus_mode = Control.FOCUS_ALL
	for label in LOCAL_MATCH_CONTROLLER_LABELS:
		controller.add_item(label)
	controller.select(index if index < 2 else 0)
	GroundfireTheme.apply_button(controller)
	parent.add_child(controller)

	var row := {
		"index": index,
		"active": active,
		"swatch": swatch,
		"name": name,
		"slot": slot,
		"controller": controller,
		"color": LOCAL_MATCH_PLAYER_COLORS[index],
	}
	_local_match_setup_rows.append(row)
	active.toggled.connect(func(_value: bool) -> void: _on_local_match_setup_row_changed(index))
	slot.item_selected.connect(func(_selected: int) -> void: _on_local_match_setup_row_changed(index))
	controller.item_selected.connect(func(selected: int) -> void: _on_local_match_controller_selected(index, selected))


func _local_match_default_name(index: int) -> String:
	if index == 0:
		return LOCAL_MATCH_DEFAULT_PLAYER_NAME
	if index == 1:
		return LOCAL_MATCH_DEFAULT_ENEMY_NAME
	return "Player %d" % (index + 1)


func _on_local_match_setup_row_changed(index: int) -> void:
	if index >= 0 and index < _local_match_setup_rows.size():
		var row: Dictionary = _local_match_setup_rows[index]
		if _local_match_row_is_human(row):
			var controller := row.get("controller") as OptionButton
			controller.select(_next_available_local_match_controller(index, controller.selected))
	_sync_local_match_setup_state()


func _on_local_match_controller_selected(index: int, selected: int) -> void:
	if index < 0 or index >= _local_match_setup_rows.size():
		return
	var row: Dictionary = _local_match_setup_rows[index]
	var controller := row.get("controller") as OptionButton
	if controller == null:
		return
	var resolved := _next_available_local_match_controller(index, selected)
	if controller.selected != resolved:
		controller.select(resolved)
	_sync_local_match_setup_state()


func _sync_local_match_setup_state(start_button: Button = null) -> void:
	var active_count := 0
	var human_count := 0
	var computer_count := 0
	for row_data in _local_match_setup_rows:
		var row: Dictionary = row_data
		var active := row.get("active") as CheckButton
		var name := row.get("name") as LineEdit
		var slot := row.get("slot") as OptionButton
		var controller := row.get("controller") as OptionButton
		var enabled := active != null and active.button_pressed
		if enabled:
			active_count += 1
			if _local_match_row_is_human(row):
				human_count += 1
			else:
				computer_count += 1
		if name != null:
			name.editable = enabled
			name.focus_mode = Control.FOCUS_ALL if enabled else Control.FOCUS_NONE
		if slot != null:
			slot.disabled = not enabled
		if controller != null:
			controller.disabled = not enabled or not _local_match_row_is_human(row)
	if start_button == null:
		start_button = _local_match_setup_start_button
	if start_button != null:
		start_button.disabled = active_count < 2 or human_count < 1
	if _local_match_setup_status_label != null:
		_local_match_setup_status_label.text = _local_match_setup_status_text(active_count, human_count, computer_count)
	_wire_local_match_setup_focus()


func _local_match_setup_status_text(active_count: int, human_count: int, computer_count: int) -> String:
	if active_count < 2:
		return "Enable at least 2 players to start."
	if human_count < 1:
		return "Add at least 1 human player to start."
	return "%d players ready  Human %d  Computer %d" % [active_count, human_count, computer_count]


func _local_match_row_is_human(row: Dictionary) -> bool:
	var slot := row.get("slot") as OptionButton
	return slot != null and slot.get_item_text(slot.selected) == "Human"


func _next_available_local_match_controller(row_index: int, start_index: int) -> int:
	var candidate := wrapi(start_index, 0, LOCAL_MATCH_CONTROLLER_LABELS.size())
	for _attempt in range(LOCAL_MATCH_CONTROLLER_LABELS.size()):
		var conflict := false
		for other_index in range(_local_match_setup_rows.size()):
			if other_index == row_index:
				continue
			var other: Dictionary = _local_match_setup_rows[other_index]
			var active := other.get("active") as CheckButton
			var controller := other.get("controller") as OptionButton
			if active != null and active.button_pressed and _local_match_row_is_human(other) and controller != null and controller.selected == candidate:
				conflict = true
				break
		if not conflict:
			return candidate
		candidate = wrapi(candidate + 1, 0, LOCAL_MATCH_CONTROLLER_LABELS.size())
	return wrapi(start_index, 0, LOCAL_MATCH_CONTROLLER_LABELS.size())


func _local_match_roster_snapshot() -> Array[Dictionary]:
	var roster: Array[Dictionary] = []
	for row_data in _local_match_setup_rows:
		var row: Dictionary = row_data
		var active := row.get("active") as CheckButton
		if active == null or not active.button_pressed:
			continue
		var index := int(row.get("index", roster.size()))
		var name := row.get("name") as LineEdit
		var slot := row.get("slot") as OptionButton
		var controller := row.get("controller") as OptionButton
		var is_human := slot != null and slot.get_item_text(slot.selected) == "Human"
		roster.append({
			"slot": index,
			"name": _setup_name_or_default(name.text if name != null else "", _local_match_default_name(index)),
			"kind": "human" if is_human else "computer",
			"controller": controller.selected if is_human and controller != null else -1,
			"color": row.get("color", Color.WHITE),
		})
	return roster


func _start_local_match(
		total_rounds: int,
		roster: Array[Dictionary] = []
) -> void:
	var normalized_roster := _normalized_local_match_roster(roster)
	var player_entry: Dictionary = normalized_roster[0]
	var enemy_entry: Dictionary = normalized_roster[1]
	_discard_paused_match_screen()
	_set_classic_fullscreen_layout(true)
	_stack.alignment = BoxContainer.ALIGNMENT_BEGIN
	_clear_content()
	_screen = LocalMatchScene.instantiate()
	_screen.name = "LocalMatch"
	_screen.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_screen.setup({
		"total_rounds": total_rounds,
		"player_name": str(player_entry.get("name", LOCAL_MATCH_DEFAULT_PLAYER_NAME)),
		"enemy_name": str(enemy_entry.get("name", LOCAL_MATCH_DEFAULT_ENEMY_NAME)),
		"player_slot": str(player_entry.get("kind", "human")),
		"enemy_slot": str(enemy_entry.get("kind", "computer")),
		"roster": normalized_roster,
	})
	_stack.add_child(_screen)


func _normalized_local_match_roster(roster: Array[Dictionary]) -> Array[Dictionary]:
	if roster.size() >= 2:
		return roster.duplicate(true)
	return [
		{
			"slot": 0,
			"name": LOCAL_MATCH_DEFAULT_PLAYER_NAME,
			"kind": "human",
			"controller": 0,
			"color": LOCAL_MATCH_PLAYER_COLORS[0],
		},
		{
			"slot": 1,
			"name": LOCAL_MATCH_DEFAULT_ENEMY_NAME,
			"kind": "computer",
			"controller": -1,
			"color": LOCAL_MATCH_PLAYER_COLORS[1],
		},
	]


func _setup_name_or_default(text: String, fallback: String) -> String:
	var cleaned := text.strip_edges()
	if cleaned.is_empty():
		return fallback
	return cleaned.left(LOCAL_MATCH_NAME_MAX_LENGTH)


func _on_find_servers() -> void:
	_discard_paused_match_screen()
	_set_classic_fullscreen_layout(true)
	_stack.alignment = BoxContainer.ALIGNMENT_BEGIN
	_clear_content()
	_screen = ServerBrowserScene.instantiate()
	_screen.name = "ServerBrowser"
	_screen.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_stack.add_child(_screen)


func _show_online_match(entry: Dictionary) -> void:
	_discard_paused_match_screen()
	_set_classic_fullscreen_layout(true)
	_stack.alignment = BoxContainer.ALIGNMENT_BEGIN
	_clear_content()
	_screen = OnlineMatchScene.instantiate()
	_screen.name = "OnlineMatch"
	_screen.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_screen.setup(entry)
	_stack.add_child(_screen)


func _on_dedicated_server() -> void:
	_discard_paused_match_screen()
	_set_classic_fullscreen_layout(false)
	_stack.alignment = BoxContainer.ALIGNMENT_CENTER
	_show_dedicated_server_tools()


func _on_options() -> void:
	_show_options()


func _on_quit() -> void:
	get_tree().quit()


func _show_placeholder(text: String) -> void:
	_in_options = false
	_set_classic_fullscreen_layout(false)
	_stack.alignment = BoxContainer.ALIGNMENT_CENTER
	_clear_content()
	_add_logo()
	_add_title("Groundfire")
	_add_subtitle(text)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style())
	_stack.add_child(panel)
	var inner := VBoxContainer.new()
	inner.add_theme_constant_override("separation", 10)
	panel.add_child(inner)
	var back := _add_button_to(inner, "Back", _show_main_menu, true)
	back.grab_focus.call_deferred()


func _show_dedicated_server_tools() -> void:
	_in_options = false
	_clear_content()
	_add_logo()
	_add_subtitle("Dedicated Server")
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(760, 620)
	panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style())
	_stack.add_child(panel)
	var inner := VBoxContainer.new()
	inner.add_theme_constant_override("separation", 12)
	panel.add_child(inner)

	var title := Label.new()
	title.text = "Browser Gateway"
	GroundfireTheme.apply_label(title, 24, GroundfireTheme.COLOR_TEXT)
	inner.add_child(title)

	var host_line := _dedicated_line_edit(_dedicated_gateway_host)
	_add_labeled_control(inner, "Host", host_line)

	var port_spin := SpinBox.new()
	port_spin.min_value = 1
	port_spin.max_value = 65535
	port_spin.step = 1
	port_spin.value = _dedicated_gateway_port
	port_spin.custom_minimum_size = Vector2(320, 36)
	port_spin.focus_mode = Control.FOCUS_ALL
	_add_labeled_control(inner, "Port", port_spin)

	var password_line := _dedicated_line_edit("")
	password_line.placeholder_text = "Optional join password"
	password_line.secret = true
	_add_labeled_control(inner, "Join Password", password_line)

	var auth_token_line := _dedicated_line_edit("")
	auth_token_line.placeholder_text = "Optional auth token"
	auth_token_line.secret = true
	_add_labeled_control(inner, "Auth Token", auth_token_line)

	var max_players_spin := SpinBox.new()
	max_players_spin.min_value = 0
	max_players_spin.max_value = 32
	max_players_spin.step = 1
	max_players_spin.value = _dedicated_gateway_max_players
	max_players_spin.custom_minimum_size = Vector2(320, 36)
	max_players_spin.focus_mode = Control.FOCUS_ALL
	_add_labeled_control(inner, "Max Players", max_players_spin)

	var closed_check := CheckButton.new()
	closed_check.text = "Reject new joins"
	closed_check.button_pressed = _dedicated_gateway_closed
	closed_check.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(closed_check)
	_add_labeled_control(inner, "Closed Joins", closed_check)

	var banned_line := _dedicated_line_edit(_dedicated_gateway_banned_players)
	banned_line.placeholder_text = "Comma-separated player names"
	_add_labeled_control(inner, "Banned Players", banned_line)

	var endpoint_label := Label.new()
	endpoint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(endpoint_label, 14, GroundfireTheme.COLOR_MUTED)
	inner.add_child(endpoint_label)

	var policy_label := Label.new()
	policy_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(policy_label, 14, GroundfireTheme.COLOR_CYAN)
	inner.add_child(policy_label)

	var command_label := Label.new()
	command_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(command_label, 13, GroundfireTheme.COLOR_MUTED)
	inner.add_child(command_label)

	var refresh_gateway_summary: Callable = func() -> void:
		var config := _dedicated_gateway_config_from_controls(
			host_line,
			port_spin,
			password_line,
			auth_token_line,
			max_players_spin,
			closed_check,
			banned_line
		)
		endpoint_label.text = "Connect endpoint: %s" % _gateway_endpoint(config)
		policy_label.text = "Join policy: %s" % _gateway_policy_summary(config)
		command_label.text = "Command preview: %s" % _gateway_command_preview(config)
	refresh_gateway_summary.call()
	host_line.text_changed.connect(func(_text: String) -> void:
		_dedicated_gateway_host = _gateway_host({"host": host_line.text})
		_save_options()
		refresh_gateway_summary.call()
	)
	port_spin.value_changed.connect(func(_value: float) -> void:
		_dedicated_gateway_port = _gateway_port({"port": int(port_spin.value)})
		_save_options()
		refresh_gateway_summary.call()
	)
	password_line.text_changed.connect(func(_text: String) -> void:
		refresh_gateway_summary.call()
	)
	auth_token_line.text_changed.connect(func(_text: String) -> void:
		refresh_gateway_summary.call()
	)
	max_players_spin.value_changed.connect(func(_value: float) -> void:
		_dedicated_gateway_max_players = max(0, int(max_players_spin.value))
		_save_options()
		refresh_gateway_summary.call()
	)
	closed_check.toggled.connect(func(value: bool) -> void:
		_dedicated_gateway_closed = value
		_save_options()
		refresh_gateway_summary.call()
	)
	banned_line.text_changed.connect(func(_text: String) -> void:
		_dedicated_gateway_banned_players = banned_line.text.strip_edges()
		_save_options()
		refresh_gateway_summary.call()
	)

	_dedicated_status_label = Label.new()
	_dedicated_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_dedicated_status_label.text = "Ready to start groundfire-web-gateway from the local .venv."
	GroundfireTheme.apply_label(_dedicated_status_label, 14, GroundfireTheme.COLOR_CYAN)
	inner.add_child(_dedicated_status_label)

	var buttons := HBoxContainer.new()
	buttons.alignment = BoxContainer.ALIGNMENT_END
	buttons.add_theme_constant_override("separation", 10)
	inner.add_child(buttons)
	var start_callback := func() -> void:
		_start_web_gateway(_dedicated_gateway_config_from_controls(
			host_line,
			port_spin,
			password_line,
			auth_token_line,
			max_players_spin,
			closed_check,
			banned_line
		))
	var start := _add_button_to(buttons, "Start Gateway", start_callback, true)
	start.custom_minimum_size = Vector2(132, 40)
	_dedicated_stop_button = _add_button_to(buttons, "Stop Gateway", _stop_web_gateway)
	_dedicated_stop_button.custom_minimum_size = Vector2(132, 40)
	_dedicated_stop_button.disabled = _dedicated_gateway_pid <= 0
	var copy_endpoint := _add_button_to(buttons, "Copy Endpoint", func() -> void:
		_copy_gateway_endpoint(_dedicated_gateway_config_from_controls(
			host_line,
			port_spin,
			password_line,
			auth_token_line,
			max_players_spin,
			closed_check,
			banned_line
		))
	)
	copy_endpoint.custom_minimum_size = Vector2(132, 40)
	var copy_command := _add_button_to(buttons, "Copy Command", func() -> void:
		_copy_gateway_command(_dedicated_gateway_config_from_controls(
			host_line,
			port_spin,
			password_line,
			auth_token_line,
			max_players_spin,
			closed_check,
			banned_line
		))
	)
	copy_command.custom_minimum_size = Vector2(132, 40)
	var back := _add_button_to(buttons, "Back", _show_main_menu)
	back.custom_minimum_size = Vector2(132, 40)
	_dedicated_gateway_form_controls = [host_line, port_spin, password_line, auth_token_line, max_players_spin, closed_check, banned_line]
	_dedicated_gateway_action_buttons = [start, _dedicated_stop_button, copy_endpoint, copy_command, back]
	_wire_dedicated_gateway_focus()
	start.grab_focus.call_deferred()


func _add_labeled_control(parent: Container, label_text: String, control: Control) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	parent.add_child(row)
	var label := Label.new()
	label.text = label_text
	label.custom_minimum_size = Vector2(150, 32)
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_MUTED)
	row.add_child(label)
	row.add_child(control)


func _dedicated_line_edit(text: String) -> LineEdit:
	return _option_line_edit(text)


func _dedicated_gateway_config_from_controls(
		host_line: LineEdit,
		port_spin: SpinBox,
		password_line: LineEdit,
		auth_token_line: LineEdit,
		max_players_spin: SpinBox,
		closed_check: CheckButton,
		banned_line: LineEdit
) -> Dictionary:
	return {
		"host": host_line.text,
		"port": int(port_spin.value),
		"password": password_line.text,
		"auth_token": auth_token_line.text,
		"max_players": int(max_players_spin.value),
		"closed": closed_check.button_pressed,
		"ban_players": banned_line.text,
	}


func _option_line_edit(text: String, placeholder := "") -> LineEdit:
	var line := LineEdit.new()
	line.text = text
	line.placeholder_text = placeholder
	line.custom_minimum_size = Vector2(320, 36)
	line.focus_mode = Control.FOCUS_ALL
	line.add_theme_stylebox_override("normal", GroundfireTheme.field_style())
	return line


func _start_web_gateway(config: Dictionary) -> void:
	if _capabilities.is_web():
		_dedicated_status_label.text = "Dedicated server tools are hidden on web builds."
		return
	if _dedicated_gateway_pid > 0:
		_dedicated_status_label.text = "Gateway already running with pid %d. Stop it before launching another." % _dedicated_gateway_pid
		return
	var executable := _gateway_executable()
	if executable.is_empty():
		_dedicated_status_label.text = "groundfire-web-gateway was not found in .venv. Install the Python package in editable mode first."
		return
	var args := _gateway_args(config)
	var pid := OS.create_process(executable, args, false)
	if pid <= 0:
		_dedicated_status_label.text = "Gateway process failed to start."
		return
	_dedicated_gateway_pid = pid
	if _dedicated_stop_button != null:
		_dedicated_stop_button.disabled = false
		_wire_dedicated_gateway_focus()
	_dedicated_status_label.text = "Gateway started on %s:%d (pid %d). Connect endpoint: %s." % [
		_gateway_host(config),
		_gateway_port(config),
		pid,
		_gateway_endpoint(config),
	]


func _stop_web_gateway() -> void:
	if _dedicated_gateway_pid <= 0:
		if _dedicated_status_label != null:
			_dedicated_status_label.text = "No gateway process is tracked."
		return
	var stopped_pid := _dedicated_gateway_pid
	var result: int = OS.kill(stopped_pid)
	if result != OK:
		if _dedicated_status_label != null:
			_dedicated_status_label.text = "Gateway stop failed for pid %d." % stopped_pid
		return
	_dedicated_gateway_pid = 0
	if _dedicated_stop_button != null:
		_dedicated_stop_button.disabled = true
		_wire_dedicated_gateway_focus()
	if _dedicated_status_label != null:
		_dedicated_status_label.text = "Gateway stopped (pid %d)." % stopped_pid


func _copy_gateway_endpoint(config: Dictionary) -> void:
	var endpoint := _gateway_endpoint(config)
	DisplayServer.clipboard_set(endpoint)
	if _dedicated_status_label != null:
		_dedicated_status_label.text = "Gateway endpoint copied: %s" % endpoint


func _copy_gateway_command(config: Dictionary) -> void:
	var command := _gateway_command_preview(config)
	DisplayServer.clipboard_set(command)
	if _dedicated_status_label != null:
		_dedicated_status_label.text = "Gateway command copied with secrets masked."


func _gateway_command_preview(config: Dictionary) -> String:
	var parts := PackedStringArray(["groundfire-web-gateway"])
	for argument in _gateway_display_args(config):
		parts.append(_shell_quote_arg(argument))
	return " ".join(parts)


func _gateway_policy_summary(config: Dictionary) -> String:
	var parts := PackedStringArray()
	parts.append("password %s" % ("on" if not str(config.get("password", "")).strip_edges().is_empty() else "off"))
	parts.append("auth %s" % ("on" if not str(config.get("auth_token", "")).strip_edges().is_empty() else "off"))
	var max_players: int = max(0, int(config.get("max_players", 0)))
	parts.append("max %s" % (str(max_players) if max_players > 0 else "unlimited"))
	parts.append("joins %s" % ("closed" if bool(config.get("closed", false)) else "open"))
	var banned := _gateway_banned_players(config.get("ban_players", ""))
	parts.append("bans %d" % banned.size())
	return ", ".join(parts)


func _gateway_display_args(config: Dictionary) -> PackedStringArray:
	var args := _gateway_args(config)
	var display_args := PackedStringArray()
	var masked_value := ""
	for argument in args:
		if not masked_value.is_empty():
			display_args.append(masked_value)
			masked_value = ""
			continue
		display_args.append(argument)
		if argument == "--password":
			masked_value = "<password>"
		elif argument == "--auth-token":
			masked_value = "<auth-token>"
	return display_args


func _shell_quote_arg(argument: String) -> String:
	if argument.is_empty():
		return "\"\""
	for special in [" ", "\t", "\"", "$", "&", "|", ";", "(", ")", "<", ">", "*", "?"]:
		if argument.contains(special):
			return "\"%s\"" % argument.replace("\\", "\\\\").replace("\"", "\\\"").replace("$", "\\$")
	return argument


func _gateway_endpoint(config: Dictionary) -> String:
	return "ws://%s:%d" % [_gateway_endpoint_host(config), _gateway_port(config)]


func _gateway_endpoint_host(config: Dictionary) -> String:
	var host := _gateway_host(config)
	if host == "0.0.0.0" or host == "::":
		return "127.0.0.1"
	if host.contains(":") and not host.begins_with("["):
		return "[%s]" % host
	return host


func _gateway_args(config: Dictionary) -> PackedStringArray:
	var args := PackedStringArray(["--host", _gateway_host(config), "--port", str(_gateway_port(config))])
	var password := str(config.get("password", "")).strip_edges()
	if not password.is_empty():
		args.append("--password")
		args.append(password)
	var auth_token := str(config.get("auth_token", "")).strip_edges()
	if not auth_token.is_empty():
		args.append("--auth-token")
		args.append(auth_token)
	var max_players: int = max(0, int(config.get("max_players", 0)))
	if max_players > 0:
		args.append("--max-players")
		args.append(str(max_players))
	if bool(config.get("closed", false)):
		args.append("--closed")
	for player_name in _gateway_banned_players(config.get("ban_players", "")):
		args.append("--ban-player")
		args.append(player_name)
	return args


func _gateway_host(config: Dictionary) -> String:
	var host := str(config.get("host", "127.0.0.1")).strip_edges()
	return "127.0.0.1" if host.is_empty() else host


func _gateway_port(config: Dictionary) -> int:
	return clampi(int(config.get("port", 8765)), 1, 65535)


func _gateway_banned_players(value: Variant) -> PackedStringArray:
	var players := PackedStringArray()
	if value is Array:
		for item in value:
			var player_name := str(item).strip_edges()
			if player_name.is_empty():
				continue
			players.append(player_name)
	else:
		for item in str(value).split(",", false):
			var player_name := str(item).strip_edges()
			if player_name.is_empty():
				continue
			players.append(player_name)
	return players


func _gateway_executable() -> String:
	for candidate in GATEWAY_EXECUTABLE_CANDIDATES:
		var path := ProjectSettings.globalize_path(candidate)
		if FileAccess.file_exists(path):
			return path
	return ""


func _show_options_for_paused_match(match_screen: Control) -> void:
	if match_screen == null or match_screen.get_parent() != _stack:
		_show_options()
		return
	_paused_match_screen = match_screen
	_stack.remove_child(match_screen)
	match_screen.visible = false
	_show_options(Callable(self, "_return_to_paused_match"))


func _return_to_paused_match() -> void:
	_in_options = false
	_set_classic_fullscreen_layout(true)
	_stack.alignment = BoxContainer.ALIGNMENT_BEGIN
	_clear_content()
	if _paused_match_screen != null and is_instance_valid(_paused_match_screen):
		_screen = _paused_match_screen
		_paused_match_screen = null
		_screen.visible = true
		_screen.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
		_stack.add_child(_screen)
		if _screen.has_method("_set_paused"):
			_screen.call("_set_paused", true)
		return
	_paused_match_screen = null
	_show_main_menu()


func _discard_paused_match_screen() -> void:
	if _paused_match_screen != null and is_instance_valid(_paused_match_screen):
		_prepare_screen_for_shutdown(_paused_match_screen)
		_paused_match_screen.queue_free()
	_paused_match_screen = null


func _show_options(back_callback: Callable = Callable()) -> void:
	_in_options = true
	_set_classic_fullscreen_layout(true)
	_stack.alignment = BoxContainer.ALIGNMENT_BEGIN
	_clear_content()
	_add_spacer(_scaled_classic_value(26.0))
	_add_title("Options")
	_add_spacer(_scaled_classic_value(150.0))
	var panel := PanelContainer.new()
	panel.custom_minimum_size = _scaled_menu_size(OPTIONS_CLASSIC_PANEL_SIZE)
	panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	panel.add_theme_stylebox_override("panel", GroundfireTheme.classic_panel_style())
	_stack.add_child(panel)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(520, 420)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)

	var inner := VBoxContainer.new()
	inner.add_theme_constant_override("separation", 12)
	scroll.add_child(inner)

	var controls_section: VBoxContainer = null
	_add_classic_options_preset_rows(inner, scroll, func() -> void:
		if controls_section != null:
			scroll.ensure_control_visible(controls_section)
			_focus_first_button(controls_section)
	)

	var video_section := _add_options_section(inner, "Video")
	var fps := CheckButton.new()
	fps.text = "Show FPS"
	fps.button_pressed = _show_fps
	GroundfireTheme.apply_button(fps)
	fps.toggled.connect(func(value: bool) -> void:
		_show_fps = value
		_save_options()
	)
	video_section.add_child(fps)

	var fullscreen := CheckButton.new()
	fullscreen.text = "Fullscreen"
	fullscreen.button_pressed = _fullscreen
	GroundfireTheme.apply_button(fullscreen)
	fullscreen.toggled.connect(func(value: bool) -> void:
		_fullscreen = value
		_apply_options()
		_save_options()
	)
	video_section.add_child(fullscreen)

	var vsync := CheckButton.new()
	vsync.text = "VSync"
	vsync.button_pressed = _vsync_enabled
	GroundfireTheme.apply_button(vsync)
	vsync.toggled.connect(func(value: bool) -> void:
		_vsync_enabled = value
		_apply_options()
		_save_options()
	)
	video_section.add_child(vsync)

	_add_resolution_selector(video_section)

	var audio_section := _add_options_section(inner, "Audio")
	var audio := CheckButton.new()
	audio.text = "Audio Enabled"
	audio.button_pressed = _audio_enabled
	GroundfireTheme.apply_button(audio)
	audio.toggled.connect(func(value: bool) -> void:
		_audio_enabled = value
		_apply_options()
		_save_options()
	)
	audio_section.add_child(audio)

	_add_slider_option(audio_section, "Master Volume", _master_volume, 0.0, 1.0, 0.05, func(value: float) -> void:
		_master_volume = value
		_apply_options()
		_save_options()
	)

	var gameplay_section := _add_options_section(inner, "Gameplay")

	var screen_shake := CheckButton.new()
	screen_shake.text = "Screen Shake"
	screen_shake.button_pressed = _screen_shake_enabled
	GroundfireTheme.apply_button(screen_shake)
	screen_shake.toggled.connect(func(value: bool) -> void:
		_screen_shake_enabled = value
		_save_options()
	)
	gameplay_section.add_child(screen_shake)

	var mouse_aim := CheckButton.new()
	mouse_aim.text = "Mouse Aim"
	mouse_aim.button_pressed = _mouse_aim_enabled
	GroundfireTheme.apply_button(mouse_aim)
	mouse_aim.toggled.connect(func(value: bool) -> void:
		_mouse_aim_enabled = value
		_save_options()
	)
	gameplay_section.add_child(mouse_aim)

	_add_slider_option(gameplay_section, "Camera Smoothing", _camera_smoothing, 0.25, 1.75, 0.05, func(value: float) -> void:
		_camera_smoothing = value
		_save_options()
	)
	_add_ai_difficulty_selector(gameplay_section)

	var online_section := _add_options_section(inner, "Online")
	_add_server_directory_options(online_section, false)

	controls_section = _add_options_section(inner, "Controls")
	_add_gamepad_profile_selector(controls_section)

	_capture_prompt = Label.new()
	_capture_prompt.text = "Select a control to rebind."
	GroundfireTheme.apply_label(_capture_prompt, 14, GroundfireTheme.COLOR_CYAN)
	controls_section.add_child(_capture_prompt)

	var controls_grid := GridContainer.new()
	controls_grid.columns = 3
	controls_grid.add_theme_constant_override("h_separation", 10)
	controls_grid.add_theme_constant_override("v_separation", 8)
	controls_section.add_child(controls_grid)
	_add_grid_header(controls_grid, "Action")
	_add_grid_header(controls_grid, "Keyboard")
	_add_grid_header(controls_grid, "Gamepad")
	for action_name in ControlSettings.action_names():
		var action_label := Label.new()
		action_label.text = ControlSettings.display_name(action_name)
		GroundfireTheme.apply_label(action_label, 14, GroundfireTheme.COLOR_MUTED)
		controls_grid.add_child(action_label)

		var key_button := _control_binding_button(ControlSettings.key_label(action_name))
		key_button.pressed.connect(_begin_key_capture.bind(action_name))
		controls_grid.add_child(key_button)

		var gamepad_button := _control_binding_button(ControlSettings.gamepad_label(action_name))
		gamepad_button.pressed.connect(_begin_gamepad_capture.bind(action_name))
		controls_grid.add_child(gamepad_button)
	var conflicts := ControlSettings.conflict_labels()
	if not conflicts.is_empty():
		var conflict_title := Label.new()
		conflict_title.text = "Conflicts"
		GroundfireTheme.apply_label(conflict_title, 16, GroundfireTheme.COLOR_WARN)
		controls_section.add_child(conflict_title)
		for conflict in conflicts:
			var conflict_label := Label.new()
			conflict_label.text = conflict
			GroundfireTheme.apply_label(conflict_label, 14, GroundfireTheme.COLOR_WARN)
			controls_section.add_child(conflict_label)
		var fix_conflicts := _add_button_to(controls_section, "Reset Conflicting Bindings", func() -> void:
			ControlSettings.reset_defaults()
			_show_options(back_callback)
		)
		fix_conflicts.custom_minimum_size = Vector2(360, 38)
	var reset_controls := _add_button_to(controls_section, "Reset Controls", func() -> void:
		ControlSettings.reset_defaults()
		_show_options(back_callback)
	)
	reset_controls.custom_minimum_size = Vector2(360, 38)
	var reset_gamepad := _add_button_to(controls_section, "Reset Gamepad Defaults", func() -> void:
		ControlSettings.reset_gamepad_defaults()
		_show_options(back_callback)
	)
	reset_gamepad.custom_minimum_size = Vector2(360, 38)
	var apply := _add_classic_options_button_to(inner, "Apply", func() -> void:
		_apply_options()
		_save_options()
	)
	apply.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	var back_action := back_callback if back_callback.is_valid() else Callable(self, "_show_main_menu")
	var back := _add_classic_options_button_to(inner, "Back", back_action)
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_wire_options_focus(inner)
	_focus_first_button(inner)


func _add_classic_options_preset_rows(parent: Container, scroll: ScrollContainer, set_controls_callback: Callable) -> void:
	var rows := VBoxContainer.new()
	rows.name = "ClassicOptionsPresetRows"
	rows.add_theme_constant_override("separation", 10)
	rows.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	parent.add_child(rows)
	_add_spacer_to(rows, _scaled_classic_value(OPTIONS_CLASSIC_TOP_SPACER))
	_add_classic_resolution_row(rows)
	_add_classic_screen_mode_row(rows)
	_add_classic_options_button_to(rows, "Set Controls", func() -> void:
		set_controls_callback.call()
	)


func _add_classic_resolution_row(parent: Container) -> OptionButton:
	var selector := OptionButton.new()
	selector.focus_mode = Control.FOCUS_ALL
	selector.disabled = _capabilities != null and _capabilities.is_web()
	GroundfireTheme.apply_classic_button(selector, int(round(float(OPTIONS_CLASSIC_ROW_FONT_SIZE) * _menu_scale())))
	for index in range(RESOLUTION_PRESETS.size()):
		var preset: Dictionary = RESOLUTION_PRESETS[index]
		selector.add_item(str(preset.get("label", "")))
	selector.select(_resolution_index)
	selector.item_selected.connect(func(index: int) -> void:
		_resolution_index = index
		_apply_options()
		_save_options()
	)
	_add_classic_option_row(parent, "Resolution:", selector)
	return selector


func _add_classic_screen_mode_row(parent: Container) -> OptionButton:
	var selector := OptionButton.new()
	selector.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_classic_button(selector, int(round(float(OPTIONS_CLASSIC_ROW_FONT_SIZE) * _menu_scale())))
	selector.add_item("Fullscreen")
	selector.add_item("Windowed")
	selector.select(0 if _fullscreen else 1)
	selector.item_selected.connect(func(index: int) -> void:
		_fullscreen = index == 0
		_apply_options()
		_save_options()
	)
	_add_classic_option_row(parent, "Screen Mode:", selector)
	return selector


func _add_classic_option_row(parent: Container, label_text: String, control: Control) -> void:
	var row_panel := PanelContainer.new()
	row_panel.custom_minimum_size = _scaled_menu_size(OPTIONS_CLASSIC_ROW_SIZE)
	row_panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	row_panel.add_theme_stylebox_override("panel", _classic_option_row_style())
	parent.add_child(row_panel)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	row_panel.add_child(row)

	var label := Label.new()
	label.text = label_text
	label.custom_minimum_size = Vector2(
		_scaled_classic_value(OPTIONS_CLASSIC_LABEL_WIDTH),
		_scaled_classic_value(OPTIONS_CLASSIC_ROW_SIZE.y)
	)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	GroundfireTheme.apply_label(label, int(round(float(OPTIONS_CLASSIC_ROW_FONT_SIZE) * _menu_scale())), GroundfireTheme.COLOR_CYAN)
	row.add_child(label)

	control.custom_minimum_size = Vector2(
		_scaled_classic_value(OPTIONS_CLASSIC_CONTROL_WIDTH),
		_scaled_classic_value(OPTIONS_CLASSIC_ROW_SIZE.y)
	)
	control.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(control)


func _add_classic_options_button_to(parent: Container, text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = _scaled_menu_size(OPTIONS_CLASSIC_ROW_SIZE)
	button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_classic_button(button, int(round(float(OPTIONS_CLASSIC_ROW_FONT_SIZE) * _menu_scale())))
	button.pressed.connect(callback)
	parent.add_child(button)
	return button


func _classic_option_row_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color("#994c0080")
	style.border_color = Color.TRANSPARENT
	style.set_border_width_all(0)
	style.corner_radius_top_left = 0
	style.corner_radius_top_right = 0
	style.corner_radius_bottom_left = 0
	style.corner_radius_bottom_right = 0
	style.content_margin_left = 0
	style.content_margin_right = 0
	style.content_margin_top = 0
	style.content_margin_bottom = 0
	return style


func _add_options_section(parent: Container, title_text: String) -> VBoxContainer:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style(true))
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(panel)

	var section := VBoxContainer.new()
	section.add_theme_constant_override("separation", 8)
	panel.add_child(section)

	var title := Label.new()
	title.text = title_text
	GroundfireTheme.apply_label(title, 18, GroundfireTheme.COLOR_TEXT)
	section.add_child(title)
	return section


func _load_options() -> void:
	var config := ConfigFile.new()
	var loaded := config.load(OPTIONS_PATH) == OK
	if loaded:
		_show_fps = bool(config.get_value("video", "show_fps", _show_fps))
		_fullscreen = bool(config.get_value("video", "fullscreen", _fullscreen))
		_resolution_index = int(clamp(
			int(config.get_value("video", "resolution_index", _resolution_index)),
			0,
			RESOLUTION_PRESETS.size() - 1
		))
		_vsync_enabled = bool(config.get_value("video", "vsync", _vsync_enabled))
		_audio_enabled = bool(config.get_value("audio", "enabled", _audio_enabled))
		_master_volume = clamp(float(config.get_value("audio", "master_volume", _master_volume)), 0.0, 1.0)
		_screen_shake_enabled = bool(config.get_value("gameplay", "screen_shake", _screen_shake_enabled))
		_camera_smoothing = clamp(float(config.get_value("gameplay", "camera_smoothing", _camera_smoothing)), 0.25, 1.75)
		_mouse_aim_enabled = bool(config.get_value("gameplay", "mouse_aim", _mouse_aim_enabled))
		_ai_difficulty = _normalized_ai_difficulty(str(config.get_value("gameplay", "ai_difficulty", _ai_difficulty)))
		_load_dedicated_gateway_options(config)
	_load_server_directory_options(config, loaded)
	_apply_server_directory_options()


func _save_options() -> void:
	var config := ConfigFile.new()
	config.set_value("video", "show_fps", _show_fps)
	config.set_value("video", "fullscreen", _fullscreen)
	config.set_value("video", "resolution_index", _resolution_index)
	config.set_value("video", "vsync", _vsync_enabled)
	config.set_value("audio", "enabled", _audio_enabled)
	config.set_value("audio", "master_volume", _master_volume)
	config.set_value("gameplay", "screen_shake", _screen_shake_enabled)
	config.set_value("gameplay", "camera_smoothing", _camera_smoothing)
	config.set_value("gameplay", "mouse_aim", _mouse_aim_enabled)
	config.set_value("gameplay", "ai_difficulty", _ai_difficulty)
	config.set_value("server_directory", "environment", _server_directory_environment)
	config.set_value("server_directory", "override_url", _server_directory_override_url)
	config.set_value("server_directory", "url_dev", _server_directory_dev_url)
	config.set_value("server_directory", "url_staging", _server_directory_staging_url)
	config.set_value("server_directory", "url_production", _server_directory_production_url)
	config.set_value("dedicated_gateway", "host", _dedicated_gateway_host)
	config.set_value("dedicated_gateway", "port", _dedicated_gateway_port)
	config.set_value("dedicated_gateway", "max_players", _dedicated_gateway_max_players)
	config.set_value("dedicated_gateway", "closed", _dedicated_gateway_closed)
	config.set_value("dedicated_gateway", "banned_players", _dedicated_gateway_banned_players)
	config.save(OPTIONS_PATH)


func _apply_options() -> void:
	AudioServer.set_bus_mute(0, not _audio_enabled)
	AudioServer.set_bus_volume_db(0, linear_to_db(max(_master_volume, 0.001)))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if _vsync_enabled else DisplayServer.VSYNC_DISABLED)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if _fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)
	if not _fullscreen and _capabilities != null and not _capabilities.is_web():
		DisplayServer.window_set_size(_selected_resolution())


func _load_dedicated_gateway_options(config: ConfigFile) -> void:
	_dedicated_gateway_host = _gateway_host({
		"host": str(config.get_value("dedicated_gateway", "host", _dedicated_gateway_host)),
	})
	_dedicated_gateway_port = _gateway_port({
		"port": int(config.get_value("dedicated_gateway", "port", _dedicated_gateway_port)),
	})
	_dedicated_gateway_max_players = clampi(
		int(config.get_value("dedicated_gateway", "max_players", _dedicated_gateway_max_players)),
		0,
		32
	)
	_dedicated_gateway_closed = bool(config.get_value("dedicated_gateway", "closed", _dedicated_gateway_closed))
	_dedicated_gateway_banned_players = str(config.get_value(
		"dedicated_gateway",
		"banned_players",
		_dedicated_gateway_banned_players
	)).strip_edges()


func _load_server_directory_options(config: ConfigFile, loaded: bool) -> void:
	_server_directory_environment = ServerDirectory.configured_directory_environment()
	_server_directory_override_url = str(ProjectSettings.get_setting(ServerDirectory.SERVER_DIRECTORY_SETTING, "")).strip_edges()
	_server_directory_dev_url = str(ProjectSettings.get_setting(ServerDirectory.SERVER_DIRECTORY_DEV_URL_SETTING, "")).strip_edges()
	_server_directory_staging_url = str(ProjectSettings.get_setting(ServerDirectory.SERVER_DIRECTORY_STAGING_URL_SETTING, "")).strip_edges()
	_server_directory_production_url = str(ProjectSettings.get_setting(ServerDirectory.SERVER_DIRECTORY_PRODUCTION_URL_SETTING, "")).strip_edges()
	if not loaded:
		return
	_server_directory_environment = ServerDirectory.normalized_directory_environment(str(config.get_value(
		"server_directory",
		"environment",
		_server_directory_environment
	)))
	_server_directory_override_url = str(config.get_value("server_directory", "override_url", _server_directory_override_url)).strip_edges()
	_server_directory_dev_url = str(config.get_value("server_directory", "url_dev", _server_directory_dev_url)).strip_edges()
	_server_directory_staging_url = str(config.get_value("server_directory", "url_staging", _server_directory_staging_url)).strip_edges()
	_server_directory_production_url = str(config.get_value("server_directory", "url_production", _server_directory_production_url)).strip_edges()


func _apply_server_directory_options() -> void:
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_SETTING, _server_directory_override_url)
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_ENVIRONMENT_SETTING, _server_directory_environment)
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_DEV_URL_SETTING, _server_directory_dev_url)
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_STAGING_URL_SETTING, _server_directory_staging_url)
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_PRODUCTION_URL_SETTING, _server_directory_production_url)


func _commit_server_directory_options(status_label: Label) -> void:
	_apply_server_directory_options()
	_save_options()
	if status_label != null:
		status_label.text = _server_directory_preview_label()


func _server_directory_error_label() -> String:
	for item in [
		["Override URL", _server_directory_override_url],
		["Dev URL", _server_directory_dev_url],
		["Staging URL", _server_directory_staging_url],
		["Production URL", _server_directory_production_url],
	]:
		var error := ServerDirectory.directory_url_error(str(item[0]), str(item[1]))
		if not error.is_empty():
			return error
	return ""


func _add_slider_option(parent: Container, label_text: String, value: float, minimum: float, maximum: float, step: float, callback: Callable) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	parent.add_child(row)
	var label := Label.new()
	label.text = label_text
	label.custom_minimum_size = Vector2(150, 28)
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_MUTED)
	row.add_child(label)
	var slider := HSlider.new()
	slider.min_value = minimum
	slider.max_value = maximum
	slider.step = step
	slider.value = value
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.focus_mode = Control.FOCUS_ALL
	row.add_child(slider)
	var value_label := Label.new()
	value_label.custom_minimum_size = Vector2(52, 28)
	value_label.text = "%d%%" % int(round(value * 100.0))
	GroundfireTheme.apply_label(value_label, 14, GroundfireTheme.COLOR_CYAN)
	row.add_child(value_label)
	slider.value_changed.connect(func(next_value: float) -> void:
		value_label.text = "%d%%" % int(round(next_value * 100.0))
		callback.call(next_value)
	)


func _add_resolution_selector(parent: Container) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	parent.add_child(row)
	var label := Label.new()
	label.text = "Resolution"
	label.custom_minimum_size = Vector2(150, 32)
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_MUTED)
	row.add_child(label)
	var selector := OptionButton.new()
	selector.custom_minimum_size = Vector2(320, 36)
	selector.focus_mode = Control.FOCUS_ALL
	selector.disabled = _capabilities != null and _capabilities.is_web()
	GroundfireTheme.apply_button(selector)
	row.add_child(selector)
	for index in range(RESOLUTION_PRESETS.size()):
		var preset: Dictionary = RESOLUTION_PRESETS[index]
		selector.add_item(str(preset.get("label", "")))
	selector.select(_resolution_index)
	selector.item_selected.connect(func(index: int) -> void:
		_resolution_index = index
		_apply_options()
		_save_options()
	)


func _selected_resolution() -> Vector2i:
	var index := int(clamp(_resolution_index, 0, RESOLUTION_PRESETS.size() - 1))
	var preset: Dictionary = RESOLUTION_PRESETS[index]
	return preset.get("size", Vector2i(1024, 768))


func _add_ai_difficulty_selector(parent: Container) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	parent.add_child(row)
	var label := Label.new()
	label.text = "AI Difficulty"
	label.custom_minimum_size = Vector2(150, 32)
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_MUTED)
	row.add_child(label)
	var selector := OptionButton.new()
	selector.custom_minimum_size = Vector2(320, 36)
	selector.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(selector)
	row.add_child(selector)
	for index in range(AI_DIFFICULTIES.size()):
		var difficulty := str(AI_DIFFICULTIES[index])
		selector.add_item(difficulty.capitalize())
		selector.set_item_metadata(index, difficulty)
		if difficulty == _ai_difficulty:
			selector.select(index)
	selector.item_selected.connect(func(index: int) -> void:
		_ai_difficulty = _normalized_ai_difficulty(str(selector.get_item_metadata(index)))
		_save_options()
	)


func _normalized_ai_difficulty(value: String) -> String:
	var normalized := value.to_lower()
	if AI_DIFFICULTIES.has(normalized):
		return normalized
	return "normal"


func _add_server_directory_options(parent: Container, include_title := true) -> void:
	if include_title:
		var title := Label.new()
		title.text = "Online"
		GroundfireTheme.apply_label(title, 18, GroundfireTheme.COLOR_TEXT)
		parent.add_child(title)

	var status := Label.new()
	status.text = _server_directory_preview_label()
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(status, 14, GroundfireTheme.COLOR_CYAN)
	parent.add_child(status)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	parent.add_child(row)
	var label := Label.new()
	label.text = "Directory Environment"
	label.custom_minimum_size = Vector2(150, 32)
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_MUTED)
	row.add_child(label)
	var selector := OptionButton.new()
	selector.custom_minimum_size = Vector2(320, 36)
	selector.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(selector)
	row.add_child(selector)
	for index in range(ServerDirectory.DIRECTORY_ENVIRONMENTS.size()):
		var environment := str(ServerDirectory.DIRECTORY_ENVIRONMENTS[index])
		selector.add_item(environment.capitalize())
		selector.set_item_metadata(index, environment)
		if environment == _server_directory_environment:
			selector.select(index)
	selector.item_selected.connect(func(index: int) -> void:
		_server_directory_environment = ServerDirectory.normalized_directory_environment(str(selector.get_item_metadata(index)))
		_commit_server_directory_options(status)
	)

	_add_directory_url_option(parent, "Override URL", _server_directory_override_url, "https://directory.example/groundfire.json", func(value: String) -> void:
		_server_directory_override_url = value
		_commit_server_directory_options(status)
	)
	_add_directory_url_option(parent, "Dev URL", _server_directory_dev_url, "https://dev.example/groundfire.json", func(value: String) -> void:
		_server_directory_dev_url = value
		_commit_server_directory_options(status)
	)
	_add_directory_url_option(parent, "Staging URL", _server_directory_staging_url, "https://staging.example/groundfire.json", func(value: String) -> void:
		_server_directory_staging_url = value
		_commit_server_directory_options(status)
	)
	_add_directory_url_option(parent, "Production URL", _server_directory_production_url, "https://play.example/groundfire.json", func(value: String) -> void:
		_server_directory_production_url = value
		_commit_server_directory_options(status)
	)


func _add_directory_url_option(parent: Container, label_text: String, value: String, placeholder: String, callback: Callable) -> void:
	var line := _option_line_edit(value, placeholder)
	_add_labeled_control(parent, label_text, line)
	line.text_submitted.connect(func(next_text: String) -> void:
		callback.call(next_text.strip_edges())
		line.text = next_text.strip_edges()
	)
	line.focus_exited.connect(func() -> void:
		line.text = line.text.strip_edges()
		callback.call(line.text)
	)


func _server_directory_preview_label() -> String:
	var error := _server_directory_error_label()
	if not error.is_empty():
		return "Directory Source: %s; using local fallback" % error
	if not _server_directory_override_url.is_empty():
		return "Directory Source: override"
	var environment_url := _server_directory_url_for_environment(_server_directory_environment)
	if environment_url.is_empty():
		return "Directory Source: %s local fallback" % _server_directory_environment
	return "Directory Source: %s" % _server_directory_environment


func _server_directory_url_for_environment(environment: String) -> String:
	if environment == ServerDirectory.ENVIRONMENT_STAGING:
		return _server_directory_staging_url
	if environment == ServerDirectory.ENVIRONMENT_PRODUCTION:
		return _server_directory_production_url
	return _server_directory_dev_url


func _add_gamepad_profile_selector(parent: Container) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	parent.add_child(row)
	var label := Label.new()
	label.text = "Gamepad Profile"
	label.custom_minimum_size = Vector2(150, 32)
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_MUTED)
	row.add_child(label)
	var selector := OptionButton.new()
	selector.custom_minimum_size = Vector2(320, 36)
	selector.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(selector)
	row.add_child(selector)
	var active_device := ControlSettings.active_gamepad_device()
	var profiles := ControlSettings.gamepad_profiles()
	for index in range(profiles.size()):
		var profile: Dictionary = profiles[index]
		var device_id := int(profile.get("device_id", ControlSettings.GAMEPAD_ALL_DEVICES))
		selector.add_item(str(profile.get("label", "Gamepad")))
		selector.set_item_metadata(index, device_id)
		if device_id == active_device:
			selector.select(index)
	selector.item_selected.connect(func(index: int) -> void:
		ControlSettings.set_active_gamepad_device(int(selector.get_item_metadata(index)))
		_show_options()
	)


func _begin_key_capture(action_name: String) -> void:
	_capture_action = action_name
	_capture_kind = "keyboard"
	if _capture_prompt != null:
		_capture_prompt.text = "Press a keyboard key for %s, or cancel." % ControlSettings.display_name(action_name)


func _begin_gamepad_capture(action_name: String) -> void:
	_capture_action = action_name
	_capture_kind = "gamepad"
	if _capture_prompt != null:
		_capture_prompt.text = "Press a gamepad button or move an axis for %s. Back cancels." % ControlSettings.display_name(action_name)


func _cancel_input_capture() -> void:
	_capture_action = ""
	_capture_kind = ""


func _is_capture_cancel(event: InputEvent) -> bool:
	if event is InputEventKey and event.is_action_pressed("ui_cancel"):
		return true
	return event is InputEventJoypadButton \
			and event.pressed \
			and event.button_index == GAMEPAD_CAPTURE_CANCEL_BUTTON


func _add_grid_header(parent: Container, text: String) -> void:
	var label := Label.new()
	label.text = text
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_TEXT)
	parent.add_child(label)


func _control_binding_button(text: String) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(150, 34)
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(button)
	return button


func _focus_first_button(root: Node) -> bool:
	for child in root.get_children():
		if child is Button:
			child.grab_focus.call_deferred()
			return true
		if _focus_first_button(child):
			return true
	return false


func _wire_vertical_focus(buttons: Array[Button]) -> void:
	if buttons.is_empty():
		return
	if buttons.size() == 1:
		var path := buttons[0].get_path()
		buttons[0].focus_neighbor_top = path
		buttons[0].focus_neighbor_bottom = path
		buttons[0].focus_neighbor_left = path
		buttons[0].focus_neighbor_right = path
		return
	for index in range(buttons.size()):
		var button := buttons[index]
		var previous := buttons[wrapi(index - 1, 0, buttons.size())]
		var next := buttons[wrapi(index + 1, 0, buttons.size())]
		var path := button.get_path()
		button.focus_neighbor_top = previous.get_path()
		button.focus_neighbor_bottom = next.get_path()
		button.focus_neighbor_left = path
		button.focus_neighbor_right = path


func _wire_vertical_control_focus(controls: Array[Control]) -> void:
	if controls.size() < 2:
		return
	for index in range(controls.size()):
		var control := controls[index]
		var previous := controls[wrapi(index - 1, 0, controls.size())]
		var next := controls[wrapi(index + 1, 0, controls.size())]
		control.focus_neighbor_top = previous.get_path()
		control.focus_neighbor_bottom = next.get_path()


func _wire_horizontal_focus(buttons: Array[Button]) -> void:
	if buttons.size() < 2:
		return
	for index in range(buttons.size()):
		var button := buttons[index]
		var previous := buttons[wrapi(index - 1, 0, buttons.size())]
		var next := buttons[wrapi(index + 1, 0, buttons.size())]
		button.focus_neighbor_left = previous.get_path()
		button.focus_neighbor_right = next.get_path()


func _wire_options_focus(root_node: Node) -> void:
	var controls := _focusable_controls_in_tree(root_node)
	_wire_vertical_control_focus(controls)
	for control in controls:
		var path := control.get_path()
		if control is BaseButton:
			control.focus_neighbor_left = path
			control.focus_neighbor_right = path


func _wire_dedicated_gateway_focus() -> void:
	var form_controls: Array[Control] = []
	for control in _dedicated_gateway_form_controls:
		_clear_focus_neighbors(control)
		if control != null and _is_focusable_control(control):
			form_controls.append(control)
	var action_buttons: Array[Button] = []
	for button in _dedicated_gateway_action_buttons:
		_clear_focus_neighbors(button)
		if button != null and _is_focusable_control(button):
			action_buttons.append(button)
	if form_controls.is_empty() or action_buttons.is_empty():
		return
	_wire_vertical_control_focus(form_controls)
	_wire_horizontal_focus(action_buttons)
	var first_form := form_controls[0]
	var last_form := form_controls[form_controls.size() - 1]
	var last_action := action_buttons[action_buttons.size() - 1]
	first_form.focus_neighbor_top = last_action.get_path()
	last_form.focus_neighbor_bottom = action_buttons[0].get_path()
	for button in action_buttons:
		button.focus_neighbor_top = last_form.get_path()
		button.focus_neighbor_bottom = first_form.get_path()


func _focusable_controls_in_tree(root_node: Node) -> Array[Control]:
	var controls: Array[Control] = []
	_collect_focusable_controls(root_node, controls)
	return controls


func _collect_focusable_controls(node: Node, controls: Array[Control]) -> void:
	for child in node.get_children():
		if child is Control:
			var control := child as Control
			if _is_focusable_control(control):
				controls.append(control)
		_collect_focusable_controls(child, controls)


func _is_focusable_control(control: Control) -> bool:
	if control.focus_mode == Control.FOCUS_NONE:
		return false
	if not control.visible:
		return false
	if control is BaseButton and (control as BaseButton).disabled:
		return false
	return true


func _wire_local_match_setup_focus() -> void:
	var rounds := _local_match_setup_rounds as Control
	var start := _local_match_setup_start_button
	var back := _local_match_setup_back_button
	if rounds == null or start == null or back == null:
		return
	var active_controls: Array[Control] = []
	var name_controls: Array[Control] = []
	var slot_controls: Array[Control] = []
	var controller_controls: Array[Control] = []
	for row_data in _local_match_setup_rows:
		var row: Dictionary = row_data
		var row_controls: Array[Control] = []
		for key in ["active", "name", "slot", "controller"]:
			_clear_focus_neighbors(row.get(key) as Control)
		var active := row.get("active") as Control
		var name := row.get("name") as Control
		var slot := row.get("slot") as Control
		var controller := row.get("controller") as Control
		if active != null:
			active_controls.append(active)
			row_controls.append(active)
		if name != null and _is_focusable_control(name):
			name_controls.append(name)
			row_controls.append(name)
		if slot != null and _is_focusable_control(slot):
			slot_controls.append(slot)
			row_controls.append(slot)
		if controller != null and _is_focusable_control(controller):
			controller_controls.append(controller)
			row_controls.append(controller)
		_wire_horizontal_control_focus(row_controls)
	for controls in [active_controls, name_controls, slot_controls, controller_controls]:
		_wire_local_match_setup_vertical_column(controls)
	_clear_focus_neighbors(rounds)
	_clear_focus_neighbors(start)
	_clear_focus_neighbors(back)
	var first_control := active_controls[0] if not active_controls.is_empty() else rounds
	var top_control := active_controls[active_controls.size() - 1] if not active_controls.is_empty() else back
	var action_buttons: Array[Button] = []
	if not start.disabled:
		action_buttons.append(start)
	action_buttons.append(back)
	_wire_horizontal_focus(action_buttons)
	rounds.focus_neighbor_bottom = action_buttons[0].get_path()
	for button in action_buttons:
		button.focus_neighbor_top = rounds.get_path()
		button.focus_neighbor_bottom = first_control.get_path()
	rounds.focus_neighbor_top = top_control.get_path()


func _wire_local_match_setup_vertical_column(controls: Array[Control]) -> void:
	if controls.is_empty():
		return
	if controls.size() == 1:
		controls[0].focus_neighbor_top = controls[0].get_path()
		controls[0].focus_neighbor_bottom = controls[0].get_path()
		return
	_wire_vertical_control_focus(controls)


func _wire_horizontal_control_focus(controls: Array[Control]) -> void:
	if controls.is_empty():
		return
	if controls.size() == 1:
		controls[0].focus_neighbor_left = controls[0].get_path()
		controls[0].focus_neighbor_right = controls[0].get_path()
		return
	for index in range(controls.size()):
		var control := controls[index]
		var previous := controls[wrapi(index - 1, 0, controls.size())]
		var next := controls[wrapi(index + 1, 0, controls.size())]
		control.focus_neighbor_left = previous.get_path()
		control.focus_neighbor_right = next.get_path()


func _clear_focus_neighbors(control: Control) -> void:
	if control == null:
		return
	control.focus_neighbor_top = NodePath()
	control.focus_neighbor_bottom = NodePath()
	control.focus_neighbor_left = NodePath()
	control.focus_neighbor_right = NodePath()
