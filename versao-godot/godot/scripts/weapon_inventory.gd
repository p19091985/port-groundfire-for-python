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
const LIMITED_WEAPON_INITIAL_STOCK := 0
const ROUND_STARTING_COOLDOWN_ADVANCE := 2.0
const SHELL_DAMAGE := 40
const SHELL_COOLDOWN := 4.0
const MACHINE_GUN_ROUND_AMMO := 50
const MACHINE_GUN_VOLLEY := 5
const MACHINE_GUN_COOLDOWN := 0.1
const MACHINE_GUN_SHOP_PACK := 50
const MACHINE_GUN_TRACER_GRAVITY := 190.0
const MACHINE_GUN_CLASSIC_POWER := 25.0
const MIRV_ROUND_AMMO := 1
const MIRV_DAMAGE := 30
const MIRV_FRAGMENTS := 5
const MIRV_SPREAD := 0.2
const MIRV_MIN_FRAGMENT_SPREAD_SPEED := 0.0
const MIRV_SHOP_PACK := 1
const MIRV_COOLDOWN := 7.5
const MISSILE_SHOP_PACK := 5
const MISSILE_DAMAGE := 40
const MISSILE_CLASSIC_SPEED := 9.0
const MISSILE_COOLDOWN := 5.0
const NUKE_SHOP_PACK := 1
const NUKE_DAMAGE := 90
const NUKE_COOLDOWN := 10.0
const ROLLING_MINES_SHOP_PACK := 5
const AIRSTRIKE_SHOP_PACK := 2
const DEATHS_HEAD_SHOP_PACK := 1
const HOVER_COIL_SHOP_PACK := 2
const CORBOMITE_SHOP_PACK := 3

const WEAPONS := [
	{"name": SHELL, "damage": SHELL_DAMAGE, "blast": 48.0, "ammo": -1, "speed": 4.2, "cost": 0, "kind": "shell", "cooldown": SHELL_COOLDOWN},
	{"name": MACHINE_GUN, "damage": 2, "blast": 0.0, "ammo": LIMITED_WEAPON_INITIAL_STOCK, "shop_pack": MACHINE_GUN_SHOP_PACK, "speed": 5.8, "cost": 50, "kind": "machine_gun", "volley": MACHINE_GUN_VOLLEY, "cooldown": MACHINE_GUN_COOLDOWN, "direct_damage": true, "tracer_gravity": MACHINE_GUN_TRACER_GRAVITY, "launch_power": MACHINE_GUN_CLASSIC_POWER},
	{"name": MIRV, "damage": MIRV_DAMAGE, "blast": 34.0, "ammo": LIMITED_WEAPON_INITIAL_STOCK, "shop_pack": MIRV_SHOP_PACK, "speed": 4.0, "cost": 50, "kind": "mirv", "fragments": MIRV_FRAGMENTS, "spread": MIRV_SPREAD, "min_fragment_spread_speed": MIRV_MIN_FRAGMENT_SPREAD_SPEED, "cooldown": MIRV_COOLDOWN},
	{"name": MISSILE, "damage": MISSILE_DAMAGE, "blast": 46.0, "ammo": LIMITED_WEAPON_INITIAL_STOCK, "shop_pack": MISSILE_SHOP_PACK, "speed": 4.8, "cost": 50, "kind": "missile", "fuel": 3.0, "steer_sensitivity": 300.0, "powered_speed": MISSILE_CLASSIC_SPEED, "cooldown": MISSILE_COOLDOWN},
	{"name": NUKE, "damage": NUKE_DAMAGE, "blast": 96.0, "ammo": LIMITED_WEAPON_INITIAL_STOCK, "shop_pack": NUKE_SHOP_PACK, "speed": 3.6, "cost": 50, "kind": "nuke", "white_out": true, "cooldown": NUKE_COOLDOWN},
	{"name": ROLLING_MINES, "damage": 30, "blast": 36.0, "ammo": 0, "shop_pack": ROLLING_MINES_SHOP_PACK, "speed": 4.0, "cost": 50, "kind": "rolling_mine"},
	{"name": AIRSTRIKE, "damage": 40, "blast": 40.0, "ammo": 0, "shop_pack": AIRSTRIKE_SHOP_PACK, "speed": 4.5, "cost": 100, "kind": "airstrike"},
	{"name": DEATHS_HEAD, "damage": 25, "blast": 30.0, "ammo": 0, "shop_pack": DEATHS_HEAD_SHOP_PACK, "speed": 3.8, "cost": 200, "kind": "deaths_head", "fragments": 8, "spread": 0.35},
	{"name": HOVER_COIL, "damage": 0, "blast": 0.0, "ammo": 0, "shop_pack": HOVER_COIL_SHOP_PACK, "speed": 4.0, "cost": 150, "kind": "hover_coil"},
	{"name": CORBOMITE, "damage": 0, "blast": 0.0, "ammo": 0, "shop_pack": CORBOMITE_SHOP_PACK, "speed": 0.0, "cost": 20, "kind": "corbomite"},
]

var _selected_index := 0
var _ammo: Dictionary = {}
var _stock: Dictionary = {}
var _cooldowns: Dictionary = {}


func _init() -> void:
	_reset_initial_stock()
	_reset_initial_cooldowns()
	reset_round_ammo()


func _reset_initial_stock() -> void:
	_stock.clear()
	for weapon in WEAPONS:
		var weapon_name := str(weapon["name"])
		_stock[weapon_name] = int(weapon["ammo"])


func _reset_initial_cooldowns() -> void:
	_cooldowns.clear()
	for weapon in WEAPONS:
		_cooldowns[str(weapon["name"])] = 0.0


func reset_round_ammo() -> void:
	_ammo.clear()
	for weapon in WEAPONS:
		var weapon_name := str(weapon["name"])
		_ammo[weapon_name] = int(_stock.get(weapon_name, weapon["ammo"]))
	_selected_index = 0
	_arm_current_cooldown(-ROUND_STARTING_COOLDOWN_ADVANCE)


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


func current_cooldown() -> float:
	return float(_cooldowns.get(current_name(), 0.0))


func is_current_ready() -> bool:
	return current_cooldown() <= 0.0


func update_current_cooldown(delta: float) -> void:
	var weapon_name := current_name()
	var cooldown := float(_cooldowns.get(weapon_name, 0.0))
	if cooldown <= 0.0:
		return
	_cooldowns[weapon_name] = max(0.0, cooldown - max(0.0, delta))


func ammo_for(weapon_name: String) -> int:
	return int(_ammo.get(weapon_name, 0))


func stock_for(weapon_name: String) -> int:
	return int(_stock.get(weapon_name, 0))


func weapon_by_name(weapon_name: String) -> Dictionary:
	for weapon in WEAPONS:
		if str(weapon["name"]) == weapon_name:
			return weapon
	return WEAPONS[0]


func select_by_name(weapon_name: String, arm_cooldown := true) -> bool:
	for index in range(WEAPONS.size()):
		if str(WEAPONS[index]["name"]) == weapon_name and int(_ammo.get(weapon_name, 0)) != 0:
			_selected_index = index
			if arm_cooldown:
				_arm_current_cooldown()
			return true
	return false


func has_ammo(weapon_name: String) -> bool:
	return ammo_for(weapon_name) != 0


func cycle(direction := 1) -> String:
	for _attempt in range(WEAPONS.size()):
		_selected_index = wrapi(_selected_index + direction, 0, WEAPONS.size())
		if current_ammo() != 0:
			_arm_current_cooldown()
			return current_name()
	return current_name()


func select_shell(arm_cooldown := true) -> void:
	_selected_index = 0
	if arm_cooldown:
		_arm_current_cooldown()


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
	var actual_spend: int = min(spend, ammo)
	_ammo[weapon_name] = max(0, ammo - actual_spend)
	var stock := int(_stock.get(weapon_name, ammo))
	if stock > 0:
		_stock[weapon_name] = max(0, stock - actual_spend)
	if int(_ammo[weapon_name]) == 0 and weapon_name == current_name():
		select_shell()
	return true


func _arm_current_cooldown(offset := 0.0) -> void:
	var weapon := current()
	var weapon_name := str(weapon["name"])
	var cooldown: float = max(0.0, float(weapon.get("cooldown", 0.0)) + offset)
	_cooldowns[weapon_name] = cooldown


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
	var current_amount := int(_stock.get(weapon_name, 0))
	if current_amount < 0:
		return current_amount
	var add_amount := amount
	if add_amount < 0:
		add_amount = ammo_pack_size(weapon_name)
	if add_amount <= 0:
		return current_amount
	_stock[weapon_name] = current_amount + add_amount
	return int(_stock[weapon_name])


func inventory_snapshot() -> Array[Dictionary]:
	var items: Array[Dictionary] = []
	for index in range(WEAPONS.size()):
		var weapon: Dictionary = WEAPONS[index].duplicate()
		var weapon_name := str(weapon["name"])
		weapon["ammo"] = int(_ammo.get(weapon_name, -1))
		weapon["stock"] = int(_stock.get(weapon_name, weapon["ammo"]))
		weapon["ready"] = float(_cooldowns.get(weapon_name, 0.0)) <= 0.0
		weapon["cooldown_remaining"] = float(_cooldowns.get(weapon_name, 0.0))
		weapon["selected"] = index == _selected_index
		items.append(weapon)
	return items


func snapshot() -> Dictionary:
	return {
		"name": current_name(),
		"ammo": current_ammo(),
		"stock": stock_for(current_name()),
		"ready": is_current_ready(),
		"cooldown": current_cooldown(),
		"weapons": inventory_snapshot(),
	}
