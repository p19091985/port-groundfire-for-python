from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "scripts" / "export_classic_reference_fixture.py"
FIXTURE = ROOT / "tests" / "fixtures" / "classic_runtime_reference.json"


def _load_exporter():
    spec = importlib.util.spec_from_file_location("classic_reference_exporter", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ClassicReferenceFixtureTests(unittest.TestCase):
    def test_fixture_matches_python_reference(self):
        expected = _load_exporter().build_fixture()
        actual = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)

    def test_fixture_captures_simultaneous_and_slot_identity_contracts(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual([item[0] for item in data["simultaneous_round"]["update_trace"]], ["landscape", "player_0", "player_1"])
        self.assertEqual(data["online_slot_2"]["predicted_entity_ids"], [42])
        self.assertEqual(data["shop"]["initial_done"], [False] * 8)

    def test_asset_manifest_records_preserved_converted_and_unused_assets(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        assets = {item["key"]: item for item in data["assets"]}
        self.assertEqual(len(assets), 22)
        self.assertEqual(assets["damage"]["transfer"], "preserved")
        self.assertEqual(assets["damage"]["usage"], "declared_reference_unused")
        self.assertEqual(assets["nuke"]["transfer"], "converted")
        self.assertEqual(
            assets["nuke"]["python_audio"]["duration_seconds"],
            assets["nuke"]["godot_audio"]["duration_seconds"],
        )
        self.assertTrue(all(item["godot_sha256"] for item in assets.values()))


if __name__ == "__main__":
    unittest.main()
