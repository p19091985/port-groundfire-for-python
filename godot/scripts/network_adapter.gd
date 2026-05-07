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
const PLAYER_NAME_DEFAULT := "GodotPlayer"


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


static func join_message(player_name: String, password := "") -> Dictionary:
	return {"type": MESSAGE_JOIN, "player_name": player_name, "password": password}


static func input_message(sequence: int, command: Dictionary) -> Dictionary:
	return {"type": MESSAGE_INPUT, "sequence": sequence, "command": command}


static func command_from_local_match(action: String, value = true) -> Dictionary:
	return {"action": action, "value": value}


static func snapshot_message(sequence: int, state: Dictionary) -> Dictionary:
	return {"type": MESSAGE_SNAPSHOT, "sequence": sequence, "state": state}


static func ping_message(sequence: int, client_time_msec: int) -> Dictionary:
	return {"type": MESSAGE_PING, "sequence": sequence, "client_time_msec": client_time_msec}


static func pong_message(sequence: int, client_time_msec: int, server_time_msec: int) -> Dictionary:
	return {
		"type": MESSAGE_PONG,
		"sequence": sequence,
		"client_time_msec": client_time_msec,
		"server_time_msec": server_time_msec,
	}


static func disconnect_message(reason := "client_disconnect") -> Dictionary:
	return {"type": MESSAGE_DISCONNECT, "reason": reason}


static func error_message(message: String) -> Dictionary:
	return {"type": MESSAGE_ERROR, "message": message}


static func encode_message(message: Dictionary) -> String:
	return JSON.stringify(message)


static func parse_message(payload: String) -> Dictionary:
	var parsed = JSON.parse_string(payload)
	if typeof(parsed) != TYPE_DICTIONARY:
		return error_message("invalid_json")
	if not parsed.has("type"):
		return error_message("missing_type")
	return parsed
