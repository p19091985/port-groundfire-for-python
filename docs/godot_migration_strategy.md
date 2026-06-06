# Groundfire Godot Migration Strategy

This migration keeps the current Python/Pygame version alive while a Godot client is built in parallel.

This is the single Markdown source of truth for the Godot migration. Keep strategy, current status, validation, build/runtime notes, release walkthroughs, WebSocket protocol details, and server-directory schema updates here instead of creating new migration Markdown files under `docs/`. The image folders under `docs/references/` are fidelity assets used by tests and review, not separate narrative migration documents.

## Document Map

- `Decision` and `Web Feature Rule`: platform direction and browser safety boundaries.
- `Migration Fidelity Contract`: non-negotiable Pygame parity rule for agents implementing Godot work.
- `Agent Migration Loop`: mandatory repeatable workflow for agents continuing the migration.
- `First Migration Slice`: chronological migration log for implemented Godot work.
- `Current Status`: implemented/started behavior and remaining migration work by area.
- `Recommended Next Large Batch`: next controlled implementation batch.
- `Next Agent Handoff`: immediate continuation instructions for another agent taking over.
- `Consolidated Migration Reference`: validated release-slice walkthrough, validation, build/export/package, QA, fidelity gate, protocol, and server-directory contracts.

## Documentation Maintenance Rule

- Add new Godot migration notes to this file.
- Keep browser QA screenshot goldens under `docs/references/godot_browser_visual/`; these are regression captures of the current Godot web build, not proof of classic fidelity by themselves.
- Keep authoritative Python/Pygame visual references under `docs/references/pygame_visual/`, generated from the GitHub-tracked Pygame client with `scripts/capture_pygame_references.py`.
- Do not add new standalone migration Markdown files unless the migration strategy is intentionally split again. Release walkthroughs, agent handoffs, protocol notes, runtime notes, QA notes, and remaining-work notes all belong in this file.
- If an agent creates temporary migration notes while working, fold the durable content back into this file and remove the temporary note before handoff.
- When code changes add or remove migration behavior, update `First Migration Slice`, `Current Status`, and the relevant reference section in the same change.

## Migration Fidelity Contract

This is a preservation migration. User experience cannot be changed by the migration. The Python/Pygame client is the behavioral, visual, input, audio, timing, and flow source of truth for every Godot implementation item unless this file explicitly calls out a browser/platform limitation from the `Web Feature Rule`.

When an agent consults this file to implement Godot work, every task inherits this contract:

- Match the player-facing Pygame behavior first; architecture, engine APIs, and internal data shapes may change only behind the same user experience.
- Start from the Pygame source, original assets, and captured references before writing Godot code.
- Treat `docs/references/pygame_visual/` and the Python/Pygame code under `src/` as the fidelity target. Godot browser goldens are regression captures, not fidelity targets.
- Preserve menu flow, copy, layout proportions, controls, timing, physics feel, audio cues, scoring/economy semantics, multiplayer-visible states, and error/recovery behavior for supported platforms.
- If web or Godot runtime constraints require a platform adaptation, document it under `Allowed Godot adaptation:` before implementing and keep the player-facing outcome as close as possible to Pygame.
- Every migration implementation batch must name its Pygame reference, user-visible invariants, allowed Godot adaptation, and required validation before code is treated as complete.
- Run `scripts/validate_godot_migration_contract.py` and the relevant fidelity/visual checks before marking migration work done.

### Fidelity Annotation Template

Use these labels in every pending migration area and in new migration notes:

- `Fidelity target:` Pygame code, original asset, captured reference, protocol, or behavior being copied.
- `User-visible invariants:` What the player/admin must experience the same way after migration.
- `Allowed Godot adaptation:` Browser/platform/engine constraint that may change internals while preserving the user-facing outcome.
- `Required validation:` Automated test, screenshot comparison, manual reference pass, or command that proves the invariant.

## Agent Migration Loop

Any agent continuing the Godot migration must work in this loop until the user stops the work, the current task is genuinely blocked, or every named remaining migration item has been closed with validation:

1. Re-read this file, especially `Migration Fidelity Contract`, `What Still Needs To Be Done`, `Recommended Next Large Batch`, and `Next Agent Handoff`.
2. Inspect `git status --short` before editing and preserve unrelated user/agent changes.
3. Pick one narrow fidelity target from this document. Name the Pygame reference, user-visible invariants, allowed Godot adaptation, and required validation before treating the patch as complete.
4. Inspect the Python/Pygame source, original assets, and `docs/references/pygame_visual/` before changing Godot behavior.
5. Implement only that narrow migration step in the Godot/Python bridge needed for parity.
6. Add or extend the closest regression test. Prefer executable fidelity coverage over prose; use manual visual review only when automation cannot yet observe the behavior.
7. Run the required validation for the touched surface: always include `scripts/validate_godot_migration_contract.py`; use `scripts/validate_godot_fidelity.sh` for gameplay/client parity; use `CI=1 .venv/bin/python scripts/run_quality_checks.py` when shared Python, gateway, launcher, release, or CI code changes; use browser visual QA when pixels, browser runtime, or web export behavior change.
8. If validation fails, fix the implementation or document a precise blocker in this file before stopping. Do not hand off a vague "needs testing" state.
9. Return the migration state to this file in the same patch: update `First Migration Slice`, `Current Status`, `What Still Needs To Be Done`, `Recommended Next Large Batch`, `Next Agent Handoff`, or the relevant reference section so the next agent can continue without reading chat history.
10. Repeat from step 2 for the next narrow target.

Never leave durable migration knowledge only in a conversation, local notes, release log, or deleted document. This file is the handoff.

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
- Groundfire menu, weapon icon, quake, fire-shell, missile-launch, missile-flight, Machine Gun, and Nuke audio assets ported into `godot/assets/`.
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
- Main menu now has a first Local Match setup route before gameplay, with explicit Human/Computer slots and classic-style 5-to-50 round selection passed into `LocalMatch`.
- Main menu now has a tighter classic visual metric pass: logo sizing preserves the source aspect ratio with reference min/max bounds, menu buttons use named min/max dimensions across viewport scales, and focused buttons share the hot accent state with hover/pressed styling.
- Main menu button stacking now removes the extra Godot-only top inset inside the classic black panel, keeping the Start/Find/Options/Quit rows closer to the Pygame `MainMenu.draw()` panel geometry.
- Options now has a classic preset block before the modern scrollable settings: Pygame-style `Resolution:` and `Screen Mode:` brown selector rows, a `Set Controls` jump into bindings, and classic-width `Apply`/`Back` actions while preserving the richer Godot settings below.
- Classic Main Menu and Options text now has a shared Pygame-style shadow/outline pass on title/copy labels, classic preset labels, and classic buttons, with classic button hover/pressed text switching to yellow like `TextButton`/`Selector` highlights.
- Local Match setup now has first-pass roster fields for up to eight slots: active toggles, editable names, Human/Computer assignment, unique human controller selection, sanitized empty-name fallbacks, and configured names carried into the HUD, score table, and final result overlay.
- Local Match setup focus now recalculates when roster rows change, skipping inactive names/slots and computer-only controller fields while keeping active toggles reachable.
- Local Match now materializes the configured roster as participant state so combat, score/final-result tables, and the shop all operate on the same configured participants instead of only the first duel pair.
- Local Match HUD now receives active-target and roster summary fields, so multi-combatant matches show the current target and alive/leader context instead of only hardcoded duel labels.
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
- Initial jump jet/airborne tank behavior with classic looped jump-jet audio, mouse aiming, weapon previous/next actions, and credits display.
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
- Local Match now has a first separate score overlay between round end and shop, awarding the round reward once before the player continues into purchases.
- Local Match score overlay now starts matching the classic score screen shape with ordered player/enemy rows, rank/tie labels, `Player / Scoring for Round / Total Score` columns, translucent per-row column boxes, white total-score text, player tank icons, defeated-player detail, defeated-player tank icons with leader flags, and enemy score tracking for local ranking.
- Local Match end-of-round scoring now has a first classic parity pass for defeat rewards, leader-defeat bonuses, self-defeat penalty, survivor bonus, and per-round money stipend before the shop opens.
- Local Match now carries the classic leader flag between rounds: leader-defeat scoring checks the previous score-screen leader state, and the next leader is assigned when the score overlay advances into shop/final flow.
- Local Match final-result winner snapshots now mark winners from the final top score instead of reusing the between-round leader flag, so tied final winners are surfaced like the classic `WinnerMenu`.
- Local Match final-result overlay now restores the classic separate `Final Result` heading above the winner/tie message.
- Local Match final-result overlay now uses the classic winner-only card layout over the scrolling tiled `menuback.png` menu background, matching `Menu.update_background()` at speed `0.1`, showing each top-score winner with name, a tank-shaped color chip, and white rotating `Winner!` letters paced like the classic `WinnerMenu`; winner rows are centered and grouped in classic batches of up to four, with no added modal panel, ranking table, summary line, or visible exit button.
- Local Match now advances from the final-round score overlay into a first winner/final-result overlay instead of opening another shop, with winner-only cards, winner/tie copy, and a direct main-menu exit.
- Local Match score and final-result overlays now honor the classic activation delay: human matches wait 2 seconds before accepting Continue/Main Menu input, while computer-only flows use the 4-second automatic advance path.
- Local Match shop now honors the classic shop input cadence with a short first-action delay and repeat delay after buy/Done attempts, preventing held confirm/navigation input from immediately double-purchasing or skipping the shop.
- Local Match shop purchases now use classic-style bundle sizes separate from round-start ammo: Machine Gun +50, MIRV +1, Missile +5, and Nuke +1, with the shop UI showing the pack size per item.
- Local Match shop now includes the remaining classic catalog rows for Rolling Mines, Airstrike, Death's Head, Hover Coil, and Corbomite as purchasable first-pass items instead of disabled placeholders.
- Local Match shop rows now restore a separate classic-style `$cost` column for both purchasable weapons/items and disabled legacy catalog rows instead of burying cost only in the buy action text.
- Local Match shop display names now match the classic catalog copy for plural weapon rows (`Mirvs`, `Missiles`, `Nukes`) while preserving internal weapon identifiers for inventory and buy actions.
- Local Match shop purchase buttons now use a plain `Buy` action label while the price lives in the separate `$cost` column, reducing duplicated cost copy and matching the classic catalog layout more closely.
- Local Match shop now presents shopper money in the classic `$N` format and uses `$` in insufficient-funds messages, while leaving the internal credits/economy model unchanged.
- Local Match shop now has a closer Jump Jet purchase path: buying Jump Jet spends 50 credits, increases the player's persistent fuel reserve by one classic fuel unit, starts later rounds with active fuel clamped to 100%, and spends reserve alongside active fuel.
- Local Match HUD/shop economy presentation now surfaces fuel reserve explicitly, with the HUD score/economy chip row and shop credit line both showing the persistent reserve percent.
- Local Match shop now shows the upcoming round as `Round N of Total` between rounds, matching the classic inter-round flow more closely than the earlier current-round label.
- Computer-controlled Local Match participants now auto-shop between rounds with difficulty-specific purchase priorities, including tested Easy partial Machine Gun/Missile purchasing without Jump Jet when funds run out, tested Normal Missile/MIRV purchases, tested Hard full-priority Nuke/MIRV/Missile/Machine Gun/Jump Jet purchasing, and tested saved-credit behavior when funds are insufficient, so visible shop flow stays focused on human players while bot credits still feed weapon/fuel economy.
- Local Match AI now chooses shell shots by simulating candidate angle/power arcs against current wind, terrain, and player position instead of using only a distance-based random shot.
- Local Match now has a first-pass turn wind model with bounded wind shifts, per-shot gust influence, AI trajectory simulation using effective wind, and directional HUD wind text.
- Local Match camera scaffold with minimum world size, smooth framing of tanks/projectiles/explosions, projectile lookahead, explosion shake, mouse-to-world aiming, zoom, and map bounds.
- Options gamepad capture can now be cancelled from the controller with Back/Select as well as from keyboard cancel.
- Local Match projectile/terrain collision now uses exact segment intersection against terrain chunks, matching the Python `ground_collision` direction more closely than fixed-step sampling.
- Local Match terrain collision now also detects collinear projectile traces along chunk edges and zero-length/boundary starts, covering glancing edge shots that were previously skipped by parallel segment handling.
- Local Match direct projectile/tank impacts now resolve the first tank intersected, apply full direct-hit damage before splash falloff, update the shot owner for turn flow, and track player/enemy damage score symmetrically.
- Godot validation now includes a runtime terrain collision smoke test for vertical, clear-air, and diagonal shots.
- Terrain chunks now carry interpolated per-side colors through crater clipping, fall as linked superblocks, and merge/link when resting against lower chunks.
- TerrainModel now has a first-pass classic `drop_terrain` path with the same minimum-land clamp used by the Python `Landscape.drop_terrain`, preparing the quake/drop fidelity pass.
- TerrainModel falling superblocks now resolve left and right landing gaps independently and apply fall speed before accelerating for the next frame, matching more Python `Landscape.update` edge cases where one side can rest while the other side keeps falling toward uneven terrain.
- TerrainModel falling superblocks now inherit a still-falling support chunk's motion after landing, keeping linked chunks moving together instead of opening a same-frame gap.
- TerrainModel crater clipping now handles a first linked-support cut case closer to Python `Landscape.clip_slice`: cutting support beneath a linked cap detaches the upper remainder, starts it falling, and propagates existing superblock motion to the lower remainder when the support was already moving.
- TerrainModel crater clipping now also carries over the linked-removal top propagation rule from Python `Landscape.clip_slice`, so deleting a linked chunk promotes its former top edge onto the following chunk before later clipping continues.
- TerrainModel crater clipping now clamps blast removal at the classic `MIN_LAND_HEIGHT` floor for chunks that extend below the floor, preserving the deep base instead of splitting it below the original terrain limit.
- TerrainModel crater clipping now preserves another classic falling split case: splitting an already falling chunk starts the detached upper cap on a fresh fall pause while the lower remainder inherits the source superblock motion, with a named Python `Landscape.clip_slice` reference regression and matching GDScript assertion.
- Local Match now wires a first-pass quake/drop event into the round loop, using timed terrain dropping, camera shake, and HUD quake status.
- Local Match now uses the classic first/between quake timing and plays the classic quake rumble as a looped Godot `AudioStreamPlayer`, pausing with the match and stopping cleanly when the quake ends or the round flow changes.
- Local Match tank damage now follows the classic exact-zero-health rule and round-over detection uses tank state instead of raw `health <= 0`.
- Local Match dead tanks now arm the classic `Tank.burn()` exhaust timer on death and emit smoke particles using the Python ground/air release, offset, velocity, rotation, growth, and fade constants, rendered through the classic `data/smoke.png` texture ported to `godot/assets/smoke.png`.
- Options now includes video/audio/gameplay settings beyond FPS/audio: fullscreen, VSync, master volume, screen shake, camera smoothing, and mouse aiming.
- Options now groups the scrollable settings into first-pass classic-style panels for Video, Audio, Gameplay, Online, and Controls, improving scanability while preserving existing keyboard/controller focus traversal.
- Local Match reads gameplay options at runtime for camera shake, camera smoothing, and mouse aiming.
- Server Browser now has richer client-side filters for passwordless servers, open slots, and sortable latency/name/player-count views.
- Local Match AI now chooses first-pass strategic weapons based on distance, line of sight, player health, trajectory miss distance, and available ammo.
- Local Match AI special-weapon choice now uses a first risk/reward projection for expected player damage, self-damage, kill bonus, difficulty thresholds, and Nuke/MIRV/Missile candidate gates instead of distance/health checks alone.
- Machine Gun now uses a closer classic direct-hit tracer volley: ammo is consumed per firing action, bullets draw line traces, fire with the classic 0.1s spacing, deal direct tank damage, and expire on terrain without cratering or splash damage.
- Machine Gun round ammo, volley size, and shot spacing now live behind `WeaponInventory` constants used by both ammo consumption and Local Match firing.
- Player-fired Machine Gun now has an incremental held-fire path: holding fire spawns one tracer per classic `0.1s` cooldown and spends ammo one bullet at a time, while the older fixed-volley helper remains for tests/AI scaffolding.
- Enemy Machine Gun firing now uses the same staged one-bullet-per-cooldown path with an AI burst budget, avoiding the previous up-front ammo spend for the whole volley.
- Machine Gun firing now has a dedicated looping Godot `AudioStreamPlayer` using the classic `machinegun.wav`, with clean pause/resume and stop handling when held fire ends, ammo runs out, the AI burst ends, or the sequence resets.
- Shell, MIRV, and Nuke launches now play the classic `fireshell.wav` one-shot, while Missile launches play `launchmissile.wav` and loop the powered-flight `missile.wav` until fuel expires or the missile explodes, with pause/resume and reset/exit cleanup alongside the other Local Match audio nodes.
- Player Machine Gun now handles weapon-cycle unselect while held fire is active, stopping the hold/audio without deleting already-fired tracer rounds and selecting the next available weapon.
- Enemy Machine Gun now has first-pass tactical hold budgets by AI difficulty, with shorter Easy bursts, longer Hard bursts, and an extended low-health finisher burst instead of a single fixed burst size.
- Machine Gun firing now honors the classic selected-weapon cooldown before the first tracer: player and enemy firing start the looped sound/held-fire state immediately, but ammo is not spent and no tracer is emitted until the `0.1s` cooldown crosses below zero, with sub-frame delay carried into the tracer update.
- Machine Gun pre-shot cancellation now returns immediately to the player's aim turn when the player unselects before the first tracer, preserving the newly selected weapon and leaving ammo/projectiles untouched.
- Machine Gun lethal hits now stop held/AI firing immediately, stop the looped audio, expire queued tracer rounds, and hand control to the normal round-over score flow instead of continuing to spend ammo after a tank is destroyed.
- Machine Gun direct-hit resolution now ignores the firing tank and has a full-roster regression covering third-participant hits, score, credits, and display names.
- Machine Gun tracer launch velocity now uses a fixed classic weapon power (`MachineGunWeapon.OPTION_Speed = 25`) instead of the tank's current gun power, with paired Python/Godot regressions covering power-independent velocity.
- Machine Gun tracer stepping now uses the same Godot projectile gravity scale as shells, matching the Python `MachineGunRound.update()`/`Shell.update()` parabolic `5.0 * t^2` source formula instead of zero-gravity straight traces.
- Machine Gun tracer line tails now use the classic `0.01s` back-time window from Python `MachineGunRound.update()` instead of stretching to the previous rendered frame.
- Machine Gun tracer positions now derive from stored launch origin, launch velocity, and active age, mirroring Python `MachineGunRound.update()`'s launch-time formula instead of accumulating frame-by-frame position drift.
- Limited-ammo weapons now return selection to Shells when the active weapon is depleted, matching `Tank.update_gun()`'s fallback after `Weapon.fire()` returns false; Machine Gun held fire consumes named Machine Gun ammo so an empty burst cannot spend Shells or the next available weapon.
- MIRV now splits closer to the classic behavior: apex-timed split, five configurable fragments, and horizontal spread with vertical velocity reset.
- MIRV round ammo, fragment count, horizontal spread, and minimum split age now live behind named constants used by both inventory data and Local Match split behavior.
- MIRV split now expires the original parent projectile after spawning fragments, leaving only the fragment shells active after the split.
- MIRV split now computes the exact split position and velocity inside the frame that crosses the apex instead of spawning fragments from the previous frame position.
- MIRV fragments spawned during a projectile update no longer advance an extra full frame on the split tick, preserving the computed split point for same-frame apex crossings.
- MIRV fragment horizontal spread now follows Python `Mirv.update()` exactly: it scales from the launch x velocity, so vertical MIRV shots split into vertically stacked fragments instead of injecting a minimum fan-out speed.
- Missile now has a first-pass classic steering model with launch angle, fuel, steer acceleration, player aim-input steering, simple enemy steering, and ballistic fall after fuel is spent instead of direct homing.
- Missile steering now uses named Local Match constants for angle-change clamp, recentring rate, and AI steer scale.
- Missile powered-flight velocity now uses the Pygame/Python `Missile.update()` formula `Missile.OPTION_Speed - cos(angle)`, scaled into Godot pixels and left unclamped, instead of preserving the tank gun launch velocity while fuel remains.
- Missile fuel exhaustion now preserves the Pygame `Missile.update()` ordering: the frame that crosses below zero fuel still uses powered-flight velocity, and ballistic gravity starts on the following update.
- Nuke now carries the classic `white_out` weapon flag into Local Match explosions, drawing a fullscreen white flash that fades at the Python `Blast` whiteout rate.
- Nuke explosions now play the classic `nuke.wav` through a dedicated one-shot Godot `AudioStreamPlayer`, with pause/resume and reset stop handling.
- Rolling Mines, Airstrike, Death's Head, Hover Coil, and Corbomite now have first-pass Local Match behavior and shop/catalog coverage: classic pack sizes, `add_ammo` purchases, real `_buy_shop_weapon` money/ammo/message paths for all five items, and insufficient-funds handling for Corbomite are protected, mines enter rolling state on terrain contact, Airstrike spawns five downward missiles, Death's Head carries split metadata and fragments, Hover Coil applies hover time to affected tanks, and Corbomite activates a reflective shield.
- Tank gun angle/power controls now use named classic default acceleration/max-speed constants and stop changing immediately when aim/power input is released.
- Jump jets now apply classic-style slope-aware thrust using the tank angle, with a separate horizontal component on inclined terrain and the Python default fuel usage rate.
- Boosting tanks now rotate in air with the classic left/right 90 degrees-per-second turn behavior and recover toward level when no turn input is held.
- Local Match jump jets now play the classic looped `jumpjets.wav` while boost input is valid for an alive tank with fuel, pause/resume with the match, and stop on release, invalid boost, phase changes, restart, or shutdown like Python `SoundEntity(..., 3, True)`.
- Local Match jump jets now also emit the classic boost exhaust smoke: `texture_id = 2`, `0.05s` exhaust cadence, no rotation/growth, `2.5` fade rate, and pre-thrust velocity derived from the current airborne velocity plus the tank-angle exhaust vector.
- Local Match projectiles now inherit the firing tank's airborne velocity, matching the classic `gun_launch_velocity` behavior for shots fired while using jump jets.
- Tank airborne gravity now uses a named constant aligned with the classic projectile/boost scale instead of the earlier oversized hardcoded fall acceleration.
- Tank passive steep-slope sliding now follows the classic signed `Tank.move_tank` direction: positive tank angles slide left and negative tank angles slide right, with a Python reference regression and matching GDScript assertion protecting the sign.
- Tank grounded left/right movement now combines player input with the signed slope-slide term like Python `Tank.move_tank`, so moving downhill is faster than moving uphill instead of using symmetric slope drag.
- Tank grounded and passive slope movement now projects the classic along-slope motion through `cos(tank_angle)` and has inclined-terrain Godot assertions for the matching visible `x`/`y` displacement.
- Tank grounded movement no longer spends active/reserve fuel; this matches Python `Tank.move_tank`, where `FuelUsageRate` is consumed by jump-jet boost rather than ordinary left/right movement.
- Tank airborne non-boost movement now ignores left/right commands in `move_on_terrain`; once airborne without boost, the tank keeps its stored velocity and fuel/reserve unchanged like Python `Tank.move_tank`.
- Tank round reset now leaves the tank initially ungrounded like Python `Tank.do_pre_round`, letting the normal terrain-settling pass establish contact instead of starting with a pre-confirmed ground state.
- Tank round reset now also starts with a level `0` tank angle like Python `Tank.do_pre_round`/`set_position_on_ground`, instead of immediately adopting the terrain slope before the normal ground-contact pass.
- Tank airborne terrain settling now preserves the current tank angle until landing, matching Python `Tank.update`/`move_tank` behavior where falling without boost does not snap chassis rotation to the terrain slope below.
- Tank gun angle and power now use the classic `-75..75` angle range, `0` upward default, `1..20` power range, and `10` default power, with an explicit pixel-scale conversion so Godot keeps playable projectile speed while exposing Pygame-style control values.
- `TankState` now names its round-start gun angle, gun power, health, and fuel defaults so final classic tuning can happen without hunting literals.
- Local Match projectile gravity now lives behind a named `PROJECTILE_GRAVITY` constant shared by AI trajectory search, MIRV apex timing, ballistic shells, and Machine Gun tracers.
- `TankState` now exposes `launch_velocity`, and Local Match player/enemy firing uses that tank-owned launch calculation instead of rebuilding the formula entirely in the scene script.
- `TankState.launch_origin` now uses a named classic-style tank center and gun offset, including tank-angle chassis displacement, with matching Godot assertions beside the Python `Tank.gun_launch_position` reference coverage.
- Local Match gun-arrow drawing now uses the same tank-center anchor as `TankState.launch_origin`; its shaft start, length, shaft width, and head width are derived from the classic `Tank.draw` `tank_size`/`gun_power` proportions, with GDScript assertions protecting the shaft/head geometry.
- `TankState` now detects when terrain drops too far beneath a grounded tank and switches back into airborne fall instead of snapping the tank down instantly.
- `TankState` now has named movement/fuel/slope constants and passively slides grounded tanks on steep slopes, matching another piece of the classic `move_tank` behavior.
- `TerrainModel` now exposes playable tank bounds, and `TankState` clamps airborne tanks to those bounds while clearing horizontal velocity at the edge.
- Control rebinding now has selectable gamepad profiles for all gamepads or a connected device-specific profile.
- Options now wires explicit keyboard/controller focus neighbors through the scrollable options and control-rebinding form, skipping disabled controls and self-looping button horizontal focus.
- Main Menu buttons now self-loop horizontal keyboard/controller focus while preserving the explicit vertical menu order.
- Local Match pause now includes Options access, explicit vertical focus neighbors, and horizontal self-loops for controller/keyboard navigation.
- Local Match pause Options now preserves the active match instance by detaching it while the Options screen is open and restoring it paused from the Options Back action.
- Local Match shop buttons now wire vertical focus neighbors across affordable buy actions and Continue for controller/keyboard navigation.
- Local Match shop buttons now also self-loop horizontal focus neighbors, preventing left/right controller input from escaping the active purchase list.
- Local Match setup now wires explicit horizontal focus neighbors for Start/Back plus round-selector focus return, and the score/final overlays self-loop their single action buttons while treating controller/keyboard cancel as the safe modal action.
- Server Browser now wires explicit keyboard/controller focus neighbors across filter controls, table rows/cells, action buttons, close/back, and the password modal; row focus selects servers, `ui_accept` connects, and `ui_cancel` closes the modal.
- Server Browser action focus now skips disabled actions such as Add Favorite and Connect before a row is selected, then rewires when selection/loading/history state changes.
- Optional mouse aiming now has a world-space reticle and left-click fire path, but it is disabled by default so the initial Local Match experience follows the keyboard/controller-focused Pygame behavior.
- Local Match HUD now draws player/enemy HP bars, fuel bar, player names, and weapon inventory icons from the classic `weaponicons.png` atlas.
- Local Match HUD now has a structured first-pass game layout with a turn/phase banner, active/target HP bars, angle and power gauges, score/credits/wins chips, wind/quake/roster status, a separate message strip, and responsive weapon inventory chips.
- WebSocket transport now reports closed connection attempts reliably and exposes connection state/last sequence for higher-level UI.
- Online Match now has reconnect/backoff UI, periodic ping latency, acknowledged-command tracking, pending-input diagnostics, terrain revision/tick diagnostics, and first-pass local tank prediction.
- Options now includes classic-style desktop resolution presets, persists the selected preset, and applies window size outside web/fullscreen builds.
- Server Browser now persists filter text, passwordless/open-slot toggles, and latency/name/player-count sort mode alongside favorites and history.
- Server Browser online directory refresh now has a first loading state that blocks duplicate refreshes, disables the Refresh All action, and restores normal action text on success or fallback.
- Server Browser table layout now uses named per-column widths and row/header heights instead of one fixed cell size for every column.
- Options now includes AI difficulty selection, and Local Match applies easy/normal/hard tuning to trajectory search precision, aim error, and strategic weapon use.
- Desktop-only Dedicated Server now has an initial Godot tool screen that can launch the local `groundfire-web-gateway` from `.venv` while staying hidden on web.
- The desktop-only Dedicated Server tool now exposes first-pass gateway administration controls for join password, auth token, max players, closed joins, and comma-separated banned player names, mapping them to the existing `groundfire-web-gateway` CLI flags.
- Dedicated Server gateway tools now track the launched process PID, prevent duplicate gateway launches, expose a Stop Gateway action, disable Stop until a process is tracked, and mask password/auth token fields in the Godot launcher.
- Dedicated Server gateway tools now show a browser-safe WebSocket connect endpoint, normalize wildcard bind hosts into a local copyable endpoint, include that endpoint in launch status, and expose a Copy Endpoint action.
- Dedicated Server gateway tools now persist non-sensitive launcher defaults under `user://groundfire_options.cfg` for host, port, max players, closed joins, and banned player names while intentionally leaving join password and auth token ephemeral.
- Dedicated Server gateway tools now show and copy a sanitized `groundfire-web-gateway` command preview for local debugging, masking join password/auth token values while preserving the effective CLI flags.
- Dedicated Server gateway tools now show a live join-policy summary for password/auth status, max-player cap, open/closed joins, and ban count before launch.
- Dedicated Server gateway action focus now skips disabled Stop Gateway and rewires when the launched process state changes.
- Main Menu logo, panel, button, margin, and stack spacing now use named 1024x768 reference metrics with bounded viewport scaling, giving 16:9, 4:3, ultrawide, and smaller browser windows a more intentional classic-menu baseline.
- GroundfireTheme now names the shared button font size plus normal, hover, disabled, and border colors, so button parity can be tuned centrally instead of hunting literal state colors.
- Local Match setup now gives clearer roster readiness copy with active, human, and computer counts, and explains when Start Match is blocked because fewer than two players are enabled or because no human player is active.
- Server Browser table scroll dimensions and horizontal/vertical scrollbar modes now use named constants, keeping future reference tuning for table width, height, and scrollbar behavior in one place.
- Online Match now exposes manual reconnect/back controls in addition to automatic reconnect/backoff diagnostics.
- Online Match reconnect/back controls now have explicit keyboard/controller focus wrapping, including vertical self-loops so focus stays in the header action row.
- `scripts/export_godot.sh` now validates the Godot project, reports missing templates with the official package URL, and runs Linux/Web export presets with the installed Godot 4.6.2 export templates.
- Linux/Web export presets now exclude `res://tests/*` from release artifacts while keeping tests available to headless validation.
- Platform capability rules now have deterministic desktop/web helpers so validation can assert hidden web features and visible desktop LAN/server tools without relying on the current export target.
- Godot validation now includes a runtime smoke test for Main Menu, Options, Server Browser, Local Match, Online Match controls, browser-safe HTTP directory parsing, and desktop/web capability visibility.
- The `Build And Runtime` section documents validation, Linux/Web export commands, generated outputs, local web serving, and platform expectations.
- Godot validation now includes local-match fidelity and online reliability checks in addition to the runtime scene smoke tests.
- `scripts/package_godot_release.sh` creates first-pass Linux/Web release artifacts, a manifest, and SHA256 checksums after export.
- `scripts/qa_godot_web.sh` exports the web build, serves it locally, captures browser screenshots through Chromium/Chrome DevTools, and compares them with `docs/references/godot_browser_visual/`.
- `scripts/capture_pygame_references.py` captures the GitHub-tracked Python/Pygame client at 1024x768 into `docs/references/pygame_visual/`, providing the visual fidelity source for Main Menu, Options, Server Browser, and Local Match.
- The first post-audit visual correction pass moves Godot away from the self-referential dark browser goldens by restoring the classic Pygame menu tile tint, brown translucent buttons, black translucent panels, main menu logo/version/copyright layout, full-viewport Local Match/Server Browser presentation, and the classic purple gameplay sky gradient.
- Local Match in-game presentation now has a first classic HUD correction pass: the large modern combat panel is replaced by Pygame-style top status cards using the original world-coordinate positions, health/fuel color formulas, tank swatches, and `weaponicons.png` atlas, and tank aiming now draws the translucent gun arrow on each living tank instead of the modern yellow aim line.
- Local Match HUD now exposes and validates the classic Pygame world-coordinate status-card geometry for the tank panel, HP/fuel bars, tank icon polygon, selected weapon placement, and health/fuel color formulas, so the in-game interface can keep matching the Python renderer instead of drifting through Godot-only layout tweaks.
- Browser QA now also runs exported-web runtime checks through `?qa=browser_runtime`, covering browser-safe favorites/history/filter persistence across seed/verify browser sessions, served schema `1` HTTP directory loading, first-pass directory cache/refresh headers, conditional `304 Not Modified`, HTTP status/header/body diagnostics, one retry for transient directory request failures, LAN/desktop-only feature hiding, invalid-directory fallback diagnostics, and Online Match fatal error handling against real local `groundfire-web-gateway` password, auth, full-server, closed-server, and banned-player rejections.
- Godot release packaging now derives the artifact version from `pyproject.toml` by default, supports release version/prefix overrides, and can attach release notes metadata to the manifest.
- The `Build And Runtime` section now documents release verification, mandatory checksum handling, current signing policy, browser hosting expectations, and distribution notes for Linux/Web artifacts.
- `scripts/validate_godot_visuals.sh` now exposes the headless Godot visual golden check with explicit `--check` and `--update-goldens` modes.
- Godot WebSocket messages and the Python gateway now carry protocol version metadata on hello, join, input, ping/pong, disconnect, errors, and snapshots, and the gateway rejects missing or mismatched protocol versions.
- The `WebSocket Protocol` section documents the first versioned WebSocket message schema, including first-pass `match_snapshot` and event schema sections; the Python gateway now advertises its supported protocol range and validates required fields, basic types, and the allowed input command set before dispatch.
- Online Match now waits for the gateway `hello`, verifies that the server-supported protocol list includes the Godot client protocol, handles pre-hello protocol errors, shows snapshot/event schema diagnostics, and disables automatic reconnect on protocol incompatibility.
- The `Server Directory Schema` section documents server directory schema `1`, and the Godot `ServerDirectory` parser now rejects invalid HTTP/local payloads before rendering entries.
- Server directory configuration now supports explicit URL overrides plus `dev`, `staging`, and `production` environment URL settings while preserving the local fallback JSON path.
- Options now exposes the server directory environment and override/dev/staging/production URLs, validates HTTP(S) directory URLs, persists them in `user://groundfire_options.cfg`, and applies them before the Server Browser loads entries.
- Online Match now classifies fatal server join/runtime errors such as invalid password, authentication failure, server full, and match not found, stops automatic reconnect for those cases, and shows a recovery-oriented status message.
- `groundfire-web-gateway` now has an optional first-pass join password gate through `--password` or `GROUNDFIRE_WEB_GATEWAY_PASSWORD`, advertises `password_required`, and emits `invalid_password` for rejected Godot joins.
- Godot `join` messages now support an optional `auth_token`, and `groundfire-web-gateway` can require it through `--auth-token` or `GROUNDFIRE_WEB_GATEWAY_AUTH_TOKEN`, advertise `auth_required`, and emit `authentication_failed` for rejected joins.
- `groundfire-web-gateway` now supports a production-oriented signed session-token path: `--session-secret` / `GROUNDFIRE_WEB_GATEWAY_SESSION_SECRET` accepts HMAC-signed expiring `auth_token` values bound to `join.player_name`, `--issue-token PLAYER_NAME` generates those tokens with `--session-token-ttl`, and `hello.auth_token_mode` advertises whether auth is `none`, `static`, `signed`, or `static_or_signed`.
- `groundfire-directory` now exposes an opt-in `/session-token.json?player_name=...` issuer when started with `--session-secret` / `GROUNDFIRE_DIRECTORY_SESSION_SECRET`, returning no-store signed join tokens compatible with the gateway's `--session-secret` validation.
- Server directory schema `1` now preserves optional `session_token_url` values, and Godot Online Match fetches a no-store signed token from that URL before `join` when no static `auth_token` is embedded in the entry.
- Server directory schema `1` now preserves an optional `auth_token` for pre-provisioned development/private-directory joins, so directory entries can feed the Godot WebSocket `join.auth_token` path.
- Online Match now holds input/ping dispatch while a join is still pending, including while a `session_token_url` HTTP request is in flight, and the Python gateway now rejects pre-join `input` messages with `not_joined`.
- `groundfire-web-gateway` now has an optional first-pass active player capacity gate through `--max-players` or `GROUNDFIRE_WEB_GATEWAY_MAX_PLAYERS`, advertises `max_players`/`players_connected`, and emits `server_full` for excess Godot joins.
- `groundfire-web-gateway` now has an optional first-pass closed-join mode through `--closed` or `GROUNDFIRE_WEB_GATEWAY_CLOSED`, advertises `joins_open`, and emits `server_closed` for rejected Godot joins.
- `groundfire-web-gateway` now has an optional first-pass player-name ban list through `--ban-player` or `GROUNDFIRE_WEB_GATEWAY_BANNED_PLAYERS`, advertises `ban_enforced`, and emits `banned` for rejected Godot joins.
- Gateway compatibility tests now exercise a real local TCP/WebSocket handshake and masked client frames through the actual gateway handler, covering connected snapshot, hello, invalid password rejection, successful join, input, ping, and disconnect messages.
- Exported web browser QA now starts real local `groundfire-web-gateway` instances for `invalid_password`, `authentication_failed`, signed session-token join, `server_full`, `server_closed`, and `banned`, reserves a `--max-players 1` slot for the full-server case, passes their WebSocket/session-token endpoints into `?qa=browser_runtime`, and verifies that Online Match surfaces failures as fatal, non-retrying join failures while proving the signed-token path reaches `joined`.
- A mandatory `Migration Fidelity Contract`, per-area fidelity annotation structure, and `scripts/validate_godot_migration_contract.py` now make explicit that Godot migration work must preserve the Python/Pygame user experience.
- `groundfire-directory` now provides a first real read-only HTTP server-directory service for schema `1`, including CORS, quoted `ETag`, conditional `If-None-Match` / `304 Not Modified` responses, `Cache-Control`, `X-Groundfire-Directory-Refresh`, ServerBook-to-Godot conversion, LAN filtering for public web directories, default public rejection of embedded static `auth_token` entries, HTTP(S) validation for `session_token_url`, and optional injected WebSocket gateway entries for local hosted testing.
- Server Browser now surfaces HTTP directory cache/ETag/refresh diagnostics and has a first classic table-header chrome pass instead of bare labels.
- `groundfire-directory` now exposes `/healthz` and `/diagnostics.json` with served/filtered/invalid server counts, making production-style directory QA easier before public hosting exists.
- Local Match HUD angle/power gauges now use the classic Pygame-facing `-75..75` angle and `1..20` power range/defaults instead of the earlier modernized `0..180` / `0..100` display scale.
- Local Match projectile out-of-world explosions now clamp the terrain-height lookup to the playable map edge, avoiding edge shots sampling terrain beyond the world bounds.
- Runtime smoke validation now exercises Main Menu classic metrics across 640x480, 1024x768, 1280x720, 1600x900, and 1920x720 viewports so scaling regressions are caught before browser visual QA.
- `scripts/validate_godot_release.sh` now defines an explicit local release gate around migration contract validation, Godot fidelity validation, optional visual/browser QA, optional packaging, and checksum verification.
- The classic `Shield` command is now present in Godot input settings and the browser-safe WebSocket input contract as `gf_shield` / `shield`, and Local Match now has first-pass shield gameplay that drains tank fuel, draws a visible tank shield, and reduces incoming explosion damage before scoring/credits are awarded.
- WebSocket snapshots now carry `player_number`, `max_players`, and `players_connected`, so online-visible state includes the same capacity/session metadata advertised by `hello`.
- Web query routing now supports `?screen=local_match_setup` / `?screen=local_setup` for direct browser capture of the Local Match setup route.
- Server Browser table sizing now responds to viewport width/height with proportional column widths and bounded scroll height, and runtime smoke validation covers 640x480, 1024x768, and 1600x900 browser layout constraints.
- GitHub Actions now runs the base Godot release validation gate on Linux and exposes manual `workflow_dispatch` options for exported browser QA and release packaging/checksum verification when export templates are installed in CI.
- TerrainModel `_settle_landed_superblock` now handles multi-chunk superblock landing: when a two-or-more chunk linked superblock falls and the bottom chunk merges with compatible lower terrain, the bottom chunk is deleted and the superblock leader (cap) inherits the lower chunk's resting motion state, matching Python `Landscape.update` lines 177–188 where `end_super_idx != start_super_idx` causes the superblock leader to be updated after the merge; a named Python reference test in `tests/test_landscape_fidelity.py` and a matching GDScript assertion in `godot/tests/local_match_fidelity_check.gd` document this path (fidelity gate: 74 tests, all passing).
- TerrainModel `_settle_landed_superblock` now handles non-compatible color landing cases: when a falling chunk lands on a resting lower chunk that has incompatible (non-matching) colours, the bottom chunk links to the lower chunk and inherits its resting state without merging or deleting chunks, matching Python `Landscape.update` lines 190–198; a named Python reference test in `tests/test_landscape_fidelity.py` and a matching GDScript assertion in `godot/tests/local_match_fidelity_check.gd` document this path.
- TerrainModel `_settle_landed_superblock` now preserves Python `Landscape.update` uniform landing onto still-falling support chunks: the merge decision follows the landing chunk's own vertical colour uniformity, ignores the support chunk's colour, and keeps the support's falling wait/speed on the merged result; matching Python and GDScript regressions document the motion handoff.
- TerrainModel falling wait now matches Python `Landscape.update` lines 137–139: a tick that starts while `wait_for_fall_time` is positive only subtracts the wait, preserves existing fall speed, does not move or accelerate the chunk, and leaves negative wait for the next moving frame if the tick crosses zero; Python and Godot regression tests cover this cadence.
- TerrainModel crater clipping now has an integrated removed-linked-cap regression: when Python `Landscape.clip_slice` fully removes a linked cap, the following chunk continues through the same clip pass and exposes the lower crater edge instead of keeping the original pre-blast cap top; matching Python and Godot assertions document the behavior.
- TerrainModel crater clipping now has a one-sided linked-bottom-cut regression for Python `Landscape.clip_slice` lines 342–356: when only one lower edge is clipped and the opposite lower edge is tangent/outside, the linked support detaches, the cap enters the classic fall pause, and the support chunk inherits the previous superblock motion.
- TerrainModel crater clipping now has an integrated double-split regression: when a blast is entirely inside a tall chunk horizontally and vertically, it splits the chunk into an upper piece and a lower piece, with the upper piece starting to fall while the lower piece remains resting, matching the Pygame/C++ exact index-shifting superblock falling behavior; matching Python and Godot assertions document the behavior.
- TerrainModel crater clipping now has linked double-split lower-support coverage for Python `Landscape.clip_slice` lines 361-407 and 408-415: when a crater splits a linked cap, the upper piece detaches and starts the classic fall pause while the lower remainder stays linked to the support chunk below it.
- TerrainModel crater clipping now has linked-support double-split leader-motion coverage for Python `Landscape.clip_slice` lines 361-407: when a crater splits the support chunk below a linked cap, the cap remains linked to the upper support remainder, the superblock leader starts the classic fall pause, and both support remainders stay individually non-falling.
- TerrainModel crater clipping now has falling linked-support double-split motion coverage for Python `Landscape.clip_slice` lines 361-407: when a crater splits the support chunk below an already-falling linked cap, the cap keeps its old fall wait/speed, the upper support remainder stays resting, and the lower support remainder inherits motion from the superblock leader even if the support chunk being split was still marked resting.
- TerrainModel crater clipping now has falling linked double-split support-motion coverage for Python `Landscape.clip_slice` lines 361-407 and 408-415: when a crater splits an already-falling linked cap, the upper piece starts a fresh fall pause while the lower linked remainder keeps the old superblock wait/speed.
- TerrainModel crater clipping now has a one-sided linked-bottom uncut above blast regression: when only one lower edge is clipped, and the opposite lower edge is uncut but above the blast, it detaches the linked support, starts the cap falling, and lowers the uncut side's bottom to match the un-clamped crater top, matching Python `Landscape.clip_slice` lines 308–321; a named Python reference test in `tests/test_landscape_fidelity.py` and a matching GDScript assertion in `godot/tests/local_match_fidelity_check.gd` document this path.
- TerrainModel crater clipping now also has explicit Python reference coverage for the mirrored one-sided linked-bottom adjustment in `Landscape.clip_slice` lines 342–356: when the left lower edge is clipped and the right lower edge is outside/above the blast (`state4 == 2`), the linked support detaches and the uncut right side is resolved through `clip_height` before fall motion is applied, matching the existing GDScript terrain assertion.
- TerrainModel crater clipping now has a two-sided linked-bottom-cut regression for Python `Landscape.clip_slice` lines 322–340: when both lower edges of a linked cap are clipped, the linked support detaches, the cap enters the classic fall pause, and the support chunk preserves the previous superblock motion.
- TerrainModel crater clipping now has a one-sided top-edge regression for Python `Landscape.clip_slice` lines 280–288: when a blast reaches only the left top edge and the opposite top edge is horizontally outside the blast, only that edge is lowered to the crater boundary while the opposite side, bottom edge, and resting state are preserved.
- TerrainModel crater clipping now has the mirrored right-top-edge regression for Python `Landscape.clip_slice` lines 285–288: when only the right top edge is inside the blast, the right edge is lowered while the left edge and bottom edge stay intact.
- TerrainModel crater clipping now has a two-sided top-edge regression for Python `Landscape.clip_slice` lines 291–298: when both top edges are inside the blast, both are lowered to the crater boundary while the bottom edge and resting state are preserved.
- TerrainModel crater clipping now preserves the classic endpoint-code `top_code = 6`/`9` top cuts for Python `Landscape.clip_slice` lines 280-288: when neither top endpoint is inside the circular blast but the left/right endpoint states straddle the blast center, Godot keeps the lower clipped remainder instead of treating the middle graze as a no-op.
- TerrainModel crater clipping now has mirrored linked top-only support-preservation coverage for Python `Landscape.clip_slice` lines 280-288 and 408-415: when only a linked cap's left or right top edge is clipped and no bottom endpoint participates, the cap remains linked to its support, no fall motion starts, and the support chunk remains unchanged.
- TerrainModel crater clipping now has mirrored multi-chunk linked-superblock edge-graze skip coverage for Python `Landscape.clip_slice` lines 270-275: a one-edge graze against either side of the cap advances over the entire linked chain, preserving the cap, connector, and support unchanged.
- TerrainModel crater clipping now has mirrored non-linked bottom-edge fall-start coverage, matching Python `Landscape.clip_slice` right-edge bottom-code branches at lines 303-321 and left-edge branches at lines 342-359 where bottom-code cuts start the owning superblock's classic fall pause even without linked support; the Godot implementation derives this from the Python-style bottom code instead of one-sided split alignment.
- TerrainModel crater clipping now has explicit `bottom_code = 12` coverage for Python `Landscape.clip_slice` lines 303-321: when only a non-linked chunk's right bottom edge is inside the blast and the left edge is horizontally out of range, the right bottom is clipped, the left bottom remains intact, and the chunk starts the classic fall pause.
- TerrainModel crater clipping now has explicit mirrored unlinked `bottom_code = 6`/`9` coverage for Python `Landscape.clip_slice` lines 303-321 and 342-359: when one bottom edge is below the blast center and the opposite bottom edge is above it, the endpoint-code branch clips only its selected edge, starts the classic fall pause, and preserves the opposite bottom because no linked support branch runs.
- TerrainModel crater clipping now has explicit mirrored unlinked `bottom_code = 11`/`14` coverage for Python `Landscape.clip_slice` lines 303-321 and 342-359: when one bottom edge is inside the blast and the opposite bottom edge is above it, only the inside edge clips, the chunk starts the classic fall pause, and the opposite bottom remains unchanged because there is no linked support to detach.
- TerrainModel crater clipping now has explicit unlinked `bottom_code = 7`/`13`/`15` coverage for Python `Landscape.clip_slice` lines 322-340: when both bottom edges enter the two-sided bottom branch, both bottom edges clip, the single unlinked chunk starts the classic fall pause, and no lower support inherits motion.
- TerrainModel crater clipping now has a one-sided removed-linked-cap regression for Python `Landscape.clip_slice` lines 280-410: when a thin linked cap's right edge is fully consumed while the left edge is horizontally outside the blast, the support inherits the cap's untouched left top and clipped right top before continuing through the crater pass.
- TerrainModel crater clipping now has mirrored falling removed-linked-cap motion propagation coverage for Python `Landscape.clip_slice` lines 303-321, 342-359, and 408-415: when an already-falling linked cap is deleted by a one-sided crater from either edge, the promoted support chunk inherits the old superblock wait/speed.
- TerrainModel crater clipping now preserves Python's mirrored removed-linked-cap promotion when only one side is fully consumed while the opposite side is still a tall valid edge: the whole linked cap is deleted, the surviving top and clipped top are promoted onto the support chunk, and the support continues through the same crater pass.
- TerrainModel crater clipping now has the mirrored one-sided removed-linked-cap regression for Python `Landscape.clip_slice` lines 280-410: when a thin linked cap's left edge is fully consumed while the right edge is horizontally outside the blast, the support inherits the clipped left top and cap's untouched right top before continuing through the crater pass.
- TerrainModel crater clipping now preserves mirrored classic endpoint-code no-ops for one-sided middle crater grazes: when a tiny blast intersects only the middle of either slice edge and neither that edge's top nor bottom endpoint is inside the blast, Godot leaves the chunk unchanged like Python `Landscape.clip_slice` instead of applying continuous interval clipping.
- TerrainModel crater clipping now has mirrored Python reference coverage for the classic linked-superblock edge-graze skip guard in `Landscape.clip_slice` lines 270-275: right-bottom and left-bottom grazes that only touch a linked cap's lower outer edge advance past the whole linked superblock, preserving the cap/support pair and their link instead of detaching or clipping it.
- TerrainModel crater clipping now has paired Python/Godot edge-colour interpolation regressions for `Landscape.clip_slice` plus `Landscape.calculate_colour`: top and bottom cuts move the changed edge colour along the original vertical gradient while leaving untouched opposite/top/bottom colours unchanged.
- TerrainModel falling merge now uses Python-faithful near-exact colour equality for the `Landscape.update` uniform-colour merge branch, with paired regressions proving that close-but-not-identical top/bottom colours link to the support instead of merging.
- TerrainModel now exposes a Python-faithful `move_to_ground(x, y)` stacked-chunk query: the supplied query height decides whether an upper cap is reachable or should be skipped so lower support terrain can be selected, matching `Landscape.move_to_ground` lines 438-458; paired Python/Godot regressions protect the difference from simple `height_at`.
- TankState ground settling and grounded movement now use `TerrainModel.move_to_ground` when available, so tanks already below a suspended upper cap resolve to the lower reachable support instead of snapping to the highest terrain surface; the Godot fidelity check covers this stacked landing path.
- TerrainModel crater clipping now has explicit coverage for the classic `top_code = 11` and `top_code = 14` cases in Python `Landscape.clip_slice` lines 291–298: when one top endpoint of a chunk is inside the blast (state 3) and the other is above it (state 2), both top edges are lowered to the crater bottom, discarding the top portion above the crater on both sides, with parallel Python and Godot regressions verifying this exact alignment.

## Current Status

The validated Godot release slice is no longer blocked by broad, generic categories such as gameplay, HUD/input, visual style, classic flow, browser runtime, or release packaging. It now covers playable local and online slices, export automation, packaging, browser runtime QA, browser visual regression QA, and the 129-test fidelity gate described below.

The Python/Pygame client remains the source of truth for any future audit. Remaining work should be stated as named follow-up targets, such as a specific `Landscape.clip_slice` branch, one exact score/shop timing path, a hosted production directory policy, or a concrete multiplayer edge case. Do not reopen the migration as incomplete based only on broad labels unless a new Pygame reference regression identifies the failing behavior.

Implemented or started:

- Main menu with Groundfire logo/background and basic navigation.
- Main menu now has a first Local Match setup screen between Start and gameplay, carrying the selected round count plus an eight-slot roster snapshot into the match scene; the battle runtime now instantiates the full roster, rotates turns across surviving participants, and keeps score/shop rows plus final winner selection tied to that same participant state.
- The Local Match setup screen now carries editable player/enemy names into the actual match state, so HUD bars, score rows, defeated-player detail, and final-result winner cards no longer depend only on hardcoded `Player`/`Enemy` labels.
- Local Match setup keyboard/controller focus now updates with active slot/type changes so disabled roster controls are skipped without trapping inactive rows.
- The Local Match HUD now follows the active participant and nearest target in roster-backed matches, including a compact alive-count and leader summary for multi-combatant rounds.
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
- The scrollable Options form now has explicit vertical focus order for controller/keyboard navigation, with disabled controls skipped and button horizontal focus self-looped.
- Local Match HUD now shows the classic top-of-screen tank status cards with HP, fuel, tank color, and selected weapon icon from the original atlas.
- Local Match has an initial post-round economy/shop screen: wins award credits, damage earns score/credits, weapon ammo packs can be bought, and continuing starts the next round without the old auto-advance banner flow.
- A first separate post-round score overlay now appears before the shop, carries the round summary/reward, and transitions into the shop without double-awarding credits.
- The score overlay now has first-pass classic table semantics: it orders player/enemy by score, shows rank/tie labels, displays who was defeated in the round, marks defeated leaders in the round detail, and tracks enemy score for local ranking.
- End-of-round score/economy now applies the classic `Player.end_round` shape in Godot: defeated normal players give +100 score/+50 credits, defeated leaders give +200 score/+50 credits, self-defeats penalize -50 score, surviving tanks get +100 score/+25 credits, and every participant receives the +10 credit round stipend.
- The final configured round now routes from score into a first winner overlay with winner/tie messaging, winner-only cards, classic human/computer activation delays, and a main-menu exit instead of another shop pass.
- Shop purchases now distinguish classic purchase bundle sizes from the current ammo stock, so MIRV/Missile/Nuke buying no longer inherits the round-start ammo value; rows expose the pack amount in the shop overlay.
- Shop actions now include the classic input-delay cadence: the first buy/Done action is locked briefly when the shop opens, and each buy/Done attempt applies a short repeat delay before more shop input is accepted.
- Shop buy actions now use the classic-style table split: prices stay in the `$cost` column and the action control reads `Buy`.
- The shop money line and blocked-purchase messages now use the classic `$N` money copy instead of exposing the prototype `Credits N` wording.
- The shop overlay now renders the remaining classic catalog entries as purchasable first-pass rows, so the full classic catalog surface is available while final behavior tuning remains tracked separately.
- Jump Jet is now a functional shop purchase that increases player fuel reserve instead of the active fuel bar maximum; `TankState` starts rounds with active fuel capped at 100% and spends the reserve alongside active fuel, moving the shop closer to the classic post-round upgrade flow.
- The HUD and shop now expose the fuel reserve value directly, making the first-pass economy presentation clearer instead of hiding Jump Jet purchases behind the active fuel bar.
- The shop subtitle now previews the next round as `Round N of Total`, moving the inter-round presentation closer to the original `ShopMenu`.
- Computer players now run a first-pass automatic shop pass using easy/normal/hard purchase priorities before the next human shopper or next round is shown.
- Enemy AI now evaluates candidate shell trajectories and picks a near-target shot with a small inaccuracy offset.
- Local Match now has first-pass camera behavior: a world larger than small viewports, smoothed zoom/framing around active subjects, projectile lookahead, explosion camera shake, mouse aiming through camera coordinates, projectile bounds, and a visible map frame.
- Options gamepad capture now supports controller-side cancellation with Back/Select.
- Pause overlay now focuses Resume when opened so controller/keyboard navigation has a usable first target.
- Local Match setup, score, and final-result overlays now have explicit focus paths for controller/keyboard navigation, including self-looped single-button overlays and cancel handling for the score/final modal flow.
- Terrain/projectile impact detection now resolves the first segment intersection against chunk polygons and feeds the actual collision point into explosions.
- Terrain/projectile impact detection now covers collinear edge overlap hits plus shots that start exactly on a chunk edge, so grazing terrain contacts are treated as hits instead of falling through.
- A headless Godot terrain collision check now covers the new segment collision path.
- Terrain chunks now keep interpolated classic-style color bands when clipped, fall as linked superblocks, and merge or relink when they settle.
- TerrainModel now exposes classic-style terrain dropping with a minimum-land clamp, and Local Match tank death now matches the Python rule where exact zero health is still alive until further damage.
- Terrain superblock falling now uses separate left/right landing gaps and classic current-frame speed/next-frame acceleration ordering, so uneven lower terrain no longer freezes the entire falling block at the first side contact.
- Terrain superblock landing now links onto a still-falling support chunk and inherits its motion for the next frame, preventing landed chunks from separating while the support continues downward.
- Terrain superblock landing now also has regression coverage for the classic same-colour merge/delete path when a falling solid cap lands on compatible lower terrain.
- Terrain superblock landing now also merges uniform chunks into still-falling supports while preserving the support's wait/speed, matching Python's support-motion handoff instead of requiring the support to be at rest.
- Terrain crater clipping now has a first linked-support parity case: severing a linked cap from the chunk below starts the cap falling and preserves inherited superblock motion on the separated lower chunk.
- Terrain crater clipping now also preserves the classic linked-removal top handoff when a linked chunk is deleted before the next chunk continues through the clip pass.
- Terrain crater clipping now preserves asymmetric one-sided split remainders by mirroring the split ratios onto the intact slice edge instead of dropping the unmatched remainder.
- Terrain crater clipping now preserves the classic minimum-land floor when blasts reach the deep base, clamping removal at `MIN_LAND_HEIGHT` and keeping below-floor base chunks intact.
- Terrain crater clipping now preserves the classic falling-split motion handoff, so a mid-air split gives the detached upper cap a fresh fall pause while the lower remainder keeps inherited falling speed/wait state; this now has explicit Python and Godot regression coverage.
- Local Match now has first-pass quake/drop wiring that periodically lowers terrain during active play, shakes the camera, and surfaces quake state in the HUD.
- Local Match now uses the classic first/between quake timing, plays the classic quake rumble as a loop during quake/drop, pauses it with the pause overlay, and stops it at quake end or round/shop transitions.
- Options now persists fullscreen, VSync, master volume, screen shake, camera smoothing, and mouse aiming.
- Options now persists classic-style resolution presets and applies the selected desktop window size.
- Options now exposes the classic-facing top preset shape from `src/optionmenu.py`: `Resolution:` and `Screen Mode:` selector rows in the brown band style, `Set Controls`, `Apply`, and `Back` actions, with the richer Video/Audio/Gameplay/Online/Controls settings retained below for Godot-specific configuration.
- Main Menu and Options now share a first classic text-effect pass: title/copy labels, top preset labels, and classic buttons receive the Pygame-style black shadow/outline treatment, while classic button hover/pressed font color uses the original yellow highlight.
- Local Match applies persisted camera shake, camera smoothing, and mouse aiming settings.
- Server Browser filters now include passwordless-only, open-slot-only, and latency/name/player-count sorting.
- Server Browser filter text, passwordless/open-slot toggles, and sort mode now persist through the browser-safe `BrowserStore`.
- Server Browser Favorites/History now supports removing favorites, clearing history, undoing those destructive actions, disabling history cleanup when empty, tab-specific empty messages, and showing saved favorite endpoints from known History details or fallback rows when the current directory omits them.
- Server Browser now prevents duplicate online directory refreshes with a visible loading action state and clears that state on HTTP success, failure fallback, or local JSON refresh.
- Server Browser loading state now renders a muted table message row while the online directory request is in flight, replacing stale rows until success or fallback.
- Server Browser table cells now have first-pass tuned column widths for server, game, players, map, and latency plus named row/header height constants.
- Server Browser now parses player counts and latency values defensively for filtering/sorting, adds row tooltips, and includes source/player/full/password/missing-directory details in selected-row status copy.
- Server Browser table width and scroll height now scale with the viewport, with runtime smoke coverage for small, classic, and wide desktop/browser sizes.
- Enemy AI can choose Shell, Machine Gun, MIRV, Missile, or Nuke based on first-pass tactical scoring and available ammo.
- Enemy AI special-weapon selection now projects expected target damage versus self-damage with difficulty-specific score thresholds, so it avoids risky close-range Nukes while still using safe high-value specials.
- Machine Gun firing now spends volley ammo and resolves as classic-style direct-hit tracers instead of splash/explosion projectiles, with per-bullet cooldown spacing instead of a fully simultaneous burst.
- Machine Gun ammo-per-round, volley size, and cooldown spacing are centralized in `WeaponInventory`, with Local Match reading those constants as fallback firing values.
- Machine Gun tracers now use the same projectile-gravity scale as shells, matching the Python `MachineGunRound` parabola instead of the earlier zero-gravity straight-line placeholder.
- Machine Gun tracer render tails now use a named `0.01s` classic back-time constant, so tracer length is tied to weapon timing instead of the current frame delta.
- Machine Gun tracer position updates now use stored launch origin/velocity plus active age, aligning the Godot path with Python `MachineGunRound.update()` and avoiding frame-step drift for held or delayed tracers.
- Limited-ammo weapon depletion now falls back to Shells instead of cycling to the next stocked weapon, and held Machine Gun fire consumes Machine Gun ammo by name so the final bullet stops the hold instead of spending another weapon's ammo.
- Player Machine Gun firing now starts moving from a fixed volley toward the classic held-fire model: each held-fire cooldown emits one tracer and consumes one ammo instead of spending the whole burst up front.
- Enemy Machine Gun firing now shares the staged cooldown/ammo path and limits itself by an AI burst budget instead of consuming the volley before any tracer is emitted.
- Machine Gun now loops the classic firing sound through a dedicated Godot audio node and stops it cleanly across release, pause/resume, empty ammo, AI burst completion, and reset paths.
- Player weapon cycling during held Machine Gun fire now mirrors the classic `unselect` direction more closely by stopping the firing state/audio while preserving active tracer rounds.
- Enemy Machine Gun burst length now varies with AI difficulty and low-health finishing context, moving away from a fixed volley-length hold.
- Machine Gun first-shot timing now matches the Python `MachineGunWeapon.select`/`update` cadence more closely: entering fire mode starts audio, waits through the classic cooldown before spending ammo or spawning the first tracer, and preserves the leftover frame time when the cooldown expires mid-frame.
- Machine Gun unselect before the first tracer now cancels the held-fire state immediately, returns to aim, keeps the cycled weapon selected, and avoids consuming ammo or advancing the turn.
- Direct tank impacts from shell-style projectiles now apply full direct-hit damage before splash falloff, record the actual shot owner for turn flow, and advance player/enemy damage scoring symmetrically.
- Machine Gun lethal hits now stop held/AI firing, stop audio, expire queued tracer rounds, and let the score overlay open from the standard round-over path.
- Machine Gun and projectile segment-hit selection now ignore the firing owner before choosing the first tank on the path, with regression coverage for a third configured roster participant receiving damage, score, credits, and name-aware status copy.
- MIRV split behavior now uses configurable five-fragment horizontal spread at projectile apex instead of the earlier three-fragment rotated placeholder.
- MIRV ammo-per-round, fragment count, spread, and minimum split age are centralized as named fidelity constants.
- MIRV fragment spread now removes the earlier minimum fan-out placeholder and follows Python `Mirv.update()`: vertical shots keep zero fragment x velocity.
- MIRV parent projectiles now expire immediately after splitting, so the active projectile set contains only the spawned fragments.
- MIRV apex splitting now preserves the intra-frame split point, moving it closer to the original entity update that spawns fragments at the computed apex time.
- MIRV projectile stepping now processes only the projectiles that existed at the start of the frame, preventing newly spawned fragments from double-advancing on the split frame.
- Missile behavior now uses fuel-limited steering and angle-change acceleration rather than direct target homing, and now loops the classic powered-flight sound while fuel remains, moving it closer to the original controllable missile entity.
- Missile powered flight now derives velocity from the Pygame `Missile.update()` angle-speed formula, keeping the old project as the propulsion authority rather than the Godot launch vector.
- Missile fuel exhaustion now defers free-fall gravity until the update after fuel crosses below zero, matching the powered-then-store-velocity order in Python `Missile.update()`.
- Missile steering clamp/recentering and AI steer scale now live behind named Local Match constants and are covered by the fidelity check.
- Nuke behavior now has a first-pass classic whiteout flash in addition to its larger blast/damage tuning.
- Nuke behavior now also plays the classic one-shot explosion sound through a dedicated Godot audio node that pauses with the match and stops on reset.
- Shell/MIRV/Nuke fire and Missile launch now use the classic one-shot launch audio cues from the Python weapon implementation, and powered Missile flight now follows the original looping sound-source behavior until fuel is spent.
- Tank gun acceleration now matches the classic release behavior more closely by zeroing aim/power change speed when controls are neutral.
- Jump jets now push along the tank's slope-adjusted normal and drain fuel at the classic default rate instead of applying only a fixed vertical impulse.
- Jump-jet input now passes tank left/right through to boost rotation, so airborne tanks can tilt while boosting and settle back toward level without side-thrust movement hijacking the input.
- Shells and special projectiles now add the tank's current airborne velocity at launch, so firing during jump-jet movement carries momentum into the projectile.
- Airborne tank falling now uses the `TANK_AIR_GRAVITY` fidelity constant, keeping jump-jet motion closer to the classic boost/gravity balance.
- Gun angle/power clamps now use the classic Pygame-facing fidelity constants instead of hardcoded modernized values in `update_gun` and mouse aiming.
- Round-start gun angle, gun power, health, and fuel now use explicit `TankState` defaults instead of repeated literals.
- Projectile gravity now uses a single Local Match fidelity constant across live projectile updates, AI shell simulation, Machine Gun tracers, and MIRV split timing.
- Projectile launch velocity inheritance now lives on the tank model, closer to the Python `gun_launch_velocity`/`gun_launch_velocity_at_power` split.
- Grounded tanks now detach into airborne fall when crater/drop terrain opens a meaningful gap under them, closer to the classic ground contact pass.
- Grounded tanks now passively slide on slopes above the classic steepness threshold, with movement speed, slope drag, and fuel-use constants named in `TankState`.
- Airborne tanks now respect terrain-provided playable bounds and zero horizontal velocity when clamped at a map edge, matching the classic edge stop behavior.
- Options now exposes gamepad profile selection and stores per-device gamepad bindings when a connected device profile is selected.
- Options control rows now use an explicit classic-facing action order from `ControlSettings.ACTION_ORDER`, keeping rebinding presentation stable across engines/runtimes.
- Main Menu now has horizontal focus self-loops on its vertical action list, keeping controller/keyboard navigation inside the menu column.
- Pause overlay now has Options access, explicit vertical focus neighbors, and horizontal self-loops for stable controller/keyboard navigation.
- Pause-to-Options now returns to the same paused Local Match instance instead of dropping the player back to a fresh menu/options flow.
- Shop overlay buy/continue controls now have first-pass vertical focus neighbors for controller/keyboard navigation.
- Shop overlay refresh now restores focus to the previously focused purchasable row when it remains available, making repeated keyboard/controller purchases less jumpy.
- Server Browser now has first-pass focus-neighbor wiring for filters, server table rows/cells, actions, close/back, and password modal controls, including controller/keyboard accept on selected rows and cancel from the modal.
- Server Browser action buttons now recalculate their focus loop from only enabled actions, keeping disabled favorite/connect/history controls out of keyboard/controller traversal.
- Optional mouse aim updates a world reticle and supports left-click firing, while staying disabled by default for classic gameplay parity.
- Local Match HUD now uses the classic `weaponicons.png` atlas in Pygame-style tank status cards, with the same top-screen world-coordinate placement and health/fuel bar color formulas as the Python renderer; those classic panel/bar/icon coordinates are now exposed through a testable helper and protected by GDScript fidelity assertions.
- Local Match aiming now uses the classic translucent per-tank gun arrow, with the arrow geometry anchored on the same tank center as the launch origin and scaled from the classic `tank_size`/`gun_power` proportions, leaving the modern line/gauge HUD as removed prototype scaffolding rather than the target experience.
- WebSocket transport exposes connection state and sequence tracking.
- Online Match now reconnects with exponential backoff, displays latency/ack/pending/tick/terrain diagnostics, prunes acknowledged commands, and applies local prediction to the player's replicated tank.
- Online Match now has explicit Reconnect and Back controls for production failure-flow polish.
- Online Match interpolation now tracks local prediction error, reconciles predicted player tanks at a named rate, and extrapolates replicated projectiles slightly between snapshots.
- Online Match Reconnect/Back controls now wire a closed focus loop for controller/keyboard navigation.
- Options persists AI difficulty, and Local Match uses it to adjust AI search granularity, aim variance, and special-weapon aggression.
- Local Match wind now shifts between turns/rounds, applies a small gust component to projectile motion and AI trajectory search, and exposes a directional wind label in the HUD.
- Desktop-only Dedicated Server exposes a first Godot gateway launcher for the Python WebSocket gateway.
- The Godot Dedicated Server launcher can now configure first-pass gateway join policy before launch: optional password, optional auth token, optional max-player cap, closed-join mode, and banned player names.
- The Godot Dedicated Server launcher now keeps first-pass process lifecycle state by storing the gateway PID, blocking accidental duplicate starts, and offering a Stop Gateway action.
- The Godot Dedicated Server launcher now previews and copies the `ws://host:port` endpoint that clients should use, including `0.0.0.0`/IPv6 normalization for safer local testing.
- The Godot Dedicated Server launcher now restores non-secret gateway defaults between sessions while avoiding persistence for join passwords and auth tokens.
- The Godot Dedicated Server launcher now previews and copies a masked launch command so desktop users can inspect or reproduce gateway startup without exposing transient secrets.
- The Godot Dedicated Server launcher now keeps keyboard/controller focus out of disabled Stop Gateway and recalculates the action row when Stop becomes available or unavailable.
- Linux desktop and web export preset scaffold.
- Export automation exists in `scripts/export_godot.sh` for Linux desktop and web presets after validation; the local workspace has Godot 4.6.2 export templates installed and both presets export successfully.
- Release exports exclude Godot runtime test scripts from the packaged Linux/Web artifacts.
- Runtime smoke validation now covers Main Menu, Options, Server Browser, Local Match, Online Match controls, web-safe directory parsing, and deterministic desktop/web feature rules.
- Runtime smoke validation now also exercises Options, including the classic preset block focus route and viewport bounds, Local Match setup, and desktop Dedicated Server tool entry points across small/classic/wide viewports so menu-route regressions are caught before export.
- Local-match fidelity and Online Match reliability checks now run through `scripts/validate_godot.sh`.
- A consolidated migration fidelity gate now exists as `scripts/validate_godot_fidelity.sh`, documented in the `Godot Fidelity Audit` section, to run the Godot validation plus Python reference/fidelity tests for the migrated contracts.
- Godot lifecycle cleanup now closes WebSocket peers, cancels browser HTTP requests, stops and releases Local Match audio streams during real shutdown, and drains queued frees in runtime/fidelity tests so the headless gate exits without the prior `ObjectDB instances leaked at exit` warning.
- Browser visual QA exists through `scripts/qa_godot_web.sh`; approved reference screenshots now exist for Main Menu, Options, Server Browser, Local Match setup, and Local Match, and missing goldens fail `--check` until they are intentionally reviewed/updated.
- Browser QA harness reliability now has a pass for local full-server fixtures and visual captures: it preserves WebSocket frame bytes coalesced with the HTTP upgrade response, waits longer for the slot-holder, scopes the QA directory URL per `seed`/`verify` phase so browser cache cannot turn the first request into a stale `304`, waits for the Godot web build to publish the expected `window.__groundfireVisualReady` route marker, rejects unpainted near-solid screenshots before comparing goldens, and prefers a direct `google-chrome` binary when available before falling back to Chromium wrappers.
- Pygame visual reference capture now exists through `scripts/capture_pygame_references.py`, producing Main Menu, Options, Server Browser, and Local Match source-of-truth screenshots under `docs/references/pygame_visual/` so Godot browser goldens cannot be mistaken for the original visual target.
- Godot visual tuning now has a first classic-reference correction pass: the shared theme uses the Pygame menu tile tint, brown translucent controls, and black translucent panels; the Main Menu restores the classic logo/version/copyright/button stack; Local Match fills the full viewport and draws the classic purple sky gradient; Server Browser and Online/Local screens use full-viewport layout instead of the earlier centered menu margins.
- Browser runtime QA now serves a schema `1` directory fixture and verifies storage/filter persistence across separate seed/verify browser sessions, HTTP directory parsing, first-pass `Cache-Control`/`ETag`/refresh headers, `If-None-Match`/`304 Not Modified` conditional refresh behavior, web-hidden LAN/desktop features, invalid-payload fallback diagnostics, transient directory request retry/reporting, real local gateway `invalid_password`, `authentication_failed`, `server_full`, `server_closed`, and `banned` handling, plus no-store signed session-token join success inside the exported web build.
- Release packaging exists through `scripts/package_godot_release.sh`, producing Linux/Web archives, a JSON manifest, and `SHA256SUMS`.
- Release artifacts now use versioned names, with `GROUNDFIRE_RELEASE_VERSION`, `GROUNDFIRE_RELEASE_PREFIX`, and `GROUNDFIRE_RELEASE_NOTES` available for prerelease/CI packaging.
- `scripts/validate_godot_release.sh --browser-qa --package` has a recorded successful local run for version `0.25.0`, covering the migration contract, the then-current fidelity tests, exported-browser runtime/visual QA, release packaging, and SHA256 verification; the release walkthrough is now folded into `Validated Release Slice Walkthrough` in this file without treating it as completion of the whole migration.
- Build/runtime documentation now covers release verification, checksum usage, current signing policy, browser hosting expectations, and distribution notes.
- Optional headless visual golden validation exists through `scripts/validate_godot_visuals.sh`; it captures Main Menu, Options, Server Browser, and Local Match and fails on missing goldens unless they are updated intentionally.
- The browser-safe WebSocket contract now has a first enforced protocol version gate shared by the Godot `NetworkAdapter` and Python `groundfire-web-gateway`.
- The first WebSocket protocol document exists and gateway-side shape validation covers hello, join, input command names/booleans, ping, disconnect, error, and snapshot envelopes; gateway hello/errors now advertise supported protocol versions, snapshots include `match_snapshot_schema` and `event_schema` metadata, and events carry a schema number.
- The browser-safe input envelope now includes the classic Shield command as `shield`, with Godot exposing `gf_shield` in project settings, Options rebinding, Local Match input registration, and Online Match input snapshots.
- Local Match now consumes the classic Shield input for the active human tank, spends fuel while held, renders a shield bubble, and applies shield-reduced explosion damage to health, score, and credit accounting.
- Online Match now performs first-pass client-side protocol compatibility negotiation before sending join/input messages, handles protocol handshake errors without reconnect loops, and surfaces protocol/schema status in the network diagnostics panel.
- Online Match and Server Browser now share first-pass fatal server error copy through `NetworkAdapter`, so password/auth/full-server failures do not enter automatic reconnect loops.
- The Python WebSocket gateway can now enforce an optional join password and returns `invalid_password`, making the Godot password rejection path testable against a real gateway scaffold.
- The Godot client can now send an optional join `auth_token`, and the Python WebSocket gateway can enforce it with `authentication_failed`, making the auth rejection path testable against a real gateway scaffold.
- The Godot server directory now validates and preserves optional `auth_token` values, allowing local/HTTP directory fixtures to exercise authenticated join rejection without hand-editing the Online Match entry.
- The Python WebSocket gateway can now enforce an optional joined-player capacity and returns `server_full`, making the Godot full-server rejection path testable against a real gateway scaffold.
- The Python WebSocket gateway now assigns reusable unique player numbers for joined sessions and includes the assigned number in snapshots, moving capacity from a raw connection counter toward player-slot semantics.
- WebSocket snapshots now include `max_players` and `players_connected` alongside the assigned `player_number`, so the replicated online state carries current join-capacity metadata after `hello`.
- The Python WebSocket gateway can now close new joins and returns `server_closed`, making the Godot closed-server recovery path testable against a real gateway scaffold.
- The Python WebSocket gateway can now enforce a first-pass player-name ban list and returns `banned`, making the Godot ban recovery path testable against a real gateway scaffold.
- Gateway compatibility coverage now includes an actual TCP/WebSocket transport round trip with real handshake/framing, password rejection, join, input, ping, and disconnect handling in addition to direct session-level contract tests.
- Browser runtime QA now covers real exported-web-to-gateway join failure paths for `invalid_password`, `authentication_failed`, `server_full`, `server_closed`, and `banned`, including user-facing fatal status and no reconnect loop, and also covers the no-store `session_token_url` success path against a local `--session-secret` gateway.
- Server directory schema `1` is now documented and enforced in Godot for HTTP and local fallback payloads, including required server fields, boolean password flags, source validation, and WebSocket-only online endpoints.
- The local `groundfire-directory` service now enforces the same public-entry shape before serving listings, filters invalid/non-WebSocket online entries, rejects embedded static `auth_token` entries by default unless `--allow-static-auth-tokens` is explicitly enabled for private/dev directories, keeps LAN entries out of public payloads unless explicitly enabled, emits quoted ETags, and accepts quoted, comma-listed, or legacy unquoted `If-None-Match` tokens for production-shaped `304` refreshes.
- The local `groundfire-directory` service now exposes production-style `/healthz` and `/diagnostics.json` endpoints with served, filtered LAN, invalid server, and invalid injected-gateway counts.
- Server directory configuration now has a first environment model: `application/config/server_directory_url` can override everything, otherwise the selected `application/config/server_directory_environment` chooses the dev/staging/production URL setting, with local JSON fallback when empty.
- Options now has first-pass online directory controls for choosing the server directory environment and editing override/dev/staging/production URLs without editing `project.godot` by hand; invalid non-HTTP(S) directory URLs are diagnosed and fall back locally.
- Build/runtime documentation exists in the `Build And Runtime` section.
- The migration document now has a validated fidelity contract and per-area annotation blocks so future Godot implementation work starts from Python/Pygame behavior instead of redesigning the user experience.
- A local production-shaped directory service now exists as `groundfire-directory`, giving the Godot Server Browser a real HTTP schema `1` endpoint to test against before a public hosted directory is chosen.
- Server Browser now reports HTTP directory cache/ETag/refresh metadata from production-shaped directory responses and uses first-pass classic table-header styling.
- Server Browser now performs conditional HTTP directory refreshes with `If-None-Match`, reuses cached entries on `304 Not Modified`, and exposes that path in exported browser runtime QA.
- Local Match HUD now uses the same Pygame-facing angle and power ranges as the tank model, and projectile edge explosions clamp terrain lookup to the playable map edge.
- Main Menu runtime smoke now covers several classic/wide/ultrawide viewport sizes for logo/button metric regressions.
- Release validation now has a single local gate script, while CI/publishing policy remains to be wired.
- The Python WebSocket gateway now assigns stable per-session player numbers from reusable join slots, advertises the player number in snapshots, and keeps capacity semantics tied to occupied player slots instead of only a counter.
- The local `groundfire-directory` service now filters invalid schema `1` public entries, rejects non-WebSocket online endpoints, and ignores invalid injected gateway endpoints before serving browser-visible listings.
- Server Browser row handling now tolerates malformed player/latency strings, adds row tooltips, and shows source/player/full/password/missing-directory details in the selected-row status copy.
- `ControlSettings` now uses an explicit classic-facing action order for Options binding lists instead of relying on dictionary iteration order.
- `ControlSettings`, `project.godot`, Local Match registration, Online Match snapshots, and gateway validation now include the classic Shield input path (`gf_shield` / `shield`) for protocol parity with the Python command set.
- Runtime smoke now covers Options classic preset rows, Local Match setup, and desktop Dedicated Server tool focus/layout entry points across small, classic, and wide viewport sizes.
- Browser visual QA now captures the Local Match setup route in addition to Main Menu, Options, Server Browser, and Local Match, and `--check` now fails on missing approved goldens instead of silently accepting a new screenshot.
- Godot validation script and Python scaffold tests.

## What Still Needs To Be Done

> [!IMPORTANT]
> **Resumo de Pendências e Estado de Fidelidade**
> 
> O marco de release Godot atual está aprovado pelos gates locais e não deve mais ser descrito como bloqueado por pendências genéricas de gameplay, HUD/input ou fluxos clássicos. Vários itens que antes eram lacunas amplas agora têm regressões Godot/Python ou QA de navegador. O que ainda fica aberto deve ser tratado como auditoria específica, implantação pública futura, ou prova visual manual contra a referência Pygame:
> 
> * **Coberto pelo gate atual**: terreno, colisões, vento/HUD, mira opcional por mouse, foco por teclado/controle, score/shop/winner, armas principais, áudio local, runtime de navegador, diretório HTTP schema `1`, cache `304`, persistência web, gateway WebSocket simulado, empacotamento e SHA256.
> * **Visual Parity**: `scripts/qa_godot_web.sh --check` compara capturas Godot contra goldens Godot aprovados em `docs/references/godot_browser_visual/`. As referências Pygame em `docs/references/pygame_visual/` continuam sendo o alvo autoritativo de revisão antes de atualizar goldens; o gate atual não é uma comparação pixel-a-pixel automática Godot-versus-Pygame.
> * **Online/Produção**: escolher endpoints públicos reais, hospedar o issuer `/session-token.json` atrás da política final de conta/sessão, manter `auth_token` estático bloqueado nos diretórios públicos por padrão, expandir QA contra diretórios hospedados e conectar/deployar o gateway WebSocket no runtime de servidor definitivo.
> * **Fidelidade futura**: abrir trabalho apenas para deltas nomeados contra fonte/captura Pygame, como uma tela específica, um timing path específico, um edge case multiplayer, economia/fuel-reserve, item futuro ou comportamento ainda sem regressão.
> * **Release/CI**: definir política de publicação, hospedagem, assinaturas digitais e quais gates pesados de navegador/rede devem bloquear CI regular versus execução manual.
> 
> **Resumo honesto**: o marco validado está pronto para distribuição local conforme os gates registrados. O que não deve ser afirmado é que há uma prova matemática ou automática de 100% de pixels contra Pygame para todo o cliente; essa afirmação exige revisão direta das referências Pygame ou um novo comparador dedicado.

### 1. Main Menu Visual Parity

The Godot menu is functional, but it is not yet a faithful match for the classic Pygame menu.

Remaining work:

Fidelity annotations:

- `Fidelity target:` `src/mainmenu.py`, `src/menu.py`, `src/optionmenu.py`, `src/playermenu.py`, `src/setcontrolsmenu.py`, `data/logo.png`, `data/menuback.png`, and `docs/references/pygame_visual/main_menu.png` / `options.png`.
- `User-visible invariants:` Menu order, copy, logo/background placement, button geometry, focus/hover behavior, setup flow, and options behavior must remain recognizably Pygame-faithful.
- `Allowed Godot adaptation:` Responsive scaling and hiding native-only server tools in web builds according to the `Web Feature Rule`.
- `Required validation:` Compare against the Pygame captures, run `scripts/validate_godot_migration_contract.py`, `scripts/validate_godot_fidelity.sh`, and browser visual QA when menu pixels change.

- Continue comparing against the original menu screenshot and tune exact logo position, size, and spacing; named 1024x768 reference metrics, bounded viewport scaling, and source-aspect logo sizing now exist, but final screenshot matching remains.
- Continue matching button width, height, typography, focus state, and disabled state; the main menu now uses the Pygame reference logo/version/copyright/button stack, classic brown/black surfaces, a closer flush button stack inside the classic panel, Pygame-style shadow/outline text, and yellow hover/pressed text for classic buttons, but exact font-atlas glyph metrics and disabled/focus parity remain.
- Continue testing desktop and web scaling at 16:9, 4:3, ultrawide, and small browser windows; runtime Main Menu metric smoke coverage now exists for common small/classic/wide/ultrawide sizes, Options/setup/dedicated entry points now have small/classic/wide smoke coverage, and browser visual QA now captures the Local Match setup route through `?screen=local_match_setup`, but final screenshot review still needs approved parity decisions against the Pygame references.
- Continue expanding Options into final classic parity; richer video/audio/gameplay settings, classic-facing Resolution/Screen Mode preset rows, Set Controls jump, Apply/Back actions, classic text shadow/outline treatment, pause access, and grouped Video/Audio/Gameplay/Online/Controls panels now exist, but exact selector triangle styling, font-atlas glyph metrics, and final layout polish remain.
- Continue adding the remaining Python/Pygame menu routes; the desktop dedicated gateway route now includes first-pass join-policy administration with a live policy summary, launch/stop lifecycle controls, copyable WebSocket endpoint handling, non-secret setting persistence, masked command preview/copy support, and disabled-action focus skipping, and Local Match setup now has an eight-slot roster grid with active slots, player type, unique human controller assignment, editable names, round selection, dynamic focus wiring, and clearer readiness/blocking copy including the no-human case, but final roster UX polish and final server administration parity still need work.

### 2. Server Browser Final Visual Parity

The Server Browser has real behavior now, but it still needs final visual and interaction polish.

Remaining work:

Fidelity annotations:

- `Fidelity target:` `src/serverbrowsermenu.py`, `conf/servers.json`, server browser fixtures, and `docs/references/pygame_visual/server_browser.png`.
- `User-visible invariants:` Table scanability, tabs, row states, connection feedback, favorites/history behavior, password prompt, and failure recovery must feel like the Pygame browser for supported platforms.
- `Allowed Godot adaptation:` Browser-safe persistence, HTTP/WebSocket directory plumbing, and hidden LAN/native-only affordances on web builds.
- `Required validation:` Run server browser Python/Godot tests, compare against the Pygame browser capture, and run browser QA for exported web behavior.

- Continue tuning table column widths, row heights, tab spacing, header styling, and scrollbar placement against the reference UI; first-pass named table dimensions, scroll modes, and table-header chrome now exist, but final visual parity still needs reference screenshot tuning.
- Continue improving hover, selected, disabled, loading, error, and empty states; full-viewport browser layout, classic brown buttons, transparent row states, table selection/focus, row tooltips, selected-row detail copy, tab-specific empty messages, disabled connect/favorite/history actions, undo copy, visible table loading rows, defensive player/latency parsing, online-directory duplicate-refresh protection, and `304 Not Modified` cached refresh reuse now exist, but final Pygame table chrome and inline-filter removal/tuning still need work.
- Continue refining richer filters; passwordless, open-slot, sort controls, and persistence now exist, but final visual/interaction parity is still pending.
- Continue final Favorites and History polish; favorite removal, clear-history, empty-history disabled state, undo restore copy, history-backed favorite details, and missing-directory favorite fallback rows now exist, but final stale/deleted-server production semantics still need tuning.
- Continue password/connect modal polish; shared fatal error copy plus real gateway `invalid_password`, `authentication_failed`, `server_full`, `server_closed`, and `banned` responses now exist, but the final modal flow still needs production server feedback and visual polish.
- Continue testing responsive behavior in the Godot web export size constraints; proportional table widths, bounded scroll height, and 640x480/1024x768/1600x900 runtime smoke coverage now exist, but final exported-browser screenshot review remains.

### 3. Real Online Server Directory

The browser can load from HTTP and a local production-shaped service exists, but the public hosted service/endpoints are not chosen yet.

Remaining work:

Fidelity annotations:

- `Fidelity target:` Existing Pygame/LAN server browser expectations, `conf/servers.json`, `src/serverbrowsermenu.py`, and the documented `Server Directory Schema`.
- `User-visible invariants:` Server list fields, password/auth expectations, visible availability, failure messages, and offline fallback behavior must not surprise players used to the Pygame flow.
- `Allowed Godot adaptation:` A browser-safe read-only HTTP directory may replace native discovery for web while desktop keeps native-capable routes where supported.
- `Required validation:` Validate schema `1`, fallback diagnostics, browser runtime QA, and production-like directory behavior before public server listings are trusted.

- Promote the documented and client-validated server directory schema `1` into the real public service contract.
- Choose and host the public read-only HTTP endpoint; a local stdlib `groundfire-directory` service now serves schema `1` with cache/quoted-ETag/refresh headers, conditional `304` handling, optional valid gateway injection, public-entry filtering for invalid/non-WebSocket online entries, default rejection of static directory-carried `auth_token`, HTTP(S) validation for `session_token_url`, `/healthz`/`/diagnostics.json`, and opt-in no-store `/session-token.json` signed-token issuance advertised through `session_token_url`, while the Godot client now exercises conditional `If-None-Match` refreshes and cached `304` reuse, but no public dev/staging/production URL has been selected.
- Fill the real dev, staging, and production values for `application/config/server_directory_url_dev`, `application/config/server_directory_url_staging`, and `application/config/server_directory_url_production`; the client-side environment selection, Options controls, user persistence, and override path now exist.
- Continue improving directory diagnostics; timeout, one retry, HTTP result diagnostics, schema diagnostics, cache/ETag/refresh diagnostics, invalid URL diagnostics, invalid-payload fallback, local service health/diagnostics endpoints, and fallback messaging are implemented, but final user-facing copy still needs polish once the public service behavior is known.
- Keep public authenticated listings on the signed `/session-token.json` flow plus production account/session policy; the service now rejects static directory-carried `auth_token` by default, with explicit `--allow-static-auth-tokens` reserved for private/dev directories only.
- Keep the local JSON fallback for offline development.
- Later, add presence and latency updates through WebSocket or WebRTC-compatible infrastructure.
- Expand the new browser runtime QA from the served schema `1` fixture, first-pass cache/refresh header checks, and local `304 Not Modified` conditional refresh checks to production-like public directory behavior under real hosting.

### 4. Local Match Gameplay Fidelity

The Local Match is now playable as a prototype, but it is not yet Groundfire gameplay.

Remaining work:

Fidelity annotations:

- `Fidelity target:` `src/game.py`, `src/gamesession.py`, `src/landscape.py`, `src/tank.py`, `src/player.py`, `src/aiplayer.py`, `src/scoremenu.py`, `src/shopmenu.py`, `src/winnermenu.py`, `src/quake.py`, and weapon scripts under `src/`.
- `User-visible invariants:` Terrain behavior, tank movement, shot feel, weapons, damage, turns, score, economy, shop, round transitions, winner flow, AI behavior, sound timing, and camera/gameplay feel must match the Pygame client as closely as possible.
- `Allowed Godot adaptation:` Internal scene/model organization, renderer implementation, and browser-safe runtime constraints may differ if the visible and playable outcome stays faithful.
- `Required validation:` Run `scripts/validate_godot_fidelity.sh`, targeted Godot fidelity checks, Python reference tests, and manual/visual comparison against Pygame gameplay captures when behavior changes.

- Continue improving the original-style terrain model until it fully matches Python `Landscape`; edge-colour interpolation for crater top/bottom cuts, near-exact uniform-colour merge checks, stacked-chunk `move_to_ground` selection, linked superblock fall/merge, independent left/right falling-superblock landing gaps, current-frame fall speed with next-frame acceleration, falling wait speed preservation and whole-tick motion deferral, falling-support motion inheritance on landing, uniform falling-support merge motion preservation, first linked-support cut propagation, linked-removal top propagation, integrated removed-linked-cap crater-edge continuation, mirrored falling removed-linked-cap support-motion propagation, mirrored one-sided removed-linked-cap asymmetric top promotion, mirrored removed-linked-cap surviving-opposite-side top promotion, mirrored one-sided and two-sided top-edge clipping including explicit endpoint-code `top_code = 6`/`9`, mirrored linked top-only support preservation, mirrored non-linked bottom-edge fall starts including explicit `bottom_code = 3`/`12`, unlinked `bottom_code = 6`/`9`/`11`/`14`, and unlinked `bottom_code = 7`/`13`/`15`, one-sided and two-sided linked-bottom support detachment, mirrored one-sided linked-bottom uncut-side adjustment, asymmetric one-sided split remainder preservation, linked double-split lower support preservation, linked-support double-split leader fall-start propagation, falling linked-support double-split leader-motion handoff, falling-split motion handoff, falling linked double-split support-motion handoff, the mirrored multi-chunk classic linked-superblock edge-graze skip guard, minimum-land crater floor clamping, first-pass terrain dropping, first-pass quake wiring, classic first/between quake timing, and looped quake rumble playback now exist, but the remaining split clipping edge cases and tuning still need fidelity work.
- Continue porting the full original tank state model; the Godot `TankState` now has movement, active fuel plus persistent reserve, health, slope angle, launch origin/velocity, classic-style tank-center launch geometry, named round-start defaults with initially ungrounded and level-angle round reset, passive steep-slope sliding with the classic signed direction, grounded input combined with signed slope-slide movement, cos-projected along-slope `x`/`y` displacement coverage, no ground-movement fuel spend, airborne non-boost input ignored, airborne angle preservation until landing, `move_to_ground`-based stacked support landing, slope-aware jump jets with in-air boost rotation, looped classic audio, and classic boost exhaust smoke, tuned airborne gravity, terrain-gap detachment, playable-bound edge stopping, airborne launch velocity inheritance, first-pass fuel-draining shield damage reduction, classic `-75..75` gun angle semantics, classic `10` default power, immediate release stop, exact-zero death semantics, and classic textured dead-tank burn smoke.
- Improve projectile physics, crater generation, and explosion damage fidelity; exact terrain segment collision, collinear/boundary chunk-edge collision, edge-clamped out-of-world explosion lookup, full direct-hit tank damage before splash falloff, named projectile gravity, splash damage, symmetric two-side damage scoring, and first-pass turn wind/gust effects are implemented, but remaining collision edge cases, wind tuning, gravity tuning, and damage tuning are not final.
- Complete original weapon behavior; `WeaponInventory` now has Shell, Machine Gun, MIRV, Missile, and Nuke definitions, plus classic Shell fallback when limited ammo is depleted, Machine Gun direct-hit tracer behavior with centralized ammo/volley/cooldown constants, player held-fire cadence, AI staged-burst cadence, named-ammo consumption, looping classic firing audio, weapon-cycle unselect handling, first-pass tactical AI hold budgets, classic cooldown-gated first-tracer timing, fixed classic tracer launch power, gravity-matched launch-age trajectory stepping, `0.01s` classic tracer tails, pre-shot unselect cancellation, lethal-hit stop/queued-tracer expiry, and first full-roster direct-hit validation, a closer apex/five-fragment MIRV split with centralized ammo/fragment/spread constants, Python-faithful vertical no-fan-out spread, parent expiry, intra-frame split positioning, and split-frame fragment stepping protection, named fuel-limited Missile steering with unclamped classic angle-speed powered velocity and next-frame free-fall transition, classic fire-shell/missile-launch one-shot audio, powered Missile flight loop audio, and first-pass Nuke blast/whiteout/audio tuning. Final classic weapon tuning and full-match edge cases still need work.
- Continue full round flow fidelity; turn ownership, wins, reset, an initial post-round score/shop flow, classic defeat/leader/survival/stipend score and money awards, previous-round leader flags, score-screen leader reassignment, self-defeat scoring, score-screen translucent column boxes, white total-score text, player tank icons, defeated-tank icons with leader flags, a first final-round winner overlay with separate `Final Result` heading, top-score/tie winner marking, classic centered winner-only tank-card rows with white rotating-letter emphasis, classic 2-second human and 4-second computer activation delays for score/final overlays, roster-backed combatants, nearest-live-target selection, surviving-participant turn rotation, roster-aware HUD target/leader context, roster-backed score ranking and winner selection, human-focused shop passes with automatic computer purchases, defeated-player details, classic purchase bundle sizes separated from round-start ammo, classic shop input delay cadence, classic shop ordering/copy, separate `$cost` shop column, non-duplicated `Buy` actions, classic `$N` shop money copy, full classic catalog rows, Jump Jet fuel-reserve purchasing, visible reserve economy state, and next-round shop labels now exist; final classic score/winner art tuning, exact multi-player semantics/tuning, exact economy/fuel-reserve tuning, and final future-item tuning are not done.
- Add better AI decision logic; the first trajectory-search shell aiming pass, strategic weapon choice, risk/reward special-weapon scoring, self-damage avoidance, and easy/normal/hard difficulty tuning exist, but final personality tuning is still pending.
- Continue camera behavior, zoom/framing, and map bounds; projectile lookahead and explosion shake now exist, but final original framing feel and tuning are not done.
- Bring over the final score, economy, shop, and end-of-round screen fidelity; first playable score/shop/economy scaffolds, roster-backed score ranking/detail rows with classic translucent column boxes, white total-score text, player tank icons plus defeated-tank/leader-flag icons, a first winner overlay with centered winner-only tank cards and white rotating `Winner!` letters, visible reserve economy state, human-focused shop passes with automatic computer purchases, and a classic-ordered full shop catalog with `Done!` completion now exist, but final classic art tuning, simultaneous classic shop behavior, final future-item tuning, and final presentation still need migration.

### 5. Input And HUD Completion

Input and HUD are only at the first useful layer.

Remaining work:

Fidelity annotations:

- `Fidelity target:` `src/weaponhud.py`, `src/gamehudrenderer.py`, `src/controls.py`, `src/controlsfile.py`, `src/controllermenu.py`, `data/weaponicons.png`, and current Pygame HUD/menu captures.
- `User-visible invariants:` Control defaults, rebinding expectations, controller navigation, HUD information density, weapon display, messages, pause/options access, and input timing must stay Pygame-faithful.
- `Allowed Godot adaptation:` Godot input event plumbing and per-device gamepad profiles may be used behind equivalent player-facing bindings.
- `Required validation:` Run input/HUD Godot checks, controller/menu focus smoke coverage, and compare HUD/status presentation against Pygame captures.

- Polish controls configuration UI; `ControlSettings` persists keyboard and gamepad bindings, exposes an explicit classic-facing action order including Shield, and Options supports keyboard/gamepad capture, reset, cancel, default gamepad bindings, keyboard/gamepad conflict reporting, per-device gamepad profiles, and a scrollable controls list.
- Polish optional mouse aiming support; pointer aiming, reticle drawing, and left-click firing now exist behind an off-by-default setting, but final cursor/reticle feel still needs tuning.
- Complete full controller/menu navigation polish; gamepad capture, controller-side capture cancellation, per-device profiles, main-menu/pause/server-browser/options/dedicated-tool/online-match focus neighbors and row selection, disabled-action skipping in Server Browser and Dedicated Server tools, pause/shop horizontal self-loops, Local Match setup dynamic roster focus, and score/final self-focus/cancel handling now exist, but final focus-neighbor tuning across every screen is still pending.
- Build the remaining original weapon HUD details; the current combat HUD now matches the classic compact card shape for HP, fuel, tank color, selected weapon icon, Machine Gun ammo strip, Missile stock marks, Pygame-facing angle/power ranges, tested classic card/bar/icon world-coordinate geometry, and tested center-anchored/size-scaled gun-arrow geometry, but final pixel tuning, font-atlas text behavior, and any missing classic status overlays still need reference comparison.
- Show angle, power, wind, HP, round messages, score, and shop state in the final visual style; the in-round HUD has moved back to the compact Pygame presentation and classic angle/power display scale, but non-combat overlays and exact feedback timing still need reference tuning.
- Expand pause/menu behavior; Local Match has a first overlay with resume focus, options access that preserves the paused match context, restart round, main menu, vertical focus neighbors, and the score/final modal flow now has stable single-action focus/cancel behavior, but final styling and broader in-match settings presentation still need polish.

### 6. Networked Gameplay Adapter

The browser-safe online path now connects through WebSocket and a Python gateway scaffold, but it is not yet the production multiplayer runtime.

Remaining work:

Fidelity annotations:

- `Fidelity target:` `groundfire/server.py`, `groundfire_net/`, `src/networkprotocol.py`, `src/networkstate.py`, and the Pygame multiplayer/server browser behavior.
- `User-visible invariants:` Joining, reconnect/recovery, snapshots, player state, match state, errors, and admin/server flows must preserve classic expectations for the same supported platform capability.
- `Allowed Godot adaptation:` WebSocket/WebRTC-compatible transport may replace native-only network paths in web builds; desktop-only UDP/LAN affordances remain gated by platform capability.
- `Required validation:` Run gateway contract tests, replicated-scene tests, browser runtime QA, and compatibility checks before changing online-visible behavior.

- Continue freezing the live protocol shape for the Godot client and Python server; protocol metadata, gateway-side envelope/input-command validation, supported-version advertisement, client-side compatibility negotiation, snapshot/event schema metadata, and first schema documentation now exist, but the final full-server `match_snapshot` shape and future compatibility policy are still pending.
- Promote the WebSocket gameplay path beyond first-pass integration; Server Browser routes to Online Match, the Python gateway emits `MatchSnapshot` payloads with player number/capacity metadata, and Godot renders terrain/entities/projectiles/effects/players with interpolation, projectile extrapolation, prediction diagnostics, and local tank reconciliation, but full fidelity and reconciliation are still early.
- Optionally keep UDP transport for desktop-only builds.
- Finish production-grade failure flows; reconnect/backoff, manual reconnect/back controls, latency display, ack pruning, stale pending-input diagnostics, closed-connection reporting, first-pass fatal password/auth/full-server/closed-server/ban handling, optional gateway password rejection, optional static auth-token rejection, signed expiring gateway join tokens, reusable player-slot capacity assignment, optional closed-join mode, optional player-name ban rejection, and desktop launcher controls for those first-pass gateway policies exist, but final retry policy, production error taxonomy, hosted account/session token issuance, production ban persistence/administration, and user recovery paths still need polish.
- Adapt the full `groundfire.server` runtime to the browser-safe gateway; the gateway currently drives the shared Python simulation scaffolds, not the complete classic server runtime.
- Expand compatibility tests between the Python gateway/server and Godot message contract; gateway tests now cover hello, join, input, ping, errors, replicated tank movement, terrain revision, events, and a real TCP/WebSocket handshake/framing round trip, but browser-level end-to-end gameplay tests are still missing.

### 7. Export And Runtime Validation

The project validates in editor/headless mode, runs runtime scene smoke checks, documents the build/runtime path, produces local Linux/Web exports through `scripts/export_godot.sh`, packages release artifacts, verifies SHA256 checksums, and has exported-browser runtime plus screenshot QA. The local release gate has passed for version `0.25.0`; remaining release work is publishing policy, signing policy, hosted-directory deployment, and CI/tag promotion rather than a blocker for the validated local release slice.

Follow-up work:

Fidelity annotations:

- `Fidelity target:` The validated Python/Pygame source tree, `docs/references/pygame_visual/`, release scripts, and the build/runtime expectations documented here.
- `User-visible invariants:` Released Godot artifacts must not regress supported Pygame-visible flows, assets, controls, networking expectations, or browser/desktop feature boundaries.
- `Allowed Godot adaptation:` CI/export/package mechanics may change as long as they keep the same fidelity gates and platform separation.
- `Required validation:` Run migration contract validation, Godot validation, fidelity tests, browser QA, release packaging checksums, and manual desktop smoke coverage before release.

- Promote `scripts/validate_godot_release.sh` and `scripts/package_godot_release.sh` into the official release/tag process; version sourcing, release notes metadata, checksums, versioned artifact names, a local release gate, and a Linux GitHub Actions release-gate job now exist, with manual CI options for browser QA and packaging, but artifact publishing policy is not finalized.
- Expand browser-driven QA beyond the current runtime fixture to exercise production directory cache behavior under real hosting and user-visible recovery flows; local browser QA now validates the exported client's `If-None-Match` request path and cached `304 Not Modified` handling against the QA server, and screenshot `--check` now requires an approved golden for every captured route.
- Add approved `docs/references/godot_visual/` goldens with a capture backend that can read viewport pixels; `scripts/validate_godot_visuals.sh` now fails cleanly under the current dummy headless renderer when viewport capture is unavailable. Then decide whether `--check` should join default validation or remain an optional pre-release visual gate.
- Finish hardening CI/release-gate coverage for `scripts/qa_godot_web.sh` where Chromium/Chrome and export templates are available; a manual workflow-dispatch path now installs export templates and can run browser QA, but the project still needs final policy on when that heavier gate blocks every PR/tag.
- Validate desktop build behavior manually or with a windowed smoke harness for LAN/server tools beyond the deterministic feature matrix; headless runtime smoke now reaches the Dedicated Server tool route and its focus wiring, but not a full launched desktop gateway session.
- Promote the documented release verification, checksum, signing, hosting, and distribution policy into the final CI/release checklist once publishing infrastructure is chosen.

## Recommended Next Large Batch

Every recommended batch inherits the `Migration Fidelity Contract`. Do not use these batches as redesign opportunities; each implementation step should copy the Pygame-facing behavior, record the relevant `Fidelity target:`, and pass the required validation before being marked complete.

The next big but controlled batch should focus on `Local Match Fidelity 2`:

1. Continue the `Landscape.clip_slice` fidelity pass by matching remaining clipping and landing edge cases against the Python implementation; independent left/right falling-superblock landing, classic fall acceleration ordering, falling wait speed preservation and whole-tick motion deferral, falling-support motion inheritance on landing, uniform falling-support merge motion preservation, first linked-support cut propagation, linked-removal top propagation, integrated removed-linked-cap crater-edge continuation, mirrored falling removed-linked-cap support-motion propagation, mirrored one-sided removed-linked-cap asymmetric top promotion, mirrored removed-linked-cap surviving-opposite-side top promotion, mirrored one-sided and two-sided top-edge clipping including explicit endpoint-code `top_code = 6`/`9`, mirrored linked top-only support preservation, mirrored non-linked bottom-edge fall starts including explicit `bottom_code = 3`/`12`, unlinked `bottom_code = 6`/`9`/`11`/`14`, and unlinked `bottom_code = 7`/`13`/`15`, one-sided and two-sided linked-bottom support detachment, asymmetric one-sided split remainder preservation, linked double-split lower support preservation, linked-support double-split leader fall-start propagation, falling linked-support double-split leader-motion handoff, falling-split motion handoff, falling linked double-split support-motion handoff, the mirrored multi-chunk linked-superblock edge-graze skip guard, minimum-land crater floor clamping, stacked-chunk `move_to_ground` terrain selection, multi-chunk superblock merge landing (`end_super_idx != start_super_idx`), non-compatible color landing (`Landscape.update` lines 190-198), mirrored multi-chunk linked-superblock edge-graze chain skips, and mirrored single-sided middle-crater graze noop guards now exist. The `Landscape.clip_slice` behavior is fully ported and covered. Tank-ground integration tuning still needs parity.
2. Continue controller polish with final focus-neighbor tuning across remaining menus and final menu navigation passes; Main Menu, Options classic preset rows, Server Browser action/table focus, Dedicated Server tools, Online Match header controls, Local Match setup dynamic roster focus, shop vertical/horizontal controls, score, and final-result overlays now have first-pass focus coverage.
3. Continue improving Online Match interpolation quality, replicated projectile fidelity, prediction, and HUD polish; first-pass prediction, prediction-error diagnostics, projectile extrapolation, and network diagnostics now exist.
4. Continue tuning landing edge cases and final projectile scale against the original Python/C++ feel; classic gun angle/power defaults/bounds, acceleration/release-stop, passive steep-slope sliding, cos-projected grounded slope movement, `move_to_ground`-based stacked support landing, slope-aware jump jet thrust, in-air boost rotation, looped classic jump-jet audio, classic boost exhaust smoke, tuned airborne gravity, terrain-gap detachment, playable-bound edge stopping, tank-owned projectile launch velocity inheritance, classic-style launch-origin geometry, center-anchored/size-scaled gun-arrow visual geometry, and textured dead-tank burn smoke now exist.
5. Continue tuning Nuke beyond the first whiteout/audio pass, keep validating Machine Gun against full-match classic turn flow beyond the fixed-power/cooldown-gated tracer launch, looped audio, weapon-cycle unselect, pre-shot cancellation, lethal-hit stop handling, and first-pass AI tactical hold paths, and keep tuning MIRV/Missile details beyond the current intra-frame apex/five-fragment split with protected split-frame fragment stepping and unclamped fuel-limited steering.
6. Continue tuning AI personality after the new risk/reward weapon scoring pass and auto-shop priorities; the AI now avoids self-damaging Nukes, ranks specials by expected value, and spends inter-round credits by difficulty, but final classic aggression/personality tuning still needs playtest calibration.
7. Replace the first score/shop scaffold with faithful end-of-round, score, economy, winner, and shop screens; classic defeat/leader/survival/stipend awards, previous-round leader flags, score-screen leader reassignment, self-defeat penalty, score-screen translucent column boxes, white total-score text, player tank icons, defeated-tank icons and leader flags, classic weapon bundle sizes, classic shop ordering/copy with `Done!`, classic shop input delays, separate `$cost` shop column, non-duplicated `Buy` actions, classic `$N` shop money copy, first-pass legacy catalog behavior, closer Jump Jet fuel-reserve purchasing, visible reserve economy state, a separate score overlay, roster-backed score rows and final-result winner selection, final `Final Result` heading, final top-score/tie winner marking, centered winner-only tank-card rows with white rotating-letter emphasis, human/computer activation delays, human-focused shop passes with automatic computer purchases, next-round shop labels, and a first final-result overlay are now started, but final classic art tuning, simultaneous classic shop behavior, exact economy/fuel-reserve tuning, and final future-item tuning still need migration.

### Local Match Fidelity 2 Execution Checklist

Use this checklist to keep the next batch narrow and reviewable:

1. Pick one Pygame reference surface per change: `Landscape.clip_slice`/`Landscape.update`, `Tank.move_tank`, a single weapon entity, one score/shop menu behavior, or one HUD/focus route. Do not mix terrain, weapon, AI, and release work in one patch unless a test proves they are coupled.
2. Add or extend the closest regression first. Prefer Godot tests under `godot/tests/local_match_fidelity_check.gd` for scene-visible behavior, Python reference tests under `tests/test_landscape_fidelity.py` or `tests/test_port_fidelity.py` for source-of-truth behavior, and scaffold assertions only for wiring that cannot be executed headlessly yet.
3. Update the status bullets in this document in the same patch as the implementation. Each update should say what now exists and what remains non-final, so this file stays a migration map instead of a changelog that implies completion too early.
4. Run `scripts/validate_godot_fidelity.sh` before treating any Local Match parity change as stable. If shared Python/gateway code changed, also run `CI=1 .venv/bin/python scripts/run_quality_checks.py`.
5. When a visual change is intentional, compare against `docs/references/pygame_visual/` first, then refresh Godot browser/headless goldens only after deciding the change improves Pygame parity.

Acceptance criteria for this batch:

- Terrain clipping and falling cases added during the batch have named Python reference cases and matching Godot assertions.
- Tank movement, projectile, shield, and weapon tuning changes preserve the classic-facing angle/power/fuel/health ranges already documented here.
- Score, shop, winner, and HUD changes keep roster-backed multi-player behavior working for at least one human-vs-computer and one multi-combatant test path.
- Browser-safe feature gates remain unchanged unless this document updates the `Web Feature Rule` first.

Avoid mixing this with the full online protocol or final release hardening in the same batch. Those should come after the local gameplay loop is stronger.

## Next Agent Handoff

This section is the practical handoff for the next agent that opens this repository. The migration strategy above is current as of this document update, but the working tree is already carrying many Godot, Python gateway, QA, reference, and documentation changes. Current verified state:

- Latest menu/options visual slices: Main Menu button rows now sit flush inside the classic black panel instead of keeping the extra Godot-only inset, and Options now starts with a Pygame-style preset block for `Resolution:`, `Screen Mode:`, `Set Controls`, `Apply`, and `Back` while retaining the richer scrollable Godot settings below. Runtime smoke now checks this classic preset focus route and viewport bounds across small/classic/wide sizes, and the browser visual goldens were refreshed after comparing that layout change against the Pygame menu/options references. The newest pass adds shared classic text shadow/outline theme metadata to Main Menu/Options titles, copy labels, classic preset labels, and classic buttons, plus yellow hover/pressed font color for classic buttons; runtime smoke now asserts those theme items on actual controls.
- Latest completed implementation slices: TerrainModel crater clipping now has explicit coverage for the classic `top_code = 11` and `top_code = 14` cases in Python `Landscape.clip_slice` lines 291-298, lowering both top edges to the crater bottom and discarding the top portion above the crater on both sides, verified by parallel Python and Godot regressions. Local Match dead tanks now start the Python `Tank.burn()` exhaust timer on death and spawn smoke particles with paired Python/Godot regressions for both ground and airborne smoke cadence, offset, velocity, texture id, rotation, growth, fade metadata, and textured draw geometry from the classic `smoke.png` asset. Jump jets now play the classic looped `jumpjets.wav` during valid alive/fueled boost input and stop on release, invalid boost, phase changes, restart, or shutdown; they also emit the classic boost exhaust smoke with `texture_id = 2`, `0.05s` cadence, no rotation/growth, `2.5` fade, and pre-thrust velocity metadata. The terrain fidelity pass also now has explicit Godot/Python regressions for Python `Landscape.clip_slice` endpoint-code `top_code = 6`/`9` top cuts, linked-support split leader-motion handoff, crater edge-colour interpolation, near-exact falling-merge colour equality, and `Landscape.move_to_ground` stacked-chunk selection, preserving the classic lower clipped remainder when neither top endpoint is inside the blast, proving that lower support remainders inherit fall wait/speed from the linked superblock leader even if the support chunk itself was resting, keeping top/bottom cut colours on the original vertical gradient, preventing close-but-not-identical terrain colours from merging, and letting `TankState` settle onto lower reachable support terrain instead of snapping to a suspended cap. The score overlay now includes classic translucent per-row column boxes, white total-score text, player tank icons, defeated-player tank icons, and leader flags in the scoring column. The final-result overlay now uses centered winner-only tank-card rows with white rotating `Winner!` letters over the classic scrolling tiled menu background, matching the Pygame `WinnerMenu` instead of showing an added modal panel, ranking table, summary line, or visible exit button. The online production-hardening pass now adds signed expiring gateway join tokens with `--session-secret`, player-bound HMAC validation, `auth_token_mode` discovery, `--issue-token` generation, and opt-in no-store `groundfire-directory /session-token.json` issuance while keeping the older static `auth_token` fixture path compatible. Online Match now waits for join/session-token completion before sending gameplay input, and the Python gateway rejects pre-join input with `not_joined`. The public directory service now rejects static directory-carried `auth_token` entries by default, requires HTTP(S) `session_token_url` values, and exposes `--allow-static-auth-tokens` only as an explicit private/dev compatibility switch. Browser runtime QA now retries transient directory fetch failures once, publishes URL/result/status/header/body diagnostics for release-gate failures, and proves a real exported-web signed session-token join reaches `joined`.
- Latest local validation run for this slice: `.venv/bin/python -m pytest -q tests/test_godot_migration_scaffold.py` passed with `14 passed`, `scripts/validate_godot_migration_contract.py` passed, `scripts/validate_godot.sh` passed, `scripts/validate_godot_fidelity.sh` passed with `132 passed`, and `scripts/qa_godot_web.sh --check` passed browser runtime plus 5 screenshot comparisons. The previous broader local release validation remains recorded for version `0.25.0`; the optional `scripts/validate_godot_visuals.sh --check` still exits with the documented dummy-renderer capture error (`viewport image is unavailable in this renderer`), so browser QA/manual reference comparison remains the current visual path.
- Files intentionally touched by the latest local-fidelity slices: `docs/godot_migration_strategy.md`, `godot/scripts/groundfire_theme.gd`, `godot/scripts/main.gd`, `godot/tests/runtime_smoke_check.gd`, `tests/test_godot_migration_scaffold.py`, plus earlier browser-golden/layout/terrain/audio fidelity files already committed in the migration history.
- The repository still has a broad dirty working tree from the larger Godot migration. Treat unrelated modified/deleted/untracked files as existing user/agent work, not cleanup targets.

Immediate objective:

- Continue `Local Match Fidelity 2`, not broad online/release work.
- Keep the Python/Pygame client as the source of truth.
- Make one narrow fidelity improvement at a time, with a regression test and a status update in this file.

Start here:

1. Read this file from `Migration Fidelity Contract` through `Recommended Next Large Batch`.
2. Inspect `git status --short` before editing. Preserve existing user/agent changes.
3. Pick one small reference surface from the checklist: preferably `Landscape.clip_slice`/`Landscape.update`, one tank movement behavior, one weapon edge case, or one score/shop/HUD behavior.
4. Find the Python reference first under `src/`, then inspect the matching Godot implementation under `godot/scripts/`.
5. Add or extend the closest test before or alongside the behavior change.
6. Update `First Migration Slice`, `Current Status`, and the relevant remaining-work bullet in this document in the same patch.

Recommended first task for the next agent:

- Continue visual parity for Main Menu and Options typography/pixel review now that the classic Options preset rows, menu button stack, text shadow/outline metadata, and yellow classic-button hover/pressed color are in place.
- Compare the Godot screens against `docs/references/pygame_visual/main_menu.png` and `options.png`, focusing on exact font-atlas glyph metrics, selector triangle styling, keyboard focus/disabled state, and exact vertical placement.
- Use browser visual QA for intentional pixel changes, and extend `godot/tests/runtime_smoke_check.gd` only for layout invariants that can be protected headlessly.

Known terrain cases already covered; do not duplicate these unless extending them:

- Double-split crater clipping (blast inside tall chunk, index-shifting superblock fall pause).
- Linked double-split crater clipping preserves the lower remainder's support link while the upper piece starts the classic fall pause.
- Linked-support double-split crater clipping starts the linked cap/superblock leader falling while the split support remainders stay individually non-falling.
- Falling linked double-split support-motion handoff.
- Falling wait preserves speed and defers motion for the whole tick.
- Multi-chunk superblock compatible merge landing.
- Non-compatible color landing that links and inherits resting state.
- Independent left/right landing gaps and acceleration ordering.
- Falling support motion inheritance.
- Uniform falling-support merge motion preservation, including multi-chunk leader inheritance.
- Falling linked-support double-split motion handoff.
- Linked support cut propagation.
- Linked-removal top propagation and integrated removed-linked-cap crater-edge continuation.
- Mirrored falling removed-linked-cap support-motion propagation.
- Mirrored one-sided removed-linked-cap asymmetric top promotion.
- Removed linked cap where one side is fully consumed while the opposite side remains tall and still promotes the final top contour to the support.
- Mirrored one-sided top-edge crater clipping.
- Two-sided top-edge crater clipping.
- Mirrored linked top-only crater clipping preserves the support link without starting fall motion.
- Mirrored non-linked bottom-edge cuts start the chunk's classic fall pause.
- Mirrored unlinked `bottom_code = 6`/`9` preserves the opposite above-blast bottom edge while clipping the endpoint-code-selected edge.
- Mirrored unlinked `bottom_code = 11`/`14` preserves the above-blast opposite bottom edge while clipping the inside edge.
- Unlinked `bottom_code = 7`/`13`/`15` clips both bottom edges and starts the single chunk's classic fall pause.
- One-sided linked-bottom support detachment.
- One-sided bottom-clipping uncut above blast.
- Mirrored one-sided linked-bottom uncut-side adjustment.
- Two-sided linked-bottom support detachment.
- Asymmetric one-sided split remainder preservation.
- Falling split motion handoff.
- Minimum-land floor clamping and mirrored linked-superblock edge-graze skip guard.
- Mirrored linked-superblock edge-graze entire chain skips.
- Mirrored single-sided middle-crater graze noop guards.

Useful files for that first visual task:

- `src/mainmenu.py`, `src/optionmenu.py`, `src/menu.py`: authoritative classic menu layout and background behavior.
- `docs/references/pygame_visual/main_menu.png` and `docs/references/pygame_visual/options.png`: visual reference captures to compare before accepting new Godot goldens.
- `godot/scripts/main.gd`: migrated Main Menu and Options implementation.
- `godot/tests/runtime_smoke_check.gd`: headless viewport/focus/layout checks for menu routes.
- `scripts/qa_godot_web.sh`: exported-browser runtime and visual screenshot QA when browser/export dependencies are available.

Do not start with these unless the user explicitly asks:

- Public hosted server-directory infrastructure.
- Full `groundfire.server` replacement behind the WebSocket gateway.
- Release publishing/signing policy.
- Large visual redesigns.
- New standalone migration Markdown files.

Validation to run after a narrow Local Match fidelity change:

```bash
scripts/validate_godot_migration_contract.py
scripts/validate_godot_fidelity.sh
```

If the change touches shared Python, gateway code, release scripts, or CI, also run:

```bash
CI=1 .venv/bin/python scripts/run_quality_checks.py
```

If the change is visual or HUD-facing:

- Compare against `docs/references/pygame_visual/` first.
- Use `scripts/qa_godot_web.sh --check` when browser export dependencies are available.
- Refresh Godot goldens only after deciding the new capture is closer to the Pygame reference.

Completion criteria for the next agent's patch:

- One clearly named Pygame fidelity behavior is implemented in Godot.
- A regression test covers the behavior or the document explains why headless coverage is not yet possible.
- The validation commands above have been run, or the final response states exactly why they could not run.
- This document records what changed and what still remains non-final.

## Consolidated Migration Reference

The sections below replace the former standalone Godot migration docs. Keep migration strategy, validation, runtime, protocol, and server-directory contract updates in this single file so the migration source of truth stays compact.

### Validated Release Slice Walkthrough

The Groundfire Godot 4 + GDScript migration release slice for version `0.25.0` has been verified, exported, and packaged locally. This closes the validated release-slice milestone, while future public-online deployment choices and newly discovered fidelity deltas remain tracked in this same strategy document.

What was done:

1. Godot export templates setup:
   - Downloaded the official Godot `4.6.2.stable` export templates package.
   - Installed the Linux release template `linux_release.x86_64` and Web release template `web_nothreads_release.zip` to `~/.local/share/godot/export_templates/4.6.2.stable/`.
2. Visual golden updates:
   - Regenerated and updated browser visual goldens under `docs/references/godot_browser_visual/` after review against corrected classic Pygame visual styles.
   - Captured and verified Main Menu, Options, Server Browser, Local Match Setup, and Local Match.
3. Validation and quality gates:
   - Ran `scripts/validate_godot_release.sh --browser-qa --package`.
   - `scripts/validate_godot_migration_contract.py` passed.
   - `scripts/validate_godot_fidelity.sh` passed the then-current 125-test fidelity suite.
   - `scripts/qa_godot_web.sh --check` ran in headless Chromium and verified browser-safe storage, filters, HTTP directory cache/304 behavior with diagnostics, online error handling, no-store signed session-token join success, and matching visual goldens.
   - `scripts/run_quality_checks.py` passed `compileall`, `unittest`, `ruff`, and `mypy`.
4. Exporting and production packaging:
   - Built the Linux desktop release at `build/godot/Groundfire.x86_64`.
   - Built the Web HTML5 release at `build/godot-web/index.html` with support WASM and PCK files.
   - Created release artifacts in `dist/`: `groundfire-godot-0.25.0-linux-x86_64.tar.gz`, `groundfire-godot-0.25.0-web.zip`, `groundfire-godot-0.25.0-manifest.json`, and `groundfire-godot-0.25.0-SHA256SUMS`.
5. Integrity verification:
   - Ran `sha256sum --check` on the generated checksums file.
   - All packaged release artifacts were verified as `OK`.

Honest release-slice status:

- Covered by the current gate: major Local Match terrain, projectile, weapon, scoring, shop, winner, HUD, audio, focus, runtime, online reliability, signed expiring gateway join tokens, no-store directory-issued session tokens, browser-safe behavior, optional mouse aiming, wind presentation, and controller/keyboard navigation. Browser QA also verifies exported-web persistence, server browser flows, real local WebSocket gateway handling including signed session-token joins, and five Godot browser visual regression screenshots.
- Important visual nuance: `scripts/qa_godot_web.sh --check` compares current Godot browser captures against approved Godot browser goldens under `docs/references/godot_browser_visual/`. The authoritative Pygame references under `docs/references/pygame_visual/` are the review target before accepting or refreshing those goldens; the current gate is not a direct automatic pixel comparison of Godot against Pygame.
- Future production work: choose real public directory endpoints, deploy the signed `/session-token.json` issuer behind the final authentication/session policy, keep the default public-directory static `auth_token` rejection enabled in hosted deployments, expand browser QA against hosted directory behavior, and bind/deploy the WebSocket gateway against the intended production server runtime.
- Future fidelity work: continue targeted audits for any screen, timing path, multiplayer edge case, economy/fuel-reserve behavior, future-item behavior, or behavior not yet covered by a named Pygame reference regression. These are follow-up hardening items, not evidence that the current validated release slice failed.

### Build And Runtime

Local Godot build/runtime path used by the migration scaffold.

#### Requirements

- Godot `4.6.2.stable`, available by default at `tools/godot/Godot_v4.6.2-stable_linux.x86_64`.
- Godot export templates `4.6.2.stable` installed under `~/.local/share/godot/export_templates/4.6.2.stable/`.
- Python dependencies installed in `.venv` so desktop tools can launch `groundfire-web-gateway`.

Required templates for the current presets:

- `linux_release.x86_64`
- `web_nothreads_release.zip`

#### Validate

Run the headless project validation and runtime smoke checks:

```bash
scripts/validate_godot.sh
```

The validation checks script parseability, data model behavior, browser-safe persistence, terrain collision, deterministic desktop/web capability rules, scene startup, and smoke coverage for Main Menu, Options, Server Browser, Local Match, and Online Match controls.

Run the consolidated migration fidelity gate when you need to confirm that migrated Godot behavior still matches the currently protected classic contracts:

```bash
scripts/validate_godot_fidelity.sh
```

That gate runs `scripts/validate_godot.sh` plus the Python-side fidelity, replicated-rendering, WebSocket gateway, landscape reference, and Godot migration scaffold tests listed in the `Godot Fidelity Audit` section.

When a Godot migration change touches shared Python, gateway, launcher, or release scripts, also run the repository quality gate:

```bash
CI=1 .venv/bin/python scripts/run_quality_checks.py
```

Run the local release gate before publishing a Godot build candidate:

```bash
scripts/validate_godot_release.sh
```

Optional release-gate checks can be enabled when the machine has the required browser/export environment:

```bash
scripts/validate_godot_release.sh --visuals --browser-qa --package
```

This runs the migration contract and fidelity gates, then can add visual goldens, exported-web browser QA, package generation, and `sha256sum --check` verification.

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

Refresh the authoritative Pygame visual references after a deliberate change to the Python/Pygame source of truth:

```bash
scripts/capture_pygame_references.py
```

This writes 1024x768 Main Menu, Options, Server Browser, and Local Match captures to `docs/references/pygame_visual/`. Do not replace these with Godot captures; they are the reference images used to judge whether the migrated Godot client is faithful to the original.

#### Export

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

#### Package

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

#### Release Verification

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

#### Browser Hosting

Host the contents of `build/godot-web/` or the unpacked web release archive from an HTTP(S) origin. Opening `index.html` directly from the filesystem is not a supported runtime path.

Recommended hosting expectations:

- Serve `index.html`, `index.wasm`, `index.pck`, JavaScript glue files, and generated assets from the same origin unless CORS is intentionally configured.
- Use HTTPS for public deployments, especially when connecting to `wss://` gameplay gateways or HTTP(S) server directory endpoints.
- Configure `.wasm` files with `application/wasm`.
- Keep compression and cache headers consistent across `index.pck`, `.wasm`, and JavaScript files. For public releases, prefer immutable cache headers on versioned artifacts and short cache headers on `index.html`.
- Do not expose desktop-only LAN, UDP, process spawning, or local dedicated server tools from the web build.

#### Distribution Notes

Linux desktop archives contain the exported executable and Godot runtime support files. Web archives contain only browser-safe assets.

Before publishing a release:

- Run `scripts/validate_godot.sh`.
- Run `scripts/package_godot_release.sh`.
- Run `scripts/qa_godot_web.sh --check` on a machine with Chromium/Chrome, export templates, and Python browser QA dependencies.
- Verify `SHA256SUMS`.
- Attach the Linux archive, Web archive, manifest, checksum file, and release notes together.

The current release process is still local/manual. CI should eventually run the same commands, upload artifacts from `dist/`, and block publishing when validation, browser QA, or checksum generation fails.

#### Browser QA

Run browser screenshot QA against the exported web build:

```bash
scripts/qa_godot_web.sh --check
```

This exports the web target, serves it locally, opens Chromium/Chrome through DevTools, captures Main Menu, Options, Server Browser, Local Match setup, and Local Match screenshots, and compares approved captures with `docs/references/godot_browser_visual/`. In `--check` mode, a captured route with no approved golden fails instead of becoming a new reference automatically.

Important: `docs/references/godot_browser_visual/` is a Godot web regression set. It must be reviewed against `docs/references/pygame_visual/` before an updated browser golden is accepted as a fidelity improvement.

Browser runtime QA also opens the web export with `?qa=browser_runtime` and waits for the Godot client to publish `window.__groundfireQaResult`. That runtime QA path runs a `seed` pass and a `verify` pass with the same Chromium profile, verifying browser-safe persistence for favorites, history, and filters across browser sessions. It also loads a served schema `1` HTTP directory fixture, validates the fixture's `Cache-Control`, `ETag`, and `X-Groundfire-Directory-Refresh` headers, sends a conditional `If-None-Match` refresh, expects `304 Not Modified`, reports URL/result/status/header/body diagnostics for the directory request, retries transient directory request failures once, confirms LAN entries and desktop-only features stay hidden in the web runtime, checks invalid-directory fallback diagnostics, and exercises Online Match fatal error handling against real local `groundfire_net.websocket_gateway` password, auth, full-server, closed-server, and banned-player rejections.

Refresh browser goldens after an intentional visual change:

```bash
scripts/qa_godot_web.sh --update-goldens
```

The browser QA requires Chromium or Chrome plus Python dependencies from `requirements.txt`, including `Pillow` and `websocket-client`.

#### WebSocket Protocol

The browser-safe Godot client and Python gateway protocol is documented in the `WebSocket Protocol` section. The current gateway enforces protocol version `1`, validates required fields before dispatching messages to the simulation scaffold, and can exercise first-pass fatal join failures:

- `invalid_password` with `groundfire-web-gateway --password secret` or `GROUNDFIRE_WEB_GATEWAY_PASSWORD=secret`.
- `authentication_failed` with `--auth-token token-123` or `GROUNDFIRE_WEB_GATEWAY_AUTH_TOKEN=token-123`.
- `server_full` with `--max-players 2` or `GROUNDFIRE_WEB_GATEWAY_MAX_PLAYERS=2`.
- `server_closed` with `--closed` or `GROUNDFIRE_WEB_GATEWAY_CLOSED=1`.
- `banned` with `--ban-player Mallory` or comma-separated `GROUNDFIRE_WEB_GATEWAY_BANNED_PLAYERS=Mallory`.

#### Server Directory

The read-only server browser directory schema is documented in the `Server Directory Schema` section. The Godot client validates schema `1` for HTTP and local fallback payloads before rendering entries.

Serve a production-shaped local HTTP directory for browser-safe Godot testing:

```bash
groundfire-directory --directory godot/data/server_directory.json
```

Inject a local gateway entry while running a local `groundfire-web-gateway`:

```bash
groundfire-directory \
  --directory godot/data/server_directory.json \
  --gateway-endpoint ws://127.0.0.1:8765 \
  --server-name "Local Gateway"
```

The service responds on `http://127.0.0.1:27880/servers.json` by default, serves schema `1`, filters LAN entries unless `--include-lan` is set, rejects entries that embed static `auth_token` unless `--allow-static-auth-tokens` is set, validates `session_token_url` as HTTP(S), and emits `Cache-Control`, quoted `ETag`, and `X-Groundfire-Directory-Refresh` headers for browser/runtime QA. The Godot client sends `If-None-Match` on later HTTP refreshes when it has a matching cached ETag and reuses the cached listing on `304 Not Modified`; the service accepts quoted, comma-listed, and legacy unquoted validators for local hosted-directory rehearsals. The service also exposes `/healthz` and `/diagnostics.json` for served-server, filtered-LAN, invalid-entry, and invalid injected-gateway checks during hosted-directory rehearsals.

For authenticated hosted rehearsals, start the directory and gateway with the same session secret:

```bash
groundfire-directory \
  --directory godot/data/server_directory.json \
  --session-secret "$GROUNDFIRE_SESSION_SECRET"

groundfire-web-gateway \
  --session-secret "$GROUNDFIRE_SESSION_SECRET"
```

Then request `http://127.0.0.1:27880/session-token.json?player_name=GodotPlayer`. The response uses `Cache-Control: no-store` and returns an `auth_token` compatible with the gateway's signed-token join validation. The endpoint is disabled by default and returns `session_tokens_disabled` unless `--session-secret` or `GROUNDFIRE_DIRECTORY_SESSION_SECRET` is configured. When an online server entry includes `session_token_url` and no static `auth_token`, Godot Online Match requests that URL with `player_name=GodotPlayer`, requires a no-store response, stores the returned `auth_token` only in memory, and then sends the normal WebSocket `join`.

`application/config/server_directory_url` is still available as an explicit override. Otherwise set `application/config/server_directory_environment` to `dev`, `staging`, or `production` and configure the matching `application/config/server_directory_url_*` setting. Empty or non-HTTP(S) environment URLs use `res://data/server_directory.json`.

The same values can be changed from the Godot Options screen during local testing. They persist in `user://groundfire_options.cfg` and are applied before opening the Server Browser.

#### Run

Run the Linux desktop export:

```bash
build/godot/Groundfire.x86_64
```

Serve the web export from a local HTTP server:

```bash
python -m http.server 8080 --directory build/godot-web
```

Then open `http://127.0.0.1:8080/`.

#### Platform Expectations

Web builds expose browser-safe flows only: local match, online server browser entries, WebSocket-compatible online play, favorites, history, and browser-safe persistence.

Desktop builds may expose native workflows: LAN tab, UDP/native networking affordances, process spawning, and the local dedicated gateway launcher.

### Godot Fidelity Audit

Automated fidelity gate for the Godot migration.

#### Gate

Run the consolidated gate before treating migrated Godot behavior as stable:

```bash
scripts/validate_godot_fidelity.sh
```

The gate includes:

- `scripts/validate_godot.sh` for Godot script parse checks, runtime smoke checks, server directory checks, terrain collision checks, Local Match fidelity checks, Online Match reliability checks, and scene startup.
- `tests/test_godot_migration_scaffold.py` for structural coverage of migrated Godot scripts, scenes, docs, export scripts, and migration strategy claims.
- `tests/test_groundfire_net_module.py` for the Godot/Python WebSocket gateway contract and protocol documentation.
- `tests/test_replicated_scene.py` for replicated rendering, score, winner, shop, lobby, and terrain presentation contracts.
- `tests/test_port_fidelity.py` for classic port behavior around player/tank/end-round fidelity.
- `tests/test_landscape_fidelity.py` for Python terrain behavior used as the reference model for the Godot terrain migration.

#### Current Automated Coverage

- Main Menu, Options, Server Browser, Local Match, Online Match, and scene startup smoke validation.
- Desktop/web feature gating for LAN, UDP, dedicated tools, and browser-safe server browser tabs.
- Server directory schema `1`, HTTP fallback diagnostics, and browser-safe filtering.
- Browser store persistence for favorites, history, and filters.
- Local Match score, shop, winner, roster, terrain collision, tank, weapon, quake, audio, HUD, and controller-focus fidelity checks.
- Online Match reliability, reconnect/fatal error paths, interpolation/prediction diagnostics, and gateway error handling.
- Godot lifecycle hygiene for migrated scenes, including WebSocket close, HTTP request cancel, Local Match audio stop, and queued-free frame draining in runtime/fidelity checks.
- Export/package/release script structure and build/runtime documentation coverage.

#### Limits

This gate protects implemented behavior against regression, but it is not a claim that the migration is complete. Visual pixel parity still depends on browser/headless visual goldens and manual reference comparison where the current renderer cannot capture reliable pixels. The remaining migration items stay tracked in this document.

### WebSocket Protocol

First browser-safe protocol contract between the Godot client and the Python `groundfire-web-gateway`.

#### Versioning

- Current protocol: `1`.
- Supported protocol range: `1..1`.
- Every JSON message must include integer field `protocol`.
- The gateway rejects missing protocol values with `missing_protocol`.
- The gateway rejects unsupported protocol values with `protocol_mismatch`.
- Protocol changes that remove or rename fields must use a new protocol number.
- Additive fields may stay on protocol `1` if older receivers can ignore them.
- The gateway advertises `min_protocol`, `max_protocol`, and `supported_protocols` in its `hello` response and protocol errors.

#### Envelope

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

#### Client To Gateway

##### `hello`

```json
{
  "type": "hello",
  "protocol": 1,
  "client": "godot"
}
```

`client` is optional and must be a string when present.

##### `join`

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

##### `input`

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
    "jump": false,
    "shield": false,
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
- `shield`
- `fire`
- `weapon_next`
- `weapon_prev`

Every command field value must be a boolean. Unknown command names are rejected. `input` is only valid after a successful `join`; pre-join input returns `not_joined` and must not advance the simulation.

##### `ping`

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

##### `disconnect`

```json
{
  "type": "disconnect",
  "protocol": 1,
  "reason": "client_disconnect"
}
```

`reason` is optional and must be a string when present.

#### Gateway To Client

##### `hello`

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
  "auth_token_mode": "none",
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
`auth_required` is advisory metadata from `groundfire-web-gateway`; the server validates `join.auth_token` when a static gateway auth token or signed session-token secret is configured.
`auth_token_mode` is `none`, `static`, `signed`, or `static_or_signed`; signed tokens use the `gf1.<claims>.<signature>` HMAC shape generated by `groundfire-web-gateway --session-secret SECRET --issue-token PLAYER_NAME` and expire according to the embedded `expires_at` claim.
`joins_open` is advisory metadata for whether new joins are accepted; when it is false, `join` returns `server_closed`.
`ban_enforced` is advisory metadata for whether a player-name ban list is active; rejected names receive `banned`.
`max_players` is `0` when the gateway is unrestricted; otherwise the gateway rejects joins above that active-session limit with `server_full`. `players_connected` is the current active joined-session count.

##### `snapshot`

```json
{
  "type": "snapshot",
  "protocol": 1,
  "sequence": 7,
  "state": {
    "status": "input",
    "player_name": "GodotPlayer",
    "player_number": 1,
    "max_players": 8,
    "players_connected": 1,
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

##### `pong`

```json
{
  "type": "pong",
  "protocol": 1,
  "sequence": 8,
  "client_time_msec": 1234,
  "server_time_msec": 123456789
}
```

##### `disconnect`

```json
{
  "type": "disconnect",
  "protocol": 1,
  "reason": "client_disconnect"
}
```

##### `error`

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
- `not_joined`
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
It emits `authentication_failed` when started with `--auth-token` or `GROUNDFIRE_WEB_GATEWAY_AUTH_TOKEN` and a `join` message supplies a different static `auth_token`; when started with `--session-secret` or `GROUNDFIRE_WEB_GATEWAY_SESSION_SECRET`, it also emits `authentication_failed` for missing, expired, tampered, or wrong-player signed session tokens.
It emits `server_full` when started with `--max-players` or `GROUNDFIRE_WEB_GATEWAY_MAX_PLAYERS` and the active joined-session limit has been reached.
It emits `server_closed` when started with `--closed` or `GROUNDFIRE_WEB_GATEWAY_CLOSED=1`.
It emits `banned` when started with one or more `--ban-player` values or comma-separated `GROUNDFIRE_WEB_GATEWAY_BANNED_PLAYERS` and a `join.player_name` matches the normalized list.

#### Remaining Protocol Work

- Replace the gateway simulation scaffold with the full `groundfire.server` runtime.
- Promote `match_snapshot` and event payloads into a complete versioned schema.
- Keep the current real TCP/WebSocket gateway transport test as the minimum compatibility guard for handshake/framing, password rejection, join, input, ping, and disconnect messages.
- Keep the signed-token path and `groundfire-directory` `/session-token.json` endpoint as the minimum production auth bridge until it is deployed behind the final hosted account/session policy.
- Add browser-level end-to-end tests against the exported Godot web build.
- Define multi-version compatibility windows and downgrade/upgrade policy for future protocol versions.

### Server Directory Schema

First browser-safe read-only server directory contract for the Godot client.

#### Versioning

- Current schema: `1`.
- The top-level JSON object must include integer field `schema`.
- The top-level JSON object must include array field `servers`.
- Additive server fields may be ignored by older clients.
- Removing or renaming required fields requires a new schema number.

#### Top-Level Shape

```json
{
  "schema": 1,
  "servers": []
}
```

Required:

- `schema`: integer directory schema version.
- `servers`: array of server objects.

#### Server Object

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
- `auth_token`: string, copied into the Godot `join` message for pre-provisioned development/private-directory joins or for short-lived signed session tokens generated by the gateway issuer path.
- `session_token_url`: string, optional no-store HTTP(S) endpoint that issues a short-lived signed `auth_token` for the selected player before WebSocket `join`.
- `tags`: array.
- `last_seen_msec`: integer timestamp.

Static `auth_token` values are not a final public authentication model. Treat them as temporary fixtures/private-directory bridges. `groundfire-directory` rejects embedded `auth_token` entries by default for public payloads; `--allow-static-auth-tokens` / `GROUNDFIRE_DIRECTORY_ALLOW_STATIC_AUTH_TOKENS=1` is only for private/dev directories that intentionally need the compatibility path. Public directories should prefer short-lived signed tokens generated by the no-store `groundfire-directory /session-token.json?player_name=...` endpoint or, for local administration, `groundfire-web-gateway --session-secret SECRET --issue-token PLAYER_NAME`; the remaining production task is to deploy that issuer behind the final account/session policy.

#### Client Behavior

The Godot client validates the payload before showing entries. Invalid JSON, missing schema, unsupported schema, missing required server fields, wrong field types, unknown `source`, or non-WebSocket online endpoints make the client fallback to `res://data/server_directory.json`.

Web builds hide `source: "lan"` entries. Desktop builds can include them.

When an online entry includes `auth_token`, the client preserves it during directory normalization and sends it as `join.auth_token` through the WebSocket transport. Empty or omitted tokens are not sent. When the entry instead includes `session_token_url`, Online Match fetches a no-store JSON token response from that URL before joining and sends the returned `auth_token`; static `auth_token` remains the compatibility path and takes precedence if both fields are present.

#### Godot Configuration

`application/config/server_directory_url` is an explicit override. When it is empty, the client reads `application/config/server_directory_environment` and then uses the matching environment URL:

- `dev`: `application/config/server_directory_url_dev`.
- `staging`: `application/config/server_directory_url_staging`.
- `production`: `application/config/server_directory_url_production`.

If the selected environment URL is empty or does not use `http://` or `https://`, the client uses the local fallback JSON. The default environment is `dev`.

The Options screen persists these values in `user://groundfire_options.cfg` under the `server_directory` section and applies them to the runtime ProjectSettings before the Server Browser reads the directory configuration.

#### Remaining Service Work

- Choose and fill the real public HTTP endpoints for dev, staging, and production.
- Use the local `groundfire-directory` service as the first implementation contract for hosted deployments; it already emits `Cache-Control`, quoted `ETag`, and `X-Groundfire-Directory-Refresh`, accepts production-shaped `If-None-Match` validators, rejects static directory-carried `auth_token` by default, validates HTTP(S) `session_token_url` values, can issue no-store signed session tokens, and the Godot client now validates conditional `304 Not Modified` reuse locally, but the public hosting cadence still needs an operational decision.
- Add presence/latency updates through WebSocket or another browser-safe channel.
- Deploy signed token issuance behind the hosted production authentication/session flow; the local directory service now blocks static directory-carried shared-secret tokens by default, leaving only explicit private/dev opt-in as a compatibility escape hatch.
- Expand the browser runtime QA beyond the current served schema `1` fixture, first-pass cache/refresh header checks, and local `304 Not Modified` rehearsal to cover production directory cache behavior under real hosting.
