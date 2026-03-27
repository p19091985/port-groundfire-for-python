from __future__ import annotations

PLAYER_COLOURS = (
    (239, 88, 83),
    (74, 163, 255),
    (255, 198, 64),
    (124, 201, 92),
    (204, 118, 255),
    (255, 146, 77),
    (80, 224, 208),
    (245, 109, 164),
)

WEAPON_ORDER = ("shell", "missile", "machinegun", "mirv", "nuke")
WEAPON_SPECS = {
    "shell": {
        "cost": 0,
        "bundle": 0,
        "projectile_count": 1,
        "speed": 6.0,
        "gravity": 5.0,
        "ttl_ticks": 18,
        "blast_radius": 0.45,
        "blast_damage": 90.0,
        "spread": 0.0,
        "size": 0.06,
        "entity_type": "shell",
    },
    "missile": {
        "cost": 25,
        "bundle": 1,
        "projectile_count": 1,
        "speed": 7.0,
        "gravity": 3.5,
        "ttl_ticks": 28,
        "blast_radius": 0.52,
        "blast_damage": 115.0,
        "spread": 0.0,
        "size": 0.08,
        "entity_type": "missile",
    },
    "machinegun": {
        "cost": 20,
        "bundle": 3,
        "projectile_count": 3,
        "speed": 8.5,
        "gravity": 4.0,
        "ttl_ticks": 14,
        "blast_radius": 0.22,
        "blast_damage": 35.0,
        "spread": 3.5,
        "size": 0.04,
        "entity_type": "machinegun",
    },
    "mirv": {
        "cost": 35,
        "bundle": 1,
        "projectile_count": 3,
        "speed": 6.2,
        "gravity": 5.0,
        "ttl_ticks": 20,
        "blast_radius": 0.34,
        "blast_damage": 55.0,
        "spread": 16.0,
        "size": 0.06,
        "entity_type": "mirv",
    },
    "nuke": {
        "cost": 60,
        "bundle": 1,
        "projectile_count": 1,
        "speed": 5.0,
        "gravity": 3.5,
        "ttl_ticks": 26,
        "blast_radius": 0.95,
        "blast_damage": 185.0,
        "spread": 0.0,
        "size": 0.1,
        "entity_type": "nuke",
    },
}

PROJECTILE_ENTITY_TYPES = frozenset(spec["entity_type"] for spec in WEAPON_SPECS.values())

INITIAL_MONEY = 50
TANK_SIZE = 0.25
TANK_MAX_HEALTH = 100.0
TANK_MAX_FUEL = 1.0
TANK_MOVE_STEP = 0.15
TANK_FUEL_STEP = 0.015
TANK_GUN_STEP = 3.0

__all__ = [
    "INITIAL_MONEY",
    "PLAYER_COLOURS",
    "PROJECTILE_ENTITY_TYPES",
    "TANK_FUEL_STEP",
    "TANK_GUN_STEP",
    "TANK_MAX_FUEL",
    "TANK_MAX_HEALTH",
    "TANK_MOVE_STEP",
    "TANK_SIZE",
    "WEAPON_ORDER",
    "WEAPON_SPECS",
]
