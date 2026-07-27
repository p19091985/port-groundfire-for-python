extends RefCounted

const SETTINGS_PATH := "user://groundfire_controls.cfg"
const CAPTURE_AXIS_THRESHOLD := 0.55
const GAMEPAD_PROFILE_SECTION := "gamepad_profile"
const GAMEPAD_PROFILE_DEVICE_KEY := "device_id"
const GAMEPAD_ALL_DEVICES := -1
const CLASSIC_UNDEFINED_LABEL := "<Undefined>"

const DEFAULT_BINDINGS := {
	"gf_aim_left": KEY_A,
	"gf_aim_right": KEY_D,
	"gf_power_up": KEY_W,
	"gf_power_down": KEY_S,
	"gf_fire": KEY_SPACE,
	"gf_weapon_next": KEY_O,
	"gf_weapon_prev": KEY_U,
	"gf_pause": KEY_ESCAPE,
	"gf_move_left": KEY_J,
	"gf_move_right": KEY_L,
	"gf_jump": KEY_I,
	"gf_shield": KEY_K,
}

const CLASSIC_ACTION_DISPLAY_NAMES := {
	"gf_fire": "Fire Weapon",
	"gf_weapon_next": "Change Weapon Up",
	"gf_weapon_prev": "Change Weapon Down",
	"gf_jump": "Use Jump Jets",
	"gf_shield": "Use Shield",
	"gf_move_left": "Move Tank Left",
	"gf_move_right": "Move Tank Right",
	"gf_aim_left": "Rotate Gun Left",
	"gf_aim_right": "Rotate Gun Right",
	"gf_power_up": "Increase Gun Power",
	"gf_power_down": "Decrease Gun Power",
	"gf_pause": "Pause",
}

const CLASSIC_AXIS_NAMES := [
	"Joystick/Pad Right",
	"Joystick/Pad Left",
	"Joystick/Pad Up",
	"Joystick/Pad Down",
	"Axis 3 (-)",
	"Axis 3 (+)",
	"Axis 4 (-)",
	"Axis 4 (+)",
]

const ACTION_ORDER := [
	"gf_fire",
	"gf_weapon_next",
	"gf_weapon_prev",
	"gf_jump",
	"gf_shield",
	"gf_move_left",
	"gf_move_right",
	"gf_aim_left",
	"gf_aim_right",
	"gf_power_up",
	"gf_power_down",
	"gf_pause",
]

const CLASSIC_REBIND_ACTION_ORDER := [
	"gf_fire",
	"gf_weapon_next",
	"gf_weapon_prev",
	"gf_jump",
	"gf_shield",
	"gf_move_left",
	"gf_move_right",
	"gf_aim_left",
	"gf_aim_right",
	"gf_power_up",
	"gf_power_down",
]

const CLASSIC_LINKED_ACTIONS := {
	"gf_weapon_next": "gf_weapon_prev",
	"gf_weapon_prev": "gf_weapon_next",
	"gf_move_left": "gf_move_right",
	"gf_move_right": "gf_move_left",
	"gf_aim_left": "gf_aim_right",
	"gf_aim_right": "gf_aim_left",
	"gf_power_up": "gf_power_down",
	"gf_power_down": "gf_power_up",
}

const DEFAULT_GAMEPAD_BUTTONS := {
	"gf_fire": 0,
	"gf_weapon_next": 2,
	"gf_weapon_prev": 1,
	"gf_pause": JOY_BUTTON_START,
	"gf_jump": 3,
	"gf_shield": 4,
	"gf_move_left": 6,
	"gf_move_right": 7,
}

const DEFAULT_GAMEPAD_AXES := {
	"gf_aim_left": {"axis": JOY_AXIS_LEFT_X, "value": -1.0},
	"gf_aim_right": {"axis": JOY_AXIS_LEFT_X, "value": 1.0},
	"gf_power_up": {"axis": JOY_AXIS_LEFT_Y, "value": 1.0},
	"gf_power_down": {"axis": JOY_AXIS_LEFT_Y, "value": -1.0},
}


static func apply_saved_bindings() -> void:
	var config := ConfigFile.new()
	var has_config := config.load(SETTINGS_PATH) == OK
	for action_name in ACTION_ORDER:
		var keycode: int = int(DEFAULT_BINDINGS[action_name])
		if has_config:
			keycode = int(config.get_value("bindings", action_name, keycode))
		_apply_action_binding(str(action_name), keycode, config)


static func save_key_binding(action_name: String, keycode: int) -> void:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	config.set_value("bindings", action_name, keycode)
	config.save(SETTINGS_PATH)
	_apply_action_binding(action_name, keycode, config)


static func save_gamepad_button_binding(action_name: String, button_index: int) -> void:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	var section := _gamepad_section(config)
	var had_axis_binding := _saved_or_default_gamepad_binding_is_axis(config, section, action_name)
	var linked_action := ""
	if had_axis_binding and CLASSIC_LINKED_ACTIONS.has(action_name):
		linked_action = str(CLASSIC_LINKED_ACTIONS[action_name])
		_set_saved_gamepad_none(config, section, linked_action)
	_set_saved_gamepad_button(config, section, action_name, button_index)
	config.save(SETTINGS_PATH)
	_apply_action_binding(action_name, _saved_keycode(config, action_name), config)
	if not linked_action.is_empty():
		_apply_action_binding(linked_action, _saved_keycode(config, linked_action), config)


static func save_gamepad_axis_binding(action_name: String, axis: int, axis_value: float) -> void:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	var section := _gamepad_section(config)
	var axis_direction := -1.0 if axis_value < 0.0 else 1.0
	var linked_action := ""
	_set_saved_gamepad_axis(config, section, action_name, axis, axis_direction)
	if CLASSIC_LINKED_ACTIONS.has(action_name):
		linked_action = str(CLASSIC_LINKED_ACTIONS[action_name])
		_set_saved_gamepad_axis(config, section, linked_action, axis, -axis_direction)
	config.save(SETTINGS_PATH)
	_apply_action_binding(action_name, _saved_keycode(config, action_name), config)
	if not linked_action.is_empty():
		_apply_action_binding(linked_action, _saved_keycode(config, linked_action), config)


static func clear_gamepad_binding(action_name: String) -> void:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	var section := _gamepad_section(config)
	_set_saved_gamepad_none(config, section, action_name)
	config.save(SETTINGS_PATH)
	_apply_action_binding(action_name, _saved_keycode(config, action_name), config)


static func reset_defaults() -> void:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	for action_name in ACTION_ORDER:
		config.set_value("bindings", action_name, int(DEFAULT_BINDINGS[action_name]))
		_apply_action_binding(str(action_name), int(DEFAULT_BINDINGS[action_name]), config)
	config.save(SETTINGS_PATH)


static func reset_gamepad_defaults() -> void:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	var section := _gamepad_section(config)
	for action_name in ACTION_ORDER:
		for suffix in ["type", "index", "value"]:
			var key := "%s_%s" % [action_name, suffix]
			if config.has_section_key(section, key):
				config.erase_section_key(section, key)
	config.save(SETTINGS_PATH)
	apply_saved_bindings()


static func active_gamepad_device() -> int:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	return _active_gamepad_device(config)


static func set_active_gamepad_device(device_id: int) -> void:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	config.set_value(GAMEPAD_PROFILE_SECTION, GAMEPAD_PROFILE_DEVICE_KEY, device_id)
	config.save(SETTINGS_PATH)
	apply_saved_bindings()


static func gamepad_profiles() -> Array[Dictionary]:
	var profiles: Array[Dictionary] = [{
		"device_id": GAMEPAD_ALL_DEVICES,
		"label": "All Gamepads",
	}]
	for device_id in Input.get_connected_joypads():
		profiles.append({
			"device_id": int(device_id),
			"label": _gamepad_device_label(int(device_id)),
		})
	return profiles


static func binding_labels() -> Array[String]:
	var labels: Array[String] = []
	for action_name in ACTION_ORDER:
		labels.append("%s: %s" % [display_name(str(action_name)), key_label(str(action_name))])
	return labels


static func action_names() -> Array[String]:
	var actions: Array[String] = []
	for action_name in CLASSIC_REBIND_ACTION_ORDER:
		actions.append(str(action_name))
	return actions


static func display_name(action_name: String) -> String:
	if CLASSIC_ACTION_DISPLAY_NAMES.has(action_name):
		return str(CLASSIC_ACTION_DISPLAY_NAMES[action_name])
	return action_name.trim_prefix("gf_").replace("_", " ").capitalize()


static func key_label(action_name: String) -> String:
	var events := InputMap.action_get_events(action_name)
	for event in events:
		if event is InputEventKey:
			return OS.get_keycode_string(event.keycode)
	return CLASSIC_UNDEFINED_LABEL


static func gamepad_label(action_name: String) -> String:
	var labels: Array[String] = []
	for event in InputMap.action_get_events(action_name):
		if event is InputEventJoypadButton:
			labels.append(_gamepad_button_label(event.button_index))
		elif event is InputEventJoypadMotion:
			labels.append(_gamepad_axis_label(event.axis, event.axis_value))
	return ", ".join(labels) if not labels.is_empty() else CLASSIC_UNDEFINED_LABEL


static func conflict_labels() -> Array[String]:
	var conflicts: Array[String] = []
	var key_owners: Dictionary = {}
	var gamepad_owners: Dictionary = {}
	for action_name in action_names():
		for event in InputMap.action_get_events(action_name):
			if event is InputEventKey:
				var keycode: int = event.keycode
				if key_owners.has(keycode):
					conflicts.append("%s / %s use %s" % [
						display_name(str(key_owners[keycode])),
						display_name(action_name),
						OS.get_keycode_string(keycode),
					])
				else:
					key_owners[keycode] = action_name
			elif event is InputEventJoypadButton:
				var button_key := "button:%d" % event.button_index
				if gamepad_owners.has(button_key):
					conflicts.append("%s / %s use %s" % [
						display_name(str(gamepad_owners[button_key])),
						display_name(action_name),
						_gamepad_button_label(event.button_index),
					])
				else:
					gamepad_owners[button_key] = action_name
			elif event is InputEventJoypadMotion:
				var axis_direction := "+" if event.axis_value > 0.0 else "-"
				var axis_key := "axis:%d:%s" % [event.axis, axis_direction]
				if gamepad_owners.has(axis_key):
					conflicts.append("%s / %s use %s" % [
						display_name(str(gamepad_owners[axis_key])),
						display_name(action_name),
						_gamepad_axis_label(event.axis, event.axis_value),
					])
				else:
					gamepad_owners[axis_key] = action_name
	return conflicts


static func _apply_key_binding(action_name: String, keycode: int) -> void:
	if not InputMap.has_action(action_name):
		InputMap.add_action(action_name)
	InputMap.action_erase_events(action_name)
	var event := InputEventKey.new()
	event.keycode = keycode
	InputMap.action_add_event(action_name, event)


static func _apply_action_binding(action_name: String, keycode: int, config: ConfigFile) -> void:
	_apply_key_binding(action_name, keycode)
	if _apply_saved_gamepad_binding(action_name, config):
		return
	_apply_default_gamepad_binding(action_name)


static func _apply_default_gamepad_binding(action_name: String) -> void:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	var device_id := _active_gamepad_device(config)
	if DEFAULT_GAMEPAD_BUTTONS.has(action_name):
		var button := InputEventJoypadButton.new()
		button.button_index = int(DEFAULT_GAMEPAD_BUTTONS[action_name])
		if device_id >= 0:
			button.device = device_id
		InputMap.action_add_event(action_name, button)
	if DEFAULT_GAMEPAD_AXES.has(action_name):
		var axis_data: Dictionary = DEFAULT_GAMEPAD_AXES[action_name]
		var axis := InputEventJoypadMotion.new()
		axis.axis = int(axis_data["axis"])
		axis.axis_value = float(axis_data["value"])
		if device_id >= 0:
			axis.device = device_id
		InputMap.action_add_event(action_name, axis)


static func _set_saved_gamepad_button(config: ConfigFile, section: String, action_name: String, button_index: int) -> void:
	config.set_value(section, "%s_type" % action_name, "button")
	config.set_value(section, "%s_index" % action_name, button_index)
	config.set_value(section, "%s_value" % action_name, 0.0)


static func _set_saved_gamepad_axis(config: ConfigFile, section: String, action_name: String, axis: int, axis_value: float) -> void:
	config.set_value(section, "%s_type" % action_name, "axis")
	config.set_value(section, "%s_index" % action_name, axis)
	config.set_value(section, "%s_value" % action_name, axis_value)


static func _set_saved_gamepad_none(config: ConfigFile, section: String, action_name: String) -> void:
	config.set_value(section, "%s_type" % action_name, "none")
	config.set_value(section, "%s_index" % action_name, 0)
	config.set_value(section, "%s_value" % action_name, 0.0)


static func _saved_or_default_gamepad_binding_is_axis(config: ConfigFile, section: String, action_name: String) -> bool:
	var type_key := "%s_type" % action_name
	if config.has_section_key(section, type_key):
		return str(config.get_value(section, type_key, "")) == "axis"
	if DEFAULT_GAMEPAD_AXES.has(action_name):
		return true
	for event in InputMap.action_get_events(action_name):
		if event is InputEventJoypadMotion:
			return true
	return false


static func _apply_saved_gamepad_binding(action_name: String, config: ConfigFile) -> bool:
	var section := _gamepad_section(config)
	var type_key := "%s_type" % action_name
	var index_key := "%s_index" % action_name
	var value_key := "%s_value" % action_name
	if not config.has_section_key(section, type_key):
		return false
	var device_id := _active_gamepad_device(config)
	var binding_type := str(config.get_value(section, type_key, ""))
	if binding_type == "none":
		return true
	if binding_type == "button":
		var button := InputEventJoypadButton.new()
		button.button_index = int(config.get_value(section, index_key, 0))
		if device_id >= 0:
			button.device = device_id
		InputMap.action_add_event(action_name, button)
		return true
	if binding_type == "axis":
		var axis := InputEventJoypadMotion.new()
		axis.axis = int(config.get_value(section, index_key, 0))
		axis.axis_value = float(config.get_value(section, value_key, 1.0))
		if device_id >= 0:
			axis.device = device_id
		InputMap.action_add_event(action_name, axis)
		return true
	return false


static func _saved_keycode(config: ConfigFile, action_name: String) -> int:
	return int(config.get_value("bindings", action_name, int(DEFAULT_BINDINGS.get(action_name, 0))))


static func _active_gamepad_device(config: ConfigFile) -> int:
	return int(config.get_value(GAMEPAD_PROFILE_SECTION, GAMEPAD_PROFILE_DEVICE_KEY, GAMEPAD_ALL_DEVICES))


static func _gamepad_section(config: ConfigFile) -> String:
	var device_id := _active_gamepad_device(config)
	if device_id >= 0:
		return "gamepad_device_%d" % device_id
	return "gamepad"


static func _gamepad_device_label(device_id: int) -> String:
	var name := Input.get_joy_name(device_id)
	if name.is_empty():
		name = "Gamepad %d" % device_id
	return "%s #%d" % [name, device_id]


static func _gamepad_button_label(button_index: int) -> String:
	return "Joy Button %d" % (button_index + 1)


static func _gamepad_axis_label(axis: int, axis_value: float) -> String:
	var axis_name_index := axis * 2
	if axis_value < 0.0:
		axis_name_index += 1
	if axis_name_index >= 0 and axis_name_index < CLASSIC_AXIS_NAMES.size():
		return str(CLASSIC_AXIS_NAMES[axis_name_index])
	return "Axis %d" % axis_name_index
