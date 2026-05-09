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
const RESOLUTION_PRESETS := [
	{"label": "640 x 480", "size": Vector2i(640, 480)},
	{"label": "800 x 600", "size": Vector2i(800, 600)},
	{"label": "1024 x 768", "size": Vector2i(1024, 768)},
	{"label": "1280 x 960", "size": Vector2i(1280, 960)},
	{"label": "1280 x 1024", "size": Vector2i(1280, 1024)},
	{"label": "1600 x 1200", "size": Vector2i(1600, 1200)},
]
const AI_DIFFICULTIES := ["easy", "normal", "hard"]
const GATEWAY_EXECUTABLE_CANDIDATES := [
	"res://../.venv/bin/groundfire-web-gateway",
	"res://../.venv/Scripts/groundfire-web-gateway.exe",
]

var _content: MarginContainer
var _stack: VBoxContainer
var _screen: Control
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
var _mouse_aim_enabled := true
var _ai_difficulty := "normal"
var _server_directory_environment := "dev"
var _server_directory_override_url := ""
var _server_directory_dev_url := ""
var _server_directory_staging_url := ""
var _server_directory_production_url := ""
var _capture_action := ""
var _capture_kind := ""
var _capture_prompt: Label
var _in_options := false


func _ready() -> void:
	_capabilities = get_node("/root/PlatformCapabilities")
	ControlSettings.apply_saved_bindings()
	_load_options()
	_apply_options()
	_build_layout()
	set_process(true)
	_show_main_menu()
	_apply_web_start_screen.call_deferred()


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
	_content.add_theme_constant_override("margin_left", 34)
	_content.add_theme_constant_override("margin_top", 26)
	_content.add_theme_constant_override("margin_right", 34)
	_content.add_theme_constant_override("margin_bottom", 26)
	add_child(_content)

	_stack = VBoxContainer.new()
	_stack.name = "Stack"
	_stack.add_theme_constant_override("separation", 14)
	_stack.alignment = BoxContainer.ALIGNMENT_CENTER
	_content.add_child(_stack)


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), GroundfireTheme.COLOR_BG)
	var tile_size := MENU_TILE.get_size()
	for x in range(0, int(size.x) + int(tile_size.x), int(tile_size.x)):
		for y in range(0, int(size.y) + int(tile_size.y), int(tile_size.y)):
			draw_texture(MENU_TILE, Vector2(x, y), Color(0.12, 0.24, 0.34, 0.45))
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
	_clear_content()
	_add_logo()
	_add_subtitle(_platform_summary())

	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style())
	panel.custom_minimum_size = Vector2(420, 330)
	panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_stack.add_child(panel)

	var menu := VBoxContainer.new()
	menu.add_theme_constant_override("separation", 10)
	panel.add_child(menu)
	var menu_buttons: Array[Button] = []
	menu_buttons.append(_add_button_to(menu, "Start Local Match", _on_start_local_match, true))
	menu_buttons.append(_add_button_to(menu, "Find Servers", _on_find_servers))
	if _capabilities.supports(_capabilities.FEATURE_DEDICATED_SERVER_TOOLS):
		menu_buttons.append(_add_button_to(menu, "Dedicated Server", _on_dedicated_server))
	else:
		_add_disabled_note_to(menu, "Dedicated server tools are desktop-only.")
	menu_buttons.append(_add_button_to(menu, "Options", _on_options))
	menu_buttons.append(_add_button_to(menu, "Quit", _on_quit))
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
		)
		return
	var screen := _web_query_param("screen").to_lower()
	match screen:
		"options":
			_show_options()
		"servers", "server_browser":
			_on_find_servers()
		"local", "local_match":
			_on_start_local_match()


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
	var request := HTTPRequest.new()
	request.timeout = 5.0
	add_child(request)
	var start_error := ServerDirectory.refresh_from_http(request, directory_url)
	if start_error != OK:
		request.queue_free()
		errors.append("directory HTTP request could not start: %d" % start_error)
		return
	var completed: Array = await request.request_completed
	request.queue_free()
	var result := int(completed[0])
	var response_code := int(completed[1])
	var response_headers: PackedStringArray = completed[2]
	var body := PackedByteArray(completed[3])
	_qa_expect(errors, result == HTTPRequest.RESULT_SUCCESS, "directory HTTP request succeeded")
	_qa_expect(errors, response_code >= 200 and response_code < 300, "directory HTTP status is 2xx")
	_qa_check_directory_cache_headers(response_headers, errors, details)
	var entries := ServerDirectory.entries_from_http_body(body, false)
	var desktop_entries := ServerDirectory.entries_from_http_body(body, true)
	details["directory_entries_web"] = entries.size()
	details["directory_entries_desktop"] = desktop_entries.size()
	_qa_expect(errors, entries.size() == 2, "web directory loaded only online entries")
	_qa_expect(errors, desktop_entries.size() == 3, "desktop directory would include LAN entry")
	_qa_expect(errors, entries.all(func(entry: Dictionary) -> bool: return str(entry.get("source", "")) == ServerDirectory.SOURCE_ONLINE), "web directory filtered LAN entries")
	_qa_expect(errors, ServerDirectory.entries_from_http_body("not-json".to_utf8_buffer(), false).is_empty(), "invalid directory payload falls back to no entries")
	_qa_expect(errors, ServerDirectory.directory_diagnostic_from_body("not-json".to_utf8_buffer()) == "invalid JSON object", "invalid directory diagnostic is exposed")


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
	logo.custom_minimum_size = Vector2(760, 170)
	logo.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_stack.add_child(logo)


func _add_title(text: String) -> void:
	var label := Label.new()
	label.text = text
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
	button.custom_minimum_size = Vector2(360, 48)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(button, accent)
	button.pressed.connect(callback)
	parent.add_child(button)
	return button


func _add_disabled_note_to(parent: Container, text: String) -> void:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(label, 15, GroundfireTheme.COLOR_MUTED)
	parent.add_child(label)


func _clear_content() -> void:
	for child in _stack.get_children():
		child.queue_free()


func _on_start_local_match() -> void:
	_clear_content()
	_screen = LocalMatchScene.instantiate()
	_screen.name = "LocalMatch"
	_screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_stack.add_child(_screen)


func _on_find_servers() -> void:
	_clear_content()
	_screen = ServerBrowserScene.instantiate()
	_screen.name = "ServerBrowser"
	_screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_stack.add_child(_screen)


func _show_online_match(entry: Dictionary) -> void:
	_clear_content()
	_screen = OnlineMatchScene.instantiate()
	_screen.name = "OnlineMatch"
	_screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_screen.setup(entry)
	_stack.add_child(_screen)


func _on_dedicated_server() -> void:
	_show_dedicated_server_tools()


func _on_options() -> void:
	_show_options()


func _on_quit() -> void:
	get_tree().quit()


func _show_placeholder(text: String) -> void:
	_in_options = false
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
	panel.custom_minimum_size = Vector2(560, 360)
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

	var host_line := _dedicated_line_edit("127.0.0.1")
	_add_labeled_control(inner, "Host", host_line)

	var port_spin := SpinBox.new()
	port_spin.min_value = 1
	port_spin.max_value = 65535
	port_spin.step = 1
	port_spin.value = 8765
	port_spin.custom_minimum_size = Vector2(320, 36)
	port_spin.focus_mode = Control.FOCUS_ALL
	_add_labeled_control(inner, "Port", port_spin)

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
		_start_web_gateway(host_line.text.strip_edges(), int(port_spin.value))
	var start := _add_button_to(buttons, "Start Gateway", start_callback, true)
	var back := _add_button_to(buttons, "Back", _show_main_menu)
	_wire_vertical_focus([start, back])
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


func _option_line_edit(text: String, placeholder := "") -> LineEdit:
	var line := LineEdit.new()
	line.text = text
	line.placeholder_text = placeholder
	line.custom_minimum_size = Vector2(320, 36)
	line.focus_mode = Control.FOCUS_ALL
	line.add_theme_stylebox_override("normal", GroundfireTheme.field_style())
	return line


func _start_web_gateway(host: String, port: int) -> void:
	if _capabilities.is_web():
		_dedicated_status_label.text = "Dedicated server tools are hidden on web builds."
		return
	var executable := _gateway_executable()
	if executable.is_empty():
		_dedicated_status_label.text = "groundfire-web-gateway was not found in .venv. Install the Python package in editable mode first."
		return
	var args := PackedStringArray(["--host", host, "--port", str(port)])
	var pid := OS.create_process(executable, args, false)
	if pid <= 0:
		_dedicated_status_label.text = "Gateway process failed to start."
		return
	_dedicated_status_label.text = "Gateway started on %s:%d (pid %d)." % [host, port, pid]


func _gateway_executable() -> String:
	for candidate in GATEWAY_EXECUTABLE_CANDIDATES:
		var path := ProjectSettings.globalize_path(candidate)
		if FileAccess.file_exists(path):
			return path
	return ""


func _show_options() -> void:
	_in_options = true
	_clear_content()
	_add_logo()
	_add_subtitle("Options")
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(560, 520)
	panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style())
	_stack.add_child(panel)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(520, 420)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)

	var inner := VBoxContainer.new()
	inner.add_theme_constant_override("separation", 12)
	scroll.add_child(inner)

	var fps := CheckButton.new()
	fps.text = "Show FPS"
	fps.button_pressed = _show_fps
	GroundfireTheme.apply_button(fps)
	fps.toggled.connect(func(value: bool) -> void:
		_show_fps = value
		_save_options()
	)
	inner.add_child(fps)

	var audio := CheckButton.new()
	audio.text = "Audio Enabled"
	audio.button_pressed = _audio_enabled
	GroundfireTheme.apply_button(audio)
	audio.toggled.connect(func(value: bool) -> void:
		_audio_enabled = value
		_apply_options()
		_save_options()
	)
	inner.add_child(audio)

	var fullscreen := CheckButton.new()
	fullscreen.text = "Fullscreen"
	fullscreen.button_pressed = _fullscreen
	GroundfireTheme.apply_button(fullscreen)
	fullscreen.toggled.connect(func(value: bool) -> void:
		_fullscreen = value
		_apply_options()
		_save_options()
	)
	inner.add_child(fullscreen)

	var vsync := CheckButton.new()
	vsync.text = "VSync"
	vsync.button_pressed = _vsync_enabled
	GroundfireTheme.apply_button(vsync)
	vsync.toggled.connect(func(value: bool) -> void:
		_vsync_enabled = value
		_apply_options()
		_save_options()
	)
	inner.add_child(vsync)

	_add_resolution_selector(inner)

	_add_slider_option(inner, "Master Volume", _master_volume, 0.0, 1.0, 0.05, func(value: float) -> void:
		_master_volume = value
		_apply_options()
		_save_options()
	)

	var gameplay_title := Label.new()
	gameplay_title.text = "Gameplay"
	GroundfireTheme.apply_label(gameplay_title, 18, GroundfireTheme.COLOR_TEXT)
	inner.add_child(gameplay_title)

	var screen_shake := CheckButton.new()
	screen_shake.text = "Screen Shake"
	screen_shake.button_pressed = _screen_shake_enabled
	GroundfireTheme.apply_button(screen_shake)
	screen_shake.toggled.connect(func(value: bool) -> void:
		_screen_shake_enabled = value
		_save_options()
	)
	inner.add_child(screen_shake)

	var mouse_aim := CheckButton.new()
	mouse_aim.text = "Mouse Aim"
	mouse_aim.button_pressed = _mouse_aim_enabled
	GroundfireTheme.apply_button(mouse_aim)
	mouse_aim.toggled.connect(func(value: bool) -> void:
		_mouse_aim_enabled = value
		_save_options()
	)
	inner.add_child(mouse_aim)

	_add_slider_option(inner, "Camera Smoothing", _camera_smoothing, 0.25, 1.75, 0.05, func(value: float) -> void:
		_camera_smoothing = value
		_save_options()
	)
	_add_ai_difficulty_selector(inner)
	_add_server_directory_options(inner)

	var controls_title := Label.new()
	controls_title.text = "Controls"
	GroundfireTheme.apply_label(controls_title, 18, GroundfireTheme.COLOR_TEXT)
	inner.add_child(controls_title)

	_add_gamepad_profile_selector(inner)

	_capture_prompt = Label.new()
	_capture_prompt.text = "Select a control to rebind."
	GroundfireTheme.apply_label(_capture_prompt, 14, GroundfireTheme.COLOR_CYAN)
	inner.add_child(_capture_prompt)

	var controls_grid := GridContainer.new()
	controls_grid.columns = 3
	controls_grid.add_theme_constant_override("h_separation", 10)
	controls_grid.add_theme_constant_override("v_separation", 8)
	inner.add_child(controls_grid)
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
		inner.add_child(conflict_title)
		for conflict in conflicts:
			var conflict_label := Label.new()
			conflict_label.text = conflict
			GroundfireTheme.apply_label(conflict_label, 14, GroundfireTheme.COLOR_WARN)
			inner.add_child(conflict_label)
		var fix_conflicts := _add_button_to(inner, "Reset Conflicting Bindings", func() -> void:
			ControlSettings.reset_defaults()
			_show_options()
		)
		fix_conflicts.custom_minimum_size = Vector2(360, 38)
	var reset_controls := _add_button_to(inner, "Reset Controls", func() -> void:
		ControlSettings.reset_defaults()
		_show_options()
	)
	reset_controls.custom_minimum_size = Vector2(360, 38)
	var reset_gamepad := _add_button_to(inner, "Reset Gamepad Defaults", func() -> void:
		ControlSettings.reset_gamepad_defaults()
		_show_options()
	)
	reset_gamepad.custom_minimum_size = Vector2(360, 38)
	_add_button_to(inner, "Back", _show_main_menu, true)
	_focus_first_button(inner)


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
	config.save(OPTIONS_PATH)


func _apply_options() -> void:
	AudioServer.set_bus_mute(0, not _audio_enabled)
	AudioServer.set_bus_volume_db(0, linear_to_db(max(_master_volume, 0.001)))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if _vsync_enabled else DisplayServer.VSYNC_DISABLED)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if _fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)
	if not _fullscreen and _capabilities != null and not _capabilities.is_web():
		DisplayServer.window_set_size(_selected_resolution())


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


func _add_server_directory_options(parent: Container) -> void:
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
	if buttons.size() < 2:
		return
	for index in range(buttons.size()):
		var button := buttons[index]
		var previous := buttons[wrapi(index - 1, 0, buttons.size())]
		var next := buttons[wrapi(index + 1, 0, buttons.size())]
		button.focus_neighbor_top = previous.get_path()
		button.focus_neighbor_bottom = next.get_path()
