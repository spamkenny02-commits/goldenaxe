# Original IRQ workload during paid-exit loading, v0180

A separate read-only emulator build adds original0137,01E3,0202,0205,0226
and full-gated audio caller markers. No original ROM instruction is patched.
The working emulator source is restored after building the DLL. All original
cycle-event arrays on24 actual six-route/mask/region paths are identical to the
archived v0179 reference arrays,including foreground and cumulative IRQ cycles.

675 audio-only interrupts pass4050 wrapper/state comparisons. The0137..0226
wrapper costs442T excluding the reader whenC030 is zero,454T otherwise,
before its final RET. Including interrupt accept/vector and RET gives524T
or536T fixed overhead. Original bank6 reader costs are measured separately:
657..17835T during the observed loading windows. They are not predicted from
reader state by this milestone.

Audio-only IRQs leaveC02F unchanged,restore the bank/SP,and decrementC030 if
nonzero. Full gated IRQs acknowledgeC02E and advanceC02F exactly once. Summing
all measured reader/full-gated spans and independently derived wrapper,
vector and return costs closes the complete observed16D0..0ACE IRQ budget
with zero residual master cycles on all24 paths.

This completes observed IRQ accounting alongside the prior foreground loading
models. It does not yet predict future audio workloads or source IRQ phase
from native state,and no physical loading delay is integrated in the MD ROM.
The production binary and every production source remain byte-identicalv0180.
Refresh RNG,combat/native audio scheduling,other graphics classes,full natural
progression and hardware validation remain open.
