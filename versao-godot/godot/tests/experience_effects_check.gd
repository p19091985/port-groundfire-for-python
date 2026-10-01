extends SceneTree
## GPU regression: entity/UV array checks alone cannot detect invisible textures.
## Run with a real renderer, not --headless (which uses the dummy renderer).

const Match := preload("res://scripts/local_match.gd")
var failures: Array[String] = []
var output := ""

class EffectCanvas extends "res://scripts/local_match.gd":
	func _ready() -> void:
		pass

	func _process(_delta: float) -> void:
		pass

	func _draw() -> void:
		draw_rect(Rect2(0, 0, 640, 256), Color.BLACK)
		_draw_trail_segment({"position":Vector2(64,128), "fade":0.8, "angle":45.0})
		_draw_smoke_particle({"position":Vector2(192,128), "size":0.5, "fade":0.7})
		_draw_blast_explosion({"position":Vector2(320,128), "radius":52.0, "fade_away":0.8})
		_draw_smoke_particle({"position":Vector2(448,128), "size":0.5, "fade":0.7, "texture_id":TankState.BOOST_SMOKE_TEXTURE_ID})
		draw_polygon(_mouse_cursor_draw_points(Vector2(560,112)), PackedColorArray([Color.WHITE]), _mouse_cursor_draw_uvs(), CURSOR_TEXTURE)

func _init() -> void:
	call_deferred("_run")

func _check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func _capture(name: String) -> Image:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var picture := root.get_texture().get_image()
	if not output.is_empty() and picture != null:
		picture.save_png(output.path_join(name + ".png"))
	return picture

func _run() -> void:
	output = OS.get_environment("EXPERIENCE_EFFECTS_DIR")
	if not output.is_empty():
		DirAccess.make_dir_recursive_absolute(output)
	root.size = Vector2i(640,256)
	root.content_scale_size = root.size
	var canvas := EffectCanvas.new()
	root.add_child(canvas)
	var picture := await _capture("effects")
	if picture == null or picture.is_empty():
		push_error("Effects check requires a real rendering driver")
		quit(1)
		return
	for index in range(5):
		var visible_pixels := 0
		for y in range(80,176):
			for x in range(index*128+16,index*128+112):
				var pixel := picture.get_pixel(x,y)
				if maxf(pixel.r,maxf(pixel.g,pixel.b)) > 0.05:
					visible_pixels += 1
		var effect: String = ["trail", "smoke", "blast", "exhaust", "cursor"][index]
		print(effect, " visible pixels: ", visible_pixels)
		_check(visible_pixels > 100, effect + " texture is missing or collapsed")
	canvas.queue_free()
	await process_frame
	root.size = Vector2i(1024,768)
	root.content_scale_size = root.size
	var game := Match.new()
	game.setup({"roster":[{"name":"Player","kind":"human","controller":0}, {"name":"Enemy","kind":"human","controller":1}]})
	game.set("_terrain_seed",1401)
	game.size = Vector2(root.size)
	root.add_child(game)
	game.set_process(false)
	for tick in range(242):
		game.call("_simulate_match_step",1.0/60.0,false)
	game.call("_fire_participant",0)
	for tick in range(30):
		game.call("_simulate_match_step",1.0/60.0,false)
	game.call("_update_camera",0.0)
	game.queue_redraw()
	var shot := await _capture("shot-with-trail")
	var segments: Array = game.get("_trail_segments").duplicate(true)
	_check(not segments.is_empty(), "A real Shell shot must emit trail segments")
	game.get("_trail_segments").clear()
	game.queue_redraw()
	var bare := await _capture("shot-without-trail")
	var changed := 0
	for y in range(shot.get_height()):
		for x in range(shot.get_width()):
			var a := shot.get_pixel(x,y)
			var b := bare.get_pixel(x,y)
			if absf(a.r-b.r)+absf(a.g-b.g)+absf(a.b-b.b) > 0.08:
				changed += 1
	print("Real shot trail pixels: ",changed)
	_check(changed > 100, "Shell trail must be visible in the rendered arena")
	game.get("_trail_segments").assign(segments)
	game.call("_update_trail_segments",5.0)
	_check(game.get("_trail_segments").is_empty(), "Trail must fade after the projectile passes")
	game.queue_free()
	await process_frame
	if failures.is_empty():
		print("Rendered effects checks passed")
	quit(0 if failures.is_empty() else 1)
