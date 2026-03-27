# Classic Controller Playtest

Use this checklist to validate the classic local menu flow on real hardware without changing the classic UI.

## Launch

Run the modern local runtime through the classic menu flow:

```powershell
python -m src.groundfire.client --canonical-local --player-name "Controller Test"
```

## Keyboard 2

1. Open `Start Game`.
2. Leave exactly one human player enabled.
3. Change the controller selector to `Keyboard2`.
4. Start a round.
5. Confirm the tank responds only to the `Keyboard2` bindings from `conf/controls.ini`.

## Joysticks

1. Repeat the same setup with `Joystick1`.
2. Press `Fire` on an unassigned joystick from the player-select screen and confirm it auto-joins the next free player row.
3. Start a round and confirm movement, aiming, weapon switching, and fire all route through the selected joystick.
4. Repeat for any additional joystick layouts you want to certify.

## Legacy Fallback

1. Enable two human players in `Start Game`.
2. Assign different controllers, for example `Keyboard1` and `Keyboard2` or `Keyboard1` and `Joystick1`.
3. Start the match.
4. Confirm the game hands off to the legacy local loop and begins the round with both players configured.

## Regression Notes

If any step fails, capture:

- Which controller label was selected in the classic menu.
- Whether the player was added by click or by pressing `Fire`.
- Whether the failure happened before the round, during the round, or during the legacy fallback handoff.
