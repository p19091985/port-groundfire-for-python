extends Node
## A cancellable Ping/Pong query; never joins or allocates a player slot.
signal completed(endpoint: String, latency_ms: int)
const UdpClient := preload("res://scripts/udp_client.gd")
const TIMEOUT_MSEC := 80
var _peer := PacketPeerUDP.new()
var _resolver := -1
var _endpoint := ""
var _port := 0
var _nonce := ""
var _started := 0
var _active := false

func cancel() -> void:
	_active = false
	_peer.close()
	if _resolver != -1:
		IP.erase_resolve_item(_resolver)
		_resolver = -1

func _exit_tree() -> void:
	cancel()

func start(endpoint: String) -> void:
	cancel()
	_endpoint = endpoint
	_started = Time.get_ticks_msec()
	_nonce = Crypto.new().generate_random_bytes(16).hex_encode()
	_active = true
	var parser := UdpClient.new()
	var address: Dictionary = parser._parse_endpoint(endpoint)
	parser.free()
	if address.is_empty():
		_finish(-1)
		return
	_port = int(address.port)
	var host := str(address.host)
	if host.is_valid_ip_address():
		_send(host)
	else:
		_resolver = IP.resolve_hostname_queue_item(host, IP.TYPE_IPV4)
		if _resolver == -1:
			_finish(-1)

func _send(host: String) -> void:
	_peer = PacketPeerUDP.new()
	if _peer.connect_to_host(host, _port) != OK:
		_finish(-1)
		return
	var packet := {"message_type":"Ping", "payload":{"nonce":_nonce, "issued_at":_started/1000.0, "protocol_version":1}}
	if _peer.put_packet(JSON.stringify(packet).to_utf8_buffer()) != OK:
		_finish(-1)

func _process(_delta: float) -> void:
	if not _active:
		return
	if Time.get_ticks_msec() - _started > TIMEOUT_MSEC:
		_finish(-1)
		return
	if _resolver != -1:
		var status := IP.get_resolve_item_status(_resolver)
		if status == IP.RESOLVER_STATUS_WAITING:
			return
		var host := IP.get_resolve_item_address(_resolver) if status == IP.RESOLVER_STATUS_DONE else ""
		IP.erase_resolve_item(_resolver)
		_resolver = -1
		if host.is_empty():
			_finish(-1)
			return
		_send(host)
	while _active and _peer.get_available_packet_count() > 0:
		var envelope = JSON.parse_string(_peer.get_packet().get_string_from_utf8())
		if not envelope is Dictionary or envelope.get("message_type") != "Pong":
			continue
		var payload = envelope.get("payload")
		if payload is Dictionary and payload.get("nonce") == _nonce and payload.get("protocol_version") == 1:
			_finish(Time.get_ticks_msec() - _started)

func _finish(latency: int) -> void:
	var endpoint := _endpoint
	cancel()
	completed.emit(endpoint, latency)
