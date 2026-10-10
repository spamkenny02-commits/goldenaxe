# V100: physical-frame SMS/MD comparisons expose substantial slowdown

The user's manual test of the delivered V50 image reveals slow movement,
monsters, text/introduction and transition artifacts. Functional route passes
must not be presented as faithful speed or full visual reproduction.
New comparisons pin both cores to NTSC at59.922743fps, use identical input
scripts and count physical frames independently of C02F game updates.

| Measurement | Original SMS | Delivered V50 | Current V100 |
| --- | ---: | ---: | ---: |
| Game updates per300 idle gameplay frames |298|225|228|
| Gameplay frames for first-screen exit script |348|531|499|
| Transition state0A→0C duration, frames |37|111|110|
| Name-entry state04→first gameplay, frames |235|701|683|
| First unskipped introduction text line, boot frame |110|455|429|

The first-screen walking sequence still runs at about70% of SMS cadence;
idle runs at about77%. The small optimizations do not solve the underlying
performance problem. Introduction lines generally remain about90 physical
frames apart, matching the asynchronous timer; expensive initial graphics
and scene preparation delay their appearance. Changing text timers or
movement constants would hide rather than resolve the backend slowdown.

The monster encounter is worse:1326 game ticks require3525 native gameplay
frames, while SMS uses1327 ticks in1330 frames, about38% relative cadence.
SMS's strict combat validation passes; native's rejects because it finishes
with24HP and never exercises hero damage. Native observes60 attacks, two
enemy hits/deaths; SMS observes61 attacks, three hits/deaths and two hero
hits. Random trajectories differ, so this comparison does not establish a
specific enemy-AI bug. The native encounter is not promoted to a pass.

The combat profile attributes about29.3% of observed instruction cycles to
the VBlank function bucket,17.6% to shadow conversion and6.9% to private
sprite pattern copying. These are instruction-location buckets, not
inclusive call graphs. Disassembly of hot VBlank addresses confirms the
inlined SMS sprite-collision bitmap work; its CPU cost is a next target.
Wait-loop buckets are not mistaken for useful computation.

## Changes and validation

- Native freestanding memcpy/memset/memcmp use aligned32-bit accesses,
  respecting the compiler's target alignment and byte-order comparison
  semantics. Mixed alignment and partial tails retain byte accesses.
- Pattern rows use one native32-bit VDP data write instead of two16-bit
  instructions. Intro/name/HUD descriptor uploads use the existing checked
  block-transfer implementation instead of repeated scalar calls.
- Unchanged shadow register writes no longer invalidate name/SAT caches;
  changed registers still invalidate them. This last change gives no
  measurable cadence gain in the chosen scenarios.
- `--region ntsc|pal` pins the standard. `--timing-trace` records physical
  frame, game counter, hero/monster state/animation/positions and intro/text
  pointers. `compare_emulator_cadence.py` rejects unpinned/mismatched
  standards and cheats. Its output is explicitly a diagnostic, not a game
  equivalence proof. Use the same input scenario for both reports.

78 Python tooling tests pass. `make test-md-runtime` checks8256 alignment/
length combinations, every mismatch position and overlapping memmove
against host libc; the address/undefined sanitizers pass with leak checking
disabled because this execution environment prevents LeakSanitizer's
process inspection. Video block/status, conversion/sprite, UI, intro,
presentation, IRQ and world-scroll differential suites pass. The native
ROM-free hardware video fixture passes30793728 pixels across537 stages,
including long data writes, sprite/cache/scroll and atomic-command stress.
Combined H-scroll/right V-lock remains unverified.

The final settled screen after first-screen crossing matches SMS over all
49152 shared viewport pixels with the fixed DAC conversion. This does not
check partially drawn frames during crossing; the user's transition defects
remain open. PAL and physical hardware comparisons remain open too.

Current production image:489158bytes/checksum2759, native-only ELF checks
and ordinary boot/first-screen route pass. Full dungeon/ending proofs from
V50–V99 remain historical evidence for that older image and their recorded
options. They have not been rerun on this performance build. No ROM or
private captures are committed. Compact results and private report hashes
are in cadence_progress_v100.json.

Reproduce comparisons (local core, original ROM and compiler required):

```sh
python3 tools/test_md_emulator.py --core "$GAW_CORE" --nm "$GAW_NM" \
  --region ntsc --timing-trace --play-inputs tests/scenarios/world_exit.json \
  --output md/build/cadence-md
python3 tools/test_md_emulator.py --core "$GAW_CORE" --reference-sms \
  --rom "$GAW_SMS_ROM" --region ntsc --timing-trace \
  --play-inputs tests/scenarios/world_exit.json --output md/build/cadence-sms
python3 tools/compare_emulator_cadence.py --md md/build/cadence-md/result.json \
  --sms md/build/cadence-sms/result.json --output md/build/cadence-comparison.json
```

For introduction timing use `--observe-only --frames 3000`; for monsters use `--combat` and
`tests/scenarios/combat_field.json`. These measurements replace qualitative
claims of adequate cadence with a reproducible baseline for the next fixes.
