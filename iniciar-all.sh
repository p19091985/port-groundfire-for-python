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
LOG_FILE="${GROUNDFIRE_ALL_LOG_FILE:-$LOG_DIR/all_debug.log}"

mkdir -p "$LOG_DIR"

SERVER_PID=""
CLIENT_LAUNCHER_PID=""
SERVER_OWN_GROUP=0
CLIENT_LAUNCHER_OWN_GROUP=0
DETACH_MODE=0
DRY_RUN_MODE=0

# Log central da orquestracao completa; servidor e clientes tambem recebem logs dedicados.
log() {
    local message="$1"
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$message" | tee -a "$LOG_FILE"
}

usage() {
    cat <<'EOF'
Uso:
  ./iniciar-all.sh
      Abre a interface grafica Ttk para iniciar uma partida automatica.

  ./iniciar-all.sh -A [opcoes]
      Usa iniciar-server.sh e iniciar-clientes.sh para subir 1 servidor LAN e 6 tanks IA.

Modos de acesso:
  --menu                  Interface grafica Ttk de gerenciamento.
  --cli, -A, --auto       Comando de texto/CLI para automacao.

Opcoes:
  -A, --auto, --cli       Inicia imediatamente sem abrir a interface Ttk.
  -n, --tanks NUMERO      Quantidade de tanks/clients IA. Padrao: 6
  --preset NUMERO         Usa um preset de tanks IA: 2, 4, 6, 8 ou 12.
  --bind-host ENDERECO    Interface do servidor. Padrao: 0.0.0.0
  --host ENDERECO         Host usado pelos clientes. Padrao: 127.0.0.1
  --port PORTA            Porta UDP do jogo. Padrao: 27015
  --discovery-port PORTA  Porta de descoberta LAN. Padrao: 27016
  --server-name NOME      Nome do servidor LAN.
  --password SENHA        Senha do servidor e dos clientes.
  --rounds NUMERO         Quantidade de rounds da partida. Padrao: 20
  --server-timeout SEG    Tempo maximo para aguardar o servidor. Padrao: 5
  --join-timeout SEG      Tempo maximo para cada cliente IA entrar. Padrao: 5
  --keepalive-seconds SEG Tempo que cada cliente headless fica vivo. Padrao: 86400
  --client-delay SEG      Intervalo entre clientes. Padrao: 0.02
  --visible-count NUM     Quantos clientes IA abrem janela Pygame. Padrao: todos.
  --com-tela              Abre uma janela Pygame para cada cliente IA.
  --sem-tela, --headless-only
                          Mantem todos os clientes IA sem janela.
  --detach                Inicia tudo e libera o terminal.
  --dry-run               Mostra e registra os comandos sem executar.
  --menu                  Abre a interface grafica Ttk explicitamente.
  -h, --help              Mostra esta ajuda.

Exemplos:
  ./iniciar-all.sh
  ./iniciar-all.sh -A
  ./iniciar-all.sh -A -n 8
  ./iniciar-all.sh -A --host 192.168.0.10 --port 27015
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

is_tank_preset() {
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

cleanup_processes() {
    if [[ "$DETACH_MODE" == "1" || "$DRY_RUN_MODE" == "1" ]]; then
        return 0
    fi

    terminate_process "launcher de clientes" "$CLIENT_LAUNCHER_PID" "$CLIENT_LAUNCHER_OWN_GROUP"
    terminate_process "launcher do servidor" "$SERVER_PID" "$SERVER_OWN_GROUP"
}

terminate_process() {
    local label="$1"
    local pid="$2"
    local own_group="$3"

    if [[ -z "$pid" ]] || ! kill -0 "$pid" >/dev/null 2>&1; then
        return 0
    fi

    log "Encerrando $label PID $pid."
    if [[ "$own_group" == "1" ]]; then
        kill -- "-$pid" >/dev/null 2>&1 || kill "$pid" >/dev/null 2>&1 || true
        return 0
    fi
    kill "$pid" >/dev/null 2>&1 || true
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

launch_ttk_menu() {
    local python_bin
    python_bin=$(find_python) || {
        log "Python compativel nao encontrado para abrir o menu Ttk."
        return 1
    }

    log "Abrindo interface Ttk do jogo automatico."
    PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$python_bin" - "$SCRIPT_PATH" "$PROJECT_DIR" "$LOG_FILE" 2>&1 <<'PY' | tee -a "$LOG_FILE"
import os
import re
import shlex
import subprocess
import sys

script_path, project_dir, log_file = sys.argv[1:4]

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except Exception as exc:
    print(f"Tkinter/Ttk indisponivel: {exc}", file=sys.stderr)
    raise SystemExit(2)


def quote_command(command):
    return " ".join(shlex.quote(part) for part in command)


root = tk.Tk()
root.title("Groundfire - Jogo automatico LAN")
root.geometry("660x720")
root.minsize(640, 560)

style = ttk.Style(root)
try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure("Root.TFrame", background="#101827")
style.configure("Header.TFrame", background="#123047")
style.configure("Panel.TLabelframe", background="#162033", bordercolor="#38bdf8")
style.configure("Panel.TLabelframe.Label", background="#162033", foreground="#fde68a", font=("TkDefaultFont", 11, "bold"))
style.configure("Title.TLabel", background="#123047", foreground="#f8fafc", font=("TkDefaultFont", 20, "bold"))
style.configure("Subtitle.TLabel", background="#123047", foreground="#bae6fd", font=("TkDefaultFont", 10))
style.configure("Field.TLabel", background="#162033", foreground="#dbeafe")
style.configure("Status.TLabel", background="#101827", foreground="#cbd5e1")
style.configure("Accent.TButton", font=("TkDefaultFont", 10, "bold"), padding=10)
style.configure("Soft.TButton", padding=10)
style.configure("Danger.TButton", padding=10)
style.map("Accent.TButton", foreground=[("active", "#052e16")], background=[("active", "#86efac")])

root.configure(background="#101827")
canvas = tk.Canvas(root, background="#101827", borderwidth=0, highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

main = ttk.Frame(canvas, style="Root.TFrame", padding=18)
main_window = canvas.create_window((0, 0), window=main, anchor="nw")

def refresh_scroll_region(_event=None):
    canvas.configure(scrollregion=canvas.bbox("all"))


def fit_main_width(event):
    canvas.itemconfigure(main_window, width=event.width)


def scroll_with_wheel(event):
    delta = -1 if event.delta > 0 else 1
    canvas.yview_scroll(delta, "units")


main.bind("<Configure>", refresh_scroll_region)
canvas.bind("<Configure>", fit_main_width)
canvas.bind_all("<MouseWheel>", scroll_with_wheel)
canvas.bind_all("<Button-4>", lambda _event: canvas.yview_scroll(-1, "units"))
canvas.bind_all("<Button-5>", lambda _event: canvas.yview_scroll(1, "units"))

header = ttk.Frame(main, style="Header.TFrame", padding=(18, 16))
header.pack(fill="x", pady=(0, 14))
ttk.Label(header, text="Groundfire LAN Auto", style="Title.TLabel").pack(anchor="w")
ttk.Label(
    header,
    text="Servidor + tanks IA usando iniciar-server.sh e iniciar-clientes.sh.",
    style="Subtitle.TLabel",
).pack(anchor="w", pady=(4, 0))

panel = ttk.LabelFrame(main, text="Partida", style="Panel.TLabelframe", padding=(16, 12))
panel.pack(fill="x")
panel.columnconfigure(1, weight=1)
panel.columnconfigure(3, weight=1)

fields = {}


def add_field(key, label, default, row, column):
    ttk.Label(panel, text=label, style="Field.TLabel").grid(row=row, column=column, sticky="w", padx=(0, 8), pady=7)
    entry = ttk.Entry(panel)
    entry.insert(0, default)
    entry.grid(row=row, column=column + 1, sticky="ew", padx=(0, 14), pady=7)
    fields[key] = entry


add_field("tanks", "Tanks IA", os.environ.get("GROUNDFIRE_AUTO_TANKS", "6"), 0, 0)
add_field("port", "Porta", os.environ.get("GROUNDFIRE_SERVER_PORT", "27015"), 0, 2)
add_field("bind_host", "Bind server", os.environ.get("GROUNDFIRE_SERVER_BIND_HOST", "0.0.0.0"), 1, 0)
add_field("host", "Host clientes", os.environ.get("GROUNDFIRE_SERVER_HOST", "127.0.0.1"), 1, 2)
add_field("discovery_port", "Descoberta", os.environ.get("GROUNDFIRE_DISCOVERY_PORT", "27016"), 2, 0)
add_field("server_name", "Nome", os.environ.get("GROUNDFIRE_SERVER_NAME", "Groundfire Auto 6 Tanks"), 2, 2)
add_field("rounds", "Rounds", os.environ.get("GROUNDFIRE_NUM_ROUNDS", "20"), 3, 0)
add_field("server_timeout", "Timeout server", os.environ.get("GROUNDFIRE_SERVER_TIMEOUT", "5"), 3, 2)
add_field("join_timeout", "Timeout cliente", os.environ.get("GROUNDFIRE_CLIENT_JOIN_TIMEOUT", "5"), 4, 0)
add_field("keepalive", "Keepalive", os.environ.get("GROUNDFIRE_CLIENT_KEEPALIVE_SECONDS", "86400"), 4, 2)
add_field("client_delay", "Delay clientes", os.environ.get("GROUNDFIRE_CLIENT_START_DELAY", "0.02"), 5, 0)
add_field("password", "Senha", os.environ.get("GROUNDFIRE_SERVER_PASSWORD", ""), 5, 2)

preset_frame = ttk.Frame(main, style="Root.TFrame", padding=(0, 10, 0, 0))
preset_frame.pack(fill="x")
ttk.Label(preset_frame, text="Presets:", style="Status.TLabel").pack(side="left", padx=(0, 8))

def set_tank_count(count):
    fields["tanks"].delete(0, tk.END)
    fields["tanks"].insert(0, str(count))

for preset in (2, 4, 6, 8, 12):
    ttk.Button(
        preset_frame,
        text=str(preset),
        command=lambda count=preset: set_tank_count(count),
        style="Soft.TButton",
    ).pack(side="left", padx=(0, 6))

visible_enabled = tk.BooleanVar(value=True)
detach_enabled = tk.BooleanVar(value=False)
checks = ttk.Frame(main, style="Root.TFrame", padding=(0, 12, 0, 0))
checks.pack(fill="x")
ttk.Checkbutton(checks, text="Abrir uma tela por jogador IA", variable=visible_enabled).pack(anchor="w")
ttk.Checkbutton(checks, text="Liberar terminal depois de iniciar (--detach)", variable=detach_enabled).pack(
    anchor="w", pady=(4, 0)
)

status = tk.StringVar(value=f"Log: {log_file}")
ttk.Label(main, textvariable=status, style="Status.TLabel", wraplength=570, justify="left").pack(fill="x", pady=(12, 8))


def value(key, fallback):
    text = fields[key].get().strip()
    return text or fallback


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
    if not is_positive_int(value("tanks", "6")):
        errors.append("Tanks IA deve ser um inteiro maior que zero.")
    if not is_valid_host(value("bind_host", "0.0.0.0")):
        errors.append("Bind server invalido.")
    if not is_valid_host(value("host", "127.0.0.1")):
        errors.append("Host dos clientes invalido.")
    if not is_port(value("port", "27015")):
        errors.append("Porta deve ficar entre 1 e 65535.")
    if not is_port(value("discovery_port", "27016")):
        errors.append("Descoberta deve ficar entre 1 e 65535.")
    if not is_positive_int(value("rounds", "20")):
        errors.append("Rounds deve ser um inteiro maior que zero.")
    for key, label in (
        ("server_timeout", "Timeout server"),
        ("join_timeout", "Timeout cliente"),
        ("keepalive", "Keepalive"),
        ("client_delay", "Delay clientes"),
    ):
        if not is_non_negative_number(value(key, "0")):
            errors.append(f"{label} deve ser um numero maior ou igual a zero.")
    if errors:
        message = "\n".join(errors)
        status.set(message)
        messagebox.showerror("Groundfire", message)
        return False
    return True


def build_command(dry_run=False):
    command = [
        "bash",
        script_path,
        "-A",
        "-n",
        value("tanks", "6"),
        "--bind-host",
        value("bind_host", "0.0.0.0"),
        "--host",
        value("host", "127.0.0.1"),
        "--port",
        value("port", "27015"),
        "--discovery-port",
        value("discovery_port", "27016"),
        "--server-name",
        value("server_name", "Groundfire Auto 6 Tanks"),
        "--rounds",
        value("rounds", "20"),
        "--server-timeout",
        value("server_timeout", "5"),
        "--join-timeout",
        value("join_timeout", "5"),
        "--keepalive-seconds",
        value("keepalive", "86400"),
        "--client-delay",
        value("client_delay", "0.02"),
    ]
    password = fields["password"].get()
    if password:
        command.extend(["--password", password])
    if visible_enabled.get():
        command.extend(["--visible-count", value("tanks", "6")])
    else:
        command.append("--sem-tela")
    if detach_enabled.get():
        command.append("--detach")
    if dry_run:
        command.append("--dry-run")
    return command


def append_log(text):
    with open(log_file, "a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def start_game():
    if not validate_form():
        return
    command = build_command()
    append_log(f"[ttk] comando: {quote_command(command)}\n")
    log_handle = open(log_file, "a", encoding="utf-8")
    subprocess.Popen(command, cwd=project_dir, stdout=log_handle, stderr=subprocess.STDOUT)
    log_handle.close()
    status.set("Partida automatica iniciada. Acompanhe all_debug.log e os logs dedicados.")
    messagebox.showinfo("Groundfire", f"Servidor e {value('tanks', '6')} tanks IA foram disparados.")


def test_command():
    if not validate_form():
        return
    command = build_command(dry_run=True)
    completed = subprocess.run(command, cwd=project_dir, text=True, capture_output=True, check=False)
    output = (completed.stdout + completed.stderr).strip()
    append_log(f"[ttk dry-run] {quote_command(command)}\n{output}\n")
    status.set((output or "Comando registrado.").strip()[-560:])


buttons = ttk.Frame(main, style="Root.TFrame")
buttons.pack(fill="x", pady=(12, 0))
ttk.Button(buttons, text="Iniciar automatico", command=start_game, style="Accent.TButton").pack(
    side="left", expand=True, fill="x", padx=(0, 8)
)
ttk.Button(buttons, text="Testar comandos", command=test_command, style="Soft.TButton").pack(
    side="left", expand=True, fill="x", padx=8
)
ttk.Button(buttons, text="Sair", command=root.destroy, style="Danger.TButton").pack(
    side="left", expand=True, fill="x", padx=(8, 0)
)

root.mainloop()
PY
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
        sock.sendto(encode_message(Ping(nonce="iniciar-all", issued_at=time.time())), (host, port))
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

start_automatic_game() {
    local tank_count="${GROUNDFIRE_AUTO_TANKS:-6}"
    local bind_host="${GROUNDFIRE_SERVER_BIND_HOST:-0.0.0.0}"
    local connect_host="${GROUNDFIRE_SERVER_HOST:-127.0.0.1}"
    local port="${GROUNDFIRE_SERVER_PORT:-27015}"
    local discovery_port="${GROUNDFIRE_DISCOVERY_PORT:-27016}"
    local server_name="${GROUNDFIRE_SERVER_NAME:-Groundfire Auto 6 Tanks}"
    local password="${GROUNDFIRE_SERVER_PASSWORD:-}"
    local rounds="${GROUNDFIRE_NUM_ROUNDS:-20}"
    local server_timeout="${GROUNDFIRE_SERVER_TIMEOUT:-5}"
    local join_timeout="${GROUNDFIRE_CLIENT_JOIN_TIMEOUT:-5}"
    local keepalive_seconds="${GROUNDFIRE_CLIENT_KEEPALIVE_SECONDS:-86400}"
    local client_delay="${GROUNDFIRE_CLIENT_START_DELAY:-0.02}"
    local visible_count="${GROUNDFIRE_CLIENT_VISIBLE_COUNT:-}"
    local detach=0
    local dry_run=0

    while (($#)); do
        case "$1" in
            -A|--auto)
                shift ;;
            --cli)
                shift ;;
            -n|--tanks|--clients)
                tank_count="${2:?Valor ausente para $1}"; shift 2 ;;
            --preset)
                tank_count="${2:?Valor ausente para --preset}"
                if ! is_tank_preset "$tank_count"; then
                    log "Preset de tanks invalido: $tank_count. Use 2, 4, 6, 8 ou 12."
                    return 2
                fi
                shift 2 ;;
            --bind-host)
                bind_host="${2:?Valor ausente para --bind-host}"; shift 2 ;;
            --host|--server)
                connect_host="${2:?Valor ausente para $1}"; shift 2 ;;
            --port)
                port="${2:?Valor ausente para --port}"; shift 2 ;;
            --discovery-port)
                discovery_port="${2:?Valor ausente para --discovery-port}"; shift 2 ;;
            --server-name)
                server_name="${2:?Valor ausente para --server-name}"; shift 2 ;;
            --password)
                password="${2:?Valor ausente para --password}"; shift 2 ;;
            --rounds|--num-rounds)
                rounds="${2:?Valor ausente para $1}"; shift 2 ;;
            --server-timeout)
                server_timeout="${2:?Valor ausente para --server-timeout}"; shift 2 ;;
            --join-timeout)
                join_timeout="${2:?Valor ausente para --join-timeout}"; shift 2 ;;
            --keepalive-seconds)
                keepalive_seconds="${2:?Valor ausente para --keepalive-seconds}"; shift 2 ;;
            --client-delay)
                client_delay="${2:?Valor ausente para --client-delay}"; shift 2 ;;
            --visible-count)
                visible_count="${2:?Valor ausente para --visible-count}"; shift 2 ;;
            --com-tela|--show-client|--visible-client)
                visible_count=all; shift ;;
            --sem-tela|--headless-only)
                visible_count=0; shift ;;
            --detach)
                detach=1; shift ;;
            --dry-run)
                dry_run=1; shift ;;
            --menu)
                launch_ttk_menu; return $? ;;
            -h|--help)
                usage; return 0 ;;
            *)
                log "Opcao desconhecida: $1"
                usage
                return 2 ;;
        esac
    done

    if ! is_positive_int "$tank_count"; then
        log "Quantidade de tanks invalida: $tank_count"
        return 2
    fi
    if ! is_valid_host "$bind_host"; then
        log "Host de bind invalido: $bind_host"
        return 2
    fi
    if ! is_valid_host "$connect_host"; then
        log "Host dos clientes invalido: $connect_host"
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
    if ! is_non_negative_number "$server_timeout"; then
        log "Timeout do servidor invalido: $server_timeout"
        return 2
    fi
    if ! is_non_negative_number "$join_timeout"; then
        log "Timeout de entrada dos clientes invalido: $join_timeout"
        return 2
    fi
    if ! is_non_negative_number "$keepalive_seconds"; then
        log "Keepalive dos clientes invalido: $keepalive_seconds"
        return 2
    fi
    if ! is_non_negative_number "$client_delay"; then
        log "Intervalo entre clientes invalido: $client_delay"
        return 2
    fi
    if [[ -z "$visible_count" || "$visible_count" == "all" ]]; then
        visible_count="$tank_count"
    fi
    if ! is_non_negative_int "$visible_count"; then
        log "Quantidade de clientes com tela invalida: $visible_count"
        return 2
    fi
    if ((visible_count > tank_count)); then
        log "Quantidade de clientes com tela ($visible_count) nao pode passar do total ($tank_count)."
        return 2
    fi

    local python_bin
    python_bin=$(find_python) || {
        log "Python compativel nao encontrado no PATH."
        return 1
    }

    local server_script="$PROJECT_DIR/iniciar-server.sh"
    local clients_script="$PROJECT_DIR/iniciar-clientes.sh"
    if [[ ! -f "$server_script" || ! -f "$clients_script" ]]; then
        log "Scripts dependentes nao encontrados: iniciar-server.sh ou iniciar-clientes.sh."
        return 1
    fi

    DETACH_MODE="$detach"
    DRY_RUN_MODE="$dry_run"
    trap cleanup_on_exit EXIT
    trap cleanup_on_signal INT TERM

    local server_log="$LOG_DIR/iniciar-all-$RUN_ID-server.log"
    local clients_log="$LOG_DIR/iniciar-all-$RUN_ID-clients.log"
    local server_cmd=(
        bash "$server_script"
        -A
        --host "$bind_host"
        --port "$port"
        --discovery-port "$discovery_port"
        --server-name "$server_name"
        --rounds "$rounds"
        --max-players "$tank_count"
        --sem-tela
    )
    if [[ -n "$password" ]]; then
        server_cmd+=(--password "$password")
    fi

    local clients_cmd=(
        bash "$clients_script"
        -n "$tank_count"
        -a
        --host "$connect_host"
        --port "$port"
        --player-prefix "CPU LAN"
        --join-timeout "$join_timeout"
        --keepalive-seconds "$keepalive_seconds"
        --client-delay "$client_delay"
    )
    if ((visible_count > 0)); then
        clients_cmd+=(--visible-count "$visible_count")
    else
        clients_cmd+=(--sem-tela)
    fi
    if [[ -n "$password" ]]; then
        clients_cmd+=(--password "$password")
    fi
    if ((detach)); then
        clients_cmd+=(--detach)
    fi

    log "Iniciando jogo automatico via scripts: 1 servidor + $tank_count tanks IA + $rounds rounds."
    log "Clientes IA com janela Pygame: $visible_count."
    log "Log principal: $LOG_FILE"
    log "Log do servidor: $server_log"
    log "Log dos clientes: $clients_log"
    log "Launcher do servidor: $(quote_command "${server_cmd[@]}")"
    log "Launcher dos clientes: $(quote_command "${clients_cmd[@]}")"

    if ((dry_run)); then
        printf 'DRY-RUN server launcher command: %s\n' "$(quote_command "${server_cmd[@]}")" | tee -a "$LOG_FILE"
        if ! PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
            GROUNDFIRE_LAUNCHER_LOG_DIR="$LOG_DIR" \
            GROUNDFIRE_LAUNCHER_PYTHON="$python_bin" \
            GROUNDFIRE_SERVER_LOG_FILE="$server_log" \
            "${server_cmd[@]}" --dry-run 2>&1 | tee -a "$LOG_FILE"; then
            return 1
        fi

        printf 'DRY-RUN clients launcher command: %s\n' "$(quote_command "${clients_cmd[@]}")" | tee -a "$LOG_FILE"
        if ! PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
            GROUNDFIRE_LAUNCHER_LOG_DIR="$LOG_DIR" \
            GROUNDFIRE_LAUNCHER_PYTHON="$python_bin" \
            GROUNDFIRE_CLIENTS_LOG_FILE="$clients_log" \
            "${clients_cmd[@]}" --dry-run 2>&1 | tee -a "$LOG_FILE"; then
            return 1
        fi
        return 0
    fi

    if command -v setsid >/dev/null 2>&1; then
        SERVER_OWN_GROUP=1
        PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
            GROUNDFIRE_LAUNCHER_LOG_DIR="$LOG_DIR" \
            GROUNDFIRE_LAUNCHER_PYTHON="$python_bin" \
            GROUNDFIRE_SERVER_LOG_FILE="$server_log" \
            setsid "${server_cmd[@]}" >> "$LOG_FILE" 2>&1 &
    else
        PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
            GROUNDFIRE_LAUNCHER_LOG_DIR="$LOG_DIR" \
            GROUNDFIRE_LAUNCHER_PYTHON="$python_bin" \
            GROUNDFIRE_SERVER_LOG_FILE="$server_log" \
            "${server_cmd[@]}" >> "$LOG_FILE" 2>&1 &
    fi
    SERVER_PID=$!
    log "Servidor disparado pelo iniciar-server.sh com PID $SERVER_PID. Aguardando UDP em $connect_host:$port."

    if ! wait_for_server "$python_bin" "$connect_host" "$port" "$server_timeout"; then
        log "Servidor nao respondeu em ate ${server_timeout}s."
        return 1
    fi

    log "Servidor respondeu. Disparando clientes pelo iniciar-clientes.sh."
    if command -v setsid >/dev/null 2>&1; then
        CLIENT_LAUNCHER_OWN_GROUP=1
        PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
            GROUNDFIRE_LAUNCHER_LOG_DIR="$LOG_DIR" \
            GROUNDFIRE_LAUNCHER_PYTHON="$python_bin" \
            GROUNDFIRE_CLIENTS_LOG_FILE="$clients_log" \
            setsid "${clients_cmd[@]}" >> "$LOG_FILE" 2>&1 &
    else
        PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
            GROUNDFIRE_LAUNCHER_LOG_DIR="$LOG_DIR" \
            GROUNDFIRE_LAUNCHER_PYTHON="$python_bin" \
            GROUNDFIRE_CLIENTS_LOG_FILE="$clients_log" \
            "${clients_cmd[@]}" >> "$LOG_FILE" 2>&1 &
    fi
    CLIENT_LAUNCHER_PID=$!

    log "Launcher de clientes iniciado com PID $CLIENT_LAUNCHER_PID."
    log "Jogo automatico iniciado com $tank_count tanks IA usando iniciar-server.sh e iniciar-clientes.sh."
    if ((visible_count > 0)); then
        log "As janelas do jogo foram disparadas por iniciar-clientes.sh; clientes headless ficam vivos por ${keepalive_seconds}s quando houver algum."
    else
        log "Clientes headless ficarao vivos por ${keepalive_seconds}s ou ate Ctrl+C."
    fi
    log "Pressione Ctrl+C neste terminal para encerrar servidor e clientes."

    if ((detach)); then
        log "Modo detach ativo. Servidor PID: $SERVER_PID. Launcher de clientes PID: $CLIENT_LAUNCHER_PID."
        return 0
    fi

    wait "$SERVER_PID"
}

main() {
    log "Launcher completo chamado com argumentos: $(quote_command "$@")"

    if (($# == 0)); then
        launch_ttk_menu
        return $?
    fi

    start_automatic_game "$@"
}

rotate_log_if_needed "$LOG_FILE"
main "$@"
