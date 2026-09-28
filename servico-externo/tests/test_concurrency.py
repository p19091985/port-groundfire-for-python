from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from gf_service.domain import GroundfireService
from gf_service.store import Store


def test_only_one_competing_reservation_wins_last_slot(settings):
    service = GroundfireService(Store(settings.database_path), settings)
    host = service.register("host_user", "Host", "senha-host-123")
    first = service.register("first_user", "First", "senha-first-123")
    second = service.register("second_user", "Second", "senha-second-123")
    lobby = service.create_lobby(
        host["user"]["user_id"],
        {"name": "One slot", "visibility": "public", "capacity": 2, "rounds": 10, "map_id": "classic", "seed": 1},
    )

    def queue(user_id: str) -> str:
        result = service.queue(user_id, {"criteria": {"target_lobby_id": lobby["lobby_id"]}})
        return result["state"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        states = sorted(executor.map(queue, [first["user"]["user_id"], second["user"]["user_id"]]))
    assert states == ["reserved", "searching"]
    active = service.store.one(
        "SELECT COUNT(*) count FROM reservation_members rm JOIN reservations r ON r.reservation_id=rm.reservation_id WHERE r.state='held'"
    )["count"]
    assert active == 1


def test_expired_reservation_releases_capacity(settings):
    now = [1_000.0]
    service = GroundfireService(Store(settings.database_path), settings, clock=lambda: now[0])
    host = service.register("expire_host", "Host", "senha-host-123")
    first = service.register("expire_first", "First", "senha-first-123")
    second = service.register("expire_second", "Second", "senha-second-123")
    lobby = service.create_lobby(
        host["user"]["user_id"],
        {"name": "Expiring", "visibility": "public", "capacity": 2, "rounds": 10, "map_id": "classic", "seed": 1},
    )
    assert (
        service.queue(first["user"]["user_id"], {"criteria": {"target_lobby_id": lobby["lobby_id"]}})["state"]
        == "reserved"
    )
    now[0] += settings.reservation_ttl_seconds + 1
    assert (
        service.queue(second["user"]["user_id"], {"criteria": {"target_lobby_id": lobby["lobby_id"]}})["state"]
        == "reserved"
    )
