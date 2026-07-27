from __future__ import annotations

import random as random_module
from typing import Callable

from .common import GameState


class GameSessionController:
    def __init__(
        self,
        *,
        human_player_factory: Callable[..., object],
        ai_player_factory: Callable[..., object],
        landscape_factory: Callable[..., object],
        quake_factory: Callable[..., object],
        blast_factory: Callable[..., object],
        sound_entity_factory: Callable[..., object],
        rng=random_module,
    ):
        self._human_player_factory = human_player_factory
        self._ai_player_factory = ai_player_factory
        self._landscape_factory = landscape_factory
        self._quake_factory = quake_factory
        self._blast_factory = blast_factory
        self._sound_entity_factory = sound_entity_factory
        self._rng = rng

    def add_player(self, game, controller: int, name: str, colour: tuple):
        if game._number_of_players >= 8:
            return

        if controller == -1:
            new_player = self._ai_player_factory(game, game._number_of_players, name, colour)
        else:
            new_player = self._human_player_factory(
                game,
                game._number_of_players,
                name,
                colour,
                controller,
                game.get_controls(),
            )
            game._human_players = True

        game._players[game._number_of_players] = new_player
        game.add_entity(new_player.get_tank())
        game._number_of_players += 1

    def delete_players(self, game):
        game._players = [None] * 8
        game._number_of_players = 0
        game._current_round = 0
        game._entity_list = []
        game._human_players = False
        game._number_of_active_tanks = 0
        game.reset_entity_registry()
        game.reset_network_session()
        game.queue_network_event("players_deleted")

    def are_human_players(self, game) -> bool:
        for i in range(game._number_of_players):
            if game._players[i] and not game._players[i].is_computer():
                return True
        return False

    def record_tank_death(self, game):
        game._number_of_active_tanks -= 1
        if game._number_of_active_tanks < 2 and game._game_state == GameState.ROUND_IN_ACTION:
            game._new_state = GameState.ROUND_FINISHING
            game._state_countdown = 5.0

    def explosion(self, game, x, y, size, damage, hit_tank_idx, sound_id, white_out, player_ref):
        if game._landscape is not None:
            game._landscape.make_hole(x, y, size)

        game.add_entity(self._blast_factory(game, x, y, size, 0.8, white_out))
        game.add_entity(self._sound_entity_factory(game, sound_id, False))
        game.queue_network_event(
            "explosion",
            x=x,
            y=y,
            size=size,
            damage=damage,
            hit_tank_idx=hit_tank_idx,
            sound_id=sound_id,
            white_out=white_out,
        )

        for i in range(8):
            if game._players[i] is None:
                break

            tank = game._players[i].get_tank()
            if i == hit_tank_idx:
                if tank.do_damage(damage):
                    player_ref.defeat(game._players[i])
                continue

            tank_x, tank_y, hit_range = tank.get_centre()
            squared_distance = (tank_x - x) ** 2 + (tank_y - y) ** 2
            max_distance = (size + hit_range) ** 2
            if squared_distance < max_distance:
                scaled_damage = damage * (1.0 - squared_distance / max_distance)
                if tank.do_damage(scaled_damage):
                    player_ref.defeat(game._players[i])

    def start_round(self, game):
        game._current_round += 1

        round_seed = game.get_clock().sample_now()
        game._landscape = self._landscape_factory(game.get_settings(), round_seed)
        game.ensure_registered_entities()

        for i in range(game._number_of_players):
            if game._players[i]:
                game._players[i].new_round()

        for entity in game._entity_list[:]:
            if not entity.do_pre_round():
                game.remove_entity(entity)

        tank_order = []
        active_tanks = 0
        for i in range(game._number_of_players):
            if game._players[i] and game._players[i].get_tank().alive():
                tank_order.append(i)
                active_tanks += 1

        for _ in range(20):
            if active_tanks > 0:
                t1 = self._rng.randint(0, active_tanks - 1)
                t2 = self._rng.randint(0, active_tanks - 1)
                tank_order[t1], tank_order[t2] = tank_order[t2], tank_order[t1]

        if active_tanks > 0:
            for i in range(active_tanks):
                player_idx = tank_order[i]
                tank = game._players[player_idx].get_tank()
                x_pos = -10.0 + (10.0 / active_tanks) + (i * (20.0 / active_tanks))
                tank.set_position_on_ground(x_pos)

        game._number_of_active_tanks = active_tanks
        quake = self._quake_factory(game)
        game.add_entity(quake)
        game._entity_list.insert(0, game._entity_list.pop())
        game.get_clock().reset(round_seed)
        game.queue_network_event(
            "round_started",
            round_number=game._current_round,
            round_seed=round_seed,
            active_tanks=active_tanks,
        )

    def end_round(self, game):
        for i in range(game._number_of_players):
            if game._players[i]:
                game._players[i].end_round()

        for entity in game._entity_list[:]:
            if not entity.do_post_round():
                game.remove_entity(entity)

        game._landscape = None
        game._new_state = GameState.ROUND_SCORE
        game.queue_network_event("round_finished", round_number=game._current_round)
