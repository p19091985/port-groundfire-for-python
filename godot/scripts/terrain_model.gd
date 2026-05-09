extends RefCounted

const CLASSIC_SURFACE_TOP := Color(0.40, 0.40, 0.00)
const CLASSIC_SURFACE_BOTTOM := Color(0.80, 0.80, 0.00)
const CLASSIC_BASE := Color(0.80, 0.80, 0.00)
const MIN_CHUNK_THICKNESS := 0.5
const CLASSIC_MIN_LAND_HEIGHT := -7.0
const TANK_EDGE_MARGIN := 30.0

var _width := 1024.0
var _height := 768.0
var _step := 10.0
var _seed := 1337
var _slice_count := 96
var _samples := PackedFloat32Array()
var _chunks: Array = []
var _fall_pause := 0.10
var _fall_acceleration := 240.0
var _fall_terminal_speed := 420.0


func rebuild(width: float, height: float) -> void:
	_width = max(width, 64.0)
	_height = max(height, 64.0)
	_slice_count = max(24, int(_width / _step))
	_generate_original_style_samples()


func rebuild_with_seed(width: float, height: float, seed: int) -> void:
	_seed = seed
	rebuild(width, height)


func _generate_original_style_samples() -> void:
	_samples.clear()
	_chunks.clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = _seed
	var heights := PackedFloat32Array()
	var smoothed := PackedFloat32Array()
	for _index in range(_slice_count + 1):
		heights.append(-7.0)
		smoothed.append(0.0)

	for _pass in range(18):
		var center: int = rng.randi_range(-int((_slice_count + 1) / 2), (_slice_count + 1) * 2)
		var mound_height: float = float(rng.randi_range(0, 999)) / 300.0
		var mound_width: int = rng.randi_range(3, max(3, int((_slice_count + 1) / 2) + 2))
		var plateau: int = rng.randi_range(0, max(0, int(mound_width / 3)))
		for index in range(_slice_count + 1):
			var distance: int = abs(center - index)
			if distance < plateau:
				heights[index] += mound_height
			elif distance < mound_width:
				heights[index] += ((mound_width - (distance - plateau)) / float(mound_width)) * mound_height
			heights[index] = min(5.0, heights[index])

	for index in range(_slice_count + 1):
		if index >= 10 and index < _slice_count - 10:
			var total := 0.0
			for neighbor in range(index - 10, index + 11):
				total += heights[neighbor]
			smoothed[index] = total / 21.0
		else:
			smoothed[index] = heights[index]

	for index in range(_slice_count + 1):
		_samples.append(_world_height_to_screen(smoothed[index]))
	_rebuild_chunks_from_samples()


func _rebuild_chunks_from_samples() -> void:
	_chunks.clear()
	if _samples.size() < 2:
		return
	for index in range(_samples.size() - 1):
		var surface_left := _samples[index]
		var surface_right := _samples[index + 1]
		var cap_bottom_left: float = min(surface_left + 42.0, _height)
		var cap_bottom_right: float = min(surface_right + 42.0, _height)
		var slice_chunks: Array[Dictionary] = []
		slice_chunks.append(_make_chunk(surface_left, surface_right, cap_bottom_left, cap_bottom_right, true, CLASSIC_SURFACE_TOP, CLASSIC_SURFACE_BOTTOM))
		if cap_bottom_left < _height or cap_bottom_right < _height:
			slice_chunks.append(_make_chunk(cap_bottom_left, cap_bottom_right, _height, _height, false, CLASSIC_BASE, CLASSIC_BASE))
		_chunks.append(slice_chunks)


func _make_chunk(
	top_left: float,
	top_right: float,
	bottom_left: float,
	bottom_right: float,
	linked_to_next: bool,
	top_color: Color,
	bottom_color: Color
) -> Dictionary:
	return {
		"top_left": top_left,
		"top_right": top_right,
		"bottom_left": bottom_left,
		"bottom_right": bottom_right,
		"linked_to_next": linked_to_next,
		"falling": false,
		"wait": 0.0,
		"speed": 0.0,
		"top_left_color": top_color,
		"top_right_color": top_color,
		"bottom_left_color": bottom_color,
		"bottom_right_color": bottom_color,
		"top_color": top_color,
		"bottom_color": bottom_color,
		"fill_color": _average_colors([top_color, top_color, bottom_color, bottom_color]),
	}


func is_empty() -> bool:
	return _samples.is_empty()


func height_at(x: float) -> float:
	if _samples.is_empty() and _chunks.is_empty():
		return _base_height_at(x)
	if not _chunks.is_empty():
		return _chunk_height_at(x)
	var clamped_x: float = clamp(x, 0.0, _width)
	var sample_position: float = clamped_x / _step
	var left: int = clamp(int(floor(sample_position)), 0, _samples.size() - 1)
	var right: int = clamp(left + 1, 0, _samples.size() - 1)
	var mix_amount: float = sample_position - float(left)
	return lerpf(_samples[left], _samples[right], mix_amount)


func _chunk_height_at(x: float) -> float:
	var clamped_x: float = clamp(x, 0.0, _width - 0.01)
	var sample_position: float = clamped_x / _step
	var slice_index: int = clamp(int(floor(sample_position)), 0, _chunks.size() - 1)
	var slice_offset: float = sample_position - float(slice_index)
	var best_height := _height
	for chunk in _chunks[slice_index]:
		var top := lerpf(float(chunk["top_left"]), float(chunk["top_right"]), slice_offset)
		var bottom := lerpf(float(chunk["bottom_left"]), float(chunk["bottom_right"]), slice_offset)
		if bottom <= top + 0.5:
			continue
		best_height = min(best_height, top)
	return best_height


func tank_position(x: float) -> Vector2:
	return Vector2(clamp(x, TANK_EDGE_MARGIN, _width - TANK_EDGE_MARGIN), height_at(x))


func playable_bounds() -> Vector2:
	return Vector2(TANK_EDGE_MARGIN, _width - TANK_EDGE_MARGIN)


func slope_angle_at(x: float) -> float:
	var left := height_at(x - _step)
	var right := height_at(x + _step)
	return clamp(rad_to_deg(atan2(right - left, _step * 2.0)), -32.0, 32.0)


func ground_collision(start: Vector2, end: Vector2) -> Dictionary:
	if _chunks.is_empty():
		if _samples.is_empty():
			return {"hit": false, "position": Vector2.ZERO, "distance": INF}
		_rebuild_chunks_from_samples()
	var best := {"hit": false, "position": Vector2.ZERO, "distance": INF}
	var min_slice: int = clamp(int(floor((min(start.x, end.x) - 1.0) / _step)), 0, _chunks.size() - 1)
	var max_slice: int = clamp(int(ceil((max(start.x, end.x) + 1.0) / _step)), 0, _chunks.size() - 1)
	for slice_index in range(min_slice, max_slice + 1):
		var x1 := float(slice_index) * _step
		var x2 := float(slice_index + 1) * _step
		for chunk in _chunks[slice_index]:
			var polygon := PackedVector2Array([
				Vector2(x1, float(chunk["bottom_left"])),
				Vector2(x1, float(chunk["top_left"])),
				Vector2(x2, float(chunk["top_right"])),
				Vector2(x2, float(chunk["bottom_right"])),
			])
			var collision := _segment_polygon_collision(start, end, polygon)
			if bool(collision["hit"]) and float(collision["distance"]) < float(best["distance"]):
				best = collision
	return best


func apply_crater(center: Vector2, radius: float) -> void:
	if _samples.is_empty():
		rebuild(_width, _height)
	var safe_radius: float = max(radius, 6.0)
	if _chunks.is_empty():
		_rebuild_chunks_from_samples()
	var min_slice: int = clamp(int(floor((center.x - safe_radius) / _step)), 0, _chunks.size() - 1)
	var max_slice: int = clamp(int(ceil((center.x + safe_radius) / _step)), 0, _chunks.size() - 1)
	for slice_index in range(min_slice, max_slice + 1):
		_clip_slice(slice_index, center, safe_radius)
	_update_samples_from_chunks()


func drop_terrain(amount: float) -> void:
	if amount <= 0.0:
		return
	if _samples.is_empty():
		rebuild(_width, _height)
	if _chunks.is_empty():
		_rebuild_chunks_from_samples()
	var floor_y := _world_height_to_screen(CLASSIC_MIN_LAND_HEIGHT)
	for slice_index in range(_chunks.size()):
		var slice_chunks: Array = _chunks[slice_index]
		for chunk_index in range(slice_chunks.size()):
			var chunk: Dictionary = slice_chunks[chunk_index]
			chunk["top_left"] = min(floor_y, float(chunk["top_left"]) + amount)
			chunk["top_right"] = min(floor_y, float(chunk["top_right"]) + amount)
			if float(chunk["top_left"]) < floor_y:
				chunk["bottom_left"] = min(_height, float(chunk["bottom_left"]) + amount)
				chunk["bottom_right"] = min(_height, float(chunk["bottom_right"]) + amount)
			slice_chunks[chunk_index] = chunk
		_chunks[slice_index] = slice_chunks
	_update_samples_from_chunks()


func update(delta: float) -> void:
	if _chunks.is_empty():
		return
	for slice_index in range(_chunks.size()):
		var slice_chunks: Array = _chunks[slice_index]
		if slice_chunks.is_empty():
			continue
		_sort_slice(slice_chunks)
		var chunk_index := 0
		while chunk_index < slice_chunks.size():
			var superblock_end := _superblock_end(slice_chunks, chunk_index)
			var leader: Dictionary = slice_chunks[chunk_index]
			if bool(leader.get("falling", false)):
				if float(leader.get("wait", 0.0)) > 0.0:
					_set_superblock_motion(
						slice_chunks,
						chunk_index,
						superblock_end,
						true,
						0.0,
						max(0.0, float(leader.get("wait", 0.0)) - delta)
					)
				else:
					var speed: float = min(_fall_terminal_speed, float(leader.get("speed", 0.0)) + _fall_acceleration * delta)
					var fall_amount := speed * delta
					var landing_gap := _superblock_landing_gap(slice_chunks, chunk_index, superblock_end)
					if landing_gap >= 0.0:
						fall_amount = min(fall_amount, landing_gap)
					_move_superblock(slice_chunks, chunk_index, superblock_end, fall_amount)
					if landing_gap >= 0.0 and fall_amount >= landing_gap - 0.01:
						_set_superblock_motion(slice_chunks, chunk_index, superblock_end, false, 0.0, 0.0)
					else:
						_set_superblock_motion(slice_chunks, chunk_index, superblock_end, true, speed, 0.0)
			chunk_index = superblock_end + 1
		_sort_slice(slice_chunks)
		_merge_resting_superblocks(slice_chunks)
	_update_samples_from_chunks()


func chunk_polygons() -> Array[Dictionary]:
	var polygons: Array[Dictionary] = []
	for slice_index in range(_chunks.size()):
		var x1 := float(slice_index) * _step
		var x2 := float(slice_index + 1) * _step
		for chunk in _chunks[slice_index]:
			if float(chunk["bottom_left"]) <= float(chunk["top_left"]) + 0.5 and float(chunk["bottom_right"]) <= float(chunk["top_right"]) + 0.5:
				continue
			polygons.append({
				"points": PackedVector2Array([
					Vector2(x1, float(chunk["bottom_left"])),
					Vector2(x1, float(chunk["top_left"])),
					Vector2(x2, float(chunk["top_right"])),
					Vector2(x2, float(chunk["bottom_right"])),
				]),
				"top_color": chunk.get("top_color", Color("#6fbf73")),
				"bottom_color": chunk.get("bottom_color", Color("#56532c")),
				"fill_color": chunk.get("fill_color", chunk.get("bottom_color", Color("#56532c"))),
				"falling": bool(chunk.get("falling", false)),
			})
	return polygons


func polygon_points() -> PackedVector2Array:
	var points := PackedVector2Array()
	points.append(Vector2(0.0, _height))
	if not _chunks.is_empty():
		_update_samples_from_chunks()
	for index in range(_samples.size()):
		points.append(Vector2(float(index) * _step, _samples[index]))
	points.append(Vector2(_width, _height))
	return points


func _clip_slice(slice_index: int, center: Vector2, radius: float) -> void:
	var x1 := float(slice_index) * _step
	var x2 := float(slice_index + 1) * _step
	var left_interval := _blast_interval_at_x(center, radius, x1)
	var right_interval := _blast_interval_at_x(center, radius, x2)
	if left_interval.x == INF and right_interval.x == INF:
		return
	var replacement: Array[Dictionary] = []
	for chunk in _chunks[slice_index]:
		var left_parts := _subtract_interval(float(chunk["top_left"]), float(chunk["bottom_left"]), left_interval)
		var right_parts := _subtract_interval(float(chunk["top_right"]), float(chunk["bottom_right"]), right_interval)
		var part_count: int = max(left_parts.size(), right_parts.size())
		for part_index in range(part_count):
			if part_index >= left_parts.size() or part_index >= right_parts.size():
				continue
			var left_part: Vector2 = left_parts[part_index]
			var right_part: Vector2 = right_parts[part_index]
			if left_part.y <= left_part.x + 0.5 and right_part.y <= right_part.x + 0.5:
				continue
			var new_chunk: Dictionary = _chunk_from_clipped_parts(chunk, left_part, right_part)
			new_chunk["linked_to_next"] = false
			if part_index == 0 and (left_parts.size() > 1 or right_parts.size() > 1):
				new_chunk["falling"] = true
				new_chunk["wait"] = _fall_pause
				new_chunk["speed"] = 0.0
			replacement.append(new_chunk)
	_chunks[slice_index] = replacement
	_sort_slice(_chunks[slice_index])
	_merge_resting_superblocks(_chunks[slice_index])


func _blast_interval_at_x(center: Vector2, radius: float, x: float) -> Vector2:
	var distance: float = abs(x - center.x)
	if distance > radius:
		return Vector2(INF, -INF)
	var root := sqrt(max(0.0, radius * radius - distance * distance))
	return Vector2(center.y - root, center.y + root)


func _segment_polygon_collision(start: Vector2, end: Vector2, polygon: PackedVector2Array) -> Dictionary:
	var best: Dictionary = {"hit": false, "position": Vector2.ZERO, "distance": INF}
	if Geometry2D.is_point_in_polygon(start, polygon):
		return {"hit": true, "position": start, "distance": 0.0}
	for index in range(polygon.size()):
		var edge_start: Vector2 = polygon[index]
		var edge_end: Vector2 = polygon[(index + 1) % polygon.size()]
		var collision: Dictionary = _segment_intersection(start, end, edge_start, edge_end)
		if bool(collision["hit"]) and float(collision["distance"]) < float(best["distance"]):
			best = collision
	return best


func _segment_intersection(a1: Vector2, a2: Vector2, b1: Vector2, b2: Vector2) -> Dictionary:
	var segment_a: Vector2 = a2 - a1
	var segment_b: Vector2 = b2 - b1
	var denominator: float = _cross(segment_a, segment_b)
	if abs(denominator) <= 0.00001:
		return {"hit": false, "position": Vector2.ZERO, "distance": INF}
	var offset: Vector2 = b1 - a1
	var t: float = _cross(offset, segment_b) / denominator
	var u: float = _cross(offset, segment_a) / denominator
	if t < -0.0001 or t > 1.0001 or u < -0.0001 or u > 1.0001:
		return {"hit": false, "position": Vector2.ZERO, "distance": INF}
	var position: Vector2 = a1 + segment_a * clamp(t, 0.0, 1.0)
	return {"hit": true, "position": position, "distance": a1.distance_to(position)}


func _cross(a: Vector2, b: Vector2) -> float:
	return a.x * b.y - a.y * b.x


func _subtract_interval(top: float, bottom: float, cut: Vector2) -> Array[Vector2]:
	if bottom <= top + MIN_CHUNK_THICKNESS:
		return []
	if cut.x == INF or cut.y <= top or cut.x >= bottom:
		return [Vector2(top, bottom)]
	var parts: Array[Vector2] = []
	var cut_top: float = clamp(cut.x, top, bottom)
	var cut_bottom: float = clamp(cut.y, top, bottom)
	if cut_top > top + MIN_CHUNK_THICKNESS:
		parts.append(Vector2(top, cut_top))
	if bottom > cut_bottom + MIN_CHUNK_THICKNESS:
		parts.append(Vector2(cut_bottom, bottom))
	return parts


func _chunk_from_clipped_parts(chunk: Dictionary, left_part: Vector2, right_part: Vector2) -> Dictionary:
	var new_chunk: Dictionary = chunk.duplicate()
	new_chunk["top_left"] = left_part.x
	new_chunk["bottom_left"] = left_part.y
	new_chunk["top_right"] = right_part.x
	new_chunk["bottom_right"] = right_part.y
	new_chunk["top_left_color"] = _vertical_color_at(chunk, true, left_part.x)
	new_chunk["bottom_left_color"] = _vertical_color_at(chunk, true, left_part.y)
	new_chunk["top_right_color"] = _vertical_color_at(chunk, false, right_part.x)
	new_chunk["bottom_right_color"] = _vertical_color_at(chunk, false, right_part.y)
	_refresh_chunk_colors(new_chunk)
	return new_chunk


func _vertical_color_at(chunk: Dictionary, left_side: bool, height: float) -> Color:
	var top_key := "top_left" if left_side else "top_right"
	var bottom_key := "bottom_left" if left_side else "bottom_right"
	var top_color_key := "top_left_color" if left_side else "top_right_color"
	var bottom_color_key := "bottom_left_color" if left_side else "bottom_right_color"
	var top_height := float(chunk.get(top_key, 0.0))
	var bottom_height := float(chunk.get(bottom_key, top_height))
	var top_color: Color = chunk.get(top_color_key, chunk.get("top_color", CLASSIC_SURFACE_TOP))
	var bottom_color: Color = chunk.get(bottom_color_key, chunk.get("bottom_color", CLASSIC_SURFACE_BOTTOM))
	if abs(bottom_height - top_height) <= 0.001:
		return top_color
	var ratio: float = clamp((height - top_height) / (bottom_height - top_height), 0.0, 1.0)
	return top_color.lerp(bottom_color, ratio)


func _refresh_chunk_colors(chunk: Dictionary) -> void:
	var top_left: Color = chunk.get("top_left_color", chunk.get("top_color", CLASSIC_SURFACE_TOP))
	var top_right: Color = chunk.get("top_right_color", chunk.get("top_color", CLASSIC_SURFACE_TOP))
	var bottom_left: Color = chunk.get("bottom_left_color", chunk.get("bottom_color", CLASSIC_SURFACE_BOTTOM))
	var bottom_right: Color = chunk.get("bottom_right_color", chunk.get("bottom_color", CLASSIC_SURFACE_BOTTOM))
	chunk["top_color"] = top_left.lerp(top_right, 0.5)
	chunk["bottom_color"] = bottom_left.lerp(bottom_right, 0.5)
	chunk["fill_color"] = _average_colors([top_left, top_right, bottom_left, bottom_right])


func _average_colors(colors: Array) -> Color:
	if colors.is_empty():
		return Color.WHITE
	var red := 0.0
	var green := 0.0
	var blue := 0.0
	var alpha := 0.0
	for raw_color in colors:
		var color: Color = raw_color
		red += color.r
		green += color.g
		blue += color.b
		alpha += color.a
	var count := float(colors.size())
	return Color(red / count, green / count, blue / count, alpha / count)


func _move_chunk(chunk: Dictionary, amount: float) -> void:
	chunk["top_left"] = float(chunk["top_left"]) + amount
	chunk["top_right"] = float(chunk["top_right"]) + amount
	chunk["bottom_left"] = min(_height, float(chunk["bottom_left"]) + amount)
	chunk["bottom_right"] = min(_height, float(chunk["bottom_right"]) + amount)


func _move_superblock(slice_chunks: Array, start_index: int, end_index: int, amount: float) -> void:
	for chunk_index in range(start_index, end_index + 1):
		var chunk: Dictionary = slice_chunks[chunk_index]
		_move_chunk(chunk, amount)
		slice_chunks[chunk_index] = chunk


func _set_superblock_motion(slice_chunks: Array, start_index: int, end_index: int, falling: bool, speed: float, wait: float) -> void:
	for chunk_index in range(start_index, end_index + 1):
		var chunk: Dictionary = slice_chunks[chunk_index]
		chunk["falling"] = falling
		chunk["speed"] = speed
		chunk["wait"] = wait
		slice_chunks[chunk_index] = chunk


func _superblock_end(slice_chunks: Array, start_index: int) -> int:
	var end_index := start_index
	while end_index < slice_chunks.size() - 1 and bool(slice_chunks[end_index].get("linked_to_next", false)):
		end_index += 1
	return end_index


func _superblock_landing_gap(slice_chunks: Array, start_index: int, end_index: int) -> float:
	var bottom_chunk: Dictionary = slice_chunks[end_index]
	var nearest_gap := INF
	var next_index := end_index + 1
	if next_index < slice_chunks.size():
		var next_chunk: Dictionary = slice_chunks[next_index]
		var left_gap: float = float(next_chunk["top_left"]) - float(bottom_chunk["bottom_left"])
		var right_gap: float = float(next_chunk["top_right"]) - float(bottom_chunk["bottom_right"])
		nearest_gap = min(nearest_gap, min(left_gap, right_gap))
	var floor_gap: float = min(_height - float(bottom_chunk["bottom_left"]), _height - float(bottom_chunk["bottom_right"]))
	nearest_gap = min(nearest_gap, floor_gap)
	if nearest_gap == INF:
		return -1.0
	return max(0.0, nearest_gap)


func _landing_gap(slice_chunks: Array, chunk_index: int) -> float:
	var chunk: Dictionary = slice_chunks[chunk_index]
	var nearest_gap := INF
	for other_index in range(slice_chunks.size()):
		if other_index == chunk_index:
			continue
		var other: Dictionary = slice_chunks[other_index]
		var left_gap: float = float(other["top_left"]) - float(chunk["bottom_left"])
		var right_gap: float = float(other["top_right"]) - float(chunk["bottom_right"])
		var gap: float = min(left_gap, right_gap)
		if gap >= 0.0:
			nearest_gap = min(nearest_gap, gap)
	var floor_gap: float = min(_height - float(chunk["bottom_left"]), _height - float(chunk["bottom_right"]))
	nearest_gap = min(nearest_gap, floor_gap)
	if nearest_gap == INF:
		return -1.0
	return max(0.0, nearest_gap)


func _merge_resting_superblocks(slice_chunks: Array) -> void:
	var chunk_index := 0
	while chunk_index < slice_chunks.size() - 1:
		var superblock_end := _superblock_end(slice_chunks, chunk_index)
		var next_index := superblock_end + 1
		if next_index >= slice_chunks.size():
			break
		var upper_chunk: Dictionary = slice_chunks[superblock_end]
		var lower_chunk: Dictionary = slice_chunks[next_index]
		if bool(upper_chunk.get("falling", false)) or bool(lower_chunk.get("falling", false)):
			chunk_index = next_index
			continue
		var left_gap: float = float(lower_chunk["top_left"]) - float(upper_chunk["bottom_left"])
		var right_gap: float = float(lower_chunk["top_right"]) - float(upper_chunk["bottom_right"])
		if abs(left_gap) > 0.75 or abs(right_gap) > 0.75:
			chunk_index = next_index
			continue
		if _merge_colors_compatible(upper_chunk, lower_chunk):
			upper_chunk["bottom_left"] = lower_chunk["bottom_left"]
			upper_chunk["bottom_right"] = lower_chunk["bottom_right"]
			upper_chunk["bottom_left_color"] = lower_chunk.get("bottom_left_color", lower_chunk.get("bottom_color", CLASSIC_BASE))
			upper_chunk["bottom_right_color"] = lower_chunk.get("bottom_right_color", lower_chunk.get("bottom_color", CLASSIC_BASE))
			upper_chunk["linked_to_next"] = bool(lower_chunk.get("linked_to_next", false))
			_refresh_chunk_colors(upper_chunk)
			slice_chunks[superblock_end] = upper_chunk
			slice_chunks.remove_at(next_index)
			continue
		upper_chunk["linked_to_next"] = true
		slice_chunks[superblock_end] = upper_chunk
		chunk_index = next_index


func _merge_colors_compatible(upper_chunk: Dictionary, lower_chunk: Dictionary) -> bool:
	var upper_left: Color = upper_chunk.get("bottom_left_color", upper_chunk.get("bottom_color", CLASSIC_BASE))
	var upper_right: Color = upper_chunk.get("bottom_right_color", upper_chunk.get("bottom_color", CLASSIC_BASE))
	var lower_left: Color = lower_chunk.get("top_left_color", lower_chunk.get("top_color", CLASSIC_BASE))
	var lower_right: Color = lower_chunk.get("top_right_color", lower_chunk.get("top_color", CLASSIC_BASE))
	return _color_distance(upper_left, lower_left) < 0.08 and _color_distance(upper_right, lower_right) < 0.08


func _color_distance(a: Color, b: Color) -> float:
	return abs(a.r - b.r) + abs(a.g - b.g) + abs(a.b - b.b) + abs(a.a - b.a)


func _sort_slice(slice_chunks: Array) -> void:
	slice_chunks.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		var a_top: float = (float(a["top_left"]) + float(a["top_right"])) * 0.5
		var b_top: float = (float(b["top_left"]) + float(b["top_right"])) * 0.5
		return a_top < b_top
	)


func _update_samples_from_chunks() -> void:
	if _chunks.is_empty():
		return
	_samples.clear()
	for sample_index in range(_chunks.size() + 1):
		var height := _height
		if sample_index > 0:
			for chunk in _chunks[sample_index - 1]:
				height = min(height, float(chunk["top_right"]))
		if sample_index < _chunks.size():
			for chunk in _chunks[sample_index]:
				height = min(height, float(chunk["top_left"]))
		_samples.append(height)


func _base_height_at(x: float) -> float:
	return _height - 135.0 - sin(x * 0.012) * 32.0 - sin(x * 0.031) * 15.0


func _world_height_to_screen(world_height: float) -> float:
	var normalized := inverse_lerp(-8.0, 5.0, world_height)
	return lerpf(_height - 72.0, _height * 0.38, normalized)
