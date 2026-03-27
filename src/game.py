from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional
import random
import uuid
import pygame

from .entityadapters import EntityAdapterRegistry
from .gamebootstrap import GameBootstrapper
from .fixedstep import FixedStepRunner
from .gameclock import GameClock
from .gameflow import GameFlowController
from .gamehudrenderer import GameHudRenderer
from .gamerenderer import GameRenderer
from .gamegraphics import GameGraphics
from .gamesimulation import GameSimulationController
from .gamesession import GameSessionController
from .gameui import GameUI
from .entityvisual import EntityVisualRenderer
from .interface import Interface, InterfaceError
from .inifile import ReadIniFile
from .controls import Controls
from .controlsfile import ControlsFile
from .font import Font
from .networkstate import MatchNetworkStateBuilder, NetworkEvent
from .networkprotocol import ClientServerEnvelopeBuilder
from .sounds import Sound, SoundError
from .landscape import Landscape
from .humanplayer import HumanPlayer
from .aiplayer import AIPlayer
from .blast import Blast
from .quake import Quake

# Menus
from .mainmenu import MainMenu
from .playermenu import PlayerMenu
from .optionmenu import OptionMenu
from .shopmenu import ShopMenu
from .scoremenu import ScoreMenu
from .quitmenu import QuitMenu
from .winnermenu import WinnerMenu
from .controllermenu import ControllerMenu
from .setcontrolsmenu import SetControlsMenu

if TYPE_CHECKING:
    from .entity import Entity
    from .player import Player
    from .menu import Menu

from .common import GameState


VERSION = "v0.25 (Python Port)"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_MANIFEST_PATH = PROJECT_ROOT / "conf" / "assets.json"


class GameError(Exception):
    pass


class Game:
    GameState = GameState
    ROUND_FIXED_STEP = 1.0 / 60.0
    ROUND_MAX_SUBSTEPS = 8

    def __init__(
        self,
        *,
        time_source: Callable[[], float] | None = None,
        clock: GameClock | None = None,
        round_stepper: FixedStepRunner | None = None,
        renderer: GameRenderer | None = None,
    ):
        self._entity_list: List["Entity"] = []
        self._game_state = GameState.MAIN_MENU
        self._new_state = GameState.MAIN_MENU
        self._state_countdown = 0.0
        self._number_of_active_tanks = 0
        self._landscape: Optional["Landscape"] = None

        self._width = 640
        self._height = 480
        self._fullscreen = False
        self._show_fps = False
        self._clock = clock or GameClock(time_source=time_source)
        self._round_stepper = round_stepper or FixedStepRunner(
            step=self.ROUND_FIXED_STEP,
            max_substeps=self.ROUND_MAX_SUBSTEPS,
        )
        self._flow = GameFlowController(menu_factories=self._build_menu_factories())
        self._renderer = renderer or self._build_renderer()
        self._entity_adapter = self._build_entity_adapter_registry()
        self._visual_renderer = self._build_visual_renderer()
        self._hud_renderer = self._build_hud_renderer()
        self._simulation = self._build_simulation_controller()
        self._network = self._build_network_state_builder()
        self._protocol = self._build_protocol_builder()
        self._session = self._build_session_controller()
        self._bootstrapper = self._build_bootstrapper()
        self._graphics = self._build_graphics()
        self._ui = self._build_ui()
        self._next_entity_id = 1
        self._entities_by_id: dict[int, "Entity"] = {}
        self._pending_network_events: list[NetworkEvent] = []
        self._session_id = uuid.uuid4().hex
        self._simulation_tick = 0
        self.pygame_module = pygame

        self._players: List[Optional["Player"]] = [None] * 8
        self._number_of_players = 0
        self._active_controller = 0
        self._num_of_rounds = 10
        self._current_round = 0
        self._round_end_timer = 0.0
        self._human_players = False

        try:
            self._bootstrapper.bootstrap(self)
        except InterfaceError as exc:
            raise GameError("Failed to initialize game interface.") from exc

    def __del__(self):
        if hasattr(self, "_controls_file") and self._controls_file:
            try:
                self._controls_file.write_file()
            except NameError:
                pass

    def get_game_state(self) -> int:
        return self._game_state

    def get_landscape(self) -> Optional["Landscape"]:
        return self._landscape

    def get_interface(self) -> Interface:
        return self._interface

    def get_settings(self) -> ReadIniFile:
        return self._settings

    def get_controls(self) -> Controls:
        return self._controls

    def get_controls_file(self) -> ControlsFile:
        return self._controls_file

    def get_font(self) -> Font:
        return self._font

    def get_ui(self) -> GameUI:
        return self._ui

    def get_graphics(self) -> GameGraphics:
        return self._graphics

    def get_renderer(self) -> GameRenderer:
        return self._renderer

    def get_visual_renderer(self) -> EntityVisualRenderer:
        return self._visual_renderer

    def get_hud_renderer(self) -> GameHudRenderer:
        return self._hud_renderer

    def get_entity_adapter_registry(self) -> EntityAdapterRegistry:
        return self._entity_adapter

    def get_sound(self):
        return self._sound

    def get_time(self) -> float:
        return self._clock.get_time()

    def set_time(self, value: float):
        self._clock.set_time(value)

    def get_clock(self) -> GameClock:
        return self._clock

    def get_session_id(self) -> str:
        return self._session_id

    def get_simulation_tick(self) -> int:
        return self._simulation_tick

    def advance_simulation_tick(self):
        self._simulation_tick += 1

    def add_entity(self, entity: "Entity"):
        self._register_entity(entity)
        self._entity_list.append(entity)

    def remove_entity(self, entity: "Entity"):
        if entity in self._entity_list:
            self._entity_list.remove(entity)

        if not hasattr(entity, "get_entity_id"):
            return

        entity_id = entity.get_entity_id()
        if entity_id is not None:
            self._entities_by_id.pop(entity_id, None)
            entity_type = entity.get_entity_type() if hasattr(entity, "get_entity_type") else type(entity).__name__.lower()
            self.queue_network_event("entity_removed", entity_id=entity_id, entity_type=entity_type)

    def build_match_snapshot(self):
        return self._network.build_snapshot(self)

    def build_snapshot_envelope(self):
        envelope = self._protocol.build_snapshot_envelope(self, self.build_match_snapshot())
        self.clear_network_events()
        return envelope

    def drain_command_envelopes(self):
        return self._protocol.build_command_envelopes(self)

    def get_pending_network_events(self) -> tuple[NetworkEvent, ...]:
        return tuple(self._pending_network_events)

    def clear_network_events(self):
        self._pending_network_events.clear()

    def queue_network_event(self, event_type: str, **payload):
        self._pending_network_events.append(NetworkEvent(event_type=event_type, payload=payload))

    def reset_entity_registry(self):
        self._next_entity_id = 1
        self._entities_by_id.clear()

    def reset_network_session(self):
        self._session_id = uuid.uuid4().hex
        self._simulation_tick = 0
        self._protocol = self._build_protocol_builder()
        self.clear_network_events()

    def ensure_registered_entities(self):
        for entity in self._entity_list:
            self._register_entity(entity, emit_spawn=False)

    def get_entity_by_id(self, entity_id: int):
        return self._entities_by_id.get(entity_id)

    def get_players(self) -> List[Optional["Player"]]:
        return self._players

    def get_num_of_players(self) -> int:
        return self._number_of_players

    def get_current_menu(self) -> Optional["Menu"]:
        return self._current_menu

    def set_active_controller(self, idx: int):
        self._active_controller = idx

    def get_active_controller(self) -> int:
        return self._active_controller

    def set_num_of_rounds(self, rounds: int):
        self._num_of_rounds = rounds

    def get_num_of_rounds(self) -> int:
        return self._num_of_rounds

    def get_current_round(self) -> int:
        return self._current_round

    def add_player(self, controller: int, name: str, colour: tuple):
        self._session.add_player(self, controller, name, colour)

    def delete_players(self):
        self._session.delete_players(self)

    def are_human_players(self) -> bool:
        return self._session.are_human_players(self)

    def record_tank_death(self):
        self._session.record_tank_death(self)

    def offset_viewport(self, x, y):
        if self._interface:
            self._interface.offset_viewport(x, y)

    def explosion(self, x, y, size, damage, hit_tank_idx, sound_id, white_out, player_ref):
        self._session.explosion(self, x, y, size, damage, hit_tank_idx, sound_id, white_out, player_ref)

    def loop_once(self) -> bool:
        frame = self._clock.tick()
        dt = frame.delta
        frame_start_time = frame.simulation_time - dt

        if self._interface.should_close():
            return False

        if not self._flow.is_round_state(self._game_state):
            self._new_state = self._flow.update_menu(self, dt)
        else:
            self._simulate_round_frame(dt, frame_start_time)

        self._renderer.render_frame(self, fps=frame.fps)

        if self._new_state != self.GameState.CURRENT_STATE and self._new_state != self._game_state:
            self._change_state(self._new_state)

        return self._game_state != self.GameState.EXITED

    def _change_state(self, new_state):
        prev_state = self._game_state
        self._game_state = new_state
        self.queue_network_event("state_changed", previous_state=prev_state, new_state=new_state)

        if new_state == self.GameState.ROUND_STARTING:
            self._round_stepper.reset()
        elif not self._flow.is_round_state(new_state):
            self._round_stepper.reset()

        self._flow.enter_state(self, new_state, prev_state)

    def _start_round(self):
        self._session.start_round(self)

    def _update_round(self, dt):
        self._simulation.update_round(self, dt)

    def _end_round(self):
        self._session.end_round(self)

    def _draw_round(self):
        self._renderer.render_round(self)

    def _simulate_round_frame(self, frame_dt: float, frame_start_time: float):
        self._simulation.simulate_round_frame(self, frame_dt, frame_start_time)

    def _simulate_round_step(self, step_dt: float):
        self._simulation.simulate_round_step(self, step_dt)

    def _build_menu_factories(self) -> dict[int, Callable[["Game"], object]]:
        return {
            self.GameState.MAIN_MENU: MainMenu,
            self.GameState.SELECT_PLAYERS_MENU: PlayerMenu,
            self.GameState.OPTION_MENU: OptionMenu,
            self.GameState.CONTROLLERS_MENU: ControllerMenu,
            self.GameState.SET_CONTROLS_MENU: lambda game: SetControlsMenu(game, game.get_active_controller()),
            self.GameState.QUIT_MENU: QuitMenu,
            self.GameState.SHOP_MENU: ShopMenu,
            self.GameState.ROUND_SCORE: ScoreMenu,
            self.GameState.WINNER_MENU: WinnerMenu,
        }

    def _build_bootstrapper(self) -> GameBootstrapper:
        return GameBootstrapper(
            settings_loader=ReadIniFile,
            interface_factory=Interface,
            controls_factory=Controls,
            controls_file_factory=ControlsFile,
            font_factory=Font,
            sound_factory=Sound,
            audio_error_cls=SoundError,
            flow_controller=self._flow,
            project_root=PROJECT_ROOT,
            asset_manifest_path=ASSET_MANIFEST_PATH,
            static_settings_readers=self._build_static_settings_readers(),
        )

    def _build_session_controller(self) -> GameSessionController:
        from .soundentity import SoundEntity

        return GameSessionController(
            human_player_factory=HumanPlayer,
            ai_player_factory=AIPlayer,
            landscape_factory=Landscape,
            quake_factory=Quake,
            blast_factory=Blast,
            sound_entity_factory=SoundEntity,
            rng=random,
        )

    def _build_renderer(self) -> GameRenderer:
        return GameRenderer()

    def _build_entity_adapter_registry(self) -> EntityAdapterRegistry:
        return EntityAdapterRegistry()

    def _build_visual_renderer(self) -> EntityVisualRenderer:
        return EntityVisualRenderer(state_builder=self._entity_adapter)

    def _build_hud_renderer(self) -> GameHudRenderer:
        return GameHudRenderer()

    def _build_simulation_controller(self) -> GameSimulationController:
        return GameSimulationController()

    def _build_network_state_builder(self) -> MatchNetworkStateBuilder:
        return MatchNetworkStateBuilder(entity_adapter=self._entity_adapter)

    def _build_protocol_builder(self) -> ClientServerEnvelopeBuilder:
        return ClientServerEnvelopeBuilder()

    def _build_graphics(self) -> GameGraphics:
        return GameGraphics(interface_provider=lambda: getattr(self, "_interface", None))

    def _build_ui(self) -> GameUI:
        return GameUI(font_provider=lambda: getattr(self, "_font", None))

    def _build_static_settings_readers(self) -> tuple[Callable[[ReadIniFile], None], ...]:
        from .mirv import Mirv
        from .missile import Missile
        from .trail import Trail
        from .weapons_impl import MachineGunWeapon, MirvWeapon, MissileWeapon, NukeWeapon, ShellWeapon

        return (
            getattr(ShellWeapon, "read_settings", None),
            getattr(NukeWeapon, "read_settings", None),
            getattr(Missile, "read_settings", None),
            getattr(Quake, "read_settings", None),
            getattr(MissileWeapon, "read_settings", None),
            getattr(Trail, "read_settings", None),
            getattr(Blast, "read_settings", None),
            getattr(Mirv, "read_settings", None),
            getattr(MirvWeapon, "read_settings", None),
            getattr(MachineGunWeapon, "read_settings", None),
        )

    def _register_entity(self, entity: "Entity", *, emit_spawn: bool = True):
        if not hasattr(entity, "get_entity_id") or not hasattr(entity, "assign_entity_id"):
            return

        entity_id = entity.get_entity_id()
        if entity_id is None:
            entity_id = self._next_entity_id
            self._next_entity_id += 1
            entity.assign_entity_id(entity_id)

        self._entities_by_id[entity_id] = entity

        if emit_spawn:
            self.queue_network_event(
                "entity_added",
                entity_id=entity_id,
                entity_type=entity.get_entity_type() if hasattr(entity, "get_entity_type") else type(entity).__name__.lower(),
            )
