extends Control
## Classic browser presentation; directory, persistence and joining stay in the backend.
const ClassicFont := preload("res://scripts/classic_font.gd")
var browser: Control
var scroll := 0
var hit_regions: Array = []
var dialog := ""
var address := "127.0.0.1:27015"
var pending_entry: Dictionary = {}
var join_role := "human"
var descending := false
var thumb := Rect2()
var dragging := false
var drag_offset := 0.0

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	focus_mode = Control.FOCUS_ALL
	grab_focus()
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR

func _process(_delta: float) -> void:
	queue_redraw()

func _point(x: float, y: float) -> Vector2:
	return Vector2(int((x + 10) * size.x / 20), int((7.5 - y) * size.y / 15))

func _rect(left: float, top: float, right: float, bottom: float) -> Rect2:
	return Rect2(_point(left, top), _point(right, bottom) - _point(left, top))

func _panel(bounds: Array, color: Color) -> void:
	draw_rect(_rect(bounds[0], bounds[1], bounds[2], bounds[3]), color)

func _text(x: float, y: float, value: String, height := 0.22, spacing := 0.09, color := Color.WHITE, centered := false, shadow := true) -> void:
	var width := height * size.x / 20
	var tall := height * size.y / 15
	ClassicFont.draw_text(self, value, Rect2(_point(x,y) - Vector2(0,tall), Vector2(0,tall)), width, color,
		HORIZONTAL_ALIGNMENT_CENTER if centered else HORIZONTAL_ALIGNMENT_LEFT,
		VERTICAL_ALIGNMENT_BOTTOM, spacing / height, shadow, Color8(0,0,0,100), Vector2(-width/8,tall/8), true)

func _button(bounds: Array, label: String, action: Callable, enabled := true) -> void:
	var rect := _rect(bounds[0], bounds[1], bounds[2], bounds[3])
	var hover := enabled and rect.has_point(get_local_mouse_position())
	_panel(bounds, Color8(153,76,0,220 if hover else 180) if enabled else Color8(0,0,0,120))
	_text((bounds[0]+bounds[2])/2, bounds[3]+0.1, label, .22,.09,Color.WHITE if enabled else Color8(76,76,76),true,enabled)
	if enabled:
		hit_regions.append({"rect":rect,"action":action})

func _tab_name() -> String:
	return browser._tabs.get_tab_title(browser._tabs.current_tab).to_lower()

func _columns() -> Array:
	if _tab_name() == "unique":
		return [["name","Servers",-9.55,-2.85],["description","Server description",-2.85,4.75],["game","Game",4.75,6.4],["players","Players",6.4,7.25],["map","Map",7.25,8.55],["latency","Latency",8.55,9.55]]
	if _tab_name() == "history":
		return [["name","Servers",-9.55,4.2],["game","Game",4.2,5.95],["players","Players",5.95,6.85],["map","Map",6.85,7.95],["latency","Latency",7.95,8.75],["last_played","Last played",8.75,9.55]]
	return [["name","Servers",-9.55,4.75],["game","Game",4.75,6.4],["players","Players",6.4,7.25],["map","Map",7.25,8.55],["latency","Latency",8.55,9.55]]

func _shorten(value: String, limit: int) -> String:
	return value if value.length() <= limit else value.left(maxi(1,limit-1)) + "..."

func _draw() -> void:
	if browser == null:
		return
	hit_regions.clear()
	_panel([-9.95,7.35,9.95,-7.35],Color8(0,0,0,145))
	_panel([-9.75,6.55,9.75,-6.95],Color8(0,0,0,120))
	_text(-9.55,6.82,"Servers",.42,.2)
	_text(9.58,6.47,"x",.45,.3,Color.WHITE,true)
	hit_regions.append({"rect":_rect(9.35,7.05,9.8,6.55),"action":browser._on_back_pressed})
	var left := -9.75
	for index in range(browser._tabs.tab_count):
		var label: String = browser._tabs.get_tab_title(index)
		var wide := 1.65 if label.to_lower() in ["favorites","spectate"] else 1.45
		var active: bool = index == browser._tabs.current_tab
		_panel([left,6.05,left+wide,5.45],Color8(153,76,0,210) if active else Color8(0,0,0,115))
		_text(left+.12,5.55,"Lan" if label == "LAN" else label,.25,.1,Color.YELLOW if active else Color.WHITE)
		hit_regions.append({"rect":_rect(left,6.05,left+wide,5.45),"action":_select_tab.bind(index)})
		left += wide+.05
	_panel([-9.75,5.25,9.55,4.85],Color8(153,76,0,150))
	for column in _columns():
		var suffix := (" v" if descending else " ^") if browser._sort_mode == column[0] else ""
		_text(column[2]+.07,4.92,column[1]+suffix)
		hit_regions.append({"rect":_rect(column[2],5.25,column[3],4.85),"action":_sort.bind(column[0])})
	var entries: Array = browser._visible_entries
	scroll = clampi(scroll,0,maxi(0,entries.size()-24))
	for index in range(scroll,mini(entries.size(),scroll+24)):
		var y := 4.48 - (index-scroll)*.42
		var selected: bool = index == browser._selected_index
		var bounds := _rect(-9.75,y+.22,9.55,y-.2)
		if selected or bounds.has_point(get_local_mouse_position()):
			draw_rect(bounds,Color8(153,76,0,135 if selected else 80))
		for column in _columns():
			var value := str(entries[index].get(column[0], ""))
			if column[0] == "name" and (bool(entries[index].get("requires_password",false)) or str(entries[index].get("passworded","false")).to_lower() == "true"):
				value = "[P] " + value
			_text(column[2]+.07,y-.12,_shorten(value,maxi(4,int((column[3]-column[2])*5))),.2,.08,Color.WHITE if selected else Color8(235,240,245))
		hit_regions.append({"rect":bounds,"action":_select_row.bind(index),"row":index})
	if entries.is_empty():
		_text(-9.55,4.35,browser._status.text,.26,.11)
	else:
		_text(-9.55,-5.65,_shorten(browser._status.text,92),.2,.08,Color8(190,215,230))
	_panel([9.55,4.85,9.75,-5.85],Color8(0,0,0,135))
	_button([9.55,4.85,9.75,4.45],"^",_scroll_by.bind(-1))
	_button([9.55,-5.45,9.75,-5.85],"v",_scroll_by.bind(1))
	var thumb_height := maxf(.65,9.7*minf(1.0,24.0/maxi(1,entries.size())))
	var thumb_top := 4.35 - (9.7-thumb_height)*scroll/maxi(1,entries.size()-24)
	thumb = _rect(9.57,thumb_top,9.73,thumb_top-thumb_height)
	draw_rect(thumb,Color8(153,76,0,180))
	for offset in [.0,.12,.24]:
		_panel([9.5+offset,-7.13,9.72+offset,-7.18],Color8(255,255,255,170))
	_button([-9.7,-5.95,-7.8,-6.55],"Change filters",_show_filters)
	_button([8.55,-5.95,9.75,-6.55],"Connect",browser._on_connect_pressed,not entries.is_empty())
	if _tab_name() == "favorites":
		_button([3,-5.95,5.4,-6.55],"Add Current Server",browser._toggle_selected_favorite,not entries.is_empty())
		_button([5.5,-5.95,7.1,-6.55],"Add a Server",browser._show_direct_join_dialog)
		_button([7.2,-5.95,8.45,-6.55],"Refresh",browser._refresh_entries)
	elif _tab_name() in ["history","lan"]:
		_button([7.1,-5.95,8.45,-6.55],"Refresh",browser._refresh_entries)
	else:
		_button([3,-5.95,5,-6.55],"Add Favorite",browser._toggle_selected_favorite,not entries.is_empty())
		_button([5.1,-5.95,6.65,-6.55],"Quick refresh",browser._refresh_entries,not entries.is_empty())
		_button([6.75,-5.95,8.45,-6.55],"Refresh all",browser._refresh_online_directory)
	_button([3.65,-6.72,5.8,-7.22],"Random Server",browser._connect_random_server,browser._best_quick_match_index(entries)>=0)
	_text(6.2,-7.08,"Open the list of all servers",.2,.08,Color.CYAN)
	hit_regions.append({"rect":_rect(5.9,-6.75,9.55,-7.15),"action":_show_all})

	if not dialog.is_empty():
		hit_regions.clear()
		_draw_dialog()

func _show_all() -> void:
	browser.classic_show_all = true
	browser._render_entries()

func _select_tab(index: int) -> void:
	scroll = 0
	browser.classic_show_all = false
	browser._tabs.current_tab = index
	browser._render_entries()

func _select_row(index: int) -> void:
	browser._select_row(index)

func _sort(column: String) -> void:
	descending = not descending if browser._sort_mode == column else false
	browser._sort_mode = column
	browser.classic_sort_descending = descending
	browser._sort_entries(browser._visible_entries)
	browser._save_browser_store()
	_select_row(0)

func _scroll_by(amount: int) -> void:
	scroll = clampi(scroll+amount,0,maxi(0,browser._visible_entries.size()-24))

func _gui_input(event: InputEvent) -> void:
	if not dialog.is_empty():
		_dialog_input(event)
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and not event.pressed:
		dragging = false
	if event is InputEventMouseMotion and dragging:
		var track := _rect(9.55,4.35,9.75,-5.35)
		var travel := maxf(1,track.size.y-thumb.size.y)
		scroll = clampi(roundi((event.position.y-drag_offset-track.position.y)/travel*maxi(0,browser._visible_entries.size()-24)),0,maxi(0,browser._visible_entries.size()-24))
		accept_event()

		return
	if event is InputEventMouseButton and event.pressed:
		grab_focus()
		if event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:
			_scroll_by(-1 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1)
		elif event.button_index == MOUSE_BUTTON_LEFT:
			if thumb.has_point(event.position):
				dragging = true
				drag_offset = event.position.y-thumb.position.y
				accept_event()
				return
			if _rect(9.55,4.45,9.75,-5.45).has_point(event.position):
				_scroll_by(-24 if event.position.y < thumb.position.y else 24)
				accept_event()
				return
			for region in hit_regions:
				if region.rect.has_point(event.position):
					region.action.call()
					if event.double_click and region.has("row"):
						browser._on_connect_pressed()
					break
		accept_event()
	elif event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_UP, KEY_DOWN, KEY_PAGEUP, KEY_PAGEDOWN:
				var amount: int = {KEY_UP:-1,KEY_DOWN:1,KEY_PAGEUP:-24,KEY_PAGEDOWN:24}[event.keycode]
				var index := clampi(browser._selected_index + amount,0,maxi(0,browser._visible_entries.size()-1))
				_select_row(index)
				scroll = clampi(scroll,maxi(0,index-23),index)
			KEY_ENTER: browser._on_connect_pressed()
			KEY_ESCAPE: browser._on_back_pressed()
			KEY_F5: browser._refresh_online_directory()
			KEY_TAB: _select_tab(posmod(browser._tabs.current_tab + (-1 if event.shift_pressed else 1),browser._tabs.tab_count))
		accept_event()


func _show_filters() -> void:
	browser._cancel_server_probe()
	dialog = "filters"
	grab_focus()

func show_join(entry: Dictionary) -> void:
	pending_entry = entry.duplicate(true)
	join_role = "spectator" if _tab_name() == "spectate" else "human"
	browser._password_line.text = ""
	dialog = "join"
	grab_focus()

func show_add() -> void:
	dialog = "add"
	grab_focus()

func close_dialog() -> void:
	browser._cancel_server_probe()
	if dialog == "join":
		browser._password_line.text = ""
		pending_entry.clear()
	dialog = ""
	grab_focus()

func _field(bounds: Array, value: String) -> void:
	_panel(bounds,Color8(0,0,0,170))
	_text(bounds[0]+.15,bounds[3]+.14,_shorten(value,maxi(8,int((bounds[2]-bounds[0])*6)))+"_",.26,.1,Color.WHITE,false,false)

func _checkbox(bounds: Array, checked: bool, label: String, action: Callable) -> void:
	_panel(bounds,Color8(0,0,0,170))
	if checked:
		_text((bounds[0]+bounds[2])/2,bounds[3]+.08,"x",.3,.1,Color.YELLOW,true,false)
	_text(bounds[2]+.25,bounds[3]+.1,label,.25,.1,Color.WHITE,false,false)
	hit_regions.append({"rect":_rect(bounds[0],bounds[1],bounds[2],bounds[3]),"action":action})

func _radio(bounds: Array, label: String, role: String) -> void:
	_panel(bounds,Color8(153,76,0,180))
	_text(bounds[0]+.18,bounds[3]+.14,("(*) " if join_role == role else "( ) ")+label,.26,.1,Color.YELLOW if join_role == role else Color.WHITE)
	hit_regions.append({"rect":_rect(bounds[0],bounds[1],bounds[2],bounds[3]),"action":func() -> void: join_role = role})

func _draw_dialog() -> void:
	if dialog == "filters":
		_panel([-5.8,3.3,5.8,-4.5],Color8(0,0,0,205))
		_panel([-5.8,3.3,5.8,2.45],Color8(153,76,0,150))
		_text(-5.35,2.8,"Filters",.38,.16)
		_text(-5.25,1.55,"Server / map",.26,.11,Color.WHITE,false,false)
		_field([-3.1,2,4.9,1.4],browser._filter_text)
		_checkbox([-4.8,.85,-4.25,.3],not browser._hide_full,"Show full servers",_toggle_filter.bind("_hide_full"))
		_checkbox([-4.8,.05,-4.25,-.5],not browser._hide_empty,"Show empty servers",_toggle_filter.bind("_hide_empty"))
		_checkbox([-4.8,-.75,-4.25,-1.3],not browser._hide_passworded,"Show passworded servers",_toggle_filter.bind("_hide_passworded"))
		_checkbox([-4.8,-1.55,-4.25,-2.1],browser._secure_only,"Secure servers only",_toggle_filter.bind("_secure_only"))
		_text(-5.25,-1.8,"Region",.26,.11,Color.WHITE,false,false)
		_button([1,-1.35,4.1,-1.95],"All regions" if browser._region.is_empty() else browser._region.to_upper(),_cycle_filter.bind("_region",["","world","na","sa","eu","asia","local"]))
		_text(-5.25,-2.8,"Maximum latency",.26,.11,Color.WHITE,false,false)
		_button([1,-2.35,4.1,-2.95],"Any" if browser._max_latency == 0 else "%d ms" % browser._max_latency,_cycle_filter.bind("_max_latency",[0,50,100,150,250,500]))
		_button([4.25,-2.35,5.55,-2.95],"Clear",_clear_filters)
		_button([1.15,-3.45,3,-4.05],"Apply",_apply_filters)
		_button([3.15,-3.45,5,-4.05],"Close",close_dialog)
	elif dialog == "add":
		_panel([-5.8,2.45,5.8,-2.3],Color8(0,0,0,205))
		_panel([-5.8,2.45,5.8,1.55],Color8(153,76,0,150))
		_text(-5.35,1.9,"Add a Server",.38,.16)
		_text(-5.15,.35,"Address",.26,.11,Color.WHITE,false,false)
		_field([-4.7,.85,4.7,.2],address)
		_button([1.3,-1.05,3.2,-1.65],"Add",_add_server)
		_button([3.35,-1.05,5.15,-1.65],"Cancel",close_dialog)
	elif dialog == "join":
		_panel([-5.8,2.7,5.8,-3.3],Color8(0,0,0,205))
		_panel([-5.8,2.7,5.8,1.8],Color8(153,76,0,150))
		_text(-5.35,2.15,"Join Server",.38,.16)
		_text(-5.15,1.15,str(pending_entry.get("endpoint","")),.24,.1,Color.WHITE,false,false)
		if str(pending_entry.get("passworded","false")).to_lower() == "true" or bool(pending_entry.get("requires_password",false)):
			_text(-5.15,.55,"Password",.24,.1,Color.WHITE,false,false)
			_field([-4.7,1.05,4.7,.4],"*".repeat(browser._password_line.text.length()))
		else:
			_text(-5.15,.45,"Player type",.24,.1,Color8(190,215,230),false,false)
		_radio([-4.7,-.1,-1.2,-.75],"Human","human")
		_radio([.3,-.1,3.8,-.75],"AI","ai")
		_radio([-2.2,-1,2.2,-1.65],"Spectator (read only)","spectator")
		_checkbox([-4.7,-1.7,-.2,-2.2],browser._auto_retry_check.button_pressed,"Join when a slot opens",func() -> void: browser._auto_retry_check.button_pressed = not browser._auto_retry_check.button_pressed)
		_button([.85,-2.25,2.7,-2.85],"Connect",_connect)
		_button([2.85,-2.25,4.65,-2.85],"Cancel",close_dialog)

func _toggle_filter(property: String) -> void:
	browser.set(property,not browser.get(property))
	_refresh_filters()

func _cycle_filter(property: String, values: Array) -> void:
	browser.set(property,values[(values.find(browser.get(property))+1)%values.size()])
	_refresh_filters()

func _clear_filters() -> void:
	browser._filter_text = ""
	for property in ["_hide_full","_hide_empty","_hide_passworded","_secure_only"]:
		browser.set(property,false)
	browser._region = ""
	browser._max_latency = 0
	_refresh_filters()

func _refresh_filters() -> void:
	var previous: int = browser._selected_index
	browser._save_browser_store()
	browser._render_entries()
	browser._selected_index = clampi(previous,0,maxi(0,browser._visible_entries.size()-1)) if not browser._visible_entries.is_empty() else -1

func _apply_filters() -> void:
	scroll = 0
	browser._selected_index = 0 if not browser._visible_entries.is_empty() else -1
	close_dialog()

func _add_server() -> void:
	if browser._add_classic_server(address):
		close_dialog()

func connection_entry() -> Dictionary:
	var entry := pending_entry.duplicate(true)
	entry["password"] = browser._password_line.text
	entry["is_computer"] = join_role == "ai"
	entry["spectator"] = join_role == "spectator"
	entry["auto_retry_when_full"] = browser._auto_retry_check.button_pressed
	return entry

func _connect() -> void:
	var entry := connection_entry()
	close_dialog()
	browser._stage_connect(entry)

func _dialog_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		for region in hit_regions:
			if region.rect.has_point(event.position):
				region.action.call()
				break
	elif event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			close_dialog()
		elif event.keycode in [KEY_ENTER,KEY_KP_ENTER]:
			match dialog:
				"filters": _apply_filters()
				"add": _add_server()
				"join": _connect()
		else:
			var value: String = browser._filter_text if dialog == "filters" else (address if dialog == "add" else browser._password_line.text)
			if event.keycode == KEY_BACKSPACE:
				value = value.left(maxi(0,value.length()-1))
			elif event.unicode >= 32 and event.unicode <= 126 and value.length() < (48 if dialog == "filters" else 64):
				value += String.chr(event.unicode)
			match dialog:
				"filters":
					browser._filter_text = value
					_refresh_filters()
				"add": address = value
				"join": browser._password_line.text = value
	accept_event()
