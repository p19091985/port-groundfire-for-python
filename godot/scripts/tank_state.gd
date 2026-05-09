extends RefCounted

const STATE_ALIVE := "alive"
const STATE_DEAD := "dead"
const GUN_ANGLE_MIN := 5.0
const GUN_ANGLE_MAX := 175.0
const GUN_ANGLE_DEFAULT := 45.0
const GUN_ANGLE_CHANGE_ACCELERATION := 60.0
const GUN_ANGLE_MAX_CHANGE_SPEED := 75.0
const GUN_POWER_MIN := 5.0
const GUN_POWER_MAX := 100.0
const GUN_POWER_DEFAULT := 55.0
const GUN_POWER_CHANGE_ACCELERATION := 20.0
const GUN_POWER_MAX_CHANGE_SPEED := 50.0
const TANK_MAX_HEALTH := 100
const TANK_FULL_FUEL := 1.0
const TANK_BOOST_ACCELERATION := 280.0
const BOOST_FUEL_USAGE_RATE := 0.2
const BOOST_TURN_RATE := 90.0
const BOOST_TURN_LIMIT := 15.0
const TANK_AIR_GRAVITY := 200.0
const TANK_GROUND_DETACH_THRESHOLD := 2.0
const TANK_MOVE_SPEED := 74.0
const TANK_AIR_CONTROL_ACCELERATION := 60.0
const TANK_GROUND_FUEL_USAGE_RATE := 0.13
const TANK_AIR_STEER_FUEL_USAGE_RATE := 0.08
const TANK_SLOPE_DRAG_SCALE := 65.0
const TANK_MIN_SLOPE_MOVE_FACTOR := 0.35
const TANK_PASSIVE_SLIDE_THRESHOLD := 30.0

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
var state := STATE_ALIVE
var on_ground := true
var airborne_velocity := Vector2.ZERO


func reset_round(x: float, terrain: RefCounted, label: String, color: Color) -> void:
	name = label
	body_color = color
	position = terrain.tank_position(x)
	tank_angle = terrain.slope_angle_at(x)
	gun_angle = GUN_ANGLE_DEFAULT
	gun_angle_change_speed = 0.0
	gun_power = GUN_POWER_DEFAULT
	gun_power_change_speed = 0.0
	health = TANK_MAX_HEALTH
	fuel = TANK_FULL_FUEL
	state = STATE_ALIVE
	on_ground = true
	airborne_velocity = Vector2.ZERO


func settle_on_terrain(terrain: RefCounted, delta := 0.0) -> void:
	if not on_ground:
		airborne_velocity.y += TANK_AIR_GRAVITY * delta
		position += airborne_velocity * delta
		if position.y >= terrain.height_at(position.x):
			position = terrain.tank_position(position.x)
			airborne_velocity = Vector2.ZERO
			on_ground = true
	else:
		var ground_position: Vector2 = terrain.tank_position(position.x)
		if ground_position.y > position.y + TANK_GROUND_DETACH_THRESHOLD:
			on_ground = false
		else:
			position = ground_position
			_apply_passive_slope_slide(delta, terrain, terrain.slope_angle_at(position.x))
	_constrain_to_terrain_bounds(terrain)
	tank_angle = terrain.slope_angle_at(position.x)


func move_on_terrain(direction: float, delta: float, terrain: RefCounted) -> void:
	if state != STATE_ALIVE or fuel <= 0.0:
		return
	if not on_ground:
		airborne_velocity.x += direction * TANK_AIR_CONTROL_ACCELERATION * delta
		fuel = max(0.0, fuel - abs(direction) * TANK_AIR_STEER_FUEL_USAGE_RATE * delta)
		return
	var slope_drag: float = abs(tank_angle) / TANK_SLOPE_DRAG_SCALE
	var move_factor: float = max(TANK_MIN_SLOPE_MOVE_FACTOR, 1.0 - slope_drag)
	var next_x: float = position.x + direction * TANK_MOVE_SPEED * move_factor * delta
	position = terrain.tank_position(next_x)
	tank_angle = terrain.slope_angle_at(position.x)
	fuel = max(0.0, fuel - abs(direction) * TANK_GROUND_FUEL_USAGE_RATE * delta)


func _apply_passive_slope_slide(delta: float, terrain: RefCounted, ground_angle: float) -> void:
	if delta <= 0.0 or state != STATE_ALIVE:
		return
	if abs(ground_angle) <= TANK_PASSIVE_SLIDE_THRESHOLD:
		return
	var slide_speed: float = TANK_MOVE_SPEED * (abs(ground_angle) / TANK_SLOPE_DRAG_SCALE)
	position = terrain.tank_position(position.x + sign(ground_angle) * slide_speed * delta)


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
	fuel = max(0.0, fuel - BOOST_FUEL_USAGE_RATE * delta)
	_update_boost_turn(delta, air_turn_direction)


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
	gun_angle = clamp(rad_to_deg(atan2(-direction.y, direction.x)), GUN_ANGLE_MIN, GUN_ANGLE_MAX)


func apply_damage(amount: int) -> bool:
	health -= amount
	if health < 0 and state == STATE_ALIVE:
		health = 0
		state = STATE_DEAD
		return true
	return false


func launch_origin() -> Vector2:
	var radians: float = deg_to_rad(gun_angle)
	return position + Vector2(cos(radians), -sin(radians)) * 34.0 + Vector2(0.0, -20.0)


func launch_velocity(power: float, speed_multiplier := 1.0) -> Vector2:
	var radians: float = deg_to_rad(gun_angle)
	return airborne_velocity + Vector2(cos(radians), -sin(radians)) * power * speed_multiplier


func snapshot() -> Dictionary:
	return {
		"name": name,
		"health": health,
		"fuel": fuel,
		"state": state,
			"tank_angle": tank_angle,
			"gun_angle": gun_angle,
			"gun_power": gun_power,
			"on_ground": on_ground,
		}
