extends Control

signal back_requested
signal servers_requested
signal match_ready(connection: Dictionary)

const GroundfireTheme := preload("res://scripts/groundfire_theme.gd")
const ServiceClient := preload("res://scripts/online/service_client.gd")

var _service: Node
var _status: Label
var _identity: Label
var _create_panel: VBoxContainer
var _join_panel: HBoxContainer
var _name: LineEdit
var _code: LineEdit
var _password: LineEdit
var _capacity: SpinBox
var _rounds: SpinBox
var _map: OptionButton
var _bots: SpinBox
var _lobby_panel: VBoxContainer
var _lobby_info: Label
var _pending_action := ""
var _session_user: Dictionary = {}
var _current_lobby: Dictionary = {}


func _ready() -> void:
	_service = ServiceClient.new()
	add_child(_service)
	_service.request_succeeded.connect(_on_service_success)
	_service.request_failed.connect(_on_service_failure)
	_build()


func _build() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var background := ColorRect.new()
	background.color = GroundfireTheme.COLOR_BG
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["margin_left", "margin_top", "margin_right", "margin_bottom"]:
		margin.add_theme_constant_override(side, 28)
	add_child(margin)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 12)
	margin.add_child(stack)
	var title := Label.new()
	title.text = "Jogar on-line"
	GroundfireTheme.apply_label(title, 32, GroundfireTheme.COLOR_WARN, true)
	stack.add_child(title)
	_identity = Label.new()
	_identity.text = "Sessão: desconectada"
	GroundfireTheme.apply_label(_identity, 18, GroundfireTheme.COLOR_TEXT)
	stack.add_child(_identity)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	stack.add_child(actions)
	_add_button(actions, "Servidores", func(): servers_requested.emit())
	_add_button(actions, "Jogar agora", _quick_match)
	_add_button(actions, "Criar sala", _toggle_create)
	_add_button(actions, "Entrar por código", _toggle_join)
	_add_button(actions, "Voltar", func(): back_requested.emit())
	_create_panel = VBoxContainer.new()
	_create_panel.visible = false
	stack.add_child(_create_panel)
	_name = _line(_create_panel, "Nome da sala", "Sala Groundfire")
	var values := HBoxContainer.new()
	_create_panel.add_child(values)
	_capacity = _spin(values, "Vagas", 2, 8, 8)
	_rounds = _spin(values, "Rodadas", 5, 50, 10)
	_bots = _spin(values, "Bots", 0, 7, 1)
	_map = OptionButton.new()
	for map_id in ["classic", "basin", "ridge", "crater", "mesa"]:
		_map.add_item(map_id)
	values.add_child(_map)
	_password = _line(_create_panel, "Senha opcional", "")
	_password.secret = true
	_add_button(_create_panel, "Criar", _create_lobby)
	_join_panel = HBoxContainer.new()
	_join_panel.visible = false
	stack.add_child(_join_panel)
	_code = LineEdit.new()
	_code.placeholder_text = "Código do convite"
	_code.custom_minimum_size.x = 280
	_join_panel.add_child(_code)
	_add_button(_join_panel, "Entrar", _accept_invite)
	_lobby_panel = VBoxContainer.new()
	_lobby_panel.visible = false
	stack.add_child(_lobby_panel)
	_lobby_info = Label.new()
	_lobby_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_lobby_panel.add_child(_lobby_info)
	var lobby_actions := HBoxContainer.new()
	_lobby_panel.add_child(lobby_actions)
	_add_button(lobby_actions, "Gerar código", _create_invite)
	_add_button(lobby_actions, "Pronto", _set_ready)
	_add_button(lobby_actions, "Iniciar", _start_lobby)
	_status = Label.new()
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	GroundfireTheme.apply_label(_status, 18, GroundfireTheme.COLOR_TEXT)
	stack.add_child(_status)
	_status.text = "Escolha uma ação. O modo LAN continua disponível em Servidores."


func _add_button(parent: Container, text: String, action: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.focus_mode = Control.FOCUS_ALL
	GroundfireTheme.apply_button(button)
	button.pressed.connect(action)
	parent.add_child(button)
	return button


func _line(parent: Container, placeholder: String, value: String) -> LineEdit:
	var line := LineEdit.new()
	line.placeholder_text = placeholder
	line.text = value
	line.max_length = 32
	parent.add_child(line)
	return line


func _spin(parent: Container, label_text: String, minimum: float, maximum: float, value: float) -> SpinBox:
	var column := VBoxContainer.new()
	parent.add_child(column)
	var label := Label.new()
	label.text = label_text
	column.add_child(label)
	var spin := SpinBox.new()
	spin.min_value = minimum
	spin.max_value = maximum
	spin.value = value
	column.add_child(spin)
	return spin


func _ensure_guest(next_action: String) -> bool:
	if not _service.access_token.is_empty():
		return true
	_pending_action = next_action
	_status.text = "Criando sessão de convidado..."
	_service.guest("GodotPlayer")
	return false


func _toggle_create() -> void:
	_create_panel.visible = not _create_panel.visible
	_join_panel.visible = false


func _toggle_join() -> void:
	_join_panel.visible = not _join_panel.visible
	_create_panel.visible = false


func _create_lobby() -> void:
	if not _ensure_guest("create_lobby"):
		return
	_status.text = "Criando sala..."
	_service.create_lobby({
		"name": _name.text.strip_edges(),
		"visibility": "private" if not _password.text.is_empty() else "public",
		"password": _password.text,
		"capacity": int(_capacity.value),
		"rounds": int(_rounds.value),
		"map_id": _map.get_item_text(_map.selected),
		"seed": 1,
		"bots": int(_bots.value),
	})


func _show_lobby(lobby: Dictionary) -> void:
	_current_lobby = lobby.duplicate(true)
	_lobby_panel.visible = true
	_lobby_info.text = "Sala: %s | %s | %s rodadas | revisão %s" % [
		str(_current_lobby.get("name", "Groundfire")),
		str(_current_lobby.get("map_id", "classic")),
		str(_current_lobby.get("rounds", 10)),
		str(_current_lobby.get("revision", 0)),
	]


func _create_invite() -> void:
	if _current_lobby.is_empty():
		_status.text = "Crie ou entre em uma sala primeiro."
		return
	_status.text = "Gerando código de convite..."
	_service.create_invite("lobby", str(_current_lobby.get("lobby_id", "")))


func _set_ready() -> void:
	if _current_lobby.is_empty():
		_status.text = "Crie ou entre em uma sala primeiro."
		return
	_status.text = "Confirmando pronto..."
	_service.set_lobby_ready(str(_current_lobby.get("lobby_id", "")), int(_current_lobby.get("revision", -1)), true)


func _start_lobby() -> void:
	if _current_lobby.is_empty():
		_status.text = "Crie uma sala primeiro."
		return
	_status.text = "Alocando servidor da partida..."
	_service.start_lobby(str(_current_lobby.get("lobby_id", "")), int(_current_lobby.get("revision", -1)))


func _accept_invite() -> void:
	if _code.text.strip_edges().is_empty():
		_status.text = "Informe o código do convite."
		return
	if not _ensure_guest("accept_invite"):
		return
	_status.text = "Validando convite..."
	_service.accept_invite(_code.text.strip_edges(), _password.text)


func _quick_match() -> void:
	if not _ensure_guest("quick_match"):
		return
	_status.text = "Procurando uma sala compatível..."
	_service.queue_match({})


func _on_service_success(operation: String, data: Variant, _request_id: String) -> void:
	if operation == "guest":
		_session_user = Dictionary(data).get("user", {})
		_identity.text = "Sessão: %s (convidado)" % str(_session_user.get("display_name", "GodotPlayer"))
		var action := _pending_action
		_pending_action = ""
		if action == "create_lobby": _create_lobby()
		elif action == "accept_invite": _accept_invite()
		elif action == "quick_match": _quick_match()
		return
	if operation == "create_lobby":
		var lobby: Dictionary = data
		_show_lobby(lobby)
		_status.text = "Sala criada. Gere um código, confirme pronto e inicie quando todos estiverem prontos."
		_service.create_invite("lobby", str(lobby.get("lobby_id", "")))
	elif operation == "create_invite":
		var invite: Dictionary = data
		_code.text = str(invite.get("code", ""))
		_status.text = "Código de convite: %s (expira automaticamente)." % _code.text
	elif operation == "accept_invite":
		var accepted: Dictionary = data
		var target: Dictionary = accepted.get("target", {})
		_show_lobby(target)
		_status.text = "Convite aceito. Confirme que está pronto."
	elif operation == "lobby_ready":
		_show_lobby(data)
		_status.text = "Pronto confirmado. O líder pode iniciar."
	elif operation == "start_lobby":
		var match_data: Dictionary = data
		_status.text = "Servidor pronto; emitindo ingresso individual..."
		_service.admission_ticket(str(match_data.get("reservation_id", "")), "ws")
	elif operation == "queue_match":
		var queue: Dictionary = data
		if str(queue.get("state", "")) == "reserved":
			_status.text = "Vagas reservadas; confirmando ingresso..."
			_service.accept_reservation(str(queue.get("reservation_id", "")))
		else:
			_status.text = "Busca ativa. Você pode voltar sem perder a sessão."
	elif operation == "accept_reservation":
		var reservation: Dictionary = data
		if reservation.get("match") is Dictionary:
			_service.admission_ticket(str(reservation.get("reservation_id", "")), "ws")
		else:
			_status.text = "Aguardando os demais membros do grupo."
	elif operation == "admission_ticket":
		var connection: Dictionary = Dictionary(data).duplicate(true)
		connection["auth_token"] = str(connection.get("admission_ticket", ""))
		_status.text = "Ingresso autorizado. Conectando..."
		match_ready.emit(connection)


func _on_service_failure(_operation: String, code: String, message: String, retryable: bool) -> void:
	_status.text = "%s%s" % [message, " Tente novamente." if retryable else ""]
	_status.tooltip_text = code
