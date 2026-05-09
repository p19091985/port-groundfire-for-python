extends SceneTree

const MainScene := preload("res://scenes/main.tscn")
const LocalMatchScene := preload("res://scenes/local_match.tscn")
const OnlineMatchScene := preload("res://scenes/online_match.tscn")
const ServerBrowserScene := preload("res://scenes/server_browser.tscn")
const PlatformCapabilities := preload("res://scripts/platform_capabilities.gd")
const ServerDirectory := preload("res://scripts/server_directory.gd")


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(1024, 768)
	_check_platform_capability_matrix()
	_check_directory_http_schema()
	await _check_main_menu_and_options()
	await _check_server_browser_scene()
	await _check_local_match_scene()
	await _check_online_match_scene()
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
	assert(_has_button(main, "Start Local Match"))
	assert(_has_button(main, "Find Servers"))
	assert(_has_button(main, "Options"))
	assert(_has_button(main, "Quit"))
	if not OS.has_feature("web"):
		assert(_has_button(main, "Dedicated Server"))
	else:
		assert(not _has_button(main, "Dedicated Server"))
	main.call("_show_options")
	await process_frame
	assert(_has_label(main, "Options"))
	assert(_has_label(main, "Gameplay"))
	assert(_has_label(main, "Controls"))
	assert(_has_label(main, "Resolution"))
	assert(_has_label(main, "AI Difficulty"))
	assert(_has_label(main, "Online"))
	assert(_has_label(main, "Directory Environment"))
	assert(_has_label(main, "Override URL"))
	assert(_has_label(main, "Dev URL"))
	assert(_has_label(main, "Staging URL"))
	assert(_has_label(main, "Production URL"))
	assert(_has_label(main, "Gamepad Profile"))
	assert(_has_button(main, "Back"))
	main.queue_free()
	await process_frame


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
	var tabs := _find_first(browser, "TabBar") as TabBar
	assert(tabs != null)
	assert(tabs.tab_count >= 3)
	if not OS.has_feature("web"):
		assert(_tab_titles(tabs).has("LAN"))
	browser.queue_free()
	await process_frame


func _check_local_match_scene() -> void:
	var local_match := LocalMatchScene.instantiate()
	root.add_child(local_match)
	await process_frame
	await process_frame
	assert(local_match.get_node_or_null("PauseOverlay") != null)
	assert(_has_button(local_match, "Resume"))
	assert(_has_button(local_match, "Options"))
	assert(_has_button(local_match, "Restart Round"))
	assert(_has_button(local_match, "Main Menu"))
	local_match.queue_free()
	await process_frame


func _check_online_match_scene() -> void:
	var online_match := OnlineMatchScene.instantiate()
	online_match.setup({"endpoint": "ws://127.0.0.1:9", "name": "Smoke Endpoint"})
	root.add_child(online_match)
	await process_frame
	await process_frame
	assert(_has_button(online_match, "Reconnect"))
	assert(_has_button(online_match, "Back"))
	online_match.queue_free()
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


func _tab_titles(tabs: TabBar) -> PackedStringArray:
	var titles := PackedStringArray()
	for index in range(tabs.tab_count):
		titles.append(tabs.get_tab_title(index))
	return titles
