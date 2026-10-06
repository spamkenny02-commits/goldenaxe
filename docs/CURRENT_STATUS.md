# Current status — V12

Golden Axe Warrior SMS -> native Mega Drive, faithful-decompilation-first.

- **127/127 active entity types are high-level C; entity fallback is absent.**
- **509/512 world callback entries are native/no-op; only 3 remain bridged.**
- Remaining world callbacks: `ADEE`, `B00A`, `B19E`.
- Ordinary gameplay renderer, HUD, map loading, progression, map animation,
  entity update and gameplay entry are native C.
- `$1C15`, `$1780` and `$2C63` gameplay initialization are native C.
- `$2C63` validation fixed the previous one-byte `$2C8D` terrain-cache error.
- Standard/keyed room entry, fixed rewards, context messages, resource rewards,
  special message branches and `B0D9/$6911` are native C.
- C090/C098 effect-state slots and non-gameplay main states still retain a
  compatibility fallback.
- Reset/save/initial SMS-VDP setup `$0404/$03C0` remains compatibility-backed.
- Mega Drive backend source/build scripts are present; this container still has
  no m68k cross-compiler, so no linked `.bin` has been produced locally.

Validation: strict C11, compatibility/regression suite, ASan/UBSan and 68000
portability audit all pass.
