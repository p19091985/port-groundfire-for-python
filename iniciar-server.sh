#!/bin/sh
if [ -z "${BASH_VERSION:-}" ]; then
    exec /usr/bin/env bash "$0" "$@"
fi
set -Eeuo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
SCRIPT_PATH="$SCRIPT_DIR/$(basename -- "${BASH_SOURCE[0]}")"
PROJECT_DIR="$SCRIPT_DIR"
LOG_DIR="${GROUNDFIRE_LAUNCHER_LOG_DIR:-$PROJECT_DIR/logs}"
RUN_ID=$(date '+%Y%m%d-%H%M%S')
LOG_FILE="${GROUNDFIRE_SERVER_LOG_FILE:-$LOG_DIR/server_debug.log}"

mkdir -p "$LOG_DIR"

SERVER_PID=""
VISIBLE_CLIENT_PID=""
DRY_RUN_MODE=0

# Log central: por default todas as execucoes do launcher do servidor vao para server_debug.log.
log() {
    local message="$1"
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$message" | tee -a "$LOG_FILE"
}

usage() {
    cat <<'EOF'
Uso:
  ./iniciar-server.sh
      Abre o menu grafico Pygame para iniciar o servidor.

  ./iniciar-server.sh -A [opcoes]
      Inicia imediatamente um servidor LAN.

Modos de acesso:
  --menu                  Interface grafica Pygame de gerenciamento do servidor.
  --cli, -A, --auto       Comando de texto/CLI para iniciar o servidor.

Opcoes principais:
  --host ENDERECO           Interface de bind. Padrao: 0.0.0.0
  --port PORTA              Porta UDP do jogo. Padrao: 27015
  --discovery-port PORTA    Porta de descoberta LAN. Padrao: 27016
  --server-name NOME        Nome anunciado na LAN.
  --map MAPA                Mapa/seed do terreno. Padrao: classic
  --max-players NUMERO      Slots maximos. Padrao: 8
  --network MODO            lan, internet ou both. Padrao: lan
  --region REGIAO           Regiao anunciada. Padrao: local
  --master-server ENDERECO  Master server para rede internet. Pode repetir.
  --password SENHA          Exige senha para entrar.
  --rcon-password SENHA     Senha administrativa reservada para RCON.
  --rounds NUMERO           Quantidade de rounds da partida. Padrao: 10
  --ticks NUMERO            Encerra depois de NUMERO ticks.
  --insecure                Anuncia o servidor como inseguro.
  --com-tela                Abre uma janela Pygame conectada ao servidor.
  --sem-tela, --server-only Mantem apenas o servidor headless. Padrao.
  --client-host ENDERECO    Host usado pela janela local. Padrao: 127.0.0.1 ou --host
  --client-name NOME        Nome do cliente visivel. Padrao: Tela Servidor
  --client-timeout SEG      Tempo para aguardar o servidor antes da janela. Padrao: 5
  --dry-run                 Registra e imprime o comando sem executar.
  -h, --help                Mostra esta ajuda.

Variaveis uteis:
  GROUNDFIRE_LAUNCHER_PYTHON    Python usado pelo launcher.
  GROUNDFIRE_LAUNCHER_LOG_DIR   Pasta dos logs.
  GROUNDFIRE_SERVER_LOG_FILE    Arquivo de log principal.
  GROUNDFIRE_SERVER_SHOW_CLIENT 0 desativa a janela local por default.
EOF
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

is_port() {
    [[ "$1" =~ ^[0-9]+$ ]] && (("$1" >= 1 && "$1" <= 65535))
}

is_positive_int() {
    [[ "$1" =~ ^[0-9]+$ ]] && (("$1" > 0))
}

is_player_count() {
    [[ "$1" =~ ^[0-9]+$ ]] && (("$1" >= 1 && "$1" <= 32))
}

is_map_value() {
    local raw="${1,,}"
    raw="${raw//_/-}"
    raw="${raw#seed }"
    raw="${raw// /}"
    case "$raw" in
        classic|basin|ridge|crater|mesa)
            return 0 ;;
        *)
            [[ "$raw" =~ ^[0-9]+$ ]] && (("$raw" > 0)) ;;
    esac
}

is_network_mode() {
    case "${1,,}" in
        lan|internet|both)
            return 0 ;;
        *)
            return 1 ;;
    esac
}

is_non_negative_number() {
    [[ "$1" =~ ^([0-9]+([.][0-9]+)?|[.][0-9]+)$ ]]
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

terminate_process() {
    local label="$1"
    local pid="$2"

    if ! process_is_running "$pid"; then
        return 0
    fi

    log "Encerrando $label PID $pid."
    kill "$pid" >/dev/null 2>&1 || true
}

stop_process_and_wait() {
    local label="$1"
    local pid="$2"
    local attempt

    if ! process_is_running "$pid"; then
        return 0
    fi

    log "Encerrando $label PID $pid."
    kill "$pid" >/dev/null 2>&1 || true
    for attempt in {1..30}; do
        if ! process_is_running "$pid"; then
            return 0
        fi
        sleep 0.1
    done

    log "$label PID $pid nao encerrou; forcando SIGKILL."
    kill -KILL "$pid" >/dev/null 2>&1 || true
    for attempt in {1..20}; do
        if ! process_is_running "$pid"; then
            return 0
        fi
        sleep 0.1
    done
    log "$label PID $pid continuou ativo apos SIGKILL."
    return 1
}

cleanup_processes() {
    if [[ "$DRY_RUN_MODE" == "1" ]]; then
        return 0
    fi

    terminate_process "cliente visivel" "$VISIBLE_CLIENT_PID"
    terminate_process "servidor" "$SERVER_PID"
}

cleanup_on_exit() {
    local status=$?
    cleanup_processes
    return "$status"
}

cleanup_on_signal() {
    log "Sinal de encerramento recebido."
    cleanup_processes
    exit 130
}

cleanup_stale_menu_server_ports() {
    if [[ "${GROUNDFIRE_SERVER_KEEP_EXISTING:-0}" == "1" ]]; then
        log "Mantendo servidores Groundfire existentes porque GROUNDFIRE_SERVER_KEEP_EXISTING=1."
        return 0
    fi

    local port="${GROUNDFIRE_SERVER_PORT:-27015}"
    local failed=0

    if is_port "$port"; then
        stop_existing_groundfire_servers_on_port "$port" || failed=1
    fi

    if ((failed)); then
        log "Nao foi possivel limpar todos os servidores antigos antes de abrir o menu."
        return 1
    fi
    return 0
}

launch_pygame_menu() {
    local python_bin
    python_bin=$(find_python) || {
        log "Python compativel nao encontrado para abrir o menu."
        return 1
    }

    cleanup_stale_menu_server_ports || true
    log "Abrindo menu Pygame do servidor."
    PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$python_bin" -m src.groundfire.app.dedicated_server_menu "$SCRIPT_PATH" "$PROJECT_DIR" "$LOG_FILE" 2>&1 | tee -a "$LOG_FILE"
    return "${PIPESTATUS[0]}"
}

wait_for_server() {
    local python_bin="$1"
    local host="$2"
    local port="$3"
    local timeout_seconds="$4"

    PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$python_bin" - "$host" "$port" "$timeout_seconds" <<'PY'
import socket
import sys
import time

from src.groundfire.network.codec import decode_message, encode_message
from src.groundfire.network.messages import Ping, Pong

host = sys.argv[1]
port = int(sys.argv[2])
timeout_seconds = float(sys.argv[3])
deadline = time.monotonic() + timeout_seconds

while time.monotonic() < deadline:
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.2)
        sock.sendto(encode_message(Ping(nonce="iniciar-server", issued_at=time.time())), (host, port))
        payload, _address = sock.recvfrom(65535)
        if isinstance(decode_message(payload), Pong):
            raise SystemExit(0)
    except OSError:
        time.sleep(0.05)
    finally:
        if sock is not None:
            sock.close()

raise SystemExit(1)
PY
}

require_server_process_running() {
    local port="$1"
    local status=1

    if process_is_running "$SERVER_PID"; then
        return 0
    fi
    if [[ -n "$SERVER_PID" ]]; then
        wait "$SERVER_PID" || status=$?
        SERVER_PID=""
    fi
    if ((status == 0)); then
        log "Servidor encerrou antes de abrir a tela local; cliente visivel nao sera aberto."
        return 1
    fi
    log "Servidor encerrou antes de responder. A porta UDP $port pode ja estar em uso; feche o servidor antigo ou escolha outra porta."
    return "$status"
}

udp_port_pids() {
    local port="$1"
    local line
    local pid
    local rest

    if command -v ss >/dev/null 2>&1; then
        while IFS= read -r line; do
            [[ "$line" =~ :${port}[[:space:]] ]] || continue
            rest="$line"
            while [[ "$rest" =~ pid=([0-9]+) ]]; do
                pid="${BASH_REMATCH[1]}"
                printf '%s\n' "$pid"
                rest="${rest#*pid=$pid}"
            done
        done < <(ss -H -lunp 2>/dev/null || true) | sort -u
        return 0
    fi

    if command -v lsof >/dev/null 2>&1; then
        lsof -nP -iUDP:"$port" -t 2>/dev/null | sort -u || true
    fi
}

pid_command_line() {
    local pid="$1"
    ps -p "$pid" -o args= 2>/dev/null || true
}

wait_until_udp_port_free() {
    local port="$1"
    local attempt
    local pids=()

    for attempt in {1..30}; do
        mapfile -t pids < <(udp_port_pids "$port")
        if ((${#pids[@]} == 0)); then
            return 0
        fi
        sleep 0.1
    done
    return 1
}

stop_existing_groundfire_servers_on_port() {
    local port="$1"
    local pids=()
    local pid
    local cmdline
    local stopped=0
    local blocked=0

    mapfile -t pids < <(udp_port_pids "$port")
    if ((${#pids[@]} == 0)); then
        return 0
    fi

    for pid in "${pids[@]}"; do
        [[ -n "$pid" ]] || continue
        cmdline="$(pid_command_line "$pid")"
        if [[ "$cmdline" == *"groundfire.server"* ]]; then
            stopped=1
            log "Servidor antigo encontrado na porta UDP $port: PID $pid."
            stop_process_and_wait "servidor antigo na porta UDP $port" "$pid" || return 1
        else
            blocked=1
            log "Porta UDP $port ocupada por processo externo PID $pid: ${cmdline:-comando indisponivel}."
        fi
    done

    if ((stopped)); then
        if wait_until_udp_port_free "$port"; then
            log "Porta UDP $port liberada para o novo servidor."
        else
            log "Porta UDP $port continuou ocupada apos encerrar o servidor antigo."
            return 1
        fi
    fi

    mapfile -t pids < <(udp_port_pids "$port")
    if ((${#pids[@]} > 0)); then
        blocked=1
    fi
    if ((blocked)); then
        log "Porta UDP $port ainda esta ocupada; servidor novo nao sera iniciado."
        return 1
    fi
    return 0
}

start_server() {
    local host="${GROUNDFIRE_SERVER_HOST:-0.0.0.0}"
    local port="${GROUNDFIRE_SERVER_PORT:-27015}"
    local discovery_port="${GROUNDFIRE_DISCOVERY_PORT:-27016}"
    local server_name="${GROUNDFIRE_SERVER_NAME:-Groundfire LAN}"
    local map_value="${GROUNDFIRE_SERVER_MAP:-classic}"
    local max_players="${GROUNDFIRE_MAX_PLAYERS:-8}"
    local network="${GROUNDFIRE_SERVER_NETWORK:-lan}"
    local region="${GROUNDFIRE_SERVER_REGION:-local}"
    local password="${GROUNDFIRE_SERVER_PASSWORD:-}"
    local rcon_password="${GROUNDFIRE_RCON_PASSWORD:-}"
    local rounds="${GROUNDFIRE_NUM_ROUNDS:-10}"
    local show_client="${GROUNDFIRE_SERVER_SHOW_CLIENT:-0}"
    local client_host="${GROUNDFIRE_SERVER_CLIENT_HOST:-}"
    local client_name="${GROUNDFIRE_SERVER_CLIENT_NAME:-Tela Servidor}"
    local client_timeout="${GROUNDFIRE_SERVER_CLIENT_TIMEOUT:-5}"
    local ticks=""
    local dry_run=0
    local insecure=0
    local master_servers_raw="${GROUNDFIRE_MASTER_SERVERS:-}"
    local master_servers=()
    local extra_args=()

    if [[ -n "$master_servers_raw" ]]; then
        IFS=',' read -r -a master_servers <<< "$master_servers_raw"
    fi

    while (($#)); do
        case "$1" in
            --host)
                host="${2:?Valor ausente para --host}"; shift 2 ;;
            --port)
                port="${2:?Valor ausente para --port}"; shift 2 ;;
            --discovery-port)
                discovery_port="${2:?Valor ausente para --discovery-port}"; shift 2 ;;
            --server-name)
                server_name="${2:?Valor ausente para --server-name}"; shift 2 ;;
            --map|--map-seed)
                map_value="${2:?Valor ausente para $1}"; shift 2 ;;
            --max-players)
                max_players="${2:?Valor ausente para --max-players}"; shift 2 ;;
            --network)
                network="${2:?Valor ausente para --network}"; shift 2 ;;
            --region)
                region="${2:?Valor ausente para --region}"; shift 2 ;;
            --master-server)
                master_servers+=("${2:?Valor ausente para --master-server}"); shift 2 ;;
            --password)
                password="${2:?Valor ausente para --password}"; shift 2 ;;
            --rcon-password)
                rcon_password="${2:?Valor ausente para --rcon-password}"; shift 2 ;;
            --rounds|--num-rounds)
                rounds="${2:?Valor ausente para $1}"; shift 2 ;;
            --ticks)
                ticks="${2:?Valor ausente para --ticks}"; shift 2 ;;
            --insecure)
                insecure=1; shift ;;
            --cli)
                shift ;;
            --com-tela|--show-client|--visible-client)
                show_client=1; shift ;;
            --sem-tela|--server-only|--headless-only)
                show_client=0; shift ;;
            --client-host)
                client_host="${2:?Valor ausente para --client-host}"; shift 2 ;;
            --client-name)
                client_name="${2:?Valor ausente para --client-name}"; shift 2 ;;
            --client-timeout)
                client_timeout="${2:?Valor ausente para --client-timeout}"; shift 2 ;;
            --dry-run)
                dry_run=1; shift ;;
            -h|--help)
                usage; return 0 ;;
            *)
                extra_args+=("$1"); shift ;;
        esac
    done

    network="${network,,}"
    region="${region:-local}"
    local normalized_masters=()
    local address
    for address in "${master_servers[@]}"; do
        address="$(trim_text "$address")"
        [[ -n "$address" ]] && normalized_masters+=("$address")
    done
    master_servers=("${normalized_masters[@]}")
    if [[ "$network" != "lan" && ${#master_servers[@]} -eq 0 ]]; then
        master_servers=("127.0.0.1:27017")
    fi

    # Falhe cedo em entradas comuns vindas da CLI ou do menu Tk.
    if ! is_valid_host "$host"; then
        log "Host invalido: $host"
        return 2
    fi
    if ! is_port "$port"; then
        log "Porta de jogo invalida: $port"
        return 2
    fi
    if ! is_port "$discovery_port"; then
        log "Porta de descoberta invalida: $discovery_port"
        return 2
    fi
    if ! is_positive_int "$rounds"; then
        log "Quantidade de rounds invalida: $rounds"
        return 2
    fi
    if ! is_map_value "$map_value"; then
        log "Mapa invalido: $map_value"
        return 2
    fi
    if ! is_player_count "$max_players"; then
        log "Maximo de jogadores invalido: $max_players"
        return 2
    fi
    if ! is_network_mode "$network"; then
        log "Modo de rede invalido: $network"
        return 2
    fi
    if [[ ! "$region" =~ ^[A-Za-z0-9_-]{1,32}$ ]]; then
        log "Regiao invalida: $region"
        return 2
    fi
    if [[ "$network" != "lan" ]]; then
        for address in "${master_servers[@]}"; do
            if ! is_master_server_address "$address"; then
                log "Master server invalido: $address"
                return 2
            fi
        done
    fi
    if [[ "$show_client" != "0" && "$show_client" != "1" ]]; then
        log "Opcao de tela local invalida: $show_client"
        return 2
    fi
    if [[ -z "$client_host" ]]; then
        if [[ "$host" == "0.0.0.0" ]]; then
            client_host="127.0.0.1"
        else
            client_host="$host"
        fi
    fi
    if ((show_client)); then
        if ! is_valid_host "$client_host"; then
            log "Host do cliente visivel invalido: $client_host"
            return 2
        fi
        if ! is_non_negative_number "$client_timeout"; then
            log "Timeout do cliente visivel invalido: $client_timeout"
            return 2
        fi
    fi

    local python_bin
    python_bin=$(find_python) || {
        log "Python compativel nao encontrado no PATH."
        return 1
    }

    local cmd=(
        "$python_bin"
        -m groundfire.server
        --host "$host"
        --port "$port"
        --discovery-port "$discovery_port"
        --server-name "$server_name"
        --map "$map_value"
        --max-players "$max_players"
        --region "$region"
        --rounds "$rounds"
        --headless
        --log-events
    )

    # O comando e montado em array para preservar quoting e evitar expansao acidental.
    if [[ "$network" == "internet" ]]; then
        cmd+=(--no-discovery)
    fi
    if [[ "$network" == "internet" || "$network" == "both" ]]; then
        for address in "${master_servers[@]}"; do
            cmd+=(--master-server "$address")
        done
    fi
    if [[ -n "$password" ]]; then
        cmd+=(--password "$password")
    fi
    if [[ -n "$rcon_password" ]]; then
        cmd+=(--rcon-password "$rcon_password")
    fi
    if [[ -n "$ticks" ]]; then
        cmd+=(--ticks "$ticks")
    fi
    if ((insecure)); then
        cmd+=(--insecure)
    fi
    if ((${#extra_args[@]})); then
        cmd+=("${extra_args[@]}")
    fi

    local client_cmd=(
        "$python_bin"
        -m groundfire.client
        --connect "$client_host:$port"
        --player-name "$client_name"
        --computer-player
        --log-network-events
    )
    if [[ -n "$password" ]]; then
        client_cmd+=(--password "$password")
    fi

    log "Preparando servidor LAN em $host:$port com descoberta UDP $discovery_port e $rounds rounds."
    log "Configuracao dedicada: rede=$network mapa=$map_value max_players=$max_players regiao=$region secure=$((1 - insecure))."
    if [[ "$network" == "internet" || "$network" == "both" ]]; then
        log "Master servers: $(quote_command "${master_servers[@]}")"
    fi
    log "Arquivo de log: $LOG_FILE"
    log "Comando: $(quote_command "${cmd[@]}")"
    if ((show_client)); then
        log "Cliente visivel: $(quote_command "${client_cmd[@]}")"
    else
        log "Modo sem tela: apenas o servidor headless sera iniciado."
    fi

    if ((dry_run)); then
        printf 'DRY-RUN server command: %s\n' "$(quote_command "${cmd[@]}")"
        if ((show_client)); then
            printf 'DRY-RUN visible client command: %s\n' "$(quote_command "${client_cmd[@]}")"
        fi
        return 0
    fi

    DRY_RUN_MODE=0
    trap cleanup_on_exit EXIT
    trap cleanup_on_signal INT TERM

    if ! stop_existing_groundfire_servers_on_port "$port"; then
        ((show_client)) && log "Cliente visivel nao sera aberto porque a porta UDP $port nao foi liberada."
        return 1
    fi
    log "Servidor iniciado. Pressione Ctrl+C para encerrar."
    PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" "${cmd[@]}" >> "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    log "Servidor PID $SERVER_PID iniciado."

    if ((show_client)); then
        local client_log="$LOG_DIR/iniciar-server-$RUN_ID-visible-client.log"
        sleep 0.25
        require_server_process_running "$port" || return $?
        log "Aguardando servidor responder em $client_host:$port para abrir a tela."
        if ! wait_for_server "$python_bin" "$client_host" "$port" "$client_timeout"; then
            require_server_process_running "$port" || return $?
            log "Servidor nao respondeu em ate ${client_timeout}s; cliente visivel nao sera aberto."
            return 1
        fi
        require_server_process_running "$port" || return $?
        log "Abrindo janela Pygame do jogo. Log do cliente visivel: $client_log"
        PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" "${client_cmd[@]}" >> "$client_log" 2>&1 &
        VISIBLE_CLIENT_PID=$!
        log "Cliente visivel iniciado com PID $VISIBLE_CLIENT_PID."
    fi

    local server_status=0
    wait "$SERVER_PID" || server_status=$?
    SERVER_PID=""
    if ((server_status != 0)); then
        log "Servidor encerrou com codigo $server_status. Consulte o log; se isso aconteceu ao iniciar, verifique se a porta UDP $port ja esta em uso."
    fi
    return "$server_status"
}

main() {
    log "Launcher do servidor chamado com argumentos: $(quote_command "$@")"

    if (($# == 0)); then
        launch_pygame_menu
        return $?
    fi

    case "$1" in
        --menu)
            shift
            if (($#)); then
                log "--menu nao aceita argumentos extras: $(quote_command "$@")"
                return 2
            fi
            launch_pygame_menu
            ;;
        -A|A|a|--auto|--cli)
            shift
            start_server "$@"
            ;;
        -h|--help)
            usage
            ;;
        *)
            log "Modo desconhecido: $1"
            usage
            return 2
            ;;
    esac
}

rotate_log_if_needed "$LOG_FILE"
main "$@"
