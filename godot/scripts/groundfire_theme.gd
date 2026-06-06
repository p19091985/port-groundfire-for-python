extends RefCounted

const COLOR_BG := Color("#365e79")
const COLOR_MENU_TILE_TINT := Color("#66b3e6")
const COLOR_PANEL := Color("#00000091")
const COLOR_PANEL_SOFT := Color("#00000078")
const COLOR_FIELD := Color("#000000aa")
const COLOR_LINE := Color("#994c00")
const COLOR_ACCENT := Color("#994c00")
const COLOR_ACCENT_HOT := Color("#be5f00")
const COLOR_TEXT := Color("#ffffff")
const COLOR_MUTED := Color("#bcd7e6")
const COLOR_CYAN := Color("#00ffff")
const COLOR_WARN := Color("#ffff00")
const BUTTON_FONT_SIZE := 16
const BUTTON_BG := Color("#994c00b4")
const BUTTON_BG_HOVER := Color("#be5f00d7")
const BUTTON_BG_DISABLED := Color("#23232396")
const BUTTON_FONT_DISABLED := Color("#4c4c4c")
const BUTTON_BORDER := Color("#994c00")


static func panel_style(soft := false) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = COLOR_PANEL_SOFT if soft else COLOR_PANEL
	style.border_color = COLOR_LINE
	style.set_border_width_all(2)
	style.corner_radius_top_left = 0
	style.corner_radius_top_right = 0
	style.corner_radius_bottom_left = 0
	style.corner_radius_bottom_right = 0
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	return style


static func classic_panel_style(soft := false) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = COLOR_PANEL_SOFT if soft else COLOR_PANEL
	style.border_color = Color.TRANSPARENT
	style.set_border_width_all(0)
	style.corner_radius_top_left = 0
	style.corner_radius_top_right = 0
	style.corner_radius_bottom_left = 0
	style.corner_radius_bottom_right = 0
	style.content_margin_left = 0
	style.content_margin_right = 0
	style.content_margin_top = 0
	style.content_margin_bottom = 0
	return style


static func button_style(accent := false, hover := false, disabled := false) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	if disabled:
		style.bg_color = BUTTON_BG_DISABLED
	elif accent:
		style.bg_color = COLOR_ACCENT_HOT if hover else COLOR_ACCENT
	else:
		style.bg_color = BUTTON_BG_HOVER if hover else BUTTON_BG
	style.border_color = COLOR_LINE if accent else BUTTON_BORDER
	style.set_border_width_all(1)
	style.corner_radius_top_left = 0
	style.corner_radius_top_right = 0
	style.corner_radius_bottom_left = 0
	style.corner_radius_bottom_right = 0
	return style


static func field_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = COLOR_FIELD
	style.border_color = Color("#5b6872")
	style.set_border_width_all(1)
	return style


static func modal_backdrop_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color("#00000099")
	return style


static func row_style(selected := false, hover := false) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	if selected:
		style.bg_color = Color("#994c0087")
	elif hover:
		style.bg_color = Color("#994c0050")
	else:
		style.bg_color = Color("#00000000")
	style.border_color = Color.TRANSPARENT
	style.set_border_width_all(0)
	return style


static func apply_button(button: Button, accent := false) -> void:
	button.add_theme_stylebox_override("normal", button_style(accent))
	button.add_theme_stylebox_override("hover", button_style(accent, true))
	button.add_theme_stylebox_override("focus", button_style(true, true))
	button.add_theme_stylebox_override("pressed", button_style(true, true))
	button.add_theme_stylebox_override("disabled", button_style(accent, false, true))
	button.add_theme_color_override("font_color", COLOR_TEXT)
	button.add_theme_color_override("font_hover_color", COLOR_TEXT)
	button.add_theme_color_override("font_pressed_color", COLOR_TEXT)
	button.add_theme_color_override("font_disabled_color", BUTTON_FONT_DISABLED)
	button.add_theme_font_size_override("font_size", BUTTON_FONT_SIZE)


static func apply_classic_button(button: Button, font_size := 16) -> void:
	button.add_theme_stylebox_override("normal", button_style(true))
	button.add_theme_stylebox_override("hover", button_style(true, true))
	button.add_theme_stylebox_override("focus", button_style(true, true))
	button.add_theme_stylebox_override("pressed", button_style(true, true))
	button.add_theme_stylebox_override("disabled", button_style(true, false, true))
	button.add_theme_color_override("font_color", COLOR_TEXT)
	button.add_theme_color_override("font_hover_color", COLOR_TEXT)
	button.add_theme_color_override("font_pressed_color", COLOR_TEXT)
	button.add_theme_color_override("font_disabled_color", BUTTON_FONT_DISABLED)
	button.add_theme_font_size_override("font_size", font_size)


static func apply_label(label: Label, size := 16, color := COLOR_TEXT) -> void:
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
