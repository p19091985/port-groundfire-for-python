extends RefCounted

const CLASSIC_SURFACE_TOP := Color(0.40, 0.40, 0.00)
const CLASSIC_SURFACE_BOTTOM := Color(0.80, 0.80, 0.00)
const CLASSIC_BASE := Color(0.80, 0.80, 0.00)
const CLASSIC_COLOUR_EQUAL_EPSILON := 0.0001
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


func move_to_ground(x: float, y: float) -> float:
	if _samples.is_empty() and _chunks.is_empty():
		return _base_height_at(x)
	if _chunks.is_empty():
		return height_at(x)
	if x < 0.0 or x > _width:
		return _world_height_to_screen(CLASSIC_MIN_LAND_HEIGHT)
	var clamped_x: float = clamp(x, 0.0, _width - 0.01)
	var sample_position: float = clamped_x / _step
	var slice_index: int = clamp(int(floor(sample_position)), 0, _chunks.size() - 1)
	var slice_offset: float = sample_position - float(slice_index)
	var height := _world_height_to_screen(CLASSIC_MIN_LAND_HEIGHT)
	var old_height := INF
	for chunk in _chunks[slice_index]:
		var state := _chunk_state_at_offset(chunk, slice_offset, y)
		if state == 2:
			continue
		var top := _chunk_top_at_offset(chunk, slice_offset)
		if state == 0:
			return top
		if old_height == INF or (top - y) < (old_height - y):
			old_height = top
			height = top
		else:
			height = old_height
	return height


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


func _chunk_state_at_offset(chunk: Dictionary, slice_offset: float, y: float) -> int:
	var top := _chunk_top_at_offset(chunk, slice_offset)
	var bottom := _chunk_bottom_at_offset(chunk, slice_offset)
	if y < top:
		return 1
	if y > bottom:
		return 2
	return 0


func _chunk_top_at_offset(chunk: Dictionary, slice_offset: float) -> float:
	return lerpf(float(chunk["top_left"]), float(chunk["top_right"]), slice_offset)


func _chunk_bottom_at_offset(chunk: Dictionary, slice_offset: float) -> float:
	return lerpf(float(chunk["bottom_left"]), float(chunk["bottom_right"]), slice_offset)


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
					# Python Landscape.update only subtracts wait on this tick; speed and
					# movement are preserved for the next frame even if wait crosses zero.
					_set_superblock_motion(
						slice_chunks,
						chunk_index,
						superblock_end,
						true,
						float(leader.get("speed", 0.0)),
						float(leader.get("wait", 0.0)) - delta
					)
				else:
					var speed: float = min(_fall_terminal_speed, float(leader.get("speed", 0.0)))
					var next_speed: float = min(_fall_terminal_speed, speed + _fall_acceleration * delta)
					var fall_amount := speed * delta
					var landing_gaps := _superblock_landing_gaps(slice_chunks, chunk_index, superblock_end)
					var left_fall_amount := fall_amount
					var right_fall_amount := fall_amount
					var left_at_rest := false
					var right_at_rest := false
					if landing_gaps.x >= 0.0 and fall_amount >= landing_gaps.x:
						left_fall_amount = landing_gaps.x
						left_at_rest = true
					if landing_gaps.y >= 0.0 and fall_amount >= landing_gaps.y:
						right_fall_amount = landing_gaps.y
						right_at_rest = true
					_move_superblock_edges(slice_chunks, chunk_index, superblock_end, left_fall_amount, right_fall_amount)
					if left_at_rest and right_at_rest:
						superblock_end = _settle_landed_superblock(slice_chunks, chunk_index, superblock_end)
					else:
						_set_superblock_motion(slice_chunks, chunk_index, superblock_end, true, next_speed, 0.0)
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
	var source_chunks: Array = _chunks[slice_index].duplicate(true)
	var replacement: Array[Dictionary] = []
	var skipped_superblock_end := -1
	for source_index in range(source_chunks.size()):
		var chunk: Dictionary = source_chunks[source_index]
		if source_index <= skipped_superblock_end:
			replacement.append(chunk)
			continue
		if _should_skip_linked_superblock_clip(chunk, center, radius, x1, x2):
			skipped_superblock_end = _superblock_end(source_chunks, source_index)
			replacement.append(chunk)
			continue
		var superblock_start := _superblock_start(source_chunks, source_index)
		var superblock_motion := _superblock_motion_for_index(source_chunks, source_index)
		var chunk_left_interval := _clamped_blast_interval_for_chunk_side(chunk, true, left_interval)
		var chunk_right_interval := _clamped_blast_interval_for_chunk_side(chunk, false, right_interval)
		var left_parts := _subtract_interval(float(chunk["top_left"]), float(chunk["bottom_left"]), chunk_left_interval)
		var right_parts := _subtract_interval(float(chunk["top_right"]), float(chunk["bottom_right"]), chunk_right_interval)
		var state1 := _blast_state_at_point(center, radius, Vector2(x1, float(chunk["top_left"])))
		var state2 := _blast_state_at_point(center, radius, Vector2(x2, float(chunk["top_right"])))
		var state3 := _bottom_blast_state_for_chunk_side(chunk, true, center, radius, x1)
		var state4 := _bottom_blast_state_for_chunk_side(chunk, false, center, radius, x2)
		if right_interval.x == INF and left_parts.size() == 2 and state1 != 3 and state3 != 3:
			left_parts = [Vector2(float(chunk["top_left"]), float(chunk["bottom_left"]))]
		if left_interval.x == INF and right_parts.size() == 2 and state2 != 3 and state4 != 3:
			right_parts = [Vector2(float(chunk["top_right"]), float(chunk["bottom_right"]))]
		var top_code := (state2 << 2) | state1
		if (top_code == 6 or top_code == 14) and left_parts.size() > 1:
			left_parts = [left_parts[left_parts.size() - 1]]
		elif (top_code == 9 or top_code == 11) and right_parts.size() > 1:
			right_parts = [right_parts[right_parts.size() - 1]]
		var bottom_code := (state4 << 2) | state3
		var split_parts := left_parts.size() == 2 and right_parts.size() == 2
		var split_non_leader := split_parts and superblock_start < source_index
		if not split_parts:
			if left_parts.size() > 1:
				left_parts.resize(1)
			if right_parts.size() > 1:
				right_parts.resize(1)
		var aligned_parts := _align_clipped_side_parts(chunk, left_parts, right_parts)
		left_parts = aligned_parts["left"]
		right_parts = aligned_parts["right"]
		var part_count: int = max(left_parts.size(), right_parts.size())
		var produced_parts: Array[Dictionary] = []
		for part_index in range(part_count):
			if part_index >= left_parts.size() or part_index >= right_parts.size():
				continue
			var left_part: Vector2 = left_parts[part_index]
			var right_part: Vector2 = right_parts[part_index]
			if left_part.y <= left_part.x + 0.5 and right_part.y <= right_part.x + 0.5:
				continue
			var new_chunk: Dictionary = _chunk_from_clipped_parts(chunk, left_part, right_part)
			new_chunk["linked_to_next"] = false
			if split_parts:
				if part_index == 0:
					if split_non_leader:
						new_chunk["falling"] = false
						new_chunk["wait"] = 0.0
						new_chunk["speed"] = 0.0
					else:
						_start_detached_fall(new_chunk)
				elif bool(superblock_motion.get("falling", false)):
					_apply_chunk_motion(new_chunk, superblock_motion)
			produced_parts.append(new_chunk)
		if split_non_leader and not bool(superblock_motion.get("falling", false)) and superblock_start < replacement.size():
			var leader_chunk: Dictionary = replacement[superblock_start]
			_start_detached_fall(leader_chunk)
			replacement[superblock_start] = leader_chunk
		var bottom_cut := bottom_code in [3, 6, 7, 9, 11, 12, 13, 14, 15]
		var support_cut := bool(chunk.get("linked_to_next", false)) and bottom_cut
		if bottom_cut and not produced_parts.is_empty() and not split_parts:
			_apply_detached_motion(produced_parts[0], superblock_motion)
		if support_cut:
			if not produced_parts.is_empty() and not split_parts:
				if state3 == 2 and left_interval.x != INF:
					produced_parts[0]["bottom_left"] = left_interval.x
				if state4 == 2 and right_interval.x != INF:
					produced_parts[0]["bottom_right"] = right_interval.x
			if source_index + 1 < source_chunks.size():
				var next_chunk: Dictionary = source_chunks[source_index + 1]
				if produced_parts.is_empty():
					_propagate_removed_linked_cut_top(next_chunk, chunk, chunk_left_interval, chunk_right_interval)
				_apply_chunk_motion(next_chunk, superblock_motion)
				source_chunks[source_index + 1] = next_chunk
		elif bool(chunk.get("linked_to_next", false)) and not produced_parts.is_empty():
			var bottom_part_index := produced_parts.size() - 1
			var bottom_part: Dictionary = produced_parts[bottom_part_index]
			bottom_part["linked_to_next"] = true
			produced_parts[bottom_part_index] = bottom_part
		replacement.append_array(produced_parts)
	_chunks[slice_index] = replacement
	_sort_slice(_chunks[slice_index])
	_merge_resting_superblocks(_chunks[slice_index])


func _blast_interval_at_x(center: Vector2, radius: float, x: float) -> Vector2:
	var distance: float = abs(x - center.x)
	if distance > radius:
		return Vector2(INF, -INF)
	var root := sqrt(max(0.0, radius * radius - distance * distance))
	return Vector2(center.y - root, center.y + root)


func _clamped_blast_interval_for_chunk_side(chunk: Dictionary, left_side: bool, raw_interval: Vector2) -> Vector2:
	if raw_interval.x == INF:
		return raw_interval
	var bottom_key := "bottom_left" if left_side else "bottom_right"
	var bottom := float(chunk[bottom_key])
	var min_land_screen_y := _world_height_to_screen(CLASSIC_MIN_LAND_HEIGHT)
	if bottom < min_land_screen_y - 0.001:
		return raw_interval
	var clamped_bottom: float = min(raw_interval.y, min_land_screen_y)
	if clamped_bottom <= raw_interval.x:
		return Vector2(INF, -INF)
	return Vector2(raw_interval.x, clamped_bottom)


func _should_skip_linked_superblock_clip(chunk: Dictionary, center: Vector2, radius: float, x1: float, x2: float) -> bool:
	if not bool(chunk.get("linked_to_next", false)):
		return false
	var state1 := _blast_state_at_point(center, radius, Vector2(x1, float(chunk["top_left"])))
	var state2 := _blast_state_at_point(center, radius, Vector2(x2, float(chunk["top_right"])))
	var state3 := _bottom_blast_state_for_chunk_side(chunk, true, center, radius, x1)
	var state4 := _bottom_blast_state_for_chunk_side(chunk, false, center, radius, x2)
	return (state1 == 0 and state2 != 3 and state4 == 3) \
			or (state2 == 0 and state1 != 3 and state3 == 3)


func _bottom_blast_state_for_chunk_side(chunk: Dictionary, left_side: bool, center: Vector2, radius: float, edge_x: float) -> int:
	var bottom_key := "bottom_left" if left_side else "bottom_right"
	var bottom := float(chunk[bottom_key])
	var min_land_screen_y := _world_height_to_screen(CLASSIC_MIN_LAND_HEIGHT)
	if bottom >= min_land_screen_y - 0.001:
		return 1
	return _blast_state_at_point(center, radius, Vector2(edge_x, bottom))


func _blast_state_at_point(center: Vector2, radius: float, point: Vector2) -> int:
	if point.x > center.x + radius or point.x < center.x - radius:
		return 0
	if point.distance_squared_to(center) < radius * radius:
		return 3
	return 1 if center.y < point.y else 2


func _segment_polygon_collision(start: Vector2, end: Vector2, polygon: PackedVector2Array) -> Dictionary:
	var best: Dictionary = {"hit": false, "position": Vector2.ZERO, "distance": INF}
	if Geometry2D.is_point_in_polygon(start, polygon):
		return {"hit": true, "position": start, "distance": 0.0}
	for index in range(polygon.size()):
		var edge_start: Vector2 = polygon[index]
		var edge_end: Vector2 = polygon[(index + 1) % polygon.size()]
		if _point_on_segment(start, edge_start, edge_end):
			return {"hit": true, "position": start, "distance": 0.0}
		var collision: Dictionary = _segment_intersection(start, end, edge_start, edge_end)
		if bool(collision["hit"]) and float(collision["distance"]) < float(best["distance"]):
			best = collision
	return best


func _segment_intersection(a1: Vector2, a2: Vector2, b1: Vector2, b2: Vector2) -> Dictionary:
	var segment_a: Vector2 = a2 - a1
	var segment_b: Vector2 = b2 - b1
	var denominator: float = _cross(segment_a, segment_b)
	if abs(denominator) <= 0.00001:
		var collinear: Dictionary = _collinear_segment_intersection(a1, a2, b1, b2)
		if bool(collinear["hit"]):
			return collinear
		return {"hit": false, "position": Vector2.ZERO, "distance": INF}
	var offset: Vector2 = b1 - a1
	var t: float = _cross(offset, segment_b) / denominator
	var u: float = _cross(offset, segment_a) / denominator
	if t < -0.0001 or t > 1.0001 or u < -0.0001 or u > 1.0001:
		return {"hit": false, "position": Vector2.ZERO, "distance": INF}
	var position: Vector2 = a1 + segment_a * clamp(t, 0.0, 1.0)
	return {"hit": true, "position": position, "distance": a1.distance_to(position)}


func _collinear_segment_intersection(a1: Vector2, a2: Vector2, b1: Vector2, b2: Vector2) -> Dictionary:
	var segment_a: Vector2 = a2 - a1
	var length_squared := segment_a.length_squared()
	if length_squared <= 0.00001:
		return {"hit": false, "position": Vector2.ZERO, "distance": INF}
	if abs(_cross(b1 - a1, segment_a)) > 0.0001 or abs(_cross(b2 - a1, segment_a)) > 0.0001:
		return {"hit": false, "position": Vector2.ZERO, "distance": INF}
	var t1: float = (b1 - a1).dot(segment_a) / length_squared
	var t2: float = (b2 - a1).dot(segment_a) / length_squared
	var overlap_start: float = max(0.0, min(t1, t2))
	var overlap_end: float = min(1.0, max(t1, t2))
	if overlap_end < overlap_start - 0.0001:
		return {"hit": false, "position": Vector2.ZERO, "distance": INF}
	var position: Vector2 = a1 + segment_a * clamp(overlap_start, 0.0, 1.0)
	return {"hit": true, "position": position, "distance": a1.distance_to(position)}


func _point_on_segment(point: Vector2, start: Vector2, end: Vector2) -> bool:
	var segment: Vector2 = end - start
	var length_squared := segment.length_squared()
	if length_squared <= 0.00001:
		return point.distance_squared_to(start) <= 0.0001
	if abs(_cross(point - start, segment)) > 0.0001:
		return false
	var projection: float = (point - start).dot(segment) / length_squared
	return projection >= -0.0001 and projection <= 1.0001


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


func _align_clipped_side_parts(chunk: Dictionary, left_parts: Array[Vector2], right_parts: Array[Vector2]) -> Dictionary:
	# A one-sided crater can split one edge while leaving the opposite edge intact.
	# Preserve both remainders by mirroring the split ratios onto the intact edge.
	if left_parts.size() == 2 and right_parts.size() == 1:
		right_parts = _split_single_part_to_match(
			right_parts[0],
			float(chunk["top_right"]),
			float(chunk["bottom_right"]),
			left_parts,
			float(chunk["top_left"]),
			float(chunk["bottom_left"])
		)
	elif right_parts.size() == 2 and left_parts.size() == 1:
		left_parts = _split_single_part_to_match(
			left_parts[0],
			float(chunk["top_left"]),
			float(chunk["bottom_left"]),
			right_parts,
			float(chunk["top_right"]),
			float(chunk["bottom_right"])
		)
	return {
		"left": left_parts,
		"right": right_parts,
	}


func _split_single_part_to_match(
	part: Vector2,
	target_top: float,
	target_bottom: float,
	source_parts: Array[Vector2],
	source_top: float,
	source_bottom: float
) -> Array[Vector2]:
	if source_parts.size() != 2:
		return [part]
	var source_span := source_bottom - source_top
	if abs(source_span) <= 0.001:
		return [part]
	var top_split_ratio: float = clamp((source_parts[0].y - source_top) / source_span, 0.0, 1.0)
	var bottom_split_ratio: float = clamp((source_parts[1].x - source_top) / source_span, 0.0, 1.0)
	var target_top_split: float = clamp(lerpf(target_top, target_bottom, top_split_ratio), part.x, part.y)
	var target_bottom_split: float = clamp(lerpf(target_top, target_bottom, bottom_split_ratio), part.x, part.y)
	return [
		Vector2(part.x, target_top_split),
		Vector2(target_bottom_split, part.y),
	]


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


func _parts_preserve_chunk_bottom(left_parts: Array[Vector2], right_parts: Array[Vector2], chunk: Dictionary) -> bool:
	if left_parts.is_empty() or right_parts.is_empty():
		return false
	var left_bottom: float = left_parts[left_parts.size() - 1].y
	var right_bottom: float = right_parts[right_parts.size() - 1].y
	return abs(left_bottom - float(chunk["bottom_left"])) <= 0.001 \
			and abs(right_bottom - float(chunk["bottom_right"])) <= 0.001


func _apply_detached_motion(chunk: Dictionary, inherited_motion: Dictionary) -> void:
	if bool(inherited_motion.get("falling", false)):
		_apply_chunk_motion(chunk, inherited_motion)
		return
	_start_detached_fall(chunk)


func _start_detached_fall(chunk: Dictionary) -> void:
	chunk["falling"] = true
	chunk["wait"] = _fall_pause
	chunk["speed"] = 0.0


func _apply_chunk_motion(chunk: Dictionary, motion: Dictionary) -> void:
	chunk["falling"] = bool(motion.get("falling", false))
	chunk["wait"] = float(motion.get("wait", 0.0))
	chunk["speed"] = float(motion.get("speed", 0.0))


func _propagate_removed_linked_top(next_chunk: Dictionary, removed_chunk: Dictionary) -> void:
	next_chunk["top_left"] = float(removed_chunk["top_left"])
	next_chunk["top_right"] = float(removed_chunk["top_right"])
	_refresh_chunk_colors(next_chunk)


func _propagate_removed_linked_cut_top(
	next_chunk: Dictionary,
	removed_chunk: Dictionary,
	left_cut: Vector2,
	right_cut: Vector2
) -> void:
	next_chunk["top_left"] = float(removed_chunk["top_left"]) if left_cut.x == INF else float(left_cut.y)
	next_chunk["top_right"] = float(removed_chunk["top_right"]) if right_cut.x == INF else float(right_cut.y)
	_refresh_chunk_colors(next_chunk)


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
	_move_chunk_edges(chunk, amount, amount)


func _move_chunk_edges(chunk: Dictionary, left_amount: float, right_amount: float) -> void:
	chunk["top_left"] = float(chunk["top_left"]) + left_amount
	chunk["top_right"] = float(chunk["top_right"]) + right_amount
	chunk["bottom_left"] = min(_height, float(chunk["bottom_left"]) + left_amount)
	chunk["bottom_right"] = min(_height, float(chunk["bottom_right"]) + right_amount)


func _move_superblock(slice_chunks: Array, start_index: int, end_index: int, amount: float) -> void:
	_move_superblock_edges(slice_chunks, start_index, end_index, amount, amount)


func _move_superblock_edges(slice_chunks: Array, start_index: int, end_index: int, left_amount: float, right_amount: float) -> void:
	for chunk_index in range(start_index, end_index + 1):
		var chunk: Dictionary = slice_chunks[chunk_index]
		_move_chunk_edges(chunk, left_amount, right_amount)
		slice_chunks[chunk_index] = chunk


func _set_superblock_motion(slice_chunks: Array, start_index: int, end_index: int, falling: bool, speed: float, wait: float) -> void:
	for chunk_index in range(start_index, end_index + 1):
		var chunk: Dictionary = slice_chunks[chunk_index]
		chunk["falling"] = falling
		chunk["speed"] = speed
		chunk["wait"] = wait
		slice_chunks[chunk_index] = chunk


func _settle_landed_superblock(slice_chunks: Array, start_index: int, end_index: int) -> int:
	var next_index := end_index + 1
	if next_index >= slice_chunks.size():
		_set_superblock_motion(slice_chunks, start_index, end_index, false, 0.0, 0.0)
		return end_index
	var lower_motion := _chunk_motion(slice_chunks[next_index])
	var bottom_chunk: Dictionary = slice_chunks[end_index]
	var lower_chunk: Dictionary = slice_chunks[next_index]
	# Fidelity target: Landscape.update() lines 169-198 (Python). The merge
	# path depends on the landing chunk's own vertical colours, then preserves
	# the lower support's motion whether that support is resting or still falling.
	if _chunk_has_classic_uniform_colors(bottom_chunk):
		lower_chunk["top_left"] = float(bottom_chunk["top_left"])
		lower_chunk["top_right"] = float(bottom_chunk["top_right"])
		lower_chunk["top_left_color"] = bottom_chunk.get("top_left_color", bottom_chunk.get("top_color", CLASSIC_SURFACE_TOP))
		lower_chunk["top_right_color"] = bottom_chunk.get("top_right_color", bottom_chunk.get("top_color", CLASSIC_SURFACE_TOP))
		lower_chunk["falling"] = bool(lower_motion.get("falling", false))
		lower_chunk["speed"] = float(lower_motion.get("speed", 0.0))
		lower_chunk["wait"] = float(lower_motion.get("wait", 0.0))
		_refresh_chunk_colors(lower_chunk)
		slice_chunks[next_index] = lower_chunk
		slice_chunks.remove_at(end_index)
		if start_index < end_index:
			_set_superblock_motion(
				slice_chunks,
				start_index,
				end_index - 1,
				bool(lower_motion.get("falling", false)),
				float(lower_motion.get("speed", 0.0)),
				float(lower_motion.get("wait", 0.0))
			)
		return end_index
	bottom_chunk["linked_to_next"] = true
	slice_chunks[end_index] = bottom_chunk
	_set_superblock_motion(
		slice_chunks,
		start_index,
		end_index,
		bool(lower_motion.get("falling", false)),
		float(lower_motion.get("speed", 0.0)),
		float(lower_motion.get("wait", 0.0))
	)
	return _superblock_end(slice_chunks, start_index)


func _chunk_motion(chunk: Dictionary) -> Dictionary:
	return {
		"falling": bool(chunk.get("falling", false)),
		"wait": float(chunk.get("wait", 0.0)),
		"speed": float(chunk.get("speed", 0.0)),
	}


func _superblock_end(slice_chunks: Array, start_index: int) -> int:
	var end_index := start_index
	while end_index < slice_chunks.size() - 1 and bool(slice_chunks[end_index].get("linked_to_next", false)):
		end_index += 1
	return end_index


func _superblock_start(slice_chunks: Array, chunk_index: int) -> int:
	var start_index := chunk_index
	while start_index > 0 and bool(slice_chunks[start_index - 1].get("linked_to_next", false)):
		start_index -= 1
	return start_index


func _superblock_motion_for_index(slice_chunks: Array, chunk_index: int) -> Dictionary:
	if slice_chunks.is_empty():
		return {"falling": false, "wait": 0.0, "speed": 0.0}
	var leader: Dictionary = slice_chunks[_superblock_start(slice_chunks, chunk_index)]
	return {
		"falling": bool(leader.get("falling", false)),
		"wait": float(leader.get("wait", 0.0)),
		"speed": float(leader.get("speed", 0.0)),
	}


func _superblock_landing_gap(slice_chunks: Array, start_index: int, end_index: int) -> float:
	var gaps := _superblock_landing_gaps(slice_chunks, start_index, end_index)
	if gaps.x < 0.0 and gaps.y < 0.0:
		return -1.0
	if gaps.x < 0.0:
		return gaps.y
	if gaps.y < 0.0:
		return gaps.x
	return min(gaps.x, gaps.y)


func _superblock_landing_gaps(slice_chunks: Array, _start_index: int, end_index: int) -> Vector2:
	var bottom_chunk: Dictionary = slice_chunks[end_index]
	var left_gap := INF
	var right_gap := INF
	var next_index := end_index + 1
	if next_index < slice_chunks.size():
		var next_chunk: Dictionary = slice_chunks[next_index]
		left_gap = min(left_gap, float(next_chunk["top_left"]) - float(bottom_chunk["bottom_left"]))
		right_gap = min(right_gap, float(next_chunk["top_right"]) - float(bottom_chunk["bottom_right"]))
	left_gap = min(left_gap, _height - float(bottom_chunk["bottom_left"]))
	right_gap = min(right_gap, _height - float(bottom_chunk["bottom_right"]))
	if left_gap == INF:
		left_gap = -1.0
	else:
		left_gap = max(0.0, left_gap)
	if right_gap == INF:
		right_gap = -1.0
	else:
		right_gap = max(0.0, right_gap)
	return Vector2(left_gap, right_gap)


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


func _chunk_has_classic_uniform_colors(chunk: Dictionary) -> bool:
	var top_left: Color = chunk.get("top_left_color", chunk.get("top_color", CLASSIC_SURFACE_TOP))
	var top_right: Color = chunk.get("top_right_color", chunk.get("top_color", CLASSIC_SURFACE_TOP))
	var bottom_left: Color = chunk.get("bottom_left_color", chunk.get("bottom_color", CLASSIC_BASE))
	var bottom_right: Color = chunk.get("bottom_right_color", chunk.get("bottom_color", CLASSIC_BASE))
	# Python Colour.__eq__ is exact; keep only a tiny float guard here.
	return _color_distance(top_left, bottom_left) <= CLASSIC_COLOUR_EQUAL_EPSILON \
			and _color_distance(top_right, bottom_right) <= CLASSIC_COLOUR_EQUAL_EPSILON


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
