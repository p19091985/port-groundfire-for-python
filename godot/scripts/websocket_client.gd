extends Node

const NetworkAdapter := preload("res://scripts/network_adapter.gd")

signal status_changed(status: String)
signal message_received(message: Dictionary)

var _peer := WebSocketPeer.new()
var _endpoint := ""
var _sequence := 0
var _connected := false
var _closed_reported := true


func connect_to_endpoint(endpoint: String) -> int:
	_endpoint = endpoint
	_peer = WebSocketPeer.new()
	_connected = false
	_closed_reported = false
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


func join(player_name: String, password := "") -> void:
	send_message(NetworkAdapter.join_message(player_name, password))


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
	_peer.send_text(NetworkAdapter.encode_message(message))


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
		message_received.emit(NetworkAdapter.parse_message(payload))
