extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const LocalMatchScene := preload("res://scenes/local_match.tscn")
const OnlineMatchScene := preload("res://scenes/online_match.tscn")
const ServerBrowserScene := preload("res://scenes/server_browser.tscn")
const ControlSettings := preload("res://scripts/control_settings.gd")
const LOGO_TEXTURE := preload("res://assets/logo.png")
const MENU_TILE := preload("res://assets/menuback.png")
const OPTIONS_PATH := "user://groundfire_options.cfg"
const GAMEPAD_CAPTURE_CANCEL_BUTTON := JOY_BUTTON_BACK

var _content: MarginContainer
var _stack: VBoxContainer
var _screen: Control
var _capabilities: Node
var _show_fps := false
var _fullscreen := false
var _vsync_enabled := true
var _audio_enabled := true
var _master_volume := 1.0
var _screen_shake_enabled := true
var _camera_smoothing := 1.0
var _mouse_aim_enabled := true
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
	_show_placeholder("Dedicated server tooling is desktop-only and will stay hidden on web builds.")


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

	var directory_hint := Label.new()
	directory_hint.text = "Server directory URL can be set with application/config/server_directory_url."
	directory_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(directory_hint, 15, GroundfireTheme.COLOR_MUTED)
	inner.add_child(directory_hint)

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
	if config.load(OPTIONS_PATH) != OK:
		return
	_show_fps = bool(config.get_value("video", "show_fps", _show_fps))
	_fullscreen = bool(config.get_value("video", "fullscreen", _fullscreen))
	_vsync_enabled = bool(config.get_value("video", "vsync", _vsync_enabled))
	_audio_enabled = bool(config.get_value("audio", "enabled", _audio_enabled))
	_master_volume = clamp(float(config.get_value("audio", "master_volume", _master_volume)), 0.0, 1.0)
	_screen_shake_enabled = bool(config.get_value("gameplay", "screen_shake", _screen_shake_enabled))
	_camera_smoothing = clamp(float(config.get_value("gameplay", "camera_smoothing", _camera_smoothing)), 0.25, 1.75)
	_mouse_aim_enabled = bool(config.get_value("gameplay", "mouse_aim", _mouse_aim_enabled))


func _save_options() -> void:
	var config := ConfigFile.new()
	config.set_value("video", "show_fps", _show_fps)
	config.set_value("video", "fullscreen", _fullscreen)
	config.set_value("video", "vsync", _vsync_enabled)
	config.set_value("audio", "enabled", _audio_enabled)
	config.set_value("audio", "master_volume", _master_volume)
	config.set_value("gameplay", "screen_shake", _screen_shake_enabled)
	config.set_value("gameplay", "camera_smoothing", _camera_smoothing)
	config.set_value("gameplay", "mouse_aim", _mouse_aim_enabled)
	config.save(OPTIONS_PATH)


func _apply_options() -> void:
	AudioServer.set_bus_mute(0, not _audio_enabled)
	AudioServer.set_bus_volume_db(0, linear_to_db(max(_master_volume, 0.001)))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if _vsync_enabled else DisplayServer.VSYNC_DISABLED)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if _fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)


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
