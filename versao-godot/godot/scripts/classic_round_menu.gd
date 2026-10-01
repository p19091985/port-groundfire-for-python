extends Control
## Presentation of ScoreMenu/ShopMenu in Python world coordinates. Rules and
## input remain in LocalMatch; this view only reads their resulting state.
const ClassicFont := preload("res://scripts/classic_font.gd")
const Tile := preload("res://assets/menuback.png")
const Defeated := preload("res://assets/damage.png")
var runtime: Control
var scroll := 0.0

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR

func _process(delta: float) -> void:
	if visible:
		scroll = fmod(scroll + delta * 0.1, 1.0)
		queue_redraw()

func _point(x: float, y: float) -> Vector2:
	return Vector2(int((x + 10.0) * size.x / 20.0), int((7.5 - y) * size.y / 15.0))

func _box(left: float, top: float, right: float, bottom: float, color: Color) -> void:
	draw_rect(Rect2(_point(left, top), _point(right, bottom) - _point(left, top)), color)

func _text(x: float, y: float, text: String, height := 0.4, spacing := 0.3, color := Color8(230,230,230), shadow := true) -> void:
	var width := height * size.x / 20.0
	var tall := height * size.y / 15.0
	# Python text is positioned by its bottom edge and scales with viewport X.
	ClassicFont.draw_text(self, text, Rect2(_point(x, y) - Vector2(0, tall), Vector2(0, tall)), width,
		color, HORIZONTAL_ALIGNMENT_CENTER, VERTICAL_ALIGNMENT_BOTTOM, spacing / height, shadow,
		Color8(0,0,0,100), Vector2(-width / 8.0, tall / 8.0), true)

func _tank(x: float, y: float, color: Color) -> void:
	draw_colored_polygon(PackedVector2Array([
		_point(x, y), _point(x + 0.3, y + 0.6), _point(x + 0.9, y + 0.6), _point(x + 1.2, y)]), color)

func _draw() -> void:
	if runtime == null:
		return
	var pixel_scale := get_viewport_transform().get_scale()
	var tile_size := Tile.get_size() / pixel_scale
	var offset := Vector2(int(scroll * Tile.get_width()), int(scroll * Tile.get_height())) / pixel_scale
	for x in range(int(ceil(size.x / tile_size.x)) + 1):
		for y in range(int(ceil(size.y / tile_size.y)) + 1):
			draw_texture_rect(Tile, Rect2(Vector2(x, y) * tile_size - offset, tile_size), false, Color8(102,179,230))
	if runtime.get("_phase") == "score":
		_draw_score()
	elif runtime.get("_phase") == "winner":
		_draw_winner()
	else:
		_draw_shop()

func _draw_score() -> void:
	var rows: Array = runtime.call("_score_rows_snapshot")
	for index in range(rows.size()):
		var row: Dictionary = rows[index]
		var top := 6.0 - index * 1.6
		for bounds in [Vector2(-8,-4.8), Vector2(-4.5,4.5), Vector2(4.8,9)]:
			_box(bounds.x, top, bounds.y, top - 1.3, Color8(0,0,0,128))
		_text(-9, top - 0.9, str(row.rank), 0.5, 0.4)
		_tank(-7, top - 0.8, row.color)
		_text(-6.4, top - 1.15, str(row.name), 0.3, 0.2, Color.WHITE, false)
		_text(6.9, top - 0.9, str(row.score), 0.5, 0.4, Color.WHITE, false)
		var position := 0.0
		for defeated in row.defeated_icons:
			var origin := _point(-4 + position, top - 0.3)
			draw_texture_rect(Defeated, Rect2(origin, _point(-3.1 + position, top - 0.9) - origin), false, defeated.color)
			if bool(defeated.get("leader", false)):
				_box(-3.7 + position, top - 0.3, -3.6 + position, top - 0.9, Color8(128,128,128))
				_box(-3.6 + position, top - 0.3, -2.9 + position, top - 0.75, defeated.color)
			position += 1.3
	_text(-6.3, 6.5, "Player", 0.5, 0.4)
	_text(0, 6.5, "Scoring for Round", 0.5, 0.4)
	_text(6.9, 6.5, "Total Score", 0.5, 0.4)

func _draw_shop() -> void:
	var rows: Array = runtime.call("_shop_participants_snapshot")
	var highlighted: Array[int] = []
	for index in range(rows.size()):
		var row: Dictionary = rows[index]
		if bool(row.done):
			continue
		var shift := index * 1.5
		var color := Color8(76,25,25,128)
		if index % 2 == 0:
			_box(-9.4 + shift, 5.6, -6.6 + shift, 4.9, color)
			_box(-9.4 + shift, 4.9, -8.1 + shift, -5.3, color)
		else:
			_box(-10.9 + shift, -5.5, -8.1 + shift, -6.2, color)
			_box(-9.4 + shift, 4.7, -8.1 + shift, -5.5, color)
		var selection := int(row.get("selected_position", 0))
		if float(runtime.get("_shop_input_delays").get(index, 0.4)) < 0.4 and not highlighted.has(selection):
			highlighted.append(selection)
			_box(-9.4, 4.6 - selection * 0.8, 9.4, 3.8 - selection * 0.8, Color8(255,255,255,25))
	for index in range(rows.size()):
		var row: Dictionary = rows[index]
		if bool(row.done):
			continue
		var shift := index * 1.5
		var selected := int(row.get("selected_position", 0))
		var v := selected * 0.8
		_tank(-9.35 + shift, 3.9 - v, row.color)
		var inventory: RefCounted = runtime.call("_shop_inventory", index)
		if selected <= 1:
			var bars: float = inventory.stock_for("Machine Gun") / 50.0 if selected == 0 else runtime.call("_shop_fuel_reserve", index)
			var bar := 0
			while bars > 0:
				_box(-9.4 + shift, 3.85 - v - bar * 0.2, -9.4 + shift + 1.3 * minf(1, bars), 3.7 - v - bar * 0.2, Color.WHITE)
				bars -= 1
				bar += 1
		elif selected < 5:
			_text(-8.75 + shift, 3.5 - v, "x%d" % inventory.stock_for(["MIRV","Missile","Nuke"][selected - 2]), 0.3, 0.25, Color.WHITE, false)
		_text((-8 if index % 2 == 0 else -9.5) + shift, 5.1 if index % 2 == 0 else -6.0,
			"$%d" % runtime.call("_shop_credits", index), 0.35, 0.275)
	_text(0, 6.5, "Round %d of %d" % [runtime.get("_round") + 1, runtime.get("_total_rounds")], 0.6, 0.5, Color.WHITE)
	_text(4, 5, "Cost")
	_text(7, 5, "Item")
	var inventory: RefCounted = runtime.call("_shop_inventory", 0)
	var items: Array = [{"name":"Machine Gun", "cost":inventory.weapon_cost("Machine Gun")},
		{"name":"Jump Jet", "cost":50}, {"name":"MIRV", "cost":inventory.weapon_cost("MIRV")},
		{"name":"Missile", "cost":inventory.weapon_cost("Missile")}, {"name":"Nuke", "cost":inventory.weapon_cost("Nuke")},
		{"name":"Rolling Mines", "cost":50}, {"name":"Airstrike", "cost":100}, {"name":"Death's Head", "cost":200},
		{"name":"Hover Coil", "cost":150}, {"name":"Corbomite", "cost":20}]
	for index in range(items.size()):
		var item: Dictionary = items[index]
		var color := Color8(230,230,230) if index < 5 else Color8(76,76,76)
		var display: String = {"MIRV":"Mirvs", "Missile":"Missiles", "Nuke":"Nukes"}.get(str(item.name), str(item.name))
		_text(7, 4.0 - index * 0.8, display, 0.4, 0.3, color)
		_text(4, 4.0 - index * 0.8, "$%d" % item.cost, 0.4, 0.3, color)
	_text(7, -4, "Done!")

func _draw_winner() -> void:
	var winners: Array = runtime.call("_winner_card_snapshots")
	_text(0, 6.5, "Final Result", 0.6, 0.5, Color.WHITE)
	_text(0, 5.5, "It's a tie!" if winners.size() > 1 else "We have a winner!", 0.6, 0.5, Color.WHITE)
	for index in range(winners.size()):
		var row := index / 4
		var columns := mini(4, winners.size() - row * 4)
		var x := -(columns - 1) * 2.0 + (index % 4) * 4.0
		var y := ((winners.size() - 1) / 4) * 2.0 - row * 4.0
		draw_colored_polygon(PackedVector2Array([_point(x - 1.5, y - 0.75), _point(x - 0.75, y + 0.75),
			_point(x + 0.75, y + 0.75), _point(x + 1.5, y - 0.75)]), winners[index].color)
		_text(x, y - 1.2, str(winners[index].name), 0.4, 0.35, Color.WHITE)
		for letter in range(7):
			var angle: float = runtime.get("_winner_spin_phase") - letter * 0.2
			var px := x + cos(angle) * 1.8
			var py := y - 0.4 + sin(angle) * 1.8
			var rotation := PI / 2.0 - angle
			var extent := absf(cos(rotation)) + absf(sin(rotation))
			var side := int(0.6 * size.x / 20.0)
			var code := "Winner!".unicode_at(letter)
			var source := Rect2((code % 16) * 32, ((code - 32) / 16) * 32, 32, 32)
			for shadow in [true, false]:
				var top_left := _point(px - (0.075 if shadow else 0.0), py - (0.075 if shadow else 0.0)) - Vector2(0, side)
				draw_set_transform(top_left + Vector2.ONE * side / 2.0, rotation, Vector2.ONE / extent)
				draw_texture_rect_region(ClassicFont.FONT_TEXTURE, Rect2(-Vector2.ONE * side / 2.0, Vector2.ONE * side), source,
					Color8(0,0,0,100) if shadow else Color.WHITE)
				draw_set_transform(Vector2.ZERO)
