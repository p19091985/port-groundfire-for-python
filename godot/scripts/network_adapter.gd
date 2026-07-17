extends RefCounted

const TRANSPORT_WEBSOCKET := "websocket"
const TRANSPORT_UDP := "udp"
const TRANSPORT_UNSUPPORTED := "unsupported"
const MESSAGE_HELLO := "hello"
const MESSAGE_JOIN := "join"
const MESSAGE_INPUT := "input"
const MESSAGE_SNAPSHOT := "snapshot"
const MESSAGE_PING := "ping"
const MESSAGE_PONG := "pong"
const MESSAGE_DISCONNECT := "disconnect"
const MESSAGE_ERROR := "error"
const PROTOCOL_VERSION := 1
const MIN_SUPPORTED_PROTOCOL := 1
const MAX_SUPPORTED_PROTOCOL := PROTOCOL_VERSION
const PLAYER_NAME_DEFAULT := "GodotPlayer"
const SERVER_ERROR_CATEGORY_CREDENTIALS := "credentials"
const SERVER_ERROR_CATEGORY_CAPACITY := "capacity"
const SERVER_ERROR_CATEGORY_SERVER_STATE := "server_state"
const SERVER_ERROR_CATEGORY_ACCESS := "access"
const SERVER_ERROR_CATEGORY_MATCH := "match"
const SERVER_ERROR_CATEGORY_TRANSIENT := "transient"
const SERVER_ERROR_CATEGORY_PROTOCOL := "protocol"
const SERVER_ERROR_CATEGORY_UNKNOWN := "unknown"
const FATAL_SERVER_ERRORS := [
	"invalid_password",
	"authentication_failed",
	"server_full",
	"server_closed",
	"server_unavailable",
	"banned",
	"join_rejected",
	"match_not_found",
]


static func transport_for_endpoint(endpoint: String, allow_udp := false) -> String:
	if endpoint.begins_with("ws://") or endpoint.begins_with("wss://"):
		return TRANSPORT_WEBSOCKET
	if allow_udp and endpoint.contains(":"):
		return TRANSPORT_UDP
	return TRANSPORT_UNSUPPORTED


static func can_connect(endpoint: String, allow_udp := false) -> bool:
	return transport_for_endpoint(endpoint, allow_udp) != TRANSPORT_UNSUPPORTED


static func staged_connect_message(entry: Dictionary, allow_udp := false) -> String:
	var endpoint := str(entry.get("endpoint", ""))
	var transport := transport_for_endpoint(endpoint, allow_udp)
	if transport == TRANSPORT_UNSUPPORTED:
		return "Unsupported endpoint for this platform: %s." % endpoint
	return "Connect target staged via %s: %s." % [transport, endpoint]


static func hello_message(protocol_version := PROTOCOL_VERSION) -> Dictionary:
	return {"type": MESSAGE_HELLO, "protocol": protocol_version, "client": "godot"}


static func join_message(player_name: String, password := "", auth_token := "") -> Dictionary:
	var message := {
		"type": MESSAGE_JOIN,
		"protocol": PROTOCOL_VERSION,
		"player_name": player_name,
		"password": password,
	}
	if not str(auth_token).is_empty():
		message["auth_token"] = auth_token
	return message


static func input_message(sequence: int, command: Dictionary) -> Dictionary:
	return {"type": MESSAGE_INPUT, "protocol": PROTOCOL_VERSION, "sequence": sequence, "command": command}


static func command_from_local_match(action: String, value = true) -> Dictionary:
	return {"action": action, "value": value}


static func snapshot_message(sequence: int, state: Dictionary) -> Dictionary:
	return {"type": MESSAGE_SNAPSHOT, "protocol": PROTOCOL_VERSION, "sequence": sequence, "state": state}


static func ping_message(sequence: int, client_time_msec: int) -> Dictionary:
	return {"type": MESSAGE_PING, "protocol": PROTOCOL_VERSION, "sequence": sequence, "client_time_msec": client_time_msec}


static func pong_message(sequence: int, client_time_msec: int, server_time_msec: int) -> Dictionary:
	return {
		"type": MESSAGE_PONG,
		"protocol": PROTOCOL_VERSION,
		"sequence": sequence,
		"client_time_msec": client_time_msec,
		"server_time_msec": server_time_msec,
	}


static func disconnect_message(reason := "client_disconnect") -> Dictionary:
	return {"type": MESSAGE_DISCONNECT, "protocol": PROTOCOL_VERSION, "reason": reason}


static func error_message(message: String) -> Dictionary:
	return {"type": MESSAGE_ERROR, "protocol": PROTOCOL_VERSION, "message": message}


static func client_supports_protocol(protocol_version: int) -> bool:
	return protocol_version >= MIN_SUPPORTED_PROTOCOL and protocol_version <= MAX_SUPPORTED_PROTOCOL


static func negotiated_protocol(message: Dictionary) -> int:
	var server_protocols := _server_supported_protocols(message)
	for protocol_version in range(MAX_SUPPORTED_PROTOCOL, MIN_SUPPORTED_PROTOCOL - 1, -1):
		if server_protocols.has(protocol_version):
			return protocol_version
	return 0


static func server_supports_client_protocol(message: Dictionary) -> bool:
	return negotiated_protocol(message) != 0


static func protocol_status_message(message: Dictionary) -> String:
	var protocol_version := negotiated_protocol(message)
	if protocol_version != 0:
		var snapshot_schema := int(message.get("match_snapshot_schema", 0))
		var event_schema := int(message.get("event_schema", 0))
		return "Protocol %d accepted. Snapshot schema %d, event schema %d." % [
			protocol_version,
			snapshot_schema,
			event_schema,
		]
	return "Incompatible protocol. Client %d, server supports %s." % [
		PROTOCOL_VERSION,
		_protocol_support_label(message),
	]


static func is_fatal_server_error(error_name: String) -> bool:
	return FATAL_SERVER_ERRORS.has(error_name)


static func server_error_category(error_name: String) -> String:
	match error_name:
		"invalid_password", "authentication_failed":
			return SERVER_ERROR_CATEGORY_CREDENTIALS
		"server_full":
			return SERVER_ERROR_CATEGORY_CAPACITY
		"server_closed":
			return SERVER_ERROR_CATEGORY_SERVER_STATE
		"server_unavailable":
			return SERVER_ERROR_CATEGORY_TRANSIENT
		"banned":
			return SERVER_ERROR_CATEGORY_ACCESS
		"join_rejected", "match_not_found":
			return SERVER_ERROR_CATEGORY_MATCH
		"missing_protocol", "invalid_protocol", "protocol_mismatch":
			return SERVER_ERROR_CATEGORY_PROTOCOL
		_:
			return SERVER_ERROR_CATEGORY_UNKNOWN


static func server_error_recovery_hint(error_name: String) -> String:
	match server_error_category(error_name):
		SERVER_ERROR_CATEGORY_CREDENTIALS:
			return "Check credentials or request a fresh session token."
		SERVER_ERROR_CATEGORY_CAPACITY:
			return "Wait for a slot or choose another server."
		SERVER_ERROR_CATEGORY_SERVER_STATE:
			return "Wait for joins to reopen or choose another server."
		SERVER_ERROR_CATEGORY_ACCESS:
			return "Choose another server or contact the server host."
		SERVER_ERROR_CATEGORY_MATCH:
			return "Refresh the server list and choose an available match."
		SERVER_ERROR_CATEGORY_TRANSIENT:
			return "Try reconnecting later."
		SERVER_ERROR_CATEGORY_PROTOCOL:
			return "Update the client or choose a compatible server."
		_:
			return "Try again or choose another server."


static func server_error_status_message(message: Dictionary) -> String:
	var error_name := str(message.get("message", "unknown"))
	var recovery_hint := server_error_recovery_hint(error_name)
	match error_name:
		"invalid_password":
			return "Join failed: password rejected. %s" % recovery_hint
		"authentication_failed":
			return "Join failed: authentication was rejected. %s" % recovery_hint
		"server_full":
			return "Join failed: server is full. %s" % recovery_hint
		"server_closed":
			return "Join failed: server is closed. %s" % recovery_hint
		"server_unavailable":
			return "Join failed: server is unavailable. %s" % recovery_hint
		"banned":
			return "Join failed: access was rejected. %s" % recovery_hint
		"join_rejected":
			return "Join failed: server rejected the player. %s" % recovery_hint
		"match_not_found":
			return "Join failed: match was not found. %s" % recovery_hint
		_:
			return "Server error: %s. %s" % [error_name, recovery_hint]


static func encode_message(message: Dictionary) -> String:
	return JSON.stringify(message)


static func parse_message(payload: String) -> Dictionary:
	var parsed = JSON.parse_string(payload)
	if typeof(parsed) != TYPE_DICTIONARY:
		return error_message("invalid_json")
	if not parsed.has("type"):
		return error_message("missing_type")
	if not parsed.has("protocol"):
		var missing := error_message("missing_protocol")
		missing["expected_protocol"] = PROTOCOL_VERSION
		return missing
	var protocol_version := int(parsed.get("protocol", 0))
	if not client_supports_protocol(protocol_version):
		var error := error_message("protocol_mismatch")
		error["expected_protocol"] = PROTOCOL_VERSION
		error["min_protocol"] = MIN_SUPPORTED_PROTOCOL
		error["max_protocol"] = MAX_SUPPORTED_PROTOCOL
		error["received_protocol"] = protocol_version
		return error
	return parsed


static func _protocol_value(value: Variant, fallback: int) -> int:
	if typeof(value) == TYPE_INT:
		return int(value)
	if typeof(value) == TYPE_FLOAT and float(value) == float(int(value)):
		return int(value)
	return fallback


static func _server_supported_protocols(message: Dictionary) -> Array[int]:
	var protocols: Array[int] = []
	var supported_protocols: Variant = message.get("supported_protocols", null)
	if typeof(supported_protocols) == TYPE_ARRAY:
		for raw_protocol in Array(supported_protocols):
			var protocol_version := _protocol_value(raw_protocol, 0)
			if protocol_version > 0 and not protocols.has(protocol_version):
				protocols.append(protocol_version)
		return protocols
	if message.has("min_protocol") or message.has("max_protocol"):
		var min_protocol := _protocol_value(message.get("min_protocol", PROTOCOL_VERSION), PROTOCOL_VERSION)
		var max_protocol := _protocol_value(message.get("max_protocol", PROTOCOL_VERSION), PROTOCOL_VERSION)
		for protocol_version in range(min_protocol, max_protocol + 1):
			if protocol_version > 0:
				protocols.append(protocol_version)
		return protocols
	var protocol_version := _protocol_value(message.get("protocol", -1), -1)
	if protocol_version > 0:
		protocols.append(protocol_version)
	return protocols


static func _protocol_support_label(message: Dictionary) -> String:
	var supported_protocols: Variant = message.get("supported_protocols", null)
	if typeof(supported_protocols) == TYPE_ARRAY:
		var label := ""
		var values := Array(supported_protocols)
		for index in range(values.size()):
			if index > 0:
				label += ", "
			label += str(values[index])
		if label.is_empty():
			return "no protocols"
		return "[%s]" % label
	if message.has("min_protocol") or message.has("max_protocol"):
		return "%d..%d" % [
			_protocol_value(message.get("min_protocol", -1), -1),
			_protocol_value(message.get("max_protocol", -1), -1),
		]
	return "protocol %s" % str(message.get("protocol", "unknown"))
