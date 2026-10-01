from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from conftest import register
from gf_service.app import create_app
from gf_service import cli
from gf_service.config import Settings


def local_client(app):
    return TestClient(app, base_url="http://127.0.0.1:27880", client=("127.0.0.1", 50000))


def test_console_requires_local_peer_host_and_instance_key(settings, monkeypatch):
    monkeypatch.setenv("GF_SERVICE_CONTROL_NONCE", "test-secret")
    app = create_app(settings)
    with local_client(app) as client:
        html = client.get("/console")
        assert html.status_code == 200
        assert "Central do servidor" in html.text
        assert "default-src 'none'" in html.headers["content-security-policy"]
        assert client.get("/console/assets/app.js").status_code == 200
        assert client.get("/console/api/snapshot").status_code == 401
        assert client.get("/console/api/snapshot", headers={"X-Groundfire-Control": "wrong"}).status_code == 401
        assert client.get("/console/api/snapshot", headers={"X-Groundfire-Control": "test-secret", "Origin": "http://evil.test"}).status_code == 403
        assert client.get("/console/api/snapshot", headers={"X-Groundfire-Control": "test-secret", "Host": "evil.test"}).status_code == 403
        result = client.get("/console/api/snapshot", headers={"X-Groundfire-Control": "test-secret"})
        assert result.status_code == 200
        assert result.json()["metrics"]["users"] == 0
        assert "session_secret" not in result.text
    with TestClient(app, base_url="http://127.0.0.1:27880", client=("192.0.2.1", 50000)) as remote:
        assert remote.get("/console").status_code == 403
    public_settings = Settings(root=settings.root, database=settings.database, bind="0.0.0.0")
    with local_client(create_app(public_settings)) as public:
        assert public.get("/console").status_code == 404


def test_console_reports_real_records_and_creates_verified_backup(settings, monkeypatch):
    monkeypatch.setenv("GF_SERVICE_CONTROL_NONCE", "test-secret")
    with local_client(create_app(settings)) as client:
        session = register(client, "console_tester")
        lobby = client.post(
            "/api/v1/lobbies",
            headers={"Authorization": f"Bearer {session['access_token']}"},
            json={"name": "Arena Teste", "visibility": "public", "capacity": 2, "rounds": 5, "map_id": "classic", "seed": 1, "bots": 0},
        )
        assert lobby.status_code == 201, lobby.text
        auth = {"X-Groundfire-Control": "test-secret"}
        snapshot = client.get("/console/api/snapshot", headers=auth).json()
        assert snapshot["metrics"]["users"] == 1
        assert snapshot["metrics"]["lobbies"] == 1
        assert snapshot["lobbies"][0]["name"] == "Arena Teste"
        assert snapshot["metrics"]["workers"] == 0
        backup = client.post("/console/api/backup", headers=auth)
        assert backup.status_code == 200, backup.text
        destination = Path(backup.json()["directory"]) / backup.json()["file"]
        assert destination.is_file()
        metadata = json.loads(destination.with_suffix(".json").read_text(encoding="utf-8"))
        assert metadata["sha256"] == hashlib.sha256(destination.read_bytes()).hexdigest()
        assert client.post("/console/api/stop").status_code == 401


def test_gui_command_starts_service_with_browser_on_local_profile(settings, monkeypatch):
    monkeypatch.setattr(cli, "_root", lambda: settings.root)
    called = []
    monkeypatch.setattr(cli, "start", lambda *, open_console=False: called.append(open_console) or 0)
    assert cli.main(["gui"]) == 0
    assert called == [True]


def test_gui_command_opens_existing_service_before_exiting(settings, monkeypatch):
    monkeypatch.setattr(cli, "_root", lambda: settings.root)
    runtime = settings.root / "data" / "service.pid.json"
    runtime.parent.mkdir()
    runtime.write_text(json.dumps({"nonce": "existing-key"}), encoding="utf-8")
    opened = []
    monkeypatch.setattr(cli, "_open_console", lambda *args: opened.append(args))

    class Ready:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(cli.urllib.request, "urlopen", lambda *_args, **_kwargs: Ready())
    assert cli.main(["gui"]) == 0
    assert opened == [("127.0.0.1", 27880, "existing-key")]
