extends SceneTree

const ServerDirectory := preload("res://scripts/server_directory.gd")


func _init() -> void:
	var web_entries := ServerDirectory.browser_entries(false)
	for entry in web_entries:
		assert(entry.get("source", "") != ServerDirectory.SOURCE_LAN)

	var desktop_entries := ServerDirectory.browser_entries(true)
	assert(desktop_entries.size() > web_entries.size())
	assert(desktop_entries.any(func(entry: Dictionary) -> bool: return entry.get("source", "") == ServerDirectory.SOURCE_LAN))

	var expected_schema := ServerDirectory.expected_schema()
	assert(int(expected_schema.get("schema", 0)) == ServerDirectory.DIRECTORY_SCHEMA_VERSION)
	assert(Dictionary(expected_schema.get("servers", {})).get("required", []).has("passworded"))
	assert(Dictionary(expected_schema.get("servers", {})).get("optional", []).has("auth_token"))
	assert(ServerDirectory.normalized_directory_environment("PRODUCTION") == ServerDirectory.ENVIRONMENT_PRODUCTION)
	assert(ServerDirectory.normalized_directory_environment("unknown") == ServerDirectory.ENVIRONMENT_DEV)
	assert(ServerDirectory.is_valid_directory_url(""))
	assert(ServerDirectory.is_valid_directory_url("https://directory.example.invalid/groundfire.json"))
	assert(not ServerDirectory.is_valid_directory_url("ftp://directory.example.invalid/groundfire.json"))
	assert(ServerDirectory.directory_url_error("Directory", "ftp://example.invalid").contains("http://"))
	assert(ServerDirectory.configured_directory_environment() == ServerDirectory.ENVIRONMENT_DEV)
	assert(ServerDirectory.directory_url_setting_for_environment(ServerDirectory.ENVIRONMENT_STAGING) == ServerDirectory.SERVER_DIRECTORY_STAGING_URL_SETTING)
	assert(ServerDirectory.configured_directory_label().contains("dev"))
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_DEV_URL_SETTING, "https://dev.example.invalid/groundfire-directory.json")
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_ENVIRONMENT_SETTING, ServerDirectory.ENVIRONMENT_DEV)
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_SETTING, "")
	assert(ServerDirectory.configured_directory_url() == "https://dev.example.invalid/groundfire-directory.json")
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_SETTING, "https://override.example.invalid/groundfire-directory.json")
	assert(ServerDirectory.configured_directory_url() == "https://override.example.invalid/groundfire-directory.json")
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_SETTING, "")
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_DEV_URL_SETTING, "")
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_SETTING, "ftp://example.invalid/groundfire-directory.json")
	assert(ServerDirectory.configured_directory_url().is_empty())
	assert(ServerDirectory.configured_directory_label().contains("invalid override"))
	ProjectSettings.set_setting(ServerDirectory.SERVER_DIRECTORY_SETTING, "")

	var valid_payload := {
		"schema": ServerDirectory.DIRECTORY_SCHEMA_VERSION,
		"servers": [
			{
				"name": "Validation Arena",
				"game": "Groundfire",
				"players": "2/8",
				"map": "Classic",
				"latency": "44ms",
				"source": ServerDirectory.SOURCE_ONLINE,
				"endpoint": "wss://example.invalid/validation",
				"passworded": false,
				"auth_token": "fixture-token",
			},
		],
	}
	var validation := ServerDirectory.validate_directory_payload(valid_payload)
	assert(bool(validation.get("ok", false)))
	var body := JSON.stringify(valid_payload).to_utf8_buffer()
	assert(ServerDirectory.directory_diagnostic_from_body(body).contains("schema 1"))
	assert(ServerDirectory.entries_from_http_body(body, false).size() == 1)
	assert(ServerDirectory.entries_from_http_body(body, false)[0].get("auth_token", "") == "fixture-token")

	var missing_schema := valid_payload.duplicate(true)
	missing_schema.erase("schema")
	assert(not bool(ServerDirectory.validate_directory_payload(missing_schema).get("ok", true)))
	assert(ServerDirectory.entries_from_http_body(JSON.stringify(missing_schema).to_utf8_buffer(), false).is_empty())

	var invalid_endpoint := valid_payload.duplicate(true)
	invalid_endpoint["servers"][0]["endpoint"] = "http://example.invalid/not-websocket"
	assert(not bool(ServerDirectory.validate_directory_payload(invalid_endpoint).get("ok", true)))

	var invalid_passworded := valid_payload.duplicate(true)
	invalid_passworded["servers"][0]["passworded"] = "false"
	assert(not bool(ServerDirectory.validate_directory_payload(invalid_passworded).get("ok", true)))

	var invalid_auth_token := valid_payload.duplicate(true)
	invalid_auth_token["servers"][0]["auth_token"] = 123
	assert(not bool(ServerDirectory.validate_directory_payload(invalid_auth_token).get("ok", true)))

	var internet_entries := ServerDirectory.filter_for_tab(desktop_entries, "Internet")
	assert(internet_entries.all(func(entry: Dictionary) -> bool: return entry.get("source", "") == ServerDirectory.SOURCE_ONLINE))

	var lan_entries := ServerDirectory.filter_for_tab(desktop_entries, "LAN")
	assert(lan_entries.all(func(entry: Dictionary) -> bool: return entry.get("source", "") == ServerDirectory.SOURCE_LAN))
	quit(0)
