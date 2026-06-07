extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const ClassicFont := preload("res://scripts/classic_font.gd")

signal item_selected(index: int)

const DISABLED_ALPHA := 0.35
const DISABLED_ARROW_ALPHA := 0.1
const EDGE_PADDING := 8.0
const MIN_ARROW_SIZE := 12.0
const MAX_ARROW_SIZE := 30.0

var selected := 0
var item_count := 0

var _items := PackedStringArray()
var _disabled := false
var _font_size := 24
var _hover_arrow := 0
var _pressed_arrow := 0


func _ready() -> void:
	clip_contents = true
	mouse_exited.connect(_on_mouse_exited)
	focus_entered.connect(func() -> void: queue_redraw())
	focus_exited.connect(func() -> void: queue_redraw())
	GroundfireTheme.apply_classic_text_effect(self)
	add_theme_color_override("font_color", GroundfireTheme.COLOR_TEXT)
	add_theme_color_override("font_hover_color", GroundfireTheme.COLOR_WARN)
	_sync_disabled_state()


func set_font_size(font_size: int) -> void:
	_font_size = max(1, font_size)
	add_theme_font_size_override("font_size", _font_size)
	queue_redraw()


func add_item(text: String) -> void:
	_items.append(text)
	item_count = _items.size()
	selected = clampi(selected, 0, max(0, item_count - 1))
	queue_redraw()


func get_item_text(index: int) -> String:
	if index < 0 or index >= _items.size():
		return ""
	return _items[index]


func select(index: int) -> void:
	if _items.is_empty():
		selected = 0
	else:
		selected = clampi(index, 0, _items.size() - 1)
	queue_redraw()


func set_disabled(value: bool) -> void:
	_disabled = value
	_hover_arrow = 0
	_pressed_arrow = 0
	_sync_disabled_state()
	queue_redraw()


func is_disabled() -> bool:
	return _disabled


func uses_classic_font_atlas() -> bool:
	return true


func _sync_disabled_state() -> void:
	focus_mode = Control.FOCUS_NONE if _disabled else Control.FOCUS_ALL
	mouse_filter = Control.MOUSE_FILTER_IGNORE if _disabled else Control.MOUSE_FILTER_STOP


func _draw() -> void:
	var left_base := _left_arrow_base_x()
	var right_base := _right_arrow_base_x()
	var arrow_size := _arrow_size()
	var center_y: float = round(size.y * 0.5)
	draw_colored_polygon(
		PackedVector2Array([
			Vector2(left_base - arrow_size, center_y),
			Vector2(left_base, center_y + arrow_size * 0.5),
			Vector2(left_base, center_y - arrow_size * 0.5),
		]),
		_arrow_color(-1)
	)
	draw_colored_polygon(
		PackedVector2Array([
			Vector2(right_base + arrow_size, center_y),
			Vector2(right_base, center_y + arrow_size * 0.5),
			Vector2(right_base, center_y - arrow_size * 0.5),
		]),
		_arrow_color(1)
	)
	if _items.is_empty():
		return
	var text := _items[selected]
	var text_left := left_base
	var text_width: float = max(1.0, right_base - left_base)
	var text_color := GroundfireTheme.COLOR_TEXT
	if _disabled:
		text_color.a = DISABLED_ALPHA
	ClassicFont.draw_text(
		self,
		text,
		Rect2(Vector2(text_left, 0.0), Vector2(text_width, size.y)),
		float(_font_size),
		text_color,
		HORIZONTAL_ALIGNMENT_CENTER,
		VERTICAL_ALIGNMENT_CENTER,
		ClassicFont.DEFAULT_SPACING_RATIO,
		not _disabled,
		GroundfireTheme.CLASSIC_TEXT_SHADOW_COLOR,
		Vector2(
			float(GroundfireTheme.CLASSIC_TEXT_SHADOW_OFFSET_X),
			float(GroundfireTheme.CLASSIC_TEXT_SHADOW_OFFSET_Y)
		)
	)


func _gui_input(event: InputEvent) -> void:
	if _disabled:
		return
	if event is InputEventMouseMotion:
		_hover_arrow = _arrow_at(event.position)
		queue_redraw()
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_pressed_arrow = _arrow_at(event.position)
			_hover_arrow = _pressed_arrow
			queue_redraw()
			accept_event()
			return
		var released_arrow := _arrow_at(event.position)
		if _pressed_arrow != 0 and released_arrow == _pressed_arrow:
			_step(_pressed_arrow)
			accept_event()
		_pressed_arrow = 0
		_hover_arrow = released_arrow
		queue_redraw()
		return
	if event.is_action_pressed("ui_left"):
		_step(-1)
		accept_event()
		return
	if event.is_action_pressed("ui_right") or event.is_action_pressed("ui_accept"):
		_step(1)
		accept_event()


func _on_mouse_exited() -> void:
	_hover_arrow = 0
	_pressed_arrow = 0
	queue_redraw()


func _step(direction: int) -> void:
	if _items.is_empty():
		return
	selected = wrapi(selected + direction, 0, _items.size())
	item_selected.emit(selected)
	queue_redraw()


func _arrow_at(point: Vector2) -> int:
	if not Rect2(Vector2.ZERO, size).has_point(point):
		return 0
	var arrow_size := _arrow_size()
	var center_y := size.y * 0.5
	if point.y < center_y - arrow_size * 0.5 or point.y > center_y + arrow_size * 0.5:
		return 0
	var left_base := _left_arrow_base_x()
	if point.x >= left_base - arrow_size and point.x <= left_base:
		return -1
	var right_base := _right_arrow_base_x()
	if point.x >= right_base and point.x <= right_base + arrow_size:
		return 1
	return 0


func _arrow_color(direction: int) -> Color:
	var color := GroundfireTheme.COLOR_TEXT
	if _disabled:
		color.a = DISABLED_ARROW_ALPHA
	elif _pressed_arrow == direction or _hover_arrow == direction or (has_focus() and _hover_arrow == 0):
		color = GroundfireTheme.COLOR_WARN
	return color


func _arrow_size() -> float:
	return clamp(size.y * 0.72, MIN_ARROW_SIZE, MAX_ARROW_SIZE)


func _left_arrow_base_x() -> float:
	return EDGE_PADDING + _arrow_size()


func _right_arrow_base_x() -> float:
	return max(_left_arrow_base_x() + _arrow_size() * 2.0, size.x - EDGE_PADDING - _arrow_size())
