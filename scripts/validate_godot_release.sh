#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/scripts/repo_paths.sh"
repo_paths_init
RUN_BROWSER_QA="${GROUNDFIRE_RELEASE_BROWSER_QA:-0}"
RUN_VISUALS="${GROUNDFIRE_RELEASE_VISUALS:-0}"
PACKAGE_RELEASE="${GROUNDFIRE_RELEASE_PACKAGE:-0}"
SIGN_RELEASE="${GROUNDFIRE_RELEASE_SIGN:-0}"

usage() {
    cat <<'EOF'
Usage: scripts/validate_godot_release.sh [--browser-qa] [--visuals] [--package] [--sign]

Runs the release gate that should protect the Godot migration from changing
the Python/Pygame user experience.

Options:
  --browser-qa   Run scripts/qa_godot_web.sh --check after fidelity validation.
  --visuals      Run scripts/validate_godot_visuals.sh --check.
  --package      Run scripts/package_godot_release.sh and verify SHA256SUMS.
  --sign         After packaging, run scripts/sign_godot_release.sh to produce
                 a detached GPG signature. Requires a GPG secret key and
                 GROUNDFIRE_SIGN_KEY to be set (or the default key is used).
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --browser-qa)
            RUN_BROWSER_QA=1
            ;;
        --visuals)
            RUN_VISUALS=1
            ;;
        --package)
            PACKAGE_RELEASE=1
            ;;
        --sign)
            SIGN_RELEASE=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            exit 2
            ;;
    esac
    shift
done

"$ROOT_DIR/scripts/validate_godot_fidelity.sh"

if [[ "$RUN_VISUALS" == "1" ]]; then
    "$ROOT_DIR/scripts/validate_godot_visuals.sh" --check
fi

if [[ "$RUN_BROWSER_QA" == "1" ]]; then
    "$ROOT_DIR/scripts/qa_godot_web.sh" --check
fi

if [[ "$PACKAGE_RELEASE" == "1" ]]; then
    "$ROOT_DIR/scripts/package_godot_release.sh"
    latest_checksums=$(find "$DIST_DIR" -maxdepth 1 -name '*-SHA256SUMS' -type f -printf '%T@ %p\n' \
        | sort -nr \
        | awk 'NR == 1 {print $2}')
    if [[ -z "${latest_checksums:-}" ]]; then
        printf 'No SHA256SUMS file produced under dist/.\n' >&2
        exit 1
    fi
    (
        cd "$DIST_DIR"
        sha256sum --check "$(basename "$latest_checksums")"
    )
    if [[ "$SIGN_RELEASE" == "1" ]]; then
        GROUNDFIRE_CHECKSUMS_FILE="$latest_checksums" \
            "$ROOT_DIR/scripts/sign_godot_release.sh"
    fi
fi

printf 'Godot release validation gate passed.\n'
