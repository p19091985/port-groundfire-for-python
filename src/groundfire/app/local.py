from __future__ import annotations

from collections.abc import Callable

from ..gameplay.match_controller import MatchController
from ..ui import CanonicalLocalMenu, LocalMenuSelection, LocalPlayerConfig
from .front import ConnectedFrontRuntime
from .server import ServerApp


class LocalFrontRuntime:
    def __init__(
        self,
        *,
        connected_runtime: ConnectedFrontRuntime | None = None,
        server_factory: Callable[[], ServerApp] | None = None,
        menu_runtime: CanonicalLocalMenu | None = None,
    ):
        self._connected_runtime = connected_runtime or ConnectedFrontRuntime()
        self._server_factory = server_factory
        self._menu_runtime = menu_runtime or CanonicalLocalMenu()

    def open_menu(
        self,
        game,
        *,
        player_name: str,
        ai_players: int = 1,
        max_frames: int | None = None,
    ) -> LocalMenuSelection:
        return self._menu_runtime.run(
            game,
            player_name=player_name,
            ai_players=ai_players,
            max_frames=max_frames,
        )

    def run(
        self,
        client,
        game,
        *,
        player_name: str,
        ai_players: int = 1,
        num_rounds: int = 10,
        local_controller: int = 0,
        requested_slot: int | None = 0,
        player_configs: tuple[LocalPlayerConfig, ...] = (),
        max_frames: int | None = None,
    ) -> int:
        interface = game.get_interface()
        enable_mouse = getattr(interface, "enable_mouse", None)
        if callable(enable_mouse):
            enable_mouse(False)
        server = self._create_server(num_rounds=num_rounds)
        server.open()
        try:
            self._seed_local_roster(server, ai_players=ai_players, player_configs=player_configs)
            client.connect(
                "127.0.0.1",
                server.get_bound_port(),
                player_name=player_name,
                requested_slot=requested_slot,
            )
            self._bootstrap(client, server)
            return self._run_loop(client, game, server, max_frames=max_frames, local_controller=local_controller)
        finally:
            server.close()

    def _run_loop(
        self,
        client,
        game,
        server: ServerApp,
        *,
        max_frames: int | None = None,
        local_controller: int = 0,
    ) -> int:
        frames = 0
        tick_duration = 1.0 / float(server.get_match_controller().simulation_hz)
        accumulated = 0.0

        while max_frames is None or frames < max_frames:
            frame = game.get_clock().tick()
            if game.get_interface().should_close():
                return 0

            accumulated += max(0.0, float(getattr(frame, "delta", 0.0)))
            self._pump_server(client, server, min_steps=1)
            while accumulated >= tick_duration:
                self._pump_server(client, server, min_steps=1)
                accumulated -= tick_duration

            self._connected_runtime.tick(client, game, frame=frame, controller=local_controller)
            frames += 1

        return 0

    def _bootstrap(self, client, server: ServerApp):
        max_steps = server.get_match_controller().snapshot_interval_ticks * 3
        for _ in range(max_steps):
            self._pump_server(client, server, min_steps=1)
            if client.get_client_state().latest_snapshot is not None:
                return

    def _pump_server(self, client, server: ServerApp, *, min_steps: int):
        for _ in range(max(1, min_steps)):
            server.poll_network(timeout=0.0)
            server.step()
            client.poll_network(timeout=0.0)

    def _seed_local_roster(
        self,
        server: ServerApp,
        *,
        ai_players: int,
        player_configs: tuple[LocalPlayerConfig, ...] = (),
    ):
        controller = server.get_match_controller()
        if player_configs:
            for player in player_configs:
                if player.is_human:
                    continue
                controller.join_player(
                    player.name,
                    requested_slot=player.slot,
                    is_computer=True,
                )
            return

        bot_slots = max(0, min(ai_players, max(0, controller.max_players - 1)))
        for index in range(bot_slots):
            controller.join_player(f"CPU {index + 1}", requested_slot=index + 1, is_computer=True)

    def _create_server(self, *, num_rounds: int) -> ServerApp:
        if self._server_factory is not None:
            return self._server_factory()
        controller = MatchController(num_rounds=num_rounds)
        return ServerApp(
            host="127.0.0.1",
            port=0,
            discovery_port=0,
            server_name="Groundfire Local",
            enable_discovery=False,
            controller=controller,
        )
