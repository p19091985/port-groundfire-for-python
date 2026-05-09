extends RefCounted

const SOURCE_ONLINE := "online"
const SOURCE_LAN := "lan"
const DEFAULT_DIRECTORY_PATH := "res://data/server_directory.json"
const SERVER_DIRECTORY_SETTING := "application/config/server_directory_url"
const SERVER_DIRECTORY_ENVIRONMENT_SETTING := "application/config/server_directory_environment"
const SERVER_DIRECTORY_DEV_URL_SETTING := "application/config/server_directory_url_dev"
const SERVER_DIRECTORY_STAGING_URL_SETTING := "application/config/server_directory_url_staging"
const SERVER_DIRECTORY_PRODUCTION_URL_SETTING := "application/config/server_directory_url_production"
const ENVIRONMENT_DEV := "dev"
const ENVIRONMENT_STAGING := "staging"
const ENVIRONMENT_PRODUCTION := "production"
const DIRECTORY_ENVIRONMENTS := [ENVIRONMENT_DEV, ENVIRONMENT_STAGING, ENVIRONMENT_PRODUCTION]
const DIRECTORY_SCHEMA_VERSION := 1
const HTTP_TIMEOUT_SECONDS := 8.0
const HTTP_RETRY_LIMIT := 1
const REQUIRED_SERVER_FIELDS := ["name", "game", "players", "map", "latency", "source", "endpoint", "passworded"]
const STRING_SERVER_FIELDS := ["name", "game", "players", "map", "latency", "source", "endpoint"]
const OPTIONAL_STRING_SERVER_FIELDS := ["region", "description", "version", "auth_token"]
const OPTIONAL_ARRAY_SERVER_FIELDS := ["tags"]
const OPTIONAL_INTEGER_SERVER_FIELDS := ["last_seen_msec"]
const OPTIONAL_SERVER_FIELDS := OPTIONAL_STRING_SERVER_FIELDS + OPTIONAL_ARRAY_SERVER_FIELDS + OPTIONAL_INTEGER_SERVER_FIELDS


static func configured_directory_url() -> String:
	var override_url := str(ProjectSettings.get_setting(SERVER_DIRECTORY_SETTING, "")).strip_edges()
	if not override_url.is_empty():
		return override_url if is_valid_directory_url(override_url) else ""
	var environment := configured_directory_environment()
	var url := str(ProjectSettings.get_setting(directory_url_setting_for_environment(environment), "")).strip_edges()
	return url if is_valid_directory_url(url) else ""


static func configured_directory_environment() -> String:
	return normalized_directory_environment(str(ProjectSettings.get_setting(SERVER_DIRECTORY_ENVIRONMENT_SETTING, ENVIRONMENT_DEV)))


static func normalized_directory_environment(value: String) -> String:
	var environment := value.to_lower().strip_edges()
	if DIRECTORY_ENVIRONMENTS.has(environment):
		return environment
	return ENVIRONMENT_DEV


static func directory_url_setting_for_environment(environment: String) -> String:
	if environment == ENVIRONMENT_STAGING:
		return SERVER_DIRECTORY_STAGING_URL_SETTING
	if environment == ENVIRONMENT_PRODUCTION:
		return SERVER_DIRECTORY_PRODUCTION_URL_SETTING
	return SERVER_DIRECTORY_DEV_URL_SETTING


static func directory_environment_urls() -> Dictionary:
	return {
		ENVIRONMENT_DEV: str(ProjectSettings.get_setting(SERVER_DIRECTORY_DEV_URL_SETTING, "")).strip_edges(),
		ENVIRONMENT_STAGING: str(ProjectSettings.get_setting(SERVER_DIRECTORY_STAGING_URL_SETTING, "")).strip_edges(),
		ENVIRONMENT_PRODUCTION: str(ProjectSettings.get_setting(SERVER_DIRECTORY_PRODUCTION_URL_SETTING, "")).strip_edges(),
	}


static func is_valid_directory_url(url: String) -> bool:
	var value := url.strip_edges()
	return value.is_empty() or value.begins_with("http://") or value.begins_with("https://")


static func directory_url_error(label: String, url: String) -> String:
	if is_valid_directory_url(url):
		return ""
	return "%s must use http:// or https://" % label


static func configured_directory_label() -> String:
	var override_url := str(ProjectSettings.get_setting(SERVER_DIRECTORY_SETTING, "")).strip_edges()
	if not override_url.is_empty():
		if not is_valid_directory_url(override_url):
			return "invalid override URL; local fallback"
		return "override: %s" % override_url
	var environment := configured_directory_environment()
	var url := str(ProjectSettings.get_setting(directory_url_setting_for_environment(environment), "")).strip_edges()
	if not is_valid_directory_url(url):
		return "%s: invalid URL; local fallback" % environment
	if url.is_empty():
		return "%s: local fallback" % environment
	return "%s: %s" % [environment, url]


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
		"servers": {
			"required": REQUIRED_SERVER_FIELDS,
			"optional": OPTIONAL_SERVER_FIELDS,
			"sources": [SOURCE_ONLINE, SOURCE_LAN],
			"online_endpoint": "ws:// or wss://",
			"passworded": "boolean",
		},
	}


static func validate_directory_payload(parsed: Dictionary) -> Dictionary:
	var errors: Array[String] = []
	if not parsed.has("schema"):
		errors.append("missing schema")
	elif not _is_integer_value(parsed.get("schema")):
		errors.append("schema must be integer")
	elif _integer_value(parsed.get("schema"), -1) != DIRECTORY_SCHEMA_VERSION:
		errors.append("unsupported schema %s" % str(parsed.get("schema")))

	var servers: Variant = parsed.get("servers", null)
	if typeof(servers) != TYPE_ARRAY:
		errors.append("servers must be array")
	else:
		var server_items := Array(servers)
		for index in range(server_items.size()):
			var item: Variant = server_items[index]
			if typeof(item) != TYPE_DICTIONARY:
				errors.append("servers[%d] must be object" % index)
				continue
			_validate_server_entry(Dictionary(item), index, errors)

	return {
		"ok": errors.is_empty(),
		"errors": errors,
	}


static func directory_diagnostic_from_body(body: PackedByteArray) -> String:
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return "invalid JSON object"
	var validation := validate_directory_payload(Dictionary(parsed))
	if not bool(validation.get("ok", false)):
		return "invalid schema: %s" % _join_errors(Array(validation.get("errors", [])))
	var servers := Array(Dictionary(parsed).get("servers", []))
	return "schema %d, %d server(s)" % [DIRECTORY_SCHEMA_VERSION, servers.size()]


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
	var validation := validate_directory_payload(parsed)
	if not bool(validation.get("ok", false)):
		return []
	var servers = parsed.get("servers", [])
	if typeof(servers) != TYPE_ARRAY:
		return []

	var entries: Array[Dictionary] = []
	for item in servers:
		if typeof(item) == TYPE_DICTIONARY:
			entries.append(_normalize_entry(item))
	return _filter_lan(entries, include_lan)


static func _normalize_entry(raw: Dictionary) -> Dictionary:
	var entry := {
		"name": str(raw.get("name", "")),
		"game": str(raw.get("game", "Groundfire")),
		"players": str(raw.get("players", "-")),
		"map": str(raw.get("map", "-")),
		"latency": str(raw.get("latency", "-")),
		"source": str(raw.get("source", SOURCE_ONLINE)),
		"endpoint": str(raw.get("endpoint", "")),
		"passworded": str(raw.get("passworded", "false")),
	}
	_copy_optional_fields(raw, entry)
	return entry


static func _validate_server_entry(entry: Dictionary, index: int, errors: Array[String]) -> void:
	for field in REQUIRED_SERVER_FIELDS:
		if not entry.has(field):
			errors.append("servers[%d].%s is required" % [index, field])

	for field in STRING_SERVER_FIELDS:
		if not entry.has(field):
			continue
		var value: Variant = entry.get(field)
		if typeof(value) != TYPE_STRING or str(value).strip_edges().is_empty():
			errors.append("servers[%d].%s must be non-empty string" % [index, field])

	if entry.has("passworded") and typeof(entry.get("passworded")) != TYPE_BOOL:
		errors.append("servers[%d].passworded must be boolean" % index)

	var source := str(entry.get("source", ""))
	if not source.is_empty() and source != SOURCE_ONLINE and source != SOURCE_LAN:
		errors.append("servers[%d].source must be online or lan" % index)

	var endpoint := str(entry.get("endpoint", ""))
	if source == SOURCE_ONLINE and not (endpoint.begins_with("ws://") or endpoint.begins_with("wss://")):
		errors.append("servers[%d].endpoint must be ws:// or wss:// for online servers" % index)

	for field in OPTIONAL_STRING_SERVER_FIELDS:
		if entry.has(field) and typeof(entry.get(field)) != TYPE_STRING:
			errors.append("servers[%d].%s must be string" % [index, field])

	for field in OPTIONAL_ARRAY_SERVER_FIELDS:
		if entry.has(field) and typeof(entry.get(field)) != TYPE_ARRAY:
			errors.append("servers[%d].%s must be array" % [index, field])

	for field in OPTIONAL_INTEGER_SERVER_FIELDS:
		if entry.has(field) and not _is_integer_value(entry.get(field)):
			errors.append("servers[%d].%s must be integer" % [index, field])


static func _copy_optional_fields(raw: Dictionary, entry: Dictionary) -> void:
	for field in OPTIONAL_STRING_SERVER_FIELDS:
		if raw.has(field):
			entry[field] = str(raw.get(field, ""))

	for field in OPTIONAL_ARRAY_SERVER_FIELDS:
		if raw.has(field):
			entry[field] = Array(raw.get(field, [])).duplicate()

	for field in OPTIONAL_INTEGER_SERVER_FIELDS:
		if raw.has(field):
			entry[field] = _integer_value(raw.get(field), 0)


static func _is_integer_value(value: Variant) -> bool:
	if typeof(value) == TYPE_INT:
		return true
	if typeof(value) == TYPE_FLOAT:
		return float(value) == float(int(value))
	return false


static func _integer_value(value: Variant, fallback: int) -> int:
	if _is_integer_value(value):
		return int(value)
	return fallback


static func _join_errors(errors: Array) -> String:
	var label := ""
	for index in range(errors.size()):
		if index > 0:
			label += "; "
		label += str(errors[index])
	return label


static func filter_for_tab(entries: Array[Dictionary], tab_name: String) -> Array[Dictionary]:
	var normalized := tab_name.to_lower()
	if normalized == "internet":
		return entries.filter(func(entry: Dictionary) -> bool: return entry.get("source", "") == SOURCE_ONLINE)
	if normalized == "lan":
		return entries.filter(func(entry: Dictionary) -> bool: return entry.get("source", "") == SOURCE_LAN)
	return entries
