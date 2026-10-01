extends RefCounted

# Local joystick layouts mirror Python Controls: eight shared layouts, each
# device independently chooses a layout. Keyboard bindings keep the existing file.
const PATH := "user://classic_joystick_layouts.cfg"
const Settings := preload("res://scripts/control_settings.gd")
const ACTIONS := ["fire", "weapon_next", "weapon_prev", "jump", "shield", "move_left", "move_right", "aim_left", "aim_right", "power_up", "power_down"]
const DEFAULTS := [0, 2, 1, 3, 4, 6, 7, 101, 100, 102, 103]
static var layouts: Array = []
static var assignments: Array = []
static var _devices: Array = [-1, -1, -1, -1, -1, -1, -1, -1]

static func load_profiles() -> void:
	var config := ConfigFile.new()
	var has_profiles := config.load(PATH) == OK
	layouts.clear()
	assignments.clear()
	for index in range(8):
		var values := DEFAULTS.duplicate()
		for action in range(ACTIONS.size()):
			var value: Variant = config.get_value("layout_%d" % index, ACTIONS[action], DEFAULTS[action])
			if (value is int or value is float) and (int(value) == -1 or (int(value) >= 0 and int(value) < 32) or (int(value) >= 100 and int(value) < 120)):
				values[action] = int(value)
		layouts.append(values)
		var selected: Variant = config.get_value("devices", str(index), 0)
		assignments.append(clampi(int(selected), 0, 7) if selected is int or selected is float else 0)
	if not has_profiles:
		var legacy := ConfigFile.new()
		if legacy.load(Settings.SETTINGS_PATH) == OK:
			import_legacy(legacy)

static func import_legacy(config: ConfigFile) -> void:
	# Import existing bindings once; the development/online file stays intact.
	# Separate layouts prevent one device's old override from changing another.
	var has_gamepad := config.has_section("gamepad")
	for slot in range(8):
		has_gamepad = has_gamepad or config.has_section("gamepad_device_%d" % slot)
	if not has_gamepad:
		return
	for slot in range(8):
		assignments[slot] = slot
		var section := "gamepad_device_%d" % slot
		for action in range(ACTIONS.size()):
			var prefix := "gf_" + str(ACTIONS[action])
			var source := section if config.has_section_key(section, prefix + "_type") else "gamepad"
			var index := int(config.get_value(source, prefix + "_index", 0))
			match str(config.get_value(source, prefix + "_type", "")):
				"none": layouts[slot][action] = -1
				"button":
					if index >= 0 and index < 32:
						layouts[slot][action] = index
				"axis":
					if index >= 0 and index < 10:
						var direction := float(config.get_value(source, prefix + "_value", 1.0))
						layouts[slot][action] = 100 + index * 2 + (1 if direction < 0 else 0)

static func ensure_loaded() -> void:
	if layouts.is_empty():
		load_profiles()

static func save_profiles() -> Error:
	ensure_loaded()
	var config := ConfigFile.new()
	for index in range(8):
		config.set_value("devices", str(index), assignments[index])
		for action in range(ACTIONS.size()):
			config.set_value("layout_%d" % index, ACTIONS[action], layouts[index][action])
	return config.save(PATH)

static func device_id(slot: int) -> int:
	refresh_devices(Input.get_connected_joypads())
	return int(_devices[slot]) if slot >= 0 and slot < 8 else -1

static func refresh_devices(connected: Array) -> void:
	# Preserve the surviving player's slot when another controller disconnects.
	for slot in range(8):
		if not connected.has(_devices[slot]):
			_devices[slot] = -1
	for device in connected:
		if not _devices.has(device) and _devices.has(-1):
			_devices[_devices.find(-1)] = device

static func pressed(slot: int, action: String) -> bool:
	ensure_loaded()
	if slot < 0 or slot >= 8 or not ACTIONS.has(action):
		return false
	var device := device_id(slot)
	if device < 0:
		return false
	var value := int(layouts[int(assignments[slot])][ACTIONS.find(action)])
	if value < 0:
		return false
	if value < 100:
		return Input.is_joy_button_pressed(device, value)
	var axis := int((value - 100) / 2)
	var direction := 1.0 if (value - 100) % 2 == 0 else -1.0
	return Input.get_joy_axis(device, axis) * direction >= 0.5

static func binding_label(value: int) -> String:
	if value < 0:
		return "<Undefined>"
	if value < 100:
		return "Joy Button %d" % (value + 1)
	var index := value - 100
	return str(Settings.CLASSIC_AXIS_NAMES[index]) if index < Settings.CLASSIC_AXIS_NAMES.size() else "Axis %d" % index

static func capture(values: Array, index: int, value: int) -> void:
	var linked := [-1, 2, 1, -1, -1, 6, 5, 8, 7, 10, 9]
	var other := int(linked[index])
	if other >= 0:
		if value >= 100:
			values[other] = value + 1 if value % 2 == 0 else value - 1
		elif int(values[index]) >= 100:
			values[other] = -1
	values[index] = value
