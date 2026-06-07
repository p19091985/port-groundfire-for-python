#!/usr/bin/env bash
# sign_godot_release.sh — produce a detached GPG signature for the latest
# Groundfire Godot release SHA256SUMS file under dist/.
#
# Usage:
#   scripts/sign_godot_release.sh [--checksums <path>] [--key <fingerprint>]
#
# Environment variables:
#   GROUNDFIRE_SIGN_KEY       GPG key fingerprint or email to sign with.
#                             Defaults to the first secret key available.
#   GROUNDFIRE_CHECKSUMS_FILE Absolute path to the SHA256SUMS file to sign.
#                             Defaults to the most recent *-SHA256SUMS under dist/.
#
# The output file is <checksums>-sig placed next to the checksums file.
# Running this script requires GPG and an imported secret key.
#
# To verify the signature offline:
#   gpg --verify dist/<prefix>-SHA256SUMS.sig dist/<prefix>-SHA256SUMS
set -Eeuo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
DIST_DIR="$ROOT_DIR/dist"
SIGN_KEY="${GROUNDFIRE_SIGN_KEY:-}"
CHECKSUMS_FILE="${GROUNDFIRE_CHECKSUMS_FILE:-}"

usage() {
    cat <<'EOF'
Usage: scripts/sign_godot_release.sh [--checksums <path>] [--key <fingerprint>]

Creates a detached GPG signature (<checksums-file>.sig) for the Groundfire
Godot release SHA256SUMS file.

Options:
  --checksums <path>       Path to the SHA256SUMS file to sign.
                           Defaults to the most recent *-SHA256SUMS in dist/.
  --key <fingerprint>      GPG key fingerprint or email address to sign with.
                           Defaults to GROUNDFIRE_SIGN_KEY or the first secret key.
  -h, --help               Show this help message.

Environment variables (take lower precedence than CLI flags):
  GROUNDFIRE_SIGN_KEY       Key fingerprint or email.
  GROUNDFIRE_CHECKSUMS_FILE Path to the checksums file.

Example:
  scripts/sign_godot_release.sh --key ABCDEF1234567890
  gpg --verify dist/groundfire-godot-0.25.0-SHA256SUMS.sig \
               dist/groundfire-godot-0.25.0-SHA256SUMS
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --checksums)
            CHECKSUMS_FILE="$2"
            shift 2
            ;;
        --key)
            SIGN_KEY="$2"
            shift 2
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
done

# Locate the checksums file if not provided explicitly.
if [[ -z "${CHECKSUMS_FILE:-}" ]]; then
    CHECKSUMS_FILE=$(find "$DIST_DIR" -maxdepth 1 -name '*-SHA256SUMS' -type f -printf '%T@ %p\n' \
        | sort -nr \
        | awk 'NR == 1 {print $2}')
    if [[ -z "${CHECKSUMS_FILE:-}" ]]; then
        printf 'No SHA256SUMS file found under %s.\n' "$DIST_DIR" >&2
        printf 'Run scripts/package_godot_release.sh first, or pass --checksums <path>.\n' >&2
        exit 1
    fi
fi

if [[ ! -f "$CHECKSUMS_FILE" ]]; then
    printf 'Checksums file not found: %s\n' "$CHECKSUMS_FILE" >&2
    exit 1
fi

# Verify GPG is available.
if ! command -v gpg &>/dev/null; then
    printf 'gpg not found. Install GnuPG to use this signing script.\n' >&2
    exit 1
fi

# Build the GPG signing command.
SIG_FILE="${CHECKSUMS_FILE}.sig"
GPG_ARGS=(--batch --yes --armor --detach-sign --output "$SIG_FILE")
if [[ -n "${SIGN_KEY:-}" ]]; then
    GPG_ARGS+=(--local-user "$SIGN_KEY")
fi
GPG_ARGS+=("$CHECKSUMS_FILE")

printf 'Signing: %s\n' "$(basename "$CHECKSUMS_FILE")"
printf 'Key:     %s\n' "${SIGN_KEY:-<default secret key>}"
printf 'Output:  %s\n' "$(basename "$SIG_FILE")"

gpg "${GPG_ARGS[@]}"

printf '\nSignature created: %s\n' "$SIG_FILE"
printf 'Verify with:\n'
printf '  gpg --verify %s %s\n' "$(basename "$SIG_FILE")" "$(basename "$CHECKSUMS_FILE")"
