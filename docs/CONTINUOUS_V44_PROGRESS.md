# V44 — Restore interrupt-safe two-byte video commands

## Cause of the V43 capture mismatch

V42 and V43 ended with identical palette/VDP registers, cell, player position
and HP, but 45 SMS-shadow VRAM bytes differed and produced 363 viewport pixels.
These were shadow-state differences, not a colour-conversion error.

The original ROM RST $28 at $0028 executes DI, emits E and D to port $BF,
then EI/RET. The native core previously emitted those bytes through two
independent C calls. An asynchronous MD VBlank reads VDP status and resets the
control latch; arriving between those calls can cancel half a command and
redirect later tile writes. Code layout/cadence changed the observed failures.

## Fix

Add gaw_platform_video_command(command). The MD backend saves SR, masks
interrupts while submitting the two shadow control bytes, then restores the
exact saved SR, including the caller's interrupt priority. The synchronous
host backend submits the same bytes without concurrency. All native core
address/register helpers use this boundary; scalar ports remain available to
the reference interpreter and protocol tests.

No game dispatch or interpreter is added to the MD build. RAM is unchanged.

## Verification

The settled controller-route capture now matches V42 byte-for-byte in the
shared 256x192 viewport. It also matches all 49152 pixels of the independent
SMS capture using a fixed per-channel DAC conversion, with no fitted palette,
spatial alignment or tolerance. A new standard-library capture comparator
provides this check and rejects one-pixel errors and unsupported DAC levels.

The ROM-free fixture uses the same production command boundary and cancels
partial commands from its real VBlank ISR. Its new stage stresses 57344
repeated active-pattern writes and deliberately leaves a VBlank pending
between the control bytes. GAW_MD_COMMAND_STRESS enables a delay for the
fixture's unused $4567 command only; it is absent from the production build.
With masking, all 537 stages / 30793728 pixels pass. A temporary build with
only the interrupt mask removed fails at stage 536, pixel [0,0], proving the
regression detects the original race rather than merely repeating writes.

The complete existing host differential/regression targets, compiled coverage,
portability and backend checks pass with private reference data. Seven tool
unit tests pass. Targeted IRQ/assets ASan/UBSan checks also pass (leak detection disabled
for the existing local process-inspection restriction).

## Full-game measurements

| Measurement | V43 | V44 |
| --- | --- | --- |
| Idle updates / 300 physical gameplay frames | 227 | 225 |
| Reference route gameplay physical frames | 529 | 529 |
| Sampled route gameplay updates | 345 | 345 |
| Profiled route master cycles | 572321489 | 572324055 |
| Final cell / position / HP / state | 94 / [56,104] / 24 / 0C | 94 / [56,104] / 24 / 0C |
| Full native image bytes | 478324 | 479592 |
| BSS bytes | 32296 | 32296 |

The route retains V43's speed improvement. Atomic commands have a small cost:
idle is two updates lower in this 300-frame observation. No new speed gain is
claimed. Actual native ELF/vector/RAM checks and ROM header/checksum pass;
checksum 5223, RAM end FF7E28. The stressed standalone fixture is 10392 bytes,
BSS 25951, checksum 6F9E. Full-game audio and hardware IRQ checks also pass.

## Reproducing the capture comparison

Run tools/test_md_emulator.py on MD and SMS using tests/scenarios/world_exit.json,
then run:

```
python3 tools/compare_game_viewports.py --md MD_OUTPUT/final.png --sms SMS_OUTPUT/final.png
```

Use the pinned GPGX core's RGB565 output. Private game data and captured game
images are not committed. This validates one settled route viewport, not a
full playthrough, exact physical input phase or all raster effects.

## Remaining work

Further profile idle uploads; verify combined fine H-scroll/right V-lock,
exact sprite overflow timing, combat/interactions, SRAM save/reload, the full
playthrough/ending and PAL/NTSC/physical hardware behavior.
