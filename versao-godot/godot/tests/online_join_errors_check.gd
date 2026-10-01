extends SceneTree
const Online := preload("res://scripts/online_match.gd")
const Store := preload("res://scripts/browser_store.gd")
var failures: Array[String] = []
var endpoint := ""

func _init() -> void:
	call_deferred("_run")

func check(condition: bool, label: String) -> void:
	if not condition:
		failures.append(label)
		push_error(label)

func client(password: String, retry := false) -> Control:
	var online := Online.new()
	online.setup({"endpoint":endpoint, "name":"Join errors fixture", "password":password, "auto_retry_when_full":retry})
	root.add_child(online)
	return online

func until(predicate: Callable, label: String, seconds := 2.0) -> void:
	var deadline := Time.get_ticks_msec() + int(seconds * 1000)
	while not predicate.call() and Time.get_ticks_msec() < deadline:
		await process_frame
	check(predicate.call(),label)

func dispose(online: Control) -> void:
	online._stop_session("test_finished")
	online.queue_free()
	await process_frame

func _run() -> void:
	endpoint = OS.get_environment("GROUNDFIRE_TEST_UDP_ENDPOINT")
	check(not endpoint.is_empty(),"Test requires password-protected one-slot Python server")
	var original := Store.load_store()
	Store.save_store([],[],Store.default_filters())
	for password in ["", "wrong-test-password"]:
		var rejected := client(password)
		await until(func() -> bool: return rejected._fatal_server_failure, "Invalid credentials rejected")
		check(not rejected._history_recorded,"Rejected join must not record history")
		check(Store.load_store().get("history",[]).is_empty(),"Rejected joins keep persisted history empty")
		check(rejected._manual_disconnect and rejected._reconnect_timer == 0.0,"Bad password must not retry automatically")
		await dispose(rejected)
	var holder := client("fixture-only")
	await until(func() -> bool: return holder._snapshot.get("joined",false), "Correct password joins real server")
	check(holder._history_recorded,"Confirmed join records history")
	holder._entry["is_computer"] = true
	holder._pending_commands.clear()
	holder._send_input_snapshot()
	check(holder._pending_commands.is_empty(),"AI connection must not send human gameplay commands")
	holder._entry["is_computer"] = false
	var full := client("fixture-only")
	await until(func() -> bool: return full._fatal_server_failure, "Full server rejects without auto retry")
	check(not full._history_recorded,"Capacity rejection must not record another join")
	await dispose(full)
	var cancelled := client("fixture-only",true)
	await until(func() -> bool: return cancelled._capacity_retry_timer > 0.0, "Full server schedules slot wait")
	cancelled._reconnect_timer = 0.1
	cancelled._stop_session("cancel_wait")
	check(cancelled._capacity_retry_timer == 0.0 and cancelled._reconnect_timer == 0.0,"Cancel clears all retry timers immediately")
	cancelled._on_websocket_message_received({"type":"hello", "protocol":1})
	cancelled._update_reconnect(1.0)
	check(not cancelled._join_sent and cancelled._manual_disconnect,"Late hello/retry cannot revive a cancelled join")
	var waiting := client("fixture-only",true)
	await until(func() -> bool: return waiting._capacity_retry_timer > 0.0, "Second waiter reaches capacity wait")
	check(waiting._capacity_retry_timer <= 1.0,"Slot retry must use Python's one-second interval")
	await dispose(holder)
	await until(func() -> bool: return waiting._snapshot.get("joined",false), "Waiter joins after slot is freed",5.0)
	check(not cancelled._snapshot.get("joined",false),"Cancelled waiter stays disconnected after slot opens")
	check(waiting._history_recorded,"Successful deferred join records history")
	await dispose(waiting)
	await dispose(cancelled)
	# Restore the isolated test store instead of changing developer preferences.
	var favorites: Array[String] = []
	for value in original.get("favorites",[]): favorites.append(str(value))
	var history: Array[Dictionary] = []
	for value in original.get("history",[]): history.append(Dictionary(value))
	Store.save_store(favorites,history,original.get("filters",{}))
	if failures.is_empty(): print("Real Python join errors passed: passwords, full server, slot release, cancellation, history")
	quit(0 if failures.is_empty() else 1)
