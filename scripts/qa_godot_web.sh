#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
BROWSER_BIN="${CHROMIUM_BIN:-${BROWSER_BIN:-}}"
UPDATE_GOLDENS=0

case "${1:-}" in
    --update-goldens)
        UPDATE_GOLDENS=1
        ;;
    ""|--check)
        ;;
    *)
        printf 'Usage: %s [--check|--update-goldens]\n' "$0" >&2
        exit 2
        ;;
esac

if [[ -z "$BROWSER_BIN" ]]; then
    for candidate in chromium chromium-browser google-chrome; do
        if command -v "$candidate" >/dev/null 2>&1; then
            BROWSER_BIN=$(command -v "$candidate")
            break
        fi
    done
fi

if [[ -z "$BROWSER_BIN" || ! -x "$BROWSER_BIN" ]]; then
    printf 'Chromium/Chrome executable not found. Set CHROMIUM_BIN or BROWSER_BIN.\n' >&2
    exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    printf 'Python executable not found: %s\n' "$PYTHON_BIN" >&2
    exit 1
fi

"$ROOT_DIR/scripts/export_godot.sh" web

tmp_dir=$(mktemp -d)
server_log="$tmp_dir/http.log"
gateway_log="$tmp_dir/gateway.log"
auth_gateway_log="$tmp_dir/auth-gateway.log"
full_gateway_log="$tmp_dir/full-gateway.log"
full_gateway_holder_log="$tmp_dir/full-gateway-holder.log"
full_gateway_ready="$tmp_dir/full-gateway-holder.ready"
closed_gateway_log="$tmp_dir/closed-gateway.log"
banned_gateway_log="$tmp_dir/banned-gateway.log"
user_data_dir="$tmp_dir/chromium-user"
actual_dir="$ROOT_DIR/.tmp/godot_browser_actual"
golden_dir="$ROOT_DIR/docs/references/godot_browser_visual"
qa_fixture_dir="$ROOT_DIR/build/godot-web/qa"
mkdir -p "$actual_dir" "$golden_dir"
mkdir -p "$qa_fixture_dir"

reserve_port() {
    "$PYTHON_BIN" - <<'PY'
import socket

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

wait_for_tcp_port() {
    local label="$1"
    local port="$2"
    local log_path="$3"
    for _attempt in $(seq 1 50); do
        if "$PYTHON_BIN" - <<PY >/dev/null 2>&1
import socket
with socket.create_connection(("127.0.0.1", $port), timeout=0.2):
    pass
PY
        then
            return 0
        fi
        sleep 0.1
    done
    printf 'Timed out waiting for %s on port %s.\n' "$label" "$port" >&2
    cat "$log_path" >&2 || true
    exit 1
}

"$PYTHON_BIN" - "$qa_fixture_dir/server_directory.json" <<'PY'
import json
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(
    json.dumps(
        {
            "schema": 1,
            "servers": [
                {
                    "name": "QA Open Arena",
                    "game": "Groundfire",
                    "players": "1/8",
                    "map": "QA Hills",
                    "latency": "18ms",
                    "source": "online",
                    "endpoint": "ws://127.0.0.1:9/qa-open",
                    "passworded": False,
                },
                {
                    "name": "QA Password Arena",
                    "game": "Groundfire",
                    "players": "8/8",
                    "map": "QA Canyon",
                    "latency": "42ms",
                    "source": "online",
                    "endpoint": "ws://127.0.0.1:9/qa-password",
                    "passworded": True,
                },
                {
                    "name": "QA LAN Hidden",
                    "game": "Groundfire",
                    "players": "0/8",
                    "map": "QA LAN",
                    "latency": "LAN",
                    "source": "lan",
                    "endpoint": "127.0.0.1:27015",
                    "passworded": False,
                },
            ],
        },
        indent=2,
    ),
    encoding="utf-8",
)
PY

port=$(reserve_port)
gateway_port=$(reserve_port)
auth_gateway_port=$(reserve_port)
full_gateway_port=$(reserve_port)
closed_gateway_port=$(reserve_port)
banned_gateway_port=$(reserve_port)

cleanup() {
    for pid in \
        "${server_pid:-}" \
        "${gateway_pid:-}" \
        "${auth_gateway_pid:-}" \
        "${full_gateway_holder_pid:-}" \
        "${full_gateway_pid:-}" \
        "${closed_gateway_pid:-}" \
        "${banned_gateway_pid:-}"; do
        if [[ -n "$pid" ]]; then
            kill "$pid" >/dev/null 2>&1 || true
            wait "$pid" >/dev/null 2>&1 || true
        fi
    done
    rm -rf "$tmp_dir"
}
trap cleanup EXIT

"$PYTHON_BIN" - "$port" "$ROOT_DIR/build/godot-web" >"$server_log" 2>&1 <<'PY' &
import functools
import http.server
import sys

port = int(sys.argv[1])
directory = sys.argv[2]


class GroundfireQAHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        path = self.path.split("?", 1)[0]
        if path == "/qa/server_directory.json":
            self.send_header("Cache-Control", "public, max-age=30, must-revalidate")
            self.send_header("ETag", '"groundfire-qa-directory-v1"')
            self.send_header("X-Groundfire-Directory-Refresh", "30")
        elif path == "/" or path == "/index.html":
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()


server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", port),
    functools.partial(GroundfireQAHandler, directory=directory),
)
server.serve_forever()
PY
server_pid=$!

PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m groundfire_net.websocket_gateway \
    --host 127.0.0.1 \
    --port "$gateway_port" \
    --password qa-secret >"$gateway_log" 2>&1 &
gateway_pid=$!

PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m groundfire_net.websocket_gateway \
    --host 127.0.0.1 \
    --port "$auth_gateway_port" \
    --auth-token qa-token >"$auth_gateway_log" 2>&1 &
auth_gateway_pid=$!

PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m groundfire_net.websocket_gateway \
    --host 127.0.0.1 \
    --port "$full_gateway_port" \
    --max-players 1 >"$full_gateway_log" 2>&1 &
full_gateway_pid=$!

PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m groundfire_net.websocket_gateway \
    --host 127.0.0.1 \
    --port "$closed_gateway_port" \
    --closed >"$closed_gateway_log" 2>&1 &
closed_gateway_pid=$!

PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" -m groundfire_net.websocket_gateway \
    --host 127.0.0.1 \
    --port "$banned_gateway_port" \
    --ban-player GodotPlayer >"$banned_gateway_log" 2>&1 &
banned_gateway_pid=$!

for _attempt in $(seq 1 50); do
    if "$PYTHON_BIN" - <<PY >/dev/null 2>&1
from urllib.request import urlopen
urlopen("http://127.0.0.1:$port/index.html", timeout=0.2).read(64)
PY
    then
        break
    fi
    sleep 0.1
done

wait_for_tcp_port "QA password WebSocket gateway" "$gateway_port" "$gateway_log"
wait_for_tcp_port "QA auth WebSocket gateway" "$auth_gateway_port" "$auth_gateway_log"
wait_for_tcp_port "QA full WebSocket gateway" "$full_gateway_port" "$full_gateway_log"
wait_for_tcp_port "QA closed WebSocket gateway" "$closed_gateway_port" "$closed_gateway_log"
wait_for_tcp_port "QA banned WebSocket gateway" "$banned_gateway_port" "$banned_gateway_log"

"$PYTHON_BIN" - "$full_gateway_port" "$full_gateway_ready" >"$full_gateway_holder_log" 2>&1 <<'PY' &
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import time

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
port = int(sys.argv[1])
ready_path = sys.argv[2]


def recv_exact(sock, length):
    data = bytearray()
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise SystemExit("gateway closed mid-frame")
        data.extend(chunk)
    return bytes(data)


def read_frame(sock):
    header = recv_exact(sock, 2)
    first, second = header
    opcode = first & 0x0F
    if opcode == 0x8:
        raise SystemExit("gateway closed while waiting for holder join")
    if opcode != 0x1:
        raise SystemExit(f"unexpected websocket opcode: {opcode}")
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", recv_exact(sock, 8))[0]
    payload = recv_exact(sock, length)
    return json.loads(payload.decode("utf-8"))


def write_frame(sock, message):
    payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
    mask = b"\x01\x23\x45\x67"
    header = bytearray([0x81])
    if len(payload) < 126:
        header.append(0x80 | len(payload))
    elif len(payload) < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", len(payload)))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", len(payload)))
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    sock.sendall(bytes(header) + mask + masked)


sock = socket.create_connection(("127.0.0.1", port), timeout=5.0)
key = base64.b64encode(b"groundfire-qa-1").decode("ascii")
accept = base64.b64encode(hashlib.sha1((key + GUID).encode("ascii")).digest()).decode("ascii")
sock.sendall(
    (
        "GET /qa-full-holder HTTP/1.1\r\n"
        f"Host: 127.0.0.1:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    ).encode("ascii")
)
response = b""
while b"\r\n\r\n" not in response:
    response += sock.recv(4096)
if b"101 Switching Protocols" not in response or accept.encode("ascii") not in response:
    raise SystemExit(f"unexpected handshake response: {response!r}")

read_frame(sock)
write_frame(sock, {"type": "hello", "protocol": 1, "client": "browser-qa-holder"})
read_frame(sock)
write_frame(sock, {"type": "join", "protocol": 1, "player_name": "SlotHolder", "password": ""})
joined = read_frame(sock)
if joined.get("type") != "snapshot" or joined.get("state", {}).get("status") != "joined":
    raise SystemExit(f"unexpected holder join response: {joined!r}")
with open(ready_path, "w", encoding="utf-8") as handle:
    handle.write("ready\n")
while True:
    time.sleep(1.0)
PY
full_gateway_holder_pid=$!

for _attempt in $(seq 1 50); do
    if [[ -f "$full_gateway_ready" ]]; then
        break
    fi
    if ! kill -0 "$full_gateway_holder_pid" >/dev/null 2>&1; then
        printf 'QA full gateway holder exited before reserving a slot.\n' >&2
        cat "$full_gateway_holder_log" >&2 || true
        exit 1
    fi
    sleep 0.1
done
if [[ ! -f "$full_gateway_ready" ]]; then
    printf 'Timed out waiting for QA full gateway holder to reserve a slot.\n' >&2
    cat "$full_gateway_holder_log" >&2 || true
    exit 1
fi

capture() {
    local name="$1"
    local query="$2"
    local output="$actual_dir/$name.png"
    rm -f "$output"
    "$PYTHON_BIN" - "$BROWSER_BIN" "$user_data_dir-$name" "$output" "http://127.0.0.1:$port/index.html$query" <<'PY'
import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import websocket

browser, user_data_dir, output, url = sys.argv[1:5]
debug_port = 0

import socket

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    debug_port = sock.getsockname()[1]

process = subprocess.Popen(
    [
        browser,
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--enable-unsafe-swiftshader",
        f"--remote-debugging-port={debug_port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--window-size=1024,768",
        "about:blank",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

try:
    version_url = f"http://127.0.0.1:{debug_port}/json/version"
    deadline = time.monotonic() + 10.0
    while True:
        try:
            with urllib.request.urlopen(version_url, timeout=0.2) as response:
                json.load(response)
            break
        except Exception:
            if time.monotonic() > deadline:
                raise SystemExit("Timed out waiting for Chromium DevTools endpoint.")
            time.sleep(0.1)

    with urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json/list", timeout=1.0) as response:
        targets = json.load(response)
    page = next(target for target in targets if target.get("type") == "page")
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30)
    message_id = 0

    def command(method, params=None):
        nonlocal_id[0] += 1
        payload = {"id": nonlocal_id[0], "method": method}
        if params is not None:
            payload["params"] = params
        ws.send(json.dumps(payload))
        while True:
            message = json.loads(ws.recv())
            if message.get("id") == nonlocal_id[0]:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    nonlocal_id = [message_id]
    command("Page.enable")
    command("Runtime.enable")
    command("Emulation.setDeviceMetricsOverride", {
        "width": 1024,
        "height": 768,
        "deviceScaleFactor": 1,
        "mobile": False,
    })
    command("Page.navigate", {"url": url})

    deadline = time.monotonic() + 45.0
    last_state = ""
    while True:
        result = command("Runtime.evaluate", {
            "expression": "(() => { const notice = document.getElementById('status-notice');"
            " if (notice && notice.innerText.trim()) return 'notice:' + notice.innerText.trim();"
            " return document.getElementById('status') ? 'loading' : 'ready'; })()",
            "returnByValue": True,
        })
        last_state = str(result.get("result", {}).get("value", "unknown"))
        if last_state == "ready":
            break
        if last_state.startswith("notice:"):
            raise SystemExit(f"Godot web export failed in browser: {last_state}")
        if time.monotonic() > deadline:
            raise SystemExit(f"Timed out waiting for Godot canvas readiness: {last_state}")
        time.sleep(0.25)

    time.sleep(0.5)
    screenshot = command("Page.captureScreenshot", {"format": "png", "fromSurface": True})
    Path(output).write_bytes(base64.b64decode(screenshot["data"]))
    ws.close()
finally:
    try:
        process.terminate()
    except PermissionError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=5)
        except PermissionError:
            pass
    except PermissionError:
        pass
PY
    [[ -s "$output" ]]
}

capture main_menu ""
capture options "?screen=options"
capture server_browser "?screen=servers"
capture local_match "?screen=local"

browser_runtime_qa() {
    local phase="$1"
    "$PYTHON_BIN" - "$BROWSER_BIN" "$user_data_dir-runtime" "http://127.0.0.1:$port/index.html?qa=browser_runtime&store_phase=$phase&directory_url=http://127.0.0.1:$port/qa/server_directory.json&gateway_endpoint=ws://127.0.0.1:$gateway_port/qa-gateway&auth_gateway_endpoint=ws://127.0.0.1:$auth_gateway_port/qa-auth-gateway&full_gateway_endpoint=ws://127.0.0.1:$full_gateway_port/qa-full-gateway&closed_gateway_endpoint=ws://127.0.0.1:$closed_gateway_port/qa-closed-gateway&banned_gateway_endpoint=ws://127.0.0.1:$banned_gateway_port/qa-banned-gateway" <<'PY'
import json
import subprocess
import sys
import time
import urllib.request

import websocket

browser, user_data_dir, url = sys.argv[1:4]

import socket

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    debug_port = sock.getsockname()[1]

process = subprocess.Popen(
    [
        browser,
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--enable-unsafe-swiftshader",
        f"--remote-debugging-port={debug_port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--window-size=1024,768",
        "about:blank",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

try:
    version_url = f"http://127.0.0.1:{debug_port}/json/version"
    deadline = time.monotonic() + 10.0
    while True:
        try:
            with urllib.request.urlopen(version_url, timeout=0.2) as response:
                json.load(response)
            break
        except Exception:
            if time.monotonic() > deadline:
                raise SystemExit("Timed out waiting for Chromium DevTools endpoint.")
            time.sleep(0.1)

    with urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json/list", timeout=1.0) as response:
        targets = json.load(response)
    page = next(target for target in targets if target.get("type") == "page")
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30)
    message_id = 0
    nonlocal_id = [message_id]

    def command(method, params=None):
        nonlocal_id[0] += 1
        payload = {"id": nonlocal_id[0], "method": method}
        if params is not None:
            payload["params"] = params
        ws.send(json.dumps(payload))
        while True:
            message = json.loads(ws.recv())
            if message.get("id") == nonlocal_id[0]:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    command("Page.enable")
    command("Runtime.enable")
    command("Emulation.setDeviceMetricsOverride", {
        "width": 1024,
        "height": 768,
        "deviceScaleFactor": 1,
        "mobile": False,
    })
    command("Page.navigate", {"url": url})

    deadline = time.monotonic() + 45.0
    last_state = ""
    while True:
        result = command("Runtime.evaluate", {
            "expression": "(() => { const notice = document.getElementById('status-notice');"
            " if (notice && notice.innerText.trim()) return 'notice:' + notice.innerText.trim();"
            " return document.getElementById('status') ? 'loading' : 'ready'; })()",
            "returnByValue": True,
        })
        last_state = str(result.get("result", {}).get("value", "unknown"))
        if last_state == "ready":
            break
        if last_state.startswith("notice:"):
            raise SystemExit(f"Godot web export failed in browser: {last_state}")
        if time.monotonic() > deadline:
            raise SystemExit(f"Timed out waiting for Godot canvas readiness: {last_state}")
        time.sleep(0.25)

    deadline = time.monotonic() + 30.0
    qa_result = None
    while True:
        result = command("Runtime.evaluate", {
            "expression": "window.__groundfireQaResult || null",
            "returnByValue": True,
        })
        qa_result = result.get("result", {}).get("value")
        if qa_result:
            break
        if time.monotonic() > deadline:
            raise SystemExit("Timed out waiting for browser runtime QA result.")
        time.sleep(0.25)

    if not qa_result.get("ok"):
        raise SystemExit(f"Browser runtime QA failed: {qa_result.get('errors')}")
    print(f"Browser runtime QA passed: {qa_result.get('details', {})}")
    ws.close()
finally:
    try:
        process.terminate()
    except PermissionError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=5)
        except PermissionError:
            pass
    except PermissionError:
        pass
PY
}

browser_runtime_qa seed
browser_runtime_qa verify

GODOT_BROWSER_GOLDEN_UPDATE="$UPDATE_GOLDENS" "$PYTHON_BIN" - "$actual_dir" "$golden_dir" <<'PY'
import os
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageChops

actual_dir = Path(sys.argv[1])
golden_dir = Path(sys.argv[2])
update = os.environ.get("GODOT_BROWSER_GOLDEN_UPDATE") == "1"
cases = ("main_menu", "options", "server_browser", "local_match")
average_tolerance = 1.0
changed_ratio_tolerance = 0.02

for case in cases:
    actual_path = actual_dir / f"{case}.png"
    golden_path = golden_dir / f"{case}.png"
    if update or not golden_path.exists():
        shutil.copy2(actual_path, golden_path)
        continue
    actual = Image.open(actual_path).convert("RGBA")
    golden = Image.open(golden_path).convert("RGBA")
    if actual.size != golden.size:
        raise SystemExit(f"{case}: image size changed: {actual.size} != {golden.size}")
    diff = ImageChops.difference(actual, golden)
    histogram = diff.convert("L").histogram()
    pixels = actual.size[0] * actual.size[1]
    total = sum(value * count for value, count in enumerate(histogram))
    changed = sum(count for value, count in enumerate(histogram) if value > 12)
    average = total / max(1, pixels)
    changed_ratio = changed / max(1, pixels)
    if average > average_tolerance or changed_ratio > changed_ratio_tolerance:
        raise SystemExit(
            f"{case}: visual diff too large: average={average:.3f}, changed_ratio={changed_ratio:.4f}"
        )

print(f"Browser visual QA passed for {len(cases)} screenshots.")
PY
