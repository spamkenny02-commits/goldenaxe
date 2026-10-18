# Loading PSG producer readiness against original per-byte deadlines

The experimental physical class0 loader can prepare the retained audio bytes
before their SMS deadlines when both paths use a loading-entry-relative epoch.
This is a readiness result, not paced playback. The playable ROM remains v0203.

`profile_native_loading_budget.py --planned --bare --precise --physical-video
--audio-readiness` builds a separate diagnostic cartridge. At each successful
logical IRQ it stores source entry/completion times and cumulative PSG bytes.
A read-only emulator observer records sink function entries (one per batch)
and an IRQ completion marker. The ordinary profiler and playable code paths
do not enable these extra stores or markers.

The source oracle replays original bank6 routine8000 with the492 reader inputs
from the24 source-checked loading contexts. The custom caller disables IRQs,
copies400 bytes, supplies DE, restores bank6 and calls the unchanged driver.
The observer records the actual cycles/data passed to `psg_write` by the SMS
port handler. All400 output bytes, returned DE, complete reader duration and
ordered PSG bytes agree with the native reader for every call. Both physical
regions produce identical reader-relative byte times and values.

Source reader-entry offsets inside IRQs come from the existing IRQ model:
the sum of stages before AUDIO plus its17T CALL for full interrupts, or the
audited gate/save/map/CALL prefix for audio-only interrupts. The whole IRQ
entry and completion times are checked against retained source vectors.
This oracle is an isolated original-reader replay, not a new natural full
loader run. Inputs are obtained by executing the native planned loader and
checking its full results and IRQ list against the retained source cases.

| Matching physical region | Logical IRQs | Compared PSG bytes | Late bytes | Smallest preparation margin |
| --- | ---: | ---: | ---: | ---: |
| NTSC |264|660|0|12245 master ticks /3.5804 scanlines|
| PAL |228|828|0|47043 master ticks /13.7553 scanlines|

Each region replays all492 reader calls and1488 source port writes, then
compares only the corresponding twelve physical-producer contexts. The
source oracle completes in101 NTSC frames and85 PAL frames. No screenshots
or full emulator save states are requested. Endpoint physical map/pattern/
palette checks from the video profiler still pass with the new instrumentation.

## Limits and next integration work

- The physical epoch starts at the budget-begin marker. Global source-entry
  phase propagation from boot is still unproved.
- Batch function entry proves preparation, before the port loop. It excludes
  the future consumer's queue copy, scheduling and physical write latency.
  The extra IRQ metadata stores/marker overhead is included in the producer.
- The measured prototype currently writes immediately, ahead of source time.
  It needs an explicit deadline consumer and bounded buffering/backpressure.
- Original-byte deadlines are now measured, but the native reader does not yet
  return per-byte timestamps. Production needs timestamps derived from source
  execution semantics; retained fixture deadlines must not become game assets.
- The whole-loading NTSC budget remains thin. A readiness margin for early
  audio bytes does not enlarge the final video publication margin.
- Other rooms, actor uploads, screen enable/fades, actual hardware and audible
  PSG chip differences remain outside this result. No full-game claim.

## Reproduction

```
python tools/profile_native_loading_budget.py --planned --bare --precise --physical-video --audio-readiness
python tools/build_audio_ports_core.py
python tools/validate_loading_psg_deadlines.py
```

The core builder temporarily instruments the local emulator source and restores
both files in a `finally` block. Its modified sources, raw calls/ports, generated
native diagnostic sources, inputs and reports are retained under
`analysis/loading-psg-v0203/`, with SHA256 values in its manifest. The oracle
checks source port times lie within the reader call and remain ordered.
