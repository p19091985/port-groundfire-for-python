extends Node

const NetworkAdapter := preload("res://scripts/network_adapter.gd")

signal status_changed(status: String)
signal message_received(message: Dictionary)

var _peer := WebSocketPeer.new()
var _endpoint := ""
var _sequence := 0
var _connected := false
var _closed_reported := true
var _negotiated_protocol := NetworkAdapter.PROTOCOL_VERSION


func connect_to_endpoint(endpoint: String) -> int:
	_endpoint = endpoint
	_peer = WebSocketPeer.new()
	_connected = false
	_closed_reported = false
	_negotiated_protocol = NetworkAdapter.PROTOCOL_VERSION
	var error := _peer.connect_to_url(endpoint)
	if error != OK:
		_closed_reported = true
		status_changed.emit("websocket_connect_failed")
		return error
	set_process(true)
	status_changed.emit("websocket_connecting")
	return OK


func disconnect_from_endpoint(reason := "client_disconnect") -> void:
	if _connected:
		send_message(NetworkAdapter.disconnect_message(reason))
	_peer.close()
	_connected = false
	_closed_reported = true
	status_changed.emit("websocket_disconnected")


func abort_connection() -> void:
	_peer.close()
	_connected = false
	_closed_reported = true
	set_process(false)


func _exit_tree() -> void:
	set_process(false)
	if _connected:
		send_message(NetworkAdapter.disconnect_message("node_exit"))
	_peer.close()
	_connected = false
	_closed_reported = true


func join(player_name: String, password := "", auth_token := "", spectator := false) -> void:
	send_message(NetworkAdapter.join_message(player_name, password, auth_token, spectator))


func resume_session(session_id: String, player_number: int, resume_token: String, player_name := NetworkAdapter.PLAYER_NAME_DEFAULT) -> void:
	send_message(NetworkAdapter.session_resume_message(session_id, player_number, resume_token, player_name))


func set_lobby_ready(ready: bool) -> int:
	_sequence += 1
	send_message(NetworkAdapter.lobby_set_ready_message("ready-%d" % _sequence, ready))
	return _sequence


func request_rematch(ready: bool) -> int:
	_sequence += 1
	send_message(NetworkAdapter.match_rematch_message("rematch-%d" % _sequence, ready))
	return _sequence


func send_chat(text: String) -> int:
	_sequence += 1
	send_message(NetworkAdapter.chat_send_message("chat-%d" % _sequence, text))
	return _sequence


func send_input(command: Dictionary) -> int:
	_sequence += 1
	send_message(NetworkAdapter.input_message(_sequence, command))
	return _sequence


func ping() -> int:
	_sequence += 1
	send_message(NetworkAdapter.ping_message(_sequence, Time.get_ticks_msec()))
	return _sequence


func send_message(message: Dictionary) -> void:
	if _peer.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return
	var negotiated_message := message.duplicate(true)
	negotiated_message["protocol"] = _negotiated_protocol
	_peer.send_text(NetworkAdapter.encode_message(negotiated_message))


func supports_session_resume() -> bool:
	return _negotiated_protocol >= 2


func is_websocket_connected() -> bool:
	return _connected and _peer.get_ready_state() == WebSocketPeer.STATE_OPEN


func last_sequence() -> int:
	return _sequence


func _process(_delta: float) -> void:
	_peer.poll()
	var state := _peer.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN and not _connected:
		_connected = true
		_closed_reported = false
		status_changed.emit("websocket_connected")
		send_message(NetworkAdapter.hello_message())
	elif state == WebSocketPeer.STATE_CLOSED and not _closed_reported:
		_connected = false
		_closed_reported = true
		status_changed.emit("websocket_closed")
	while _peer.get_available_packet_count() > 0:
		var payload := _peer.get_packet().get_string_from_utf8()
		var message := NetworkAdapter.parse_message(payload)
		if str(message.get("type", "")) == NetworkAdapter.MESSAGE_HELLO:
			var negotiated := NetworkAdapter.negotiated_protocol(message)
			if negotiated > 0:
				_negotiated_protocol = negotiated
		message_received.emit(message)
