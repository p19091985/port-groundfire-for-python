#!/usr/bin/env bash

repo_paths_init() {
    if [[ -z "${ROOT_DIR:-}" ]]; then
        ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
    fi

    GODOT_PROJECT_DIR="${GODOT_PROJECT_DIR:-$ROOT_DIR/versao-godot/godot}"
    if [[ ! -f "$GODOT_PROJECT_DIR/project.godot" && -f "$ROOT_DIR/godot/project.godot" ]]; then
        GODOT_PROJECT_DIR="$ROOT_DIR/godot"
    fi

    PYTHON_VERSION_DIR="${PYTHON_VERSION_DIR:-$ROOT_DIR/versao-python}"
    if [[ ! -d "$PYTHON_VERSION_DIR/src" && -d "$ROOT_DIR/src" ]]; then
        PYTHON_VERSION_DIR="$ROOT_DIR"
    fi

    PYTHON_SRC_DIR="${PYTHON_SRC_DIR:-$PYTHON_VERSION_DIR/src}"
    PYTHON_CONF_DIR="${PYTHON_CONF_DIR:-$PYTHON_VERSION_DIR/conf}"
    PYTHON_DATA_DIR="${PYTHON_DATA_DIR:-$PYTHON_VERSION_DIR/data}"
    BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build}"
    DIST_DIR="${DIST_DIR:-$ROOT_DIR/dist}"
    GROUNDFIRE_NET_DIR="${GROUNDFIRE_NET_DIR:-$ROOT_DIR/groundfire_net}"
}

repo_pythonpath() {
    printf '%s:%s' "$PYTHON_VERSION_DIR" "$ROOT_DIR"
    if [[ -n "${PYTHONPATH:-}" ]]; then
        printf ':%s' "$PYTHONPATH"
    fi
}
