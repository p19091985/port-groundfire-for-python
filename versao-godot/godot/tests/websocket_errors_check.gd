extends SceneTree
const Main := preload("res://scenes/main.tscn")
const Online := preload("res://scripts/online_match.gd")
const Store := preload("res://scripts/browser_store.gd")
const WebSocketClient := preload("res://scripts/websocket_client.gd")
var failures: Array[String] = []
var results: Array[Dictionary] = []
var app: Control
var endpoints: Dictionary

func _init() -> void:
	call_deferred("run")

func check(value: bool, message: String) -> void:
	results.append({"label":message,"status":"passed" if value else "failed"})
	if not value:
		failures.append(message)
		push_error(message)

func until(predicate: Callable, label: String, seconds := 3.0) -> void:
	var deadline := Time.get_ticks_msec()+int(seconds*1000)
	while not predicate.call() and Time.get_ticks_msec()<deadline:
		await process_frame
	check(predicate.call(),label)

func open(name: String, extra: Dictionary = {}) -> Control:
	var entry := {"endpoint":endpoints[name],"name":"WebSocket fixture"}
	entry.merge(extra,true)
	app._show_online_match(entry)
	return app._screen

func back(online: Control) -> void:
	online._back_button.pressed.emit()
	check(online._manual_disconnect and online._reconnect_timer == 0.0 and online._capacity_retry_timer == 0.0,"Back immediately cancels attempts")
	check(app._screen != online,"Back leaves online screen")
	await process_frame

func has_local_participant(online: Control) -> bool:
	for player in online._snapshot.get("match_snapshot",{}).get("players",[]):
		if int(player.get("player_number",-2)) == online._local_player_number:
			return true
	return false

func run() -> void:
	endpoints = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("GROUNDFIRE_TEST_WS_FIXTURE")))
	app = Main.instantiate()
	root.add_child(app)
	Store.save_store([],[],Store.default_filters())
	for fixture in [
		["password",{},"password rejected"],
		["password",{"password":"wrong"},"password rejected"],
		["auth",{},"authentication was rejected"],
		["closed",{},"server is closed"],
		["banned",{},"access was rejected"]]:
		var rejected := open(fixture[0],fixture[1])
		await until(func() -> bool: return rejected._fatal_server_failure,"Real gateway rejects " + fixture[0])
		check(rejected._status.contains(fixture[2]),"Error status retained for " + fixture[0])
		check(not rejected._history_recorded,"Rejected connection does not record history")
		await back(rejected)
	check(Store.load_store().get("history",[]).is_empty(),"Failures keep persisted history empty")
	var mismatch := open("protocol")
	await until(func() -> bool: return mismatch._protocol_failure,"Incompatible hello is rejected")
	check(not mismatch._join_sent,"Incompatible server never receives a join")
	await back(mismatch)
	for name in ["http-stall","hello-stall"]:
		var stalled := open(name)
		await until(func() -> bool: return stalled._reconnect_attempt > 0,"Bounded timeout for " + name,7.0)
		check(not stalled._history_recorded,"Timeout does not record history")
		await back(stalled)
	var malformed := WebSocketClient.new()
	var invalid_messages: Array[Dictionary] = []
	malformed.message_received.connect(func(message: Dictionary) -> void:
		if message.get("type") == "hello":
			malformed.send_message({"type":"join","player_name":"Malformed", "password":"fixture-only", "is_computer":"false"})
		elif message.get("type") == "error":
			invalid_messages.append(message))
	root.add_child(malformed)
	malformed.connect_to_endpoint(endpoints.password)
	await until(func() -> bool: return not invalid_messages.is_empty(),"Gateway rejects malformed AI flag")
	if not invalid_messages.is_empty():
		check(invalid_messages[0].get("message") == "invalid_field" and invalid_messages[0].get("field") == "is_computer","AI flag must be a boolean")
	malformed.disconnect_from_endpoint("invalid_field_test_done")
	malformed.queue_free()
	await process_frame
	var holder := Online.new()
	holder.setup({"endpoint":endpoints.password,"password":"fixture-only"})
	root.add_child(holder)
	await until(func() -> bool: return holder._snapshot.get("joined",false),"Correct credentials join through real gateway")
	var full := open("password",{"password":"fixture-only"})
	await until(func() -> bool: return full._fatal_server_failure,"Full gateway rejects without waiting")
	check(full._status.contains("server is full"),"Full gateway message")
	await back(full)
	var cancelled := open("password",{"password":"fixture-only","auto_retry_when_full":true})
	await until(func() -> bool: return cancelled._capacity_retry_timer > 0.0,"Full gateway offers wait")
	await back(cancelled)
	var waiting := open("password",{"password":"fixture-only","auto_retry_when_full":true})
	await until(func() -> bool: return waiting._capacity_retry_timer > 0.0,"Second waiter reaches capacity wait")
	holder._stop_session("release_slot")
	holder.queue_free()
	await until(func() -> bool: return waiting._snapshot.get("joined",false),"Waiter joins after slot release",5.0)
	check(waiting._history_recorded,"Successful gateway join records history")
	await back(waiting)
	for journey in [["password","human"],["password","ai"],["password","spectator"],["udp","human"]]:
		var target: String = journey[0]
		var role: String = journey[1]
		app._show_server_browser()
		var browser: Control = app._screen
		var view: Control = browser.get_node("ClassicBrowser")
		view.show_join({"endpoint":endpoints[target],"name":"Gateway UI journey"})
		check(browser._password_line.text.is_empty(),"Reentry starts without previous credentials")
		browser._password_line.text = "fixture-only" if target == "password" else ""
		view.join_role = role
		var enter := InputEventKey.new()
		enter.keycode = KEY_ENTER
		enter.pressed = true
		view._dialog_input(enter)
		check(browser._password_line.text.is_empty(),"Submitting dialog clears its password field")
		var joined: Control = app._screen
		check(joined != browser and joined is Online,"Browser confirmation opens online screen")
		if joined == browser:
			continue
		await until(func() -> bool: return joined._snapshot.get("joined",false),"Browser joins as " + role)
		check(joined._spectating == (role == "spectator"),"Server role agrees with browser selection")
		if role != "spectator":
			await until(func() -> bool: return has_local_participant(joined),"Authoritative participant arrives for " + role)
			var participants: Array = joined._snapshot.get("match_snapshot",{}).get("players",[])
			var found := false
			for participant in participants:
				if int(participant.get("player_number",-2)) == joined._local_player_number:
					found = true
					check(bool(participant.get("is_computer",false)) == (role == "ai"),"Server AI flag agrees with browser selection")
			check(found,"Joined participant exists in authoritative snapshot")
		await back(joined)
		await create_timer(0.15).timeout
	app._show_server_browser()
	var browser: Control = app._screen
	browser._on_back_pressed()
	check(app._screen != browser,"Browser Back returns to main menu")
	app.queue_free()
	await process_frame
	var report := FileAccess.open(OS.get_environment("GROUNDFIRE_TEST_WS_RESULTS"),FileAccess.WRITE)
	if report != null:
		report.store_string(JSON.stringify(results,"  "))
		report.close()
	if failures.is_empty(): print("WebSocket screen checks passed")
	quit(0 if failures.is_empty() else 1)
