extends SceneTree

const TerrainModel := preload("res://scripts/terrain_model.gd")


func _init() -> void:
	var terrain := TerrainModel.new()
	terrain.rebuild_with_seed(1024.0, 768.0, 1401)

	var x := 512.0
	var surface_y: float = terrain.height_at(x)
	var vertical_hit: Dictionary = terrain.ground_collision(Vector2(x, 0.0), Vector2(x, 768.0))
	assert(bool(vertical_hit["hit"]))
	assert(Vector2(vertical_hit["position"]).distance_to(Vector2(x, surface_y)) < 4.0)

	var above_ground: Dictionary = terrain.ground_collision(Vector2(80.0, 20.0), Vector2(220.0, 20.0))
	assert(not bool(above_ground["hit"]))

	var diagonal_hit: Dictionary = terrain.ground_collision(Vector2(96.0, 0.0), Vector2(928.0, 768.0))
	assert(bool(diagonal_hit["hit"]))
	var diagonal_position := Vector2(diagonal_hit["position"])
	assert(diagonal_position.x >= 96.0 and diagonal_position.x <= 928.0)
	assert(diagonal_position.y >= 0.0 and diagonal_position.y <= 768.0)

	var edge_terrain := TerrainModel.new()
	edge_terrain.set("_step", 10.0)
	edge_terrain.set("_height", 100.0)
	var edge_chunk: Dictionary = edge_terrain.call(
		"_make_chunk",
		40.0,
		40.0,
		90.0,
		90.0,
		false,
		Color.WHITE,
		Color.BLACK
	)
	edge_terrain.set("_chunks", [[edge_chunk]])
	var collinear_edge_hit: Dictionary = edge_terrain.ground_collision(Vector2(-5.0, 40.0), Vector2(15.0, 40.0))
	assert(bool(collinear_edge_hit["hit"]))
	assert(Vector2(collinear_edge_hit["position"]).distance_to(Vector2(0.0, 40.0)) < 0.01)
	var parallel_clear_hit: Dictionary = edge_terrain.ground_collision(Vector2(-5.0, 35.0), Vector2(15.0, 35.0))
	assert(not bool(parallel_clear_hit["hit"]))
	var zero_length_edge_hit: Dictionary = edge_terrain.ground_collision(Vector2(0.0, 40.0), Vector2(0.0, 40.0))
	assert(bool(zero_length_edge_hit["hit"]))
	assert(Vector2(zero_length_edge_hit["position"]).distance_to(Vector2(0.0, 40.0)) < 0.01)
	var zero_length_clear_hit: Dictionary = edge_terrain.ground_collision(Vector2(0.0, 35.0), Vector2(0.0, 35.0))
	assert(not bool(zero_length_clear_hit["hit"]))
	quit(0)
