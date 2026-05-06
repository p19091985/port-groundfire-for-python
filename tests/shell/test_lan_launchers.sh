#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN="${GROUNDFIRE_LAUNCHER_PYTHON:-$PROJECT_DIR/.venv/bin/python}"

fail() {
    printf 'FAIL: %s\n' "$1" >&2
    exit 1
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    if [[ "$haystack" != *"$needle"* ]]; then
        fail "saida nao contem: $needle"
    fi
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    if [[ "$haystack" == *"$needle"* ]]; then
        fail "saida contem texto inesperado: $needle"
    fi
}

run_with_logs() {
    local temp_dir="$1"
    shift
    GROUNDFIRE_LAUNCHER_PYTHON="$PYTHON_BIN" \
    GROUNDFIRE_LAUNCHER_LOG_DIR="$temp_dir" \
        "$@"
}

main() {
    local temp_dir
    temp_dir=$(mktemp -d)
    SHELL_TEST_TEMP_DIR="$temp_dir"
    trap 'rm -rf "$SHELL_TEST_TEMP_DIR"' EXIT

    local output
    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-all.sh" -A --port 27781 --discovery-port 27782 --dry-run)
    assert_contains "$output" "DRY-RUN server launcher command:"
    assert_contains "$output" "DRY-RUN clients launcher command:"
    assert_contains "$output" "DRY-RUN server command:"
    assert_contains "$output" "DRY-RUN client 6 command:"
    assert_contains "$output" "iniciar-server.sh"
    assert_contains "$output" "iniciar-clientes.sh"
    assert_contains "$output" "--visible-count 6"
    assert_not_contains "$output" "--headless-client"
    assert_contains "$output" "--keepalive-seconds 86400"
    [[ -f "$temp_dir/all_debug.log" ]] || fail "all_debug.log nao foi criado"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-all.sh" --help)
    assert_contains "$output" "Modos de acesso:"
    assert_contains "$output" "--menu"
    assert_contains "$output" "--cli"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-all.sh" --cli --sem-tela --dry-run)
    assert_contains "$output" "DRY-RUN clients launcher command:"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-all.sh" -A --preset 8 --sem-tela --dry-run)
    assert_contains "$output" "DRY-RUN client 8 command:"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-server.sh" -A --port 27780 --com-tela --dry-run)
    assert_contains "$output" "DRY-RUN server command:"
    assert_contains "$output" "DRY-RUN visible client command:"
    assert_contains "$output" "--connect 127.0.0.1:27780"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-server.sh" --cli --sem-tela --dry-run)
    assert_contains "$output" "DRY-RUN server command:"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-clientes.sh" --preset 4 -a --sem-tela --check-server --dry-run)
    assert_contains "$output" "DRY-RUN client 1 command:"
    assert_contains "$output" "DRY-RUN client 4 command:"
    assert_contains "$output" "--headless-client"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-clientes.sh" --cli -n 1 -a --sem-tela --dry-run)
    assert_contains "$output" "DRY-RUN client 1 command:"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-server.sh" -A --port 70000 --dry-run 2>&1 || true)
    assert_contains "$output" "Porta de jogo invalida"
    [[ -f "$temp_dir/server_debug.log" ]] || fail "server_debug.log nao foi criado"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-server.sh" -A --host "host invalido" --dry-run 2>&1 || true)
    assert_contains "$output" "Host invalido"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-clientes.sh" -n 2 --port banana --dry-run 2>&1 || true)
    assert_contains "$output" "Porta do servidor invalida"
    [[ -f "$temp_dir/clients_debug.log" ]] || fail "clients_debug.log nao foi criado"

    output=$(run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-clientes.sh" -n 2 --host "host invalido" --dry-run 2>&1 || true)
    assert_contains "$output" "Host do servidor invalido"

    printf 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n' > "$temp_dir/server_debug.log"
    output=$(GROUNDFIRE_LOG_MAX_BYTES=8 run_with_logs "$temp_dir" "$PROJECT_DIR/iniciar-server.sh" -A --port 27783 --dry-run)
    assert_contains "$output" "DRY-RUN server command:"
    [[ -f "$temp_dir/server_debug.log.1" ]] || fail "server_debug.log nao foi rotacionado"

    printf 'OK: shell launcher tests passed\n'
}

main "$@"
