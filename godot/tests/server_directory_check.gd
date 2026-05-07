extends SceneTree

const ServerDirectory := preload("res://scripts/server_directory.gd")


func _init() -> void:
	var web_entries := ServerDirectory.browser_entries(false)
	for entry in web_entries:
		assert(entry.get("source", "") != ServerDirectory.SOURCE_LAN)

	var desktop_entries := ServerDirectory.browser_entries(true)
	assert(desktop_entries.size() > web_entries.size())
	assert(desktop_entries.any(func(entry: Dictionary) -> bool: return entry.get("source", "") == ServerDirectory.SOURCE_LAN))

	var internet_entries := ServerDirectory.filter_for_tab(desktop_entries, "Internet")
	assert(internet_entries.all(func(entry: Dictionary) -> bool: return entry.get("source", "") == ServerDirectory.SOURCE_ONLINE))

	var lan_entries := ServerDirectory.filter_for_tab(desktop_entries, "LAN")
	assert(lan_entries.all(func(entry: Dictionary) -> bool: return entry.get("source", "") == ServerDirectory.SOURCE_LAN))
	quit(0)
