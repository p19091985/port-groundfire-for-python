extends RefCounted

# CPython's integer-seeded MT19937 path. The classic client uses Python's
# random module, so Godot must not substitute its unrelated PCG stream.
const STATE_SIZE := 624
const PERIOD := 397
const UINT32_MASK := 0xffffffff
const UPPER_MASK := 0x80000000
const LOWER_MASK := 0x7fffffff

var _state: Array[int] = []
var _index := STATE_SIZE


func _init(seed_value := 0) -> void:
	seed_from_int(seed_value)


func seed_from_int(seed_value: int) -> void:
	var absolute_seed := absi(seed_value)
	var key: Array[int] = []
	while absolute_seed > 0:
		key.append(absolute_seed & UINT32_MASK)
		absolute_seed >>= 32
	if key.is_empty():
		key.append(0)
	_init_by_array(key)


func randbelow(stop: int) -> int:
	assert(stop > 0)
	var bits := _bit_length(stop)
	var value := getrandbits(bits)
	while value >= stop:
		value = getrandbits(bits)
	return value


func getrandbits(bit_count: int) -> int:
	assert(bit_count > 0 and bit_count <= 32)
	return _next_uint32() >> (32 - bit_count)


func _bit_length(value: int) -> int:
	var bits := 0
	while value > 0:
		bits += 1
		value >>= 1
	return bits


func _init_genrand(seed_value: int) -> void:
	_state.resize(STATE_SIZE)
	_state[0] = seed_value & UINT32_MASK
	for index in range(1, STATE_SIZE):
		var previous := _state[index - 1]
		_state[index] = (1812433253 * (previous ^ (previous >> 30)) + index) & UINT32_MASK
	_index = STATE_SIZE


func _init_by_array(key: Array[int]) -> void:
	_init_genrand(19650218)
	var state_index := 1
	var key_index := 0
	var remaining := maxi(STATE_SIZE, key.size())
	while remaining > 0:
		var previous := _state[state_index - 1]
		_state[state_index] = ((_state[state_index] ^ ((previous ^ (previous >> 30)) * 1664525)) + key[key_index] + key_index) & UINT32_MASK
		state_index += 1
		key_index += 1
		if state_index >= STATE_SIZE:
			_state[0] = _state[STATE_SIZE - 1]
			state_index = 1
		if key_index >= key.size():
			key_index = 0
		remaining -= 1
	remaining = STATE_SIZE - 1
	while remaining > 0:
		var previous := _state[state_index - 1]
		_state[state_index] = ((_state[state_index] ^ ((previous ^ (previous >> 30)) * 1566083941)) - state_index) & UINT32_MASK
		state_index += 1
		if state_index >= STATE_SIZE:
			_state[0] = _state[STATE_SIZE - 1]
			state_index = 1
		remaining -= 1
	_state[0] = UPPER_MASK
	_index = STATE_SIZE


func _next_uint32() -> int:
	if _index >= STATE_SIZE:
		_twist()
	var value := _state[_index]
	_index += 1
	value ^= value >> 11
	value ^= (value << 7) & 0x9d2c5680
	value ^= (value << 15) & 0xefc60000
	value ^= value >> 18
	return value & UINT32_MASK


func _twist() -> void:
	for index in range(STATE_SIZE):
		var combined := (_state[index] & UPPER_MASK) | (_state[(index + 1) % STATE_SIZE] & LOWER_MASK)
		var value := _state[(index + PERIOD) % STATE_SIZE] ^ (combined >> 1)
		if (combined & 1) != 0:
			value ^= 0x9908b0df
		_state[index] = value & UINT32_MASK
	_index = 0
