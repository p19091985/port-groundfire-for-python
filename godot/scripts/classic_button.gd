extends Button

const ClassicFont := preload("res://scripts/classic_font.gd")
const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")

var _classic_font_color := GroundfireTheme.COLOR_TEXT
var _classic_font_hover_color := GroundfireTheme.COLOR_WARN
var _classic_font_disabled_color := GroundfireTheme.BUTTON_FONT_DISABLED
var _classic_spacing_ratio := ClassicFont.DEFAULT_SPACING_RATIO


func _ready() -> void:
	resized.connect(queue_redraw)
	mouse_entered.connect(queue_redraw)
	mouse_exited.connect(queue_redraw)
	focus_entered.connect(queue_redraw)
	focus_exited.connect(queue_redraw)
	button_down.connect(queue_redraw)
	button_up.connect(queue_redraw)
	_hide_builtin_normal_text()


func set_classic_font_colours(normal: Color, hover: Color, disabled_color: Color) -> void:
	_classic_font_color = normal
	_classic_font_hover_color = hover
	_classic_font_disabled_color = disabled_color
	_hide_builtin_normal_text()
	queue_redraw()


func set_classic_spacing_ratio(ratio: float) -> void:
	_classic_spacing_ratio = max(0.1, ratio)
	queue_redraw()


func uses_classic_font_atlas() -> bool:
	return true


func classic_hover_color() -> Color:
	return _classic_font_hover_color


func _draw() -> void:
	var text_color := _classic_font_color
	if disabled:
		text_color = _classic_font_disabled_color
	elif is_hovered() or button_pressed:
		text_color = _classic_font_hover_color
	ClassicFont.draw_text(
		self,
		text,
		Rect2(Vector2.ZERO, size),
		float(get_theme_font_size("font_size")),
		text_color,
		HORIZONTAL_ALIGNMENT_CENTER,
		VERTICAL_ALIGNMENT_CENTER,
		_classic_spacing_ratio,
		not disabled,
		GroundfireTheme.CLASSIC_TEXT_SHADOW_COLOR,
		Vector2(
			float(GroundfireTheme.CLASSIC_TEXT_SHADOW_OFFSET_X),
			float(GroundfireTheme.CLASSIC_TEXT_SHADOW_OFFSET_Y)
		)
	)


func _hide_builtin_normal_text() -> void:
	add_theme_color_override("font_color", Color(_classic_font_color.r, _classic_font_color.g, _classic_font_color.b, 0.0))
	add_theme_color_override("font_hover_color", Color(_classic_font_hover_color.r, _classic_font_hover_color.g, _classic_font_hover_color.b, 0.0))
	add_theme_color_override("font_pressed_color", Color(_classic_font_hover_color.r, _classic_font_hover_color.g, _classic_font_hover_color.b, 0.0))
	add_theme_color_override("font_hover_pressed_color", Color(_classic_font_hover_color.r, _classic_font_hover_color.g, _classic_font_hover_color.b, 0.0))
	add_theme_color_override("font_focus_color", Color(_classic_font_color.r, _classic_font_color.g, _classic_font_color.b, 0.0))
	add_theme_color_override("font_disabled_color", Color(_classic_font_disabled_color.r, _classic_font_disabled_color.g, _classic_font_disabled_color.b, 0.0))
	add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.0))
	add_theme_color_override("font_outline_color", Color(0.0, 0.0, 0.0, 0.0))
