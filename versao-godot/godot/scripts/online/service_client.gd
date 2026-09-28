extends Node
class_name GroundfireServiceClient

signal request_succeeded(operation: String, data: Variant, request_id: String)
signal request_failed(operation: String, code: String, message: String, retryable: bool)

const DEFAULT_URL := "http://127.0.0.1:27880"
const MAX_RESPONSE_BYTES := 65536

var base_url := DEFAULT_URL
var access_token := ""
var refresh_token := ""
var _http: HTTPRequest
var _active_operation := ""
var _generation := 0
var _active_generation := 0


func _ready() -> void:
	base_url = str(ProjectSettings.get_setting("application/config/service_base_url", DEFAULT_URL)).trim_suffix("/")
	_http = HTTPRequest.new()
	_http.timeout = 8.0
	_http.download_chunk_size = 16384
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)


func request_json(operation: String, method: HTTPClient.Method, path: String, payload := {}, authenticated := true) -> int:
	_generation += 1
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		_http.cancel_request()
	_active_operation = operation
	_active_generation = _generation
	var headers := PackedStringArray(["Accept: application/json"])
	var body := ""
	if method != HTTPClient.METHOD_GET and method != HTTPClient.METHOD_DELETE:
		headers.append("Content-Type: application/json")
		body = JSON.stringify(payload)
	if authenticated and not access_token.is_empty():
		headers.append("Authorization: Bearer %s" % access_token)
	var result := _http.request(base_url + path, headers, method, body)
	if result != OK:
		request_failed.emit(operation, "service_unavailable", error_string(result), true)
	return _generation


func cancel_active() -> void:
	_generation += 1
	_http.cancel_request()
	_active_operation = ""


func register_account(handle: String, display_name: String, password: String) -> int:
	return request_json("register", HTTPClient.METHOD_POST, "/api/v1/auth/register", {"handle": handle, "display_name": display_name, "password": password}, false)


func login(handle: String, password: String) -> int:
	return request_json("login", HTTPClient.METHOD_POST, "/api/v1/auth/login", {"handle": handle, "password": password}, false)


func guest(display_name: String) -> int:
	return request_json("guest", HTTPClient.METHOD_POST, "/api/v1/auth/guest", {"display_name": display_name}, false)


func create_lobby(rules: Dictionary) -> int:
	return request_json("create_lobby", HTTPClient.METHOD_POST, "/api/v1/lobbies", rules)


func set_lobby_ready(lobby_id: String, revision: int, ready := true) -> int:
	return request_json("lobby_ready", HTTPClient.METHOD_PUT, "/api/v1/lobbies/%s/members/me/ready" % lobby_id.uri_encode(), {"revision": revision, "ready": ready})


func start_lobby(lobby_id: String, revision: int) -> int:
	return request_json("start_lobby", HTTPClient.METHOD_POST, "/api/v1/lobbies/%s/start" % lobby_id.uri_encode(), {"revision": revision})


func create_invite(target_type: String, target_id: String) -> int:
	return request_json("create_invite", HTTPClient.METHOD_POST, "/api/v1/invites", {"target_type": target_type, "target_id": target_id})


func accept_invite(code: String, password := "") -> int:
	return request_json("accept_invite", HTTPClient.METHOD_POST, "/api/v1/invites/accept", {"code": code, "password": password})


func queue_match(criteria := {}, party_id := "", party_revision := -1) -> int:
	var payload := {"criteria": criteria}
	if not party_id.is_empty():
		payload["party_id"] = party_id
		payload["party_revision"] = party_revision
	return request_json("queue_match", HTTPClient.METHOD_POST, "/api/v1/matchmaking/queue", payload)


func cancel_queue(queue_id: String) -> int:
	return request_json("cancel_queue", HTTPClient.METHOD_DELETE, "/api/v1/matchmaking/queue/%s" % queue_id.uri_encode())


func accept_reservation(reservation_id: String) -> int:
	return request_json("accept_reservation", HTTPClient.METHOD_POST, "/api/v1/reservations/%s/accept" % reservation_id.uri_encode(), {})


func admission_ticket(reservation_id: String, transport := "wss") -> int:
	return request_json("admission_ticket", HTTPClient.METHOD_POST, "/api/v1/reservations/%s/admission-tickets" % reservation_id.uri_encode(), {"transport": transport})


func send_chat(channel_type: String, channel_id: String, text: String, client_message_id: String) -> int:
	return request_json("send_chat", HTTPClient.METHOD_POST, "/api/v1/channels/%s/%s/messages" % [channel_type.uri_encode(), channel_id.uri_encode()], {"text": text, "client_message_id": client_message_id})


func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var completed_generation := _active_generation
	var operation := _active_operation
	_active_operation = ""
	if completed_generation != _generation:
		return
	if result != HTTPRequest.RESULT_SUCCESS:
		request_failed.emit(operation, "service_unavailable", "O serviço não respondeu.", true)
		return
	if body.size() > MAX_RESPONSE_BYTES:
		request_failed.emit(operation, "response_too_large", "A resposta excedeu o limite.", false)
		return
	var decoded = JSON.parse_string(body.get_string_from_utf8())
	if not decoded is Dictionary:
		request_failed.emit(operation, "invalid_response", "O serviço retornou JSON inválido.", false)
		return
	var response: Dictionary = decoded
	if response_code < 200 or response_code >= 300:
		var error: Dictionary = response.get("error", {})
		request_failed.emit(operation, str(error.get("code", "http_error")), str(error.get("message", "Erro do serviço.")), bool(error.get("retryable", false)))
		return
	var data = response.get("data")
	if operation in ["register", "login", "guest"] and data is Dictionary:
		access_token = str(data.get("access_token", ""))
		refresh_token = str(data.get("refresh_token", ""))
	request_succeeded.emit(operation, data, str(response.get("request_id", "")))
