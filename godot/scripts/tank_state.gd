extends RefCounted

const STATE_ALIVE := "alive"
const STATE_DEAD := "dead"

var name := "Player"
var body_color := Color.WHITE
var position := Vector2.ZERO
var tank_angle := 0.0
var gun_angle := 45.0
var gun_angle_change_speed := 0.0
var gun_power := 55.0
var gun_power_change_speed := 0.0
var health := 100
var fuel := 1.0
var state := STATE_ALIVE
var on_ground := true
var airborne_velocity := Vector2.ZERO


func reset_round(x: float, terrain: RefCounted, label: String, color: Color) -> void:
	name = label
	body_color = color
	position = terrain.tank_position(x)
	tank_angle = terrain.slope_angle_at(x)
	gun_angle = 45.0
	gun_angle_change_speed = 0.0
	gun_power = 55.0
	gun_power_change_speed = 0.0
	health = 100
	fuel = 1.0
	state = STATE_ALIVE
	on_ground = true
	airborne_velocity = Vector2.ZERO


func settle_on_terrain(terrain: RefCounted, delta := 0.0) -> void:
	if not on_ground:
		airborne_velocity.y += 410.0 * delta
		position += airborne_velocity * delta
		if position.y >= terrain.height_at(position.x):
			position = terrain.tank_position(position.x)
			airborne_velocity = Vector2.ZERO
			on_ground = true
	else:
		position = terrain.tank_position(position.x)
	tank_angle = terrain.slope_angle_at(position.x)


func move_on_terrain(direction: float, delta: float, terrain: RefCounted) -> void:
	if state != STATE_ALIVE or fuel <= 0.0:
		return
	if not on_ground:
		airborne_velocity.x += direction * 60.0 * delta
		fuel = max(0.0, fuel - abs(direction) * 0.08 * delta)
		return
	var speed := 74.0
	var slope_drag: float = abs(tank_angle) / 65.0
	var next_x: float = position.x + direction * speed * max(0.35, 1.0 - slope_drag) * delta
	position = terrain.tank_position(next_x)
	tank_angle = terrain.slope_angle_at(position.x)
	fuel = max(0.0, fuel - abs(direction) * 0.13 * delta)


func boost(delta: float) -> void:
	if state != STATE_ALIVE or fuel <= 0.0:
		return
	on_ground = false
	airborne_velocity.y -= 280.0 * delta
	fuel = max(0.0, fuel - 0.28 * delta)


func update_gun(delta: float, aim_direction: float, power_direction: float) -> void:
	if aim_direction != 0.0:
		gun_angle_change_speed += aim_direction * 60.0 * delta
		gun_angle_change_speed = clamp(gun_angle_change_speed, -75.0, 75.0)
	else:
		gun_angle_change_speed = move_toward(gun_angle_change_speed, 0.0, 180.0 * delta)
	if power_direction != 0.0:
		gun_power_change_speed += power_direction * 20.0 * delta
		gun_power_change_speed = clamp(gun_power_change_speed, -50.0, 50.0)
	else:
		gun_power_change_speed = move_toward(gun_power_change_speed, 0.0, 160.0 * delta)
	gun_angle = clamp(gun_angle + gun_angle_change_speed * delta, 5.0, 175.0)
	gun_power = clamp(gun_power + gun_power_change_speed * delta, 5.0, 100.0)


func aim_at(screen_position: Vector2) -> void:
	var origin := launch_origin()
	var direction := screen_position - origin
	if direction.length_squared() <= 1.0:
		return
	gun_angle = clamp(rad_to_deg(atan2(-direction.y, direction.x)), 5.0, 175.0)


func apply_damage(amount: int) -> bool:
	health = max(0, health - amount)
	if health <= 0:
		state = STATE_DEAD
		return true
	return false


func launch_origin() -> Vector2:
	var radians: float = deg_to_rad(gun_angle)
	return position + Vector2(cos(radians), -sin(radians)) * 34.0 + Vector2(0.0, -20.0)


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
