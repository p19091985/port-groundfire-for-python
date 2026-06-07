#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

echo "=========================================================="
echo " Groundfire GPG Key Generation for GitHub Releases"
echo "=========================================================="
echo ""

KEY_DIR=$(mktemp -d)
trap 'rm -rf "$KEY_DIR"' EXIT

export GNUPGHOME="$KEY_DIR"
cat <<EOF > "$KEY_DIR/gen-key-script"
%echo Generating Groundfire Release Key
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: Groundfire Release Automation
Name-Comment: GitHub Actions
Name-Email: releases@groundfire.net
Expire-Date: 0
%no-ask-passphrase
%no-protection
%commit
%echo Done
EOF

echo "Generating new 4096-bit RSA keypair (this might take a moment)..."
gpg --batch --gen-key "$KEY_DIR/gen-key-script" >/dev/null 2>&1

KEY_FINGERPRINT=$(gpg --list-secret-keys --with-colons | grep "^fpr:" | head -n 1 | cut -d: -f10)

echo ""
echo "Exporting PRIVATE KEY..."
PRIVATE_KEY=$(gpg --armor --export-secret-keys "$KEY_FINGERPRINT")

echo "=========================================================="
echo " ACTION REQUIRED: Update GitHub Secrets"
echo "=========================================================="
echo ""
echo "1. Go to your repository settings on GitHub:"
echo "   Settings -> Secrets and variables -> Actions"
echo ""
echo "2. Create a new repository secret named: RELEASE_GPG_PRIVATE_KEY"
echo "   Paste the following block (including BEGIN/END lines):"
echo ""
echo "$PRIVATE_KEY"
echo ""
echo "----------------------------------------------------------"
echo ""
echo "3. Create a new repository secret named: RELEASE_SIGN_KEY"
echo "   Paste the following exact fingerprint:"
echo ""
echo "$KEY_FINGERPRINT"
echo ""
echo "=========================================================="
echo "Once these are saved, pushing a v* tag will automatically"
echo "sign your release assets."
