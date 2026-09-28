#!/bin/sh
if [ -z "${BASH_VERSION:-}" ]; then
    exec /usr/bin/env bash "$0" "$@"
fi
set -Eeuo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/scripts/launcher_common.sh"

usage() {
    cat <<'EOF'
Uso: sh iniciar-clientes.sh [-n NUMERO] [opcoes]

  -n, --num NUMERO        Abre 1 a 8 clientes Godot (padrao: 2).
  -NUMERO                 Atalho, por exemplo -3.
  --host ENDERECO         Host do servidor UDP (padrao: 127.0.0.1).
  --port PORTA            Porta do servidor UDP (padrao: 27015).
  --player-prefix NOME    Prefixo dos jogadores (padrao: Godot).
  --password SENHA        Senha da sala/servidor.
  --spectator             Abre os clientes como espectadores.
  --headless              Executa Godot sem janela.
  --quit-after FRAMES     Encerra cada cliente apos FRAMES (testes).
  --check-only            Verifica o servidor sem abrir janelas.
  --no-check-server       Abre mesmo sem resposta ao ping UDP.
  --detach                Libera o terminal e mantem as janelas abertas.
  --dry-run               Mostra comandos sem executa-los.
  -h, --help              Mostra esta ajuda.

Use GODOT_BIN para escolher o executavel Godot 4. Os clientes usam
--connect passado apos o separador de argumentos do Godot.
EOF
}

count=2
host=127.0.0.1
port=27015
player_prefix=Godot
password=
spectator=0
headless=0
check_server=1
check_only=0
detach=0
dry_run=0
quit_after=0
declare -a client_pids=()

while (($#)); do
    case "$1" in
        -n|--num) count="${2:?Falta NUMERO para $1}"; shift 2 ;;
        -[0-9]*) count="${1#-}"; shift ;;
        --host) host="${2:?Falta ENDERECO}"; shift 2 ;;
        --port) port="${2:?Falta PORTA}"; shift 2 ;;
        --player-prefix) player_prefix="${2:?Falta NOME}"; shift 2 ;;
        --password) password="${2:?Falta SENHA}"; shift 2 ;;
        --spectator) spectator=1; shift ;;
        --headless) headless=1; shift ;;
        --quit-after) quit_after="${2:?Falta FRAMES}"; shift 2 ;;
        --check-only) check_only=1; shift ;;
        --no-check-server) check_server=0; shift ;;
        --detach) detach=1; shift ;;
        --dry-run) dry_run=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Opcao desconhecida: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
done

if [[ ! "$count" =~ ^[1-8]$ || ! "$port" =~ ^[0-9]+$ || "$port" -lt 1 || "$port" -gt 65535 || ! "$quit_after" =~ ^[0-9]+$ || -z "$host" ]]; then
    printf 'Quantidade, host, porta ou quit-after invalido.\n' >&2
    exit 2
fi

if ((dry_run == 0 && (check_server == 1 || check_only == 1))); then
    godot_launcher_configure_python
    printf 'Verificando servidor UDP em %s:%s...\n' "$host" "$port"
    PYTHONPATH="$SCRIPT_DIR/runtime/headless:$SCRIPT_DIR/runtime/headless/src${PYTHONPATH:+:$PYTHONPATH}" "$GROUNDFIRE_LAUNCHER_PYTHON" "$SCRIPT_DIR/scripts/check_udp_server.py" --host "$host" --port "$port"
fi
if ((check_only)); then
    if ((dry_run)); then
        printf 'DRY-RUN: verificar servidor %s:%s\n' "$host" "$port"
    fi
    exit 0
fi

godot_launcher_require_project
GODOT_EXECUTABLE=$(godot_launcher_find_binary)

cleanup() {
    local pid
    for pid in "${client_pids[@]}"; do
        kill "$pid" >/dev/null 2>&1 || true
    done
}
if ((detach == 0 && dry_run == 0)); then
    trap cleanup EXIT
    trap 'exit 130' INT TERM
fi

for ((number = 1; number <= count; number++)); do
    cmd=("$GODOT_EXECUTABLE" --path "$GODOT_LAUNCHER_PROJECT")
    ((headless)) && cmd+=(--headless)
    ((quit_after > 0)) && cmd+=(--quit-after "$quit_after")
    cmd+=(-- --connect "$host:$port" --player-name "$player_prefix $number")
    ((spectator)) && cmd+=(--spectator)
    [[ -n "$password" ]] && cmd+=(--password "$password")
    if ((dry_run)); then
        display_cmd=("${cmd[@]}")
        if [[ -n "$password" ]]; then
            display_cmd[$((${#display_cmd[@]} - 1))]='<redacted>'
        fi
        printf 'DRY-RUN client %d:' "$number"
        printf ' %q' "${display_cmd[@]}"
        printf '\n'
    else
        "${cmd[@]}" &
        client_pids+=("$!")
        printf 'Cliente Godot %d iniciado (PID %s).\n' "$number" "$!"
    fi
done

if ((detach && dry_run == 0)); then
    printf 'Clientes mantidos em segundo plano.\n'
    exit 0
fi
if ((dry_run)); then
    exit 0
fi
status=0
for pid in "${client_pids[@]}"; do
    wait "$pid" || status=1
done
exit "$status"
