extends RefCounted

const COLOR_BG := Color("#07131e")
const COLOR_PANEL := Color("#0b1722")
const COLOR_PANEL_SOFT := Color("#111f2b")
const COLOR_FIELD := Color("#1b2a34")
const COLOR_LINE := Color("#8b5206")
const COLOR_ACCENT := Color("#a85d00")
const COLOR_ACCENT_HOT := Color("#d47708")
const COLOR_TEXT := Color("#f8fafc")
const COLOR_MUTED := Color("#b9c7d2")
const COLOR_CYAN := Color("#80d8ff")
const COLOR_WARN := Color("#ffd166")


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


static func button_style(accent := false, hover := false, disabled := false) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	if disabled:
		style.bg_color = Color("#262d34")
	elif accent:
		style.bg_color = COLOR_ACCENT_HOT if hover else COLOR_ACCENT
	else:
		style.bg_color = Color("#263744") if hover else COLOR_PANEL_SOFT
	style.border_color = COLOR_LINE if accent else Color("#5b6872")
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
		style.bg_color = Color("#8b5206aa")
	elif hover:
		style.bg_color = Color("#a85d004f")
	else:
		style.bg_color = Color("#111f2b55")
	style.border_color = Color("#223241")
	style.set_border_width_all(1)
	return style


static func apply_button(button: Button, accent := false) -> void:
	button.add_theme_stylebox_override("normal", button_style(accent))
	button.add_theme_stylebox_override("hover", button_style(accent, true))
	button.add_theme_stylebox_override("pressed", button_style(true, true))
	button.add_theme_stylebox_override("disabled", button_style(accent, false, true))
	button.add_theme_color_override("font_color", COLOR_TEXT)
	button.add_theme_color_override("font_hover_color", COLOR_TEXT)
	button.add_theme_color_override("font_pressed_color", COLOR_TEXT)
	button.add_theme_color_override("font_disabled_color", Color("#525b65"))
	button.add_theme_font_size_override("font_size", 16)


static func apply_label(label: Label, size := 16, color := COLOR_TEXT) -> void:
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
