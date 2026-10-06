from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from threading import RLock

from groundfire.network.codec import decode_message, encode_message
from groundfire.network.messages import HelloAccept, HelloRequest, JoinAccept, JoinRequest

from .config import Settings


@dataclass(frozen=True)
class WorkerSpec:
    match_id: str
    lobby_id: str
    name: str
    rounds: int
    seed: int
    capacity: int
    bots: int
    password: str
    session_secret: str


@dataclass(frozen=True)
class WorkerAllocation:
    udp_host: str
    udp_port: int
    websocket_url: str
    worker_pid: int
    gateway_pid: int


@dataclass
class _WorkerProcesses:
    worker: subprocess.Popen[bytes]
    gateway: subprocess.Popen[bytes]
    worker_log: object
    gateway_log: object


class WorkerSupervisor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = RLock()
        self._processes: dict[str, _WorkerProcesses] = {}
        self._log_dir = settings.root / "logs" / "matches"
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def active_count(self) -> int:
        with self._lock:
            self._reap()
            return len(self._processes)

    def start(self, spec: WorkerSpec) -> WorkerAllocation:
        with self._lock:
            self._reap()
            existing = self._processes.get(spec.match_id)
            if existing is not None:
                raise RuntimeError("match worker is already running")
            if len(self._processes) >= self.settings.max_workers:
                raise RuntimeError("worker capacity is exhausted")

            udp_port = _unused_port(self.settings.worker_bind, socket.SOCK_DGRAM)
            websocket_port = _unused_port(self.settings.worker_bind, socket.SOCK_STREAM)
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            worker_log = (self._log_dir / f"{spec.match_id}-worker.log").open("ab", buffering=0)
            gateway_log = (self._log_dir / f"{spec.match_id}-gateway.log").open("ab", buffering=0)
            common = {
                "cwd": str(self.settings.root),
                "stdin": subprocess.DEVNULL,
                "creationflags": creation_flags,
            }
            worker = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "groundfire.server",
                    "--host",
                    self.settings.worker_bind,
                    "--port",
                    str(udp_port),
                    "--discovery-port",
                    "0",
                    "--server-name",
                    spec.name,
                    "--map",
                    str(spec.seed),
                    "--rounds",
                    str(spec.rounds),
                    "--max-players",
                    str(spec.capacity),
                    "--no-discovery",
                    "--insecure",
                    "--log-events",
                    "--log-format",
                    "json",
                ],
                stdout=worker_log,
                stderr=subprocess.STDOUT,
                **common,
            )
            gateway_command = [
                sys.executable,
                "-m",
                "groundfire_net.websocket_gateway",
                "--host",
                self.settings.worker_bind,
                "--port",
                str(websocket_port),
                "--udp-host",
                self.settings.worker_bind,
                "--udp-port",
                str(udp_port),
                "--session-secret",
                spec.session_secret,
                "--max-players",
                str(spec.capacity),
            ]
            if self.settings.admission_redeem_enabled:
                gateway_command.extend(
                    [
                        "--admission-redeem-url",
                        f"http://{self.settings.bind}:{self.settings.port}/internal/v1/admissions/redeem",
                        "--admission-secret",
                        "local-worker",
                    ]
                )
            gateway = subprocess.Popen(
                gateway_command,
                stdout=gateway_log,
                stderr=subprocess.STDOUT,
                **common,
            )
            processes = _WorkerProcesses(worker, gateway, worker_log, gateway_log)
            self._processes[spec.match_id] = processes
            try:
                self._wait_ready(processes, udp_port, websocket_port)
                _add_bots(self.settings.worker_bind, udp_port, spec.bots)
            except BaseException:
                self._stop_processes(processes)
                self._processes.pop(spec.match_id, None)
                raise

            scheme = "wss" if self.settings.public_base_url.startswith("https://") else "ws"
            url = f"{scheme}://{self.settings.worker_public_host}:{websocket_port}"
            return WorkerAllocation(
                udp_host=self.settings.worker_public_host,
                udp_port=udp_port,
                websocket_url=url,
                worker_pid=worker.pid,
                gateway_pid=gateway.pid,
            )

    def stop(self, match_id: str) -> None:
        with self._lock:
            processes = self._processes.pop(match_id, None)
            if processes is not None:
                self._stop_processes(processes)

    def stop_all(self) -> None:
        with self._lock:
            for processes in tuple(self._processes.values()):
                self._stop_processes(processes)
            self._processes.clear()

    def _wait_ready(self, processes: _WorkerProcesses, udp_port: int, websocket_port: int) -> None:
        deadline = time.monotonic() + self.settings.worker_startup_seconds
        udp_ready = False
        gateway_ready = False
        while time.monotonic() < deadline:
            if processes.worker.poll() is not None:
                raise RuntimeError(f"game worker exited with {processes.worker.returncode}")
            if processes.gateway.poll() is not None:
                raise RuntimeError(f"gateway exited with {processes.gateway.returncode}")
            if not udp_ready:
                udp_ready = _probe_udp(self.settings.worker_bind, udp_port)
            if not gateway_ready:
                gateway_ready = _probe_tcp(self.settings.worker_bind, websocket_port)
            if udp_ready and gateway_ready:
                return
            time.sleep(0.05)
        raise RuntimeError("game worker readiness timed out")

    def _reap(self) -> None:
        for match_id, processes in tuple(self._processes.items()):
            if processes.worker.poll() is None and processes.gateway.poll() is None:
                continue
            self._stop_processes(processes)
            self._processes.pop(match_id, None)

    @staticmethod
    def _stop_processes(processes: _WorkerProcesses) -> None:
        for process in (processes.gateway, processes.worker):
            if process.poll() is None:
                process.terminate()
        deadline = time.monotonic() + 3.0
        for process in (processes.gateway, processes.worker):
            remaining = max(0.0, deadline - time.monotonic())
            try:
                process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2.0)
        processes.worker_log.close()
        processes.gateway_log.close()


def _unused_port(host: str, socket_type: int) -> int:
    with socket.socket(socket.AF_INET, socket_type) as candidate:
        candidate.bind((host, 0))
        return int(candidate.getsockname()[1])


def _probe_tcp(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.1):
            return True
    except OSError:
        return False


def _probe_udp(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.settimeout(0.1)
        try:
            client.sendto(encode_message(HelloRequest(player_name="readiness")), (host, port))
            payload, _address = client.recvfrom(65535)
            return isinstance(decode_message(payload), HelloAccept)
        except (OSError, ValueError):
            return False


def _add_bots(host: str, port: int, count: int) -> None:
    for index in range(count):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.settimeout(1.0)
            client.sendto(
                encode_message(JoinRequest(player_name=f"Bot {index + 1}", is_computer=True)),
                (host, port),
            )
            payload, _address = client.recvfrom(65535)
            if not isinstance(decode_message(payload), JoinAccept):
                raise RuntimeError("game worker rejected a configured bot")
