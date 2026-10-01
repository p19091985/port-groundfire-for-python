extends SceneTree
const Match := preload("res://scripts/local_match.gd")
const World := preload("res://scripts/classic_world.gd")

func _init() -> void:
	var reference = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("EXPERIENCE_SMOKE_REFERENCE")))
	var game := Match.new()
	for case in reference:
		game.get("_smoke_particles").clear()
		game.get("_smoke_particles").append({"position":World.from_classic(2.0,1.0),
			"velocity":Vector2(0.2,-0.5)*World.SCALE,"size":0.25,"rotation":0.0,"fade":0.7,
			"rotation_rate":case.rotation_rate,"growth_rate":case.growth_rate,"fade_rate":case.fade_rate})
		for frame in case.frames:
			if frame.tick > 0:
				game.call("_update_smoke_particles",1.0/60.0)
			var particles: Array = game.get("_smoke_particles")
			if particles.is_empty() == bool(frame.alive):
				_fail(game,"Smoke lifetime differs at tick %s" % frame.tick)
				return
			if not frame.alive:
				continue
			var points: PackedVector2Array = game.call("_smoke_particle_draw_points",particles[0])
			var edge := points[1]-points[0]
			if absf(edge.length()/World.SCALE-float(frame.width)) > 0.00001:
				_fail(game,"Smoke width differs at tick %s: %s vs Python %s" % [frame.tick,edge.length()/World.SCALE,frame.width])
				return
			# Pygame positive angles turn counterclockwise; screen-space Y points down.
			if absf(edge.angle()+deg_to_rad(float(frame.rotation))) > 0.00001:
				_fail(game,"Smoke rotation differs at tick %s" % frame.tick)
				return
			var center := World.to_classic((points[0]+points[2])*0.5)
			if center.distance_to(Vector2(frame.position[0],frame.position[1])) > 0.0001:
				_fail(game,"Smoke position differs at tick %s" % frame.tick)
				return
	game.free()
	print("Smoke geometry comparison passed")
	quit(0)

func _fail(game: Control, message: String) -> void:
	game.free()
	push_error(message)
	quit(1)
