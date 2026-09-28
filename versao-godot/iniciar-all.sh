#!/bin/sh
if [ -z "${BASH_VERSION:-}" ]; then
    exec /usr/bin/env bash "$0" "$@"
fi
set -Eeuo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/scripts/launcher_common.sh"

usage() {
    cat <<'EOF'
Uso: sh iniciar-all.sh [opcoes]

Inicia o servidor autoritativo Python e clientes Godot conectados.

  -n, --num NUMERO       Quantidade de clientes Godot (padrao: 2).
  --bind-host ENDERECO   Interface do servidor (padrao: 0.0.0.0).
  --host ENDERECO        Endereco visto pelos clientes (padrao: 127.0.0.1).
  --port PORTA           Porta UDP do jogo (padrao: 27015).
  --rounds NUMERO        Rodadas da partida (padrao: 20).
  --server-name NOME     Nome anunciado na LAN.
  --password SENHA       Senha do servidor e clientes.
  --headless             Clientes Godot sem janela.
  --spectator            Abre clientes como espectadores.
  --quit-after FRAMES    Encerra cada cliente apos FRAMES (testes).
  --dry-run              Mostra os comandos sem executa-los.
  -h, --help             Mostra esta ajuda.
EOF
}

count=2
bind_host=0.0.0.0
host=127.0.0.1
port=27015
rounds=20
server_name='Groundfire Godot LAN'
password=
headless=0
spectator=0
quit_after=0
dry_run=0

while (($#)); do
    case "$1" in
        -n|--num) count="${2:?Falta NUMERO}"; shift 2 ;;
        -[0-9]*) count="${1#-}"; shift ;;
        --bind-host) bind_host="${2:?Falta ENDERECO}"; shift 2 ;;
        --host) host="${2:?Falta ENDERECO}"; shift 2 ;;
        --port) port="${2:?Falta PORTA}"; shift 2 ;;
        --rounds) rounds="${2:?Falta NUMERO}"; shift 2 ;;
        --server-name) server_name="${2:?Falta NOME}"; shift 2 ;;
        --password) password="${2:?Falta SENHA}"; shift 2 ;;
        --headless) headless=1; shift ;;
        --spectator) spectator=1; shift ;;
        --quit-after) quit_after="${2:?Falta FRAMES}"; shift 2 ;;
        --dry-run) dry_run=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Opcao desconhecida: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
done

if [[ ! "$count" =~ ^[1-8]$ || ! "$rounds" =~ ^[1-9][0-9]*$ || ! "$port" =~ ^[0-9]+$ || "$port" -lt 1 || "$port" -gt 65535 || ! "$quit_after" =~ ^[0-9]+$ || -z "$host" || -z "$bind_host" ]]; then
    printf 'Quantidade, host, porta, rodadas ou quit-after invalido.\n' >&2
    exit 2
fi

server_args=(--host "$bind_host" --port "$port" --rounds "$rounds" --server-name "$server_name")
client_args=(-n "$count" --host "$host" --port "$port" --no-check-server)
[[ -n "$password" ]] && { server_args+=(--password "$password"); client_args+=(--password "$password"); }
((headless)) && client_args+=(--headless)
((spectator)) && client_args+=(--spectator)
((quit_after > 0)) && client_args+=(--quit-after "$quit_after")

if ((dry_run)); then
    if [[ -n "$password" ]]; then
        printf 'DRY-RUN com senha: comandos omitidos para nao exibir a credencial.\n'
        exit 0
    fi
    bash "$SCRIPT_DIR/iniciar-server.sh" "${server_args[@]}" --dry-run
    bash "$SCRIPT_DIR/iniciar-clientes.sh" "${client_args[@]}" --dry-run
    exit 0
fi

godot_launcher_configure_python
if ! "$GROUNDFIRE_LAUNCHER_PYTHON" - "$bind_host" "$port" <<'PY'
import socket
import sys

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
    try:
        probe.bind((sys.argv[1], int(sys.argv[2])))
    except OSError as exc:
        print(f"Porta UDP indisponivel para o novo servidor: {exc}", file=sys.stderr)
        raise SystemExit(1)
PY
then
    exit 1
fi

server_pid=
clients_pid=
cleanup() {
    [[ -n "$clients_pid" ]] && kill "$clients_pid" >/dev/null 2>&1 || true
    [[ -n "$server_pid" ]] && kill "$server_pid" >/dev/null 2>&1 || true
    [[ -n "$clients_pid" ]] && wait "$clients_pid" >/dev/null 2>&1 || true
    [[ -n "$server_pid" ]] && wait "$server_pid" >/dev/null 2>&1 || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM

bash "$SCRIPT_DIR/iniciar-server.sh" "${server_args[@]}" &
server_pid=$!
printf 'Aguardando servidor LAN em %s:%s...\n' "$host" "$port"
ready=0
for ((attempt = 1; attempt <= 8; attempt++)); do
    if ! kill -0 "$server_pid" >/dev/null 2>&1; then
        printf 'O processo do servidor terminou antes de ficar pronto.\n' >&2
        exit 1
    fi
    if PYTHONPATH="$SCRIPT_DIR/runtime/headless:$SCRIPT_DIR/runtime/headless/src${PYTHONPATH:+:$PYTHONPATH}" "$GROUNDFIRE_LAUNCHER_PYTHON" "$SCRIPT_DIR/scripts/check_udp_server.py" --host "$host" --port "$port" >/dev/null 2>&1; then
        ready=1
        break
    fi
done
if ((ready == 0)); then
    printf 'Servidor nao respondeu ao ping UDP. Verifique os logs do launcher Python.\n' >&2
    exit 1
fi

bash "$SCRIPT_DIR/iniciar-clientes.sh" "${client_args[@]}" &
clients_pid=$!
status=0
wait -n "$server_pid" "$clients_pid" || status=$?
exit "$status"
