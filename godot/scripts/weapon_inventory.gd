extends RefCounted

const SHELL := "Shell"
const MACHINE_GUN := "Machine Gun"
const MIRV := "MIRV"
const MISSILE := "Missile"
const NUKE := "Nuke"

const WEAPONS := [
	{"name": SHELL, "damage": 40, "blast": 48.0, "ammo": -1, "speed": 4.2, "cost": 0, "kind": "shell"},
	{"name": MACHINE_GUN, "damage": 6, "blast": 16.0, "ammo": 50, "speed": 5.8, "cost": 50, "kind": "machine_gun", "volley": 5},
	{"name": MIRV, "damage": 22, "blast": 34.0, "ammo": 3, "speed": 4.0, "cost": 50, "kind": "mirv"},
	{"name": MISSILE, "damage": 40, "blast": 46.0, "ammo": 4, "speed": 4.8, "cost": 50, "kind": "missile"},
	{"name": NUKE, "damage": 90, "blast": 96.0, "ammo": 1, "speed": 3.6, "cost": 50, "kind": "nuke"},
]

var _selected_index := 0
var _ammo: Dictionary = {}


func _init() -> void:
	reset_round_ammo()


func reset_round_ammo() -> void:
	_ammo.clear()
	for weapon in WEAPONS:
		_ammo[str(weapon["name"])] = int(weapon["ammo"])
	_selected_index = 0


func current() -> Dictionary:
	return WEAPONS[_selected_index]


func current_name() -> String:
	return str(current()["name"])


func current_damage() -> int:
	return int(current()["damage"])


func current_blast_radius() -> float:
	return float(current()["blast"])


func current_speed_multiplier() -> float:
	return float(current()["speed"])


func current_kind() -> String:
	return str(current()["kind"])


func current_ammo() -> int:
	return int(_ammo.get(current_name(), -1))


func ammo_for(weapon_name: String) -> int:
	return int(_ammo.get(weapon_name, 0))


func weapon_by_name(weapon_name: String) -> Dictionary:
	for weapon in WEAPONS:
		if str(weapon["name"]) == weapon_name:
			return weapon
	return WEAPONS[0]


func select_by_name(weapon_name: String) -> bool:
	for index in range(WEAPONS.size()):
		if str(WEAPONS[index]["name"]) == weapon_name and int(_ammo.get(weapon_name, 0)) != 0:
			_selected_index = index
			return true
	return false


func has_ammo(weapon_name: String) -> bool:
	return ammo_for(weapon_name) != 0


func cycle(direction := 1) -> String:
	for _attempt in range(WEAPONS.size()):
		_selected_index = wrapi(_selected_index + direction, 0, WEAPONS.size())
		if current_ammo() != 0:
			return current_name()
	return current_name()


func consume_current() -> bool:
	var ammo := current_ammo()
	if ammo == -1:
		return true
	if ammo <= 0:
		return false
	var spend: int = max(1, int(current().get("volley", 1)))
	_ammo[current_name()] = max(0, ammo - min(spend, ammo))
	if int(_ammo[current_name()]) == 0:
		cycle(1)
	return true


func weapon_cost(weapon_name: String) -> int:
	for weapon in WEAPONS:
		if str(weapon["name"]) == weapon_name:
			return int(weapon.get("cost", 0))
	return 0


func ammo_pack_size(weapon_name: String) -> int:
	for weapon in WEAPONS:
		if str(weapon["name"]) == weapon_name:
			return max(0, int(weapon.get("ammo", 0)))
	return 0


func add_ammo(weapon_name: String, amount := -1) -> int:
	var current_amount := int(_ammo.get(weapon_name, 0))
	if current_amount < 0:
		return current_amount
	var add_amount := amount
	if add_amount < 0:
		add_amount = ammo_pack_size(weapon_name)
	if add_amount <= 0:
		return current_amount
	_ammo[weapon_name] = current_amount + add_amount
	return int(_ammo[weapon_name])


func inventory_snapshot() -> Array[Dictionary]:
	var items: Array[Dictionary] = []
	for index in range(WEAPONS.size()):
		var weapon: Dictionary = WEAPONS[index].duplicate()
		var weapon_name := str(weapon["name"])
		weapon["ammo"] = int(_ammo.get(weapon_name, -1))
		weapon["selected"] = index == _selected_index
		items.append(weapon)
	return items


func snapshot() -> Dictionary:
	return {
		"name": current_name(),
		"ammo": current_ammo(),
		"weapons": inventory_snapshot(),
	}
