extends RefCounted

const DEFAULT_STORE_PATH := "user://server_browser_store.json"
const MAX_HISTORY := 20


static func default_filters() -> Dictionary:
	return {
		"text": "",
		"hide_passworded": false,
		"hide_full": false,
		"hide_empty": false,
		"secure_only": false,
		"region": "",
		"max_latency": 0,
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


static func filter_state(
	text: String,
	hide_passworded: bool,
	hide_full: bool,
	sort_mode: String,
	hide_empty := false,
	secure_only := false,
	region := "",
	max_latency := 0
) -> Dictionary:
	return normalize_filters({
		"text": text,
		"hide_passworded": hide_passworded,
		"hide_full": hide_full,
		"hide_empty": hide_empty,
		"secure_only": secure_only,
		"region": region,
		"max_latency": max_latency,
		"sort_mode": sort_mode,
	})


static func normalize_filters(value) -> Dictionary:
	var filters := default_filters()
	if typeof(value) != TYPE_DICTIONARY:
		return filters
	filters["text"] = str(value.get("text", filters["text"]))
	filters["hide_passworded"] = _bool_value(value.get("hide_passworded", filters["hide_passworded"]), false)
	filters["hide_full"] = _bool_value(value.get("hide_full", filters["hide_full"]), false)
	filters["hide_empty"] = _bool_value(value.get("hide_empty", filters["hide_empty"]), false)
	filters["secure_only"] = _bool_value(value.get("secure_only", filters["secure_only"]), false)
	filters["region"] = str(value.get("region", filters["region"])).to_lower().strip_edges()
	filters["max_latency"] = max(0, int(value.get("max_latency", filters["max_latency"])))
	var sort_mode := str(value.get("sort_mode", filters["sort_mode"])).to_lower()
	if ["latency", "name", "players"].has(sort_mode):
		filters["sort_mode"] = sort_mode
	return filters


static func filter_entries(entries: Array[Dictionary], value) -> Array[Dictionary]:
	var filters := normalize_filters(value)
	var result: Array[Dictionary] = []
	var text := str(filters["text"]).to_lower()
	for entry in entries:
		var counts := _player_counts(entry)
		if bool(filters["hide_passworded"]) and _entry_bool(entry, "passworded", false):
			continue
		if bool(filters["hide_full"]) and counts.y > 0 and counts.x >= counts.y:
			continue
		if bool(filters["hide_empty"]) and counts.x <= 0:
			continue
		if bool(filters["secure_only"]) and not _entry_secure(entry):
			continue
		var region := str(filters["region"])
		if not region.is_empty() and str(entry.get("region", "world")).to_lower() != region:
			continue
		var max_latency := int(filters["max_latency"])
		if max_latency > 0 and _entry_latency(entry) > max_latency:
			continue
		if not text.is_empty() and not _entry_search_text(entry).contains(text):
			continue
		result.append(entry)
	return result


static func _entry_search_text(entry: Dictionary) -> String:
	return ("%s %s %s" % [entry.get("name", ""), entry.get("map", ""), entry.get("endpoint", "")]).to_lower()


static func _entry_bool(entry: Dictionary, key: String, fallback: bool) -> bool:
	var value = entry.get(key, fallback)
	if typeof(value) == TYPE_BOOL:
		return bool(value)
	return str(value).to_lower() == "true"


static func _entry_secure(entry: Dictionary) -> bool:
	if entry.has("secure"):
		return _entry_bool(entry, "secure", false)
	return str(entry.get("endpoint", "")).begins_with("wss://")


static func _player_counts(entry: Dictionary) -> Vector2i:
	var parts := str(entry.get("players", "0/0")).split("/")
	if parts.size() != 2:
		return Vector2i.ZERO
	return Vector2i(_safe_int(parts[0]), _safe_int(parts[1]))


static func _entry_latency(entry: Dictionary) -> int:
	var value := str(entry.get("latency", "9999")).to_lower().replace("ms", "").strip_edges()
	if value == "lan":
		return 0
	return _safe_int(value, 9999)


static func _safe_int(value: String, fallback := 0) -> int:
	return int(value) if value.is_valid_int() else fallback


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
