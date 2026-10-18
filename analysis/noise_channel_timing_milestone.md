# Complete native864F noise channel with per-byte PSG times

The separately named timed864F composition reuses the authoritative noise
channel C. Sequence events are rebased by its33T DEC/JP prefix; envelope mute
and final volume OUTs occur10T before their returning RET. Existing state,
DE, work, rejection rollback and reader-exit behavior are unchanged. Ordinary
gameplay compiles without sidecar stores or the extra timing loop.

## Original source and compiled68000

| Original864F suite, each region | Cases | PSG bytes |
| --- | ---: | ---: |
| Noise channel matrix |19680|13160|
| Commands |5760|4800|
| F1/F2 termination/restoration |3072|4224|
| F3 ownership |480|819|
| Held/envelope cases |1152|348|
| Mirrored DE/FE streams |128|96|
| Mirrored DF/FF streams |128|96|
| Flow/loops/calls |270|216|
| Total |30670|23759|

The port oracle observes original864F and closes at the appropriate normal
or caller-unwind return. Bank6 is intact; only the custom fixture caller's
hold is removed. Every call first checks its full400-byte input and incoming
DE against the retained fixture. All400 output bytes, complete T, DE, whole
reader exit, actual PSG byte order and completed-OUT time agree in PAL/NTSC.
M1 is compared against retained source-verified vectors, not recounted by the
new port observer. The ordinary and timed native implementations also agree.

All30670 cases repeat in compiled68000 PAL/NTSC with zero failures. The23759
events per region pass native queue roundtrips with early WAIT and exact
logical-deadline retrieval. Two cartridges keep each diagnostic below4MiB;
NTSC parts finish in7326/1795 frames, PAL in6130/1503. The shared test backend
now supports explicit fixture seeds, incoming DE and variable event capacity.
Its original tonal-sequence mode was rerun:85760 cases/5888 events per region,
zero failures. These test-harness durations are not gameplay performance data.

Nine additional host cases compare rejection and capacity behavior against
the ordinary channel: unsupported controls, rejection after an earlier staged
write,256-control guard with up to512 writes, and a valid510-write sequence.
Full state/DE/work rollback, invalid event count and surrounding output guards
pass. Such boundary fixtures do not establish natural gameplay reachability.

## Regression and remaining integration

The whole-reader differential against local8f8e451 still passes28644 cases:
28555 accepted streams/transactions and89 restored rejections, unchanged
digest680ebb69.... The complete game rebuild remains exact v0203, checksum368C.
No timing API in this milestone is wired into gameplay or physical PSG output.

Noise8655 sequence annotations are now exercised through the complete864F
channel, including controls and reader exits. A separate direct8655 entry
oracle is not claimed. Tone/frequency writes, prefix bursts and complete8000
composition remain. Physical subframe clock, global source phase and combined
production timing budget also remain unproved; queue checks supply logical
time and are not audible waveform or physical delivery measurements.

`analysis/noise-channel-timing-v0203/` retains compressed/deduplicated source
calls/ports, fixture/code/ROM snapshots, reports and hashes. No full save states
are generated. Reproduce with:

```
python tools/build_audio_ports_core.py --noise-channel
python tools/validate_noise_channel_timing.py
python tools/validate_audio_stream_equivalence.py
```
