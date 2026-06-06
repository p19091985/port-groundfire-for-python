extends SceneTree

const LocalMatchScene := preload("res://scenes/local_match.tscn")
const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const LocalMatchHud := preload("res://scripts/local_match_hud.gd")
const LocalMatchShop := preload("res://scripts/local_match_shop.gd")
const TankState := preload("res://scripts/tank_state.gd")
const TerrainModel := preload("res://scripts/terrain_model.gd")
const WeaponInventory := preload("res://scripts/weapon_inventory.gd")
const SHUTDOWN_DRAIN_FRAMES := 8


class FlatTerrain:
	extends RefCounted

	var ground_y := 100.0
	var slope_angle := 0.0
	var bounds := Vector2(30.0, 190.0)

	func height_at(_x: float) -> float:
		return ground_y

	func tank_position(x: float) -> Vector2:
		return Vector2(x, ground_y)

	func slope_angle_at(_x: float) -> float:
		return slope_angle

	func playable_bounds() -> Vector2:
		return bounds


class SlopedTerrain:
	extends FlatTerrain

	var origin := Vector2(0.0, 100.0)

	func _init(origin_x := 0.0, origin_y := 100.0, angle_degrees := 0.0) -> void:
		origin = Vector2(origin_x, origin_y)
		ground_y = origin_y
		slope_angle = angle_degrees

	func height_at(x: float) -> float:
		return origin.y + tan(deg_to_rad(slope_angle)) * (x - origin.x)

	func tank_position(x: float) -> Vector2:
		return Vector2(x, height_at(x))


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(1024, 768)
	var local_match := LocalMatchScene.instantiate()
	local_match.setup({"total_rounds": 5})
	root.add_child(local_match)
	await process_frame
	await process_frame

	var direct_damage := int(local_match.call("_splash_damage", Vector2(100.0, 100.0), Vector2(100.0, 100.0), 40, 50.0))
	var half_radius_damage := int(local_match.call("_splash_damage", Vector2(100.0, 100.0), Vector2(125.0, 100.0), 40, 50.0))
	var edge_damage := int(local_match.call("_splash_damage", Vector2(100.0, 100.0), Vector2(150.0, 100.0), 40, 50.0))
	var beyond_damage := int(local_match.call("_splash_damage", Vector2(100.0, 100.0), Vector2(151.0, 100.0), 40, 50.0))

	assert(direct_damage == 40)
	assert(half_radius_damage == 30)
	assert(edge_damage == 0)
	assert(beyond_damage == 0)
	assert(not bool(local_match.call("_terrain_blocks_splash", Vector2(100.0, 40.0), Vector2(100.0, 41.0))))
	var player_tank: RefCounted = local_match.get("_player")
	var enemy_tank: RefCounted = local_match.get("_enemy")
	player_tank.position = Vector2(120.0, 120.0)
	enemy_tank.position = Vector2(240.0, 120.0)
	assert(str(local_match.call("_segment_tank_hit_owner", Vector2(60.0, 102.0), Vector2(300.0, 102.0))) == "Player")
	assert(str(local_match.call("_segment_tank_hit_owner", Vector2(60.0, 102.0), Vector2(300.0, 102.0), "Player")) == "Enemy")
	assert(str(local_match.call("_segment_tank_hit_owner", Vector2(180.0, 102.0), Vector2(300.0, 102.0))) == "Enemy")
	assert(abs(float(local_match.call("_explosion_damage_for_target", Vector2(10.0, 10.0), Vector2(400.0, 400.0), 40, 4.0, "Enemy", "Enemy")) - 40.0) < 0.01)
	enemy_tank.health = TankState.TANK_MAX_HEALTH
	player_tank.health = TankState.TANK_MAX_HEALTH
	local_match.set("_score", 0)
	local_match.set("_enemy_score", 0)
	local_match.call(
		"_apply_explosion",
		enemy_tank.position + Vector2(0.0, -20.0),
		{"weapon": {"name": "Shell", "kind": "shell", "damage": 40, "blast": 1.0}, "player_owned": true},
		"Enemy"
	)
	assert(int(enemy_tank.health) == TankState.TANK_MAX_HEALTH - 40)
	assert(int(local_match.get("_score")) == 40)
	assert(int(local_match.get("_credits")) == 40)
	_clear_explosions(local_match)
	enemy_tank.health = TankState.TANK_MAX_HEALTH
	enemy_tank.shield_active = true
	local_match.set("_score", 0)
	local_match.set("_credits", 0)
	local_match.call(
		"_apply_explosion",
		enemy_tank.position + Vector2(0.0, -20.0),
		{"weapon": {"name": "Shell", "kind": "shell", "damage": 40, "blast": 1.0}, "player_owned": true},
		"Enemy"
	)
	assert(int(enemy_tank.health) == TankState.TANK_MAX_HEALTH - 20)
	assert(int(local_match.get("_score")) == 20)
	assert(int(local_match.get("_credits")) == 20)
	enemy_tank.shield_active = false
	_clear_explosions(local_match)
	local_match.set("_score", 0)
	local_match.set("_enemy_score", 0)
	player_tank.health = TankState.TANK_MAX_HEALTH
	local_match.call(
		"_apply_explosion",
		player_tank.position + Vector2(0.0, -20.0),
		{"weapon": {"name": "Shell", "kind": "shell", "damage": 40, "blast": 1.0}, "player_owned": false},
		"Player"
	)
	assert(int(player_tank.health) == TankState.TANK_MAX_HEALTH - 40)
	assert(int(local_match.get("_enemy_score")) == 40)
	_clear_explosions(local_match)

	var full_roster_match := LocalMatchScene.instantiate()
	full_roster_match.setup({
		"total_rounds": 5,
		"roster": [
			{"slot": 0, "name": "Pilot", "kind": "human", "controller": 0, "color": Color.RED},
			{"slot": 1, "name": "Gunner", "kind": "computer", "controller": -1, "color": Color.BLUE},
			{"slot": 2, "name": "Scout", "kind": "computer", "controller": -1, "color": Color.GREEN},
		],
	})
	root.add_child(full_roster_match)
	await process_frame
	await process_frame
	var roster_participants: Array = full_roster_match.get("_participants")
	var roster_player_tank: RefCounted = Dictionary(roster_participants[0]).get("tank") as RefCounted
	var roster_enemy_tank: RefCounted = Dictionary(roster_participants[1]).get("tank") as RefCounted
	var roster_scout_tank: RefCounted = Dictionary(roster_participants[2]).get("tank") as RefCounted
	roster_player_tank.position = Vector2(120.0, 180.0)
	roster_enemy_tank.position = Vector2(240.0, 180.0)
	roster_scout_tank.position = Vector2(360.0, 180.0)
	assert(str(full_roster_match.call("_segment_tank_hit_owner", Vector2(60.0, 162.0), Vector2(420.0, 162.0), "Player")) == "Enemy")
	assert(str(full_roster_match.call("_segment_tank_hit_owner", Vector2(300.0, 162.0), Vector2(420.0, 162.0), "Enemy")) == "Slot 3")
	full_roster_match.set("_score", 0)
	full_roster_match.set("_credits", 0)
	roster_scout_tank.health = TankState.TANK_MAX_HEALTH
	full_roster_match.call(
		"_apply_machine_gun_damage",
		{"weapon": {"name": "Machine Gun", "kind": "machine_gun", "damage": 2}, "owner": "Player"},
		"Slot 3"
	)
	assert(int(roster_scout_tank.health) == TankState.TANK_MAX_HEALTH - 2)
	assert(int(full_roster_match.get("_score")) == 2)
	assert(int(full_roster_match.get("_credits")) == 2)
	assert(str(full_roster_match.get("_message")).contains("Scout"))
	assert(str(full_roster_match.call("_participant_hud_summary")).contains("Alive 3/3"))
	var full_roster_hud: Node = full_roster_match.get("_hud")
	full_roster_match.call("_set_turn_index", 1)
	full_roster_match.call("_update_hud")
	var full_roster_hud_snapshot: Dictionary = full_roster_hud.get("_snapshot")
	assert(str(full_roster_hud_snapshot.get("player_name", "")) == "Gunner")
	assert(str(full_roster_hud_snapshot.get("target_name", "")) == "Pilot")
	assert(str(full_roster_hud_snapshot.get("participant_summary", "")).contains("Alive 3/3"))
	await _free_node(full_roster_match)

	_clear_projectiles(local_match)
	local_match.call(
		"_spawn_mirv_children",
		Vector2(200.0, 120.0),
		Vector2(100.0, -40.0),
		"Player",
		{"name": "MIRV", "kind": "mirv", "damage": 22, "blast": 34.0, "fragments": WeaponInventory.MIRV_FRAGMENTS, "spread": WeaponInventory.MIRV_SPREAD}
	)
	var mirv_children: Array = local_match.get("_projectiles")
	assert(mirv_children.size() == WeaponInventory.MIRV_FRAGMENTS)
	var first_mirv_child: Dictionary = mirv_children[0]
	var middle_mirv_child: Dictionary = mirv_children[2]
	var last_mirv_child: Dictionary = mirv_children[4]
	var first_mirv_weapon: Dictionary = first_mirv_child.get("weapon", {})
	assert(str(first_mirv_child.get("kind", "")) == "shell")
	assert(str(first_mirv_weapon.get("name", "")) == "MIRV Fragment")
	assert(abs(Vector2(first_mirv_child.get("velocity", Vector2.ZERO)).x - 60.0) < 0.01)
	assert(abs(Vector2(middle_mirv_child.get("velocity", Vector2.ZERO)).x - 100.0) < 0.01)
	assert(abs(Vector2(last_mirv_child.get("velocity", Vector2.ZERO)).x - 140.0) < 0.01)
	assert(abs(Vector2(first_mirv_child.get("velocity", Vector2.ZERO)).y) < 0.01)
	_clear_projectiles(local_match)

	var inventory := WeaponInventory.new()
	assert(inventory.select_by_name(WeaponInventory.MACHINE_GUN))
	assert(inventory.ammo_for(WeaponInventory.MACHINE_GUN) == WeaponInventory.MACHINE_GUN_ROUND_AMMO)
	assert(inventory.consume_current())
	assert(inventory.ammo_for(WeaponInventory.MACHINE_GUN) == WeaponInventory.MACHINE_GUN_ROUND_AMMO - WeaponInventory.MACHINE_GUN_VOLLEY)
	assert(inventory.consume_current_amount(WeaponInventory.DEFAULT_AMMO_SPEND))
	assert(inventory.ammo_for(WeaponInventory.MACHINE_GUN) == WeaponInventory.MACHINE_GUN_ROUND_AMMO - WeaponInventory.MACHINE_GUN_VOLLEY - 1)
	assert(inventory.ammo_pack_size(WeaponInventory.MACHINE_GUN) == WeaponInventory.MACHINE_GUN_SHOP_PACK)
	assert(inventory.ammo_pack_size(WeaponInventory.MIRV) == WeaponInventory.MIRV_SHOP_PACK)
	assert(inventory.ammo_pack_size(WeaponInventory.MISSILE) == WeaponInventory.MISSILE_SHOP_PACK)
	assert(inventory.ammo_pack_size(WeaponInventory.NUKE) == WeaponInventory.NUKE_SHOP_PACK)
	assert(inventory.ammo_pack_size(WeaponInventory.ROLLING_MINES) == WeaponInventory.ROLLING_MINES_SHOP_PACK)
	assert(inventory.ammo_pack_size(WeaponInventory.AIRSTRIKE) == WeaponInventory.AIRSTRIKE_SHOP_PACK)
	assert(inventory.ammo_pack_size(WeaponInventory.DEATHS_HEAD) == WeaponInventory.DEATHS_HEAD_SHOP_PACK)
	assert(inventory.ammo_pack_size(WeaponInventory.HOVER_COIL) == WeaponInventory.HOVER_COIL_SHOP_PACK)
	assert(inventory.ammo_pack_size(WeaponInventory.CORBOMITE) == WeaponInventory.CORBOMITE_SHOP_PACK)
	assert(abs(float(inventory.weapon_by_name(WeaponInventory.MACHINE_GUN).get("tracer_gravity", -1.0)) - WeaponInventory.MACHINE_GUN_TRACER_GRAVITY) < 0.01)
	assert(abs(WeaponInventory.MACHINE_GUN_TRACER_GRAVITY - 190.0) < 0.01)
	assert(abs(float(inventory.weapon_by_name(WeaponInventory.MIRV).get("min_fragment_spread_speed", -1.0)) - WeaponInventory.MIRV_MIN_FRAGMENT_SPREAD_SPEED) < 0.01)
	assert(abs(float(inventory.weapon_by_name(WeaponInventory.MISSILE).get("powered_speed", -1.0)) - WeaponInventory.MISSILE_CLASSIC_SPEED) < 0.01)
	assert(inventory.select_by_name(WeaponInventory.MIRV))
	assert(inventory.ammo_for(WeaponInventory.MIRV) == WeaponInventory.MIRV_ROUND_AMMO)
	var depleted_inventory := WeaponInventory.new()
	assert(depleted_inventory.select_by_name(WeaponInventory.MISSILE))
	assert(depleted_inventory.ammo_for(WeaponInventory.NUKE) > 0)
	assert(depleted_inventory.consume_current_amount(depleted_inventory.ammo_for(WeaponInventory.MISSILE)))
	assert(depleted_inventory.ammo_for(WeaponInventory.MISSILE) == 0)
	assert(depleted_inventory.current_name() == WeaponInventory.SHELL)

	local_match.set("_wind", 0.0)
	local_match.set("_wind_gust", 0.0)
	local_match.call(
		"_fire_from",
		Vector2(300.0, 60.0),
		0.0,
		10.0,
		true,
		{"name": "MIRV", "kind": "mirv", "damage": 22, "blast": 34.0, "fragments": WeaponInventory.MIRV_FRAGMENTS, "spread": WeaponInventory.MIRV_SPREAD},
		Vector2.ZERO,
		Vector2(100.0, 0.0)
	)
	local_match.call("_update_projectiles", 0.25)
	mirv_children = local_match.get("_projectiles")
	assert(mirv_children.size() == WeaponInventory.MIRV_FRAGMENTS)
	var split_mirv_position: Vector2 = Dictionary(mirv_children[0]).get("position", Vector2.ZERO)
	assert(abs(split_mirv_position.x - 325.0) < 0.01)
	assert(abs(split_mirv_position.y - 71.875) < 0.01)
	for mirv_projectile in mirv_children:
		assert(str(mirv_projectile.get("kind", "")) == "shell")
		assert(str(Dictionary(mirv_projectile.get("weapon", {})).get("name", "")) == "MIRV Fragment")
	_clear_projectiles(local_match)

	local_match.call(
		"_spawn_mirv_children",
		Vector2(200.0, 120.0),
		Vector2(0.0, -80.0),
		"Player",
		{"name": "MIRV", "kind": "mirv", "damage": 22, "blast": 34.0, "fragments": WeaponInventory.MIRV_FRAGMENTS, "spread": WeaponInventory.MIRV_SPREAD, "min_fragment_spread_speed": WeaponInventory.MIRV_MIN_FRAGMENT_SPREAD_SPEED}
	)
	mirv_children = local_match.get("_projectiles")
	assert(mirv_children.size() == WeaponInventory.MIRV_FRAGMENTS)
	assert(abs(Vector2(Dictionary(mirv_children[0]).get("velocity", Vector2.ZERO)).x) < 0.01)
	assert(abs(Vector2(Dictionary(mirv_children[2]).get("velocity", Vector2.ZERO)).x) < 0.01)
	assert(abs(Vector2(Dictionary(mirv_children[4]).get("velocity", Vector2.ZERO)).x) < 0.01)
	_clear_projectiles(local_match)

	local_match.call(
		"_fire_from",
		Vector2(320.0, 160.0),
		0.0,
		10.0,
		true,
		{"name": "Missile", "kind": "missile", "damage": 40, "blast": 46.0, "speed": 4.8, "fuel": 3.0, "steer_sensitivity": 300.0}
	)
	var missile_projectiles: Array = local_match.get("_projectiles")
	assert(missile_projectiles.size() == 1)
	var missile_projectile: Dictionary = missile_projectiles[0]
	assert(abs(float(missile_projectile.get("fuel", 0.0)) - 3.0) < 0.01)
	assert(float(missile_projectile.get("angle_change", -1.0)) == 0.0)
	var missile_flight_audio: AudioStreamPlayer = local_match.get_node("MissileFlightAudio")
	assert(missile_flight_audio.stream != null)
	var missile_flight_stream := missile_flight_audio.stream as AudioStreamWAV
	assert(missile_flight_stream != null)
	assert(missile_flight_stream.loop_mode == AudioStreamWAV.LOOP_FORWARD)
	assert(missile_flight_audio.playing)
	Input.action_press("gf_aim_left")
	local_match.call("_update_projectiles", 0.1)
	Input.action_release("gf_aim_left")
	missile_projectiles = local_match.get("_projectiles")
	assert(missile_projectiles.size() == 1)
	missile_projectile = missile_projectiles[0]
	assert(float(missile_projectile.get("angle_change", 0.0)) > 0.0)
	assert(float(missile_projectile.get("angle", 0.0)) > 0.0)
	assert(float(missile_projectile.get("fuel", 3.0)) < 3.0)
	local_match.call("_set_paused", true)
	assert(missile_flight_audio.stream_paused)
	local_match.call("_set_paused", false)
	assert(not missile_flight_audio.stream_paused)
	missile_projectile["fuel"] = 0.05
	missile_projectiles[0] = missile_projectile
	local_match.set("_projectiles", missile_projectiles)
	local_match.call("_update_projectiles", 0.1)
	assert(not missile_flight_audio.playing)
	_clear_projectiles(local_match)
	var clamped_missile := {
		"fuel": 1.0,
		"angle": 45.0,
		"angle_change": 490.0,
		"steer_sensitivity": 300.0,
		"player_owned": true,
	}
	Input.action_press("gf_aim_left")
	var clamped_missile_velocity: Vector2 = local_match.call("_update_missile_projectile", clamped_missile, Vector2(120.0, 0.0), Vector2.ZERO, 1.0)
	Input.action_release("gf_aim_left")
	assert(abs(float(clamped_missile.get("angle_change", 0.0)) - 500.0) < 0.01)
	var clamped_expected_speed := (WeaponInventory.MISSILE_CLASSIC_SPEED - cos(deg_to_rad(float(clamped_missile.get("angle", 0.0))))) * TankState.GUN_POWER_PIXEL_SCALE
	assert(abs(clamped_missile_velocity.length() - clamped_expected_speed) < 0.01)
	var recentered_missile := {
		"fuel": 1.0,
		"angle": 45.0,
		"angle_change": 90.0,
		"steer_sensitivity": 300.0,
		"player_owned": true,
	}
	local_match.call("_update_missile_projectile", recentered_missile, Vector2(120.0, 0.0), Vector2.ZERO, 0.1)
	assert(abs(float(recentered_missile.get("angle_change", -1.0))) < 0.01)
	assert(abs(float(local_match.call("_short_angle_delta", 350.0, 10.0)) - 20.0) < 0.01)
	assert(abs(float(local_match.call("_short_angle_delta", 10.0, 350.0)) + 20.0) < 0.01)

	var low_speed_missile := {
		"weapon": {"name": "Missile", "kind": "missile", "powered_speed": 0.25},
		"fuel": 1.0,
		"angle": 0.0,
		"angle_change": 0.0,
		"owner": "Player",
	}
	var low_speed_velocity: Vector2 = local_match.call("_update_missile_projectile", low_speed_missile, Vector2.ZERO, Vector2.ZERO, 0.1)
	var low_speed_factor := (0.25 - cos(0.0)) * TankState.GUN_POWER_PIXEL_SCALE
	assert(low_speed_factor < 0.0)
	assert(low_speed_velocity.distance_to(Vector2(0.0, -low_speed_factor)) < 0.01)

	var exhausting_missile := {
		"weapon": {"name": "Missile", "kind": "missile", "powered_speed": WeaponInventory.MISSILE_CLASSIC_SPEED},
		"fuel": 0.05,
		"angle": 0.0,
		"angle_change": 0.0,
		"owner": "Player",
	}
	var missile_classic_pixel_speed := (WeaponInventory.MISSILE_CLASSIC_SPEED - cos(0.0)) * TankState.GUN_POWER_PIXEL_SCALE
	var exhausted_frame_velocity: Vector2 = local_match.call("_update_missile_projectile", exhausting_missile, Vector2.ZERO, Vector2.ZERO, 0.1)
	assert(float(exhausting_missile.get("fuel", 0.0)) < 0.0)
	assert(bool(exhausting_missile.get("fuel_exhausted_this_frame", false)))
	assert(not bool(local_match.call("_missile_applies_ballistic_acceleration", exhausting_missile)))
	assert(exhausted_frame_velocity.distance_to(Vector2(0.0, -missile_classic_pixel_speed)) < 0.01)
	var next_freefall_velocity: Vector2 = local_match.call("_update_missile_projectile", exhausting_missile, exhausted_frame_velocity, Vector2.ZERO, 0.1)
	assert(not bool(exhausting_missile.get("fuel_exhausted_this_frame", true)))
	assert(bool(local_match.call("_missile_applies_ballistic_acceleration", exhausting_missile)))
	assert(next_freefall_velocity.distance_to(exhausted_frame_velocity) < 0.01)

	local_match.call(
		"_fire_from",
		Vector2(100.0, 140.0),
		0.0,
		10.0,
		true,
		{"name": "Shell", "kind": "shell", "damage": 40, "blast": 48.0, "speed": 4.2},
		Vector2(12.0, -8.0)
	)
	var airborne_projectiles: Array = local_match.get("_projectiles")
	assert(airborne_projectiles.size() == 1)
	var airborne_projectile: Dictionary = airborne_projectiles[0]
	assert(abs(Vector2(airborne_projectile.get("velocity", Vector2.ZERO)).x - 12.0) < 0.01)
	assert(abs(Vector2(airborne_projectile.get("velocity", Vector2.ZERO)).y + 239.0) < 0.01)
	_clear_projectiles(local_match)

	local_match.call(
		"_fire_from",
		Vector2(100.0, 140.0),
		0.0,
		10.0,
		true,
		{"name": "Shell", "kind": "shell", "damage": 40, "blast": 48.0, "speed": 4.2},
		Vector2.ZERO,
		Vector2(54.0, -8.0)
	)
	airborne_projectiles = local_match.get("_projectiles")
	assert(airborne_projectiles.size() == 1)
	airborne_projectile = airborne_projectiles[0]
	assert(Vector2(airborne_projectile.get("velocity", Vector2.ZERO)) == Vector2(54.0, -8.0))
	_clear_projectiles(local_match)

	local_match.set("_wind", 0.0)
	local_match.set("_wind_gust", 0.0)
	local_match.call(
		"_fire_from",
		Vector2(300.0, 30.0),
		0.0,
		0.0,
		true,
		{"name": "Shell", "kind": "shell", "damage": 40, "blast": 48.0, "speed": 4.2},
		Vector2.ZERO,
		Vector2.ZERO
	)
	local_match.call("_update_projectiles", 0.1)
	var gravity_projectiles: Array = local_match.get("_projectiles")
	assert(gravity_projectiles.size() == 1)
	var gravity_projectile: Dictionary = gravity_projectiles[0]
	assert(abs(Vector2(gravity_projectile.get("velocity", Vector2.ZERO)).y - 19.0) < 0.01)
	_clear_projectiles(local_match)

	local_match.call(
		"_fire_weapon",
		Vector2(320.0, 160.0),
		0.0,
		10.0,
		true,
		{"name": "Machine Gun", "kind": "machine_gun", "damage": 2, "blast": 0.0, "speed": 5.8, "volley": 5, "cooldown": 0.1, "direct_damage": true}
	)
	var machine_gun_projectiles: Array = local_match.get("_projectiles")
	assert(machine_gun_projectiles.size() == 5)
	var first_machine_gun_projectile: Dictionary = machine_gun_projectiles[0]
	var fixed_machine_gun_speed := TankState.GUN_POWER_PIXEL_SCALE * WeaponInventory.MACHINE_GUN_CLASSIC_POWER * 5.8
	assert(str(first_machine_gun_projectile.get("kind", "")) == "machine_gun")
	assert(Vector2(first_machine_gun_projectile.get("back_position", Vector2.ZERO)) == Vector2(320.0, 160.0))
	assert(abs(Vector2(first_machine_gun_projectile.get("velocity", Vector2.ZERO)).y + fixed_machine_gun_speed) < 0.01)
	assert(abs(float(first_machine_gun_projectile.get("delay", -1.0))) < 0.01)
	assert(abs(float(machine_gun_projectiles[1].get("delay", 0.0)) - 0.1) < 0.01)
	assert(abs(float(machine_gun_projectiles[4].get("delay", 0.0)) - 0.4) < 0.01)
	var enemy_health_before := int(enemy_tank.health)
	var score_before := int(local_match.get("_score"))
	local_match.call("_apply_machine_gun_damage", first_machine_gun_projectile, "Enemy")
	assert(int(enemy_tank.health) == enemy_health_before - 2)
	assert(int(local_match.get("_score")) == score_before + 2)
	_clear_projectiles(local_match)
	enemy_tank.health = 1
	enemy_tank.state = TankState.STATE_ALIVE
	local_match.set("_machine_gun_active", true)
	local_match.set("_machine_gun_fire_held", true)
	local_match.set("_machine_gun_ai_burst_remaining", 4)
	local_match.call("_play_machine_gun_audio")
	var lethal_machine_gun_audio: AudioStreamPlayer = local_match.get_node("MachineGunAudio")
	var lethal_machine_gun_projectile := {
		"kind": "machine_gun",
		"weapon": {"name": "Machine Gun", "kind": "machine_gun", "damage": 2},
		"player_owned": true,
	}
	var pending_machine_gun_projectile := {"kind": "machine_gun", "expired": false}
	var lethal_machine_gun_projectiles: Array[Dictionary] = []
	lethal_machine_gun_projectiles.append(lethal_machine_gun_projectile)
	lethal_machine_gun_projectiles.append(pending_machine_gun_projectile)
	local_match.set("_projectiles", lethal_machine_gun_projectiles)
	assert(Array(local_match.get("_projectiles")).size() == 2)
	local_match.call("_apply_machine_gun_damage", lethal_machine_gun_projectile, "Enemy")
	assert(enemy_tank.state == TankState.STATE_DEAD)
	assert(not bool(local_match.get("_machine_gun_fire_held")))
	assert(int(local_match.get("_machine_gun_ai_burst_remaining")) == 0)
	assert(not lethal_machine_gun_audio.playing)
	var expired_machine_gun_projectiles: Array = local_match.get("_projectiles")
	assert(bool(Dictionary(expired_machine_gun_projectiles[0]).get("expired", false)))
	assert(bool(Dictionary(expired_machine_gun_projectiles[1]).get("expired", false)))
	assert(str(local_match.get("_message")).contains("destroyed"))
	_clear_projectiles(local_match)
	local_match.call("_reset_machine_gun_fire")
	enemy_tank.health = TankState.TANK_MAX_HEALTH
	enemy_tank.state = TankState.STATE_ALIVE

	local_match.call(
		"_fire_weapon",
		Vector2(320.0, 160.0),
		30.0,
		40.0,
		true,
		{"name": "Machine Gun", "kind": "machine_gun", "damage": 2, "blast": 0.0, "speed": 5.8, "volley": 5, "cooldown": 0.1, "direct_damage": true}
	)
	local_match.call("_update_projectiles", 0.05)
	machine_gun_projectiles = local_match.get("_projectiles")
	assert(machine_gun_projectiles.size() == 5)
	var fixed_power_machine_gun_velocity := Vector2(-sin(deg_to_rad(30.0)), -cos(deg_to_rad(30.0))) * fixed_machine_gun_speed
	var gravity_adjusted_machine_gun_velocity := fixed_power_machine_gun_velocity + Vector2(0.0, WeaponInventory.MACHINE_GUN_TRACER_GRAVITY * 0.05)
	var expected_machine_gun_position := Vector2(320.0, 160.0) + fixed_power_machine_gun_velocity * 0.05 + Vector2(0.0, 0.5 * WeaponInventory.MACHINE_GUN_TRACER_GRAVITY * 0.05 * 0.05)
	var expected_machine_gun_back_position := Vector2(320.0, 160.0) + fixed_power_machine_gun_velocity * 0.04 + Vector2(0.0, 0.5 * WeaponInventory.MACHINE_GUN_TRACER_GRAVITY * 0.04 * 0.04)
	assert(Vector2(machine_gun_projectiles[0].get("velocity", Vector2.ZERO)).distance_to(gravity_adjusted_machine_gun_velocity) < 0.01)
	assert(Vector2(machine_gun_projectiles[0].get("position", Vector2.ZERO)).distance_to(expected_machine_gun_position) < 0.01)
	assert(Vector2(machine_gun_projectiles[0].get("back_position", Vector2.ZERO)).distance_to(expected_machine_gun_back_position) < 0.01)
	assert(Vector2(machine_gun_projectiles[0].get("velocity", Vector2.ZERO)).y < -100.0)
	assert(Vector2(machine_gun_projectiles[1].get("position", Vector2.ZERO)) == Vector2(320.0, 160.0))
	assert(float(machine_gun_projectiles[1].get("delay", 0.0)) > 0.0)
	_clear_projectiles(local_match)

	var falling_machine_gun_projectile := {
		"weapon": {"name": "Machine Gun", "kind": "machine_gun", "damage": 2},
		"position": Vector2(600.0, 30.0),
		"owner": "Player",
		"age": 0.25,
		"launch_position": Vector2(600.0, 30.0),
		"launch_velocity": Vector2(12.0, -40.0),
	}
	var falling_machine_gun_velocity := Vector2(12.0, -40.0)
	local_match.call("_update_machine_gun_projectile", falling_machine_gun_projectile, Vector2(600.0, 30.0), falling_machine_gun_velocity, 0.25)
	var expected_falling_machine_gun_velocity := falling_machine_gun_velocity + Vector2(0.0, WeaponInventory.MACHINE_GUN_TRACER_GRAVITY * 0.25)
	var expected_falling_machine_gun_position := Vector2(600.0, 30.0) + falling_machine_gun_velocity * 0.25 + Vector2(0.0, 0.5 * WeaponInventory.MACHINE_GUN_TRACER_GRAVITY * 0.25 * 0.25)
	var expected_falling_machine_gun_back_position := Vector2(600.0, 30.0) + falling_machine_gun_velocity * 0.24 + Vector2(0.0, 0.5 * WeaponInventory.MACHINE_GUN_TRACER_GRAVITY * 0.24 * 0.24)
	assert(Vector2(falling_machine_gun_projectile.get("velocity", Vector2.ZERO)).distance_to(expected_falling_machine_gun_velocity) < 0.01)
	assert(Vector2(falling_machine_gun_projectile.get("position", Vector2.ZERO)).distance_to(expected_falling_machine_gun_position) < 0.01)
	assert(Vector2(falling_machine_gun_projectile.get("back_position", Vector2.ZERO)).distance_to(expected_falling_machine_gun_back_position) < 0.01)
	assert(not bool(falling_machine_gun_projectile.get("expired", false)))

	var delayed_machine_gun_projectile := {
		"delay": WeaponInventory.MACHINE_GUN_COOLDOWN,
		"position": Vector2(320.0, 160.0),
		"back_position": Vector2.ZERO,
	}
	assert(abs(float(local_match.call("_machine_gun_projectile_delta", delayed_machine_gun_projectile, WeaponInventory.MACHINE_GUN_COOLDOWN * 0.4))) < 0.01)
	assert(abs(float(delayed_machine_gun_projectile.get("delay", 0.0)) - WeaponInventory.MACHINE_GUN_COOLDOWN * 0.6) < 0.01)
	var remaining_machine_gun_delta := float(local_match.call("_machine_gun_projectile_delta", delayed_machine_gun_projectile, WeaponInventory.MACHINE_GUN_COOLDOWN))
	assert(abs(remaining_machine_gun_delta - WeaponInventory.MACHINE_GUN_COOLDOWN * 0.4) < 0.01)
	assert(abs(float(delayed_machine_gun_projectile.get("delay", -1.0))) < 0.01)
	assert(Vector2(delayed_machine_gun_projectile.get("back_position", Vector2.ZERO)) == Vector2(320.0, 160.0))

	var player_inventory: RefCounted = local_match.get("_inventory")
	player_inventory.reset_round_ammo()
	assert(player_inventory.select_by_name(WeaponInventory.MACHINE_GUN))
	var held_machine_gun_ammo_before := int(player_inventory.ammo_for(WeaponInventory.MACHINE_GUN))
	local_match.set("_phase", "aim")
	local_match.call("_set_turn_index", 0)
	Input.action_press("gf_fire")
	local_match.call("_fire_player")
	assert(bool(local_match.get("_machine_gun_active")))
	var machine_gun_audio: AudioStreamPlayer = local_match.get_node("MachineGunAudio")
	assert(machine_gun_audio.stream != null)
	var machine_gun_stream := machine_gun_audio.stream as AudioStreamWAV
	assert(machine_gun_stream != null)
	assert(machine_gun_stream.loop_mode == AudioStreamWAV.LOOP_FORWARD)
	assert(machine_gun_audio.playing)
	machine_gun_projectiles = local_match.get("_projectiles")
	assert(machine_gun_projectiles.is_empty())
	assert(int(player_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == held_machine_gun_ammo_before)
	local_match.call("_unselect_machine_gun_and_cycle", 1)
	assert(not bool(local_match.get("_machine_gun_active")))
	assert(not bool(local_match.get("_machine_gun_fire_held")))
	assert(not machine_gun_audio.playing)
	assert(str(local_match.get("_phase")) == "aim")
	assert(str(local_match.get("_turn_owner")) == "Player")
	assert(player_inventory.current_name() != WeaponInventory.MACHINE_GUN)
	assert(Array(local_match.get("_projectiles")).is_empty())
	assert(int(player_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == held_machine_gun_ammo_before)
	assert(str(local_match.get("_message")).contains("unselected"))
	Input.action_release("gf_fire")
	assert(player_inventory.select_by_name(WeaponInventory.MACHINE_GUN))
	held_machine_gun_ammo_before = int(player_inventory.ammo_for(WeaponInventory.MACHINE_GUN))
	Input.action_press("gf_fire")
	local_match.call("_fire_player")
	assert(bool(local_match.get("_machine_gun_active")))
	assert(machine_gun_audio.playing)
	assert(Array(local_match.get("_projectiles")).is_empty())
	local_match.call("_update_machine_gun_fire", WeaponInventory.MACHINE_GUN_COOLDOWN)
	assert(Array(local_match.get("_projectiles")).is_empty())
	assert(int(player_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == held_machine_gun_ammo_before)
	local_match.call("_update_machine_gun_fire", WeaponInventory.MACHINE_GUN_COOLDOWN * 0.1)
	assert(Array(local_match.get("_projectiles")).size() == 1)
	assert(int(player_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == held_machine_gun_ammo_before - 1)
	local_match.call("_unselect_machine_gun_and_cycle", 1)
	assert(not bool(local_match.get("_machine_gun_fire_held")))
	assert(not machine_gun_audio.playing)
	assert(bool(local_match.get("_machine_gun_active")))
	assert(player_inventory.current_name() != WeaponInventory.MACHINE_GUN)
	assert(str(local_match.get("_message")).contains("unselected"))
	assert(Array(local_match.get("_projectiles")).size() == 1)
	assert(int(player_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == held_machine_gun_ammo_before - 1)
	player_inventory.select_by_name(WeaponInventory.MACHINE_GUN)
	local_match.set("_machine_gun_fire_held", true)
	local_match.call("_play_machine_gun_audio")
	Input.action_release("gf_fire")
	local_match.call("_update_machine_gun_fire", WeaponInventory.MACHINE_GUN_COOLDOWN)
	assert(not bool(local_match.get("_machine_gun_fire_held")))
	assert(not machine_gun_audio.playing)
	local_match.call("_reset_machine_gun_fire")
	_clear_projectiles(local_match)

	player_inventory.reset_round_ammo()
	assert(player_inventory.select_by_name(WeaponInventory.MACHINE_GUN))
	assert(player_inventory.consume_ammo(WeaponInventory.MACHINE_GUN, WeaponInventory.MACHINE_GUN_ROUND_AMMO - 1))
	assert(int(player_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == 1)
	local_match.set("_phase", "aim")
	local_match.call("_set_turn_index", 0)
	Input.action_press("gf_fire")
	local_match.call("_fire_player")
	local_match.call("_update_machine_gun_fire", WeaponInventory.MACHINE_GUN_COOLDOWN * 1.1)
	machine_gun_projectiles = local_match.get("_projectiles")
	assert(machine_gun_projectiles.size() == 1)
	assert(int(player_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == 0)
	assert(player_inventory.current_name() == WeaponInventory.SHELL)
	local_match.call("_update_machine_gun_fire", WeaponInventory.MACHINE_GUN_COOLDOWN * 1.1)
	assert(Array(local_match.get("_projectiles")).size() == 1)
	assert(not bool(local_match.get("_machine_gun_fire_held")))
	assert(not machine_gun_audio.playing)
	Input.action_release("gf_fire")
	_clear_projectiles(local_match)
	local_match.call("_reset_machine_gun_fire")

	var enemy_inventory: RefCounted = local_match.get("_enemy_inventory")
	enemy_inventory.reset_round_ammo()
	assert(enemy_inventory.select_by_name(WeaponInventory.MACHINE_GUN))
	local_match.call("_set_turn_index", 1)
	var ai_burst_weapon: Dictionary = enemy_inventory.weapon_by_name(WeaponInventory.MACHINE_GUN)
	var player_for_burst: RefCounted = local_match.get("_player")
	var enemy_for_burst: RefCounted = local_match.get("_enemy")
	player_for_burst.position = Vector2(220.0, player_for_burst.position.y)
	enemy_for_burst.position = Vector2(420.0, enemy_for_burst.position.y)
	player_for_burst.health = TankState.TANK_MAX_HEALTH
	local_match.set("_ai_difficulty", "easy")
	assert(int(local_match.call("_machine_gun_ai_burst_budget", ai_burst_weapon)) == 3)
	local_match.set("_ai_difficulty", "normal")
	assert(int(local_match.call("_machine_gun_ai_burst_budget", ai_burst_weapon)) == 5)
	local_match.set("_ai_difficulty", "hard")
	assert(int(local_match.call("_machine_gun_ai_burst_budget", ai_burst_weapon)) == 8)
	player_for_burst.health = 10
	assert(int(local_match.call("_machine_gun_ai_burst_budget", ai_burst_weapon)) == 10)
	player_for_burst.health = TankState.TANK_MAX_HEALTH
	local_match.set("_ai_difficulty", "normal")
	assert(enemy_inventory.select_by_name(WeaponInventory.SHELL))
	assert(int(local_match.call("_machine_gun_ai_burst_budget", ai_burst_weapon)) == 5)
	assert(enemy_inventory.select_by_name(WeaponInventory.MACHINE_GUN))
	var enemy_machine_gun_ammo_before := int(enemy_inventory.ammo_for(WeaponInventory.MACHINE_GUN))
	local_match.call("_begin_enemy_machine_gun_fire", enemy_inventory.weapon_by_name(WeaponInventory.MACHINE_GUN))
	assert(bool(local_match.get("_machine_gun_active")))
	assert(not bool(local_match.get("_machine_gun_player_owned")))
	assert(machine_gun_audio.playing)
	assert(int(local_match.get("_machine_gun_ai_burst_remaining")) == WeaponInventory.MACHINE_GUN_VOLLEY)
	assert(Array(local_match.get("_projectiles")).is_empty())
	assert(int(enemy_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == enemy_machine_gun_ammo_before)
	local_match.call("_update_machine_gun_fire", WeaponInventory.MACHINE_GUN_COOLDOWN * 1.1)
	assert(Array(local_match.get("_projectiles")).size() == 1)
	assert(int(enemy_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == enemy_machine_gun_ammo_before - 1)
	assert(int(local_match.get("_machine_gun_ai_burst_remaining")) == WeaponInventory.MACHINE_GUN_VOLLEY - 1)
	local_match.call("_update_machine_gun_fire", WeaponInventory.MACHINE_GUN_COOLDOWN * 1.1)
	assert(Array(local_match.get("_projectiles")).size() == 2)
	assert(int(enemy_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == enemy_machine_gun_ammo_before - 2)
	assert(int(local_match.get("_machine_gun_ai_burst_remaining")) == WeaponInventory.MACHINE_GUN_VOLLEY - 2)
	local_match.call("_reset_machine_gun_fire")
	assert(not machine_gun_audio.playing)
	_clear_projectiles(local_match)

	var nuke_weapon: Dictionary = enemy_inventory.weapon_by_name(WeaponInventory.NUKE)
	player_for_burst.health = 20
	enemy_for_burst.health = TankState.TANK_MAX_HEALTH
	player_for_burst.position = Vector2(360.0, 300.0)
	enemy_for_burst.position = Vector2(392.0, 300.0)
	local_match.set("_ai_difficulty", "hard")
	var risky_nuke_projection: Dictionary = local_match.call("_ai_weapon_projection", nuke_weapon, {"miss": 0.0}, true, 32.0)
	assert(int(risky_nuke_projection.get("self_damage", 0)) > 0)
	assert(float(risky_nuke_projection.get("score", 0.0)) < 0.0)
	var risky_weapon: Dictionary = local_match.call("_choose_ai_weapon", {"miss": 0.0})
	assert(str(risky_weapon.get("name", "")) != WeaponInventory.NUKE)
	player_for_burst.health = 60
	player_for_burst.position = Vector2(220.0, 300.0)
	enemy_for_burst.position = Vector2(760.0, 300.0)
	var safe_nuke_projection: Dictionary = local_match.call("_ai_weapon_projection", nuke_weapon, {"miss": 10.0}, false, 540.0)
	assert(int(safe_nuke_projection.get("self_damage", -1)) == 0)
	assert(float(safe_nuke_projection.get("score", 0.0)) > float(local_match.call("_ai_weapon_score_threshold")))
	var safe_weapon: Dictionary = local_match.call("_choose_ai_weapon", {"miss": 10.0})
	assert(str(safe_weapon.get("name", "")) == WeaponInventory.NUKE)
	player_for_burst.health = TankState.TANK_MAX_HEALTH
	enemy_for_burst.health = TankState.TANK_MAX_HEALTH

	var match_terrain: Variant = local_match.get("_terrain")
	var tracer_x := 520.0
	var tracer_ground_before := float(match_terrain.height_at(tracer_x))
	local_match.call(
		"_fire_from",
		Vector2(tracer_x, tracer_ground_before - 28.0),
		180.0,
		10.0,
		true,
		{"name": "Machine Gun", "kind": "machine_gun", "damage": 2, "blast": 0.0, "speed": 5.8, "volley": 1, "cooldown": 0.1, "direct_damage": true}
	)
	local_match.call("_update_projectiles", 0.2)
	assert(local_match.get("_projectiles").is_empty())
	assert(local_match.get("_explosions").is_empty())
	assert(abs(float(match_terrain.height_at(tracer_x)) - tracer_ground_before) < 0.01)
	local_match.set("_phase", "aim")
	local_match.call("_set_turn_index", 0)

	local_match.call("_spawn_explosion", Vector2(430.0, 220.0), 96.0, true)
	var nuke_explosions: Array = local_match.get("_explosions")
	assert(nuke_explosions.size() == 1)
	var nuke_explosion: Dictionary = nuke_explosions[0]
	assert(bool(nuke_explosion.get("white_out", false)))
	assert(abs(float(nuke_explosion.get("white_out_level", 0.0)) - 1.0) < 0.01)
	assert(float(local_match.call("_whiteout_alpha")) > 0.99)
	var nuke_audio: AudioStreamPlayer = local_match.get_node("NukeAudio")
	assert(nuke_audio.stream != null)
	var nuke_stream := nuke_audio.stream as AudioStreamWAV
	assert(nuke_stream != null)
	assert(nuke_stream.loop_mode == AudioStreamWAV.LOOP_DISABLED)
	assert(nuke_audio.playing)
	local_match.call("_set_paused", true)
	assert(nuke_audio.stream_paused)
	local_match.call("_set_paused", false)
	assert(not nuke_audio.stream_paused)
	local_match.call("_update_explosions", 1.0)
	nuke_explosions = local_match.get("_explosions")
	assert(nuke_explosions.size() == 1)
	nuke_explosion = nuke_explosions[0]
	assert(bool(nuke_explosion.get("white_out", false)))
	assert(float(nuke_explosion.get("white_out_level", 0.0)) < 0.5)
	assert(float(local_match.call("_whiteout_alpha")) < 0.5)
	local_match.call("_stop_nuke_audio")
	assert(not nuke_audio.playing)
	_clear_explosions(local_match)

	local_match.set("_wind", 4.0)
	local_match.set("_wind_gust", 0.0)
	assert(float(local_match.call("_wind_acceleration", 0.0)) == 4.0)
	local_match.set("_wind", 8.8)
	local_match.call("_shift_wind_for_turn")
	var shifted_wind := float(local_match.get("_wind"))
	assert(shifted_wind >= -9.0 and shifted_wind <= 9.0)

	var hud := LocalMatchHud.new()
	assert(int(hud.call("_weapon_icon_index", "Shell")) == 0)
	assert(int(hud.call("_weapon_icon_index", "Nuke")) == 1)
	assert(int(hud.call("_weapon_icon_index", "Machine Gun")) == 2)
	assert(int(hud.call("_weapon_icon_index", "MIRV")) == 4)
	assert(int(hud.call("_weapon_icon_index", "Missile")) == 10)
	var missile_icon_rect: Rect2 = hud.call("_weapon_icon_source_rect", "Missile")
	assert(missile_icon_rect.position == Vector2(32.0, 32.0))
	assert(missile_icon_rect.size == Vector2(16.0, 16.0))
	var classic_metrics: Dictionary = hud.call("_classic_hud_metrics", {
		"health": 50,
		"fuel": 0.25,
		"color": Color.RED,
		"weapon": "Machine Gun",
		"ammo": 25,
		"state": "alive",
		"order": 2,
	}, 0)
	var panel_rect: Vector4 = classic_metrics["panel"]
	assert(abs(panel_rect.x - (-4.9)) < 0.01)
	assert(abs(panel_rect.y - 7.4) < 0.01)
	assert(abs(panel_rect.z - (-2.6)) < 0.01)
	assert(abs(panel_rect.w - 6.6) < 0.01)
	var health_rect: Vector4 = classic_metrics["health"]
	assert(abs(health_rect.x - (-4.8)) < 0.01)
	assert(abs(health_rect.y - 7.4) < 0.01)
	assert(abs(health_rect.z - (-3.75)) < 0.01)
	assert(abs(health_rect.w - 7.3) < 0.01)
	var fuel_rect: Vector4 = classic_metrics["fuel"]
	assert(abs(fuel_rect.x - (-4.8)) < 0.01)
	assert(abs(fuel_rect.y - 7.2) < 0.01)
	assert(abs(fuel_rect.z - (-4.275)) < 0.01)
	assert(abs(fuel_rect.w - 7.1) < 0.01)
	assert(Color(classic_metrics["health_color"]).is_equal_approx(Color8(191, 191, 128)))
	assert(Color(classic_metrics["fuel_color"]).is_equal_approx(Color8(95, 128, 159)))
	var tank_points: Array = classic_metrics["tank_points"]
	assert(tank_points.size() == 4)
	var tank_point_0: Vector2 = tank_points[0]
	var tank_point_1: Vector2 = tank_points[1]
	var tank_point_2: Vector2 = tank_points[2]
	var tank_point_3: Vector2 = tank_points[3]
	assert(abs(tank_point_0.x - (-4.75)) < 0.01)
	assert(abs(tank_point_0.y - 7.0) < 0.01)
	assert(abs(tank_point_1.x - (-4.9)) < 0.01)
	assert(abs(tank_point_1.y - 6.7) < 0.01)
	assert(abs(tank_point_2.x - (-4.3)) < 0.01)
	assert(abs(tank_point_2.y - 6.7) < 0.01)
	assert(abs(tank_point_3.x - (-4.45)) < 0.01)
	assert(abs(tank_point_3.y - 7.0) < 0.01)
	var weapon_rect: Vector4 = classic_metrics["weapon"]
	assert(abs(weapon_rect.x - (-4.2)) < 0.01)
	assert(abs(weapon_rect.y - 7.0) < 0.01)
	assert(abs(weapon_rect.z - (-3.9)) < 0.01)
	assert(abs(weapon_rect.w - 6.7) < 0.01)
	assert(str(classic_metrics["weapon_name"]) == "Machine Gun")
	assert(int(classic_metrics["ammo"]) == 25)
	assert(hud.call("_wind_label", 5.1) == "Wind -> 5")
	assert(hud.call("_wind_label", -2.6) == "Wind <- 3")
	assert(hud.call("_wind_label", 0.2) == "Wind calm")
	assert(hud.call("_quake_label", true, 3.0) == "Quake!")
	assert(hud.call("_quake_label", false, 9.2) == "Quake in 10s")
	assert(hud.call("_quake_label", false, 60.0) == "")
	await _free_node(hud)

	var jump_jets_audio: AudioStreamPlayer = local_match.get_node("JumpJetsAudio")
	assert(jump_jets_audio.stream != null)
	var jump_jets_stream := jump_jets_audio.stream as AudioStreamWAV
	assert(jump_jets_stream != null)
	assert(jump_jets_stream.loop_mode == AudioStreamWAV.LOOP_FORWARD)
	assert(not bool(local_match.get("_jump_jets_active")))
	local_match.call("_play_jump_jets_audio")
	assert(bool(local_match.get("_jump_jets_active")))
	assert(jump_jets_audio.playing)
	local_match.call("_set_paused", true)
	assert(jump_jets_audio.stream_paused)
	local_match.call("_set_paused", false)
	assert(not jump_jets_audio.stream_paused)
	assert(jump_jets_audio.playing)
	local_match.call("_stop_jump_jets_audio")
	assert(not bool(local_match.get("_jump_jets_active")))
	assert(not jump_jets_audio.playing)
	var jump_jets_tank := TankState.new()
	jump_jets_tank.fuel = 0.001
	jump_jets_tank.state = TankState.STATE_ALIVE
	assert(bool(local_match.call("_tank_can_boost", jump_jets_tank)))
	jump_jets_tank.fuel = 0.0
	assert(not bool(local_match.call("_tank_can_boost", jump_jets_tank)))
	jump_jets_tank.fuel = TankState.TANK_FULL_FUEL
	jump_jets_tank.state = TankState.STATE_DEAD
	assert(not bool(local_match.call("_tank_can_boost", jump_jets_tank)))

	local_match.call("_play_weapon_launch_audio", "shell")
	var fire_shell_audio: AudioStreamPlayer = local_match.get_node("FireShellAudio")
	assert(fire_shell_audio.stream != null)
	var fire_shell_stream := fire_shell_audio.stream as AudioStreamWAV
	assert(fire_shell_stream != null)
	assert(fire_shell_stream.loop_mode == AudioStreamWAV.LOOP_DISABLED)
	assert(fire_shell_audio.playing)
	local_match.call("_set_paused", true)
	assert(fire_shell_audio.stream_paused)
	local_match.call("_set_paused", false)
	assert(not fire_shell_audio.stream_paused)
	local_match.call("_stop_fire_shell_audio")
	assert(not fire_shell_audio.playing)

	local_match.call("_play_weapon_launch_audio", "missile")
	var launch_missile_audio: AudioStreamPlayer = local_match.get_node("LaunchMissileAudio")
	assert(launch_missile_audio.stream != null)
	var launch_missile_stream := launch_missile_audio.stream as AudioStreamWAV
	assert(launch_missile_stream != null)
	assert(launch_missile_stream.loop_mode == AudioStreamWAV.LOOP_DISABLED)
	assert(launch_missile_audio.playing)
	local_match.call("_stop_launch_missile_audio")
	assert(not launch_missile_audio.playing)

	var quake_x := 360.0
	var before_quake_drop := float(match_terrain.height_at(quake_x))
	local_match.set("_quake_countdown", -0.1)
	local_match.call("_update_quake", 0.1)
	assert(bool(local_match.get("_quake_active")))
	var quake_audio: AudioStreamPlayer = local_match.get_node("QuakeAudio")
	assert(quake_audio.stream != null)
	var quake_stream := quake_audio.stream as AudioStreamWAV
	assert(quake_stream != null)
	assert(quake_stream.loop_mode == AudioStreamWAV.LOOP_FORWARD)
	assert(quake_audio.playing)
	local_match.call("_update_quake", 1.0)
	assert(float(match_terrain.height_at(quake_x)) > before_quake_drop)
	assert(str(local_match.get("_message")).contains("Quake"))
	local_match.set("_quake_countdown", -0.1)
	local_match.call("_update_quake", 0.1)
	assert(not bool(local_match.get("_quake_active")))
	assert(float(local_match.get("_quake_countdown")) >= 29.0)
	assert(not quake_audio.playing)

	local_match.set("_score", 40)
	local_match.set("_enemy_score", 60)
	local_match.set("_credits", 7)
	var leader_participants: Array = local_match.get("_participants")
	var leader_enemy: Dictionary = leader_participants[1]
	leader_enemy["leader"] = true
	leader_participants[1] = leader_enemy
	local_match.set("_participants", leader_participants)
	enemy_tank.state = TankState.STATE_DEAD
	local_match.call("_record_round_defeat", "Player", "Enemy")
	local_match.call("_open_round_score", "Round Won", 100, "Player")
	assert(str(local_match.get("_phase")) == "score")
	assert(abs(float(local_match.get("_score_continue_delay")) - 2.0) < 0.01)
	assert(int(local_match.get("_score")) == 340)
	assert(int(local_match.get("_enemy_score")) == 60)
	assert(int(local_match.get("_credits")) == 92)
	assert(local_match.get_node("ScoreOverlay").visible)
	var score_reward_label := local_match.get("_score_reward_label") as Label
	assert(score_reward_label.text == "Round credits +85  Credits 92")
	var score_rows: Array = local_match.call("_score_rows_snapshot")
	assert(score_rows.size() == 2)
	assert(str(Dictionary(score_rows[0]).get("rank", "")) == "1st")
	assert(str(Dictionary(score_rows[0]).get("name", "")) == "Player")
	assert(str(Dictionary(score_rows[0]).get("round_detail", "")) == "Defeated Enemy leader +200, Survived +100")
	var score_defeated_icons: Array = Dictionary(score_rows[0]).get("defeated_icons", [])
	assert(score_defeated_icons.size() == 1)
	assert(str(Dictionary(score_defeated_icons[0]).get("owner", "")) == "Enemy")
	assert(str(Dictionary(score_defeated_icons[0]).get("name", "")) == "Enemy")
	assert(bool(Dictionary(score_defeated_icons[0]).get("leader", false)))
	var score_rows_container := local_match.get("_score_rows_container") as VBoxContainer
	var first_score_row := score_rows_container.get_child(1) as HBoxContainer
	var score_player_panel := first_score_row.get_child(1) as PanelContainer
	var score_round_panel := first_score_row.get_child(2) as PanelContainer
	var score_total_panel := first_score_row.get_child(3) as PanelContainer
	assert(score_player_panel.name == "ScorePlayerColumn")
	assert(score_round_panel.name == "ScoreRoundColumn")
	assert(score_total_panel.name == "ScoreTotalColumn")
	var score_panel_style := score_player_panel.get_theme_stylebox("panel") as StyleBoxFlat
	assert(score_panel_style != null)
	assert(score_panel_style.bg_color == Color("#00000080"))
	var score_player_cell := score_player_panel.get_child(0) as HBoxContainer
	var score_player_icon := score_player_cell.get_child(0) as Control
	var score_player_tank := score_player_icon.get_node_or_null("ScorePlayerTank") as Polygon2D
	var first_score_color: Color = Dictionary(score_rows[0]).get("color", Color.WHITE)
	assert(score_player_tank != null)
	assert(score_player_tank.polygon.size() == 4)
	assert(score_player_tank.color == first_score_color)
	var score_round_detail_cell := score_round_panel.get_child(0) as HBoxContainer
	var score_defeated_icon := score_round_detail_cell.get_child(0) as Control
	assert(score_defeated_icon.get_node_or_null("DefeatedTank") != null)
	assert(score_defeated_icon.get_node_or_null("LeaderPole") != null)
	assert(score_defeated_icon.get_node_or_null("LeaderFlag") != null)
	var score_detail_label := score_round_detail_cell.get_child(1) as Label
	assert(score_detail_label.text == "Defeated Enemy leader +200, Survived +100")
	var score_total_label := score_total_panel.get_child(0) as Label
	assert(score_total_label.text == "340")
	assert(score_total_label.get_theme_color("font_color") == Color.WHITE)
	assert(str(Dictionary(score_rows[1]).get("rank", "")) == "2nd")
	var score_shop_continue_button := local_match.get("_score_continue_button") as Button
	assert(score_shop_continue_button.text == "Continue to Shop")
	assert(score_shop_continue_button.focus_neighbor_top == score_shop_continue_button.get_path())
	assert(score_shop_continue_button.focus_neighbor_bottom == score_shop_continue_button.get_path())
	assert(score_shop_continue_button.focus_neighbor_left == score_shop_continue_button.get_path())
	assert(score_shop_continue_button.focus_neighbor_right == score_shop_continue_button.get_path())
	assert(score_shop_continue_button.disabled)
	local_match.call("_continue_from_score")
	assert(str(local_match.get("_phase")) == "score")
	local_match.call("_update_modal_activation", 2.0)
	assert(abs(float(local_match.get("_score_continue_delay"))) < 0.01)
	assert(not score_shop_continue_button.disabled)
	local_match.call("_continue_from_score")
	assert(str(local_match.get("_phase")) == "shop")
	assert(int(local_match.get("_credits")) == 92)
	var updated_leader_participants: Array = local_match.get("_participants")
	assert(bool(Dictionary(updated_leader_participants[0]).get("leader", false)))
	assert(not bool(Dictionary(updated_leader_participants[1]).get("leader", true)))
	assert(not local_match.get_node("ScoreOverlay").visible)
	var match_shop_overlay := local_match.get("_shop_overlay") as Control
	assert(match_shop_overlay.visible)
	assert(abs(float(local_match.get("_shop_input_delay")) - 0.4) < 0.01)
	assert(str(local_match.call("_shop_participant_name", local_match.call("_current_shop_participant_index"))) == "Player")
	local_match.call("_continue_from_shop")
	assert(str(local_match.get("_phase")) == "shop")
	local_match.call("_update_modal_activation", 0.4)
	assert(abs(float(local_match.get("_shop_input_delay"))) < 0.01)
	local_match.call("_continue_from_shop")
	assert(str(local_match.get("_phase")) == "aim")
	assert(int(local_match.get("_round")) == 2)
	enemy_tank.state = TankState.STATE_ALIVE
	assert(not match_shop_overlay.visible)
	assert(str(local_match.get("_message")).contains("Round 2 ready"))

	var enemy_shop_inventory: RefCounted = local_match.get("_enemy_inventory") as RefCounted
	var enemy_missile_before_shop := int(enemy_shop_inventory.ammo_for(WeaponInventory.MISSILE))
	var enemy_mirv_before_shop := int(enemy_shop_inventory.ammo_for(WeaponInventory.MIRV))
	local_match.set("_ai_difficulty", "normal")
	local_match.call("_set_shop_credits", 1, 100)
	local_match.call("_run_computer_shop_for_participant", 1)
	assert(int(local_match.call("_shop_credits", 1)) == 0)
	assert(int(enemy_shop_inventory.ammo_for(WeaponInventory.MISSILE)) == enemy_missile_before_shop + WeaponInventory.MISSILE_SHOP_PACK)
	assert(int(enemy_shop_inventory.ammo_for(WeaponInventory.MIRV)) == enemy_mirv_before_shop + WeaponInventory.MIRV_SHOP_PACK)
	assert(str(local_match.get("_message")).contains("Enemy bought"))
	local_match.set("_ai_difficulty", "easy")
	var easy_shop_priority: Array = local_match.call("_computer_shop_priority")
	assert(str(easy_shop_priority[0]) == WeaponInventory.MACHINE_GUN)
	var enemy_machine_gun_before_easy_shop := int(enemy_shop_inventory.ammo_for(WeaponInventory.MACHINE_GUN))
	var enemy_missile_before_easy_shop := int(enemy_shop_inventory.ammo_for(WeaponInventory.MISSILE))
	var enemy_fuel_reserve_before_easy_shop := float(enemy_tank.fuel_reserve)
	local_match.call("_set_shop_credits", 1, 100)
	local_match.call("_run_computer_shop_for_participant", 1)
	assert(int(local_match.call("_shop_credits", 1)) == 0)
	assert(int(enemy_shop_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == enemy_machine_gun_before_easy_shop + WeaponInventory.MACHINE_GUN_SHOP_PACK)
	assert(int(enemy_shop_inventory.ammo_for(WeaponInventory.MISSILE)) == enemy_missile_before_easy_shop + WeaponInventory.MISSILE_SHOP_PACK)
	assert(abs(float(enemy_tank.fuel_reserve) - enemy_fuel_reserve_before_easy_shop) < 0.01)
	assert(str(local_match.get("_message")).contains("Machine Gun, Missile"))
	assert(not str(local_match.get("_message")).contains("Jump Jet"))
	local_match.set("_ai_difficulty", "hard")
	var hard_shop_priority: Array = local_match.call("_computer_shop_priority")
	assert(str(hard_shop_priority[0]) == WeaponInventory.NUKE)
	var enemy_nuke_before_hard_shop := int(enemy_shop_inventory.ammo_for(WeaponInventory.NUKE))
	var enemy_mirv_before_hard_shop := int(enemy_shop_inventory.ammo_for(WeaponInventory.MIRV))
	var enemy_missile_before_hard_shop := int(enemy_shop_inventory.ammo_for(WeaponInventory.MISSILE))
	var enemy_machine_gun_before_hard_shop := int(enemy_shop_inventory.ammo_for(WeaponInventory.MACHINE_GUN))
	var enemy_fuel_reserve_before_hard_shop := float(enemy_tank.fuel_reserve)
	local_match.call("_set_shop_credits", 1, 250)
	local_match.call("_run_computer_shop_for_participant", 1)
	assert(int(local_match.call("_shop_credits", 1)) == 0)
	assert(int(enemy_shop_inventory.ammo_for(WeaponInventory.NUKE)) == enemy_nuke_before_hard_shop + WeaponInventory.NUKE_SHOP_PACK)
	assert(int(enemy_shop_inventory.ammo_for(WeaponInventory.MIRV)) == enemy_mirv_before_hard_shop + WeaponInventory.MIRV_SHOP_PACK)
	assert(int(enemy_shop_inventory.ammo_for(WeaponInventory.MISSILE)) == enemy_missile_before_hard_shop + WeaponInventory.MISSILE_SHOP_PACK)
	assert(int(enemy_shop_inventory.ammo_for(WeaponInventory.MACHINE_GUN)) == enemy_machine_gun_before_hard_shop + WeaponInventory.MACHINE_GUN_SHOP_PACK)
	assert(abs(float(enemy_tank.fuel_reserve) - (enemy_fuel_reserve_before_hard_shop + TankState.TANK_FUEL_PURCHASE_AMOUNT)) < 0.01)
	assert(str(local_match.get("_message")).contains("Nuke, MIRV, Missile, Machine Gun, Jump Jet"))
	local_match.call("_set_shop_credits", 1, 10)
	local_match.call("_run_computer_shop_for_participant", 1)
	assert(int(local_match.call("_shop_credits", 1)) == 10)
	assert(str(local_match.get("_message")) == "Enemy saved credits.")

	local_match.set("_round", int(local_match.get("_total_rounds")))
	local_match.set("_score", 180)
	local_match.set("_enemy_score", 80)
	local_match.set("_credits", 4)
	local_match.call("_open_round_score", "Round Won", 100, "Player")
	assert(abs(float(local_match.get("_score_continue_delay")) - 2.0) < 0.01)
	var score_final_continue_button := local_match.get("_score_continue_button") as Button
	assert(score_final_continue_button.text == "Continue to Final Result")
	assert(score_final_continue_button.focus_neighbor_top == score_final_continue_button.get_path())
	assert(score_final_continue_button.focus_neighbor_bottom == score_final_continue_button.get_path())
	assert(score_final_continue_button.disabled)
	local_match.call("_update_modal_activation", 2.0)
	assert(not score_final_continue_button.disabled)
	local_match.call("_continue_from_score")
	assert(str(local_match.get("_phase")) == "winner")
	assert(abs(float(local_match.get("_winner_continue_delay")) - 2.0) < 0.01)
	assert(not local_match.get_node("ScoreOverlay").visible)
	var winner_overlay := local_match.get_node("WinnerOverlay") as Control
	assert(winner_overlay.visible)
	assert(not (winner_overlay is PanelContainer))
	var winner_background_fill := winner_overlay.get_node("WinnerMenuBackgroundFill") as ColorRect
	assert(winner_background_fill.color == GroundfireTheme.COLOR_BG)
	assert(winner_background_fill.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	var winner_background := winner_overlay.get_node("WinnerMenuBackground") as TextureRect
	assert(winner_background.texture != null)
	assert(winner_background.stretch_mode == TextureRect.STRETCH_TILE)
	assert(winner_background.modulate == GroundfireTheme.COLOR_MENU_TILE_TINT)
	assert(winner_background.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	var winner_background_tile_size := winner_background.texture.get_size()
	assert(abs(winner_background.offset_left) < 0.01)
	assert(abs(winner_background.offset_top) < 0.01)
	assert(abs(winner_background.offset_right - float(winner_background_tile_size.x)) < 0.01)
	assert(abs(winner_background.offset_bottom - float(winner_background_tile_size.y)) < 0.01)
	local_match.call("_update_winner_background", 0.5)
	var expected_winner_background_offset := Vector2(
		float(int(0.5 * 0.1 * float(winner_background_tile_size.x))),
		float(int(0.5 * 0.1 * float(winner_background_tile_size.y)))
	)
	assert(abs(winner_background.offset_left + expected_winner_background_offset.x) < 0.01)
	assert(abs(winner_background.offset_top + expected_winner_background_offset.y) < 0.01)
	assert(abs((winner_background.offset_right - winner_background.offset_left) - float(winner_background_tile_size.x)) < 0.01)
	assert(abs((winner_background.offset_bottom - winner_background.offset_top) - float(winner_background_tile_size.y)) < 0.01)
	var winner_main_menu_button := local_match.get("_winner_main_menu_button") as Button
	assert(not winner_main_menu_button.visible)
	assert(winner_main_menu_button.focus_mode == Control.FOCUS_NONE)
	assert(winner_main_menu_button.disabled)
	local_match.call("_update_modal_activation", 2.0)
	assert(abs(float(local_match.get("_winner_continue_delay"))) < 0.01)
	assert(not winner_main_menu_button.disabled)
	assert(not winner_main_menu_button.visible)
	assert(winner_main_menu_button.focus_mode == Control.FOCUS_NONE)
	var winner_heading_label := local_match.get("_winner_heading_label") as Label
	assert(winner_heading_label.text == "Final Result")
	var winner_title_label := local_match.get("_winner_title_label") as Label
	assert(winner_title_label.text == "We have a winner!")
	var winner_summary_label := local_match.get("_winner_summary_label") as Label
	assert(not winner_summary_label.visible)
	assert(winner_summary_label.text == "")
	var winner_rows: Array = local_match.call("_winner_rows_snapshot")
	assert(winner_rows.size() == 2)
	assert(str(Dictionary(winner_rows[0]).get("rank", "")) == "1st")
	assert(str(Dictionary(winner_rows[0]).get("name", "")) == "Player")
	assert(str(Dictionary(winner_rows[0]).get("round_detail", "")) == "-")
	assert(bool(Dictionary(winner_rows[0]).get("winner", false)))
	assert(not bool(Dictionary(winner_rows[1]).get("winner", true)))
	var winner_cards: Array = local_match.call("_winner_card_snapshots")
	assert(winner_cards.size() == 1)
	assert(str(Dictionary(winner_cards[0]).get("name", "")) == "Player")
	assert(bool(Dictionary(winner_cards[0]).get("winner", false)))
	var winner_card_rows: Array = local_match.call("_winner_card_rows", winner_cards)
	assert(winner_card_rows.size() == 1)
	assert(Array(winner_card_rows[0]).size() == 1)
	var five_winner_card_rows: Array = local_match.call("_winner_card_rows", [
		{"name": "A"},
		{"name": "B"},
		{"name": "C"},
		{"name": "D"},
		{"name": "E"},
	])
	assert(five_winner_card_rows.size() == 2)
	assert(Array(five_winner_card_rows[0]).size() == 4)
	assert(Array(five_winner_card_rows[1]).size() == 1)
	var winner_cards_container := local_match.get("_winner_cards_container") as VBoxContainer
	assert(winner_cards_container.get_child_count() == 1)
	var first_winner_row := winner_cards_container.get_child(0) as HBoxContainer
	assert(first_winner_row.alignment == BoxContainer.ALIGNMENT_CENTER)
	assert(first_winner_row.get_child_count() == 1)
	var first_winner_card := first_winner_row.get_child(0) as VBoxContainer
	var first_winner_tank_chip := first_winner_card.get_child(0) as Control
	var first_winner_tank_shape := first_winner_tank_chip.get_child(0) as Polygon2D
	assert(first_winner_tank_shape.polygon.size() == 4)
	assert(first_winner_tank_shape.color == Color(Dictionary(winner_cards[0]).get("color", Color.WHITE)))
	var first_winner_letter_ring := first_winner_card.get_child(2) as Control
	assert(first_winner_letter_ring.name == "WinnerLetterRing")
	assert(first_winner_letter_ring.get_child_count() == 7)
	var first_winner_letter := first_winner_letter_ring.get_child(0) as Label
	var second_winner_letter := first_winner_letter_ring.get_child(1) as Label
	var last_winner_letter := first_winner_letter_ring.get_child(6) as Label
	assert(first_winner_letter.text == "W")
	assert(second_winner_letter.text == "i")
	assert(last_winner_letter.text == "!")
	assert(first_winner_letter.get_theme_color("font_color") == Color.WHITE)
	var initial_winner_letter_rotation := first_winner_letter.rotation
	local_match.call("_update_winner_spin", 0.25)
	assert(abs(first_winner_letter.rotation - (initial_winner_letter_rotation - 1.0)) < 0.01)
	var winner_rows_container := local_match.get("_winner_rows_container") as VBoxContainer
	assert(not winner_rows_container.visible)
	assert(winner_rows_container.get_child_count() == 0)
	local_match.set("_score", 300)
	local_match.set("_enemy_score", 300)
	local_match.call("_refresh_winner_overlay")
	assert(winner_title_label.text == "It's a tie!")
	var tied_winner_rows: Array = local_match.call("_winner_rows_snapshot")
	assert(bool(Dictionary(tied_winner_rows[0]).get("winner", false)))
	assert(bool(Dictionary(tied_winner_rows[1]).get("winner", false)))
	var tied_winner_cards: Array = local_match.call("_winner_card_snapshots")
	assert(tied_winner_cards.size() == 2)
	assert(winner_cards_container.get_child_count() == 1)
	var tied_winner_row := winner_cards_container.get_child(0) as HBoxContainer
	assert(tied_winner_row.alignment == BoxContainer.ALIGNMENT_CENTER)
	assert(tied_winner_row.get_child_count() == 2)
	var tied_second_card := tied_winner_row.get_child(1) as VBoxContainer
	var tied_second_letter_ring := tied_second_card.get_child(2) as Control
	assert(tied_second_letter_ring.name == "WinnerLetterRing")
	assert(tied_second_letter_ring.get_child_count() == 7)
	winner_rows_container = local_match.get("_winner_rows_container") as VBoxContainer
	assert(not winner_rows_container.visible)
	assert(winner_rows_container.get_child_count() == 0)
	local_match.call("_hide_winner_overlay")
	local_match.set("_round", 1)

	var shop := LocalMatchShop.new()
	assert(shop.call("_format_pack", 0) == "-")
	assert(shop.call("_format_pack", 5) == "+5")
	assert(Array(shop.call("_classic_catalog_rows")).is_empty())
	var disabled_shop_items: Array = shop.call("_disabled_shop_items")
	assert(disabled_shop_items.size() == 0)
	root.add_child(shop)
	await process_frame
	shop.refresh({
		"title": "Round Won",
		"round": 2,
		"total_rounds": 5,
		"score": 120,
		"reward": 100,
		"credits": 100,
		"fuel_reserve": 200,
		"inventory": [
			{"name": "Shell", "cost": 0, "ammo": -1, "damage": 40, "blast": 48},
			{"name": "Machine Gun", "cost": 50, "ammo": 50, "shop_pack": 50, "damage": 2, "blast": 0},
			{"name": "MIRV", "cost": 50, "ammo": 1, "shop_pack": 1, "damage": 22, "blast": 34},
			{"name": "Missile", "cost": 50, "ammo": 0, "shop_pack": 5, "damage": 40, "blast": 48},
			{"name": "Nuke", "cost": 50, "ammo": 1, "shop_pack": 1, "damage": 90, "blast": 96},
			{"name": "Rolling Mines", "cost": 50, "ammo": 5, "shop_pack": 5, "damage": 30, "blast": 36},
			{"name": "Airstrike", "cost": 100, "ammo": 2, "shop_pack": 2, "damage": 40, "blast": 40},
			{"name": "Death's Head", "cost": 200, "ammo": 1, "shop_pack": 1, "damage": 25, "blast": 30},
			{"name": "Hover Coil", "cost": 150, "ammo": 2, "shop_pack": 2, "damage": 0, "blast": 0},
			{"name": "Corbomite", "cost": 20, "ammo": 3, "shop_pack": 3, "damage": 0, "blast": 0},
		],
		"shop_items": [
			{"name": "Jump Jet", "cost": 50, "effect": "+100% reserve", "current": "100% reserve"},
		],
		"message": "Shop focus check",
	})
	await process_frame
	var shop_credits_label := shop.get("_credits_label") as Label
	assert(shop_credits_label.text == "Player  Money $100  Fuel reserve 200%")
	var shop_subtitle_label := shop.get("_subtitle_label") as Label
	assert(shop_subtitle_label.text == "Round 2 of 5  Score 120  Reward 100")
	var shop_weapon_list := shop.get("_weapon_list") as VBoxContainer
	var first_catalog_row := shop_weapon_list.get_child(1) as HBoxContainer
	var first_catalog_cost := first_catalog_row.get_child(0) as Label
	assert(first_catalog_cost.text == "$50")
	var first_catalog_item := first_catalog_row.get_child(1) as Label
	assert(str(first_catalog_item.text).begins_with("Machine Gun"))
	var mirv_catalog_row := shop_weapon_list.get_child(3) as HBoxContainer
	var mirv_catalog_item := mirv_catalog_row.get_child(1) as Label
	assert(str(mirv_catalog_item.text).begins_with("Mirvs"))
	var missile_catalog_row := shop_weapon_list.get_child(4) as HBoxContainer
	var missile_catalog_item := missile_catalog_row.get_child(1) as Label
	assert(str(missile_catalog_item.text).begins_with("Missiles"))
	var nuke_catalog_row := shop_weapon_list.get_child(5) as HBoxContainer
	var nuke_catalog_item := nuke_catalog_row.get_child(1) as Label
	assert(str(nuke_catalog_item.text).begins_with("Nukes"))
	var first_locked_row := shop_weapon_list.get_child(6) as HBoxContainer
	var first_locked_cost := first_locked_row.get_child(0) as Label
	assert(first_locked_cost.text == "$50")
	var first_locked_item := first_locked_row.get_child(1) as Label
	assert(str(first_locked_item.text).begins_with("Rolling Mines"))
	var shop_focus_buttons: Array = shop.get("_focus_buttons")
	assert(shop_focus_buttons.size() == 9)
	var first_shop_button: Button = shop_focus_buttons[0]
	var second_shop_button: Button = shop_focus_buttons[1]
	var third_shop_button: Button = shop_focus_buttons[2]
	assert(first_shop_button.text == "Buy")
	assert(second_shop_button.text == "Buy")
	assert(first_shop_button.focus_neighbor_bottom == second_shop_button.get_path())
	assert(first_shop_button.focus_neighbor_left == first_shop_button.get_path())
	assert(first_shop_button.focus_neighbor_right == first_shop_button.get_path())
	assert(second_shop_button.focus_neighbor_top == first_shop_button.get_path())
	assert(second_shop_button.focus_neighbor_bottom == third_shop_button.get_path())
	var shop_continue_button := shop.get("_continue_button") as Button
	assert(shop_continue_button.text == "Done!")
	var classic_rows: Array = shop.call("_classic_catalog_rows")
	assert(classic_rows.size() == 10)
	assert(str(Dictionary(classic_rows[0]).get("name", "")) == "Machine Gun")
	assert(str(Dictionary(classic_rows[1]).get("name", "")) == "Jump Jet")
	assert(str(Dictionary(classic_rows[9]).get("name", "")) == "Corbomite")
	shop.refresh({
		"title": "Round Won",
		"round": 2,
		"total_rounds": 5,
		"score": 120,
		"reward": 100,
		"credits": 100,
		"fuel_reserve": 200,
		"inventory": [
			{"name": "Machine Gun", "cost": 50, "ammo": 50, "shop_pack": 50, "damage": 2, "blast": 0},
		],
		"shop_items": [
			{"name": "Jump Jet", "cost": 50, "effect": "+100% reserve", "current": "100% reserve"},
		],
		"message": "Shop input locked",
		"input_locked": true,
	})
	await process_frame
	var locked_first_row := (shop.get("_weapon_list") as VBoxContainer).get_child(1) as HBoxContainer
	assert(bool((locked_first_row.get_child(2) as Button).disabled))
	var locked_shop_buttons: Array = shop.get("_focus_buttons")
	assert(bool((locked_shop_buttons[0] as Button).disabled))
	assert(bool((shop.get("_continue_button") as Button).disabled))
	shop.call("_remember_shop_focus", "Missile")
	shop.refresh({
		"title": "Round Won",
		"round": 2,
		"total_rounds": 5,
		"score": 120,
		"reward": 100,
		"credits": 100,
		"fuel_reserve": 200,
		"inventory": [
			{"name": "Shell", "cost": 0, "ammo": -1, "damage": 40, "blast": 48},
			{"name": "Machine Gun", "cost": 50, "ammo": 50, "shop_pack": 50, "damage": 2, "blast": 0},
			{"name": "MIRV", "cost": 50, "ammo": 1, "shop_pack": 1, "damage": 22, "blast": 34},
			{"name": "Missile", "cost": 50, "ammo": 0, "shop_pack": 5, "damage": 40, "blast": 48},
			{"name": "Nuke", "cost": 50, "ammo": 1, "shop_pack": 1, "damage": 90, "blast": 96},
		],
		"shop_items": [
			{"name": "Jump Jet", "cost": 50, "effect": "+100% reserve", "current": "100% reserve"},
		],
		"message": "Shop focus restore",
	})
	await process_frame
	var focused_shop_button := root.gui_get_focus_owner() as Button
	assert(focused_shop_button != null)
	assert(str(focused_shop_button.get_meta("shop_focus_name", "")) == "Missile")
	await _free_node(shop)

	var shop_player_tank: RefCounted = local_match.get("_player")
	local_match.set("_credits", 4)
	local_match.set("_phase", "shop")
	local_match.call("_buy_shop_weapon", "Jump Jet")
	assert(str(local_match.get("_message")) == "Need $50 for Jump Jet.")
	assert(abs(float(local_match.get("_shop_input_delay")) - 0.2) < 0.01)
	local_match.call("_update_modal_activation", 0.2)
	local_match.set("_credits", 50)
	var active_fuel_before_buy := float(shop_player_tank.fuel)
	var fuel_reserve_before_buy := float(shop_player_tank.fuel_reserve)
	local_match.call("_buy_shop_weapon", "Jump Jet")
	assert(int(local_match.get("_credits")) == 0)
	assert(abs(float(shop_player_tank.fuel_reserve) - (fuel_reserve_before_buy + TankState.TANK_FUEL_PURCHASE_AMOUNT)) < 0.01)
	assert(abs(float(shop_player_tank.fuel) - active_fuel_before_buy) < 0.01)
	assert(str(local_match.get("_message")).contains("Fuel reserve"))
	local_match.call("_refresh_shop_overlay")
	assert((local_match.get("_shop_overlay") as Control).visible)
	var shop_items: Array = local_match.call("_shop_items_snapshot")
	assert(shop_items.size() == 1)
	assert(str(Dictionary(shop_items[0]).get("name", "")) == "Jump Jet")
	assert(str(Dictionary(shop_items[0]).get("current", "")).contains("reserve"))

	local_match.call("_update_modal_activation", 0.2)
	local_match.set("_credits", 1000)
	var classic_shop_inventory: RefCounted = local_match.get("_inventory")
	var classic_shop_cases := [
		{"name": WeaponInventory.ROLLING_MINES, "cost": 50, "pack": WeaponInventory.ROLLING_MINES_SHOP_PACK},
		{"name": WeaponInventory.AIRSTRIKE, "cost": 100, "pack": WeaponInventory.AIRSTRIKE_SHOP_PACK},
		{"name": WeaponInventory.DEATHS_HEAD, "cost": 200, "pack": WeaponInventory.DEATHS_HEAD_SHOP_PACK},
		{"name": WeaponInventory.HOVER_COIL, "cost": 150, "pack": WeaponInventory.HOVER_COIL_SHOP_PACK},
		{"name": WeaponInventory.CORBOMITE, "cost": 20, "pack": WeaponInventory.CORBOMITE_SHOP_PACK},
	]
	for shop_case in classic_shop_cases:
		var item_name := str(Dictionary(shop_case).get("name", ""))
		var item_cost := int(Dictionary(shop_case).get("cost", 0))
		var item_pack := int(Dictionary(shop_case).get("pack", 0))
		var credits_before_item_buy := int(local_match.get("_credits"))
		var ammo_before_item_buy := int(classic_shop_inventory.ammo_for(item_name))
		local_match.call("_buy_shop_weapon", item_name)
		assert(int(local_match.get("_credits")) == credits_before_item_buy - item_cost)
		assert(classic_shop_inventory.ammo_for(item_name) == ammo_before_item_buy + item_pack)
		assert(str(local_match.get("_message")).contains("Bought %s ammo" % item_name))
		local_match.call("_update_modal_activation", 0.2)
	local_match.set("_credits", 19)
	var corbomite_before_failed_buy := int(classic_shop_inventory.ammo_for(WeaponInventory.CORBOMITE))
	local_match.call("_buy_shop_weapon", WeaponInventory.CORBOMITE)
	assert(int(local_match.get("_credits")) == 19)
	assert(classic_shop_inventory.ammo_for(WeaponInventory.CORBOMITE) == corbomite_before_failed_buy)
	assert(str(local_match.get("_message")) == "Need $20 for Corbomite.")
	local_match.call("_update_modal_activation", 0.2)

	var buy_inventory := WeaponInventory.new()
	assert(buy_inventory.select_by_name(WeaponInventory.MIRV))
	var mirv_before_buy := int(buy_inventory.ammo_for(WeaponInventory.MIRV))
	assert(buy_inventory.add_ammo(WeaponInventory.MIRV) == mirv_before_buy + WeaponInventory.MIRV_SHOP_PACK)
	var missile_before_buy := int(buy_inventory.ammo_for(WeaponInventory.MISSILE))
	assert(buy_inventory.add_ammo(WeaponInventory.MISSILE) == missile_before_buy + WeaponInventory.MISSILE_SHOP_PACK)
	var rolling_mines_before_buy := int(buy_inventory.ammo_for(WeaponInventory.ROLLING_MINES))
	assert(buy_inventory.add_ammo(WeaponInventory.ROLLING_MINES) == rolling_mines_before_buy + WeaponInventory.ROLLING_MINES_SHOP_PACK)
	var airstrike_before_buy := int(buy_inventory.ammo_for(WeaponInventory.AIRSTRIKE))
	assert(buy_inventory.add_ammo(WeaponInventory.AIRSTRIKE) == airstrike_before_buy + WeaponInventory.AIRSTRIKE_SHOP_PACK)
	var deaths_head_before_buy := int(buy_inventory.ammo_for(WeaponInventory.DEATHS_HEAD))
	assert(buy_inventory.add_ammo(WeaponInventory.DEATHS_HEAD) == deaths_head_before_buy + WeaponInventory.DEATHS_HEAD_SHOP_PACK)
	var hover_coil_before_buy := int(buy_inventory.ammo_for(WeaponInventory.HOVER_COIL))
	assert(buy_inventory.add_ammo(WeaponInventory.HOVER_COIL) == hover_coil_before_buy + WeaponInventory.HOVER_COIL_SHOP_PACK)
	var corbomite_before_buy := int(buy_inventory.ammo_for(WeaponInventory.CORBOMITE))
	assert(buy_inventory.add_ammo(WeaponInventory.CORBOMITE) == corbomite_before_buy + WeaponInventory.CORBOMITE_SHOP_PACK)

	var tank := TankState.new()
	assert(abs(tank.gun_angle - TankState.GUN_ANGLE_DEFAULT) < 0.01)
	assert(abs(tank.gun_power - TankState.GUN_POWER_DEFAULT) < 0.01)
	assert(tank.health == TankState.TANK_MAX_HEALTH)
	assert(abs(tank.fuel - TankState.TANK_FULL_FUEL) < 0.01)
	assert(abs(tank.fuel_capacity - TankState.TANK_FULL_FUEL) < 0.01)
	assert(abs(tank.fuel_reserve - TankState.TANK_FULL_FUEL) < 0.01)
	assert(abs(tank.add_fuel_reserve() - (TankState.TANK_FULL_FUEL + TankState.TANK_FUEL_PURCHASE_AMOUNT)) < 0.01)
	assert(abs(tank.fuel - TankState.TANK_FULL_FUEL) < 0.01)
	tank.boost(0.5)
	assert(abs(tank.fuel - 0.9) < 0.01)
	assert(abs(tank.fuel_reserve - 1.9) < 0.01)
	tank.reset_round(360.0, match_terrain, "Player", Color.WHITE)
	assert(abs(tank.tank_angle) < 0.01)
	assert(abs(tank.fuel - TankState.TANK_FULL_FUEL) < 0.01)
	assert(abs(tank.fuel_reserve - 1.9) < 0.01)
	assert(not tank.on_ground)
	tank.health = TankState.TANK_MAX_HEALTH
	assert(not bool(tank.apply_damage(100)))
	assert(tank.health == 0)
	assert(tank.state == TankState.STATE_ALIVE)
	assert(bool(tank.apply_damage(1)))
	assert(tank.state == TankState.STATE_DEAD)
	assert(abs(float(tank.exhaust_time) + 0.5) < 0.01)
	tank.position = Vector2(200.0, 320.0)
	tank.on_ground = true
	local_match.get("_smoke_particles").clear()
	local_match.call("_emit_tank_burn_smoke", tank, 0.1)
	var burn_smoke_particles: Array = local_match.get("_smoke_particles")
	assert(burn_smoke_particles.size() == 1)
	var ground_smoke: Dictionary = burn_smoke_particles[0]
	assert(Vector2(ground_smoke.get("position", Vector2.ZERO)).distance_to(Vector2(200.0, 320.0 + TankState.GROUND_SMOKE_Y_OFFSET * TankState.GUN_POWER_PIXEL_SCALE)) < 0.01)
	assert(Vector2(ground_smoke.get("velocity", Vector2.ZERO)).distance_to(Vector2(0.0, TankState.SMOKE_Y_VELOCITY * TankState.GUN_POWER_PIXEL_SCALE)) < 0.01)
	assert(int(ground_smoke.get("texture_id", -1)) == TankState.SMOKE_TEXTURE_ID)
	assert(abs(float(ground_smoke.get("rotation_rate", 0.0)) - TankState.SMOKE_ROTATION_RATE) < 0.01)
	assert(abs(float(ground_smoke.get("growth_rate", 0.0)) - TankState.GROUND_SMOKE_GROWTH_RATE) < 0.01)
	assert(abs(float(ground_smoke.get("fade_rate", 0.0)) - TankState.GROUND_SMOKE_FADE_RATE) < 0.01)
	assert(abs(float(tank.exhaust_time) - 0.5) < 0.01)
	local_match.call("_emit_tank_burn_smoke", tank, 0.1)
	assert(abs(float(tank.exhaust_time) - 0.4) < 0.01)
	tank.position = Vector2(210.0, 330.0)
	tank.on_ground = false
	tank.exhaust_time = -0.1
	local_match.get("_smoke_particles").clear()
	local_match.call("_emit_tank_burn_smoke", tank, 0.1)
	var air_smoke_particles: Array = local_match.get("_smoke_particles")
	assert(air_smoke_particles.size() == 1)
	var air_smoke: Dictionary = air_smoke_particles[0]
	assert(Vector2(air_smoke.get("position", Vector2.ZERO)).distance_to(Vector2(210.0, 330.0)) < 0.01)
	assert(Vector2(air_smoke.get("velocity", Vector2.ZERO)).distance_to(Vector2(0.0, TankState.SMOKE_Y_VELOCITY * TankState.GUN_POWER_PIXEL_SCALE)) < 0.01)
	assert(int(air_smoke.get("texture_id", -1)) == TankState.SMOKE_TEXTURE_ID)
	assert(abs(float(air_smoke.get("rotation_rate", 0.0)) - TankState.SMOKE_ROTATION_RATE) < 0.01)
	assert(abs(float(air_smoke.get("growth_rate", 0.0)) - TankState.GROUND_SMOKE_GROWTH_RATE) < 0.01)
	assert(abs(float(air_smoke.get("fade_rate", 0.0)) - TankState.AIR_SMOKE_FADE_RATE) < 0.01)
	assert(abs(float(tank.exhaust_time) + 0.05) < 0.01)
	var boost_smoke_tank := TankState.new()
	boost_smoke_tank.position = Vector2(240.0, 260.0)
	boost_smoke_tank.tank_angle = 30.0
	boost_smoke_tank.airborne_velocity = Vector2(12.0, -8.0)
	boost_smoke_tank.exhaust_time = -0.1
	local_match.get("_smoke_particles").clear()
	local_match.call("_emit_jump_jet_smoke", boost_smoke_tank, 0.1)
	var boost_smoke_particles: Array = local_match.get("_smoke_particles")
	assert(boost_smoke_particles.size() == 1)
	var boost_smoke: Dictionary = boost_smoke_particles[0]
	var expected_boost_smoke_velocity := Vector2(
		12.0 + sin(deg_to_rad(30.0)) * TankState.BOOST_SMOKE_VELOCITY * TankState.GUN_POWER_PIXEL_SCALE,
		-8.0 - cos(deg_to_rad(30.0)) * TankState.BOOST_SMOKE_VELOCITY * TankState.GUN_POWER_PIXEL_SCALE
	)
	assert(Vector2(boost_smoke.get("position", Vector2.ZERO)).distance_to(Vector2(240.0, 260.0)) < 0.01)
	assert(Vector2(boost_smoke.get("velocity", Vector2.ZERO)).distance_to(expected_boost_smoke_velocity) < 0.01)
	assert(int(boost_smoke.get("texture_id", -1)) == TankState.BOOST_SMOKE_TEXTURE_ID)
	assert(abs(float(boost_smoke.get("rotation_rate", -1.0)) - TankState.BOOST_SMOKE_ROTATION_RATE) < 0.01)
	assert(abs(float(boost_smoke.get("growth_rate", -1.0)) - TankState.BOOST_SMOKE_GROWTH_RATE) < 0.01)
	assert(abs(float(boost_smoke.get("fade_rate", 0.0)) - TankState.BOOST_SMOKE_FADE_RATE) < 0.01)
	assert(abs(float(boost_smoke_tank.exhaust_time) + 0.05) < 0.01)
	boost_smoke_tank.exhaust_time = 0.03
	local_match.call("_emit_jump_jet_smoke", boost_smoke_tank, 0.1)
	assert(boost_smoke_particles.size() == 1)
	assert(abs(float(boost_smoke_tank.exhaust_time) + 0.07) < 0.01)
	var smoke_draw_points: PackedVector2Array = local_match.call("_smoke_particle_draw_points", {
		"position": Vector2(10.0, 20.0),
		"size": 0.25,
		"rotation": 0.0,
	})
	var smoke_half_size := TankState.TANK_BODY_HALF_WIDTH * 0.25
	assert(smoke_draw_points.size() == 4)
	assert(smoke_draw_points[0].distance_to(Vector2(10.0 - smoke_half_size, 20.0 - smoke_half_size)) < 0.01)
	assert(smoke_draw_points[2].distance_to(Vector2(10.0 + smoke_half_size, 20.0 + smoke_half_size)) < 0.01)
	var smoke_draw_uvs: PackedVector2Array = local_match.call("_smoke_particle_draw_uvs")
	assert(smoke_draw_uvs.size() == 4)
	assert(smoke_draw_uvs[0] == Vector2.ZERO)
	assert(smoke_draw_uvs[2] == Vector2(64.0, 64.0))
	var shield_tank := TankState.new()
	shield_tank.fuel = TankState.TANK_FULL_FUEL
	shield_tank.fuel_reserve = TankState.TANK_FULL_FUEL
	shield_tank.update_shield(true, 0.5)
	assert(bool(shield_tank.shield_active))
	assert(abs(shield_tank.fuel - (TankState.TANK_FULL_FUEL - TankState.SHIELD_FUEL_USAGE_RATE * 0.5)) < 0.01)
	assert(abs(shield_tank.fuel_reserve - (TankState.TANK_FULL_FUEL - TankState.SHIELD_FUEL_USAGE_RATE * 0.5)) < 0.01)
	assert(int(shield_tank.damage_after_shield(40)) == 20)
	shield_tank.update_shield(false, 0.0)
	assert(not bool(shield_tank.shield_active))
	player_tank.fuel = TankState.TANK_FULL_FUEL
	player_tank.fuel_reserve = TankState.TANK_FULL_FUEL
	player_tank.shield_active = false
	local_match.call("_set_turn_index", 0)
	local_match.set("_phase", "aim")
	Input.action_press("gf_shield")
	local_match.call("_update_shields", 0.25)
	Input.action_release("gf_shield")
	assert(bool(player_tank.shield_active))
	assert(float(player_tank.fuel) < TankState.TANK_FULL_FUEL)
	local_match.call("_update_shields", 0.0)
	assert(not bool(player_tank.shield_active))
	tank.gun_angle = TankState.GUN_ANGLE_DEFAULT
	tank.gun_power = TankState.GUN_POWER_DEFAULT
	tank.gun_angle_change_speed = 30.0
	tank.gun_power_change_speed = 12.0
	tank.update_gun(0.1, 0.0, 0.0)
	assert(tank.gun_angle_change_speed == 0.0)
	assert(tank.gun_power_change_speed == 0.0)
	assert(abs(tank.gun_angle - TankState.GUN_ANGLE_DEFAULT) < 0.01)
	assert(abs(tank.gun_power - TankState.GUN_POWER_DEFAULT) < 0.01)
	tank.update_gun(0.5, 1.0, 1.0)
	assert(abs(tank.gun_angle_change_speed - 30.0) < 0.01)
	assert(abs(tank.gun_power_change_speed - 10.0) < 0.01)
	assert(abs(tank.gun_angle - 15.0) < 0.01)
	assert(abs(tank.gun_power - 15.0) < 0.01)
	tank.gun_angle = 74.0
	tank.gun_power = 19.0
	tank.gun_angle_change_speed = 75.0
	tank.gun_power_change_speed = 50.0
	tank.update_gun(1.0, 1.0, 1.0)
	assert(abs(tank.gun_angle - TankState.GUN_ANGLE_MAX) < 0.01)
	assert(abs(tank.gun_power - TankState.GUN_POWER_MAX) < 0.01)
	tank.gun_angle = -74.0
	tank.gun_power = 2.0
	tank.gun_angle_change_speed = -75.0
	tank.gun_power_change_speed = -50.0
	tank.update_gun(1.0, -1.0, -1.0)
	assert(abs(tank.gun_angle - TankState.GUN_ANGLE_MIN) < 0.01)
	assert(abs(tank.gun_power - TankState.GUN_POWER_MIN) < 0.01)
	tank.tank_angle = 30.0
	tank.fuel = 1.0
	tank.on_ground = true
	tank.airborne_velocity = Vector2.ZERO
	tank.state = TankState.STATE_ALIVE
	tank.boost(0.5)
	assert(not tank.on_ground)
	assert(abs(tank.airborne_velocity.x + 33.25) < 0.01)
	assert(abs(tank.airborne_velocity.y + 57.5907) < 0.01)
	assert(abs(tank.fuel - 0.9) < 0.01)
	assert(abs(tank.tank_angle) < 0.01)
	tank.tank_angle = 0.0
	tank.fuel = 1.0
	tank.on_ground = true
	tank.airborne_velocity = Vector2.ZERO
	tank.boost(0.1, -1.0)
	assert(abs(tank.tank_angle - 9.0) < 0.01)
	tank.boost(0.1, 1.0)
	assert(abs(tank.tank_angle) < 0.01)
	tank.position = Vector2(120.0, 80.0)
	tank.tank_angle = 30.0
	tank.gun_angle = -20.0
	var tank_center := tank.tank_center()
	var expected_tank_center := Vector2(
		120.0 - sin(deg_to_rad(30.0)) * TankState.TANK_CENTER_OFFSET,
		80.0 - cos(deg_to_rad(30.0)) * TankState.TANK_CENTER_OFFSET
	)
	assert(tank_center.distance_to(expected_tank_center) < 0.01)
	var tank_launch_origin := tank.launch_origin()
	var expected_launch_origin := expected_tank_center + Vector2(
		-sin(deg_to_rad(-20.0)),
		-cos(deg_to_rad(-20.0))
	) * TankState.GUN_LAUNCH_OFFSET
	assert(tank_launch_origin.distance_to(expected_launch_origin) < 0.01)
	tank.gun_power = 10.0
	var expected_arrow_direction := Vector2(
		-sin(deg_to_rad(-20.0)),
		-cos(deg_to_rad(-20.0))
	)
	var arrow_geometry: Dictionary = local_match.call("_tank_gun_arrow_geometry", tank)
	var arrow_center: Vector2 = arrow_geometry.get("center", Vector2.ZERO)
	var arrow_shaft_start: Vector2 = arrow_geometry.get("shaft_start", Vector2.ZERO)
	var arrow_head_tip: Vector2 = arrow_geometry.get("head_tip", Vector2.ZERO)
	var arrow_length := float(arrow_geometry.get("arrow_length", 0.0))
	var arrow_shaft_polygon: PackedVector2Array = arrow_geometry.get("shaft_polygon", PackedVector2Array())
	var arrow_head_polygon: PackedVector2Array = arrow_geometry.get("head_polygon", PackedVector2Array())
	var expected_arrow_start_offset := TankState.TANK_BODY_HALF_WIDTH * 1.5
	var expected_arrow_length := TankState.TANK_BODY_HALF_WIDTH * 2.0 + tank.gun_power * TankState.TANK_BODY_HALF_WIDTH * 0.5
	var expected_shaft_width := TankState.TANK_BODY_HALF_WIDTH * 0.8
	var expected_head_width := TankState.TANK_BODY_HALF_WIDTH * 1.6
	assert(arrow_center.distance_to(expected_tank_center) < 0.01)
	assert(abs(arrow_length - expected_arrow_length) < 0.01)
	assert(arrow_shaft_start.distance_to(expected_tank_center + expected_arrow_direction * expected_arrow_start_offset) < 0.01)
	assert(arrow_head_tip.distance_to(expected_tank_center + expected_arrow_direction * arrow_length * 1.25) < 0.01)
	assert(arrow_shaft_start.distance_to(tank.position + expected_arrow_direction * expected_arrow_start_offset) > 1.0)
	assert(arrow_shaft_polygon.size() == 4)
	assert(arrow_head_polygon.size() == 3)
	assert(abs(arrow_shaft_polygon[0].distance_to(arrow_shaft_polygon[3]) - expected_shaft_width) < 0.01)
	assert(abs(arrow_head_polygon[0].distance_to(arrow_head_polygon[2]) - expected_head_width) < 0.01)
	tank.gun_angle = 0.0
	tank.airborne_velocity = Vector2(12.0, -8.0)
	var tank_launch_velocity := tank.launch_velocity(10.0, 4.2)
	assert(abs(tank_launch_velocity.x - 12.0) < 0.01)
	assert(abs(tank_launch_velocity.y + 239.0) < 0.01)
	tank.position = Vector2(120.0, 80.0)
	tank.airborne_velocity = Vector2(12.0, -8.0)
	tank.fuel = 0.5
	tank.fuel_reserve = 0.5
	tank.on_ground = false
	tank.move_on_terrain(1.0, 0.5, match_terrain)
	assert(tank.airborne_velocity == Vector2(12.0, -8.0))
	assert(abs(tank.fuel - 0.5) < 0.01)
	assert(abs(tank.fuel_reserve - 0.5) < 0.01)

	# Fidelity target: Landscape.move_to_ground() lines 438-458 (Python).
	# The query y selects which stacked chunk is reachable; TerrainModel.height_at()
	# still reports the highest surface, but move_to_ground can resolve a lower
	# support when the query is already below the upper cap.
	var stacked_ground_terrain := TerrainModel.new()
	stacked_ground_terrain.set("_width", 70.0)
	stacked_ground_terrain.set("_height", 120.0)
	stacked_ground_terrain.set("_step", 70.0)
	var stacked_upper: Dictionary = stacked_ground_terrain.call(
		"_make_chunk",
		20.0,
		20.0,
		40.0,
		40.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	var stacked_lower: Dictionary = stacked_ground_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		100.0,
		100.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	stacked_ground_terrain.set("_chunks", [[stacked_upper, stacked_lower]])
	assert(abs(float(stacked_ground_terrain.height_at(35.0)) - 20.0) < 0.01)
	assert(abs(float(stacked_ground_terrain.move_to_ground(35.0, 0.0)) - 20.0) < 0.01)
	assert(abs(float(stacked_ground_terrain.move_to_ground(35.0, 30.0)) - 20.0) < 0.01)
	assert(abs(float(stacked_ground_terrain.move_to_ground(35.0, 50.0)) - 60.0) < 0.01)
	assert(abs(float(stacked_ground_terrain.move_to_ground(35.0, 80.0)) - 60.0) < 0.01)
	var stacked_landing_tank := TankState.new()
	stacked_landing_tank.position = Vector2(35.0, 65.0)
	stacked_landing_tank.airborne_velocity = Vector2.ZERO
	stacked_landing_tank.on_ground = false
	stacked_landing_tank.settle_on_terrain(stacked_ground_terrain, 0.0)
	assert(stacked_landing_tank.on_ground)
	assert(abs(stacked_landing_tank.position.y - 60.0) < 0.01)

	var terrain := TerrainModel.new()
	terrain.rebuild_with_seed(320.0, 240.0, 1401)
	tank.position = Vector2(160.0, 20.0)
	tank.tank_angle = 12.0
	tank.airborne_velocity = Vector2(4.0, -10.0)
	tank.on_ground = false
	tank.settle_on_terrain(terrain, 0.1)
	assert(abs(tank.airborne_velocity.y + 0.5) < 0.01)
	assert(abs(tank.position.x - 160.4) < 0.01)
	assert(abs(tank.position.y - 19.95) < 0.01)
	assert(abs(tank.tank_angle - 12.0) < 0.01)
	assert(not tank.on_ground)
	var flat_terrain := FlatTerrain.new()
	tank.position = Vector2(80.0, 100.0)
	tank.airborne_velocity = Vector2.ZERO
	tank.on_ground = true
	flat_terrain.ground_y = 101.0
	tank.settle_on_terrain(flat_terrain, 0.1)
	assert(tank.on_ground)
	assert(abs(tank.position.y - 101.0) < 0.01)
	flat_terrain.ground_y = 106.0
	tank.settle_on_terrain(flat_terrain, 0.1)
	assert(not tank.on_ground)
	assert(abs(tank.position.y - 101.0) < 0.01)
	assert(tank.airborne_velocity == Vector2.ZERO)
	tank.settle_on_terrain(flat_terrain, 0.3)
	assert(tank.on_ground)
	assert(tank.airborne_velocity == Vector2.ZERO)
	assert(abs(tank.position.y - 106.0) < 0.01)
	flat_terrain.ground_y = 100.0
	flat_terrain.slope_angle = 29.0
	tank.position = Vector2(120.0, 100.0)
	tank.tank_angle = 29.0
	tank.on_ground = true
	tank.state = TankState.STATE_ALIVE
	tank.settle_on_terrain(flat_terrain, 1.0)
	assert(abs(tank.position.x - 120.0) < 0.01)
	var positive_slope_terrain := SlopedTerrain.new(120.0, 100.0, 31.0)
	var passive_positive_delta := -TankState.TANK_MOVE_SPEED * (31.0 / TankState.TANK_SLOPE_DRAG_SCALE)
	var passive_positive_x := 120.0 + cos(deg_to_rad(31.0)) * passive_positive_delta
	tank.tank_angle = 31.0
	tank.position = positive_slope_terrain.tank_position(120.0)
	tank.settle_on_terrain(positive_slope_terrain, 1.0)
	assert(abs(tank.position.x - passive_positive_x) < 0.01)
	assert(abs(tank.position.y - positive_slope_terrain.height_at(passive_positive_x)) < 0.01)
	assert(abs(tank.tank_angle - 31.0) < 0.01)
	var negative_slope_terrain := SlopedTerrain.new(120.0, 100.0, -31.0)
	var passive_negative_delta := -TankState.TANK_MOVE_SPEED * (-31.0 / TankState.TANK_SLOPE_DRAG_SCALE)
	var passive_negative_x := 120.0 + cos(deg_to_rad(-31.0)) * passive_negative_delta
	tank.tank_angle = -31.0
	tank.position = negative_slope_terrain.tank_position(120.0)
	tank.settle_on_terrain(negative_slope_terrain, 1.0)
	assert(abs(tank.position.x - passive_negative_x) < 0.01)
	assert(abs(tank.position.y - negative_slope_terrain.height_at(passive_negative_x)) < 0.01)
	tank.tank_angle = 31.0
	tank.fuel = 1.0
	tank.fuel_reserve = 1.0
	tank.on_ground = true
	tank.position = positive_slope_terrain.tank_position(120.0)
	var right_track_delta := TankState.TANK_MOVE_SPEED * (1.0 - 31.0 / TankState.TANK_SLOPE_DRAG_SCALE)
	var right_expected_x := 120.0 + cos(deg_to_rad(31.0)) * right_track_delta
	tank.move_on_terrain(1.0, 1.0, positive_slope_terrain)
	assert(abs(tank.position.x - right_expected_x) < 0.01)
	assert(abs(tank.position.y - positive_slope_terrain.height_at(right_expected_x)) < 0.01)
	assert(abs(tank.fuel - 1.0) < 0.01)
	assert(abs(tank.fuel_reserve - 1.0) < 0.01)
	tank.position = positive_slope_terrain.tank_position(120.0)
	tank.fuel = 1.0
	tank.fuel_reserve = 1.0
	var left_track_delta := TankState.TANK_MOVE_SPEED * (-1.0 - 31.0 / TankState.TANK_SLOPE_DRAG_SCALE)
	var left_expected_x := 120.0 + cos(deg_to_rad(31.0)) * left_track_delta
	tank.move_on_terrain(-1.0, 1.0, positive_slope_terrain)
	assert(abs(tank.position.x - left_expected_x) < 0.01)
	assert(abs(tank.position.y - positive_slope_terrain.height_at(left_expected_x)) < 0.01)
	flat_terrain.ground_y = 200.0
	flat_terrain.slope_angle = 0.0
	tank.position = Vector2(20.0, 80.0)
	tank.airborne_velocity = Vector2(-30.0, 0.0)
	tank.on_ground = false
	tank.settle_on_terrain(flat_terrain, 0.1)
	assert(abs(tank.position.x - 30.0) < 0.01)
	assert(abs(tank.airborne_velocity.x) < 0.01)
	assert(not tank.on_ground)
	tank.position = Vector2(205.0, 80.0)
	tank.airborne_velocity = Vector2(30.0, 0.0)
	tank.on_ground = false
	tank.settle_on_terrain(flat_terrain, 0.1)
	assert(abs(tank.position.x - 190.0) < 0.01)
	assert(abs(tank.airborne_velocity.x) < 0.01)
	var terrain_x := 160.0
	var before_drop := float(terrain.height_at(terrain_x))
	terrain.drop_terrain(12.0)
	var after_drop := float(terrain.height_at(terrain_x))
	var floor_y := float(terrain.call("_world_height_to_screen", -7.0))
	assert(after_drop >= before_drop)
	assert(after_drop <= floor_y + 0.01)
	if before_drop + 12.0 < floor_y:
		assert(abs(after_drop - (before_drop + 12.0)) < 0.01)
	terrain.drop_terrain(10000.0)
	assert(abs(float(terrain.height_at(terrain_x)) - floor_y) < 0.01)

	var min_land_clip_terrain := TerrainModel.new()
	min_land_clip_terrain.set("_height", 100.0)
	min_land_clip_terrain.set("_step", 10.0)
	var deep_base_chunk: Dictionary = min_land_clip_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	var min_land_screen_y := float(min_land_clip_terrain.call("_world_height_to_screen", TerrainModel.CLASSIC_MIN_LAND_HEIGHT))
	assert(int(min_land_clip_terrain.call("_bottom_blast_state_for_chunk_side", deep_base_chunk, true, Vector2(5.0, 60.0), 80.0, 0.0)) == 1)
	min_land_clip_terrain.set("_chunks", [[deep_base_chunk]])
	min_land_clip_terrain.call("_clip_slice", 0, Vector2(5.0, 40.0), 30.0)
	var min_land_clip_chunks: Array = min_land_clip_terrain.get("_chunks")
	assert(Array(min_land_clip_chunks[0]).size() == 1)
	var min_land_preserved_chunk: Dictionary = Array(min_land_clip_chunks[0])[0]
	assert(abs(float(min_land_preserved_chunk.get("top_left", 0.0)) - min_land_screen_y) < 0.01)
	assert(abs(float(min_land_preserved_chunk.get("top_right", 0.0)) - min_land_screen_y) < 0.01)
	assert(abs(float(min_land_preserved_chunk.get("bottom_left", 0.0)) - 90.0) < 0.01)
	assert(abs(float(min_land_preserved_chunk.get("bottom_right", 0.0)) - 90.0) < 0.01)

	var support_cut_terrain := TerrainModel.new()
	support_cut_terrain.set("_step", 10.0)
	var supported_cap: Dictionary = support_cut_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var supported_base: Dictionary = support_cut_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	support_cut_terrain.set("_chunks", [[supported_cap, supported_base]])
	support_cut_terrain.call("_clip_slice", 0, Vector2(5.0, 35.0), 10.0)
	var support_cut_chunks: Array = support_cut_terrain.get("_chunks")
	var detached_cap: Dictionary = Array(support_cut_chunks[0])[0]
	var detached_base: Dictionary = Array(support_cut_chunks[0])[1]
	assert(bool(detached_cap.get("falling", false)))
	assert(abs(float(detached_cap.get("wait", 0.0)) - 0.1) < 0.01)
	assert(not bool(detached_cap.get("linked_to_next", true)))
	assert(not bool(detached_base.get("falling", true)))

	var inherited_motion_terrain := TerrainModel.new()
	inherited_motion_terrain.set("_step", 10.0)
	var falling_cap: Dictionary = inherited_motion_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	falling_cap["falling"] = true
	falling_cap["wait"] = 0.25
	falling_cap["speed"] = 42.0
	var carried_base: Dictionary = inherited_motion_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	inherited_motion_terrain.set("_chunks", [[falling_cap, carried_base]])
	inherited_motion_terrain.call("_clip_slice", 0, Vector2(5.0, 35.0), 10.0)
	var inherited_motion_chunks: Array = inherited_motion_terrain.get("_chunks")
	var inherited_cap: Dictionary = Array(inherited_motion_chunks[0])[0]
	var inherited_base: Dictionary = Array(inherited_motion_chunks[0])[1]
	assert(bool(inherited_cap.get("falling", false)))
	assert(abs(float(inherited_cap.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(inherited_cap.get("speed", 0.0)) - 42.0) < 0.01)
	assert(bool(inherited_base.get("falling", false)))
	assert(abs(float(inherited_base.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(inherited_base.get("speed", 0.0)) - 42.0) < 0.01)

	var removed_link_terrain := TerrainModel.new()
	removed_link_terrain.set("_step", 10.0)
	var removable_cap: Dictionary = removed_link_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var surviving_base: Dictionary = removed_link_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	var propagated_base: Dictionary = surviving_base.duplicate(true)
	removed_link_terrain.call("_propagate_removed_linked_top", propagated_base, removable_cap)
	assert(abs(float(propagated_base.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(propagated_base.get("top_right", 0.0)) - 10.0) < 0.01)
	removed_link_terrain.set("_chunks", [[removable_cap, surviving_base]])
	removed_link_terrain.call("_clip_slice", 0, Vector2(5.0, 20.0), sqrt(125.0))
	var removed_link_chunks: Array = removed_link_terrain.get("_chunks")
	assert(Array(removed_link_chunks[0]).size() == 1)

	# Fidelity target: Landscape.clip_slice() lines 286-410 (Python). A fully
	# removed linked cap promotes the cut into the following chunk, which is then
	# clipped to the lower crater edge during the same pass instead of keeping the
	# original pre-blast cap top.
	var removed_link_cut_top_terrain := TerrainModel.new()
	removed_link_cut_top_terrain.set("_step", 10.0)
	var removable_cut_cap: Dictionary = removed_link_cut_top_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var surviving_cut_base: Dictionary = removed_link_cut_top_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	removed_link_cut_top_terrain.set("_chunks", [[removable_cut_cap, surviving_cut_base]])
	removed_link_cut_top_terrain.call("_clip_slice", 0, Vector2(5.0, 20.0), sqrt(200.0))
	var removed_link_cut_top_chunks: Array = removed_link_cut_top_terrain.get("_chunks")
	assert(Array(removed_link_cut_top_chunks[0]).size() == 1)
	var promoted_cut_base: Dictionary = Array(removed_link_cut_top_chunks[0])[0]
	var expected_promoted_top := 20.0 + sqrt(175.0)
	assert(abs(float(promoted_cut_base.get("top_left", 0.0)) - expected_promoted_top) < 0.01)
	assert(abs(float(promoted_cut_base.get("top_right", 0.0)) - expected_promoted_top) < 0.01)
	assert(abs(float(promoted_cut_base.get("top_left", 0.0)) - 10.0) > 0.5)

	# Fidelity target: Landscape.clip_slice() lines 280-288 (Python), the
	# top_code in (3, 6, 7) branch. A blast that reaches only the left top edge
	# lowers that edge to the crater boundary while preserving the opposite side.
	var one_sided_top_cut_terrain := TerrainModel.new()
	one_sided_top_cut_terrain.set("_step", 10.0)
	var one_sided_top_chunk: Dictionary = one_sided_top_cut_terrain.call(
		"_make_chunk",
		20.0,
		10.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	one_sided_top_cut_terrain.set("_chunks", [[one_sided_top_chunk]])
	one_sided_top_cut_terrain.call("_clip_slice", 0, Vector2(0.0, 20.0), 5.0)
	var one_sided_top_chunks: Array = one_sided_top_cut_terrain.get("_chunks")
	assert(Array(one_sided_top_chunks[0]).size() == 1)
	var one_sided_top_result: Dictionary = Array(one_sided_top_chunks[0])[0]
	assert(abs(float(one_sided_top_result.get("top_left", 0.0)) - 25.0) < 0.01)
	assert(abs(float(one_sided_top_result.get("top_right", 0.0)) - 10.0) < 0.01)
	assert(abs(float(one_sided_top_result.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(one_sided_top_result.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(one_sided_top_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 285-288 (Python), the
	# top_code in (9, 12, 13) branch. This mirrors the one-sided top-edge case
	# on the right side.
	var right_top_cut_terrain := TerrainModel.new()
	right_top_cut_terrain.set("_step", 10.0)
	var right_top_chunk: Dictionary = right_top_cut_terrain.call(
		"_make_chunk",
		10.0,
		20.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	right_top_cut_terrain.set("_chunks", [[right_top_chunk]])
	right_top_cut_terrain.call("_clip_slice", 0, Vector2(10.0, 20.0), 5.0)
	var right_top_chunks: Array = right_top_cut_terrain.get("_chunks")
	assert(Array(right_top_chunks[0]).size() == 1)
	var right_top_result: Dictionary = Array(right_top_chunks[0])[0]
	assert(abs(float(right_top_result.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(right_top_result.get("top_right", 0.0)) - 25.0) < 0.01)
	assert(abs(float(right_top_result.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(right_top_result.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(right_top_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 280-284 (Python), the
	# top_code = 6 branch. Neither top endpoint is inside the blast, but the
	# classic endpoint-code rule still cuts the left top edge.
	var top_code_6_terrain := TerrainModel.new()
	top_code_6_terrain.set("_step", 10.0)
	var top_code_6_chunk: Dictionary = top_code_6_terrain.call(
		"_make_chunk",
		10.0,
		30.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	top_code_6_terrain.set("_chunks", [[top_code_6_chunk]])
	top_code_6_terrain.call("_clip_slice", 0, Vector2(5.0, 20.0), 6.0)
	var top_code_6_chunks: Array = top_code_6_terrain.get("_chunks")
	assert(Array(top_code_6_chunks[0]).size() == 1)
	var top_code_6_result: Dictionary = Array(top_code_6_chunks[0])[0]
	var expected_top_code_6_left := 20.0 + sqrt(11.0)
	assert(abs(float(top_code_6_result.get("top_left", 0.0)) - expected_top_code_6_left) < 0.01)
	assert(abs(float(top_code_6_result.get("top_right", 0.0)) - 30.0) < 0.01)
	assert(abs(float(top_code_6_result.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(top_code_6_result.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(top_code_6_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 285-288 (Python), the
	# top_code = 9 mirror of the endpoint-code top cut.
	var top_code_9_terrain := TerrainModel.new()
	top_code_9_terrain.set("_step", 10.0)
	var top_code_9_chunk: Dictionary = top_code_9_terrain.call(
		"_make_chunk",
		30.0,
		10.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	top_code_9_terrain.set("_chunks", [[top_code_9_chunk]])
	top_code_9_terrain.call("_clip_slice", 0, Vector2(5.0, 20.0), 6.0)
	var top_code_9_chunks: Array = top_code_9_terrain.get("_chunks")
	assert(Array(top_code_9_chunks[0]).size() == 1)
	var top_code_9_result: Dictionary = Array(top_code_9_chunks[0])[0]
	var expected_top_code_9_right := 20.0 + sqrt(11.0)
	assert(abs(float(top_code_9_result.get("top_left", 0.0)) - 30.0) < 0.01)
	assert(abs(float(top_code_9_result.get("top_right", 0.0)) - expected_top_code_9_right) < 0.01)
	assert(abs(float(top_code_9_result.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(top_code_9_result.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(top_code_9_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 291-298 (Python), the
	# top_code = 11 case (state2 = 2, state1 = 3).
	var top_code_11_terrain := TerrainModel.new()
	top_code_11_terrain.set("_step", 10.0)
	var top_code_11_chunk: Dictionary = top_code_11_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	top_code_11_terrain.set("_chunks", [[top_code_11_chunk]])
	top_code_11_terrain.call("_clip_slice", 0, Vector2(2.0, 15.0), 8.01)
	var top_code_11_chunks: Array = top_code_11_terrain.get("_chunks")
	assert(Array(top_code_11_chunks[0]).size() == 1)
	var top_code_11_result: Dictionary = Array(top_code_11_chunks[0])[0]
	var expected_top_code_11_left := 15.0 + sqrt(64.1601 - 4.0)
	var expected_top_code_11_right := 15.0 + sqrt(64.1601 - 64.0)
	assert(abs(float(top_code_11_result.get("top_left", 0.0)) - expected_top_code_11_left) < 0.01)
	assert(abs(float(top_code_11_result.get("top_right", 0.0)) - expected_top_code_11_right) < 0.01)
	assert(abs(float(top_code_11_result.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(top_code_11_result.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(top_code_11_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 291-298 (Python), the
	# top_code = 14 case (state2 = 3, state1 = 2).
	var top_code_14_terrain := TerrainModel.new()
	top_code_14_terrain.set("_step", 10.0)
	var top_code_14_chunk: Dictionary = top_code_14_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	top_code_14_terrain.set("_chunks", [[top_code_14_chunk]])
	top_code_14_terrain.call("_clip_slice", 0, Vector2(8.0, 15.0), 8.01)
	var top_code_14_chunks: Array = top_code_14_terrain.get("_chunks")
	assert(Array(top_code_14_chunks[0]).size() == 1)
	var top_code_14_result: Dictionary = Array(top_code_14_chunks[0])[0]
	var expected_top_code_14_left := 15.0 + sqrt(64.1601 - 64.0)
	var expected_top_code_14_right := 15.0 + sqrt(64.1601 - 4.0)
	assert(abs(float(top_code_14_result.get("top_left", 0.0)) - expected_top_code_14_left) < 0.01)
	assert(abs(float(top_code_14_result.get("top_right", 0.0)) - expected_top_code_14_right) < 0.01)
	assert(abs(float(top_code_14_result.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(top_code_14_result.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(top_code_14_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() plus Landscape.calculate_colour()
	# (Python). Top and bottom cuts interpolate the changed edge colour along
	# the original vertical gradient instead of keeping a flat fill colour.
	var top_colour_cut_terrain := TerrainModel.new()
	top_colour_cut_terrain.set("_step", 10.0)
	var top_colour_chunk: Dictionary = top_colour_cut_terrain.call(
		"_make_chunk",
		20.0,
		10.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	top_colour_cut_terrain.set("_chunks", [[top_colour_chunk]])
	top_colour_cut_terrain.call("_clip_slice", 0, Vector2(0.0, 20.0), 5.0)
	var top_colour_chunks: Array = top_colour_cut_terrain.get("_chunks")
	var top_colour_result: Dictionary = Array(top_colour_chunks[0])[0]
	assert(Color(top_colour_result.get("top_left_color", Color.TRANSPARENT)).is_equal_approx(Color(0.875, 0.875, 0.875)))
	assert(Color(top_colour_result.get("top_right_color", Color.TRANSPARENT)).is_equal_approx(Color.WHITE))
	assert(Color(top_colour_result.get("bottom_left_color", Color.TRANSPARENT)).is_equal_approx(Color.BLACK))

	var bottom_colour_cut_terrain := TerrainModel.new()
	bottom_colour_cut_terrain.set("_step", 10.0)
	var bottom_colour_chunk: Dictionary = bottom_colour_cut_terrain.call(
		"_make_chunk",
		20.0,
		20.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	bottom_colour_cut_terrain.set("_chunks", [[bottom_colour_chunk]])
	bottom_colour_cut_terrain.call("_clip_slice", 0, Vector2(0.0, 60.0), 5.0)
	var bottom_colour_chunks: Array = bottom_colour_cut_terrain.get("_chunks")
	var bottom_colour_result: Dictionary = Array(bottom_colour_chunks[0])[0]
	assert(Color(bottom_colour_result.get("bottom_left_color", Color.TRANSPARENT)).is_equal_approx(Color(0.125, 0.125, 0.125)))
	assert(Color(bottom_colour_result.get("top_left_color", Color.TRANSPARENT)).is_equal_approx(Color.WHITE))
	assert(Color(bottom_colour_result.get("bottom_right_color", Color.TRANSPARENT)).is_equal_approx(Color.BLACK))

	# Fidelity target: Landscape.clip_slice() lines 291-298 (Python), the
	# top_code in (11, 14, 15) branch. When both top edges are clipped, both
	# move to the crater boundary while the bottom edge/resting state survives.
	var two_sided_top_cut_terrain := TerrainModel.new()
	two_sided_top_cut_terrain.set("_step", 10.0)
	var two_sided_top_chunk: Dictionary = two_sided_top_cut_terrain.call(
		"_make_chunk",
		20.0,
		20.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	two_sided_top_cut_terrain.set("_chunks", [[two_sided_top_chunk]])
	two_sided_top_cut_terrain.call("_clip_slice", 0, Vector2(5.0, 20.0), 6.0)
	var two_sided_top_chunks: Array = two_sided_top_cut_terrain.get("_chunks")
	assert(Array(two_sided_top_chunks[0]).size() == 1)
	var two_sided_top_result: Dictionary = Array(two_sided_top_chunks[0])[0]
	var expected_two_sided_top := 20.0 + sqrt(11.0)
	assert(abs(float(two_sided_top_result.get("top_left", 0.0)) - expected_two_sided_top) < 0.01)
	assert(abs(float(two_sided_top_result.get("top_right", 0.0)) - expected_two_sided_top) < 0.01)
	assert(abs(float(two_sided_top_result.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(two_sided_top_result.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(two_sided_top_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 280-288 and 408-415
	# (Python). A top-only cut on a linked cap keeps the cap linked to its
	# support because no bottom-code branch detaches the superblock.
	var linked_left_top_cut_terrain := TerrainModel.new()
	linked_left_top_cut_terrain.set("_step", 10.0)
	var linked_left_top_cap: Dictionary = linked_left_top_cut_terrain.call(
		"_make_chunk",
		20.0,
		10.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var linked_left_top_base: Dictionary = linked_left_top_cut_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	linked_left_top_cut_terrain.set("_chunks", [[linked_left_top_cap, linked_left_top_base]])
	linked_left_top_cut_terrain.call("_clip_slice", 0, Vector2(0.0, 20.0), 5.0)
	var linked_left_top_chunks: Array = linked_left_top_cut_terrain.get("_chunks")
	assert(Array(linked_left_top_chunks[0]).size() == 2)
	var linked_left_top_result_cap: Dictionary = Array(linked_left_top_chunks[0])[0]
	var linked_left_top_result_base: Dictionary = Array(linked_left_top_chunks[0])[1]
	assert(abs(float(linked_left_top_result_cap.get("top_left", 0.0)) - 25.0) < 0.01)
	assert(abs(float(linked_left_top_result_cap.get("top_right", 0.0)) - 10.0) < 0.01)
	assert(abs(float(linked_left_top_result_cap.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(linked_left_top_result_cap.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(bool(linked_left_top_result_cap.get("linked_to_next", false)))
	assert(not bool(linked_left_top_result_cap.get("falling", true)))
	assert(abs(float(linked_left_top_result_cap.get("wait", -1.0))) < 0.01)
	assert(abs(float(linked_left_top_result_cap.get("speed", -1.0))) < 0.01)
	assert(abs(float(linked_left_top_result_base.get("top_left", 0.0)) - 60.0) < 0.01)
	assert(not bool(linked_left_top_result_base.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 285-288 and 408-415
	# (Python), the right-edge mirror of the linked top-only cut.
	var linked_right_top_cut_terrain := TerrainModel.new()
	linked_right_top_cut_terrain.set("_step", 10.0)
	var linked_right_top_cap: Dictionary = linked_right_top_cut_terrain.call(
		"_make_chunk",
		10.0,
		20.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var linked_right_top_base: Dictionary = linked_right_top_cut_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	linked_right_top_cut_terrain.set("_chunks", [[linked_right_top_cap, linked_right_top_base]])
	linked_right_top_cut_terrain.call("_clip_slice", 0, Vector2(10.0, 20.0), 5.0)
	var linked_right_top_chunks: Array = linked_right_top_cut_terrain.get("_chunks")
	assert(Array(linked_right_top_chunks[0]).size() == 2)
	var linked_right_top_result_cap: Dictionary = Array(linked_right_top_chunks[0])[0]
	var linked_right_top_result_base: Dictionary = Array(linked_right_top_chunks[0])[1]
	assert(abs(float(linked_right_top_result_cap.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(linked_right_top_result_cap.get("top_right", 0.0)) - 25.0) < 0.01)
	assert(abs(float(linked_right_top_result_cap.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(linked_right_top_result_cap.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(bool(linked_right_top_result_cap.get("linked_to_next", false)))
	assert(not bool(linked_right_top_result_cap.get("falling", true)))
	assert(abs(float(linked_right_top_result_cap.get("wait", -1.0))) < 0.01)
	assert(abs(float(linked_right_top_result_cap.get("speed", -1.0))) < 0.01)
	assert(abs(float(linked_right_top_result_base.get("top_left", 0.0)) - 60.0) < 0.01)
	assert(not bool(linked_right_top_result_base.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 342-356 (Python), the
	# bottom_code in (3, 9, 11) branch with state4 == 2. A one-sided bottom cut
	# detaches a linked support, starts the cap falling, carries the old support
	# motion to the base, and resolves the tangent/above right side through
	# clip_height like the named Python reference regression.
	var one_sided_bottom_cut_terrain := TerrainModel.new()
	one_sided_bottom_cut_terrain.set("_step", 10.0)
	var one_sided_cap: Dictionary = one_sided_bottom_cut_terrain.call(
		"_make_chunk",
		0.0,
		0.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var one_sided_base: Dictionary = one_sided_bottom_cut_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		110.0,
		110.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	one_sided_bottom_cut_terrain.set("_chunks", [[one_sided_cap, one_sided_base]])
	one_sided_bottom_cut_terrain.call("_clip_slice", 0, Vector2(-10.0, 60.0), 20.0)
	var one_sided_bottom_cut_chunks: Array = one_sided_bottom_cut_terrain.get("_chunks")
	assert(Array(one_sided_bottom_cut_chunks[0]).size() == 2)
	var one_sided_result_cap: Dictionary = Array(one_sided_bottom_cut_chunks[0])[0]
	var one_sided_result_base: Dictionary = Array(one_sided_bottom_cut_chunks[0])[1]
	assert(abs(float(one_sided_result_cap.get("bottom_left", 0.0)) - (60.0 - sqrt(300.0))) < 0.01)
	assert(abs(float(one_sided_result_cap.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(one_sided_result_cap.get("linked_to_next", true)))
	assert(bool(one_sided_result_cap.get("falling", false)))
	assert(abs(float(one_sided_result_cap.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(one_sided_result_cap.get("speed", -1.0))) < 0.01)
	assert(not bool(one_sided_result_base.get("falling", true)))
	assert(abs(float(one_sided_result_base.get("wait", -1.0))) < 0.01)
	assert(abs(float(one_sided_result_base.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 322-340 (Python), the
	# bottom_code in (7, 13, 15) branch. When both lower edges are clipped,
	# the linked support is detached and the cap enters the classic fall pause.
	var two_sided_bottom_cut_terrain := TerrainModel.new()
	two_sided_bottom_cut_terrain.set("_step", 10.0)
	var two_sided_cap: Dictionary = two_sided_bottom_cut_terrain.call(
		"_make_chunk",
		0.0,
		0.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var two_sided_base: Dictionary = two_sided_bottom_cut_terrain.call(
		"_make_chunk",
		85.0,
		85.0,
		120.0,
		120.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	two_sided_bottom_cut_terrain.set("_chunks", [[two_sided_cap, two_sided_base]])
	two_sided_bottom_cut_terrain.call("_clip_slice", 0, Vector2(5.0, 60.0), 20.0)
	var two_sided_bottom_cut_chunks: Array = two_sided_bottom_cut_terrain.get("_chunks")
	assert(Array(two_sided_bottom_cut_chunks[0]).size() == 2)
	var two_sided_result_cap: Dictionary = Array(two_sided_bottom_cut_chunks[0])[0]
	var two_sided_result_base: Dictionary = Array(two_sided_bottom_cut_chunks[0])[1]
	var expected_two_sided_bottom := 60.0 - sqrt(375.0)
	assert(abs(float(two_sided_result_cap.get("bottom_left", 0.0)) - expected_two_sided_bottom) < 0.01)
	assert(abs(float(two_sided_result_cap.get("bottom_right", 0.0)) - expected_two_sided_bottom) < 0.01)
	assert(not bool(two_sided_result_cap.get("linked_to_next", true)))
	assert(bool(two_sided_result_cap.get("falling", false)))
	assert(abs(float(two_sided_result_cap.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(two_sided_result_cap.get("speed", -1.0))) < 0.01)
	assert(not bool(two_sided_result_base.get("falling", true)))
	assert(abs(float(two_sided_result_base.get("wait", -1.0))) < 0.01)
	assert(abs(float(two_sided_result_base.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 322-340 (Python), the
	# bottom_code = 15 case (state4 = 3, state3 = 3) without linked support.
	# Both lower endpoints are clipped and the single unlinked chunk starts the
	# classic fall pause.
	var unlinked_bottom_code_15_terrain := TerrainModel.new()
	unlinked_bottom_code_15_terrain.set("_step", 10.0)
	var unlinked_bc15_chunk: Dictionary = unlinked_bottom_code_15_terrain.call(
		"_make_chunk",
		0.0,
		0.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	unlinked_bottom_code_15_terrain.set("_chunks", [[unlinked_bc15_chunk]])
	unlinked_bottom_code_15_terrain.call("_clip_slice", 0, Vector2(5.0, 60.0), 20.0)
	var unlinked_bc15_chunks: Array = unlinked_bottom_code_15_terrain.get("_chunks")
	assert(Array(unlinked_bc15_chunks[0]).size() == 1)
	var unlinked_bc15_result: Dictionary = Array(unlinked_bc15_chunks[0])[0]
	var expected_unlinked_bc15_bottom := 60.0 - sqrt(375.0)
	assert(abs(float(unlinked_bc15_result.get("bottom_left", 0.0)) - expected_unlinked_bc15_bottom) < 0.01)
	assert(abs(float(unlinked_bc15_result.get("bottom_right", 0.0)) - expected_unlinked_bc15_bottom) < 0.01)
	assert(not bool(unlinked_bc15_result.get("linked_to_next", true)))
	assert(bool(unlinked_bc15_result.get("falling", false)))
	assert(abs(float(unlinked_bc15_result.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(unlinked_bc15_result.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 322-340 (Python), the
	# bottom_code = 7 case (state4 = 1, state3 = 3) without linked support.
	var unlinked_bottom_code_7_terrain := TerrainModel.new()
	unlinked_bottom_code_7_terrain.set("_step", 10.0)
	var unlinked_bc7_chunk: Dictionary = unlinked_bottom_code_7_terrain.call(
		"_make_chunk",
		-200.0,
		-200.0,
		0.0,
		105.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	unlinked_bottom_code_7_terrain.set("_chunks", [[unlinked_bc7_chunk]])
	unlinked_bottom_code_7_terrain.call("_clip_slice", 0, Vector2(0.0, 0.0), 100.0)
	var unlinked_bc7_chunks: Array = unlinked_bottom_code_7_terrain.get("_chunks")
	assert(Array(unlinked_bc7_chunks[0]).size() == 1)
	var unlinked_bc7_result: Dictionary = Array(unlinked_bc7_chunks[0])[0]
	assert(abs(float(unlinked_bc7_result.get("bottom_left", 0.0)) - (-100.0)) < 0.01)
	assert(abs(float(unlinked_bc7_result.get("bottom_right", 0.0)) - (-sqrt(9900.0))) < 0.01)
	assert(not bool(unlinked_bc7_result.get("linked_to_next", true)))
	assert(bool(unlinked_bc7_result.get("falling", false)))
	assert(abs(float(unlinked_bc7_result.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(unlinked_bc7_result.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 322-340 (Python), the
	# bottom_code = 13 case (state4 = 3, state3 = 1) without linked support.
	# This mirrors bottom_code = 7 on the opposite side.
	var unlinked_bottom_code_13_terrain := TerrainModel.new()
	unlinked_bottom_code_13_terrain.set("_step", 10.0)
	var unlinked_bc13_chunk: Dictionary = unlinked_bottom_code_13_terrain.call(
		"_make_chunk",
		-200.0,
		-200.0,
		105.0,
		0.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	unlinked_bottom_code_13_terrain.set("_chunks", [[unlinked_bc13_chunk]])
	unlinked_bottom_code_13_terrain.call("_clip_slice", 0, Vector2(0.0, 0.0), 100.0)
	var unlinked_bc13_chunks: Array = unlinked_bottom_code_13_terrain.get("_chunks")
	assert(Array(unlinked_bc13_chunks[0]).size() == 1)
	var unlinked_bc13_result: Dictionary = Array(unlinked_bc13_chunks[0])[0]
	assert(abs(float(unlinked_bc13_result.get("bottom_left", 0.0)) - (-100.0)) < 0.01)
	assert(abs(float(unlinked_bc13_result.get("bottom_right", 0.0)) - (-sqrt(9900.0))) < 0.01)
	assert(not bool(unlinked_bc13_result.get("linked_to_next", true)))
	assert(bool(unlinked_bc13_result.get("falling", false)))
	assert(abs(float(unlinked_bc13_result.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(unlinked_bc13_result.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 303-321 (Python), the
	# bottom_code in (6, 12, 14) branch without linked support. Cutting a
	# non-linked chunk's bottom edge still starts that chunk falling.
	var unlinked_right_bottom_cut_terrain := TerrainModel.new()
	unlinked_right_bottom_cut_terrain.set("_step", 10.0)
	var unlinked_right_bottom_chunk: Dictionary = unlinked_right_bottom_cut_terrain.call(
		"_make_chunk",
		20.0,
		20.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	unlinked_right_bottom_cut_terrain.set("_chunks", [[unlinked_right_bottom_chunk]])
	unlinked_right_bottom_cut_terrain.call("_clip_slice", 0, Vector2(10.0, 60.0), 5.0)
	var unlinked_right_bottom_chunks: Array = unlinked_right_bottom_cut_terrain.get("_chunks")
	assert(Array(unlinked_right_bottom_chunks[0]).size() == 1)
	var unlinked_right_bottom_result: Dictionary = Array(unlinked_right_bottom_chunks[0])[0]
	assert(abs(float(unlinked_right_bottom_result.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(unlinked_right_bottom_result.get("bottom_right", 0.0)) - 55.0) < 0.01)
	assert(not bool(unlinked_right_bottom_result.get("linked_to_next", true)))
	assert(bool(unlinked_right_bottom_result.get("falling", false)))
	assert(abs(float(unlinked_right_bottom_result.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(unlinked_right_bottom_result.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 342-359 (Python), the
	# bottom_code in (3, 9, 11) branch without linked support. This mirrors the
	# right-bottom non-linked fall-start case.
	var unlinked_left_bottom_cut_terrain := TerrainModel.new()
	unlinked_left_bottom_cut_terrain.set("_step", 10.0)
	var unlinked_left_bottom_chunk: Dictionary = unlinked_left_bottom_cut_terrain.call(
		"_make_chunk",
		20.0,
		20.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	unlinked_left_bottom_cut_terrain.set("_chunks", [[unlinked_left_bottom_chunk]])
	unlinked_left_bottom_cut_terrain.call("_clip_slice", 0, Vector2(0.0, 60.0), 5.0)
	var unlinked_left_bottom_chunks: Array = unlinked_left_bottom_cut_terrain.get("_chunks")
	assert(Array(unlinked_left_bottom_chunks[0]).size() == 1)
	var unlinked_left_bottom_result: Dictionary = Array(unlinked_left_bottom_chunks[0])[0]
	assert(abs(float(unlinked_left_bottom_result.get("bottom_left", 0.0)) - 55.0) < 0.01)
	assert(abs(float(unlinked_left_bottom_result.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(unlinked_left_bottom_result.get("linked_to_next", true)))
	assert(bool(unlinked_left_bottom_result.get("falling", false)))
	assert(abs(float(unlinked_left_bottom_result.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(unlinked_left_bottom_result.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 303-321 (Python), the
	# bottom_code = 6 case (state4 = 1, state3 = 2).
	var bottom_code_6_terrain := TerrainModel.new()
	bottom_code_6_terrain.set("_step", 10.0)
	var bc6_cap: Dictionary = bottom_code_6_terrain.call(
		"_make_chunk",
		-200.0,
		-200.0,
		-105.0,
		105.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var bc6_base: Dictionary = bottom_code_6_terrain.call(
		"_make_chunk",
		105.0,
		105.0,
		200.0,
		200.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	bottom_code_6_terrain.set("_chunks", [[bc6_cap, bc6_base]])
	bottom_code_6_terrain.call("_clip_slice", 0, Vector2(0.0, 0.0), 100.0)
	var bc6_chunks: Array = bottom_code_6_terrain.get("_chunks")
	assert(Array(bc6_chunks[0]).size() == 2)
	var bc6_result_cap: Dictionary = Array(bc6_chunks[0])[0]
	var bc6_result_base: Dictionary = Array(bc6_chunks[0])[1]
	assert(abs(float(bc6_result_cap.get("bottom_left", 0.0)) - (-100.0)) < 0.01)
	assert(abs(float(bc6_result_cap.get("bottom_right", 0.0)) - (-sqrt(9900.0))) < 0.01)
	assert(not bool(bc6_result_cap.get("linked_to_next", true)))
	assert(bool(bc6_result_cap.get("falling", false)))

	# Fidelity target: Landscape.clip_slice() lines 303-321 (Python), the
	# bottom_code = 6 case (state4 = 1, state3 = 2) without linked support.
	# The above-blast left bottom edge is preserved when no support is linked.
	var unlinked_bottom_code_6_terrain := TerrainModel.new()
	unlinked_bottom_code_6_terrain.set("_step", 10.0)
	var unlinked_bc6_chunk: Dictionary = unlinked_bottom_code_6_terrain.call(
		"_make_chunk",
		-200.0,
		-200.0,
		-105.0,
		105.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	unlinked_bottom_code_6_terrain.set("_chunks", [[unlinked_bc6_chunk]])
	unlinked_bottom_code_6_terrain.call("_clip_slice", 0, Vector2(0.0, 0.0), 100.0)
	var unlinked_bc6_chunks: Array = unlinked_bottom_code_6_terrain.get("_chunks")
	assert(Array(unlinked_bc6_chunks[0]).size() == 1)
	var unlinked_bc6_result: Dictionary = Array(unlinked_bc6_chunks[0])[0]
	assert(abs(float(unlinked_bc6_result.get("bottom_left", 0.0)) - (-105.0)) < 0.01)
	assert(abs(float(unlinked_bc6_result.get("bottom_right", 0.0)) - (-sqrt(9900.0))) < 0.01)
	assert(not bool(unlinked_bc6_result.get("linked_to_next", true)))
	assert(bool(unlinked_bc6_result.get("falling", false)))
	assert(abs(float(unlinked_bc6_result.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(unlinked_bc6_result.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 342-359 (Python), the
	# bottom_code = 3 case (state4 = 0, state3 = 3) without linked support.
	# Only the left bottom is clipped; the horizontally out-of-range right
	# bottom remains unchanged while the chunk starts the classic fall pause.
	var bottom_code_3_terrain := TerrainModel.new()
	bottom_code_3_terrain.set("_step", 10.0)
	var bc3_chunk: Dictionary = bottom_code_3_terrain.call(
		"_make_chunk",
		40.0,
		40.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	bottom_code_3_terrain.set("_chunks", [[bc3_chunk]])
	bottom_code_3_terrain.call("_clip_slice", 0, Vector2(0.0, 60.0), 5.0)
	var bc3_chunks: Array = bottom_code_3_terrain.get("_chunks")
	assert(Array(bc3_chunks[0]).size() == 1)
	var bc3_result: Dictionary = Array(bc3_chunks[0])[0]
	assert(abs(float(bc3_result.get("bottom_left", 0.0)) - 55.0) < 0.01)
	assert(abs(float(bc3_result.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(bc3_result.get("linked_to_next", true)))
	assert(bool(bc3_result.get("falling", false)))
	assert(abs(float(bc3_result.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(bc3_result.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 303-321 (Python), the
	# bottom_code = 12 case (state4 = 3, state3 = 0). Only the right bottom
	# is clipped; the horizontally out-of-range left bottom remains.
	var bottom_code_12_terrain := TerrainModel.new()
	bottom_code_12_terrain.set("_step", 10.0)
	var bc12_chunk: Dictionary = bottom_code_12_terrain.call(
		"_make_chunk",
		40.0,
		40.0,
		60.0,
		60.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	bottom_code_12_terrain.set("_chunks", [[bc12_chunk]])
	bottom_code_12_terrain.call("_clip_slice", 0, Vector2(10.0, 60.0), 5.0)
	var bc12_chunks: Array = bottom_code_12_terrain.get("_chunks")
	assert(Array(bc12_chunks[0]).size() == 1)
	var bc12_result: Dictionary = Array(bc12_chunks[0])[0]
	assert(abs(float(bc12_result.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(bc12_result.get("bottom_right", 0.0)) - 55.0) < 0.01)
	assert(not bool(bc12_result.get("linked_to_next", true)))
	assert(bool(bc12_result.get("falling", false)))

	# Fidelity target: Landscape.clip_slice() lines 303-321 (Python), the
	# bottom_code = 14 case (state4 = 3, state3 = 2) without linked support.
	# The above-blast left bottom edge stays untouched unless support is linked.
	var bottom_code_14_terrain := TerrainModel.new()
	bottom_code_14_terrain.set("_step", 10.0)
	var bc14_chunk: Dictionary = bottom_code_14_terrain.call(
		"_make_chunk",
		20.0,
		20.0,
		48.0,
		60.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	bottom_code_14_terrain.set("_chunks", [[bc14_chunk]])
	bottom_code_14_terrain.call("_clip_slice", 0, Vector2(10.0, 60.0), 15.0)
	var bc14_chunks: Array = bottom_code_14_terrain.get("_chunks")
	assert(Array(bc14_chunks[0]).size() == 1)
	var bc14_result: Dictionary = Array(bc14_chunks[0])[0]
	assert(abs(float(bc14_result.get("bottom_left", 0.0)) - 48.0) < 0.01)
	assert(abs(float(bc14_result.get("bottom_right", 0.0)) - 45.0) < 0.01)
	assert(not bool(bc14_result.get("linked_to_next", true)))
	assert(bool(bc14_result.get("falling", false)))
	assert(abs(float(bc14_result.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(bc14_result.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 342-359 (Python), the
	# bottom_code = 11 case (state4 = 2, state3 = 3) without linked support.
	# This mirrors bottom_code = 14: the above-blast opposite bottom edge stays
	# untouched unless support is linked.
	var bottom_code_11_terrain := TerrainModel.new()
	bottom_code_11_terrain.set("_step", 10.0)
	var bc11_chunk: Dictionary = bottom_code_11_terrain.call(
		"_make_chunk",
		20.0,
		20.0,
		60.0,
		48.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	bottom_code_11_terrain.set("_chunks", [[bc11_chunk]])
	bottom_code_11_terrain.call("_clip_slice", 0, Vector2(0.0, 60.0), 15.0)
	var bc11_chunks: Array = bottom_code_11_terrain.get("_chunks")
	assert(Array(bc11_chunks[0]).size() == 1)
	var bc11_result: Dictionary = Array(bc11_chunks[0])[0]
	assert(abs(float(bc11_result.get("bottom_left", 0.0)) - 45.0) < 0.01)
	assert(abs(float(bc11_result.get("bottom_right", 0.0)) - 48.0) < 0.01)
	assert(not bool(bc11_result.get("linked_to_next", true)))
	assert(bool(bc11_result.get("falling", false)))
	assert(abs(float(bc11_result.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(bc11_result.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 280-410 (Python). A thin
	# linked cap removed by a one-sided right-edge crater promotes the untouched
	# left top and clipped right top onto the support chunk.
	var one_sided_removed_linked_cap_terrain := TerrainModel.new()
	one_sided_removed_linked_cap_terrain.set("_step", 10.0)
	var one_sided_removed_cap: Dictionary = one_sided_removed_linked_cap_terrain.call(
		"_make_chunk",
		59.0,
		59.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var one_sided_removed_base: Dictionary = one_sided_removed_linked_cap_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	one_sided_removed_linked_cap_terrain.set("_chunks", [[one_sided_removed_cap, one_sided_removed_base]])
	one_sided_removed_linked_cap_terrain.call("_clip_slice", 0, Vector2(10.0, 60.0), 5.0)
	var one_sided_removed_chunks: Array = one_sided_removed_linked_cap_terrain.get("_chunks")
	assert(Array(one_sided_removed_chunks[0]).size() == 1)
	var one_sided_removed_result: Dictionary = Array(one_sided_removed_chunks[0])[0]
	assert(abs(float(one_sided_removed_result.get("top_left", 0.0)) - 59.0) < 0.01)
	assert(abs(float(one_sided_removed_result.get("top_right", 0.0)) - 65.0) < 0.01)
	assert(abs(float(one_sided_removed_result.get("bottom_left", 0.0)) - 90.0) < 0.01)
	assert(abs(float(one_sided_removed_result.get("bottom_right", 0.0)) - 90.0) < 0.01)
	assert(not bool(one_sided_removed_result.get("linked_to_next", true)))
	assert(not bool(one_sided_removed_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 303-321 and 408-415
	# (Python). Removing an already-falling linked cap promotes the clipped top
	# to the support chunk and carries the old superblock wait/speed with it.
	var falling_removed_linked_cap_terrain := TerrainModel.new()
	falling_removed_linked_cap_terrain.set("_step", 10.0)
	var falling_removed_cap: Dictionary = falling_removed_linked_cap_terrain.call(
		"_make_chunk",
		59.0,
		59.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	falling_removed_cap["falling"] = true
	falling_removed_cap["wait"] = 0.25
	falling_removed_cap["speed"] = 42.0
	var falling_removed_base: Dictionary = falling_removed_linked_cap_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	falling_removed_linked_cap_terrain.set("_chunks", [[falling_removed_cap, falling_removed_base]])
	falling_removed_linked_cap_terrain.call("_clip_slice", 0, Vector2(10.0, 60.0), 5.0)
	var falling_removed_chunks: Array = falling_removed_linked_cap_terrain.get("_chunks")
	assert(Array(falling_removed_chunks[0]).size() == 1)
	var falling_removed_result: Dictionary = Array(falling_removed_chunks[0])[0]
	assert(abs(float(falling_removed_result.get("top_left", 0.0)) - 59.0) < 0.01)
	assert(abs(float(falling_removed_result.get("top_right", 0.0)) - 65.0) < 0.01)
	assert(not bool(falling_removed_result.get("linked_to_next", true)))
	assert(bool(falling_removed_result.get("falling", false)))
	assert(abs(float(falling_removed_result.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(falling_removed_result.get("speed", 0.0)) - 42.0) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 280-410 (Python). If a
	# one-sided crater fully consumes only the right edge of a linked cap while
	# the opposite left edge remains tall, Python still deletes the cap and
	# promotes the surviving left top plus clipped right top to the support.
	var surviving_side_removed_cap_terrain := TerrainModel.new()
	surviving_side_removed_cap_terrain.set("_step", 10.0)
	var surviving_side_removed_cap: Dictionary = surviving_side_removed_cap_terrain.call(
		"_make_chunk",
		10.0,
		59.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var surviving_side_removed_base: Dictionary = surviving_side_removed_cap_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	surviving_side_removed_cap_terrain.set("_chunks", [[surviving_side_removed_cap, surviving_side_removed_base]])
	surviving_side_removed_cap_terrain.call("_clip_slice", 0, Vector2(10.0, 60.0), 5.0)
	var surviving_side_removed_chunks: Array = surviving_side_removed_cap_terrain.get("_chunks")
	assert(Array(surviving_side_removed_chunks[0]).size() == 1)
	var surviving_side_removed_result: Dictionary = Array(surviving_side_removed_chunks[0])[0]
	assert(abs(float(surviving_side_removed_result.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(surviving_side_removed_result.get("top_right", 0.0)) - 65.0) < 0.01)
	assert(abs(float(surviving_side_removed_result.get("bottom_left", 0.0)) - 90.0) < 0.01)
	assert(abs(float(surviving_side_removed_result.get("bottom_right", 0.0)) - 90.0) < 0.01)
	assert(not bool(surviving_side_removed_result.get("linked_to_next", true)))
	assert(not bool(surviving_side_removed_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 280-410 (Python). This
	# mirrors the right-edge removed linked cap case: a thin cap removed by a
	# one-sided left-edge crater promotes the clipped left top and untouched
	# right top onto the support chunk.
	var left_sided_removed_linked_cap_terrain := TerrainModel.new()
	left_sided_removed_linked_cap_terrain.set("_step", 10.0)
	var left_sided_removed_cap: Dictionary = left_sided_removed_linked_cap_terrain.call(
		"_make_chunk",
		59.0,
		59.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var left_sided_removed_base: Dictionary = left_sided_removed_linked_cap_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	left_sided_removed_linked_cap_terrain.set("_chunks", [[left_sided_removed_cap, left_sided_removed_base]])
	left_sided_removed_linked_cap_terrain.call("_clip_slice", 0, Vector2(0.0, 60.0), 5.0)
	var left_sided_removed_chunks: Array = left_sided_removed_linked_cap_terrain.get("_chunks")
	assert(Array(left_sided_removed_chunks[0]).size() == 1)
	var left_sided_removed_result: Dictionary = Array(left_sided_removed_chunks[0])[0]
	assert(abs(float(left_sided_removed_result.get("top_left", 0.0)) - 65.0) < 0.01)
	assert(abs(float(left_sided_removed_result.get("top_right", 0.0)) - 59.0) < 0.01)
	assert(abs(float(left_sided_removed_result.get("bottom_left", 0.0)) - 90.0) < 0.01)
	assert(abs(float(left_sided_removed_result.get("bottom_right", 0.0)) - 90.0) < 0.01)
	assert(not bool(left_sided_removed_result.get("linked_to_next", true)))
	assert(not bool(left_sided_removed_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 342-359 and 408-415
	# (Python). This mirrors the falling removed linked cap motion propagation
	# for a left-edge crater.
	var left_falling_removed_linked_cap_terrain := TerrainModel.new()
	left_falling_removed_linked_cap_terrain.set("_step", 10.0)
	var left_falling_removed_cap: Dictionary = left_falling_removed_linked_cap_terrain.call(
		"_make_chunk",
		59.0,
		59.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	left_falling_removed_cap["falling"] = true
	left_falling_removed_cap["wait"] = 0.25
	left_falling_removed_cap["speed"] = 42.0
	var left_falling_removed_base: Dictionary = left_falling_removed_linked_cap_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	left_falling_removed_linked_cap_terrain.set("_chunks", [[left_falling_removed_cap, left_falling_removed_base]])
	left_falling_removed_linked_cap_terrain.call("_clip_slice", 0, Vector2(0.0, 60.0), 5.0)
	var left_falling_removed_chunks: Array = left_falling_removed_linked_cap_terrain.get("_chunks")
	assert(Array(left_falling_removed_chunks[0]).size() == 1)
	var left_falling_removed_result: Dictionary = Array(left_falling_removed_chunks[0])[0]
	assert(abs(float(left_falling_removed_result.get("top_left", 0.0)) - 65.0) < 0.01)
	assert(abs(float(left_falling_removed_result.get("top_right", 0.0)) - 59.0) < 0.01)
	assert(not bool(left_falling_removed_result.get("linked_to_next", true)))
	assert(bool(left_falling_removed_result.get("falling", false)))
	assert(abs(float(left_falling_removed_result.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(left_falling_removed_result.get("speed", 0.0)) - 42.0) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 280-410 (Python). This
	# mirrors the surviving-side removal case: a left-edge crater can delete a
	# linked cap even when the right edge remains tall, promoting both final tops
	# onto the support chunk.
	var surviving_right_removed_cap_terrain := TerrainModel.new()
	surviving_right_removed_cap_terrain.set("_step", 10.0)
	var surviving_right_removed_cap: Dictionary = surviving_right_removed_cap_terrain.call(
		"_make_chunk",
		59.0,
		10.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var surviving_right_removed_base: Dictionary = surviving_right_removed_cap_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	surviving_right_removed_cap_terrain.set("_chunks", [[surviving_right_removed_cap, surviving_right_removed_base]])
	surviving_right_removed_cap_terrain.call("_clip_slice", 0, Vector2(0.0, 60.0), 5.0)
	var surviving_right_removed_chunks: Array = surviving_right_removed_cap_terrain.get("_chunks")
	assert(Array(surviving_right_removed_chunks[0]).size() == 1)
	var surviving_right_removed_result: Dictionary = Array(surviving_right_removed_chunks[0])[0]
	assert(abs(float(surviving_right_removed_result.get("top_left", 0.0)) - 65.0) < 0.01)
	assert(abs(float(surviving_right_removed_result.get("top_right", 0.0)) - 10.0) < 0.01)
	assert(abs(float(surviving_right_removed_result.get("bottom_left", 0.0)) - 90.0) < 0.01)
	assert(abs(float(surviving_right_removed_result.get("bottom_right", 0.0)) - 90.0) < 0.01)
	assert(not bool(surviving_right_removed_result.get("linked_to_next", true)))
	assert(not bool(surviving_right_removed_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 342-356 (Python), the
	# bottom_code = 9 case (state4 = 2, state3 = 1).
	var bottom_code_9_terrain := TerrainModel.new()
	bottom_code_9_terrain.set("_step", 10.0)
	var bc9_cap: Dictionary = bottom_code_9_terrain.call(
		"_make_chunk",
		-200.0,
		-200.0,
		105.0,
		-105.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var bc9_base: Dictionary = bottom_code_9_terrain.call(
		"_make_chunk",
		105.0,
		105.0,
		200.0,
		200.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	bottom_code_9_terrain.set("_chunks", [[bc9_cap, bc9_base]])
	bottom_code_9_terrain.call("_clip_slice", 0, Vector2(0.0, 0.0), 100.0)
	var bc9_chunks: Array = bottom_code_9_terrain.get("_chunks")
	assert(Array(bc9_chunks[0]).size() == 2)
	var bc9_result_cap: Dictionary = Array(bc9_chunks[0])[0]
	var bc9_result_base: Dictionary = Array(bc9_chunks[0])[1]
	assert(abs(float(bc9_result_cap.get("bottom_left", 0.0)) - (-100.0)) < 0.01)
	assert(abs(float(bc9_result_cap.get("bottom_right", 0.0)) - (-sqrt(9900.0))) < 0.01)
	assert(not bool(bc9_result_cap.get("linked_to_next", true)))
	assert(bool(bc9_result_cap.get("falling", false)))

	# Fidelity target: Landscape.clip_slice() lines 342-359 (Python), the
	# bottom_code = 9 case (state4 = 2, state3 = 1) without linked support.
	# This mirrors unlinked bottom_code = 6 on the left side.
	var unlinked_bottom_code_9_terrain := TerrainModel.new()
	unlinked_bottom_code_9_terrain.set("_step", 10.0)
	var unlinked_bc9_chunk: Dictionary = unlinked_bottom_code_9_terrain.call(
		"_make_chunk",
		-200.0,
		-200.0,
		105.0,
		-105.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	unlinked_bottom_code_9_terrain.set("_chunks", [[unlinked_bc9_chunk]])
	unlinked_bottom_code_9_terrain.call("_clip_slice", 0, Vector2(0.0, 0.0), 100.0)
	var unlinked_bc9_chunks: Array = unlinked_bottom_code_9_terrain.get("_chunks")
	assert(Array(unlinked_bc9_chunks[0]).size() == 1)
	var unlinked_bc9_result: Dictionary = Array(unlinked_bc9_chunks[0])[0]
	assert(abs(float(unlinked_bc9_result.get("bottom_left", 0.0)) - (-100.0)) < 0.01)
	assert(abs(float(unlinked_bc9_result.get("bottom_right", 0.0)) - (-105.0)) < 0.01)
	assert(not bool(unlinked_bc9_result.get("linked_to_next", true)))
	assert(bool(unlinked_bc9_result.get("falling", false)))
	assert(abs(float(unlinked_bc9_result.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(unlinked_bc9_result.get("speed", -1.0))) < 0.01)

	var skipped_linked_terrain := TerrainModel.new()
	skipped_linked_terrain.set("_step", 10.0)
	var skipped_cap: Dictionary = skipped_linked_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var skipped_base: Dictionary = skipped_linked_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	skipped_linked_terrain.set("_chunks", [[skipped_cap, skipped_base]])
	skipped_linked_terrain.call("_clip_slice", 0, Vector2(9.0, 28.0), 3.0)
	var skipped_chunks: Array = skipped_linked_terrain.get("_chunks")
	assert(Array(skipped_chunks[0]).size() == 2)
	var preserved_cap: Dictionary = Array(skipped_chunks[0])[0]
	assert(abs(float(preserved_cap.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(preserved_cap.get("bottom_right", 0.0)) - 30.0) < 0.01)
	assert(bool(preserved_cap.get("linked_to_next", false)))

	# Fidelity target: Landscape.clip_slice() lines 270-275 (Python). The
	# linked-superblock edge-graze skip advances over the entire linked chain,
	# preserving a cap, connector, and support unchanged.
	var skipped_chain_terrain := TerrainModel.new()
	skipped_chain_terrain.set("_step", 10.0)
	var skipped_chain_cap: Dictionary = skipped_chain_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var skipped_chain_connector: Dictionary = skipped_chain_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		60.0,
		60.0,
		true,
		Color.GRAY,
		Color.DARK_GRAY
	)
	var skipped_chain_base: Dictionary = skipped_chain_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.DARK_GRAY,
		Color.BLACK
	)
	skipped_chain_terrain.set("_chunks", [[skipped_chain_cap, skipped_chain_connector, skipped_chain_base]])
	skipped_chain_terrain.call("_clip_slice", 0, Vector2(9.0, 28.0), 3.0)
	var skipped_chain_chunks: Array = skipped_chain_terrain.get("_chunks")
	assert(Array(skipped_chain_chunks[0]).size() == 3)
	var preserved_chain_cap: Dictionary = Array(skipped_chain_chunks[0])[0]
	var preserved_chain_connector: Dictionary = Array(skipped_chain_chunks[0])[1]
	var preserved_chain_base: Dictionary = Array(skipped_chain_chunks[0])[2]
	assert(abs(float(preserved_chain_cap.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(preserved_chain_cap.get("bottom_right", 0.0)) - 30.0) < 0.01)
	assert(bool(preserved_chain_cap.get("linked_to_next", false)))
	assert(not bool(preserved_chain_cap.get("falling", true)))
	assert(abs(float(preserved_chain_connector.get("top_left", 0.0)) - 30.0) < 0.01)
	assert(abs(float(preserved_chain_connector.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(bool(preserved_chain_connector.get("linked_to_next", false)))
	assert(not bool(preserved_chain_connector.get("falling", true)))
	assert(abs(float(preserved_chain_base.get("top_left", 0.0)) - 60.0) < 0.01)
	assert(abs(float(preserved_chain_base.get("bottom_right", 0.0)) - 90.0) < 0.01)
	assert(not bool(preserved_chain_base.get("linked_to_next", true)))
	assert(not bool(preserved_chain_base.get("falling", true)))

	var skipped_left_linked_terrain := TerrainModel.new()
	skipped_left_linked_terrain.set("_step", 10.0)
	var skipped_left_cap: Dictionary = skipped_left_linked_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var skipped_left_base: Dictionary = skipped_left_linked_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	skipped_left_linked_terrain.set("_chunks", [[skipped_left_cap, skipped_left_base]])
	skipped_left_linked_terrain.call("_clip_slice", 0, Vector2(1.0, 28.0), 3.0)
	var skipped_left_chunks: Array = skipped_left_linked_terrain.get("_chunks")
	assert(Array(skipped_left_chunks[0]).size() == 2)
	var preserved_left_cap: Dictionary = Array(skipped_left_chunks[0])[0]
	var preserved_left_base: Dictionary = Array(skipped_left_chunks[0])[1]
	assert(abs(float(preserved_left_cap.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(preserved_left_cap.get("top_right", 0.0)) - 10.0) < 0.01)
	assert(abs(float(preserved_left_cap.get("bottom_left", 0.0)) - 30.0) < 0.01)
	assert(abs(float(preserved_left_cap.get("bottom_right", 0.0)) - 30.0) < 0.01)
	assert(bool(preserved_left_cap.get("linked_to_next", false)))
	assert(abs(float(preserved_left_base.get("top_left", 0.0)) - 30.0) < 0.01)
	assert(not bool(preserved_left_base.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 270-275 (Python). The
	# multi-chunk chain skip is mirrored for a left-edge graze.
	var skipped_left_chain_terrain := TerrainModel.new()
	skipped_left_chain_terrain.set("_step", 10.0)
	var skipped_left_chain_cap: Dictionary = skipped_left_chain_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var skipped_left_chain_connector: Dictionary = skipped_left_chain_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		60.0,
		60.0,
		true,
		Color.GRAY,
		Color.DARK_GRAY
	)
	var skipped_left_chain_base: Dictionary = skipped_left_chain_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.DARK_GRAY,
		Color.BLACK
	)
	skipped_left_chain_terrain.set("_chunks", [[skipped_left_chain_cap, skipped_left_chain_connector, skipped_left_chain_base]])
	skipped_left_chain_terrain.call("_clip_slice", 0, Vector2(1.0, 28.0), 3.0)
	var skipped_left_chain_chunks: Array = skipped_left_chain_terrain.get("_chunks")
	assert(Array(skipped_left_chain_chunks[0]).size() == 3)
	var preserved_left_chain_cap: Dictionary = Array(skipped_left_chain_chunks[0])[0]
	var preserved_left_chain_connector: Dictionary = Array(skipped_left_chain_chunks[0])[1]
	var preserved_left_chain_base: Dictionary = Array(skipped_left_chain_chunks[0])[2]
	assert(abs(float(preserved_left_chain_cap.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(preserved_left_chain_cap.get("bottom_left", 0.0)) - 30.0) < 0.01)
	assert(bool(preserved_left_chain_cap.get("linked_to_next", false)))
	assert(not bool(preserved_left_chain_cap.get("falling", true)))
	assert(abs(float(preserved_left_chain_connector.get("top_right", 0.0)) - 30.0) < 0.01)
	assert(abs(float(preserved_left_chain_connector.get("bottom_left", 0.0)) - 60.0) < 0.01)
	assert(bool(preserved_left_chain_connector.get("linked_to_next", false)))
	assert(not bool(preserved_left_chain_connector.get("falling", true)))
	assert(abs(float(preserved_left_chain_base.get("top_right", 0.0)) - 60.0) < 0.01)
	assert(abs(float(preserved_left_chain_base.get("bottom_left", 0.0)) - 90.0) < 0.01)
	assert(not bool(preserved_left_chain_base.get("linked_to_next", true)))
	assert(not bool(preserved_left_chain_base.get("falling", true)))

	var asymmetric_split_terrain := TerrainModel.new()
	asymmetric_split_terrain.set("_step", 10.0)
	var asymmetric_chunk: Dictionary = asymmetric_split_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	asymmetric_split_terrain.set("_chunks", [[asymmetric_chunk]])
	asymmetric_split_terrain.call("_clip_slice", 0, Vector2(1.0, 20.0), 5.0)
	var asymmetric_chunks: Array = asymmetric_split_terrain.get("_chunks")
	assert(Array(asymmetric_chunks[0]).size() == 1)
	var asymmetric_result: Dictionary = Array(asymmetric_chunks[0])[0]
	assert(abs(float(asymmetric_result.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(asymmetric_result.get("top_right", 0.0)) - 10.0) < 0.01)
	assert(abs(float(asymmetric_result.get("bottom_left", 0.0)) - 30.0) < 0.01)
	assert(abs(float(asymmetric_result.get("bottom_right", 0.0)) - 30.0) < 0.01)
	assert(not bool(asymmetric_result.get("falling", true)))

	var mirrored_middle_graze_terrain := TerrainModel.new()
	mirrored_middle_graze_terrain.set("_step", 10.0)
	var mirrored_middle_graze_chunk: Dictionary = mirrored_middle_graze_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	mirrored_middle_graze_terrain.set("_chunks", [[mirrored_middle_graze_chunk]])
	mirrored_middle_graze_terrain.call("_clip_slice", 0, Vector2(9.0, 20.0), 5.0)
	var mirrored_middle_graze_chunks: Array = mirrored_middle_graze_terrain.get("_chunks")
	assert(Array(mirrored_middle_graze_chunks[0]).size() == 1)
	var mirrored_middle_graze_result: Dictionary = Array(mirrored_middle_graze_chunks[0])[0]
	assert(abs(float(mirrored_middle_graze_result.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(mirrored_middle_graze_result.get("top_right", 0.0)) - 10.0) < 0.01)
	assert(abs(float(mirrored_middle_graze_result.get("bottom_left", 0.0)) - 30.0) < 0.01)
	assert(abs(float(mirrored_middle_graze_result.get("bottom_right", 0.0)) - 30.0) < 0.01)
	assert(not bool(mirrored_middle_graze_result.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 361-407 (Python). Splitting
	# an already-falling chunk starts the detached upper cap on a fresh fall pause
	# while the lower remainder keeps the source falling wait/speed.
	var falling_split_terrain := TerrainModel.new()
	falling_split_terrain.set("_step", 10.0)
	var falling_split_chunk: Dictionary = falling_split_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	falling_split_chunk["falling"] = true
	falling_split_chunk["wait"] = 0.25
	falling_split_chunk["speed"] = 42.0
	falling_split_terrain.set("_chunks", [[falling_split_chunk]])
	falling_split_terrain.call("_clip_slice", 0, Vector2(5.0, 20.0), 7.0)
	var falling_split_chunks: Array = falling_split_terrain.get("_chunks")
	assert(Array(falling_split_chunks[0]).size() == 2)
	var falling_split_top: Dictionary = Array(falling_split_chunks[0])[0]
	var falling_split_bottom: Dictionary = Array(falling_split_chunks[0])[1]
	assert(bool(falling_split_top.get("falling", false)))
	assert(abs(float(falling_split_top.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(falling_split_top.get("speed", -1.0))) < 0.01)
	assert(bool(falling_split_bottom.get("falling", false)))
	assert(abs(float(falling_split_bottom.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(falling_split_bottom.get("speed", 0.0)) - 42.0) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 361-407 and 408-415
	# (Python). Splitting a linked cap detaches the upper piece while the lower
	# remainder stays linked to the support chunk below it.
	var linked_split_terrain := TerrainModel.new()
	linked_split_terrain.set("_step", 10.0)
	var linked_split_cap: Dictionary = linked_split_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var linked_split_base: Dictionary = linked_split_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		60.0,
		60.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	linked_split_terrain.set("_chunks", [[linked_split_cap, linked_split_base]])
	linked_split_terrain.call("_clip_slice", 0, Vector2(5.0, 20.0), 7.0)
	var linked_split_chunks: Array = linked_split_terrain.get("_chunks")
	assert(Array(linked_split_chunks[0]).size() == 3)
	var linked_split_upper: Dictionary = Array(linked_split_chunks[0])[0]
	var linked_split_lower: Dictionary = Array(linked_split_chunks[0])[1]
	var linked_split_support: Dictionary = Array(linked_split_chunks[0])[2]
	var expected_linked_split_top_cut := 20.0 - sqrt(24.0)
	var expected_linked_split_bottom_cut := 20.0 + sqrt(24.0)
	assert(abs(float(linked_split_upper.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(linked_split_upper.get("bottom_left", 0.0)) - expected_linked_split_top_cut) < 0.01)
	assert(not bool(linked_split_upper.get("linked_to_next", true)))
	assert(bool(linked_split_upper.get("falling", false)))
	assert(abs(float(linked_split_upper.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(linked_split_upper.get("speed", -1.0))) < 0.01)
	assert(abs(float(linked_split_lower.get("top_left", 0.0)) - expected_linked_split_bottom_cut) < 0.01)
	assert(abs(float(linked_split_lower.get("bottom_left", 0.0)) - 30.0) < 0.01)
	assert(bool(linked_split_lower.get("linked_to_next", false)))
	assert(not bool(linked_split_lower.get("falling", true)))
	assert(abs(float(linked_split_lower.get("wait", -1.0))) < 0.01)
	assert(abs(float(linked_split_lower.get("speed", -1.0))) < 0.01)
	assert(abs(float(linked_split_support.get("top_left", 0.0)) - 30.0) < 0.01)
	assert(not bool(linked_split_support.get("falling", true)))

	# Fidelity target: Landscape.clip_slice() lines 361-407 (Python). Splitting
	# a linked support chunk starts the superblock leader's fall pause while both
	# support remainders themselves stay individually non-falling.
	var linked_support_split_terrain := TerrainModel.new()
	linked_support_split_terrain.set("_step", 10.0)
	var linked_support_split_cap: Dictionary = linked_support_split_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		40.0,
		40.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var linked_support_split_support: Dictionary = linked_support_split_terrain.call(
		"_make_chunk",
		40.0,
		40.0,
		70.0,
		70.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	linked_support_split_terrain.set("_chunks", [[linked_support_split_cap, linked_support_split_support]])
	linked_support_split_terrain.call("_clip_slice", 0, Vector2(5.0, 55.0), 7.0)
	var linked_support_split_chunks: Array = linked_support_split_terrain.get("_chunks")
	assert(Array(linked_support_split_chunks[0]).size() == 3)
	var linked_support_split_result_cap: Dictionary = Array(linked_support_split_chunks[0])[0]
	var linked_support_split_upper: Dictionary = Array(linked_support_split_chunks[0])[1]
	var linked_support_split_lower: Dictionary = Array(linked_support_split_chunks[0])[2]
	var expected_linked_support_split_top_cut := 55.0 - sqrt(24.0)
	var expected_linked_support_split_bottom_cut := 55.0 + sqrt(24.0)
	assert(abs(float(linked_support_split_result_cap.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(linked_support_split_result_cap.get("bottom_left", 0.0)) - 40.0) < 0.01)
	assert(bool(linked_support_split_result_cap.get("linked_to_next", false)))
	assert(bool(linked_support_split_result_cap.get("falling", false)))
	assert(abs(float(linked_support_split_result_cap.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(linked_support_split_result_cap.get("speed", -1.0))) < 0.01)
	assert(abs(float(linked_support_split_upper.get("top_left", 0.0)) - 40.0) < 0.01)
	assert(abs(float(linked_support_split_upper.get("bottom_left", 0.0)) - expected_linked_support_split_top_cut) < 0.01)
	assert(not bool(linked_support_split_upper.get("linked_to_next", true)))
	assert(not bool(linked_support_split_upper.get("falling", true)))
	assert(abs(float(linked_support_split_upper.get("wait", -1.0))) < 0.01)
	assert(abs(float(linked_support_split_upper.get("speed", -1.0))) < 0.01)
	assert(abs(float(linked_support_split_lower.get("top_left", 0.0)) - expected_linked_support_split_bottom_cut) < 0.01)
	assert(abs(float(linked_support_split_lower.get("bottom_left", 0.0)) - 70.0) < 0.01)
	assert(not bool(linked_support_split_lower.get("linked_to_next", true)))
	assert(not bool(linked_support_split_lower.get("falling", true)))
	assert(abs(float(linked_support_split_lower.get("wait", -1.0))) < 0.01)
	assert(abs(float(linked_support_split_lower.get("speed", -1.0))) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 361-407 (Python). Splitting
	# the support under an already-falling linked cap keeps the cap's old motion,
	# leaves the upper support remainder resting, and hands old wait/speed to the
	# lower support remainder.
	var falling_linked_support_split_terrain := TerrainModel.new()
	falling_linked_support_split_terrain.set("_step", 10.0)
	var falling_linked_support_split_cap: Dictionary = falling_linked_support_split_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		40.0,
		40.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	falling_linked_support_split_cap["falling"] = true
	falling_linked_support_split_cap["wait"] = 0.25
	falling_linked_support_split_cap["speed"] = 42.0
	var falling_linked_support_split_support: Dictionary = falling_linked_support_split_terrain.call(
		"_make_chunk",
		40.0,
		40.0,
		70.0,
		70.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	falling_linked_support_split_support["falling"] = true
	falling_linked_support_split_support["wait"] = 0.25
	falling_linked_support_split_support["speed"] = 42.0
	falling_linked_support_split_terrain.set("_chunks", [[falling_linked_support_split_cap, falling_linked_support_split_support]])
	falling_linked_support_split_terrain.call("_clip_slice", 0, Vector2(5.0, 55.0), 7.0)
	var falling_linked_support_split_chunks: Array = falling_linked_support_split_terrain.get("_chunks")
	assert(Array(falling_linked_support_split_chunks[0]).size() == 3)
	var falling_linked_support_split_result_cap: Dictionary = Array(falling_linked_support_split_chunks[0])[0]
	var falling_linked_support_split_upper: Dictionary = Array(falling_linked_support_split_chunks[0])[1]
	var falling_linked_support_split_lower: Dictionary = Array(falling_linked_support_split_chunks[0])[2]
	assert(bool(falling_linked_support_split_result_cap.get("linked_to_next", false)))
	assert(bool(falling_linked_support_split_result_cap.get("falling", false)))
	assert(abs(float(falling_linked_support_split_result_cap.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(falling_linked_support_split_result_cap.get("speed", 0.0)) - 42.0) < 0.01)
	assert(abs(float(falling_linked_support_split_upper.get("top_left", 0.0)) - 40.0) < 0.01)
	assert(abs(float(falling_linked_support_split_upper.get("bottom_left", 0.0)) - expected_linked_support_split_top_cut) < 0.01)
	assert(not bool(falling_linked_support_split_upper.get("linked_to_next", true)))
	assert(not bool(falling_linked_support_split_upper.get("falling", true)))
	assert(abs(float(falling_linked_support_split_upper.get("wait", -1.0))) < 0.01)
	assert(abs(float(falling_linked_support_split_upper.get("speed", -1.0))) < 0.01)
	assert(abs(float(falling_linked_support_split_lower.get("top_left", 0.0)) - expected_linked_support_split_bottom_cut) < 0.01)
	assert(abs(float(falling_linked_support_split_lower.get("bottom_left", 0.0)) - 70.0) < 0.01)
	assert(not bool(falling_linked_support_split_lower.get("linked_to_next", true)))
	assert(bool(falling_linked_support_split_lower.get("falling", false)))
	assert(abs(float(falling_linked_support_split_lower.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(falling_linked_support_split_lower.get("speed", 0.0)) - 42.0) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 361-407 (Python). Motion
	# for a split linked support is copied from the superblock leader, not from
	# the support chunk being cut. The lower remainder inherits the falling cap's
	# wait/speed even when the support itself was still marked resting.
	var leader_motion_support_split_terrain := TerrainModel.new()
	leader_motion_support_split_terrain.set("_step", 10.0)
	var leader_motion_support_split_cap: Dictionary = leader_motion_support_split_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		40.0,
		40.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	leader_motion_support_split_cap["falling"] = true
	leader_motion_support_split_cap["wait"] = 0.25
	leader_motion_support_split_cap["speed"] = 42.0
	var leader_motion_support_split_support: Dictionary = leader_motion_support_split_terrain.call(
		"_make_chunk",
		40.0,
		40.0,
		70.0,
		70.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	leader_motion_support_split_support["falling"] = false
	leader_motion_support_split_support["wait"] = 0.0
	leader_motion_support_split_support["speed"] = 0.0
	leader_motion_support_split_terrain.set("_chunks", [[leader_motion_support_split_cap, leader_motion_support_split_support]])
	leader_motion_support_split_terrain.call("_clip_slice", 0, Vector2(5.0, 55.0), 7.0)
	var leader_motion_support_split_chunks: Array = leader_motion_support_split_terrain.get("_chunks")
	assert(Array(leader_motion_support_split_chunks[0]).size() == 3)
	var leader_motion_support_split_result_cap: Dictionary = Array(leader_motion_support_split_chunks[0])[0]
	var leader_motion_support_split_upper: Dictionary = Array(leader_motion_support_split_chunks[0])[1]
	var leader_motion_support_split_lower: Dictionary = Array(leader_motion_support_split_chunks[0])[2]
	assert(bool(leader_motion_support_split_result_cap.get("linked_to_next", false)))
	assert(bool(leader_motion_support_split_result_cap.get("falling", false)))
	assert(abs(float(leader_motion_support_split_result_cap.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(leader_motion_support_split_result_cap.get("speed", 0.0)) - 42.0) < 0.01)
	assert(abs(float(leader_motion_support_split_upper.get("top_left", 0.0)) - 40.0) < 0.01)
	assert(abs(float(leader_motion_support_split_upper.get("bottom_left", 0.0)) - expected_linked_support_split_top_cut) < 0.01)
	assert(not bool(leader_motion_support_split_upper.get("linked_to_next", true)))
	assert(not bool(leader_motion_support_split_upper.get("falling", true)))
	assert(abs(float(leader_motion_support_split_upper.get("wait", -1.0))) < 0.01)
	assert(abs(float(leader_motion_support_split_upper.get("speed", -1.0))) < 0.01)
	assert(abs(float(leader_motion_support_split_lower.get("top_left", 0.0)) - expected_linked_support_split_bottom_cut) < 0.01)
	assert(abs(float(leader_motion_support_split_lower.get("bottom_left", 0.0)) - 70.0) < 0.01)
	assert(not bool(leader_motion_support_split_lower.get("linked_to_next", true)))
	assert(bool(leader_motion_support_split_lower.get("falling", false)))
	assert(abs(float(leader_motion_support_split_lower.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(leader_motion_support_split_lower.get("speed", 0.0)) - 42.0) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 361-407 and 408-415
	# (Python). Splitting an already-falling linked cap starts the detached
	# upper piece on a fresh fall pause while the lower linked remainder keeps
	# the old superblock motion.
	var falling_linked_split_terrain := TerrainModel.new()
	falling_linked_split_terrain.set("_step", 10.0)
	var falling_linked_split_cap: Dictionary = falling_linked_split_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	falling_linked_split_cap["falling"] = true
	falling_linked_split_cap["wait"] = 0.25
	falling_linked_split_cap["speed"] = 42.0
	var falling_linked_split_base: Dictionary = falling_linked_split_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		60.0,
		60.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	falling_linked_split_terrain.set("_chunks", [[falling_linked_split_cap, falling_linked_split_base]])
	falling_linked_split_terrain.call("_clip_slice", 0, Vector2(5.0, 20.0), 7.0)
	var falling_linked_split_chunks: Array = falling_linked_split_terrain.get("_chunks")
	assert(Array(falling_linked_split_chunks[0]).size() == 3)
	var falling_linked_split_upper: Dictionary = Array(falling_linked_split_chunks[0])[0]
	var falling_linked_split_lower: Dictionary = Array(falling_linked_split_chunks[0])[1]
	var falling_linked_split_support: Dictionary = Array(falling_linked_split_chunks[0])[2]
	assert(abs(float(falling_linked_split_upper.get("bottom_left", 0.0)) - expected_linked_split_top_cut) < 0.01)
	assert(not bool(falling_linked_split_upper.get("linked_to_next", true)))
	assert(bool(falling_linked_split_upper.get("falling", false)))
	assert(abs(float(falling_linked_split_upper.get("wait", 0.0)) - 0.1) < 0.01)
	assert(abs(float(falling_linked_split_upper.get("speed", -1.0))) < 0.01)
	assert(abs(float(falling_linked_split_lower.get("top_left", 0.0)) - expected_linked_split_bottom_cut) < 0.01)
	assert(bool(falling_linked_split_lower.get("linked_to_next", false)))
	assert(bool(falling_linked_split_lower.get("falling", false)))
	assert(abs(float(falling_linked_split_lower.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(falling_linked_split_lower.get("speed", 0.0)) - 42.0) < 0.01)
	assert(not bool(falling_linked_split_support.get("falling", true)))

	var falling_terrain := TerrainModel.new()
	falling_terrain.set("_height", 100.0)
	falling_terrain.set("_fall_acceleration", 0.0)
	var falling_chunk: Dictionary = falling_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		20.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	falling_chunk["falling"] = true
	falling_chunk["wait"] = 0.0
	falling_chunk["speed"] = 100.0
	var landing_chunk: Dictionary = falling_terrain.call(
		"_make_chunk",
		40.0,
		70.0,
		100.0,
		100.0,
		false,
		Color.BLACK,
		Color.BLACK
	)
	falling_terrain.set("_chunks", [[falling_chunk, landing_chunk]])
	var landing_gaps: Vector2 = falling_terrain.call("_superblock_landing_gaps", [falling_chunk, landing_chunk], 0, 0)
	assert(abs(landing_gaps.x - 10.0) < 0.01)
	assert(abs(landing_gaps.y - 50.0) < 0.01)
	falling_terrain.update(0.2)
	var falling_chunks: Array = falling_terrain.get("_chunks")
	var moved_chunk: Dictionary = Array(falling_chunks[0])[0]
	assert(abs(float(moved_chunk["bottom_left"]) - 40.0) < 0.01)
	assert(abs(float(moved_chunk["bottom_right"]) - 40.0) < 0.01)
	assert(bool(moved_chunk.get("falling", false)))
	falling_terrain.update(0.2)
	falling_chunks = falling_terrain.get("_chunks")
	moved_chunk = Array(falling_chunks[0])[0]
	assert(abs(float(moved_chunk["bottom_left"]) - 40.0) < 0.01)
	assert(abs(float(moved_chunk["bottom_right"]) - 60.0) < 0.01)
	assert(bool(moved_chunk.get("falling", false)))

	var falling_support_terrain := TerrainModel.new()
	falling_support_terrain.set("_height", 120.0)
	falling_support_terrain.set("_fall_acceleration", 0.0)
	var falling_upper: Dictionary = falling_support_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	falling_upper["falling"] = true
	falling_upper["wait"] = 0.0
	falling_upper["speed"] = 100.0
	var falling_lower: Dictionary = falling_support_terrain.call(
		"_make_chunk",
		50.0,
		50.0,
		90.0,
		90.0,
		false,
		Color.BLACK,
		Color.BLACK
	)
	falling_lower["falling"] = true
	falling_lower["wait"] = 0.0
	falling_lower["speed"] = 25.0
	falling_support_terrain.set("_chunks", [[falling_upper, falling_lower]])
	falling_support_terrain.update(0.2)
	var falling_support_chunks: Array = falling_support_terrain.get("_chunks")
	var landed_upper: Dictionary = Array(falling_support_chunks[0])[0]
	var moving_lower: Dictionary = Array(falling_support_chunks[0])[1]
	assert(abs(float(landed_upper["bottom_left"]) - 50.0) < 0.01)
	assert(abs(float(landed_upper["bottom_right"]) - 50.0) < 0.01)
	assert(bool(landed_upper.get("linked_to_next", false)))
	assert(bool(landed_upper.get("falling", false)))
	assert(abs(float(landed_upper.get("speed", 0.0)) - 25.0) < 0.01)
	assert(bool(moving_lower.get("falling", false)))
	falling_support_terrain.update(0.2)
	falling_support_chunks = falling_support_terrain.get("_chunks")
	landed_upper = Array(falling_support_chunks[0])[0]
	moving_lower = Array(falling_support_chunks[0])[1]
	assert(abs(float(landed_upper["bottom_left"]) - 55.0) < 0.01)
	assert(abs(float(moving_lower["top_left"]) - 55.0) < 0.01)
	assert(bool(landed_upper.get("linked_to_next", false)))

	# Fidelity target: Landscape.update() lines 169-188 (Python). A uniform
	# chunk that lands on a still-falling support merges into that support and
	# preserves the support's falling wait/speed, even if the support colour differs.
	var falling_merge_support_terrain := TerrainModel.new()
	falling_merge_support_terrain.set("_height", 120.0)
	falling_merge_support_terrain.set("_fall_acceleration", 0.0)
	var falling_merge_upper: Dictionary = falling_merge_support_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	falling_merge_upper["falling"] = true
	falling_merge_upper["wait"] = 0.0
	falling_merge_upper["speed"] = 60.0
	var falling_merge_lower: Dictionary = falling_merge_support_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		90.0,
		90.0,
		false,
		Color.RED,
		Color.RED
	)
	falling_merge_lower["falling"] = true
	falling_merge_lower["wait"] = 0.25
	falling_merge_lower["speed"] = 42.0
	falling_merge_support_terrain.set("_chunks", [[falling_merge_upper, falling_merge_lower]])
	falling_merge_support_terrain.update(0.01)
	var falling_merge_chunks: Array = falling_merge_support_terrain.get("_chunks")
	assert(Array(falling_merge_chunks[0]).size() == 1)
	var falling_merge_result: Dictionary = Array(falling_merge_chunks[0])[0]
	assert(abs(float(falling_merge_result.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(falling_merge_result.get("top_right", 0.0)) - 10.0) < 0.01)
	assert(abs(float(falling_merge_result.get("bottom_left", 0.0)) - 90.0) < 0.01)
	assert(abs(float(falling_merge_result.get("bottom_right", 0.0)) - 90.0) < 0.01)
	assert(bool(falling_merge_result.get("falling", false)))
	assert(abs(float(falling_merge_result.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(falling_merge_result.get("speed", 0.0)) - 42.0) < 0.01)

	var linked_support_terrain := TerrainModel.new()
	linked_support_terrain.set("_height", 140.0)
	linked_support_terrain.set("_fall_acceleration", 0.0)
	var linked_upper: Dictionary = linked_support_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	linked_upper["falling"] = true
	linked_upper["wait"] = 0.0
	linked_upper["speed"] = 100.0
	var linked_lower: Dictionary = linked_support_terrain.call(
		"_make_chunk",
		50.0,
		50.0,
		70.0,
		70.0,
		true,
		Color.BLACK,
		Color.BLACK
	)
	linked_lower["falling"] = true
	linked_lower["wait"] = 0.0
	linked_lower["speed"] = 25.0
	var linked_deep: Dictionary = linked_support_terrain.call(
		"_make_chunk",
		70.0,
		70.0,
		110.0,
		110.0,
		false,
		Color.BLACK,
		Color.BLACK
	)
	linked_support_terrain.set("_chunks", [[linked_upper, linked_lower, linked_deep]])
	linked_support_terrain.update(0.2)
	var linked_support_chunks: Array = linked_support_terrain.get("_chunks")
	var linked_lower_after_first: Dictionary = Array(linked_support_chunks[0])[1]
	var linked_deep_after_first: Dictionary = Array(linked_support_chunks[0])[2]
	assert(abs(float(linked_lower_after_first.get("top_left", 0.0)) - 50.0) < 0.01)
	assert(abs(float(linked_deep_after_first.get("top_left", 0.0)) - 70.0) < 0.01)
	linked_support_terrain.update(0.2)
	linked_support_chunks = linked_support_terrain.get("_chunks")
	var linked_upper_after_second: Dictionary = Array(linked_support_chunks[0])[0]
	var linked_lower_after_second: Dictionary = Array(linked_support_chunks[0])[1]
	var linked_deep_after_second: Dictionary = Array(linked_support_chunks[0])[2]
	assert(abs(float(linked_upper_after_second.get("bottom_left", 0.0)) - 55.0) < 0.01)
	assert(abs(float(linked_lower_after_second.get("top_left", 0.0)) - 55.0) < 0.01)
	assert(abs(float(linked_deep_after_second.get("top_left", 0.0)) - 75.0) < 0.01)

	var merge_landing_terrain := TerrainModel.new()
	merge_landing_terrain.set("_height", 120.0)
	merge_landing_terrain.set("_fall_acceleration", 0.0)
	var merge_upper: Dictionary = merge_landing_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	merge_upper["falling"] = true
	merge_upper["wait"] = 0.0
	merge_upper["speed"] = 100.0
	var merge_lower: Dictionary = merge_landing_terrain.call(
		"_make_chunk",
		50.0,
		50.0,
		90.0,
		90.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	merge_landing_terrain.set("_chunks", [[merge_upper, merge_lower]])
	merge_landing_terrain.update(0.2)
	var merged_landing_chunks: Array = merge_landing_terrain.get("_chunks")
	assert(Array(merged_landing_chunks[0]).size() == 1)
	var merged_landing_chunk: Dictionary = Array(merged_landing_chunks[0])[0]
	assert(abs(float(merged_landing_chunk.get("top_left", 0.0)) - 30.0) < 0.01)
	assert(abs(float(merged_landing_chunk.get("bottom_left", 0.0)) - 90.0) < 0.01)
	assert(not bool(merged_landing_chunk.get("falling", true)))

	# Fidelity target: Landscape.update() lines 177-188 (Python), the branch where
	# end_super_idx != start_super_idx.  A two-chunk linked superblock (cap linked to
	# connector) falls onto a compatible resting chunk.  The connector (bottom of the
	# superblock) is merged into the lower chunk and deleted; the lower chunk's top edge
	# is raised to the connector's top, and the cap (superblock leader) inherits the
	# resting state (falling=false, speed=0, wait=0) from the lower chunk.
	var multi_merge_terrain := TerrainModel.new()
	multi_merge_terrain.set("_height", 120.0)
	multi_merge_terrain.set("_fall_acceleration", 0.0)
	# cap: top of superblock, linked to connector, falling with speed=60.
	# Uniform top/bottom colour (WHITE/WHITE) triggers the colour-match merge branch.
	var multi_merge_cap: Dictionary = multi_merge_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.WHITE
	)
	multi_merge_cap["falling"] = true
	multi_merge_cap["wait"] = 0.0
	multi_merge_cap["speed"] = 60.0
	# connector: bottom of superblock, not linked further, same falling state.
	# connector.bottom (50.0) == lower.top (50.0) → zero gap → lands immediately.
	var multi_merge_connector: Dictionary = multi_merge_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		50.0,
		50.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	multi_merge_connector["falling"] = true
	multi_merge_connector["wait"] = 0.0
	multi_merge_connector["speed"] = 60.0
	# lower: resting chunk, compatible colour, directly below the connector.
	var multi_merge_lower: Dictionary = multi_merge_terrain.call(
		"_make_chunk",
		50.0,
		50.0,
		100.0,
		100.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	multi_merge_lower["falling"] = false
	multi_merge_lower["wait"] = 0.0
	multi_merge_lower["speed"] = 0.0
	multi_merge_terrain.set("_chunks", [[multi_merge_cap, multi_merge_connector, multi_merge_lower]])
	multi_merge_terrain.update(0.01)
	var multi_merge_result_chunks: Array = multi_merge_terrain.get("_chunks")
	# Connector should be deleted; only cap + lower remain.
	assert(Array(multi_merge_result_chunks[0]).size() == 2, "connector should be merged/deleted")
	var multi_merge_result_cap: Dictionary = Array(multi_merge_result_chunks[0])[0]
	var multi_merge_result_lower: Dictionary = Array(multi_merge_result_chunks[0])[1]
	# lower.top absorbs connector.top (30.0)
	assert(abs(float(multi_merge_result_lower.get("top_left", 0.0)) - 30.0) < 0.01)
	assert(abs(float(multi_merge_result_lower.get("top_right", 0.0)) - 30.0) < 0.01)
	# cap inherits lower's resting state
	assert(not bool(multi_merge_result_cap.get("falling", true)))
	assert(abs(float(multi_merge_result_cap.get("speed", 1.0))) < 0.01)
	assert(abs(float(multi_merge_result_cap.get("wait", 1.0))) < 0.01)

	# Fidelity target: Landscape.update() lines 177-188 (Python). If the lower
	# support is still falling, a uniform connector still merges into it and the
	# linked superblock leader inherits the support wait/speed.
	var multi_falling_merge_terrain := TerrainModel.new()
	multi_falling_merge_terrain.set("_height", 120.0)
	multi_falling_merge_terrain.set("_fall_acceleration", 0.0)
	var multi_falling_merge_cap: Dictionary = multi_falling_merge_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.WHITE
	)
	multi_falling_merge_cap["falling"] = true
	multi_falling_merge_cap["wait"] = 0.0
	multi_falling_merge_cap["speed"] = 60.0
	var multi_falling_merge_connector: Dictionary = multi_falling_merge_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		50.0,
		50.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	multi_falling_merge_connector["falling"] = true
	multi_falling_merge_connector["wait"] = 0.0
	multi_falling_merge_connector["speed"] = 60.0
	var multi_falling_merge_lower: Dictionary = multi_falling_merge_terrain.call(
		"_make_chunk",
		50.0,
		50.0,
		100.0,
		100.0,
		false,
		Color.RED,
		Color.RED
	)
	multi_falling_merge_lower["falling"] = true
	multi_falling_merge_lower["wait"] = 0.25
	multi_falling_merge_lower["speed"] = 42.0
	multi_falling_merge_terrain.set("_chunks", [[multi_falling_merge_cap, multi_falling_merge_connector, multi_falling_merge_lower]])
	multi_falling_merge_terrain.update(0.01)
	var multi_falling_merge_chunks: Array = multi_falling_merge_terrain.get("_chunks")
	assert(Array(multi_falling_merge_chunks[0]).size() == 2)
	var multi_falling_merge_result_cap: Dictionary = Array(multi_falling_merge_chunks[0])[0]
	var multi_falling_merge_result_lower: Dictionary = Array(multi_falling_merge_chunks[0])[1]
	assert(bool(multi_falling_merge_result_cap.get("linked_to_next", false)))
	assert(bool(multi_falling_merge_result_cap.get("falling", false)))
	assert(abs(float(multi_falling_merge_result_cap.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(multi_falling_merge_result_cap.get("speed", 0.0)) - 42.0) < 0.01)
	assert(abs(float(multi_falling_merge_result_lower.get("top_left", 0.0)) - 30.0) < 0.01)
	assert(abs(float(multi_falling_merge_result_lower.get("top_right", 0.0)) - 30.0) < 0.01)
	assert(bool(multi_falling_merge_result_lower.get("falling", false)))
	assert(abs(float(multi_falling_merge_result_lower.get("wait", 0.0)) - 0.25) < 0.01)
	assert(abs(float(multi_falling_merge_result_lower.get("speed", 0.0)) - 42.0) < 0.01)

	# Fidelity target: Landscape.update() lines 190-198 (Python), the else-branch after
	# the colour-match check (lines 170-172).
	# When a falling chunk lands (both sides at rest) on a lower resting chunk whose
	# colour is NOT compatible (non-matching), the landing chunk must NOT be deleted. Instead:
	#   - falling_chunk["linked_to_next"] is set to true
	#   - the superblock leader inherits the lower chunk's motion: falling=false, speed=0.0, wait=0.0
	# This stops the fall cleanly without merging and without leaving the chunk falling forever.
	var non_merge_terrain := TerrainModel.new()
	non_merge_terrain.set("_height", 120.0)
	non_merge_terrain.set("_fall_acceleration", 0.0)
		# falling chunk: top and bottom colours differ, excluding the classic merge path.
	var non_merge_falling: Dictionary = non_merge_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		false,
		Color.RED,
		Color.BLUE
	)
	non_merge_falling["falling"] = true
	non_merge_falling["wait"] = 0.0
	non_merge_falling["speed"] = 60.0
	# lower chunk: resting chunk directly below (gap = 0).
	var non_merge_lower: Dictionary = non_merge_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		80.0,
		80.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	non_merge_lower["falling"] = false
	non_merge_lower["wait"] = 0.0
	non_merge_lower["speed"] = 0.0

	non_merge_terrain.set("_chunks", [[non_merge_falling, non_merge_lower]])
	non_merge_terrain.update(0.01)

	var non_merge_result_chunks: Array = non_merge_terrain.get("_chunks")
	assert(Array(non_merge_result_chunks[0]).size() == 2, "falling chunk should remain (non-merge path)")
	var non_merge_result_falling: Dictionary = Array(non_merge_result_chunks[0])[0]
	var non_merge_result_lower: Dictionary = Array(non_merge_result_chunks[0])[1]

	# falling chunk links down to lower chunk
	assert(bool(non_merge_result_falling.get("linked_to_next", false)), "landed chunk should be linked_to_next")
	# leader inherits resting state from lower chunk
	assert(not bool(non_merge_result_falling.get("falling", true)), "landed chunk should inherit falling=false")
	assert(abs(float(non_merge_result_falling.get("speed", 1.0))) < 0.01, "landed chunk speed should be 0")
	assert(abs(float(non_merge_result_falling.get("wait", 1.0))) < 0.01, "landed chunk wait should be 0")
	# lower chunk is unchanged
	assert(abs(float(non_merge_result_lower.get("top_left", 0.0)) - 30.0) < 0.01, "lower chunk top should be unchanged")

	# Fidelity target: Landscape.update() lines 170-198 (Python). The classic
	# merge branch requires exact Colour equality, so near-uniform colours must
	# still use the non-merge link-and-inherit path.
	var near_uniform_terrain := TerrainModel.new()
	near_uniform_terrain.set("_height", 120.0)
	near_uniform_terrain.set("_fall_acceleration", 0.0)
	var near_uniform_falling: Dictionary = near_uniform_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		false,
		Color(0.50, 0.50, 0.00),
		Color(0.52, 0.50, 0.00)
	)
	near_uniform_falling["falling"] = true
	near_uniform_falling["wait"] = 0.0
	near_uniform_falling["speed"] = 60.0
	var near_uniform_lower: Dictionary = near_uniform_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		80.0,
		80.0,
		false,
		Color(0.52, 0.50, 0.00),
		Color(0.52, 0.50, 0.00)
	)
	near_uniform_terrain.set("_chunks", [[near_uniform_falling, near_uniform_lower]])
	near_uniform_terrain.update(0.01)
	var near_uniform_chunks: Array = near_uniform_terrain.get("_chunks")
	assert(Array(near_uniform_chunks[0]).size() == 2, "near-uniform colours should not merge")
	var near_uniform_result_falling: Dictionary = Array(near_uniform_chunks[0])[0]
	var near_uniform_result_lower: Dictionary = Array(near_uniform_chunks[0])[1]
	assert(bool(near_uniform_result_falling.get("linked_to_next", false)))
	assert(not bool(near_uniform_result_falling.get("falling", true)))
	assert(abs(float(near_uniform_result_falling.get("speed", 1.0))) < 0.01)
	assert(abs(float(near_uniform_result_lower.get("top_left", 0.0)) - 30.0) < 0.01)

	# Fidelity target: Landscape.update() lines 137-139 (Python). When a falling
	# chunk still has positive wait, the tick only subtracts wait and defers all
	# movement/acceleration until the next frame, preserving the current speed even
	# if the wait crosses below zero.
	var waiting_fall_terrain := TerrainModel.new()
	waiting_fall_terrain.set("_height", 100.0)
	waiting_fall_terrain.set("_fall_acceleration", 10.0)
	var waiting_fall_chunk: Dictionary = waiting_fall_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	waiting_fall_chunk["falling"] = true
	waiting_fall_chunk["wait"] = 0.05
	waiting_fall_chunk["speed"] = 42.0
	waiting_fall_terrain.set("_chunks", [[waiting_fall_chunk]])
	waiting_fall_terrain.update(0.08)
	var waiting_fall_chunks: Array = waiting_fall_terrain.get("_chunks")
	var waiting_after_tick: Dictionary = Array(waiting_fall_chunks[0])[0]
	assert(abs(float(waiting_after_tick.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(waiting_after_tick.get("bottom_left", 0.0)) - 30.0) < 0.01)
	assert(abs(float(waiting_after_tick.get("speed", 0.0)) - 42.0) < 0.01)
	assert(abs(float(waiting_after_tick.get("wait", 0.0)) + 0.03) < 0.01)
	waiting_fall_terrain.update(0.1)
	waiting_fall_chunks = waiting_fall_terrain.get("_chunks")
	var waiting_after_move: Dictionary = Array(waiting_fall_chunks[0])[0]
	assert(abs(float(waiting_after_move.get("top_left", 0.0)) - 14.2) < 0.01)
	assert(abs(float(waiting_after_move.get("bottom_left", 0.0)) - 34.2) < 0.01)
	assert(abs(float(waiting_after_move.get("speed", 0.0)) - 43.0) < 0.01)

	var accelerating_terrain := TerrainModel.new()
	accelerating_terrain.set("_height", 100.0)
	accelerating_terrain.set("_fall_acceleration", 100.0)
	var accelerating_chunk: Dictionary = accelerating_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		20.0,
		20.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	accelerating_chunk["falling"] = true
	accelerating_chunk["wait"] = 0.0
	accelerating_chunk["speed"] = 0.0
	accelerating_terrain.set("_chunks", [[accelerating_chunk]])
	accelerating_terrain.update(0.2)
	var accelerating_chunks: Array = accelerating_terrain.get("_chunks")
	var accelerated_chunk: Dictionary = Array(accelerating_chunks[0])[0]
	assert(abs(float(accelerated_chunk["bottom_left"]) - 20.0) < 0.01)
	assert(abs(float(accelerated_chunk["speed"]) - 20.0) < 0.01)
	accelerating_terrain.update(0.2)
	accelerating_chunks = accelerating_terrain.get("_chunks")
	accelerated_chunk = Array(accelerating_chunks[0])[0]
	assert(abs(float(accelerated_chunk["bottom_left"]) - 24.0) < 0.01)
	assert(abs(float(accelerated_chunk["speed"]) - 40.0) < 0.01)

	# Test case: double split crater clipping.
	# A blast is entirely inside a tall chunk horizontally and vertically.
	# It splits the chunk into an upper piece and a lower piece.
	# The upper piece (part_index == 0) starts falling (wait = 0.1), while the
	# lower piece (part_index == 1) does not start falling (wait = 0.0).
	var split_terrain := TerrainModel.new()
	split_terrain.set("_height", 768.0)
	split_terrain.set("_step", 0.05)
	split_terrain.set("_fall_pause", 0.1)
	var split_chunk: Dictionary = split_terrain.call(
		"_make_chunk",
		300.0,
		300.0,
		500.0,
		500.0,
		false,
		Color.WHITE,
		Color.WHITE
	)
	split_terrain.set("_chunks", [[split_chunk]])
	var blast_center := Vector2(0.025, 400.0)
	var blast_radius := 50.0
	split_terrain.call("_clip_slice", 0, blast_center, blast_radius)
	var split_chunks: Array = split_terrain.get("_chunks")
	var result_slice: Array = Array(split_chunks[0])
	assert(result_slice.size() == 2, "chunk should be split into 2 pieces in GDScript")
	var result_upper: Dictionary = result_slice[0]
	var result_lower: Dictionary = result_slice[1]
	assert(abs(float(result_upper["top_left"]) - 300.0) < 0.01)
	assert(float(result_upper["bottom_left"]) < 400.0)
	assert(bool(result_upper["falling"]), "upper chunk should be falling")
	assert(abs(float(result_upper["wait"]) - 0.1) < 0.01)
	assert(not bool(result_upper["linked_to_next"]))
	assert(float(result_lower["top_left"]) > 400.0)
	assert(abs(float(result_lower["bottom_left"]) - 500.0) < 0.01)
	assert(not bool(result_lower["falling"]), "lower chunk should not start falling")
	assert(abs(float(result_lower["wait"])) < 0.01)

	# Fidelity target: Landscape.clip_slice() lines 280-407 (Python).
	# If a tiny blast intersects the middle of only one vertical slice edge
	# but neither the top nor bottom endpoint is inside the blast, the classic
	# endpoint-code clipping path leaves the chunk unchanged.
	var middle_graze_left_terrain := TerrainModel.new()
	middle_graze_left_terrain.set("_step", 10.0)
	var mg_left_chunk: Dictionary = middle_graze_left_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		90.0,
		90.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	middle_graze_left_terrain.set("_chunks", [[mg_left_chunk]])
	middle_graze_left_terrain.call("_clip_slice", 0, Vector2(0.1, 50.0), 5.0)
	var mg_left_chunks: Array = middle_graze_left_terrain.get("_chunks")
	assert(Array(mg_left_chunks[0]).size() == 1)
	var mg_left_result: Dictionary = Array(mg_left_chunks[0])[0]
	assert(abs(float(mg_left_result.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(mg_left_result.get("top_right", 0.0)) - 10.0) < 0.01)
	assert(abs(float(mg_left_result.get("bottom_left", 0.0)) - 90.0) < 0.01)
	assert(abs(float(mg_left_result.get("bottom_right", 0.0)) - 90.0) < 0.01)
	assert(not bool(mg_left_result.get("falling", false)))

	# Fidelity target: Landscape.clip_slice() lines 280-407 (Python).
	# This is the right-edge mirror of the one-sided middle crater graze.
	var middle_graze_right_terrain := TerrainModel.new()
	middle_graze_right_terrain.set("_step", 10.0)
	var mg_right_chunk: Dictionary = middle_graze_right_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		90.0,
		90.0,
		false,
		Color.WHITE,
		Color.GRAY
	)
	middle_graze_right_terrain.set("_chunks", [[mg_right_chunk]])
	middle_graze_right_terrain.call("_clip_slice", 0, Vector2(9.9, 50.0), 5.0)
	var mg_right_chunks: Array = middle_graze_right_terrain.get("_chunks")
	assert(Array(mg_right_chunks[0]).size() == 1)
	var mg_right_result: Dictionary = Array(mg_right_chunks[0])[0]
	assert(abs(float(mg_right_result.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(mg_right_result.get("top_right", 0.0)) - 10.0) < 0.01)
	assert(abs(float(mg_right_result.get("bottom_left", 0.0)) - 90.0) < 0.01)
	assert(abs(float(mg_right_result.get("bottom_right", 0.0)) - 90.0) < 0.01)
	assert(not bool(mg_right_result.get("falling", false)))

	# Fidelity target: Landscape.clip_slice() lines 270-275 (Python).
	# A left-bottom edge graze advances over the linked superblock without detaching or clipping it.
	var left_graze_skip_terrain := TerrainModel.new()
	left_graze_skip_terrain.set("_step", 10.0)
	var left_graze_cap: Dictionary = left_graze_skip_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var left_graze_base: Dictionary = left_graze_skip_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	left_graze_skip_terrain.set("_chunks", [[left_graze_cap, left_graze_base]])
	left_graze_skip_terrain.call("_clip_slice", 0, Vector2(1.0, 28.0), 3.0)
	var lgs_chunks: Array = left_graze_skip_terrain.get("_chunks")
	assert(Array(lgs_chunks[0]).size() == 2)
	var lgs_cap: Dictionary = Array(lgs_chunks[0])[0]
	var lgs_base: Dictionary = Array(lgs_chunks[0])[1]
	assert(abs(float(lgs_cap.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(abs(float(lgs_cap.get("bottom_left", 0.0)) - 30.0) < 0.01)
	assert(bool(lgs_cap.get("linked_to_next", false)))
	assert(not bool(lgs_cap.get("falling", false)))
	assert(abs(float(lgs_base.get("top_left", 0.0)) - 30.0) < 0.01)
	assert(not bool(lgs_base.get("falling", false)))

	# Fidelity target: Landscape.clip_slice() lines 270-275 (Python).
	# A right-edge graze against the cap leaves the cap, connector, and final support intact.
	var right_graze_chain_terrain := TerrainModel.new()
	right_graze_chain_terrain.set("_step", 10.0)
	var right_graze_cap: Dictionary = right_graze_chain_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		30.0,
		30.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var right_graze_conn: Dictionary = right_graze_chain_terrain.call(
		"_make_chunk",
		30.0,
		30.0,
		60.0,
		60.0,
		true,
		Color.GRAY,
		Color.BLACK
	)
	var right_graze_base: Dictionary = right_graze_chain_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.BLACK,
		Color.BLACK
	)
	right_graze_chain_terrain.set("_chunks", [[right_graze_cap, right_graze_conn, right_graze_base]])
	right_graze_chain_terrain.call("_clip_slice", 0, Vector2(9.0, 28.0), 3.0)
	var rgc_chunks: Array = right_graze_chain_terrain.get("_chunks")
	assert(Array(rgc_chunks[0]).size() == 3)
	var rgc_cap: Dictionary = Array(rgc_chunks[0])[0]
	var rgc_conn: Dictionary = Array(rgc_chunks[0])[1]
	var rgc_base: Dictionary = Array(rgc_chunks[0])[2]
	assert(abs(float(rgc_cap.get("top_left", 0.0)) - 10.0) < 0.01)
	assert(bool(rgc_cap.get("linked_to_next", false)))
	assert(abs(float(rgc_conn.get("top_left", 0.0)) - 30.0) < 0.01)
	assert(bool(rgc_conn.get("linked_to_next", false)))
	assert(abs(float(rgc_base.get("top_left", 0.0)) - 60.0) < 0.01)
	assert(not bool(rgc_base.get("linked_to_next", false)))

	# Fidelity target: Landscape.clip_slice() lines 342-359 (Python).
	# A one-sided bottom cut on a linked chunk detaches its support.
	var one_sided_linked_bottom_cut_terrain := TerrainModel.new()
	one_sided_linked_bottom_cut_terrain.set("_step", 10.0)
	var osc_cap: Dictionary = one_sided_linked_bottom_cut_terrain.call(
		"_make_chunk",
		10.0,
		10.0,
		60.0,
		60.0,
		true,
		Color.WHITE,
		Color.GRAY
	)
	var osc_base: Dictionary = one_sided_linked_bottom_cut_terrain.call(
		"_make_chunk",
		60.0,
		60.0,
		90.0,
		90.0,
		false,
		Color.GRAY,
		Color.BLACK
	)
	one_sided_linked_bottom_cut_terrain.set("_chunks", [[osc_cap, osc_base]])
	one_sided_linked_bottom_cut_terrain.call("_clip_slice", 0, Vector2(0.0, 60.0), 10.0)
	var osc_chunks: Array = one_sided_linked_bottom_cut_terrain.get("_chunks")
	assert(Array(osc_chunks[0]).size() == 2)
	var osc_result_cap: Dictionary = Array(osc_chunks[0])[0]
	assert(abs(float(osc_result_cap.get("bottom_left", 0.0)) - 50.0) < 0.01)
	assert(abs(float(osc_result_cap.get("bottom_right", 0.0)) - 60.0) < 0.01)
	assert(not bool(osc_result_cap.get("linked_to_next", true)))
	assert(bool(osc_result_cap.get("falling", false)))

	# Regression tests for Phase 2 weapons
	# 1. Rolling Mines
	var rolling_mine_weapon := {"name": "Rolling Mines", "kind": "rolling_mine", "damage": 30, "blast": 36.0, "speed": 4.0}
	_clear_projectiles(local_match)
	var rolling_mine_start_y := float(local_match.get("_terrain").height_at(100.0)) - 10.0
	local_match.call(
		"_fire_weapon",
		Vector2(100.0, rolling_mine_start_y),
		180.0,
		10.0,
		"Player",
		rolling_mine_weapon
	)
	var rolling_projectiles: Array = local_match.get("_projectiles")
	assert(rolling_projectiles.size() == 1)
	var roll_proj: Dictionary = rolling_projectiles[0]
	assert(str(roll_proj.get("kind")) == "rolling_mine")
	assert(not bool(roll_proj.get("rolling", false)))

	# Simulate hitting the ground (terrain collision)
	local_match.call("_update_projectiles", 0.5)
	rolling_projectiles = local_match.get("_projectiles")
	assert(rolling_projectiles.size() == 1)
	roll_proj = rolling_projectiles[0]
	assert(bool(roll_proj.get("rolling", false)), "Rolling mine must enter rolling state on terrain contact")
	assert(abs(float(roll_proj.get("roll_speed", 0.0))) > 0.0)

	# 2. Airstrike
	var airstrike_weapon := {"name": "Airstrike", "kind": "airstrike", "damage": 40, "blast": 40.0, "speed": 4.5}
	_clear_projectiles(local_match)
	var airstrike_proj := {
		"position": Vector2(120.0, 300.0),
		"previous_position": Vector2(120.0, 290.0),
		"velocity": Vector2(0.0, 100.0),
		"owner": "Player",
		"player_owned": true,
		"weapon": airstrike_weapon,
		"kind": "airstrike",
		"age": 0.0,
	}
	local_match.get("_projectiles").append(airstrike_proj)
	local_match.call("_apply_explosion", Vector2(120.0, 300.0), airstrike_proj)
	var airstrike_missiles: Array = local_match.get("_projectiles")
	assert(airstrike_missiles.size() == 5, "Airstrike must spawn 5 horizontal missiles")
	assert(str(airstrike_missiles[0].get("kind")) == "shell")
	assert(str(airstrike_missiles[0].get("weapon").get("name")) == "Airstrike Missile")
	_clear_projectiles(local_match)

	# 3. Death's Head
	var deaths_head_weapon := {"name": "Death's Head", "kind": "deaths_head", "damage": 25, "blast": 30.0, "speed": 3.8, "fragments": 8, "spread": 0.35}
	_clear_projectiles(local_match)
	local_match.call(
		"_fire_weapon",
		Vector2(200.0, 150.0),
		-45.0,
		15.0,
		"Player",
		deaths_head_weapon
	)
	var deaths_head_projectiles: Array = local_match.get("_projectiles")
	assert(deaths_head_projectiles.size() == 1)
	var dh_proj: Dictionary = deaths_head_projectiles[0]
	assert(str(dh_proj.get("kind")) == "deaths_head")
	assert(float(dh_proj.get("split_age", INF)) < INF, "Death's Head must have a split age")
	_clear_projectiles(local_match)

	# 4. Hover Coil
	var hover_coil_weapon := {"name": "Hover Coil", "kind": "hover_coil", "damage": 0, "blast": 0.0, "speed": 4.0}
	var hover_proj := {
		"position": enemy_tank.position,
		"previous_position": enemy_tank.position,
		"velocity": Vector2.ZERO,
		"owner": "Player",
		"player_owned": true,
		"weapon": hover_coil_weapon,
		"kind": "hover_coil",
	}
	enemy_tank.hover_time = 0.0
	local_match.call("_apply_explosion", enemy_tank.position, hover_proj)
	assert(enemy_tank.hover_time == 4.0, "Hover Coil must apply hover_time to hit tank")
	assert(not enemy_tank.on_ground, "Hovered tank must float")
	enemy_tank.hover_time = 0.0
	enemy_tank.on_ground = true

	# 5. Corbomite
	var corbomite_weapon := {"name": "Corbomite", "kind": "corbomite", "damage": 0, "blast": 0.0, "speed": 0.0}
	local_match.set("_phase", "aim")
	local_match.call("_set_turn_index", 0)
	var p_inventory: RefCounted = local_match.get("_inventory")
	p_inventory.reset_round_ammo()
	p_inventory.select_by_name("Corbomite")
	player_tank.corbomite_active = false
	local_match.call("_fire_player")
	assert(player_tank.corbomite_active, "Corbomite activation must set corbomite_active on tank")
	assert(player_tank.shield_active, "Corbomite activation must activate shield")
	player_tank.corbomite_active = false
	player_tank.shield_active = false

	await _free_node(local_match)
	await _drain_frames(SHUTDOWN_DRAIN_FRAMES)
	quit(0)


func _free_node(node: Node) -> void:
	if node == null:
		return
	if node.has_method("_prepare_for_shutdown"):
		node.call("_prepare_for_shutdown")
	await process_frame
	node.queue_free()
	await _drain_frames(SHUTDOWN_DRAIN_FRAMES)


func _drain_frames(count: int) -> void:
	for index in range(count):
		await process_frame


func _clear_projectiles(local_match: Node) -> void:
	var projectiles: Array = local_match.get("_projectiles")
	projectiles.clear()
	local_match.set("_projectiles", projectiles)


func _clear_explosions(local_match: Node) -> void:
	var explosions: Array = local_match.get("_explosions")
	explosions.clear()
	local_match.set("_explosions", explosions)
