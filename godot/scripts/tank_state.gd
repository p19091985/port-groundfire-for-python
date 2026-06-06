extends RefCounted

const STATE_ALIVE := "alive"
const STATE_DEAD := "dead"
const GUN_ANGLE_MIN := -75.0
const GUN_ANGLE_MAX := 75.0
const GUN_ANGLE_DEFAULT := 0.0
const GUN_ANGLE_CHANGE_ACCELERATION := 60.0
const GUN_ANGLE_MAX_CHANGE_SPEED := 75.0
const GUN_POWER_MIN := 1.0
const GUN_POWER_MAX := 20.0
const GUN_POWER_DEFAULT := 10.0
const GUN_POWER_CHANGE_ACCELERATION := 20.0
const GUN_POWER_MAX_CHANGE_SPEED := 50.0
const GUN_POWER_PIXEL_SCALE := 5.5
const TANK_MAX_HEALTH := 100
const TANK_FULL_FUEL := 1.0
const TANK_FUEL_PURCHASE_AMOUNT := 1.0
const TANK_BOOST_ACCELERATION := 133.0
const BOOST_FUEL_USAGE_RATE := 0.2
const BOOST_TURN_RATE := 90.0
const BOOST_TURN_LIMIT := 15.0
const TANK_AIR_GRAVITY := 95.0
const TANK_GROUND_DETACH_THRESHOLD := 2.0
const TANK_MOVE_SPEED := 74.0
const TANK_SLOPE_DRAG_SCALE := 65.0
const TANK_MIN_SLOPE_MOVE_FACTOR := 0.35
const TANK_PASSIVE_SLIDE_THRESHOLD := 30.0
const TANK_BODY_HALF_WIDTH := 26.0
const TANK_CENTER_OFFSET := TANK_BODY_HALF_WIDTH * 0.5
const GUN_LAUNCH_OFFSET := TANK_BODY_HALF_WIDTH * 1.2
const SHIELD_DAMAGE_MULTIPLIER := 0.5
const SHIELD_FUEL_USAGE_RATE := 0.12
const GROUND_SMOKE_RELEASE_TIME := 1.0
const AIR_SMOKE_RELEASE_TIME := 0.05
const SMOKE_TEXTURE_ID := 5
const GROUND_SMOKE_Y_OFFSET := 0.2
const SMOKE_Y_VELOCITY := 0.5
const SMOKE_ROTATION_RATE := 0.1
const GROUND_SMOKE_GROWTH_RATE := 0.3
const GROUND_SMOKE_FADE_RATE := 0.15
const AIR_SMOKE_FADE_RATE := 0.3
const BOOST_SMOKE_RELEASE_TIME := 0.05
const BOOST_SMOKE_TEXTURE_ID := 2
const BOOST_SMOKE_VELOCITY := 2.0
const BOOST_SMOKE_ROTATION_RATE := 0.0
const BOOST_SMOKE_GROWTH_RATE := 0.0
const BOOST_SMOKE_FADE_RATE := 2.5

var name := "Player"
var body_color := Color.WHITE
var position := Vector2.ZERO
var tank_angle := 0.0
var gun_angle := GUN_ANGLE_DEFAULT
var gun_angle_change_speed := 0.0
var gun_power := GUN_POWER_DEFAULT
var gun_power_change_speed := 0.0
var health := TANK_MAX_HEALTH
var fuel := TANK_FULL_FUEL
var fuel_capacity := TANK_FULL_FUEL
var fuel_reserve := TANK_FULL_FUEL
var state := STATE_ALIVE
var on_ground := true
var airborne_velocity := Vector2.ZERO
var shield_active := false
var hover_time := 0.0
var corbomite_active := false
var exhaust_time := 0.0


func reset_round(x: float, terrain: RefCounted, label: String, color: Color) -> void:
	name = label
	body_color = color
	position = terrain.tank_position(x)
	tank_angle = 0.0
	gun_angle = GUN_ANGLE_DEFAULT
	gun_angle_change_speed = 0.0
	gun_power = GUN_POWER_DEFAULT
	gun_power_change_speed = 0.0
	health = TANK_MAX_HEALTH
	fuel_capacity = TANK_FULL_FUEL
	fuel = min(TANK_FULL_FUEL, fuel_reserve)
	state = STATE_ALIVE
	on_ground = false
	airborne_velocity = Vector2.ZERO
	shield_active = false
	hover_time = 0.0
	corbomite_active = false
	exhaust_time = 0.0


func settle_on_terrain(terrain: RefCounted, delta := 0.0) -> void:
	if hover_time > 0.0:
		hover_time -= delta
		if hover_time < 0.0:
			hover_time = 0.0
		on_ground = false
		airborne_velocity.y -= TANK_AIR_GRAVITY * 0.45 * delta
		airborne_velocity.y = max(-130.0, airborne_velocity.y)
		_spend_fuel(0.18 * delta)
		position += airborne_velocity * delta
		var ground_position := _ground_position_for_query(terrain, position.x, position.y)
		var terr_y: float = ground_position.y
		if position.y < terr_y - 180.0:
			position.y = terr_y - 180.0
			airborne_velocity.y = 0.0
		elif position.y >= terr_y:
			position = ground_position
			airborne_velocity = Vector2.ZERO
			on_ground = true
	elif not on_ground:
		airborne_velocity.y += TANK_AIR_GRAVITY * delta
		position += airborne_velocity * delta
		var ground_position := _ground_position_for_query(terrain, position.x, position.y)
		if position.y >= ground_position.y:
			position = ground_position
			airborne_velocity = Vector2.ZERO
			on_ground = true
	else:
		var ground_position := _ground_position_for_query(terrain, position.x, position.y)
		if ground_position.y > position.y + TANK_GROUND_DETACH_THRESHOLD:
			on_ground = false
		else:
			position = ground_position
			_apply_passive_slope_slide(delta, terrain, terrain.slope_angle_at(position.x))
	_constrain_to_terrain_bounds(terrain)
	if on_ground:
		tank_angle = terrain.slope_angle_at(position.x)


func move_on_terrain(direction: float, delta: float, terrain: RefCounted) -> void:
	if state != STATE_ALIVE:
		return
	if not on_ground:
		return
	var slope_term: float = -(tank_angle / TANK_SLOPE_DRAG_SCALE)
	var track_delta: float = (direction + slope_term) * TANK_MOVE_SPEED * delta
	var next_x: float = position.x + cos(deg_to_rad(tank_angle)) * track_delta
	position = _ground_position_for_query(terrain, next_x, position.y)
	tank_angle = terrain.slope_angle_at(position.x)


func _apply_passive_slope_slide(delta: float, terrain: RefCounted, ground_angle: float) -> void:
	if delta <= 0.0 or state != STATE_ALIVE:
		return
	if abs(ground_angle) <= TANK_PASSIVE_SLIDE_THRESHOLD:
		return
	var slide_speed: float = TANK_MOVE_SPEED * (abs(ground_angle) / TANK_SLOPE_DRAG_SCALE)
	var horizontal_delta: float = cos(deg_to_rad(ground_angle)) * slide_speed * delta
	position = _ground_position_for_query(terrain, position.x - sign(ground_angle) * horizontal_delta, position.y)


func _ground_position_for_query(terrain: RefCounted, x: float, query_y: float) -> Vector2:
	if terrain.has_method("move_to_ground"):
		return Vector2(x, float(terrain.call("move_to_ground", x, query_y)))
	return terrain.tank_position(x)


func _constrain_to_terrain_bounds(terrain: RefCounted) -> void:
	if not terrain.has_method("playable_bounds"):
		return
	var bounds: Vector2 = terrain.playable_bounds()
	if position.x < bounds.x:
		position.x = bounds.x
		airborne_velocity.x = 0.0
	elif position.x > bounds.y:
		position.x = bounds.y
		airborne_velocity.x = 0.0


func boost(delta: float, air_turn_direction := 0.0) -> void:
	if state != STATE_ALIVE or fuel <= 0.0:
		return
	var radians := deg_to_rad(tank_angle)
	on_ground = false
	airborne_velocity.x -= sin(radians) * TANK_BOOST_ACCELERATION * delta
	airborne_velocity.y -= cos(radians) * TANK_BOOST_ACCELERATION * delta
	_spend_fuel(BOOST_FUEL_USAGE_RATE * delta)
	_update_boost_turn(delta, air_turn_direction)


func update_shield(active: bool, delta: float) -> void:
	if state != STATE_ALIVE or not active or fuel <= 0.0:
		shield_active = false
		return
	shield_active = true
	_spend_fuel(SHIELD_FUEL_USAGE_RATE * max(0.0, delta))
	if fuel <= 0.0:
		shield_active = false


func _update_boost_turn(delta: float, air_turn_direction: float) -> void:
	if air_turn_direction < 0.0 and tank_angle < BOOST_TURN_LIMIT:
		tank_angle += BOOST_TURN_RATE * delta
	elif air_turn_direction > 0.0 and tank_angle > -BOOST_TURN_LIMIT:
		tank_angle -= BOOST_TURN_RATE * delta
	elif tank_angle < 0.0:
		tank_angle += BOOST_TURN_RATE * delta
		if tank_angle > 0.0:
			tank_angle = 0.0
	elif tank_angle > 0.0:
		tank_angle -= BOOST_TURN_RATE * delta
		if tank_angle < 0.0:
			tank_angle = 0.0


func update_gun(delta: float, aim_direction: float, power_direction: float) -> void:
	if aim_direction != 0.0:
		gun_angle_change_speed += aim_direction * GUN_ANGLE_CHANGE_ACCELERATION * delta
		gun_angle_change_speed = clamp(gun_angle_change_speed, -GUN_ANGLE_MAX_CHANGE_SPEED, GUN_ANGLE_MAX_CHANGE_SPEED)
	else:
		gun_angle_change_speed = 0.0
	if power_direction != 0.0:
		gun_power_change_speed += power_direction * GUN_POWER_CHANGE_ACCELERATION * delta
		gun_power_change_speed = clamp(gun_power_change_speed, -GUN_POWER_MAX_CHANGE_SPEED, GUN_POWER_MAX_CHANGE_SPEED)
	else:
		gun_power_change_speed = 0.0
	gun_angle = clamp(gun_angle + gun_angle_change_speed * delta, GUN_ANGLE_MIN, GUN_ANGLE_MAX)
	gun_power = clamp(gun_power + gun_power_change_speed * delta, GUN_POWER_MIN, GUN_POWER_MAX)


func aim_at(screen_position: Vector2) -> void:
	var origin := launch_origin()
	var direction := screen_position - origin
	if direction.length_squared() <= 1.0:
		return
	gun_angle = clamp(rad_to_deg(atan2(-direction.x, -direction.y)), GUN_ANGLE_MIN, GUN_ANGLE_MAX)


func gun_direction() -> Vector2:
	var radians: float = deg_to_rad(gun_angle)
	return Vector2(-sin(radians), -cos(radians)).normalized()


func tank_center() -> Vector2:
	var radians: float = deg_to_rad(tank_angle)
	return position + Vector2(
		-sin(radians) * TANK_CENTER_OFFSET,
		-cos(radians) * TANK_CENTER_OFFSET
	)


func apply_damage(amount: int) -> bool:
	health -= amount
	if health < 0 and state == STATE_ALIVE:
		health = 0
		state = STATE_DEAD
		shield_active = false
		exhaust_time = -0.5
		return true
	return false


func damage_after_shield(amount: int) -> int:
	var raw_damage: int = max(0, amount)
	if not shield_active:
		return raw_damage
	return int(round(float(raw_damage) * SHIELD_DAMAGE_MULTIPLIER))


func launch_origin() -> Vector2:
	return tank_center() + gun_direction() * GUN_LAUNCH_OFFSET


func launch_velocity(power: float, speed_multiplier := 1.0) -> Vector2:
	return airborne_velocity + gun_direction() * power * GUN_POWER_PIXEL_SCALE * speed_multiplier


func add_fuel_capacity(amount := TANK_FUEL_PURCHASE_AMOUNT) -> float:
	return add_fuel_reserve(amount)


func add_fuel_reserve(amount := TANK_FUEL_PURCHASE_AMOUNT) -> float:
	fuel_reserve = max(0.0, fuel_reserve) + max(0.0, amount)
	return fuel_reserve


func _spend_fuel(amount: float) -> void:
	var fuel_spent: float = min(fuel, max(0.0, amount))
	fuel = max(0.0, fuel - fuel_spent)
	fuel_reserve = max(0.0, fuel_reserve - fuel_spent)


func snapshot() -> Dictionary:
	return {
		"name": name,
		"health": health,
		"fuel": fuel,
		"fuel_capacity": fuel_capacity,
		"fuel_reserve": fuel_reserve,
		"state": state,
		"tank_angle": tank_angle,
		"gun_angle": gun_angle,
		"gun_power": gun_power,
		"on_ground": on_ground,
		"shield_active": shield_active,
	}
