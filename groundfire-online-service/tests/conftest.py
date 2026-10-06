from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gf_service.app import create_app  # noqa: E402
from gf_service.config import Settings  # noqa: E402


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        root=tmp_path,
        database=str(tmp_path / "service.sqlite3"),
        public_base_url="http://testserver",
        admission_redeem_enabled=False,
        legacy_master_enabled=False,
    )


@pytest.fixture
def app(settings: Settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    with TestClient(app) as value:
        yield value


def register(client: TestClient, handle: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"handle": handle, "display_name": handle.title(), "password": f"Senha-{handle}-1234"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def headers(session: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}
