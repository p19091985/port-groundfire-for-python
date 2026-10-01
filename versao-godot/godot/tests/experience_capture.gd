extends SceneTree

const Main := preload("res://scenes/main.tscn")
const Match := preload("res://scripts/local_match.gd")

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var output := OS.get_environment("EXPERIENCE_CAPTURE_DIR")
	if output.is_empty():
		push_error("EXPERIENCE_CAPTURE_DIR is required; reference goldens are never overwritten")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output)
	var main := Main.instantiate()
	root.add_child(main)
	main.set_process(false) # Same frozen menu animation time as the Python capture.
	var width := int(OS.get_environment("EXPERIENCE_CAPTURE_WIDTH"))
	var height := int(OS.get_environment("EXPERIENCE_CAPTURE_HEIGHT"))
	root.size = Vector2i(width if width > 0 else 1024, height if height > 0 else 768)
	for screen in ["main_menu", "options", "controllers", "keyboard_layout", "quit", "local_match_setup", "server_browser", "server_filters", "server_add", "server_join", "server_password", "server_unavailable", "server_invalid_address"]:
		match screen:
			"main_menu": main.call("_show_main_menu")
			"options": main.call("_show_options")
			"controllers": main.get("_screen").show_controllers()
			"keyboard_layout": main.get("_screen").edit_layout(0)
			"quit": main.call("_on_quit")
			"local_match_setup": main.call("_show_local_match_setup")
			"server_browser", "server_filters", "server_add", "server_join", "server_password", "server_unavailable", "server_invalid_address":
				main.call("_show_server_browser")
				var browser: Control = main.get("_screen")
				browser._entries.assign([
					{"name":"Groundfire Online Test", "endpoint":"127.0.0.1:8765", "game":"Groundfire", "map":"classic", "players":"2/8", "latency":"42", "source":"online", "description":"Browser-safe reference server"},
					{"name":"Groundfire SA Lobby", "endpoint":"127.0.0.1:8766", "game":"Groundfire", "map":"mesa", "players":"0/12", "latency":"88", "source":"online", "description":"South America lobby"}])
				browser._filter_text = ""
				browser._hide_passworded = false
				browser._hide_full = false
				browser._hide_empty = false
				browser._secure_only = false
				browser._region = ""
				browser._max_latency = 0
				browser._sort_mode = "latency"
				browser.classic_sort_descending = false
				browser._render_entries()
				var view: Control = browser.get_node("ClassicBrowser")
				match screen:
					"server_filters": view._show_filters()
					"server_add": view.show_add()
					"server_unavailable":
						browser._probe_entry = browser._visible_entries[0].duplicate()
						browser._on_server_probe_completed("127.0.0.1:8765",-1)
					"server_invalid_address":
						view.show_add()
						view.address = "127.0.0.1:65536"
						view._add_server()
					"server_join", "server_password":
						if screen == "server_password":
							browser._visible_entries[0]["passworded"] = "true"
						view.show_join(browser._visible_entries[0])
						if screen == "server_password":
							browser._password_line.text = "secret"
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		var picture := root.get_texture().get_image()
		if picture == null or picture.is_empty():
			push_error("No rendered image for %s" % screen)
			quit(1)
			return
		if picture.save_png(output.path_join(screen + ".png")) != OK:
			quit(1)
			return
	main.queue_free()
	await process_frame
	for screen in ["round_starting", "local_match", "score", "shop", "winner", "winner_eight", "shop_selected", "shell_flight"]:
		var game := Match.new()
		var roster: Array[Dictionary] = [
			{"name": "Player", "kind": "human", "controller": 0, "color": Color(1, 0, 1)},
			{"name": "Enemy", "kind": "human", "controller": 1, "color": Color8(255, 128, 0)}]
		if screen == "winner_eight":
			for index in range(2,8):
				roster.append({"name":"Player %d" % (index + 1), "kind":"computer", "controller":-1,
					"color":Color8(32 * index, 255 - 24 * index, 64 + 20 * index)})
		game.setup({"total_rounds":5, "roster":roster})
		game.size = Vector2(root.size)
		game.set("_terrain_seed", 1401)
		root.add_child(game)
		game.size = game.get_viewport_rect().size
		game.set_process(false)
		game.set("_phase", "round_starting" if screen == "round_starting" else "aim")
		for index in range(2):
			game.call("_set_shop_credits", index, 200)
		game.set("_score", 100)
		game.get("_participants")[0].score = 100
		if screen == "winner_eight":
			game.set("_enemy_score", 100)
			for participant in game.get("_participants"):
				participant.score = 100
		match screen:
			"score":
				game.set("_phase", "score")
				game.call("_refresh_score_overlay")
			"shop", "shop_selected":
				game.call("_open_post_round_shop", "Shop", 0, false)
				if screen == "shop_selected":
					game.get("_shop_select_positions")[1] = 3
					for index in range(2):
						game.get("_shop_input_delays")[index] = 0.2
					game.call("_participant_inventory", 0).add_ammo("Machine Gun", 125)
					game.call("_participant_inventory", 1).add_ammo("Missile", 5)
			"winner", "winner_eight": game.call("_open_winner_overlay")
		if screen == "shell_flight":
			for tick in range(1, 511):
				if tick == 500:
					Input.action_press("gf_fire")
				elif tick == 501:
					Input.action_release("gf_fire")
				game.call("_simulate_match_step", 1.0 / 60.0, false)
			Input.action_release("gf_fire")
			if game.get("_projectiles").is_empty():
				push_error("Shell flight capture did not launch a projectile")
				quit(1)
				return
		game.call("_update_hud")
		game.get("_classic_round_menu").set_process(false)
		game.call("_update_camera", 0.0)
		game.queue_redraw()
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		if root.get_texture().get_image().save_png(output.path_join(screen + ".png")) != OK:
			quit(1)
			return
		game.queue_free()
		await process_frame
	print("Experience captures written to ", output)
	quit(0)
