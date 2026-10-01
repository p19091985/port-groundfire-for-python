extends SceneTree

const UdpClient := preload("res://scripts/udp_client.gd")
var client: Node
var elapsed := 0.0

func _init() -> void:
	client = UdpClient.new()
	client.message_received.connect(_on_message)
	root.add_child(client)
	assert(client.connect_to_endpoint(OS.get_environment("GROUNDFIRE_TEST_UDP_ENDPOINT")) == OK)

func _process(delta: float) -> bool:
	elapsed += delta
	if elapsed >= 8:
		push_error("Python server did not confirm the AI participant")
		quit(1)
	return false

func _on_message(message: Dictionary) -> void:
	if str(message.get("type","")) == "hello":
		client.join("Godot AI", "", "", false, true)
	elif str(message.get("type","")) == "snapshot":
		var state: Dictionary = message.get("state",{})
		var number := int(state.get("player_number",-1))
		for player in state.get("match_snapshot",{}).get("players",[]):
			if int(player.get("player_number",-2)) == number:
				assert(bool(player.get("is_computer",false)), "AI selection must reach the real Python server")
				client.disconnect_from_endpoint("ai_integration_complete")
				print("Godot/Python AI join confirmed")
				quit(0)
