from __future__ import annotations

import json

from scripts.build_visual_review import build_review


def test_capture_is_pending_and_changed_content_invalidates_review(tmp_path):
    for runtime in ("python", "godot"):
        image = tmp_path / "captures" / "1024x768" / runtime / "arena.png"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"same capture")
    result = build_review(tmp_path)
    assert result["pairs"][0]["review"]["status"] == "pending"
    result["pairs"][0]["review"] = {"status": "reviewed", "reviewer": "fixture", "notes": "Layout examined"}
    (tmp_path / "visual-review.json").write_text(json.dumps(result))
    assert build_review(tmp_path)["pairs"][0]["review"]["reviewer"] == "fixture"
    image.write_bytes(b"new capture")
    assert build_review(tmp_path)["pairs"][0]["review"]["status"] == "pending"


def test_missing_counterpart_cannot_be_reviewed(tmp_path):
    image = tmp_path / "captures" / "640x480" / "python" / "arena.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"capture")
    result = build_review(tmp_path)
    assert result["pairs"][0]["review"]["status"] == "missing-capture"
