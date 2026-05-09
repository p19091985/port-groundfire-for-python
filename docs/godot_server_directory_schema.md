# Groundfire Godot Server Directory Schema

This document records the first browser-safe read-only server directory contract for the Godot client.

## Versioning

- Current schema: `1`.
- The top-level JSON object must include integer field `schema`.
- The top-level JSON object must include array field `servers`.
- Additive server fields may be ignored by older clients.
- Removing or renaming required fields requires a new schema number.

## Top-Level Shape

```json
{
  "schema": 1,
  "servers": []
}
```

Required:

- `schema`: integer directory schema version.
- `servers`: array of server objects.

## Server Object

```json
{
  "name": "Groundfire Online Test",
  "game": "Groundfire",
  "players": "2/8",
  "map": "classic",
  "latency": "42",
  "source": "online",
  "endpoint": "wss://play.groundfire.local/servers/test",
  "passworded": false,
  "auth_token": "dev-directory-token"
}
```

Required fields:

- `name`: non-empty string.
- `game`: non-empty string.
- `players`: non-empty string, currently display text such as `2/8`.
- `map`: non-empty string.
- `latency`: non-empty string, currently display text such as `42`, `33ms`, or `LAN`.
- `source`: `online` or `lan`.
- `endpoint`: non-empty string. Online entries must use `ws://` or `wss://`.
- `passworded`: boolean.

Optional fields reserved for the public service:

- `region`: string.
- `description`: string.
- `version`: string.
- `auth_token`: string, copied into the Godot `join` message for pre-provisioned development or private-directory joins.
- `tags`: array.
- `last_seen_msec`: integer timestamp.

`auth_token` is not a final public authentication model. Treat it as a temporary fixture/private-directory bridge while production account/session authentication is designed. Public directories should not publish long-lived shared secrets.

## Client Behavior

The Godot client validates the payload before showing entries. Invalid JSON, missing schema, unsupported schema, missing required server fields, wrong field types, unknown `source`, or non-WebSocket online endpoints make the client fallback to `res://data/server_directory.json`.

Web builds hide `source: "lan"` entries. Desktop builds can include them.

When an online entry includes `auth_token`, the client preserves it during directory normalization and sends it as `join.auth_token` through the WebSocket transport. Empty or omitted tokens are not sent.

## Godot Configuration

`application/config/server_directory_url` is an explicit override. When it is empty, the client reads `application/config/server_directory_environment` and then uses the matching environment URL:

- `dev`: `application/config/server_directory_url_dev`.
- `staging`: `application/config/server_directory_url_staging`.
- `production`: `application/config/server_directory_url_production`.

If the selected environment URL is empty or does not use `http://` or `https://`, the client uses the local fallback JSON. The default environment is `dev`.

The Options screen persists these values in `user://groundfire_options.cfg` under the `server_directory` section and applies them to the runtime ProjectSettings before the Server Browser reads the directory configuration.

## Remaining Service Work

- Choose and fill the real public HTTP endpoints for dev, staging, and production.
- Decide cache headers and refresh cadence for browser builds.
- Add presence/latency updates through WebSocket or another browser-safe channel.
- Replace temporary directory-carried `auth_token` fixtures with production authentication/session flow.
- Expand the browser runtime QA beyond the current served schema `1` fixture and first-pass cache/refresh header checks to cover production directory cache behavior under real hosting.
