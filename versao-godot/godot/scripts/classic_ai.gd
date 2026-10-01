extends RefCounted
## Decision state from Python AIPlayer. Coordinates here are classic world units.
## The resulting commands go through the same tank controls as a human player.
const World := preload("res://scripts/classic_world.gd")
const Tank := preload("res://scripts/tank_state.gd")

var target := -1
var target_angle := 0.0
var target_power := 0.0
var target_x := 0.0
var target_y := 0.0
var shots_in_air := 0
var last_x := 0.0
var last_y := 0.0
var last_shot := false
var ignore_shot := false
var on_target := false
var aim_directly := false
var commands: Dictionary = {}

func new_round() -> void:
	target = -1
	target_angle = 0.0
	target_power = 0.0
	on_target = false
	ignore_shot = false
	shots_in_air = 0
	last_shot = false

func _tank(runtime: Object, index: int) -> RefCounted:
	var body: RefCounted = runtime._participant_tank(index)
	body._read_motion_state()
	return body

func command(runtime: Object, index: int) -> Dictionary:
	var result := {}
	commands = result
	if runtime._phase == "shop":
		result["power_up" if int(runtime._shop_select_positions[index]) != 10 else "fire"] = true
		return result
	if runtime._phase != "aim":
		return result
	var body := _tank(runtime, index)
	if target < 0:
		_find_target(runtime, index)
		_guess_aim(runtime, index)
	else:
		var enemy := _tank(runtime, target)
		if enemy.state == Tank.STATE_ALIVE:
			var displacement: float = pow(enemy._motion_x - target_x, 2) + pow(enemy._motion_y - target_y, 2)
			if displacement > 4.0:
				target = -1
			else:
				var ready := true
				var angle_diff: float = body.gun_angle - target_angle
				if angle_diff > 1.0:
					result["aim_right"] = true
					ready = false
				elif angle_diff < -1.0:
					result["aim_left"] = true
					ready = false
				var power_diff: float = body.gun_power - target_power
				if power_diff > 0.2:
					result["power_down"] = true
					ready = false
				elif power_diff < -0.2:
					result["power_up"] = true
					ready = false
				if ready and runtime._participant_inventory(index).is_current_ready():
					if aim_directly and displacement > 0.04:
						ready = false
						_guess_aim(runtime, index)
					if ready and shots_in_air == 0:
						result["fire"] = true
		else:
			target = -1
		if target < 0:
			if shots_in_air > 0:
				ignore_shot = true
			last_shot = false
	return result

func _find_target(runtime: Object, index: int) -> void:
	var body := _tank(runtime, index)
	var top_score := 0
	aim_directly = false
	for candidate in range(runtime._participants.size()):
		if candidate == index or not runtime._participant_is_alive(candidate):
			continue
		var enemy := _tank(runtime, candidate)
		var score := 0
		if not runtime._terrain_hits_segment(body.launch_origin(), enemy.tank_center()):
			score += 100
			if enemy._motion_y > body._motion_y:
				score += 50
				aim_directly = true
		score += 40 - int(2.0 * absf(enemy._motion_x - body._motion_x))
		if score >= top_score:
			top_score = score
			target = candidate

func _guess_aim(runtime: Object, index: int) -> void:
	if target < 0:
		return
	var body := _tank(runtime, index)
	var enemy := _tank(runtime, target)
	var dx: float = enemy._motion_x - body._motion_x
	if aim_directly:
		var dy: float = enemy._motion_y - body._motion_y
		if dy > 0.2:
			target_angle = -(atan(dx / dy) / World.CLASSIC_PI) * 180.0
			target_power = Tank.GUN_POWER_MAX
			if target_angle > Tank.GUN_ANGLE_MAX or target_angle < Tank.GUN_ANGLE_MIN:
				aim_directly = false
		else:
			aim_directly = false
	target_x = enemy._motion_x
	target_y = enemy._motion_y
	if not aim_directly:
		target_angle = -dx * 3.0
		target_power = 10.0
	target_angle = clampf(target_angle, Tank.GUN_ANGLE_MIN, Tank.GUN_ANGLE_MAX)

func record_fired() -> void:
	shots_in_air += 1

func record_shot(runtime: Object, index: int, x: float, y: float, hit: int) -> void:
	shots_in_air = maxi(0, shots_in_air - 1)
	if hit >= 0 and hit < runtime._participants.size() and runtime._participant_is_alive(hit):
		if hit == index:
			target = -1
		elif target < 0 or hit != target:
			target = hit
			var enemy := _tank(runtime, target)
			target_x = enemy._motion_x
			target_y = enemy._motion_y
			on_target = true
		else:
			on_target = true
	elif aim_directly:
		aim_directly = false
		_guess_aim(runtime, index)
		last_shot = false
	elif ignore_shot:
		ignore_shot = false
	elif target >= 0:
		var body := _tank(runtime, index)
		var enemy := _tank(runtime, target)
		var previous_distance: float = last_x - enemy._motion_x
		var distance: float = x - enemy._motion_x
		if last_shot and ((distance < 0.0 and previous_distance < 0.0 and distance < previous_distance) or (distance > 0.0 and previous_distance > 0.0 and distance > previous_distance)):
			target_angle /= 2.0
			target_power = minf(target_power + 2.0, Tank.GUN_POWER_MAX)
			last_shot = false
		else:
			target_angle += absf(sin((target_angle / 180.0) * World.CLASSIC_PI)) * distance * 4.0
			if distance < 0.0:
				target_angle = maxf(target_angle, Tank.GUN_ANGLE_MIN)
			else:
				target_angle = minf(target_angle, Tank.GUN_ANGLE_MAX)
			var correction: float = absf(distance) * 1.2 * (1.0 - sin((absf(target_angle) / 180.0) * World.CLASSIC_PI))
			if enemy._motion_x < body._motion_x:
				target_power += correction if distance >= 0.0 else -correction
			else:
				target_power += correction if distance < 0.0 else -correction
			target_power = clampf(target_power, Tank.GUN_POWER_MIN, Tank.GUN_POWER_MAX)
			last_shot = true
		on_target = false
	last_x = x
	last_y = y
