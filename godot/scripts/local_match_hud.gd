extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const WEAPON_ICONS := preload("res://assets/weaponicons.png")

const HUD_MARGIN := 18.0
const HUD_TOP := 16.0
const HUD_PADDING := 14.0
const HUD_MIN_WIDTH := 292.0
const HUD_MAX_WIDTH := 900.0
const HUD_BANNER_HEIGHT := 30.0
const HUD_STAT_HEIGHT := 34.0
const HUD_GAUGE_HEIGHT := 28.0
const HUD_SCORE_HEIGHT := 26.0
const HUD_MESSAGE_HEIGHT := 26.0
const HUD_GAP := 10.0
const INVENTORY_CHIP_WIDTH := 142.0
const INVENTORY_CHIP_HEIGHT := 28.0
const INVENTORY_ROW_HEIGHT := 34.0
const INVENTORY_GAP := 8.0
const ANGLE_MIN := 0.0
const ANGLE_MAX := 180.0
const POWER_MIN := 0.0
const POWER_MAX := 100.0
const WEAPON_ICON_COLUMNS := 4
const WEAPON_ICON_ROWS := 4

var _snapshot := {
	"round": 1,
	"phase": "aim",
	"player_name": "Player",
	"enemy_name": "Enemy",
	"player_hp": 100,
	"enemy_hp": 100,
	"player_fuel": 100,
	"angle": 45,
	"power": 55,
	"wind": 0,
	"wind_effect": 0.0,
	"quake_active": false,
	"quake_countdown": 60.0,
	"weapon": "Shell",
	"ammo": -1,
	"turn": "Player",
	"score": 0,
	"credits": 0,
	"player_wins": 0,
	"enemy_wins": 0,
	"inventory": [],
	"message": "",
}


func set_snapshot(snapshot: Dictionary) -> void:
	_snapshot = snapshot
	queue_redraw()


func _draw() -> void:
	var inventory: Array = _snapshot.get("inventory", [])
	var panel_width := _panel_width()
	var panel := Rect2(HUD_MARGIN, HUD_TOP, panel_width, _panel_height(panel_width, inventory.size()))
	_draw_panel_background(panel)

	var cursor_y := panel.position.y + HUD_PADDING
	cursor_y = _draw_turn_banner(panel, cursor_y)
	cursor_y = _draw_stat_row(panel, cursor_y + HUD_GAP)
	cursor_y = _draw_gauge_row(panel, cursor_y + HUD_GAP)
	cursor_y = _draw_score_row(panel, cursor_y + HUD_GAP)
	cursor_y += HUD_GAP

	var inventory_rows := _inventory_rows(panel_width, inventory.size())
	_draw_weapon_inventory(
		Rect2(
			panel.position + Vector2(HUD_PADDING, cursor_y - panel.position.y),
			Vector2(panel.size.x - HUD_PADDING * 2.0, float(inventory_rows) * INVENTORY_ROW_HEIGHT)
		),
		inventory
	)
	cursor_y += float(inventory_rows) * INVENTORY_ROW_HEIGHT
	_draw_message_strip(
		Rect2(
			panel.position + Vector2(HUD_PADDING, cursor_y - panel.position.y + HUD_GAP),
			Vector2(panel.size.x - HUD_PADDING * 2.0, HUD_MESSAGE_HEIGHT)
		)
	)


func _panel_width() -> float:
	return max(HUD_MIN_WIDTH, min(size.x - HUD_MARGIN * 2.0, HUD_MAX_WIDTH))


func _panel_height(panel_width: float, item_count: int) -> float:
	return HUD_PADDING * 2.0 \
		+ HUD_BANNER_HEIGHT \
		+ HUD_GAP \
		+ HUD_STAT_HEIGHT \
		+ HUD_GAP \
		+ _gauge_row_height(panel_width) \
		+ HUD_GAP \
		+ HUD_SCORE_HEIGHT \
		+ HUD_GAP \
		+ float(_inventory_rows(panel_width, item_count)) * INVENTORY_ROW_HEIGHT \
		+ HUD_GAP \
		+ HUD_MESSAGE_HEIGHT


func _gauge_row_height(panel_width: float) -> float:
	var inner_width := panel_width - HUD_PADDING * 2.0
	if inner_width < 420.0:
		return HUD_GAUGE_HEIGHT * 2.0 + INVENTORY_GAP
	return HUD_GAUGE_HEIGHT


func _draw_panel_background(panel: Rect2) -> void:
	draw_rect(panel, Color("#0b1722dd"))
	draw_rect(panel.grow(-4.0), Color("#111f2b66"), false, 1.0)
	draw_rect(panel, GroundfireTheme.COLOR_LINE, false, 2.0)


func _draw_turn_banner(panel: Rect2, cursor_y: float) -> float:
	var rect := Rect2(panel.position + Vector2(HUD_PADDING, cursor_y - panel.position.y), Vector2(panel.size.x - HUD_PADDING * 2.0, HUD_BANNER_HEIGHT))
	var phase := str(_snapshot.get("phase", "aim"))
	var turn := str(_snapshot.get("turn", "Player"))
	draw_rect(rect, _phase_color(phase))
	draw_rect(rect, _turn_color(turn), false, 1.0)
	var banner_text := "Round %d  %s turn  %s  Weapon %s %s" % [
		int(_snapshot.get("round", 1)),
		turn,
		phase.capitalize(),
		str(_snapshot.get("weapon", "Shell")),
		_format_ammo_label(int(_snapshot.get("ammo", -1))),
	]
	draw_string(ThemeDB.fallback_font, rect.position + Vector2(10.0, 21.0), banner_text, HORIZONTAL_ALIGNMENT_LEFT, rect.size.x - 20.0, 16, GroundfireTheme.COLOR_TEXT)
	return cursor_y + HUD_BANNER_HEIGHT


func _draw_stat_row(panel: Rect2, cursor_y: float) -> float:
	var inner_width := panel.size.x - HUD_PADDING * 2.0
	var gap := INVENTORY_GAP
	var bar_width: float = max(76.0, (inner_width - gap * 2.0) / 3.0)
	var y := cursor_y + 18.0
	_draw_stat_bar(Rect2(panel.position.x + HUD_PADDING, y, bar_width, 10.0), "%s HP" % str(_snapshot.get("player_name", "Player")), int(_snapshot.get("player_hp", 0)), 100, Color("#56d364"))
	_draw_stat_bar(Rect2(panel.position.x + HUD_PADDING + bar_width + gap, y, bar_width, 10.0), "%s HP" % str(_snapshot.get("enemy_name", "Enemy")), int(_snapshot.get("enemy_hp", 0)), 100, Color("#ff6b6b"))
	_draw_stat_bar(Rect2(panel.position.x + HUD_PADDING + (bar_width + gap) * 2.0, y, bar_width, 10.0), "Fuel", int(_snapshot.get("player_fuel", 0)), 100, Color("#7dd3fc"))
	return cursor_y + HUD_STAT_HEIGHT


func _draw_gauge_row(panel: Rect2, cursor_y: float) -> float:
	var inner_width := panel.size.x - HUD_PADDING * 2.0
	var stacked := inner_width < 420.0
	var gauge_width := inner_width if stacked else (inner_width - INVENTORY_GAP) * 0.5
	var angle_rect := Rect2(panel.position + Vector2(HUD_PADDING, cursor_y - panel.position.y), Vector2(gauge_width, HUD_GAUGE_HEIGHT))
	var power_rect := Rect2(
		panel.position + Vector2(HUD_PADDING, cursor_y - panel.position.y + HUD_GAUGE_HEIGHT + INVENTORY_GAP),
		Vector2(gauge_width, HUD_GAUGE_HEIGHT)
	) if stacked else Rect2(
		panel.position + Vector2(HUD_PADDING + gauge_width + INVENTORY_GAP, cursor_y - panel.position.y),
		Vector2(gauge_width, HUD_GAUGE_HEIGHT)
	)
	_draw_gauge(angle_rect, "Angle", float(_snapshot.get("angle", 0)), ANGLE_MIN, ANGLE_MAX, GroundfireTheme.COLOR_WARN)
	_draw_gauge(power_rect, "Power", float(_snapshot.get("power", 0)), POWER_MIN, POWER_MAX, GroundfireTheme.COLOR_CYAN)
	return cursor_y + _gauge_row_height(panel.size.x)


func _draw_score_row(panel: Rect2, cursor_y: float) -> float:
	var inner_width := panel.size.x - HUD_PADDING * 2.0
	var gap := INVENTORY_GAP
	var chip_width: float = max(64.0, (inner_width - gap * 3.0) / 4.0)
	var labels := [
		{"label": "Score", "value": str(int(_snapshot.get("score", 0))), "color": GroundfireTheme.COLOR_CYAN},
		{"label": "Credits", "value": str(int(_snapshot.get("credits", 0))), "color": GroundfireTheme.COLOR_WARN},
		{"label": "Player", "value": str(int(_snapshot.get("player_wins", 0))), "color": Color("#56d364")},
		{"label": "Enemy", "value": str(int(_snapshot.get("enemy_wins", 0))), "color": Color("#ff6b6b")},
	]
	for index in range(labels.size()):
		var item: Dictionary = labels[index]
		var chip_color: Color = item["color"]
		_draw_value_chip(
			Rect2(panel.position + Vector2(HUD_PADDING + float(index) * (chip_width + gap), cursor_y - panel.position.y), Vector2(chip_width, HUD_SCORE_HEIGHT)),
			str(item["label"]),
			str(item["value"]),
			chip_color
		)
	return cursor_y + HUD_SCORE_HEIGHT


func _draw_value_chip(rect: Rect2, label: String, value: String, color: Color) -> void:
	draw_rect(rect, Color("#07131ecc"))
	draw_rect(rect, color.darkened(0.25), false, 1.0)
	draw_string(ThemeDB.fallback_font, rect.position + Vector2(7.0, 18.0), label, HORIZONTAL_ALIGNMENT_LEFT, rect.size.x * 0.58, 12, GroundfireTheme.COLOR_MUTED)
	draw_string(ThemeDB.fallback_font, rect.position + Vector2(rect.size.x * 0.58, 18.0), value, HORIZONTAL_ALIGNMENT_RIGHT, rect.size.x * 0.38, 13, color)


func _draw_gauge(rect: Rect2, label: String, value: float, minimum: float, maximum: float, color: Color) -> void:
	var ratio: float = clamp((value - minimum) / max(1.0, maximum - minimum), 0.0, 1.0)
	draw_rect(rect, Color("#07131ecc"))
	draw_rect(Rect2(rect.position, Vector2(rect.size.x * ratio, rect.size.y)), color.darkened(0.25))
	draw_rect(rect, color.darkened(0.1), false, 1.0)
	draw_string(ThemeDB.fallback_font, rect.position + Vector2(8.0, 19.0), "%s %d" % [label, int(round(value))], HORIZONTAL_ALIGNMENT_LEFT, rect.size.x - 16.0, 13, GroundfireTheme.COLOR_TEXT)


func _draw_message_strip(rect: Rect2) -> void:
	var quake_label := _quake_label(bool(_snapshot.get("quake_active", false)), float(_snapshot.get("quake_countdown", 60.0)))
	var status := "%s%s" % [
		_wind_label(float(_snapshot.get("wind_effect", _snapshot.get("wind", 0)))),
		"" if quake_label.is_empty() else "  " + quake_label,
	]
	draw_rect(rect, Color("#07131ecc"))
	draw_rect(rect, GroundfireTheme.COLOR_LINE, false, 1.0)
	draw_string(ThemeDB.fallback_font, rect.position + Vector2(8.0, 18.0), status, HORIZONTAL_ALIGNMENT_LEFT, rect.size.x * 0.36, 13, GroundfireTheme.COLOR_WARN)
	draw_string(ThemeDB.fallback_font, rect.position + Vector2(rect.size.x * 0.36, 18.0), str(_snapshot.get("message", "")), HORIZONTAL_ALIGNMENT_LEFT, rect.size.x * 0.62, 13, GroundfireTheme.COLOR_CYAN)


func _phase_color(phase: String) -> Color:
	match phase:
		"projectile":
			return Color("#3b2a10dd")
		"round_over":
			return Color("#1e293bdd")
		"shop":
			return Color("#321c3add")
		_:
			return Color("#10223add")


func _turn_color(turn: String) -> Color:
	if turn == "Enemy":
		return Color("#ff6b6b")
	return GroundfireTheme.COLOR_LINE


func _format_ammo_label(value: int) -> String:
	return "Ammo %s" % _format_ammo(value)


func _draw_weapon_inventory(bounds: Rect2, inventory: Array) -> void:
	if inventory.is_empty():
		return
	var per_row: int = max(1, int(floor((bounds.size.x + INVENTORY_GAP) / (INVENTORY_CHIP_WIDTH + INVENTORY_GAP))))
	for index in range(inventory.size()):
		var weapon: Dictionary = inventory[index]
		var row: int = int(index / per_row)
		var column: int = index % per_row
		var rect := Rect2(
			bounds.position + Vector2(float(column) * (INVENTORY_CHIP_WIDTH + INVENTORY_GAP), float(row) * INVENTORY_ROW_HEIGHT),
			Vector2(INVENTORY_CHIP_WIDTH, INVENTORY_CHIP_HEIGHT)
		)
		var selected := bool(weapon.get("selected", false))
		var weapon_name := str(weapon.get("name", "Weapon"))
		draw_rect(rect, Color("#a85d00cc") if selected else Color("#111f2bcc"))
		draw_rect(rect, GroundfireTheme.COLOR_LINE if selected else Color("#5b6872"), false, 1.0)
		_draw_weapon_icon(Rect2(rect.position + Vector2(6.0, 5.0), Vector2(18.0, 18.0)), weapon_name, selected)
		draw_string(
			ThemeDB.fallback_font,
			rect.position + Vector2(30.0, 19.0),
			"%s %s" % [weapon_name, _format_ammo(int(weapon.get("ammo", -1)))],
			HORIZONTAL_ALIGNMENT_LEFT,
			INVENTORY_CHIP_WIDTH - 36.0,
			13,
			GroundfireTheme.COLOR_TEXT if selected else GroundfireTheme.COLOR_MUTED
		)


func _inventory_rows(panel_width: float, item_count: int) -> int:
	if item_count <= 0:
		return 1
	var inner_width := panel_width - HUD_PADDING * 2.0
	var per_row: int = max(1, int(floor((inner_width + INVENTORY_GAP) / (INVENTORY_CHIP_WIDTH + INVENTORY_GAP))))
	return int(ceil(float(item_count) / float(per_row)))


func _draw_stat_bar(rect: Rect2, label: String, value: int, maximum: int, color: Color) -> void:
	var ratio: float = clamp(float(value) / float(max(1, maximum)), 0.0, 1.0)
	draw_string(ThemeDB.fallback_font, rect.position + Vector2(0.0, -4.0), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, GroundfireTheme.COLOR_MUTED)
	draw_rect(rect, Color("#111f2bcc"))
	draw_rect(Rect2(rect.position, Vector2(rect.size.x * ratio, rect.size.y)), color)
	draw_rect(rect, GroundfireTheme.COLOR_LINE, false, 1.0)


func _draw_weapon_icon(rect: Rect2, weapon_name: String, selected: bool) -> void:
	var color := _weapon_color(weapon_name)
	if selected:
		color = color.lerp(Color.WHITE, 0.18)
	draw_rect(rect, Color("#07131e99"))
	draw_rect(rect, color, false, 1.0)
	var source_rect := _weapon_icon_source_rect(weapon_name)
	if source_rect.size.x > 0.0 and source_rect.size.y > 0.0:
		draw_texture_rect_region(WEAPON_ICONS, rect.grow(-1.0), source_rect)
		return
	var center := rect.get_center()
	if weapon_name == "Machine Gun":
		for raw_offset in [-5.0, 0.0, 5.0]:
			var offset := float(raw_offset)
			draw_line(center + Vector2(-5.0, offset), center + Vector2(6.0, offset - 2.0), color, 2.0)
	elif weapon_name == "MIRV":
		draw_circle(center + Vector2(-4.0, -3.0), 3.0, color)
		draw_circle(center + Vector2(4.0, -3.0), 3.0, color)
		draw_circle(center + Vector2(0.0, 5.0), 3.0, color)
	elif weapon_name == "Missile":
		var points := PackedVector2Array([
			center + Vector2(0.0, -8.0),
			center + Vector2(7.0, 6.0),
			center + Vector2(0.0, 3.0),
			center + Vector2(-7.0, 6.0),
		])
		draw_colored_polygon(points, color)
	elif weapon_name == "Nuke":
		draw_circle(center, 6.0, color)
		draw_line(center + Vector2(-8.0, 0.0), center + Vector2(8.0, 0.0), Color("#07131e"), 2.0)
		draw_line(center + Vector2(0.0, -8.0), center + Vector2(0.0, 8.0), Color("#07131e"), 2.0)
	else:
		draw_circle(center, 5.0, color)


func _weapon_icon_source_rect(weapon_name: String) -> Rect2:
	var icon_index := _weapon_icon_index(weapon_name)
	if icon_index < 0:
		return Rect2()
	var cell_size := Vector2(
		float(WEAPON_ICONS.get_width()) / float(WEAPON_ICON_COLUMNS),
		float(WEAPON_ICONS.get_height()) / float(WEAPON_ICON_ROWS)
	)
	var column := icon_index % WEAPON_ICON_COLUMNS
	var row := int(icon_index / WEAPON_ICON_COLUMNS)
	return Rect2(Vector2(float(column) * cell_size.x, float(row) * cell_size.y), cell_size)


func _weapon_icon_index(weapon_name: String) -> int:
	match weapon_name:
		"Nuke":
			return 1
		"Machine Gun":
			return 2
		"MIRV":
			return 4
		"Missile":
			return 10
		_:
			return 0


func _weapon_color(weapon_name: String) -> Color:
	match weapon_name:
		"Machine Gun":
			return Color("#f97316")
		"MIRV":
			return Color("#c084fc")
		"Missile":
			return Color("#60a5fa")
		"Nuke":
			return Color("#facc15")
		_:
			return Color("#e5e7eb")


func _format_ammo(value: int) -> String:
	if value < 0:
		return "inf"
	return str(value)


func _wind_label(value: float) -> String:
	var magnitude: int = int(abs(round(value)))
	if magnitude == 0:
		return "Wind calm"
	if value > 0.0:
		return "Wind -> %d" % magnitude
	return "Wind <- %d" % magnitude


func _quake_label(active: bool, countdown: float) -> String:
	if active:
		return "Quake!"
	if countdown <= 10.0:
		return "Quake in %ds" % max(0, int(ceil(countdown)))
	return ""
