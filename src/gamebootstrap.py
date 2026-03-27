from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

from .assets import load_sound_specs, load_texture_specs, resolve_asset_path
from .common import GameState


class GameBootstrapper:
    def __init__(
        self,
        *,
        settings_loader: Callable[[str], object],
        interface_factory: Callable[..., object],
        controls_factory: Callable[..., object],
        controls_file_factory: Callable[..., object],
        font_factory: Callable[..., object],
        sound_factory: Callable[..., object],
        audio_error_cls: type[Exception],
        flow_controller,
        project_root: str | Path,
        asset_manifest_path: str | Path,
        static_settings_readers: Iterable[Callable[[object], None]],
    ):
        self._settings_loader = settings_loader
        self._interface_factory = interface_factory
        self._controls_factory = controls_factory
        self._controls_file_factory = controls_file_factory
        self._font_factory = font_factory
        self._sound_factory = sound_factory
        self._audio_error_cls = audio_error_cls
        self._flow_controller = flow_controller
        self._project_root = Path(project_root)
        self._asset_manifest_path = Path(asset_manifest_path)
        self._static_settings_readers = tuple(static_settings_readers)

    def bootstrap(self, game):
        game._settings = self._settings_loader("conf/options.ini")

        game._width = game._settings.get_int("Graphics", "ScreenWidth", 640)
        game._height = game._settings.get_int("Graphics", "ScreenHeight", 480)
        game._fullscreen = game._settings.get_int("Graphics", "Fullscreen", 0) != 0

        game._interface = self._interface_factory(game._width, game._height, game._fullscreen)
        self._load_resources(game)
        game._show_fps = game._settings.get_int("Graphics", "ShowFPS", 0) != 0
        self._read_class_settings(game)

        game._controls = self._controls_factory(game._interface)
        game._controls_file = self._controls_file_factory(game._controls, "conf/controls.ini")
        game._controls_file.read_file()

        game._current_menu = None
        self._flow_controller.enter_state(game, GameState.MAIN_MENU, GameState.MAIN_MENU)
        game.get_clock().reset()

    def _load_resources(self, game):
        texture_specs = load_texture_specs(self._asset_manifest_path)
        texture_ids = [spec.asset_id for spec in texture_specs]
        max_texture_id = max(texture_ids + [3])
        game._interface.define_textures(max_texture_id + 1)

        for spec in texture_specs:
            path = resolve_asset_path(spec.candidates, root=self._project_root)
            if path is None:
                print(f"Warning: No asset candidates found for texture '{spec.key}'")
                continue
            if not game._interface.load_texture(str(path), spec.asset_id):
                print(f"Warning: Failed to load texture '{path}'")

        game._font = self._font_factory(game._interface, 3)

        sound_specs = load_sound_specs(self._asset_manifest_path)
        sound_ids = [spec.asset_id for spec in sound_specs]
        game._sound = None
        if sound_ids:
            try:
                game._sound = self._sound_factory(max(sound_ids) + 1)
            except self._audio_error_cls:
                print("Warning: Failed to initialize audio; continuing without sound.")

        if game._sound is None:
            return

        for spec in sound_specs:
            path = resolve_asset_path(spec.candidates, root=self._project_root)
            if path is None:
                print(f"Warning: No asset candidates found for sound '{spec.key}'")
                continue
            game._sound.load_sound(spec.asset_id, str(path))

    def _read_class_settings(self, game):
        for settings_reader in self._static_settings_readers:
            if settings_reader is not None:
                settings_reader(game._settings)
