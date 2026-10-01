"""Index paired captures without treating generated images as accepted reviews."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def build_review(output: Path, *, diffs: bool = False) -> dict:
    target = output / "visual-review.json"
    previous = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    prior = {item["id"]: item for item in previous.get("pairs", [])}
    pairs = []
    for python_image in sorted((output / "captures").glob("*/python/*.png")):
        godot_image = python_image.parent.parent / "godot" / python_image.name
        key = f"{python_image.parent.parent.name}/{python_image.stem}"
        paths = {"python": python_image, "godot": godot_image}
        hashes = {
            name: hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            for name, path in paths.items()
        }
        old = prior.get(key, {})
        review = old.get("review", {}) if old.get("sha256") == hashes else {}
        record = {
            "id": key,
            "images": {name: path.relative_to(output).as_posix() for name, path in paths.items()},
            "sha256": hashes,
            "review": review
            or {"status": "pending", "reviewer": "", "date": "", "regions": [], "differences": [], "notes": ""},
        }
        if not godot_image.is_file():
            record["review"] = {"status": "missing-capture"}
        elif diffs:
            record["metrics"] = _diff(output, python_image, godot_image)
        pairs.append(record)
    data = {"schema": 1, "note": "Pixel metrics are diagnostics, not visual acceptance.", "pairs": pairs}
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def _diff(output: Path, python_image: Path, godot_image: Path) -> dict:
    import pygame

    reference = pygame.image.load(str(python_image))
    actual = pygame.image.load(str(godot_image))
    if reference.get_size() != actual.get_size():
        return {"size_mismatch": [reference.get_size(), actual.get_size()]}
    positive = reference.copy()
    positive.blit(actual, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    negative = actual.copy()
    negative.blit(reference, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    positive.blit(negative, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    difference = output / "diffs" / python_image.parent.parent.name / python_image.name
    difference.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(positive, str(difference))
    channels = pygame.image.tobytes(positive, "RGB")
    changed = sum(any(channels[offset : offset + 3]) for offset in range(0, len(channels), 3))
    return {
        "diff": difference.relative_to(output).as_posix(),
        "changed_pixels": changed,
        "total_pixels": len(channels) // 3,
        "mean_absolute_channel_difference": sum(channels) / len(channels),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--diffs", action="store_true")
    args = parser.parse_args()
    data = build_review(args.output, diffs=args.diffs)
    print(f"Indexed {len(data['pairs'])} pairs; review remains explicit: {args.output / 'visual-review.json'}")


if __name__ == "__main__":
    main()
