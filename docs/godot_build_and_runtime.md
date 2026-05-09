# Godot Build And Runtime

This document records the local Godot build/runtime path used by the migration scaffold.

## Requirements

- Godot `4.6.2.stable`, available by default at `tools/godot/Godot_v4.6.2-stable_linux.x86_64`.
- Godot export templates `4.6.2.stable` installed under `~/.local/share/godot/export_templates/4.6.2.stable/`.
- Python dependencies installed in `.venv` so desktop tools can launch `groundfire-web-gateway`.

Required templates for the current presets:

- `linux_release.x86_64`
- `web_nothreads_release.zip`

## Validate

Run the headless project validation and runtime smoke checks:

```bash
scripts/validate_godot.sh
```

The validation checks script parseability, data model behavior, browser-safe persistence, terrain collision, deterministic desktop/web capability rules, scene startup, and smoke coverage for Main Menu, Options, Server Browser, Local Match, and Online Match controls.

Run the optional headless visual golden check:

```bash
scripts/validate_godot_visuals.sh --check
```

Refresh headless visual goldens after an intentional visual change:

```bash
scripts/validate_godot_visuals.sh --update-goldens
```

This captures Main Menu, Options, Server Browser, and Local Match through Godot headless rendering and compares them with `docs/references/godot_visual/`. The check fails if a golden is missing, so update goldens deliberately before adding the check to CI.

On renderers where Godot cannot read viewport pixels, such as the current dummy headless renderer, the script exits with a clear capture error instead of creating invalid goldens. Use browser QA as the current automated visual path until a capturable Godot render backend is available.

## Export

Export both supported targets:

```bash
scripts/export_godot.sh all
```

Export a single target:

```bash
scripts/export_godot.sh web
scripts/export_godot.sh linux
```

Outputs:

- Linux desktop: `build/godot/Groundfire.x86_64`
- Web: `build/godot-web/index.html`, `index.wasm`, `index.pck`, and support files

The export presets exclude `res://tests/*` from packaged artifacts; validation scripts still run those tests before export.

If templates are missing, `scripts/export_godot.sh` exits before validation and prints the expected template directory plus the official Godot template package URL.

## Package

Create release archives after validation/export:

```bash
scripts/package_godot_release.sh
```

Outputs are written to `dist/` with the project version from `pyproject.toml`:

- `groundfire-godot-<version>-linux-x86_64.tar.gz`
- `groundfire-godot-<version>-web.zip`
- `groundfire-godot-<version>-manifest.json`
- `groundfire-godot-<version>-SHA256SUMS`

Override release metadata when packaging a prerelease or CI build:

```bash
GROUNDFIRE_RELEASE_VERSION=0.25.0-dev scripts/package_godot_release.sh
GROUNDFIRE_RELEASE_PREFIX=groundfire-godot-nightly scripts/package_godot_release.sh
GROUNDFIRE_RELEASE_NOTES=docs/release_notes.md scripts/package_godot_release.sh
```

When `GROUNDFIRE_RELEASE_NOTES` is set, the manifest records the notes path and SHA256 so the packaged artifacts can be traced back to the release text.

## Release Verification

Every packaged release must include `groundfire-godot-<version>-SHA256SUMS` and `groundfire-godot-<version>-manifest.json`.

Verify downloaded artifacts before publishing or redistributing them:

```bash
cd dist
sha256sum --check groundfire-godot-<version>-SHA256SUMS
```

The manifest records artifact names, sizes, SHA256 digests, target platforms, and optional release notes metadata. Treat the manifest and checksum file as required release artifacts, not optional build logs.

Signing policy for the current migration phase:

- Checksums are mandatory for every Linux/Web package.
- Detached cryptographic signatures are not required yet because there is no finalized project signing key.
- When a signing key is introduced, publish detached signatures beside the archives and record the signing key fingerprint in this document before making signed packages the official release gate.

## Browser Hosting

Host the contents of `build/godot-web/` or the unpacked web release archive from an HTTP(S) origin. Opening `index.html` directly from the filesystem is not a supported runtime path.

Recommended hosting expectations:

- Serve `index.html`, `index.wasm`, `index.pck`, JavaScript glue files, and generated assets from the same origin unless CORS is intentionally configured.
- Use HTTPS for public deployments, especially when connecting to `wss://` gameplay gateways or HTTP(S) server directory endpoints.
- Configure `.wasm` files with `application/wasm`.
- Keep compression and cache headers consistent across `index.pck`, `.wasm`, and JavaScript files. For public releases, prefer immutable cache headers on versioned artifacts and short cache headers on `index.html`.
- Do not expose desktop-only LAN, UDP, process spawning, or local dedicated server tools from the web build.

## Distribution Notes

Linux desktop archives contain the exported executable and Godot runtime support files. Web archives contain only browser-safe assets.

Before publishing a release:

- Run `scripts/validate_godot.sh`.
- Run `scripts/package_godot_release.sh`.
- Run `scripts/qa_godot_web.sh --check` on a machine with Chromium/Chrome, export templates, and Python browser QA dependencies.
- Verify `SHA256SUMS`.
- Attach the Linux archive, Web archive, manifest, checksum file, and release notes together.

The current release process is still local/manual. CI should eventually run the same commands, upload artifacts from `dist/`, and block publishing when validation, browser QA, or checksum generation fails.

## Browser QA

Run browser screenshot QA against the exported web build:

```bash
scripts/qa_godot_web.sh --check
```

This exports the web target, serves it locally, opens Chromium/Chrome through DevTools, captures Main Menu, Options, Server Browser, and Local Match screenshots, and compares them with `docs/references/godot_browser_visual/`.

Browser runtime QA also opens the web export with `?qa=browser_runtime` and waits for the Godot client to publish `window.__groundfireQaResult`. That runtime QA path runs a `seed` pass and a `verify` pass with the same Chromium profile, verifying browser-safe persistence for favorites, history, and filters across browser sessions. It also loads a served schema `1` HTTP directory fixture, validates the fixture's `Cache-Control`, `ETag`, and `X-Groundfire-Directory-Refresh` headers, confirms LAN entries and desktop-only features stay hidden in the web runtime, checks invalid-directory fallback diagnostics, and exercises Online Match fatal error handling against real local `groundfire_net.websocket_gateway` password, auth, full-server, closed-server, and banned-player rejections.

Refresh browser goldens after an intentional visual change:

```bash
scripts/qa_godot_web.sh --update-goldens
```

The browser QA requires Chromium or Chrome plus Python dependencies from `requirements.txt`, including `Pillow` and `websocket-client`.

## WebSocket Protocol

The browser-safe Godot client and Python gateway protocol is documented in `docs/godot_websocket_protocol.md`. The current gateway enforces protocol version `1`, validates required fields before dispatching messages to the simulation scaffold, and can exercise first-pass fatal join failures:

- `invalid_password` with `groundfire-web-gateway --password secret` or `GROUNDFIRE_WEB_GATEWAY_PASSWORD=secret`.
- `authentication_failed` with `--auth-token token-123` or `GROUNDFIRE_WEB_GATEWAY_AUTH_TOKEN=token-123`.
- `server_full` with `--max-players 2` or `GROUNDFIRE_WEB_GATEWAY_MAX_PLAYERS=2`.
- `server_closed` with `--closed` or `GROUNDFIRE_WEB_GATEWAY_CLOSED=1`.
- `banned` with `--ban-player Mallory` or comma-separated `GROUNDFIRE_WEB_GATEWAY_BANNED_PLAYERS=Mallory`.

## Server Directory

The read-only server browser directory schema is documented in `docs/godot_server_directory_schema.md`. The Godot client validates schema `1` for HTTP and local fallback payloads before rendering entries.

`application/config/server_directory_url` is still available as an explicit override. Otherwise set `application/config/server_directory_environment` to `dev`, `staging`, or `production` and configure the matching `application/config/server_directory_url_*` setting. Empty or non-HTTP(S) environment URLs use `res://data/server_directory.json`.

The same values can be changed from the Godot Options screen during local testing. They persist in `user://groundfire_options.cfg` and are applied before opening the Server Browser.

## Run

Run the Linux desktop export:

```bash
build/godot/Groundfire.x86_64
```

Serve the web export from a local HTTP server:

```bash
python -m http.server 8080 --directory build/godot-web
```

Then open `http://127.0.0.1:8080/`.

## Platform Expectations

Web builds expose browser-safe flows only: local match, online server browser entries, WebSocket-compatible online play, favorites, history, and browser-safe persistence.

Desktop builds may expose native workflows: LAN tab, UDP/native networking affordances, process spawning, and the local dedicated gateway launcher.
