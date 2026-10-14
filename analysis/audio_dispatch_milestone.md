# Predict original80FF audio command dispatch, v0180

Independent instruction/state models now cover13 music starts81..8D,
29 effects90..AC,80 idle,B0 fade,B1 stop,B2 effect release andB3 borrowed
channel restoration. Low-bit commands and commandsB5..FF execute the original
reset branch. The model includes ROM header/table reads,channel initialization,
noise ownership/borrowed music flags,395-byte reset and the source mute loop.
PSG write instruction time is counted;actual waveforms are not compared here.

An unchanged original bank6/80FF unit fixture tests24000 states per region,
48000 total. Complete helper cost and400 audio RAM bytes match for each case.
Eight noise flag patterns,fourDE0F values andthreeDE0E values cover ownership
and restore branches;high/reset values are explicit synthetic inputs.
Six values are excluded:8E/8F,AD/AE/AF andB4. The first five index outside the
defined music/control entries;B4 points at7000,inside an unrelated instruction
in fixed ROM,and is not asserted as a supported normal sound command.

Live read-only instrumentation on controlled6D->96/full-mask gameplay captures
601 calls of each arbitration/tempo/fade/dispatch helper per region. Independent
models match4808 helper costs/states,including1202 dispatch calls. Commands
observed are80,B0,82 and98. There are3606 exact consecutive helper-state links.
All original cycle-event arrays remain identical to the archived v0179 source.
The isolated suite supplies the other music/effect cases;the live route does
not claim to exercise all of them naturally.

Every production source and the production ROM remain byte-identicalv0180.
Seven channel/envelope paths and the surrounding reader entry/region gating
still need cost prediction,then futureIRQ-phase/physical loading alignment.
No fixed loading wait,native RNG replacement or full progression/hardware
equivalence is claimed by this milestone.
