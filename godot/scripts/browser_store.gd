extends RefCounted

const DEFAULT_STORE_PATH := "user://server_browser_store.json"
const MAX_HISTORY := 20


static func default_filters() -> Dictionary:
	return {
		"text": "",
		"hide_passworded": false,
		"hide_full": false,
		"sort_mode": "latency",
	}


static func load_store(path := DEFAULT_STORE_PATH) -> Dictionary:
	var defaults := {"favorites": [], "history": [], "filters": default_filters()}
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
		"filters": normalize_filters(parsed.get("filters", {})),
	}


static func save_store(
	favorites: Array[String],
	history: Array[Dictionary],
	filters := {},
	path := DEFAULT_STORE_PATH
) -> void:
	var store_path := path
	var filter_payload = filters
	if typeof(filters) == TYPE_STRING:
		store_path = str(filters)
		filter_payload = {}
	var payload := {
		"favorites": favorites,
		"history": history.slice(0, MAX_HISTORY),
		"filters": normalize_filters(filter_payload),
	}
	var file := FileAccess.open(store_path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(payload, "\t"))


static func remember_favorite(favorites: Array[String], endpoint: String) -> Array[String]:
	var next := favorites.duplicate()
	if endpoint != "" and not next.has(endpoint):
		next.append(endpoint)
	return next


static func forget_favorite(favorites: Array[String], endpoint: String) -> Array[String]:
	var next: Array[String] = []
	for item in favorites:
		if item != endpoint:
			next.append(item)
	return next


static func clear_history() -> Array[Dictionary]:
	return []


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


static func filter_state(text: String, hide_passworded: bool, hide_full: bool, sort_mode: String) -> Dictionary:
	return normalize_filters({
		"text": text,
		"hide_passworded": hide_passworded,
		"hide_full": hide_full,
		"sort_mode": sort_mode,
	})


static func normalize_filters(value) -> Dictionary:
	var filters := default_filters()
	if typeof(value) != TYPE_DICTIONARY:
		return filters
	filters["text"] = str(value.get("text", filters["text"]))
	filters["hide_passworded"] = _bool_value(value.get("hide_passworded", filters["hide_passworded"]), false)
	filters["hide_full"] = _bool_value(value.get("hide_full", filters["hide_full"]), false)
	var sort_mode := str(value.get("sort_mode", filters["sort_mode"])).to_lower()
	if ["latency", "name", "players"].has(sort_mode):
		filters["sort_mode"] = sort_mode
	return filters


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


static func _bool_value(value, fallback: bool) -> bool:
	if typeof(value) == TYPE_BOOL:
		return value
	if typeof(value) == TYPE_STRING:
		return str(value).to_lower() == "true"
	if typeof(value) == TYPE_INT:
		return int(value) != 0
	return fallback
