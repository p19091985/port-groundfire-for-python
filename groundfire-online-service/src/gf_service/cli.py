from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

from .config import load_settings


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _runtime_file() -> Path:
    path = _root() / "data" / "service.pid.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def check() -> int:
    from .store import Store

    settings = load_settings(_root())
    _verify_runtime()
    Store(settings.database_path).one("SELECT 1")
    print(f"Configuração e runtime válidos; banco pronto em {settings.database_path}")
    return 0


def status() -> int:
    settings = load_settings(_root())
    try:
        with urllib.request.urlopen(f"http://{settings.bind}:{settings.port}/readyz", timeout=2) as response:
            payload = response.read().decode("utf-8")
        print(payload)
        return 0
    except (OSError, urllib.error.URLError) as exc:
        print(f"Serviço indisponível: {exc}", file=sys.stderr)
        return 6


def stop() -> int:
    path = _runtime_file()
    if not path.exists():
        print("Nenhuma instância registrada.", file=sys.stderr)
        return 4
    data = json.loads(path.read_text(encoding="utf-8"))
    pid = int(data["pid"])
    try:
        request = urllib.request.Request(
            str(data["control_url"]),
            data=b"{}",
            method="POST",
            headers={"X-Groundfire-Control": str(data["nonce"]), "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            if response.status != 202:
                raise OSError(f"unexpected shutdown status {response.status}")
    except (urllib.error.URLError, OSError, KeyError):
        try:
            os.kill(pid, 0)
        except OSError:
            path.unlink(missing_ok=True)
            print("O processo registrado já terminou.")
            return 0
        print("A instância não aceitou a parada autenticada.", file=sys.stderr)
        return 6
    print(f"Parada solicitada ao processo {pid}.")
    return 0


def _open_console(host: str, port: int, nonce: str) -> None:
    address = "[::1]" if host == "::1" else host
    url = f"http://{address}:{port}/console#key={urllib.parse.quote(nonce)}"
    ready = f"http://{address}:{port}/readyz"
    for _ in range(100):
        try:
            with urllib.request.urlopen(ready, timeout=0.3) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.1)
    print("O navegador não pôde ser aberto antes do servidor ficar pronto.", file=sys.stderr)


def gui() -> int:
    settings = load_settings(_root())
    if settings.bind not in {"127.0.0.1", "localhost", "::1"}:
        print("O console gráfico exige que service.bind seja local.", file=sys.stderr)
        return 4
    path = _runtime_file()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            address = "[::1]" if settings.bind == "::1" else settings.bind
            with urllib.request.urlopen(f"http://{address}:{settings.port}/readyz", timeout=2) as response:
                if response.status == 200:
                    _open_console(settings.bind, settings.port, str(data["nonce"]))
                    print("Abrindo o console da instância em execução...")
                    return 0
        except (OSError, urllib.error.URLError, ValueError, KeyError, json.JSONDecodeError):
            pass
    return start(open_console=True)


def start(*, open_console: bool = False) -> int:
    import uvicorn

    settings = load_settings(_root())
    _verify_runtime()
    path = _runtime_file()
    if path.exists():
        try:
            prior = json.loads(path.read_text(encoding="utf-8"))
            os.kill(int(prior["pid"]), 0)
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            path.unlink(missing_ok=True)
        else:
            print("Uma instância já está registrada.", file=sys.stderr)
            return 4
    nonce = secrets.token_urlsafe(32)
    os.environ["GF_SERVICE_CONTROL_NONCE"] = nonce
    handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(
            handle,
            json.dumps(
                {
                    "pid": os.getpid(),
                    "root": str(_root()),
                    "nonce": nonce,
                    "control_url": f"http://{settings.bind}:{settings.port}/internal/v1/shutdown",
                }
            ).encode("utf-8"),
        )
    finally:
        os.close(handle)
    try:
        if open_console:
            threading.Thread(target=_open_console, args=(settings.bind, settings.port, nonce), daemon=True).start()
        uvicorn.run("gf_service.app:create_app", factory=True, host=settings.bind, port=settings.port, log_level="info")
    finally:
        path.unlink(missing_ok=True)
    return 0


def _verify_runtime() -> None:
    root = _root()
    manifest_path = root / "runtime-manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("runtime-manifest.json não foi encontrado")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files", {})
    if not isinstance(files, dict) or not files:
        raise RuntimeError("manifesto do runtime está vazio ou inválido")
    for relative, expected in files.items():
        path = (root / str(relative)).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise RuntimeError("manifesto do runtime contém caminho externo") from exc
        if not path.is_file():
            raise RuntimeError(f"arquivo do runtime ausente: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"hash do runtime inválido: {relative}")


def backup() -> int:
    settings = load_settings(_root())
    backup_dir = _root() / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    destination = backup_dir / time.strftime("groundfire-%Y%m%d-%H%M%S.sqlite3", time.gmtime())
    source = sqlite3.connect(settings.database_path)
    target = sqlite3.connect(destination)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    manifest = destination.with_suffix(".json")
    manifest.write_text(
        json.dumps({"schema": 1, "database": destination.name, "sha256": digest}, indent=2) + "\n", encoding="utf-8"
    )
    print(destination)
    return 0


def restore(file_name: str) -> int:
    runtime = _runtime_file()
    if runtime.exists():
        print("Pare o serviço antes de restaurar um backup.", file=sys.stderr)
        return 4
    settings = load_settings(_root())
    source = Path(file_name).resolve()
    if not source.is_file():
        print(f"Backup não encontrado: {source}", file=sys.stderr)
        return 5
    manifest = source.with_suffix(".json")
    if not manifest.is_file():
        print("Manifesto do backup não encontrado.", file=sys.stderr)
        return 5
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if metadata.get("sha256") != digest:
        print("Checksum do backup é inválido.", file=sys.stderr)
        return 5
    probe = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
    try:
        if probe.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            print("O backup falhou na verificação de integridade.", file=sys.stderr)
            return 5
    finally:
        probe.close()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    previous = settings.database_path.with_suffix(".before-restore.sqlite3")
    if settings.database_path.exists():
        shutil.copy2(settings.database_path, previous)
    temporary = settings.database_path.with_suffix(".restore.tmp")
    shutil.copy2(source, temporary)
    os.replace(temporary, settings.database_path)
    print(f"Backup restaurado em {settings.database_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gf-service")
    parser.add_argument(
        "command", nargs="?", default="start", choices=("start", "gui", "check", "status", "stop", "backup", "restore")
    )
    parser.add_argument("--file", default="", help="Arquivo usado por restore.")
    args = parser.parse_args(argv)
    if args.command == "restore":
        if not args.file:
            parser.error("restore requires --file")
        return restore(args.file)
    return {"start": start, "gui": gui, "check": check, "status": status, "stop": stop, "backup": backup}[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
