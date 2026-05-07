extends RefCounted

const SOURCE_ONLINE := "online"
const SOURCE_LAN := "lan"
const DEFAULT_DIRECTORY_PATH := "res://data/server_directory.json"
const SERVER_DIRECTORY_SETTING := "application/config/server_directory_url"
const DIRECTORY_SCHEMA_VERSION := 1
const HTTP_TIMEOUT_SECONDS := 8.0
const HTTP_RETRY_LIMIT := 1


static func configured_directory_url() -> String:
	return str(ProjectSettings.get_setting(SERVER_DIRECTORY_SETTING, ""))


static func refresh_from_http(request: HTTPRequest, url: String) -> int:
	request.timeout = HTTP_TIMEOUT_SECONDS
	return request.request(url, PackedStringArray(), HTTPClient.METHOD_GET)


static func should_retry_directory_request(result: int, response_code: int, attempt: int) -> bool:
	if attempt >= HTTP_RETRY_LIMIT:
		return false
	return result != HTTPRequest.RESULT_SUCCESS or response_code == 0 or response_code >= 500


static func http_diagnostic(result: int, response_code: int) -> String:
	if result == HTTPRequest.RESULT_TIMEOUT:
		return "request timed out"
	if result != HTTPRequest.RESULT_SUCCESS:
		return "request failed with result %d" % result
	if response_code == 0:
		return "no HTTP response"
	return "HTTP %d" % response_code


static func expected_schema() -> Dictionary:
	return {
		"schema": DIRECTORY_SCHEMA_VERSION,
		"servers": ["name", "game", "players", "map", "latency", "source", "endpoint", "passworded"],
	}


static func entries_from_http_body(body: PackedByteArray, include_lan := false) -> Array[Dictionary]:
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return []
	return _entries_from_dictionary(parsed, include_lan)


static func browser_entries(include_lan := false, directory_path := DEFAULT_DIRECTORY_PATH) -> Array[Dictionary]:
	var entries := _load_directory(directory_path, include_lan)
	return entries


static func _filter_lan(entries: Array[Dictionary], include_lan: bool) -> Array[Dictionary]:
	if include_lan:
		return entries
	return entries.filter(func(entry: Dictionary) -> bool: return entry.get("source", "") != SOURCE_LAN)


static func _load_directory(directory_path: String, include_lan := false) -> Array[Dictionary]:
	if not FileAccess.file_exists(directory_path):
		return []
	var file := FileAccess.open(directory_path, FileAccess.READ)
	if file == null:
		return []
	var parsed = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		return []
	return _entries_from_dictionary(parsed, include_lan)


static func _entries_from_dictionary(parsed: Dictionary, include_lan := false) -> Array[Dictionary]:
	var servers = parsed.get("servers", [])
	if typeof(servers) != TYPE_ARRAY:
		return []

	var entries: Array[Dictionary] = []
	for item in servers:
		if typeof(item) == TYPE_DICTIONARY:
			entries.append(_normalize_entry(item))
	return _filter_lan(entries, include_lan)


static func _normalize_entry(raw: Dictionary) -> Dictionary:
	return {
		"name": str(raw.get("name", "")),
		"game": str(raw.get("game", "Groundfire")),
		"players": str(raw.get("players", "-")),
		"map": str(raw.get("map", "-")),
		"latency": str(raw.get("latency", "-")),
		"source": str(raw.get("source", SOURCE_ONLINE)),
		"endpoint": str(raw.get("endpoint", "")),
		"passworded": str(raw.get("passworded", "false")),
	}


static func filter_for_tab(entries: Array[Dictionary], tab_name: String) -> Array[Dictionary]:
	var normalized := tab_name.to_lower()
	if normalized == "internet":
		return entries.filter(func(entry: Dictionary) -> bool: return entry.get("source", "") == SOURCE_ONLINE)
	if normalized == "lan":
		return entries.filter(func(entry: Dictionary) -> bool: return entry.get("source", "") == SOURCE_LAN)
	return entries
