#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT_DIR/scripts/repo_paths.sh"
repo_paths_init
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
    PYTHON_BIN="${PYTHON_BIN_FALLBACK:-python}"
fi

"$PYTHON_BIN" "$ROOT_DIR/scripts/validate_godot_migration_contract.py"
"$PYTHON_BIN" "$ROOT_DIR/scripts/export_classic_reference_fixture.py" --check
"$PYTHON_BIN" "$ROOT_DIR/scripts/export_classic_replay.py" --check
"$ROOT_DIR/scripts/validate_godot.sh"
"$PYTHON_BIN" "$ROOT_DIR/scripts/validate_godot_udp_integration.py"

export PYTHONPATH
PYTHONPATH="$(repo_pythonpath)"
"$PYTHON_BIN" -m pytest -q \
    "$ROOT_DIR/tests/test_godot_migration_scaffold.py" \
    "$ROOT_DIR/tests/test_classic_reference_fixture.py" \
    "$ROOT_DIR/tests/test_classic_replay_comparator.py" \
    "$ROOT_DIR/tests/test_external_service_client_contract.py" \
    "$ROOT_DIR/tests/test_groundfire_net_module.py" \
    "$ROOT_DIR/tests/test_online_match_simulation.py" \
    "$ROOT_DIR/tests/test_server_browser_real_network_paths.py" \
    "$ROOT_DIR/tests/test_hosted_deployment_verifier.py" \
    "$ROOT_DIR/tests/test_replicated_scene.py" \
    "$ROOT_DIR/tests/test_port_fidelity.py" \
    "$ROOT_DIR/tests/test_landscape_fidelity.py"

printf 'Godot migration fidelity gate passed.\n'
