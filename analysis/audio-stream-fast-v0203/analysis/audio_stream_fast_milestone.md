# Audio composition without nested rollback copies

The clocked loading engine now uses a faster native audio composition. The
playable ROM remains byte-identical to v0203. The complete port is unfinished.

`source_audio_fast.c` compiles the existing tone, noise, sequence and reader
semantics under separate names. A conditional removes only the nested 400-byte
rollback snapshots. The fast capture reader retains its outer rollback; the
fast streaming reader documents that rejected state is not rolled back.
Rejected channels emit no PSG writes, while earlier successful writes remain
published. The ordinary APIs keep their existing rollback behavior.

`source_irq_context.c` uses this composition for the experimental source-clock
engine. The production IRQ in `sound.inc` still uses the original composition.
Changing it globally advanced unclocked loaders and regressed northward timing.
Those v0205-v0207 builds are preserved as diagnostics, not recommended releases.
The intended integration still requires physical uploads and a source calendar
for the entire loader, rather than regional frame-delay constants.

## Validation

- 25644 retained source vectors pass on compiled 68000 in both physical regions:
  all 400 audio bytes, T states, M1 counts and DE match, with zero failures.
- 28644 host comparisons against committed v0203 include 3000 mutated states:
  28555 accepted results have identical state, work, DE, status and PSG lists;
  89 rejected capture calls restore the complete input state and DE.
- 24 complete class-0 loading contexts retain all sixteen source checkpoints,
  including phase, R, M1, RAM, audio and IRQ offsets, on host and 68000 PAL/NTSC.
- The default tone/noise suites pass, and rebuilding the playable ROM produces
  exactly `7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7`.

## Complete-chain CPU measurements

Read-only 68000 PC observations bracket the four native loading calls. Two
small marker calls are included in the measurements. Both variants use the
same generated contexts and loading code; only the audio composition changes.

| Physical region | Original audio, frames | Fast audio, frames | Source duration, frames |
| --- | ---: | ---: | ---: |
| NTSC | 22.3384-23.5106 | 20.8663-22.0383 | 22.7104 |
| PAL | 17.8644-18.7452 | 16.5339-17.4172 | 19.5707 |

The measured CPU cost is below the source duration on these 24 contexts, with
at least 176 scanlines left in NTSC and 674 in PAL. This is a display-off lower
bound: PSG writes are discarded, physical VRAM transfers are absent, and
controller scheduling is absent. It does not prove renderer headroom or game
frame rate. All room classes and global entry phase propagation remain pending.

Reports and source snapshots are in `audio-stream-fast-v0203`. Relevant commands:

```
python tools/validate_audio_stream_equivalence.py
python tools/validate_native_audio_reader_68k.py --fast
python tools/validate_native_room_finish.py --planned
python tools/validate_native_room_finish_68k.py --planned
python tools/profile_native_loading_budget.py --planned --bare --precise --baseline-audio
python tools/profile_native_loading_budget.py --planned --bare --precise
```

Existing retained fixtures are required. Full emulator save states remain
disabled by default; this milestone does not require regenerating them.
