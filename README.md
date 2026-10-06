# Golden Axe Warrior — SMS decompilation / native Mega Drive port

Faithful decompilation of **Golden Axe Warrior** (Master System) into portable C, with a native Motorola 68000 / Mega Drive backend.

## Current status (V12)

- 127/127 active entity types are high-level C; no entity Z80 fallback remains.
- 509/512 world callback entries are native/no-op; 3 interactive callbacks remain bridged.
- Map loading, progression, gameplay renderer, HUD, map animation, entity update, gameplay entry, map entity spawning and Arthur initialization are native C.
- Mega Drive backend source and build scripts are present.
- Strict C11 tests, differential/regression tests, ASan/UBSan and the 68000 portability audit pass on the current working tree.
- A linked/tested Mega Drive ROM is **not claimed yet**.

See `docs/CURRENT_STATUS.md` for the exact verified state.

## Original game data

This repository does **not** include the original Master System ROM or generated full-ROM dumps. Provide your own legally obtained ROM locally and use the extraction/generation tools in `tools/` for ROM-derived build inputs.

Reference ROM SHA-256 used during reverse engineering:

`852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9`

## Goal

The goal is not an approximate rewrite. Gameplay behavior is lifted from the original Z80 program and checked against original execution wherever practical; platform-specific SMS presentation/hardware behavior is isolated behind the platform layer and replaced by a Mega Drive implementation.
