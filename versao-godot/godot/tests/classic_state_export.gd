extends SceneTree

const Runtime := preload("res://scripts/local_match.gd")
const Settings := preload("res://scripts/control_settings.gd")
const Actions := ["fire", "weapon_next", "weapon_prev", "jump", "shield", "move_left", "move_right", "aim_left", "aim_right", "power_up", "power_down"]
const Weapons := ["Machine Gun", "MIRV", "Missile", "Nuke"]
const World := preload("res://scripts/classic_world.gd")

class ObservedRuntime extends Runtime:
	var menu_requested := false
	var freeze_projectiles := false
	var audio_events: Array = []
	var missile_loop := false
	var machine_gun_loop := false
	func _play_missile_flight_audio() -> void:
		missile_loop = true
		super._play_missile_flight_audio()
	func _stop_missile_flight_audio() -> void:
		missile_loop = false
		super._stop_missile_flight_audio()
	func _play_machine_gun_audio() -> void:
		machine_gun_loop = true
		super._play_machine_gun_audio()
	func _stop_machine_gun_audio(force := false) -> void:
		if force or not _any_machine_gun_fire_held():
			machine_gun_loop = false
		super._stop_machine_gun_audio(force)
	func _play_fire_shell_audio() -> void:
		audio_events.append(0)
		super._play_fire_shell_audio()
	func _play_shell_death_audio() -> void:
		audio_events.append(1)
		super._play_shell_death_audio()
	func _play_launch_missile_audio() -> void:
		audio_events.append(5)
		super._play_launch_missile_audio()
	func _play_missile_death_audio() -> void:
		audio_events.append(6)
		super._play_missile_death_audio()
	func _play_nuke_audio() -> void:
		audio_events.append(7)
		super._play_nuke_audio()
	func _play_metal_hit_audio() -> void:
		audio_events.append(9)
		super._play_metal_hit_audio()
	func _return_to_main_menu() -> void:
		menu_requested = true
	func _update_projectiles(delta: float) -> void:
		if not freeze_projectiles:
			super._update_projectiles(delta)

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2:
		quit(2)
		return
	var source: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	Settings.apply_saved_bindings()
	var scenarios: Array = []
	for spec in source.scenarios:
		scenarios.append(_trace(spec))
	var output := FileAccess.open(args[1], FileAccess.WRITE)
	output.store_string(JSON.stringify({"schema": 1, "scenarios": scenarios}, "  ") + "\n")
	output.close()
	print("Godot tank/reward/shop replay exported")
	quit(0)

func _inputs(player: int, buttons: Array) -> void:
	for index in range(Actions.size()):
		var action := ("gf_" if player == 0 else "gf_p2_") + str(Actions[index])
		if buttons.any(func(value: Variant) -> bool: return int(value) == index):
			Input.action_press(action)
		else:
			Input.action_release(action)

func _trace(spec: Dictionary) -> Dictionary:
	var runtime := ObservedRuntime.new()
	var roster: Array[Dictionary] = []
	for index in range(int(spec.get("players", 2))):
		var computer: bool = Array(spec.get("computers", [])).has(float(index))
		roster.append({"name": "Player %d" % (index + 1), "kind": "computer" if computer else "human", "controller": index})
	runtime.setup({"roster": roster})
	runtime.call("_apply_classic_reference_config")
	var frames: Array = []
	var tank: RefCounted = runtime.call("_participant_tank", 0)
	match str(spec.kind):
		"gun":
			for tick in range(int(spec.ticks) + 1):
				for command in spec.commands:
					if int(command.tick) == tick:
						_inputs(0, command.buttons)
				if tick > 0:
					runtime.call("_handle_participant_input", 0, float(spec.step), false)
				frames.append({"tick": tick, "angle": tank.gun_angle, "power": tank.gun_power,
					"angle_speed": tank.gun_angle_change_speed, "power_speed": tank.gun_power_change_speed})
		"damage":
			for amount in spec.damage:
				var killed: bool = tank.apply_damage(float(amount))
				frames.append({"killed": killed, "health": tank.health, "alive": tank.state == "alive"})
		"weapons":
			runtime.freeze_projectiles = true
			for participant in runtime.get("_participants"):
				for index in range(Weapons.size()):
					participant.inventory.add_ammo(Weapons[index], int(spec.ammo[index]))
				participant.inventory.reset_round_ammo()
			runtime.call("_start_round_turn", "Weapon replay")
			for tick in range(int(spec.ticks) + 1):
				for command in spec.commands:
					if int(command.tick) == tick:
						_inputs(int(command.get("player", 0)), command.buttons)
				if tick > 0:
					runtime.call("_simulate_match_step", 1.0 / 60.0, false)
				var tanks: Array = []
				for index in range(roster.size()):
					var inventory: RefCounted = runtime.call("_participant_inventory", index)
					var ammo: Array = []
					for weapon in Weapons:
						ammo.append(inventory.stock_for(weapon))
					var shots: Array = []
					for projectile in runtime.get("_projectiles"):
						if projectile.owner == runtime.call("_participant_owner", index):
							shots.append(projectile.weapon.name)
					tanks.append({"selected": inventory.current_name(), "cooldown": inventory.current_cooldown(),
						"ready": inventory.is_current_ready(), "ammo": ammo, "shots": shots})
				frames.append({"tick": tick, "starting": runtime.get("_phase") == "round_starting", "tanks": tanks})
		"terrain":
			runtime.size = Vector2(1024.0, 768.0)
			runtime.set("_terrain_seed", int(spec.seed))
			runtime.call("_rebuild_terrain_if_needed", true)
			var terrain: RefCounted = runtime.get("_terrain")
			for operation in spec.operations:
				if operation.has("hole"):
					terrain.apply_crater(World.from_classic(float(operation.hole[0]), float(operation.hole[1])), float(operation.hole[2]) * World.SCALE)
				if operation.has("drop"):
					terrain.drop_terrain(float(operation.drop) * World.SCALE)
				for _tick in range(int(operation.get("ticks", 0))):
					terrain.update(1.0 / 60.0)
				var slices: Array = []
				for chunks in terrain.get("_chunks"):
					var slice: Array = []
					for index in range(chunks.size()):
						var chunk: Dictionary = chunks[index]
						slice.append({"top": [(World.ORIGIN.y - float(chunk.top_left)) / World.SCALE, (World.ORIGIN.y - float(chunk.top_right)) / World.SCALE],
							"bottom": [(World.ORIGIN.y - float(chunk.bottom_left)) / World.SCALE, (World.ORIGIN.y - float(chunk.bottom_right)) / World.SCALE],
							"linked": chunk.linked_to_next,
							"motion": {"falling": chunk.falling, "wait": chunk.wait, "speed": float(chunk.speed) / World.SCALE}
								if index == 0 or not chunks[index - 1].linked_to_next else null})
					slices.append(slice)
				frames.append({"terrain": slices})
		"explosions":
			runtime.size = Vector2(1024.0, 768.0)
			runtime.set("_terrain_seed", int(spec.seed))
			runtime.call("_rebuild_terrain_if_needed", true)
			for index in range(spec.initial.size()):
				var target: RefCounted = runtime.call("_participant_tank", index)
				var initial: Dictionary = spec.initial[index]
				target.position = World.from_classic(float(initial.position[0]), float(initial.position[1]))
				target.health = float(initial.get("health", 100.0))
			for blast in spec.blasts:
				var projectile := {"kind": "shell", "owner": runtime.call("_participant_owner", int(blast.owner)),
					"weapon": {"damage": int(blast.damage), "blast": float(blast.radius) * World.SCALE}}
				var hit_owner: String = runtime.call("_participant_owner", int(blast.hit)) if int(blast.get("hit", -1)) >= 0 else ""
				runtime.call("_apply_explosion", World.from_classic(float(blast.position[0]), float(blast.position[1])), projectile, hit_owner)
				var tanks: Array = []
				for index in range(roster.size()):
					var target: RefCounted = runtime.call("_participant_tank", index)
					var defeated: Array = []
					for victim in runtime.get("_round_defeats").get(runtime.call("_participant_owner", index), []):
						defeated.append(runtime.call("_participant_index_for_owner", victim))
					tanks.append({"health": target.health, "alive": target.state == "alive",
						"position": [(target.position.x - World.ORIGIN.x) / World.SCALE, (World.ORIGIN.y - target.position.y) / World.SCALE], "defeated": defeated})
				frames.append({"tanks": tanks})
		"rewards":
			for index in range(spec.initial.size()):
				var initial: Dictionary = spec.initial[index]
				var participant: Dictionary = runtime.get("_participants")[index]
				participant.score = int(initial.score)
				participant.credits = int(initial.money)
				participant.leader = initial.leader
				participant.tank.state = "alive" if initial.alive else "dead"
			for defeat in spec.defeats:
				var attacker: String = runtime.call("_participant_owner", int(defeat[0]))
				var victim: String = runtime.call("_participant_owner", int(defeat[1]))
				var defeats: Dictionary = runtime.get("_round_defeats")
				if not defeats.has(attacker):
					defeats[attacker] = []
				defeats[attacker].append(victim)
			runtime.set("_score", int(spec.initial[0].score))
			runtime.set("_credits", int(spec.initial[0].money))
			runtime.set("_enemy_score", int(spec.initial[1].score))
			runtime.call("_apply_classic_round_rewards", "")
			for participant in runtime.get("_participants"):
				frames.append({"score": participant.score, "money": participant.credits})
		"phases":
			runtime.call("_start_round_turn", "Phase replay")
			for tick in range(int(spec.ticks) + 1):
				if tick > 0:
					match str(runtime.get("_phase")):
						"round_starting": runtime.call("_update_round_starting", float(spec.step))
						"round_finishing": runtime.call("_update_round_finishing", float(spec.step))
				for death in spec.deaths:
					if int(death.tick) == tick:
						var victim: RefCounted = runtime.call("_participant_tank", int(death.victim))
						if victim.apply_damage(101.0):
							runtime.call("_record_round_defeat", runtime.call("_participant_owner", int(death.attacker)), runtime.call("_participant_owner", int(death.victim)))
						runtime.call("_after_explosion")
				var players: Array = []
				for index in range(roster.size()):
					players.append({"alive": runtime.call("_participant_is_alive", index),
						"score": runtime.call("_participant_score", index), "money": runtime.call("_participant_credits", index)})
				frames.append({"tick": tick, "phase": runtime.get("_phase"), "players": players})
		"score":
			runtime.set("_round", int(spec.round))
			runtime.set("_phase", "score")
			runtime.set("_score_continue_delay", 2.0)
			for index in range(spec.initial.size()):
				runtime.get("_participants")[index].score = int(spec.initial[index].score)
				runtime.get("_participants")[index].leader = spec.initial[index].leader
			runtime.set("_score", int(spec.initial[0].score))
			runtime.set("_enemy_score", int(spec.initial[1].score))
			for tick in range(int(spec.ticks) + 1):
				for command in spec.commands:
					if int(command.tick) == tick:
						_inputs(int(command.player), command.buttons)
				if tick > 0:
					runtime.call("_update_modal_activation", float(spec.step))
				var leaders: Array = []
				for participant in runtime.get("_participants"):
					leaders.append(participant.leader)
				frames.append({"tick": tick, "phase": runtime.get("_phase"), "leaders": leaders})
				if runtime.get("_phase") != "score":
					break
		"ai":
			runtime.size = Vector2(1024.0, 768.0)
			runtime.set("_terrain_seed", int(spec.seed))
			runtime.call("_rebuild_terrain_if_needed", true)
			runtime.call("_start_round_turn", "AI replay")
			runtime.set("_phase", "aim")
			var index := int(spec.computers[0])
			var bot: RefCounted = runtime.get("_participants")[index].classic_ai
			runtime.call("_participant_inventory", index).update_current_cooldown(4.0)
			for event in spec.events:
				if event.has("move"):
					var body: RefCounted = runtime.call("_participant_tank", int(event.move[0]))
					body._motion_x = float(event.move[1])
					body._motion_y = float(event.move[2])
					body._write_motion_state()
				if event.has("dead"):
					runtime.call("_participant_tank", int(event.dead)).state = "dead"
				if event.has("fired"):
					bot.record_fired()
				if event.has("shot"):
					bot.record_shot(runtime, index, float(event.shot[0]), float(event.shot[1]), int(event.shot[2]))
				if event.has("new_round"):
					bot.new_round()
				if event.has("phase"):
					runtime.set("_phase", {"ROUND_IN_ACTION": "aim", "ROUND_STARTING": "round_starting", "ROUND_FINISHING": "round_finishing"}[event.phase])
				bot.command(runtime, index)
				frames.append(_ai_snapshot(runtime, index))
		"combat":
			runtime.size = Vector2(1024.0, 768.0)
			runtime.set("_total_rounds", int(spec.get("total_rounds", 5)))
			runtime.set("_terrain_seed", int(spec.seed))
			runtime.call("_rebuild_terrain_if_needed", true)
			runtime.call("_start_round_turn", "Combat replay")
			for index in range(Array(spec.get("initial_fuel", [])).size()):
				var body: RefCounted = runtime.call("_participant_tank", index)
				body.fuel = float(spec.initial_fuel[index])
				body.fuel_reserve = float(spec.initial_fuel[index])
			if spec.has("quake_countdown"):
				runtime.set("_quake_countdown", float(spec.quake_countdown))
			var shop_ticks := 0
			var second_round_ticks := 0
			var round_tick := 0
			var previous_round := 1
			for index in range(Array(spec.get("initial_money", [])).size()):
				runtime.call("_set_shop_credits", index, int(spec.initial_money[index]))
			for index in range(Array(spec.get("loadouts", [])).size()):
				var inventory: RefCounted = runtime.call("_participant_inventory", index)
				for weapon in range(Weapons.size()):
					inventory.add_ammo(Weapons[weapon], int(spec.loadouts[index].ammo[weapon]))
				inventory.reset_round_ammo()
				inventory.select_by_name(str(spec.loadouts[index].selected))
			for index in range(Array(spec.get("initial_tanks", [])).size()):
				var body: RefCounted = runtime.call("_participant_tank", index)
				var initial: Dictionary = spec.initial_tanks[index]
				if initial.has("x"):
					body.set_position_on_ground(World.ORIGIN.x + float(initial.x) * World.SCALE, runtime.get("_terrain"))
				body.gun_angle = float(initial.get("angle", body.gun_angle))
				body.gun_power = float(initial.get("power", body.gun_power))
			for tick in range(int(spec.ticks) + 1):
				runtime.audio_events.clear()
				for command in spec.commands:
					if int(command.tick) == tick:
						_inputs(int(command.get("player", 0)), command.buttons)
				if bool(spec.get("complete_match", false)) and runtime.get("_phase") in ["round_starting", "aim", "round_finishing"]:
					for command in spec.round_commands:
						if int(command.tick) == round_tick + 1:
							_inputs(int(command.get("player", 0)), command.buttons)
				if bool(spec.get("cycle", false)):
					if runtime.get("_phase") == "score":
						for index in range(roster.size()):
							_inputs(index, [0])
					elif runtime.get("_phase") == "shop":
						shop_ticks += 1
						for index in range(roster.size()):
							_inputs(index, [0] if shop_ticks == 30 or shop_ticks >= 60 else ([9] if shop_ticks == 45 else []))
				if tick > 0:
					runtime.call("_simulate_match_step", 1.0 / 60.0, false)
					round_tick += 1
				if int(runtime.get("_round")) != previous_round:
					previous_round = int(runtime.get("_round"))
					round_tick = 0
					shop_ticks = 0
				if int(runtime.get("_round")) == 2:
					if second_round_ticks == 0:
						for index in range(roster.size()):
							_inputs(index, [])
					second_round_ticks += 1
				var tanks: Array = []
				for index in range(roster.size()):
					var target: RefCounted = runtime.call("_participant_tank", index)
					var inventory: RefCounted = runtime.call("_participant_inventory", index)
					var ammo: Array = []
					for weapon in Weapons:
						ammo.append(inventory.stock_for(weapon))
					tanks.append({"position": [(target.position.x - World.ORIGIN.x) / World.SCALE, (World.ORIGIN.y - target.position.y) / World.SCALE],
						"body_angle": target.tank_angle, "health": target.health, "alive": target.state == "alive",
						"gun_angle": target.gun_angle, "gun_power": target.gun_power, "fuel": target.fuel,
						"simulation_position": [target._motion_x, target._motion_y],
						"score": runtime.call("_participant_score", index), "money": runtime.call("_participant_credits", index),
						"selected": inventory.current_name(), "ammo": ammo, "cooldown": inventory.current_cooldown()})
				var projectiles: Array = []
				for projectile in runtime.get("_projectiles"):
					projectiles.append({"position": [(projectile.position.x - World.ORIGIN.x) / World.SCALE, (World.ORIGIN.y - projectile.position.y) / World.SCALE],
						"owner": runtime.call("_participant_index_for_owner", projectile.owner), "kind": projectile.kind})
				frames.append({"tick": tick, "phase": runtime.get("_phase"), "tanks": tanks, "projectiles": projectiles})
				if Array(spec.get("terrain_ticks", [])).has(float(tick)):
					var slices: Array = []
					var landscape: RefCounted = runtime.get("_terrain")
					for chunks in landscape.get("_chunks"):
						var layers: Array = []
						for chunk in chunks:
							var heights: Array = landscape.call("_classic_heights", chunk)
							layers.append({"top": [heights[0], heights[1]], "bottom": [heights[2], heights[3]], "linked": chunk.linked_to_next})
						slices.append(layers)
					frames[-1]["terrain"] = slices
				if bool(spec.get("audio", false)):
					runtime.audio_events.sort()
					frames[-1]["audio_one_shots"] = runtime.audio_events.duplicate()
					var loops: Array = []
					if runtime.get("_quake_active"):
						loops.append(2)
					for kind in ["jets", "missile", "machine_gun"]:
						for source in runtime.get("_loop_voices").get(kind, {}):
							loops.append({"jets":3, "missile":4, "machine_gun":8}[kind])
					frames[-1]["audio_loops"] = loops
				if not Array(spec.get("computers", [])).is_empty():
					var brains: Array = []
					for index in spec.computers:
						brains.append(_ai_snapshot(runtime, int(index)))
					frames[-1]["ai"] = brains
				if bool(spec.get("cycle", false)):
					frames[-1]["round"] = runtime.get("_round")
					var stocks: Array = []
					var shop: Array = []
					for index in range(roster.size()):
						var inventory: RefCounted = runtime.call("_participant_inventory", index)
						var ammo: Array = []
						for weapon in Weapons:
							ammo.append(inventory.stock_for(weapon))
						stocks.append(ammo)
						if runtime.get("_phase") == "shop":
							shop.append({"selection": runtime.get("_shop_select_positions")[index], "done": runtime.get("_shop_done")[index]})
					frames[-1]["stocks"] = stocks
					frames[-1]["shop"] = shop
					if bool(spec.get("complete_match", false)) and runtime.get("_phase") == "winner":
						break
					if not bool(spec.get("complete_match", false)) and second_round_ticks >= 126:
						break
				elif runtime.get("_phase") == "score":
					break
		"motion":
			var step := 1.0 / float(spec.step_hz)
			runtime.size = Vector2(1024.0, 768.0)
			runtime.set("_terrain_seed", int(spec.seed))
			runtime.call("_rebuild_terrain_if_needed", true)
			runtime.set("_phase", "aim")
			for index in range(spec.initial.size()):
				var initial: Dictionary = spec.initial[index]
				var target: RefCounted = runtime.call("_participant_tank", index)
				target.set_position_on_ground(World.ORIGIN.x + float(initial.x) * World.SCALE, runtime.get("_terrain"))
				target.position.y -= float(initial.get("height", 0.0)) * World.SCALE
				target.tank_angle = float(initial.get("angle", 0.0))
				target.on_ground = bool(initial.get("grounded", true))
				target.fuel = float(initial.get("fuel", 0.0))
				target.fuel_reserve = target.fuel
				var velocity: Array = initial.get("velocity", [0.0, 0.0])
				target.airborne_velocity = Vector2(float(velocity[0]) * World.SCALE, -float(velocity[1]) * World.SCALE)
				if bool(initial.get("dead", false)):
					target.state = "dead"
			for tick in range(int(spec.ticks) + 1):
				for command in spec.commands:
					if int(command.tick) == tick:
						_inputs(int(command.get("player", 0)), command.buttons)
				if tick > 0:
					runtime.call("_simulate_match_step", step, false)
				var tanks: Array = []
				for participant in runtime.get("_participants"):
					var target: RefCounted = participant.tank
					tanks.append({"position": [(target.position.x - World.ORIGIN.x) / World.SCALE, (World.ORIGIN.y - target.position.y) / World.SCALE],
						"velocity": [target.airborne_velocity.x / World.SCALE, -target.airborne_velocity.y / World.SCALE],
						"angle": target.tank_angle, "grounded": target.on_ground, "fuel": target.fuel, "reserve": target.fuel_reserve})
				frames.append({"tick": tick, "tanks": tanks})
		"world":
			runtime.size = Vector2(1024.0, 768.0)
			runtime.set("_terrain_seed", int(spec.seed))
			runtime.call("_rebuild_terrain_if_needed", true)
			var terrain: Array = []
			for chunks in runtime.get("_terrain").get("_chunks"):
				var slice: Array = []
				for chunk in chunks:
					slice.append({"top": [(World.ORIGIN.y - float(chunk.top_left)) / World.SCALE, (World.ORIGIN.y - float(chunk.top_right)) / World.SCALE],
						"bottom": [(World.ORIGIN.y - float(chunk.bottom_left)) / World.SCALE, (World.ORIGIN.y - float(chunk.bottom_right)) / World.SCALE], "linked": chunk.linked_to_next})
				terrain.append(slice)
			var tanks: Array = []
			for index in range(roster.size()):
				var body: RefCounted = runtime.call("_participant_tank", index)
				body.gun_angle = float(spec.angles[index % spec.angles.size()])
				body.gun_power = float(spec.powers[index % spec.powers.size()])
				var angles: Array = spec.get("tank_angles", [0])
				body.tank_angle = float(angles[index % angles.size()])
				var polygon: Array = []
				for point in runtime.call("_tank_body_polygon", body):
					polygon.append(_classic_point(point))
				var velocity: Vector2 = body.launch_velocity(body.gun_power)
				tanks.append({"position": _classic_point(body.position), "origin": _classic_point(body.launch_origin()),
					"velocity": [float(velocity.x) / World.SCALE, -float(velocity.y) / World.SCALE], "fuel": body.fuel, "body": polygon})
			var blast_sizes: Array = []
			var inventory: RefCounted = runtime.call("_participant_inventory", 0)
			for weapon in ["Shell", "MIRV", "Missile", "Nuke"]:
				blast_sizes.append(float(inventory.weapon_by_name(weapon).blast) / World.SCALE)
			frames.append({"terrain": terrain, "tanks": tanks, "blast_sizes": blast_sizes,
				"projectile_gravity": runtime.get("_projectile_gravity") / World.SCALE,
				"tank_gravity": body_gravity(), "tank_move_speed": Runtime.TankState.TANK_MOVE_SPEED / World.SCALE})
		"winner":
			runtime.set("_phase", "winner")
			runtime.set("_winner_continue_delay", 2.0)
			for index in range(spec.scores.size()):
				runtime.get("_participants")[index].score = int(spec.scores[index])
			runtime.set("_score", int(spec.scores[0]))
			runtime.set("_enemy_score", int(spec.scores[1]))
			var winners: Array = []
			for card in runtime.call("_winner_card_snapshots"):
				winners.append(card.name)
			for tick in range(int(spec.ticks) + 1):
				for command in spec.commands:
					if int(command.tick) == tick:
						_inputs(int(command.player), command.buttons)
				if tick > 0:
					runtime.call("_update_modal_activation", float(spec.step))
				frames.append({"tick": tick, "exited": runtime.menu_requested, "winners": winners})
				if runtime.menu_requested:
					break
		"shop":
			runtime.set("_phase", "shop")
			runtime.call("_prepare_shop_pass")
			for index in range(spec.money.size()):
				runtime.call("_set_shop_credits", index, int(spec.money[index]))
			for tick in range(int(spec.ticks) + 1):
				for command in spec.commands:
					if int(command.tick) == tick:
						_inputs(int(command.player), command.buttons)
				if tick > 0:
					runtime.call("_simulate_match_step", float(spec.step), false)
				var next_round: bool = runtime.get("_phase") != "shop"
				if next_round:
					# The Python menu returns the phase request before GameFlow
					# constructs the next round; preserve the departing shop view.
					frames.append({"tick": tick, "next_round": true, "players": frames[-1].players.duplicate(true)})
					break
				var players: Array = []
				for index in range(roster.size()):
					var inventory: RefCounted = runtime.call("_participant_inventory", index)
					var ammo: Array = []
					for weapon in Weapons:
						ammo.append(inventory.stock_for(weapon))
					players.append({"money": runtime.call("_shop_credits", index), "fuel": runtime.call("_shop_fuel_reserve", index),
						"ammo": ammo, "selection": runtime.get("_shop_select_positions")[index],
						"delay": runtime.get("_shop_input_delays")[index], "done": runtime.get("_shop_done")[index]})
				frames.append({"tick": tick, "next_round": next_round, "players": players})
	_inputs(0, [])
	_inputs(1, [])
	runtime.free()
	return {"id": spec.id, "frames": frames}

func _classic_point(point: Vector2) -> Array:
	return [(float(point.x) - World.ORIGIN.x) / World.SCALE, (World.ORIGIN.y - float(point.y)) / World.SCALE]

func body_gravity() -> float:
	return Runtime.TankState.TANK_AIR_GRAVITY / World.SCALE

func _ai_snapshot(runtime: Object, index: int) -> Dictionary:
	var bot: RefCounted = runtime.get("_participants")[index].classic_ai
	var body: RefCounted = runtime.call("_participant_tank", index)
	body._read_motion_state()
	var commands: Array = []
	for action in range(Actions.size()):
		if bool(bot.commands.get(Actions[action], false)):
			commands.append(action)
	return {"target": bot.target, "target_angle": bot.target_angle, "target_power": bot.target_power,
		"target_x": bot.target_x, "target_y": bot.target_y, "shots_in_air": bot.shots_in_air,
		"last_x": bot.last_x, "last_y": bot.last_y, "last_shot": bot.last_shot,
		"ignore_shot": bot.ignore_shot, "on_target": bot.on_target, "aim_directly": bot.aim_directly,
		"commands": commands, "angle": body.gun_angle, "power": body.gun_power,
		"position_precise": [body._motion_x, body._motion_y]}
