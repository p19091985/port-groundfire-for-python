"use strict";

const $ = (id) => document.getElementById(id);
const state = { token: sessionStorage.getItem("gf-console-key") || "", snapshot: null, view: "overview", busy: false };
const pages = { overview: "Visão geral", lobbies: "Salas", matches: "Partidas", activity: "Atividade", settings: "Operações" };
const eventNames = {
  "lobby.created": "Sala criada", "lobby.changed": "Sala atualizada", "lobby.started": "Partida iniciada",
  "match.started": "Partida iniciada", "match.failed": "Partida falhou", "match.ended": "Partida encerrada",
  "friend_request.created": "Pedido de amizade", "friendship.changed": "Amizade atualizada",
  "presence.changed": "Presença atualizada", "party.changed": "Grupo atualizado",
  "reservation.created": "Reserva criada", "reservation.changed": "Reserva atualizada",
  "queue.changed": "Fila atualizada", "chat.message": "Mensagem recebida"
};

function el(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = String(value);
  return node;
}
function append(parent, ...children) { children.forEach((child) => parent.append(child)); return parent; }
function shortId(value) { return value ? String(value).slice(0, 13) + "…" : "—"; }
function timeLabel(value) { return value ? new Date(value * 1000).toLocaleString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }) : "—"; }
function pill(value) {
  const words = { open: "Aberta", active: "Ativa", finished: "Finalizada", failed: "Falhou", private: "Privada", public: "Pública", starting: "Iniciando", stopped: "Encerrada" };
  const style = ["open", "active", "public"].includes(value) ? "pill-live" : ["failed", "starting"].includes(value) ? "pill-warning" : "pill-muted";
  return el("span", `pill ${style}`, words[value] || value || "—");
}
function tableCell(row, content) { const cell = el("td"); cell.append(content instanceof Node ? content : document.createTextNode(String(content))); row.append(cell); }
function emptyTable(tbody, columns, message) { const row = el("tr"); const cell = el("td", "empty-state", message); cell.colSpan = columns; row.append(cell); tbody.append(row); }
function bar(id, value, maximum) { $(id).style.width = `${Math.max(0, Math.min(100, maximum ? value / maximum * 100 : 0))}%`; }

function renderLobbies(items, compact = false) {
  const tbody = $(compact ? "overview-lobbies" : "lobbies-table");
  tbody.replaceChildren();
  const query = compact ? "" : $("lobby-search").value.trim().toLocaleLowerCase("pt-BR");
  const filtered = items.filter((item) => `${item.name} ${item.map_id}`.toLocaleLowerCase("pt-BR").includes(query));
  if (!compact) $("lobbies-result").textContent = `${filtered.length} resultado${filtered.length === 1 ? "" : "s"}`;
  const visible = compact ? filtered.slice(0, 4) : filtered;
  if (!visible.length) { emptyTable(tbody, compact ? 3 : 6, "Nenhuma sala encontrada."); return; }
  visible.forEach((item) => {
    const row = el("tr");
    const name = el("span", "room-name"); append(name, el("span", "room-icon", "◆"), el("span", "", item.name)); tableCell(row, name);
    if (!compact) { tableCell(row, pill(item.visibility)); tableCell(row, item.map_id); }
    tableCell(row, `${item.players} / ${item.capacity}`);
    if (!compact) tableCell(row, item.rounds);
    tableCell(row, pill(item.state)); tbody.append(row);
  });
}
function renderMatches(items) {
  const tbody = $("matches-table"); tbody.replaceChildren();
  const query = $("match-search").value.trim().toLocaleLowerCase("pt-BR");
  const filtered = items.filter((item) => `${item.name} ${item.match_id}`.toLocaleLowerCase("pt-BR").includes(query));
  $("matches-result").textContent = `${filtered.length} resultado${filtered.length === 1 ? "" : "s"}`;
  if (!filtered.length) { emptyTable(tbody, 5, "Nenhuma partida encontrada."); return; }
  filtered.forEach((item) => {
    const row = el("tr"); tableCell(row, item.name); tableCell(row, shortId(item.match_id));
    tableCell(row, timeLabel(item.started_at || item.created_at)); tableCell(row, item.udp_port || "—");
    tableCell(row, pill(item.state)); tbody.append(row);
  });
}
function renderActivity(items, compact = false) {
  const target = $(compact ? "overview-activity" : "activity-list"); target.replaceChildren();
  const visible = compact ? items.slice(0, 4) : items;
  if (!visible.length) { target.append(el("div", "activity-empty", "Ainda não há eventos registrados.")); return; }
  visible.forEach((item) => {
    const row = el("div", "activity-item"); const copy = el("div", "activity-text");
    append(copy, el("strong", "", eventNames[item.event_type] || item.event_type.replaceAll(".", " · ")), el("small", "", item.resource_id || "Evento do serviço"));
    append(row, el("div", "activity-icon", "✦"), copy, el("span", "activity-time", timeLabel(item.created_at))); target.append(row);
  });
}
function render(data) {
  state.snapshot = data; const m = data.metrics;
  $("metric-online").textContent = m.online; $("metric-lobbies").textContent = m.lobbies;
  $("metric-matches").textContent = m.matches; $("metric-queued").textContent = m.queued;
  $("nav-lobbies").textContent = m.lobbies; $("nav-matches").textContent = m.matches;
  $("online-note").textContent = `${m.users} usuário${m.users === 1 ? "" : "s"} no total`;
  $("worker-note").textContent = `Workers: ${m.workers} / ${data.worker_limit}`;
  bar("online-bar", m.online, Math.max(m.users, 1)); bar("lobbies-bar", m.lobbies, Math.max(m.lobbies, 8));
  bar("matches-bar", m.workers, data.worker_limit); bar("queued-bar", m.queued, Math.max(m.queued, 8));
  $("lobbies-total").textContent = String(data.lobbies.length).padStart(2, "0");
  $("matches-total").textContent = String(data.matches.length).padStart(2, "0");
  $("detail-endpoint").textContent = data.endpoint; $("detail-database").textContent = data.database;
  $("detail-users").textContent = m.users; $("detail-workers").textContent = `${m.workers} / ${data.worker_limit}`;
  $("detail-updated").textContent = timeLabel(data.timestamp);
  $("last-update").textContent = `Atualizado às ${new Date(data.timestamp * 1000).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`;
  renderLobbies(data.lobbies, true); renderLobbies(data.lobbies); renderMatches(data.matches);
  renderActivity(data.activity, true); renderActivity(data.activity);
}
function connection(value) {
  $("connection-label").textContent = value; $("sidebar-status").textContent = value === "Conectado" ? "Servidor online" : value;
  document.querySelectorAll(".live-indicator > span:first-child,.status-pulse").forEach((node) => { node.style.background = value === "Conectado" ? "#70d49d" : "#ed8f71"; });
}
function showAuth(message = "") { $("auth-backdrop").hidden = false; $("auth-error").textContent = message; connection("Acesso necessário"); }
function hideAuth() { $("auth-backdrop").hidden = true; $("auth-token").value = ""; $("auth-error").textContent = ""; }
async function request(path, options = {}) {
  const response = await fetch(path, { ...options, cache: "no-store", headers: { "X-Groundfire-Control": state.token, ...(options.headers || {}) } });
  if (response.status === 401) { sessionStorage.removeItem("gf-console-key"); state.token = ""; showAuth("Chave inválida ou instância reiniciada."); throw new Error("Autenticação necessária"); }
  if (!response.ok) throw new Error(`Falha HTTP ${response.status}`);
  return response.json();
}
async function refresh() {
  if (!state.token || state.busy) return;
  state.busy = true;
  try { render(await request("/console/api/snapshot")); connection("Conectado"); hideAuth(); }
  catch (error) { if (state.token) connection("Sem conexão"); }
  finally { state.busy = false; }
}
function navigate(view) {
  if (!pages[view]) return;
  state.view = view; document.querySelectorAll(".page-view").forEach((node) => node.classList.toggle("hidden", node.id !== `view-${view}`));
  document.querySelectorAll(".nav-item[data-view]").forEach((node) => node.classList.toggle("active", node.dataset.view === view));
  $("page-name").textContent = pages[view]; window.scrollTo({ top: 0, behavior: "smooth" });
}
let toastTimer;
function toast(message) { const node = $("toast"); node.textContent = message; node.classList.add("show"); clearTimeout(toastTimer); toastTimer = setTimeout(() => node.classList.remove("show"), 5000); }

document.querySelectorAll("[data-view]").forEach((node) => node.addEventListener("click", () => navigate(node.dataset.view)));
$("lobby-search").addEventListener("input", () => state.snapshot && renderLobbies(state.snapshot.lobbies));
$("match-search").addEventListener("input", () => state.snapshot && renderMatches(state.snapshot.matches));
$("refresh-button").addEventListener("click", refresh); $("refresh-secondary").addEventListener("click", refresh);
$("auth-form").addEventListener("submit", (event) => { event.preventDefault(); state.token = $("auth-token").value.trim(); if (!state.token) return; sessionStorage.setItem("gf-console-key", state.token); refresh(); });
$("backup-button").addEventListener("click", async () => {
  const button = $("backup-button"); button.disabled = true; button.textContent = "Criando…";
  try { const result = await request("/console/api/backup", { method: "POST" }); toast(`Backup criado: ${result.file}`); }
  catch (error) { toast(`Não foi possível criar o backup: ${error.message}`); }
  finally { button.disabled = false; button.textContent = "Criar"; }
});
$("stop-button").addEventListener("click", () => $("stop-dialog").showModal());
$("cancel-stop").addEventListener("click", () => $("stop-dialog").close());
$("confirm-stop").addEventListener("click", async () => {
  try { await request("/console/api/stop", { method: "POST" }); $("stop-dialog").close(); connection("Encerrando"); toast("Servidor encerrando. Para iniciar novamente, execute o launcher."); }
  catch (error) { toast(`Falha ao parar: ${error.message}`); }
});

const fragment = new URLSearchParams(location.hash.slice(1));
if (fragment.has("key")) { state.token = fragment.get("key") || ""; sessionStorage.setItem("gf-console-key", state.token); history.replaceState(null, "", location.pathname); }
if (state.token) refresh(); else showAuth();
setInterval(refresh, 5000);
