extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const BrowserStore := preload("res://scripts/browser_store.gd")
const NetworkAdapter := preload("res://scripts/network_adapter.gd")
const ServerDirectory := preload("res://scripts/server_directory.gd")
const WebSocketClient := preload("res://scripts/websocket_client.gd")

var _tabs: TabBar
var _status: Label
var _table: GridContainer
var _table_scroll: ScrollContainer
var _connect_button: Button
var _filter_line: LineEdit
var _password_line: LineEdit
var _join_modal: PanelContainer
var _join_modal_title: Label
var _join_modal_hint: Label
var _http_request: HTTPRequest
var _websocket_client: Node
var _capabilities: Node
var _entries: Array[Dictionary] = []
var _visible_entries: Array[Dictionary] = []
var _favorites: Array[String] = []
var _history: Array[Dictionary] = []
var _selected_index := -1
var _hovered_index := -1
var _filter_text := ""
var _hide_passworded := false
var _hide_full := false
var _sort_mode := "latency"
var _directory_url := ""
var _directory_retry_count := 0
var _directory_retry_url := ""
var _pending_join_entry: Dictionary = {}


func _ready() -> void:
	_capabilities = get_node("/root/PlatformCapabilities")
	_build()


func _build() -> void:
	_load_browser_store()
	_directory_url = ServerDirectory.configured_directory_url()
	_http_request = HTTPRequest.new()
	_http_request.timeout = ServerDirectory.HTTP_TIMEOUT_SECONDS
	_http_request.request_completed.connect(_on_http_directory_completed)
	add_child(_http_request)
	_websocket_client = WebSocketClient.new()
	_websocket_client.status_changed.connect(_on_websocket_status_changed)
	_websocket_client.message_received.connect(_on_websocket_message_received)
	add_child(_websocket_client)

	var root := VBoxContainer.new()
	root.anchor_right = 1.0
	root.anchor_bottom = 1.0
	root.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_theme_constant_override("separation", 12)
	add_child(root)

	var title_row := HBoxContainer.new()
	title_row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	root.add_child(title_row)

	var title := Label.new()
	title.text = "Servers"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	GroundfireTheme.apply_label(title, 34, GroundfireTheme.COLOR_TEXT)
	title_row.add_child(title)

	var close := Button.new()
	close.text = "x"
	close.custom_minimum_size = Vector2(42, 36)
	GroundfireTheme.apply_button(close)
	close.pressed.connect(_on_back_pressed)
	title_row.add_child(close)

	_tabs = TabBar.new()
	_tabs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for tab_name in _capabilities.visible_server_browser_tabs():
		_tabs.add_tab(tab_name)
	_tabs.tab_changed.connect(_on_tab_changed)
	root.add_child(_tabs)

	var filters := HBoxContainer.new()
	filters.add_theme_constant_override("separation", 10)
	root.add_child(filters)
	_filter_line = LineEdit.new()
	_filter_line.placeholder_text = "Filter servers"
	_filter_line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_filter_line.add_theme_stylebox_override("normal", GroundfireTheme.field_style())
	_filter_line.text_changed.connect(_on_filter_changed)
	filters.add_child(_filter_line)

	var no_password := CheckButton.new()
	no_password.text = "No Password"
	no_password.button_pressed = _hide_passworded
	GroundfireTheme.apply_button(no_password)
	no_password.toggled.connect(func(value: bool) -> void:
		_hide_passworded = value
		_render_entries()
	)
	filters.add_child(no_password)

	var open_slots := CheckButton.new()
	open_slots.text = "Open Slots"
	open_slots.button_pressed = _hide_full
	GroundfireTheme.apply_button(open_slots)
	open_slots.toggled.connect(func(value: bool) -> void:
		_hide_full = value
		_render_entries()
	)
	filters.add_child(open_slots)

	var sort_menu := OptionButton.new()
	sort_menu.custom_minimum_size = Vector2(138, 36)
	sort_menu.add_item("Latency")
	sort_menu.add_item("Name")
	sort_menu.add_item("Players")
	GroundfireTheme.apply_button(sort_menu)
	sort_menu.item_selected.connect(func(index: int) -> void:
		_sort_mode = sort_menu.get_item_text(index).to_lower()
		_render_entries()
	)
	filters.add_child(sort_menu)

	var panel := PanelContainer.new()
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style())
	root.add_child(panel)

	var panel_stack := VBoxContainer.new()
	panel_stack.add_theme_constant_override("separation", 8)
	panel.add_child(panel_stack)

	_table_scroll = ScrollContainer.new()
	_table_scroll.custom_minimum_size = Vector2(860, 390)
	_table_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_table_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_table_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel_stack.add_child(_table_scroll)

	_table = GridContainer.new()
	_table.columns = 5
	_table.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_table.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_table_scroll.add_child(_table)
	_add_header("Server")
	_add_header("Game")
	_add_header("Players")
	_add_header("Map")
	_add_header("Latency")

	_status = Label.new()
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status.text = _empty_message()
	GroundfireTheme.apply_label(_status, 15, GroundfireTheme.COLOR_CYAN)
	panel_stack.add_child(_status)

	var actions := HBoxContainer.new()
	actions.alignment = BoxContainer.ALIGNMENT_END
	actions.add_theme_constant_override("separation", 10)
	root.add_child(actions)
	_add_action(actions, "Change Filters").pressed.connect(_focus_filter)
	_add_action(actions, "Add Favorite").pressed.connect(_add_selected_favorite)
	_add_action(actions, "Quick Refresh").pressed.connect(_refresh_entries)
	_add_action(actions, "Refresh All", true).pressed.connect(_refresh_online_directory)
	_connect_button = _add_action(actions, "Connect", true)
	_connect_button.disabled = true
	_connect_button.pressed.connect(_on_connect_pressed)
	_build_join_dialog()
	_refresh_entries()


func _add_header(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.custom_minimum_size = Vector2(120, 28)
	GroundfireTheme.apply_label(label, 16, GroundfireTheme.COLOR_WARN)
	_table.add_child(label)


func _refresh_entries() -> void:
	_entries = ServerDirectory.browser_entries(_capabilities.supports(_capabilities.FEATURE_LAN_DISCOVERY))
	_render_entries()


func _render_entries() -> void:
	while _table.get_child_count() > 5:
		_table.get_child(5).queue_free()
	var tab_name := _tabs.get_tab_title(_tabs.current_tab)
	_visible_entries = ServerDirectory.filter_for_tab(_entries, tab_name)
	_visible_entries = _filter_entries(_visible_entries, tab_name)
	_selected_index = -1
	_hovered_index = -1
	_update_connect_button()
	if _visible_entries.is_empty():
		_add_row({
			"name": _empty_message(),
			"game": "Groundfire",
			"players": "-",
			"map": "-",
			"latency": "-",
		}, true)
		_status.text = _empty_message()
		return
	for index in range(_visible_entries.size()):
		_add_row(_visible_entries[index], false, index)
	_status.text = "%d server(s) listed for %s." % [_visible_entries.size(), tab_name]


func _add_row(entry: Dictionary, muted := false, row_index := -1) -> void:
	var values := PackedStringArray([
		str(entry.get("name", "")),
		str(entry.get("game", "")),
		str(entry.get("players", "")),
		str(entry.get("map", "")),
		str(entry.get("latency", "")),
	])
	for value in values:
		var cell := PanelContainer.new()
		cell.custom_minimum_size = Vector2(120, 34)
		cell.add_theme_stylebox_override("panel", GroundfireTheme.row_style(row_index == _selected_index))
		if row_index >= 0:
			cell.gui_input.connect(_on_row_gui_input.bind(row_index))
			cell.mouse_entered.connect(_on_row_hovered.bind(row_index))
			cell.mouse_exited.connect(_on_row_unhovered.bind(row_index))
		_table.add_child(cell)

		var label := Label.new()
		label.text = value
		label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var color := GroundfireTheme.COLOR_MUTED if muted else GroundfireTheme.COLOR_TEXT
		GroundfireTheme.apply_label(label, 15, color)
		cell.add_child(label)


func _add_action(parent: Container, text: String, accent := false) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(128, 44)
	GroundfireTheme.apply_button(button, accent)
	parent.add_child(button)
	return button


func _empty_message() -> String:
	if _capabilities.is_web():
		return "No online servers responded. LAN discovery is not available in web builds."
	return "No servers responded. Use Refresh for online servers or LAN discovery on desktop builds."


func _filter_entries(entries: Array[Dictionary], tab_name: String) -> Array[Dictionary]:
	var normalized_filter := _filter_text.to_lower()
	var filtered := entries
	if tab_name.to_lower() == "favorites":
		filtered = filtered.filter(func(entry: Dictionary) -> bool: return _favorites.has(str(entry.get("endpoint", ""))))
	elif tab_name.to_lower() == "history":
		filtered = _history.duplicate()
	if _hide_passworded:
		filtered = filtered.filter(func(entry: Dictionary) -> bool: return str(entry.get("passworded", "false")) != "true")
	if _hide_full:
		filtered = filtered.filter(func(entry: Dictionary) -> bool: return _entry_has_open_slot(entry))
	if normalized_filter.is_empty():
		_sort_entries(filtered)
		return filtered
	filtered = filtered.filter(func(entry: Dictionary) -> bool: return _entry_matches_filter(entry, normalized_filter))
	_sort_entries(filtered)
	return filtered


func _entry_matches_filter(entry: Dictionary, normalized_filter: String) -> bool:
	return str(entry.get("name", "")).to_lower().contains(normalized_filter) \
		or str(entry.get("map", "")).to_lower().contains(normalized_filter) \
		or str(entry.get("endpoint", "")).to_lower().contains(normalized_filter)


func _entry_has_open_slot(entry: Dictionary) -> bool:
	var players := str(entry.get("players", ""))
	var parts := players.split("/")
	if parts.size() != 2:
		return true
	return int(parts[0]) < int(parts[1])


func _sort_entries(entries: Array[Dictionary]) -> void:
	entries.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		if _sort_mode == "name":
			return str(a.get("name", "")).to_lower() < str(b.get("name", "")).to_lower()
		if _sort_mode == "players":
			return _player_count(a) > _player_count(b)
		return _latency_value(a) < _latency_value(b)
	)


func _player_count(entry: Dictionary) -> int:
	var players := str(entry.get("players", "0"))
	var parts := players.split("/")
	return int(parts[0]) if not parts.is_empty() else 0


func _latency_value(entry: Dictionary) -> int:
	var latency := str(entry.get("latency", "9999")).replace("ms", "").strip_edges()
	if latency == "-":
		return 9999
	return int(latency)


func _build_join_dialog() -> void:
	_join_modal = PanelContainer.new()
	_join_modal.visible = false
	_join_modal.anchor_right = 1.0
	_join_modal.anchor_bottom = 1.0
	_join_modal.add_theme_stylebox_override("panel", GroundfireTheme.modal_backdrop_style())
	add_child(_join_modal)

	var center := CenterContainer.new()
	_join_modal.add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(460, 210)
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style())
	center.add_child(panel)

	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 12)
	panel.add_child(stack)

	_join_modal_title = Label.new()
	_join_modal_title.text = "Connect"
	GroundfireTheme.apply_label(_join_modal_title, 24, GroundfireTheme.COLOR_TEXT)
	stack.add_child(_join_modal_title)

	_join_modal_hint = Label.new()
	_join_modal_hint.text = "Enter server password if required."
	_join_modal_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(_join_modal_hint, 15, GroundfireTheme.COLOR_CYAN)
	stack.add_child(_join_modal_hint)

	_password_line = LineEdit.new()
	_password_line.placeholder_text = "Password"
	_password_line.secret = true
	_password_line.add_theme_stylebox_override("normal", GroundfireTheme.field_style())
	stack.add_child(_password_line)

	var actions := HBoxContainer.new()
	actions.alignment = BoxContainer.ALIGNMENT_END
	actions.add_theme_constant_override("separation", 10)
	stack.add_child(actions)
	var cancel := _add_action(actions, "Cancel")
	cancel.pressed.connect(_hide_join_dialog)
	var connect := _add_action(actions, "Connect", true)
	connect.pressed.connect(_confirm_join_dialog)


func _on_tab_changed(_tab: int) -> void:
	_render_entries()


func _on_filter_changed(value: String) -> void:
	_filter_text = value
	_render_entries()


func _focus_filter() -> void:
	_filter_line.grab_focus()


func _add_selected_favorite() -> void:
	if _selected_index < 0 or _selected_index >= _visible_entries.size():
		_status.text = "Select a server before adding a favorite."
		return
	var endpoint := str(_visible_entries[_selected_index].get("endpoint", ""))
	_favorites = BrowserStore.remember_favorite(_favorites, endpoint)
	_save_browser_store()
	_status.text = "Favorite saved: %s." % endpoint


func _refresh_online_directory() -> void:
	var url := _directory_url
	if url.is_empty():
		url = ServerDirectory.DEFAULT_DIRECTORY_PATH
	if url.begins_with("http"):
		_directory_retry_count = 0
		_request_online_directory(url)
	else:
		_refresh_entries()
		_status.text = "Server directory refreshed from local JSON."


func _request_online_directory(url: String, message := "Loading online server directory...") -> void:
	_directory_retry_url = url
	_status.text = message
	var error := ServerDirectory.refresh_from_http(_http_request, url)
	if error != OK:
		_load_directory_fallback("Online server directory request could not start: %d." % error)


func _on_http_directory_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if ServerDirectory.should_retry_directory_request(result, response_code, _directory_retry_count):
		_directory_retry_count += 1
		_request_online_directory(
			_directory_retry_url,
			"Retrying online server directory (%d/%d)..." % [
				_directory_retry_count,
				ServerDirectory.HTTP_RETRY_LIMIT,
			]
		)
		return
	if result != HTTPRequest.RESULT_SUCCESS:
		_load_directory_fallback(
			"Online server directory failed: %s. Using local fallback." % ServerDirectory.http_diagnostic(result, response_code)
		)
		return
	if response_code < 200 or response_code >= 300:
		_load_directory_fallback(
			"Online server directory failed: %s. Using local fallback." % ServerDirectory.http_diagnostic(result, response_code)
		)
		return
	_entries = ServerDirectory.entries_from_http_body(body, _capabilities.supports(_capabilities.FEATURE_LAN_DISCOVERY))
	if _entries.is_empty():
		_load_directory_fallback("Online server directory was empty. Using local fallback.")
	else:
		_status.text = "Online server directory loaded."
		_render_entries()


func _load_directory_fallback(message: String) -> void:
	_entries = ServerDirectory.browser_entries(_capabilities.supports(_capabilities.FEATURE_LAN_DISCOVERY))
	_render_entries()
	_status.text = message


func _on_row_gui_input(event: InputEvent, row_index: int) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		_selected_index = row_index
		_update_connect_button()
		_render_selected_row_styles()
		var entry := _visible_entries[_selected_index]
		_status.text = "Selected %s at %s." % [entry.get("name", ""), entry.get("endpoint", "")]


func _on_row_hovered(row_index: int) -> void:
	_hovered_index = row_index
	_render_selected_row_styles()


func _on_row_unhovered(row_index: int) -> void:
	if _hovered_index == row_index:
		_hovered_index = -1
		_render_selected_row_styles()


func _render_selected_row_styles() -> void:
	for index in range(_visible_entries.size()):
		for column in range(5):
			var cell := _table.get_child(5 + index * 5 + column)
			cell.add_theme_stylebox_override(
				"panel",
				GroundfireTheme.row_style(index == _selected_index, index == _hovered_index)
			)


func _update_connect_button() -> void:
	if _connect_button != null:
		_connect_button.disabled = _selected_index < 0


func _on_connect_pressed() -> void:
	if _selected_index < 0 or _selected_index >= _visible_entries.size():
		return
	var entry := _visible_entries[_selected_index]
	if str(entry.get("passworded", "false")) == "true":
		_password_line.text = ""
		_show_join_dialog(entry)
		return
	_stage_connect(entry)


func _confirm_join_dialog() -> void:
	if _selected_index < 0 or _selected_index >= _visible_entries.size():
		return
	var entry := _visible_entries[_selected_index].duplicate()
	entry["password"] = _password_line.text
	_hide_join_dialog()
	_stage_connect(entry)


func _show_join_dialog(entry: Dictionary) -> void:
	_join_modal_title.text = "Connect to %s" % entry.get("name", "server")
	_join_modal_hint.text = "Enter server password if required. Endpoint: %s" % entry.get("endpoint", "")
	_join_modal.visible = true
	_password_line.grab_focus()


func _hide_join_dialog() -> void:
	_join_modal.visible = false


func _stage_connect(entry: Dictionary) -> void:
	_history = BrowserStore.remember_history(_history, entry)
	_save_browser_store()
	var allow_udp: bool = _capabilities.supports(_capabilities.FEATURE_UDP_TRANSPORT)
	var endpoint := str(entry.get("endpoint", ""))
	var transport := NetworkAdapter.transport_for_endpoint(endpoint, allow_udp)
	if transport == NetworkAdapter.TRANSPORT_WEBSOCKET:
		_pending_join_entry = entry.duplicate()
		_status.text = "Connecting to %s..." % endpoint
		get_parent().get_parent()._show_online_match(_pending_join_entry)
		return
	_status.text = NetworkAdapter.staged_connect_message(entry, allow_udp)


func _on_websocket_status_changed(status: String) -> void:
	if status == "websocket_connected":
		var player_name := NetworkAdapter.PLAYER_NAME_DEFAULT
		var password := str(_pending_join_entry.get("password", ""))
		_websocket_client.join(player_name, password)
		_websocket_client.ping()
		_status.text = "WebSocket connected. Join sent as %s." % player_name
	elif status == "websocket_connecting":
		_status.text = "Opening WebSocket..."
	elif status == "websocket_closed" or status == "websocket_disconnected":
		_status.text = "WebSocket disconnected."
	else:
		_status.text = status.capitalize().replace("_", " ")


func _on_websocket_message_received(message: Dictionary) -> void:
	var message_type := str(message.get("type", "unknown"))
	if message_type == NetworkAdapter.MESSAGE_ERROR:
		_status.text = "WebSocket error: %s." % message.get("message", "unknown")
	elif message_type == NetworkAdapter.MESSAGE_SNAPSHOT:
		_status.text = "Received online snapshot."
	elif message_type == NetworkAdapter.MESSAGE_PONG:
		_status.text = "Latency pong received."
	else:
		_status.text = "Received online message: %s." % message_type


func _load_browser_store() -> void:
	var store := BrowserStore.load_store()
	_favorites = store.get("favorites", [])
	_history = store.get("history", [])


func _save_browser_store() -> void:
	BrowserStore.save_store(_favorites, _history)


func _on_back_pressed() -> void:
	get_parent().get_parent()._show_main_menu()
