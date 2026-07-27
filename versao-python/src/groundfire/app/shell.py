from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from ..assets import load_texture_specs, resolve_asset_path
from ..core.clock import GameClock
from ..core.settings import ReadIniFile
from ..input.controls import Controls
from ..input.controlsfile import ControlsFile
from ..ui import GameGraphics, GameUI
from ..ui.font import Font
from ..ui.interface import Interface

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "conf" / "options.ini"
DEFAULT_CONTROLS_PATH = PROJECT_ROOT / "conf" / "controls.ini"
DEFAULT_ASSET_MANIFEST_PATH = PROJECT_ROOT / "conf" / "assets.json"


class SettingsReader(Protocol):
    def get_int(self, section: str, entry: str, default: int) -> int:
        ...


class CanonicalClientShell:
    def __init__(
        self,
        *,
        time_source: Callable[[], float] | None = None,
        settings_path: str | Path = DEFAULT_SETTINGS_PATH,
        controls_path: str | Path = DEFAULT_CONTROLS_PATH,
        asset_manifest_path: str | Path = DEFAULT_ASSET_MANIFEST_PATH,
        settings_loader: Callable[[str], SettingsReader] = ReadIniFile,
        interface_factory: Callable[..., Interface] = Interface,
        controls_factory: Callable[[Interface], Controls] = Controls,
        controls_file_factory: Callable[[Controls, str], ControlsFile] = ControlsFile,
        font_factory: Callable[..., Font] = Font,
        graphics_factory: Callable[..., GameGraphics] = GameGraphics,
        ui_factory: Callable[..., GameUI] = GameUI,
    ):
        self._settings_path = Path(settings_path)
        self._controls_path = Path(controls_path)
        self._asset_manifest_path = Path(asset_manifest_path)
        self._settings = settings_loader(str(self._settings_path))
        self._width = self._settings.get_int("Graphics", "ScreenWidth", 640)
        self._height = self._settings.get_int("Graphics", "ScreenHeight", 480)
        self._fullscreen = self._settings.get_int("Graphics", "Fullscreen", 0) != 0
        self._show_fps = self._settings.get_int("Graphics", "ShowFPS", 0) != 0

        self._interface = interface_factory(self._width, self._height, self._fullscreen)
        self._load_textures()
        self._font = font_factory(self._interface, 3)
        self._graphics = graphics_factory(interface_provider=lambda: self._interface)
        self._ui = ui_factory(font_provider=lambda: self._font)
        self._controls = controls_factory(self._interface)
        self._controls_file = controls_file_factory(self._controls, str(self._controls_path))
        self._controls_file.read_file()
        self._clock = GameClock(time_source=time_source)
        self._clock.reset()
        self._closed = False

    def close(self):
        if self._closed:
            return
        self._closed = True
        if hasattr(self, "_controls_file") and self._controls_file is not None:
            try:
                self._controls_file.write_file()
            except Exception:
                pass
        if hasattr(self, "_interface") and self._interface is not None:
            try:
                self._interface.close()
            except Exception:
                pass

    def get_clock(self) -> GameClock:
        return self._clock

    def get_interface(self) -> Interface:
        return self._interface

    def get_controls(self) -> Controls:
        return self._controls

    def get_font(self) -> Font:
        return self._font

    def get_ui(self) -> GameUI:
        return self._ui

    def get_graphics(self) -> GameGraphics:
        return self._graphics

    def get_settings(self) -> SettingsReader:
        return self._settings

    def get_settings_path(self) -> Path:
        return self._settings_path

    def _load_textures(self):
        texture_specs = load_texture_specs(self._asset_manifest_path)
        texture_ids = [spec.asset_id for spec in texture_specs]
        self._interface.define_textures((max(texture_ids) + 1) if texture_ids else 4)
        for spec in texture_specs:
            path = resolve_asset_path(spec.candidates, root=PROJECT_ROOT)
            if path is not None:
                self._interface.load_texture(str(path), spec.asset_id)
