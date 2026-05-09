extends SceneTree

const LocalMatchScene := preload("res://scenes/local_match.tscn")
const LocalMatchHud := preload("res://scripts/local_match_hud.gd")
const LocalMatchShop := preload("res://scripts/local_match_shop.gd")
const TankState := preload("res://scripts/tank_state.gd")
const TerrainModel := preload("res://scripts/terrain_model.gd")
const WeaponInventory := preload("res://scripts/weapon_inventory.gd")


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


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(1024, 768)
	var local_match := LocalMatchScene.instantiate()
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

	_clear_projectiles(local_match)
	local_match.call(
		"_spawn_mirv_children",
		Vector2(200.0, 120.0),
		Vector2(100.0, -40.0),
		true,
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
	assert(inventory.select_by_name(WeaponInventory.MIRV))
	assert(inventory.ammo_for(WeaponInventory.MIRV) == WeaponInventory.MIRV_ROUND_AMMO)

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
	for mirv_projectile in mirv_children:
		assert(str(mirv_projectile.get("kind", "")) == "shell")
		assert(str(Dictionary(mirv_projectile.get("weapon", {})).get("name", "")) == "MIRV Fragment")
	_clear_projectiles(local_match)

	local_match.call(
		"_fire_from",
		Vector2(320.0, 160.0),
		45.0,
		40.0,
		true,
		{"name": "Missile", "kind": "missile", "damage": 40, "blast": 46.0, "speed": 4.8, "fuel": 3.0, "steer_sensitivity": 300.0}
	)
	var missile_projectiles: Array = local_match.get("_projectiles")
	assert(missile_projectiles.size() == 1)
	var missile_projectile: Dictionary = missile_projectiles[0]
	assert(abs(float(missile_projectile.get("fuel", 0.0)) - 3.0) < 0.01)
	assert(float(missile_projectile.get("angle_change", -1.0)) == 0.0)
	Input.action_press("gf_aim_left")
	local_match.call("_update_projectiles", 0.1)
	Input.action_release("gf_aim_left")
	missile_projectiles = local_match.get("_projectiles")
	assert(missile_projectiles.size() == 1)
	missile_projectile = missile_projectiles[0]
	assert(float(missile_projectile.get("angle_change", 0.0)) > 0.0)
	assert(float(missile_projectile.get("angle", 45.0)) > 45.0)
	assert(float(missile_projectile.get("fuel", 3.0)) < 3.0)
	_clear_projectiles(local_match)
	var clamped_missile := {
		"fuel": 1.0,
		"angle": 45.0,
		"angle_change": 490.0,
		"steer_sensitivity": 300.0,
		"player_owned": true,
	}
	Input.action_press("gf_aim_left")
	local_match.call("_update_missile_projectile", clamped_missile, Vector2(120.0, 0.0), Vector2.ZERO, 1.0)
	Input.action_release("gf_aim_left")
	assert(abs(float(clamped_missile.get("angle_change", 0.0)) - 500.0) < 0.01)
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
	assert(abs(Vector2(airborne_projectile.get("velocity", Vector2.ZERO)).x - 54.0) < 0.01)
	assert(abs(Vector2(airborne_projectile.get("velocity", Vector2.ZERO)).y + 8.0) < 0.01)
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
		30.0,
		40.0,
		true,
		{"name": "Machine Gun", "kind": "machine_gun", "damage": 2, "blast": 0.0, "speed": 5.8, "volley": 5, "cooldown": 0.1, "direct_damage": true}
	)
	var machine_gun_projectiles: Array = local_match.get("_projectiles")
	assert(machine_gun_projectiles.size() == 5)
	var first_machine_gun_projectile: Dictionary = machine_gun_projectiles[0]
	assert(str(first_machine_gun_projectile.get("kind", "")) == "machine_gun")
	assert(Vector2(first_machine_gun_projectile.get("back_position", Vector2.ZERO)) == Vector2(320.0, 160.0))
	assert(abs(float(first_machine_gun_projectile.get("delay", -1.0))) < 0.01)
	assert(abs(float(machine_gun_projectiles[1].get("delay", 0.0)) - 0.1) < 0.01)
	assert(abs(float(machine_gun_projectiles[4].get("delay", 0.0)) - 0.4) < 0.01)
	var enemy_tank: RefCounted = local_match.get("_enemy")
	var enemy_health_before := int(enemy_tank.health)
	var score_before := int(local_match.get("_score"))
	local_match.call("_apply_machine_gun_damage", first_machine_gun_projectile, true)
	assert(int(enemy_tank.health) == enemy_health_before - 2)
	assert(int(local_match.get("_score")) == score_before + 2)
	_clear_projectiles(local_match)

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
	assert(Vector2(machine_gun_projectiles[0].get("position", Vector2.ZERO)).distance_to(Vector2(320.0, 160.0)) > 1.0)
	assert(Vector2(machine_gun_projectiles[1].get("position", Vector2.ZERO)) == Vector2(320.0, 160.0))
	assert(float(machine_gun_projectiles[1].get("delay", 0.0)) > 0.0)
	_clear_projectiles(local_match)

	var match_terrain: Variant = local_match.get("_terrain")
	var tracer_x := 520.0
	var tracer_ground_before := float(match_terrain.height_at(tracer_x))
	local_match.call(
		"_fire_from",
		Vector2(tracer_x, tracer_ground_before - 28.0),
		-90.0,
		50.0,
		true,
		{"name": "Machine Gun", "kind": "machine_gun", "damage": 2, "blast": 0.0, "speed": 5.8, "volley": 1, "cooldown": 0.1, "direct_damage": true}
	)
	local_match.call("_update_projectiles", 0.2)
	assert(local_match.get("_projectiles").is_empty())
	assert(local_match.get("_explosions").is_empty())
	assert(abs(float(match_terrain.height_at(tracer_x)) - tracer_ground_before) < 0.01)
	local_match.set("_phase", "aim")
	local_match.set("_turn_owner", "Player")

	local_match.call("_spawn_explosion", Vector2(430.0, 220.0), 96.0, true)
	var nuke_explosions: Array = local_match.get("_explosions")
	assert(nuke_explosions.size() == 1)
	var nuke_explosion: Dictionary = nuke_explosions[0]
	assert(bool(nuke_explosion.get("white_out", false)))
	assert(abs(float(nuke_explosion.get("white_out_level", 0.0)) - 1.0) < 0.01)
	assert(float(local_match.call("_whiteout_alpha")) > 0.99)
	local_match.call("_update_explosions", 1.0)
	nuke_explosions = local_match.get("_explosions")
	assert(nuke_explosions.size() == 1)
	nuke_explosion = nuke_explosions[0]
	assert(bool(nuke_explosion.get("white_out", false)))
	assert(float(nuke_explosion.get("white_out_level", 0.0)) < 0.5)
	assert(float(local_match.call("_whiteout_alpha")) < 0.5)
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
	assert(hud.call("_wind_label", 5.1) == "Wind -> 5")
	assert(hud.call("_wind_label", -2.6) == "Wind <- 3")
	assert(hud.call("_wind_label", 0.2) == "Wind calm")
	assert(hud.call("_quake_label", true, 3.0) == "Quake!")
	assert(hud.call("_quake_label", false, 9.2) == "Quake in 10s")
	assert(hud.call("_quake_label", false, 60.0) == "")
	hud.queue_free()

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

	var shop := LocalMatchShop.new()
	root.add_child(shop)
	await process_frame
	shop.refresh({
		"title": "Round Won",
		"round": 1,
		"score": 120,
		"reward": 100,
		"credits": 100,
		"inventory": [
			{"name": "Missile", "cost": 50, "ammo": 0, "damage": 40, "blast": 48},
		],
		"message": "Shop focus check",
	})
	await process_frame
	var shop_focus_buttons: Array = shop.get("_focus_buttons")
	assert(shop_focus_buttons.size() == 2)
	var first_shop_button: Button = shop_focus_buttons[0]
	var second_shop_button: Button = shop_focus_buttons[1]
	assert(first_shop_button.focus_neighbor_bottom == second_shop_button.get_path())
	assert(second_shop_button.focus_neighbor_top == first_shop_button.get_path())
	shop.queue_free()

	var tank := TankState.new()
	assert(abs(tank.gun_angle - TankState.GUN_ANGLE_DEFAULT) < 0.01)
	assert(abs(tank.gun_power - TankState.GUN_POWER_DEFAULT) < 0.01)
	assert(tank.health == TankState.TANK_MAX_HEALTH)
	assert(abs(tank.fuel - TankState.TANK_FULL_FUEL) < 0.01)
	tank.health = TankState.TANK_MAX_HEALTH
	assert(not bool(tank.apply_damage(100)))
	assert(tank.health == 0)
	assert(tank.state == TankState.STATE_ALIVE)
	assert(bool(tank.apply_damage(1)))
	assert(tank.state == TankState.STATE_DEAD)
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
	assert(abs(tank.gun_angle - 60.0) < 0.01)
	assert(abs(tank.gun_power - 60.0) < 0.01)
	tank.gun_angle = 174.0
	tank.gun_power = 99.0
	tank.gun_angle_change_speed = 75.0
	tank.gun_power_change_speed = 50.0
	tank.update_gun(1.0, 1.0, 1.0)
	assert(abs(tank.gun_angle - TankState.GUN_ANGLE_MAX) < 0.01)
	assert(abs(tank.gun_power - TankState.GUN_POWER_MAX) < 0.01)
	tank.gun_angle = 6.0
	tank.gun_power = 6.0
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
	assert(abs(tank.airborne_velocity.x + 70.0) < 0.01)
	assert(abs(tank.airborne_velocity.y + 121.243) < 0.01)
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
	tank.gun_angle = 0.0
	tank.airborne_velocity = Vector2(12.0, -8.0)
	var tank_launch_velocity := tank.launch_velocity(10.0, 4.2)
	assert(abs(tank_launch_velocity.x - 54.0) < 0.01)
	assert(abs(tank_launch_velocity.y + 8.0) < 0.01)

	var terrain := TerrainModel.new()
	terrain.rebuild_with_seed(320.0, 240.0, 1401)
	tank.position = Vector2(160.0, 20.0)
	tank.airborne_velocity = Vector2(4.0, -10.0)
	tank.on_ground = false
	tank.settle_on_terrain(terrain, 0.1)
	assert(abs(tank.airborne_velocity.y - 10.0) < 0.01)
	assert(abs(tank.position.x - 160.4) < 0.01)
	assert(abs(tank.position.y - 21.0) < 0.01)
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
	flat_terrain.slope_angle = 31.0
	tank.tank_angle = 31.0
	tank.settle_on_terrain(flat_terrain, 1.0)
	assert(abs(tank.position.x - (120.0 + 74.0 * 31.0 / 65.0)) < 0.01)
	assert(abs(tank.tank_angle - 31.0) < 0.01)
	tank.position = Vector2(120.0, 100.0)
	flat_terrain.slope_angle = -31.0
	tank.tank_angle = -31.0
	tank.settle_on_terrain(flat_terrain, 1.0)
	assert(abs(tank.position.x - (120.0 - 74.0 * 31.0 / 65.0)) < 0.01)
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

	local_match.queue_free()
	await process_frame
	quit(0)


func _clear_projectiles(local_match: Node) -> void:
	var projectiles: Array = local_match.get("_projectiles")
	projectiles.clear()
	local_match.set("_projectiles", projectiles)


func _clear_explosions(local_match: Node) -> void:
	var explosions: Array = local_match.get("_explosions")
	explosions.clear()
	local_match.set("_explosions", explosions)
