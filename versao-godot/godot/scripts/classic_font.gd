extends RefCounted

const FONT_TEXTURE := preload("res://assets/fonts.png")
const CELL_SIZE := 32.0
const PROPORTIONAL_ROW_OFFSET := 8
const DEFAULT_SPACING_RATIO := 0.86
const GLYPH_WIDTH_RATIO := 0.8
const WIDTHS := [
	9, 9, 14, 18, 18, 27, 24, 8, 11, 11, 15, 18, 9, 9, 9, 8,
	18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 9, 9, 18, 18, 18, 17,
	20, 21, 21, 21, 21, 20, 18, 22, 22, 11, 18, 22, 18, 25, 22, 22,
	20, 22, 21, 20, 20, 22, 21, 27, 21, 21, 20, 11, 8, 11, 18, 14,
	9, 18, 18, 18, 18, 18, 11, 18, 18, 9, 9, 18, 9, 27, 18, 18,
	18, 18, 14, 17, 13, 18, 17, 25, 18, 17, 15, 11, 8, 11, 18, 17,
	18, 10, 8, 18, 14, 27, 18, 18, 9, 27, 20, 9, 27, 10, 20, 10,
	10, 8, 8, 14, 14, 14, 14, 27, 9, 26, 17, 9, 27, 10, 15, 21,
]


static func measure(text: String, font_size: float, spacing_ratio := DEFAULT_SPACING_RATIO) -> float:
	var spacing: float = max(1.0, font_size * spacing_ratio)
	var length := 0.0
	for index in range(text.length()):
		length += float(_width_for_code(text.unicode_at(index))) / 24.0 * spacing
	return length


static func draw_text(
	canvas_item: CanvasItem,
	text: String,
	rect: Rect2,
	font_size: float,
	color: Color,
	horizontal_alignment := HORIZONTAL_ALIGNMENT_CENTER,
	vertical_alignment := VERTICAL_ALIGNMENT_CENTER,
	spacing_ratio := DEFAULT_SPACING_RATIO,
	shadow := true,
	shadow_color := Color("#00000096"),
	shadow_offset := Vector2(3.0, 3.0)
) -> void:
	if text.is_empty() or font_size <= 0.0:
		return
	if shadow:
		_draw_text_run(
			canvas_item,
			text,
			rect.position + shadow_offset,
			rect.size,
			font_size,
			shadow_color,
			horizontal_alignment,
			vertical_alignment,
			spacing_ratio
		)
	_draw_text_run(
		canvas_item,
		text,
		rect.position,
		rect.size,
		font_size,
		color,
		horizontal_alignment,
		vertical_alignment,
		spacing_ratio
	)


static func _draw_text_run(
	canvas_item: CanvasItem,
	text: String,
	position: Vector2,
	available_size: Vector2,
	font_size: float,
	color: Color,
	horizontal_alignment: HorizontalAlignment,
	vertical_alignment: VerticalAlignment,
	spacing_ratio: float
) -> void:
	var text_width := measure(text, font_size, spacing_ratio)
	var glyph_width: float = max(1.0, round(font_size * GLYPH_WIDTH_RATIO))
	var x := position.x
	if horizontal_alignment == HORIZONTAL_ALIGNMENT_CENTER:
		x += (available_size.x - text_width) * 0.5
	elif horizontal_alignment == HORIZONTAL_ALIGNMENT_RIGHT:
		x += available_size.x - text_width

	var y := position.y
	if vertical_alignment == VERTICAL_ALIGNMENT_CENTER:
		y += (available_size.y - font_size) * 0.5
	elif vertical_alignment == VERTICAL_ALIGNMENT_BOTTOM:
		y += available_size.y - font_size

	var spacing: float = max(1.0, font_size * spacing_ratio)
	for index in range(text.length()):
		var code := text.unicode_at(index)
		if code >= 32 and code < 128 and code != 32:
			var source := _source_rect_for_code(code)
			canvas_item.draw_texture_rect_region(
				FONT_TEXTURE,
				Rect2(Vector2(round(x), round(y)), Vector2(glyph_width, round(font_size))),
				source,
				color
			)
		x += float(_width_for_code(code)) / 24.0 * spacing


static func _source_rect_for_code(code: int) -> Rect2:
	var glyph_code := clampi(code, 32, 127)
	var col := glyph_code % 16
	var row := int(floor(float(glyph_code - 32) / 16.0)) + PROPORTIONAL_ROW_OFFSET
	return Rect2(float(col) * CELL_SIZE, float(row) * CELL_SIZE, CELL_SIZE, CELL_SIZE)


static func _width_for_code(code: int) -> int:
	var index := code - 32
	if index >= 0 and index < WIDTHS.size():
		return int(WIDTHS[index])
	return 18
