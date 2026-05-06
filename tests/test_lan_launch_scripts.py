import os
import signal
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LanLaunchScriptTests(unittest.TestCase):
    def test_all_script_can_start_real_server_and_six_headless_ai_tanks_for_ci(self):
        with TemporaryDirectory() as temp_dir:
            port = self._unused_udp_port()
            discovery_port = self._unused_udp_port()
            env = os.environ.copy()
            env["GROUNDFIRE_LAUNCHER_PYTHON"] = sys.executable
            env["GROUNDFIRE_LAUNCHER_LOG_DIR"] = temp_dir

            process = subprocess.Popen(
                [
                    "bash",
                    str(PROJECT_ROOT / "iniciar-all.sh"),
                    "-A",
                    "-n",
                    "6",
                    "--port",
                    str(port),
                    "--discovery-port",
                    str(discovery_port),
                    "--keepalive-seconds",
                    "30",
                    "--client-delay",
                    "0",
                    "--sem-tela",
                ],
                cwd=PROJECT_ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )
            try:
                self._wait_for_log_text(Path(temp_dir) / "all_debug.log", "Jogo automatico iniciado", timeout=6.0)
                for index in range(1, 7):
                    client_log = self._wait_for_glob(
                        Path(temp_dir),
                        f"iniciar-clientes-*-cliente-{index}.log",
                        timeout=3.0,
                    )
                    self._wait_for_log_text(client_log, "join_accept", timeout=3.0)
                self.assertIsNone(process.poll())
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=5.0)

            combined_output = f"{stdout}\n{stderr}"
            self.assertIn("Jogo automatico iniciado com 6 tanks IA", combined_output)
            self.assertNotIn("Traceback", combined_output)
            self.assertNotIn("Servidor nao respondeu", combined_output)

    def test_shell_launcher_test_script_passes(self):
        with TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["GROUNDFIRE_LAUNCHER_PYTHON"] = sys.executable
            env["GROUNDFIRE_LAUNCHER_LOG_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", str(PROJECT_ROOT / "tests" / "shell" / "test_lan_launchers.sh")],
                cwd=PROJECT_ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("OK: shell launcher tests passed", result.stdout)

    def test_ci_runs_bats_launcher_suite_on_linux(self):
        workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertIn("sudo apt-get install -y bats", workflow)
        self.assertIn("bats tests/shell/test_lan_launchers.bats", workflow)
        self.assertIn("if: runner.os == 'Linux'", workflow)

    def test_launchers_document_cli_and_ttk_management_modes(self):
        expectations = {
            "iniciar-all.sh": ("--menu", "--cli, -A, --auto", "Interface grafica Ttk"),
            "iniciar-server.sh": ("--menu", "--cli, -A, --auto", "Interface grafica Pygame"),
            "iniciar-clientes.sh": ("--menu", "--cli", "Interface grafica Ttk"),
        }

        with TemporaryDirectory() as temp_dir:
            for script_name, needles in expectations.items():
                with self.subTest(script_name=script_name):
                    result = self._run_script(script_name, ["--help"], temp_dir)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("Modos de acesso:", result.stdout)
                    for needle in needles:
                        self.assertIn(needle, result.stdout)

    def test_all_ttk_menu_uses_scrollable_layout_to_keep_buttons_visible(self):
        launcher = (PROJECT_ROOT / "iniciar-all.sh").read_text(encoding="utf-8")

        self.assertIn('root.geometry("660x720")', launcher)
        self.assertIn("tk.Canvas", launcher)
        self.assertIn("ttk.Scrollbar", launcher)
        self.assertIn("scrollregion=canvas.bbox", launcher)
        self.assertIn('canvas.create_window((0, 0), window=main, anchor="nw")', launcher)

    def test_launchers_accept_explicit_cli_mode(self):
        commands = (
            (
                "iniciar-all.sh",
                ["--cli", "--sem-tela", "--dry-run"],
                "DRY-RUN clients launcher command:",
            ),
            (
                "iniciar-server.sh",
                ["--cli", "--sem-tela", "--dry-run"],
                "DRY-RUN server command:",
            ),
            (
                "iniciar-clientes.sh",
                ["--cli", "-n", "1", "-a", "--sem-tela", "--dry-run"],
                "DRY-RUN client 1 command:",
            ),
        )

        with TemporaryDirectory() as temp_dir:
            for script_name, args, expected in commands:
                with self.subTest(script_name=script_name):
                    result = self._run_script(script_name, args, temp_dir)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(expected, result.stdout)

    def test_launchers_reexec_bash_when_called_with_sh(self):
        with TemporaryDirectory() as temp_dir:
            commands = (
                (
                    "iniciar-all.sh",
                    ["-A", "--port", "27770", "--discovery-port", "27771", "--sem-tela", "--dry-run"],
                    "DRY-RUN clients launcher command:",
                ),
                ("iniciar-server.sh", ["-A", "--port", "27772", "--sem-tela", "--dry-run"], "DRY-RUN server command:"),
                (
                    "iniciar-clientes.sh",
                    ["-n", "1", "-a", "--sem-tela", "--dry-run"],
                    "DRY-RUN client 1 command:",
                ),
            )

            for script_name, args, expected in commands:
                with self.subTest(script_name=script_name):
                    result = self._run_script_with_invoker("sh", script_name, args, temp_dir)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(expected, result.stdout)
                    self.assertNotIn("Illegal option -o pipefail", result.stderr)

    def test_graphical_menus_pass_absolute_launcher_path_to_python_callbacks(self):
        for script_name in ("iniciar-all.sh", "iniciar-server.sh", "iniciar-clientes.sh"):
            with self.subTest(script_name=script_name):
                launcher = (PROJECT_ROOT / script_name).read_text(encoding="utf-8")

                self.assertIn('SCRIPT_PATH="$SCRIPT_DIR/$(basename -- "${BASH_SOURCE[0]}")"', launcher)
                if script_name == "iniciar-server.sh":
                    self.assertIn("-m src.groundfire.app.dedicated_server_menu", launcher)
                    self.assertIn('"$SCRIPT_PATH" "$PROJECT_DIR" "$LOG_FILE"', launcher)
                else:
                    self.assertIn('"$python_bin" - "$SCRIPT_PATH" "$PROJECT_DIR" "$LOG_FILE"', launcher)
                self.assertNotIn('"$python_bin" - "$0" "$PROJECT_DIR" "$LOG_FILE"', launcher)

    def test_all_script_default_mode_builds_server_six_ai_tanks_and_six_visible_windows(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-all.sh",
                ["--port", "27779", "--discovery-port", "27780", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DRY-RUN server launcher command:", result.stdout)
            self.assertIn("DRY-RUN clients launcher command:", result.stdout)
            self.assertIn("DRY-RUN server command:", result.stdout)
            self.assertEqual(result.stdout.count("DRY-RUN client "), 6)
            self.assertIn("iniciar-server.sh", result.stdout)
            self.assertIn("iniciar-clientes.sh", result.stdout)
            self.assertIn("-m groundfire.server", result.stdout)
            self.assertIn("--log-events", result.stdout)
            self.assertIn("-m groundfire.client", result.stdout)
            self.assertIn("--connect 127.0.0.1:27779", result.stdout)
            self.assertIn("--computer-player", result.stdout)
            self.assertIn("--log-network-events", result.stdout)
            self.assertIn("--rounds 20", result.stdout)
            self.assertIn("--visible-count 6", result.stdout)
            self.assertIn("--sem-tela", result.stdout)
            self.assertIn("CPU\\ LAN\\ 6", result.stdout)
            first_client = self._dry_run_client_line(result.stdout, 1)
            sixth_client = self._dry_run_client_line(result.stdout, 6)
            self.assertNotIn("--headless-client", first_client)
            self.assertNotIn("--headless-client", sixth_client)
            self.assertNotIn("--headless-client", result.stdout)

            log_path = Path(temp_dir) / "all_debug.log"
            self.assertTrue(log_path.exists())
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("1 servidor + 6 tanks IA + 20 rounds", log_text)
            self.assertIn("Clientes IA com janela Pygame: 6", log_text)

    def test_all_script_can_configure_twenty_round_match(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-all.sh",
                ["-A", "--rounds", "20", "--sem-tela", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--rounds 20", result.stdout)
            self.assertIn(
                "1 servidor + 6 tanks IA + 20 rounds",
                (Path(temp_dir) / "all_debug.log").read_text(encoding="utf-8"),
            )

    def test_all_script_accepts_common_tank_presets(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-all.sh",
                ["-A", "--preset", "8", "--sem-tela", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("DRY-RUN client "), 8)
            self.assertIn("-n 8", result.stdout)

    def test_all_script_rejects_unknown_tank_preset(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-all.sh",
                ["-A", "--preset", "5", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("Preset de tanks invalido", (Path(temp_dir) / "all_debug.log").read_text(encoding="utf-8"))

    def test_server_script_auto_mode_builds_lan_command_visible_client_and_logs(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-server.sh",
                [
                    "-A",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "27777",
                    "--discovery-port",
                    "27778",
                    "--server-name",
                    "Groundfire LAN Test",
                    "--ticks",
                    "2",
                    "--com-tela",
                    "--dry-run",
                ],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DRY-RUN server command:", result.stdout)
            self.assertIn("-m groundfire.server", result.stdout)
            self.assertIn("--host 0.0.0.0", result.stdout)
            self.assertIn("--port 27777", result.stdout)
            self.assertIn("--discovery-port 27778", result.stdout)
            self.assertIn("--headless", result.stdout)
            self.assertIn("--log-events", result.stdout)
            self.assertIn("--ticks 2", result.stdout)
            self.assertIn("--rounds 10", result.stdout)
            self.assertIn("DRY-RUN visible client command:", result.stdout)
            self.assertIn("-m groundfire.client", result.stdout)
            self.assertIn("--connect 127.0.0.1:27777", result.stdout)
            self.assertIn("--computer-player", result.stdout)
            self.assertIn("--log-network-events", result.stdout)

            log_path = Path(temp_dir) / "server_debug.log"
            self.assertTrue(log_path.exists())
            self.assertIn("Preparando servidor LAN", log_path.read_text(encoding="utf-8"))
            self.assertIn("Cliente visivel", log_path.read_text(encoding="utf-8"))

    def test_server_script_can_run_server_only_for_headless_automation(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-server.sh",
                ["-A", "--port", "27775", "--sem-tela", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DRY-RUN server command:", result.stdout)
            self.assertNotIn("DRY-RUN visible client command:", result.stdout)
            log_path = Path(temp_dir) / "server_debug.log"
            self.assertIn("Modo sem tela", log_path.read_text(encoding="utf-8"))

    def test_server_script_builds_dedicated_server_options(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-server.sh",
                [
                    "-A",
                    "--network",
                    "internet",
                    "--master-server",
                    "127.0.0.1:27017",
                    "--map",
                    "ridge",
                    "--max-players",
                    "24",
                    "--region",
                    "sa",
                    "--rcon-password",
                    "admin",
                    "--insecure",
                    "--sem-tela",
                    "--dry-run",
                ],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--map ridge", result.stdout)
            self.assertIn("--max-players 24", result.stdout)
            self.assertIn("--log-events", result.stdout)
            self.assertIn("--region sa", result.stdout)
            self.assertIn("--no-discovery", result.stdout)
            self.assertIn("--master-server 127.0.0.1:27017", result.stdout)
            self.assertIn("--rcon-password admin", result.stdout)
            self.assertIn("--insecure", result.stdout)
            self.assertNotIn("DRY-RUN visible client command:", result.stdout)

    def test_server_menu_uses_pygame_dedicated_visuals_and_fields(self):
        launcher = (PROJECT_ROOT / "iniciar-server.sh").read_text(encoding="utf-8")
        module = (PROJECT_ROOT / "src" / "groundfire" / "app" / "dedicated_server_menu.py").read_text(encoding="utf-8")

        self.assertIn("launch_pygame_menu", launcher)
        self.assertIn("src.groundfire.app.dedicated_server_menu", launcher)
        self.assertIn("Abrindo menu Pygame do servidor.", launcher)
        self.assertIn("import pygame", module)
        self.assertIn("import pygame_gui", module)
        self.assertIn("import pygame_menu", module)
        self.assertIn('"menuback.png"', module)
        self.assertIn('"logo.png"', module)
        self.assertIn("pygame.RESIZABLE", module)
        self.assertIn("Start Dedicated Server", module)
        self.assertIn("RCON Password", module)
        self.assertIn("Secure server", module)
        self.assertIn("Open local game window", module)
        self.assertIn("NETWORK_VALUES", module)
        self.assertIn("MAP_VALUES", module)
        self.assertIn("Copy Status", module)
        self.assertIn("Iniciar Partida", module)
        self.assertIn("def _poll_lobby", module)
        self.assertIn("def _send_rcon", module)
        self.assertIn("rcon iniciar_partida solicitado", module)
        self.assertIn('"--log-events"', module)
        self.assertIn("pygame.scrap.put", module)
        self.assertIn("cleanup_stale_menu_server_ports", launcher)
        self.assertIn("GROUNDFIRE_SERVER_KEEP_EXISTING", launcher)

    def test_server_visible_client_uses_specific_bind_host_by_default(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-server.sh",
                ["-A", "--host", "localhost", "--port", "27774", "--com-tela", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DRY-RUN visible client command:", result.stdout)
            self.assertIn("--connect localhost:27774", result.stdout)

    def test_server_script_does_not_open_client_when_port_is_blocked_by_external_process(self):
        with TemporaryDirectory() as temp_dir, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as busy_socket:
            busy_socket.bind(("127.0.0.1", 0))
            port = int(busy_socket.getsockname()[1])
            discovery_port = self._unused_udp_port()

            result = self._run_script(
                "iniciar-server.sh",
                [
                    "-A",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--discovery-port",
                    str(discovery_port),
                    "--client-timeout",
                    "0.1",
                ],
                temp_dir,
            )

            self.assertNotEqual(result.returncode, 0)
            log_text = (Path(temp_dir) / "server_debug.log").read_text(encoding="utf-8")
            self.assertIn("Porta UDP", log_text)
            self.assertTrue(
                "ocupada por processo externo" in log_text
                or "Servidor encerrou antes de responder" in log_text
            )
            self.assertNotIn("Cliente visivel iniciado", log_text)

    def test_server_script_allows_discovery_port_used_by_browser_listener(self):
        with TemporaryDirectory() as temp_dir, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as browser_socket:
            browser_socket.bind(("127.0.0.1", 0))
            port = self._unused_udp_port()
            discovery_port = int(browser_socket.getsockname()[1])

            result = self._run_script(
                "iniciar-server.sh",
                [
                    "-A",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--discovery-port",
                    str(discovery_port),
                    "--sem-tela",
                    "--ticks",
                    "1",
                ],
                temp_dir,
            )

            log_text = (Path(temp_dir) / "server_debug.log").read_text(encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout + log_text)
            self.assertIn("Servidor PID", log_text)
            self.assertNotIn(f"Porta UDP {discovery_port} ainda esta ocupada", log_text)

    def test_server_script_restarts_existing_groundfire_server_on_requested_port(self):
        with TemporaryDirectory() as temp_dir:
            port = self._unused_udp_port()
            discovery_port = self._unused_udp_port()
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{PROJECT_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"
            old_log_path = Path(temp_dir) / "old-server.log"
            old_log = old_log_path.open("w", encoding="utf-8")
            old_server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "groundfire.server",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--discovery-port",
                    str(discovery_port),
                    "--server-name",
                    "Old Groundfire",
                    "--headless",
                    "--no-discovery",
                ],
                cwd=PROJECT_ROOT,
                env=env,
                text=True,
                stdout=old_log,
                stderr=subprocess.STDOUT,
            )
            try:
                self._wait_until_udp_server_responds(port, old_server, timeout=4.0)

                result = self._run_script(
                    "iniciar-server.sh",
                    [
                        "-A",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                        "--discovery-port",
                        str(discovery_port),
                        "--sem-tela",
                        "--ticks",
                        "1",
                    ],
                    temp_dir,
                )

                log_text = (Path(temp_dir) / "server_debug.log").read_text(encoding="utf-8")
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout + log_text)
                old_server.wait(timeout=2.0)
                self.assertIn("Servidor antigo encontrado na porta UDP", log_text)
                self.assertIn(f"Porta UDP {port} liberada para o novo servidor", log_text)
                self.assertIn("Servidor PID", log_text)
            finally:
                if old_server.poll() is None:
                    old_server.terminate()
                    try:
                        old_server.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        old_server.kill()
                        old_server.wait(timeout=2.0)
                old_log.close()

    def test_server_script_rejects_invalid_port_and_logs_error(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-server.sh",
                ["-A", "--port", "70000", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 2)
            log_path = Path(temp_dir) / "server_debug.log"
            self.assertTrue(log_path.exists())
            self.assertIn("Porta de jogo invalida", log_path.read_text(encoding="utf-8"))

    def test_server_script_rejects_invalid_host_and_logs_error(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-server.sh",
                ["-A", "--host", "host invalido", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 2)
            log_path = Path(temp_dir) / "server_debug.log"
            self.assertTrue(log_path.exists())
            self.assertIn("Host invalido", log_path.read_text(encoding="utf-8"))

    def test_all_script_rejects_invalid_client_host_and_logs_error(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-all.sh",
                ["-A", "--host", "host invalido", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 2)
            log_path = Path(temp_dir) / "all_debug.log"
            self.assertTrue(log_path.exists())
            self.assertIn("Host dos clientes invalido", log_path.read_text(encoding="utf-8"))

    def test_server_script_rotates_central_log_when_limit_is_reached(self):
        with TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "server_debug.log"
            log_path.write_text("x" * 64, encoding="utf-8")

            result = self._run_script(
                "iniciar-server.sh",
                ["-A", "--port", "27776", "--dry-run"],
                temp_dir,
                env_extra={"GROUNDFIRE_LOG_MAX_BYTES": "32", "GROUNDFIRE_LOG_BACKUPS": "2"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((Path(temp_dir) / "server_debug.log.1").read_text(encoding="utf-8"), "x" * 64)
            self.assertIn("Launcher do servidor", log_path.read_text(encoding="utf-8"))

    def test_client_script_count_ai_mode_builds_all_ai_clients_visible_by_default(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-clientes.sh",
                [
                    "-3",
                    "-a",
                    "--host",
                    "192.0.2.55",
                    "--port",
                    "27777",
                    "--player-prefix",
                    "Carga",
                    "--once",
                    "--dry-run",
                ],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("DRY-RUN client"), 3)
            self.assertIn("-m groundfire.client", result.stdout)
            self.assertIn("--connect 192.0.2.55:27777", result.stdout)
            self.assertIn("--computer-player", result.stdout)
            self.assertIn("--log-network-events", result.stdout)
            self.assertIn("CPU\\ LAN\\ 3", result.stdout)
            self.assertIn("--once", result.stdout)
            first_client = self._dry_run_client_line(result.stdout, 1)
            second_client = self._dry_run_client_line(result.stdout, 2)
            third_client = self._dry_run_client_line(result.stdout, 3)
            self.assertNotIn("--headless-client", first_client)
            self.assertNotIn("--headless-client", second_client)
            self.assertNotIn("--headless-client", third_client)

            log_path = Path(temp_dir) / "clients_debug.log"
            self.assertTrue(log_path.exists())
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("Preparando 3 cliente(s)", log_text)
            self.assertIn("Modo IA ativado", log_text)
            self.assertIn("Modo com tela: todos os 3", log_text)

    def test_client_script_can_limit_visible_ai_clients_and_leave_rest_headless(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-clientes.sh",
                ["-n", "3", "-a", "--visible-count", "1", "--host", "192.0.2.55", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("DRY-RUN client"), 3)
            self.assertNotIn("--headless-client", self._dry_run_client_line(result.stdout, 1))
            self.assertIn("--headless-client", self._dry_run_client_line(result.stdout, 2))
            self.assertIn("--headless-client", self._dry_run_client_line(result.stdout, 3))
            self.assertIn("Modo com tela: 1", (Path(temp_dir) / "clients_debug.log").read_text(encoding="utf-8"))

    def test_client_script_can_force_all_ai_clients_headless(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-clientes.sh",
                ["-n", "2", "-a", "--sem-tela", "--host", "192.0.2.55", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("DRY-RUN client"), 2)
            self.assertIn("--headless-client", self._dry_run_client_line(result.stdout, 1))
            self.assertIn("--headless-client", self._dry_run_client_line(result.stdout, 2))
            log_path = Path(temp_dir) / "clients_debug.log"
            self.assertIn("Modo sem tela", log_path.read_text(encoding="utf-8"))

    def test_client_script_accepts_common_client_presets(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-clientes.sh",
                ["--preset", "4", "-a", "--sem-tela", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("DRY-RUN client"), 4)
            self.assertIn("Preparando 4 cliente(s)", (Path(temp_dir) / "clients_debug.log").read_text(encoding="utf-8"))

    def test_client_script_rejects_unknown_client_preset(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-clientes.sh",
                ["--preset", "5", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn(
                "Preset de clientes invalido",
                (Path(temp_dir) / "clients_debug.log").read_text(encoding="utf-8"),
            )

    def test_client_script_check_server_dry_run_is_logged_without_network_probe(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-clientes.sh",
                ["-n", "2", "-a", "--sem-tela", "--check-server", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("DRY-RUN client"), 2)
            log_text = (Path(temp_dir) / "clients_debug.log").read_text(encoding="utf-8")
            self.assertIn("Verificando alcance UDP", log_text)
            self.assertIn("Dry-run ativo", log_text)

    def test_client_script_check_only_fails_when_server_is_unreachable(self):
        with TemporaryDirectory() as temp_dir:
            port = self._unused_udp_port()
            result = self._run_script(
                "iniciar-clientes.sh",
                ["--check-only", "--host", "127.0.0.1", "--port", str(port), "--join-timeout", "0.05"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stdout + result.stderr)
            self.assertIn(
                "Servidor nao respondeu ao ping UDP",
                (Path(temp_dir) / "clients_debug.log").read_text(encoding="utf-8"),
            )

    def test_client_script_rejects_invalid_port_and_logs_error(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-clientes.sh",
                ["-n", "2", "--port", "banana", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 2)
            log_path = Path(temp_dir) / "clients_debug.log"
            self.assertTrue(log_path.exists())
            self.assertIn("Porta do servidor invalida", log_path.read_text(encoding="utf-8"))

    def test_client_script_rejects_invalid_host_and_logs_error(self):
        with TemporaryDirectory() as temp_dir:
            result = self._run_script(
                "iniciar-clientes.sh",
                ["-n", "2", "--host", "host invalido", "--dry-run"],
                temp_dir,
            )

            self.assertEqual(result.returncode, 2)
            log_path = Path(temp_dir) / "clients_debug.log"
            self.assertTrue(log_path.exists())
            self.assertIn("Host do servidor invalido", log_path.read_text(encoding="utf-8"))

    def _run_script(
        self,
        script_name: str,
        args: list[str],
        log_dir: str,
        *,
        env_extra: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["GROUNDFIRE_LAUNCHER_PYTHON"] = sys.executable
        env["GROUNDFIRE_LAUNCHER_LOG_DIR"] = log_dir
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            ["bash", str(PROJECT_ROOT / script_name), *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_script_with_invoker(
        self,
        invoker: str,
        script_name: str,
        args: list[str],
        log_dir: str,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["GROUNDFIRE_LAUNCHER_PYTHON"] = sys.executable
        env["GROUNDFIRE_LAUNCHER_LOG_DIR"] = log_dir
        return subprocess.run(
            [invoker, str(PROJECT_ROOT / script_name), *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def _unused_udp_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _wait_until_udp_server_responds(self, port: int, process: subprocess.Popen[str], *, timeout: float):
        from src.groundfire.network.codec import decode_message, encode_message
        from src.groundfire.network.messages import Ping, Pong

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                self.fail(f"Server process exited before answering on UDP port {port}.")
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(0.1)
                try:
                    sock.sendto(encode_message(Ping(nonce="test", issued_at=time.time())), ("127.0.0.1", port))
                    payload, _address = sock.recvfrom(65535)
                except OSError:
                    time.sleep(0.05)
                    continue
                if isinstance(decode_message(payload), Pong):
                    return
            time.sleep(0.05)
        self.fail(f"UDP server on port {port} did not answer.")

    def _wait_for_log_text(self, path: Path, needle: str, *, timeout: float):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if path.exists():
                text = path.read_text(encoding="utf-8")
                if needle in text:
                    return
            time.sleep(0.05)
        if path.exists():
            self.fail(f"Log {path} did not contain {needle!r}. Content:\n{path.read_text(encoding='utf-8')}")
        self.fail(f"Log {path} was not created.")

    def _wait_for_glob(self, directory: Path, pattern: str, *, timeout: float) -> Path:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            matches = sorted(directory.glob(pattern))
            if matches:
                return matches[0]
            time.sleep(0.05)
        self.fail(f"No file matching {pattern!r} was created in {directory}.")

    def _dry_run_client_line(self, output: str, index: int) -> str:
        prefix = f"DRY-RUN client {index} command:"
        for line in output.splitlines():
            if line.startswith(prefix):
                return line
        self.fail(f"Could not find {prefix!r} in output:\n{output}")


if __name__ == "__main__":
    unittest.main()
