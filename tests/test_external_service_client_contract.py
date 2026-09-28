from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_EDITION = ROOT / "versao-python"
if str(PYTHON_EDITION) not in sys.path:
    sys.path.insert(0, str(PYTHON_EDITION))

from src.groundfire.service_client import GroundfireServiceClient  # noqa: E402


def test_python_service_adapter_exposes_cancelable_ui_delivery_queue(monkeypatch):
    client = GroundfireServiceClient("http://127.0.0.1:27880")
    completed = []

    def fake_request(method, path, body=None, *, authenticated=True):
        from src.groundfire.service_client import ServiceResult

        return ServiceResult("req_test", {"method": method, "path": path, "body": body, "authenticated": authenticated})

    monkeypatch.setattr(client, "request", fake_request)
    client.submit("POST", "/api/v1/lobbies", {"name": "Room"}, lambda result, error: completed.append((result, error)))
    import time

    deadline = time.monotonic() + 2
    while not completed and time.monotonic() < deadline:
        client.poll()
        time.sleep(0.01)
    assert completed[0][1] is None
    assert completed[0][0].data["path"] == "/api/v1/lobbies"


def test_godot_service_adapter_and_online_hub_are_wired():
    project = (ROOT / "versao-godot" / "godot" / "project.godot").read_text(encoding="utf-8")
    client = (ROOT / "versao-godot" / "godot" / "scripts" / "online" / "service_client.gd").read_text(encoding="utf-8")
    hub = (ROOT / "versao-godot" / "godot" / "scripts" / "online" / "online_hub.gd").read_text(encoding="utf-8")
    main = (ROOT / "versao-godot" / "godot" / "scripts" / "main.gd").read_text(encoding="utf-8")
    assert 'config/service_base_url="http://127.0.0.1:27880"' in project
    assert "_http.cancel_request()" in client
    assert "completed_generation != _generation" in client
    assert '"/api/v1/matchmaking/queue"' in client
    assert "func accept_reservation" in client
    assert "func admission_ticket" in client
    assert '"Criar sala"' in hub
    assert '"Entrar por código"' in hub
    assert "OnlineHubScene.instantiate()" in main
    assert "_screen.match_ready.connect(_show_online_match)" in main
