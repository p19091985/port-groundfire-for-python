import re
import sys

with open("groundfire_net/websocket_gateway.py", "r") as f:
    content = f.read()

# 1. Remove GatewaySimulation
content = re.sub(r"@dataclass\nclass GatewaySimulation:.*?def snapshot.*?return {.*?}\n", "", content, flags=re.DOTALL)

# 2. Update WebSocketGatewaySession to remove GatewaySimulation and add proxy state
session_replacement = """
@dataclass
class WebSocketGatewaySession:
    required_password: str = ""
    required_auth_token: str = ""
    session_secret: str = ""
    join_registry: GatewayJoinRegistry = field(default_factory=GatewayJoinRegistry)
    joins_closed: bool = False
    banned_players: frozenset[str] = field(default_factory=frozenset)
    _joined: bool = False
    _player_number: int = 0
    player_name: str = "Guest"
    last_input: dict = field(default_factory=dict)
    last_input_sequence: int = 0
"""
content = re.sub(r"@dataclass\nclass WebSocketGatewaySession:.*?_player_number: int = 0\n", session_replacement, content, flags=re.DOTALL)

# 3. Modify `_handle_client` in `WebSocketGateway`
handle_client_replacement = """
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        session = WebSocketGatewaySession(
            required_password=self.password,
            required_auth_token=self.auth_token,
            session_secret=self.session_secret,
            join_registry=self.join_registry,
            joins_closed=self.closed,
            banned_players=self.banned_players,
        )
        ws_queue = asyncio.Queue()

        class UdpProxyProtocol(asyncio.DatagramProtocol):
            def connection_made(self, transport):
                pass
            def datagram_received(self, data, addr):
                from src.groundfire.network.codec import decode_message
                try:
                    msg = decode_message(data)
                    ws_queue.put_nowait(msg)
                except Exception:
                    pass
            def error_received(self, exc):
                pass
            def connection_lost(self, exc):
                pass

        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: UdpProxyProtocol(),
            remote_addr=(self.udp_host, self.udp_port)
        )

        async def udp_to_ws_loop():
            from src.groundfire.network.messages import ServerSnapshotEnvelope, JoinAccept, JoinReject
            from groundfire_net.codec import to_plain
            while True:
                msg = await ws_queue.get()
                if isinstance(msg, ServerSnapshotEnvelope):
                    response = {
                        "type": "snapshot",
                        "protocol": PROTOCOL_VERSION,
                        "sequence": session.last_input_sequence,
                        "state": {
                            "status": "joined",
                            "player_name": session.player_name,
                            "player_number": session._player_number,
                            "joined": True,
                            "last_input": session.last_input,
                            "server_time_msec": int(time.time() * 1000),
                            "match_snapshot_schema": MATCH_SNAPSHOT_SCHEMA_VERSION,
                            "event_schema": EVENT_SCHEMA_VERSION,
                            "match_snapshot": to_plain(msg.snapshot),
                            "terrain_patches": [to_plain(patch) for patch in msg.terrain_patches],
                            "events": [_version_event(event) for event in msg.events],
                        }
                    }
                    response["state"].update(session.join_registry.metadata())
                    await _write_text(writer, json.dumps(response, separators=(",", ":")))
                elif isinstance(msg, JoinAccept):
                    session._joined = True
                    session._player_number = msg.player_number
                elif isinstance(msg, JoinReject):
                    await _write_text(writer, json.dumps(_error(msg.reason), separators=(",", ":")))
                    writer.close()

        udp_task = asyncio.create_task(udp_to_ws_loop())

        try:
            await _accept_handshake(reader, writer)
            
            from src.groundfire.network.messages import HelloRequest, JoinRequest, ClientCommandEnvelope
            from src.groundfire.network.codec import encode_message
            
            while not reader.at_eof():
                payload = await _read_frame(reader)
                if payload is None:
                    break
                
                try:
                    message = json.loads(payload)
                except json.JSONDecodeError:
                    await _write_text(writer, json.dumps(_error("invalid_json"), separators=(",", ":")))
                    continue
                    
                message_type = str(message.get("type", ""))
                
                if message_type == "hello":
                    # Send hello to UDP server just to wake it up or log it, but proxy returns standard JSON immediately
                    transport.sendto(encode_message(HelloRequest(player_name="WebGuest")))
                    response = {
                        "type": "hello",
                        "protocol": PROTOCOL_VERSION,
                        "min_protocol": MIN_PROTOCOL_VERSION,
                        "max_protocol": MAX_PROTOCOL_VERSION,
                        "supported_protocols": list(SUPPORTED_PROTOCOL_VERSIONS),
                        "match_snapshot_schema": MATCH_SNAPSHOT_SCHEMA_VERSION,
                        "event_schema": EVENT_SCHEMA_VERSION,
                        "password_required": bool(session.required_password),
                        "auth_required": bool(session.required_auth_token or session.session_secret),
                        "auth_token_mode": _auth_token_mode(session.required_auth_token, session.session_secret),
                        "joins_open": not session.joins_closed,
                        "ban_enforced": bool(session.banned_players),
                        **session.join_registry.metadata(),
                        "server": "python-websocket-proxy",
                    }
                    await _write_text(writer, json.dumps(response, separators=(",", ":")))
                
                elif message_type == "join":
                    if session.joins_closed:
                        await _write_text(writer, json.dumps(_error("server_closed"), separators=(",", ":")))
                        continue
                    
                    player_name = str(message.get("player_name", "Guest"))
                    if _normalized_player_name(player_name) in session.banned_players:
                        await _write_text(writer, json.dumps(_error("banned"), separators=(",", ":")))
                        continue
                    
                    if not _auth_token_is_authorized(
                        str(message.get("auth_token", "")),
                        required_auth_token=session.required_auth_token,
                        session_secret=session.session_secret,
                        player_name=player_name,
                    ):
                        await _write_text(writer, json.dumps(_error("authentication_failed"), separators=(",", ":")))
                        continue
                        
                    if session.required_password and str(message.get("password", "")) != session.required_password:
                        await _write_text(writer, json.dumps(_error("invalid_password"), separators=(",", ":")))
                        continue
                    
                    session.player_name = player_name
                    transport.sendto(encode_message(JoinRequest(player_name=player_name)))
                
                elif message_type == "input":
                    if not session._joined:
                        await _write_text(writer, json.dumps(_error("not_joined"), separators=(",", ":")))
                        continue
                        
                    sequence = int(message.get("sequence", session.last_input_sequence + 1))
                    command = message.get("command", {})
                    if isinstance(command, dict):
                        session.last_input_sequence = sequence
                        session.last_input = command
                        env = ClientCommandEnvelope(
                            session_id="web",
                            player_number=session._player_number,
                            client_sequence=sequence,
                            simulation_tick=0,
                            issued_at=time.time(),
                            source="websocket",
                            commands={k: bool(v) for k, v in command.items() if k in INPUT_COMMAND_FIELDS},
                            protocol_version=PROTOCOL_VERSION,
                        )
                        transport.sendto(encode_message(env))
                
                elif message_type == "ping":
                    response = {
                        "type": "pong",
                        "protocol": PROTOCOL_VERSION,
                        "sequence": int(message.get("sequence", 0)),
                        "client_time_msec": int(message.get("client_time_msec", 0)),
                        "server_time_msec": int(time.time() * 1000),
                    }
                    await _write_text(writer, json.dumps(response, separators=(",", ":")))
                    
                elif message_type == "disconnect":
                    break
        finally:
            udp_task.cancel()
            transport.close()
            session.close()
            writer.close()
            await writer.wait_closed()
"""

# Find `_handle_client` definition and replace it
content = re.sub(r"    async def _handle_client\(self, reader: asyncio\.StreamReader, writer: asyncio\.StreamWriter\) -> None:.*?            await writer\.wait_closed\(\)\n", handle_client_replacement, content, flags=re.DOTALL)

with open("groundfire_net/websocket_gateway.py", "w") as f:
    f.write(content)
