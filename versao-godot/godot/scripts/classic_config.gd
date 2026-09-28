extends RefCounted

const OPTIONS_PATH := "res://data/classic/options.ini"
const CONTROLS_PATH := "res://data/classic/controls.ini"


static func load_options() -> Dictionary:
	var config := _read_classic_ini(OPTIONS_PATH)
	assert(not config.is_empty(), "Classic options.ini must be available in the Godot data bundle")
	return {
		"terrain": {
			"slices": int(_value(config, "Terrain", "Slices", 500)),
			"width": float(_value(config, "Terrain", "Width", 11.0)),
			"fall_pause": float(_value(config, "Terrain", "FallPause", 0.2)),
			"fall_acceleration": float(_value(config, "Terrain", "FallAcceleration", 5.0)),
		},
		"tank": {
			"gravity": float(_value(config, "Tank", "Gravity", 5.0)),
			"move_speed": float(_value(config, "Tank", "MoveSpeed", 0.2)),
			"fuel_usage_rate": float(_value(config, "Tank", "FuelUsageRate", 0.2)),
		},
		"weapons": {
			"Shell": _weapon(config, "Shell", "", 40.0, 4.0),
			"Machine Gun": _weapon(config, "MachineGun", "MachineGun", 2.0, 0.1),
			"MIRV": _weapon(config, "Mirv", "Mirvs", 30.0, 7.5),
			"Missile": _weapon(config, "Missile", "Missiles", 40.0, 5.0),
			"Nuke": _weapon(config, "Nuke", "Nukes", 90.0, 10.0),
		},
	}


static func _weapon(config: Dictionary, section: String, price_key: String, damage: float, cooldown: float) -> Dictionary:
	var result := {
		"damage": float(_value(config, section, "Damage", damage)),
		"cooldown": float(_value(config, section, "CooldownTime", cooldown)),
	}
	if not price_key.is_empty():
		result["cost"] = int(_value(config, "Price", price_key, 50))
	for key in ["BlastSize", "Fuel", "SteerSensitivity", "Speed", "Fragments", "Spread"]:
		if Dictionary(config.get(section, {})).has(key):
			result[key.to_snake_case()] = _value(config, section, key, 0)
	return result


static func _value(config: Dictionary, section: String, key: String, fallback: Variant) -> Variant:
	return Dictionary(config.get(section, {})).get(key, fallback)


static func _read_classic_ini(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var result: Dictionary = {}
	var section := ""
	while not file.eof_reached():
		var line := file.get_line().strip_edges()
		if line.is_empty() or line.begins_with(";") or line.begins_with("#"):
			continue
		if line.begins_with("[") and line.ends_with("]"):
			section = line.substr(1, line.length() - 2).strip_edges()
			if not result.has(section):
				result[section] = {}
			continue
		var separator := line.find("=")
		if separator < 0 or section.is_empty():
			continue
		var key := line.substr(0, separator).strip_edges()
		var raw := line.substr(separator + 1).strip_edges()
		var parsed: Variant = raw
		if raw.is_valid_int():
			parsed = int(raw)
		elif raw.is_valid_float():
			parsed = float(raw)
		var values := Dictionary(result[section])
		values[key] = parsed
		result[section] = values
	return result
