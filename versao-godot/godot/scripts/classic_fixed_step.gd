extends RefCounted

const DEFAULT_STEP := 1.0 / 60.0
const DEFAULT_MAX_SUBSTEPS := 8

var _step: float
var _max_substeps: int
var _accumulator := 0.0


func _init(step := DEFAULT_STEP, max_substeps := DEFAULT_MAX_SUBSTEPS) -> void:
	assert(step > 0.0, "step must be positive")
	assert(max_substeps >= 1, "max_substeps must be at least 1")
	_step = float(step)
	_max_substeps = int(max_substeps)


func reset() -> void:
	_accumulator = 0.0


func consume(frame_delta: float) -> Array[float]:
	if frame_delta > 0.0:
		_accumulator += frame_delta
	var steps: Array[float] = []
	while _accumulator + 1.0e-9 >= _step and steps.size() < _max_substeps:
		steps.append(_step)
		_accumulator -= _step
	if steps.size() == _max_substeps and _accumulator > _step:
		_accumulator = _step
	return steps


func accumulator() -> float:
	return _accumulator


func step() -> float:
	return _step

