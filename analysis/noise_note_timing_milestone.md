# First source-semantic timed PSG primitive: original8679

`source_audio_noise_note_timed` produces the optional noise-selector PSG byte
and its source master-tick deadline. It calls the authoritative native8679
state/work implementation, then computes `source_entry+(helperT-10)*15`.
Both writing exits execute OUT followed immediately by a10T RET (86D8/86DA
and the863E mute exit); the formula locates the completed port operation.
Suppressed output leaves the caller's event untouched. Invalid arguments
produce no event and zero the valid work/has-event outputs.

The timestamp is derived from the actual semantic path and its instruction
cost, without fixture tables in game assets. The API changes state once and
returns an event for the caller to retain if queue publication encounters FULL.
The caller must retry that event rather than rerun the semantic helper.

## Evidence

The separate noise-port observer records actual PSG handler timestamps at
original8679 entry and3003 return. The fixture leaves all of bank6 unchanged,
disables IRQs and supplies patterned400-byte state and A. All256 note selectors
are crossed with flags0/4/128/132, volume0/15/255 and noise offset0/3/255:
9216 cases per physical region, including4608 emitted and4608 suppressed bytes.

For every case in both regions, the host timed helper agrees with original
all400-byte output state, complete work duration, optional byte and exact
reader-relative port timestamp. DE is unchanged by the source routine. The
relative event times/values and resulting states agree between PAL and NTSC.
Five invalid host calls check null arguments and offset353 with no mutation
or event publication. Coverage uses the actual noise channel at offsetD0.

The compiled68000 cartridge repeats all9216 cases in PAL/NTSC, including
absolute source epochs that wrap32 bits. Each of the4608 generated events is
also pushed into a one-entry native deadline queue: a second push reports FULL,
take one tick early reports WAIT without changing its output, and take exactly
at the deadline returns the expected byte/time. Suppressed outputs leave the
queue empty. Zero failures;1889 NTSC and1581 PAL frontend frames.

## Scope and next work

This is one original helper, not a complete timed8000 audio reader. Sequence,
tone/envelope, dispatch and mute-burst event times must still be composed and
verified. Queue consumption here uses supplied logical timestamps; there is
no physical subframe clock, paced port output or waveform assertion. Global
source phase and total producer/consumer loading budget remain pending.

The complete game build is still byte-identical to v0203 (SHA2567660a4b5...,
checksum368C); the timed API is not yet called by gameplay. No full emulator
save states are generated. Original raw calls/ports are compressed losslessly
in `analysis/noise-note-timing-v0203/`; its manifest preserves raw and stored
hashes along with source, generated diagnostic code, ROM and reports.

```
python tools/build_audio_ports_core.py --noise-note
python tools/validate_noise_note_timing.py
```
