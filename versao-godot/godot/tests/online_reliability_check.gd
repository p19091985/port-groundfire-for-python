extends SceneTree

const OnlineMatchScene := preload("res://scenes/online_match.tscn")


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(1024, 768)
	var online := OnlineMatchScene.instantiate()
	root.add_child(online)
	await process_frame
	await process_frame

	var reconnect := online.get("_manual_reconnect_button") as Button
	var back := online.get("_back_button") as Button
	assert(reconnect != null)
	assert(back != null)
	assert(reconnect.focus_neighbor_left == back.get_path())
	assert(reconnect.focus_neighbor_right == back.get_path())
	assert(reconnect.focus_neighbor_top == reconnect.get_path())
	assert(back.focus_neighbor_left == reconnect.get_path())
	assert(back.focus_neighbor_right == reconnect.get_path())
	assert(back.focus_neighbor_bottom == back.get_path())

	var now := Time.get_ticks_msec()
	online.set("_pending_commands", {
		1: {"command": {"move_left": true}, "sent_msec": now - 6000},
		2: {"command": {"move_right": true}, "sent_msec": now},
	})
	assert(int(online.call("_stale_pending_count")) == 1)
	online.call("_prune_stale_pending_commands")
	var pending := Dictionary(online.get("_pending_commands"))
	assert(pending.size() == 1)
	assert(pending.has(2))

	online.set("_auth_token", "")
	online.set("_session_token_url", "https://directory.example.test/session-token.json?room=alpha")
	assert(bool(online.call("_needs_session_token")))
	var token_url := str(online.call("_session_token_request_url", "Godot Player"))
	assert(token_url.begins_with("https://directory.example.test/session-token.json?room=alpha&player_name="))
	assert(token_url.contains("Godot%20Player"))
	online.set("_auth_token", "static-token")
	assert(not bool(online.call("_needs_session_token")))
	online.set("_auto_retry_when_full", true)
	online.set("_server_protocol_ready", true)
	online.set("_join_sent", true)
	online.call("_on_websocket_message_received", {"type": "error", "protocol": 2, "message": "server_full"})
	assert(not bool(online.get("_join_sent")))
	assert(abs(float(online.get("_capacity_retry_timer")) - 3.0) < 0.01)
	assert(str(online.get("_status")).contains("slot opens"))

	online.set("_endpoint", "ws://127.0.0.1:9")
	online.call("_force_reconnect", "snapshot_timeout")
	assert(str(online.get("_status")).contains("snapshot_timeout"))
	assert(int(online.get("_reconnect_attempt")) == 1)
	online.call("_on_websocket_status_changed", "websocket_connected")
	assert(int(online.get("_reconnect_attempt")) == 1)
	online.call("_schedule_reconnect", "hello_timeout")
	assert(int(online.get("_reconnect_attempt")) == 2)
	assert(str(online.get("_status")).contains("(2/5)"))
	online.call("_mark_session_healthy")
	assert(int(online.get("_reconnect_attempt")) == 0)
	assert(abs(float(online.get("_reconnect_timer"))) < 0.01)

	online.set("_render_entities", {
		42: {
			"entity_id": 42,
			"entity_type": "tank",
			"owner_player": 1,
			"render_position": Vector2.ZERO,
			"target_position": Vector2.ZERO,
			"velocity": Vector2.ZERO,
			"angle": 0.0,
		},
		99: {
			"entity_id": 99,
			"entity_type": "projectile",
			"owner_player": 2,
			"render_position": Vector2.ZERO,
			"target_position": Vector2(10.0, 0.0),
			"velocity": Vector2(100.0, 0.0),
		},
	})
	online.set("_local_player_number", 1)
	online.call("_apply_local_prediction", {"move_right": true, "aim_left": true})
	var render_entities := Dictionary(online.get("_render_entities"))
	var predicted_tank := Dictionary(render_entities[42])
	assert(bool(predicted_tank.get("predicted", false)))
	assert(abs(Vector2(predicted_tank.get("render_position", Vector2.ZERO)).x - 0.08) < 0.01)
	assert(abs(float(predicted_tank.get("angle", 0.0)) - 1.5) < 0.01)
	online.call("_update_interpolation", 0.1)
	render_entities = Dictionary(online.get("_render_entities"))
	var projectile := Dictionary(render_entities[99])
	assert(Vector2(projectile.get("render_position", Vector2.ZERO)).x > 10.0)
	online.set("_match_snapshot", {
		"entities": [
			{"entity_id": 42, "entity_type": "tank", "owner_player": 1, "position": [1.0, 0.0], "velocity": [0.0, 0.0], "angle": 0.0, "payload": {}},
			{"entity_id": 99, "entity_type": "projectile", "owner_player": 2, "position": [14.0, 0.0], "velocity": [100.0, 0.0], "angle": 0.0, "payload": {}},
		],
	})
	online.call("_ingest_replicated_entities")
	render_entities = Dictionary(online.get("_render_entities"))
	predicted_tank = Dictionary(render_entities[42])
	assert(not bool(predicted_tank.get("predicted", true)))
	assert(float(online.get("_last_prediction_error")) > 0.0)

	online.set("_local_player_number", 2)
	online.set("_render_entities", {
		42: {"entity_id": 42, "entity_type": "tank", "owner_player": 1, "render_position": Vector2.ZERO},
		43: {"entity_id": 43, "entity_type": "tank", "owner_player": 2, "render_position": Vector2.ZERO},
		44: {"entity_id": 44, "entity_type": "tank", "owner_player": 8, "render_position": Vector2.ZERO},
	})
	online.call("_apply_local_prediction", {"move_right": true})
	render_entities = Dictionary(online.get("_render_entities"))
	assert(not bool(Dictionary(render_entities[42]).get("predicted", false)))
	assert(bool(Dictionary(render_entities[43]).get("predicted", false)))
	assert(not bool(Dictionary(render_entities[44]).get("predicted", false)))
	online.set("_local_player_number", 8)
	online.call("_apply_local_prediction", {"move_left": true})
	render_entities = Dictionary(online.get("_render_entities"))
	assert(bool(Dictionary(render_entities[44]).get("predicted", false)))

	online.set("_spectating", true)
	online.set("_local_player_number", -1)
	online.set("_match_snapshot", {"players": [{"player_number": 1, "name": "Alice", "is_ready": false}]})
	assert(str(online.call("_lobby_summary")).contains("Spectating lobby"))

	await _free_node(online)
	quit(0)


func _free_node(node: Node) -> void:
	if node == null:
		return
	node.queue_free()
	await process_frame
	await process_frame
