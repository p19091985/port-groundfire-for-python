extends RefCounted

const KEYBOARD_1 := 0
const KEYBOARD_2 := 1
const FIRST_GAMEPAD := 2
const PLAYER_2_PREFIX := "gf_p2_"

const ACTIONS := [
	"aim_left",
	"aim_right",
	"power_up",
	"power_down",
	"fire",
	"weapon_next",
	"weapon_prev",
	"move_left",
	"move_right",
	"jump",
	"shield",
]

# SDL 1 used unusual modifier keys for Keyboard2. These numpad defaults keep the
# same independent second-keyboard contract on current Godot/desktop builds.
const KEYBOARD_2_DEFAULTS := {
	"fire": KEY_KP_ENTER,
	"weapon_next": KEY_KP_ADD,
	"weapon_prev": KEY_KP_SUBTRACT,
	"jump": KEY_KP_MULTIPLY,
	"shield": KEY_KP_5,
	"move_left": KEY_KP_4,
	"move_right": KEY_KP_6,
	"aim_left": KEY_F4,
	"aim_right": KEY_F5,
	"power_up": KEY_F2,
	"power_down": KEY_F3,
}

const GAMEPAD_BUTTONS := {
	"fire": 0,
	"weapon_next": 2,
	"weapon_prev": 1,
	"jump": 3,
	"shield": 4,
	"move_left": 6,
	"move_right": 7,
}

const GAMEPAD_AXES := {
	"aim_left": {"axis": JOY_AXIS_LEFT_X, "direction": -1.0},
	"aim_right": {"axis": JOY_AXIS_LEFT_X, "direction": 1.0},
	"power_up": {"axis": JOY_AXIS_LEFT_Y, "direction": 1.0},
	"power_down": {"axis": JOY_AXIS_LEFT_Y, "direction": -1.0},
}

const AXIS_THRESHOLD := 0.5
const Profiles := preload("res://scripts/classic_control_profiles.gd")

static var _previous_gamepad_buttons: Dictionary = {}


static func ensure_actions() -> void:
	for action in ACTIONS:
		var action_name := action_name_for_controller(KEYBOARD_2, action)
		if not InputMap.has_action(action_name):
			InputMap.add_action(action_name)
		if InputMap.action_get_events(action_name).is_empty():
			var event := InputEventKey.new()
			event.physical_keycode = int(KEYBOARD_2_DEFAULTS[action])
			InputMap.action_add_event(action_name, event)


static func action_name_for_controller(controller: int, action: String) -> String:
	if controller == KEYBOARD_2:
		return "%s%s" % [PLAYER_2_PREFIX, action]
	return "gf_%s" % action


static func gamepad_device_for_controller(controller: int) -> int:
	return Profiles.device_id(controller - FIRST_GAMEPAD)


static func command_for_controller(controller: int, include_edges := true) -> Dictionary:
	var command := {}
	for action in ACTIONS:
		command[action] = _pressed(controller, action)
	if controller <= KEYBOARD_2:
		command["fire_pressed"] = include_edges and _just_pressed(controller, "fire")
		command["weapon_next_pressed"] = include_edges and _just_pressed(controller, "weapon_next")
		command["weapon_prev_pressed"] = include_edges and _just_pressed(controller, "weapon_prev")
	else:
		for action in ["fire", "weapon_next", "weapon_prev"]:
			var key := "%d:%s" % [controller, action]
			var held := bool(command[action])
			command["%s_pressed" % action] = include_edges and held and not bool(_previous_gamepad_buttons.get(key, false))
			if include_edges:
				_previous_gamepad_buttons[key] = held
	return command


static func empty_command() -> Dictionary:
	var command := {}
	for action in ACTIONS:
		command[action] = false
	command["fire_pressed"] = false
	command["weapon_next_pressed"] = false
	command["weapon_prev_pressed"] = false
	return command


static func _pressed(controller: int, action: String) -> bool:
	if controller <= KEYBOARD_2:
		var name := action_name_for_controller(controller, action)
		if InputMap.has_action("keyboard_" + name) and Input.is_action_pressed("keyboard_" + name):
			return true
		# action_press is also used by deterministic replays. Real gamepad input
		# in the shared online action must not leak into keyboard participants.
		return Input.is_action_pressed(name) and not _gamepad_action_held(name)
	return Profiles.pressed(controller - FIRST_GAMEPAD, action)


static func _just_pressed(controller: int, action: String) -> bool:
	if controller <= KEYBOARD_2:
		var name := action_name_for_controller(controller, action)
		if InputMap.has_action("keyboard_" + name) and Input.is_action_just_pressed("keyboard_" + name):
			return true
		return Input.is_action_just_pressed(name) and not _gamepad_action_held(name)
	return false

static func _gamepad_action_held(action: String) -> bool:
	for event in InputMap.action_get_events(action):
		if not (event is InputEventJoypadButton or event is InputEventJoypadMotion):
			continue
		for device in Input.get_connected_joypads():
			if event.device >= 0 and event.device != device:
				continue
			if event is InputEventJoypadButton and Input.is_joy_button_pressed(device, event.button_index):
				return true
			if event is InputEventJoypadMotion and Input.get_joy_axis(device, event.axis) * signf(event.axis_value) >= AXIS_THRESHOLD:
				return true
	return false
