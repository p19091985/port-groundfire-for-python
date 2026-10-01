extends Label

const ClassicFont := preload("res://scripts/classic_font.gd")
const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")

var _classic_font_color := GroundfireTheme.COLOR_TEXT
var _classic_spacing_ratio := ClassicFont.DEFAULT_SPACING_RATIO
var _draw_font_size := 0.0
var classic_shadow := true

func set_classic_draw_size(value: float) -> void:
	_draw_font_size = value
	clip_text = true
	add_theme_font_size_override("font_size", 1)
	queue_redraw()


func _ready() -> void:
	resized.connect(queue_redraw)
	_hide_builtin_text()


func set_classic_font_color(color: Color) -> void:
	_classic_font_color = color
	_hide_builtin_text()
	queue_redraw()


func set_classic_spacing_ratio(ratio: float) -> void:
	_classic_spacing_ratio = max(0.1, ratio)
	queue_redraw()


func uses_classic_font_atlas() -> bool:
	return true


func _draw() -> void:
	ClassicFont.draw_text(
		self,
		text,
		Rect2(Vector2.ZERO, size),
		_draw_font_size if _draw_font_size > 0 else float(get_theme_font_size("font_size")),
		_classic_font_color,
		horizontal_alignment,
		VERTICAL_ALIGNMENT_BOTTOM if _draw_font_size > 0 else vertical_alignment,
		_classic_spacing_ratio,
		classic_shadow,
		Color8(0, 0, 0, 100) if _draw_font_size > 0 else GroundfireTheme.CLASSIC_TEXT_SHADOW_COLOR,
		Vector2(
			float(GroundfireTheme.CLASSIC_TEXT_SHADOW_OFFSET_X),
			float(GroundfireTheme.CLASSIC_TEXT_SHADOW_OFFSET_Y)
		) if _draw_font_size <= 0 else Vector2(-_draw_font_size / 8, size.y / 8),
		_draw_font_size > 0
	)


func _hide_builtin_text() -> void:
	add_theme_color_override("font_color", Color(_classic_font_color.r, _classic_font_color.g, _classic_font_color.b, 0.0))
	add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.0))
	add_theme_color_override("font_outline_color", Color(0.0, 0.0, 0.0, 0.0))
