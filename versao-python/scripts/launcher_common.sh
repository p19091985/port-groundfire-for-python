#!/usr/bin/env bash

# Shared helpers for the Groundfire shell launchers.  This file assumes the
# caller already re-execed under Bash and set PROJECT_DIR, LOG_DIR and LOG_FILE.

launcher_init_logs() {
    mkdir -p "$LOG_DIR"
}

log() {
    local message="$1"
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$message" | tee -a "$LOG_FILE"
}

find_python() {
    if [[ -n "${GROUNDFIRE_LAUNCHER_PYTHON:-}" ]]; then
        printf '%s\n' "$GROUNDFIRE_LAUNCHER_PYTHON"
        return 0
    fi

    if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
        printf '%s\n' "$PROJECT_DIR/.venv/bin/python"
        return 0
    fi

    local candidate
    for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    return 1
}

quote_command() {
    local quoted=()
    local part
    for part in "$@"; do
        quoted+=("$(printf '%q' "$part")")
    done
    printf '%s\n' "${quoted[*]}"
}

trim_text() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

is_positive_int() {
    [[ "$1" =~ ^[0-9]+$ ]] && (("$1" > 0))
}

is_non_negative_int() {
    [[ "$1" =~ ^[0-9]+$ ]]
}

is_port() {
    [[ "$1" =~ ^[0-9]+$ ]] && (("$1" >= 1 && "$1" <= 65535))
}

is_player_count() {
    [[ "$1" =~ ^[0-9]+$ ]] && (("$1" >= 1 && "$1" <= 32))
}

is_non_negative_number() {
    [[ "$1" =~ ^([0-9]+([.][0-9]+)?|[.][0-9]+)$ ]]
}

is_common_preset() {
    case "$1" in
        2|4|6|8|12) return 0 ;;
        *) return 1 ;;
    esac
}

is_valid_host() {
    local host="$1"
    [[ -n "$host" && ${#host} -le 253 ]] || return 1

    if [[ "$host" == "localhost" ]]; then
        return 0
    fi

    if [[ "$host" =~ ^[0-9]+[.][0-9]+[.][0-9]+[.][0-9]+$ ]]; then
        local a b c d octet
        IFS=. read -r a b c d <<< "$host"
        for octet in "$a" "$b" "$c" "$d"; do
            [[ "$octet" =~ ^[0-9]+$ ]] && ((octet >= 0 && octet <= 255)) || return 1
        done
        return 0
    fi

    [[ "$host" =~ ^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?([.][A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$ ]]
}

is_master_server_address() {
    local address="$1"
    local host port
    [[ "$address" == *:* ]] || return 1
    host="${address%:*}"
    port="${address##*:}"
    is_valid_host "$host" && is_port "$port"
}

rotate_log_if_needed() {
    local log_path="$1"
    local max_bytes="${GROUNDFIRE_LOG_MAX_BYTES:-5242880}"
    local backups="${GROUNDFIRE_LOG_BACKUPS:-3}"

    [[ "$max_bytes" =~ ^[0-9]+$ ]] || max_bytes=5242880
    [[ "$backups" =~ ^[0-9]+$ ]] || backups=3
    ((max_bytes > 0 && backups > 0)) || return 0
    [[ -f "$log_path" ]] || return 0

    local size
    size=$(wc -c < "$log_path" 2>/dev/null || printf '0')
    ((size >= max_bytes)) || return 0

    local index
    for ((index = backups - 1; index >= 1; index--)); do
        if [[ -f "$log_path.$index" ]]; then
            mv -f "$log_path.$index" "$log_path.$((index + 1))"
        fi
    done
    mv -f "$log_path" "$log_path.1"
    : > "$log_path"
}

process_is_running() {
    local pid="$1"
    local state=""

    if [[ -z "$pid" ]] || ! kill -0 "$pid" >/dev/null 2>&1; then
        return 1
    fi
    if command -v ps >/dev/null 2>&1; then
        state=$(ps -p "$pid" -o stat= 2>/dev/null | tr -d '[:space:]' || true)
        if [[ -z "$state" || "$state" == Z* ]]; then
            return 1
        fi
    fi
    return 0
}
