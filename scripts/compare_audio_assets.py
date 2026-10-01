#!/usr/bin/env python3
"""Measure decoded PCM, duration, onset and RMS of the ten classic sounds.

RMS is an asset-level measurement, not a device loudness or listening test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def measure(path: Path) -> dict:
    with wave.open(str(path), "rb") as stream:
        channels, width, rate, frames = (
            stream.getnchannels(),
            stream.getsampwidth(),
            stream.getframerate(),
            stream.getnframes(),
        )
        pcm = stream.readframes(frames)
    if width == 1:
        values = [(sample - 128) / 128.0 for sample in pcm]
    elif width == 2:
        values = [sample[0] / 32768.0 for sample in struct.iter_unpack("<h", pcm)]
    else:
        raise ValueError(f"Unsupported PCM width: {path}: {width}")
    rms = math.sqrt(sum(sample * sample for sample in values) / len(values))
    onset = next((index // channels / rate for index, value in enumerate(values) if abs(value) >= 0.01), None)
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "pcm_sha256": hashlib.sha256(pcm).hexdigest(),
        "channels": channels,
        "bits": width * 8,
        "rate_hz": rate,
        "duration_s": frames / rate,
        "onset_1_percent_s": onset,
        "rms_dbfs": 20 * math.log10(max(rms, 1e-12)),
        "peak": max(map(abs, values)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sounds = json.loads((ROOT / "versao-python/conf/assets.json").read_text())["sounds"]
    checks = []
    for sound in sounds:
        relative = Path(sound["candidates"][0])
        reference = measure(ROOT / "versao-python" / relative)
        candidate = measure(ROOT / "versao-godot/godot/assets" / relative.name)
        duration_error = abs(reference["duration_s"] - candidate["duration_s"])
        rms_error = abs(reference["rms_dbfs"] - candidate["rms_dbfs"])
        onset_error = abs(reference["onset_1_percent_s"] - candidate["onset_1_percent_s"])
        preserved = reference["pcm_sha256"] == candidate["pcm_sha256"]
        passed = (preserved or sound["key"] == "nuke") and (
            duration_error <= 1 / 60
            and onset_error <= 1 / 60
            and rms_error <= 1
            and reference["channels"] == candidate["channels"]
        )
        checks.append(
            {
                "id": sound["key"],
                "status": "passed" if passed else "failed",
                "python": reference,
                "godot": candidate,
                "pcm_identical": preserved,
                "duration_error_s": duration_error,
                "onset_error_s": onset_error,
                "rms_error_db": rms_error,
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"checks": checks, "listening": "not-performed"}, indent=2) + "\n")
    for check in checks:
        print(
            check["id"], check["status"], f"duration={check['duration_error_s']:.6f}s RMS={check['rms_error_db']:.4f}dB"
        )
    return int(any(check["status"] == "failed" for check in checks))


if __name__ == "__main__":
    raise SystemExit(main())
