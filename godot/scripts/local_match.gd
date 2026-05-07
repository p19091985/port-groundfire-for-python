extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const LocalMatchHud := preload("res://scripts/local_match_hud.gd")
const LocalMatchShop := preload("res://scripts/local_match_shop.gd")
const TankState := preload("res://scripts/tank_state.gd")
const TerrainModel := preload("res://scripts/terrain_model.gd")
const WeaponInventory := preload("res://scripts/weapon_inventory.gd")

const OPTIONS_PATH := "user://groundfire_options.cfg"
const PHASE_AIM := "aim"
const PHASE_PROJECTILE := "projectile"
const PHASE_ROUND_OVER := "round_over"
const PHASE_SHOP := "shop"
const TURN_PLAYER := "Player"
const TURN_ENEMY := "Enemy"

var _hud: Node
var _terrain := TerrainModel.new()
var _terrain_size := Vector2.ZERO
var _terrain_seed := 1401
var _world_size := Vector2(1280.0, 768.0)
var _camera_offset := Vector2.ZERO
var _camera_zoom := 1.0
var _camera_ready := false
var _camera_shake := 0.0
var _camera_shake_offset := Vector2.ZERO
var _camera_shake_rng := RandomNumberGenerator.new()
var _screen_shake_enabled := true
var _camera_smoothing := 1.0
var _mouse_aim_enabled := true
var _mouse_world_position := Vector2.ZERO
var _player := TankState.new()
var _enemy := TankState.new()
var _inventory := WeaponInventory.new()
var _enemy_inventory := WeaponInventory.new()
var _round := 1
var _phase := PHASE_AIM
var _turn_owner := TURN_PLAYER
var _wind := -6.0
var _score := 0
var _credits := 0
var _player_wins := 0
var _enemy_wins := 0
var _message := "Aim with arrows, move with A/D, weapon with Tab, fire with Space."
var _projectiles: Array[Dictionary] = []
var _explosions: Array[Dictionary] = []
var _ai_timer := 0.0
var _last_shot_player_owned := true
var _pause_overlay: Control
var _resume_button: Button
var _is_paused := false
var _shop_overlay: Control
var _shop_title := ""
var _shop_reward := 0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	_camera_shake_rng.seed = 4319
	_load_gameplay_options()
	_ensure_input_actions()
	_rebuild_terrain_if_needed(true)
	_hud = LocalMatchHud.new()
	_hud.anchor_right = 1.0
	_hud.anchor_bottom = 1.0
	add_child(_hud)
	_build_pause_overlay()
	_build_shop_overlay()
	set_process(true)
	_update_hud()


func _process(delta: float) -> void:
	_rebuild_terrain_if_needed()
	if _is_paused:
		queue_redraw()
		return
	if _mouse_aim_enabled and _phase == PHASE_AIM and _turn_owner == TURN_PLAYER:
		_mouse_world_position = _screen_to_world(get_local_mouse_position())
	if _phase == PHASE_AIM and _turn_owner == TURN_PLAYER:
		_handle_player_input(delta)
	elif _phase == PHASE_ROUND_OVER:
		_ai_timer -= delta
		if _ai_timer <= 0.0:
			_start_next_turn_or_round()
	_update_projectiles(delta)
	_update_explosions(delta)
	_terrain.update(delta)
	_player.settle_on_terrain(_terrain, delta)
	_enemy.settle_on_terrain(_terrain, delta)
	_update_camera(delta)
	_update_hud()
	queue_redraw()


func _ensure_input_actions() -> void:
	_ensure_key_action("gf_aim_left", KEY_LEFT)
	_ensure_key_action("gf_aim_right", KEY_RIGHT)
	_ensure_key_action("gf_power_up", KEY_W)
	_ensure_key_action("gf_power_down", KEY_S)
	_ensure_key_action("gf_fire", KEY_SPACE)
	_ensure_key_action("gf_weapon_next", KEY_TAB)
	_ensure_key_action("gf_pause", KEY_ESCAPE)
	_ensure_key_action("gf_move_left", KEY_A)
	_ensure_key_action("gf_move_right", KEY_D)
	_ensure_key_action("gf_weapon_prev", KEY_Q)
	_ensure_key_action("gf_jump", KEY_SHIFT)


func _ensure_key_action(action_name: String, keycode: Key) -> void:
	if not InputMap.has_action(action_name):
		InputMap.add_action(action_name)
	if not InputMap.action_get_events(action_name).is_empty():
		return
	var event := InputEventKey.new()
	event.keycode = keycode
	InputMap.action_add_event(action_name, event)


func _handle_player_input(delta: float) -> void:
	var aim_direction := 0.0
	var power_direction := 0.0
	if Input.is_action_pressed("gf_aim_left"):
		aim_direction += 1.0
	if Input.is_action_pressed("gf_aim_right"):
		aim_direction -= 1.0
	if Input.is_action_pressed("gf_power_up"):
		power_direction += 1.0
	if Input.is_action_pressed("gf_power_down"):
		power_direction -= 1.0
	_player.update_gun(delta, aim_direction, power_direction)
	if Input.is_action_pressed("gf_move_left"):
		_player.move_on_terrain(-1.0, delta, _terrain)
	if Input.is_action_pressed("gf_move_right"):
		_player.move_on_terrain(1.0, delta, _terrain)
	if Input.is_action_pressed("gf_jump"):
		_player.boost(delta)


func _unhandled_input(event: InputEvent) -> void:
	if _phase == PHASE_SHOP:
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("ui_cancel") or event.is_action_pressed("gf_pause"):
		_set_paused(not _is_paused)
		get_viewport().set_input_as_handled()
		return
	if _is_paused:
		return
	if event.is_action_pressed("ui_accept"):
		_fire_player()
	elif _mouse_aim_enabled and event is InputEventMouseMotion and _phase == PHASE_AIM and _turn_owner == TURN_PLAYER:
		_mouse_world_position = _screen_to_world(get_local_mouse_position())
		_player.aim_at(_mouse_world_position)
	elif _mouse_aim_enabled \
			and event is InputEventMouseButton \
			and event.button_index == MOUSE_BUTTON_LEFT \
			and event.pressed \
			and _phase == PHASE_AIM \
			and _turn_owner == TURN_PLAYER:
		_mouse_world_position = _screen_to_world(event.position)
		_player.aim_at(_mouse_world_position)
		_fire_player()
	elif event.is_action_pressed("gf_weapon_prev"):
		_cycle_weapon(-1)
	elif event.is_action_pressed("gf_weapon_next"):
		_cycle_weapon(1)
	elif event.is_action_pressed("gf_fire"):
		_fire_player()


func _build_pause_overlay() -> void:
	var backdrop := PanelContainer.new()
	backdrop.name = "PauseOverlay"
	backdrop.anchor_right = 1.0
	backdrop.anchor_bottom = 1.0
	backdrop.visible = false
	backdrop.mouse_filter = Control.MOUSE_FILTER_STOP
	backdrop.add_theme_stylebox_override("panel", GroundfireTheme.modal_backdrop_style())
	add_child(backdrop)
	_pause_overlay = backdrop

	var center := CenterContainer.new()
	center.anchor_right = 1.0
	center.anchor_bottom = 1.0
	backdrop.add_child(center)

	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(360.0, 282.0)
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style())
	center.add_child(panel)

	var menu := VBoxContainer.new()
	menu.add_theme_constant_override("separation", 10)
	panel.add_child(menu)

	var title := Label.new()
	title.text = "Paused"
	GroundfireTheme.apply_label(title, 28, GroundfireTheme.COLOR_TEXT)
	menu.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Local match is paused."
	GroundfireTheme.apply_label(subtitle, 15, GroundfireTheme.COLOR_CYAN)
	menu.add_child(subtitle)

	var pause_buttons: Array[Button] = []
	_resume_button = _pause_button("Resume", _set_paused.bind(false), true)
	menu.add_child(_resume_button)
	pause_buttons.append(_resume_button)
	var options_button := _pause_button("Options", _open_options_from_pause)
	menu.add_child(options_button)
	pause_buttons.append(options_button)
	var restart_button := _pause_button("Restart Round", _restart_round)
	menu.add_child(restart_button)
	pause_buttons.append(restart_button)
	var main_menu_button := _pause_button("Main Menu", _return_to_main_menu)
	menu.add_child(main_menu_button)
	pause_buttons.append(main_menu_button)
	_wire_vertical_focus(pause_buttons)


func _build_shop_overlay() -> void:
	_shop_overlay = LocalMatchShop.new()
	_shop_overlay.visible = false
	_shop_overlay.continue_requested.connect(_continue_from_shop)
	_shop_overlay.buy_requested.connect(_buy_shop_weapon)
	add_child(_shop_overlay)


func _pause_button(text: String, callback: Callable, accent := false) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(300.0, 42.0)
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(button, accent)
	button.pressed.connect(callback)
	return button


func _set_paused(value: bool) -> void:
	_is_paused = value
	if _pause_overlay != null:
		_pause_overlay.visible = value
	if value and _resume_button != null:
		_resume_button.grab_focus.call_deferred()
	if not value:
		_load_gameplay_options()
	_message = "Paused." if value else "Match resumed."
	_update_hud()


func _restart_round() -> void:
	_set_paused(false)
	_hide_shop_overlay()
	_projectiles.clear()
	_explosions.clear()
	_ai_timer = 0.0
	_phase = PHASE_AIM
	_turn_owner = TURN_PLAYER
	_inventory.reset_round_ammo()
	_enemy_inventory.reset_round_ammo()
	_rebuild_terrain_if_needed(true)
	_message = "Round restarted."
	_update_hud()


func _return_to_main_menu() -> void:
	_set_paused(false)
	get_parent().get_parent()._show_main_menu()


func _open_options_from_pause() -> void:
	_set_paused(false)
	get_parent().get_parent()._show_options()


func _fire_player() -> void:
	if _phase != PHASE_AIM or _turn_owner != TURN_PLAYER or not _projectiles.is_empty():
		return
	if not _inventory.consume_current():
		_message = "No ammo for %s." % _inventory.current_name()
		return
	_fire_weapon(_player.launch_origin(), _player.gun_angle, _player.gun_power, true, _inventory.current())
	_phase = PHASE_PROJECTILE
	_message = "%s fired." % _inventory.current_name()


func _fire_ai() -> void:
	_turn_owner = TURN_ENEMY
	var shot := _choose_ai_shot()
	var weapon := _choose_ai_weapon(shot)
	if str(weapon.get("kind", "shell")) == "missile" or str(weapon.get("kind", "shell")) == "machine_gun":
		shot = _direct_ai_shot(weapon, shot)
	_enemy.gun_angle = float(shot["angle"])
	_enemy.gun_power = float(shot["power"])
	_enemy_inventory.select_by_name(str(weapon.get("name", WeaponInventory.SHELL)))
	_enemy_inventory.consume_current()
	_fire_weapon(_enemy.launch_origin(), _enemy.gun_angle, _enemy.gun_power, false, weapon)
	_phase = PHASE_PROJECTILE
	_message = "Enemy fires %s." % str(weapon.get("name", "Shell"))


func _choose_ai_shot() -> Dictionary:
	var shell := WeaponInventory.WEAPONS[0]
	var origin := _enemy.launch_origin()
	var target := _player.position + Vector2(0.0, -20.0)
	var best_angle := 135.0
	var best_power := 55.0
	var best_miss := INF
	for angle in range(100, 171, 5):
		for power in range(32, 91, 4):
			var miss := _simulate_ai_shell_miss(origin, float(angle), float(power), target, shell)
			if miss < best_miss:
				best_miss = miss
				best_angle = float(angle)
				best_power = float(power)
	return {
		"angle": clamp(best_angle + randf_range(-2.0, 2.0), 95.0, 175.0),
		"power": clamp(best_power + randf_range(-3.0, 3.0), 28.0, 95.0),
		"miss": best_miss,
	}


func _simulate_ai_shell_miss(origin: Vector2, angle_degrees: float, power: float, target: Vector2, weapon: Dictionary) -> float:
	var radians := deg_to_rad(angle_degrees)
	var velocity := Vector2(cos(radians), -sin(radians)) * power * float(weapon.get("speed", 4.2))
	var position := origin
	var closest := origin.distance_to(target)
	var step := 1.0 / 30.0
	for _index in range(120):
		var previous_position := position
		velocity.x += _wind * step
		velocity.y += 190.0 * step
		position += velocity * step
		closest = min(closest, _distance_to_segment(target, previous_position, position))
		if _terrain_hits_segment(previous_position, position) or position.x < 0.0 or position.x > _world_size.x:
			break
	return closest


func _choose_ai_weapon(shot: Dictionary) -> Dictionary:
	var shell: Dictionary = _enemy_inventory.weapon_by_name(WeaponInventory.SHELL)
	var distance: float = abs(_enemy.position.x - _player.position.x)
	var miss := float(shot.get("miss", INF))
	var direct_line: bool = _has_direct_line_to_player()
	if _enemy_inventory.has_ammo(WeaponInventory.NUKE) and (_player.health <= 55 or (distance > 360.0 and miss < 46.0)):
		return _enemy_inventory.weapon_by_name(WeaponInventory.NUKE)
	if direct_line and distance < 320.0 and _enemy_inventory.has_ammo(WeaponInventory.MACHINE_GUN):
		return _enemy_inventory.weapon_by_name(WeaponInventory.MACHINE_GUN)
	if distance > 460.0 and _enemy_inventory.has_ammo(WeaponInventory.MIRV):
		return _enemy_inventory.weapon_by_name(WeaponInventory.MIRV)
	if _enemy_inventory.has_ammo(WeaponInventory.MISSILE) and (direct_line or miss > 72.0):
		return _enemy_inventory.weapon_by_name(WeaponInventory.MISSILE)
	return shell


func _direct_ai_shot(weapon: Dictionary, fallback: Dictionary) -> Dictionary:
	var origin := _enemy.launch_origin()
	var target := _player.position + Vector2(0.0, -20.0)
	var direction := target - origin
	if direction.length_squared() <= 1.0:
		return fallback
	var angle: float = clamp(rad_to_deg(atan2(-direction.y, direction.x)), 95.0, 175.0)
	var speed_multiplier: float = max(0.1, float(weapon.get("speed", 4.2)))
	var power: float = clamp(direction.length() / speed_multiplier * 0.18, 34.0, 95.0)
	return {"angle": angle, "power": power, "miss": fallback.get("miss", INF)}


func _has_direct_line_to_player() -> bool:
	var origin := _enemy.launch_origin()
	var target := _player.position + Vector2(0.0, -20.0)
	return not bool(_terrain_collision(origin, target)["hit"])


func _fire_weapon(origin: Vector2, angle_degrees: float, power: float, player_owned: bool, weapon: Dictionary) -> void:
	var kind := str(weapon.get("kind", "shell"))
	if kind == "machine_gun":
		for index in range(5):
			_fire_from(origin, angle_degrees + randf_range(-3.5, 3.5), power + float(index) * 1.4, player_owned, weapon)
		return
	_fire_from(origin, angle_degrees, power, player_owned, weapon)


func _fire_from(origin: Vector2, angle_degrees: float, power: float, player_owned: bool, weapon: Dictionary) -> void:
	var radians := deg_to_rad(angle_degrees)
	var speed_multiplier := float(weapon.get("speed", 4.2))
	var velocity := Vector2(cos(radians), -sin(radians)) * power * speed_multiplier
	var kind := str(weapon.get("kind", "shell"))
	_last_shot_player_owned = player_owned
	_projectiles.append({
		"position": origin,
		"previous_position": origin,
		"velocity": velocity,
		"player_owned": player_owned,
		"weapon": weapon,
		"kind": kind,
		"age": 0.0,
		"split": false,
	})


func _update_projectiles(delta: float) -> void:
	for projectile in _projectiles:
		var previous_position := Vector2(projectile["position"])
		var velocity: Vector2 = projectile["velocity"]
		var kind := str(projectile.get("kind", "shell"))
		projectile["age"] = float(projectile.get("age", 0.0)) + delta
		if kind == "missile":
			var target_position: Vector2 = _enemy.position if bool(projectile["player_owned"]) else _player.position
			var desired: Vector2 = (target_position + Vector2(0.0, -20.0) - previous_position).normalized() * velocity.length()
			velocity = velocity.lerp(desired, 0.75 * delta)
		if kind == "mirv" and not bool(projectile.get("split", false)) and float(projectile["age"]) > 0.8:
			projectile["split"] = true
			_spawn_mirv_children(previous_position, velocity, bool(projectile["player_owned"]), Dictionary(projectile["weapon"]))
		velocity.x += _wind * delta
		velocity.y += 190.0 * delta
		var position := previous_position + velocity * delta
		projectile["previous_position"] = previous_position
		projectile["velocity"] = velocity
		projectile["position"] = position
		if _segment_hits_tank(previous_position, position, _enemy.position) \
				or _segment_hits_tank(previous_position, position, _player.position):
			_apply_explosion(position, projectile)
			return
		var terrain_collision := _terrain_collision(previous_position, position)
		if bool(terrain_collision["hit"]):
			_apply_explosion(Vector2(terrain_collision["position"]), projectile)
			return
		if position.x < 0.0 or position.x > _world_size.x:
			_apply_explosion(Vector2(clamp(position.x, 0.0, _world_size.x), min(position.y, _terrain.height_at(position.x))), projectile)
			return


func _spawn_mirv_children(origin: Vector2, velocity: Vector2, player_owned: bool, weapon: Dictionary) -> void:
	for offset in [-0.45, 0.0, 0.45]:
		var child_weapon := weapon.duplicate()
		child_weapon["kind"] = "shell"
		child_weapon["name"] = "MIRV Fragment"
		var child_velocity: Vector2 = velocity.rotated(offset) * 0.72
		_projectiles.append({
			"position": origin,
			"previous_position": origin,
			"velocity": child_velocity,
			"player_owned": player_owned,
			"weapon": child_weapon,
			"kind": "shell",
			"age": 0.0,
			"split": true,
		})


func _segment_hits_tank(start: Vector2, end: Vector2, tank_position: Vector2) -> bool:
	return _distance_to_segment(tank_position + Vector2(0.0, -18.0), start, end) < 34.0


func _distance_to_segment(point: Vector2, start: Vector2, end: Vector2) -> float:
	var segment: Vector2 = end - start
	var length_squared: float = segment.length_squared()
	if length_squared <= 0.0:
		return start.distance_to(point)
	var t: float = clamp((point - start).dot(segment) / length_squared, 0.0, 1.0)
	var closest: Vector2 = start + segment * t
	return closest.distance_to(point)


func _terrain_hits_segment(start: Vector2, end: Vector2) -> bool:
	return bool(_terrain_collision(start, end)["hit"])


func _terrain_collision(start: Vector2, end: Vector2) -> Dictionary:
	if _terrain.has_method("ground_collision"):
		return _terrain.ground_collision(start, end)
	var steps: int = max(2, int(start.distance_to(end) / 8.0))
	for index in range(steps + 1):
		var t: float = float(index) / float(steps)
		var point: Vector2 = start.lerp(end, t)
		if point.y >= _terrain.height_at(point.x):
			return {"hit": true, "position": point, "distance": start.distance_to(point)}
	return {"hit": false, "position": Vector2.ZERO, "distance": INF}


func _apply_explosion(position: Vector2, projectile: Dictionary) -> void:
	var weapon: Dictionary = projectile["weapon"]
	var damage := int(weapon.get("damage", 40))
	var blast_radius := float(weapon.get("blast", 48.0))
	_spawn_explosion(position, blast_radius)
	var enemy_damage := _splash_damage(position, _enemy.position + Vector2(0.0, -20.0), damage, blast_radius)
	var player_damage := _splash_damage(position, _player.position + Vector2(0.0, -20.0), damage, blast_radius)
	if enemy_damage > 0:
		_enemy.apply_damage(enemy_damage)
		_score += enemy_damage
		_credits += enemy_damage
	if player_damage > 0:
		_player.apply_damage(player_damage)
	if bool(projectile["player_owned"]):
		_message = "%s dealt %d enemy damage." % [str(weapon.get("name", "Shell")), enemy_damage]
	else:
		_message = "Enemy dealt %d player damage." % player_damage
	_projectiles.clear()
	_after_explosion()


func _after_explosion() -> void:
	if _enemy.health <= 0:
		_player_wins += 1
		_open_post_round_shop("Round Won", 100)
	elif _player.health <= 0:
		_enemy_wins += 1
		_open_post_round_shop("Round Lost", 0)
	elif _last_shot_player_owned:
		_phase = PHASE_ROUND_OVER
		_ai_timer = 0.75
	else:
		_turn_owner = TURN_PLAYER
		_phase = PHASE_AIM


func _start_next_turn_or_round() -> void:
	if _last_shot_player_owned:
		_fire_ai()


func _open_post_round_shop(title: String, reward: int) -> void:
	_shop_title = title
	_shop_reward = reward
	_credits += reward
	_phase = PHASE_SHOP
	_ai_timer = 0.0
	_message = "%s. Spend credits or continue." % title
	_refresh_shop_overlay()


func _refresh_shop_overlay() -> void:
	if _shop_overlay == null:
		return
	_shop_overlay.visible = true
	_shop_overlay.refresh({
		"title": _shop_title,
		"round": _round,
		"score": _score,
		"reward": _shop_reward,
		"credits": _credits,
		"inventory": _inventory.inventory_snapshot(),
		"message": _message,
	})
	_update_hud()


func _hide_shop_overlay() -> void:
	if _shop_overlay != null:
		_shop_overlay.visible = false
	_shop_title = ""
	_shop_reward = 0


func _buy_shop_weapon(weapon_name: String) -> void:
	var cost := _inventory.weapon_cost(weapon_name)
	if cost <= 0:
		_message = "%s is already stocked." % weapon_name
		_refresh_shop_overlay()
		return
	if _credits < cost:
		_message = "Need %d credits for %s." % [cost, weapon_name]
		_refresh_shop_overlay()
		return
	_credits -= cost
	var ammo_count := _inventory.add_ammo(weapon_name)
	_message = "Bought %s ammo. Ammo now %s." % [weapon_name, str(ammo_count)]
	_refresh_shop_overlay()


func _continue_from_shop() -> void:
	_hide_shop_overlay()
	_round += 1
	_wind = randf_range(-9.0, 9.0)
	_terrain_seed += 17
	_projectiles.clear()
	_explosions.clear()
	_enemy_inventory.reset_round_ammo()
	_rebuild_terrain_if_needed(true)
	_turn_owner = TURN_PLAYER
	_phase = PHASE_AIM
	_message = "Round %d ready." % _round
	_update_hud()


func _spawn_explosion(position: Vector2, crater_radius: float) -> void:
	_terrain.apply_crater(position, crater_radius)
	_player.settle_on_terrain(_terrain)
	_enemy.settle_on_terrain(_terrain)
	_add_camera_shake(crater_radius)
	_explosions.append({"position": position, "radius": 8.0, "life": 0.55, "crater_radius": crater_radius})


func _update_explosions(delta: float) -> void:
	for explosion in _explosions:
		explosion["life"] = float(explosion["life"]) - delta
		explosion["radius"] = float(explosion["radius"]) + 120.0 * delta
	_explosions = _explosions.filter(func(explosion: Dictionary) -> bool: return float(explosion["life"]) > 0.0)


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), GroundfireTheme.COLOR_BG)
	var camera_offset := _camera_offset + _camera_shake_offset
	draw_set_transform(-camera_offset * _camera_zoom, 0.0, Vector2(_camera_zoom, _camera_zoom))
	_draw_terrain()
	_draw_tank(_player)
	_draw_tank(_enemy)
	_draw_aim()
	_draw_mouse_reticle()
	for projectile in _projectiles:
		draw_circle(Vector2(projectile["position"]), 5.0, GroundfireTheme.COLOR_WARN)
	for explosion in _explosions:
		draw_circle(Vector2(explosion["position"]), float(explosion["radius"]), Color("#f59e0b66"))
	_draw_map_bounds()
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	if _phase == PHASE_ROUND_OVER and (_enemy.health <= 0 or _player.health <= 0):
		_draw_round_banner()


func _draw_terrain() -> void:
	var chunk_polygons: Array = _terrain.chunk_polygons()
	if chunk_polygons.is_empty():
		var points := _terrain.polygon_points()
		draw_colored_polygon(points, Color("#244326"))
		for index in range(1, points.size() - 2):
			draw_line(points[index], points[index + 1], Color("#6fbf73"), 2.0)
		return
	for chunk in chunk_polygons:
		var color: Color = chunk.get("fill_color", chunk["bottom_color"])
		if bool(chunk.get("falling", false)):
			color = color.lerp(GroundfireTheme.COLOR_WARN, 0.22)
		draw_colored_polygon(chunk["points"], color)
		var points: PackedVector2Array = chunk["points"]
		draw_line(points[1], points[2], chunk["top_color"], 2.0)


func _draw_map_bounds() -> void:
	draw_rect(Rect2(Vector2.ZERO, _world_size), Color("#80d8ff22"), false, 2.0)


func _draw_tank(tank: RefCounted) -> void:
	var position: Vector2 = tank.position
	var body_points := PackedVector2Array([
		_transform_tank_point(Vector2(-26.0, 0.0), tank),
		_transform_tank_point(Vector2(-13.0, -22.0), tank),
		_transform_tank_point(Vector2(13.0, -22.0), tank),
		_transform_tank_point(Vector2(26.0, 0.0), tank),
	])
	draw_colored_polygon(body_points, tank.body_color)
	draw_circle(position + Vector2(-15.0, 2.0), 7.0, Color("#111f2b"))
	draw_circle(position + Vector2(15.0, 2.0), 7.0, Color("#111f2b"))
	var hp_width := 52.0 * float(tank.health) / 100.0
	draw_rect(Rect2(position.x - 26.0, position.y - 42.0, hp_width, 5.0), Color("#56d364"))
	draw_rect(Rect2(position.x - 26.0, position.y - 34.0, 52.0 * float(tank.fuel), 4.0), Color("#7dd3fc"))


func _transform_tank_point(local: Vector2, tank: RefCounted) -> Vector2:
	var radians := deg_to_rad(tank.tank_angle)
	return tank.position + Vector2(
		local.x * cos(radians) - local.y * sin(radians),
		local.x * sin(radians) + local.y * cos(radians)
	)


func _draw_aim() -> void:
	if _turn_owner != TURN_PLAYER or _phase != PHASE_AIM:
		return
	var start := _player.launch_origin()
	var radians := deg_to_rad(_player.gun_angle)
	var end := start + Vector2(cos(radians), -sin(radians)) * (48.0 + _player.gun_power * 0.75)
	draw_line(start, end, GroundfireTheme.COLOR_WARN, 4.0)


func _draw_mouse_reticle() -> void:
	if not _mouse_aim_enabled or _turn_owner != TURN_PLAYER or _phase != PHASE_AIM:
		return
	var target := _mouse_world_position
	if target == Vector2.ZERO:
		target = _screen_to_world(get_local_mouse_position())
	draw_circle(target, 9.0, Color("#7dd3fc44"))
	draw_line(target + Vector2(-13.0, 0.0), target + Vector2(-4.0, 0.0), GroundfireTheme.COLOR_CYAN, 2.0)
	draw_line(target + Vector2(4.0, 0.0), target + Vector2(13.0, 0.0), GroundfireTheme.COLOR_CYAN, 2.0)
	draw_line(target + Vector2(0.0, -13.0), target + Vector2(0.0, -4.0), GroundfireTheme.COLOR_CYAN, 2.0)
	draw_line(target + Vector2(0.0, 4.0), target + Vector2(0.0, 13.0), GroundfireTheme.COLOR_CYAN, 2.0)


func _draw_round_banner() -> void:
	var panel := Rect2(size.x * 0.5 - 190.0, size.y * 0.5 - 44.0, 380.0, 88.0)
	draw_rect(panel, Color("#0b1722dd"))
	draw_rect(panel, GroundfireTheme.COLOR_LINE, false, 2.0)
	draw_string(ThemeDB.fallback_font, panel.position + Vector2(24.0, 52.0), _message, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, GroundfireTheme.COLOR_TEXT)


func _update_hud() -> void:
	if _hud == null:
		return
	_hud.set_snapshot({
		"round": _round,
		"phase": _phase,
		"turn": _turn_owner,
		"player_name": _player.name,
		"enemy_name": _enemy.name,
		"player_hp": _player.health,
		"enemy_hp": _enemy.health,
		"player_fuel": int(_player.fuel * 100.0),
		"angle": int(_player.gun_angle),
		"power": int(_player.gun_power),
		"wind": int(_wind),
		"weapon": _inventory.current_name(),
		"ammo": _inventory.current_ammo(),
		"inventory": _inventory.inventory_snapshot(),
		"score": _score,
		"credits": _credits,
		"player_wins": _player_wins,
		"enemy_wins": _enemy_wins,
		"message": _message,
	})


func _cycle_weapon(direction := 1) -> void:
	if _phase != PHASE_AIM or _turn_owner != TURN_PLAYER:
		return
	_message = "Weapon selected: %s." % _inventory.cycle(direction)


func _splash_damage(explosion_position: Vector2, target_position: Vector2, max_damage: int, radius: float) -> int:
	var distance := explosion_position.distance_to(target_position)
	if distance > radius:
		return 0
	return int(round(float(max_damage) * (1.0 - distance / radius)))


func _update_camera(delta: float) -> void:
	if size.x <= 0.0 or size.y <= 0.0:
		return
	_update_camera_shake(delta)
	var subjects := _camera_subjects()
	if subjects.is_empty():
		return
	var bounds := _bounds_for_subjects(subjects).grow_individual(180.0, 160.0, 180.0, 120.0)
	var target_zoom: float = min(size.x / max(bounds.size.x, 1.0), size.y / max(bounds.size.y, 1.0))
	target_zoom = clamp(target_zoom, 0.58, 1.12)
	var target_offset := bounds.get_center() - (size / target_zoom) * 0.5
	target_offset = _constrain_camera_offset(target_offset, target_zoom)
	if not _camera_ready:
		_camera_offset = target_offset
		_camera_zoom = target_zoom
		_camera_ready = true
		return
	var smoothing: float = min(1.0, delta * 4.8 * _camera_smoothing)
	_camera_offset = _camera_offset.lerp(target_offset, smoothing)
	_camera_zoom = lerpf(_camera_zoom, target_zoom, smoothing)


func _camera_subjects() -> Array[Vector2]:
	var subjects: Array[Vector2] = [_player.position, _enemy.position]
	for projectile in _projectiles:
		var projectile_position := Vector2(projectile["position"])
		var projectile_velocity := Vector2(projectile["velocity"])
		subjects.append(projectile_position)
		if projectile_velocity.length_squared() > 1.0:
			subjects.append(projectile_position + projectile_velocity.normalized() * min(220.0, projectile_velocity.length() * 0.35))
	for explosion in _explosions:
		subjects.append(Vector2(explosion["position"]))
	return subjects


func _bounds_for_subjects(subjects: Array[Vector2]) -> Rect2:
	var min_point := subjects[0]
	var max_point := subjects[0]
	for point in subjects:
		min_point.x = min(min_point.x, point.x)
		min_point.y = min(min_point.y, point.y)
		max_point.x = max(max_point.x, point.x)
		max_point.y = max(max_point.y, point.y)
	min_point = Vector2(clamp(min_point.x, 0.0, _world_size.x), clamp(min_point.y, 0.0, _world_size.y))
	max_point = Vector2(clamp(max_point.x, 0.0, _world_size.x), clamp(max_point.y, 0.0, _world_size.y))
	return Rect2(min_point, max_point - min_point)


func _constrain_camera_offset(offset: Vector2, zoom: float) -> Vector2:
	var viewport_world := size / zoom
	var constrained := offset
	if viewport_world.x >= _world_size.x:
		constrained.x = (_world_size.x - viewport_world.x) * 0.5
	else:
		constrained.x = clamp(constrained.x, 0.0, _world_size.x - viewport_world.x)
	if viewport_world.y >= _world_size.y:
		constrained.y = (_world_size.y - viewport_world.y) * 0.5
	else:
		constrained.y = clamp(constrained.y, 0.0, _world_size.y - viewport_world.y)
	return constrained


func _screen_to_world(screen_position: Vector2) -> Vector2:
	return screen_position / _camera_zoom + _camera_offset + _camera_shake_offset


func _add_camera_shake(strength: float) -> void:
	if not _screen_shake_enabled:
		return
	_camera_shake = clamp(max(_camera_shake, strength * 0.22), 0.0, 24.0)


func _update_camera_shake(delta: float) -> void:
	if _camera_shake <= 0.01:
		_camera_shake = 0.0
		_camera_shake_offset = Vector2.ZERO
		return
	_camera_shake = max(0.0, _camera_shake - 42.0 * delta)
	_camera_shake_offset = Vector2(
		_camera_shake_rng.randf_range(-_camera_shake, _camera_shake),
		_camera_shake_rng.randf_range(-_camera_shake, _camera_shake)
	)


func _target_world_size() -> Vector2:
	return Vector2(max(size.x, 1280.0), max(size.y, 720.0))


func _rebuild_terrain_if_needed(force := false) -> void:
	if size.x <= 0.0 or size.y <= 0.0:
		return
	_world_size = _target_world_size()
	if force or _terrain.is_empty() or _terrain_size != _world_size:
		_terrain_size = _world_size
		_terrain.rebuild_with_seed(_world_size.x, _world_size.y, _terrain_seed)
		_player.reset_round(_world_size.x * 0.22, _terrain, "Player", GroundfireTheme.COLOR_ACCENT_HOT)
		_enemy.reset_round(_world_size.x * 0.76, _terrain, "Enemy", Color("#4d95ff"))
		_camera_ready = false


func _load_gameplay_options() -> void:
	var config := ConfigFile.new()
	if config.load(OPTIONS_PATH) != OK:
		return
	_screen_shake_enabled = bool(config.get_value("gameplay", "screen_shake", _screen_shake_enabled))
	_camera_smoothing = clamp(float(config.get_value("gameplay", "camera_smoothing", _camera_smoothing)), 0.25, 1.75)
	_mouse_aim_enabled = bool(config.get_value("gameplay", "mouse_aim", _mouse_aim_enabled))


func _wire_vertical_focus(buttons: Array[Button]) -> void:
	if buttons.size() < 2:
		return
	for index in range(buttons.size()):
		var button := buttons[index]
		var previous := buttons[wrapi(index - 1, 0, buttons.size())]
		var next := buttons[wrapi(index + 1, 0, buttons.size())]
		button.focus_neighbor_top = previous.get_path()
		button.focus_neighbor_bottom = next.get_path()
