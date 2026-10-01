extends SceneTree

const Main := preload("res://scenes/main.tscn")
const Profiles := preload("res://scripts/classic_control_profiles.gd")
const Router := preload("res://scripts/player_input_router.gd")
const MatchScript := preload("res://scripts/local_match.gd")
var failures: Array[String] = []

func _init() -> void:
	call_deferred("_run")

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func buttons(node: Node) -> Array[String]:
	var result: Array[String] = []
	if node is Button:
		result.append(node.text)
	for child in node.get_children():
		result.append_array(buttons(child))
	return result

func press(node: Node, text: String) -> bool:
	if node is Button and node.text == text:
		node.pressed.emit()
		return true
	for child in node.get_children():
		if press(child, text):
			return true
	return false

func settle() -> void:
	await process_frame
	await process_frame

func _run() -> void:
	root.size = Vector2i(1024, 768)
	var main := Main.instantiate()
	root.add_child(main)
	await settle()
	check(buttons(main) == ["Start Game", "Find Servers", "Options", "Quit"], "Classic main menu must contain exactly the Python actions in order")
	press(main, "Start Game")
	await settle()
	var setup: Control = main.get("_screen")
	check(setup.roster.all(func(entry: Dictionary) -> bool: return not entry.enabled), "Python setup starts with no players")
	setup._toggle_player(0, true)
	setup._toggle_player(1, true)
	check(setup.roster[0].controller != setup.roster[1].controller, "Adding humans must select separate controllers")
	press(setup, "Back")
	await settle()
	press(main, "Quit")
	await settle()
	check(buttons(main) == ["Yes", "No"], "Quit must ask for confirmation")
	press(main, "No")
	await settle()
	press(main, "Find Servers")
	await settle()
	check(main.get("_screen").name == "ServerBrowser", "Find Servers must open the browser directly")
	var browser: Control = main.get("_screen")
	var browser_view: Control = browser.get_node("ClassicBrowser")
	browser._entries.assign([
		{"name":"Zulu", "source":"online", "endpoint":"127.0.0.1:8765", "players":"2/8", "latency":"42"},
		{"name":"Alpha", "source":"online", "endpoint":"127.0.0.1:8766", "players":"0/8", "latency":"88"}])
	browser._filter_text = ""
	browser._hide_empty = false
	browser._region = ""
	browser._secure_only = false
	browser._max_latency = 0
	browser._sort_mode = "latency"
	browser.classic_sort_descending = false
	browser._render_entries()
	check(browser._selected_index == 0, "Classic browser selects the first available server")
	browser_view._sort("name")
	check(browser._visible_entries[0].name == "Alpha", "Classic headers sort the backend entries")
	var down := InputEventKey.new()
	down.keycode = KEY_DOWN
	down.pressed = true
	browser_view._gui_input(down)
	check(browser._selected_index == 1, "Arrow navigation selects the next server")
	browser_view._show_filters()
	check(browser_view.dialog == "filters", "Classic filters must remain reachable")
	for letter in "Alpha":
		var typed := InputEventKey.new()
		typed.pressed = true
		typed.unicode = letter.unicode_at(0)
		browser_view._gui_input(typed)
	check(browser._visible_entries.size() == 1, "Classic filter changes affect actual directory results")
	browser_view._clear_filters()
	check(browser._visible_entries.size() == 2, "Clear restores default filters")
	browser_view.close_dialog()
	browser._show_join_dialog(browser._visible_entries[0])
	check(browser_view.dialog == "join", "Connect opens the classic join dialog")
	browser_view.join_role = "ai"
	browser._password_line.text = "test-password"
	browser._auto_retry_check.button_pressed = true
	var connection: Dictionary = browser_view.connection_entry()
	check(connection.is_computer and not connection.spectator and connection.password == "test-password" and connection.auto_retry_when_full, "Join retains AI, password and retry choices")
	browser_view.join_role = "spectator"
	connection = browser_view.connection_entry()
	check(connection.spectator and not connection.is_computer, "Spectator and AI are mutually exclusive")
	browser._hide_join_dialog()
	check(browser._password_line.text.is_empty() and browser_view.pending_entry.is_empty(), "Cancel clears pending credentials")
	browser._show_direct_join_dialog()
	browser_view.address = ""
	browser_view._add_server()
	check(browser_view.dialog == "add", "Empty address keeps Add open")
	browser_view.address = "127.0.0.1:28765"
	browser_view._add_server()
	check(browser_view.dialog.is_empty() and browser._favorites.has("127.0.0.1:28765"), "Add saves a favorite without connecting")
	check(main.get("_screen") == browser and browser_view._tab_name() == "favorites", "Add stays in Favorites")
	browser._toggle_selected_favorite()
	check(browser._favorites.has("127.0.0.1:28765"), "Adding an existing favorite must not remove it")
	browser._show_direct_join_dialog()
	browser_view.address = "localhost:65536"
	browser_view._add_server()
	check(browser_view.dialog == "add" and browser._status.text == "Server port must be between 1 and 65535.", "Invalid port keeps the address dialog open")
	browser_view.address = "localhost"
	browser_view._add_server()
	check(browser._favorites.has("localhost:27015"), "A bare hostname uses the Python default port")
	main.call("_show_main_menu")
	press(main, "Options")
	await settle()
	var options: Control = main.get("_screen")
	check(buttons(options) == ["Set Controls", "Apply", "Back"], "Classic Options must not expose exclusive settings")
	var previous := int(main.get("_resolution_index"))
	options.get_node("Resolution").item_selected.emit((previous + 1) % 6)
	check(int(main.get("_resolution_index")) == previous, "Changing a selector must not apply the resolution")
	press(options, "Set Controls")
	await settle()
	check(options.screen == "controllers", "Set Controls must open controller selection")
	check(buttons(options).count("Edit Layout") >= 2, "Both keyboard layouts must be editable")
	options.edit_layout(1)
	await settle()
	check(buttons(options).size() == 13, "Each layout has eleven actions, reset and done")
	check(not buttons(options).has("Pause"), "Pause is not one of the eleven classic controls")
	var original := int(options.values[0])
	options._begin_capture(0)
	var key := InputEventKey.new()
	key.keycode = KEY_F9
	key.pressed = true
	options._input(key)
	check(int(options.values[0]) == KEY_F9, "Key capture must update only the draft layout")
	check(int(options.layout) == 1, "Key capture must stay on Keyboard 2")
	options.values[0] = original
	press(options, "Done")
	await settle()
	check(options.screen == "controllers", "Done returns to controller selection")
	press(options, "Back")
	await settle()
	check(options.screen == "options", "Controller Back returns to Options")
	check(int(options.resolution) == (previous + 1) % 6, "Options draft survives controller navigation")
	press(options, "Back")
	await settle()
	check(int(main.get("_resolution_index")) == previous, "Back must discard unapplied resolution")
	press(main, "Options")
	await settle()
	options = main.get("_screen")
	var selected := (previous + 1) % 6
	options.get_node("Resolution").item_selected.emit(selected)
	press(options, "Apply")
	check(int(main.get("_resolution_index")) == selected, "Apply commits the selected resolution")
	var saved := ConfigFile.new()
	check(saved.load("user://groundfire_options.cfg") == OK, "Apply persists options")
	check(int(saved.get_value("video", "resolution_index", -1)) == selected, "Persisted resolution matches Apply")
	options.get_node("Resolution").item_selected.emit(previous)
	press(options, "Apply")
	var axis_values := Profiles.DEFAULTS.duplicate()
	Profiles.capture(axis_values, 7, 105)
	check(axis_values[8] == 104, "Axis capture must bind opposite linked direction")
	Profiles.capture(axis_values, 7, 9)
	check(axis_values[8] == -1, "Replacing a paired axis with a button clears its opposite")
	var saved_layouts := Profiles.layouts.duplicate(true)
	var saved_assignments := Profiles.assignments.duplicate()
	var legacy := ConfigFile.new()
	legacy.set_value("gamepad", "gf_fire_type", "button")
	legacy.set_value("gamepad", "gf_fire_index", 8)
	legacy.set_value("gamepad_device_1", "gf_fire_type", "button")
	legacy.set_value("gamepad_device_1", "gf_fire_index", 9)
	Profiles.import_legacy(legacy)
	check(Profiles.layouts[Profiles.assignments[0]][0] == 8, "Existing global joystick binding is preserved")
	check(Profiles.layouts[Profiles.assignments[1]][0] == 9, "Existing device override is preserved independently")
	Profiles.save_profiles()
	Profiles.load_profiles()
	check(Profiles.layouts[Profiles.assignments[1]][0] == 9, "Joystick layout survives reload")
	Profiles.layouts = saved_layouts
	Profiles.assignments = saved_assignments
	Profiles.save_profiles()
	Profiles.refresh_devices([])
	Profiles.refresh_devices([3, 7])
	check(Profiles._devices[0] == 3 and Profiles._devices[1] == 7, "Sparse device IDs occupy independent slots")
	Profiles.refresh_devices([7])
	check(Profiles._devices[0] == -1 and Profiles._devices[1] == 7, "Disconnect must not reassign the surviving player")
	Profiles.refresh_devices([7, 9])
	check(Profiles._devices[0] == 9 and Profiles._devices[1] == 7, "New device reuses the empty slot")
	Profiles.refresh_devices([])
	Router.ensure_actions()
	var match_node := MatchScript.new()
	match_node.setup({"roster": [{"name": "One", "controller": 0, "kind": "human"}, {"name": "Two", "controller": 1, "kind": "human"}]})
	Input.action_press("gf_p2_aim_left")
	var owner := str(match_node.call("_participant_owner", 1))
	check(match_node.call("_missile_steer_direction", {"owner": owner}, Vector2.ZERO) == 1.0, "Keyboard 2 must steer its own missile")
	Input.action_release("gf_p2_aim_left")
	match_node.free()
	main.call("_start_local_match", 5)
	await settle()
	var active_match: Control = main.get("_screen")
	var escape := InputEventAction.new()
	escape.action = "gf_pause"
	escape.pressed = true
	active_match.call("_unhandled_input", escape)
	await settle()
	check(buttons(main) == ["Yes", "No"], "Escape from combat must enter Python's QuitMenu")
	press(main, "No")
	await settle()
	check(buttons(main) == ["Start Game", "Find Servers", "Options", "Quit"], "Declining Quit returns to MainMenu")
	main.queue_free()
	await settle()
	if failures.is_empty():
		print("Experience menu/control checks passed")
	quit(0 if failures.is_empty() else 1)
