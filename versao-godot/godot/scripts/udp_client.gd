extends Node

const PROTOCOL_VERSION := 1

signal status_changed(status: String)
signal message_received(message: Dictionary)

var _peer := PacketPeerUDP.new()
var _endpoint := ""
var _connected := false
var _sequence := 0
var _session_id := ""
var _player_number := -1
var _session_token := ""
var _last_snapshot_sequence := 0
var _last_simulation_tick := 0
var _latest_snapshot: Dictionary = {}
var _player_name := "GodotPlayer"
var _pending_events: Array = []
var _joined_confirmed := false
var _role := "player"


func connect_to_endpoint(endpoint: String) -> int:
	_endpoint = endpoint.strip_edges()
	var address := _parse_endpoint(_endpoint)
	if address.is_empty():
		status_changed.emit("websocket_connect_failed")
		return ERR_INVALID_PARAMETER
	_peer = PacketPeerUDP.new()
	var error := _peer.connect_to_host(str(address["host"]), int(address["port"]))
	if error != OK:
		status_changed.emit("websocket_connect_failed")
		return error
	_connected = true
	_joined_confirmed = false
	_last_snapshot_sequence = 0
	_last_simulation_tick = 0
	_latest_snapshot.clear()
	set_process(true)
	status_changed.emit("websocket_connected")
	_send_typed("HelloRequest", {"player_name": _player_name, "protocol_version": PROTOCOL_VERSION})
	return OK


func disconnect_from_endpoint(reason := "client_disconnect") -> void:
	if _connected and _joined_confirmed and not _session_id.is_empty() and not _session_token.is_empty():
		_send_typed("DisconnectNotice", {
			"session_id": _session_id,
			"player_number": _player_number,
			"session_token": _session_token,
			"reason": reason,
			"protocol_version": PROTOCOL_VERSION,
		})
	_peer.close()
	_connected = false
	_joined_confirmed = false
	set_process(false)
	status_changed.emit("websocket_disconnected")


func abort_connection() -> void:
	_peer.close()
	_connected = false
	_joined_confirmed = false
	set_process(false)


func _exit_tree() -> void:
	if _connected:
		disconnect_from_endpoint("node_exit")


func join(player_name: String, password := "", _auth_token := "", spectator := false, is_computer := false) -> void:
	_player_name = player_name
	_send_typed("JoinRequest", {
		"player_name": player_name,
		"requested_slot": null,
		"password": password,
		"is_computer": is_computer and not spectator,
		"spectator": spectator,
		"protocol_version": PROTOCOL_VERSION,
	})


func resume_session(session_id: String, player_number: int, resume_token: String, player_name := "GodotPlayer") -> void:
	_player_name = player_name
	_send_typed("ResumeRequest", {
		"session_id": session_id,
		"player_number": player_number,
		"session_token": resume_token,
		"player_name": player_name,
		"protocol_version": PROTOCOL_VERSION,
	})


func set_lobby_ready(ready: bool) -> int:
	_sequence += 1
	_send_session_command("LobbySetReadyRequest", "ready-%d" % _sequence, {"ready": ready})
	return _sequence


func request_rematch(ready: bool) -> int:
	_sequence += 1
	_send_session_command("MatchRematchRequest", "rematch-%d" % _sequence, {"ready": ready})
	return _sequence


func send_chat(text: String) -> int:
	_sequence += 1
	_send_session_command("ChatSendRequest", "chat-%d" % _sequence, {"text": text}, true)
	return _sequence


func _send_session_command(message_type: String, request_id: String, fields: Dictionary, allow_spectator := false) -> void:
	if (_player_number < 0 and not (allow_spectator and _role == "spectator")) or _session_id.is_empty() or _session_token.is_empty():
		return
	var payload := {
		"session_id": _session_id,
		"player_number": _player_number,
		"session_token": _session_token,
		"request_id": request_id,
		"protocol_version": PROTOCOL_VERSION,
	}
	for key in fields:
		payload[key] = fields[key]
	_send_typed(message_type, payload)


func send_input(command: Dictionary) -> int:
	if _player_number < 0 or _session_id.is_empty() or _session_token.is_empty():
		return 0
	_sequence += 1
	_send_typed("ClientCommandEnvelope", {
		"session_id": _session_id,
		"player_number": _player_number,
		"client_sequence": _sequence,
		"acknowledged_snapshot_sequence": _last_snapshot_sequence,
		"simulation_tick": _last_simulation_tick,
		"issued_at": Time.get_unix_time_from_system(),
		"source": "godot:udp",
		"commands": command,
		"session_token": _session_token,
		"protocol_version": PROTOCOL_VERSION,
	})
	return _sequence


func ping() -> int:
	_sequence += 1
	var client_time := Time.get_ticks_msec()
	_send_typed("Ping", {
		"nonce": str(client_time),
		"issued_at": Time.get_unix_time_from_system(),
		"protocol_version": PROTOCOL_VERSION,
	})
	return _sequence


func is_websocket_connected() -> bool:
	return _connected


func last_sequence() -> int:
	return _sequence


func _process(_delta: float) -> void:
	while _connected and _peer.get_available_packet_count() > 0:
		var packet := _peer.get_packet().get_string_from_utf8()
		var decoded = JSON.parse_string(packet)
		if typeof(decoded) != TYPE_DICTIONARY:
			continue
		var envelope := Dictionary(decoded)
		_handle_typed_message(str(envelope.get("message_type", "")), Dictionary(envelope.get("payload", {})))


func _handle_typed_message(message_type: String, payload: Dictionary) -> void:
	match message_type:
		"HelloAccept":
			_session_id = str(payload.get("session_id", ""))
			message_received.emit({
				"type": "hello",
				"protocol": int(payload.get("protocol_version", PROTOCOL_VERSION)),
				"supported_protocols": [int(payload.get("protocol_version", PROTOCOL_VERSION))],
				"match_snapshot_schema": 1,
				"event_schema": 1,
				"server_name": str(payload.get("server_name", "Groundfire LAN")),
			})
		"JoinAccept":
			_session_id = str(payload.get("session_id", _session_id))
			_player_number = int(payload.get("player_number", -1))
			_session_token = str(payload.get("session_token", ""))
			_role = str(payload.get("role", "player"))
			_joined_confirmed = true
		"JoinReject":
			var reason := str(payload.get("reason", "join_rejected"))
			if reason in ["password_required", "bad_password"]:
				reason = "invalid_password"
			elif reason == "server_full_or_slot_unavailable":
				reason = "server_full"
			message_received.emit({"type": "error", "protocol": PROTOCOL_VERSION, "message": reason})
		"ResumeAccept":
			_session_id = str(payload.get("session_id", _session_id))
			_player_number = int(payload.get("player_number", _player_number))
			_session_token = str(payload.get("session_token", _session_token))
			_joined_confirmed = true
			message_received.emit({
				"type": "session_resumed",
				"protocol": PROTOCOL_VERSION,
				"session_id": _session_id,
				"player_number": _player_number,
				"resume_token": _session_token,
			})
		"ResumeReject":
			message_received.emit({"type": "error", "protocol": PROTOCOL_VERSION, "message": str(payload.get("reason", "resume_rejected"))})
		"ServerSnapshotEnvelope":
			# The authoritative server also emits public lobby snapshots before a
			# JoinAccept. They are useful for discovery, but must not enter the
			# joined gameplay stream without a player identity and session token.
			if not _joined_confirmed or _session_token.is_empty():
				return
			var snapshot_sequence := int(payload.get("snapshot_sequence", 0))
			if snapshot_sequence <= _last_snapshot_sequence:
				return
			var snapshot_kind := str(payload.get("snapshot_kind", "full"))
			var snapshot := Dictionary(payload.get("snapshot", {}))
			if snapshot_kind == "delta":
				var baseline := int(payload.get("baseline_snapshot_sequence", 0))
				if _latest_snapshot.is_empty() or baseline != _last_snapshot_sequence:
					return
				snapshot = _merge_delta_snapshot(_latest_snapshot, snapshot, payload)
			_latest_snapshot = snapshot.duplicate(true)
			_last_snapshot_sequence = snapshot_sequence
			_last_simulation_tick = int(payload.get("simulation_tick", _last_simulation_tick))
			var events := Array(payload.get("events", [])) + _pending_events
			_pending_events.clear()
			message_received.emit({
				"type": "snapshot",
				"protocol": PROTOCOL_VERSION,
				"sequence": _last_snapshot_sequence,
				"state": {
					"status": "joined",
					"player_name": _player_name,
					"player_number": _player_number,
					"session_id": _session_id,
					"resume_token": _session_token,
					"joined": true,
					"role": _role,
					"server_time_msec": Time.get_ticks_msec(),
					"match_snapshot_schema": 1,
					"event_schema": 1,
					"snapshot_kind": snapshot_kind,
					"baseline_snapshot_sequence": payload.get("baseline_snapshot_sequence", null),
					"match_snapshot": snapshot,
					"terrain_patches": Array(payload.get("terrain_patches", [])),
					"events": events,
				},
			})
		"ServerEventEnvelope":
			var incoming_events := Array(payload.get("events", []))
			_pending_events.append_array(incoming_events)
			for raw_event in incoming_events:
				if typeof(raw_event) != TYPE_DICTIONARY:
					continue
				var event := Dictionary(raw_event)
				if str(event.get("event_type", "")) == "chat_message":
					var chat_payload := Dictionary(event.get("payload", {}))
					chat_payload["type"] = "chat_event"
					chat_payload["protocol"] = PROTOCOL_VERSION
					message_received.emit(chat_payload)
		"CommandResult":
			message_received.emit({
				"type": "command_result",
				"protocol": PROTOCOL_VERSION,
				"request_id": str(payload.get("request_id", "")),
				"command": str(payload.get("command", "")),
				"accepted": bool(payload.get("accepted", false)),
				"reason": str(payload.get("reason", "")),
			})
		"Pong":
			message_received.emit({
				"type": "pong",
				"protocol": PROTOCOL_VERSION,
				"sequence": _sequence,
				"client_time_msec": int(str(payload.get("nonce", Time.get_ticks_msec()))),
				"server_time_msec": Time.get_ticks_msec(),
			})
		"DisconnectNotice":
			message_received.emit({"type": "disconnect", "protocol": PROTOCOL_VERSION, "reason": str(payload.get("reason", "server_disconnect"))})


func _send_typed(message_type: String, payload: Dictionary) -> void:
	if not _connected:
		return
	var envelope := {"message_type": message_type, "payload": payload}
	_peer.put_packet(JSON.stringify(envelope).to_utf8_buffer())


func _merge_delta_snapshot(base: Dictionary, delta: Dictionary, envelope: Dictionary) -> Dictionary:
	var merged := base.duplicate(true)
	for key in delta.keys():
		if key not in ["players", "entities", "terrain_profile"]:
			merged[key] = delta[key]

	var players_by_number := {}
	for player in Array(base.get("players", [])):
		players_by_number[int(Dictionary(player).get("player_number", -1))] = Dictionary(player).duplicate(true)
	for player_number in Array(envelope.get("removed_player_numbers", [])):
		players_by_number.erase(int(player_number))
	for player in Array(delta.get("players", [])):
		players_by_number[int(Dictionary(player).get("player_number", -1))] = Dictionary(player).duplicate(true)
	var players: Array = players_by_number.values()
	players.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a.get("player_number", -1)) < int(b.get("player_number", -1)))
	merged["players"] = players

	var entities_by_id := {}
	for entity in Array(base.get("entities", [])):
		entities_by_id[int(Dictionary(entity).get("entity_id", -1))] = Dictionary(entity).duplicate(true)
	for entity_id in Array(envelope.get("removed_entity_ids", [])):
		entities_by_id.erase(int(entity_id))
	for entity in Array(delta.get("entities", [])):
		entities_by_id[int(Dictionary(entity).get("entity_id", -1))] = Dictionary(entity).duplicate(true)
	var entities: Array = entities_by_id.values()
	entities.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a.get("entity_id", -1)) < int(b.get("entity_id", -1)))
	merged["entities"] = entities

	var terrain_profile := Array(delta.get("terrain_profile", []))
	if not terrain_profile.is_empty():
		merged["terrain_profile"] = terrain_profile.duplicate(true)
	return merged


func _parse_endpoint(endpoint: String) -> Dictionary:
	var normalized := endpoint.trim_prefix("udp://")
	var separator := normalized.rfind(":")
	if separator <= 0 or separator >= normalized.length() - 1:
		return {}
	var host := normalized.substr(0, separator).strip_edges()
	var port_text := normalized.substr(separator + 1).strip_edges()
	if host.is_empty() or not port_text.is_valid_int():
		return {}
	var port := int(port_text)
	if port <= 0 or port > 65535:
		return {}
	return {"host": host, "port": port}
