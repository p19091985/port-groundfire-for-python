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
const CLASSIC_LIMITED_STOCK_INDICATORS := {
	"MIRV": true,
	"Missile": true,
	"Nuke": true,
}
const CLASSIC_BUY_ACTION_LABEL := "Buy"
const CLASSIC_DONE_POSITION := 10
const CLASSIC_SELECTED_ROW_COLOR := Color(1.0, 1.0, 1.0, 0.92)
const CLASSIC_BAR_CELL_SIZE := Vector2(58.0, 24.0)
const CLASSIC_BAR_FULL_WIDTH := 52.0
const CLASSIC_BAR_HEIGHT := 6.0
const CLASSIC_BAR_GAP := 2

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
	var shop_position := 0
	for item_data in _classic_catalog_rows():
		if bool(item_data.get("is_shop_item", false)):
			_add_shop_item_row(item_data, credits, input_locked, shop_position)
		else:
			_add_weapon_row(item_data, credits, input_locked, shop_position)
		shop_position += 1
	_add_disabled_catalog_rows()

	var participants: Array = _state.get("participants", [])
	for p_data in participants:
		var p: Dictionary = p_data
		var money_label := Label.new()
		money_label.text = "%s: $%d" % [str(p.get("name", "Player")), int(p.get("credits", 0))]
		GroundfireTheme.apply_label(money_label, 14, p.get("color", Color.WHITE))
		_roster_money_container.add_child(money_label)

	_continue_button.disabled = input_locked
	_continue_button.set_meta("classic_shop_position", CLASSIC_DONE_POSITION)
	_continue_button.set_meta("classic_shop_selected", _is_selected_position(CLASSIC_DONE_POSITION))
	_continue_button.add_theme_color_override(
		"font_color",
		GroundfireTheme.COLOR_WARN if _is_selected_position(CLASSIC_DONE_POSITION) else GroundfireTheme.COLOR_TEXT
	)
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


func _add_weapon_row(weapon_data: Dictionary, credits: int, input_locked := false, shop_position := 0) -> void:
	var weapon_name := str(weapon_data.get("name", "Weapon"))
	var cost := int(weapon_data.get("cost", 0))
	var pack_size := int(weapon_data.get("shop_pack", weapon_data.get("ammo", 0)))
	var stock_amount := int(weapon_data.get("stock", weapon_data.get("ammo", -1)))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	_mark_classic_row(row, shop_position)
	row.set_meta("classic_shop_stock", stock_amount)
	row.set_meta("classic_shop_pack", pack_size)
	_weapon_list.add_child(row)

	var selected := _is_selected_position(shop_position)
	row.add_child(_cost_cell(cost, GroundfireTheme.COLOR_TEXT if selected else GroundfireTheme.COLOR_WARN))

	var label := Label.new()
	label.text = _catalog_display_name(weapon_name)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_TEXT if selected else GroundfireTheme.COLOR_MUTED)
	row.add_child(label)

	var stock_indicator := _selected_limited_stock_text(weapon_name, shop_position, stock_amount)
	if stock_indicator != "":
		var stock_label := Label.new()
		stock_label.text = stock_indicator
		stock_label.custom_minimum_size = Vector2(48.0, 24.0)
		GroundfireTheme.apply_label(stock_label, 14, GroundfireTheme.COLOR_TEXT)
		row.add_child(stock_label)
	var bar_value := _selected_weapon_bar_value(weapon_name, shop_position, stock_amount)
	if bar_value > 0.0:
		row.add_child(_classic_bar_indicator(bar_value))

	var buy_button := _shop_button(CLASSIC_BUY_ACTION_LABEL)
	buy_button.disabled = input_locked or cost <= 0 or credits < cost
	buy_button.set_meta("shop_focus_name", weapon_name)
	var captured_name := weapon_name
	buy_button.focus_entered.connect(_remember_shop_focus.bind(captured_name))
	buy_button.pressed.connect(func() -> void: buy_requested.emit(captured_name))
	row.add_child(buy_button)
	if not buy_button.disabled:
		_focus_buttons.append(buy_button)


func _add_shop_item_row(item_data: Dictionary, credits: int, input_locked := false, shop_position := 0) -> void:
	var item_name := str(item_data.get("name", "Item"))
	var item_cost := int(item_data.get("cost", 0))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	_mark_classic_row(row, shop_position)
	row.set_meta("classic_shop_effect", str(item_data.get("effect", "")))
	row.set_meta("classic_shop_current", str(item_data.get("current", "")))
	_weapon_list.add_child(row)

	var selected := _is_selected_position(shop_position)
	row.add_child(_cost_cell(item_cost, GroundfireTheme.COLOR_TEXT if selected else GroundfireTheme.COLOR_WARN))

	var label := Label.new()
	label.text = _catalog_display_name(item_name)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_TEXT if selected else GroundfireTheme.COLOR_MUTED)
	row.add_child(label)

	var bar_value := _selected_shop_item_bar_value(item_name, shop_position)
	if bar_value > 0.0:
		row.add_child(_classic_bar_indicator(bar_value))

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
	for item_index in range(DISABLED_CLASSIC_ITEMS.size()):
		var item = DISABLED_CLASSIC_ITEMS[item_index]
		var item_data: Dictionary = item
		var shop_position := CLASSIC_SHOP_ORDER.find(str(item_data.get("name", "")))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		_mark_classic_row(row, shop_position)
		_weapon_list.add_child(row)

		var selected := _is_selected_position(shop_position)
		row.add_child(_cost_cell(int(item_data.get("cost", 0)), GroundfireTheme.COLOR_TEXT if selected else GroundfireTheme.COLOR_MUTED))

		var label := Label.new()
		label.text = str(item_data.get("name", "Item"))
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		GroundfireTheme.apply_label(label, 14, GroundfireTheme.COLOR_TEXT if selected else GroundfireTheme.COLOR_MUTED)
		row.add_child(label)


func _disabled_shop_items() -> Array:
	return DISABLED_CLASSIC_ITEMS.duplicate(true)


func _catalog_display_name(item_name: String) -> String:
	return str(CLASSIC_SHOP_DISPLAY_NAMES.get(item_name, item_name))


func _selected_limited_stock_text(weapon_name: String, shop_position: int, stock_amount: int) -> String:
	if not _is_selected_position(shop_position):
		return ""
	if not CLASSIC_LIMITED_STOCK_INDICATORS.has(weapon_name):
		return ""
	return "x%d" % max(0, stock_amount)


func _selected_weapon_bar_value(weapon_name: String, shop_position: int, stock_amount: int) -> float:
	if not _is_selected_position(shop_position):
		return 0.0
	if weapon_name != "Machine Gun":
		return 0.0
	return max(0.0, float(stock_amount) / 50.0)


func _selected_shop_item_bar_value(item_name: String, shop_position: int) -> float:
	if not _is_selected_position(shop_position):
		return 0.0
	if item_name != "Jump Jet":
		return 0.0
	return max(0.0, float(_state.get("fuel_reserve", 100)) / 100.0)


func _classic_bar_indicator(num_bars: float) -> VBoxContainer:
	var container := VBoxContainer.new()
	container.custom_minimum_size = CLASSIC_BAR_CELL_SIZE
	container.add_theme_constant_override("separation", CLASSIC_BAR_GAP)
	container.set_meta("classic_shop_indicator_kind", "bars")
	container.set_meta("classic_shop_bar_value", num_bars)
	var remaining := num_bars
	while remaining > 0.0:
		var fraction = min(1.0, remaining)
		var bar := ColorRect.new()
		bar.color = Color.WHITE
		bar.custom_minimum_size = Vector2(CLASSIC_BAR_FULL_WIDTH * fraction, CLASSIC_BAR_HEIGHT)
		bar.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		bar.set_meta("classic_shop_bar_fraction", fraction)
		container.add_child(bar)
		remaining -= 1.0
	return container


func _cost_cell(cost: int, color := GroundfireTheme.COLOR_WARN) -> Label:
	var label := Label.new()
	label.text = _format_money(cost)
	label.custom_minimum_size = Vector2(84.0, 24.0)
	GroundfireTheme.apply_label(label, 14, color)
	return label


func _format_money(value: int) -> String:
	return "$%d" % value


func _mark_classic_row(row: Control, shop_position: int) -> void:
	row.set_meta("classic_shop_position", shop_position)
	row.set_meta("classic_shop_selected", _is_selected_position(shop_position))
	if _is_selected_position(shop_position):
		row.modulate = CLASSIC_SELECTED_ROW_COLOR


func _is_selected_position(shop_position: int) -> bool:
	return int(_state.get("selected_position", -1)) == shop_position


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
