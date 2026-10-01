extends RefCounted
## One internal scale for every local simulation quantity. Rendering alone
## converts this space to Python's fixed [-10,10] x [-7.5,7.5] viewport.
const SCALE := 104.0
const CLASSIC_PI := 3.141592654 # src/common.py; tank movement uses math.radians instead.
const TERRAIN_HALF_WIDTH := 11.0
const ORIGIN := Vector2(11.0, 7.5) * SCALE
const SIZE := Vector2(22.0, 15.5) * SCALE
const PROJECTILE_GRAVITY := 10.0 * SCALE

static func from_classic(x: float, y: float) -> Vector2:
	return Vector2(ORIGIN.x + x * SCALE, ORIGIN.y - y * SCALE)

static func to_classic(point: Vector2) -> Vector2:
	return Vector2((point.x - ORIGIN.x) / SCALE, (ORIGIN.y - point.y) / SCALE)

static func viewport_scale(viewport: Vector2) -> Vector2:
	return viewport / (Vector2(20.0, 15.0) * SCALE)
