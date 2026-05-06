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
LOG_FILE="${GROUNDFIRE_CLIENTS_LOG_FILE:-$LOG_DIR/clients_debug.log}"

mkdir -p "$LOG_DIR"

CLIENT_PIDS=()
DETACH_MODE=0
DRY_RUN_MODE=0

# Log central dos clientes; logs por instancia continuam separados para facilitar depuracao.
log() {
    local message="$1"
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$message" | tee -a "$LOG_FILE"
}

usage() {
    cat <<'EOF'
Uso:
  ./iniciar-clientes.sh
      Abre o menu grafico Ttk para iniciar clientes.

  ./iniciar-clientes.sh -3
      Inicia 3 clientes conectando no servidor LAN padrao.

  ./iniciar-clientes.sh -3 -a
      Inicia 3 clientes como jogadores de computador controlados pela IA do servidor.

Modos de acesso:
  --menu                  Interface grafica Ttk de gerenciamento dos clientes.
  --cli                   Comando de texto/CLI para iniciar clientes.

Opcoes principais:
  -NUMERO                  Quantidade de clientes. Exemplo: -4
  -n, --num NUMERO         Quantidade de clientes.
  --preset NUMERO          Usa um preset de clientes: 2, 4, 6, 8 ou 12.
  -a                       Conecta cada cliente como jogador de computador.
  --host ENDERECO          Host do servidor. Padrao: 127.0.0.1
  --server ENDERECO        Alias de --host.
  --port PORTA             Porta UDP do servidor. Padrao: 27015
  --password SENHA         Senha enviada ao servidor.
  --player-prefix NOME     Prefixo dos nomes dos jogadores.
  --join-timeout SEG       Tempo maximo para aguardar entrada headless. Padrao: 5
  --keepalive-seconds SEG  Tempo que cliente IA headless fica vivo. Padrao: 86400
  --client-delay SEG       Intervalo entre aberturas de clientes. Padrao: 0.15
  --visible-count NUM      Quantos clientes IA abrem janela Pygame. Padrao: todos.
  --com-tela               Abre uma janela Pygame para cada cliente IA.
  --sem-tela, --headless-only
                           Mantem todos os clientes IA sem janela.
  --check-server           Faz ping UDP no servidor antes de abrir clientes.
  --no-check-server        Nao verifica alcancabilidade antes de abrir clientes.
  --check-only             Apenas verifica o servidor e sai.
  --once                   Cada cliente roda uma tentativa/frame e sai.
  --detach                 Nao espera os clientes fecharem.
  --dry-run                Registra e imprime comandos sem executar.
  -h, --help               Mostra esta ajuda.

Variaveis uteis:
  GROUNDFIRE_LAUNCHER_PYTHON    Python usado pelo launcher.
  GROUNDFIRE_LAUNCHER_LOG_DIR   Pasta dos logs.
  GROUNDFIRE_CLIENTS_LOG_FILE   Arquivo de log principal.
  GROUNDFIRE_SERVER_HOST        Host padrao do servidor.
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

is_positive_int() {
    [[ "$1" =~ ^[0-9]+$ ]] && (("$1" > 0))
}

is_non_negative_int() {
    [[ "$1" =~ ^[0-9]+$ ]]
}

is_client_preset() {
    case "$1" in
        2|4|6|8|12) return 0 ;;
        *) return 1 ;;
    esac
}

is_port() {
    [[ "$1" =~ ^[0-9]+$ ]] && (("$1" >= 1 && "$1" <= 65535))
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
        sock.sendto(encode_message(Ping(nonce="iniciar-clientes", issued_at=time.time())), (host, port))
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

cleanup_clients() {
    if [[ "$DETACH_MODE" == "1" || "$DRY_RUN_MODE" == "1" ]]; then
        return 0
    fi

    local pid
    for pid in "${CLIENT_PIDS[@]}"; do
        if kill -0 "$pid" >/dev/null 2>&1; then
            log "Encerrando cliente PID $pid."
            kill "$pid" >/dev/null 2>&1 || true
        fi
    done
}

cleanup_on_exit() {
    local status=$?
    cleanup_clients
    return "$status"
}

cleanup_on_signal() {
    log "Sinal de encerramento recebido."
    cleanup_clients
    exit 130
}

launch_tk_menu() {
    local python_bin
    python_bin=$(find_python) || {
        log "Python compativel nao encontrado para abrir o menu."
        return 1
    }

    log "Abrindo menu Tk dos clientes."
PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$python_bin" - "$SCRIPT_PATH" "$PROJECT_DIR" "$LOG_FILE" 2>&1 <<'PY' | tee -a "$LOG_FILE"
import os
import re
import subprocess
import sys

script_path, project_dir, log_file = sys.argv[1:4]

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except Exception as exc:
    print(f"Tkinter/Ttk indisponivel: {exc}", file=sys.stderr)
    raise SystemExit(2)

root = tk.Tk()
root.title("Groundfire - Clientes LAN")
root.configure(background="#111827")
root.geometry("600x590")
root.resizable(False, False)

style = ttk.Style(root)
try:
    style.theme_use("clam")
except tk.TclError:
    pass
style.configure("Root.TFrame", background="#111827")
style.configure("Panel.TLabelframe", background="#1f2937")
style.configure("Panel.TLabelframe.Label", background="#1f2937", foreground="#fde68a", font=("TkDefaultFont", 11, "bold"))
style.configure("Title.TLabel", background="#111827", foreground="#facc15", font=("TkDefaultFont", 20, "bold"))
style.configure("Text.TLabel", background="#111827", foreground="#e5e7eb")
style.configure("Field.TLabel", background="#1f2937", foreground="#fde68a")
style.configure("Primary.TButton", padding=10)
style.configure("Soft.TButton", padding=10)

main = ttk.Frame(root, style="Root.TFrame", padding=22)
main.pack(fill="both", expand=True)

ttk.Label(main, text="Groundfire LAN Clients", style="Title.TLabel").pack(anchor="w", pady=(0, 4))
ttk.Label(main, text="Abra varias instancias e conecte na sala LAN em poucos cliques.", style="Text.TLabel").pack(
    anchor="w", pady=(0, 18)
)

panel = ttk.LabelFrame(main, text="Clientes", style="Panel.TLabelframe", padding=(16, 12))
panel.pack(fill="x")
panel.columnconfigure(1, weight=1)
panel.columnconfigure(3, weight=1)

fields = {}

def add_field(label, default, row, column):
    ttk.Label(panel, text=label, style="Field.TLabel").grid(row=row, column=column, sticky="w", padx=(0, 8), pady=8)
    entry = ttk.Entry(panel)
    entry.insert(0, default)
    entry.grid(row=row, column=column + 1, sticky="ew", padx=(0, 12), pady=8)
    fields[label] = entry

add_field("Clientes", os.environ.get("GROUNDFIRE_CLIENT_COUNT", "2"), 0, 0)
add_field("Servidor", os.environ.get("GROUNDFIRE_SERVER_HOST", "127.0.0.1"), 0, 2)
add_field("Porta", os.environ.get("GROUNDFIRE_SERVER_PORT", "27015"), 1, 0)
add_field("Prefixo", os.environ.get("GROUNDFIRE_PLAYER_PREFIX", "Cliente LAN"), 1, 2)
add_field("Join timeout", os.environ.get("GROUNDFIRE_CLIENT_JOIN_TIMEOUT", "5"), 2, 0)
add_field("Keepalive", os.environ.get("GROUNDFIRE_CLIENT_KEEPALIVE_SECONDS", "86400"), 2, 2)
add_field("Delay", os.environ.get("GROUNDFIRE_CLIENT_START_DELAY", "0.15"), 3, 0)
add_field("Senha", os.environ.get("GROUNDFIRE_SERVER_PASSWORD", ""), 3, 2)

preset_frame = ttk.Frame(main, style="Root.TFrame")
preset_frame.pack(fill="x", pady=(10, 0))
ttk.Label(preset_frame, text="Presets:", style="Text.TLabel").pack(side="left", padx=(0, 8))

def set_client_count(count):
    fields["Clientes"].delete(0, tk.END)
    fields["Clientes"].insert(0, str(count))

for preset in (2, 4, 6, 8, 12):
    ttk.Button(
        preset_frame,
        text=str(preset),
        command=lambda count=preset: set_client_count(count),
        style="Soft.TButton",
    ).pack(side="left", padx=(0, 6))

ai_enabled = tk.BooleanVar(value=True)
visible_enabled = tk.BooleanVar(value=True)
check_server_enabled = tk.BooleanVar(value=True)
detach_enabled = tk.BooleanVar(value=False)
once_enabled = tk.BooleanVar(value=False)

checks = ttk.Frame(main, style="Root.TFrame")
checks.pack(fill="x", pady=(12, 4))
ttk.Checkbutton(checks, text="Jogadores de computador (-a)", variable=ai_enabled).pack(side="left")
ttk.Checkbutton(checks, text="Abrir uma tela por jogador", variable=visible_enabled).pack(side="left", padx=(16, 0))

checks_two = ttk.Frame(main, style="Root.TFrame")
checks_two.pack(fill="x", pady=(2, 4))
ttk.Checkbutton(checks_two, text="Verificar servidor UDP", variable=check_server_enabled).pack(side="left")
ttk.Checkbutton(checks_two, text="Uma tentativa (--once)", variable=once_enabled).pack(side="left", padx=(16, 0))
ttk.Checkbutton(checks_two, text="Nao esperar (--detach)", variable=detach_enabled).pack(side="left", padx=(16, 0))

status = tk.StringVar(value=f"Log: {log_file}")
ttk.Label(main, textvariable=status, style="Text.TLabel", wraplength=540, justify="left").pack(
    fill="x", pady=(10, 4)
)

def is_port(text):
    return text.isdigit() and 1 <= int(text) <= 65535

def is_positive_int(text):
    return text.isdigit() and int(text) > 0

def is_non_negative_number(text):
    try:
        return float(text) >= 0
    except ValueError:
        return False

def is_valid_host(text):
    host = text.strip()
    if not host or len(host) > 253:
        return False
    if host == "localhost":
        return True
    parts = host.split(".")
    if len(parts) == 4 and all(part.isdigit() for part in parts):
        return all(0 <= int(part) <= 255 for part in parts)
    label = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    return re.fullmatch(rf"{label}(?:\.{label})*", host) is not None

def validate_form():
    errors = []
    if not is_positive_int(fields["Clientes"].get().strip() or "1"):
        errors.append("Clientes deve ser um inteiro maior que zero.")
    if not is_valid_host(fields["Servidor"].get().strip() or "127.0.0.1"):
        errors.append("Servidor invalido.")
    if not is_port(fields["Porta"].get().strip() or "27015"):
        errors.append("Porta deve ficar entre 1 e 65535.")
    for label in ("Join timeout", "Keepalive", "Delay"):
        if not is_non_negative_number(fields[label].get().strip() or "0"):
            errors.append(f"{label} deve ser um numero maior ou igual a zero.")
    if errors:
        message = "\n".join(errors)
        status.set(message)
        messagebox.showerror("Groundfire", message)
        return False
    return True

def build_command(dry_run=False):
    count = fields["Clientes"].get().strip() or "1"
    cmd = [
        script_path,
        "-n",
        count,
        "--host",
        fields["Servidor"].get().strip() or "127.0.0.1",
        "--port",
        fields["Porta"].get().strip() or "27015",
        "--player-prefix",
        fields["Prefixo"].get().strip() or "Cliente LAN",
        "--join-timeout",
        fields["Join timeout"].get().strip() or "5",
        "--keepalive-seconds",
        fields["Keepalive"].get().strip() or "86400",
        "--client-delay",
        fields["Delay"].get().strip() or "0.15",
    ]
    password = fields["Senha"].get()
    if password:
        cmd.extend(["--password", password])
    if ai_enabled.get():
        cmd.append("-a")
        if visible_enabled.get():
            cmd.extend(["--visible-count", count])
        else:
            cmd.append("--sem-tela")
    if check_server_enabled.get():
        cmd.append("--check-server")
    if once_enabled.get():
        cmd.append("--once")
    if detach_enabled.get():
        cmd.append("--detach")
    if dry_run:
        cmd.append("--dry-run")
    return cmd

def start_clients():
    if not validate_form():
        return
    subprocess.Popen(build_command(), cwd=project_dir)
    status.set("Clientes iniciados. Veja os logs individuais para diagnostico.")
    messagebox.showinfo("Groundfire", "Clientes LAN iniciados.")

def check_server():
    if not validate_form():
        return
    cmd = [
        script_path,
        "--check-only",
        "--host",
        fields["Servidor"].get().strip() or "127.0.0.1",
        "--port",
        fields["Porta"].get().strip() or "27015",
        "--join-timeout",
        fields["Join timeout"].get().strip() or "5",
    ]
    completed = subprocess.run(cmd, cwd=project_dir, text=True, capture_output=True, check=False)
    output = (completed.stdout + completed.stderr).strip()
    if completed.returncode == 0:
        status.set("Servidor UDP respondeu.")
        messagebox.showinfo("Groundfire", "Servidor UDP respondeu.")
    else:
        status.set((output or "Servidor nao respondeu.").strip()[-440:])
        messagebox.showerror("Groundfire", "Servidor UDP nao respondeu.")

def test_command():
    if not validate_form():
        return
    completed = subprocess.run(
        build_command(dry_run=True),
        cwd=project_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    status.set((completed.stdout or completed.stderr or "Comandos registrados.").strip()[-440:])

buttons = ttk.Frame(main, style="Root.TFrame")
buttons.pack(fill="x", pady=(18, 0))
ttk.Button(buttons, text="Iniciar clientes", command=start_clients, style="Primary.TButton").pack(
    side="left", expand=True, fill="x", padx=(0, 8)
)
ttk.Button(buttons, text="Testar comandos", command=test_command, style="Soft.TButton").pack(
    side="left", expand=True, fill="x", padx=8
)
ttk.Button(buttons, text="Verificar servidor", command=check_server, style="Soft.TButton").pack(
    side="left", expand=True, fill="x", padx=8
)
ttk.Button(buttons, text="Sair", command=root.destroy, style="Soft.TButton").pack(
    side="left", expand=True, fill="x", padx=(8, 0)
)

root.mainloop()
PY
    return "${PIPESTATUS[0]}"
}

start_clients() {
    local count=1
    local host="${GROUNDFIRE_SERVER_HOST:-127.0.0.1}"
    local port="${GROUNDFIRE_SERVER_PORT:-27015}"
    local password="${GROUNDFIRE_SERVER_PASSWORD:-}"
    local player_prefix="${GROUNDFIRE_PLAYER_PREFIX:-Cliente LAN}"
    local join_timeout="${GROUNDFIRE_CLIENT_JOIN_TIMEOUT:-5}"
    local keepalive_seconds="${GROUNDFIRE_CLIENT_KEEPALIVE_SECONDS:-86400}"
    local computer_player=0
    local visible_count="${GROUNDFIRE_CLIENT_VISIBLE_COUNT:-}"
    local check_server="${GROUNDFIRE_CLIENT_CHECK_SERVER:-0}"
    local check_only=0
    local dry_run=0
    local once=0
    local wait_for_clients=1
    local delay_seconds="${GROUNDFIRE_CLIENT_START_DELAY:-0.15}"

    while (($#)); do
        case "$1" in
            -[0-9]*)
                count="${1#-}"; shift ;;
            -n|--num|--count)
                count="${2:?Valor ausente para $1}"; shift 2 ;;
            --preset)
                count="${2:?Valor ausente para --preset}"
                if ! is_client_preset "$count"; then
                    log "Preset de clientes invalido: $count. Use 2, 4, 6, 8 ou 12."
                    return 2
                fi
                shift 2 ;;
            -a)
                computer_player=1; shift ;;
            --host|--server)
                host="${2:?Valor ausente para $1}"; shift 2 ;;
            --port)
                port="${2:?Valor ausente para --port}"; shift 2 ;;
            --password)
                password="${2:?Valor ausente para --password}"; shift 2 ;;
            --player-prefix)
                player_prefix="${2:?Valor ausente para --player-prefix}"; shift 2 ;;
            --join-timeout)
                join_timeout="${2:?Valor ausente para --join-timeout}"; shift 2 ;;
            --keepalive-seconds)
                keepalive_seconds="${2:?Valor ausente para --keepalive-seconds}"; shift 2 ;;
            --client-delay)
                delay_seconds="${2:?Valor ausente para --client-delay}"; shift 2 ;;
            --visible-count)
                visible_count="${2:?Valor ausente para --visible-count}"; shift 2 ;;
            --com-tela|--show-client|--visible-client)
                visible_count=all; shift ;;
            --sem-tela|--headless-only)
                visible_count=0; shift ;;
            --check-server)
                check_server=1; shift ;;
            --no-check-server)
                check_server=0; shift ;;
            --check-only)
                check_server=1; check_only=1; shift ;;
            --cli)
                shift ;;
            --once)
                once=1; shift ;;
            --detach)
                wait_for_clients=0; shift ;;
            --dry-run)
                dry_run=1; shift ;;
            -h|--help)
                usage; return 0 ;;
            *)
                log "Opcao desconhecida para clientes: $1"
                usage
                return 2 ;;
        esac
    done

    if ! is_positive_int "$count"; then
        log "Quantidade de clientes invalida: $count"
        return 2
    fi
    if ! is_valid_host "$host"; then
        log "Host do servidor invalido: $host"
        return 2
    fi
    if ! is_port "$port"; then
        log "Porta do servidor invalida: $port"
        return 2
    fi
    if ! is_non_negative_number "$join_timeout"; then
        log "Timeout de entrada invalido: $join_timeout"
        return 2
    fi
    if ! is_non_negative_number "$keepalive_seconds"; then
        log "Keepalive invalido: $keepalive_seconds"
        return 2
    fi
    if ! is_non_negative_number "$delay_seconds"; then
        log "Intervalo entre clientes invalido: $delay_seconds"
        return 2
    fi
    if [[ -z "$visible_count" ]]; then
        if ((computer_player)); then
            visible_count="$count"
        else
            visible_count=0
        fi
    fi
    if [[ "$visible_count" == "all" ]]; then
        visible_count="$count"
    fi
    if ! is_non_negative_int "$visible_count"; then
        log "Quantidade de clientes com tela invalida: $visible_count"
        return 2
    fi
    if ((computer_player && visible_count > count)); then
        log "Quantidade de clientes com tela ($visible_count) nao pode passar do total ($count)."
        return 2
    fi
    if ((computer_player && once)); then
        keepalive_seconds=0
    fi
    if [[ "$check_server" != "0" && "$check_server" != "1" ]]; then
        log "Opcao de verificacao do servidor invalida: $check_server"
        return 2
    fi

    # Depois do parse, valide entradas antes de abrir varias janelas/processos.
    local python_bin
    python_bin=$(find_python) || {
        log "Python compativel nao encontrado no PATH."
        return 1
    }

    log "Preparando $count cliente(s) para conectar em $host:$port."
    if ((check_server)); then
        log "Verificando alcance UDP do servidor em $host:$port por ate ${join_timeout}s."
        if ((dry_run)); then
            log "Dry-run ativo: verificacao UDP nao sera executada."
        elif ! wait_for_server "$python_bin" "$host" "$port" "$join_timeout"; then
            log "Servidor nao respondeu ao ping UDP em ate ${join_timeout}s."
            return 1
        else
            log "Servidor respondeu ao ping UDP."
        fi
    fi
    if ((check_only)); then
        return 0
    fi
    if ((computer_player)); then
        log "Modo IA ativado: clientes entram como jogadores de computador."
        if ((visible_count > 0)); then
            if ((visible_count == count)); then
                log "Modo com tela: todos os $count cliente(s) IA abrirao janela Pygame."
            else
                log "Modo com tela: $visible_count cliente(s) IA abrirao janela Pygame; os demais ficam headless."
            fi
        else
            log "Modo sem tela: todos os clientes IA ficam headless."
        fi
    else
        log "Clientes humanos abrirao janelas Pygame."
    fi
    log "Arquivo de log principal: $LOG_FILE"

    CLIENT_PIDS=()
    DETACH_MODE="$((1 - wait_for_clients))"
    DRY_RUN_MODE="$dry_run"
    # Se o usuario interromper o launcher, encerramos os clientes filhos tambem.
    trap cleanup_on_exit EXIT
    trap cleanup_on_signal INT TERM

    local index
    for ((index = 1; index <= count; index++)); do
        local player_name
        if ((computer_player)); then
            player_name="CPU LAN $index"
        else
            player_name="$player_prefix $index"
        fi

        local cmd=(
            "$python_bin"
            -m groundfire.client
            --connect "$host:$port"
            --player-name "$player_name"
            --log-network-events
        )

        # Em modo IA o servidor joga pelo tank; --visible-count pode deixar parte dos clientes headless para carga.
        if [[ -n "$password" ]]; then
            cmd+=(--password "$password")
        fi
        if ((computer_player)); then
            cmd+=(--computer-player)
            if ((index > visible_count)); then
                cmd+=(
                    --headless-client
                    --join-timeout "$join_timeout"
                    --keepalive-seconds "$keepalive_seconds"
                )
            fi
        fi
        if ((once)); then
            cmd+=(--once)
        fi

        local client_log="$LOG_DIR/iniciar-clientes-$RUN_ID-cliente-$index.log"
        log "Cliente $index ($player_name): $(quote_command "${cmd[@]}")"
        log "Log do cliente $index: $client_log"

        if ((dry_run)); then
            printf 'DRY-RUN client %d command: %s\n' "$index" "$(quote_command "${cmd[@]}")"
            continue
        fi

        PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" "${cmd[@]}" >> "$client_log" 2>&1 &
        CLIENT_PIDS+=("$!")
        log "Cliente $index iniciado com PID ${CLIENT_PIDS[-1]}."
        sleep "$delay_seconds"
    done

    if ((dry_run)); then
        return 0
    fi

    if ((wait_for_clients)); then
        local status=0
        local pid
        for pid in "${CLIENT_PIDS[@]}"; do
            if ! wait "$pid"; then
                status=1
                log "Cliente PID $pid encerrou com erro."
            else
                log "Cliente PID $pid encerrou normalmente."
            fi
        done
        return "$status"
    fi

    log "Clientes destacados; o launcher nao aguardara encerramento."
    return 0
}

main() {
    log "Launcher de clientes chamado com argumentos: $(quote_command "$@")"

    if (($# == 0)); then
        launch_tk_menu
        return $?
    fi

    if [[ "$1" == "--menu" ]]; then
        shift
        if (($#)); then
            log "--menu nao aceita argumentos extras: $(quote_command "$@")"
            return 2
        fi
        launch_tk_menu
        return $?
    fi

    start_clients "$@"
}

rotate_log_if_needed "$LOG_FILE"
main "$@"
