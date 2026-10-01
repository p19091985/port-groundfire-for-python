extends SceneTree

const Runtime := preload("res://scripts/local_match.gd")

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var game := Runtime.new()
	game.size = Vector2(1024,768)
	root.add_child(game)
	game.set_process(false)
	for name in ["fire_shell", "shell_death", "launch_missile", "missile_death", "metal_hit", "nuke"]:
		var player: AudioStreamPlayer = game.get("_" + name + "_audio")
		game.call("_play_" + name + "_audio")
		await process_frame
		var first := player.get_stream_playback()
		game.call("_play_" + name + "_audio")
		await process_frame
		assert(first != player.get_stream_playback(), "Concurrent effects need distinct playbacks")
		assert(first.is_playing(), "A second effect must not cut off the first")
		game.call("_set_paused", true, false)
		assert(player.stream_paused)
		game.call("_set_paused", false, false)
		assert(not player.stream_paused)
		game.call("_stop_all_audio")
		assert(not player.playing)
	for kind in ["jets", "missile", "machine_gun"]:
		var template: AudioStreamPlayer = game.get({"jets":"_jump_jets_audio", "missile":"_missile_flight_audio", "machine_gun":"_machine_gun_audio"}[kind])
		game.call("_set_loop_sources", kind, template, ["first", "second"])
		await create_timer(0.05).timeout
		var voices: Dictionary = game.get("_loop_voices")[kind]
		var first: AudioStreamPlayer = voices.first
		var second: AudioStreamPlayer = voices.second
		assert(first.playing and second.playing)
		assert(first.get_stream_playback() != second.get_stream_playback())
		var survivor := second.get_stream_playback()
		game.call("_set_loop_sources", kind, template, ["second"])
		assert(not first.playing, "Released source must stop immediately")
		assert(second.get_stream_playback() == survivor and survivor.is_playing(), "Other source must continue without restart")
		game.call("_set_paused", true, false)
		assert(second.stream_paused)
		game.call("_set_paused", false, false)
		assert(not second.stream_paused)
		game.call("_stop_all_audio")
		assert(not second.playing and game.get("_loop_voices")[kind].is_empty())
	# Exit must stop even a held trigger, without waiting for a key release.
	game.set("_machine_gun_active", true)
	game.set("_machine_gun_fire_held", true)
	game.call("_play_machine_gun_audio")
	assert(not game.get("_loop_voices").machine_gun.is_empty())
	game.call("_stop_all_audio")
	assert(game.get("_loop_voices").machine_gun.is_empty())
	game.queue_free()
	await process_frame
	print("Experience audio overlap, pause and cleanup passed")
	quit(0)
