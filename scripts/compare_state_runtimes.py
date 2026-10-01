#!/usr/bin/env python3
"""Compare real tank, reward and shop state transitions in both editions."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from compare_classic_replay import ReplayDifference, compare

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "tests/fixtures/experience_parity/states.json"
MAX_GODOT_BATCH_TICKS = 20_000
sys.path.insert(0, str(ROOT / "versao-python"))


def python_trace(spec):
    # Lazy imports keep pygame out of pytest's fake-module collection phase.
    from src.aiplayer import AIPlayer
    from src.common import GameState
    from src.inifile import ReadIniFile
    from src.player import Player
    from src.shopmenu import ShopMenu
    from src.tank import Tank
    from src.weapons_impl import MachineGunWeapon, MirvWeapon, MissileWeapon, NukeWeapon, ShellWeapon

    class Inputs(Player):
        buttons = ()

        def update(self, time=0.0):
            pass

        def get_command(self, command, _time=None):
            return command in self.buttons

    class Context:
        def get_settings(self):
            return settings

        def get_players(self):
            return players + [None] * (8 - len(players))

        def get_font(self):
            return None

        get_interface = get_font
        get_graphics = get_font
        get_ui = get_font
        get_sound = get_font

        def get_time(self):
            return 0.0

        def record_tank_death(self):
            pass

    settings = ReadIniFile(str(ROOT / "versao-python/conf/options.ini"))
    for weapon in (ShellWeapon, MachineGunWeapon, MirvWeapon, MissileWeapon, NukeWeapon):
        weapon.read_settings(settings)
    game = Context()
    players = [
        (AIPlayer if i in spec.get("computers", []) else Inputs)(game, i, f"Player {i + 1}", (255, 255, 255))
        for i in range(spec.get("players", 2))
    ]
    kind = spec["kind"]
    frames = []
    if kind == "gun":
        tank = players[0].get_tank()
        buttons = []
        for tick in range(spec["ticks"] + 1):
            for command in spec["commands"]:
                if command["tick"] == tick:
                    buttons = command["buttons"]
            players[0].buttons = buttons
            if tick:
                tank.update_gun(spec["step"])
            frames.append(
                {
                    "tick": tick,
                    "angle": tank._gun_angle,
                    "power": tank._gun_power,
                    "angle_speed": tank._gun_angle_change_speed,
                    "power_speed": tank._gun_power_change_speed,
                }
            )
    elif kind == "damage":
        tank = players[0].get_tank()
        for amount in spec["damage"]:
            killed = tank.do_damage(amount)
            frames.append({"killed": killed, "health": tank._health, "alive": tank.alive()})
    elif kind == "weapons":
        from src.gamesimulation import GameSimulationController
        from src.machinegunround import MachineGunRound
        from src.mirv import Mirv
        from src.missile import Missile
        from src.shell import Shell

        names = ["Shell", "Machine Gun", "MIRV", "Missile", "Nuke"]
        shots = [[] for _ in players]
        game.GameState = GameState
        game._game_state = GameState.ROUND_STARTING
        game._new_state = GameState.CURRENT_STATE
        game._state_countdown = 2.0
        game._landscape = None
        game.get_landscape = lambda: None
        game.get_game_state = lambda: game._game_state
        game.pygame_module = SimpleNamespace(K_ESCAPE=27)
        game.get_interface = lambda: SimpleNamespace(get_key=lambda _key: False)

        def spawned(entity):
            if isinstance(entity, (Shell, Mirv, Missile, MachineGunRound)):
                owner = players.index(entity._player)
                shots[owner].append(names[players[owner].get_tank()._selected_weapon])

        game.add_entity = spawned  # Observe launches; do not advance their physics in a weapon-state replay.
        game._entity_list = [p.get_tank() for p in players]
        for player in players:
            for index, amount in enumerate(spec.get("ammo", [0, 0, 0, 0]), 1):
                player.get_tank().get_weapon(index).add_amount(amount)
            player.get_tank().do_pre_round()
        for tick in range(spec["ticks"] + 1):
            game.get_time = lambda: tick / 60.0
            for command in spec["commands"]:
                if command["tick"] == tick:
                    players[command.get("player", 0)].buttons = command["buttons"]
            if tick:
                GameSimulationController().simulate_round_step(game, 1.0 / 60.0)
                if game._new_state != GameState.CURRENT_STATE:
                    game._game_state = game._new_state
                    game._new_state = GameState.CURRENT_STATE
            frames.append(
                {
                    "tick": tick,
                    "starting": game._game_state == GameState.ROUND_STARTING,
                    "tanks": [
                        {
                            "selected": names[p.get_tank()._selected_weapon],
                            "cooldown": p.get_tank().get_weapon(p.get_tank()._selected_weapon)._cooldown,
                            "ready": p.get_tank().get_weapon(p.get_tank()._selected_weapon).ready_to_fire(),
                            "ammo": [p.get_tank().get_weapon(i).get_ammo() for i in range(1, 5)],
                            "shots": list(shots[i]),
                        }
                        for i, p in enumerate(players)
                    ],
                }
            )
    elif kind == "terrain":
        from src.landscape import Landscape

        landscape = Landscape(settings, spec["seed"] / 1000.0)
        for operation in spec["operations"]:
            if "hole" in operation:
                landscape.make_hole(*operation["hole"])
            if "drop" in operation:
                landscape.drop_terrain(operation["drop"])
            for _ in range(operation.get("ticks", 0)):
                landscape.update(1.0 / 60.0)
            slices = []
            for chunks in landscape._land_chunks:
                slices.append(
                    [
                        {
                            "top": [c.max_height_1, c.max_height_2],
                            "bottom": [c.min_height_1, c.min_height_2],
                            "linked": c.linked_to_next,
                            "motion": {
                                "falling": c.falling_state,
                                "wait": c.wait_for_fall_time,
                                "speed": c.falling_speed,
                            }
                            if i == 0 or not chunks[i - 1].linked_to_next
                            else None,
                        }
                        for i, c in enumerate(chunks)
                    ]
                )
            frames.append({"terrain": slices})
    elif kind == "explosions":
        from src.blast import Blast
        from src.gamesession import GameSessionController
        from src.landscape import Landscape
        from src.soundentity import SoundEntity

        game._players = game.get_players()
        game._landscape = Landscape(settings, spec["seed"] / 1000.0)
        game.add_entity = lambda _entity: None
        game.queue_network_event = lambda *args, **kwargs: None
        session = GameSessionController(
            human_player_factory=None,
            ai_player_factory=None,
            landscape_factory=None,
            quake_factory=None,
            blast_factory=Blast,
            sound_entity_factory=SoundEntity,
        )
        for player, initial in zip(players, spec["initial"]):
            tank = player.get_tank()
            tank._x, tank._y = initial["position"]
            tank._health = initial.get("health", 100.0)
        for blast in spec["blasts"]:
            session.explosion(
                game,
                *blast["position"],
                blast["radius"],
                blast["damage"],
                blast.get("hit", -1),
                1,
                False,
                players[blast["owner"]],
            )
            frames.append(
                {
                    "tanks": [
                        {
                            "health": p.get_tank()._health,
                            "alive": p.get_tank().alive(),
                            "position": list(p.get_tank().get_position()),
                            "defeated": [players.index(victim) for victim in p._defeated_players],
                        }
                        for p in players
                    ]
                }
            )
    elif kind == "rewards":
        for index, initial in enumerate(spec["initial"]):
            player = players[index]
            player._score = initial["score"]
            player.set_money(initial["money"])
            player.set_leader(initial["leader"])
            player.get_tank()._state = Tank.TANK_ALIVE if initial["alive"] else Tank.TANK_DEAD
        for attacker, victim in spec["defeats"]:
            players[attacker].defeat(players[victim])
        for player in players:
            player.end_round()
        frames = [{"score": player.get_score(), "money": player.get_money()} for player in players]
    elif kind == "phases":
        from src.gamesession import GameSessionController
        from src.gamesimulation import GameSimulationController

        session = GameSessionController(
            human_player_factory=None,
            ai_player_factory=None,
            landscape_factory=None,
            quake_factory=None,
            blast_factory=None,
            sound_entity_factory=None,
        )
        simulation = GameSimulationController()
        game._players = players
        game._number_of_players = len(players)
        game._number_of_active_tanks = len(players)
        game._entity_list = []  # Phase replay isolates timing/rewards from world geometry.
        game._landscape = None
        game._current_round = 1
        game._game_state = GameState.ROUND_STARTING
        game._new_state = GameState.CURRENT_STATE
        game._state_countdown = 2.0
        game.pygame_module = SimpleNamespace(K_ESCAPE=27)
        game.get_interface = lambda: SimpleNamespace(get_key=lambda _key: False)
        game.record_tank_death = lambda: session.record_tank_death(game)
        game._end_round = lambda: session.end_round(game)
        game.queue_network_event = lambda *args, **kwargs: None
        names = {
            GameState.ROUND_STARTING: "round_starting",
            GameState.ROUND_IN_ACTION: "aim",
            GameState.ROUND_FINISHING: "round_finishing",
            GameState.ROUND_SCORE: "score",
        }
        for tick in range(spec["ticks"] + 1):
            if tick and game._game_state != GameState.ROUND_SCORE:
                simulation.simulate_round_step(game, spec["step"])
                if game._new_state != GameState.CURRENT_STATE:
                    game._game_state = game._new_state
                    game._new_state = GameState.CURRENT_STATE
            for death in spec["deaths"]:
                if death["tick"] == tick:
                    victim, attacker = players[death["victim"]], players[death["attacker"]]
                    if victim.get_tank().do_damage(101.0):
                        attacker.defeat(victim)
                    if game._new_state != GameState.CURRENT_STATE:
                        game._game_state = game._new_state
                        game._new_state = GameState.CURRENT_STATE
            frames.append(
                {
                    "tick": tick,
                    "phase": names[game._game_state],
                    "players": [
                        {"alive": player.get_tank().alive(), "score": player.get_score(), "money": player.get_money()}
                        for player in players
                    ],
                }
            )
    elif kind == "score":
        from unittest.mock import patch

        from src.scoremenu import ScoreMenu

        game.are_human_players = lambda: True
        game.get_current_round = lambda: spec["round"]
        game.get_num_of_rounds = lambda: 5
        for player, initial in zip(players, spec["initial"]):
            player._score = initial["score"]
            player.set_leader(initial["leader"])
        menu = ScoreMenu(game)
        phase = "score"
        with patch("pygame.key.get_pressed", return_value={32: False, 13: False}):
            for tick in range(spec["ticks"] + 1):
                for command in spec["commands"]:
                    if command["tick"] == tick:
                        players[command["player"]].buttons = command["buttons"]
                if tick:
                    state = menu.update(spec["step"])
                    phase = {
                        GameState.CURRENT_STATE: "score",
                        GameState.SHOP_MENU: "shop",
                        GameState.WINNER_MENU: "winner",
                    }[state]
                frames.append({"tick": tick, "phase": phase, "leaders": [player.is_leader() for player in players]})
                if phase != "score":
                    break
    elif kind in ("world", "motion", "combat", "ai"):
        from src.blast import Blast
        from src.gamesession import GameSessionController
        from src.landscape import Landscape
        from src.quake import Quake
        from src.soundentity import SoundEntity

        game._players = players
        game._number_of_players = len(players)
        game._current_round = 0
        game._entity_list = [p.get_tank() for p in players]
        game.get_landscape = lambda: game._landscape
        game.get_clock = lambda: SimpleNamespace(sample_now=lambda: spec["seed"] / 1000.0, reset=lambda _seed: None)
        game.ensure_registered_entities = lambda: None
        game.add_entity = lambda entity: game._entity_list.append(entity)
        game.remove_entity = lambda entity: game._entity_list.remove(entity)
        game.queue_network_event = lambda *args, **kwargs: None
        session = GameSessionController(
            human_player_factory=None,
            ai_player_factory=None,
            landscape_factory=Landscape,
            quake_factory=Quake,
            blast_factory=Blast,
            sound_entity_factory=SoundEntity,
        )
        Quake.read_settings(settings)
        session.start_round(game)
        if kind == "ai":
            game.GameState = GameState
            game._game_state = GameState.ROUND_IN_ACTION
            game.get_game_state = lambda: game._game_state
            bot = players[spec["computers"][0]]
            bot.get_tank().get_weapon(0)._cooldown = 0.0
            for event in spec["events"]:
                if "move" in event:
                    index, x, y = event["move"]
                    players[index].get_tank()._x, players[index].get_tank()._y = x, y
                if "dead" in event:
                    players[event["dead"]].get_tank()._state = Tank.TANK_DEAD
                if "fired" in event:
                    bot.record_fired()
                if "shot" in event:
                    bot.record_shot(*event["shot"])
                if "new_round" in event:
                    bot.new_round()
                if "phase" in event:
                    game._game_state = getattr(GameState, event["phase"])
                bot.update()
                frames.append(ai_snapshot(bot, players))
            return {"id": spec["id"], "frames": frames}
        if kind == "combat":
            from unittest.mock import patch

            from src.gameflow import GameFlowController
            from src.gamesimulation import GameSimulationController
            from src.machinegunround import MachineGunRound
            from src.mirv import Mirv
            from src.missile import Missile
            from src.scoremenu import ScoreMenu
            from src.shell import Shell
            from src.winnermenu import WinnerMenu

            game._players = game.get_players()
            game.GameState = GameState
            game._game_state = GameState.ROUND_STARTING
            game._new_state = GameState.CURRENT_STATE
            game._state_countdown = 2.0
            game.get_game_state = lambda: game._game_state
            game.pygame_module = SimpleNamespace(K_ESCAPE=27)
            game.get_interface = lambda: SimpleNamespace(get_key=lambda _key: False, offset_viewport=lambda *args: None)
            game.record_tank_death = lambda: session.record_tank_death(game)
            game._end_round = lambda: session.end_round(game)
            game.explosion = lambda *args: session.explosion(game, *args)
            game._current_menu = None
            game.get_current_menu = lambda: game._current_menu
            game.get_current_round = lambda: game._current_round
            game.get_num_of_rounds = lambda: spec.get("total_rounds", 5)
            game.get_num_of_players = lambda: len(players)
            game.are_human_players = lambda: len(spec.get("computers", [])) < len(players)
            game._start_round = lambda: session.start_round(game)
            game.get_clock = lambda: SimpleNamespace(
                sample_now=lambda: (spec["seed"] + 17 * (game._current_round - 1)) / 1000.0,
                reset=lambda _seed: None,
            )
            game.get_interface = lambda: SimpleNamespace(
                get_key=lambda _key: False, offset_viewport=lambda *args: None, enable_mouse=lambda _value: None
            )
            flow = GameFlowController(
                menu_factories={
                    GameState.ROUND_SCORE: ScoreMenu,
                    GameState.SHOP_MENU: ShopMenu,
                    GameState.WINNER_MENU: WinnerMenu,
                }
            )
            round_tick = 0
            shop_ticks = 0
            audio_events = []

            class AudioProbe:
                # Observe actual sound construction; do not change weapon/entity rules.
                class SoundSource:
                    def __init__(self, _sound, sound_id, looping):
                        if not looping:
                            audio_events.append(sound_id)

                    def is_source_playing(self):
                        return False

            if spec.get("audio"):
                game.get_sound = lambda: AudioProbe
            for player, fuel in zip(players, spec.get("initial_fuel", [])):
                player.get_tank()._fuel = fuel
                player.get_tank()._total_fuel = fuel
            if "quake_countdown" in spec:
                for entity in game._entity_list:
                    if isinstance(entity, Quake):
                        entity._earthquake_countdown = spec["quake_countdown"]
            names = ["Shell", "Machine Gun", "MIRV", "Missile", "Nuke"]
            for player, money in zip(players, spec.get("initial_money", [])):
                player.set_money(money)
            for player, loadout in zip(players, spec.get("loadouts", [])):
                tank = player.get_tank()
                for index, ammo in enumerate(loadout["ammo"], 1):
                    tank.get_weapon(index).add_amount(ammo)
                tank.get_weapon(Tank.MACHINEGUN).set_ammo_for_round()
                tank.get_weapon(Tank.MISSILES).set_ammo_for_round()
                tank._selected_weapon = names.index(loadout["selected"])
                tank.get_weapon(tank._selected_weapon).select()
            for player, initial in zip(players, spec.get("initial_tanks", [])):
                tank = player.get_tank()
                if "x" in initial:
                    tank.set_position_on_ground(initial["x"])
                tank._gun_angle = float(initial.get("angle", tank._gun_angle))
                tank._gun_power = float(initial.get("power", tank._gun_power))
            phases = {
                GameState.ROUND_STARTING: "round_starting",
                GameState.ROUND_IN_ACTION: "aim",
                GameState.ROUND_FINISHING: "round_finishing",
                GameState.ROUND_SCORE: "score",
                GameState.SHOP_MENU: "shop",
                GameState.WINNER_MENU: "winner",
            }
            for tick in range(spec["ticks"] + 1):
                game.get_time = lambda: round_tick / 60.0
                audio_events.clear()
                for command in spec["commands"]:
                    if command["tick"] == tick:
                        players[command.get("player", 0)].buttons = command["buttons"]
                if spec.get("complete_match") and flow.is_round_state(game._game_state):
                    for command in spec["round_commands"]:
                        if command["tick"] == round_tick + 1:
                            players[command.get("player", 0)].buttons = command["buttons"]
                if spec.get("cycle"):
                    if game._game_state == GameState.ROUND_SCORE:
                        for player in players:
                            player.buttons = [0]
                    elif game._game_state == GameState.SHOP_MENU:
                        shop_ticks += 1
                        for player in players:
                            player.buttons = (
                                [0] if shop_ticks == 30 or shop_ticks >= 60 else [9] if shop_ticks == 45 else []
                            )
                if tick:
                    if flow.is_round_state(game._game_state):
                        round_tick += 1
                        GameSimulationController().simulate_round_step(game, 1.0 / 60.0)
                    else:
                        with patch("pygame.key.get_pressed", return_value={32: False, 13: False}):
                            game._new_state = flow.update_menu(game, 1.0 / 60.0)
                    if game._new_state != GameState.CURRENT_STATE:
                        previous_state = game._game_state
                        game._game_state = game._new_state
                        game._new_state = GameState.CURRENT_STATE
                        if spec.get("cycle"):
                            flow.enter_state(game, game._game_state, previous_state)
                            if game._game_state == GameState.ROUND_STARTING:
                                round_tick = 0
                                shop_ticks = 0
                                for player in players:
                                    player.buttons = []
                frames.append(
                    {
                        "tick": tick,
                        "phase": phases[game._game_state],
                        "tanks": [
                            {
                                "position": list(p.get_tank().get_position()),
                                "simulation_position": [p.get_tank()._x, p.get_tank()._y],
                                "body_angle": p.get_tank()._tank_angle,
                                "gun_angle": p.get_tank()._gun_angle,
                                "gun_power": p.get_tank()._gun_power,
                                "fuel": p.get_tank()._fuel,
                                "health": p.get_tank()._health,
                                "alive": p.get_tank().alive(),
                                "score": p.get_score(),
                                "money": p.get_money(),
                                "selected": names[p.get_tank()._selected_weapon],
                                "ammo": [p.get_tank().get_weapon(i).get_ammo() for i in range(1, 5)],
                                "cooldown": p.get_tank().get_weapon(p.get_tank()._selected_weapon)._cooldown,
                            }
                            for p in players
                        ],
                        "projectiles": [
                            {
                                "position": list(e.get_position()),
                                "owner": players.index(e._player),
                                "kind": "machine_gun"
                                if isinstance(e, MachineGunRound)
                                else "mirv"
                                if isinstance(e, Mirv)
                                else "missile"
                                if isinstance(e, Missile)
                                else "nuke"
                                if e._white_out
                                else "shell",
                            }
                            for e in game._entity_list
                            if isinstance(e, (Shell, Mirv, Missile, MachineGunRound))
                        ],
                    }
                )
                if spec.get("computers"):
                    frames[-1]["ai"] = [ai_snapshot(players[i], players) for i in spec["computers"]]
                if tick in spec.get("terrain_ticks", []):
                    frames[-1]["terrain"] = [
                        [{"top": [c.max_height_1, c.max_height_2],
                          "bottom": [c.min_height_1, c.min_height_2], "linked": c.linked_to_next}
                         for c in chunks] for chunks in game._landscape._land_chunks
                    ]
                if spec.get("audio"):
                    # Independent voices starting in one tick have no playback ordering.
                    frames[-1]["audio_one_shots"] = sorted(audio_events)
                    frames[-1]["audio_loops"] = (
                        [2] * sum(isinstance(e, Quake) and e._rumble is not None for e in game._entity_list)
                        + [3] * sum(p.get_tank()._boosting_sound is not None for p in players)
                        + [4] * sum(isinstance(e, Missile) and e._missile_sound is not None for e in game._entity_list)
                        + [8] * sum(p.get_tank().get_weapon(Tank.MACHINEGUN)._gun_source is not None for p in players)
                    )
                if spec.get("cycle"):
                    frames[-1]["round"] = game._current_round
                    frames[-1]["stocks"] = [
                        [p.get_tank().get_weapon(i).get_ammo() for i in range(1, 5)] for p in players
                    ]
                    frames[-1]["shop"] = (
                        [
                            {
                                "selection": game._current_menu._player_select_pos[i],
                                "done": game._current_menu._player_done[i],
                            }
                            for i in range(len(players))
                        ]
                        if game._game_state == GameState.SHOP_MENU
                        else []
                    )
                    if spec.get("complete_match") and game._game_state == GameState.WINNER_MENU:
                        break
                    if not spec.get("complete_match") and game._current_round == 2 and round_tick >= 125:
                        break
                elif game._game_state == GameState.ROUND_SCORE:
                    break
            if spec.get("cycle"):
                validate_cycle_coverage(spec, frames)
            validate_combat_coverage(spec, frames)
            return {"id": spec["id"], "frames": frames}
        if kind == "motion":
            step = 1.0 / spec["step_hz"]
            game.GameState = GameState
            game.get_game_state = lambda: GameState.ROUND_IN_ACTION
            for index, initial in enumerate(spec["initial"]):
                tank = players[index].get_tank()
                tank.set_position_on_ground(initial["x"])
                tank._y += initial.get("height", 0.0)
                tank._tank_angle = initial.get("angle", 0.0)
                tank._on_ground = initial.get("grounded", True)
                tank._fuel = tank._total_fuel = initial.get("fuel", 0.0)
                tank._airbourne_x_vel, tank._airbourne_y_vel = initial.get("velocity", [0.0, 0.0])
                if initial.get("dead", False):
                    tank._state = Tank.TANK_DEAD
            for tick in range(spec["ticks"] + 1):
                for command in spec["commands"]:
                    if command["tick"] == tick:
                        players[command.get("player", 0)].buttons = command["buttons"]
                if tick:
                    game._landscape.update(step)
                    for player in players:
                        player.get_tank().update(step)
                frames.append(
                    {
                        "tick": tick,
                        "tanks": [
                            {
                                "position": list(p.get_tank().get_position()),
                                "velocity": [p.get_tank()._airbourne_x_vel, p.get_tank()._airbourne_y_vel],
                                "angle": p.get_tank()._tank_angle,
                                "grounded": p.get_tank()._on_ground,
                                "fuel": p.get_tank()._fuel,
                                "reserve": p.get_tank()._total_fuel,
                            }
                            for p in players
                        ],
                    }
                )
            return {"id": spec["id"], "frames": frames}
        terrain = [
            [
                {
                    "top": [c.max_height_1, c.max_height_2],
                    "bottom": [c.min_height_1, c.min_height_2],
                    "linked": c.linked_to_next,
                }
                for c in chunks
            ]
            for chunks in game._landscape._land_chunks
        ]
        tanks = []
        for index, player in enumerate(players):
            tank = player.get_tank()
            tank._gun_angle = spec["angles"][index % len(spec["angles"])]
            tank._gun_power = spec["powers"][index % len(spec["powers"])]
            tank._tank_angle = spec.get("tank_angles", [0])[index % len(spec.get("tank_angles", [0]))]
            tanks.append(
                {
                    "position": list(tank.get_position()),
                    "origin": list(tank.gun_launch_position()),
                    "velocity": list(tank.gun_launch_velocity()),
                    "fuel": tank._fuel,
                    "body": [list(point) for point in tank._build_body_points()],
                }
            )
        frames = [
            {
                "terrain": terrain,
                "tanks": tanks,
                "blast_sizes": [
                    ShellWeapon.OPTION_BlastSize,
                    MirvWeapon.OPTION_BlastSize,
                    MissileWeapon.OPTION_BlastSize,
                    NukeWeapon.OPTION_BlastSize,
                ],
                "projectile_gravity": 10.0,
                "tank_gravity": players[0].get_tank()._tank_gravity,
                "tank_move_speed": players[0].get_tank()._movement_speed,
            }
        ]
    elif kind == "winner":
        from src.winnermenu import WinnerMenu

        game.are_human_players = lambda: True
        game.get_num_of_players = lambda: len(players)
        game.delete_players = lambda: None
        for player, score in zip(players, spec["scores"]):
            player._score = score
        menu = WinnerMenu(game)
        for tick in range(spec["ticks"] + 1):
            for command in spec["commands"]:
                if command["tick"] == tick:
                    players[command["player"]].buttons = command["buttons"]
            exited = tick > 0 and menu.update(spec["step"]) == GameState.MAIN_MENU
            frames.append({"tick": tick, "exited": exited, "winners": [p.get_name() for p in menu._winners]})
            if exited:
                break
    elif kind == "shop":
        for index, money in enumerate(spec["money"]):
            players[index].set_money(money)
        shop = ShopMenu(game)
        game.GameState = GameState
        game.get_game_state = lambda: GameState.SHOP_MENU
        game.get_current_menu = lambda: shop
        buttons = [[] for _ in players]
        transition = False
        for tick in range(spec["ticks"] + 1):
            for command in spec["commands"]:
                if command["tick"] == tick:
                    buttons[command["player"]] = command["buttons"]
            for player, held in zip(players, buttons):
                player.buttons = held
            if tick:
                transition = shop.update(spec["step"]) == GameState.ROUND_STARTING
            frames.append(
                {
                    "tick": tick,
                    "next_round": transition,
                    "players": [
                        {
                            "money": player.get_money(),
                            "fuel": player.get_tank().get_total_fuel(),
                            "ammo": [player.get_tank().get_weapon(i).get_ammo() for i in range(1, 5)],
                            "selection": shop._player_select_pos[index],
                            "delay": shop._player_select_delay[index],
                            "done": shop._player_done[index],
                        }
                        for index, player in enumerate(players)
                    ],
                }
            )
            if transition:
                break
    else:
        raise ValueError(f"Unknown scenario kind: {kind}")
    return {"id": spec["id"], "frames": frames}


def ai_snapshot(bot, players):
    return {
        "target": players.index(bot._target_tank.get_player()) if bot._target_tank else -1,
        "target_angle": bot._target_angle,
        "target_power": bot._target_power,
        "target_x": bot._target_last_x_pos,
        "target_y": bot._target_last_y_pos,
        "shots_in_air": bot._shots_in_air,
        "last_x": bot._last_shot_x,
        "last_y": bot._last_shot_y,
        "last_shot": bot._last_shot,
        "ignore_shot": bot._ignore_shot,
        "on_target": bot._on_target,
        "aim_directly": bot._aim_directly,
        "commands": [i for i, held in enumerate(bot._commands) if held],
        "angle": bot.get_tank()._gun_angle,
        "power": bot.get_tank()._gun_power,
        "position_precise": list(bot.get_tank().get_position()),
    }


def validate_cycle_coverage(spec, frames):
    """Fail a truncated or vacuous reference before calling it a cycle test."""
    terminal = "winner" if spec.get("complete_match") else "aim"
    phases = {frame["phase"] for frame in frames}
    if not {"score", "shop", terminal}.issubset(phases) or frames[-1]["phase"] != terminal or frames[-1]["round"] < 2:
        raise ValueError(f"{spec['id']}: incomplete combat/shop/next-round journey")
    if not any(
        before["phase"] == "shop" and after["stocks"][0][0] == before["stocks"][0][0] + 50
        for before, after in zip(frames, frames[1:])
    ):
        raise ValueError(f"{spec['id']}: no successful purchase observed")


def validate_combat_coverage(spec, frames):
    """Reject a combat fixture that never exercises its required launches."""
    seen = {(p["owner"], p["kind"]) for frame in frames for p in frame["projectiles"]}
    for required in spec.get("required_shots", []):
        if (required["owner"], required["kind"]) not in seen:
            raise ValueError(f"{spec['id']}: required projectile not observed: {required}")


def compare_runs(expected: dict, actual: dict) -> list[dict]:
    try:
        if expected.keys() != actual.keys():
            raise ReplayDifference("$: replay fields differ")
        compare(expected["schema"], actual["schema"])
        compare([case["id"] for case in expected["scenarios"]], [case["id"] for case in actual["scenarios"]])
    except (ReplayDifference, KeyError, TypeError) as exc:
        return [{"id": "replay-schema", "status": "failed", "first_difference": str(exc)}]
    results = []
    for reference, candidate in zip(expected["scenarios"], actual["scenarios"]):
        outcome = {"id": reference["id"], "status": "passed"}
        try:
            # The scalar terrain/launch path also keeps post-crater body tilt
            # within the normal bound. No special allowance for health or AI.
            compare(reference, candidate)
        except ReplayDifference as exc:
            outcome.update(status="failed", first_difference=str(exc))
        results.append(outcome)
    return results


def scenario_batches(scenarios: list[dict], max_ticks: int = MAX_GODOT_BATCH_TICKS) -> list[list[dict]]:
    """Keep each real-engine export below the process deadline."""
    batches = []
    current = []
    ticks = 0
    for spec in scenarios:
        weight = max(1, int(spec.get("ticks", 0)))
        if current and ticks + weight > max_ticks:
            batches.append(current)
            current = []
            ticks = 0
        current.append(spec)
        ticks += weight
    if current:
        batches.append(current)
    return batches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot-bin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scenario", action="append", help="Run this exact scenario ID (repeatable); default: all")
    parser.add_argument("--fixtures", type=Path, default=SCENARIOS, help="Scenario JSON (default: parity states)")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    specs = json.loads(args.fixtures.read_text(encoding="utf-8"))
    if args.scenario:
        unknown = set(args.scenario) - {spec["id"] for spec in specs["scenarios"]}
        if unknown:
            parser.error(f"Unknown scenarios: {sorted(unknown)}")
        specs["scenarios"] = [spec for spec in specs["scenarios"] if spec["id"] in args.scenario]
    inputs = args.output.resolve() / "scenario-inputs.json"
    inputs.write_text(json.dumps(specs, indent=2) + "\n", encoding="utf-8")
    expected = {"schema": 1, "scenarios": [python_trace(spec) for spec in specs["scenarios"]]}
    (args.output / "python.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    actual = {"schema": specs["schema"], "scenarios": []}
    logs = []
    for number, batch in enumerate(scenario_batches(specs["scenarios"]), 1):
        batch_inputs = args.output.resolve() / f"godot-input-{number:02d}.json"
        batch_target = args.output.resolve() / f"godot-output-{number:02d}.json"
        batch_inputs.write_text(json.dumps({"schema": specs["schema"], "scenarios": batch}), encoding="utf-8")
        result = subprocess.run(
            [
                str(args.godot_bin.resolve()),
                "--headless",
                "--path",
                str(ROOT / "versao-godot/godot"),
                "--script",
                "res://tests/classic_state_export.gd",
                "--",
                str(batch_inputs),
                str(batch_target),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240,
        )
        log = result.stdout + result.stderr
        logs.append(f"batch {number} ({len(batch)} scenarios):\n{log}")
        if result.returncode or "ERROR:" in log:
            (args.output / "godot.log").write_text("\n".join(logs), encoding="utf-8")
            print(logs[-1])
            return 1
        batch_actual = json.loads(batch_target.read_text(encoding="utf-8"))
        if batch_actual.get("schema") != specs["schema"]:
            raise ValueError(f"Godot batch {number} returned a different schema")
        actual["scenarios"].extend(batch_actual["scenarios"])
    (args.output / "godot.log").write_text("\n".join(logs), encoding="utf-8")
    (args.output / "godot.json").write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    results = compare_runs(expected, actual)
    for outcome in results:
        print(outcome)
    (args.output / "comparison.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return int(any(case["status"] == "failed" for case in results))


if __name__ == "__main__":
    raise SystemExit(main())
