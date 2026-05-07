extends RefCounted

const DEFAULT_STORE_PATH := "user://server_browser_store.json"
const MAX_HISTORY := 20


static func load_store(path := DEFAULT_STORE_PATH) -> Dictionary:
	var defaults := {"favorites": [], "history": []}
	if not FileAccess.file_exists(path):
		return defaults
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return defaults
	var parsed = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		return defaults
	return {
		"favorites": _string_array(parsed.get("favorites", [])),
		"history": _entry_array(parsed.get("history", [])),
	}


static func save_store(favorites: Array[String], history: Array[Dictionary], path := DEFAULT_STORE_PATH) -> void:
	var payload := {
		"favorites": favorites,
		"history": history.slice(0, MAX_HISTORY),
	}
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(payload, "\t"))


static func remember_favorite(favorites: Array[String], endpoint: String) -> Array[String]:
	var next := favorites.duplicate()
	if endpoint != "" and not next.has(endpoint):
		next.append(endpoint)
	return next


static func remember_history(history: Array[Dictionary], entry: Dictionary) -> Array[Dictionary]:
	var endpoint := str(entry.get("endpoint", ""))
	var next: Array[Dictionary] = []
	if endpoint == "":
		return history
	next.append(entry)
	for item in history:
		if str(item.get("endpoint", "")) != endpoint:
			next.append(item)
	return next.slice(0, MAX_HISTORY)


static func _string_array(value) -> Array[String]:
	var result: Array[String] = []
	if typeof(value) != TYPE_ARRAY:
		return result
	for item in value:
		result.append(str(item))
	return result


static func _entry_array(value) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if typeof(value) != TYPE_ARRAY:
		return result
	for item in value:
		if typeof(item) == TYPE_DICTIONARY:
			result.append(item)
	return result
