extends SceneTree

const MainScene := preload("res://scenes/main.tscn")
const LocalMatchScene := preload("res://scenes/local_match.tscn")
const OnlineMatchScene := preload("res://scenes/online_match.tscn")
const ServerBrowserScene := preload("res://scenes/server_browser.tscn")
const PlatformCapabilities := preload("res://scripts/platform_capabilities.gd")
const ServerDirectory := preload("res://scripts/server_directory.gd")
const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const ClassicSelector := preload("res://scripts/classic_selector.gd")
const SHUTDOWN_DRAIN_FRAMES := 8


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(1024, 768)
	_check_platform_capability_matrix()
	_check_directory_http_schema()
	await _check_main_menu_and_options()
	await _check_main_menu_responsive_metrics()
	await _check_menu_subscreen_responsive_metrics()
	await _check_server_browser_scene()
	await _check_server_browser_responsive_metrics()
	await _check_local_match_scene()
	await _check_online_match_scene()
	await _drain_frames(SHUTDOWN_DRAIN_FRAMES)
	quit(0)


func _check_platform_capability_matrix() -> void:
	assert(PlatformCapabilities.supports_for_platform(PlatformCapabilities.FEATURE_BROWSER_SAFE_ONLINE, true))
	assert(PlatformCapabilities.supports_for_platform(PlatformCapabilities.FEATURE_BROWSER_SAFE_ONLINE, false))
	assert(not PlatformCapabilities.supports_for_platform(PlatformCapabilities.FEATURE_LAN_DISCOVERY, true))
	assert(not PlatformCapabilities.supports_for_platform(PlatformCapabilities.FEATURE_UDP_TRANSPORT, true))
	assert(not PlatformCapabilities.supports_for_platform(PlatformCapabilities.FEATURE_DEDICATED_SERVER_TOOLS, true))
	assert(PlatformCapabilities.supports_for_platform(PlatformCapabilities.FEATURE_LAN_DISCOVERY, false))
	assert(PlatformCapabilities.supports_for_platform(PlatformCapabilities.FEATURE_UDP_TRANSPORT, false))
	assert(PlatformCapabilities.supports_for_platform(PlatformCapabilities.FEATURE_DEDICATED_SERVER_TOOLS, false))
	assert(not PlatformCapabilities.visible_server_browser_tabs_for(true).has("LAN"))
	assert(PlatformCapabilities.visible_server_browser_tabs_for(false).has("LAN"))
	assert(PlatformCapabilities.hidden_features_for_platform(true).has(PlatformCapabilities.FEATURE_DEDICATED_SERVER_TOOLS))
	assert(PlatformCapabilities.hidden_features_for_platform(false).is_empty())


func _check_directory_http_schema() -> void:
	var body := JSON.stringify({
		"schema": ServerDirectory.DIRECTORY_SCHEMA_VERSION,
		"servers": [
			{
				"name": "Web Arena",
				"game": "Groundfire",
				"players": "1/8",
				"map": "Islands",
				"latency": "33ms",
				"source": ServerDirectory.SOURCE_ONLINE,
				"endpoint": "wss://example.invalid/groundfire",
				"passworded": false,
			},
			{
				"name": "Desktop LAN",
				"game": "Groundfire",
				"players": "0/8",
				"map": "Classic",
				"latency": "LAN",
				"source": ServerDirectory.SOURCE_LAN,
				"endpoint": "127.0.0.1:27015",
				"passworded": false,
			},
		],
	}).to_utf8_buffer()
	var web_entries := ServerDirectory.entries_from_http_body(body, false)
	var desktop_entries := ServerDirectory.entries_from_http_body(body, true)
	assert(web_entries.size() == 1)
	assert(web_entries[0].get("endpoint", "") == "wss://example.invalid/groundfire")
	assert(desktop_entries.size() == 2)
	assert(desktop_entries.any(func(entry: Dictionary) -> bool: return entry.get("source", "") == ServerDirectory.SOURCE_LAN))


func _check_main_menu_and_options() -> void:
	var main := MainScene.instantiate()
	root.add_child(main)
	await process_frame
	await process_frame
	assert(_has_button(main, "Start Game"))
	assert(_has_button(main, "Find Servers"))
	assert(_has_button(main, "Options"))
	assert(_has_button(main, "Quit"))
	var start_local := _find_control_with_text(main, "Button", "Start Game") as Button
	var find_servers := _find_control_with_text(main, "Button", "Find Servers") as Button
	var quit_button := _find_control_with_text(main, "Button", "Quit") as Button
	var version_label := _find_control_with_text(main, "Label", "0.25 (Python Port)") as Label
	assert(start_local != null)
	assert(find_servers != null)
	assert(quit_button != null)
	assert(version_label != null)
	var logo := _find_first(main, "TextureRect") as TextureRect
	assert(logo != null)
	assert(logo.custom_minimum_size.x >= 547.0)
	assert(logo.custom_minimum_size.x <= 874.0)
	assert(start_local.custom_minimum_size.x >= 259.0)
	assert(start_local.custom_minimum_size.x <= 414.0)
	assert(start_local.custom_minimum_size.y >= 34.0)
	assert(start_local.custom_minimum_size.y <= 56.0)
	assert(start_local.focus_neighbor_bottom == find_servers.get_path())
	assert(find_servers.focus_neighbor_top == start_local.get_path())
	assert(start_local.focus_neighbor_top == quit_button.get_path())
	assert(start_local.focus_neighbor_left == start_local.get_path())
	assert(start_local.focus_neighbor_right == start_local.get_path())
	assert(find_servers.focus_neighbor_left == find_servers.get_path())
	assert(find_servers.focus_neighbor_right == find_servers.get_path())
	_assert_classic_text_effect(start_local)
	_assert_classic_text_effect(version_label)
	_assert_classic_hover_color(start_local)
	if not OS.has_feature("web"):
		assert(_has_button(main, "Dedicated Server"))
		main.set("_dedicated_gateway_host", "0.0.0.0")
		main.set("_dedicated_gateway_port", 27999)
		main.set("_dedicated_gateway_max_players", 4)
		main.set("_dedicated_gateway_closed", true)
		main.set("_dedicated_gateway_banned_players", "Mallory, Eve")
		main.call("_show_dedicated_server_tools")
		await process_frame
		assert(_has_label(main, "Dedicated Server"))
		assert(_has_label(main, "Browser Gateway"))
		assert(_has_label(main, "Host"))
		assert(_has_label(main, "Port"))
		assert(_has_label(main, "Join Password"))
		assert(_has_label(main, "Auth Token"))
		assert(_has_label(main, "Max Players"))
		assert(_has_label(main, "Closed Joins"))
		assert(_has_label(main, "Banned Players"))
		assert(_has_label(main, "Connect endpoint: ws://127.0.0.1:27999"))
		assert(_has_label(main, "Join policy: password off, auth off, max 4, joins closed, bans 2"))
		assert(_find_control_with_text(main, "LineEdit", "0.0.0.0") != null)
		assert(_find_control_with_text(main, "LineEdit", "Mallory, Eve") != null)
		assert(_has_button(main, "Start Gateway"))
		assert(_has_button(main, "Stop Gateway"))
		assert(_has_button(main, "Copy Endpoint"))
		assert(_has_button(main, "Copy Command"))
		assert(_has_button(main, "Back"))
		var start_gateway := _find_control_with_text(main, "Button", "Start Gateway") as Button
		var stop_gateway := _find_control_with_text(main, "Button", "Stop Gateway") as Button
		var copy_endpoint := _find_control_with_text(main, "Button", "Copy Endpoint") as Button
		var copy_command := _find_control_with_text(main, "Button", "Copy Command") as Button
		var dedicated_back := _find_control_with_text(main, "Button", "Back") as Button
		assert(start_gateway != null)
		assert(stop_gateway != null)
		assert(copy_endpoint != null)
		assert(copy_command != null)
		assert(dedicated_back != null)
		assert(stop_gateway.disabled)
		assert(start_gateway.focus_neighbor_right == copy_endpoint.get_path())
		assert(copy_endpoint.focus_neighbor_left == start_gateway.get_path())
		assert(stop_gateway.focus_neighbor_left == NodePath())
		assert(stop_gateway.focus_neighbor_right == NodePath())
		stop_gateway.disabled = false
		main.call("_wire_dedicated_gateway_focus")
		assert(start_gateway.focus_neighbor_right == stop_gateway.get_path())
		assert(stop_gateway.focus_neighbor_left == start_gateway.get_path())
		assert(stop_gateway.focus_neighbor_right == copy_endpoint.get_path())
		assert(copy_command.focus_neighbor_right == dedicated_back.get_path())
		var gateway_args: PackedStringArray = main.call("_gateway_args", {
			"host": "0.0.0.0",
			"port": 27999,
			"password": "secret",
			"auth_token": "token-123",
			"max_players": 4,
			"closed": true,
			"ban_players": "Mallory, Eve",
		})
		_assert_arg_pair(gateway_args, "--host", "0.0.0.0")
		_assert_arg_pair(gateway_args, "--port", "27999")
		_assert_arg_pair(gateway_args, "--password", "secret")
		_assert_arg_pair(gateway_args, "--auth-token", "token-123")
		_assert_arg_pair(gateway_args, "--max-players", "4")
		var gateway_args_array := Array(gateway_args)
		assert(gateway_args_array.has("--closed"))
		assert(gateway_args_array.count("--ban-player") == 2)
		assert(gateway_args_array.has("Mallory"))
		assert(gateway_args_array.has("Eve"))
		assert(str(main.call("_gateway_endpoint", {"host": "0.0.0.0", "port": 27999})) == "ws://127.0.0.1:27999")
		assert(str(main.call("_gateway_endpoint", {"host": "::1", "port": 27999})) == "ws://[::1]:27999")
		assert(str(main.call("_gateway_policy_summary", {
			"password": "secret",
			"auth_token": "token-123",
			"max_players": 4,
			"closed": true,
			"ban_players": "Mallory, Eve",
		})) == "password on, auth on, max 4, joins closed, bans 2")
		var gateway_command_preview := str(main.call("_gateway_command_preview", {
			"host": "0.0.0.0",
			"port": 27999,
			"password": "secret",
			"auth_token": "token-123",
			"max_players": 4,
			"closed": true,
			"ban_players": "Bad Name",
		}))
		assert(gateway_command_preview.contains("groundfire-web-gateway --host 0.0.0.0 --port 27999"))
		assert(gateway_command_preview.contains("--password"))
		assert(gateway_command_preview.contains("<password>"))
		assert(gateway_command_preview.contains("--auth-token"))
		assert(gateway_command_preview.contains("<auth-token>"))
		assert(gateway_command_preview.contains("--ban-player \"Bad Name\""))
		assert(not gateway_command_preview.contains("secret"))
		assert(not gateway_command_preview.contains("token-123"))
	else:
		assert(not _has_button(main, "Dedicated Server"))
	main.call("_show_local_match_setup")
	await process_frame
	assert(_has_label(main, "Local Match Setup"))
	assert(_has_label(main, "Active"))
	assert(_has_label(main, "Color"))
	assert(_has_label(main, "Name"))
	assert(_has_label(main, "Controlled by"))
	assert(_has_label(main, "Controller"))
	assert(_has_label(main, "Rounds"))
	assert(_has_button(main, "Start Match"))
	assert(_has_button(main, "Back"))
	var setup_player_name := _find_control_with_text(main, "LineEdit", "Player") as LineEdit
	var setup_enemy_name := _find_control_with_text(main, "LineEdit", "Enemy") as LineEdit
	var roster: Array = main.call("_local_match_roster_snapshot")
	assert(roster.size() == 2)
	assert(str(Dictionary(roster[0]).get("kind", "")) == "human")
	assert(str(Dictionary(roster[1]).get("kind", "")) == "computer")
	assert(int(Dictionary(roster[0]).get("controller", -1)) == 0)
	var setup_rows: Array = main.get("_local_match_setup_rows")
	var first_active := Dictionary(setup_rows[0]).get("active") as BaseButton
	var second_active := Dictionary(setup_rows[1]).get("active") as BaseButton
	var third_active := Dictionary(setup_rows[2]).get("active") as BaseButton
	var first_slot := Dictionary(setup_rows[0]).get("slot") as OptionButton
	var first_controller := Dictionary(setup_rows[0]).get("controller") as OptionButton
	var second_controller := Dictionary(setup_rows[1]).get("controller") as OptionButton
	var second_slot := Dictionary(setup_rows[1]).get("slot") as OptionButton
	var third_name := Dictionary(setup_rows[2]).get("name") as LineEdit
	var third_slot := Dictionary(setup_rows[2]).get("slot") as OptionButton
	var third_controller := Dictionary(setup_rows[2]).get("controller") as OptionButton
	assert(first_active.button_pressed)
	assert(second_active.button_pressed)
	assert(not third_active.button_pressed)
	assert(first_slot.get_item_text(first_slot.selected) == "Human")
	assert(first_controller.selected == 0)
	assert(second_controller.disabled)
	assert(_has_label(main, "2 players ready  Human 1  Computer 1"))
	assert(second_active.focus_neighbor_right == setup_enemy_name.get_path())
	assert(second_slot.focus_neighbor_right == second_active.get_path())
	assert(second_controller.focus_neighbor_top == NodePath())
	assert(third_name.focus_mode == Control.FOCUS_NONE)
	third_active.button_pressed = true
	main.call("_on_local_match_setup_row_changed", 2)
	roster = main.call("_local_match_roster_snapshot")
	assert(roster.size() == 3)
	assert(_has_label(main, "3 players ready  Human 1  Computer 2"))
	assert(third_name.focus_mode == Control.FOCUS_ALL)
	assert(not third_slot.disabled)
	assert(third_controller.disabled)
	assert(third_active.focus_neighbor_right == third_name.get_path())
	assert(third_slot.focus_neighbor_right == third_active.get_path())
	assert(third_controller.focus_neighbor_top == NodePath())
	var setup_rounds := _find_option_button_with_items(main, PackedStringArray(["5", "10", "15", "20", "25", "30", "35", "40", "45", "50"]))
	var setup_start := _find_control_with_text(main, "Button", "Start Match") as Button
	var setup_back := _find_control_with_text(main, "Button", "Back") as Button
	assert(setup_player_name != null)
	assert(setup_enemy_name != null)
	assert(setup_rounds != null)
	assert(setup_start != null)
	assert(setup_back != null)
	assert(setup_player_name.focus_neighbor_bottom != NodePath())
	assert(setup_enemy_name.focus_neighbor_bottom != NodePath())
	assert(setup_rounds.focus_neighbor_top != NodePath())
	assert(setup_rounds.focus_neighbor_bottom == setup_start.get_path())
	assert(setup_start.focus_neighbor_right == setup_back.get_path())
	assert(setup_back.focus_neighbor_left == setup_start.get_path())
	assert(setup_start.focus_neighbor_top == setup_rounds.get_path())
	assert(setup_back.focus_neighbor_top == setup_rounds.get_path())
	first_slot.select(1)
	main.call("_on_local_match_setup_row_changed", 0)
	assert(setup_start.disabled)
	assert(_has_label(main, "Add at least 1 human player to start."))
	first_slot.select(0)
	main.call("_on_local_match_setup_row_changed", 0)
	assert(not setup_start.disabled)
	second_active.button_pressed = false
	third_active.button_pressed = false
	main.call("_on_local_match_setup_row_changed", 1)
	main.call("_on_local_match_setup_row_changed", 2)
	assert(setup_start.disabled)
	assert(_has_label(main, "Enable at least 2 players to start."))
	main.call("_show_options")
	await process_frame
	assert(_has_label(main, "Options"))
	assert(_has_label(main, "Video"))
	assert(_has_label(main, "Audio"))
	assert(_has_label(main, "Gameplay"))
	assert(_has_label(main, "Controls"))
	assert(_has_label(main, "Resolution"))
	assert(_has_label(main, "Resolution:"))
	assert(_has_label(main, "Screen Mode:"))
	assert(_has_label(main, "AI Difficulty"))
	assert(_has_label(main, "Online"))
	assert(_has_label(main, "Directory Environment"))
	assert(_has_label(main, "Override URL"))
	assert(_has_label(main, "Dev URL"))
	assert(_has_label(main, "Staging URL"))
	assert(_has_label(main, "Production URL"))
	assert(_has_label(main, "Gamepad Profile"))
	assert(_has_button(main, "Set Controls"))
	assert(_has_button(main, "Apply"))
	assert(_has_button(main, "Back"))
	var classic_resolution := _find_classic_selector_with_items(main, PackedStringArray(["640 x 480", "800 x 600", "1024 x 768", "1280 x 960", "1280 x 1024", "1600 x 1200"]))
	var screen_mode := _find_classic_selector_with_items(main, PackedStringArray(["Fullscreen", "Windowed"]))
	var set_controls := _find_control_with_text(main, "Button", "Set Controls") as Button
	var resolution_label := _find_control_with_text(main, "Label", "Resolution:") as Label
	var show_fps := _find_control_with_text(main, "CheckButton", "Show FPS") as CheckButton
	var fullscreen := _find_control_with_text(main, "CheckButton", "Fullscreen") as CheckButton
	var audio_enabled := _find_control_with_text(main, "CheckButton", "Audio Enabled") as CheckButton
	var options_apply := _find_control_with_text(main, "Button", "Apply") as Button
	var options_back := _find_control_with_text(main, "Button", "Back") as Button
	assert(classic_resolution != null)
	assert(screen_mode != null)
	assert(set_controls != null)
	assert(resolution_label != null)
	assert(show_fps != null)
	assert(fullscreen != null)
	assert(audio_enabled != null)
	assert(options_apply != null)
	assert(options_back != null)
	assert(classic_resolution.custom_minimum_size.x >= 220.0)
	assert(screen_mode.custom_minimum_size.y >= 29.0)
	assert(classic_resolution.item_count == 6)
	assert(screen_mode.item_count == 2)
	assert(classic_resolution.has_method("set_disabled"))
	assert(screen_mode.focus_mode == Control.FOCUS_ALL)
	_assert_classic_text_effect(classic_resolution)
	_assert_classic_text_effect(set_controls)
	_assert_classic_text_effect(resolution_label)
	_assert_classic_hover_color(set_controls)
	assert(classic_resolution.focus_neighbor_bottom == screen_mode.get_path())
	assert(screen_mode.focus_neighbor_top == classic_resolution.get_path())
	assert(screen_mode.focus_neighbor_bottom == set_controls.get_path())
	assert(set_controls.focus_neighbor_top == screen_mode.get_path())
	assert(set_controls.focus_neighbor_bottom == show_fps.get_path())
	assert(show_fps.focus_neighbor_top == set_controls.get_path())
	assert(show_fps.focus_neighbor_bottom == fullscreen.get_path())
	assert(options_apply.focus_neighbor_bottom == options_back.get_path())
	assert(options_back.focus_neighbor_top == options_apply.get_path())
	assert(options_back.focus_neighbor_bottom == classic_resolution.get_path())
	assert(options_back.focus_neighbor_left == options_back.get_path())
	assert(options_back.focus_neighbor_right == options_back.get_path())

	main.call("_start_local_match", 5)
	await process_frame
	await process_frame
	var paused_match := main.get("_screen") as Control
	assert(paused_match != null)
	paused_match.call("_open_options_from_pause")
	await process_frame
	await process_frame
	assert(_has_label(main, "Options"))
	assert(paused_match.get_parent() == null)
	assert(not paused_match.visible)
	options_back = _find_control_with_text(main, "Button", "Back") as Button
	assert(options_back != null)
	options_back.emit_signal("pressed")
	await process_frame
	await process_frame
	assert(paused_match.get_parent() != null)
	assert(paused_match.visible)
	assert(bool(paused_match.get("_is_paused")))
	assert((paused_match.get_node("PauseOverlay") as Control).visible)
	await _free_node(main)


func _check_main_menu_responsive_metrics() -> void:
	var original_size := root.size
	var sizes := [
		Vector2i(640, 480),
		Vector2i(1024, 768),
		Vector2i(1280, 720),
		Vector2i(1600, 900),
		Vector2i(1920, 720),
	]
	for viewport_size in sizes:
		root.size = viewport_size
		var main := MainScene.instantiate()
		root.add_child(main)
		await process_frame
		await process_frame
		var logo := _find_first(main, "TextureRect") as TextureRect
		var start_button := _find_control_with_text(main, "Button", "Start Game") as Button
		var find_servers := _find_control_with_text(main, "Button", "Find Servers") as Button
		assert(logo != null)
		assert(start_button != null)
		assert(find_servers != null)
		assert(logo.custom_minimum_size.x >= 590.0)
		assert(logo.custom_minimum_size.x <= 920.0)
		assert(start_button.custom_minimum_size.x <= 414.0)
		assert(start_button.custom_minimum_size.y >= 34.0)
		assert(start_button.focus_neighbor_bottom == find_servers.get_path())
		await _free_node(main)
	root.size = original_size


func _check_menu_subscreen_responsive_metrics() -> void:
	var original_size := root.size
	var sizes := [
		Vector2i(640, 480),
		Vector2i(1024, 768),
		Vector2i(1600, 900),
	]
	for viewport_size in sizes:
		root.size = viewport_size
		var main := MainScene.instantiate()
		root.add_child(main)
		await process_frame
		await process_frame
		main.call("_show_options")
		await process_frame
		var options_scroll := _find_first(main, "ScrollContainer") as ScrollContainer
		var options_back := _find_control_with_text(main, "Button", "Back") as Button
		var classic_resolution := _find_classic_selector_with_items(main, PackedStringArray(["640 x 480", "800 x 600", "1024 x 768", "1280 x 960", "1280 x 1024", "1600 x 1200"]))
		var screen_mode := _find_classic_selector_with_items(main, PackedStringArray(["Fullscreen", "Windowed"]))
		var set_controls := _find_control_with_text(main, "Button", "Set Controls") as Button
		var show_fps := _find_control_with_text(main, "CheckButton", "Show FPS") as CheckButton
		assert(options_scroll != null)
		assert(options_scroll.horizontal_scroll_mode == ScrollContainer.SCROLL_MODE_DISABLED)
		assert(options_back != null)
		assert(classic_resolution != null)
		assert(screen_mode != null)
		assert(set_controls != null)
		assert(show_fps != null)
		assert(options_scroll.custom_minimum_size.x <= float(viewport_size.x))
		assert(options_scroll.custom_minimum_size.y <= float(viewport_size.y))
		assert(classic_resolution.custom_minimum_size.x <= float(viewport_size.x))
		assert(screen_mode.focus_neighbor_bottom == set_controls.get_path())
		assert(set_controls.focus_neighbor_bottom == show_fps.get_path())
		assert(options_back.focus_neighbor_bottom == classic_resolution.get_path())
		main.call("_show_local_match_setup")
		await process_frame
		var setup_start := _find_control_with_text(main, "Button", "Start Match") as Button
		var setup_back := _find_control_with_text(main, "Button", "Back") as Button
		assert(setup_start != null)
		assert(setup_back != null)
		assert(setup_start.focus_neighbor_right == setup_back.get_path())
		assert(setup_back.focus_neighbor_left == setup_start.get_path())
		if not OS.has_feature("web"):
			main.call("_show_dedicated_server_tools")
			await process_frame
			var start_gateway := _find_control_with_text(main, "Button", "Start Gateway") as Button
			var copy_endpoint := _find_control_with_text(main, "Button", "Copy Endpoint") as Button
			var dedicated_back := _find_control_with_text(main, "Button", "Back") as Button
			assert(start_gateway != null)
			assert(copy_endpoint != null)
			assert(dedicated_back != null)
			assert(start_gateway.focus_neighbor_right == copy_endpoint.get_path())
			assert(dedicated_back.focus_neighbor_left != NodePath())
		await _free_node(main)
	root.size = original_size


func _check_server_browser_scene() -> void:
	var browser := ServerBrowserScene.instantiate()
	root.add_child(browser)
	await process_frame
	await process_frame
	assert(_has_label(browser, "Servers"))
	assert(_has_button(browser, "Change Filters"))
	assert(_has_button(browser, "Add Favorite"))
	assert(_has_button(browser, "Quick Refresh"))
	assert(_has_button(browser, "Refresh All"))
	assert(_has_button(browser, "Connect"))
	var change_filters := _find_control_with_text(browser, "Button", "Change Filters") as Button
	var add_favorite := _find_control_with_text(browser, "Button", "Add Favorite") as Button
	var connect := _find_control_with_text(browser, "Button", "Connect") as Button
	assert(change_filters != null)
	assert(add_favorite != null)
	assert(connect != null)
	assert(add_favorite.disabled)
	assert(connect.disabled)
	assert(add_favorite.focus_neighbor_left == NodePath())
	assert(add_favorite.focus_neighbor_right == NodePath())
	assert(connect.focus_neighbor_left == NodePath())
	assert(connect.focus_neighbor_right == NodePath())
	assert(change_filters.focus_neighbor_right != add_favorite.get_path())
	var tabs := _find_first(browser, "TabBar") as TabBar
	assert(tabs != null)
	assert(tabs.tab_count >= 3)
	var table_scroll := _find_first(browser, "ScrollContainer") as ScrollContainer
	assert(table_scroll != null)
	assert(table_scroll.horizontal_scroll_mode == ScrollContainer.SCROLL_MODE_DISABLED)
	assert(table_scroll.vertical_scroll_mode == ScrollContainer.SCROLL_MODE_AUTO)
	if not OS.has_feature("web"):
		assert(_tab_titles(tabs).has("LAN"))
	await _free_node(browser)


func _check_server_browser_responsive_metrics() -> void:
	var original_size := root.size
	var sizes := [
		Vector2i(640, 480),
		Vector2i(1024, 768),
		Vector2i(1600, 900),
	]
	for viewport_size in sizes:
		root.size = viewport_size
		var browser := ServerBrowserScene.instantiate()
		browser.anchor_right = 0.0
		browser.anchor_bottom = 0.0
		browser.size = Vector2(viewport_size)
		root.add_child(browser)
		await process_frame
		await process_frame
		browser.call("_apply_responsive_table_metrics")
		var table_scroll := _find_first(browser, "ScrollContainer") as ScrollContainer
		assert(table_scroll != null)
		assert(table_scroll.horizontal_scroll_mode == ScrollContainer.SCROLL_MODE_DISABLED)
		assert(table_scroll.custom_minimum_size.x <= float(viewport_size.x))
		assert(table_scroll.custom_minimum_size.y <= float(viewport_size.y))
		assert(table_scroll.custom_minimum_size.x >= 440.0)
		await _free_node(browser)
	root.size = original_size


func _check_local_match_scene() -> void:
	var local_match := LocalMatchScene.instantiate()
	local_match.setup({
		"total_rounds": 15,
		"player_name": "Pilot",
		"enemy_name": "CPU",
		"roster": [
			{"slot": 0, "name": "Pilot", "kind": "human", "controller": 0, "color": Color("#ff00ff")},
			{"slot": 1, "name": "CPU", "kind": "computer", "controller": -1, "color": Color("#4d95ff")},
			{"slot": 2, "name": "Spare", "kind": "computer", "controller": -1, "color": Color("#00ff00")},
		],
	})
	root.add_child(local_match)
	await process_frame
	await process_frame
	assert(int(local_match.get("_total_rounds")) == 15)
	var player_tank: RefCounted = local_match.get("_player")
	var enemy_tank: RefCounted = local_match.get("_enemy")
	assert(player_tank.get("name") == "Pilot")
	assert(enemy_tank.get("name") == "CPU")
	var participants: Array = local_match.get("_participants")
	assert(participants.size() == 3)
	assert(Dictionary(participants[2]).get("tank") != null)
	assert(int(local_match.call("_living_participant_count")) == 3)
	local_match.call("_set_turn_index", 0)
	local_match.set("_last_shot_owner", "Player")
	local_match.call("_start_next_turn_or_round")
	assert(str(local_match.get("_turn_owner")) == "Enemy")
	var spare_tank: RefCounted = Dictionary(participants[2]).get("tank")
	enemy_tank.set("state", "dead")
	local_match.set("_last_shot_owner", "Player")
	local_match.call("_start_next_turn_or_round")
	assert(str(local_match.get("_turn_owner")) == "Slot 3")
	enemy_tank.set("state", "alive")
	assert(spare_tank != null)
	var score_rows: Array = local_match.call("_score_rows_snapshot")
	assert(score_rows.size() == 3)
	assert(str(Dictionary(score_rows[2]).get("name", "")) == "Spare")
	var winner_rows: Array = local_match.call("_winner_rows_snapshot")
	assert(winner_rows.size() == 3)
	assert(local_match.get_node_or_null("PauseOverlay") != null)
	assert(_has_button(local_match, "Resume"))
	assert(_has_button(local_match, "Options"))
	assert(_has_button(local_match, "Restart Round"))
	assert(_has_button(local_match, "Main Menu"))
	var pause_resume := _find_control_with_text(local_match, "Button", "Resume") as Button
	var pause_options := _find_control_with_text(local_match, "Button", "Options") as Button
	var pause_main_menu := _find_control_with_text(local_match, "Button", "Main Menu") as Button
	assert(pause_resume != null)
	assert(pause_options != null)
	assert(pause_main_menu != null)
	assert(pause_resume.focus_neighbor_bottom == pause_options.get_path())
	assert(pause_options.focus_neighbor_top == pause_resume.get_path())
	assert(pause_resume.focus_neighbor_top == pause_main_menu.get_path())
	assert(pause_resume.focus_neighbor_left == pause_resume.get_path())
	assert(pause_resume.focus_neighbor_right == pause_resume.get_path())
	assert(pause_options.focus_neighbor_left == pause_options.get_path())
	assert(pause_options.focus_neighbor_right == pause_options.get_path())
	await _free_node(local_match)


func _check_online_match_scene() -> void:
	var online_match := OnlineMatchScene.instantiate()
	online_match.setup({"endpoint": "ws://127.0.0.1:9", "name": "Smoke Endpoint"})
	root.add_child(online_match)
	await process_frame
	await process_frame
	assert(_has_button(online_match, "Reconnect"))
	assert(_has_button(online_match, "Back"))
	var reconnect := _find_control_with_text(online_match, "Button", "Reconnect") as Button
	var online_back := _find_control_with_text(online_match, "Button", "Back") as Button
	assert(reconnect != null)
	assert(online_back != null)
	assert(reconnect.focus_neighbor_left == online_back.get_path())
	assert(reconnect.focus_neighbor_right == online_back.get_path())
	assert(reconnect.focus_neighbor_top == reconnect.get_path())
	assert(reconnect.focus_neighbor_bottom == reconnect.get_path())
	assert(online_back.focus_neighbor_left == reconnect.get_path())
	assert(online_back.focus_neighbor_right == reconnect.get_path())
	assert(online_back.focus_neighbor_top == online_back.get_path())
	assert(online_back.focus_neighbor_bottom == online_back.get_path())
	await _free_node(online_match)


func _free_node(node: Node) -> void:
	if node == null:
		return
	if node.has_method("_prepare_for_shutdown"):
		node.call("_prepare_for_shutdown")
	await process_frame
	node.queue_free()
	await _drain_frames(SHUTDOWN_DRAIN_FRAMES)


func _drain_frames(count: int) -> void:
	for index in range(count):
		await process_frame


func _has_button(node: Node, text: String) -> bool:
	return _find_control_with_text(node, "Button", text) != null


func _has_label(node: Node, text: String) -> bool:
	return _find_control_with_text(node, "Label", text) != null


func _find_control_with_text(node: Node, target_class: String, text: String) -> Control:
	if node.is_class(target_class) and str(node.get("text")) == text:
		return node as Control
	for child in node.get_children():
		var found := _find_control_with_text(child, target_class, text)
		if found != null:
			return found
	return null


func _find_first(node: Node, target_class: String) -> Node:
	if node.is_class(target_class):
		return node
	for child in node.get_children():
		var found := _find_first(child, target_class)
		if found != null:
			return found
	return null


func _find_option_button_with_items(node: Node, items: PackedStringArray) -> OptionButton:
	if node is OptionButton and node.item_count == items.size():
		var option := node as OptionButton
		var matches := true
		for index in range(items.size()):
			if option.get_item_text(index) != items[index]:
				matches = false
				break
		if matches:
			return option
	for child in node.get_children():
		var found := _find_option_button_with_items(child, items)
		if found != null:
			return found
	return null


func _find_classic_selector_with_items(node: Node, items: PackedStringArray) -> ClassicSelector:
	if node is ClassicSelector and int(node.get("item_count")) == items.size():
		var selector := node as ClassicSelector
		var matches := true
		for index in range(items.size()):
			if selector.get_item_text(index) != items[index]:
				matches = false
				break
		if matches:
			return selector
	for child in node.get_children():
		var found := _find_classic_selector_with_items(child, items)
		if found != null:
			return found
	return null


func _tab_titles(tabs: TabBar) -> PackedStringArray:
	var titles := PackedStringArray()
	for index in range(tabs.tab_count):
		titles.append(tabs.get_tab_title(index))
	return titles


func _assert_arg_pair(args: PackedStringArray, arg_name: String, expected_value: String) -> void:
	var args_array := Array(args)
	var index := args_array.find(arg_name)
	assert(index >= 0)
	assert(index + 1 < args.size())
	assert(str(args[index + 1]) == expected_value)


func _assert_classic_text_effect(control: Control) -> void:
	if control.has_method("uses_classic_font_atlas"):
		assert(control.call("uses_classic_font_atlas"))
		return
	assert(control.get_theme_color("font_shadow_color") == GroundfireTheme.CLASSIC_TEXT_SHADOW_COLOR)
	assert(control.get_theme_color("font_outline_color") == GroundfireTheme.CLASSIC_TEXT_OUTLINE_COLOR)
	assert(control.get_theme_constant("shadow_offset_x") == GroundfireTheme.CLASSIC_TEXT_SHADOW_OFFSET_X)
	assert(control.get_theme_constant("shadow_offset_y") == GroundfireTheme.CLASSIC_TEXT_SHADOW_OFFSET_Y)
	assert(control.get_theme_constant("outline_size") == GroundfireTheme.CLASSIC_TEXT_OUTLINE_SIZE)


func _assert_classic_hover_color(control: Control) -> void:
	if control.has_method("classic_hover_color"):
		assert(control.call("classic_hover_color") == GroundfireTheme.COLOR_WARN)
		return
	assert(control.get_theme_color("font_hover_color") == GroundfireTheme.COLOR_WARN)
