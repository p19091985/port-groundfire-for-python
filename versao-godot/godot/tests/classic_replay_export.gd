extends SceneTree

# Runs the production LocalMatch projectile updater. The adapter supplies only
# the test environment (empty world and no tanks), never replacement physics.
const MatchRuntime := preload("res://scripts/local_match.gd")
const Terrain := preload("res://scripts/terrain_model.gd")
const FixedStep := preload("res://scripts/classic_fixed_step.gd")
const Settings := preload("res://scripts/control_settings.gd")
const SCALE := preload("res://scripts/classic_world.gd").SCALE
const ORIGIN := preload("res://scripts/classic_world.gd").ORIGIN

class EmptyTerrain:
	extends Terrain
	func projectile_bounds() -> Vector2:
		return Vector2(ORIGIN.x - 100.0 * SCALE, ORIGIN.x + 100.0 * SCALE)
	func ground_collision(_start: Vector2, _end: Vector2) -> Dictionary:
		return {"hit": false, "position": Vector2.ZERO, "distance": INF}
	func height_at(_x: float) -> float:
		return (1000.0 * SCALE)

class ObservedRuntime:
	extends MatchRuntime
	var replay_events: Array = []
	func _after_explosion() -> void:
		# No UI or round lifecycle in this isolated projectile scenario.
		pass
	func _apply_explosion(position: Vector2, projectile: Dictionary, direct_hit_owner := "", classic_position: Array = []) -> void:
		replay_events.append({"position": [(float(position.x) - ORIGIN.x) / SCALE, (ORIGIN.y - float(position.y)) / SCALE],
			"size": float(projectile.weapon.blast) / SCALE, "damage": float(projectile.weapon.damage), "white_out": bool(projectile.weapon.white_out)})
		super._apply_explosion(position, projectile, direct_hit_owner, classic_position)

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2:
		push_error("Expected input-scenarios.json output-replay.json")
		quit(2)
		return
	var source: Variant = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not source is Dictionary or not source.has("scenarios"):
		quit(2)
		return
	var scenarios: Array = []
	Settings.apply_saved_bindings()
	for spec in source.scenarios:
		scenarios.append(_trace(spec))
	var timing: Array = []
	for spec in source.timing:
		var stepper := FixedStep.new()
		var frames: Array = []
		for index in range(spec.deltas.size()):
			var steps := stepper.consume(float(spec.deltas[index]))
			frames.append({"frame": index, "steps": steps, "accumulator": stepper.accumulator()})
		timing.append({"id": spec.id, "frames": frames})
	var output := FileAccess.open(args[1], FileAccess.WRITE)
	if output == null:
		quit(2)
		return
	output.store_string(JSON.stringify({"schema": 1, "scenarios": scenarios, "timing": timing}, "  ") + "\n")
	output.close()
	print("Godot production projectile replay exported")
	quit(0)

func _point(value: Vector2) -> Array:
	return [(float(value.x) - ORIGIN.x) / SCALE, (ORIGIN.y - float(value.y)) / SCALE]

func _trace(spec: Dictionary) -> Dictionary:
	var runtime := ObservedRuntime.new()
	var owner := "Replay"
	if spec.has("commands"):
		runtime.setup({"roster": [{"name": "Replay", "controller": 0, "kind": "human"}]})
		owner = runtime.call("_participant_owner", 0)
	runtime.set("_terrain", EmptyTerrain.new())
	if spec.has("ground"):
		var terrain := Terrain.new()
		terrain.set("_width", (22.0 * SCALE))
		terrain.set("_height", (1000.0 * SCALE))
		terrain.set("_step", (22.0 * SCALE) / 500.0)
		var chunks: Array = []
		for index in range(500):
			var top := ORIGIN.y - float(spec.ground) * SCALE
			var bottom := ORIGIN.y + 10.0 * SCALE
			chunks.append([terrain.call("_make_chunk", top, top, bottom, bottom, false, Color.BLACK, Color.BLACK)])
		terrain.set("_chunks", chunks)
		runtime.set("_terrain", terrain)
	runtime.set("_world_size", Vector2(22.0 * SCALE, 1000.0 * SCALE))
	runtime.set("_wind", 0.0)
	runtime.set("_wind_gust", 0.0)
	var initial: Dictionary = spec.initial
	var position := Vector2(ORIGIN.x + float(initial.position[0]) * SCALE, ORIGIN.y - float(initial.position[1]) * SCALE)
	var velocity := Vector2(float(initial.velocity[0]) * SCALE, -float(initial.velocity[1]) * SCALE)
	var weapon := {"name": spec.kind, "kind": spec.kind, "blast": float(initial.blast) * SCALE, "damage": initial.damage,
		"white_out": spec.kind == "nuke", "fuel": initial.get("fuel", 3.0), "fragments": 5, "spread": 0.2}
	runtime.call("_fire_from", position, float(initial.get("angle", 0.0)), 10.0, owner, weapon, Vector2.ZERO, velocity)
	var projectile: Dictionary = runtime.get("_projectiles")[0]
	var frames: Array = []
	var step := float(spec.step)
	for tick in range(int(spec.ticks) + 1):
		for command in spec.get("commands", []):
			if int(command.tick) == tick:
				for direction in ["left", "right"]:
					var action := "gf_aim_" + str(direction)
					if command.buttons.has(direction):
						Input.action_press(action)
					else:
						Input.action_release(action)
		if tick > 0:
			runtime.call("_update_projectiles", step)
		var alive: bool = runtime.get("_projectiles").has(projectile) and not bool(projectile.get("expired", false))
		var frame := {"tick": tick, "alive": alive, "position": _point(projectile.position), "spawned": [], "explosions": runtime.replay_events.duplicate(true)}
		if spec.kind == "machine_gun":
			frame["back_position"] = _point(projectile.back_position)
			frame["kill_next_frame"] = bool(projectile.get("kill_next_frame", false))
		if spec.kind == "missile":
			frame["fuel"] = float(projectile.fuel)
			frame["angle"] = float(projectile.angle)
			frame["angle_change"] = float(projectile.angle_change)
		for child in runtime.get("_projectiles"):
			if is_same(child, projectile):
				continue
			frame.spawned.append({"position": _point(child.position), "velocity": [float(child.velocity.x) / SCALE, -float(child.velocity.y) / SCALE]})
		frames.append(frame)
		if not alive:
			break
	Input.action_release("gf_aim_left")
	Input.action_release("gf_aim_right")
	runtime.free()
	return {"id": spec.id, "frames": frames}
