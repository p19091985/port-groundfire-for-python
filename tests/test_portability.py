import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSION_DIR = PROJECT_ROOT / "versao-python"
if not (PYTHON_VERSION_DIR / "src").exists():
    PYTHON_VERSION_DIR = PROJECT_ROOT


class PortabilityFilesTests(unittest.TestCase):
    def test_launchers_forward_arguments_and_check_native_runtime(self):
        bat = (PROJECT_ROOT / "run_game.bat").read_text(encoding="utf-8")
        ps1 = (PROJECT_ROOT / "run_game.ps1").read_text(encoding="utf-8")
        sh = (PROJECT_ROOT / "run_game.sh").read_text(encoding="utf-8")
        impl_bat = (PYTHON_VERSION_DIR / "run_game.bat").read_text(encoding="utf-8")
        impl_ps1 = (PYTHON_VERSION_DIR / "run_game.ps1").read_text(encoding="utf-8")
        impl_sh = (PYTHON_VERSION_DIR / "run_game.sh").read_text(encoding="utf-8")

        self.assertIn("%*", bat)
        self.assertIn("@args", ps1)
        self.assertIn('"$@"', sh)
        self.assertIn("versao-python", bat)
        self.assertIn("versao-python", ps1)
        self.assertIn("versao-python", sh)

        self.assertIn("groundfire", impl_bat)
        self.assertIn("groundfire", impl_ps1)
        self.assertIn("groundfire", impl_sh)
        self.assertNotIn("msgpack", impl_bat)
        self.assertNotIn("msgpack", impl_ps1)
        self.assertNotIn("msgpack", impl_sh)

    def test_pyproject_declares_installable_project_and_console_scripts(self):
        pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn("[project]", pyproject)
        self.assertIn('groundfire = "groundfire.client:main"', pyproject)
        self.assertIn('groundfire-server = "groundfire.server:main"', pyproject)
        self.assertIn('groundfire-master = "groundfire.master:main"', pyproject)
        self.assertIn('groundfire-directory = "groundfire_net.directory_service:main"', pyproject)
        self.assertIn('"groundfire_net*"', pyproject)
        self.assertNotIn("mpgameserver", pyproject)
        self.assertNotIn("msgpack", pyproject)

    def test_shell_launcher_installs_package_into_virtual_environment(self):
        sh = (PYTHON_VERSION_DIR / "run_game.sh").read_text(encoding="utf-8")

        self.assertIn('version("groundfire")', sh)
        self.assertIn('pip install --only-binary=pygame -e "$PROJECT_DIR"', sh)
        self.assertIn('pip install -e "$PROJECT_DIR"', sh)
        self.assertIn('exec "$VENV_GROUNDFIRE" "$@"', sh)

    def test_ci_matrix_covers_main_desktop_operating_systems(self):
        workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("windows-latest", workflow)
        self.assertIn("macos-latest", workflow)

    def test_readme_and_legacy_entrypoint_align_with_canonical_install_flow(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        legacy_main = (PYTHON_VERSION_DIR / "src" / "main.py").read_text(encoding="utf-8")

        self.assertIn("pip install -e .", readme)
        self.assertIn("groundfire", readme)
        self.assertNotIn("sys.path.insert", legacy_main)

    def test_flat_runtime_modules_are_now_minimal_bridges(self):
        bridge_targets = {
            "src/assets.py": "src.groundfire.assets",
            "src/pygamebackend.py": "src.groundfire.core.pygame",
            "src/controls.py": "src.groundfire.input.controls",
            "src/controlsfile.py": "src.groundfire.input.controlsfile",
            "src/inifile.py": "src.groundfire.core.settings",
            "src/interface.py": "src.groundfire.ui.interface",
            "src/font.py": "src.groundfire.ui.font",
            "src/gamehudrenderer.py": "src.groundfire.render.hud",
        }

        for relative_path, expected_import in bridge_targets.items():
            content = (PYTHON_VERSION_DIR / relative_path).read_text(encoding="utf-8")
            self.assertIn(expected_import, content)

    def test_canonical_package_runtime_no_longer_imports_flat_modules_in_shell_and_hud(self):
        shell = (PYTHON_VERSION_DIR / "src" / "groundfire" / "app" / "shell.py").read_text(encoding="utf-8")
        hud = (PYTHON_VERSION_DIR / "src" / "groundfire" / "render" / "hud.py").read_text(encoding="utf-8")

        self.assertNotIn("from src.", shell)
        self.assertNotIn("import src.", shell)
        self.assertNotIn("from src.", hud)
        self.assertNotIn("import src.", hud)


if __name__ == "__main__":
    unittest.main()
