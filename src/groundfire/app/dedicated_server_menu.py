from __future__ import annotations

import os
import re
import shlex
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pygame

try:  # pygame_gui is the preferred widget layer when available.
    import pygame_gui  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    pygame_gui = None

try:  # pygame-menu remains useful for future desktop/web menu composition.
    import pygame_menu  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    pygame_menu = None


MAP_VALUES = ("classic", "basin", "ridge", "crater", "mesa", "seed 31")
NETWORK_VALUES = ("LAN", "Internet", "LAN + Internet")
NETWORK_ARGS = {"LAN": "lan", "Internet": "internet", "LAN + Internet": "both"}
NETWORK_LABELS = {"lan": "LAN", "internet": "Internet", "both": "LAN + Internet"}

COLORS = {
    "bg": (7, 19, 30),
    "panel": (11, 23, 34),
    "panel_soft": (17, 31, 43),
    "field": (27, 42, 52),
    "line": (139, 82, 6),
    "accent": (168, 93, 0),
    "accent_hot": (212, 119, 8),
    "text": (248, 250, 252),
    "muted": (185, 199, 210),
    "cyan": (128, 216, 255),
    "warn": (255, 209, 102),
    "disabled": (82, 91, 101),
}


@dataclass
class Field:
    key: str
    label: str
    value: str
    rect: pygame.Rect
    kind: str = "entry"
    options: tuple[str, ...] = ()
    password: bool = False


class DedicatedServerMenu:
    def __init__(self, script_path: str, project_dir: str, log_file: str):
        self.script_path = script_path
        self.project_dir = Path(project_dir)
        self.log_file = Path(log_file)
        self.size = (860, 720)
        self.running = True
        self.scroll_y = 0
        self.active_field: str | None = None
        self.open_combo: str | None = None
        self.secure_enabled = os.environ.get("GROUNDFIRE_SERVER_SECURE", "1") != "0" and os.environ.get(
            "GROUNDFIRE_SERVER_INSECURE", "0"
        ) != "1"
        self.show_client_enabled = os.environ.get("GROUNDFIRE_SERVER_SHOW_CLIENT", "0") == "1"
        self.server_process: subprocess.Popen | None = None
        self.last_player_count = 0
        self.status = f"Log: {self.log_file}"
        self.lobby_status = "Servidor parado."
        self.players_summary = "Jogadores conectados: 0/0"
        self.players_text = "Nenhum jogador conectado."
        self.can_start_match = False
        self.last_poll = 0.0

        pygame.init()
        pygame.display.set_caption("Groundfire - Dedicated Server")
        self.screen = pygame.display.set_mode(self.size, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 17)
        self.title_font = pygame.font.Font(None, 34)
        self.logo = self._load_image("logo.png")
        self.tile = self._load_image("menuback.png")
        self.fields = self._build_fields()

    def _load_image(self, name: str) -> pygame.Surface | None:
        path = self.project_dir / "data" / name
        if not path.exists():
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None

    def _build_fields(self) -> dict[str, Field]:
        network_default = NETWORK_LABELS.get(os.environ.get("GROUNDFIRE_SERVER_NETWORK", "lan").lower(), "LAN")
        defaults = {
            "game": "Groundfire",
            "name": os.environ.get("GROUNDFIRE_SERVER_NAME", "Groundfire LAN"),
            "map": os.environ.get("GROUNDFIRE_SERVER_MAP", "classic"),
            "network": network_default,
            "max_players": os.environ.get("GROUNDFIRE_MAX_PLAYERS", "8"),
            "port": os.environ.get("GROUNDFIRE_SERVER_PORT", "27015"),
            "discovery": os.environ.get("GROUNDFIRE_DISCOVERY_PORT", "27016"),
            "host": os.environ.get("GROUNDFIRE_SERVER_HOST", "0.0.0.0"),
            "region": os.environ.get("GROUNDFIRE_SERVER_REGION", "local"),
            "master": os.environ.get("GROUNDFIRE_MASTER_SERVERS", "127.0.0.1:27017"),
            "rcon": os.environ.get("GROUNDFIRE_RCON_PASSWORD", ""),
            "password": os.environ.get("GROUNDFIRE_SERVER_PASSWORD", ""),
            "rounds": os.environ.get("GROUNDFIRE_NUM_ROUNDS", "10"),
        }
        specs = (
            ("game", "Game", "combo", ("Groundfire",), False),
            ("name", "Server Name", "entry", (), False),
            ("map", "Map", "combo", MAP_VALUES, False),
            ("network", "Network", "combo", NETWORK_VALUES, False),
            ("max_players", "Max. players", "combo", tuple(str(v) for v in (2, 4, 6, 8, 12, 16, 24, 32)), False),
            ("port", "UDP Port", "entry", (), False),
            ("discovery", "Discovery Port", "entry", (), False),
            ("host", "Host", "entry", (), False),
            ("region", "Region", "entry", (), False),
            ("master", "Master Server", "entry", (), False),
            ("rcon", "RCON Password", "entry", (), False),
            ("password", "Join Password", "entry", (), True),
            ("rounds", "Rounds", "entry", (), False),
        )
        return {
            key: Field(key, label, defaults[key], pygame.Rect(0, 0, 0, 0), kind, options, password)
            for key, label, kind, options, password in specs
        }

    def run(self) -> int:
        while self.running:
            self.clock.tick(60)
            self._poll_lobby()
            for event in pygame.event.get():
                self._handle_event(event)
            self._draw()
            pygame.display.flip()
        self._stop_server()
        pygame.quit()
        return 0

    def _handle_event(self, event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            width = max(720, event.w)
            height = max(560, event.h)
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            self.size = (width, height)
        elif event.type == pygame.MOUSEWHEEL:
            content_height = 1010
            max_scroll = max(0, content_height - self.size[1])
            self.scroll_y = max(0, min(max_scroll, self.scroll_y - event.y * 38))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        x, y = pos
        y += self.scroll_y
        self.active_field = None

        if self.open_combo:
            combo = self.fields[self.open_combo]
            for index, option in enumerate(combo.options):
                rect = pygame.Rect(combo.rect.x, combo.rect.bottom + index * 28, combo.rect.width, 28)
                if rect.collidepoint(x, y):
                    combo.value = option
                    self.open_combo = None
                    return
            self.open_combo = None

        for field in self.fields.values():
            if field.rect.collidepoint(x, y):
                if field.kind == "combo":
                    self.open_combo = field.key
                else:
                    self.active_field = field.key
                return

        if self.secure_rect.collidepoint(x, y):
            self.secure_enabled = not self.secure_enabled
        elif self.client_rect.collidepoint(x, y):
            self.show_client_enabled = not self.show_client_enabled
        elif self.start_rect.collidepoint(x, y):
            self._start_server()
        elif self.test_rect.collidepoint(x, y):
            self._test_command()
        elif self.copy_rect.collidepoint(x, y):
            try:
                pygame.scrap.init()
                pygame.scrap.put(pygame.SCRAP_TEXT, self.status.encode("utf-8"))
                self._set_status("Status completo copiado para a area de transferencia.")
            except pygame.error:
                self._set_status("Clipboard indisponivel neste ambiente.")
        elif self.cancel_rect.collidepoint(x, y):
            self.running = False
        elif self.start_match_rect.collidepoint(x, y) and self.can_start_match:
            self._start_match()

    def _handle_key(self, event) -> None:
        if event.key == pygame.K_ESCAPE:
            if self.open_combo:
                self.open_combo = None
            elif self.active_field:
                self.active_field = None
            else:
                self.running = False
            return
        if not self.active_field:
            return
        field = self.fields[self.active_field]
        if event.key == pygame.K_BACKSPACE:
            field.value = field.value[:-1]
        elif event.key in {pygame.K_RETURN, pygame.K_TAB}:
            self.active_field = None
        elif event.unicode and event.unicode.isprintable():
            field.value += event.unicode

    def _draw(self) -> None:
        self._draw_background()
        width, _height = self.size
        surface = self.screen
        offset = -self.scroll_y
        page = pygame.Rect(34, 286 + offset, width - 68, 356)
        lobby = pygame.Rect(34, 666 + offset, width - 68, 220)
        status = pygame.Rect(34, 906 + offset, width - 68, 78)

        if self.logo:
            logo = pygame.transform.smoothscale(self.logo, (min(760, width - 90), 180))
            surface.blit(logo, (44, 48 + offset))
        else:
            self._text("Groundfire", 44, 64 + offset, self.title_font, COLORS["accent_hot"])

        self._text("Dedicated Server", 44, 252 + offset, self.title_font, COLORS["text"])
        self._text(
            "LAN, Internet listing, slots, map seed, secure mode",
            46,
            288 + offset,
            self.small_font,
            COLORS["cyan"],
        )
        self._panel(page)
        pygame.draw.rect(surface, COLORS["accent"], (page.x, page.y, page.width, 10))
        self._text("Start Dedicated Server", page.x + 16, page.y + 26, self.font, COLORS["text"])
        self._layout_fields(page)
        self._draw_fields()
        self._draw_checkboxes(page)
        self._draw_lobby(lobby)
        self._draw_status(status)
        self._draw_buttons(width, 1004 + offset)

    def _draw_background(self) -> None:
        self.screen.fill(COLORS["bg"])
        if not self.tile:
            return
        tint = pygame.Surface(self.tile.get_size(), pygame.SRCALPHA)
        tint.fill((6, 18, 28, 220))
        tile = self.tile.copy()
        tile.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        for x in range(0, self.size[0], tile.get_width()):
            for y in range(0, self.size[1], tile.get_height()):
                self.screen.blit(tile, (x, y))

    def _layout_fields(self, panel_rect: pygame.Rect) -> None:
        left_label = panel_rect.x + 28
        left_field = panel_rect.x + 132
        right_label = panel_rect.x + panel_rect.width // 2 + 36
        right_field = panel_rect.x + panel_rect.width // 2 + 140
        field_width = max(180, panel_rect.width // 2 - 172)
        rows = [
            (("game", left_label, left_field), ("name", right_label, right_field)),
            (("map", left_label, left_field), ("network", right_label, right_field)),
            (("max_players", left_label, left_field), ("port", right_label, right_field)),
            (("discovery", left_label, left_field), ("host", right_label, right_field)),
            (("region", left_label, left_field), ("master", right_label, right_field)),
            (("rcon", left_label, left_field), ("password", right_label, right_field)),
            (("rounds", left_label, left_field),),
        ]
        y = panel_rect.y + 60
        self.label_positions = {}
        for row in rows:
            for key, label_x, field_x in row:
                self.fields[key].rect = pygame.Rect(field_x, y, field_width, 26)
                self.label_positions[key] = (label_x, y + 5)
            y += 33

    def _draw_fields(self) -> None:
        for field in self.fields.values():
            lx, ly = self.label_positions[field.key]
            self._text(field.label, lx, ly, self.small_font, COLORS["muted"])
            border = (
                COLORS["accent_hot"]
                if self.active_field == field.key or self.open_combo == field.key
                else (91, 104, 114)
            )
            pygame.draw.rect(self.screen, COLORS["field"], field.rect)
            pygame.draw.rect(self.screen, border, field.rect, 1)
            value = "*" * len(field.value) if field.password else field.value
            self._text(value, field.rect.x + 6, field.rect.y + 5, self.small_font, COLORS["text"])
            if field.kind == "combo":
                pygame.draw.rect(
                    self.screen,
                    COLORS["accent"],
                    (field.rect.right - 16, field.rect.y, 16, field.rect.height),
                )
                self._text("v", field.rect.right - 12, field.rect.y + 4, self.small_font, COLORS["text"])
        if self.open_combo:
            field = self.fields[self.open_combo]
            for index, option in enumerate(field.options):
                rect = pygame.Rect(field.rect.x, field.rect.bottom + index * 28, field.rect.width, 28)
                pygame.draw.rect(self.screen, COLORS["panel_soft"], rect)
                pygame.draw.rect(self.screen, COLORS["line"], rect, 1)
                self._text(option, rect.x + 6, rect.y + 6, self.small_font, COLORS["text"])

    def _draw_checkboxes(self, panel_rect: pygame.Rect) -> None:
        self.secure_rect = pygame.Rect(panel_rect.x + 138, panel_rect.y + 294, 16, 16)
        self.client_rect = pygame.Rect(panel_rect.x + 278, panel_rect.y + 294, 16, 16)
        self._checkbox(self.secure_rect, self.secure_enabled, "Secure server")
        self._checkbox(self.client_rect, self.show_client_enabled, "Open local game window")

    def _draw_lobby(self, rect: pygame.Rect) -> None:
        self._panel(rect, soft=True)
        self._text(self.players_summary, rect.x + 14, rect.y + 18, self.font, COLORS["text"])
        self._text(self.lobby_status, rect.x + 14, rect.y + 48, self.small_font, COLORS["cyan"])
        self.start_match_rect = pygame.Rect(rect.right - 174, rect.y + 18, 150, 54)
        self._button(self.start_match_rect, "Iniciar Partida", enabled=self.can_start_match, accent=True)
        box = pygame.Rect(rect.x + 14, rect.y + 84, rect.width - 28, rect.height - 98)
        pygame.draw.rect(self.screen, COLORS["panel_soft"], box)
        pygame.draw.rect(self.screen, (91, 104, 114), box, 1)
        self._wrapped_text(self.players_text, box.x + 8, box.y + 8, box.width - 16, self.small_font, COLORS["muted"])

    def _draw_status(self, rect: pygame.Rect) -> None:
        self._panel(rect, soft=True)
        self._wrapped_text(self.status, rect.x + 10, rect.y + 8, rect.width - 20, self.small_font, COLORS["cyan"])

    def _draw_buttons(self, width: int, y: int) -> None:
        gap = 12
        left = 34
        button_w = (width - 68 - gap * 3) // 4
        self.start_rect = pygame.Rect(left, y, button_w, 48)
        self.test_rect = pygame.Rect(left + (button_w + gap), y, button_w, 48)
        self.copy_rect = pygame.Rect(left + (button_w + gap) * 2, y, button_w, 48)
        self.cancel_rect = pygame.Rect(left + (button_w + gap) * 3, y, button_w, 48)
        self._button(self.start_rect, "Start Server", accent=True)
        self._button(self.test_rect, "Test Command")
        self._button(self.copy_rect, "Copy Status")
        self._button(self.cancel_rect, "Cancel")

    def _panel(self, rect: pygame.Rect, *, soft: bool = False) -> None:
        pygame.draw.rect(self.screen, COLORS["panel_soft" if soft else "panel"], rect)
        pygame.draw.rect(self.screen, COLORS["line"], rect, 2)

    def _checkbox(self, rect: pygame.Rect, checked: bool, label: str) -> None:
        pygame.draw.rect(self.screen, COLORS["field"], rect)
        pygame.draw.rect(self.screen, (91, 104, 114), rect, 1)
        if checked:
            self._text("x", rect.x + 3, rect.y - 1, self.small_font, COLORS["warn"])
        self._text(label, rect.right + 6, rect.y - 1, self.small_font, COLORS["warn"])

    def _button(self, rect: pygame.Rect, label: str, *, enabled: bool = True, accent: bool = False) -> None:
        color = COLORS["accent"] if accent and enabled else COLORS["panel_soft"]
        if not enabled:
            color = (38, 45, 52)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, COLORS["line"] if accent else (91, 104, 114), rect, 1)
        text_color = COLORS["text"] if enabled else COLORS["disabled"]
        rendered = self.small_font.render(label, True, text_color)
        self.screen.blit(rendered, rendered.get_rect(center=rect.center))

    def _text(self, text: str, x: int, y: int, font: pygame.font.Font, color: tuple[int, int, int]) -> None:
        self.screen.blit(font.render(str(text), True, color), (x, y))

    def _wrapped_text(
        self,
        text: str,
        x: int,
        y: int,
        width: int,
        font: pygame.font.Font,
        color: tuple[int, int, int],
    ) -> None:
        line = ""
        for word in str(text).split():
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] <= width:
                line = candidate
                continue
            self._text(line, x, y, font, color)
            y += font.get_linesize()
            line = word
        if line:
            self._text(line, x, y, font, color)

    def _value(self, key: str) -> str:
        return self.fields[key].value.strip()

    def _set_status(self, text: str) -> None:
        self.status = str(text or "Status vazio.").strip() or "Status vazio."
        self._append_log(f"status: {self.status}")

    def _append_log(self, text: str) -> None:
        try:
            with self.log_file.open("a", encoding="utf-8") as handle:
                handle.write(f"[pygame] {text}\n")
        except OSError:
            pass

    def _validate(self) -> bool:
        errors = []
        if not self._is_valid_host(self._value("host") or "0.0.0.0"):
            errors.append("Host invalido.")
        if not self._is_port(self._value("port") or "27015"):
            errors.append("Porta deve ficar entre 1 e 65535.")
        if not self._is_port(self._value("discovery") or "27016"):
            errors.append("Descoberta deve ficar entre 1 e 65535.")
        if not self._value("rounds").isdigit() or int(self._value("rounds") or "0") <= 0:
            errors.append("Rounds deve ser um inteiro maior que zero.")
        if not self._value("max_players").isdigit() or not 1 <= int(self._value("max_players") or "0") <= 32:
            errors.append("Max. players deve ficar entre 1 e 32.")
        if self._value("network") not in NETWORK_ARGS:
            errors.append("Network invalido.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", self._value("region") or "local"):
            errors.append("Region deve usar letras, numeros, _ ou -.")
        if errors:
            self._set_status("\n".join(errors))
            return False
        return True

    def _build_command(self, *, dry_run: bool = False, require_admin: bool = False) -> list[str]:
        network_label = self._value("network") or "LAN"
        cmd = [
            self.script_path,
            "-A",
            "--host",
            self._value("host") or "0.0.0.0",
            "--port",
            self._value("port") or "27015",
            "--discovery-port",
            self._value("discovery") or "27016",
            "--server-name",
            self._value("name") or "Groundfire LAN",
            "--map",
            self._value("map") or "classic",
            "--max-players",
            self._value("max_players") or "8",
            "--network",
            NETWORK_ARGS[network_label],
            "--region",
            self._value("region") or "local",
            "--rounds",
            self._value("rounds") or "10",
            "--log-events",
        ]
        if network_label != "LAN":
            for address in [item.strip() for item in self._value("master").split(",") if item.strip()]:
                cmd.extend(["--master-server", address])
        rcon = self._ensure_admin_password() if require_admin else self._value("rcon")
        if rcon:
            cmd.extend(["--rcon-password", rcon])
        if self._value("password"):
            cmd.extend(["--password", self._value("password")])
        if not self.secure_enabled:
            cmd.append("--insecure")
        cmd.append("--com-tela" if self.show_client_enabled else "--sem-tela")
        if dry_run:
            cmd.append("--dry-run")
        return cmd

    def _start_server(self) -> None:
        if not self._validate():
            return
        command = self._build_command(require_admin=True)
        self._append_log(f"start_server command: {shlex.join(command)}")
        self.server_process = subprocess.Popen(command, cwd=self.project_dir)
        self.last_player_count = 0
        self._set_status("Iniciando servidor dedicado. Acompanhe o log para diagnostico.")

    def _test_command(self) -> None:
        if not self._validate():
            return
        command = self._build_command(dry_run=True)
        self._append_log(f"test_command dry-run: {shlex.join(command)}")
        completed = subprocess.run(command, cwd=self.project_dir, text=True, capture_output=True, check=False)
        self._set_status((completed.stdout + completed.stderr).strip() or "Comando registrado.")

    def _stop_server(self) -> None:
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()

    def _ensure_admin_password(self) -> str:
        if self._value("rcon"):
            return self._value("rcon")
        password = f"local-{os.getpid()}-{int(time.time() * 1000)}"
        self.fields["rcon"].value = password
        return password

    def _poll_lobby(self) -> None:
        if time.monotonic() - self.last_poll < 1.0:
            return
        self.last_poll = time.monotonic()
        if self.server_process is None:
            self.players_summary = "Jogadores conectados: 0/0"
            self.lobby_status = "Servidor parado."
            self.can_start_match = False
            return
        code = self.server_process.poll()
        if code is not None:
            self.players_summary = "Jogadores conectados: 0/0"
            self.lobby_status = f"Servidor encerrado (codigo {code})."
            self.can_start_match = False
            return
        response = self._send_rcon("status")
        if response is None or not response[0]:
            self.lobby_status = "Servidor iniciado; aguardando status administrativo."
            self.can_start_match = False
            return
        output = response[1]
        player_count, max_players, phase, can_start = self._parse_status(output)
        self.players_summary = f"Jogadores conectados: {player_count}/{max_players}"
        self.lobby_status = (
            "Aguardando jogadores conectarem." if phase == "lobby" else f"Partida em andamento: {phase}."
        )
        self.can_start_match = can_start and phase == "lobby" and player_count > 0
        players = self._send_rcon("players")
        if players is not None and players[0]:
            self.players_text = players[1].strip() or "Nenhum jogador conectado."

    def _start_match(self) -> None:
        self._append_log("rcon iniciar_partida solicitado pela interface.")
        response = self._send_rcon("iniciar_partida", timeout=0.35)
        if response is None:
            self._set_status("Senha RCON local indisponivel para iniciar a partida.")
            return
        self._set_status(response[1])

    def _send_rcon(self, command: str, *, timeout: float = 0.18):
        password = self._value("rcon")
        if not password:
            return None
        try:
            from src.groundfire.network.codec import decode_message, encode_message
            from src.groundfire.network.messages import RconCommand, RconResponse
        except Exception as exc:
            return (False, f"rcon_import_failed: {exc}")
        request_id = f"pygame-{time.time():.6f}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(timeout)
            sock.sendto(
                encode_message(RconCommand(command=command, password=password, request_id=request_id)),
                (self._local_admin_host(), int(self._value("port") or "27015")),
            )
            payload, _address = sock.recvfrom(65535)
            response = decode_message(payload)
        except OSError as exc:
            return (False, f"rcon_unreachable: {exc}")
        finally:
            sock.close()
        if not isinstance(response, RconResponse):
            return (False, "unexpected_rcon_response")
        return (bool(response.ok), response.output)

    def _local_admin_host(self) -> str:
        host = self._value("host") or "0.0.0.0"
        return "127.0.0.1" if host in {"0.0.0.0", "::", ""} else host

    def _parse_status(self, output: str) -> tuple[int, int, str, bool]:
        players_match = re.search(r"players=(\d+)/(\d+)", output or "")
        phase_match = re.search(r"phase=([A-Za-z0-9_]+)", output or "")
        can_start_match = re.search(r"can_start=(true|false)", output or "")
        player_count = int(players_match.group(1)) if players_match else 0
        max_players = int(players_match.group(2)) if players_match else int(self._value("max_players") or "0")
        phase = phase_match.group(1) if phase_match else "unknown"
        can_start = can_start_match is not None and can_start_match.group(1) == "true"
        return player_count, max_players, phase, can_start

    @staticmethod
    def _is_port(text: str) -> bool:
        return text.isdigit() and 1 <= int(text) <= 65535

    @staticmethod
    def _is_valid_host(text: str) -> bool:
        host = text.strip()
        if not host or len(host) > 253:
            return False
        if host == "localhost":
            return True
        parts = host.split(".")
        if len(parts) == 4 and all(part.isdigit() for part in parts):
            return all(0 <= int(part) <= 255 for part in parts)
        label = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        return re.fullmatch(rf"{label}(?:\.{label})*", host) is not None


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 3:
        print("usage: dedicated_server_menu.py SCRIPT_PATH PROJECT_DIR LOG_FILE", file=sys.stderr)
        return 2
    return DedicatedServerMenu(argv[0], argv[1], argv[2]).run()


if __name__ == "__main__":
    raise SystemExit(main())
