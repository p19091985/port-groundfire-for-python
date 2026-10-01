extends SceneTree
const Browser := preload("res://scripts/server_browser.gd")
var failures: Array[String] = []
var browser: Control
var view: Control

func _init() -> void:
	call_deferred("_run")

func check(condition: bool, label: String) -> void:
	if not condition:
		failures.append(label)
		push_error(label)

func fixture(endpoint: String) -> void:
	view.close_dialog()
	browser._entries.assign([{"name":"Probe fixture", "endpoint":endpoint, "source":"online", "players":"0/8", "latency":"12"}])
	browser._filter_text = ""
	browser._hide_full = false
	browser._hide_empty = false
	browser._hide_passworded = false
	browser._secure_only = false
	browser._region = ""
	browser._max_latency = 0
	browser._render_entries()

func receive(peer: PacketPeerUDP) -> Dictionary:
	var deadline := Time.get_ticks_msec() + 500
	while peer.get_available_packet_count() == 0 and Time.get_ticks_msec() < deadline:
		await process_frame
	if peer.get_available_packet_count() == 0:
		check(false,"Probe must send a real UDP datagram")
		return {}
	var value = JSON.parse_string(peer.get_packet().get_string_from_utf8())
	peer.set_dest_address(peer.get_packet_ip(),peer.get_packet_port())
	check(value is Dictionary and value.get("message_type") == "Ping", "Availability must only send Ping, never Join")
	return value.get("payload",{}) if value is Dictionary else {}

func pong(peer: PacketPeerUDP, payload: Dictionary) -> void:
	peer.put_packet(JSON.stringify({"message_type":"Pong", "payload":payload}).to_utf8_buffer())

func _run() -> void:
	browser = Browser.new()
	browser.classic_presentation = true
	root.add_child(browser)
	view = browser.get_node("ClassicBrowser")
	if browser._lan_discovery != null:
		browser._lan_discovery.stop()
	browser._http_request.cancel_request()
	browser._directory_loading = false
	var peer := PacketPeerUDP.new()
	check(peer.bind(0,"127.0.0.1") == OK,"Bind local fixture")
	var endpoint := "127.0.0.1:%d" % peer.get_local_port()
	fixture(endpoint)
	browser._on_connect_pressed()
	var payload: Dictionary = await receive(peer)
	check(view.dialog.is_empty(),"Do not open Join before Pong")
	pong(peer,payload)
	await create_timer(0.04).timeout
	check(view.dialog == "join", "Valid matching Pong opens Join")
	check(browser._status.text.contains("responded in"),"Successful ping records latency")
	fixture(endpoint)
	browser._on_connect_pressed()
	payload = await receive(peer)
	var bad := payload.duplicate()
	bad.nonce = "stale-nonce"
	pong(peer,bad)
	bad = payload.duplicate()
	bad.protocol_version = 99
	pong(peer,bad)
	peer.put_packet('{"message_type":"Pong","payload":[]}'.to_utf8_buffer())
	await create_timer(0.12).timeout
	check(view.dialog.is_empty(),"Wrong nonce/malformed reply must not open Join")
	check(browser._visible_entries[0].latency == "-", "Timeout invalidates stale latency")
	check(browser._status.text == endpoint + " did not respond. Start the server or refresh the list.", "Timeout uses the Python message")
	pong(peer,payload)
	await create_timer(0.03).timeout
	check(view.dialog.is_empty(),"Reply after deadline cannot reopen Join")
	fixture("localhost:%d" % peer.get_local_port())
	browser._on_connect_pressed()
	payload = await receive(peer)
	pong(peer,payload)
	await create_timer(0.03).timeout
	check(view.dialog == "join", "Hostname resolves asynchronously before ping")
	fixture("groundfire-test.invalid:27015")
	browser._on_connect_pressed()
	await create_timer(0.12).timeout
	check(view.dialog.is_empty() and browser._status.text.contains("did not respond"), "Unresolvable hostname keeps browser responsive")
	for action in ["select", "refresh", "cancel", "filters"]:
		fixture(endpoint)
		browser._on_connect_pressed()
		payload = await receive(peer)
		match action:
			"select": browser._select_row(0)
			"refresh": browser._render_entries()
			"cancel": view.close_dialog()
			"filters": view._show_filters()
		pong(peer,payload)
		await create_timer(0.03).timeout
		check(view.dialog != "join", "Late response after " + action + " must be ignored")
	fixture(endpoint)
	browser._on_connect_pressed()
	var old: Dictionary = await receive(peer)
	browser._on_connect_pressed()
	payload = await receive(peer)
	pong(peer,old)
	await create_timer(0.02).timeout
	check(view.dialog.is_empty(),"An older request cannot satisfy a newer request")
	pong(peer,payload)
	await create_timer(0.02).timeout
	check(view.dialog == "join", "Newest matching response opens Join")
	fixture("invalid:70000")
	browser._on_connect_pressed()
	check(view.dialog.is_empty() and browser._status.text.contains("did not respond"), "Invalid endpoint fails without opening Join")
	fixture("ws://127.0.0.1:8765")
	browser._on_connect_pressed()
	check(view.dialog == "join", "WebSocket endpoint must not require UDP")
	var real_endpoint := OS.get_environment("GROUNDFIRE_TEST_UDP_ENDPOINT")
	if not real_endpoint.is_empty():
		fixture(real_endpoint)
		browser._on_connect_pressed()
		await create_timer(0.12).timeout
		check(view.dialog == "join", "Python server Pong must open the real classic Join dialog")
	fixture(endpoint)
	browser._on_connect_pressed()
	payload = await receive(peer)
	browser.queue_free()
	await process_frame
	pong(peer,payload)
	await create_timer(0.02).timeout
	peer.close()
	if failures.is_empty():
		print("Browser probe checks passed (real UDP, timeout, cancellation, stale replies and WS)")
	quit(0 if failures.is_empty() else 1)
