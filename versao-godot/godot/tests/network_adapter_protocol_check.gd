extends SceneTree

const NetworkAdapter := preload("res://scripts/network_adapter.gd")


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	assert(NetworkAdapter.PROTOCOL_VERSION == 1)
	assert(NetworkAdapter.MIN_SUPPORTED_PROTOCOL == 1)
	assert(NetworkAdapter.MAX_SUPPORTED_PROTOCOL == NetworkAdapter.PROTOCOL_VERSION)
	assert(NetworkAdapter.client_supports_protocol(1))
	assert(not NetworkAdapter.client_supports_protocol(0))
	assert(not NetworkAdapter.client_supports_protocol(2))

	var explicit_protocols := {
		"type": "hello",
		"protocol": 1,
		"supported_protocols": [0, 1, 2],
		"match_snapshot_schema": 1,
		"event_schema": 1,
	}
	assert(NetworkAdapter.negotiated_protocol(explicit_protocols) == 1)
	assert(NetworkAdapter.server_supports_client_protocol(explicit_protocols))
	assert(
		NetworkAdapter.protocol_status_message(explicit_protocols)
		== "Protocol 1 accepted. Snapshot schema 1, event schema 1."
	)

	var range_protocols := {"type": "hello", "protocol": 2, "min_protocol": 1, "max_protocol": 2}
	assert(NetworkAdapter.negotiated_protocol(range_protocols) == 1)
	assert(NetworkAdapter.server_supports_client_protocol(range_protocols))

	var incompatible := {"type": "hello", "protocol": 2, "supported_protocols": [2, 3]}
	assert(NetworkAdapter.negotiated_protocol(incompatible) == 0)
	assert(not NetworkAdapter.server_supports_client_protocol(incompatible))
	assert(NetworkAdapter.protocol_status_message(incompatible).contains("server supports [2, 3]"))

	var missing := NetworkAdapter.parse_message(JSON.stringify({"type": "hello"}))
	assert(missing.get("message", "") == "missing_protocol")
	assert(missing.get("expected_protocol", 0) == NetworkAdapter.PROTOCOL_VERSION)

	var mismatch := NetworkAdapter.parse_message(JSON.stringify({"type": "hello", "protocol": 2}))
	assert(mismatch.get("message", "") == "protocol_mismatch")
	assert(mismatch.get("min_protocol", 0) == NetworkAdapter.MIN_SUPPORTED_PROTOCOL)
	assert(mismatch.get("max_protocol", 0) == NetworkAdapter.MAX_SUPPORTED_PROTOCOL)
	assert(mismatch.get("received_protocol", 0) == 2)

	var parsed := NetworkAdapter.parse_message(JSON.stringify({"type": "hello", "protocol": 1}))
	assert(parsed.get("type", "") == "hello")
	assert(NetworkAdapter.server_error_category("invalid_password") == NetworkAdapter.SERVER_ERROR_CATEGORY_CREDENTIALS)
	assert(NetworkAdapter.server_error_category("authentication_failed") == NetworkAdapter.SERVER_ERROR_CATEGORY_CREDENTIALS)
	assert(NetworkAdapter.server_error_category("server_full") == NetworkAdapter.SERVER_ERROR_CATEGORY_CAPACITY)
	assert(NetworkAdapter.server_error_category("server_closed") == NetworkAdapter.SERVER_ERROR_CATEGORY_SERVER_STATE)
	assert(NetworkAdapter.server_error_category("server_unavailable") == NetworkAdapter.SERVER_ERROR_CATEGORY_TRANSIENT)
	assert(NetworkAdapter.server_error_category("banned") == NetworkAdapter.SERVER_ERROR_CATEGORY_ACCESS)
	assert(NetworkAdapter.server_error_category("join_rejected") == NetworkAdapter.SERVER_ERROR_CATEGORY_MATCH)
	assert(NetworkAdapter.server_error_category("match_not_found") == NetworkAdapter.SERVER_ERROR_CATEGORY_MATCH)
	assert(NetworkAdapter.server_error_category("protocol_mismatch") == NetworkAdapter.SERVER_ERROR_CATEGORY_PROTOCOL)
	assert(NetworkAdapter.server_error_category("surprise") == NetworkAdapter.SERVER_ERROR_CATEGORY_UNKNOWN)
	assert(NetworkAdapter.server_error_recovery_hint("authentication_failed").contains("session token"))
	assert(NetworkAdapter.server_error_recovery_hint("server_full").contains("slot"))
	assert(NetworkAdapter.server_error_recovery_hint("server_closed").contains("joins"))
	assert(NetworkAdapter.server_error_recovery_hint("banned").contains("server host"))
	assert(NetworkAdapter.server_error_recovery_hint("match_not_found").contains("server list"))
	assert(NetworkAdapter.server_error_recovery_hint("protocol_mismatch").contains("compatible server"))
	assert(NetworkAdapter.server_error_status_message(NetworkAdapter.error_message("invalid_password")).contains("password rejected"))
	assert(NetworkAdapter.server_error_status_message(NetworkAdapter.error_message("server_full")).contains("Wait for a slot"))
	assert(NetworkAdapter.server_error_status_message(NetworkAdapter.error_message("surprise")).contains("Try again"))
	quit(0)
