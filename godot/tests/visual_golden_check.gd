extends SceneTree

const MainScene := preload("res://scenes/main.tscn")
const LocalMatchScene := preload("res://scenes/local_match.tscn")
const ServerBrowserScene := preload("res://scenes/server_browser.tscn")

const CAPTURE_SIZE := Vector2i(1024, 768)
const GOLDEN_DIR := "res://../docs/references/godot_visual"
const ACTUAL_DIR := "res://../.tmp/godot_visual_actual"
const UPDATE_ENV := "GODOT_VISUAL_UPDATE"
const SAMPLE_STEP := 8
const AVG_DELTA_TOLERANCE := 1.0
const CHANGED_RATIO_TOLERANCE := 0.02

var _failed := false


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	_reset_user_state()
	root.size = CAPTURE_SIZE
	var update_goldens := OS.get_environment(UPDATE_ENV) == "1"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(GOLDEN_DIR))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(ACTUAL_DIR))

	for case_name in ["main_menu", "options", "server_browser", "local_match"]:
		var image: Image = await _capture_case(case_name)
		if _failed:
			quit(4)
			return
		_assert_nonblank(image, case_name)
		var actual_path := ProjectSettings.globalize_path("%s/%s.png" % [ACTUAL_DIR, case_name])
		var golden_path := ProjectSettings.globalize_path("%s/%s.png" % [GOLDEN_DIR, case_name])
		assert(image.save_png(actual_path) == OK)
		if update_goldens:
			assert(image.save_png(golden_path) == OK)
		elif not FileAccess.file_exists(golden_path):
			push_error("%s golden is missing. Run scripts/validate_godot_visuals.sh --update-goldens first." % case_name)
			quit(3)
			return
		else:
			var golden := Image.load_from_file(golden_path)
			assert(golden != null)
			_assert_image_close(image, golden, case_name)

	quit(0)


func _capture_case(case_name: String) -> Image:
	var node: Node
	match case_name:
		"main_menu", "options":
			node = MainScene.instantiate()
		"server_browser":
			node = ServerBrowserScene.instantiate()
		"local_match":
			node = LocalMatchScene.instantiate()
		_:
			push_error("Unknown visual case: %s" % case_name)
			quit(2)
			return Image.create_empty(1, 1, false, Image.FORMAT_RGBA8)
	root.add_child(node)
	await process_frame
	await process_frame
	if case_name == "options":
		node.call("_show_options")
		await process_frame
		await process_frame
	var viewport_texture := root.get_texture()
	if viewport_texture == null:
		_failed = true
		push_error("%s capture failed: viewport texture is unavailable in this renderer." % case_name)
		node.queue_free()
		return Image.create_empty(1, 1, false, Image.FORMAT_RGBA8)
	var image := viewport_texture.get_image()
	if image == null or image.get_width() <= 1 or image.get_height() <= 1:
		_failed = true
		push_error("%s capture failed: viewport image is unavailable in this renderer." % case_name)
		node.queue_free()
		return Image.create_empty(1, 1, false, Image.FORMAT_RGBA8)
	image.convert(Image.FORMAT_RGBA8)
	node.queue_free()
	await process_frame
	return image


func _assert_nonblank(image: Image, label: String) -> void:
	var first := image.get_pixel(0, 0)
	var different_samples := 0
	for y in range(0, image.get_height(), 64):
		for x in range(0, image.get_width(), 64):
			if _pixel_delta(first, image.get_pixel(x, y)) > 1.0:
				different_samples += 1
	assert(different_samples > 6, "%s capture appears blank" % label)


func _assert_image_close(actual: Image, golden: Image, label: String) -> void:
	assert(actual.get_size() == golden.get_size(), "%s golden size changed" % label)
	var total_delta := 0.0
	var changed := 0
	var samples := 0
	for y in range(0, actual.get_height(), SAMPLE_STEP):
		for x in range(0, actual.get_width(), SAMPLE_STEP):
			var delta := _pixel_delta(actual.get_pixel(x, y), golden.get_pixel(x, y))
			total_delta += delta
			if delta > 12.0:
				changed += 1
			samples += 1
	var average_delta: float = total_delta / max(1.0, float(samples))
	var changed_ratio: float = float(changed) / max(1.0, float(samples))
	assert(average_delta <= AVG_DELTA_TOLERANCE, "%s average pixel delta %.3f" % [label, average_delta])
	assert(changed_ratio <= CHANGED_RATIO_TOLERANCE, "%s changed pixel ratio %.4f" % [label, changed_ratio])


func _pixel_delta(a: Color, b: Color) -> float:
	return (
		abs(a.r - b.r) +
		abs(a.g - b.g) +
		abs(a.b - b.b) +
		abs(a.a - b.a)
	) * 63.75


func _reset_user_state() -> void:
	for path in [
		"user://groundfire_options.cfg",
		"user://groundfire_controls.cfg",
		"user://server_browser_store.json",
	]:
		var absolute_path := ProjectSettings.globalize_path(path)
		if FileAccess.file_exists(absolute_path):
			DirAccess.remove_absolute(absolute_path)
