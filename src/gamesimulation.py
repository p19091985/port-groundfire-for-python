from __future__ import annotations

from .common import GameState


class GameSimulationController:
    def update_round(self, game, dt: float):
        if game._landscape is not None:
            game._landscape.update(dt)

        for entity in game._entity_list[:]:
            if not entity.update(dt):
                game.remove_entity(entity)

        if game.get_interface().get_key(game.pygame_module.K_ESCAPE):
            game._new_state = GameState.QUIT_MENU

    def simulate_round_frame(self, game, frame_dt: float, frame_start_time: float):
        processed_time = 0.0

        for step_dt in game._round_stepper.consume(frame_dt):
            processed_time += step_dt
            game.get_clock().set_time(frame_start_time + processed_time)
            self.simulate_round_step(game, step_dt)

            if game._new_state != GameState.CURRENT_STATE and game._new_state != game._game_state:
                break

        game.get_clock().set_time(frame_start_time + processed_time)

    def simulate_round_step(self, game, step_dt: float):
        if hasattr(game, "advance_simulation_tick"):
            game.advance_simulation_tick()
        self.update_round(game, step_dt)

        if game._game_state == GameState.ROUND_STARTING:
            game._state_countdown -= step_dt
            if game._state_countdown < 0.0:
                game._new_state = GameState.ROUND_IN_ACTION

        elif game._game_state == GameState.ROUND_FINISHING:
            game._state_countdown -= step_dt
            if game._state_countdown < 0.0:
                game._end_round()
