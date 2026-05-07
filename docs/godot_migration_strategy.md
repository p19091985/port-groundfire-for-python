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
- Groundfire menu assets copied into `godot/assets/`.
- Shared `GroundfireTheme` script for colors, panels, buttons, and field styling.
- `ServerDirectory` read-only browser model with browser-safe online entries and desktop-only LAN entries.
- `godot/data/server_directory.json` as the temporary data source until HTTP/WebSocket is connected.
- Godot runtime validation script for server directory filtering.
- Server browser row selection and staged connect target status.
- Server browser filters, favorites/history, password dialog, and functional refresh/connect actions.
- Browser-safe `user://` persistence for favorites and history via `BrowserStore`.
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
- Local Match camera scaffold with minimum world size, smooth framing of tanks/projectiles/explosions, projectile lookahead, explosion shake, mouse-to-world aiming, zoom, and map bounds.
- Options gamepad capture can now be cancelled from the controller with Back/Select as well as from keyboard cancel.
- Local Match projectile/terrain collision now uses exact segment intersection against terrain chunks, matching the Python `ground_collision` direction more closely than fixed-step sampling.
- Godot validation now includes a runtime terrain collision smoke test for vertical, clear-air, and diagonal shots.
- Terrain chunks now carry interpolated per-side colors through crater clipping, fall as linked superblocks, and merge/link when resting against lower chunks.
- Options now includes video/audio/gameplay settings beyond FPS/audio: fullscreen, VSync, master volume, screen shake, camera smoothing, and mouse aiming.
- Local Match reads gameplay options at runtime for camera shake, camera smoothing, and mouse aiming.
- Server Browser now has richer client-side filters for passwordless servers, open slots, and sortable latency/name/player-count views.
- Local Match AI now chooses first-pass strategic weapons based on distance, line of sight, player health, trajectory miss distance, and available ammo.
- Machine Gun ammo now consumes a volley per firing action instead of spending one round for a full burst.
- Control rebinding now has selectable gamepad profiles for all gamepads or a connected device-specific profile.
- Local Match pause now includes Options access and explicit vertical focus neighbors for controller/keyboard navigation.
- Mouse aiming now has a world-space reticle and left-click fire path.
- Local Match HUD now draws player/enemy HP bars, fuel bar, player names, and first-pass weapon icons.
- WebSocket transport now reports closed connection attempts reliably and exposes connection state/last sequence for higher-level UI.
- Online Match now has reconnect/backoff UI, periodic ping latency, acknowledged-command tracking, pending-input diagnostics, terrain revision/tick diagnostics, and first-pass local tank prediction.

## Current Status

The Godot client now has a usable migration scaffold instead of only placeholder screens.

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
- Options now persists fullscreen, VSync, master volume, screen shake, camera smoothing, and mouse aiming.
- Local Match applies persisted camera shake, camera smoothing, and mouse aiming settings.
- Server Browser filters now include passwordless-only, open-slot-only, and latency/name/player-count sorting.
- Enemy AI can choose Shell, Machine Gun, MIRV, Missile, or Nuke based on first-pass tactical scoring and available ammo.
- Machine Gun firing now spends volley ammo to match the burst behavior more closely.
- Options now exposes gamepad profile selection and stores per-device gamepad bindings when a connected device profile is selected.
- Pause overlay now has Options access and explicit focus neighbors for stable controller/keyboard navigation.
- Mouse aim now updates a world reticle and supports left-click firing.
- Local Match HUD now has first-pass visual weapon icons and separate bars for player HP, enemy HP, and fuel.
- WebSocket transport exposes connection state and sequence tracking.
- Online Match now reconnects with exponential backoff, displays latency/ack/pending/tick/terrain diagnostics, prunes acknowledged commands, and applies local prediction to the player's replicated tank.
- Linux desktop and web export preset scaffold.
- Godot validation script and Python scaffold tests.

## What Still Needs To Be Done

### 1. Main Menu Visual Parity

The Godot menu is functional, but it is not yet a faithful match for the classic Pygame menu.

Remaining work:

- Compare against the original menu screenshot and tune exact logo position, size, and spacing.
- Match button width, height, typography, hover state, and disabled state.
- Make desktop and web scaling feel intentional at 16:9, 4:3, ultrawide, and small browser windows.
- Continue expanding Options into final classic parity; richer video/audio/gameplay settings and pause access now exist, but resolution presets and final layout polish remain.
- Add the missing menu routes that still exist only in the Python/Pygame client.

### 2. Server Browser Final Visual Parity

The Server Browser has real behavior now, but it still needs final visual and interaction polish.

Remaining work:

- Tune table column widths, row heights, tab spacing, header styling, and scrollbar placement against the reference UI.
- Improve hover, selected, disabled, loading, error, and empty states.
- Continue refining richer filters; passwordless, open-slot, and sort controls now exist, but final parity and persistence are still pending.
- Make Favorites and History behavior match the expected game flow.
- Finalize password/connect modal interaction and error messages.
- Test responsive behavior in the Godot web export size constraints.

### 3. Real Online Server Directory

The browser can load from HTTP, but the real service does not exist yet.

Remaining work:

- Finalize the production server directory JSON schema; the client now documents the expected first schema shape.
- Create or choose the real read-only HTTP endpoint; the gameplay WebSocket gateway exists, but the public directory service is still separate.
- Configure `application/config/server_directory_url` for dev, staging, and production.
- Continue improving directory diagnostics; timeout, one retry, HTTP result diagnostics, and fallback messaging are implemented.
- Keep the local JSON fallback for offline development.
- Later, add presence and latency updates through WebSocket or WebRTC-compatible infrastructure.

### 4. Local Match Gameplay Fidelity

The Local Match is now playable as a prototype, but it is not yet Groundfire gameplay.

Remaining work:

- Continue improving the original-style terrain model until it fully matches Python `Landscape`; color interpolation and linked superblock fall/merge now exist, but exact edge cases still need fidelity work.
- Continue porting the full original tank state model; the Godot `TankState` now has movement, fuel, health, slope angle, launch origin, jump jets, airborne gravity, and accelerating gun controls.
- Improve projectile physics, crater generation, and explosion damage fidelity; exact terrain segment collision and splash damage are implemented, but collision edge cases and damage tuning are not final.
- Complete original weapon behavior; `WeaponInventory` now has Shell, Machine Gun, MIRV, Missile, and Nuke definitions, plus first-pass Machine Gun burst with volley ammo, MIRV split, Missile steering, and Nuke blast tuning.
- Continue full round flow fidelity; turn ownership, wins, reset, and an initial post-round shop exist, but the final score/economy/shop presentation and balancing are not done.
- Add better AI decision logic; the first trajectory-search shell aiming pass and strategic weapon choice exist, but personality/difficulty tuning is still pending.
- Continue camera behavior, zoom/framing, and map bounds; projectile lookahead and explosion shake now exist, but final original framing feel and tuning are not done.
- Bring over the final score, economy, shop, and end-of-round screen fidelity; a first playable shop/economy scaffold now exists.

### 5. Input And HUD Completion

Input and HUD are only at the first useful layer.

Remaining work:

- Polish controls configuration UI; `ControlSettings` persists keyboard and gamepad bindings, Options supports keyboard/gamepad capture, reset, cancel, default gamepad bindings, keyboard/gamepad conflict reporting, per-device gamepad profiles, and the controls list is scrollable.
- Polish mouse aiming support; pointer aiming, reticle drawing, and left-click firing now exist, but final cursor/reticle feel still needs tuning.
- Complete full controller/menu navigation polish; gamepad capture, controller-side capture cancellation, per-device profiles, and pause/main-menu focus neighbors now exist, but final focus-neighbor tuning across every screen is still pending.
- Build a complete weapon HUD; the current HUD now shows selected weapon, ammo, credits, core round values, full inventory chips, HP/fuel bars, and first-pass drawn weapon icons, but still needs final art/styling.
- Show angle, power, wind, HP, player names, round messages, score, and shop state in the final visual style; the prototype HUD already shows the first core values and player names.
- Expand pause/menu behavior; Local Match has a first overlay with resume focus, options access, restart round, main menu, and vertical focus neighbors, but still needs final styling and settings behavior that preserves the match context.

### 6. Networked Gameplay Adapter

The message contract exists, but no real online gameplay path is connected yet.

Remaining work:

- Decide the live protocol shape for Godot client to Python server.
- Complete WebSocket gameplay integration; Server Browser routes to Online Match, the Python gateway emits `MatchSnapshot` payloads, and Godot renders terrain/entities/projectiles/effects/players with first-pass interpolation.
- Optionally keep UDP transport for desktop-only builds.
- Add reconnect/backoff UI and full error handling; hello, join, input, ping, disconnect, parsing helpers, Server Browser status reporting, Online Match reconnect/backoff, latency display, ack pruning, and pending-input diagnostics now exist, but final production-grade failure flows still need polish.
- Adapt the full `groundfire.server` runtime to the browser-safe gateway; the gateway currently drives the shared Python simulation scaffolds, not the complete classic server runtime.
- Expand compatibility tests between the Python gateway/server and Godot message contract; gateway tests now cover hello, join, input, ping, errors, replicated tank movement, terrain revision, and events.

### 7. Export And Runtime Validation

The project validates in editor/headless mode, but final desktop/web export work is still pending.

Remaining work:

- Complete Godot export presets with installed export templates and final release options.
- Validate the web build with browser storage, HTTP server list loading, and disabled desktop-only features.
- Validate desktop build behavior with LAN/server features visible.
- Add screenshots or automated smoke checks for Main Menu, Server Browser, Options, and Local Match.
- Document how to build and run both targets.

## Recommended Next Large Batch

The next big but controlled batch should focus on `Local Match Fidelity 2`:

1. Continue the `Landscape.clip_slice` fidelity pass by matching remaining clipping, landing, and edge cases against the Python implementation.
2. Continue controller polish with final focus-neighbor tuning across all menus and final menu navigation passes.
3. Continue improving Online Match interpolation quality, replicated projectile fidelity, prediction, and HUD polish; first-pass prediction and network diagnostics now exist.
4. Tune jump jets, airborne gravity, and gun acceleration against the original Python/C++ feel.
5. Replace the first-pass Machine Gun, MIRV, Missile, and Nuke behaviors with faithful entity ports and final AI difficulty/personality tuning.
6. Replace the first shop scaffold with faithful end-of-round, score, economy, and shop screens.

Avoid mixing this with the full online protocol or final web export in the same batch. Those should come after the local gameplay loop is stronger.
