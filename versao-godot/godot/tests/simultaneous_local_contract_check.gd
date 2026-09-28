extends SceneTree

const LocalMatchScene := preload("res://scenes/local_match.tscn")


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(1024, 768)
	var local_match := LocalMatchScene.instantiate()
	local_match.setup({
		"total_rounds": 5,
		"roster": [
			{"slot": 0, "name": "Keyboard One", "kind": "human", "controller": 0},
			{"slot": 1, "name": "Keyboard Two", "kind": "human", "controller": 1},
		],
	})
	root.add_child(local_match)
	await process_frame
	await process_frame

	var participants: Array = local_match.get("_participants")
	assert(participants.size() == 2)
	assert(int(Dictionary(participants[0]).get("controller", -1)) == 0)
	assert(int(Dictionary(participants[1]).get("controller", -1)) == 1)

	local_match.set("_phase", "aim")
	local_match.set("_projectiles", [])
	for index in range(2):
		var inventory := Dictionary(participants[index]).get("inventory") as RefCounted
		inventory.call("select_shell")
		inventory.call("update_current_cooldown", 99.0)
	local_match.call("_fire_participant", 0)
	local_match.call("_fire_participant", 1)
	assert(str(local_match.get("_phase")) == "aim")
	var projectiles: Array = local_match.get("_projectiles")
	assert(projectiles.size() == 2)
	assert(str(Dictionary(projectiles[0]).get("owner", "")) != str(Dictionary(projectiles[1]).get("owner", "")))

	# Machine Gun firing state is owned by each participant as well. Starting a
	# second stream must not overwrite the first player's held-fire/cooldown.
	local_match.call("_reset_machine_gun_fire")
	local_match.set("_projectiles", [])
	for index in range(2):
		var inventory := Dictionary(participants[index]).get("inventory") as RefCounted
		inventory.call("add_ammo", "Machine Gun", 2)
		inventory.call("reset_round_ammo")
		assert(bool(inventory.call("select_by_name", "Machine Gun", false)))
	local_match.call("_set_turn_index", 0)
	var first_inventory := Dictionary(participants[0]).get("inventory") as RefCounted
	local_match.call("_begin_player_machine_gun_fire", first_inventory.call("current"))
	local_match.call("_set_turn_index", 1)
	var second_inventory := Dictionary(participants[1]).get("inventory") as RefCounted
	local_match.call("_begin_player_machine_gun_fire", second_inventory.call("current"))
	assert(bool(local_match.get("_machine_gun_active")))
	var extra_states := Dictionary(local_match.get("_machine_gun_extra_states"))
	assert(extra_states.size() == 1)
	assert(bool(local_match.call("_spawn_machine_gun_round", 0.0)))
	var extra_owner := str(extra_states.keys()[0])
	var extra_state := Dictionary(extra_states[extra_owner])
	assert(bool(local_match.call("_spawn_extra_machine_gun_round", extra_owner, extra_state, 0.0)))
	projectiles = local_match.get("_projectiles")
	var machine_gun_owners := {}
	for projectile in projectiles:
		if str(Dictionary(projectile).get("kind", "")) == "machine_gun":
			machine_gun_owners[str(Dictionary(projectile).get("owner", ""))] = true
	assert(machine_gun_owners.size() == 2)
	local_match.call("_reset_machine_gun_fire")
	local_match.set("_projectiles", [])

	local_match.call("_prepare_shop_pass")
	local_match.set("_phase", "shop")
	local_match.set("_shop_input_delays", {0: -0.01, 1: -0.01})
	assert(bool(local_match.call("_handle_shop_command_for_participant", 0, "down")))
	assert(bool(local_match.call("_handle_shop_command_for_participant", 1, "up")))
	var positions := Dictionary(local_match.get("_shop_select_positions"))
	assert(int(positions[0]) == 1)
	assert(int(positions[1]) == 10)

	local_match.set("_shop_input_delays", {0: -0.01, 1: -0.01})
	assert(bool(local_match.call("_handle_shop_command_for_participant", 1, "fire")))
	assert(not bool(local_match.get("_shop_finish_pending")))
	local_match.set("_shop_select_positions", {0: 10, 1: 10})
	local_match.set("_shop_input_delays", {0: -0.01, 1: -0.01})
	assert(bool(local_match.call("_handle_shop_command_for_participant", 0, "fire")))
	assert(bool(local_match.get("_shop_finish_pending")))

	local_match.queue_free()
	await process_frame
	await process_frame
	quit(0)
