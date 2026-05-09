extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const BrowserStore := preload("res://scripts/browser_store.gd")
const NetworkAdapter := preload("res://scripts/network_adapter.gd")
const ServerDirectory := preload("res://scripts/server_directory.gd")
const WebSocketClient := preload("res://scripts/websocket_client.gd")

const TABLE_COLUMN_WIDTHS := [292.0, 150.0, 96.0, 220.0, 96.0]
const TABLE_HEADER_HEIGHT := 30.0
const TABLE_ROW_HEIGHT := 38.0

var _tabs: TabBar
var _status: Label
var _table: GridContainer
var _table_scroll: ScrollContainer
var _close_button: Button
var _connect_button: Button
var _favorite_button: Button
var _clear_history_button: Button
var _undo_button: Button
var _refresh_all_button: Button
var _action_buttons: Array[Button] = []
var _filter_controls: Array[Control] = []
var _filter_line: LineEdit
var _password_line: LineEdit
var _join_modal: PanelContainer
var _join_modal_title: Label
var _join_modal_hint: Label
var _join_cancel_button: Button
var _join_connect_button: Button
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
var _directory_loading := false
var _pending_join_entry: Dictionary = {}
var _last_undo_action: Dictionary = {}


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

	_close_button = Button.new()
	_close_button.text = "x"
	_close_button.custom_minimum_size = Vector2(42, 36)
	_close_button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(_close_button)
	_close_button.pressed.connect(_on_back_pressed)
	title_row.add_child(_close_button)

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
	_filter_line.text = _filter_text
	_filter_line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_filter_line.focus_mode = Control.FOCUS_ALL
	_filter_line.add_theme_stylebox_override("normal", GroundfireTheme.field_style())
	_filter_line.text_changed.connect(_on_filter_changed)
	filters.add_child(_filter_line)
	_filter_controls.append(_filter_line)

	var no_password := CheckButton.new()
	no_password.text = "No Password"
	no_password.button_pressed = _hide_passworded
	no_password.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(no_password)
	no_password.toggled.connect(func(value: bool) -> void:
		_hide_passworded = value
		_save_browser_store()
		_render_entries()
	)
	filters.add_child(no_password)
	_filter_controls.append(no_password)

	var open_slots := CheckButton.new()
	open_slots.text = "Open Slots"
	open_slots.button_pressed = _hide_full
	open_slots.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(open_slots)
	open_slots.toggled.connect(func(value: bool) -> void:
		_hide_full = value
		_save_browser_store()
		_render_entries()
	)
	filters.add_child(open_slots)
	_filter_controls.append(open_slots)

	var sort_menu := OptionButton.new()
	sort_menu.custom_minimum_size = Vector2(138, 36)
	sort_menu.add_item("Latency")
	sort_menu.add_item("Name")
	sort_menu.add_item("Players")
	sort_menu.select(_sort_index(_sort_mode))
	sort_menu.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(sort_menu)
	sort_menu.item_selected.connect(func(index: int) -> void:
		_sort_mode = sort_menu.get_item_text(index).to_lower()
		_save_browser_store()
		_render_entries()
	)
	filters.add_child(sort_menu)
	_filter_controls.append(sort_menu)

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
	_add_header("Server", 0)
	_add_header("Game", 1)
	_add_header("Players", 2)
	_add_header("Map", 3)
	_add_header("Latency", 4)

	_status = Label.new()
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status.text = _empty_message()
	GroundfireTheme.apply_label(_status, 15, GroundfireTheme.COLOR_CYAN)
	panel_stack.add_child(_status)

	var actions := HBoxContainer.new()
	actions.alignment = BoxContainer.ALIGNMENT_END
	actions.add_theme_constant_override("separation", 10)
	root.add_child(actions)
	var filter_button := _add_action(actions, "Change Filters")
	filter_button.pressed.connect(_focus_filter)
	_action_buttons.append(filter_button)
	_favorite_button = _add_action(actions, "Add Favorite")
	_favorite_button.pressed.connect(_toggle_selected_favorite)
	_action_buttons.append(_favorite_button)
	_clear_history_button = _add_action(actions, "Clear History")
	_clear_history_button.pressed.connect(_clear_history)
	_action_buttons.append(_clear_history_button)
	_undo_button = _add_action(actions, "Undo")
	_undo_button.pressed.connect(_undo_last_browser_action)
	_action_buttons.append(_undo_button)
	var quick_refresh := _add_action(actions, "Quick Refresh")
	quick_refresh.pressed.connect(_refresh_entries)
	_action_buttons.append(quick_refresh)
	_refresh_all_button = _add_action(actions, "Refresh All", true)
	_refresh_all_button.pressed.connect(_refresh_online_directory)
	_action_buttons.append(_refresh_all_button)
	_connect_button = _add_action(actions, "Connect", true)
	_connect_button.disabled = true
	_connect_button.pressed.connect(_on_connect_pressed)
	_action_buttons.append(_connect_button)
	_wire_server_browser_focus()
	_build_join_dialog()
	_refresh_entries()


func _add_header(text: String, column_index: int) -> void:
	var label := Label.new()
	label.text = text
	label.custom_minimum_size = Vector2(_column_width(column_index), TABLE_HEADER_HEIGHT)
	GroundfireTheme.apply_label(label, 16, GroundfireTheme.COLOR_WARN)
	_table.add_child(label)


func _refresh_entries() -> void:
	_entries = ServerDirectory.browser_entries(_capabilities.supports(_capabilities.FEATURE_LAN_DISCOVERY))
	_render_entries()


func _render_entries() -> void:
	_clear_table_rows()
	var tab_name := _tabs.get_tab_title(_tabs.current_tab)
	_visible_entries = ServerDirectory.filter_for_tab(_entries, tab_name)
	_visible_entries = _filter_entries(_visible_entries, tab_name)
	_selected_index = -1
	_hovered_index = -1
	_update_action_buttons()
	if _visible_entries.is_empty():
		var empty_message := _empty_message(tab_name)
		_add_row({
			"name": empty_message,
			"game": "Groundfire",
			"players": "-",
			"map": "-",
			"latency": "-",
		}, true)
		_status.text = empty_message
		return
	for index in range(_visible_entries.size()):
		_add_row(_visible_entries[index], false, index)
	_wire_table_focus()
	_status.text = "%d server(s) listed for %s." % [_visible_entries.size(), tab_name]


func _clear_table_rows() -> void:
	while _table.get_child_count() > 5:
		var old_child := _table.get_child(5)
		_table.remove_child(old_child)
		old_child.queue_free()


func _render_table_message(message: String) -> void:
	_clear_table_rows()
	_visible_entries = []
	_selected_index = -1
	_hovered_index = -1
	_add_row({
		"name": message,
		"game": "Groundfire",
		"players": "-",
		"map": "-",
		"latency": "-",
	}, true)
	_status.text = message
	_update_action_buttons()


func _add_row(entry: Dictionary, muted := false, row_index := -1) -> void:
	var values := PackedStringArray([
		str(entry.get("name", "")),
		str(entry.get("game", "")),
		str(entry.get("players", "")),
		str(entry.get("map", "")),
		str(entry.get("latency", "")),
	])
	for column_index in range(values.size()):
		var value := values[column_index]
		var cell := PanelContainer.new()
		cell.custom_minimum_size = Vector2(_column_width(column_index), TABLE_ROW_HEIGHT)
		cell.add_theme_stylebox_override("panel", GroundfireTheme.row_style(row_index == _selected_index))
		if row_index >= 0:
			cell.focus_mode = Control.FOCUS_ALL
			cell.gui_input.connect(_on_row_gui_input.bind(row_index))
			cell.focus_entered.connect(_on_row_focused.bind(row_index))
			cell.mouse_entered.connect(_on_row_hovered.bind(row_index))
			cell.mouse_exited.connect(_on_row_unhovered.bind(row_index))
		_table.add_child(cell)

		var label := Label.new()
		label.text = value
		label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var color := GroundfireTheme.COLOR_MUTED if muted else GroundfireTheme.COLOR_TEXT
		GroundfireTheme.apply_label(label, 15, color)
		cell.add_child(label)


func _column_width(column_index: int) -> float:
	if column_index < 0 or column_index >= TABLE_COLUMN_WIDTHS.size():
		return 120.0
	return float(TABLE_COLUMN_WIDTHS[column_index])


func _add_action(parent: Container, text: String, accent := false) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(128, 44)
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(button, accent)
	parent.add_child(button)
	return button


func _empty_message(tab_name := "") -> String:
	var normalized_tab := tab_name.to_lower()
	if normalized_tab == "favorites":
		if _favorites.is_empty():
			return "No favorites saved yet."
		return "No favorites match the current filters."
	if normalized_tab == "history":
		if _history.is_empty():
			return "No connection history yet."
		return "No history entries match the current filters."
	if _capabilities.is_web():
		return "No online servers responded. LAN discovery is not available in web builds."
	return "No servers responded. Use Refresh for online servers or LAN discovery on desktop builds."


func _filter_entries(entries: Array[Dictionary], tab_name: String) -> Array[Dictionary]:
	var normalized_filter := _filter_text.to_lower()
	var filtered := entries
	if tab_name.to_lower() == "favorites":
		filtered = _favorite_entries(entries)
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


func _favorite_entries(entries: Array[Dictionary]) -> Array[Dictionary]:
	var by_endpoint := {}
	for entry in entries:
		var endpoint := str(entry.get("endpoint", ""))
		if _favorites.has(endpoint):
			by_endpoint[endpoint] = entry
	for entry in _history:
		var endpoint := str(entry.get("endpoint", ""))
		if _favorites.has(endpoint) and not by_endpoint.has(endpoint):
			by_endpoint[endpoint] = entry
	var result: Array[Dictionary] = []
	for endpoint in _favorites:
		if by_endpoint.has(endpoint):
			result.append(Dictionary(by_endpoint[endpoint]))
		else:
			result.append(_favorite_placeholder(endpoint))
	return result


func _favorite_placeholder(endpoint: String) -> Dictionary:
	var source := ServerDirectory.SOURCE_ONLINE if endpoint.begins_with("ws://") or endpoint.begins_with("wss://") else ServerDirectory.SOURCE_LAN
	return {
		"name": "Saved Favorite",
		"game": "Groundfire",
		"players": "-",
		"map": "Not in directory",
		"latency": "-",
		"source": source,
		"endpoint": endpoint,
		"passworded": "false",
		"directory_status": "missing",
	}


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
	_password_line.focus_mode = Control.FOCUS_ALL
	_password_line.add_theme_stylebox_override("normal", GroundfireTheme.field_style())
	stack.add_child(_password_line)

	var actions := HBoxContainer.new()
	actions.alignment = BoxContainer.ALIGNMENT_END
	actions.add_theme_constant_override("separation", 10)
	stack.add_child(actions)
	_join_cancel_button = _add_action(actions, "Cancel")
	_join_cancel_button.pressed.connect(_hide_join_dialog)
	_join_connect_button = _add_action(actions, "Connect", true)
	_join_connect_button.pressed.connect(_confirm_join_dialog)
	_wire_join_modal_focus()


func _unhandled_input(event: InputEvent) -> void:
	if _join_modal != null and _join_modal.visible and event.is_action_pressed("ui_cancel"):
		_hide_join_dialog()
		get_viewport().set_input_as_handled()


func _on_tab_changed(_tab: int) -> void:
	_render_entries()


func _on_filter_changed(value: String) -> void:
	_filter_text = value
	_save_browser_store()
	_render_entries()


func _focus_filter() -> void:
	_filter_line.grab_focus()


func _wire_server_browser_focus() -> void:
	_wire_horizontal_focus(_filter_controls)
	_wire_horizontal_focus(_action_buttons)
	if _close_button != null:
		_close_button.focus_neighbor_bottom = _filter_line.get_path()
		_close_button.focus_neighbor_left = _connect_button.get_path()
		_close_button.focus_neighbor_right = _connect_button.get_path()
	if not _filter_controls.is_empty() and not _action_buttons.is_empty():
		for control in _filter_controls:
			control.focus_neighbor_top = _close_button.get_path()
			control.focus_neighbor_bottom = _action_buttons[0].get_path()
		for button in _action_buttons:
			button.focus_neighbor_top = _filter_line.get_path()
	if _connect_button != null:
		_connect_button.focus_neighbor_right = _close_button.get_path()


func _wire_table_focus() -> void:
	if _visible_entries.is_empty():
		return
	var first_cell: Control = _table.get_child(5)
	var last_row_first_cell: Control = _table.get_child(5 + (_visible_entries.size() - 1) * 5)
	for control in _filter_controls:
		control.focus_neighbor_bottom = first_cell.get_path()
	for button in _action_buttons:
		button.focus_neighbor_top = last_row_first_cell.get_path()
	for row_index in range(_visible_entries.size()):
		for column in range(5):
			var cell: Control = _table.get_child(5 + row_index * 5 + column)
			var left_column: int = column - 1 if column > 0 else 0
			var right_column: int = column + 1 if column < 4 else 4
			cell.focus_neighbor_left = _table.get_child(5 + row_index * 5 + left_column).get_path()
			cell.focus_neighbor_right = _table.get_child(5 + row_index * 5 + right_column).get_path()
			if row_index == 0:
				cell.focus_neighbor_top = _filter_line.get_path()
			else:
				cell.focus_neighbor_top = _table.get_child(5 + (row_index - 1) * 5 + column).get_path()
			if row_index == _visible_entries.size() - 1:
				cell.focus_neighbor_bottom = _action_buttons[0].get_path()
			else:
				cell.focus_neighbor_bottom = _table.get_child(5 + (row_index + 1) * 5 + column).get_path()


func _wire_join_modal_focus() -> void:
	if _password_line == null or _join_cancel_button == null or _join_connect_button == null:
		return
	_password_line.focus_neighbor_bottom = _join_connect_button.get_path()
	_password_line.focus_neighbor_top = _join_connect_button.get_path()
	_join_cancel_button.focus_neighbor_left = _join_connect_button.get_path()
	_join_cancel_button.focus_neighbor_right = _join_connect_button.get_path()
	_join_cancel_button.focus_neighbor_top = _password_line.get_path()
	_join_cancel_button.focus_neighbor_bottom = _password_line.get_path()
	_join_connect_button.focus_neighbor_left = _join_cancel_button.get_path()
	_join_connect_button.focus_neighbor_right = _join_cancel_button.get_path()
	_join_connect_button.focus_neighbor_top = _password_line.get_path()
	_join_connect_button.focus_neighbor_bottom = _password_line.get_path()


func _wire_horizontal_focus(controls: Array) -> void:
	if controls.is_empty():
		return
	if controls.size() == 1:
		controls[0].focus_neighbor_left = controls[0].get_path()
		controls[0].focus_neighbor_right = controls[0].get_path()
		return
	for index in range(controls.size()):
		var previous: Control = controls[(index - 1 + controls.size()) % controls.size()]
		var next: Control = controls[(index + 1) % controls.size()]
		var control: Control = controls[index]
		control.focus_neighbor_left = previous.get_path()
		control.focus_neighbor_right = next.get_path()


func _toggle_selected_favorite() -> void:
	if _selected_index < 0 or _selected_index >= _visible_entries.size():
		_status.text = "Select a server before changing favorites."
		return
	var endpoint := str(_visible_entries[_selected_index].get("endpoint", ""))
	if _favorites.has(endpoint):
		_favorites = BrowserStore.forget_favorite(_favorites, endpoint)
		_last_undo_action = {
			"type": "favorite_removed",
			"endpoint": endpoint,
		}
		_status.text = "Favorite removed: %s. Press Undo to restore." % endpoint
	else:
		_favorites = BrowserStore.remember_favorite(_favorites, endpoint)
		_last_undo_action.clear()
		_status.text = "Favorite saved: %s." % endpoint
	var status_message := _status.text
	_save_browser_store()
	if _tabs.get_tab_title(_tabs.current_tab).to_lower() == "favorites":
		_render_entries()
	else:
		_update_action_buttons()
	_status.text = status_message


func _clear_history() -> void:
	if _history.is_empty():
		_status.text = "History is already empty."
		return
	_last_undo_action = {
		"type": "history_cleared",
		"history": _copy_history_entries(_history),
	}
	_history = BrowserStore.clear_history()
	_save_browser_store()
	var status_message := "Connection history cleared. Press Undo to restore."
	if _tabs.get_tab_title(_tabs.current_tab).to_lower() == "history":
		_render_entries()
	else:
		_update_action_buttons()
	_status.text = status_message


func _undo_last_browser_action() -> void:
	if _last_undo_action.is_empty():
		_status.text = "Nothing to undo."
		return
	var undo_type := str(_last_undo_action.get("type", ""))
	var status_message := ""
	if undo_type == "favorite_removed":
		var endpoint := str(_last_undo_action.get("endpoint", ""))
		_favorites = BrowserStore.remember_favorite(_favorites, endpoint)
		status_message = "Favorite restored: %s." % endpoint
	elif undo_type == "history_cleared":
		_history = _copy_history_entries(_last_undo_action.get("history", []))
		status_message = "Connection history restored."
	else:
		status_message = "Nothing to undo."
	_last_undo_action.clear()
	_save_browser_store()
	_render_entries()
	_status.text = status_message


func _copy_history_entries(history_entries) -> Array[Dictionary]:
	var copied: Array[Dictionary] = []
	if typeof(history_entries) != TYPE_ARRAY:
		return copied
	for entry in history_entries:
		if typeof(entry) == TYPE_DICTIONARY:
			copied.append(Dictionary(entry))
	return copied


func _refresh_online_directory() -> void:
	if _directory_loading:
		_status.text = "Online server directory is already loading."
		return
	var url := _directory_url
	if url.is_empty():
		url = ServerDirectory.DEFAULT_DIRECTORY_PATH
	if url.begins_with("http"):
		_directory_retry_count = 0
		_request_online_directory(url)
	else:
		_directory_loading = false
		_refresh_entries()
		_status.text = "Server directory refreshed from local JSON (%s)." % ServerDirectory.configured_directory_label()


func _request_online_directory(url: String, message := "Loading online server directory...") -> void:
	_directory_retry_url = url
	_directory_loading = true
	_render_table_message(message)
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
	var directory_diagnostic := ServerDirectory.directory_diagnostic_from_body(body)
	if _entries.is_empty():
		_load_directory_fallback("Online server directory invalid or empty (%s). Using local fallback." % directory_diagnostic)
	else:
		_directory_loading = false
		_status.text = "Online server directory loaded (%s)." % directory_diagnostic
		_render_entries()


func _load_directory_fallback(message: String) -> void:
	_directory_loading = false
	_entries = ServerDirectory.browser_entries(_capabilities.supports(_capabilities.FEATURE_LAN_DISCOVERY))
	_render_entries()
	_status.text = message


func _on_row_gui_input(event: InputEvent, row_index: int) -> void:
	if event.is_action_pressed("ui_accept"):
		_select_row(row_index)
		_on_connect_pressed()
		get_viewport().set_input_as_handled()
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		_select_row(row_index)
		if event.double_click:
			_on_connect_pressed()


func _on_row_focused(row_index: int) -> void:
	_select_row(row_index)


func _select_row(row_index: int) -> void:
	if row_index < 0 or row_index >= _visible_entries.size():
		return
	_selected_index = row_index
	_update_action_buttons()
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


func _update_action_buttons() -> void:
	if _connect_button != null:
		_connect_button.disabled = _selected_index < 0
	if _favorite_button != null:
		_favorite_button.disabled = _selected_index < 0
		_favorite_button.text = "Add Favorite"
		if _selected_index >= 0 and _selected_index < _visible_entries.size():
			var endpoint := str(_visible_entries[_selected_index].get("endpoint", ""))
			if _favorites.has(endpoint):
				_favorite_button.text = "Remove Favorite"
	if _clear_history_button != null:
		_clear_history_button.disabled = _history.is_empty()
	if _undo_button != null:
		_undo_button.disabled = _last_undo_action.is_empty()
	if _refresh_all_button != null:
		_refresh_all_button.disabled = _directory_loading
		_refresh_all_button.text = "Loading..." if _directory_loading else "Refresh All"


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
		var auth_token := str(_pending_join_entry.get("auth_token", ""))
		_websocket_client.join(player_name, password, auth_token)
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
		_status.text = NetworkAdapter.server_error_status_message(message)
	elif message_type == NetworkAdapter.MESSAGE_SNAPSHOT:
		_status.text = "Received online snapshot."
	elif message_type == NetworkAdapter.MESSAGE_PONG:
		_status.text = "Latency pong received."
	else:
		_status.text = "Received online message: %s." % message_type


func _load_browser_store() -> void:
	var store := BrowserStore.load_store()
	_favorites = []
	for endpoint in store.get("favorites", []):
		_favorites.append(str(endpoint))
	_history = []
	for entry in store.get("history", []):
		if typeof(entry) == TYPE_DICTIONARY:
			_history.append(Dictionary(entry))
	var filters: Dictionary = store.get("filters", BrowserStore.default_filters())
	_filter_text = str(filters.get("text", ""))
	_hide_passworded = bool(filters.get("hide_passworded", false))
	_hide_full = bool(filters.get("hide_full", false))
	_sort_mode = str(filters.get("sort_mode", "latency"))


func _save_browser_store() -> void:
	BrowserStore.save_store(_favorites, _history, _browser_filter_state())


func _browser_filter_state() -> Dictionary:
	return BrowserStore.filter_state(_filter_text, _hide_passworded, _hide_full, _sort_mode)


func _sort_index(sort_mode: String) -> int:
	if sort_mode == "name":
		return 1
	if sort_mode == "players":
		return 2
	return 0


func _on_back_pressed() -> void:
	get_parent().get_parent()._show_main_menu()
