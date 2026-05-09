# Groundfire Godot Migration Strategy

This migration keeps the current Python/Pygame version alive while a Godot client is built in parallel.

## Decision

- Official future client: Godot 4 + GDScript.
- Web build: only browser-safe features.
- Desktop build: can expose local, LAN, UDP, and dedicated server tools.
- Current Python server: remains the dedicated/headless server while the client migrates.

## Web Feature Rule

If a multiplayer feature depends on native OS/network behavior that browsers do not support well, it is not exposed in the web build.

Hidden on web:

- LAN discovery.
- UDP transport.
- Local dedicated server launcher/tools.
- Process spawning for local client/server workflows.
- RCON over local UDP.

Allowed on web:

- Local match against AI.
- Online server browser backed by browser-safe transport.
- Online play through WebSocket/WebRTC-compatible services.
- Favorites/history stored by browser-safe persistence.

## First Migration Slice

The `godot/` project is a standalone Godot client scaffold. It starts with:

- `PlatformCapabilities` autoload.
- Main menu.
- Server browser placeholder.
- Platform-aware feature visibility.
- Groundfire menu and weapon icon assets copied into `godot/assets/`.
- Shared `GroundfireTheme` script for colors, panels, buttons, and field styling.
- `ServerDirectory` read-only browser model with browser-safe online entries and desktop-only LAN entries.
- `godot/data/server_directory.json` as the temporary data source until HTTP/WebSocket is connected.
- Godot runtime validation script for server directory filtering.
- Server browser row selection and staged connect target status.
- Server browser filters, favorites/history, password dialog, and functional refresh/connect actions.
- Browser-safe `user://` persistence for favorites and history via `BrowserStore`.
- Server Browser Favorites/History now has a first-pass game-flow polish layer: favorite toggle/removal, clear-history action, disabled empty-history state, undo restore for removed favorites/cleared history, History-backed favorite details, and fallback rows for saved favorite endpoints missing from the current directory.
- Server browser scroll container and hover/selection row states.
- Themed connect/password modal built from Groundfire panels and buttons.
- `NetworkAdapter` scaffold for WebSocket-safe web connects and desktop UDP allowance.
- `LocalMatch` vertical slice with terrain, tanks, projectile, input, and HUD.
- Main menu options screen with initial FPS/audio toggles and server directory configuration hint.
- Project input actions for aim, power, and fire, with runtime key defaults.
- HTTP server directory configuration via `application/config/server_directory_url` with local JSON fallback.
- Local match round state, player/enemy HP, simple AI shot, explosion, damage, and round reset.
- Separated `LocalMatchHud` script for HUD rendering.
- Network message contract helpers for hello, join, input, snapshots, and parse errors.
- Initial destructible terrain model with crater generation.
- Turn owner tracking, player/enemy round wins, score, and weapon cycling in Local Match.
- Options persistence through `user://groundfire_options.cfg`.
- Export preset scaffold for Linux desktop and web.
- Original-style terrain generation scaffold based on the Python `Landscape.generate_terrain` slice/mound/smoothing model.
- Separate `TankState` model for health, fuel, slope angle, movement, gun angle, and launch origin.
- Separate `WeaponInventory` model with Shell, Machine Gun, MIRV, Missile, and Nuke definitions, ammo, blast radius, damage, and speed multipliers.
- Initial jump jet/airborne tank behavior, mouse aiming, weapon previous/next actions, and credits display.
- First special projectile behaviors for Machine Gun bursts, MIRV fragment split, Missile steering, and Nuke blast tuning.
- `ControlSettings` for browser-safe persistent input bindings under `user://groundfire_controls.cfg`.
- Initial `WebSocketClient` transport node using Godot `WebSocketPeer` for hello, join, input, ping, disconnect, and parsed messages.
- Interactive key capture/rebinding in Options on top of `ControlSettings`.
- Server Browser connect path now instantiates `WebSocketClient`, opens `ws://`/`wss://` endpoints, sends join, pings, and reports incoming message status.
- Initial `OnlineMatch` scene that connects through `WebSocketClient`, sends local input commands, receives snapshots, and renders snapshot key/value state.
- `groundfire-web-gateway` Python entrypoint with a standard-library WebSocket gateway for Godot hello, join, input, ping, disconnect, and snapshot messages.
- Gateway simulation scaffold wired to existing Python `MatchState` and `WorldState`, including replicated player/tank state, command acknowledgements, terrain explosions, terrain patches, and match snapshots.
- Online Match replicated rendering for terrain profiles, replicated entities/tanks, player panel, round, and simulation tick.
- Online Match interpolation layer for replicated entities plus projectile drawing and terrain explosion effects.
- Local Match terrain chunk scaffold with slice clipping, crater interval subtraction, falling chunk pause/acceleration, and chunk polygon rendering.
- Options control rebinding now captures keyboard keys plus gamepad buttons/axes, persists custom gamepad bindings, reports gamepad conflicts, and separates keyboard/gamepad columns.
- Local Match HUD now receives a full weapon inventory snapshot and renders selected weapon/ammo chips instead of only a single selected weapon label.
- Local Match post-round shop overlay with round result, score, reward, credits, weapon ammo packs, buy actions, and continue-to-next-round flow.
- Local Match AI now chooses shell shots by simulating candidate angle/power arcs against current wind, terrain, and player position instead of using only a distance-based random shot.
- Local Match now has a first-pass turn wind model with bounded wind shifts, per-shot gust influence, AI trajectory simulation using effective wind, and directional HUD wind text.
- Local Match camera scaffold with minimum world size, smooth framing of tanks/projectiles/explosions, projectile lookahead, explosion shake, mouse-to-world aiming, zoom, and map bounds.
- Options gamepad capture can now be cancelled from the controller with Back/Select as well as from keyboard cancel.
- Local Match projectile/terrain collision now uses exact segment intersection against terrain chunks, matching the Python `ground_collision` direction more closely than fixed-step sampling.
- Godot validation now includes a runtime terrain collision smoke test for vertical, clear-air, and diagonal shots.
- Terrain chunks now carry interpolated per-side colors through crater clipping, fall as linked superblocks, and merge/link when resting against lower chunks.
- TerrainModel now has a first-pass classic `drop_terrain` path with the same minimum-land clamp used by the Python `Landscape.drop_terrain`, preparing the quake/drop fidelity pass.
- Local Match now wires a first-pass quake/drop event into the round loop, using timed terrain dropping, camera shake, and HUD quake status.
- Local Match now uses the classic first/between quake timing and plays the classic quake rumble as a looped Godot `AudioStreamPlayer`, pausing with the match and stopping cleanly when the quake ends or the round flow changes.
- Local Match tank damage now follows the classic exact-zero-health rule and round-over detection uses tank state instead of raw `health <= 0`.
- Options now includes video/audio/gameplay settings beyond FPS/audio: fullscreen, VSync, master volume, screen shake, camera smoothing, and mouse aiming.
- Local Match reads gameplay options at runtime for camera shake, camera smoothing, and mouse aiming.
- Server Browser now has richer client-side filters for passwordless servers, open slots, and sortable latency/name/player-count views.
- Local Match AI now chooses first-pass strategic weapons based on distance, line of sight, player health, trajectory miss distance, and available ammo.
- Machine Gun now uses a closer classic direct-hit tracer volley: ammo is consumed per firing action, bullets draw line traces, fire with the classic 0.1s spacing, deal direct tank damage, and expire on terrain without cratering or splash damage.
- Machine Gun round ammo, volley size, and shot spacing now live behind `WeaponInventory` constants used by both ammo consumption and Local Match firing.
- MIRV now splits closer to the classic behavior: apex-timed split, five configurable fragments, and horizontal spread with vertical velocity reset.
- MIRV round ammo, fragment count, horizontal spread, and minimum split age now live behind named constants used by both inventory data and Local Match split behavior.
- MIRV split now expires the original parent projectile after spawning fragments, leaving only the fragment shells active after the split.
- Missile now has a first-pass classic steering model with launch angle, fuel, steer acceleration, player aim-input steering, simple enemy steering, and ballistic fall after fuel is spent instead of direct homing.
- Missile steering now uses named Local Match constants for angle-change clamp, recentring rate, AI steer scale, and minimum preserved speed.
- Nuke now carries the classic `white_out` weapon flag into Local Match explosions, drawing a fullscreen white flash that fades at the Python `Blast` whiteout rate.
- Tank gun angle/power controls now use named classic default acceleration/max-speed constants and stop changing immediately when aim/power input is released.
- Jump jets now apply classic-style slope-aware thrust using the tank angle, with a separate horizontal component on inclined terrain and the Python default fuel usage rate.
- Boosting tanks now rotate in air with the classic left/right 90 degrees-per-second turn behavior and recover toward level when no turn input is held.
- Local Match projectiles now inherit the firing tank's airborne velocity, matching the classic `gun_launch_velocity` behavior for shots fired while using jump jets.
- Tank airborne gravity now uses a named constant aligned with the classic projectile/boost scale instead of the earlier oversized hardcoded fall acceleration.
- Tank gun angle and power bounds now live behind named `TankState` constants and are covered by the local-match fidelity check, preparing final bound/scale tuning against the classic values.
- `TankState` now names its round-start gun angle, gun power, health, and fuel defaults so final classic tuning can happen without hunting literals.
- Local Match projectile gravity now lives behind a named `PROJECTILE_GRAVITY` constant shared by AI trajectory search, MIRV apex timing, ballistic shells, and Machine Gun tracers.
- `TankState` now exposes `launch_velocity`, and Local Match player/enemy firing uses that tank-owned launch calculation instead of rebuilding the formula entirely in the scene script.
- `TankState` now detects when terrain drops too far beneath a grounded tank and switches back into airborne fall instead of snapping the tank down instantly.
- `TankState` now has named movement/fuel/slope constants and passively slides grounded tanks on steep slopes, matching another piece of the classic `move_tank` behavior.
- `TerrainModel` now exposes playable tank bounds, and `TankState` clamps airborne tanks to those bounds while clearing horizontal velocity at the edge.
- Control rebinding now has selectable gamepad profiles for all gamepads or a connected device-specific profile.
- Local Match pause now includes Options access and explicit vertical focus neighbors for controller/keyboard navigation.
- Local Match shop buttons now wire vertical focus neighbors across affordable buy actions and Continue for controller/keyboard navigation.
- Server Browser now wires explicit keyboard/controller focus neighbors across filter controls, table rows/cells, action buttons, close/back, and the password modal; row focus selects servers, `ui_accept` connects, and `ui_cancel` closes the modal.
- Mouse aiming now has a world-space reticle and left-click fire path.
- Local Match HUD now draws player/enemy HP bars, fuel bar, player names, and weapon inventory icons from the classic `weaponicons.png` atlas.
- Local Match HUD now has a structured first-pass game layout with a turn/phase banner, angle and power gauges, score/credits/wins chips, wind/quake status, a separate message strip, and responsive weapon inventory chips.
- WebSocket transport now reports closed connection attempts reliably and exposes connection state/last sequence for higher-level UI.
- Online Match now has reconnect/backoff UI, periodic ping latency, acknowledged-command tracking, pending-input diagnostics, terrain revision/tick diagnostics, and first-pass local tank prediction.
- Options now includes classic-style desktop resolution presets, persists the selected preset, and applies window size outside web/fullscreen builds.
- Server Browser now persists filter text, passwordless/open-slot toggles, and latency/name/player-count sort mode alongside favorites and history.
- Server Browser online directory refresh now has a first loading state that blocks duplicate refreshes, disables the Refresh All action, and restores normal action text on success or fallback.
- Server Browser table layout now uses named per-column widths and row/header heights instead of one fixed cell size for every column.
- Options now includes AI difficulty selection, and Local Match applies easy/normal/hard tuning to trajectory search precision, aim error, and strategic weapon use.
- Desktop-only Dedicated Server now has an initial Godot tool screen that can launch the local `groundfire-web-gateway` from `.venv` while staying hidden on web.
- Online Match now exposes manual reconnect/back controls in addition to automatic reconnect/backoff diagnostics.
- `scripts/export_godot.sh` now validates the Godot project, reports missing templates with the official package URL, and runs Linux/Web export presets with the installed Godot 4.6.2 export templates.
- Linux/Web export presets now exclude `res://tests/*` from release artifacts while keeping tests available to headless validation.
- Platform capability rules now have deterministic desktop/web helpers so validation can assert hidden web features and visible desktop LAN/server tools without relying on the current export target.
- Godot validation now includes a runtime smoke test for Main Menu, Options, Server Browser, Local Match, Online Match controls, browser-safe HTTP directory parsing, and desktop/web capability visibility.
- `docs/godot_build_and_runtime.md` documents validation, Linux/Web export commands, generated outputs, local web serving, and platform expectations.
- Godot validation now includes local-match fidelity and online reliability checks in addition to the runtime scene smoke tests.
- `scripts/package_godot_release.sh` creates first-pass Linux/Web release artifacts, a manifest, and SHA256 checksums after export.
- `scripts/qa_godot_web.sh` exports the web build, serves it locally, captures browser screenshots through Chromium/Chrome DevTools, and compares them with `docs/references/godot_browser_visual/`.
- Browser QA now also runs exported-web runtime checks through `?qa=browser_runtime`, covering browser-safe favorites/history/filter persistence across seed/verify browser sessions, served schema `1` HTTP directory loading, first-pass directory cache/refresh headers, LAN/desktop-only feature hiding, invalid-directory fallback diagnostics, and Online Match fatal error handling against real local `groundfire-web-gateway` password, auth, full-server, closed-server, and banned-player rejections.
- Godot release packaging now derives the artifact version from `pyproject.toml` by default, supports release version/prefix overrides, and can attach release notes metadata to the manifest.
- `docs/godot_build_and_runtime.md` now documents release verification, mandatory checksum handling, current signing policy, browser hosting expectations, and distribution notes for Linux/Web artifacts.
- `scripts/validate_godot_visuals.sh` now exposes the headless Godot visual golden check with explicit `--check` and `--update-goldens` modes.
- Godot WebSocket messages and the Python gateway now carry protocol version metadata on hello, join, input, ping/pong, disconnect, errors, and snapshots, and the gateway rejects missing or mismatched protocol versions.
- `docs/godot_websocket_protocol.md` documents the first versioned WebSocket message schema, including first-pass `match_snapshot` and event schema sections; the Python gateway now advertises its supported protocol range and validates required fields, basic types, and the allowed input command set before dispatch.
- Online Match now waits for the gateway `hello`, verifies that the server-supported protocol list includes the Godot client protocol, handles pre-hello protocol errors, shows snapshot/event schema diagnostics, and disables automatic reconnect on protocol incompatibility.
- `docs/godot_server_directory_schema.md` documents server directory schema `1`, and the Godot `ServerDirectory` parser now rejects invalid HTTP/local payloads before rendering entries.
- Server directory configuration now supports explicit URL overrides plus `dev`, `staging`, and `production` environment URL settings while preserving the local fallback JSON path.
- Options now exposes the server directory environment and override/dev/staging/production URLs, validates HTTP(S) directory URLs, persists them in `user://groundfire_options.cfg`, and applies them before the Server Browser loads entries.
- Online Match now classifies fatal server join/runtime errors such as invalid password, authentication failure, server full, and match not found, stops automatic reconnect for those cases, and shows a recovery-oriented status message.
- `groundfire-web-gateway` now has an optional first-pass join password gate through `--password` or `GROUNDFIRE_WEB_GATEWAY_PASSWORD`, advertises `password_required`, and emits `invalid_password` for rejected Godot joins.
- Godot `join` messages now support an optional `auth_token`, and `groundfire-web-gateway` can require it through `--auth-token` or `GROUNDFIRE_WEB_GATEWAY_AUTH_TOKEN`, advertise `auth_required`, and emit `authentication_failed` for rejected joins.
- Server directory schema `1` now preserves an optional `auth_token` for pre-provisioned development/private-directory joins, so directory entries can feed the Godot WebSocket `join.auth_token` path.
- `groundfire-web-gateway` now has an optional first-pass active player capacity gate through `--max-players` or `GROUNDFIRE_WEB_GATEWAY_MAX_PLAYERS`, advertises `max_players`/`players_connected`, and emits `server_full` for excess Godot joins.
- `groundfire-web-gateway` now has an optional first-pass closed-join mode through `--closed` or `GROUNDFIRE_WEB_GATEWAY_CLOSED`, advertises `joins_open`, and emits `server_closed` for rejected Godot joins.
- `groundfire-web-gateway` now has an optional first-pass player-name ban list through `--ban-player` or `GROUNDFIRE_WEB_GATEWAY_BANNED_PLAYERS`, advertises `ban_enforced`, and emits `banned` for rejected Godot joins.
- Gateway compatibility tests now exercise a real local TCP/WebSocket handshake and masked client frames through the actual gateway handler, covering connected snapshot, hello, invalid password rejection, successful join, input, ping, and disconnect messages.
- Exported web browser QA now starts real local `groundfire-web-gateway` instances for `invalid_password`, `authentication_failed`, `server_full`, `server_closed`, and `banned`, reserves a `--max-players 1` slot for the full-server case, passes their WebSocket endpoints into `?qa=browser_runtime`, and verifies that Online Match surfaces each as a fatal, non-retrying join failure.

## Current Status

The Godot client now has a usable migration scaffold instead of only placeholder screens, but the migration is not complete. It covers playable local and online slices, export automation, packaging, and browser visual QA; it still needs final gameplay fidelity, production networking, visual parity, release hardening, and the remaining classic client flows before it can replace the Python/Pygame client.

Implemented or started:

- Main menu with Groundfire logo/background and basic navigation.
- Initial Options screen with FPS/audio toggles.
- Platform capability split for desktop versus web.
- Server Browser with tabs, filtering, selection, favorites/history, password modal, connect action, and persistence.
- Configurable HTTP server directory URL with local JSON fallback.
- HTTP server directory loading now has timeout, one retry, diagnostics, and fallback messaging.
- Local Match vertical slice with player tank, enemy tank, aim, power, projectile, explosion, HP, simple AI, round state, and reset.
- Local Match now has a separate terrain model, crater deformation, turn tracking, round wins, score, and basic weapon cycling.
- Local Match now uses separate terrain, tank, and weapon inventory scripts instead of keeping all gameplay state inside the scene script.
- Player movement on terrain, fuel drain, slope angle, ammo usage, per-weapon damage/blast radius, and end-of-round banner are implemented as a fidelity scaffold.
- Jump jets, airborne gravity, accelerating gun controls, mouse aim, credits, and first-pass special weapon behavior are implemented.
- Terrain now has an initial chunk-based model inspired by Python `Landscape.clip_slice`, including crater clipping, detached/falling chunk animation, and chunk polygon drawing in Local Match.
- Separate HUD script for Local Match.
- Initial input actions for aim, power, fire, weapon cycling, and pause.
- Local Match pause overlay exists with resume, restart round, and main menu actions.
- Network adapter message contract helpers for browser-safe protocol work, including snapshot, ping, disconnect, encode, and parse helpers.
- WebSocket transport scaffold now exists and can connect, send hello/join/input/ping/disconnect, and emit parsed messages.
- Server Browser can now route WebSocket endpoints into an initial Online Match scene.
- Online Match can connect, join, ping, send local input snapshots, consume server snapshots, interpolate replicated entities, and render terrain/entities/projectiles/players from `match_snapshot`.
- Python WebSocket gateway scaffold exists in `groundfire_net.websocket_gateway` and has contract tests against the Godot message shape.
- The gateway now produces real `MatchSnapshot` payloads from Python simulation scaffolds instead of only echo-style status snapshots.
- Persistent control binding scaffold exists, is visible/resettable from Options, and supports interactive key capture.
- Default gamepad bindings now exist for fire, weapon cycling, pause, jump, aim, power, and movement.
- Options now shows gamepad hints beside each action and reports keyboard binding conflicts.
- Options controls now live inside a scrollable panel, buttons can receive controller/keyboard focus, key capture can be cancelled, gamepad buttons/axes can be captured interactively, and conflicting keyboard/gamepad bindings can be reset from the conflict section.
- Local Match HUD now shows full weapon inventory chips with selected weapon state and live ammo counts.
- Local Match has an initial post-round economy/shop screen: wins award credits, damage earns score/credits, weapon ammo packs can be bought, and continuing starts the next round without the old auto-advance banner flow.
- Enemy AI now evaluates candidate shell trajectories and picks a near-target shot with a small inaccuracy offset.
- Local Match now has first-pass camera behavior: a world larger than small viewports, smoothed zoom/framing around active subjects, projectile lookahead, explosion camera shake, mouse aiming through camera coordinates, projectile bounds, and a visible map frame.
- Options gamepad capture now supports controller-side cancellation with Back/Select.
- Pause overlay now focuses Resume when opened so controller/keyboard navigation has a usable first target.
- Terrain/projectile impact detection now resolves the first segment intersection against chunk polygons and feeds the actual collision point into explosions.
- A headless Godot terrain collision check now covers the new segment collision path.
- Terrain chunks now keep interpolated classic-style color bands when clipped, fall as linked superblocks, and merge or relink when they settle.
- TerrainModel now exposes classic-style terrain dropping with a minimum-land clamp, and Local Match tank death now matches the Python rule where exact zero health is still alive until further damage.
- Local Match now has first-pass quake/drop wiring that periodically lowers terrain during active play, shakes the camera, and surfaces quake state in the HUD.
- Local Match now uses the classic first/between quake timing, plays the classic quake rumble as a loop during quake/drop, pauses it with the pause overlay, and stops it at quake end or round/shop transitions.
- Options now persists fullscreen, VSync, master volume, screen shake, camera smoothing, and mouse aiming.
- Options now persists classic-style resolution presets and applies the selected desktop window size.
- Local Match applies persisted camera shake, camera smoothing, and mouse aiming settings.
- Server Browser filters now include passwordless-only, open-slot-only, and latency/name/player-count sorting.
- Server Browser filter text, passwordless/open-slot toggles, and sort mode now persist through the browser-safe `BrowserStore`.
- Server Browser Favorites/History now supports removing favorites, clearing history, undoing those destructive actions, disabling history cleanup when empty, tab-specific empty messages, and showing saved favorite endpoints from known History details or fallback rows when the current directory omits them.
- Server Browser now prevents duplicate online directory refreshes with a visible loading action state and clears that state on HTTP success, failure fallback, or local JSON refresh.
- Server Browser loading state now renders a muted table message row while the online directory request is in flight, replacing stale rows until success or fallback.
- Server Browser table cells now have first-pass tuned column widths for server, game, players, map, and latency plus named row/header height constants.
- Enemy AI can choose Shell, Machine Gun, MIRV, Missile, or Nuke based on first-pass tactical scoring and available ammo.
- Machine Gun firing now spends volley ammo and resolves as classic-style direct-hit tracers instead of splash/explosion projectiles, with per-bullet cooldown spacing instead of a fully simultaneous burst.
- Machine Gun ammo-per-round, volley size, and cooldown spacing are centralized in `WeaponInventory`, with Local Match reading those constants as fallback firing values.
- MIRV split behavior now uses configurable five-fragment horizontal spread at projectile apex instead of the earlier three-fragment rotated placeholder.
- MIRV ammo-per-round, fragment count, spread, and minimum split age are centralized as named fidelity constants.
- MIRV parent projectiles now expire immediately after splitting, so the active projectile set contains only the spawned fragments.
- Missile behavior now uses fuel-limited steering and angle-change acceleration rather than direct target homing, moving it closer to the original controllable missile entity.
- Missile steering clamp/recentering and AI steer scale now live behind named Local Match constants and are covered by the fidelity check.
- Nuke behavior now has a first-pass classic whiteout flash in addition to its larger blast/damage tuning.
- Tank gun acceleration now matches the classic release behavior more closely by zeroing aim/power change speed when controls are neutral.
- Jump jets now push along the tank's slope-adjusted normal and drain fuel at the classic default rate instead of applying only a fixed vertical impulse.
- Jump-jet input now passes tank left/right through to boost rotation, so airborne tanks can tilt while boosting and settle back toward level without side-thrust movement hijacking the input.
- Shells and special projectiles now add the tank's current airborne velocity at launch, so firing during jump-jet movement carries momentum into the projectile.
- Airborne tank falling now uses the `TANK_AIR_GRAVITY` fidelity constant, keeping jump-jet motion closer to the classic boost/gravity balance.
- Gun angle/power clamps now use explicit fidelity constants instead of hardcoded magic numbers in `update_gun` and mouse aiming.
- Round-start gun angle, gun power, health, and fuel now use explicit `TankState` defaults instead of repeated literals.
- Projectile gravity now uses a single Local Match fidelity constant across live projectile updates, AI shell simulation, Machine Gun tracers, and MIRV split timing.
- Projectile launch velocity inheritance now lives on the tank model, closer to the Python `gun_launch_velocity`/`gun_launch_velocity_at_power` split.
- Grounded tanks now detach into airborne fall when crater/drop terrain opens a meaningful gap under them, closer to the classic ground contact pass.
- Grounded tanks now passively slide on slopes above the classic steepness threshold, with movement speed, slope drag, and fuel-use constants named in `TankState`.
- Airborne tanks now respect terrain-provided playable bounds and zero horizontal velocity when clamped at a map edge, matching the classic edge stop behavior.
- Options now exposes gamepad profile selection and stores per-device gamepad bindings when a connected device profile is selected.
- Pause overlay now has Options access and explicit focus neighbors for stable controller/keyboard navigation.
- Shop overlay buy/continue controls now have first-pass vertical focus neighbors for controller/keyboard navigation.
- Server Browser now has first-pass focus-neighbor wiring for filters, server table rows/cells, actions, close/back, and password modal controls, including controller/keyboard accept on selected rows and cancel from the modal.
- Mouse aim now updates a world reticle and supports left-click firing.
- Local Match HUD now uses the classic `weaponicons.png` atlas for weapon chips and has separate bars for player HP, enemy HP, and fuel.
- Local Match HUD now groups the core combat state into a more production-shaped overlay: turn/phase/weapon banner, HP/fuel bars, angle/power gauges, score/economy chips, wind/quake status, message strip, and responsive weapon inventory rows.
- WebSocket transport exposes connection state and sequence tracking.
- Online Match now reconnects with exponential backoff, displays latency/ack/pending/tick/terrain diagnostics, prunes acknowledged commands, and applies local prediction to the player's replicated tank.
- Online Match now has explicit Reconnect and Back controls for production failure-flow polish.
- Options persists AI difficulty, and Local Match uses it to adjust AI search granularity, aim variance, and special-weapon aggression.
- Local Match wind now shifts between turns/rounds, applies a small gust component to projectile motion and AI trajectory search, and exposes a directional wind label in the HUD.
- Desktop-only Dedicated Server exposes a first Godot gateway launcher for the Python WebSocket gateway.
- Linux desktop and web export preset scaffold.
- Export automation exists in `scripts/export_godot.sh` for Linux desktop and web presets after validation; the local workspace has Godot 4.6.2 export templates installed and both presets export successfully.
- Release exports exclude Godot runtime test scripts from the packaged Linux/Web artifacts.
- Runtime smoke validation now covers Main Menu, Options, Server Browser, Local Match, Online Match controls, web-safe directory parsing, and deterministic desktop/web feature rules.
- Local-match fidelity and Online Match reliability checks now run through `scripts/validate_godot.sh`.
- Browser visual QA exists through `scripts/qa_godot_web.sh` with reference screenshots for Main Menu, Options, Server Browser, and Local Match.
- Browser runtime QA now serves a schema `1` directory fixture and verifies storage/filter persistence across separate seed/verify browser sessions, HTTP directory parsing, first-pass `Cache-Control`/`ETag`/refresh headers, web-hidden LAN/desktop features, invalid-payload fallback diagnostics, and real local gateway `invalid_password`, `authentication_failed`, `server_full`, `server_closed`, and `banned` handling inside the exported web build.
- Release packaging exists through `scripts/package_godot_release.sh`, producing Linux/Web archives, a JSON manifest, and `SHA256SUMS`.
- Release artifacts now use versioned names, with `GROUNDFIRE_RELEASE_VERSION`, `GROUNDFIRE_RELEASE_PREFIX`, and `GROUNDFIRE_RELEASE_NOTES` available for prerelease/CI packaging.
- Build/runtime documentation now covers release verification, checksum usage, current signing policy, browser hosting expectations, and distribution notes.
- Optional headless visual golden validation exists through `scripts/validate_godot_visuals.sh`; it captures Main Menu, Options, Server Browser, and Local Match and fails on missing goldens unless they are updated intentionally.
- The browser-safe WebSocket contract now has a first enforced protocol version gate shared by the Godot `NetworkAdapter` and Python `groundfire-web-gateway`.
- The first WebSocket protocol document exists and gateway-side shape validation covers hello, join, input command names/booleans, ping, disconnect, error, and snapshot envelopes; gateway hello/errors now advertise supported protocol versions, snapshots include `match_snapshot_schema` and `event_schema` metadata, and events carry a schema number.
- Online Match now performs first-pass client-side protocol compatibility negotiation before sending join/input messages, handles protocol handshake errors without reconnect loops, and surfaces protocol/schema status in the network diagnostics panel.
- Online Match and Server Browser now share first-pass fatal server error copy through `NetworkAdapter`, so password/auth/full-server failures do not enter automatic reconnect loops.
- The Python WebSocket gateway can now enforce an optional join password and returns `invalid_password`, making the Godot password rejection path testable against a real gateway scaffold.
- The Godot client can now send an optional join `auth_token`, and the Python WebSocket gateway can enforce it with `authentication_failed`, making the auth rejection path testable against a real gateway scaffold.
- The Godot server directory now validates and preserves optional `auth_token` values, allowing local/HTTP directory fixtures to exercise authenticated join rejection without hand-editing the Online Match entry.
- The Python WebSocket gateway can now enforce an optional joined-player capacity and returns `server_full`, making the Godot full-server rejection path testable against a real gateway scaffold.
- The Python WebSocket gateway can now close new joins and returns `server_closed`, making the Godot closed-server recovery path testable against a real gateway scaffold.
- The Python WebSocket gateway can now enforce a first-pass player-name ban list and returns `banned`, making the Godot ban recovery path testable against a real gateway scaffold.
- Gateway compatibility coverage now includes an actual TCP/WebSocket transport round trip with real handshake/framing, password rejection, join, input, ping, and disconnect handling in addition to direct session-level contract tests.
- Browser runtime QA now covers real exported-web-to-gateway join failure paths for `invalid_password`, `authentication_failed`, `server_full`, `server_closed`, and `banned`, including user-facing fatal status and no reconnect loop.
- Server directory schema `1` is now documented and enforced in Godot for HTTP and local fallback payloads, including required server fields, boolean password flags, source validation, and WebSocket-only online endpoints.
- Server directory configuration now has a first environment model: `application/config/server_directory_url` can override everything, otherwise the selected `application/config/server_directory_environment` chooses the dev/staging/production URL setting, with local JSON fallback when empty.
- Options now has first-pass online directory controls for choosing the server directory environment and editing override/dev/staging/production URLs without editing `project.godot` by hand; invalid non-HTTP(S) directory URLs are diagnosed and fall back locally.
- Build/runtime documentation exists in `docs/godot_build_and_runtime.md`.
- Godot validation script and Python scaffold tests.

## What Still Needs To Be Done

### 1. Main Menu Visual Parity

The Godot menu is functional, but it is not yet a faithful match for the classic Pygame menu.

Remaining work:

- Compare against the original menu screenshot and tune exact logo position, size, and spacing.
- Match button width, height, typography, hover state, and disabled state.
- Make desktop and web scaling feel intentional at 16:9, 4:3, ultrawide, and small browser windows.
- Continue expanding Options into final classic parity; richer video/audio/gameplay settings, resolution presets, and pause access now exist, but final layout polish remains.
- Continue adding the remaining Python/Pygame menu routes; the desktop dedicated gateway route now exists, but final player setup/server administration routes still need parity.

### 2. Server Browser Final Visual Parity

The Server Browser has real behavior now, but it still needs final visual and interaction polish.

Remaining work:

- Continue tuning table column widths, row heights, tab spacing, header styling, and scrollbar placement against the reference UI; first-pass named table dimensions now exist, but final visual parity still needs reference screenshot tuning.
- Continue improving hover, selected, disabled, loading, error, and empty states; table selection/focus, tab-specific empty messages, disabled connect/favorite/history actions, undo copy, visible table loading rows, and online-directory duplicate-refresh protection now exist, but final visual parity still needs tuning.
- Continue refining richer filters; passwordless, open-slot, sort controls, and persistence now exist, but final visual/interaction parity is still pending.
- Continue final Favorites and History polish; favorite removal, clear-history, empty-history disabled state, undo restore copy, history-backed favorite details, and missing-directory favorite fallback rows now exist, but final stale/deleted-server production semantics still need tuning.
- Continue password/connect modal polish; shared fatal error copy plus real gateway `invalid_password`, `authentication_failed`, `server_full`, `server_closed`, and `banned` responses now exist, but the final modal flow still needs production server feedback and visual polish.
- Test responsive behavior in the Godot web export size constraints.

### 3. Real Online Server Directory

The browser can load from HTTP, but the real service does not exist yet.

Remaining work:

- Promote the documented and client-validated server directory schema `1` into the real public service contract.
- Create or choose the real read-only HTTP endpoint; the gameplay WebSocket gateway exists, but the public directory service is still separate.
- Fill the real dev, staging, and production values for `application/config/server_directory_url_dev`, `application/config/server_directory_url_staging`, and `application/config/server_directory_url_production`; the client-side environment selection, Options controls, user persistence, and override path now exist.
- Continue improving directory diagnostics; timeout, one retry, HTTP result diagnostics, schema diagnostics, invalid URL diagnostics, invalid-payload fallback, and fallback messaging are implemented, but final user-facing copy still needs polish once the public service behavior is known.
- Replace the temporary directory-carried `auth_token` fixture path with production authentication/session semantics before exposing authenticated public servers.
- Keep the local JSON fallback for offline development.
- Later, add presence and latency updates through WebSocket or WebRTC-compatible infrastructure.
- Expand the new browser runtime QA from the served schema `1` fixture and first-pass cache/refresh header checks to production-like public directory behavior under real hosting.

### 4. Local Match Gameplay Fidelity

The Local Match is now playable as a prototype, but it is not yet Groundfire gameplay.

Remaining work:

- Continue improving the original-style terrain model until it fully matches Python `Landscape`; color interpolation, linked superblock fall/merge, first-pass terrain dropping, first-pass quake wiring, classic first/between quake timing, and looped quake rumble playback now exist, but exact edge cases and tuning still need fidelity work.
- Continue porting the full original tank state model; the Godot `TankState` now has movement, fuel, health, slope angle, launch origin/velocity, named round-start defaults, passive steep-slope sliding, slope-aware jump jets with in-air boost rotation, tuned airborne gravity, terrain-gap detachment, playable-bound edge stopping, airborne launch velocity inheritance, and classic-default accelerating gun controls with named default/bound constants and immediate release stop.
- Improve projectile physics, crater generation, and explosion damage fidelity; exact terrain segment collision, named projectile gravity, splash damage, and first-pass turn wind/gust effects are implemented, but collision edge cases, wind tuning, gravity tuning, and damage tuning are not final.
- Complete original weapon behavior; `WeaponInventory` now has Shell, Machine Gun, MIRV, Missile, and Nuke definitions, plus Machine Gun direct-hit tracer volley behavior with centralized ammo/volley/cooldown constants, a closer apex/five-fragment MIRV split with centralized ammo/fragment/spread constants and parent expiry, named fuel-limited Missile steering, and first-pass Nuke blast/whiteout tuning.
- Continue full round flow fidelity; turn ownership, wins, reset, and an initial post-round shop exist, but the final score/economy/shop presentation and balancing are not done.
- Add better AI decision logic; the first trajectory-search shell aiming pass, strategic weapon choice, and easy/normal/hard difficulty tuning exist, but final personality tuning is still pending.
- Continue camera behavior, zoom/framing, and map bounds; projectile lookahead and explosion shake now exist, but final original framing feel and tuning are not done.
- Bring over the final score, economy, shop, and end-of-round screen fidelity; a first playable shop/economy scaffold now exists.

### 5. Input And HUD Completion

Input and HUD are only at the first useful layer.

Remaining work:

- Polish controls configuration UI; `ControlSettings` persists keyboard and gamepad bindings, Options supports keyboard/gamepad capture, reset, cancel, default gamepad bindings, keyboard/gamepad conflict reporting, per-device gamepad profiles, and the controls list is scrollable.
- Polish mouse aiming support; pointer aiming, reticle drawing, and left-click firing now exist, but final cursor/reticle feel still needs tuning.
- Complete full controller/menu navigation polish; gamepad capture, controller-side capture cancellation, per-device profiles, pause/main-menu/server-browser focus neighbors and row selection, and first-pass shop focus neighbors now exist, but final focus-neighbor tuning across every screen is still pending.
- Build a complete weapon HUD; the current HUD now shows selected weapon, ammo, credits, core round values, full inventory chips, HP/fuel bars, angle/power gauges, score/economy chips, wind/quake status, a message strip, and classic-atlas weapon icons, but still needs final HUD art/styling.
- Show angle, power, wind, HP, player names, round messages, score, and shop state in the final visual style; the prototype HUD now groups those values into a production-shaped overlay, but final art direction and reference tuning are still pending.
- Expand pause/menu behavior; Local Match has a first overlay with resume focus, options access, restart round, main menu, and vertical focus neighbors, but still needs final styling and settings behavior that preserves the match context.

### 6. Networked Gameplay Adapter

The browser-safe online path now connects through WebSocket and a Python gateway scaffold, but it is not yet the production multiplayer runtime.

Remaining work:

- Continue freezing the live protocol shape for the Godot client and Python server; protocol metadata, gateway-side envelope/input-command validation, supported-version advertisement, client-side compatibility negotiation, snapshot/event schema metadata, and first schema documentation now exist, but the final full-server `match_snapshot` shape and future compatibility policy are still pending.
- Promote the WebSocket gameplay path beyond first-pass integration; Server Browser routes to Online Match, the Python gateway emits `MatchSnapshot` payloads, and Godot renders terrain/entities/projectiles/effects/players with interpolation and prediction, but fidelity and reconciliation are still early.
- Optionally keep UDP transport for desktop-only builds.
- Finish production-grade failure flows; reconnect/backoff, manual reconnect/back controls, latency display, ack pruning, stale pending-input diagnostics, closed-connection reporting, first-pass fatal password/auth/full-server/closed-server/ban handling, optional gateway password rejection, optional directory-carried gateway auth-token rejection, optional gateway capacity rejection, optional closed-join mode, and optional player-name ban rejection exist, but final retry policy, production error taxonomy, durable authentication/session model, production ban persistence/administration, production capacity semantics, and user recovery paths still need polish.
- Adapt the full `groundfire.server` runtime to the browser-safe gateway; the gateway currently drives the shared Python simulation scaffolds, not the complete classic server runtime.
- Expand compatibility tests between the Python gateway/server and Godot message contract; gateway tests now cover hello, join, input, ping, errors, replicated tank movement, terrain revision, events, and a real TCP/WebSocket handshake/framing round trip, but browser-level end-to-end gameplay tests are still missing.

### 7. Export And Runtime Validation

The project validates in editor/headless mode, runs runtime scene smoke checks, documents the build/runtime path, produces local Linux/Web exports through `scripts/export_godot.sh`, packages first-pass release artifacts, and has browser screenshot QA. Final release hardening is still pending.

Remaining work:

- Promote `scripts/package_godot_release.sh` into the official release/tag process; version sourcing, release notes metadata, checksums, and versioned artifact names now exist, but CI invocation and publishing policy are not finalized.
- Expand browser-driven QA beyond the current runtime fixture to exercise production directory cache behavior under real hosting and user-visible recovery flows.
- Add approved `docs/references/godot_visual/` goldens with a capture backend that can read viewport pixels; `scripts/validate_godot_visuals.sh` now fails cleanly under the current dummy headless renderer when viewport capture is unavailable. Then decide whether `--check` should join default validation or remain an optional pre-release visual gate.
- Add CI/release-gate coverage for `scripts/qa_godot_web.sh` where Chromium/Chrome and export templates are available.
- Validate desktop build behavior manually or with a windowed smoke harness for LAN/server tools beyond the deterministic feature matrix.
- Promote the documented release verification, checksum, signing, hosting, and distribution policy into the final CI/release checklist once publishing infrastructure is chosen.

## Recommended Next Large Batch

The next big but controlled batch should focus on `Local Match Fidelity 2`:

1. Continue the `Landscape.clip_slice` fidelity pass by matching remaining clipping, landing, and edge cases against the Python implementation.
2. Continue controller polish with final focus-neighbor tuning across all menus and final menu navigation passes.
3. Continue improving Online Match interpolation quality, replicated projectile fidelity, prediction, and HUD polish; first-pass prediction and network diagnostics now exist.
4. Continue tuning landing edge cases and final gun angle/power default/bound values against the original Python/C++ feel; classic gun acceleration/release-stop, named gun defaults/bounds, passive steep-slope sliding, slope-aware jump jet thrust, in-air boost rotation, tuned airborne gravity, terrain-gap detachment, playable-bound edge stopping, and tank-owned projectile launch velocity inheritance now exist.
5. Continue tuning Nuke beyond the first whiteout pass, tune Machine Gun from cooldown-spaced volley toward full continuous hold/unselect behavior, and keep tuning MIRV/Missile details beyond the current apex/five-fragment split and fuel-limited steering.
6. Replace the first shop scaffold with faithful end-of-round, score, economy, and shop screens.

Avoid mixing this with the full online protocol or final release hardening in the same batch. Those should come after the local gameplay loop is stronger.
