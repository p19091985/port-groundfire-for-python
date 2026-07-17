extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")

const DISABLED_CLASSIC_ITEMS := [
	{"name": "Rolling Mines", "cost": 50},
	{"name": "Airstrike", "cost": 100},
	{"name": "Death's Head", "cost": 200},
	{"name": "Hover Coil", "cost": 150},
	{"name": "Corbomite", "cost": 20},
]
const DISABLED_CLASSIC_ITEM_NAMES := {
	"Rolling Mines": true,
	"Airstrike": true,
	"Death's Head": true,
	"Hover Coil": true,
	"Corbomite": true,
}
const CLASSIC_SHOP_ORDER := [
	"Machine Gun",
	"Jump Jet",
	"MIRV",
	"Missile",
	"Nuke",
	"Rolling Mines",
	"Airstrike",
	"Death's Head",
	"Hover Coil",
	"Corbomite",
]
const CLASSIC_SHOP_DISPLAY_NAMES := {
	"MIRV": "Mirvs",
	"Missile": "Missiles",
	"Nuke": "Nukes",
}
const CLASSIC_BUY_ACTION_LABEL := "Buy"

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
var _preferred_focus_name := ""
var _roster_money_container: HBoxContainer


func _ready() -> void:
	_build()
	refresh(_state)


func refresh(state: Dictionary) -> void:
	_state = state
	if _weapon_list == null:
		return
	_title_label.text = str(_state.get("title", "Round Complete"))
	var round_number := int(_state.get("round", 1))
	var total_rounds := int(_state.get("total_rounds", 0))
	if total_rounds > 0:
		_subtitle_label.text = "Round %d of %d  Score %d  Reward %d" % [
			round_number,
			total_rounds,
			int(_state.get("score", 0)),
			int(_state.get("reward", 0)),
		]
	else:
		_subtitle_label.text = "Round %d  Score %d  Reward %d" % [
			round_number,
			int(_state.get("score", 0)),
			int(_state.get("reward", 0)),
		]
	_credits_label.text = "%s  Money %s  Fuel reserve %d%%" % [
		str(_state.get("shopper_name", "Player")),
		_format_money(int(_state.get("credits", 0))),
		int(_state.get("fuel_reserve", 100)),
	]
	_message_label.text = str(_state.get("message", ""))
	_rebuild_weapon_rows()
	call_deferred("_restore_shop_focus")


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

	_continue_button = _shop_button("Done!", true)
	_continue_button.pressed.connect(func() -> void: continue_requested.emit())
	stack.add_child(_continue_button)

	_roster_money_container = HBoxContainer.new()
	_roster_money_container.add_theme_constant_override("separation", 16)
	_roster_money_container.alignment = BoxContainer.ALIGNMENT_CENTER
	stack.add_child(_roster_money_container)


func _rebuild_weapon_rows() -> void:
	for child in _weapon_list.get_children():
		child.queue_free()
	for child in _roster_money_container.get_children():
		child.queue_free()
	_focus_buttons.clear()
	var credits := int(_state.get("credits", 0))
	var input_locked := bool(_state.get("input_locked", false))
	_add_catalog_header()
	for item_data in _classic_catalog_rows():
		if bool(item_data.get("is_shop_item", false)):
			_add_shop_item_row(item_data, credits, input_locked)
		else:
			_add_weapon_row(item_data, credits, input_locked)
	_add_disabled_catalog_rows()

	var participants: Array = _state.get("participants", [])
	for p_data in participants:
		var p: Dictionary = p_data
		var money_label := Label.new()
		money_label.text = "%s: $%d" % [str(p.get("name", "Player")), int(p.get("credits", 0))]
		GroundfireTheme.apply_label(money_label, 14, p.get("color", Color.WHITE))
		_roster_money_container.add_child(money_label)

	_continue_button.disabled = input_locked
	_focus_buttons.append(_continue_button)
	_wire_vertical_focus(_focus_buttons)


func _add_catalog_header() -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	_weapon_list.add_child(row)
	var cost := Label.new()
	cost.text = "Cost"
	cost.custom_minimum_size = Vector2(84.0, 22.0)
	GroundfireTheme.apply_label(cost, 13, GroundfireTheme.COLOR_WARN)
	row.add_child(cost)
	var item := Label.new()
	item.text = "Item"
	item.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	GroundfireTheme.apply_label(item, 13, GroundfireTheme.COLOR_WARN)
	row.add_child(item)


func _classic_catalog_rows() -> Array[Dictionary]:
	var by_name: Dictionary = {}
	for weapon in Array(_state.get("inventory", [])):
		var weapon_data: Dictionary = weapon
		if int(weapon_data.get("cost", 0)) > 0:
			var weapon_name := str(weapon_data.get("name", ""))
			if not DISABLED_CLASSIC_ITEM_NAMES.has(weapon_name):
				by_name[weapon_name] = weapon_data.duplicate(true)
	for shop_item in Array(_state.get("shop_items", [])):
		var item_data: Dictionary = shop_item
		var copy := item_data.duplicate(true)
		copy["is_shop_item"] = true
		var item_name := str(copy.get("name", ""))
		if not DISABLED_CLASSIC_ITEM_NAMES.has(item_name):
			by_name[item_name] = copy
	var ordered: Array[Dictionary] = []
	for name in CLASSIC_SHOP_ORDER:
		if by_name.has(name):
			ordered.append(Dictionary(by_name[name]))
	return ordered


func _add_weapon_row(weapon_data: Dictionary, credits: int, input_locked := false) -> void:
	var weapon_name := str(weapon_data.get("name", "Weapon"))
	var cost := int(weapon_data.get("cost", 0))
	var pack_size := int(weapon_data.get("shop_pack", weapon_data.get("ammo", 0)))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	_weapon_list.add_child(row)

	row.add_child(_cost_cell(cost))

	var stock_amount := int(weapon_data.get("stock", weapon_data.get("ammo", -1)))
	var label := Label.new()
	label.text = "%s  Stock %s  Pack %s  Damage %d  Blast %d" % [
		_catalog_display_name(weapon_name),
		_format_ammo(stock_amount),
		_format_pack(pack_size),
		int(weapon_data.get("damage", 0)),
		int(weapon_data.get("blast", 0)),
	]
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_MUTED)
	row.add_child(label)

	var buy_button := _shop_button(CLASSIC_BUY_ACTION_LABEL)
	buy_button.disabled = input_locked or cost <= 0 or credits < cost
	buy_button.set_meta("shop_focus_name", weapon_name)
	var captured_name := weapon_name
	buy_button.focus_entered.connect(_remember_shop_focus.bind(captured_name))
	buy_button.pressed.connect(func() -> void: buy_requested.emit(captured_name))
	row.add_child(buy_button)
	if not buy_button.disabled:
		_focus_buttons.append(buy_button)


func _add_shop_item_row(item_data: Dictionary, credits: int, input_locked := false) -> void:
	var item_name := str(item_data.get("name", "Item"))
	var item_cost := int(item_data.get("cost", 0))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	_weapon_list.add_child(row)

	row.add_child(_cost_cell(item_cost))

	var label := Label.new()
	label.text = "%s  %s  Current %s" % [
		_catalog_display_name(item_name),
		str(item_data.get("effect", "")),
		str(item_data.get("current", "")),
	]
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_MUTED)
	row.add_child(label)

	var buy_button := _shop_button(CLASSIC_BUY_ACTION_LABEL)
	buy_button.disabled = input_locked or item_cost <= 0 or credits < item_cost
	buy_button.set_meta("shop_focus_name", item_name)
	var captured_name := item_name
	buy_button.focus_entered.connect(_remember_shop_focus.bind(captured_name))
	buy_button.pressed.connect(func() -> void: buy_requested.emit(captured_name))
	row.add_child(buy_button)
	if not buy_button.disabled:
		_focus_buttons.append(buy_button)


func _add_disabled_catalog_rows() -> void:
	for item in DISABLED_CLASSIC_ITEMS:
		var item_data: Dictionary = item
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		_weapon_list.add_child(row)

		row.add_child(_cost_cell(int(item_data.get("cost", 0)), GroundfireTheme.COLOR_MUTED))

		var label := Label.new()
		label.text = "%s  Not migrated yet" % str(item_data.get("name", "Item"))
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_MUTED)
		row.add_child(label)

		var locked_button := _shop_button("Locked")
		locked_button.disabled = true
		row.add_child(locked_button)


func _disabled_shop_items() -> Array:
	return DISABLED_CLASSIC_ITEMS.duplicate(true)


func _catalog_display_name(item_name: String) -> String:
	return str(CLASSIC_SHOP_DISPLAY_NAMES.get(item_name, item_name))


func _cost_cell(cost: int, color := GroundfireTheme.COLOR_WARN) -> Label:
	var label := Label.new()
	label.text = _format_money(cost)
	label.custom_minimum_size = Vector2(84.0, 24.0)
	GroundfireTheme.apply_label(label, 14, color)
	return label


func _format_money(value: int) -> String:
	return "$%d" % value


func _shop_button(text: String, accent := false) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(116.0, 36.0)
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(button, accent)
	return button


func _remember_shop_focus(item_name: String) -> void:
	_preferred_focus_name = item_name


func _restore_shop_focus() -> void:
	for button in _focus_buttons:
		if button == null or button.disabled:
			continue
		if str(button.get_meta("shop_focus_name", "")) == _preferred_focus_name:
			button.grab_focus()
			return
	if _continue_button != null:
		_continue_button.grab_focus()


func _format_ammo(value: int) -> String:
	if value < 0:
		return "inf"
	return str(value)


func _format_pack(value: int) -> String:
	if value <= 0:
		return "-"
	return "+%d" % value


func _wire_vertical_focus(buttons: Array[Button]) -> void:
	if buttons.is_empty():
		return
	if buttons.size() == 1:
		buttons[0].focus_neighbor_top = buttons[0].get_path()
		buttons[0].focus_neighbor_bottom = buttons[0].get_path()
		buttons[0].focus_neighbor_left = buttons[0].get_path()
		buttons[0].focus_neighbor_right = buttons[0].get_path()
		return
	for index in range(buttons.size()):
		var button := buttons[index]
		var previous := buttons[wrapi(index - 1, 0, buttons.size())]
		var next := buttons[wrapi(index + 1, 0, buttons.size())]
		button.focus_neighbor_top = previous.get_path()
		button.focus_neighbor_bottom = next.get_path()
		button.focus_neighbor_left = button.get_path()
		button.focus_neighbor_right = button.get_path()
