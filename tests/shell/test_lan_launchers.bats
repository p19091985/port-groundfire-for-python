#!/usr/bin/env bats

setup() {
    SCRIPT_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)"
    PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
    PYTHON_BIN="${GROUNDFIRE_LAUNCHER_PYTHON:-$PROJECT_DIR/.venv/bin/python}"
    TEST_LOG_DIR="$(mktemp -d)"
}

teardown() {
    rm -rf "$TEST_LOG_DIR"
}

run_launcher() {
    GROUNDFIRE_LAUNCHER_PYTHON="$PYTHON_BIN" \
    GROUNDFIRE_LAUNCHER_LOG_DIR="$TEST_LOG_DIR" \
        "$@"
}

@test "iniciar-all monta servidor e seis clientes IA via scripts" {
    run run_launcher "$PROJECT_DIR/iniciar-all.sh" -A --port 27781 --discovery-port 27782 --dry-run

    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY-RUN server launcher command:"* ]]
    [[ "$output" == *"DRY-RUN clients launcher command:"* ]]
    [[ "$output" == *"DRY-RUN client 6 command:"* ]]
    [[ "$output" == *"iniciar-server.sh"* ]]
    [[ "$output" == *"iniciar-clientes.sh"* ]]
    [[ "$output" == *"--visible-count 6"* ]]
    [[ "$output" != *"--headless-client"* ]]
    [[ -f "$TEST_LOG_DIR/all_debug.log" ]]
}

@test "launchers documentam modos CLI e Ttk" {
    run run_launcher "$PROJECT_DIR/iniciar-all.sh" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Modos de acesso:"* ]]
    [[ "$output" == *"--menu"* ]]
    [[ "$output" == *"--cli"* ]]

    run run_launcher "$PROJECT_DIR/iniciar-server.sh" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Modos de acesso:"* ]]
    [[ "$output" == *"--menu"* ]]
    [[ "$output" == *"--cli"* ]]

    run run_launcher "$PROJECT_DIR/iniciar-clientes.sh" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Modos de acesso:"* ]]
    [[ "$output" == *"--menu"* ]]
    [[ "$output" == *"--cli"* ]]
}

@test "launchers aceitam modo CLI explicito" {
    run run_launcher "$PROJECT_DIR/iniciar-all.sh" --cli --sem-tela --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY-RUN clients launcher command:"* ]]

    run run_launcher "$PROJECT_DIR/iniciar-server.sh" --cli --sem-tela --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY-RUN server command:"* ]]

    run run_launcher "$PROJECT_DIR/iniciar-clientes.sh" --cli -n 1 -a --sem-tela --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY-RUN client 1 command:"* ]]
}

@test "iniciar-server pode abrir cliente visivel por dry-run" {
    run run_launcher "$PROJECT_DIR/iniciar-server.sh" -A --port 27780 --com-tela --dry-run

    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY-RUN server command:"* ]]
    [[ "$output" == *"DRY-RUN visible client command:"* ]]
    [[ "$output" == *"--connect 127.0.0.1:27780"* ]]
}

@test "launchers aceitam presets frequentes" {
    run run_launcher "$PROJECT_DIR/iniciar-all.sh" -A --preset 8 --sem-tela --dry-run

    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY-RUN client 8 command:"* ]]

    run run_launcher "$PROJECT_DIR/iniciar-clientes.sh" --preset 4 -a --sem-tela --dry-run

    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY-RUN client 4 command:"* ]]
}

@test "iniciar-clientes permite IA totalmente headless para automacao" {
    run run_launcher "$PROJECT_DIR/iniciar-clientes.sh" -n 2 -a --sem-tela --dry-run

    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY-RUN client 1 command:"* ]]
    [[ "$output" == *"DRY-RUN client 2 command:"* ]]
    [[ "$output" == *"--headless-client"* ]]
}

@test "iniciar-clientes registra verificacao UDP em dry-run" {
    run run_launcher "$PROJECT_DIR/iniciar-clientes.sh" -n 2 -a --sem-tela --check-server --dry-run

    [ "$status" -eq 0 ]
    [[ "$output" == *"Verificando alcance UDP"* ]]
    [[ "$output" == *"Dry-run ativo"* ]]
}

@test "launchers rejeitam portas e hosts invalidos" {
    run run_launcher "$PROJECT_DIR/iniciar-server.sh" -A --port 70000 --dry-run
    [ "$status" -eq 2 ]
    [[ "$output" == *"Porta de jogo invalida"* ]]

    run run_launcher "$PROJECT_DIR/iniciar-server.sh" -A --host "host invalido" --dry-run
    [ "$status" -eq 2 ]
    [[ "$output" == *"Host invalido"* ]]

    run run_launcher "$PROJECT_DIR/iniciar-clientes.sh" -n 2 --port banana --dry-run
    [ "$status" -eq 2 ]
    [[ "$output" == *"Porta do servidor invalida"* ]]

    run run_launcher "$PROJECT_DIR/iniciar-clientes.sh" -n 2 --host "host invalido" --dry-run
    [ "$status" -eq 2 ]
    [[ "$output" == *"Host do servidor invalido"* ]]
}

@test "log central rotaciona quando passa do limite" {
    printf 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n' > "$TEST_LOG_DIR/server_debug.log"

    run env \
        GROUNDFIRE_LOG_MAX_BYTES=8 \
        GROUNDFIRE_LAUNCHER_PYTHON="$PYTHON_BIN" \
        GROUNDFIRE_LAUNCHER_LOG_DIR="$TEST_LOG_DIR" \
        "$PROJECT_DIR/iniciar-server.sh" -A --port 27783 --dry-run

    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY-RUN server command:"* ]]
    [[ -f "$TEST_LOG_DIR/server_debug.log.1" ]]
}
