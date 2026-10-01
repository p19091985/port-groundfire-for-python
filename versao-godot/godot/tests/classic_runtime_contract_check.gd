extends SceneTree

const ClassicFixedStep := preload("res://scripts/classic_fixed_step.gd")
const PlayerInputRouter := preload("res://scripts/player_input_router.gd")
const PythonRandom := preload("res://scripts/python_random.gd")
const TerrainModel := preload("res://scripts/terrain_model.gd")
const ClassicConfig := preload("res://scripts/classic_config.gd")
const WeaponInventory := preload("res://scripts/weapon_inventory.gd")


func _init() -> void:
	_check_fixed_step_contract()
	_check_controller_routing_contract()
	_check_python_random_contract()
	_check_python_terrain_fixture()
	_check_classic_configuration_contract()
	quit(0)


func _check_fixed_step_contract() -> void:
	var stepper := ClassicFixedStep.new(0.02, 2)
	assert(stepper.consume(0.01).is_empty())
	assert(stepper.consume(0.03) == [0.02, 0.02])
	assert(is_equal_approx(stepper.accumulator(), 0.0))
	assert(stepper.consume(0.20) == [0.02, 0.02])
	assert(is_equal_approx(stepper.accumulator(), 0.02))
	stepper.reset()
	assert(is_equal_approx(stepper.accumulator(), 0.0))


func _check_controller_routing_contract() -> void:
	assert(PlayerInputRouter.action_name_for_controller(0, "fire") == "gf_fire")
	assert(PlayerInputRouter.action_name_for_controller(1, "fire") == "gf_p2_fire")
	# Godot device IDs can be sparse after hotplug. Controller slots index the
	# connected device list, and a disconnected slot must never read device 0.
	var devices := Input.get_connected_joypads()
	for slot in range(8):
		var expected := int(devices[slot]) if slot < devices.size() else -1
		assert(PlayerInputRouter.gamepad_device_for_controller(slot + 2) == expected)
	var empty := PlayerInputRouter.empty_command()
	assert(not empty["fire"])
	assert(not empty["fire_pressed"])


func _check_python_random_contract() -> void:
	var rng := PythonRandom.new(1401)
	var stops := [1002, 1000, 250, 20, 1002, 1000, 250, 30]
	var expected := [749, 908, 113, 1, 736, 163, 127, 13]
	for index in range(stops.size()):
		assert(rng.randbelow(stops[index]) == expected[index])


func _check_python_terrain_fixture() -> void:
	var fixture_file := FileAccess.open("res://data/classic_runtime_reference.json", FileAccess.READ)
	assert(fixture_file != null)
	var fixture: Dictionary = JSON.parse_string(fixture_file.get_as_text())
	var expected: Array = Dictionary(fixture["terrain_rng"])["world_heights"]
	var terrain := TerrainModel.new()
	terrain.rebuild_with_seed(1280.0, 768.0, int(Dictionary(fixture["terrain_rng"])["seed"]))
	var actual := terrain.world_height_samples()
	assert(actual.size() == expected.size())
	for index in range(actual.size()):
		assert(abs(float(actual[index]) - float(expected[index])) <= 0.0001)


func _check_classic_configuration_contract() -> void:
	var settings := ClassicConfig.load_options()
	var terrain := Dictionary(settings["terrain"])
	assert(int(terrain["slices"]) == 500)
	assert(is_equal_approx(float(terrain["fall_pause"]), 0.2))
	var inventory := WeaponInventory.new()
	inventory.configure_classic(settings)
	assert(int(inventory.weapon_by_name("Shell")["damage"]) == 40)
	assert(is_equal_approx(float(inventory.weapon_by_name("MIRV")["cooldown"]), 7.5))
	assert(int(inventory.weapon_by_name("Missile")["cost"]) == 50)
