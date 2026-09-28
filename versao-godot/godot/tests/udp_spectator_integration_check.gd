extends SceneTree

const UdpClient := preload("res://scripts/udp_client.gd")

var _client: Node
var _elapsed := 0.0
var _joined := false
var _chat_accepted := false


func _init() -> void:
	_client = UdpClient.new()
	_client.status_changed.connect(_on_status)
	_client.message_received.connect(_on_message)
	root.add_child(_client)
	var endpoint := OS.get_environment("GROUNDFIRE_TEST_UDP_ENDPOINT")
	if endpoint.is_empty():
		endpoint = "127.0.0.1:28015"
	assert(_client.connect_to_endpoint(endpoint) == OK)


func _process(delta: float) -> bool:
	_elapsed += delta
	if _joined and _chat_accepted:
		_client.disconnect_from_endpoint("spectator_integration_complete")
		quit(0)
		return true
	if _elapsed >= 8.0:
		push_error("Timed out waiting for the Python UDP spectator flow")
		quit(1)
	return false


func _on_status(status: String) -> void:
	assert(status != "websocket_connect_failed")


func _on_message(message: Dictionary) -> void:
	var message_type := str(message.get("type", ""))
	if message_type == "hello":
		_client.join("Godot Caster", "", "", true)
		return
	if message_type == "snapshot":
		var state := Dictionary(message.get("state", {}))
		assert(bool(state.get("joined", false)))
		assert(str(state.get("role", "")) == "spectator")
		assert(int(state.get("player_number", 0)) == -1)
		assert(not str(state.get("resume_token", "")).is_empty())
		assert(_client.send_input({"fire": true}) == 0)
		if not _joined:
			_joined = true
			_client.send_chat("Spectator integration chat")
		return
	if message_type == "command_result" and str(message.get("command", "")) == "chat_send":
		assert(bool(message.get("accepted", false)))
		_chat_accepted = true
