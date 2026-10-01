extends Control

const ButtonScript := preload("res://scripts/classic_button.gd")
const LabelScript := preload("res://scripts/classic_label.gd")
const Selector := preload("res://scripts/classic_selector.gd")
const ThemeScript := preload("res://scripts/groundfire_theme.gd")
const Settings := preload("res://scripts/control_settings.gd")
const Profiles := preload("res://scripts/classic_control_profiles.gd")
const Router := preload("res://scripts/player_input_router.gd")
const FontAtlas := preload("res://scripts/classic_font.gd")

signal back_requested
signal options_applied(resolution: int, fullscreen: bool)

var resolution := 2
var fullscreen := false
var resolutions: Array = []
var screen := "options"
var layout := 0
var waiting := -1
var values: Array = []
var _geometry: Array = []
var _focus: Array[Control] = []
var _icons: Array = []
var roster: Array = []
var rounds_index := 0
var _start_match := Callable()
var _setup_back := Callable()

func _ready() -> void:
	resized.connect(_arrange)
	Input.joy_connection_changed.connect(_controller_changed)
	Profiles.ensure_loaded()
	show_options()

func _controller_changed(_device: int, _connected: bool) -> void:
	if screen == "controllers":
		show_controllers()

func back_from_controllers() -> void:
	Profiles.save_profiles()
	show_options()

func _clear(next_screen: String) -> void:
	screen = next_screen
	waiting = -1
	_geometry.clear()
	_focus.clear()
	_icons.clear()
	for child in get_children():
		remove_child(child)
		child.queue_free()

func _place(node: Control, rect: Rect2, font_height := 0.0) -> Control:
	add_child(node)
	_geometry.append({"node": node, "rect": rect, "font": font_height})
	_arrange()
	return node

func _arrange() -> void:
	var scale := size / Vector2(20, 15)
	for item in _icons:
		var points := PackedVector2Array()
		for point in item.points:
			points.append(Vector2(point.x + 10, 7.5 - point.y) * scale)
		item.node.polygon = points
	for item in _geometry:
		var node: Control = item.node
		var rect: Rect2 = item.rect
		node.position = Vector2(rect.position.x + 10, 7.5 - rect.position.y) * scale
		node.size = rect.size * scale
		if float(item.font) > 0:
			# Python's scale_len uses viewport width for both glyph dimensions;
			# baselines and hit boxes still use the separate vertical projection.
			var font_size := maxf(1, float(item.font) * scale.x)
			if node.has_method("set_font_size"):
				node.set_font_size(font_size)
			elif node.has_method("set_classic_draw_size"):
				node.set_classic_draw_size(font_size)
			else:
				node.add_theme_font_size_override("font_size", font_size)

func _panel(left: float, top: float, width: float, height: float, color := Color(0, 0, 0, 0.502)) -> void:
	var panel := ColorRect.new()
	panel.color = color
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_place(panel, Rect2(left, top, width, height))

func _label(text: String, x: float, y: float, font := 0.6, color := Color.CYAN, width := 14.0) -> Label:
	var label := LabelScript.new()
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.set_classic_font_color(color)
	label.classic_shadow = color == Color.WHITE
	label.set_classic_spacing_ratio((font - 0.1) / font)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_place(label, Rect2(x - width / 2, y + font, width, font), font)
	return label

func _button(text: String, x: float, y: float, callback: Callable, font := 0.7, width := 8.0) -> Button:
	var button := ButtonScript.new()
	button.text = text
	button.set_classic_spacing_ratio((font - 0.1) / font)
	button.set_classic_font_colours(Color.WHITE, Color.YELLOW, Color(0.1, 0.1, 0.1))
	for state in ["normal", "hover", "pressed", "focus", "disabled"]:
		button.add_theme_stylebox_override(state, StyleBoxEmpty.new())
	button.pressed.connect(callback)
	width = FontAtlas.measure(text, font * 100, (font - 0.1) / font) / 100
	_place(button, Rect2(x - width / 2, y + font / 2, width, font), font)
	_focus.append(button)
	return button

func _selector(items: Array, selected: int, x: float, y: float, width: float, callback: Callable, font := 0.6) -> Control:
	var selector := Selector.new()
	selector.classic_geometry = true
	selector.classic_spacing_ratio = (font - 0.1) / font
	for item in items:
		selector.add_item(str(item))
	selector.select(selected)
	selector.item_selected.connect(callback)
	_place(selector, Rect2(x - width / 2 - font, y + font / 2, width + 2 * font, font), font)
	_focus.append(selector)
	return selector

func _wire_focus() -> void:
	_focus = _focus.filter(func(control: Control) -> bool: return control.focus_mode != Control.FOCUS_NONE and not (control is Button and control.disabled))
	for index in range(_focus.size()):
		var control := _focus[index]
		control.focus_neighbor_top = _focus[wrapi(index - 1, 0, _focus.size())].get_path()
		control.focus_neighbor_bottom = _focus[wrapi(index + 1, 0, _focus.size())].get_path()
	if not _focus.is_empty():
		_focus_current.call_deferred()

func _focus_current() -> void:
	if is_inside_tree() and not _focus.is_empty() and is_instance_valid(_focus[0]) and _focus[0].is_inside_tree():
		_focus[0].grab_focus()

func _logo() -> void:
	var logo := TextureRect.new()
	logo.texture = preload("res://assets/logo.png")
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_place(logo, Rect2(-8, 4, 16, 4))

func show_main(actions: Array) -> void:
	_clear("main")
	_logo()
	_label("0.25 (Python Port)", 0, 0, 0.4, Color.WHITE).set_classic_spacing_ratio(0.875)
	_label("www.groundfire.net", 0, -0.5, 0.4, Color.WHITE).set_classic_spacing_ratio(0.875)
	_label("Copyright Tom Russell 2004", 0, -2.5, 0.4, Color.WHITE).set_classic_spacing_ratio(0.875)
	_label("All Rights Reserved", 0, -2.9, 0.4, Color.WHITE).set_classic_spacing_ratio(0.875)
	_panel(-7, -3.05, 14, 4.05)
	for index in range(actions.size()):
		_panel(-4, -3.2 - index, 8, 0.8, Color8(153, 76, 0))
		_button(actions[index][0], 0, -3.6 - index, actions[index][1])
	_wire_focus()

func show_quit(yes: Callable, no: Callable) -> void:
	_clear("quit")
	_logo()
	_panel(-7, -3.4, 14, 3.2)
	_label("Are you sure?", 0, -4.35, 0.7, Color.WHITE)
	for index in range(2):
		_panel(-4, -4.6 - index, 8, 0.8, Color8(153, 76, 0, 128))
	_button("Yes", 0, -5, yes)
	_button("No", 0, -6, no)
	_wire_focus()

func show_setup(colors: Array, start: Callable, back: Callable) -> void:
	roster.clear()
	for index in range(8):
		roster.append({"slot": index, "enabled": false, "name": "Player %d" % (index + 1), "color": colors[index], "kind": "human", "controller": 0})
	_start_match = start
	_setup_back = back
	rounds_index = 0
	_draw_setup()

func _draw_setup() -> void:
	_clear("setup")
	_label("Select Players", 0, 6.5, 0.6, Color.WHITE)
	_label("Add a player by clicking on a '+' icon or press the 'Fire' Button on any Controller", 0, 5.5, 0.4, Color.WHITE, 20).set_classic_spacing_ratio(0.875)
	_panel(-9, 4.7, 18, 7.3)
	_panel(-7, -3.4, 14, 3.2)
	for index in range(3):
		_panel(-4, -3.6 - index, 8, 0.8, Color8(153, 76, 0, 128))
	for header in [["Add/Remove", -8.0, 4.3], ["Player", -8.0, 4.0], ["Name", -4.0, 4.1], ["Controlled by", 1.6, 4.1], ["Controller", 6.3, 4.1]]:
		_label(header[0], header[1], header[2], 0.3).set_classic_spacing_ratio(0.25 / 0.3)
	for index in range(8):
		var entry: Dictionary = roster[index]
		var y := 3.5 - index * 0.8
		if entry.enabled:
			_panel(-8.8, y + 0.3, 17.6, 0.6, Color8(153, 76, 0, 128))
		for remove in [false, true]:
			var toggle := TextureButton.new()
			toggle.texture_normal = preload("res://assets/removebutton.png") if remove else preload("res://assets/addbutton.png")
			toggle.ignore_texture_size = true
			toggle.stretch_mode = TextureButton.STRETCH_SCALE
			toggle.disabled = not entry.enabled if remove else entry.enabled
			toggle.modulate.a = 0.2 if toggle.disabled else 1.0
			toggle.pressed.connect(func() -> void: _toggle_player(index, not remove))
			_place(toggle, Rect2(-8.1 if remove else -8.8, y + 0.3, 0.6, 0.6))
		var color: Color = entry.color
		var icon := Polygon2D.new()
		icon.polygon = PackedVector2Array([Vector2(-7, y + 0.2), Vector2(-6.6, y + 0.2), Vector2(-6.4, y - 0.2), Vector2(-7.2, y - 0.2)])
		_icons.append({"node": icon, "points": icon.polygon})
		icon.color = color if entry.enabled else Color8(int(color.r8 / 4), int(color.g8 / 4), int(color.b8 / 4))
		add_child(icon)
		_arrange()
		if entry.enabled:
			_label(entry.name, -4.0, y - 0.2, 0.5, Color.WHITE, 4).classic_shadow = false
		var kind := _selector(["Human", "Computer"], 0 if entry.kind == "human" else 1, 1.6, y, 3, func(selected: int) -> void:
			roster[index].kind = "human" if selected == 0 else "computer"
			_select_available_controller(index)
			_draw_setup()
		, 0.5)
		kind.set_disabled(not entry.enabled)
		var controller := _selector(["Keyboard1", "Keyboard2", "Joystick1", "Joystick2", "Joystick3", "Joystick4", "Joystick5", "Joystick6", "Joystick7", "Joystick8"], int(entry.controller), 6.4, y, 3.2, func(selected: int) -> void:
			var direction := -1 if selected == wrapi(int(roster[index].controller) - 1, 0, 10) else 1
			roster[index].controller = selected
			_select_available_controller(index, direction)
			_draw_setup()
		, 0.5)
		controller.set_disabled(not entry.enabled or entry.kind != "human")
	_label("Rounds :", -2, -4.35, 0.7, Color.WHITE)
	_selector(["5", "10", "15", "20", "25", "30", "35", "40", "45", "50"], rounds_index, 2, -4, 2, func(index: int) -> void: rounds_index = index, 0.7)
	var start_button := _button("Start!", 0, -5, func() -> void:
		var players: Array[Dictionary] = []
		for entry in roster:
			if entry.enabled:
				var player: Dictionary = entry.duplicate()
				if player.kind != "human":
					player.controller = -1
				players.append(player)
		_start_match.call((rounds_index + 1) * 5, players)
	)
	start_button.disabled = roster.filter(func(entry: Dictionary) -> bool: return entry.enabled).size() < 2
	_button("Back", 0, -6, _setup_back)
	_wire_focus()

func _toggle_player(index: int, enabled: bool) -> void:
	roster[index].enabled = enabled
	if enabled:
		_select_available_controller(index)
	_draw_setup()

func _select_available_controller(index: int, direction := 1) -> void:
	if roster[index].kind != "human":
		return
	for attempt in range(10):
		var conflict := false
		for other in range(8):
			if other != index and roster[other].enabled and roster[other].kind == "human" and roster[other].controller == roster[index].controller:
				conflict = true
		if not conflict:
			return
		roster[index].controller = wrapi(int(roster[index].controller) + direction, 0, 10)

func _process(_delta: float) -> void:
	if screen != "setup":
		return
	for controller in range(10):
		if not bool(Router.command_for_controller(controller, false).fire):
			continue
		if roster.any(func(entry: Dictionary) -> bool: return entry.enabled and entry.kind == "human" and entry.controller == controller):
			continue
		for entry in roster:
			if not entry.enabled:
				entry.enabled = true
				entry.kind = "human"
				entry.controller = controller
				_draw_setup()
				break

func show_options() -> void:
	_clear("options")
	_panel(-7, 3, 14, 6)
	_panel(-7, -4.4, 14, 2.2)
	for y in [1.4, 0.4, -0.6]:
		_panel(-6, y, 12, 0.8, Color(0.6, 0.298, 0, 0.502))
	for y in [-4.6, -5.6]:
		_panel(-4, y, 8, 0.8, Color(0.6, 0.298, 0, 0.502))
	_label("Options", 0, 6.5, 0.6, Color.WHITE)
	_label("Resolution:", -3, 0.7)
	_label("Screen Mode:", -3, -0.3)
	var web := OS.has_feature("web")
	var selector := _selector(["Browser size"] if web else resolutions, 0 if web else resolution, 3, 1, 4, func(index: int) -> void: resolution = index)
	selector.name = "Resolution"
	selector.show_disabled_value = web
	selector.set_disabled(web)
	_selector(["Fullscreen", "Windowed"], 0 if fullscreen else 1, 3, 0, 4, func(index: int) -> void: fullscreen = index == 0).name = "ScreenMode"
	_button("Set Controls", 0, -1, show_controllers, 0.6)
	_button("Apply", 0, -5, func() -> void: options_applied.emit(resolution, fullscreen))
	_button("Back", 0, -6, func() -> void: back_requested.emit())
	_wire_focus()

func show_controllers() -> void:
	_clear("controllers")
	_panel(-7, 6, 14, 2.8)
	_panel(-7, 2.8, 14, 8)
	_panel(-7, -5.4, 14, 1.2)
	_label("Set Controls", 0, 6.5, 0.6, Color.WHITE)
	_label("Change", 2, 5.4, 0.4, Color.GRAY)
	_label("keyboard layout", 2, 5.0, 0.4, Color.GRAY)
	for index in range(2):
		_panel(-6.4, 4.9 - index * 0.8, 12.8, 0.7, Color(0.6, 0.298, 0, 0.502))
		_label("Keyboard %d" % (index + 1), -2, 4.3 - index * 0.8)
		_button("Edit Layout", 2, 4.6 - index * 0.8, edit_layout.bind(index), 0.5, 4)
	_label("Joystick", 0, 2.2, 0.4, Color.GRAY)
	_label("layout number", 0, 1.8, 0.4, Color.GRAY)
	_label("Change", 4.5, 2.2, 0.4, Color.GRAY)
	_label("joystick layout", 4.5, 1.8, 0.4, Color.GRAY)
	for index in range(8):
		var y := 1.45 - index * 0.8
		_panel(-6.4, y, 12.8, 0.7, Color(0.6, 0.298, 0, 0.502))
		var connected := Profiles.device_id(index) >= 0
		_label("Joystick %d" % (index + 1), -4.6, 0.8 - index * 0.8, 0.5, Color.CYAN if connected else Color.GRAY)
		if connected:
			_selector(["Layout 1", "Layout 2", "Layout 3", "Layout 4", "Layout 5", "Layout 6", "Layout 7", "Layout 8"], Profiles.assignments[index], 0, 1.1 - index * 0.8, 3.3, func(selected: int) -> void: Profiles.assignments[index] = selected, 0.5)
			_button("Edit Layout", 4.5, 1.1 - index * 0.8, func() -> void: edit_layout(2 + int(Profiles.assignments[index])), 0.5, 3)
		else:
			_label("<<Not Connected>>", 2, 0.8 - index * 0.8, 0.5, Color.GRAY)
	_panel(-4, -5.6, 8, 0.8, Color(0.6, 0.298, 0, 0.502))
	_button("Back", 0, -6, back_from_controllers)
	_wire_focus()

func _action(index: int) -> String:
	return ("gf_p2_" if layout == 1 else "gf_") + str(Profiles.ACTIONS[index])

func edit_layout(index: int) -> void:
	layout = index
	values = []
	if layout >= 2:
		values = Profiles.layouts[layout - 2].duplicate()
	else:
		for action in range(11):
			var key := int(Settings.DEFAULT_BINDINGS[_action(action)])
			for event in InputMap.action_get_events(_action(action)):
				if event is InputEventKey:
					key = int(event.keycode if event.keycode else event.physical_keycode)
			values.append(key)
	_show_layout()

func _show_layout() -> void:
	_clear("layout")
	_panel(-7, 6, 14, 10)
	_panel(-7, -4.4, 14, 2.2)
	_label("Editing %s Layout %d" % ["Keyboard" if layout < 2 else "Joystick", layout + 1 if layout < 2 else layout - 1], 0, 6.5, 0.6, Color.WHITE)
	for index in range(11):
		var y := 5.0 - index * 0.8
		_panel(-6, y + 0.3, 6, 0.7, Color(0.6, 0.298, 0, 0.502))
		_panel(0.1, y + 0.3, 5.9, 0.7, Color(0.6, 0.298, 0, 0.502))
		_button(Settings.display_name("gf_" + str(Profiles.ACTIONS[index])), -3, y, _begin_capture.bind(index), 0.5, 6)
		var text := OS.get_keycode_string(int(values[index])).to_lower() if layout < 2 else Profiles.binding_label(int(values[index]))
		_label(text, 3, y - 0.3, 0.5)
	_panel(-4, -4.6, 8, 0.8, Color(0.6, 0.298, 0, 0.502))
	_panel(-4, -5.6, 8, 0.8, Color(0.6, 0.298, 0, 0.502))
	_button("Reset To Defaults", 0, -5, func() -> void:
		for index in range(11):
			values[index] = Settings.DEFAULT_BINDINGS[_action(index)] if layout < 2 else Profiles.DEFAULTS[index]
		_show_layout()
	)
	_button("Done", 0, -6, func() -> void:
		if layout < 2:
			for index in range(11):
				Settings.save_key_binding(_action(index), int(values[index]))
		else:
			Profiles.layouts[layout - 2] = values.duplicate()
		show_controllers()
	)
	_wire_focus()

func _begin_capture(index: int) -> void:
	waiting = index
	for control in _focus:
		if control is Button:
			control.disabled = true
	_label("Press Button for '%s'" % Settings.display_name("gf_" + str(Profiles.ACTIONS[index])), 0, -4, 0.6, Color.GRAY).classic_shadow = true

func _input(event: InputEvent) -> void:
	if waiting < 0:
		return
	var captured := false
	if layout < 2 and event is InputEventKey and event.pressed and not event.echo:
		values[waiting] = event.keycode
		captured = true
	elif layout >= 2 and event is InputEventJoypadButton and event.pressed:
		Profiles.capture(values, waiting, event.button_index)
		captured = true
	elif layout >= 2 and event is InputEventJoypadMotion and absf(event.axis_value) > 0.5:
		Profiles.capture(values, waiting, 100 + event.axis * 2 + (1 if event.axis_value < 0 else 0))
		captured = true
	if captured:
		get_viewport().set_input_as_handled()
		_show_layout()
