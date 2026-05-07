extends Control

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")

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
	var panel_width: float = max(284.0, min(size.x - 36.0, 840.0))
	var inventory_rows := _inventory_rows(panel_width, inventory.size())
	var panel := Rect2(18.0, 16.0, panel_width, 162.0 + float(inventory_rows) * 34.0)
	draw_rect(panel, Color("#0b1722cc"))
	draw_rect(panel, GroundfireTheme.COLOR_LINE, false, 2.0)

	var player_name := str(_snapshot.get("player_name", "Player"))
	var enemy_name := str(_snapshot.get("enemy_name", "Enemy"))
	var line_one := "Round %d  Turn %s  %s  Weapon %s" % [
		int(_snapshot.get("round", 1)),
		str(_snapshot.get("turn", "Player")),
		str(_snapshot.get("phase", "aim")).capitalize(),
		str(_snapshot.get("weapon", "Shell")),
	]
	var ammo := str(_snapshot.get("ammo", -1))
	if int(_snapshot.get("ammo", -1)) < 0:
		ammo = "inf"
	var player_hp := int(_snapshot.get("player_hp", 0))
	var enemy_hp := int(_snapshot.get("enemy_hp", 0))
	var player_fuel := int(_snapshot.get("player_fuel", 0))
	var line_two := "Angle %d  Power %d  Wind %d  Ammo %s" % [
		int(_snapshot.get("angle", 0)),
		int(_snapshot.get("power", 0)),
		int(_snapshot.get("wind", 0)),
		ammo,
	]
	var line_three := "Score %d  Credits %d  Player Rounds %d  Enemy Rounds %d" % [
		int(_snapshot.get("score", 0)),
		int(_snapshot.get("credits", 0)),
		int(_snapshot.get("player_wins", 0)),
		int(_snapshot.get("enemy_wins", 0)),
	]
	draw_string(ThemeDB.fallback_font, Vector2(32.0, 44.0), line_one, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, GroundfireTheme.COLOR_TEXT)
	draw_string(ThemeDB.fallback_font, Vector2(32.0, 70.0), line_two, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, GroundfireTheme.COLOR_WARN)
	_draw_stat_bar(Rect2(32.0, 82.0, 180.0, 10.0), "%s HP" % player_name, player_hp, 100, Color("#56d364"))
	_draw_stat_bar(Rect2(246.0, 82.0, 180.0, 10.0), "%s HP" % enemy_name, enemy_hp, 100, Color("#ff6b6b"))
	_draw_stat_bar(Rect2(460.0, 82.0, 150.0, 10.0), "Fuel", player_fuel, 100, Color("#7dd3fc"))
	draw_string(ThemeDB.fallback_font, Vector2(32.0, 118.0), line_three, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, GroundfireTheme.COLOR_MUTED)
	_draw_weapon_inventory(Rect2(32.0, 128.0, panel.size.x - 28.0, float(inventory_rows) * 34.0), inventory)
	draw_string(
		ThemeDB.fallback_font,
		Vector2(32.0, panel.position.y + panel.size.y - 18.0),
		str(_snapshot.get("message", "")),
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		15,
		GroundfireTheme.COLOR_CYAN
	)


func _draw_weapon_inventory(bounds: Rect2, inventory: Array) -> void:
	if inventory.is_empty():
		return
	var chip_width := 132.0
	var chip_height := 28.0
	var gap := 8.0
	var per_row: int = max(1, int(floor((bounds.size.x + gap) / (chip_width + gap))))
	for index in range(inventory.size()):
		var weapon: Dictionary = inventory[index]
		var row: int = int(index / per_row)
		var column: int = index % per_row
		var rect := Rect2(
			bounds.position + Vector2(float(column) * (chip_width + gap), float(row) * 34.0),
			Vector2(chip_width, chip_height)
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
			chip_width - 36.0,
			13,
			GroundfireTheme.COLOR_TEXT if selected else GroundfireTheme.COLOR_MUTED
		)


func _inventory_rows(panel_width: float, item_count: int) -> int:
	if item_count <= 0:
		return 1
	var chip_width := 132.0
	var gap := 8.0
	var per_row: int = max(1, int(floor((panel_width - 28.0 + gap) / (chip_width + gap))))
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
