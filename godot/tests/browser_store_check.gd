extends SceneTree

const BrowserStore := preload("res://scripts/browser_store.gd")


func _init() -> void:
	var path := "user://browser_store_check.json"
	var favorite_endpoint := "wss://play.groundfire.local/servers/test"
	var history_entry := {
		"name": "Groundfire Online Test",
		"endpoint": favorite_endpoint,
		"source": "online",
	}

	var favorites := BrowserStore.remember_favorite([], favorite_endpoint)
	assert(favorites.size() == 1)
	assert(BrowserStore.remember_favorite(favorites, favorite_endpoint).size() == 1)

	var history := BrowserStore.remember_history([], history_entry)
	assert(history.size() == 1)
	BrowserStore.save_store(favorites, history, path)

	var loaded := BrowserStore.load_store(path)
	assert(loaded.get("favorites", []).has(favorite_endpoint))
	assert(loaded.get("history", []).size() == 1)
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	quit(0)
