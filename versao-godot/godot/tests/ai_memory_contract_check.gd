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
			{"slot": 0, "name": "Human", "kind": "human", "controller": 0},
			{"slot": 1, "name": "Classic CPU", "kind": "computer", "controller": -1},
		],
	})
	root.add_child(local_match)
	await process_frame
	await process_frame
	local_match.set("_phase", "aim")
	local_match.call("_set_turn_index", 1)
	var first_shot: Dictionary = local_match.call("_choose_ai_shot")
	assert(is_equal_approx(float(first_shot["power"]), 10.0))
	local_match.call("_remember_ai_fired", 1, first_shot)
	var participants: Array = local_match.get("_participants")
	assert(int(Dictionary(participants[1])["ai_shots_in_air"]) == 1)
	var target_tank := local_match.call("_target_tank") as RefCounted
	var target_position: Vector2 = local_match.call("_tank_damage_center", target_tank)
	local_match.call("_record_ai_shot", local_match.call("_participant_owner", 1), target_position + Vector2(120.0, 0.0), "")
	participants = local_match.get("_participants")
	var memory := Dictionary(participants[1])
	assert(int(memory["ai_shots_in_air"]) == 0)
	assert(bool(memory["ai_last_shot"]))
	var adjusted_shot: Dictionary = local_match.call("_choose_ai_shot")
	assert(not is_equal_approx(float(adjusted_shot["angle"]), float(first_shot["angle"])) or not is_equal_approx(float(adjusted_shot["power"]), float(first_shot["power"])))

	local_match.queue_free()
	await process_frame
	await process_frame
	quit(0)
