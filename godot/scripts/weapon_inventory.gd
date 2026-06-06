extends RefCounted

const SHELL := "Shell"
const MACHINE_GUN := "Machine Gun"
const MIRV := "MIRV"
const MISSILE := "Missile"
const NUKE := "Nuke"
const ROLLING_MINES := "Rolling Mines"
const AIRSTRIKE := "Airstrike"
const DEATHS_HEAD := "Death's Head"
const HOVER_COIL := "Hover Coil"
const CORBOMITE := "Corbomite"

const DEFAULT_AMMO_SPEND := 1
const MACHINE_GUN_ROUND_AMMO := 50
const MACHINE_GUN_VOLLEY := 5
const MACHINE_GUN_COOLDOWN := 0.1
const MACHINE_GUN_SHOP_PACK := 50
const MACHINE_GUN_TRACER_GRAVITY := 190.0
const MACHINE_GUN_CLASSIC_POWER := 25.0
const MIRV_ROUND_AMMO := 3
const MIRV_FRAGMENTS := 5
const MIRV_SPREAD := 0.2
const MIRV_MIN_FRAGMENT_SPREAD_SPEED := 0.0
const MIRV_SHOP_PACK := 1
const MISSILE_SHOP_PACK := 5
const MISSILE_CLASSIC_SPEED := 9.0
const NUKE_SHOP_PACK := 1
const ROLLING_MINES_SHOP_PACK := 5
const AIRSTRIKE_SHOP_PACK := 2
const DEATHS_HEAD_SHOP_PACK := 1
const HOVER_COIL_SHOP_PACK := 2
const CORBOMITE_SHOP_PACK := 3

const WEAPONS := [
	{"name": SHELL, "damage": 40, "blast": 48.0, "ammo": -1, "speed": 4.2, "cost": 0, "kind": "shell"},
	{"name": MACHINE_GUN, "damage": 2, "blast": 0.0, "ammo": MACHINE_GUN_ROUND_AMMO, "shop_pack": MACHINE_GUN_SHOP_PACK, "speed": 5.8, "cost": 50, "kind": "machine_gun", "volley": MACHINE_GUN_VOLLEY, "cooldown": MACHINE_GUN_COOLDOWN, "direct_damage": true, "tracer_gravity": MACHINE_GUN_TRACER_GRAVITY, "launch_power": MACHINE_GUN_CLASSIC_POWER},
	{"name": MIRV, "damage": 22, "blast": 34.0, "ammo": MIRV_ROUND_AMMO, "shop_pack": MIRV_SHOP_PACK, "speed": 4.0, "cost": 50, "kind": "mirv", "fragments": MIRV_FRAGMENTS, "spread": MIRV_SPREAD, "min_fragment_spread_speed": MIRV_MIN_FRAGMENT_SPREAD_SPEED},
	{"name": MISSILE, "damage": 40, "blast": 46.0, "ammo": 4, "shop_pack": MISSILE_SHOP_PACK, "speed": 4.8, "cost": 50, "kind": "missile", "fuel": 3.0, "steer_sensitivity": 300.0, "powered_speed": MISSILE_CLASSIC_SPEED},
	{"name": NUKE, "damage": 90, "blast": 96.0, "ammo": 1, "shop_pack": NUKE_SHOP_PACK, "speed": 3.6, "cost": 50, "kind": "nuke", "white_out": true},
	{"name": ROLLING_MINES, "damage": 30, "blast": 36.0, "ammo": 5, "shop_pack": ROLLING_MINES_SHOP_PACK, "speed": 4.0, "cost": 50, "kind": "rolling_mine"},
	{"name": AIRSTRIKE, "damage": 40, "blast": 40.0, "ammo": 2, "shop_pack": AIRSTRIKE_SHOP_PACK, "speed": 4.5, "cost": 100, "kind": "airstrike"},
	{"name": DEATHS_HEAD, "damage": 25, "blast": 30.0, "ammo": 1, "shop_pack": DEATHS_HEAD_SHOP_PACK, "speed": 3.8, "cost": 200, "kind": "deaths_head", "fragments": 8, "spread": 0.35},
	{"name": HOVER_COIL, "damage": 0, "blast": 0.0, "ammo": 2, "shop_pack": HOVER_COIL_SHOP_PACK, "speed": 4.0, "cost": 150, "kind": "hover_coil"},
	{"name": CORBOMITE, "damage": 0, "blast": 0.0, "ammo": 3, "shop_pack": CORBOMITE_SHOP_PACK, "speed": 0.0, "cost": 20, "kind": "corbomite"},
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


func select_shell() -> void:
	_selected_index = 0


func consume_current() -> bool:
	var spend: int = max(DEFAULT_AMMO_SPEND, int(current().get("volley", DEFAULT_AMMO_SPEND)))
	return consume_current_amount(spend)


func consume_current_amount(amount := DEFAULT_AMMO_SPEND) -> bool:
	return consume_ammo(current_name(), amount)


func consume_ammo(weapon_name: String, amount := DEFAULT_AMMO_SPEND) -> bool:
	var ammo := int(_ammo.get(weapon_name, 0))
	if ammo == -1:
		return true
	if ammo <= 0:
		if weapon_name == current_name():
			select_shell()
		return false
	var spend: int = max(DEFAULT_AMMO_SPEND, amount)
	_ammo[weapon_name] = max(0, ammo - min(spend, ammo))
	if int(_ammo[weapon_name]) == 0 and weapon_name == current_name():
		select_shell()
	return true


func weapon_cost(weapon_name: String) -> int:
	for weapon in WEAPONS:
		if str(weapon["name"]) == weapon_name:
			return int(weapon.get("cost", 0))
	return 0


func ammo_pack_size(weapon_name: String) -> int:
	for weapon in WEAPONS:
		if str(weapon["name"]) == weapon_name:
			return max(0, int(weapon.get("shop_pack", weapon.get("ammo", 0))))
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
