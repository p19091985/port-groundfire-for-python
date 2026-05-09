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

	online.set("_endpoint", "ws://127.0.0.1:9")
	online.call("_force_reconnect", "snapshot_timeout")
	assert(str(online.get("_status")).contains("snapshot_timeout"))

	online.queue_free()
	await process_frame
	quit(0)
