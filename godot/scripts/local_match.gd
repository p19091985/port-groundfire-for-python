extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const LocalMatchHud := preload("res://scripts/local_match_hud.gd")
const LocalMatchShop := preload("res://scripts/local_match_shop.gd")
const TankState := preload("res://scripts/tank_state.gd")
const TerrainModel := preload("res://scripts/terrain_model.gd")
const WeaponInventory := preload("res://scripts/weapon_inventory.gd")
const QUAKE_SOUND := preload("res://assets/quake.wav")
const JUMP_JETS_SOUND := preload("res://assets/jumpjets.wav")
const FIRE_SHELL_SOUND := preload("res://assets/fireshell.wav")
const SHELL_DEATH_SOUND := preload("res://assets/shelldeath.wav")
const LAUNCH_MISSILE_SOUND := preload("res://assets/launchmissile.wav")
const MISSILE_FLIGHT_SOUND := preload("res://assets/missile.wav")
const MISSILE_DEATH_SOUND := preload("res://assets/missiledeath.wav")
const MACHINE_GUN_SOUND := preload("res://assets/machinegun.wav")
const METAL_HIT_SOUND := preload("res://assets/metal.wav")
const NUKE_SOUND := preload("res://assets/nuke.wav")
const SMOKE_TEXTURE := preload("res://assets/smoke.png")
const MENU_TILE := preload("res://assets/menuback.png")

const OPTIONS_PATH := "user://groundfire_options.cfg"
const PHASE_AIM := "aim"
const PHASE_PROJECTILE := "projectile"
const PHASE_ROUND_OVER := "round_over"
const PHASE_SCORE := "score"
const PHASE_SHOP := "shop"
const PHASE_WINNER := "winner"
const TURN_PLAYER := "Player"
const TURN_ENEMY := "Enemy"
const AI_DIFFICULTY_EASY := "easy"
const AI_DIFFICULTY_NORMAL := "normal"
const AI_DIFFICULTY_HARD := "hard"
const PROJECTILE_GRAVITY := 190.0
const MIRV_MIN_SPLIT_AGE := 0.25
const MISSILE_ANGLE_CHANGE_LIMIT := 500.0
const MISSILE_RECENTER_MULTIPLIER := 3.0
const MISSILE_AI_STEER_ANGLE_SCALE := 18.0
const PROJECTILE_WORLD_MARGIN := 160.0
const SPLASH_OCCLUSION_MULTIPLIER := 0.45
const TANK_GUN_ARROW_START_OFFSET := TankState.TANK_BODY_HALF_WIDTH * 1.5
const TANK_GUN_ARROW_BASE_LENGTH := TankState.TANK_BODY_HALF_WIDTH * 2.0
const TANK_GUN_ARROW_POWER_SCALE := TankState.TANK_BODY_HALF_WIDTH * 0.5
const TANK_GUN_ARROW_HEAD_TIP_SCALE := 1.25
const TANK_GUN_ARROW_SHAFT_HALF_WIDTH := TankState.TANK_BODY_HALF_WIDTH * 0.4
const TANK_GUN_ARROW_HEAD_HALF_WIDTH := TankState.TANK_BODY_HALF_WIDTH * 0.8
const WIND_MIN := -9.0
const WIND_MAX := 9.0
const WIND_TURN_SHIFT := 3.0
const WIND_GUST_MAX := 2.0
const WIND_GUST_SCALE := 0.35
const WIND_GUST_FREQUENCY := 2.7
const QUAKE_DURATION := 5.0
const QUAKE_DROP_RATE := 7.0
const QUAKE_TIME_TILL_FIRST := 90.0
const QUAKE_TIME_BETWEEN := 30.0
const QUAKE_CAMERA_SHAKE := 14.0
const NUKE_WHITEOUT_FADE_RATE := 0.6
const SCORE_ROUND_WIN_REWARD := 100
const SCORE_DEFEAT_REWARD := 100
const SCORE_DEFEAT_LEADER_REWARD := 200
const SCORE_SELF_DEFEAT_PENALTY := -50
const SCORE_SURVIVAL_REWARD := 100
const CREDITS_DEFEAT_REWARD := 50
const CREDITS_SURVIVAL_REWARD := 25
const CREDITS_ROUND_STIPEND := 10
const MATCH_TOTAL_ROUNDS := 5
const SHOP_JUMP_JET := "Jump Jet"
const SHOP_JUMP_JET_COST := 50
const MACHINE_GUN_AI_EASY_BURST := 3
const MACHINE_GUN_AI_NORMAL_BURST := 5
const MACHINE_GUN_AI_HARD_BURST := 8
const MACHINE_GUN_AI_FINISHER_BURST := 10
const MACHINE_GUN_TRACER_TRAIL_TIME := 0.01
const AI_WEAPON_SCORE_THRESHOLD_EASY := 18.0
const AI_WEAPON_SCORE_THRESHOLD_NORMAL := 16.0
const AI_WEAPON_SCORE_THRESHOLD_HARD := 10.0
const AI_SELF_DAMAGE_WEIGHT_EASY := 1.45
const AI_SELF_DAMAGE_WEIGHT_NORMAL := 2.2
const AI_SELF_DAMAGE_WEIGHT_HARD := 3.0
const AI_KILL_BONUS := 35.0
const AI_SELF_KILL_PENALTY := 1000.0
const AI_SHOP_PRIORITY_EASY := ["Machine Gun", "Missile", "Jump Jet"]
const AI_SHOP_PRIORITY_NORMAL := ["Missile", "MIRV", "Machine Gun", "Jump Jet"]
const AI_SHOP_PRIORITY_HARD := ["Nuke", "MIRV", "Missile", "Machine Gun", "Jump Jet"]
const SCORE_HUMAN_ACTIVATION_DELAY := 2.0
const SCORE_COMPUTER_ACTIVATION_DELAY := 4.0
const WINNER_HUMAN_ACTIVATION_DELAY := 2.0
const WINNER_COMPUTER_ACTIVATION_DELAY := 4.0
const WINNER_SPIN_TEXT := "Winner!"
const WINNER_SPIN_SPEED := 4.0
const WINNER_SPIN_LETTER_SPACING := 0.2
const WINNER_SPIN_RADIUS := 24.0
const WINNER_BACKGROUND_SCROLL_SPEED := 0.1
const SHOP_INITIAL_INPUT_DELAY := 0.4
const SHOP_ACTION_INPUT_DELAY := 0.2

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
var _mouse_aim_enabled := false
var _ai_difficulty := AI_DIFFICULTY_NORMAL
var _mouse_world_position := Vector2.ZERO
var _player := TankState.new()
var _enemy := TankState.new()
var _player_name := TURN_PLAYER
var _enemy_name := TURN_ENEMY
var _configured_roster: Array[Dictionary] = []
var _participants: Array[Dictionary] = []
var _inventory := WeaponInventory.new()
var _enemy_inventory := WeaponInventory.new()
var _round := 1
var _total_rounds := MATCH_TOTAL_ROUNDS
var _requested_total_rounds := 0
var _phase := PHASE_AIM
var _turn_owner := TURN_PLAYER
var _turn_index := 0
var _target_index := 1
var _wind := -6.0
var _wind_gust := 0.0
var _wind_rng := RandomNumberGenerator.new()
var _quake_active := false
var _quake_countdown := QUAKE_TIME_TILL_FIRST
var _jump_jets_active := false
var _score := 0
var _enemy_score := 0
var _credits := 0
var _player_wins := 0
var _enemy_wins := 0
var _message := "Aim with arrows, move with A/D, weapon with Tab, fire with Space."
var _projectiles: Array[Dictionary] = []
var _explosions: Array[Dictionary] = []
var _smoke_particles: Array[Dictionary] = []
var _machine_gun_active := false
var _machine_gun_fire_held := false
var _machine_gun_player_owned := true
var _machine_gun_owner := TURN_PLAYER
var _machine_gun_weapon: Dictionary = {}
var _machine_gun_cooldown := 0.0
var _machine_gun_shots_fired := 0
var _machine_gun_ai_burst_remaining := 0
var _ai_timer := 0.0
var _last_shot_player_owned := true
var _last_shot_owner := TURN_PLAYER
var _round_defeats: Dictionary = {}
var _pause_overlay: Control
var _resume_button: Button
var _is_paused := false
var _shop_overlay: Control
var _score_overlay: Control
var _score_title_label: Label
var _score_summary_label: Label
var _score_reward_label: Label
var _score_rows_container: VBoxContainer
var _score_continue_button: Button
var _score_title := ""
var _score_reward := 0
var _score_round_winner := ""
var _score_defeated_name := ""
var _score_defeated_was_leader := false
var _score_round_details: Dictionary = {}
var _score_round_credits: Dictionary = {}
var _score_continue_delay := 0.0
var _shop_title := ""
var _shop_reward := 0
var _shop_participant_indices: Array[int] = []
var _shop_participant_cursor := 0
var _shop_input_delay := 0.0
var _winner_overlay: Control
var _winner_heading_label: Label
var _winner_title_label: Label
var _winner_summary_label: Label
var _winner_cards_container: VBoxContainer
var _winner_rows_container: VBoxContainer
var _winner_main_menu_button: Button
var _winner_background: TextureRect
var _winner_continue_delay := 0.0
var _winner_spin_phase := 0.0
var _winner_background_scroll := 0.0
var _quake_audio: AudioStreamPlayer
var _jump_jets_audio: AudioStreamPlayer
var _fire_shell_audio: AudioStreamPlayer
var _shell_death_audio: AudioStreamPlayer
var _launch_missile_audio: AudioStreamPlayer
var _missile_flight_audio: AudioStreamPlayer
var _missile_death_audio: AudioStreamPlayer
var _machine_gun_audio: AudioStreamPlayer
var _metal_hit_audio: AudioStreamPlayer
var _nuke_audio: AudioStreamPlayer
var _shutting_down := false


func setup(config: Dictionary) -> void:
	_requested_total_rounds = max(1, int(config.get("total_rounds", MATCH_TOTAL_ROUNDS)))
	_configured_roster.clear()
	for entry in Array(config.get("roster", [])):
		_configured_roster.append(Dictionary(entry).duplicate(true))
	_player_name = _setup_name_or_default(str(config.get("player_name", TURN_PLAYER)), TURN_PLAYER)
	_enemy_name = _setup_name_or_default(str(config.get("enemy_name", TURN_ENEMY)), TURN_ENEMY)
	_build_participants_from_roster()


func _setup_name_or_default(text: String, fallback: String) -> String:
	var cleaned := text.strip_edges()
	if cleaned.is_empty():
		return fallback
	return cleaned.left(18)


func _build_participants_from_roster() -> void:
	var roster := _normalized_roster_for_participants()
	_participants.clear()
	for index in range(roster.size()):
		var entry: Dictionary = roster[index]
		var participant := {
			"slot": int(entry.get("slot", index)),
			"name": _setup_name_or_default(str(entry.get("name", _default_participant_name(index))), _default_participant_name(index)),
			"kind": str(entry.get("kind", "computer")),
			"controller": int(entry.get("controller", -1)),
			"color": entry.get("color", _default_participant_color(index)),
			"score": 0,
			"credits": 0,
			"wins": 0,
			"fuel_reserve": TankState.TANK_FULL_FUEL,
			"leader": bool(entry.get("leader", false)),
			"order": index,
		}
		if index == 0:
			participant["tank"] = _player
			participant["inventory"] = _inventory
		elif index == 1:
			participant["tank"] = _enemy
			participant["inventory"] = _enemy_inventory
		else:
			participant["tank"] = TankState.new()
			participant["inventory"] = WeaponInventory.new()
		_participants.append(participant)
	if _participants.size() >= 2:
		_player_name = str(_participants[0].get("name", TURN_PLAYER))
		_enemy_name = str(_participants[1].get("name", TURN_ENEMY))
	_sync_participant_state_from_legacy()


func _normalized_roster_for_participants() -> Array[Dictionary]:
	if _configured_roster.size() >= 2:
		return _configured_roster.duplicate(true)
	return [
		{
			"slot": 0,
			"name": _player_name,
			"kind": "human",
			"controller": 0,
			"color": GroundfireTheme.COLOR_ACCENT_HOT,
		},
		{
			"slot": 1,
			"name": _enemy_name,
			"kind": "computer",
			"controller": -1,
			"color": Color("#4d95ff"),
		},
	]


func _default_participant_name(index: int) -> String:
	if index == 0:
		return TURN_PLAYER
	if index == 1:
		return TURN_ENEMY
	return "Player %d" % (index + 1)


func _default_participant_color(index: int) -> Color:
	if index == 0:
		return GroundfireTheme.COLOR_ACCENT_HOT
	if index == 1:
		return Color("#4d95ff")
	return Color.WHITE


func _sync_participant_state_from_legacy() -> void:
	if _participants.size() > 0:
		var player_participant: Dictionary = _participants[0]
		player_participant["score"] = _score
		player_participant["credits"] = _credits
		player_participant["wins"] = _player_wins
		player_participant["name"] = _player_name
		if _player.name == _player_name:
			player_participant["color"] = _player.body_color
		_participants[0] = player_participant
	if _participants.size() > 1:
		var enemy_participant: Dictionary = _participants[1]
		enemy_participant["score"] = _enemy_score
		enemy_participant["wins"] = _enemy_wins
		enemy_participant["name"] = _enemy_name
		if _enemy.name == _enemy_name:
			enemy_participant["color"] = _enemy.body_color
		_participants[1] = enemy_participant


func _participant_rows_snapshot() -> Array[Dictionary]:
	_sync_participant_state_from_legacy()
	var rows: Array[Dictionary] = []
	for participant_data in _participants:
		var participant: Dictionary = participant_data
		var tank := participant.get("tank") as RefCounted
		var inventory := participant.get("inventory") as RefCounted
		var tank_color: Color = participant.get("color", Color.WHITE)
		var tank_health := TankState.TANK_MAX_HEALTH
		var tank_fuel := TankState.TANK_FULL_FUEL
		var tank_state := TankState.STATE_ALIVE
		if tank != null:
			tank_color = tank.get("body_color")
			tank_health = int(tank.get("health"))
			tank_fuel = float(tank.get("fuel"))
			tank_state = str(tank.get("state"))
		var weapon_name := "Shell"
		var weapon_ammo := -1
		if inventory != null:
			weapon_name = str(inventory.call("current_name"))
			weapon_ammo = int(inventory.call("current_ammo"))
		rows.append({
			"slot": int(participant.get("slot", rows.size())),
			"name": str(participant.get("name", _default_participant_name(rows.size()))),
			"kind": str(participant.get("kind", "computer")),
			"controller": int(participant.get("controller", -1)),
			"color": tank_color,
			"score": int(participant.get("score", 0)),
			"credits": int(participant.get("credits", 0)),
			"wins": int(participant.get("wins", 0)),
			"leader": bool(participant.get("leader", false)),
			"order": int(participant.get("order", rows.size())),
			"health": tank_health,
			"fuel": tank_fuel,
			"state": tank_state,
			"weapon": weapon_name,
			"ammo": weapon_ammo,
		})
	return rows


func _participant_index_for_owner(owner: String) -> int:
	if owner == TURN_PLAYER:
		return 0
	if owner == TURN_ENEMY:
		return 1
	if owner.begins_with("Slot "):
		return int(owner.trim_prefix("Slot ")) - 1
	return -1


func _add_participant_score(owner: String, amount: int) -> void:
	if amount == 0:
		return
	var index := _participant_index_for_owner(owner)
	if index < 0 or index >= _participants.size():
		return
	var participant: Dictionary = _participants[index]
	participant["score"] = int(participant.get("score", 0)) + amount
	_participants[index] = participant


func _add_participant_credits(owner: String, amount: int) -> void:
	if amount == 0:
		return
	var index := _participant_index_for_owner(owner)
	if index < 0 or index >= _participants.size():
		return
	var participant: Dictionary = _participants[index]
	participant["credits"] = int(participant.get("credits", 0)) + amount
	_participants[index] = participant


func _add_participant_win(owner: String) -> void:
	var index := _participant_index_for_owner(owner)
	if index < 0 or index >= _participants.size():
		return
	var participant: Dictionary = _participants[index]
	participant["wins"] = int(participant.get("wins", 0)) + 1
	_participants[index] = participant


func _participant_is_leader_owner(owner: String) -> bool:
	var index := _participant_index_for_owner(owner)
	if index < 0 or index >= _participants.size():
		return false
	return bool(_participants[index].get("leader", false))


func _update_leader_flags() -> void:
	var leader := _unique_score_leader()
	for index in range(_participants.size()):
		var participant: Dictionary = _participants[index]
		participant["leader"] = not leader.is_empty() and _participant_owner(index) == leader
		_participants[index] = participant


func _add_win_for_owner(owner: String) -> void:
	var index := _participant_index_for_owner(owner)
	if index == 0:
		_player_wins += 1
	elif index == 1:
		_enemy_wins += 1
	_add_participant_win(owner)


func _participant_owner(index: int) -> String:
	return _participant_owner_for_index(index)


func _participant_tank(index: int) -> RefCounted:
	if index < 0 or index >= _participants.size():
		return null
	return _participants[index].get("tank") as RefCounted


func _tank_position(tank: RefCounted) -> Vector2:
	if tank == null:
		return Vector2.ZERO
	return tank.get("position") as Vector2


func _participant_inventory(index: int) -> RefCounted:
	if index < 0 or index >= _participants.size():
		return null
	return _participants[index].get("inventory") as RefCounted


func _participant_is_human(index: int) -> bool:
	if index < 0 or index >= _participants.size():
		return false
	return str(_participants[index].get("kind", "computer")) == "human"


func _has_human_participants() -> bool:
	for index in range(_participants.size()):
		if _participant_is_human(index):
			return true
	return false


func _participant_is_alive(index: int) -> bool:
	var tank := _participant_tank(index)
	return tank != null and str(tank.get("state")) == TankState.STATE_ALIVE


func _living_participant_indices() -> Array[int]:
	var living: Array[int] = []
	for index in range(_participants.size()):
		if _participant_is_alive(index):
			living.append(index)
	return living


func _living_participant_count() -> int:
	return _living_participant_indices().size()


func _next_living_participant_index(after_index: int) -> int:
	if _participants.is_empty():
		return -1
	for offset in range(1, _participants.size() + 1):
		var candidate := wrapi(after_index + offset, 0, _participants.size())
		if _participant_is_alive(candidate):
			return candidate
	return -1


func _target_index_for_attacker(attacker_index: int) -> int:
	if _participants.is_empty():
		return -1
	var attacker_tank := _participant_tank(attacker_index)
	var best_index := -1
	var best_distance := INF
	for index in range(_participants.size()):
		if index == attacker_index or not _participant_is_alive(index):
			continue
		var tank := _participant_tank(index)
		if tank == null or attacker_tank == null:
			continue
		var distance: float = abs(_tank_position(tank).x - _tank_position(attacker_tank).x)
		if distance < best_distance:
			best_index = index
			best_distance = distance
	return best_index


func _set_turn_index(index: int) -> void:
	_turn_index = clamp(index, 0, max(0, _participants.size() - 1))
	_turn_owner = _participant_owner(_turn_index)
	_target_index = _target_index_for_attacker(_turn_index)


func _turn_tank() -> RefCounted:
	return _participant_tank(_turn_index)


func _turn_inventory() -> RefCounted:
	return _participant_inventory(_turn_index)


func _target_tank() -> RefCounted:
	return _participant_tank(_target_index)


func _target_owner() -> String:
	if _target_index < 0:
		return ""
	return _participant_owner(_target_index)


func _record_round_defeat(attacker_owner: String, target_owner: String) -> void:
	if attacker_owner.is_empty() or target_owner.is_empty():
		return
	if not _round_defeats.has(attacker_owner):
		_round_defeats[attacker_owner] = []
	var defeats: Array = _round_defeats[attacker_owner]
	if not defeats.has(target_owner):
		defeats.append(target_owner)
	_round_defeats[attacker_owner] = defeats


func _owner_from_player_owned(player_owned: bool) -> String:
	return TURN_PLAYER if player_owned else TURN_ENEMY


func _normalized_owner(owner: Variant) -> String:
	if owner is bool:
		return _owner_from_player_owned(bool(owner))
	return str(owner)


func _add_score_for_owner(owner: String, amount: int) -> void:
	var index := _participant_index_for_owner(owner)
	if index == 0:
		_score += amount
	elif index == 1:
		_enemy_score += amount
	_add_participant_score(owner, amount)


func _add_credits_for_owner(owner: String, amount: int) -> void:
	var index := _participant_index_for_owner(owner)
	if index == 0:
		_credits += amount
	_add_participant_credits(owner, amount)


func _participant_score(index: int) -> int:
	if index == 0:
		return _score
	if index == 1:
		return _enemy_score
	if index >= 0 and index < _participants.size():
		return int(_participants[index].get("score", 0))
	return 0


func _participant_credits(index: int) -> int:
	if index == 0:
		return _credits
	if index >= 0 and index < _participants.size():
		return int(_participants[index].get("credits", 0))
	return 0


func _participant_wins(index: int) -> int:
	if index == 0:
		return _player_wins
	if index == 1:
		return _enemy_wins
	if index >= 0 and index < _participants.size():
		return int(_participants[index].get("wins", 0))
	return 0


func _credits_for_owner(owner: String) -> int:
	return _participant_credits(_participant_index_for_owner(owner))


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	_camera_shake_rng.seed = 4319
	_wind_rng.seed = 2783
	_load_gameplay_options()
	if _requested_total_rounds > 0:
		_total_rounds = _requested_total_rounds
	if _participants.is_empty():
		_build_participants_from_roster()
	_ensure_input_actions()
	_rebuild_terrain_if_needed(true)
	_start_round_turn("Round %d ready." % _round)
	_hud = LocalMatchHud.new()
	_hud.anchor_right = 1.0
	_hud.anchor_bottom = 1.0
	add_child(_hud)
	_build_quake_audio()
	_build_jump_jets_audio()
	_build_fire_shell_audio()
	_build_shell_death_audio()
	_build_launch_missile_audio()
	_build_missile_flight_audio()
	_build_missile_death_audio()
	_build_machine_gun_audio()
	_build_metal_hit_audio()
	_build_nuke_audio()
	_build_pause_overlay()
	_build_score_overlay()
	_build_winner_overlay()
	_build_shop_overlay()
	set_process(true)
	_update_hud()


func _enter_tree() -> void:
	if not _shutting_down:
		set_process(true)


func _exit_tree() -> void:
	if _shutting_down or is_queued_for_deletion():
		_prepare_for_shutdown()
	else:
		set_process(false)
		_stop_all_audio()


func _process(delta: float) -> void:
	_rebuild_terrain_if_needed()
	if _is_paused:
		queue_redraw()
		return
	if _mouse_aim_enabled and _phase == PHASE_AIM and _participant_is_human(_turn_index):
		_mouse_world_position = _screen_to_world(get_local_mouse_position())
	if _phase == PHASE_AIM and _participant_is_human(_turn_index):
		_handle_player_input(delta)
	else:
		_stop_jump_jets_audio()
		if _phase == PHASE_ROUND_OVER:
			_ai_timer -= delta
			if _ai_timer <= 0.0:
				_start_next_turn_or_round()
	_update_modal_activation(delta)
	_update_winner_spin(delta)
	_update_winner_background(delta)
	_update_shields(delta)
	_update_machine_gun_fire(delta)
	_update_projectiles(delta)
	_update_explosions(delta)
	_update_smoke_particles(delta)
	_update_tank_burn_smoke(delta)
	_update_quake(delta)
	_terrain.update(delta)
	for participant_data in _participants:
		var participant: Dictionary = participant_data
		var tank := participant.get("tank") as RefCounted
		if tank != null:
			tank.call("settle_on_terrain", _terrain, delta)
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
	_ensure_key_action("gf_shield", KEY_K)


func _ensure_key_action(action_name: String, keycode: Key) -> void:
	if not InputMap.has_action(action_name):
		InputMap.add_action(action_name)
	if not InputMap.action_get_events(action_name).is_empty():
		return
	var event := InputEventKey.new()
	event.keycode = keycode
	InputMap.action_add_event(action_name, event)


func _handle_player_input(delta: float) -> void:
	var tank := _turn_tank()
	if tank == null:
		return
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
	tank.call("update_gun", delta, aim_direction, power_direction)
	var move_direction := 0.0
	if Input.is_action_pressed("gf_move_left"):
		move_direction -= 1.0
	if Input.is_action_pressed("gf_move_right"):
		move_direction += 1.0
	if Input.is_action_pressed("gf_jump"):
		var can_boost := _tank_can_boost(tank)
		if can_boost:
			_emit_jump_jet_smoke(tank, delta)
		tank.call("boost", delta, move_direction)
		if can_boost:
			_play_jump_jets_audio()
		else:
			_stop_jump_jets_audio()
	elif move_direction != 0.0:
		_stop_jump_jets_audio()
		tank.call("move_on_terrain", move_direction, delta, _terrain)
	else:
		_stop_jump_jets_audio()


func _tank_can_boost(tank: RefCounted) -> bool:
	return tank != null and str(tank.get("state")) == TankState.STATE_ALIVE and float(tank.get("fuel")) > 0.0


func _update_shields(delta: float) -> void:
	for index in range(_participants.size()):
		var tank := _participant_tank(index)
		if tank == null or not tank.has_method("update_shield"):
			continue
		var can_hold_shield := index == _turn_index \
				and _participant_is_human(index) \
				and (_phase == PHASE_AIM or _phase == PHASE_PROJECTILE)
		tank.call("update_shield", can_hold_shield and Input.is_action_pressed("gf_shield"), delta)


func _unhandled_input(event: InputEvent) -> void:
	if _phase == PHASE_SHOP:
		get_viewport().set_input_as_handled()
		return
	if _phase == PHASE_WINNER:
		if event.is_action_pressed("ui_accept") or event.is_action_pressed("gf_fire") or event.is_action_pressed("ui_cancel"):
			_return_to_main_menu()
		get_viewport().set_input_as_handled()
		return
	if _phase == PHASE_SCORE:
		if event.is_action_pressed("ui_accept") or event.is_action_pressed("gf_fire") or event.is_action_pressed("ui_cancel"):
			_continue_from_score()
		get_viewport().set_input_as_handled()
		return
	if _machine_gun_active and _machine_gun_player_owned and event.is_action_pressed("gf_weapon_prev"):
		_unselect_machine_gun_and_cycle(-1)
		get_viewport().set_input_as_handled()
		return
	if _machine_gun_active and _machine_gun_player_owned and event.is_action_pressed("gf_weapon_next"):
		_unselect_machine_gun_and_cycle(1)
		get_viewport().set_input_as_handled()
		return
	if _machine_gun_active and _machine_gun_release_event(event):
		_machine_gun_fire_held = false
		_stop_machine_gun_audio()
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
	elif _mouse_aim_enabled and event is InputEventMouseMotion and _phase == PHASE_AIM and _participant_is_human(_turn_index):
		_mouse_world_position = _screen_to_world(get_local_mouse_position())
		_turn_tank().call("aim_at", _mouse_world_position)
	elif _mouse_aim_enabled \
			and event is InputEventMouseButton \
			and event.button_index == MOUSE_BUTTON_LEFT \
			and event.pressed \
			and _phase == PHASE_AIM \
			and _participant_is_human(_turn_index):
		_mouse_world_position = _screen_to_world(event.position)
		_turn_tank().call("aim_at", _mouse_world_position)
		_fire_player()
	elif event.is_action_pressed("gf_weapon_prev"):
		_cycle_weapon(-1)
	elif event.is_action_pressed("gf_weapon_next"):
		_cycle_weapon(1)
	elif event.is_action_pressed("gf_fire"):
		_fire_player()


func _update_modal_activation(delta: float) -> void:
	if _phase == PHASE_SHOP and _shop_input_delay > 0.0:
		_shop_input_delay = max(0.0, _shop_input_delay - delta)
		if _shop_input_delay <= 0.0:
			_refresh_shop_overlay()
	elif _phase == PHASE_SCORE and _score_continue_delay > 0.0:
		_score_continue_delay = max(0.0, _score_continue_delay - delta)
		if _score_continue_delay <= 0.0:
			_refresh_score_continue_button()
			if not _has_human_participants():
				_continue_from_score()
	elif _phase == PHASE_WINNER and _winner_continue_delay > 0.0:
		_winner_continue_delay = max(0.0, _winner_continue_delay - delta)
		if _winner_continue_delay <= 0.0:
			_refresh_winner_continue_button()
			if not _has_human_participants():
				_return_to_main_menu()


func _machine_gun_release_event(event: InputEvent) -> bool:
	if event.is_action_released("gf_fire"):
		return true
	return event is InputEventMouseButton \
			and event.button_index == MOUSE_BUTTON_LEFT \
			and not event.pressed


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


func _build_score_overlay() -> void:
	var backdrop := PanelContainer.new()
	backdrop.name = "ScoreOverlay"
	backdrop.anchor_right = 1.0
	backdrop.anchor_bottom = 1.0
	backdrop.visible = false
	backdrop.mouse_filter = Control.MOUSE_FILTER_STOP
	backdrop.add_theme_stylebox_override("panel", GroundfireTheme.modal_backdrop_style())
	add_child(backdrop)
	_score_overlay = backdrop

	var center := CenterContainer.new()
	center.anchor_right = 1.0
	center.anchor_bottom = 1.0
	backdrop.add_child(center)

	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(700.0, 360.0)
	panel.add_theme_stylebox_override("panel", GroundfireTheme.panel_style())
	center.add_child(panel)

	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 10)
	panel.add_child(stack)

	_score_title_label = Label.new()
	GroundfireTheme.apply_label(_score_title_label, 28, GroundfireTheme.COLOR_TEXT)
	stack.add_child(_score_title_label)

	_score_summary_label = Label.new()
	GroundfireTheme.apply_label(_score_summary_label, 16, GroundfireTheme.COLOR_CYAN)
	stack.add_child(_score_summary_label)

	_score_reward_label = Label.new()
	GroundfireTheme.apply_label(_score_reward_label, 16, GroundfireTheme.COLOR_WARN)
	stack.add_child(_score_reward_label)

	_score_rows_container = VBoxContainer.new()
	_score_rows_container.add_theme_constant_override("separation", 4)
	stack.add_child(_score_rows_container)

	_score_continue_button = _pause_button("Continue to Shop", _continue_from_score, true)
	stack.add_child(_score_continue_button)
	_wire_single_button_focus(_score_continue_button)


func _build_winner_overlay() -> void:
	var backdrop := Control.new()
	backdrop.name = "WinnerOverlay"
	backdrop.anchor_right = 1.0
	backdrop.anchor_bottom = 1.0
	backdrop.visible = false
	backdrop.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(backdrop)
	_winner_overlay = backdrop

	var background_fill := ColorRect.new()
	background_fill.name = "WinnerMenuBackgroundFill"
	background_fill.anchor_right = 1.0
	background_fill.anchor_bottom = 1.0
	background_fill.color = GroundfireTheme.COLOR_BG
	background_fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	backdrop.add_child(background_fill)

	var background := TextureRect.new()
	background.name = "WinnerMenuBackground"
	background.anchor_right = 1.0
	background.anchor_bottom = 1.0
	background.texture = MENU_TILE
	background.stretch_mode = TextureRect.STRETCH_TILE
	background.modulate = GroundfireTheme.COLOR_MENU_TILE_TINT
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	backdrop.add_child(background)
	_winner_background = background
	_apply_winner_background_scroll()

	var center := CenterContainer.new()
	center.anchor_right = 1.0
	center.anchor_bottom = 1.0
	backdrop.add_child(center)

	var content := MarginContainer.new()
	content.custom_minimum_size = Vector2(700.0, 420.0)
	center.add_child(content)

	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 10)
	content.add_child(stack)

	_winner_heading_label = Label.new()
	_winner_heading_label.text = "Final Result"
	GroundfireTheme.apply_label(_winner_heading_label, 28, GroundfireTheme.COLOR_TEXT)
	stack.add_child(_winner_heading_label)

	_winner_title_label = Label.new()
	GroundfireTheme.apply_label(_winner_title_label, 22, GroundfireTheme.COLOR_TEXT)
	stack.add_child(_winner_title_label)

	_winner_summary_label = Label.new()
	_winner_summary_label.visible = false
	GroundfireTheme.apply_label(_winner_summary_label, 16, GroundfireTheme.COLOR_CYAN)
	stack.add_child(_winner_summary_label)

	_winner_cards_container = VBoxContainer.new()
	_winner_cards_container.add_theme_constant_override("v_separation", 8)
	stack.add_child(_winner_cards_container)

	_winner_rows_container = VBoxContainer.new()
	_winner_rows_container.visible = false
	_winner_rows_container.add_theme_constant_override("separation", 4)
	stack.add_child(_winner_rows_container)

	_winner_main_menu_button = _pause_button("Main Menu", _return_to_main_menu, true)
	stack.add_child(_winner_main_menu_button)
	_wire_single_button_focus(_winner_main_menu_button)
	# Pygame WinnerMenu exits through fire/accept after the delay; it does not draw a menu button.
	_winner_main_menu_button.visible = false
	_winner_main_menu_button.focus_mode = Control.FOCUS_NONE


func _build_quake_audio() -> void:
	_quake_audio = AudioStreamPlayer.new()
	_quake_audio.name = "QuakeAudio"
	var quake_stream := QUAKE_SOUND.duplicate()
	if quake_stream is AudioStreamWAV:
		quake_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	_quake_audio.stream = quake_stream
	add_child(_quake_audio)


func _build_jump_jets_audio() -> void:
	_jump_jets_audio = AudioStreamPlayer.new()
	_jump_jets_audio.name = "JumpJetsAudio"
	var jump_jets_stream := JUMP_JETS_SOUND.duplicate()
	if jump_jets_stream is AudioStreamWAV:
		jump_jets_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	_jump_jets_audio.stream = jump_jets_stream
	add_child(_jump_jets_audio)


func _build_fire_shell_audio() -> void:
	_fire_shell_audio = AudioStreamPlayer.new()
	_fire_shell_audio.name = "FireShellAudio"
	var fire_shell_stream := FIRE_SHELL_SOUND.duplicate()
	if fire_shell_stream is AudioStreamWAV:
		fire_shell_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED
	_fire_shell_audio.stream = fire_shell_stream
	add_child(_fire_shell_audio)


func _build_shell_death_audio() -> void:
	_shell_death_audio = AudioStreamPlayer.new()
	_shell_death_audio.name = "ShellDeathAudio"
	var shell_death_stream := SHELL_DEATH_SOUND.duplicate()
	if shell_death_stream is AudioStreamWAV:
		shell_death_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED
	_shell_death_audio.stream = shell_death_stream
	add_child(_shell_death_audio)


func _build_launch_missile_audio() -> void:
	_launch_missile_audio = AudioStreamPlayer.new()
	_launch_missile_audio.name = "LaunchMissileAudio"
	var launch_missile_stream := LAUNCH_MISSILE_SOUND.duplicate()
	if launch_missile_stream is AudioStreamWAV:
		launch_missile_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED
	_launch_missile_audio.stream = launch_missile_stream
	add_child(_launch_missile_audio)


func _build_missile_flight_audio() -> void:
	_missile_flight_audio = AudioStreamPlayer.new()
	_missile_flight_audio.name = "MissileFlightAudio"
	var missile_flight_stream := MISSILE_FLIGHT_SOUND.duplicate()
	if missile_flight_stream is AudioStreamWAV:
		missile_flight_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	_missile_flight_audio.stream = missile_flight_stream
	add_child(_missile_flight_audio)


func _build_missile_death_audio() -> void:
	_missile_death_audio = AudioStreamPlayer.new()
	_missile_death_audio.name = "MissileDeathAudio"
	var missile_death_stream := MISSILE_DEATH_SOUND.duplicate()
	if missile_death_stream is AudioStreamWAV:
		missile_death_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED
	_missile_death_audio.stream = missile_death_stream
	add_child(_missile_death_audio)


func _build_machine_gun_audio() -> void:
	_machine_gun_audio = AudioStreamPlayer.new()
	_machine_gun_audio.name = "MachineGunAudio"
	var machine_gun_stream := MACHINE_GUN_SOUND.duplicate()
	if machine_gun_stream is AudioStreamWAV:
		machine_gun_stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	_machine_gun_audio.stream = machine_gun_stream
	add_child(_machine_gun_audio)


func _build_metal_hit_audio() -> void:
	_metal_hit_audio = AudioStreamPlayer.new()
	_metal_hit_audio.name = "MetalHitAudio"
	var metal_hit_stream := METAL_HIT_SOUND.duplicate()
	if metal_hit_stream is AudioStreamWAV:
		metal_hit_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED
	_metal_hit_audio.stream = metal_hit_stream
	add_child(_metal_hit_audio)


func _build_nuke_audio() -> void:
	_nuke_audio = AudioStreamPlayer.new()
	_nuke_audio.name = "NukeAudio"
	var nuke_stream := NUKE_SOUND.duplicate()
	if nuke_stream is AudioStreamWAV:
		nuke_stream.loop_mode = AudioStreamWAV.LOOP_DISABLED
	_nuke_audio.stream = nuke_stream
	add_child(_nuke_audio)


func _pause_button(text: String, callback: Callable, accent := false) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(300.0, 42.0)
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(button, accent)
	button.pressed.connect(callback)
	return button


func _set_paused(value: bool, focus_resume := true) -> void:
	_is_paused = value
	if _pause_overlay != null:
		_pause_overlay.visible = value
	if value and focus_resume and _resume_button != null:
		_resume_button.grab_focus.call_deferred()
	if not value:
		_load_gameplay_options()
	if _quake_audio != null:
		_quake_audio.stream_paused = value
		if not value and _quake_active:
			_play_quake_audio()
	if _jump_jets_audio != null:
		_jump_jets_audio.stream_paused = value
		if not value and _jump_jets_active:
			_play_jump_jets_audio()
	if _fire_shell_audio != null:
		_fire_shell_audio.stream_paused = value
	if _shell_death_audio != null:
		_shell_death_audio.stream_paused = value
	if _launch_missile_audio != null:
		_launch_missile_audio.stream_paused = value
	if _missile_flight_audio != null:
		_missile_flight_audio.stream_paused = value
		if not value and _has_fueled_missile_projectile():
			_play_missile_flight_audio()
	if _missile_death_audio != null:
		_missile_death_audio.stream_paused = value
	if _machine_gun_audio != null:
		_machine_gun_audio.stream_paused = value
		if not value and _machine_gun_active and _machine_gun_fire_held:
			_play_machine_gun_audio()
	if _metal_hit_audio != null:
		_metal_hit_audio.stream_paused = value
	if _nuke_audio != null:
		_nuke_audio.stream_paused = value
	_message = "Paused." if value else "Match resumed."
	_update_hud()


func _restart_round() -> void:
	_set_paused(false)
	_hide_score_overlay()
	_hide_shop_overlay()
	_hide_winner_overlay()
	_reset_quake_cycle()
	_stop_jump_jets_audio()
	_reset_machine_gun_fire()
	_stop_fire_shell_audio()
	_stop_shell_death_audio()
	_stop_launch_missile_audio()
	_stop_missile_flight_audio()
	_stop_missile_death_audio()
	_stop_nuke_audio()
	_stop_metal_hit_audio()
	_projectiles.clear()
	_explosions.clear()
	_smoke_particles.clear()
	_ai_timer = 0.0
	_phase = PHASE_AIM
	_round_defeats.clear()
	for index in range(_participants.size()):
		var inventory := _participant_inventory(index)
		if inventory != null:
			inventory.call("reset_round_ammo")
	_rebuild_terrain_if_needed(true)
	_start_round_turn("Round restarted.")
	_update_hud()


func _return_to_main_menu() -> void:
	if _phase == PHASE_WINNER and _winner_continue_delay > 0.0:
		return
	_set_paused(false)
	var host := get_parent()
	while host != null and not host.has_method("_show_main_menu"):
		host = host.get_parent()
	if host != null and host.has_method("_show_main_menu"):
		host.call("_show_main_menu")


func _open_options_from_pause() -> void:
	_set_paused(true, false)
	var host := get_parent()
	while host != null and not host.has_method("_show_options_for_paused_match"):
		host = host.get_parent()
	if host != null and host.has_method("_show_options_for_paused_match"):
		host.call("_show_options_for_paused_match", self)
		return
	_set_paused(false)


func _fire_player() -> void:
	if _phase != PHASE_AIM or not _participant_is_human(_turn_index) or not _projectiles.is_empty():
		return
	var tank := _turn_tank()
	var inventory := _turn_inventory()
	if tank == null or inventory == null:
		return
	var weapon: Dictionary = inventory.call("current")
	var kind := str(weapon.get("kind", "shell"))
	if kind == "corbomite":
		if not bool(inventory.call("consume_current")):
			_message = "No ammo for %s." % str(inventory.call("current_name"))
			return
		tank.corbomite_active = true
		tank.shield_active = true
		_message = "%s activated Corbomite shield!" % _participant_name_for_owner(_turn_owner)
		_phase = PHASE_ROUND_OVER
		_ai_timer = 0.75
		return
	if str(weapon.get("kind", "shell")) == "machine_gun":
		_begin_player_machine_gun_fire(weapon)
		return
	if not bool(inventory.call("consume_current")):
		_message = "No ammo for %s." % str(inventory.call("current_name"))
		return
	var speed_multiplier := float(weapon.get("speed", 4.2))
	_fire_weapon(
		tank.call("launch_origin"),
		float(tank.get("gun_angle")),
		float(tank.get("gun_power")),
		_turn_owner,
		weapon,
		tank.get("airborne_velocity"),
		tank.call("launch_velocity", float(tank.get("gun_power")), speed_multiplier)
	)
	_phase = PHASE_PROJECTILE
	_message = "%s fired %s." % [_participant_name_for_owner(_turn_owner), str(inventory.call("current_name"))]


func _fire_ai() -> void:
	var tank := _turn_tank()
	var inventory := _turn_inventory()
	if tank == null or inventory == null or _target_index < 0:
		return
	var shot := _choose_ai_shot()
	var weapon := _choose_ai_weapon(shot)
	var kind := str(weapon.get("kind", "shell"))
	if kind == "corbomite":
		inventory.call("select_by_name", str(weapon.get("name", WeaponInventory.SHELL)))
		inventory.call("consume_current")
		tank.corbomite_active = true
		tank.shield_active = true
		_message = "%s activated Corbomite shield!" % _participant_name_for_owner(_turn_owner)
		_phase = PHASE_ROUND_OVER
		_ai_timer = 0.75
		return
	if str(weapon.get("kind", "shell")) == "missile" or str(weapon.get("kind", "shell")) == "machine_gun":
		shot = _direct_ai_shot(weapon, shot)
	tank.set("gun_angle", float(shot["angle"]))
	tank.set("gun_power", float(shot["power"]))
	inventory.call("select_by_name", str(weapon.get("name", WeaponInventory.SHELL)))
	if str(weapon.get("kind", "shell")) == "machine_gun":
		_begin_enemy_machine_gun_fire(weapon)
		return
	inventory.call("consume_current")
	var speed_multiplier := float(weapon.get("speed", 4.2))
	_fire_weapon(
		tank.call("launch_origin"),
		float(tank.get("gun_angle")),
		float(tank.get("gun_power")),
		_turn_owner,
		weapon,
		tank.get("airborne_velocity"),
		tank.call("launch_velocity", float(tank.get("gun_power")), speed_multiplier)
	)
	_phase = PHASE_PROJECTILE
	_message = "%s fires %s." % [_participant_name_for_owner(_turn_owner), str(weapon.get("name", "Shell"))]


func _choose_ai_shot() -> Dictionary:
	var shell := WeaponInventory.WEAPONS[0]
	var attacker := _turn_tank()
	var target_tank := _target_tank()
	var origin: Vector2 = attacker.call("launch_origin")
	var target: Vector2 = _tank_position(target_tank) + Vector2(0.0, -20.0)
	var aim_sign := 1.0 if target.x < origin.x else -1.0
	var best_angle := 45.0 * aim_sign
	var best_power := TankState.GUN_POWER_DEFAULT
	var best_miss := INF
	for angle_offset in range(0, int(TankState.GUN_ANGLE_MAX) + 1, _ai_angle_step()):
		var angle := aim_sign * float(angle_offset)
		for power in range(6, int(TankState.GUN_POWER_MAX) + 1, _ai_power_step()):
			var miss := _simulate_ai_shell_miss(origin, angle, float(power), target, shell)
			if miss < best_miss:
				best_miss = miss
				best_angle = angle
				best_power = float(power)
	var angle_error := _ai_angle_error()
	var power_error := _ai_power_error()
	return {
		"angle": clampf(best_angle + randf_range(-angle_error, angle_error), TankState.GUN_ANGLE_MIN, TankState.GUN_ANGLE_MAX),
		"power": clampf(best_power + randf_range(-power_error, power_error), TankState.GUN_POWER_MIN, TankState.GUN_POWER_MAX),
		"miss": best_miss,
	}


func _simulate_ai_shell_miss(origin: Vector2, angle_degrees: float, power: float, target: Vector2, weapon: Dictionary) -> float:
	var velocity := _gun_direction_for_angle(angle_degrees) * _scaled_gun_power(power) * float(weapon.get("speed", 4.2))
	var position := origin
	var closest := origin.distance_to(target)
	var step := 1.0 / 30.0
	var age := 0.0
	for _index in range(120):
		var previous_position := position
		age += step
		velocity.x += _wind_acceleration(age) * step
		velocity.y += PROJECTILE_GRAVITY * step
		position += velocity * step
		closest = min(closest, _distance_to_segment(target, previous_position, position))
		if _terrain_hits_segment(previous_position, position) or position.x < 0.0 or position.x > _world_size.x:
			break
	return closest


func _gun_direction_for_angle(angle_degrees: float) -> Vector2:
	var radians := deg_to_rad(angle_degrees)
	return Vector2(-sin(radians), -cos(radians)).normalized()


func _angle_from_direction(direction: Vector2) -> float:
	if direction.length_squared() <= 0.0001:
		return 0.0
	return rad_to_deg(atan2(-direction.x, -direction.y))


func _scaled_gun_power(power: float) -> float:
	return power * TankState.GUN_POWER_PIXEL_SCALE


func _choose_ai_weapon(shot: Dictionary) -> Dictionary:
	var inventory := _turn_inventory()
	var attacker := _turn_tank()
	var target := _target_tank()
	var shell: Dictionary = inventory.call("weapon_by_name", WeaponInventory.SHELL)
	var distance: float = abs(_tank_position(attacker).x - _tank_position(target).x)
	var miss := float(shot.get("miss", INF))
	var direct_line: bool = _has_direct_line_to_player()
	var best_weapon := shell
	var best_score: float = float(_ai_weapon_projection(shell, shot, direct_line, distance).get("score", 0.0))
	for weapon in _ai_weapon_candidates(direct_line, distance, miss):
		var candidate: Dictionary = weapon
		var projection := _ai_weapon_projection(candidate, shot, direct_line, distance)
		var candidate_score := float(projection.get("score", -INF))
		if candidate_score >= _ai_weapon_score_threshold() and candidate_score > best_score:
			best_weapon = candidate
			best_score = candidate_score
	return best_weapon


func _ai_weapon_candidates(direct_line: bool, distance: float, miss: float) -> Array[Dictionary]:
	var candidates: Array[Dictionary] = []
	var inventory := _turn_inventory()
	var target := _target_tank()
	if direct_line and bool(inventory.call("has_ammo", WeaponInventory.MACHINE_GUN)):
		candidates.append(inventory.call("weapon_by_name", WeaponInventory.MACHINE_GUN))
	if _ai_difficulty == AI_DIFFICULTY_EASY:
		return candidates
	if bool(inventory.call("has_ammo", WeaponInventory.MISSILE)) and (direct_line or miss > _ai_missile_miss_threshold()):
		candidates.append(inventory.call("weapon_by_name", WeaponInventory.MISSILE))
	if bool(inventory.call("has_ammo", WeaponInventory.MIRV)) and distance > _ai_mirv_distance_threshold():
		candidates.append(inventory.call("weapon_by_name", WeaponInventory.MIRV))
	if bool(inventory.call("has_ammo", WeaponInventory.NUKE)) and (int(target.get("health")) <= _ai_nuke_health_threshold() or (distance > _ai_nuke_distance_threshold() and miss < _ai_nuke_miss_threshold())):
		candidates.append(inventory.call("weapon_by_name", WeaponInventory.NUKE))
	return candidates


func _ai_weapon_projection(weapon: Dictionary, shot: Dictionary, direct_line: bool, distance: float) -> Dictionary:
	var player_damage := _ai_expected_player_damage(weapon, shot, direct_line, distance)
	var self_damage := _ai_expected_self_damage(weapon)
	var score := float(player_damage) - float(self_damage) * _ai_self_damage_weight()
	if player_damage >= int(_target_tank().get("health")):
		score += AI_KILL_BONUS
	if self_damage >= int(_turn_tank().get("health")):
		score -= AI_SELF_KILL_PENALTY
	return {
		"score": score,
		"player_damage": player_damage,
		"self_damage": self_damage,
	}


func _ai_expected_player_damage(weapon: Dictionary, shot: Dictionary, direct_line: bool, distance: float) -> int:
	var kind := str(weapon.get("kind", "shell"))
	var damage := int(weapon.get("damage", 40))
	var quality := _ai_hit_quality(weapon, shot, direct_line, distance)
	if kind == "machine_gun":
		if not direct_line:
			return 0
		var burst := _machine_gun_ai_burst_budget(weapon)
		return min(int(_target_tank().get("health")), burst * damage)
	if kind == "mirv":
		var fragments: int = max(1, int(weapon.get("fragments", WeaponInventory.MIRV_FRAGMENTS)))
		return min(int(_target_tank().get("health")), int(round(float(damage * min(3, fragments)) * quality * 0.72)))
	return min(int(_target_tank().get("health")), int(round(float(damage) * quality)))


func _ai_expected_self_damage(weapon: Dictionary) -> int:
	if str(weapon.get("kind", "shell")) == "machine_gun":
		return 0
	var blast_radius := float(weapon.get("blast", 0.0))
	if blast_radius <= 0.0:
		return 0
	var damage := int(weapon.get("damage", 0))
	return _splash_damage(_tank_position(_target_tank()) + Vector2(0.0, -20.0), _tank_position(_turn_tank()) + Vector2(0.0, -20.0), damage, blast_radius)


func _ai_hit_quality(weapon: Dictionary, shot: Dictionary, direct_line: bool, distance: float) -> float:
	var kind := str(weapon.get("kind", "shell"))
	var blast_radius: float = max(1.0, float(weapon.get("blast", 48.0)))
	var miss := float(shot.get("miss", blast_radius))
	var quality: float = clamp(1.0 - (miss / (blast_radius * 1.65)), 0.0, 1.0)
	if direct_line and (kind == "missile" or kind == "machine_gun"):
		quality = max(quality, 0.9)
	if kind == "nuke":
		quality = max(quality, 0.82 if distance > 280.0 else 0.55)
	elif kind == "mirv" and distance > _ai_mirv_distance_threshold():
		quality = max(quality, 0.55)
	return quality


func _ai_weapon_score_threshold() -> float:
	if _ai_difficulty == AI_DIFFICULTY_EASY:
		return AI_WEAPON_SCORE_THRESHOLD_EASY
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return AI_WEAPON_SCORE_THRESHOLD_HARD
	return AI_WEAPON_SCORE_THRESHOLD_NORMAL


func _ai_self_damage_weight() -> float:
	if _ai_difficulty == AI_DIFFICULTY_EASY:
		return AI_SELF_DAMAGE_WEIGHT_EASY
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return AI_SELF_DAMAGE_WEIGHT_HARD
	return AI_SELF_DAMAGE_WEIGHT_NORMAL


func _ai_missile_miss_threshold() -> float:
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return 52.0
	return 72.0


func _ai_mirv_distance_threshold() -> float:
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return 340.0
	return 460.0


func _ai_nuke_health_threshold() -> int:
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return 70
	return 55


func _ai_nuke_distance_threshold() -> float:
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return 320.0
	return 360.0


func _ai_nuke_miss_threshold() -> float:
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return 56.0
	return 46.0


func _direct_ai_shot(weapon: Dictionary, fallback: Dictionary) -> Dictionary:
	var origin: Vector2 = _turn_tank().call("launch_origin")
	var target: Vector2 = _tank_position(_target_tank()) + Vector2(0.0, -20.0)
	var direction := target - origin
	if direction.length_squared() <= 1.0:
		return fallback
	var angle: float = clampf(_angle_from_direction(direction), TankState.GUN_ANGLE_MIN, TankState.GUN_ANGLE_MAX)
	var speed_multiplier: float = max(0.1, float(weapon.get("speed", 4.2)))
	var power: float = clampf(direction.length() / speed_multiplier * 0.18 / TankState.GUN_POWER_PIXEL_SCALE, 6.0, 18.0)
	return {"angle": angle, "power": power, "miss": fallback.get("miss", INF)}


func _has_direct_line_to_player() -> bool:
	var origin: Vector2 = _turn_tank().call("launch_origin")
	var target: Vector2 = _tank_position(_target_tank()) + Vector2(0.0, -20.0)
	return not bool(_terrain_collision(origin, target)["hit"])


func _begin_player_machine_gun_fire(weapon: Dictionary) -> void:
	var inventory := _turn_inventory()
	if inventory == null:
		return
	if int(inventory.call("current_ammo")) == 0:
		_message = "No ammo for %s." % str(inventory.call("current_name"))
		return
	_machine_gun_active = true
	_machine_gun_fire_held = true
	_machine_gun_owner = _turn_owner
	_machine_gun_player_owned = _machine_gun_owner == TURN_PLAYER
	_machine_gun_weapon = weapon.duplicate()
	_machine_gun_shots_fired = 0
	_machine_gun_ai_burst_remaining = 0
	_last_shot_owner = _machine_gun_owner
	_last_shot_player_owned = _last_shot_owner == TURN_PLAYER
	_phase = PHASE_PROJECTILE
	_message = "Machine Gun firing."
	_machine_gun_cooldown = _machine_gun_cooldown_time(_machine_gun_weapon)
	_play_machine_gun_audio()


func _begin_enemy_machine_gun_fire(weapon: Dictionary) -> void:
	var inventory := _turn_inventory()
	if inventory == null or int(inventory.call("current_ammo")) == 0:
		_last_shot_owner = _turn_owner
		_last_shot_player_owned = _last_shot_owner == TURN_PLAYER
		_start_next_turn_or_round()
		_message = "%s Machine Gun is empty." % _participant_name_for_owner(_turn_owner)
		return
	_machine_gun_active = true
	_machine_gun_fire_held = true
	_machine_gun_owner = _turn_owner
	_machine_gun_player_owned = _machine_gun_owner == TURN_PLAYER
	_machine_gun_weapon = weapon.duplicate()
	_machine_gun_shots_fired = 0
	_machine_gun_ai_burst_remaining = _machine_gun_ai_burst_budget(weapon)
	_last_shot_owner = _machine_gun_owner
	_last_shot_player_owned = _last_shot_owner == TURN_PLAYER
	_phase = PHASE_PROJECTILE
	_message = "%s fires Machine Gun." % _participant_name_for_owner(_machine_gun_owner)
	_machine_gun_cooldown = _machine_gun_cooldown_time(_machine_gun_weapon)
	_play_machine_gun_audio()


func _machine_gun_ai_burst_budget(weapon: Dictionary) -> int:
	var inventory := _turn_inventory()
	var target := _target_tank()
	var ammo := int(inventory.call("ammo_for", str(weapon.get("name", WeaponInventory.MACHINE_GUN))))
	if ammo <= 0:
		return 0
	var volley: int = max(1, int(weapon.get("volley", WeaponInventory.MACHINE_GUN_VOLLEY)))
	var distance: float = abs(_tank_position(_turn_tank()).x - _tank_position(target).x)
	var budget: int = MACHINE_GUN_AI_NORMAL_BURST
	if _ai_difficulty == AI_DIFFICULTY_EASY:
		budget = MACHINE_GUN_AI_EASY_BURST
	elif _ai_difficulty == AI_DIFFICULTY_HARD:
		budget = MACHINE_GUN_AI_HARD_BURST
	if int(target.get("health")) <= 16 and distance < 360.0:
		budget = max(budget, MACHINE_GUN_AI_FINISHER_BURST)
	elif distance > 340.0:
		budget = min(budget, volley)
	return min(ammo, max(1, budget))


func _machine_gun_cooldown_time(weapon: Dictionary) -> float:
	return max(0.001, float(weapon.get("cooldown", WeaponInventory.MACHINE_GUN_COOLDOWN)))


func _update_machine_gun_fire(delta: float) -> void:
	if not _machine_gun_active:
		return
	if _machine_gun_player_owned \
			and _machine_gun_fire_held \
			and not Input.is_action_pressed("gf_fire") \
			and not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		_machine_gun_fire_held = false
		_stop_machine_gun_audio()
	if not _machine_gun_fire_held:
		_finish_machine_gun_sequence_if_idle()
		return
	_machine_gun_cooldown -= delta
	var cooldown := _machine_gun_cooldown_time(_machine_gun_weapon)
	while _machine_gun_cooldown < 0.0 and _machine_gun_fire_held:
		if not _machine_gun_player_owned and _machine_gun_ai_burst_remaining <= 0:
			_machine_gun_fire_held = false
			_stop_machine_gun_audio()
			break
		var frame_delay: float = max(0.0, delta + _machine_gun_cooldown)
		if not _spawn_machine_gun_round(frame_delay):
			_machine_gun_fire_held = false
			_stop_machine_gun_audio()
			break
		_machine_gun_cooldown += cooldown


func _spawn_machine_gun_round(frame_delay := 0.0) -> bool:
	var owner_index := _participant_index_for_owner(_machine_gun_owner)
	var inventory := _participant_inventory(owner_index)
	var tank := _participant_tank(owner_index)
	var weapon_name := str(_machine_gun_weapon.get("name", WeaponInventory.MACHINE_GUN))
	if inventory == null or tank == null or not bool(inventory.call("consume_ammo", weapon_name, WeaponInventory.DEFAULT_AMMO_SPEND)):
		_message = "Machine Gun empty."
		return false
	var speed_multiplier := float(_machine_gun_weapon.get("speed", 5.8))
	var launch_power := _machine_gun_launch_power(_machine_gun_weapon)
	_fire_from(
		tank.call("launch_origin"),
		float(tank.get("gun_angle")),
		launch_power,
		_machine_gun_owner,
		_machine_gun_weapon,
		tank.get("airborne_velocity"),
		tank.call("launch_velocity", launch_power, speed_multiplier)
	)
	if frame_delay > 0.0 and not _projectiles.is_empty():
		_projectiles[_projectiles.size() - 1]["delay"] = frame_delay
	_machine_gun_shots_fired += 1
	if not _machine_gun_player_owned:
		_machine_gun_ai_burst_remaining -= 1
	return true


func _spawn_player_machine_gun_round() -> bool:
	return _spawn_machine_gun_round()


func _machine_gun_launch_power(weapon: Dictionary) -> float:
	return float(weapon.get("launch_power", WeaponInventory.MACHINE_GUN_CLASSIC_POWER))


func _reset_machine_gun_fire() -> void:
	_stop_machine_gun_audio()
	_machine_gun_active = false
	_machine_gun_fire_held = false
	_machine_gun_player_owned = true
	_machine_gun_owner = TURN_PLAYER
	_machine_gun_weapon = {}
	_machine_gun_cooldown = 0.0
	_machine_gun_shots_fired = 0
	_machine_gun_ai_burst_remaining = 0


func _finish_machine_gun_sequence_if_idle() -> void:
	if not _machine_gun_active or _machine_gun_fire_held or _has_projectile_kind("machine_gun"):
		return
	var shots_fired := _machine_gun_shots_fired
	if shots_fired > 0:
		_reset_machine_gun_fire()
		_after_explosion()
	else:
		_cancel_machine_gun_before_first_shot("Machine Gun cancelled.")


func _unselect_machine_gun_and_cycle(direction := 1) -> void:
	if not _machine_gun_active or not _machine_gun_player_owned:
		return
	_machine_gun_fire_held = false
	_stop_machine_gun_audio()
	var inventory := _participant_inventory(_participant_index_for_owner(_machine_gun_owner))
	if inventory == null:
		return
	var weapon_name := str(inventory.call("cycle", direction))
	_message = "Machine Gun unselected. Weapon selected: %s." % weapon_name
	if _machine_gun_shots_fired == 0 and not _has_projectile_kind("machine_gun"):
		_cancel_machine_gun_before_first_shot(_message)


func _cancel_machine_gun_before_first_shot(message: String) -> void:
	_reset_machine_gun_fire()
	_phase = PHASE_AIM
	_message = message


func _fire_weapon(origin: Vector2, angle_degrees: float, power: float, owner: Variant, weapon: Dictionary, inherited_velocity := Vector2.ZERO, velocity_override: Variant = null) -> void:
	var normalized_owner := _normalized_owner(owner)
	var kind := str(weapon.get("kind", "shell"))
	if kind == "machine_gun":
		var volley: int = max(1, int(weapon.get("volley", WeaponInventory.MACHINE_GUN_VOLLEY)))
		var cooldown: float = max(0.0, float(weapon.get("cooldown", WeaponInventory.MACHINE_GUN_COOLDOWN)))
		var launch_power := _machine_gun_launch_power(weapon)
		for index in range(volley):
			_fire_from(origin, angle_degrees, launch_power, normalized_owner, weapon, inherited_velocity, velocity_override)
			if not _projectiles.is_empty():
				_projectiles[_projectiles.size() - 1]["delay"] = float(index) * cooldown
		return
	_play_weapon_launch_audio(kind)
	_fire_from(origin, angle_degrees, power, normalized_owner, weapon, inherited_velocity, velocity_override)


func _play_weapon_launch_audio(kind: String) -> void:
	if kind == "missile":
		_play_launch_missile_audio()
	else:
		_play_fire_shell_audio()


func _fire_from(origin: Vector2, angle_degrees: float, power: float, owner: Variant, weapon: Dictionary, inherited_velocity := Vector2.ZERO, velocity_override: Variant = null) -> void:
	var normalized_owner := _normalized_owner(owner)
	var speed_multiplier := float(weapon.get("speed", 4.2))
	var velocity := _gun_direction_for_angle(angle_degrees) * _scaled_gun_power(power) * speed_multiplier + inherited_velocity
	if velocity_override is Vector2:
		velocity = Vector2(velocity_override)
	var kind := str(weapon.get("kind", "shell"))
	var split_age := INF
	if kind == "mirv" or kind == "deaths_head":
		split_age = max(MIRV_MIN_SPLIT_AGE, -velocity.y / PROJECTILE_GRAVITY)
	var missile_fuel := -1.0
	if kind == "missile":
		missile_fuel = float(weapon.get("fuel", 3.0))
	_last_shot_owner = normalized_owner
	_last_shot_player_owned = normalized_owner == TURN_PLAYER
	_projectiles.append({
		"position": origin,
		"previous_position": origin,
		"velocity": velocity,
		"launch_position": origin,
		"launch_velocity": velocity,
		"owner": normalized_owner,
		"player_owned": normalized_owner == TURN_PLAYER,
		"weapon": weapon,
		"kind": kind,
		"age": 0.0,
		"angle": angle_degrees,
		"angle_change": 0.0,
		"fuel": missile_fuel,
		"steer_sensitivity": float(weapon.get("steer_sensitivity", 300.0)),
		"back_position": origin,
		"split_age": split_age,
		"split": false,
	})
	if kind == "missile":
		_play_missile_flight_audio()


func _update_projectiles(delta: float) -> void:
	var projectiles_this_step := _projectiles.duplicate()
	for projectile in projectiles_this_step:
		if projectile.get("expired", false):
			continue
		var previous_position := Vector2(projectile["position"])
		var velocity: Vector2 = projectile["velocity"]
		var kind := str(projectile.get("kind", "shell"))
		if kind == "machine_gun":
			var active_delta := _machine_gun_projectile_delta(projectile, delta)
			if active_delta <= 0.0:
				continue
			projectile["age"] = float(projectile.get("age", 0.0)) + active_delta
			_update_machine_gun_projectile(projectile, previous_position, velocity, active_delta)
			continue
		if kind == "rolling_mine" and bool(projectile.get("rolling", false)):
			var roll_speed: float = float(projectile.get("roll_speed", 125.0))
			var x_change := roll_speed * delta
			var previous_pos := Vector2(projectile["position"])
			var new_x := previous_pos.x + x_change
			var new_y := _terrain.height_at(new_x)
			var position := Vector2(new_x, new_y)
			projectile["previous_position"] = previous_pos
			projectile["position"] = position
			projectile["age"] = float(projectile.get("age", 0.0)) + delta
			
			var direct_hit_owner := _segment_tank_hit_owner(previous_pos, position, str(projectile.get("owner", _owner_from_player_owned(bool(projectile.get("player_owned", true))))))
			if not direct_hit_owner.is_empty():
				_apply_explosion(position, projectile, direct_hit_owner)
				return
			if position.x < 0.0 or position.x > _world_size.x:
				var clamped_x: float = clampf(position.x, 0.0, _world_size.x)
				_apply_explosion(Vector2(clamped_x, _terrain.height_at(clamped_x)), projectile)
				return
			if float(projectile.get("age", 0.0)) >= 2.5:
				_apply_explosion(position, projectile)
				return
			continue
		var previous_age := float(projectile.get("age", 0.0))
		projectile["age"] = previous_age + delta
		var apply_ballistic_acceleration := true
		if kind == "missile":
			velocity = _update_missile_projectile(projectile, velocity, previous_position, delta)
			apply_ballistic_acceleration = _missile_applies_ballistic_acceleration(projectile)
		if (kind == "mirv" or kind == "deaths_head") and not bool(projectile.get("split", false)) and float(projectile["age"]) >= float(projectile.get("split_age", 0.8)):
			var split_delta: float = clamp(float(projectile.get("split_age", 0.8)) - previous_age, 0.0, delta)
			var split_velocity := _mirv_split_velocity(velocity, previous_age, split_delta)
			var split_position := previous_position + split_velocity * split_delta
			projectile["split"] = true
			if kind == "deaths_head":
				_spawn_deaths_head_children(split_position, split_velocity, str(projectile.get("owner", _owner_from_player_owned(bool(projectile.get("player_owned", true))))), Dictionary(projectile["weapon"]))
			else:
				_spawn_mirv_children(split_position, split_velocity, str(projectile.get("owner", _owner_from_player_owned(bool(projectile.get("player_owned", true))))), Dictionary(projectile["weapon"]))
			projectile["expired"] = true
			continue
		if apply_ballistic_acceleration:
			velocity.x += _wind_acceleration(float(projectile["age"])) * delta
			velocity.y += PROJECTILE_GRAVITY * delta
		var position := previous_position + velocity * delta
		projectile["previous_position"] = previous_position
		projectile["velocity"] = velocity
		projectile["position"] = position
		var direct_hit_owner := _segment_tank_hit_owner(
			previous_position,
			position,
			str(projectile.get("owner", _owner_from_player_owned(bool(projectile.get("player_owned", true)))))
		)
		if not direct_hit_owner.is_empty():
			_apply_explosion(position, projectile, direct_hit_owner)
			return
		var terrain_collision := _terrain_collision(previous_position, position)
		if bool(terrain_collision["hit"]):
			if kind == "rolling_mine":
				projectile["rolling"] = true
				projectile["position"] = Vector2(terrain_collision["position"])
				projectile["roll_speed"] = 125.0 * (1.0 if velocity.x >= 0.0 else -1.0)
				projectile["age"] = 0.0
				continue
			_apply_explosion(Vector2(terrain_collision["position"]), projectile)
			return
		if position.x < 0.0 or position.x > _world_size.x:
			var clamped_x: float = clampf(position.x, 0.0, _world_size.x)
			_apply_explosion(Vector2(clamped_x, min(position.y, _terrain.height_at(clamped_x))), projectile)
			return
		if position.y > _world_size.y + PROJECTILE_WORLD_MARGIN:
			_apply_explosion(Vector2(position.x, _terrain.height_at(position.x)), projectile)
			return
	_sync_missile_flight_audio()
	_finish_machine_gun_volley_if_needed()


func _mirv_split_velocity(velocity: Vector2, age: float, delta: float) -> Vector2:
	var split_velocity := velocity
	split_velocity.x += _wind_acceleration(age) * delta
	split_velocity.y += PROJECTILE_GRAVITY * delta
	return split_velocity


func _machine_gun_projectile_delta(projectile: Dictionary, delta: float) -> float:
	var delay := float(projectile.get("delay", 0.0))
	if delay <= 0.0:
		return delta
	delay -= delta
	projectile["delay"] = delay
	if delay >= 0.0:
		return 0.0
	projectile["delay"] = 0.0
	projectile["back_position"] = Vector2(projectile.get("position", Vector2.ZERO))
	return -delay


func _update_machine_gun_projectile(projectile: Dictionary, previous_position: Vector2, velocity: Vector2, delta: float) -> void:
	var weapon: Dictionary = projectile.get("weapon", {})
	if not projectile.has("launch_position"):
		projectile["launch_position"] = previous_position
	if not projectile.has("launch_velocity"):
		projectile["launch_velocity"] = velocity
	var age: float = max(0.0, float(projectile.get("age", delta)))
	var launch_velocity: Vector2 = Vector2(projectile.get("launch_velocity", velocity))
	var tracer_gravity: float = float(weapon.get("tracer_gravity", PROJECTILE_GRAVITY))
	var position: Vector2 = _machine_gun_projectile_position_at(projectile, age)
	var back_age: float = max(0.0, age - MACHINE_GUN_TRACER_TRAIL_TIME)
	velocity = launch_velocity + Vector2(0.0, tracer_gravity * age)
	projectile["back_position"] = _machine_gun_projectile_position_at(projectile, back_age)
	projectile["previous_position"] = previous_position
	projectile["velocity"] = velocity
	projectile["position"] = position
	var target_owner := _segment_tank_hit_owner(
		previous_position,
		position,
		str(projectile.get("owner", _owner_from_player_owned(bool(projectile.get("player_owned", true)))))
	)
	if not target_owner.is_empty():
		_apply_machine_gun_damage(projectile, target_owner)
		projectile["expired"] = true
		return
	var terrain_collision := _terrain_collision(previous_position, position)
	if bool(terrain_collision["hit"]):
		projectile["position"] = Vector2(terrain_collision["position"])
		projectile["expired"] = true
		return
	if position.x < 0.0 or position.x > _world_size.x or position.y > _world_size.y + PROJECTILE_WORLD_MARGIN:
		projectile["expired"] = true


func _machine_gun_projectile_position_at(projectile: Dictionary, age: float) -> Vector2:
	var launch_position: Vector2 = Vector2(projectile.get("launch_position", projectile.get("position", Vector2.ZERO)))
	var launch_velocity: Vector2 = Vector2(projectile.get("launch_velocity", projectile.get("velocity", Vector2.ZERO)))
	var weapon: Dictionary = projectile.get("weapon", {})
	var tracer_gravity: float = float(weapon.get("tracer_gravity", PROJECTILE_GRAVITY))
	var t: float = max(0.0, age)
	return launch_position + Vector2(
		launch_velocity.x * t,
		launch_velocity.y * t + 0.5 * tracer_gravity * t * t
	)


func _apply_machine_gun_damage(projectile: Dictionary, target_owner: String) -> void:
	var target_index := _participant_index_for_owner(target_owner)
	var target := _participant_tank(target_index)
	if target == null:
		return
	if target.state != TankState.STATE_ALIVE:
		return
	var weapon: Dictionary = projectile.get("weapon", {})
	var damage: int = max(0, int(weapon.get("damage", 2)))
	if damage <= 0:
		return
	_play_metal_hit_audio()
	var killed := bool(target.apply_damage(damage))
	var owner := str(projectile.get("owner", _owner_from_player_owned(bool(projectile.get("player_owned", true)))))
	if owner != target_owner:
		_add_score_for_owner(owner, damage)
		_add_credits_for_owner(owner, damage)
	_message = "%s Machine Gun dealt %d damage to %s." % [
		_participant_name_for_owner(owner),
		damage,
		_participant_name_for_owner(target_owner),
	]
	if killed:
		_record_round_defeat(owner, target_owner)
		_stop_machine_gun_after_lethal_hit(target_owner)


func _stop_machine_gun_after_lethal_hit(target_owner: String) -> void:
	_machine_gun_fire_held = false
	_machine_gun_ai_burst_remaining = 0
	_stop_machine_gun_audio()
	_expire_pending_machine_gun_rounds()
	_message = "Machine Gun destroyed %s." % _participant_name_for_owner(target_owner)


func _expire_pending_machine_gun_rounds() -> void:
	for projectile in _projectiles:
		if str(projectile.get("kind", "shell")) == "machine_gun":
			projectile["expired"] = true


func _finish_machine_gun_volley_if_needed() -> void:
	var had_machine_gun := false
	var remaining: Array[Dictionary] = []
	for projectile in _projectiles:
		if str(projectile.get("kind", "shell")) == "machine_gun":
			had_machine_gun = true
		if not bool(projectile.get("expired", false)):
			remaining.append(projectile)
	if remaining.size() == _projectiles.size():
		_finish_machine_gun_sequence_if_idle()
		return
	_projectiles = remaining
	if had_machine_gun and not _has_projectile_kind("machine_gun"):
		if _machine_gun_active:
			_finish_machine_gun_sequence_if_idle()
		else:
			_after_explosion()


func _has_projectile_kind(kind: String) -> bool:
	for projectile in _projectiles:
		if str(projectile.get("kind", "shell")) == kind:
			return true
	return false


func _update_missile_projectile(projectile: Dictionary, velocity: Vector2, position: Vector2, delta: float) -> Vector2:
	if float(projectile.get("fuel", -1.0)) < 0.0:
		projectile["fuel_exhausted_this_frame"] = false
		return velocity
	var steer := _missile_steer_direction(projectile, position)
	var steer_sensitivity := float(projectile.get("steer_sensitivity", 300.0))
	var angle_change := float(projectile.get("angle_change", 0.0))
	if steer > 0.0:
		angle_change = min(MISSILE_ANGLE_CHANGE_LIMIT, angle_change + steer_sensitivity * delta)
	elif steer < 0.0:
		angle_change = max(-MISSILE_ANGLE_CHANGE_LIMIT, angle_change - steer_sensitivity * delta)
	else:
		angle_change = move_toward(angle_change, 0.0, MISSILE_RECENTER_MULTIPLIER * steer_sensitivity * delta)
	var angle := float(projectile.get("angle", _angle_from_direction(velocity)))
	angle += angle_change * delta
	var powered_velocity := _missile_powered_velocity(angle, projectile)
	var previous_fuel := float(projectile.get("fuel", 0.0))
	var remaining_fuel := previous_fuel - delta
	projectile["angle"] = angle
	projectile["angle_change"] = angle_change
	projectile["fuel"] = remaining_fuel
	projectile["fuel_exhausted_this_frame"] = previous_fuel >= 0.0 and remaining_fuel < 0.0
	return powered_velocity


func _missile_applies_ballistic_acceleration(projectile: Dictionary) -> bool:
	return float(projectile.get("fuel", -1.0)) < 0.0 and not bool(projectile.get("fuel_exhausted_this_frame", false))


func _missile_powered_velocity(angle_degrees: float, projectile: Dictionary) -> Vector2:
	var weapon: Dictionary = projectile.get("weapon", {})
	var classic_speed := float(weapon.get("powered_speed", WeaponInventory.MISSILE_CLASSIC_SPEED))
	var radians := deg_to_rad(angle_degrees)
	var speed_factor: float = classic_speed - cos(radians)
	return _gun_direction_for_angle(angle_degrees) * speed_factor * TankState.GUN_POWER_PIXEL_SCALE


func _missile_steer_direction(projectile: Dictionary, position: Vector2) -> float:
	var owner := str(projectile.get("owner", _owner_from_player_owned(bool(projectile.get("player_owned", false)))))
	var owner_index := _participant_index_for_owner(owner)
	if _participant_is_human(owner_index):
		var steer := 0.0
		if Input.is_action_pressed("gf_aim_left"):
			steer += 1.0
		if Input.is_action_pressed("gf_aim_right"):
			steer -= 1.0
		return steer
	var target_index := _target_index_for_attacker(owner_index)
	var target_tank := _participant_tank(target_index)
	if target_tank == null:
		return 0.0
	var target: Vector2 = _tank_position(target_tank) + Vector2(0.0, -20.0)
	var desired_angle := _angle_from_direction(target - position)
	var delta_angle := _short_angle_delta(float(projectile.get("angle", 0.0)), desired_angle)
	return clamp(delta_angle / MISSILE_AI_STEER_ANGLE_SCALE, -1.0, 1.0)


func _short_angle_delta(from_degrees: float, to_degrees: float) -> float:
	return fposmod(to_degrees - from_degrees + 180.0, 360.0) - 180.0


func _spawn_mirv_children(origin: Vector2, velocity: Vector2, owner: Variant, weapon: Dictionary) -> void:
	var normalized_owner := _normalized_owner(owner)
	var fragments: int = max(1, int(weapon.get("fragments", WeaponInventory.MIRV_FRAGMENTS)))
	var spread: float = float(weapon.get("spread", WeaponInventory.MIRV_SPREAD))
	var spread_direction := -1.0 if velocity.x < 0.0 else 1.0
	var spread_step: float = max(abs(velocity.x) * spread, float(weapon.get("min_fragment_spread_speed", WeaponInventory.MIRV_MIN_FRAGMENT_SPREAD_SPEED))) * spread_direction
	for index in range(fragments):
		var offset: float = float(index) - (float(fragments - 1) * 0.5)
		var child_weapon := weapon.duplicate()
		child_weapon["kind"] = "shell"
		child_weapon["name"] = "MIRV Fragment"
		var child_velocity := Vector2(velocity.x + (spread_step * offset), 0.0)
		_projectiles.append({
			"position": origin,
			"previous_position": origin,
			"velocity": child_velocity,
			"owner": normalized_owner,
			"player_owned": normalized_owner == TURN_PLAYER,
			"weapon": child_weapon,
			"kind": "shell",
			"age": 0.0,
			"split": true,
		})


func _spawn_deaths_head_children(origin: Vector2, velocity: Vector2, owner: Variant, weapon: Dictionary) -> void:
	var normalized_owner := _normalized_owner(owner)
	var fragments: int = max(1, int(weapon.get("fragments", 8)))
	var spread: float = float(weapon.get("spread", 0.35))
	var spread_direction := -1.0 if velocity.x < 0.0 else 1.0
	var spread_step: float = max(abs(velocity.x) * spread, 25.0) * spread_direction
	for index in range(fragments):
		var offset: float = float(index) - (float(fragments - 1) * 0.5)
		var child_weapon := weapon.duplicate()
		child_weapon["kind"] = "shell"
		child_weapon["name"] = "Death's Head Fragment"
		child_weapon["damage"] = 25
		child_weapon["blast"] = 30.0
		var child_velocity := Vector2(velocity.x + (spread_step * offset), -abs(offset) * 8.0)
		_projectiles.append({
			"position": origin,
			"previous_position": origin,
			"velocity": child_velocity,
			"owner": normalized_owner,
			"player_owned": normalized_owner == TURN_PLAYER,
			"weapon": child_weapon,
			"kind": "shell",
			"age": 0.0,
			"split": true,
		})


func _trigger_airstrike(impact_x: float, owner: String, weapon: Dictionary) -> void:
	var normalized_owner := _normalized_owner(owner)
	var count := 5
	var spacing := 32.0
	var child_weapon := weapon.duplicate()
	child_weapon["kind"] = "shell"
	child_weapon["name"] = "Airstrike Missile"
	child_weapon["damage"] = 40
	child_weapon["blast"] = 40.0
	for i in range(count):
		var offset: float = float(i) - (float(count - 1) * 0.5)
		var spawn_x := impact_x + offset * spacing
		var spawn_y := -100.0
		var spawn_pos := Vector2(spawn_x, spawn_y)
		var velocity := Vector2(0.0, 250.0)
		_projectiles.append({
			"position": spawn_pos,
			"previous_position": spawn_pos,
			"velocity": velocity,
			"owner": normalized_owner,
			"player_owned": normalized_owner == TURN_PLAYER,
			"weapon": child_weapon,
			"kind": "shell",
			"age": 0.0,
			"split": true,
		})


func _segment_hits_tank(start: Vector2, end: Vector2, tank_position: Vector2) -> bool:
	return _distance_to_segment(tank_position + Vector2(0.0, -18.0), start, end) < 34.0


func _segment_tank_hit_owner(start: Vector2, end: Vector2, ignored_owner := "") -> String:
	var best_owner := ""
	var best_fraction := INF
	for index in range(_participants.size()):
		if not _participant_is_alive(index):
			continue
		var owner := _participant_owner(index)
		if owner == ignored_owner:
			continue
		var tank := _participant_tank(index)
		if tank == null:
			continue
		var fraction := _segment_tank_hit_fraction(start, end, _tank_position(tank))
		if fraction < best_fraction:
			best_owner = owner
			best_fraction = fraction
	return best_owner


func _segment_tank_hit_fraction(start: Vector2, end: Vector2, tank_position: Vector2) -> float:
	if not _segment_hits_tank(start, end, tank_position):
		return INF
	var segment := end - start
	if segment.length_squared() <= 0.0:
		return 0.0
	var tank_center := tank_position + Vector2(0.0, -18.0)
	return clamp((tank_center - start).dot(segment) / segment.length_squared(), 0.0, 1.0)


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


func _apply_explosion(position: Vector2, projectile: Dictionary, direct_hit_owner := "") -> void:
	var weapon: Dictionary = projectile["weapon"]
	var kind := str(projectile.get("kind", "shell"))
	var owner := str(projectile.get("owner", _owner_from_player_owned(bool(projectile.get("player_owned", true)))))
	
	if kind == "airstrike":
		_trigger_airstrike(position.x, owner, weapon)
		_projectiles.erase(projectile)
		return
		
	if kind == "hover_coil":
		_spawn_explosion(position, 60.0, false)
		var total_affected := 0
		for index in range(_participants.size()):
			if not _participant_is_alive(index):
				continue
			var target_tank := _participant_tank(index)
			if target_tank == null:
				continue
			var tank_pos := _tank_position(target_tank)
			if position.distance_to(tank_pos) <= 120.0:
				target_tank.hover_time = 4.0
				target_tank.airborne_velocity = Vector2(0.0, -85.0)
				target_tank.on_ground = false
				total_affected += 1
		_message = "Hover Coil activated! Hovering %d tanks." % total_affected
		_projectiles.erase(projectile)
		if _projectiles.is_empty():
			_after_explosion()
		return

	var damage := int(weapon.get("damage", 40))
	var blast_radius := float(weapon.get("blast", 48.0))
	_last_shot_owner = owner
	_last_shot_player_owned = owner == TURN_PLAYER
	var white_out := _weapon_white_out(weapon)
	_play_explosion_death_audio(kind, white_out)
	_spawn_explosion(position, blast_radius, white_out)
	var total_other_damage := 0
	for index in range(_participants.size()):
		if not _participant_is_alive(index):
			continue
		var target_owner := _participant_owner(index)
		var target := _participant_tank(index)
		if target == null:
			continue
		var raw_target_damage := _explosion_damage_for_target(
			position,
			_tank_position(target) + Vector2(0.0, -20.0),
			damage,
			blast_radius,
			target_owner,
			direct_hit_owner
		)
		if target.get("corbomite_active") and raw_target_damage > 0:
			var shooter_index := _participant_index_for_owner(owner)
			var shooter_tank := _participant_tank(shooter_index)
			if shooter_tank != null and shooter_tank.state == TankState.STATE_ALIVE:
				shooter_tank.call("apply_damage", raw_target_damage)
				_message = "Corbomite reflected %d damage to %s!" % [raw_target_damage, _participant_name_for_owner(owner)]
				if shooter_tank.state == TankState.STATE_DEAD:
					_record_round_defeat(target_owner, owner)
			continue
		var target_damage := _damage_after_tank_shield(target, raw_target_damage)
		if target_damage <= 0:
			continue
		var killed := bool(target.call("apply_damage", target_damage))
		if owner != target_owner:
			total_other_damage += target_damage
			_add_score_for_owner(owner, target_damage)
			_add_credits_for_owner(owner, target_damage)
		if killed:
			_record_round_defeat(owner, target_owner)
	_message = "%s dealt %d damage." % [_participant_name_for_owner(owner), total_other_damage]
	_stop_missile_flight_audio()
	_projectiles.clear()
	_after_explosion()


func _explosion_damage_for_target(
		explosion_position: Vector2,
		target_position: Vector2,
		max_damage: int,
		radius: float,
		target_owner: String,
		direct_hit_owner: String) -> int:
	if direct_hit_owner == target_owner:
		return max_damage
	return _splash_damage(explosion_position, target_position, max_damage, radius)


func _damage_after_tank_shield(tank: RefCounted, amount: int) -> int:
	if tank != null and tank.has_method("damage_after_shield"):
		return int(tank.call("damage_after_shield", amount))
	return amount


func _weapon_white_out(weapon: Dictionary) -> bool:
	return bool(weapon.get("white_out", str(weapon.get("kind", "")) == "nuke"))


func _play_explosion_death_audio(kind: String, white_out: bool) -> void:
	if white_out:
		return
	if kind == "missile":
		_play_missile_death_audio()
	else:
		_play_shell_death_audio()


func _after_explosion() -> void:
	var living := _living_participant_indices()
	if living.size() <= 1:
		var winner_owner := _participant_owner(living[0]) if living.size() == 1 else ""
		if not winner_owner.is_empty():
			_add_win_for_owner(winner_owner)
		var title := "Round Draw" if winner_owner.is_empty() else "%s Wins" % _participant_name_for_owner(winner_owner)
		var reward := SCORE_ROUND_WIN_REWARD if not winner_owner.is_empty() else 0
		_open_round_score(title, reward, winner_owner)
		return
	_phase = PHASE_ROUND_OVER
	_ai_timer = 0.75


func _start_next_turn_or_round() -> void:
	var last_index := _participant_index_for_owner(_last_shot_owner)
	var next_index := _next_living_participant_index(last_index)
	if next_index < 0:
		return
	_set_turn_index(next_index)
	_shift_wind_for_turn()
	if _participant_is_human(_turn_index):
		_phase = PHASE_AIM
		_message = "%s turn. %s." % [_participant_name_for_owner(_turn_owner), _wind_status()]
	else:
		_fire_ai()


func _start_round_turn(message: String) -> void:
	var first_index := _next_living_participant_index(_participants.size() - 1)
	if first_index < 0:
		return
	_set_turn_index(first_index)
	if _participant_is_human(_turn_index):
		_phase = PHASE_AIM
		_message = "%s %s turn. %s." % [message, _participant_name_for_owner(_turn_owner), _wind_status()]
	else:
		_message = "%s %s starts." % [message, _participant_name_for_owner(_turn_owner)]
		_fire_ai()


func _open_round_score(title: String, reward: int, score_winner := TURN_PLAYER) -> void:
	_reset_machine_gun_fire()
	_score_title = title
	_score_reward = reward
	_score_round_winner = score_winner
	var defeated_owners: Array = _round_defeats.get(score_winner, [])
	if defeated_owners.is_empty():
		for index in range(_participants.size()):
			var owner := _participant_owner(index)
			if owner != score_winner and not _participant_is_alive(index):
				defeated_owners.append(owner)
	if defeated_owners.is_empty() and _participants.size() == 2 and not score_winner.is_empty():
		defeated_owners.append(TURN_ENEMY if score_winner == TURN_PLAYER else TURN_PLAYER)
	_score_defeated_name = ", ".join(defeated_owners.map(func(owner: String) -> String: return _participant_name_for_owner(owner)))
	_score_defeated_was_leader = false
	for defeated_owner_variant in defeated_owners:
		if _participant_is_leader_owner(str(defeated_owner_variant)):
			_score_defeated_was_leader = true
			break
	_apply_classic_round_rewards(score_winner)
	_phase = PHASE_SCORE
	_score_continue_delay = _score_activation_delay()
	_ai_timer = 0.0
	_stop_quake_audio()
	_message = "%s. Review score before shopping." % title
	_refresh_score_overlay()


func _apply_classic_round_rewards(score_winner: String) -> void:
	_score_round_details.clear()
	_score_round_credits.clear()
	for index in range(_participants.size()):
		var owner := _participant_owner(index)
		var score_delta := 0
		var credits_delta := CREDITS_ROUND_STIPEND
		var details: Array[String] = []
		var defeated_owners: Array = _round_defeats.get(owner, [])
		for defeated_variant in defeated_owners:
			var defeated_owner := str(defeated_variant)
			if defeated_owner == owner:
				score_delta += SCORE_SELF_DEFEAT_PENALTY
				details.append("Self defeat %d" % SCORE_SELF_DEFEAT_PENALTY)
			elif _participant_is_leader_owner(defeated_owner):
				score_delta += SCORE_DEFEAT_LEADER_REWARD
				credits_delta += CREDITS_DEFEAT_REWARD
				details.append("Defeated %s leader +%d" % [_participant_name_for_owner(defeated_owner), SCORE_DEFEAT_LEADER_REWARD])
			else:
				score_delta += SCORE_DEFEAT_REWARD
				credits_delta += CREDITS_DEFEAT_REWARD
				details.append("Defeated %s +%d" % [_participant_name_for_owner(defeated_owner), SCORE_DEFEAT_REWARD])
		if _participant_is_alive(index):
			score_delta += SCORE_SURVIVAL_REWARD
			credits_delta += CREDITS_SURVIVAL_REWARD
			details.append("Survived +%d" % SCORE_SURVIVAL_REWARD)
		if owner == score_winner and defeated_owners.is_empty() and not score_winner.is_empty():
			details.append("Round winner")
		_add_score_for_owner(owner, score_delta)
		_add_credits_for_owner(owner, credits_delta)
		_score_round_credits[owner] = credits_delta
		_score_round_details[owner] = ", ".join(details) if not details.is_empty() else "Round stipend"


func _refresh_score_overlay() -> void:
	if _score_overlay == null:
		return
	_score_overlay.visible = true
	_score_title_label.text = _score_title
	_score_summary_label.text = "Round %d of %d  %d players  %s" % [
		_round,
		_total_rounds,
		_participant_rows_snapshot().size(),
		_score_leader_summary(),
	]
	var score_credits := _credits_for_owner(_score_round_winner) if not _score_round_winner.is_empty() else _credits
	var round_credits := int(_score_round_credits.get(_score_round_winner, 0)) if not _score_round_winner.is_empty() else 0
	_score_reward_label.text = "Round credits +%d  Credits %d" % [round_credits, score_credits]
	_rebuild_score_rows()
	_refresh_score_continue_button()
	_update_hud()


func _refresh_score_continue_button() -> void:
	if _score_continue_button == null:
		return
	_score_continue_button.text = "Continue to Final Result" if _is_final_round() else "Continue to Shop"
	_score_continue_button.disabled = _score_continue_delay > 0.0
	if not _score_continue_button.disabled:
		_score_continue_button.grab_focus.call_deferred()


func _rebuild_score_rows() -> void:
	if _score_rows_container == null:
		return
	for child in _score_rows_container.get_children():
		_score_rows_container.remove_child(child)
		child.queue_free()
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 8)
	header.add_child(_score_cell("Rank", 52.0, GroundfireTheme.COLOR_MUTED, 13))
	header.add_child(_score_cell("Player", 160.0, GroundfireTheme.COLOR_MUTED, 13))
	header.add_child(_score_cell("Scoring for Round", 270.0, GroundfireTheme.COLOR_MUTED, 13))
	header.add_child(_score_cell("Total Score", 110.0, GroundfireTheme.COLOR_MUTED, 13))
	_score_rows_container.add_child(header)
	for row_data in _score_rows_snapshot():
		_add_score_row(row_data)


func _score_cell(text: String, width: float, color: Color, font_size: int) -> Label:
	var label := Label.new()
	label.text = text
	label.custom_minimum_size = Vector2(width, 24.0)
	GroundfireTheme.apply_label(label, font_size, color)
	return label


func _add_score_row(row_data: Dictionary) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	row.add_child(_score_cell(str(row_data.get("rank", "")), 52.0, GroundfireTheme.COLOR_TEXT, 16))

	var player_cell := HBoxContainer.new()
	player_cell.custom_minimum_size = Vector2(160.0, 28.0)
	player_cell.add_theme_constant_override("separation", 8)
	var player_color: Color = row_data.get("color", Color.WHITE)
	player_cell.add_child(_score_tank_icon(player_color, "ScorePlayerTank"))
	var name_text := str(row_data.get("name", ""))
	if bool(row_data.get("leader", false)):
		name_text = "%s leader" % name_text
	player_cell.add_child(_score_cell(name_text, 120.0, GroundfireTheme.COLOR_TEXT, 15))
	row.add_child(_score_column_panel(player_cell, 160.0, "ScorePlayerColumn"))

	row.add_child(_score_column_panel(_score_round_detail_cell(row_data), 270.0, "ScoreRoundColumn"))
	row.add_child(_score_column_panel(_score_cell(str(row_data.get("score", 0)), 110.0, GroundfireTheme.COLOR_TEXT, 16), 110.0, "ScoreTotalColumn"))
	_score_rows_container.add_child(row)


func _score_column_panel(content: Control, width: float, node_name: String) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.name = node_name
	panel.custom_minimum_size = Vector2(width, 28.0)
	var style := GroundfireTheme.classic_panel_style()
	style.bg_color = Color("#00000080")
	panel.add_theme_stylebox_override("panel", style)
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.add_child(content)
	return panel


func _score_round_detail_cell(row_data: Dictionary) -> HBoxContainer:
	var cell := HBoxContainer.new()
	cell.custom_minimum_size = Vector2(270.0, 28.0)
	cell.add_theme_constant_override("separation", 6)
	for icon_data in Array(row_data.get("defeated_icons", [])):
		cell.add_child(_score_defeated_icon(Dictionary(icon_data)))
	var detail := _score_cell(str(row_data.get("round_detail", "-")), 120.0, GroundfireTheme.COLOR_CYAN, 15)
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cell.add_child(detail)
	return cell


func _score_defeated_icon(icon_data: Dictionary) -> Control:
	var icon_color: Color = icon_data.get("color", Color.WHITE)
	var icon := _score_tank_icon(icon_color, "DefeatedTank")
	if bool(icon_data.get("leader", false)):
		var pole := Polygon2D.new()
		pole.name = "LeaderPole"
		pole.polygon = PackedVector2Array([
			Vector2(5.0, 18.0),
			Vector2(5.0, 4.0),
			Vector2(7.0, 4.0),
			Vector2(7.0, 18.0),
		])
		pole.color = Color("#808080")
		icon.add_child(pole)
		var flag := Polygon2D.new()
		flag.name = "LeaderFlag"
		flag.polygon = PackedVector2Array([
			Vector2(7.0, 5.0),
			Vector2(7.0, 13.0),
			Vector2(22.0, 13.0),
			Vector2(22.0, 5.0),
		])
		flag.color = icon_color
		icon.add_child(flag)
	return icon


func _score_tank_icon(color: Color, node_name: String) -> Control:
	var icon := Control.new()
	icon.custom_minimum_size = Vector2(34.0, 24.0)
	var body := Polygon2D.new()
	body.name = node_name
	body.polygon = PackedVector2Array([
		Vector2(2.0, 18.0),
		Vector2(8.0, 6.0),
		Vector2(24.0, 6.0),
		Vector2(31.0, 18.0),
	])
	body.color = color
	icon.add_child(body)
	return icon


func _score_rows_snapshot() -> Array[Dictionary]:
	var rows := _participant_rows_snapshot()
	for index in range(rows.size()):
		var row: Dictionary = rows[index]
		var owner := _participant_owner_for_index(int(row.get("order", index)))
		row["owner"] = owner
		row["round_detail"] = _score_round_detail_for(owner)
		row["defeated_icons"] = _score_defeated_icons_for(owner)
		rows[index] = row
	rows.sort_custom(_score_row_before)
	var ranked_rows: Array[Dictionary] = []
	for index in range(rows.size()):
		var row := rows[index].duplicate()
		row["rank"] = _score_rank_label(index, rows)
		ranked_rows.append(row)
	return ranked_rows


func _score_row_before(left: Dictionary, right: Dictionary) -> bool:
	var left_score := int(left.get("score", 0))
	var right_score := int(right.get("score", 0))
	if left_score != right_score:
		return left_score > right_score
	return int(left.get("order", 0)) < int(right.get("order", 0))


func _score_rank_label(index: int, rows: Array[Dictionary]) -> String:
	if index > 0 and int(rows[index].get("score", 0)) == int(rows[index - 1].get("score", 0)):
		return " = "
	match index:
		0:
			return "1st"
		1:
			return "2nd"
		2:
			return "3rd"
		_:
			return "%dth" % (index + 1)


func _score_round_detail_for(owner: String) -> String:
	return str(_score_round_details.get(owner, "-"))


func _score_defeated_icons_for(owner: String) -> Array[Dictionary]:
	var icons: Array[Dictionary] = []
	for defeated_variant in Array(_round_defeats.get(owner, [])):
		var defeated_owner := str(defeated_variant)
		var index := _participant_index_for_owner(defeated_owner)
		if index < 0:
			continue
		var participant: Dictionary = _participants[index]
		var color: Color = participant.get("color", Color.WHITE)
		var tank := participant.get("tank") as RefCounted
		if tank != null:
			color = tank.get("body_color")
		icons.append({
			"owner": defeated_owner,
			"name": _participant_name_for_owner(defeated_owner),
			"color": color,
			"leader": bool(participant.get("leader", false)),
		})
	return icons


func _unique_score_leader() -> String:
	var rows := _participant_rows_snapshot()
	if rows.is_empty():
		return ""
	rows.sort_custom(_score_row_before)
	if rows.size() > 1 and int(rows[0].get("score", 0)) == int(rows[1].get("score", 0)):
		return ""
	return _participant_owner_for_index(int(rows[0].get("order", 0)))


func _participant_owner_for_index(index: int) -> String:
	if index == 0:
		return TURN_PLAYER
	if index == 1:
		return TURN_ENEMY
	return "Slot %d" % (index + 1)


func _participant_name_for_owner(owner: String) -> String:
	var index := _participant_index_for_owner(owner)
	if index >= 0 and index < _participants.size():
		return str(_participants[index].get("name", _default_participant_name(index)))
	if owner.begins_with("Slot "):
		var slot_number := int(owner.trim_prefix("Slot "))
		var participant_index := slot_number - 1
		if participant_index >= 0 and participant_index < _participants.size():
			return str(_participants[participant_index].get("name", _default_participant_name(participant_index)))
	return owner


func _score_leader_summary() -> String:
	var leader := _unique_score_leader()
	if leader.is_empty():
		return "No unique leader"
	var rows := _score_rows_snapshot()
	if rows.is_empty():
		return "No unique leader"
	return "Leader %s %d" % [_participant_name_for_owner(leader), int(rows[0].get("score", 0))]


func _participant_count() -> int:
	return _participant_rows_snapshot().size()


func _participant_top_score() -> int:
	var rows := _score_rows_snapshot()
	if rows.is_empty():
		return 0
	return int(rows[0].get("score", 0))


func _participant_hud_summary() -> String:
	var total := _participants.size()
	var living := _living_participant_count()
	var leader := _unique_score_leader()
	var leader_name := "No leader" if leader.is_empty() else _participant_name_for_owner(leader)
	return "Alive %d/%d  Lead %s" % [living, total, leader_name]


func _score_activation_delay() -> float:
	return SCORE_HUMAN_ACTIVATION_DELAY if _has_human_participants() else SCORE_COMPUTER_ACTIVATION_DELAY


func _winner_activation_delay() -> float:
	return WINNER_HUMAN_ACTIVATION_DELAY if _has_human_participants() else WINNER_COMPUTER_ACTIVATION_DELAY


func _tank_name_for_owner(owner: String) -> String:
	if owner == TURN_ENEMY:
		return _enemy.name
	if owner == TURN_PLAYER:
		return _player.name
	return _participant_name_for_owner(owner)


func _hide_score_overlay() -> void:
	if _score_overlay != null:
		_score_overlay.visible = false
	_score_title = ""
	_score_reward = 0
	_score_round_winner = ""
	_score_defeated_name = ""
	_score_defeated_was_leader = false
	_score_round_details.clear()
	_score_round_credits.clear()
	_score_continue_delay = 0.0


func _continue_from_score() -> void:
	if _phase != PHASE_SCORE:
		return
	if _score_continue_delay > 0.0:
		return
	_update_leader_flags()
	if _is_final_round():
		_hide_score_overlay()
		_open_winner_overlay()
		return
	var title := _score_title
	var reward := _score_reward
	_hide_score_overlay()
	_open_post_round_shop(title, reward, false)


func _open_post_round_shop(title: String, reward: int, award_credits := true) -> void:
	_reset_machine_gun_fire()
	_shop_title = title
	_shop_reward = reward
	if award_credits:
		_credits += reward
	_prepare_shop_pass()
	_phase = PHASE_SHOP
	_shop_input_delay = SHOP_INITIAL_INPUT_DELAY
	_ai_timer = 0.0
	_stop_quake_audio()
	_message = "%s. Spend credits or continue." % title
	if not _complete_computer_shop_passes():
		_finish_shop_and_start_next_round()
		return
	_refresh_shop_overlay()


func _refresh_shop_overlay() -> void:
	if _shop_overlay == null:
		return
	var shopper_index := _current_shop_participant_index()
	_shop_overlay.visible = true
	_shop_overlay.refresh({
		"title": _shop_title,
		"round": min(_round + 1, _total_rounds),
		"total_rounds": _total_rounds,
		"score": _participant_score(shopper_index),
		"reward": _shop_reward,
		"shopper_name": _shop_participant_name(shopper_index),
		"credits": _shop_credits(shopper_index),
		"fuel_reserve": int(round(_shop_fuel_reserve(shopper_index) * 100.0)),
		"inventory": _shop_inventory(shopper_index).inventory_snapshot(),
		"shop_items": _shop_items_snapshot(),
		"message": _message,
		"input_locked": _shop_input_delay > 0.0,
	})
	_update_hud()


func _hide_shop_overlay() -> void:
	if _shop_overlay != null:
		_shop_overlay.visible = false
	_shop_title = ""
	_shop_reward = 0
	_shop_participant_indices.clear()
	_shop_participant_cursor = 0
	_shop_input_delay = 0.0


func _buy_shop_weapon(weapon_name: String) -> void:
	if _shop_input_delay > 0.0:
		return
	_shop_input_delay = SHOP_ACTION_INPUT_DELAY
	if weapon_name == SHOP_JUMP_JET:
		_buy_jump_jet()
		return
	var shopper_index := _current_shop_participant_index()
	var inventory := _shop_inventory(shopper_index)
	var credits := _shop_credits(shopper_index)
	var cost: int = int(inventory.call("weapon_cost", weapon_name))
	if cost <= 0:
		_message = "%s is already stocked." % weapon_name
		_refresh_shop_overlay()
		return
	if credits < cost:
		_message = "Need $%d for %s." % [cost, weapon_name]
		_refresh_shop_overlay()
		return
	_set_shop_credits(shopper_index, credits - cost)
	var ammo_count: int = int(inventory.call("add_ammo", weapon_name))
	_message = "Bought %s ammo. Ammo now %s." % [weapon_name, str(ammo_count)]
	_refresh_shop_overlay()


func _buy_jump_jet() -> void:
	var shopper_index := _current_shop_participant_index()
	var credits := _shop_credits(shopper_index)
	if credits < SHOP_JUMP_JET_COST:
		_message = "Need $%d for %s." % [SHOP_JUMP_JET_COST, SHOP_JUMP_JET]
		_refresh_shop_overlay()
		return
	_set_shop_credits(shopper_index, credits - SHOP_JUMP_JET_COST)
	var fuel_reserve: float = _add_shop_fuel_reserve(shopper_index, TankState.TANK_FUEL_PURCHASE_AMOUNT)
	_message = "Bought %s. Fuel reserve now %d%%." % [SHOP_JUMP_JET, int(round(fuel_reserve * 100.0))]
	_refresh_shop_overlay()


func _shop_items_snapshot() -> Array[Dictionary]:
	var shopper_index := _current_shop_participant_index()
	return [
		{
				"name": SHOP_JUMP_JET,
				"cost": SHOP_JUMP_JET_COST,
				"effect": "+%d%% reserve" % int(round(TankState.TANK_FUEL_PURCHASE_AMOUNT * 100.0)),
				"current": "%d%% reserve" % int(round(_shop_fuel_reserve(shopper_index) * 100.0)),
			},
		]


func _continue_from_shop() -> void:
	if _shop_input_delay > 0.0:
		return
	_shop_input_delay = SHOP_ACTION_INPUT_DELAY
	if _advance_shop_participant():
		if not _complete_computer_shop_passes():
			_finish_shop_and_start_next_round()
			return
		_message = "%s is shopping." % _shop_participant_name(_current_shop_participant_index())
		_refresh_shop_overlay()
		return
	_finish_shop_and_start_next_round()


func _finish_shop_and_start_next_round() -> void:
	_hide_score_overlay()
	_hide_shop_overlay()
	_hide_winner_overlay()
	_round += 1
	_roll_round_wind()
	_terrain_seed += 17
	_reset_quake_cycle()
	_reset_machine_gun_fire()
	_stop_missile_flight_audio()
	_projectiles.clear()
	_explosions.clear()
	_smoke_particles.clear()
	_round_defeats.clear()
	_rebuild_terrain_if_needed(true)
	_start_round_turn("Round %d ready." % _round)
	_update_hud()


func _prepare_shop_pass() -> void:
	_shop_participant_indices.clear()
	for index in range(_participants.size()):
		_shop_participant_indices.append(index)
	_shop_participant_cursor = 0


func _current_shop_participant_index() -> int:
	if _shop_participant_indices.is_empty():
		return 0
	return _shop_participant_indices[clamp(_shop_participant_cursor, 0, _shop_participant_indices.size() - 1)]


func _advance_shop_participant() -> bool:
	if _shop_participant_indices.is_empty():
		return false
	if _shop_participant_cursor + 1 >= _shop_participant_indices.size():
		return false
	_shop_participant_cursor += 1
	return true


func _complete_computer_shop_passes() -> bool:
	while not _shop_participant_indices.is_empty():
		var shopper_index := _current_shop_participant_index()
		if _participant_is_human(shopper_index):
			return true
		_run_computer_shop_for_participant(shopper_index)
		if not _advance_shop_participant():
			return false
	return false


func _run_computer_shop_for_participant(index: int) -> void:
	var inventory := _shop_inventory(index)
	if inventory == null:
		return
	var credits := _shop_credits(index)
	var purchases: Array[String] = []
	for item_name in _computer_shop_priority():
		if item_name == SHOP_JUMP_JET:
			if credits >= SHOP_JUMP_JET_COST and _shop_fuel_reserve(index) <= TankState.TANK_FULL_FUEL:
				credits -= SHOP_JUMP_JET_COST
				_set_shop_credits(index, credits)
				_add_shop_fuel_reserve(index, TankState.TANK_FUEL_PURCHASE_AMOUNT)
				purchases.append(SHOP_JUMP_JET)
			continue
		var cost: int = int(inventory.call("weapon_cost", item_name))
		if cost <= 0 or credits < cost:
			continue
		credits -= cost
		_set_shop_credits(index, credits)
		inventory.call("add_ammo", item_name)
		purchases.append(item_name)
	if purchases.is_empty():
		_message = "%s saved credits." % _shop_participant_name(index)
	else:
		_message = "%s bought %s." % [_shop_participant_name(index), ", ".join(purchases)]


func _computer_shop_priority() -> Array:
	if _ai_difficulty == AI_DIFFICULTY_EASY:
		return AI_SHOP_PRIORITY_EASY.duplicate()
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return AI_SHOP_PRIORITY_HARD.duplicate()
	return AI_SHOP_PRIORITY_NORMAL.duplicate()


func _shop_participant_name(index: int) -> String:
	if index >= 0 and index < _participants.size():
		return str(_participants[index].get("name", _default_participant_name(index)))
	return _default_participant_name(index)


func _shop_inventory(index: int) -> RefCounted:
	if index >= 0 and index < _participants.size():
		return _participants[index].get("inventory") as RefCounted
	return _inventory


func _shop_credits(index: int) -> int:
	if index == 0:
		return _credits
	if index >= 0 and index < _participants.size():
		return int(_participants[index].get("credits", 0))
	return 0


func _set_shop_credits(index: int, value: int) -> void:
	if index == 0:
		_credits = value
	if index < 0 or index >= _participants.size():
		return
	var participant: Dictionary = _participants[index]
	participant["credits"] = value
	_participants[index] = participant


func _shop_fuel_reserve(index: int) -> float:
	if index >= 0 and index < _participants.size():
		var participant: Dictionary = _participants[index]
		var tank := participant.get("tank") as RefCounted
		if tank != null:
			return float(tank.get("fuel_reserve"))
		return float(participant.get("fuel_reserve", TankState.TANK_FULL_FUEL))
	return TankState.TANK_FULL_FUEL


func _add_shop_fuel_reserve(index: int, amount: float) -> float:
	if index < 0 or index >= _participants.size():
		return TankState.TANK_FULL_FUEL
	var participant: Dictionary = _participants[index]
	var tank := participant.get("tank") as RefCounted
	var fuel_reserve := TankState.TANK_FULL_FUEL
	if tank != null:
		fuel_reserve = float(tank.call("add_fuel_reserve", amount))
	else:
		fuel_reserve = float(participant.get("fuel_reserve", TankState.TANK_FULL_FUEL)) + amount
	participant["fuel_reserve"] = fuel_reserve
	_participants[index] = participant
	return fuel_reserve


func _is_final_round() -> bool:
	return _round >= _total_rounds


func _open_winner_overlay() -> void:
	_reset_machine_gun_fire()
	_hide_shop_overlay()
	_phase = PHASE_WINNER
	_winner_continue_delay = _winner_activation_delay()
	_winner_spin_phase = 0.0
	_ai_timer = 0.0
	_stop_quake_audio()
	_message = "Final result ready."
	_refresh_winner_overlay()


func _refresh_winner_overlay() -> void:
	if _winner_overlay == null:
		return
	_winner_overlay.visible = true
	var leader := _unique_score_leader()
	_winner_title_label.text = "It's a tie!" if leader.is_empty() else "We have a winner!"
	_winner_summary_label.text = ""
	_winner_summary_label.visible = false
	_rebuild_winner_cards()
	_rebuild_winner_rows()
	_refresh_winner_continue_button()
	_update_hud()


func _refresh_winner_continue_button() -> void:
	if _winner_main_menu_button != null:
		_winner_main_menu_button.disabled = _winner_continue_delay > 0.0
		_winner_main_menu_button.visible = false
		_winner_main_menu_button.focus_mode = Control.FOCUS_NONE


func _rebuild_winner_cards() -> void:
	if _winner_cards_container == null:
		return
	for child in _winner_cards_container.get_children():
		_winner_cards_container.remove_child(child)
		child.queue_free()
	for row_data in _winner_card_rows(_winner_card_snapshots()):
		var row := HBoxContainer.new()
		row.alignment = BoxContainer.ALIGNMENT_CENTER
		row.add_theme_constant_override("separation", 18)
		_winner_cards_container.add_child(row)
		for card_data in Array(row_data):
			row.add_child(_winner_card(Dictionary(card_data)))


func _winner_card_rows(cards: Array) -> Array:
	var rows: Array = []
	var index := 0
	while index < cards.size():
		var row: Array[Dictionary] = []
		for offset in range(4):
			var card_index := index + offset
			if card_index >= cards.size():
				break
			row.append(Dictionary(cards[card_index]))
		rows.append(row)
		index += 4
	return rows


func _winner_card(card_data: Dictionary) -> VBoxContainer:
	var card := VBoxContainer.new()
	card.custom_minimum_size = Vector2(136.0, 104.0)
	card.alignment = BoxContainer.ALIGNMENT_CENTER
	card.add_theme_constant_override("separation", 4)
	card.add_child(_winner_tank_chip(card_data.get("color", Color.WHITE)))
	card.add_child(_winner_card_label(str(card_data.get("name", "")), 15, GroundfireTheme.COLOR_TEXT))
	card.add_child(_winner_letter_ring())
	return card


func _winner_letter_ring() -> Control:
	var ring := Control.new()
	ring.name = "WinnerLetterRing"
	ring.custom_minimum_size = Vector2(136.0, 56.0)
	ring.set_meta("winner_spin_ring", true)
	for index in range(WINNER_SPIN_TEXT.length()):
		var letter := _winner_card_label(WINNER_SPIN_TEXT.substr(index, 1), 18, GroundfireTheme.COLOR_TEXT)
		letter.name = "WinnerLetter%d" % index
		letter.custom_minimum_size = Vector2(22.0, 22.0)
		letter.size = Vector2(22.0, 22.0)
		letter.pivot_offset = Vector2(11.0, 11.0)
		letter.set_meta("winner_spin_index", index)
		ring.add_child(letter)
	_refresh_winner_letter_ring(ring)
	return ring


func _winner_tank_chip(color: Color) -> Control:
	var chip := Control.new()
	chip.custom_minimum_size = Vector2(112.0, 50.0)
	var tank_shape := Polygon2D.new()
	tank_shape.polygon = PackedVector2Array([
		Vector2(8.0, 38.0),
		Vector2(32.0, 12.0),
		Vector2(80.0, 12.0),
		Vector2(104.0, 38.0),
	])
	tank_shape.color = color
	chip.add_child(tank_shape)
	return chip


func _winner_card_label(text: String, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.custom_minimum_size = Vector2(136.0, 22.0)
	GroundfireTheme.apply_label(label, font_size, color)
	return label


func _update_winner_spin(delta: float) -> void:
	if _phase != PHASE_WINNER or _winner_overlay == null or not _winner_overlay.visible:
		return
	_winner_spin_phase -= delta * WINNER_SPIN_SPEED
	_refresh_winner_letter_rings()


func _update_winner_background(delta: float) -> void:
	if _phase != PHASE_WINNER or _winner_overlay == null or not _winner_overlay.visible:
		return
	_winner_background_scroll += delta * WINNER_BACKGROUND_SCROLL_SPEED
	while _winner_background_scroll > 1.0:
		_winner_background_scroll -= 1.0
	_apply_winner_background_scroll()


func _apply_winner_background_scroll() -> void:
	if _winner_background == null:
		return
	var tile_size := MENU_TILE.get_size()
	if tile_size.x <= 0 or tile_size.y <= 0:
		return
	var offset := Vector2(
		float(int(_winner_background_scroll * float(tile_size.x))),
		float(int(_winner_background_scroll * float(tile_size.y)))
	)
	_winner_background.offset_left = -offset.x
	_winner_background.offset_top = -offset.y
	_winner_background.offset_right = float(tile_size.x) - offset.x
	_winner_background.offset_bottom = float(tile_size.y) - offset.y


func _refresh_winner_letter_rings() -> void:
	if _winner_cards_container == null:
		return
	for row_variant in _winner_cards_container.get_children():
		var row_node := row_variant as Node
		if row_node == null:
			continue
		for card_variant in row_node.get_children():
			var card_node := card_variant as Node
			if card_node == null:
				continue
			var ring := card_node.get_node_or_null("WinnerLetterRing") as Control
			if ring != null:
				_refresh_winner_letter_ring(ring)


func _refresh_winner_letter_ring(ring: Control) -> void:
	var center := Vector2(68.0, 28.0)
	for letter_variant in ring.get_children():
		var letter := letter_variant as Label
		if letter == null:
			continue
		var index := int(letter.get_meta("winner_spin_index", 0))
		var angle := _winner_spin_phase - float(index) * WINNER_SPIN_LETTER_SPACING
		letter.position = center + Vector2(cos(angle), sin(angle)) * WINNER_SPIN_RADIUS - Vector2(11.0, 11.0)
		letter.rotation = angle - PI * 0.5


func _rebuild_winner_rows() -> void:
	if _winner_rows_container == null:
		return
	for child in _winner_rows_container.get_children():
		_winner_rows_container.remove_child(child)
		child.queue_free()
	# Pygame WinnerMenu shows only winner cards; keep row data internal for winner selection.
	_winner_rows_container.visible = false


func _winner_rows_snapshot() -> Array[Dictionary]:
	var rows := _score_rows_snapshot()
	var top_score := _participant_top_score()
	for row in rows:
		row["round_detail"] = "-"
		row["winner"] = int(row.get("score", 0)) == top_score
	return rows


func _winner_card_snapshots() -> Array[Dictionary]:
	var cards: Array[Dictionary] = []
	for row in _winner_rows_snapshot():
		var row_data: Dictionary = row
		if bool(row_data.get("winner", false)):
			cards.append(row_data.duplicate())
	return cards


func _hide_winner_overlay() -> void:
	if _winner_overlay != null:
		_winner_overlay.visible = false
	_winner_continue_delay = 0.0


func _spawn_explosion(position: Vector2, crater_radius: float, white_out := false) -> void:
	_terrain.apply_crater(position, crater_radius)
	for participant_data in _participants:
		var participant: Dictionary = participant_data
		var tank := participant.get("tank") as RefCounted
		if tank != null:
			tank.call("settle_on_terrain", _terrain)
	_add_camera_shake(crater_radius)
	var life := 0.55
	if white_out:
		_play_nuke_audio()
		life = max(life, 1.0 / NUKE_WHITEOUT_FADE_RATE)
	_explosions.append({
		"position": position,
		"radius": 8.0,
		"life": life,
		"crater_radius": crater_radius,
		"white_out": white_out,
		"white_out_level": 1.0 if white_out else 0.0,
	})


func _update_explosions(delta: float) -> void:
	for explosion in _explosions:
		explosion["life"] = float(explosion["life"]) - delta
		explosion["radius"] = float(explosion["radius"]) + 120.0 * delta
		if bool(explosion.get("white_out", false)):
			var whiteout_level: float = max(0.0, float(explosion.get("white_out_level", 0.0)) - delta * NUKE_WHITEOUT_FADE_RATE)
			explosion["white_out_level"] = whiteout_level
			if whiteout_level <= 0.0:
				explosion["white_out"] = false
	_explosions = _explosions.filter(func(explosion: Dictionary) -> bool: return float(explosion["life"]) > 0.0)


func _update_smoke_particles(delta: float) -> void:
	for smoke in _smoke_particles:
		smoke["rotation"] = float(smoke.get("rotation", 0.0)) + delta * float(smoke.get("rotation_rate", 0.0))
		smoke["size"] = float(smoke.get("size", 0.25)) + delta * float(smoke.get("growth_rate", 0.0))
		smoke["fade"] = float(smoke.get("fade", 0.7)) - delta * float(smoke.get("fade_rate", 0.0))
		smoke["position"] = Vector2(smoke.get("position", Vector2.ZERO)) + Vector2(smoke.get("velocity", Vector2.ZERO)) * delta
	_smoke_particles = _smoke_particles.filter(func(smoke: Dictionary) -> bool: return float(smoke.get("fade", 0.0)) >= 0.0)


func _update_tank_burn_smoke(delta: float) -> void:
	for participant_data in _participants:
		var participant: Dictionary = participant_data
		var tank := participant.get("tank") as RefCounted
		if tank == null or str(tank.get("state")) != TankState.STATE_DEAD:
			continue
		_emit_tank_burn_smoke(tank, delta)


func _emit_tank_burn_smoke(tank: RefCounted, delta: float) -> void:
	var exhaust_time := float(tank.get("exhaust_time"))
	if exhaust_time < 0.0:
		var on_ground := bool(tank.get("on_ground"))
		var smoke_position := _tank_position(tank)
		if on_ground:
			smoke_position += Vector2(0.0, TankState.GROUND_SMOKE_Y_OFFSET * TankState.GUN_POWER_PIXEL_SCALE)
		_smoke_particles.append({
			"position": smoke_position,
			"velocity": Vector2(0.0, TankState.SMOKE_Y_VELOCITY * TankState.GUN_POWER_PIXEL_SCALE),
			"texture_id": TankState.SMOKE_TEXTURE_ID,
			"rotation": 0.0,
			"rotation_rate": TankState.SMOKE_ROTATION_RATE,
			"size": 0.25,
			"growth_rate": TankState.GROUND_SMOKE_GROWTH_RATE,
			"fade": 0.7,
			"fade_rate": TankState.GROUND_SMOKE_FADE_RATE if on_ground else TankState.AIR_SMOKE_FADE_RATE,
		})
		tank.set("exhaust_time", exhaust_time + (TankState.GROUND_SMOKE_RELEASE_TIME if on_ground else TankState.AIR_SMOKE_RELEASE_TIME))
	else:
		tank.set("exhaust_time", exhaust_time - delta)


func _emit_jump_jet_smoke(tank: RefCounted, delta: float) -> void:
	var exhaust_time := float(tank.get("exhaust_time"))
	if exhaust_time < 0.0:
		var tank_angle := float(tank.get("tank_angle"))
		var radians := deg_to_rad(tank_angle)
		var airborne_velocity := Vector2(tank.get("airborne_velocity"))
		_smoke_particles.append({
			"position": _tank_position(tank),
			"velocity": airborne_velocity + Vector2(
				sin(radians) * TankState.BOOST_SMOKE_VELOCITY * TankState.GUN_POWER_PIXEL_SCALE,
				-cos(radians) * TankState.BOOST_SMOKE_VELOCITY * TankState.GUN_POWER_PIXEL_SCALE
			),
			"texture_id": TankState.BOOST_SMOKE_TEXTURE_ID,
			"rotation": 0.0,
			"rotation_rate": TankState.BOOST_SMOKE_ROTATION_RATE,
			"size": 0.25,
			"growth_rate": TankState.BOOST_SMOKE_GROWTH_RATE,
			"fade": 0.7,
			"fade_rate": TankState.BOOST_SMOKE_FADE_RATE,
		})
		tank.set("exhaust_time", exhaust_time + TankState.BOOST_SMOKE_RELEASE_TIME)
	else:
		tank.set("exhaust_time", exhaust_time - delta)


func _draw() -> void:
	_draw_classic_sky()
	var camera_offset := _camera_offset + _camera_shake_offset
	draw_set_transform(-camera_offset * _camera_zoom, 0.0, Vector2(_camera_zoom, _camera_zoom))
	_draw_terrain()
	for index in range(_participants.size()):
		var participant: Dictionary = _participants[index]
		var tank := participant.get("tank") as RefCounted
		if tank != null:
			_draw_tank(tank, _participant_inventory(index))
	_draw_aim()
	_draw_mouse_reticle()
	for projectile in _projectiles:
		var projectile_position := Vector2(projectile["position"])
		if str(projectile.get("kind", "shell")) == "machine_gun":
			if float(projectile.get("delay", 0.0)) > 0.0:
				continue
			var back_position := Vector2(projectile.get("back_position", projectile.get("previous_position", projectile_position)))
			draw_line(back_position, projectile_position, Color.WHITE, 2.0)
		else:
			draw_circle(projectile_position, 5.0, GroundfireTheme.COLOR_WARN)
	for explosion in _explosions:
		var explosion_color := Color("#f59e0b66")
		if bool(explosion.get("white_out", false)):
			explosion_color = Color("#ffffff99")
		draw_circle(Vector2(explosion["position"]), float(explosion["radius"]), explosion_color)
	for smoke in _smoke_particles:
		_draw_smoke_particle(smoke)
	_draw_map_bounds()
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	_draw_whiteout_overlay()
	if _phase == PHASE_ROUND_OVER and _living_participant_count() <= 1:
		_draw_round_banner()


func _draw_smoke_particle(smoke: Dictionary) -> void:
	var fade: float = clamp(float(smoke.get("fade", 0.0)), 0.0, 1.0)
	if fade <= 0.0:
		return
	draw_polygon(
		_smoke_particle_draw_points(smoke),
		PackedColorArray([Color(1.0, 1.0, 1.0, fade)]),
		_smoke_particle_draw_uvs(),
		SMOKE_TEXTURE
	)


func _smoke_particle_draw_points(smoke: Dictionary) -> PackedVector2Array:
	var center: Vector2 = Vector2(smoke.get("position", Vector2.ZERO))
	var half_size: float = max(1.0, float(smoke.get("size", 0.25)) * TankState.TANK_BODY_HALF_WIDTH)
	var rotation: float = -float(smoke.get("rotation", 0.0))
	var axis_x: Vector2 = Vector2(cos(rotation), sin(rotation)) * half_size
	var axis_y: Vector2 = Vector2(-sin(rotation), cos(rotation)) * half_size
	return PackedVector2Array([
		center - axis_x - axis_y,
		center + axis_x - axis_y,
		center + axis_x + axis_y,
		center - axis_x + axis_y,
	])


func _smoke_particle_draw_uvs() -> PackedVector2Array:
	var texture_size := SMOKE_TEXTURE.get_size()
	return PackedVector2Array([
		Vector2.ZERO,
		Vector2(texture_size.x, 0.0),
		texture_size,
		Vector2(0.0, texture_size.y),
	])


func _draw_classic_sky() -> void:
	var band_count := 24
	for band in range(band_count):
		var ratio_top := float(band) / float(band_count)
		var ratio_bottom := float(band + 1) / float(band_count)
		var color := Color(0.6 * ratio_top, 0.0, 0.4)
		var top_y := size.y * ratio_top
		var bottom_y := size.y * ratio_bottom
		draw_rect(Rect2(0.0, top_y, size.x, max(1.0, bottom_y - top_y)), color)


func _draw_whiteout_overlay() -> void:
	var alpha := _whiteout_alpha()
	if alpha <= 0.0:
		return
	draw_rect(Rect2(Vector2.ZERO, size), Color(1.0, 1.0, 1.0, clamp(alpha, 0.0, 1.0)))


func _whiteout_alpha() -> float:
	var alpha := 0.0
	for explosion in _explosions:
		if bool(explosion.get("white_out", false)):
			alpha = max(alpha, float(explosion.get("white_out_level", 0.0)))
	return alpha


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
	pass


func _draw_tank(tank: RefCounted, inventory: RefCounted = null) -> void:
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
	if str(tank.get("state")) == TankState.STATE_ALIVE:
		if bool(tank.get("shield_active")):
			_draw_tank_shield(tank)
		_draw_tank_gun_arrow(tank, inventory)


func _draw_tank_shield(tank: RefCounted) -> void:
	var center: Vector2 = tank.position + Vector2(0.0, -12.0)
	draw_circle(center, 43.0, Color("#7dd3fc22"))
	draw_arc(center, 43.0, 0.0, TAU, 48, Color("#7dd3fccc"), 3.0)


func _draw_tank_gun_arrow(tank: RefCounted, inventory: RefCounted) -> void:
	var geometry := _tank_gun_arrow_geometry(tank)
	var arrow_color := Color("#00ff0080") if _tank_weapon_ready(inventory) else Color("#ff000080")
	draw_colored_polygon(PackedVector2Array(geometry.get("shaft_polygon", PackedVector2Array())), arrow_color)
	draw_colored_polygon(PackedVector2Array(geometry.get("head_polygon", PackedVector2Array())), arrow_color)


func _tank_gun_arrow_geometry(tank: RefCounted) -> Dictionary:
	var center: Vector2 = tank.call("tank_center") if tank.has_method("tank_center") else tank.position
	var direction := _gun_direction_for_angle(float(tank.get("gun_angle")))
	var normal := Vector2(-direction.y, direction.x)
	var arrow_length := TANK_GUN_ARROW_BASE_LENGTH + float(tank.get("gun_power")) * TANK_GUN_ARROW_POWER_SCALE
	var shaft_start := center + direction * TANK_GUN_ARROW_START_OFFSET
	var shaft_end := center + direction * arrow_length
	var head_tip := center + direction * (arrow_length * TANK_GUN_ARROW_HEAD_TIP_SCALE)
	return {
		"center": center,
		"direction": direction,
		"start_offset": TANK_GUN_ARROW_START_OFFSET,
		"arrow_length": arrow_length,
		"shaft_start": shaft_start,
		"shaft_end": shaft_end,
		"head_tip": head_tip,
		"shaft_polygon": PackedVector2Array([
			shaft_start - normal * TANK_GUN_ARROW_SHAFT_HALF_WIDTH,
			shaft_end - normal * TANK_GUN_ARROW_SHAFT_HALF_WIDTH,
			shaft_end + normal * TANK_GUN_ARROW_SHAFT_HALF_WIDTH,
			shaft_start + normal * TANK_GUN_ARROW_SHAFT_HALF_WIDTH,
		]),
		"head_polygon": PackedVector2Array([
			shaft_end - normal * TANK_GUN_ARROW_HEAD_HALF_WIDTH,
			head_tip,
			shaft_end + normal * TANK_GUN_ARROW_HEAD_HALF_WIDTH,
		]),
	}


func _tank_weapon_ready(inventory: RefCounted) -> bool:
	return inventory == null or int(inventory.call("current_ammo")) != 0


func _transform_tank_point(local: Vector2, tank: RefCounted) -> Vector2:
	var radians := deg_to_rad(tank.tank_angle)
	return tank.position + Vector2(
		local.x * cos(radians) - local.y * sin(radians),
		local.x * sin(radians) + local.y * cos(radians)
	)


func _draw_aim() -> void:
	pass


func _draw_mouse_reticle() -> void:
	if not _mouse_aim_enabled or not _participant_is_human(_turn_index) or _phase != PHASE_AIM:
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
	var active_tank := _turn_tank()
	var target_tank := _target_tank()
	if active_tank == null:
		active_tank = _player
	if target_tank == null:
		target_tank = _enemy
	var active_inventory := _turn_inventory()
	if active_inventory == null:
		active_inventory = _inventory
	_hud.set_snapshot({
		"round": _round,
		"phase": _phase,
		"turn": _turn_owner,
		"player_name": str(active_tank.get("name")),
		"enemy_name": str(target_tank.get("name")),
		"target_name": str(target_tank.get("name")),
		"player_hp": int(active_tank.get("health")),
		"enemy_hp": int(target_tank.get("health")),
		"target_hp": int(target_tank.get("health")),
		"player_fuel": int(float(active_tank.get("fuel")) * 100.0),
		"player_fuel_max": int(TankState.TANK_FULL_FUEL * 100.0),
		"player_fuel_reserve": int(round(float(active_tank.get("fuel_reserve")) * 100.0)),
		"angle": int(active_tank.get("gun_angle")),
		"power": int(active_tank.get("gun_power")),
		"wind": int(round(_wind)),
		"wind_effect": _wind_acceleration(0.0),
		"quake_active": _quake_active,
		"quake_countdown": _quake_countdown,
		"weapon": str(active_inventory.call("current_name")),
		"ammo": int(active_inventory.call("current_ammo")),
		"inventory": active_inventory.call("inventory_snapshot"),
		"score": _participant_score(_turn_index),
		"credits": _participant_credits(_turn_index),
		"player_wins": _participant_wins(_turn_index),
		"enemy_wins": _participant_wins(_target_index),
		"target_wins": _participant_wins(_target_index),
		"participant_summary": _participant_hud_summary(),
		"participants": _participant_rows_snapshot(),
		"active_index": _turn_index,
		"target_index": _target_index,
		"message": _message,
	})


func _cycle_weapon(direction := 1) -> void:
	if _phase != PHASE_AIM or not _participant_is_human(_turn_index):
		return
	_message = "Weapon selected: %s." % str(_turn_inventory().call("cycle", direction))


func _splash_damage(explosion_position: Vector2, target_position: Vector2, max_damage: int, radius: float) -> int:
	var distance_squared := explosion_position.distance_squared_to(target_position)
	var radius_squared := radius * radius
	if distance_squared > radius_squared:
		return 0
	var damage_multiplier := 1.0 - (distance_squared / radius_squared)
	if _terrain_blocks_splash(explosion_position, target_position):
		damage_multiplier *= SPLASH_OCCLUSION_MULTIPLIER
	return int(round(float(max_damage) * clamp(damage_multiplier, 0.0, 1.0)))


func _terrain_blocks_splash(explosion_position: Vector2, target_position: Vector2) -> bool:
	var distance := explosion_position.distance_to(target_position)
	if distance <= 1.0:
		return false
	var start := explosion_position.lerp(target_position, min(0.25, 12.0 / distance))
	return _terrain_hits_segment(start, target_position)


func _wind_acceleration(age := 0.0) -> float:
	var gust: float = sin(float(age) * WIND_GUST_FREQUENCY + _wind_gust) * abs(_wind_gust) * WIND_GUST_SCALE
	return clamp(_wind + gust, WIND_MIN, WIND_MAX)


func _wind_status() -> String:
	var magnitude: int = int(abs(round(_wind)))
	if magnitude == 0:
		return "Wind calm"
	if _wind > 0.0:
		return "Wind -> %d" % magnitude
	return "Wind <- %d" % magnitude


func _shift_wind_for_turn() -> void:
	_wind = clamp(_wind + _wind_rng.randf_range(-WIND_TURN_SHIFT, WIND_TURN_SHIFT), WIND_MIN, WIND_MAX)
	_wind_gust = _wind_rng.randf_range(-WIND_GUST_MAX, WIND_GUST_MAX)


func _roll_round_wind() -> void:
	_wind = _wind_rng.randf_range(WIND_MIN, WIND_MAX)
	_wind_gust = _wind_rng.randf_range(-WIND_GUST_MAX, WIND_GUST_MAX)


func _update_quake(delta: float) -> void:
	if _phase == PHASE_SHOP or _phase == PHASE_SCORE or _phase == PHASE_WINNER or _phase == PHASE_ROUND_OVER:
		_stop_quake_audio()
		return
	_quake_countdown -= delta
	if _quake_active:
		_play_quake_audio()
		_terrain.drop_terrain(delta * QUAKE_DROP_RATE)
		_add_camera_shake(QUAKE_CAMERA_SHAKE)
		_message = "Quake! Terrain dropping."
		if _quake_countdown < 0.0:
			_quake_active = false
			_quake_countdown = QUAKE_TIME_BETWEEN
			_stop_quake_audio()
			_message = "Quake settled. %s." % _wind_status()
	elif _quake_countdown < 0.0:
		_quake_active = true
		_quake_countdown = QUAKE_DURATION
		_play_quake_audio()
		_message = "Quake! Terrain dropping."


func _play_quake_audio() -> void:
	if _quake_audio == null or _is_paused:
		return
	if not _quake_audio.playing:
		_quake_audio.play()


func _prepare_for_shutdown() -> void:
	_shutting_down = true
	set_process(false)
	_stop_all_audio()
	_release_audio_stream(_quake_audio)
	_release_audio_stream(_jump_jets_audio)
	_release_audio_stream(_fire_shell_audio)
	_release_audio_stream(_shell_death_audio)
	_release_audio_stream(_launch_missile_audio)
	_release_audio_stream(_missile_flight_audio)
	_release_audio_stream(_missile_death_audio)
	_release_audio_stream(_machine_gun_audio)
	_release_audio_stream(_metal_hit_audio)
	_release_audio_stream(_nuke_audio)


func _stop_all_audio() -> void:
	_stop_quake_audio()
	_stop_jump_jets_audio()
	_stop_fire_shell_audio()
	_stop_shell_death_audio()
	_stop_launch_missile_audio()
	_stop_missile_flight_audio()
	_stop_missile_death_audio()
	_stop_machine_gun_audio()
	_stop_metal_hit_audio()
	_stop_nuke_audio()


func _release_audio_stream(player: AudioStreamPlayer) -> void:
	if player == null:
		return
	player.stream_paused = false
	player.stop()
	player.stream = null


func _stop_quake_audio() -> void:
	if _quake_audio != null and _quake_audio.playing:
		_quake_audio.stop()


func _play_jump_jets_audio() -> void:
	_jump_jets_active = true
	if _jump_jets_audio == null or _is_paused:
		return
	if not _jump_jets_audio.playing:
		_jump_jets_audio.play()


func _stop_jump_jets_audio() -> void:
	_jump_jets_active = false
	if _jump_jets_audio != null and _jump_jets_audio.playing:
		_jump_jets_audio.stop()


func _play_fire_shell_audio() -> void:
	if _fire_shell_audio == null or _is_paused:
		return
	_fire_shell_audio.stop()
	_fire_shell_audio.play()


func _stop_fire_shell_audio() -> void:
	if _fire_shell_audio != null and _fire_shell_audio.playing:
		_fire_shell_audio.stop()


func _play_shell_death_audio() -> void:
	if _shell_death_audio == null or _is_paused:
		return
	_shell_death_audio.stop()
	_shell_death_audio.play()


func _stop_shell_death_audio() -> void:
	if _shell_death_audio != null and _shell_death_audio.playing:
		_shell_death_audio.stop()


func _play_launch_missile_audio() -> void:
	if _launch_missile_audio == null or _is_paused:
		return
	_launch_missile_audio.stop()
	_launch_missile_audio.play()


func _stop_launch_missile_audio() -> void:
	if _launch_missile_audio != null and _launch_missile_audio.playing:
		_launch_missile_audio.stop()


func _play_missile_flight_audio() -> void:
	if _missile_flight_audio == null or _is_paused:
		return
	if not _missile_flight_audio.playing:
		_missile_flight_audio.play()


func _stop_missile_flight_audio() -> void:
	if _missile_flight_audio != null and _missile_flight_audio.playing:
		_missile_flight_audio.stop()


func _play_missile_death_audio() -> void:
	if _missile_death_audio == null or _is_paused:
		return
	_missile_death_audio.stop()
	_missile_death_audio.play()


func _stop_missile_death_audio() -> void:
	if _missile_death_audio != null and _missile_death_audio.playing:
		_missile_death_audio.stop()


func _sync_missile_flight_audio() -> void:
	if _has_fueled_missile_projectile():
		_play_missile_flight_audio()
	else:
		_stop_missile_flight_audio()


func _has_fueled_missile_projectile() -> bool:
	for projectile in _projectiles:
		if str(projectile.get("kind", "shell")) == "missile" and float(projectile.get("fuel", -1.0)) >= 0.0:
			return true
	return false


func _play_machine_gun_audio() -> void:
	if _machine_gun_audio == null or _is_paused:
		return
	if not _machine_gun_audio.playing:
		_machine_gun_audio.play()


func _stop_machine_gun_audio() -> void:
	if _machine_gun_audio != null and _machine_gun_audio.playing:
		_machine_gun_audio.stop()


func _play_metal_hit_audio() -> void:
	if _metal_hit_audio == null or _is_paused:
		return
	_metal_hit_audio.stop()
	_metal_hit_audio.play()


func _stop_metal_hit_audio() -> void:
	if _metal_hit_audio != null and _metal_hit_audio.playing:
		_metal_hit_audio.stop()


func _play_nuke_audio() -> void:
	if _nuke_audio == null or _is_paused:
		return
	_nuke_audio.stop()
	_nuke_audio.play()


func _stop_nuke_audio() -> void:
	if _nuke_audio != null and _nuke_audio.playing:
		_nuke_audio.stop()


func _reset_quake_cycle(countdown := QUAKE_TIME_TILL_FIRST) -> void:
	_quake_active = false
	_quake_countdown = countdown
	_stop_quake_audio()


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
	var subjects: Array[Vector2] = []
	for participant_data in _participants:
		var participant: Dictionary = participant_data
		var tank := participant.get("tank") as RefCounted
		if tank != null:
			subjects.append(_tank_position(tank))
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
		for index in range(_participants.size()):
			var participant: Dictionary = _participants[index]
			var tank := participant.get("tank") as RefCounted
			if tank == null:
				continue
			tank.call(
				"reset_round",
				_round_spawn_x(index, _participants.size()),
				_terrain,
				str(participant.get("name", _default_participant_name(index))),
				participant.get("color", _default_participant_color(index))
			)
		_camera_ready = false


func _round_spawn_x(index: int, count: int) -> float:
	if count <= 2:
		return _world_size.x * (0.22 if index == 0 else 0.76)
	return _world_size.x * (float(index + 1) / float(count + 1))


func _load_gameplay_options() -> void:
	var config := ConfigFile.new()
	if config.load(OPTIONS_PATH) != OK:
		return
	_screen_shake_enabled = bool(config.get_value("gameplay", "screen_shake", _screen_shake_enabled))
	_camera_smoothing = clamp(float(config.get_value("gameplay", "camera_smoothing", _camera_smoothing)), 0.25, 1.75)
	_mouse_aim_enabled = bool(config.get_value("gameplay", "mouse_aim", _mouse_aim_enabled))
	_ai_difficulty = _normalized_ai_difficulty(str(config.get_value("gameplay", "ai_difficulty", _ai_difficulty)))


func _normalized_ai_difficulty(value: String) -> String:
	var normalized := value.to_lower()
	if normalized == AI_DIFFICULTY_EASY or normalized == AI_DIFFICULTY_HARD:
		return normalized
	return AI_DIFFICULTY_NORMAL


func _ai_angle_step() -> int:
	if _ai_difficulty == AI_DIFFICULTY_EASY:
		return 10
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return 3
	return 5


func _ai_power_step() -> int:
	if _ai_difficulty == AI_DIFFICULTY_EASY:
		return 2
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return 1
	return 1


func _ai_angle_error() -> float:
	if _ai_difficulty == AI_DIFFICULTY_EASY:
		return 7.0
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return 0.75
	return 2.0


func _ai_power_error() -> float:
	if _ai_difficulty == AI_DIFFICULTY_EASY:
		return 1.75
	if _ai_difficulty == AI_DIFFICULTY_HARD:
		return 0.25
	return 0.75


func _wire_vertical_focus(buttons: Array[Button]) -> void:
	if buttons.size() == 1:
		_wire_single_button_focus(buttons[0])
		return
	if buttons.size() < 2:
		return
	for index in range(buttons.size()):
		var button := buttons[index]
		var previous := buttons[wrapi(index - 1, 0, buttons.size())]
		var next := buttons[wrapi(index + 1, 0, buttons.size())]
		var path := button.get_path()
		button.focus_neighbor_top = previous.get_path()
		button.focus_neighbor_bottom = next.get_path()
		button.focus_neighbor_left = path
		button.focus_neighbor_right = path


func _wire_single_button_focus(button: Button) -> void:
	var path := button.get_path()
	button.focus_neighbor_top = path
	button.focus_neighbor_bottom = path
	button.focus_neighbor_left = path
	button.focus_neighbor_right = path
