extends RefCounted
## Opt-in release-package verification. Explicit checks work when assertions
## and editor command-line switches are compiled out of the export template.

var checks: Array[Dictionary] = []
var initial_resolution := -1

func _check(id: String, condition: bool) -> bool:
	checks.append({"id": id, "status": "passed" if condition else "failed"})
	return condition

func _press(node: Node, caption: String) -> bool:
	if node is Button and node.text == caption and not node.disabled:
		node.pressed.emit()
		return true
	for child in node.get_children():
		if not child.is_queued_for_deletion() and _press(child, caption):
			return true
	return false

func run(main: Control, report_path: String) -> void:
	var tree := main.get_tree()
	initial_resolution = int(main.get("_resolution_index"))
	var resources_available := true
	for path in ["res://data/classic/options.ini", "res://data/classic/controls.ini"]:
		resources_available = _check(path, FileAccess.file_exists(path)) and resources_available
	if not resources_available:
		_finish(tree, report_path)
		return
	_check("main-to-setup", _press(main, "Start Game"))
	await tree.process_frame
	var setup: Control = main.get("_screen")
	setup.call("_toggle_player", 0, true)
	setup.call("_toggle_player", 1, true)
	await tree.process_frame
	_check("setup-to-match", _press(setup, "Start!"))
	await tree.process_frame
	var runtime: Control = main.get("_screen")
	runtime.set_process(false)
	_check("two-human-match", runtime.get("_participants").size() == 2)
	_check("classic-configuration", int(runtime.get("_classic_settings").terrain.slices) == 500)
	for index in range(242):
		runtime.call("_simulate_match_step", 1.0 / 60.0, false)
	_check("round-starts", runtime.get("_phase") == "aim")
	runtime.call("_fire_participant", 0)
	runtime.call("_fire_participant", 1)
	_check("simultaneous-shots", runtime.get("_projectiles").size() == 2)
	runtime.call("_set_paused", true)
	_check("pause", runtime.get("_is_paused"))
	runtime.call("_set_paused", false)
	_check("resume", not runtime.get("_is_paused"))
	# Fixture deaths isolate the phase journey; projectile equivalence has a
	# separate differential runner. Do not let these shots choose the winner.
	runtime.get("_projectiles").clear()
	var victim: RefCounted = runtime.call("_participant_tank", 1)
	victim.call("apply_damage", 101.0)
	runtime.call("_record_round_defeat", "Player", "Enemy")
	runtime.call("_after_explosion")
	_check("finishing-delay", runtime.get("_phase") == "round_finishing" and runtime.get("_score") == 0)
	for index in range(301):
		runtime.call("_simulate_match_step", 1.0 / 60.0, false)
	_check("score-after-delay", runtime.get("_phase") == "score" and runtime.get("_score") == 200)
	runtime.call("_update_modal_activation", 2.1)
	runtime.call("_continue_from_score")
	_check("score-to-shop", runtime.get("_phase") == "shop")
	for index in range(2):
		runtime.get("_shop_select_positions")[index] = 10
		runtime.get("_shop_input_delays")[index] = -0.01
		runtime.call("_handle_shop_command_for_participant", index, "fire")
	runtime.call("_simulate_match_step", 1.0 / 60.0, false)
	_check("shop-to-next-round", runtime.get("_phase") == "round_starting" and runtime.get("_round") == 2)
	var escape := InputEventAction.new()
	escape.action = "gf_pause"
	escape.pressed = true
	runtime.call("_unhandled_input", escape)
	await tree.process_frame
	_check("escape-to-quit", _press(main, "No"))
	await tree.process_frame
	_check("return-to-menu", _press(main, "Options"))
	await tree.process_frame
	main.get("_screen").get_node("Resolution").item_selected.emit(1)
	_check("save-options", _press(main.get("_screen"), "Apply"))
	var config := ConfigFile.new()
	_check("saved-options-readable", config.load("user://groundfire_options.cfg") == OK)
	main.call("_show_server_browser")
	await tree.process_frame
	var browser: Control = main.get("_screen")
	var classic: Control = browser.get_node("ClassicBrowser")
	classic.call("_show_filters")
	_check("browser-filters", classic.get("dialog") == "filters")
	classic.call("close_dialog")
	classic.call("show_add")
	classic.set("address", "127.0.0.1:28765")
	classic.call("_add_server")
	_check("browser-add-without-connect", main.get("_screen") == browser and classic.get("dialog") == "")
	var entry := {"name": "Package fixture", "endpoint": "udp://127.0.0.1:28765", "requires_password": true}
	classic.call("show_join", entry)
	classic.set("join_role", "ai")
	browser.get("_password_line").text = "package-test"
	var connection: Dictionary = classic.call("connection_entry")
	_check("browser-ai-credentials", connection.get("is_computer", false) and not connection.get("spectator", true) and connection.get("password", "") == "package-test")
	classic.call("close_dialog")
	_check("browser-cancel-clears-password", browser.get("_password_line").text.is_empty() and classic.get("pending_entry").is_empty())
	_finish(tree, report_path)

func _finish(tree: SceneTree, report_path: String) -> void:
	var passed := checks.all(func(item: Dictionary) -> bool: return item.status == "passed")
	var report := FileAccess.open(report_path, FileAccess.WRITE)
	if report == null:
		push_error("Cannot write package verification report: " + report_path)
		tree.quit(1)
		return
	report.store_string(JSON.stringify({"schema": 1, "status": "passed" if passed else "failed", "checks": checks,
		"engine": Engine.get_version_info().string, "platform": OS.get_name(), "userdata": OS.get_user_data_dir(),
		"initial_resolution": initial_resolution, "saved_resolution": 1}, "  ") + "\n")
	report.close()
	tree.quit(0 if passed else 1)
