import json
import tempfile
import unittest
from pathlib import Path

from src.assets import DEFAULT_MANIFEST_PATH, find_spec_by_key, load_sound_specs, load_texture_specs, resolve_asset_path


class AssetManifestTests(unittest.TestCase):
    def test_manifest_loading_and_resolution_prefers_first_existing_candidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "data"
            data_dir.mkdir()
            (data_dir / "blast.png").write_bytes(b"png")
            (data_dir / "blast.tga").write_bytes(b"tga")
            (data_dir / "quake.wav").write_bytes(b"wav")

            manifest_path = root / "assets.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "textures": [
                            {
                                "id": 0,
                                "key": "blast",
                                "candidates": ["data/blast.png", "data/blast.tga"],
                            }
                        ],
                        "sounds": [
                            {
                                "id": 2,
                                "key": "quake",
                                "candidates": ["data/quake.wav"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            texture_specs = load_texture_specs(manifest_path)
            sound_specs = load_sound_specs(manifest_path)

            texture_spec = find_spec_by_key(texture_specs, "blast")
            sound_spec = find_spec_by_key(sound_specs, "quake")

            self.assertIsNotNone(texture_spec)
            self.assertIsNotNone(sound_spec)
            self.assertEqual(resolve_asset_path(texture_spec.candidates, root=root), data_dir / "blast.png")
            self.assertEqual(resolve_asset_path(sound_spec.candidates, root=root), data_dir / "quake.wav")

    def test_runtime_manifest_uses_png_only_for_textures(self):
        texture_specs = load_texture_specs(DEFAULT_MANIFEST_PATH)

        self.assertTrue(texture_specs)
        self.assertTrue(all(spec.candidates == (spec.candidates[0],) for spec in texture_specs))
        self.assertTrue(all(spec.candidates[0].endswith(".png") for spec in texture_specs))


if __name__ == "__main__":
    unittest.main()
