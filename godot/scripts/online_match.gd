extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const NetworkAdapter := preload("res://scripts/network_adapter.gd")
const WebSocketClient := preload("res://scripts/websocket_client.gd")

const INPUT_INTERVAL := 0.08
const PING_INTERVAL := 1.5
const RECONNECT_BASE_DELAY := 0.75
const RECONNECT_MAX_DELAY := 6.0
const RECONNECT_MAX_ATTEMPTS := 5
const PREDICTION_MOVE_STEP := 0.08
const PREDICTION_ANGLE_STEP := 1.5

var _websocket_client: Node
var _entry: Dictionary = {}
var _endpoint := ""
var _password := ""
var _status := "Preparing online match."
var _snapshot: Dictionary = {}
var _match_snapshot: Dictionary = {}
var _render_entities: Dictionary = {}
var _effects: Array[Dictionary] = []
var _input_tick := 0.0
var _ping_tick := 0.0
var _reconnect_timer := 0.0
var _reconnect_attempt := 0
var _manual_disconnect := false
var _last_latency_ms := -1
var _last_ack_sequence := 0
var _last_snapshot_tick := 0
var _last_terrain_revision := 0
var _pending_commands: Dictionary = {}


func setup(entry: Dictionary) -> void:
	_entry = entry.duplicate()
	_endpoint = str(_entry.get("endpoint", ""))
	_password = str(_entry.get("password", ""))


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	_websocket_client = WebSocketClient.new()
	_websocket_client.status_changed.connect(_on_websocket_status_changed)
	_websocket_client.message_received.connect(_on_websocket_message_received)
	add_child(_websocket_client)
	set_process(true)
	if _endpoint.is_empty():
		_status = "Missing online endpoint."
	else:
		_connect_now("Connecting to %s." % _endpoint)


func _process(delta: float) -> void:
	_update_reconnect(delta)
	if not _websocket_client.is_websocket_connected():
		_update_interpolation(delta)
		_update_effects(delta)
		queue_redraw()
		return
	_input_tick -= delta
	if _input_tick <= 0.0:
		_input_tick = INPUT_INTERVAL
		_send_input_snapshot()
	_ping_tick -= delta
	if _ping_tick <= 0.0:
		_ping_tick = PING_INTERVAL
		_websocket_client.ping()
	_update_interpolation(delta)
	_update_effects(delta)
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") or event.is_action_pressed("gf_pause"):
		_manual_disconnect = true
		_websocket_client.disconnect_from_endpoint("back_to_server_browser")
		get_parent().get_parent()._show_main_menu()


func _send_input_snapshot() -> void:
	if _websocket_client == null:
		return
	if not _websocket_client.is_websocket_connected():
		return
	var command := {
		"aim_left": Input.is_action_pressed("gf_aim_left"),
		"aim_right": Input.is_action_pressed("gf_aim_right"),
		"power_up": Input.is_action_pressed("gf_power_up"),
		"power_down": Input.is_action_pressed("gf_power_down"),
		"move_left": Input.is_action_pressed("gf_move_left"),
		"move_right": Input.is_action_pressed("gf_move_right"),
		"jump": Input.is_action_pressed("gf_jump"),
		"fire": Input.is_action_pressed("gf_fire"),
		"weapon_next": Input.is_action_just_pressed("gf_weapon_next"),
		"weapon_prev": Input.is_action_just_pressed("gf_weapon_prev"),
	}
	var sequence: int = _websocket_client.send_input(command)
	_pending_commands[sequence] = command
	_apply_local_prediction(command)


func _on_websocket_status_changed(status: String) -> void:
	if status == "websocket_connected":
		_reconnect_attempt = 0
		_reconnect_timer = 0.0
		_input_tick = 0.0
		_ping_tick = 0.0
		_websocket_client.join(NetworkAdapter.PLAYER_NAME_DEFAULT, _password)
		_websocket_client.ping()
		_status = "Connected. Waiting for snapshot."
	elif status == "websocket_connecting":
		_status = "Opening WebSocket."
	elif status == "websocket_closed" or status == "websocket_connect_failed":
		_schedule_reconnect(status)
	elif status == "websocket_disconnected":
		_status = "Disconnected."
	else:
		_status = status.capitalize().replace("_", " ")


func _on_websocket_message_received(message: Dictionary) -> void:
	var message_type := str(message.get("type", "unknown"))
	if message_type == NetworkAdapter.MESSAGE_SNAPSHOT:
		_snapshot = Dictionary(message.get("state", {}))
		_match_snapshot = Dictionary(_snapshot.get("match_snapshot", {}))
		_last_snapshot_tick = int(_match_snapshot.get("simulation_tick", _last_snapshot_tick))
		_last_terrain_revision = int(_match_snapshot.get("terrain_revision", _last_terrain_revision))
		_ingest_acknowledgements()
		_ingest_replicated_entities()
		_ingest_events()
		_status = "Snapshot received."
	elif message_type == NetworkAdapter.MESSAGE_PONG:
		_last_latency_ms = max(0, Time.get_ticks_msec() - int(message.get("client_time_msec", Time.get_ticks_msec())))
		_status = "Pong received: %d ms." % _last_latency_ms
	elif message_type == NetworkAdapter.MESSAGE_ERROR:
		_status = "Error: %s." % message.get("message", "unknown")
	elif message_type == NetworkAdapter.MESSAGE_DISCONNECT:
		_status = "Server disconnected: %s." % message.get("reason", "unknown")
		_schedule_reconnect("server_disconnect")
	else:
		_status = "Message: %s." % message_type


func _connect_now(message: String) -> void:
	_manual_disconnect = false
	_status = message
	_websocket_client.connect_to_endpoint(_endpoint)


func _schedule_reconnect(reason: String) -> void:
	if _manual_disconnect:
		_status = "Disconnected."
		return
	if _endpoint.is_empty():
		_status = "Disconnected: missing endpoint."
		return
	if _reconnect_attempt >= RECONNECT_MAX_ATTEMPTS:
		_status = "Connection lost (%s). Reconnect failed." % reason
		return
	_reconnect_attempt += 1
	_reconnect_timer = min(RECONNECT_MAX_DELAY, RECONNECT_BASE_DELAY * pow(2.0, float(_reconnect_attempt - 1)))
	_status = "Connection lost (%s). Reconnecting in %.1fs (%d/%d)." % [
		reason.replace("websocket_", ""),
		_reconnect_timer,
		_reconnect_attempt,
		RECONNECT_MAX_ATTEMPTS,
	]


func _update_reconnect(delta: float) -> void:
	if _reconnect_timer <= 0.0:
		return
	_reconnect_timer = max(0.0, _reconnect_timer - delta)
	if _reconnect_timer <= 0.0:
		_connect_now("Reconnecting to %s." % _endpoint)


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), GroundfireTheme.COLOR_BG)
	_draw_header()
	_draw_replicated_world()
	_draw_snapshot_panel()


func _draw_header() -> void:
	draw_string(ThemeDB.fallback_font, Vector2(28.0, 46.0), "Groundfire Online Match", HORIZONTAL_ALIGNMENT_LEFT, -1, 28, GroundfireTheme.COLOR_TEXT)
	draw_string(ThemeDB.fallback_font, Vector2(28.0, 76.0), _endpoint, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, GroundfireTheme.COLOR_CYAN)
	draw_string(ThemeDB.fallback_font, Vector2(28.0, 104.0), _status, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, GroundfireTheme.COLOR_WARN)


func _draw_replicated_world() -> void:
	var world_rect := Rect2(28.0, 124.0, max(320.0, size.x - 56.0), max(260.0, size.y - 300.0))
	draw_rect(world_rect, Color("#07131ecc"))
	draw_rect(world_rect, GroundfireTheme.COLOR_LINE, false, 2.0)
	if _match_snapshot.is_empty():
		draw_string(ThemeDB.fallback_font, world_rect.position + Vector2(18.0, 42.0), "No replicated match snapshot yet.", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, GroundfireTheme.COLOR_MUTED)
		return
	_draw_terrain_profile(world_rect)
	_draw_entities(world_rect)
	_draw_players(world_rect)


func _draw_terrain_profile(world_rect: Rect2) -> void:
	var profile: Array = Array(_match_snapshot.get("terrain_profile", []))
	if profile.size() < 2:
		return
	var world_width := float(_match_snapshot.get("world_width", 20.0))
	var points := PackedVector2Array()
	points.append(Vector2(world_rect.position.x, world_rect.end.y))
	for index in range(profile.size()):
		var world_x := -world_width * 0.5 + (float(index) / float(profile.size() - 1)) * world_width
		points.append(_world_to_screen(Vector2(world_x, float(profile[index])), world_rect))
	points.append(Vector2(world_rect.end.x, world_rect.end.y))
	draw_colored_polygon(points, Color("#244326"))
	for index in range(1, points.size() - 2):
		draw_line(points[index], points[index + 1], Color("#6fbf73"), 2.0)


func _draw_entities(world_rect: Rect2) -> void:
	for entity_id in _render_entities.keys():
		var entity: Dictionary = _render_entities[entity_id]
		var screen_position := _world_to_screen(Vector2(entity.get("render_position", Vector2.ZERO)), world_rect)
		var entity_type := str(entity.get("entity_type", "entity"))
		if entity_type == "tank":
			_draw_replicated_tank(screen_position, entity)
		elif entity_type == "projectile":
			_draw_replicated_projectile(screen_position, entity)
		else:
			draw_circle(screen_position, 5.0, GroundfireTheme.COLOR_WARN)
	for effect in _effects:
		var effect_position := _world_to_screen(Vector2(effect.get("position", Vector2.ZERO)), world_rect)
		draw_circle(effect_position, float(effect.get("radius", 8.0)), Color("#f59e0b66"))


func _draw_replicated_projectile(screen_position: Vector2, entity: Dictionary) -> void:
	draw_circle(screen_position, 5.0, GroundfireTheme.COLOR_WARN)
	var velocity := _entity_velocity(entity)
	if velocity.length_squared() > 0.0:
		var tail := screen_position - velocity.normalized() * 18.0
		draw_line(tail, screen_position, Color("#ffd16699"), 2.0)


func _draw_replicated_tank(screen_position: Vector2, entity: Dictionary) -> void:
	var owner := int(entity.get("owner_player", 0))
	var color := GroundfireTheme.COLOR_ACCENT_HOT if owner == 1 else Color("#4d95ff")
	draw_rect(Rect2(screen_position.x - 22.0, screen_position.y - 18.0, 44.0, 20.0), color)
	draw_circle(screen_position + Vector2(-13.0, 3.0), 6.0, Color("#111f2b"))
	draw_circle(screen_position + Vector2(13.0, 3.0), 6.0, Color("#111f2b"))
	var payload := Dictionary(entity.get("payload", {}))
	var health := float(payload.get("health", 100))
	draw_rect(Rect2(screen_position.x - 24.0, screen_position.y - 34.0, 48.0 * health / 100.0, 5.0), Color("#56d364"))
	var angle := deg_to_rad(float(entity.get("angle", 0.0)))
	var barrel_end := screen_position + Vector2(cos(angle), -sin(angle)) * 42.0
	draw_line(screen_position + Vector2(0.0, -16.0), barrel_end, GroundfireTheme.COLOR_WARN, 3.0)


func _draw_players(world_rect: Rect2) -> void:
	var panel := Rect2(world_rect.position.x + 14.0, world_rect.position.y + 14.0, 280.0, 92.0)
	draw_rect(panel, Color("#0b1722cc"))
	draw_rect(panel, GroundfireTheme.COLOR_LINE, false, 1.0)
	var title := "Round %s  Tick %s" % [
		str(_match_snapshot.get("current_round", 0)),
		str(_match_snapshot.get("simulation_tick", 0)),
	]
	draw_string(ThemeDB.fallback_font, panel.position + Vector2(12.0, 26.0), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, GroundfireTheme.COLOR_WARN)
	var y := panel.position.y + 52.0
	for raw_player in Array(_match_snapshot.get("players", [])):
		if typeof(raw_player) != TYPE_DICTIONARY:
			continue
		var player := Dictionary(raw_player)
		var line := "%s  score %s  money %s" % [
			str(player.get("name", "Player")),
			str(player.get("score", 0)),
			str(player.get("money", 0)),
		]
		draw_string(ThemeDB.fallback_font, Vector2(panel.position.x + 12.0, y), line, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, GroundfireTheme.COLOR_TEXT)
		y += 20.0


func _draw_snapshot_panel() -> void:
	var panel := Rect2(28.0, max(400.0, size.y - 172.0), min(size.x - 56.0, 900.0), 140.0)
	draw_rect(panel, Color("#0b1722cc"))
	draw_rect(panel, GroundfireTheme.COLOR_LINE, false, 2.0)
	if _snapshot.is_empty():
		draw_string(ThemeDB.fallback_font, panel.position + Vector2(18.0, 44.0), "No server snapshot yet.", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, GroundfireTheme.COLOR_MUTED)
		_draw_network_diagnostics(panel.position + Vector2(18.0, 76.0))
		return
	var y := panel.position.y + 38.0
	for key in ["status", "player_name", "joined", "server_time_msec"]:
		draw_string(
			ThemeDB.fallback_font,
			Vector2(panel.position.x + 18.0, y),
			"%s: %s" % [str(key), str(_snapshot[key])],
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			16,
			GroundfireTheme.COLOR_TEXT
		)
		y += 24.0
	_draw_network_diagnostics(Vector2(panel.position.x + 360.0, panel.position.y + 38.0))


func _draw_network_diagnostics(origin: Vector2) -> void:
	var latency_text := "n/a" if _last_latency_ms < 0 else "%d ms" % _last_latency_ms
	var lines := PackedStringArray([
		"latency: %s" % latency_text,
		"ack: %d  pending: %d" % [_last_ack_sequence, _pending_commands.size()],
		"tick: %d  terrain: %d" % [_last_snapshot_tick, _last_terrain_revision],
	])
	for index in range(lines.size()):
		draw_string(
			ThemeDB.fallback_font,
			origin + Vector2(0.0, float(index) * 24.0),
			lines[index],
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			15,
			GroundfireTheme.COLOR_CYAN if index == 0 else GroundfireTheme.COLOR_TEXT
		)


func _entity_position(entity: Dictionary) -> Vector2:
	var raw_position: Variant = entity.get("position", [0.0, 0.0])
	if typeof(raw_position) == TYPE_ARRAY and raw_position.size() >= 2:
		return Vector2(float(raw_position[0]), float(raw_position[1]))
	return Vector2.ZERO


func _entity_velocity(entity: Dictionary) -> Vector2:
	var raw_velocity: Variant = entity.get("velocity", [0.0, 0.0])
	if typeof(raw_velocity) == TYPE_ARRAY and raw_velocity.size() >= 2:
		return Vector2(float(raw_velocity[0]), float(raw_velocity[1]))
	return Vector2.ZERO


func _ingest_replicated_entities() -> void:
	var live_ids: Array[int] = []
	for raw_entity in Array(_match_snapshot.get("entities", [])):
		if typeof(raw_entity) != TYPE_DICTIONARY:
			continue
		var entity := Dictionary(raw_entity)
		var entity_id := int(entity.get("entity_id", 0))
		var target_position := _entity_position(entity)
		live_ids.append(entity_id)
		if _render_entities.has(entity_id):
			var current := Dictionary(_render_entities[entity_id])
			current["target_position"] = target_position
			current["velocity"] = _entity_velocity(entity)
			current["angle"] = float(entity.get("angle", 0.0))
			current["payload"] = Dictionary(entity.get("payload", {}))
			current["owner_player"] = int(entity.get("owner_player", 0))
			current["entity_type"] = str(entity.get("entity_type", "entity"))
			_render_entities[entity_id] = current
		else:
			entity["render_position"] = target_position
			entity["target_position"] = target_position
			entity["velocity"] = _entity_velocity(entity)
			_render_entities[entity_id] = entity
	for entity_id in _render_entities.keys():
		if not live_ids.has(int(entity_id)):
			_render_entities.erase(entity_id)


func _ingest_acknowledgements() -> void:
	var acknowledged := _last_ack_sequence
	for raw_player in Array(_match_snapshot.get("players", [])):
		if typeof(raw_player) != TYPE_DICTIONARY:
			continue
		var player := Dictionary(raw_player)
		if int(player.get("player_number", -1)) == 1 or str(player.get("name", "")) == NetworkAdapter.PLAYER_NAME_DEFAULT:
			acknowledged = max(acknowledged, int(player.get("acknowledged_command_sequence", acknowledged)))
	_last_ack_sequence = acknowledged
	for sequence in _pending_commands.keys():
		if int(sequence) <= _last_ack_sequence:
			_pending_commands.erase(sequence)


func _apply_local_prediction(command: Dictionary) -> void:
	for entity_id in _render_entities.keys():
		var entity := Dictionary(_render_entities[entity_id])
		if str(entity.get("entity_type", "")) != "tank" or int(entity.get("owner_player", 0)) != 1:
			continue
		var render_position := Vector2(entity.get("render_position", _entity_position(entity)))
		if bool(command.get("move_left", false)):
			render_position.x -= PREDICTION_MOVE_STEP
		if bool(command.get("move_right", false)):
			render_position.x += PREDICTION_MOVE_STEP
		if bool(command.get("aim_left", false)):
			entity["angle"] = float(entity.get("angle", 0.0)) + PREDICTION_ANGLE_STEP
		if bool(command.get("aim_right", false)):
			entity["angle"] = float(entity.get("angle", 0.0)) - PREDICTION_ANGLE_STEP
		entity["render_position"] = render_position
		entity["target_position"] = render_position
		_render_entities[entity_id] = entity
		return


func _update_interpolation(delta: float) -> void:
	for entity_id in _render_entities.keys():
		var entity := Dictionary(_render_entities[entity_id])
		var current_position := Vector2(entity.get("render_position", Vector2.ZERO))
		var target_position := Vector2(entity.get("target_position", current_position))
		entity["render_position"] = current_position.lerp(target_position, min(1.0, delta * 12.0))
		_render_entities[entity_id] = entity


func _ingest_events() -> void:
	for raw_event in Array(_snapshot.get("events", [])):
		if typeof(raw_event) != TYPE_DICTIONARY:
			continue
		var event := Dictionary(raw_event)
		if str(event.get("event_type", "")) != "terrain_explosion":
			continue
		var payload := Dictionary(event.get("payload", {}))
		var raw_position: Variant = payload.get("position", [0.0, 0.0])
		var position := Vector2.ZERO
		if typeof(raw_position) == TYPE_ARRAY and raw_position.size() >= 2:
			position = Vector2(float(raw_position[0]), float(raw_position[1]))
		_effects.append({"position": position, "radius": 8.0, "life": 0.45})


func _update_effects(delta: float) -> void:
	for effect in _effects:
		effect["life"] = float(effect.get("life", 0.0)) - delta
		effect["radius"] = float(effect.get("radius", 0.0)) + 90.0 * delta
	_effects = _effects.filter(func(effect: Dictionary) -> bool: return float(effect.get("life", 0.0)) > 0.0)


func _world_to_screen(world_position: Vector2, world_rect: Rect2) -> Vector2:
	var world_width: float = max(0.001, float(_match_snapshot.get("world_width", 20.0)))
	var x_ratio: float = (world_position.x + world_width * 0.5) / world_width
	var y_ratio: float = inverse_lerp(5.0, -8.0, world_position.y)
	return Vector2(
		lerpf(world_rect.position.x + 20.0, world_rect.end.x - 20.0, x_ratio),
		lerpf(world_rect.position.y + 40.0, world_rect.end.y - 24.0, y_ratio)
	)
