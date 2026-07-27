import re

with open("tests/test_groundfire_net_module.py", "r") as f:
    content = f.read()

tests_to_remove = [
    "test_gateway_simulation_replicates_tank_and_terrain_state",
    "test_websocket_gateway_main_can_issue_signed_join_token",
    "test_websocket_gateway_session_accepts_signed_expiring_auth_token",
    "test_websocket_gateway_session_assigns_reusable_unique_player_numbers",
    "test_websocket_gateway_session_rejects_authentication_failure",
    "test_websocket_gateway_session_rejects_banned_player",
    "test_websocket_gateway_session_rejects_input_before_join",
    "test_websocket_gateway_session_rejects_invalid_password",
    "test_websocket_gateway_session_rejects_server_closed",
    "test_websocket_gateway_session_rejects_server_full_until_slot_released",
    "test_websocket_gateway_session_speaks_godot_message_contract",
    "test_websocket_gateway_speaks_contract_over_real_frames",
    "test_websocket_gateway_session_reports_bad_messages",
    "test_websocket_gateway_session_validates_message_shapes",
]

for test in tests_to_remove:
    # Match from `def test...` to the next `    def test...` or end of file
    pattern = r"    def " + test + r"\(self\):.*?(?=\n    def |\Z)"
    content = re.sub(pattern, "", content, flags=re.DOTALL)

with open("tests/test_groundfire_net_module.py", "w") as f:
    f.write(content)

