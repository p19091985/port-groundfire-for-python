from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..core.clock import ClockTick
from ..input.commands import ALL_PLAYER_COMMANDS
from ..ui import ClientMenuRenderer

if TYPE_CHECKING:
    from .client import ClientApp


@dataclass(frozen=True)
class ConnectedFrontFrame:
    commands: dict[str, bool]
    fps: float
    rendered_remote: bool
    overlay_text: str | None = None
    frame_metadata: dict[str, object] | None = None


class LocalCommandSampler:
    def sample(self, game, *, controller: int = 0) -> dict[str, bool]:
        controls = game.get_controls()
        return {
            command.name.lower(): bool(controls.get_command(controller, int(command)))
            for command in ALL_PLAYER_COMMANDS
        }


class ConnectedFrontRuntime:
    COMMAND_SEND_INTERVAL = 1.0 / 60.0

    def __init__(
        self,
        *,
        command_sampler: LocalCommandSampler | None = None,
        menu_renderer: ClientMenuRenderer | None = None,
    ):
        self._command_sampler = command_sampler or LocalCommandSampler()
        self._menu_renderer = menu_renderer or ClientMenuRenderer()
        self._last_sent_commands: dict[str, bool] | None = None
        self._last_send_time = -1.0

    def run(self, client: "ClientApp", game, *, max_frames: int | None = None, controller: int = 0) -> int:
        frames = 0
        while max_frames is None or frames < max_frames:
            frame = game.get_clock().tick()

            if game.get_interface().should_close():
                return 0

            self.tick(client, game, frame=frame, controller=controller)
            frames += 1

        return 0

    def tick(self, client: "ClientApp", game, *, frame: ClockTick, controller: int = 0) -> ConnectedFrontFrame:
        client.poll_network(timeout=0.0)

        commands = self._command_sampler.sample(game, controller=controller)
        if self._should_send_commands(client, frame, commands):
            client.build_and_send_command_envelope(commands, source=self._command_source(controller))
            self._last_sent_commands = dict(commands)
            self._last_send_time = frame.simulation_time

        rendered_remote, overlay_text, frame_metadata = self._render(game, client, fps=frame.fps)
        return ConnectedFrontFrame(
            commands=commands,
            fps=frame.fps,
            rendered_remote=rendered_remote,
            overlay_text=overlay_text,
            frame_metadata=frame_metadata,
        )

    def _should_send_commands(self, client: "ClientApp", frame: ClockTick, commands: dict[str, bool]) -> bool:
        client_state = client.get_client_state()
        if client_state.session_id is None or client_state.player_number is None:
            return False

        if self._last_sent_commands != commands:
            return True

        return (frame.simulation_time - self._last_send_time) >= self.COMMAND_SEND_INTERVAL

    def _render(self, game, client: "ClientApp", *, fps: float) -> tuple[bool, str | None, dict[str, object] | None]:
        interface = game.get_interface()
        interface.start_draw()
        overlay_text = None
        frame_metadata = None

        try:
            if client.get_client_state().latest_snapshot is not None:
                remote_frame = client.build_remote_render_frame()
                client.render_connected_frame(game, frame=remote_frame)
                rendered_remote = True
                frame_metadata = dict(remote_frame.metadata)
                if self._should_show_status_overlay(client):
                    overlay_text = self._status_text(client)
                    self._draw_status_overlay(game, overlay_text)
            else:
                rendered_remote = False
                overlay_text = self._status_text(client)
                self._draw_status_overlay(game, overlay_text)

            if getattr(game, "_show_fps", False):
                self._render_fps(game, fps)
        finally:
            interface.end_draw()

        return rendered_remote, overlay_text, frame_metadata

    def _status_text(self, client: "ClientApp") -> str:
        client_state = client.get_client_state()
        if client_state.disconnect_reason:
            return f"Disconnected: {client_state.disconnect_reason}"
        if client_state.join_reject_reason:
            return f"Join rejected: {client_state.join_reject_reason}"
        if client_state.session_id is None:
            if client_state.server_name:
                return f"Joining {client_state.server_name}..."
            return "Connecting..."
        return "Synchronizing..."

    def _should_show_status_overlay(self, client: "ClientApp") -> bool:
        client_state = client.get_client_state()
        return bool(client_state.disconnect_reason or client_state.join_reject_reason)

    def _draw_status_overlay(self, game, text: str):
        self._menu_renderer.draw_status_overlay(game, text)

    def _command_source(self, controller: int) -> str:
        if controller < 2:
            return f"client:keyboard{controller}"
        return f"client:joystick{controller - 1}"

    def _render_fps(self, game, fps: float):
        hud_renderer = getattr(game, "get_hud_renderer", None)
        if callable(hud_renderer):
            renderer = hud_renderer()
            if hasattr(renderer, "render_fps"):
                renderer.render_fps(game, fps)
                return

        ui = game.get_ui()
        ui.printf(-10.0, -7.3, "%.1f FPS", fps, style=ui.style(0.3, (128, 255, 51), spacing=0.25))
