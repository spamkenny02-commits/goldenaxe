# Continuous V12 progress

V12 continues directly from V11 and reduces world-callback compatibility from
8 entries to **3 entries**.

## World callback coverage

- 509 / 512 callback-table entries: high-level/native/no-op C
- 3 / 512: instruction-compatible bridge
- remaining: `ADEE`, `B00A`, `B19E`

New high-level families after the V11 checkpoint:

- `$62A9` context-sensitive tile/message interaction;
- `$61F4` and `$621E` early-exit message variants;
- callbacks `ADA1`, `ADF2`, `AF88`;
- `$5FC7/B205` permanent capacity reward;
- `$6497/AF25` signed resource adjustment with 0..255 saturation and original
  HUD-step side effects.

The earlier V11 work in the same continuation also includes native `$1780`,
`$2C63`, 116 generated `$6594` room callbacks, keyed rooms, fixed rewards,
message callbacks, special `ACB9/AD55` branches and `B0D9/$6911`.

## Remaining three callbacks

- `ADEE` -> `$66F6`: a multi-state scripted/minigame dispatcher.
- `B00A` -> `$66B5`: an interactive scripted sequence with resource checks and
  room/world transitions.
- `B19E` -> `$616F` + `$6036`: a saved-room transition plus an interactive
  selector/resource-spend sequence.

They are intentionally still bridged rather than replaced by approximate
behavior.

## Validation

- strict C11 `-Wall -Wextra -Werror`: OK
- final compatibility/regression suite: OK
- ASan + UBSan: OK
- 68000 portability audit: OK
- entity dispatcher: 127/127 high-level C, no fallback
- world callback table: 509/512 native/no-op
