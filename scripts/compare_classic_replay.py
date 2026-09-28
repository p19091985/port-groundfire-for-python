#!/usr/bin/env python3
"""Compare normalized Python/Godot replay files and report the first divergence."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


class ReplayDifference(AssertionError):
    pass


def compare(expected: Any, actual: Any, *, tolerance: float = 1e-5, path: str = "$") -> None:
    if isinstance(expected, bool) or isinstance(actual, bool):
        if expected is not actual:
            raise ReplayDifference(f"{path}: expected {expected!r}, got {actual!r}")
        return
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if not math.isclose(float(expected), float(actual), rel_tol=0.0, abs_tol=tolerance):
            raise ReplayDifference(f"{path}: expected {expected!r}, got {actual!r}; tolerance={tolerance}")
        return
    if type(expected) is not type(actual):
        raise ReplayDifference(f"{path}: expected type {type(expected).__name__}, got {type(actual).__name__}")
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            missing = sorted(expected.keys() - actual.keys())
            extra = sorted(actual.keys() - expected.keys())
            raise ReplayDifference(f"{path}: key mismatch; missing={missing}, extra={extra}")
        for key in expected:
            compare(expected[key], actual[key], tolerance=tolerance, path=f"{path}.{key}")
        return
    if isinstance(expected, list):
        if len(expected) != len(actual):
            raise ReplayDifference(f"{path}: expected {len(expected)} items, got {len(actual)}")
        for index, (left, right) in enumerate(zip(expected, actual, strict=True)):
            compare(left, right, tolerance=tolerance, path=f"{path}[{index}]")
        return
    if expected != actual:
        raise ReplayDifference(f"{path}: expected {expected!r}, got {actual!r}")


def compare_files(expected_path: Path, actual_path: Path, *, tolerance: float = 1e-5) -> None:
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    actual = json.loads(actual_path.read_text(encoding="utf-8"))
    compare(expected, actual, tolerance=tolerance)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("expected", type=Path)
    parser.add_argument("actual", type=Path)
    parser.add_argument("--tolerance", type=float, default=1e-5)
    args = parser.parse_args()
    try:
        compare_files(args.expected, args.actual, tolerance=args.tolerance)
    except ReplayDifference as exc:
        print(f"Classic replay comparison failed: {exc}")
        return 1
    print("Classic replay comparison passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
