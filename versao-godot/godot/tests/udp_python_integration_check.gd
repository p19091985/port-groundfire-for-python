extends SceneTree

const UdpClient := preload("res://scripts/udp_client.gd")
const LanDiscovery := preload("res://scripts/lan_discovery.gd")

var _client: Node
var _elapsed := 0.0
var _joined := false
var _discovered := false
var _saw_full_snapshot := false
var _saw_delta_snapshot := false
var _resume_started := false
var _resumed := false
var _post_resume_snapshot := false
var _resume_session_id := ""
var _resume_token := ""
var _resume_player_number := -1
var _endpoint := ""


func _init() -> void:
	_client = UdpClient.new()
	_client.status_changed.connect(_on_status)
	_client.message_received.connect(_on_message)
	root.add_child(_client)
	var discovery := LanDiscovery.new()
	discovery.servers_changed.connect(_on_servers_changed)
	root.add_child(discovery)
	var discovery_port := int(OS.get_environment("GROUNDFIRE_TEST_DISCOVERY_PORT"))
	if discovery_port <= 0:
		discovery_port = LanDiscovery.DEFAULT_DISCOVERY_PORT
	assert(discovery.start(discovery_port) == OK)
	_endpoint = OS.get_environment("GROUNDFIRE_TEST_UDP_ENDPOINT")
	if _endpoint.is_empty():
		_endpoint = "127.0.0.1:28015"
	assert(_client.connect_to_endpoint(_endpoint) == OK)


func _process(delta: float) -> bool:
	_elapsed += delta
	if _joined and _discovered and _post_resume_snapshot:
		_client.disconnect_from_endpoint("integration_complete")
		quit(0)
		return true
	if _elapsed >= 8.0:
		push_error("Timed out waiting for the Python UDP resume flow")
		quit(1)
	return false


func _on_status(status: String) -> void:
	assert(status != "websocket_connect_failed")


func _on_message(message: Dictionary) -> void:
	var message_type := str(message.get("type", ""))
	if message_type == "hello":
		if _resume_started:
			_client.resume_session(
				_resume_session_id,
				_resume_player_number,
				_resume_token,
				"Godot UDP Test"
			)
		else:
			_client.join("Godot UDP Test")
		return
	if message_type == "session_resumed":
		assert(str(message.get("session_id", "")) == _resume_session_id)
		assert(int(message.get("player_number", -1)) == _resume_player_number)
		assert(str(message.get("resume_token", "")) == _resume_token)
		_resumed = true
		return
	if message_type != "snapshot":
		return
	var state := Dictionary(message.get("state", {}))
	assert(bool(state.get("joined", false)))
	assert(int(state.get("player_number", -1)) >= 0)
	assert(not str(state.get("session_id", "")).is_empty())
	assert(not str(state.get("resume_token", "")).is_empty())
	var match_snapshot := Dictionary(state.get("match_snapshot", {}))
	assert(not Array(match_snapshot.get("players", [])).is_empty())
	if _resumed:
		assert(int(state.get("player_number", -1)) == _resume_player_number)
		if str(state.get("snapshot_kind", "")) != "full":
			return
		_post_resume_snapshot = true
		_joined = true
		return
	var snapshot_kind := str(state.get("snapshot_kind", ""))
	if snapshot_kind == "full":
		_saw_full_snapshot = true
	elif snapshot_kind == "delta":
		assert(_saw_full_snapshot)
		assert(int(state.get("baseline_snapshot_sequence", 0)) > 0)
		_saw_delta_snapshot = true
	_joined = true
	if _saw_full_snapshot and _saw_delta_snapshot and not _resume_started:
		_resume_session_id = str(state.get("session_id", ""))
		_resume_token = str(state.get("resume_token", ""))
		_resume_player_number = int(state.get("player_number", -1))
		_resume_started = true
		_client.abort_connection()
		call_deferred("_reconnect_for_resume")


func _reconnect_for_resume() -> void:
	assert(_client.connect_to_endpoint(_endpoint) == OK)


func _on_servers_changed(entries: Array[Dictionary]) -> void:
	for entry in entries:
		if str(entry.get("name", "")) == "GodotUDPIntegration":
			assert(str(entry.get("source", "")) == "lan")
			assert(str(entry.get("endpoint", "")).contains(":"))
			_discovered = true
