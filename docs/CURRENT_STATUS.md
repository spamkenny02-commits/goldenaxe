# Current status — V13

Objective: faithful Golden Axe Warrior decompilation into portable C, then
platform backends, including native Motorola 68000/Mega Drive.

- Complete V12 sources/tests/tools/backend imported into Git, not just reports.
- Actual compiled dispatchers register 127/127 entity types and 509/512 world
  callbacks as native/RET. This is registration coverage, not an equivalence
  proof for every state of every handler.
- World scripts ADEE, B00A, B19E still use the instruction bridge.
- Reset/save initialization $0404 and initial SMS VDP setup $03C0 are now native
  C. Neither reset initialization call executes the Z80 instruction stream.
- $0404 matches original execution across 58 SRAM cases (both mapper pages,
  each possible signature mismatch, valid zero/nonzero saved flags). All 32 KiB
  SRAM bytes are compared; RAM outside CPU stack workspace is compared.
- $03C0 matches original RAM, full VRAM, CRAM and VDP register state; the final
  command selects CRAM index $10. Subsequent-write behavior is checked too.
- Four instruction-bridge call sites remain: world dispatch, two effect-state
  slots C090/C098, and non-gameplay main-state dispatch.
- Ten MD presentation hooks remain empty. Graphics/resource uploads, world
  rebuild/scroll presentation, inventory, special effects, world map, messages
  and transition presentation still need implementations.
- ROM/VDP shadow state still lives in sms_compat.c; separating these data/hardware
  services from the instruction interpreter is required before removing that
  file from console builds.
- No linked/play-tested Mega Drive ROM was produced in this session.

Validation performed locally: strict C11 Phase 17/final suites; reset differential
suite; ASan/UBSan final/reset suites (LeakSanitizer disabled because /proc access
is blocked in this sandbox); extraction failure tests; ROM table comparison;
compiled-dispatcher coverage probe; portability and MD structure/syntax checks.

Reproduction: see README.md. GitHub has source and workflows. Reference-ROM
behavioral checks and manual MD builds need private GAW_ROM_BASE64 input;
without it, CI reports behavioral tests as skipped, not passed.

Next: shared interactive menu + ADEE/B00A/B19E, effect dispatch, non-gameplay
states, separate asset/VDP services, complete platform hooks, then cross-link,
full-game differential integration, emulator and hardware validation.
