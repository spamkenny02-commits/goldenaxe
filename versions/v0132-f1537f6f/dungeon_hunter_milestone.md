# v0132 - pursuit4F/50/51, aligned charge and cardinal projectile18

Native4FD2/9DA6 implements common emergence and cardinal walking, larger-axis pursuit4A15 with unchanged direction on ties, terrain/bounds rejection and separate variant endings. Type4F resumes walking;50 aligns by16-pixel hero row/column, pauses and executes up to16 charge segments using927F;51 may allocate projectile18 after a completed move. Every state transition retains the source fallthrough/velocity writes, including motion on the charge-control ticks.

Projectile18 now has native4036 initialization and common3DAF/3DFA lifetime/bounds behavior. Its22 literal bytes preserve descriptor8FAA, damage14, vertical origin offset-8, two frames/period2 and cardinal velocity2 pixels per tick. Allocation inherits parent graphics base/position/direction. Current-frame collision descriptor publication includes18, as source0940 does.

1000 isolated original/native cases compare all768 actor bytes with five explicit register-preserving random-input shims. They cover seven even AI states, candidate selection, pursuit/ties, terrain/bounds, alignment/charge, shot chance and occupied/free allocation, plus all four18 initializer/cull directions. State0 uses loader animation0. Reused87CD walk and927F charge tables (17 bytes each) and the new22-byte projectile table match the ROM.

22 controlled PAL/NTSC production segments compare1460 actor frames exactly. They cover appearances, walking, the complete16-segment50 charge and four18 projectile flights through removal. Charge uses a zero collision-map fixture; actor/hero records and initial native clock are controlled. Compared segments end before random pursuit/shoot choices. Shot chance/allocation is exercised only by direct routines; production flights inject18 rather than claiming a complete natural51 attack cycle.

Actual176/122/1BC scroll/load paths verify all34/80/60 loaded tiles at three samples in both regions and thirty first-actor appearance records per path. Random X/Y high bytes and direction, plus other actor records, are excluded. Departure uses controlled relocation before real destination loading. Full natural fights, random placement equivalence, framebuffer/SAT and original clock/RNG remain unproved.

Scope audit againstv0131 permits only these AI helpers/dispatch, type18 initialization/dispatch/publication and new-type collision inclusion. main.c and earlier actor implementations are unchanged. Regressions rerun1440 prior actor/magic cases,48 prior contact/HUD frames, six natural inventory static-background restore routes, ordinary hero/three scrolling directions/eight deterministic enemy timing and natural music89 in both regions. These checks pass.

17 reviewed room actor types52..62 still lack native behavior. Global clock/RNG, full natural combat/progression, remaining audio hooks, ending, complete quests/saves and a natural full playthrough remain incomplete or unverified. Port incomplete.
