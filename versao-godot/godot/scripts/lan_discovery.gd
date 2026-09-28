extends Node

const DEFAULT_DISCOVERY_PORT := 27016
const EXPIRY_MSEC := 3000
const PROTOCOL_VERSION := 1

signal servers_changed(entries: Array[Dictionary])

var _peer := PacketPeerUDP.new()
var _servers: Dictionary = {}
var _listening := false


func start(port := DEFAULT_DISCOVERY_PORT) -> int:
	_peer = PacketPeerUDP.new()
	var error := _peer.bind(port, "0.0.0.0")
	if error != OK:
		return error
	_listening = true
	set_process(true)
	return OK


func stop() -> void:
	_peer.close()
	_listening = false
	set_process(false)
	_servers.clear()


func _exit_tree() -> void:
	stop()


func entries() -> Array[Dictionary]:
	_expire_servers()
	var result: Array[Dictionary] = []
	for value in _servers.values():
		result.append(Dictionary(value["entry"]).duplicate(true))
	result.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return str(a["name"]).to_lower() < str(b["name"]).to_lower())
	return result


func _process(_delta: float) -> void:
	if not _listening:
		return
	var changed := false
	while _peer.get_available_packet_count() > 0:
		var packet := _peer.get_packet()
		var sender_ip := _peer.get_packet_ip()
		var decoded = JSON.parse_string(packet.get_string_from_utf8())
		if typeof(decoded) != TYPE_DICTIONARY:
			continue
		var envelope := Dictionary(decoded)
		if str(envelope.get("message_type", "")) != "LanServerAnnouncement":
			continue
		var payload := Dictionary(envelope.get("payload", {}))
		if int(payload.get("protocol_version", 0)) != PROTOCOL_VERSION:
			continue
		var game_port := int(payload.get("server_port", 0))
		if game_port <= 0 or game_port > 65535:
			continue
		var session_id := str(payload.get("session_id", ""))
		var endpoint := "%s:%d" % [sender_ip, game_port]
		var key := "%s/%s" % [endpoint, session_id]
		_servers[key] = {
			"last_seen_msec": Time.get_ticks_msec(),
			"entry": {
				"name": str(payload.get("server_name", "Groundfire LAN")),
				"game": "Groundfire",
				"players": "%d/%d" % [int(payload.get("player_count", 0)), int(payload.get("max_players", 0))],
				"map": "Seed %d" % int(payload.get("map_seed", 1)),
				"latency": "LAN",
				"source": "lan",
				"endpoint": endpoint,
				"passworded": bool(payload.get("requires_password", false)),
				"region": str(payload.get("region", "local")),
				"secure": bool(payload.get("secure", true)),
				"session_id": session_id,
			},
		}
		changed = true
	if _expire_servers():
		changed = true
	if changed:
		servers_changed.emit(entries())


func _expire_servers() -> bool:
	var now := Time.get_ticks_msec()
	var changed := false
	for key in _servers.keys():
		if now - int(Dictionary(_servers[key]).get("last_seen_msec", now)) > EXPIRY_MSEC:
			_servers.erase(key)
			changed = true
	return changed
