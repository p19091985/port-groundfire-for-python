# Groundfire Godot WebSocket Protocol

This document records the first browser-safe protocol contract between the Godot client and the Python `groundfire-web-gateway`.

## Versioning

- Current protocol: `1`.
- Supported protocol range: `1..1`.
- Every JSON message must include integer field `protocol`.
- The gateway rejects missing protocol values with `missing_protocol`.
- The gateway rejects unsupported protocol values with `protocol_mismatch`.
- Protocol changes that remove or rename fields must use a new protocol number.
- Additive fields may stay on protocol `1` if older receivers can ignore them.
- The gateway advertises `min_protocol`, `max_protocol`, and `supported_protocols` in its `hello` response and protocol errors.

## Envelope

All messages are UTF-8 JSON objects:

```json
{
  "type": "hello",
  "protocol": 1
}
```

Common fields:

- `type`: string message type.
- `protocol`: integer protocol version.

Errors use the same envelope:

```json
{
  "type": "error",
  "protocol": 1,
  "message": "missing_field",
  "field": "player_name"
}
```

## Client To Gateway

### `hello`

```json
{
  "type": "hello",
  "protocol": 1,
  "client": "godot"
}
```

`client` is optional and must be a string when present.

### `join`

```json
{
  "type": "join",
  "protocol": 1,
  "player_name": "GodotPlayer",
  "password": "",
  "auth_token": ""
}
```

Required:

- `player_name`: string.

Optional:

- `password`: string.
- `auth_token`: string.

### `input`

```json
{
  "type": "input",
  "protocol": 1,
  "sequence": 7,
  "command": {
    "move_left": false,
    "move_right": true,
    "aim_left": false,
    "aim_right": false,
    "fire": false
  }
}
```

Required:

- `sequence`: integer command sequence.
- `command`: object containing local input booleans.

Allowed `command` fields:

- `aim_left`
- `aim_right`
- `power_up`
- `power_down`
- `move_left`
- `move_right`
- `jump`
- `fire`
- `weapon_next`
- `weapon_prev`

Every command field value must be a boolean. Unknown command names are rejected.

### `ping`

```json
{
  "type": "ping",
  "protocol": 1,
  "sequence": 8,
  "client_time_msec": 1234
}
```

Required:

- `sequence`: integer ping sequence.
- `client_time_msec`: integer client timestamp.

### `disconnect`

```json
{
  "type": "disconnect",
  "protocol": 1,
  "reason": "client_disconnect"
}
```

`reason` is optional and must be a string when present.

## Gateway To Client

### `hello`

```json
{
  "type": "hello",
  "protocol": 1,
  "min_protocol": 1,
  "max_protocol": 1,
  "supported_protocols": [1],
  "match_snapshot_schema": 1,
  "event_schema": 1,
  "password_required": false,
  "auth_required": false,
  "joins_open": true,
  "ban_enforced": false,
  "max_players": 0,
  "players_connected": 0,
  "server": "python-websocket-gateway"
}
```

The client should treat `supported_protocols` as the authoritative compatibility list for this gateway instance.
The Godot Online Match flow waits for this message before sending `join`, checks whether protocol `1` is in `supported_protocols`, handles pre-hello protocol errors, and disconnects without automatic retry when the gateway is incompatible.
`password_required` is advisory metadata from `groundfire-web-gateway`; the server still validates the actual `join.password` value when a gateway password is configured.
`auth_required` is advisory metadata from `groundfire-web-gateway`; the server validates `join.auth_token` when a gateway auth token is configured.
`joins_open` is advisory metadata for whether new joins are accepted; when it is false, `join` returns `server_closed`.
`ban_enforced` is advisory metadata for whether a player-name ban list is active; rejected names receive `banned`.
`max_players` is `0` when the gateway is unrestricted; otherwise the gateway rejects joins above that active-session limit with `server_full`. `players_connected` is the current active joined-session count.

### `snapshot`

```json
{
  "type": "snapshot",
  "protocol": 1,
  "sequence": 7,
  "state": {
    "status": "input",
    "player_name": "GodotPlayer",
    "joined": true,
    "last_input": {},
    "server_time_msec": 123456789,
    "match_snapshot_schema": 1,
    "event_schema": 1,
    "match_snapshot": {},
    "terrain_patches": [],
    "events": [
      {
        "schema": 1,
        "event_type": "terrain_explosion",
        "payload": {}
      }
    ]
  }
}
```

`match_snapshot_schema` and `event_schema` are independent schema numbers for the replicated state and event payloads carried inside the protocol envelope. Current value: `1`.

The current `match_snapshot` shape is the Python replicated simulation scaffold. Required top-level fields in schema `1`:

- `authority`: string, currently `server`.
- `game_phase`: string, for example `lobby` or `online`.
- `current_round`: integer.
- `num_rounds`: integer.
- `simulation_tick`: integer.
- `players`: array of replicated player objects.
- `entities`: array of replicated entity objects.
- `phase_ticks_remaining`: integer.
- `round_winner_player_number`: integer or null.
- `winner_player_number`: integer or null.
- `seed`: integer.
- `world_width`: number.
- `terrain_revision`: integer.
- `terrain_profile`: array of numbers.

Replicated players currently include:

- `player_number`: integer.
- `name`: string.
- `score`: integer.
- `money`: integer.
- `connected`: boolean.
- `is_computer`: boolean.
- `tank_entity_id`: integer or null.
- `acknowledged_command_sequence`: integer.
- `acknowledged_snapshot_sequence`: integer.
- `colour`: RGB integer tuple/array.
- `is_leader`: boolean.
- `selected_weapon`: string.
- `weapon_stocks`: array of `[weapon_name, count]` pairs.
- `round_defeated_player_numbers`: array of integers.

Replicated entities currently include:

- `entity_id`: integer.
- `entity_type`: string.
- `position`: two-number tuple/array.
- `velocity`: two-number tuple/array.
- `angle`: number.
- `owner_player`: integer or null.
- `payload`: object.

Events in schema `1` include:

- `schema`: integer event schema version.
- `event_type`: string.
- `payload`: object.

The only event currently emitted by the gateway scaffold is `terrain_explosion`.

### `pong`

```json
{
  "type": "pong",
  "protocol": 1,
  "sequence": 8,
  "client_time_msec": 1234,
  "server_time_msec": 123456789
}
```

### `disconnect`

```json
{
  "type": "disconnect",
  "protocol": 1,
  "reason": "client_disconnect"
}
```

### `error`

```json
{
  "type": "error",
  "protocol": 1,
  "message": "invalid_field",
  "field": "sequence",
  "expected": "integer"
}
```

Known validation errors:

- `invalid_json`
- `invalid_message`
- `missing_protocol`
- `invalid_protocol`
- `protocol_mismatch`
- `missing_field`
- `invalid_field`
- `unknown_command`
- `invalid_command`
- `unknown_type`

Reserved fatal join/runtime errors for client recovery:

- `invalid_password`
- `authentication_failed`
- `server_full`
- `server_closed`
- `server_unavailable`
- `banned`
- `join_rejected`
- `match_not_found`

The Godot client treats these as non-retryable until the user changes server or credentials.
The Python `groundfire-web-gateway` currently emits `invalid_password` when started with `--password` or `GROUNDFIRE_WEB_GATEWAY_PASSWORD` and a `join` message supplies a different password.
It emits `authentication_failed` when started with `--auth-token` or `GROUNDFIRE_WEB_GATEWAY_AUTH_TOKEN` and a `join` message supplies a different `auth_token`.
It emits `server_full` when started with `--max-players` or `GROUNDFIRE_WEB_GATEWAY_MAX_PLAYERS` and the active joined-session limit has been reached.
It emits `server_closed` when started with `--closed` or `GROUNDFIRE_WEB_GATEWAY_CLOSED=1`.
It emits `banned` when started with one or more `--ban-player` values or comma-separated `GROUNDFIRE_WEB_GATEWAY_BANNED_PLAYERS` and a `join.player_name` matches the normalized list.

## Remaining Protocol Work

- Replace the gateway simulation scaffold with the full `groundfire.server` runtime.
- Promote `match_snapshot` and event payloads into a complete versioned schema.
- Keep the current real TCP/WebSocket gateway transport test as the minimum compatibility guard for handshake/framing, password rejection, join, input, ping, and disconnect messages.
- Add browser-level end-to-end tests against the exported Godot web build.
- Define multi-version compatibility windows and downgrade/upgrade policy for future protocol versions.
