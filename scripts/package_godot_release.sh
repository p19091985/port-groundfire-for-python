#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
DIST_DIR="$ROOT_DIR/dist"
RELEASE_NOTES_PATH="${GROUNDFIRE_RELEASE_NOTES:-}"

if [[ ! -x "$PYTHON_BIN" ]]; then
    printf 'Python executable not found: %s\n' "$PYTHON_BIN" >&2
    exit 1
fi

if [[ -n "$RELEASE_NOTES_PATH" && ! -f "$RELEASE_NOTES_PATH" ]]; then
    printf 'Release notes file not found: %s\n' "$RELEASE_NOTES_PATH" >&2
    exit 1
fi

PROJECT_VERSION="${GROUNDFIRE_RELEASE_VERSION:-}"
if [[ -z "$PROJECT_VERSION" ]]; then
    PROJECT_VERSION=$("$PYTHON_BIN" - "$ROOT_DIR/pyproject.toml" <<'PY'
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

with Path(sys.argv[1]).open("rb") as pyproject:
    print(tomllib.load(pyproject)["project"]["version"])
PY
)
fi

PACKAGE_PREFIX="${GROUNDFIRE_RELEASE_PREFIX:-groundfire-godot-$PROJECT_VERSION}"
LINUX_ARCHIVE="$DIST_DIR/${PACKAGE_PREFIX}-linux-x86_64.tar.gz"
WEB_ARCHIVE="$DIST_DIR/${PACKAGE_PREFIX}-web.zip"
MANIFEST="$DIST_DIR/${PACKAGE_PREFIX}-manifest.json"
CHECKSUMS="$DIST_DIR/${PACKAGE_PREFIX}-SHA256SUMS"

"$ROOT_DIR/scripts/export_godot.sh" all
mkdir -p "$DIST_DIR"
rm -f "$LINUX_ARCHIVE" "$WEB_ARCHIVE" "$MANIFEST" "$CHECKSUMS"

tar -C "$ROOT_DIR/build/godot" -czf "$LINUX_ARCHIVE" Groundfire.x86_64

"$PYTHON_BIN" - \
    "$ROOT_DIR" \
    "$WEB_ARCHIVE" \
    "$MANIFEST" \
    "$PROJECT_VERSION" \
    "$(basename "$LINUX_ARCHIVE")" \
    "$(basename "$WEB_ARCHIVE")" \
    "$RELEASE_NOTES_PATH" <<'PY'
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
web_archive = Path(sys.argv[2])
manifest_path = Path(sys.argv[3])
version = sys.argv[4]
linux_archive_name = sys.argv[5]
web_archive_name = sys.argv[6]
release_notes_path = Path(sys.argv[7]) if sys.argv[7] else None
web_dir = root / "build" / "godot-web"

with zipfile.ZipFile(web_archive, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(web_dir.rglob("*")):
        if path.is_file():
            archive.write(path, path.relative_to(web_dir))

manifest = {
    "name": "Groundfire Godot",
    "version": version,
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "targets": {
        "linux_x86_64": linux_archive_name,
        "web": web_archive_name,
    },
    "godot": "4.6.2.stable",
    "notes": [
        "Linux archive contains the exported desktop executable.",
        "Web archive contains the static files from build/godot-web.",
        "Release presets exclude res://tests/*.",
    ],
}
if release_notes_path is not None:
    release_notes_bytes = release_notes_path.read_bytes()
    manifest["release_notes"] = {
        "path": str(release_notes_path),
        "sha256": hashlib.sha256(release_notes_bytes).hexdigest(),
    }
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY

(
    cd "$DIST_DIR"
    sha256sum \
        "$(basename "$LINUX_ARCHIVE")" \
        "$(basename "$WEB_ARCHIVE")" \
        "$(basename "$MANIFEST")" > "$CHECKSUMS"
)

printf 'Packaged Godot release artifacts:\n'
printf '  %s\n' "$LINUX_ARCHIVE"
printf '  %s\n' "$WEB_ARCHIVE"
printf '  %s\n' "$MANIFEST"
printf '  %s\n' "$CHECKSUMS"
