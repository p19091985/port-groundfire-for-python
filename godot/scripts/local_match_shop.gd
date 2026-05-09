extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")

signal continue_requested
signal buy_requested(weapon_name: String)

var _title_label: Label
var _subtitle_label: Label
var _credits_label: Label
var _message_label: Label
var _weapon_list: VBoxContainer
var _continue_button: Button
var _focus_buttons: Array[Button] = []
var _state := {}


func _ready() -> void:
	_build()
	refresh(_state)


func refresh(state: Dictionary) -> void:
	_state = state
	if _weapon_list == null:
		return
	_title_label.text = str(_state.get("title", "Round Complete"))
	_subtitle_label.text = "Round %d  Score %d  Reward %d" % [
		int(_state.get("round", 1)),
		int(_state.get("score", 0)),
		int(_state.get("reward", 0)),
	]
	_credits_label.text = "Credits %d" % int(_state.get("credits", 0))
	_message_label.text = str(_state.get("message", ""))
	_rebuild_weapon_rows()
	_continue_button.grab_focus.call_deferred()


func _build() -> void:
	anchor_right = 1.0
	anchor_bottom = 1.0
	mouse_filter = Control.MOUSE_FILTER_STOP

	var backdrop := PanelContainer.new()
	backdrop.anchor_right = 1.0
	backdrop.anchor_bottom = 1.0
	backdrop.add_theme_stylebox_override("panel", GroundfireTheme.modal_backdrop_style())
	add_child(backdrop)

	var center := CenterContainer.new()
	center.anchor_right = 1.0
	center.anchor_bottom = 1.0
	backdrop.add_child(center)

	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(560.0, 430.0)
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style())
	center.add_child(panel)

	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 10)
	panel.add_child(stack)

	_title_label = Label.new()
	GroundfireTheme.apply_label(_title_label, 28, GroundfireTheme.COLOR_TEXT)
	stack.add_child(_title_label)

	_subtitle_label = Label.new()
	GroundfireTheme.apply_label(_subtitle_label, 15, GroundfireTheme.COLOR_CYAN)
	stack.add_child(_subtitle_label)

	_credits_label = Label.new()
	GroundfireTheme.apply_label(_credits_label, 18, GroundfireTheme.COLOR_WARN)
	stack.add_child(_credits_label)

	_message_label = Label.new()
	_message_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(_message_label, 14, GroundfireTheme.COLOR_CYAN)
	stack.add_child(_message_label)

	_weapon_list = VBoxContainer.new()
	_weapon_list.add_theme_constant_override("separation", 8)
	stack.add_child(_weapon_list)

	_continue_button = _shop_button("Continue", true)
	_continue_button.pressed.connect(func() -> void: continue_requested.emit())
	stack.add_child(_continue_button)


func _rebuild_weapon_rows() -> void:
	for child in _weapon_list.get_children():
		child.queue_free()
	_focus_buttons.clear()
	var inventory: Array = _state.get("inventory", [])
	var credits := int(_state.get("credits", 0))
	for weapon in inventory:
		var weapon_data: Dictionary = weapon
		var weapon_name := str(weapon_data.get("name", "Weapon"))
		var cost := int(weapon_data.get("cost", 0))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		_weapon_list.add_child(row)

		var label := Label.new()
		label.text = "%s  Ammo %s  Damage %d  Blast %d" % [
			weapon_name,
			_format_ammo(int(weapon_data.get("ammo", -1))),
			int(weapon_data.get("damage", 0)),
			int(weapon_data.get("blast", 0)),
		]
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_MUTED)
		row.add_child(label)

		var buy_button := _shop_button("Buy %d" % cost)
		buy_button.disabled = cost <= 0 or credits < cost
		var captured_name := weapon_name
		buy_button.pressed.connect(func() -> void: buy_requested.emit(captured_name))
		row.add_child(buy_button)
		if not buy_button.disabled:
			_focus_buttons.append(buy_button)
	_focus_buttons.append(_continue_button)
	_wire_vertical_focus(_focus_buttons)


func _shop_button(text: String, accent := false) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(116.0, 36.0)
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(button, accent)
	return button


func _format_ammo(value: int) -> String:
	if value < 0:
		return "inf"
	return str(value)


func _wire_vertical_focus(buttons: Array[Button]) -> void:
	if buttons.is_empty():
		return
	if buttons.size() == 1:
		buttons[0].focus_neighbor_top = buttons[0].get_path()
		buttons[0].focus_neighbor_bottom = buttons[0].get_path()
		return
	for index in range(buttons.size()):
		var button := buttons[index]
		var previous := buttons[wrapi(index - 1, 0, buttons.size())]
		var next := buttons[wrapi(index + 1, 0, buttons.size())]
		button.focus_neighbor_top = previous.get_path()
		button.focus_neighbor_bottom = next.get_path()
