from __future__ import annotations

from .common import GameState


class GameRenderer:
    ROUND_STATES = {
        GameState.ROUND_STARTING,
        GameState.ROUND_IN_ACTION,
        GameState.ROUND_FINISHING,
    }

    def render_frame(self, game, *, fps: float):
        interface = game.get_interface()
        interface.start_draw()

        try:
            if game.get_game_state() in self.ROUND_STATES:
                self.render_round(game)

                if game.get_game_state() == GameState.ROUND_STARTING:
                    self.render_round_start_overlay(game)
            else:
                self.render_menu(game)

            if game._show_fps:
                self.render_fps(game, fps)
        finally:
            interface.end_draw()

    def render_menu(self, game):
        current_menu = game.get_current_menu()
        if current_menu is not None:
            current_menu.draw()

    def render_round(self, game):
        landscape = game.get_landscape()
        if landscape is not None:
            landscape.draw()

        for entity in game._entity_list:
            if not game.get_visual_renderer().render_entity(game, entity):
                entity.draw()

        game.get_hud_renderer().render_round_hud(game)

    def render_round_start_overlay(self, game):
        game.get_hud_renderer().render_round_start_overlay(game)

    def render_fps(self, game, fps: float):
        game.get_hud_renderer().render_fps(game, fps)
