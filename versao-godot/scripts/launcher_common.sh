#!/usr/bin/env bash

# Groundfire Godot edition — helpers standalone (ST03/ST04).
# Usa somente arquivos dentro desta pasta (versao-godot/). Nunca le ../tools,
# a edicao Python irma, o venv da raiz ou a raiz do repositorio.

GODOT_LAUNCHER_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
GODOT_LAUNCHER_PROJECT="$GODOT_LAUNCHER_DIR/godot"
GODOT_EDITION_DIR="$GODOT_LAUNCHER_DIR"
# Alias historico: aponta para a propria edicao (nunca para a raiz).
GODOT_LAUNCHER_ROOT="$GODOT_LAUNCHER_DIR"

godot_platform_dir() {
    case "$(uname -s 2>/dev/null || printf unknown)" in
        Linux*) printf 'linux' ;;
        MINGW*|MSYS*|CYGWIN*|Windows*) printf 'windows' ;;
        Darwin*) printf 'macos' ;;
        *) printf 'linux' ;;
    esac
}

godot_launcher_find_binary() {
    local candidate
    local platform
    platform=$(godot_platform_dir)
    # 1) Binarios incluidos na propria edicao (ST06).
    for candidate in \
        "$GODOT_EDITION_DIR/runtime/$platform/Groundfire" \
        "$GODOT_EDITION_DIR/runtime/$platform/Groundfire.exe" \
        "$GODOT_EDITION_DIR/runtime/$platform/Godot" \
        "$GODOT_EDITION_DIR/runtime/$platform/godot" \
        "$GODOT_EDITION_DIR/runtime/linux/Groundfire.x86_64" \
        "$GODOT_EDITION_DIR/runtime/windows/Groundfire.exe"; do
        if [[ -x "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    # 2) Override explicito / sistema (desenvolvimento de fonte).
    if [[ -n "${GODOT_BIN:-}" ]]; then
        if [[ -x "$GODOT_BIN" ]]; then
            printf '%s\n' "$GODOT_BIN"
            return 0
        fi
        if command -v "$GODOT_BIN" >/dev/null 2>&1; then
            command -v "$GODOT_BIN"
            return 0
        fi
        printf 'Godot nao encontrado em GODOT_BIN=%s\n' "$GODOT_BIN" >&2
        return 1
    fi
    for candidate in godot godot4 Godot; do
        if command -v "$candidate" >/dev/null 2>&1; then
            command -v "$candidate"
            return 0
        fi
    done
    printf 'Godot nao encontrado. Coloque o binario em versao-godot/runtime/<plataforma>/ ou defina GODOT_BIN.\n' >&2
    return 1
}

godot_launcher_require_project() {
    if [[ ! -f "$GODOT_LAUNCHER_PROJECT/project.godot" ]]; then
        printf 'Projeto Godot nao encontrado: %s\n' "$GODOT_LAUNCHER_PROJECT/project.godot" >&2
        return 1
    fi
}

godot_launcher_configure_python() {
    # Companion headless local (ST04). Nunca usa a edicao irma nem o venv da raiz.
    if [[ -n "${GROUNDFIRE_LAUNCHER_PYTHON:-}" ]]; then
        return 0
    fi
    local candidate
    for candidate in \
        "$GODOT_EDITION_DIR/.venv/bin/python" \
        "$GODOT_EDITION_DIR/.venv/Scripts/python.exe" \
        python3.14 python3.13 python3.12 python3.11 python3.10 python3 python; do
        if [[ "$candidate" == *"/"* ]]; then
            if [[ -x "$candidate" ]]; then
                export GROUNDFIRE_LAUNCHER_PYTHON="$candidate"
                return 0
            fi
            continue
        fi
        if command -v "$candidate" >/dev/null 2>&1 && \
            "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
            export GROUNDFIRE_LAUNCHER_PYTHON="$candidate"
            return 0
        fi
    done
    printf 'Python 3.10 ou superior nao encontrado para o companion LAN.\n' >&2
    return 1
}

godot_launcher_userdata_dir() {
    if [[ -n "${GROUNDFIRE_USERDATA_DIR:-}" ]]; then
        printf '%s\n' "$GROUNDFIRE_USERDATA_DIR"
    else
        printf '%s\n' "$GODOT_EDITION_DIR/userdata"
    fi
}

godot_launcher_require_userdata_writable() {
    local dir
    dir=$(godot_launcher_userdata_dir)
    if ! mkdir -p "$dir" 2>/dev/null; then
        printf 'Erro: pasta userdata nao e gravavel: %s\n' "$dir" >&2
        return 1
    fi
    if ! touch "$dir/.writetest" 2>/dev/null; then
        printf 'Erro: pasta userdata nao e gravavel: %s\n' "$dir" >&2
        return 1
    fi
    rm -f "$dir/.writetest"
}

godot_launcher_companion_entry() {
    # Servidor/gateway proprios da edicao (ST04): runtime/<plataforma>/ ou headless local.
    local platform
    platform=$(godot_platform_dir)
    local candidate
    for candidate in \
        "$GODOT_EDITION_DIR/runtime/$platform/groundfire-server" \
        "$GODOT_EDITION_DIR/runtime/$platform/groundfire-server.exe" \
        "$GODOT_EDITION_DIR/runtime/linux/groundfire-server" \
        "$GODOT_EDITION_DIR/runtime/windows/groundfire-server.exe"; do
        if [[ -x "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    # Fallback fonte: headless vendorizado dentro da edicao.
    if [[ -d "$GODOT_EDITION_DIR/runtime/headless" ]]; then
        printf 'headless:%s\n' "$GODOT_EDITION_DIR/runtime/headless"
        return 0
    fi
    return 1
}
